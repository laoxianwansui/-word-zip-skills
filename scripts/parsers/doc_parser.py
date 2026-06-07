"""解析旧版 .doc 文件。"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.docx_parser import FormattedSpan, Paragraph, ParsedDocument, parse_docx


def _resolve_path(file_path: str) -> str:
    return os.path.abspath(file_path)


def convert_doc_to_docx(doc_path: str) -> str:
    try:
        import win32com.client as win32
    except ImportError:
        raise ImportError("解析 .doc 文件需要 pywin32: pip install pywin32")

    doc_path_normalized = _resolve_path(doc_path)
    fd, temp_docx_path = tempfile.mkstemp(suffix='.docx', prefix='thesis_template_conv_')
    os.close(fd)

    word = None
    try:
        word = win32.Dispatch('Word.Application')
        word.Visible = False
        word.DisplayAlerts = 0

        doc = word.Documents.Open(doc_path_normalized)
        doc.SaveAs2(temp_docx_path, FileFormat=12)
        doc.Close()
        word.Quit()
        word = None

        time.sleep(1)

        if not os.path.exists(temp_docx_path) or os.path.getsize(temp_docx_path) == 0:
            raise RuntimeError(f"转换后的 .docx 文件为空或不存在: {temp_docx_path}")

        return temp_docx_path
    except Exception as e:
        raise RuntimeError(f".doc → .docx 转换失败: {e}")
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


def parse_doc_via_com(file_path: str) -> ParsedDocument:
    try:
        import win32com.client as win32
    except ImportError:
        raise ImportError("解析 .doc 文件需要 pywin32: pip install pywin32")

    file_path_normalized = _resolve_path(file_path)
    word = None
    try:
        word = win32.Dispatch('Word.Application')
        word.Visible = False
        word.DisplayAlerts = 0

        doc = word.Documents.Open(file_path_normalized)
        text = doc.Content.Text

        doc_info = ParsedDocument(
            file_path=file_path,
            file_type="doc",
            total_pages_estimate=max(1, len(text.split('\r')) // 40),
            parser_backend="doc-com-text-only",
            parser_warnings=["旧 .doc 降级为纯文本 COM 读取，格式信息不完整。"],
        )

        lines = text.split('\r')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                if '\x0c' in line and doc_info.paragraphs:
                    doc_info.paragraphs[-1].page_break_before = True
                continue

            cleaned = stripped.replace('\x07', '').replace('\x0c', '').replace('\n', '')
            if cleaned:
                doc_info.paragraphs.append(Paragraph(
                    index=i,
                    text=cleaned,
                    spans=[FormattedSpan(text=cleaned)],
                ))

        doc.Close()
        word.Quit()
        word = None
        return doc_info
    except Exception as e:
        raise RuntimeError(f"COM 读取 .doc 文件失败: {e}")
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


def parse_doc(file_path: str) -> ParsedDocument:
    temp_docx = None
    try:
        temp_docx = convert_doc_to_docx(file_path)
        result = parse_docx(temp_docx)
        result.file_type = "doc"
        result.file_path = file_path
        result.parser_backend = "doc-to-docx-python-docx"
        return result
    except Exception:
        print("[警告] .doc → .docx 转换失败，使用降级方案（纯文本提取，无格式信息）")
        return parse_doc_via_com(file_path)
    finally:
        if temp_docx and os.path.exists(temp_docx):
            try:
                os.unlink(temp_docx)
            except Exception:
                pass
