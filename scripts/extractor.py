"""格式规格提取器 (聚类版)。

新架构：不再从正则匹配的"格式注解"文本中解析字号/字体，
而是直接使用聚类结果中每个簇的格式统计数据。
Claude 标注每个簇的语义角色后，直接映射到 ThesisSpec。
"""

from dataclasses import dataclass, field
from typing import Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cluster import ClusteringResult, ClusterProfile


# ── 字号 pt → LaTeX \zihao 映射 ──

_PT_TO_ZIHAO = {
    42: '\\zihao{0}', 36: '\\zihao{-0}',
    26: '\\zihao{1}', 24: '\\zihao{-1}',
    22: '\\zihao{2}', 18: '\\zihao{-2}',
    16: '\\zihao{3}', 15: '\\zihao{-3}',
    14: '\\zihao{4}', 12: '\\zihao{-4}',
    10.5: '\\zihao{5}', 9: '\\zihao{-5}',
}

_FONT_TO_LATEX = {
    '宋体': '\\songti', '黑体': '\\heiti', '楷体': '\\kaishu',
    '仿宋': '\\fangsong',
    'Times New Roman': '\\rmfamily', 'TNR': '\\rmfamily',
}


def _pt_to_zihao(pt: Optional[float]) -> str:
    r"""磅值 → 最近的 \zihao 命令"""
    if pt is None:
        return '\\zihao{-4}'
    # 找最近的匹配
    best = min(_PT_TO_ZIHAO.keys(), key=lambda k: abs(k - pt))
    return _PT_TO_ZIHAO[best]


def _font_to_latex(name: Optional[str]) -> str:
    if not name:
        return '\\songti'
    return _FONT_TO_LATEX.get(name, '\\songti')


# ── Data Classes ──

@dataclass
class PageSetup:
    paper: str = "a4paper"
    top_margin: float = 2.54
    bottom_margin: float = 2.54
    left_margin: float = 3.18
    right_margin: float = 3.18
    line_spread: float = 1.5


@dataclass
class TextFormat:
    font_cn: str = "\\songti"
    font_en: str = "\\rmfamily"
    font_size_cmd: str = "\\zihao{-4}"
    font_size_pt: float = 12.0
    bold: bool = False
    alignment: str = "left"
    first_line_indent: str = "2\\ccwd"
    space_before: str = "0pt"
    space_after: str = "0pt"


@dataclass
class ThesisSpec:
    document_class: str = "ctexrep"
    page_setup: PageSetup = field(default_factory=PageSetup)

    cover_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{2}", font_size_pt=22,
        bold=True, alignment="center"
    ))
    cover_info: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\songti", font_size_cmd="\\zihao{-3}", font_size_pt=15,
        bold=False, alignment="center"
    ))
    cover_fields: list[str] = field(default_factory=lambda: [
        "题目", "学号", "姓名", "学院", "专业", "指导教师", "指导教师职称"
    ])

    abstract_cn_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{3}", font_size_pt=16,
        bold=False, alignment="center"
    ))
    abstract_cn_body: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\songti", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False
    ))
    abstract_cn_keyword_label: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False
    ))
    abstract_cn_keyword_body: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\songti", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False
    ))

    abstract_en_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_en="\\rmfamily", font_size_cmd="\\zihao{3}", font_size_pt=16,
        bold=True, alignment="center"
    ))
    abstract_en_body: TextFormat = field(default_factory=lambda: TextFormat(
        font_en="\\rmfamily", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False
    ))
    abstract_en_keyword_label: TextFormat = field(default_factory=lambda: TextFormat(
        font_en="\\rmfamily", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=True
    ))
    abstract_en_keyword_body: TextFormat = field(default_factory=lambda: TextFormat(
        font_en="\\rmfamily", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False
    ))

    toc_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{3}", font_size_pt=16,
        bold=False, alignment="center"
    ))

    heading1: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{4}", font_size_pt=14,
        bold=False, alignment="left"
    ))
    heading2: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False, alignment="left"
    ))
    heading3: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\kaishu", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False, alignment="left"
    ))

    body_text: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\songti", font_size_cmd="\\zihao{-4}", font_size_pt=12,
        bold=False, first_line_indent="2\\ccwd"
    ))

    conclusion_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{4}", font_size_pt=14,
        bold=False, alignment="left"
    ))

    acknowledgement_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{4}", font_size_pt=14,
        bold=False, alignment="center"
    ))

    references_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{4}", font_size_pt=14,
        bold=False, alignment="left"
    ))
    references_body: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\songti", font_size_cmd="\\zihao{5}", font_size_pt=10.5,
        bold=False
    ))

    appendix_title: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\heiti", font_size_cmd="\\zihao{4}", font_size_pt=14,
        bold=False, alignment="center"
    ))

    figure_caption_below: bool = True
    table_caption_above: bool = True
    equation_number_right: bool = True

    header_font: TextFormat = field(default_factory=lambda: TextFormat(
        font_cn="\\songti", font_size_cmd="\\zihao{5}", font_size_pt=10.5,
        bold=False
    ))


def format_rule_to_text_format(profile: ClusterProfile, target_label: str = "") -> Optional[TextFormat]:
    try:
        from format_rule_parser import parse_format_rule
    except Exception:
        return None

    fallback = None
    for example in profile.examples:
        rule = parse_format_rule(example)
        if not rule:
            continue
        if rule.semantic_label and target_label and _match_label_to_field(rule.semantic_label) == _match_label_to_field(target_label):
            return rule.text_format
        if fallback is None:
            fallback = rule.text_format
    return fallback


# ── 簇 → TextFormat 转换 ──

def cluster_to_text_format(profile: ClusterProfile, target_label: str = "") -> TextFormat:
    """从簇的格式统计创建 TextFormat"""
    rule_format = format_rule_to_text_format(profile, target_label)
    if rule_format is not None:
        return rule_format

    fmt = TextFormat()

    # 字体
    if profile.font_name:
        fmt.font_cn = _font_to_latex(profile.font_name)
        fmt.font_en = _font_to_latex(profile.font_name)

    # 字号
    if profile.font_size_pt:
        fmt.font_size_cmd = _pt_to_zihao(profile.font_size_pt)
        fmt.font_size_pt = profile.font_size_pt

    # 加粗
    fmt.bold = profile.bold_ratio > 0.5

    # 对齐
    if profile.alignment:
        fmt.alignment = profile.alignment

    # 缩进
    if profile.indent_ratio > 0.5 and profile.first_line_indent_pt:
        fmt.first_line_indent = f"{profile.first_line_indent_pt:.0f}pt"

    # 间距
    if profile.space_before_pt and profile.space_before_pt > 0:
        fmt.space_before = f"{profile.space_before_pt:.0f}pt"
    if profile.space_after_pt and profile.space_after_pt > 0:
        fmt.space_after = f"{profile.space_after_pt:.0f}pt"

    return fmt


# ── 簇 → 规格字段映射表 ──
# 每个语义标签对应 ThesisSpec 的哪个字段

_LABEL_TO_FIELD = {
    '论文大标题': 'cover_title',
    '封面信息': 'cover_info',
    '中文摘要标题': 'abstract_cn_title',
    '中文摘要正文': 'abstract_cn_body',
    '中文关键词标签': 'abstract_cn_keyword_label',
    '中文关键词正文': 'abstract_cn_keyword_body',
    '英文摘要标题': 'abstract_en_title',
    '英文摘要正文': 'abstract_en_body',
    '英文关键词标签': 'abstract_en_keyword_label',
    '英文关键词正文': 'abstract_en_keyword_body',
    '目录标题': 'toc_title',
    '一级标题': 'heading1',
    '章标题': 'heading1',
    '二级标题': 'heading2',
    '节标题': 'heading2',
    '三级标题': 'heading3',
    '小节标题': 'heading3',
    '正文段落': 'body_text',
    '正文': 'body_text',
    '结论标题': 'conclusion_title',
    '谢辞标题': 'acknowledgement_title',
    '致谢标题': 'acknowledgement_title',
    '参考文献标题': 'references_title',
    '参考文献条目': 'references_body',
    '附录标题': 'appendix_title',
    '页眉': 'header_font',
    '页脚': 'footer_font',
    '图题': 'figure_caption',
    '表题': 'table_caption',
    '公式': 'equation',
}


def extract_specs_from_clusters(
    result: ClusteringResult,
    label_map: dict[int, str] = None,
) -> ThesisSpec:
    """从聚类结果和 LLM 标注直接生成 ThesisSpec。

    这是新架构的核心：不再需要分析"格式注解"文本，
    直接从格式统计数据中取值。

    Args:
        result: 聚类结果
        label_map: {cluster_id: semantic_label} LLM 标注结果

    Returns:
        ThesisSpec
    """
    spec = ThesisSpec()

    if label_map is None:
        label_map = {}

    print(f"[提取] 从 {len(result.clusters)} 个格式簇生成规格...")

    for profile in result.clusters:
        cid = profile.cluster_id
        label = label_map.get(cid, "")

        # 跳过未标注的簇
        if not label:
            print(f"  [簇{cid}] 未标注 → 跳过 ({profile.count}段, {profile.font_name} {profile.font_size_pt}pt)")
            continue

        # 查找对应的 spec 字段
        field_name = _match_label_to_field(label)
        if not field_name:
            print(f"  [簇{cid}] \"{label}\" → 未匹配到规格字段 ({profile.count}段)")
            continue

        # 将簇的格式统计转为 TextFormat
        fmt = cluster_to_text_format(profile, label)

        # 写入 spec 对应字段
        _set_spec_field(spec, field_name, fmt, profile)

        print(f"  [簇{cid}] \"{label}\" → spec.{field_name} "
              f"({fmt.font_cn} {fmt.font_size_cmd}, {profile.count}段)")

    return spec


def _match_label_to_field(label: str) -> Optional[str]:
    """将 LLM 标注的语义标签映射到 ThesisSpec 字段名"""
    # 精确匹配
    if label in _LABEL_TO_FIELD:
        return _LABEL_TO_FIELD[label]

    # 模糊匹配
    for key, field in _LABEL_TO_FIELD.items():
        if key in label or label in key:
            return field

    return None


def _set_spec_field(spec: ThesisSpec, field_name: str, fmt: TextFormat, profile: ClusterProfile):
    """将格式写入 ThesisSpec 的对应字段"""
    if hasattr(spec, field_name):
        setattr(spec, field_name, fmt)


# ── 向后兼容 ──

def extract_specs(structure=None):
    """向后兼容的入口。如果传入的是旧 DocumentStructure，转为使用聚类。

    实际上新架构中不再需要 analyze_structure，
    但如果调用方仍传入 structure，我们尽量兼容。
    """
    raise DeprecationWarning(
        "请使用 extract_specs_from_clusters(result, label_map) 替代 extract_specs(structure)。"
        "新流程: cluster_paragraphs() → LLM标注 → extract_specs_from_clusters()"
    )


# ── 辅助：生成 LLM 标注提示 ──

def format_clusters_for_labeling(result: ClusteringResult) -> str:
    """将聚类结果格式化为 LLM 可读的标注请求。

    这个输出会被包含在 SKILL.md 工作流中，由 Claude 阅读并标注。
    """
    lines = [
        f"以下是 {result.n_clusters} 个格式簇的统计信息，请为每个簇标注语义角色：",
        "",
        "| 簇ID | 段数 | 字体 | 字号 | 加粗 | 对齐 | 缩进 | 间距 | 示例 |",
        "|------|------|------|------|------|------|------|------|------|",
    ]

    for c in result.clusters:
        font = f"{c.font_name or '?'}"
        size = f"{c.font_size_pt:.0f}pt" if c.font_size_pt else "?"
        bold = "✓" if c.bold_ratio > 0.5 else ""
        align = c.alignment or "?"
        indent = f"{c.first_line_indent_pt:.0f}pt" if c.indent_ratio > 0.5 else ""
        space = ""
        if c.space_before_pt and c.space_before_pt > 1:
            space += f"前{c.space_before_pt:.0f}pt"
        if c.space_after_pt and c.space_after_pt > 1:
            space += f"后{c.space_after_pt:.0f}pt"
        example = c.examples[0][:40] if c.examples else ""

        lines.append(
            f"| {c.cluster_id} | {c.count} | {font} | {size} | {bold} | "
            f"{align} | {indent} | {space} | {example} |"
        )

    lines.append("")
    lines.append("**可选标签**: 论文大标题, 封面信息, 中文摘要标题, 中文摘要正文, ")
    lines.append("  中文关键词标签, 中文关键词正文, 英文摘要标题, 英文摘要正文, ")
    lines.append("  英文关键词标签, 英文关键词正文, 目录标题, 一级标题(章标题), ")
    lines.append("  二级标题(节标题), 三级标题(小节标题), 正文段落, 结论标题, ")
    lines.append("  谢辞标题, 参考文献标题, 参考文献条目, 附录标题, 页眉, 页脚, ")
    lines.append("  图题, 表题, 公式, 格式说明(可忽略), 其他(可忽略)")
    lines.append("")
    lines.append("请以 JSON 格式返回标注结果: `{\"0\": \"一级标题\", \"1\": \"正文段落\", ...}`")

    return "\n".join(lines)
