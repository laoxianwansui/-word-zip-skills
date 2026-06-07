"""文档结构分析引擎 (聚类版)。

新架构：使用格式聚类 + LLM 标注替代旧的正则分类器。
"""

from dataclasses import dataclass, field
from typing import Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.docx_parser import ParsedDocument
from cluster import cluster_paragraphs, print_cluster_summary, ClusteringResult


# ── 保持旧的 Section 和 DocumentStructure 以兼容 generator ──

class SectionType:
    COVER = "cover"
    ABSTRACT_CN = "abstract_cn"
    ABSTRACT_EN = "abstract_en"
    TOC = "toc"
    CHAPTER_HEADING = "chapter_heading"
    CHAPTER_BODY = "chapter_body"
    CONCLUSION = "conclusion"
    ACKNOWLEDGEMENT = "acknowledgement"
    REFERENCES = "references"
    APPENDIX = "appendix"
    FORMAT_ANNOTATION = "format_annotation"
    UNKNOWN = "unknown"


@dataclass
class Section:
    section_type: str = SectionType.UNKNOWN
    title: str = ""
    start_index: int = 0
    end_index: int = 0
    font_name: Optional[str] = None
    font_size_pt: Optional[float] = None
    bold: bool = False
    alignment: Optional[str] = None


@dataclass
class DocumentStructure:
    file_type: str = ""
    total_paragraphs: int = 0
    sections: list = field(default_factory=list)
    has_cover: bool = False
    has_abstract_cn: bool = False
    has_abstract_en: bool = False
    has_toc: bool = False
    chapter_count: int = 0
    has_conclusion: bool = False
    has_acknowledgement: bool = False
    has_references: bool = False
    has_appendix: bool = False


def analyze_structure(parsed_doc: ParsedDocument) -> tuple[DocumentStructure, ClusteringResult]:
    """分析文档结构。

    新流程：先聚类，再由 LLM 标注，返回两者。

    Returns:
        (DocumentStructure, ClusteringResult)
        ClusteringResult 需要传给 LLM 标注后用于 extract_specs_from_clusters()
    """
    print("[分析] 正在按格式聚类...")
    result = cluster_paragraphs(parsed_doc.paragraphs)
    print_cluster_summary(result)

    # 构建基本的 DocumentStructure (保持向后兼容)
    structure = DocumentStructure(
        file_type=parsed_doc.file_type,
        total_paragraphs=len(parsed_doc.paragraphs),
    )

    # 从簇的示例文本推断基本结构
    _infer_basic_structure(structure, result)

    print(f"\n[分析] 基本结构: 封面={structure.has_cover}, 摘要={structure.has_abstract_cn}, "
          f"目录={structure.has_toc}, 章={structure.chapter_count}, "
          f"结论={structure.has_conclusion}, 谢辞={structure.has_acknowledgement}, "
          f"参考文献={structure.has_references}, 附录={structure.has_appendix}")

    return structure, result


def _infer_basic_structure(structure: DocumentStructure, result: ClusteringResult):
    """从簇的示例文本推断文档基本结构（辅助信息，不影响格式提取）"""
    all_examples = []
    for c in result.clusters:
        all_examples.extend(c.examples)

    all_text = " ".join(all_examples)

    structure.has_cover = any(kw in all_text for kw in ['学号', '姓名', '题目', '学院', '专业'])
    structure.has_abstract_cn = '摘要' in all_text or '摘  要' in all_text
    structure.has_abstract_en = 'Abstract' in all_text
    structure.has_toc = '目录' in all_text or '目  录' in all_text
    structure.chapter_count = sum(1 for ex in all_examples if ex.startswith('第') and '章' in ex)
    structure.has_conclusion = '结论' in all_text or '结  论' in all_text
    structure.has_acknowledgement = '谢辞' in all_text or '致谢' in all_text
    structure.has_references = '参考文献' in all_text
    structure.has_appendix = '附录' in all_text or '附  录' in all_text
