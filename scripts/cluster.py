"""格式优先聚类引擎。

核心理念：不再逐段用正则猜"这段文字是什么"，而是：
1. 全量提取每段的格式属性（字体、字号、对齐、缩进、行距）
2. KMeans 聚类，相同格式的段落自动归为一组
3. 输出每个格式簇的统计特征和示例，交给 LLM 一次性标注

这样"居中对齐"等排版属性是第一特征，文本内容只是辅助验证。
"""

import os
import sys
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.docx_parser import Paragraph
try:
    from classifier import classify_paragraph
except Exception:
    classify_paragraph = None

# 尝试导入 sklearn，没有则降级为简单分桶
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


# ── 格式对齐方式映射 ──

_ALIGNMENT_MAP = {
    'left': 0, 'center': 1, 'right': 2, 'justify': 3, None: -1,
}


@dataclass
class ClusterProfile:
    """一个格式簇的统计特征"""
    cluster_id: int
    count: int                                                # 段落数
    examples: list[str] = field(default_factory=list)         # 示例文本 (前3条)
    # 众数/均值
    font_name: Optional[str] = None
    font_size_pt: Optional[float] = None
    bold_ratio: float = 0.0                                   # 加粗比例
    alignment: Optional[str] = None                           # left/center/right/justify
    alignment_ratio: float = 0.0                              # 该对齐方式的比例
    first_line_indent_pt: Optional[float] = None              # 首行缩进均值
    indent_ratio: float = 0.0                                 # 有缩进的比例
    line_spacing: Optional[float] = None                      # 行距均值
    space_before_pt: Optional[float] = None                   # 段前均值
    space_after_pt: Optional[float] = None                    # 段后均值
    style_name: Optional[str] = None                          # Word 样式名
    format_signature: str = ""                                # 稳定格式签名
    # 标注 (由 LLM 填写)
    semantic_label: str = ""                                  # 如 "一级标题"
    confidence: float = 0.0
    classification_counts: dict[str, int] = field(default_factory=dict)
    low_confidence_count: int = 0
    suggested_label: str = ""
    suggested_label_confidence: float = 0.0


@dataclass
class ClusteringResult:
    """聚类结果"""
    labels: list[int]                                          # 每段的簇 ID (-1 = 空段落)
    clusters: list[ClusterProfile]                             # 所有簇的统计
    n_paragraphs: int = 0
    n_clusters: int = 0
    n_empty: int = 0


# ── 特征提取 ──

def _make_feature_vector(para: Paragraph) -> Optional[list[float]]:
    """从段落提取聚类特征向量。空段落返回 None。"""
    if para.is_empty():
        return None

    font_size = para.dominant_font_size_pt() or 12.0
    is_bold = 1.0 if para.is_bold() else 0.0

    # 对齐: 一次性编码 4 类
    align = para.alignment
    align_left = 1.0 if align == 'left' else 0.0
    align_center = 1.0 if align == 'center' else 0.0
    align_right = 1.0 if align == 'right' else 0.0
    align_justify = 1.0 if align == 'justify' else 0.0
    align_none = 1.0 if align is None else 0.0

    # 首行缩进 (归一化: 磅值 / 24, 因为2字符≈24pt)
    indent = (para.first_line_indent_pt or 0.0)
    has_indent = 1.0 if indent > 1.0 else 0.0

    # 行距 (归一化)
    line_sp = (para.line_spacing or 1.0)

    # 段前/段后 (归一化: 磅值 / 12)
    space_before = (para.space_before_pt or 0.0) / 12.0
    space_after = (para.space_after_pt or 0.0) / 12.0

    return [
        font_size / 12.0,     # 归一化到 ~1.0
        is_bold,
        align_left,
        align_center,
        align_right,
        align_justify,
        align_none,
        indent / 24.0,        # 归一到磅值/24
        has_indent,
        line_sp,
        space_before,
        space_after,
    ]


def extract_format_matrix(paragraphs: list[Paragraph]) -> tuple:
    """提取所有非空段落的特征矩阵。

    Returns:
        (matrix: np.ndarray shape (n, 12), valid_indices: list[int])
        valid_indices[i] 是原始 paragraphs 中的索引
    """
    rows = []
    indices = []
    for i, para in enumerate(paragraphs):
        vec = _make_feature_vector(para)
        if vec is not None:
            rows.append(vec)
            indices.append(i)
    if not rows:
        return np.array([]).reshape(0, 12), []
    return np.array(rows), indices


def _format_number(value: Optional[float]) -> str:
    if value is None:
        return "?"
    return f"{value:.1f}".rstrip("0").rstrip(".")


def build_format_signature(profile: ClusterProfile) -> str:
    return " | ".join([
        f"style={profile.style_name or '?'}",
        f"font={profile.font_name or '?'}",
        f"size={_format_number(profile.font_size_pt)}pt",
        f"bold={profile.bold_ratio:.2f}",
        f"align={profile.alignment or '?'}",
        f"firstIndent={_format_number(profile.first_line_indent_pt)}pt",
        f"lineSpacing={_format_number(profile.line_spacing)}",
        f"before={_format_number(profile.space_before_pt)}pt",
        f"after={_format_number(profile.space_after_pt)}pt",
    ])


# ── 聚类 ──

def _estimate_n_clusters(X: np.ndarray, n_samples: int) -> int:
    """自动估计最佳聚类数，论文模板文档使用更高的最小簇数。"""
    unique_count = len(np.unique(X, axis=0))
    if unique_count <= 1:
        return 1

    if n_samples >= 120:
        floor, ceiling = 8, 12
    elif n_samples >= 80:
        floor, ceiling = 7, 10
    elif n_samples >= 40:
        floor, ceiling = 5, 8
    else:
        floor, ceiling = 2, max(2, min(6, n_samples))

    floor = min(floor, unique_count)
    ceiling = min(ceiling, unique_count)

    if not _HAS_SKLEARN:
        return min(ceiling, max(floor, int(math.sqrt(n_samples))))

    max_k = min(ceiling, max(floor, n_samples // 3))
    best_k, best_score = floor, -1.0

    for k in range(floor, max_k + 1):
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(X, labels)
            if score > best_score:
                best_score = score
                best_k = k
        except Exception:
            continue

    return best_k


def _classification_stats(cluster_paras: list[Paragraph]) -> tuple[dict[str, int], int]:
    counts = {
        "format_annotation": 0,
        "content_placeholder": 0,
        "content_body": 0,
        "section_boundary": 0,
        "unknown": 0,
    }
    low_confidence = 0
    if classify_paragraph is None:
        return counts, len(cluster_paras)

    for para in cluster_paras:
        result = classify_paragraph(para)
        counts[result.classification.value] = counts.get(result.classification.value, 0) + 1
        if result.confidence < 0.75:
            low_confidence += 1
    return counts, low_confidence


def _suggest_label(profile: ClusterProfile) -> tuple[str, float]:
    examples_text = " ".join(profile.examples)
    format_count = profile.classification_counts.get("format_annotation", 0)
    body_count = profile.classification_counts.get("content_body", 0)
    placeholder_count = profile.classification_counts.get("content_placeholder", 0)
    total = max(profile.count, 1)
    format_ratio = format_count / total
    body_ratio = body_count / total
    placeholder_ratio = placeholder_count / total

    if "本科毕业设计" in examples_text and profile.alignment == "center" and (profile.font_size_pt or 0) >= 22:
        return "论文大标题", 0.95
    if any(keyword in examples_text for keyword in ["学号", "姓名", "学院", "专业", "指导教师"]):
        return "封面信息", 0.88
    if "Abstract" in examples_text:
        return "英文摘要标题", 0.86
    if "摘" in examples_text and "要" in examples_text and profile.alignment == "center":
        return "中文摘要标题", 0.86
    if "目" in examples_text and "录" in examples_text and profile.alignment == "center":
        return "目录标题", 0.86
    if "Key words" in examples_text or "Key Words" in examples_text:
        return "英文关键词标签", 0.84
    if "关键词" in examples_text:
        return "中文关键词标签", 0.84
    if "参考文献" in examples_text:
        return "参考文献标题", 0.84
    if format_ratio >= 0.55:
        return "格式说明", min(0.95, 0.65 + format_ratio * 0.35)
    if profile.indent_ratio >= 0.65 and profile.alignment in {"justify", "left"} and (profile.font_size_pt is None or 10 <= profile.font_size_pt <= 13):
        return "正文段落", max(0.75, min(0.9, 0.65 + body_ratio * 0.2))
    if placeholder_ratio >= 0.5:
        return "其他", 0.6
    return "", 0.0


def _build_cluster_profile(cluster_id: int, cluster_paras: list[Paragraph]) -> ClusterProfile:
    """为一个簇构建统计 Profile"""
    n = len(cluster_paras)

    # 字体名众数
    font_names = [p.dominant_font_name() for p in cluster_paras]
    font_name = max(set(font_names), key=font_names.count) if font_names else None

    # 字号众数
    font_sizes = [p.dominant_font_size_pt() for p in cluster_paras if p.dominant_font_size_pt()]
    font_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else None

    # 加粗比例
    bold_count = sum(1 for p in cluster_paras if p.is_bold())
    bold_ratio = bold_count / n if n > 0 else 0.0

    # 对齐方式众数
    alignments = [p.alignment for p in cluster_paras if p.alignment]
    alignment = max(set(alignments), key=alignments.count) if alignments else None
    align_count = sum(1 for p in cluster_paras if p.alignment == alignment)
    align_ratio = align_count / n if n > 0 else 0.0

    # 首行缩进均值
    indents = [p.first_line_indent_pt for p in cluster_paras if p.first_line_indent_pt]
    mean_indent = sum(indents) / len(indents) if indents else None
    indent_count = sum(1 for p in cluster_paras if p.first_line_indent_pt and p.first_line_indent_pt > 1)
    indent_ratio = indent_count / n if n > 0 else 0.0

    # 行距均值
    line_spacings = [p.line_spacing for p in cluster_paras if p.line_spacing]
    mean_line_sp = sum(line_spacings) / len(line_spacings) if line_spacings else None

    # 段前/段后均值
    sb = [p.space_before_pt for p in cluster_paras if p.space_before_pt]
    sa = [p.space_after_pt for p in cluster_paras if p.space_after_pt]
    mean_sb = sum(sb) / len(sb) if sb else None
    mean_sa = sum(sa) / len(sa) if sa else None

    # Word 样式名众数
    styles = [p.style_name for p in cluster_paras if p.style_name]
    style = max(set(styles), key=styles.count) if styles else None

    # 示例文本
    examples = [p.text.strip()[:60] for p in cluster_paras[:3] if p.text.strip()]

    profile = ClusterProfile(
        cluster_id=cluster_id,
        count=n,
        examples=examples,
        font_name=font_name,
        font_size_pt=font_size,
        bold_ratio=bold_ratio,
        alignment=alignment,
        alignment_ratio=align_ratio,
        first_line_indent_pt=mean_indent,
        indent_ratio=indent_ratio,
        line_spacing=mean_line_sp,
        space_before_pt=mean_sb,
        space_after_pt=mean_sa,
        style_name=style,
    )
    profile.classification_counts, profile.low_confidence_count = _classification_stats(cluster_paras)
    profile.suggested_label, profile.suggested_label_confidence = _suggest_label(profile)
    return profile


def cluster_paragraphs(paragraphs: list[Paragraph], n_clusters: int = None) -> ClusteringResult:
    """对段落按格式特征聚类，返回聚类结果。

    Args:
        paragraphs: 解析后的段落列表
        n_clusters: 指定簇数 (None=自动确定)

    Returns:
        ClusteringResult 含每段标签和簇统计
    """
    X, valid_indices = extract_format_matrix(paragraphs)

    if len(X) == 0:
        return ClusteringResult(
            labels=[-1] * len(paragraphs),
            clusters=[],
            n_paragraphs=len(paragraphs),
            n_empty=len(paragraphs),
        )

    n_valid = len(X)
    n_empty = len(paragraphs) - n_valid

    # 自动确定簇数
    if n_clusters is None:
        n_clusters = _estimate_n_clusters(X, n_valid)

    print(f"[聚类] {n_valid} 个非空段落 → {n_clusters} 个格式簇 (空段落: {n_empty})")

    # 标准化 + KMeans
    if _HAS_SKLEARN and n_valid >= n_clusters * 2:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_ids = km.fit_predict(X_scaled)
    else:
        # 降级：简单按字号+对齐分桶
        cluster_ids = _simple_bucket(X, n_clusters)

    # 构建完整标签数组 (-1 = 空段落)
    full_labels = [-1] * len(paragraphs)
    for j, orig_idx in enumerate(valid_indices):
        full_labels[orig_idx] = int(cluster_ids[j])

    # 构建每个簇的 Profile
    clusters = []
    for cid in range(n_clusters):
        cluster_paras = []
        for j, orig_idx in enumerate(valid_indices):
            if cluster_ids[j] == cid:
                cluster_paras.append(paragraphs[orig_idx])

        profile = _build_cluster_profile(cid, cluster_paras)
        profile.format_signature = build_format_signature(profile)
        clusters.append(profile)

    # 按段落数降序排列
    clusters.sort(key=lambda c: c.count, reverse=True)

    return ClusteringResult(
        labels=full_labels,
        clusters=clusters,
        n_paragraphs=len(paragraphs),
        n_clusters=n_clusters,
        n_empty=n_empty,
    )


def _simple_bucket(X: np.ndarray, n_buckets: int) -> np.ndarray:
    """无 sklearn 时的简单分桶：按字号+对齐组合分组"""
    # 特征: [font_size_norm, bold, align_left, align_center, align_right, align_justify, align_none, indent_norm, has_indent, line_sp, space_before, space_after]
    # 用字号(列0)和对齐方式(列2-5)做简单分组
    font_sizes = X[:, 0]  # 归一化字号
    # 找对齐(列2-6的argmax)
    align_idx = np.argmax(X[:, 2:7], axis=1)

    # 组合 key: 字号桶 (每0.2一档) + 对齐方式
    keys = []
    for i in range(len(X)):
        size_bucket = int(font_sizes[i] * 5)  # 0.2 per bucket
        key = size_bucket * 10 + align_idx[i]
        keys.append(key)

    # 按 key 分组，小的组合并到大的
    from collections import Counter
    key_counts = Counter(keys)
    # 保留 top n_buckets 个 key，其余归到最近的
    top_keys = [k for k, _ in key_counts.most_common(n_buckets)]

    labels = np.zeros(len(X), dtype=int)
    for i, k in enumerate(keys):
        if k in top_keys:
            labels[i] = top_keys.index(k)
        else:
            # 归到最近的有值的 key
            labels[i] = abs(np.array(top_keys) - k).argmin()

    return labels


def print_cluster_summary(result: ClusteringResult):
    """打印聚类结果摘要 (供 Claude 阅读和标注)"""
    print(f"\n{'='*60}")
    print(f"格式聚类结果: {result.n_clusters} 个格式簇")
    print(f"{'='*60}")
    print(f"总段落: {result.n_paragraphs}, 空段落: {result.n_empty}")
    print()

    for c in sorted(result.clusters, key=lambda x: x.count, reverse=True):
        align_str = c.alignment or '未指定'
        font_str = f"{c.font_name or '?'} {c.font_size_pt or '?'}pt"
        bold_str = "加粗" if c.bold_ratio > 0.5 else ""
        indent_str = f"首行缩进{c.first_line_indent_pt:.0f}pt" if c.indent_ratio > 0.5 else ""
        space_str = ""
        if c.space_before_pt and c.space_before_pt > 1:
            space_str += f"段前{c.space_before_pt:.0f}pt "
        if c.space_after_pt and c.space_after_pt > 1:
            space_str += f"段后{c.space_after_pt:.0f}pt"

        print(f"[簇 {c.cluster_id}] {c.count} 段 | {font_str} | {align_str} | {bold_str} {indent_str} {space_str}")
        if c.style_name:
            print(f"           Word样式: {c.style_name}")
        print(f"           格式签名: {c.format_signature}")
        if c.suggested_label:
            print(f"           建议标签: {c.suggested_label} ({c.suggested_label_confidence:.2f})")
        print(f"           分类统计: {c.classification_counts}, 低置信度: {c.low_confidence_count}")
        for ex in c.examples[:3]:
            print(f"           示例: {ex[:70]}")
        print()
