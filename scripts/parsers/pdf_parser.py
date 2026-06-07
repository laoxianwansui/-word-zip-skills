"""解析 .pdf 文件，提取文本块及其字体和位置信息。

使用 PyMuPDF (fitz) 进行文本提取，pdfplumber 辅助提取表格。
"""

from dataclasses import dataclass, field
from typing import Optional
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.docx_parser import (
    Paragraph, FormattedSpan, ParsedDocument, TableInfo
)


# PDF 中文字体名映射到标准字体名
_CJK_FONT_MAP = {
    'simsun': '宋体',
    'simsunb': '宋体',
    'simhei': '黑体',
    'simkaib': '楷体',
    'kaiti': '楷体',
    'kaiti_gb2312': '楷体',
    'fangsong': '仿宋',
    'fangsong_gb2312': '仿宋',
    'simli': '隶书',
    'simyou': '幼圆',
    'microsoftyahei': '微软雅黑',
    'msyahei': '微软雅黑',
    'timesnewroman': 'Times New Roman',
    'timesnewromanps': 'Times New Roman',
    'timesnewromanpsmt': 'Times New Roman',
    'arial': 'Arial',
    'arialmt': 'Arial',
    'helvetica': 'Helvetica',
    'courier': 'Courier',
    'couriernew': 'Courier New',
    'songti': '宋体',
    'heiti': '黑体',
    'kaishu': '楷体',
}


def _normalize_font_name(raw_name: str) -> Optional[str]:
    """将 PDF 中的字体名标准化"""
    if not raw_name:
        return None
    # 去掉子集前缀 (如 "ABCDEF+SimSun" → "SimSun")
    if '+' in raw_name:
        raw_name = raw_name.split('+', 1)[1]
    # 去掉风格后缀
    raw_name = re.sub(r'[,\-_]?(Bold|Italic|Oblique|Regular|MT|PS|Std)$', '', raw_name, flags=re.I)
    key = raw_name.strip().lower().replace(' ', '')
    return _CJK_FONT_MAP.get(key, raw_name.strip())


def _is_bold_from_font_name(font_name: str) -> bool:
    """从字体名推断是否加粗"""
    if not font_name:
        return False
    lowered = font_name.lower()
    return any(kw in lowered for kw in ['bold', 'black', 'heavy'])


def parse_pdf(file_path: str) -> ParsedDocument:
    """解析 PDF 文件，返回统一的 ParsedDocument 对象。

    Args:
        file_path: .pdf 文件的绝对路径

    Returns:
        ParsedDocument 对象
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")

    doc = fitz.open(file_path)
    doc_info = ParsedDocument(
        file_path=file_path,
        file_type="pdf",
        total_pages_estimate=len(doc),
        raw_metadata=dict(doc.metadata) if doc.metadata else {},
    )

    para_index = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        # 使用 dict 模式获取结构化文本
        text_dict = page.get_text("dict")

        for block in text_dict.get("blocks", []):
            block_type = block.get("type", 0)

            if block_type == 0:  # 文本块
                lines = block.get("lines", [])
                if not lines:
                    continue

                # 将相邻的同格式行合并为段落
                block_text_parts = []
                all_spans = []

                for line in lines:
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if not text.strip():
                            continue
                        font_name = _normalize_font_name(str(span.get("font", "")))
                        font_size = span.get("size", None)  # PyMuPDF 直接返回 pt
                        bold = _is_bold_from_font_name(str(span.get("font", "")))
                        flags = span.get("flags", 0)
                        # flags bit 2^1 = 斜体
                        italic = bool(flags & 2)

                        block_text_parts.append(text)
                        all_spans.append(FormattedSpan(
                            text=text,
                            font_name=font_name,
                            font_size_pt=font_size,
                            bold=bold,
                            italic=italic,
                        ))

                if not block_text_parts:
                    continue

                full_text = "".join(block_text_parts)

                # 估算对齐方式
                bbox = block.get("bbox", [0, 0, 0, 0])
                left_margin = bbox[0]
                right_margin = doc[page_num].rect.width - bbox[2]
                alignment = "left"
                if left_margin > 100:
                    alignment = "center"
                elif abs(left_margin - right_margin) < 10 and left_margin < 30:
                    alignment = "justify"

                # 估算首行缩进
                first_line_indent = None
                if lines:
                    first_span = lines[0].get("spans", [])
                    if first_span:
                        first_bbox = first_span[0].get("bbox", [0, 0, 0, 0])
                        first_indent = first_bbox[0] - bbox[0]
                        if first_indent > 5:  # 有缩进
                            first_line_indent = first_indent

                para = Paragraph(
                    index=para_index,
                    text=full_text.strip(),
                    spans=all_spans,
                    alignment=alignment,
                    first_line_indent_pt=first_line_indent,
                )
                doc_info.paragraphs.append(para)
                para_index += 1

            elif block_type == 1:  # 图片块
                # 图片暂不提取文本，仅记录存在
                pass

    doc.close()

    # 尝试使用 pdfplumber 提取表格
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        headers = [str(h or "") for h in table[0]]
                        doc_info.tables.append(TableInfo(
                            index=len(doc_info.tables),
                            rows=len(table),
                            cols=len(table[0]) if table[0] else 0,
                            headers=headers,
                            cells=[[str(c or "") for c in row] for row in table],
                        ))
    except ImportError:
        pass  # pdfplumber 可选
    except Exception:
        pass

    return doc_info
