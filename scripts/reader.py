"""统一的文档读取入口。"""

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parsers.docx_parser import ParsedDocument, parse_docx

SUPPORTED_EXTENSIONS = {
    '.docx': 'docx',
    '.doc': 'doc',
    '.pdf': 'pdf',
}


def detect_file_type(file_path: str) -> Optional[str]:
    """检测文件类型"""
    ext = os.path.splitext(file_path)[1].lower()
    return SUPPORTED_EXTENSIONS.get(ext, None)


def _validate_backend(backend: str) -> None:
    valid_backends = {"auto", "pywin32", "docx"}
    if backend not in valid_backends:
        raise ValueError(f"不支持的解析后端: {backend}。支持: {', '.join(sorted(valid_backends))}")


def _parse_docx_with_backend(file_path: str, backend: str) -> ParsedDocument:
    if backend in {"auto", "pywin32"}:
        try:
            from parsers.word_com_parser import is_word_com_available, parse_word_via_com
            if is_word_com_available():
                return parse_word_via_com(file_path)
            if backend == "pywin32":
                raise RuntimeError("pywin32 或 Microsoft Word 不可用")
            parsed = parse_docx(file_path)
            parsed.parser_warnings.append("Word COM 不可用，已降级为 python-docx；精细格式识别准确率会降低。")
            return parsed
        except Exception as exc:
            if backend == "pywin32":
                raise
            parsed = parse_docx(file_path)
            parsed.parser_warnings.append(f"Word COM 解析失败，已降级为 python-docx: {exc}")
            return parsed
    return parse_docx(file_path)


def _parse_doc_with_backend(file_path: str, backend: str) -> ParsedDocument:
    if backend in {"auto", "pywin32"}:
        try:
            from parsers.word_com_parser import is_word_com_available, parse_word_via_com
            if is_word_com_available():
                return parse_word_via_com(file_path)
            if backend == "pywin32":
                raise RuntimeError("pywin32 或 Microsoft Word 不可用")
            from parsers.doc_parser import parse_doc
            parsed = parse_doc(file_path)
            parsed.parser_warnings.append("Word COM 不可用，.doc 使用旧转换流程；格式识别准确率会降低。")
            return parsed
        except Exception as exc:
            if backend == "pywin32":
                raise
            from parsers.doc_parser import parse_doc
            parsed = parse_doc(file_path)
            parsed.parser_warnings.append(f"Word COM 解析失败，.doc 已降级为旧转换流程: {exc}")
            return parsed
    from parsers.doc_parser import parse_doc
    return parse_doc(file_path)


def read_document(file_path: str, backend: str = "auto") -> ParsedDocument:
    """读取文档，自动选择解析器。

    Args:
        file_path: 文件路径（支持 .docx, .doc, .pdf）
        backend: "auto", "pywin32", or "docx" for Word files
    """
    _validate_backend(backend)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_type = detect_file_type(file_path)
    if file_type is None:
        ext = os.path.splitext(file_path)[1].lower()
        raise ValueError(
            f"不支持的文件格式: {ext}。支持的格式: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    print(f"[读取] 正在解析 {file_type.upper()} 文件: {file_path}")

    if file_type == 'docx':
        parsed = _parse_docx_with_backend(file_path, backend)
    elif file_type == 'doc':
        parsed = _parse_doc_with_backend(file_path, backend)
    elif file_type == 'pdf':
        from parsers.pdf_parser import parse_pdf
        parsed = parse_pdf(file_path)
        if not getattr(parsed, "parser_backend", None):
            parsed.parser_backend = "pdf-parser"
    else:
        raise ValueError(f"内部错误：未处理的文件类型 {file_type}")

    print(f"[读取] 完成。解析 {len(parsed.paragraphs)} 个段落, {len(parsed.tables)} 个表格。后端: {parsed.parser_backend}")
    for warning in parsed.parser_warnings:
        print(f"[读取警告] {warning}")
    return parsed
