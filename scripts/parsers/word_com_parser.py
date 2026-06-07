"""High-accuracy Word parser using Microsoft Word COM automation."""

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.docx_parser import FormattedSpan, Paragraph, ParsedDocument, TableInfo

_ALIGNMENT_MAP = {
    0: "left",
    1: "center",
    2: "right",
    3: "justify",
}


def is_word_com_available() -> bool:
    if os.name != "nt":
        return False
    try:
        import win32com.client  # noqa: F401
        return True
    except ImportError:
        return False


def _clean_text(text: str) -> str:
    return (text or "").replace("\r", "").replace("\x07", "").replace("\x0c", "").strip()


def _alignment_to_str(value) -> Optional[str]:
    try:
        return _ALIGNMENT_MAP.get(int(value))
    except Exception:
        return None


def _points(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _line_spacing(paragraph_format) -> Optional[float]:
    try:
        rule = int(paragraph_format.LineSpacingRule)
        value = float(paragraph_format.LineSpacing)
    except Exception:
        return None

    if rule in (0, 1, 2):
        return {0: 1.0, 1: 1.5, 2: 2.0}.get(rule)
    if value > 0:
        return value / 12.0
    return None


def _font_name(font) -> Optional[str]:
    for attr in ("NameFarEast", "Name"):
        try:
            value = getattr(font, attr)
            if value:
                return str(value)
        except Exception:
            continue
    return None


def _font_size(font) -> Optional[float]:
    try:
        size = float(font.Size)
        return size if 0 < size < 1000 else None
    except Exception:
        return None


def _font_bold(font) -> bool:
    try:
        return bool(font.Bold)
    except Exception:
        return False


def _font_italic(font) -> bool:
    try:
        return bool(font.Italic)
    except Exception:
        return False


def parse_word_via_com(file_path: str) -> ParsedDocument:
    try:
        import win32com.client as win32
    except ImportError as exc:
        raise ImportError("解析 Word 格式需要 pywin32: pip install pywin32") from exc

    absolute_path = os.path.abspath(file_path)
    ext = os.path.splitext(file_path)[1].lower().lstrip(".") or "docx"
    word = None
    document = None

    try:
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(absolute_path, ReadOnly=True, AddToRecentFiles=False)

        parsed = ParsedDocument(
            file_path=file_path,
            file_type=ext,
            parser_backend="pywin32-word-com",
            raw_metadata={"backend": "pywin32-word-com"},
        )

        for index, paragraph in enumerate(document.Paragraphs):
            text = _clean_text(paragraph.Range.Text)
            if not text:
                continue

            fmt = paragraph.Format
            font = paragraph.Range.Font
            style_name = None
            try:
                style_name = str(paragraph.Style.NameLocal)
            except Exception:
                try:
                    style_name = str(paragraph.Style.Name)
                except Exception:
                    style_name = None

            parsed.paragraphs.append(Paragraph(
                index=index,
                text=text,
                spans=[FormattedSpan(
                    text=text,
                    font_name=_font_name(font),
                    font_size_pt=_font_size(font),
                    bold=_font_bold(font),
                    italic=_font_italic(font),
                )],
                style_name=style_name,
                alignment=_alignment_to_str(fmt.Alignment),
                first_line_indent_pt=_points(fmt.FirstLineIndent),
                line_spacing=_line_spacing(fmt),
                space_before_pt=_points(fmt.SpaceBefore),
                space_after_pt=_points(fmt.SpaceAfter),
            ))

        for table_index, table in enumerate(document.Tables):
            cells = []
            for row_index in range(1, table.Rows.Count + 1):
                row_values = []
                for col_index in range(1, table.Columns.Count + 1):
                    try:
                        cell_text = _clean_text(table.Cell(row_index, col_index).Range.Text)
                    except Exception:
                        cell_text = ""
                    row_values.append(cell_text)
                cells.append(row_values)

            parsed.tables.append(TableInfo(
                index=table_index,
                rows=len(cells),
                cols=len(cells[0]) if cells else 0,
                headers=cells[0] if cells else [],
                cells=cells,
            ))

        parsed.total_pages_estimate = max(1, len(parsed.paragraphs) // 30)
        try:
            parsed.total_pages_estimate = int(document.ComputeStatistics(2))
        except Exception:
            pass

        return parsed
    except Exception as exc:
        raise RuntimeError(f"Word COM 解析失败: {exc}") from exc
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
