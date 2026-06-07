"""段落分类器：区分格式注解和内容占位符。

核心分类逻辑：
- Layer 1 (P0): 关键词/模式匹配 — 处理 90% 的段落
- Layer 2 (P1): 字号一致性检验 — 处理 8%
- Layer 3: 低置信度兜底 — 处理 2%
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.docx_parser import Paragraph


class SectionType(Enum):
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
    FIGURE_CAPTION = "figure_caption"
    TABLE_CAPTION = "table_caption"
    EQUATION = "equation"
    UNKNOWN = "unknown"


class Classification(Enum):
    FORMAT_ANNOTATION = "format_annotation"
    CONTENT_PLACEHOLDER = "content_placeholder"
    CONTENT_BODY = "content_body"
    SECTION_BOUNDARY = "section_boundary"
    UNKNOWN = "unknown"


@dataclass
class ClassifiedParagraph:
    paragraph: Paragraph
    classification: Classification
    section_type: SectionType
    confidence: float
    reasoning: str = ""


# ── 模式库 ──

_FONT_SIZE_PATTERN = r'(初号|小初|一号|小一|二号|小二|三号|小三|四号|小四|五号|小五)'
_FONT_FAMILY_PATTERN = r'(宋体|黑体|楷体|仿宋|隶书|幼圆|Times\s*New\s*Roman|TNR|Arial)'
_FORMAT_POSITION = r'(居中|顶格|缩进|加粗|加黑|空[一两二三四五六七八九十\d]*[行格]|空行|空一行|接排|悬挂缩进|另起[一]?页|段前|段后|行距|首行)'
_FORMAT_INSTRUCTION = r'(采用|使用|用|要求|应|为|必须|一般|统一|注意|请|不要|不得|可以|需要|放在|在下[方面]|在上[方面]|右边|右对齐|左对齐|包括以下)'

# 示例引导词（"例如"、"如：" → 是示范内容，非格式说明）
_EXAMPLE_MARKER = re.compile(r'^(例如|如)[：:]')

# 所有格式相关关键词（宽泛匹配）
_ANY_FORMAT_TERM = re.compile(
    rf'({_FONT_SIZE_PATTERN}|{_FONT_FAMILY_PATTERN}|{_FORMAT_POSITION}|'
    r'字号|字体|字间距|行间距|页眉|页脚|页码|页面|边距|'
    r'图编号|表编号|公式编号|编号|图名|表名|'
    r'单倍|双倍|多倍|磅值|'
    r'\[M\]|\[J\]|\[D\]|\[P\]|\[S\]|\[N\]|\[A\]|\[C\]|'
    r'著录|文献资料|参考文献.*格式|'
    r'章名|序号|包括以下内容|必须包含|需要.*环境|开发工具|数据库|'
    r'接口函数|伪代码|可执行文件|安装使用说明|电子文档)'
)

# 括号内容
_PAREN_FORMAT_RE = re.compile(r'[（(]([^）)]*(?:号|体|格|齐|缩进|空|间距|居)[^）)]*)[）)]')

# 章节标题前缀匹配（放宽锚定）
_SECTION_HEADINGS = {
    SectionType.ABSTRACT_CN: [
        r'摘\s*要', r'摘要',
    ],
    SectionType.ABSTRACT_EN: [
        r'Abstract', r'ABSTRACT',
    ],
    SectionType.TOC: [
        r'目\s*录', r'目录',
    ],
    SectionType.CONCLUSION: [
        r'结\s*论', r'结论', r'总结', r'结语', r'结束语',
    ],
    SectionType.ACKNOWLEDGEMENT: [
        r'谢\s*辞', r'谢辞', r'致\s*谢', r'致谢',
    ],
    SectionType.REFERENCES: [
        r'参考文献', r'References', r'REFERENCE',
    ],
    SectionType.APPENDIX: [
        r'附\s*录', r'附录', r'Appendix',
    ],
}

_CHAPTER_NUMBER_RE = re.compile(
    r'第[一二三四五六七八九十\d]+章|'
    r'第[一二三四五六七八九十\d]+节|'
    r'^[1-9]\d*[\.\s、]|'
    r'^[1-9]\d*\.[1-9]\d*[\.\s、]?'
)

_COVER_KEYWORDS_RE = re.compile(
    r'(学号|姓名|学院|专业|指导\s*教师|题目|导师|系别|班级|年级|日期|年\s*月\s*日|职称|学\s*院|专\s*业|姓\s*名)'
)

_REF_ENTRY_RE = re.compile(r'^\[\d+\]')
_TOC_LINE_RE = re.compile(r'…{3,}.*\d+$')
_EQUATION_RE = re.compile(r'^\s*\([1-9]\d*-[1-9]\d*\)\s*$')

# 纯格式描述关键词（这些词出现说明在描述格式）
_FORMAT_DESCRIPTION = re.compile(
    r'(格式|排版|要求|规范|范例|样板|说明|指南|标准|规定|条例|'
    r'撰写格式|格式要求|格式范例|格式说明|排版要求|'
    r'以.*表示|.*在下[方]|.*在上[方]|'
    r'验收条例)'
)

# 参考文献类型标记
_REF_TYPE_MARKERS = re.compile(r'\[M\]|\[J\]|\[D\]|\[P\]|\[S\]|\[N\]|\[A\]|\[C\]|著录')

# 图表公式编号说明
_FIG_TAB_EQ_FORMAT = re.compile(
    r'(图编号|表编号|公式编号|编号在|图名|表名|'
    r'章名.*序号|序号.*章名|'
    r'圆括号|右对齐|右\t*对齐)'
)


def classify_paragraph(para: Paragraph,
                       prev_paras: list[Paragraph] = None,
                       next_paras: list[Paragraph] = None) -> ClassifiedParagraph:
    text = para.text.strip()
    if not text:
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.UNKNOWN,
            section_type=SectionType.UNKNOWN,
            confidence=0.0,
            reasoning="空段落",
        )

    # ── Layer 1: 规则匹配 ──

    # P0: 格式注解检测（拓宽）
    format_reason = _check_format_annotation(text, para)
    if format_reason:
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.FORMAT_ANNOTATION,
            section_type=SectionType.FORMAT_ANNOTATION,
            confidence=0.88,
            reasoning=format_reason,
        )

    # P0: 示例引导词（"例如：第4章..." → 不是格式说明，是示范内容）
    if _EXAMPLE_MARKER.match(text):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.CONTENT_BODY,
            section_type=SectionType.UNKNOWN,
            confidence=0.85,
            reasoning="示例内容",
        )

    # P1: 章节标题
    section_type, section_reason = _check_section_heading(text)
    if section_type is not None:
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.CONTENT_PLACEHOLDER,
            section_type=section_type,
            confidence=0.95,
            reasoning=section_reason,
        )

    # P1: 封面关键词
    cover_match = _COVER_KEYWORDS_RE.search(text)
    if cover_match and len(text) < 60:
        if _is_annotation_in_parens(text):
            return ClassifiedParagraph(
                paragraph=para,
                classification=Classification.FORMAT_ANNOTATION,
                section_type=SectionType.FORMAT_ANNOTATION,
                confidence=0.85,
                reasoning="封面格式说明",
            )
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.CONTENT_PLACEHOLDER,
            section_type=SectionType.COVER,
            confidence=0.85,
            reasoning=f"封面字段: {cover_match.group()}",
        )

    # P1: 章节编号
    if _CHAPTER_NUMBER_RE.match(text):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.CONTENT_PLACEHOLDER,
            section_type=SectionType.CHAPTER_HEADING,
            confidence=0.90,
            reasoning="章节编号",
        )

    # P1: 参考文献条目
    if _REF_ENTRY_RE.match(text):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.CONTENT_BODY,
            section_type=SectionType.REFERENCES,
            confidence=0.95,
            reasoning="参考文献条目",
        )

    # P1: 目录点线行
    if _TOC_LINE_RE.search(text):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.CONTENT_PLACEHOLDER,
            section_type=SectionType.TOC,
            confidence=0.90,
            reasoning="目录条目",
        )

    # P1: 格式描述关键词
    if _FORMAT_DESCRIPTION.search(text):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.FORMAT_ANNOTATION,
            section_type=SectionType.FORMAT_ANNOTATION,
            confidence=0.85,
            reasoning="格式描述关键词",
        )

    # P1: 图表公式编号格式说明
    if _FIG_TAB_EQ_FORMAT.search(text):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.FORMAT_ANNOTATION,
            section_type=SectionType.FORMAT_ANNOTATION,
            confidence=0.85,
            reasoning="图表公式格式说明",
        )

    # ── Layer 2: 辅助特征 ──

    # P2: 字号一致性
    size_consistency = _check_size_consistency(text, para)
    if size_consistency is not None and not size_consistency:
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.FORMAT_ANNOTATION,
            section_type=SectionType.FORMAT_ANNOTATION,
            confidence=0.80,
            reasoning="字号描述与实际不一致",
        )

    # P3: 包含格式术语的长文本 → 可能是格式说明
    if len(text) > 15 and _ANY_FORMAT_TERM.search(text):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.FORMAT_ANNOTATION,
            section_type=SectionType.FORMAT_ANNOTATION,
            confidence=0.75,
            reasoning="包含格式术语",
        )

    # P4: 参考文献类型标记
    if _REF_TYPE_MARKERS.search(text) and len(text) > 15:
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.FORMAT_ANNOTATION,
            section_type=SectionType.FORMAT_ANNOTATION,
            confidence=0.80,
            reasoning="参考文献格式描述",
        )

    # ── Layer 3: 兜底 ──

    # 纯数字/符号/短无意义文本 → 可能是示例内容
    if len(text) < 10 and not any(kw in text for kw in ['摘要', '目录', '结论', '谢辞', '附录', '封面']):
        return ClassifiedParagraph(
            paragraph=para,
            classification=Classification.CONTENT_BODY,
            section_type=SectionType.UNKNOWN,
            confidence=0.50,
            reasoning="短文本，可能是示例内容",
        )

    return ClassifiedParagraph(
        paragraph=para,
        classification=Classification.UNKNOWN,
        section_type=SectionType.UNKNOWN,
        confidence=0.30,
        reasoning="无法自动分类",
    )


def _check_format_annotation(text: str, para: Paragraph) -> str:
    """检查是否为格式注解。返回空→不是，非空→判定依据。"""

    # 括号内含字号/字体/格式关键词 → 格式注解
    paren_matches = _PAREN_FORMAT_RE.findall(text)
    for match in paren_matches:
        if re.search(rf'({_FONT_SIZE_PATTERN}|{_FONT_FAMILY_PATTERN}|{_FORMAT_POSITION})', match):
            return f"括号内含格式: {match[:40]}"

    has_font_size = bool(re.search(_FONT_SIZE_PATTERN, text))
    has_font_family = bool(re.search(_FONT_FAMILY_PATTERN, text))
    has_format_pos = bool(re.search(_FORMAT_POSITION, text))

    # 字号/字体 + 格式位置词 → 格式注解
    if (has_font_size or has_font_family) and has_format_pos:
        return f"字体+格式位置: {text[:50]}"

    # 纯格式位置词 + 长度较短（"另起一页"、"居中排版"等）
    if has_format_pos and len(text) < 30:
        return f"短格式位置描述: {text[:50]}"

    # 包含"号字" + 指令词
    if re.search(r'(号字|号\s*[，,]|字体)', text) and len(text) > 10:
        return f"字体相关描述: {text[:50]}"

    # 参考文献格式描述
    if _REF_TYPE_MARKERS.search(text) and len(text) > 20:
        return f"参考文献格式: {text[:50]}"

    return ""


def _check_section_heading(text: str) -> tuple:
    """检查是否为章节标题。对纯标题做精确匹配，对含格式说明的做前缀匹配。"""
    clean = text.replace('\x07', '').replace('\n', '').strip()

    # 先做精确匹配（纯标题，不含额外文字）
    pure_heading_patterns = {
        SectionType.ABSTRACT_CN: [r'^摘\s*要$', r'^摘要$'],
        SectionType.ABSTRACT_EN: [r'^Abstract[\s:：]*$', r'^ABSTRACT[\s:：]*$'],
        SectionType.TOC: [r'^目\s*录$', r'^目录$'],
        SectionType.CONCLUSION: [r'^结\s*论$', r'^结论$'],
        SectionType.ACKNOWLEDGEMENT: [r'^谢\s*辞$', r'^谢辞$', r'^致\s*谢$', r'^致谢$'],
        SectionType.REFERENCES: [r'^参考文献$', r'^References[\s:：]*$'],
        SectionType.APPENDIX: [r'^附\s*录\s*[A-Za-z]*$', r'^附录\s*$', r'^Appendix[\s:：]*$'],
    }

    for stype, patterns in pure_heading_patterns.items():
        for pat in patterns:
            if re.match(pat, clean):
                return stype, f"章节标题(完全匹配): {clean[:30]}"

    # 短文本（<12字符）且以章节关键词开头 → 也是标题
    if len(clean) < 12:
        prefix_map = [
            (SectionType.ABSTRACT_CN, ['摘', '摘要']),
            (SectionType.ABSTRACT_EN, ['Abstract', 'ABSTRACT']),
            (SectionType.TOC, ['目', '目录']),
            (SectionType.CONCLUSION, ['结', '结论']),
            (SectionType.ACKNOWLEDGEMENT, ['谢', '致']),
            (SectionType.REFERENCES, ['参考']),
            (SectionType.APPENDIX, ['附', '附录']),
        ]
        for stype, prefixes in prefix_map:
            for prefix in prefixes:
                if clean.startswith(prefix):
                    return stype, f"章节标题(前缀匹配): {clean[:30]}"

    return None, ""


def _check_size_consistency(text: str, para: Paragraph) -> Optional[bool]:
    actual_size = para.dominant_font_size_pt()
    if actual_size is None:
        return None

    size_names = {
        '初号': 42, '小初': 36, '一号': 26, '小一': 24,
        '二号': 22, '小二': 18, '三号': 16, '小三': 15,
        '四号': 14, '小四': 12, '五号': 10.5, '小五': 9,
    }

    for name, expected_pt in size_names.items():
        if name in text:
            if abs(actual_size - expected_pt) <= 1:
                return True
            else:
                return False

    return None


def _is_annotation_in_parens(text: str) -> bool:
    paren_content = _PAREN_FORMAT_RE.findall(text)
    if not paren_content:
        return False
    paren_total = sum(len(c) for c in paren_content)
    return paren_total > len(text) * 0.3


def _has_font_term(text: str) -> bool:
    return bool(re.search(rf'({_FONT_SIZE_PATTERN}|{_FONT_FAMILY_PATTERN})', text))


def classify_all(paragraphs: list[Paragraph]) -> list[ClassifiedParagraph]:
    results = []
    for i, para in enumerate(paragraphs):
        prev_paras = paragraphs[max(0, i - 3):i]
        next_paras = paragraphs[i + 1:i + 4]
        result = classify_paragraph(para, prev_paras, next_paras)
        results.append(result)
    return results


def classification_stats(results: list[ClassifiedParagraph]) -> dict:
    stats = {
        "total": len(results),
        "format_annotation": 0,
        "content_placeholder": 0,
        "content_body": 0,
        "unknown": 0,
        "high_confidence": 0,
        "low_confidence": 0,
    }
    for r in results:
        if r.classification == Classification.FORMAT_ANNOTATION:
            stats["format_annotation"] += 1
        elif r.classification == Classification.CONTENT_PLACEHOLDER:
            stats["content_placeholder"] += 1
        elif r.classification == Classification.CONTENT_BODY:
            stats["content_body"] += 1
        elif r.classification == Classification.UNKNOWN:
            stats["unknown"] += 1

        if r.confidence >= 0.8:
            stats["high_confidence"] += 1
        else:
            stats["low_confidence"] += 1

    return stats
