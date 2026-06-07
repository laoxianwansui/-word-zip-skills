"""Parse Chinese thesis formatting instructions into structured rules."""

from dataclasses import dataclass
import re

from extractor import TextFormat

_SIZE_TO_PT = {
    "初号": 42,
    "小初": 36,
    "一号": 26,
    "小一": 24,
    "二号": 22,
    "小二": 18,
    "三号": 16,
    "小三": 15,
    "四号": 14,
    "小四": 12,
    "五号": 10.5,
    "小五": 9,
}

_SIZE_TO_CMD = {
    "初号": "\\zihao{0}",
    "小初": "\\zihao{-0}",
    "一号": "\\zihao{1}",
    "小一": "\\zihao{-1}",
    "二号": "\\zihao{2}",
    "小二": "\\zihao{-2}",
    "三号": "\\zihao{3}",
    "小三": "\\zihao{-3}",
    "四号": "\\zihao{4}",
    "小四": "\\zihao{-4}",
    "五号": "\\zihao{5}",
    "小五": "\\zihao{-5}",
}

_FONT_TO_CMD = {
    "宋体": "\\songti",
    "黑体": "\\heiti",
    "楷体": "\\kaishu",
    "仿宋": "\\fangsong",
    "Times New Roman": "\\rmfamily",
    "TimesNewRoman": "\\rmfamily",
    "TNR": "\\rmfamily",
    "Arial": "\\rmfamily",
}


@dataclass
class FormatRule:
    semantic_label: str
    text_format: TextFormat
    source_text: str
    confidence: float = 0.8


def parse_format_rule(text: str) -> FormatRule | None:
    source = (text or "").strip()
    if not source:
        return None

    compact = re.sub(r"\s+", "", source)
    if not _looks_like_format_rule(compact):
        return None

    fmt = TextFormat()
    semantic_label = _semantic_label(compact)

    size_name = _find_size_name(compact)
    if size_name:
        fmt.font_size_pt = _SIZE_TO_PT[size_name]
        fmt.font_size_cmd = _SIZE_TO_CMD[size_name]

    font_name = _find_font_name(source, compact)
    if font_name:
        cmd = _FONT_TO_CMD[font_name]
        if font_name in {"Times New Roman", "TimesNewRoman", "TNR", "Arial"}:
            fmt.font_en = cmd
            fmt.font_cn = cmd
        else:
            fmt.font_cn = cmd

    if any(word in compact for word in ["加粗", "加黑", "黑体"]):
        fmt.bold = "黑体" not in compact or "加" in compact

    if "居中" in compact:
        fmt.alignment = "center"
    elif "右对齐" in compact:
        fmt.alignment = "right"
    elif "左对齐" in compact or "顶格" in compact:
        fmt.alignment = "left"
    elif "接排" in compact or "正文" in compact or "内容" in compact:
        fmt.alignment = "justify"

    if "首行缩进两个字" in compact or "首行缩进2个字" in compact or "首行缩进二个字" in compact:
        fmt.first_line_indent = "2\\ccwd"
    elif "首行缩进" in compact:
        fmt.first_line_indent = "2\\ccwd"

    return FormatRule(
        semantic_label=semantic_label,
        text_format=fmt,
        source_text=source,
        confidence=0.9 if semantic_label else 0.8,
    )


def _looks_like_format_rule(text: str) -> bool:
    return bool(
        _find_size_name(text)
        or _find_font_name(text, text)
        or any(word in text for word in ["居中", "顶格", "缩进", "行距", "加粗", "加黑", "字体", "字号"])
    )


def _find_size_name(text: str) -> str | None:
    names = ["小初", "小一", "小二", "小三", "小四", "小五", "初号", "一号", "二号", "三号", "四号", "五号"]
    for name in names:
        if re.search(rf"(?<![大小]){re.escape(name)}(?:号|字|字体)?", text):
            return name
    return None


def _find_font_name(source: str, compact: str) -> str | None:
    normalized = compact.replace("TimesNewRoman", "Times New Roman")
    for name in ["Times New Roman", "TNR", "Arial", "宋体", "黑体", "楷体", "仿宋"]:
        if name in source or name in normalized or name in compact:
            return name
    return None


def _semantic_label(text: str) -> str:
    if "KeyWords" in text or "Keywords" in text or "Key words" in text:
        return "英文关键词标签"
    if "关键词" in text:
        return "中文关键词标签"
    if "Abstract" in text or "ABSTRACT" in text:
        return "英文摘要标题"
    if "摘要" in text or "摘" in text and "要" in text:
        return "中文摘要标题"
    if "目录" in text or "目" in text and "录" in text:
        return "目录标题"
    if "参考文献" in text:
        return "参考文献标题"
    if "附录" in text:
        return "附录标题"
    if "谢辞" in text or "致谢" in text:
        return "谢辞标题"
    if "正文" in text or "内容" in text:
        return "正文段落"
    return ""
