"""Build Overleaf-ready projects from a reference LaTeX ZIP."""

import re
import shutil
import zipfile
from pathlib import Path

DEFAULT_REFERENCE_ZIP = Path(r"path/to/reference-template.zip")
COMPILED_SUFFIXES = {
    ".aux", ".log", ".out", ".toc", ".lof", ".lot", ".fls", ".fdb_latexmk",
    ".synctex", ".synctex.gz", ".pdf", ".bcf", ".blg", ".bbl", ".run.xml", ".nlo"
}
TEXT_SUFFIXES = {".tex", ".bib"}


def find_reference_zip(reference_zip: str | None = None) -> Path | None:
    if reference_zip:
        path = Path(reference_zip)
        return path if path.exists() else None
    return DEFAULT_REFERENCE_ZIP if DEFAULT_REFERENCE_ZIP.exists() else None


def extract_reference_zip(reference_zip: Path, output_dir: Path) -> Path:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(reference_zip, "r") as archive:
        archive.extractall(output_dir)
    return output_dir


def remove_build_directories(project_dir: Path) -> None:
    for dirname in ("Build", "build"):
        path = project_dir / dirname
        if path.exists() and path.is_dir():
            shutil.rmtree(path)


def _compiled_suffix(path: Path, project_dir: Path) -> bool:
    rel_parts = path.relative_to(project_dir).parts
    if rel_parts and rel_parts[0] in {"Pictures", "Chapters"}:
        return False
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in COMPILED_SUFFIXES)


def remove_compiled_artifacts(project_dir: Path) -> None:
    for path in project_dir.rglob("*"):
        if path.is_file() and _compiled_suffix(path, project_dir):
            path.unlink()


def _placeholderize_text(text: str) -> str:
    replacements = [
        (r"\\title\{[^{}]*\}", r"\\title{<<< 论文题目 >>>}"),
        (r"\\author\{[^{}]*\}", r"\\author{<<< 作者姓名 >>>}"),
        (r"\\date\{[^{}]*\}", r"\\date{<<< 日期 >>>}"),
    ]
    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result)

    result = re.sub(r"(?m)^(\\chapter\{)([^{}]+)(\})", r"\1<<< 章节标题 >>>\3", result)
    result = re.sub(r"(?m)^(\\section\{)([^{}]+)(\})", r"\1<<< 小节标题 >>>\3", result)
    result = re.sub(r"(?m)^(\\subsection\{)([^{}]+)(\})", r"\1<<< 子小节标题 >>>\3", result)
    return result


def placeholderize_project(project_dir: Path) -> list[str]:
    changed = []
    for path in project_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            text = path.read_text(encoding="gbk", errors="ignore")
            encoding = "gbk"
        updated = _placeholderize_text(text)
        if updated != text:
            path.write_text(updated, encoding=encoding)
            changed.append(str(path.relative_to(project_dir)))
    return changed


def write_generation_note(project_dir: Path, report_relative_path: str, changed_files: list[str]) -> None:
    note = project_dir / "THESIS_TEMPLATE_GENERATION.md"
    lines = [
        "# Thesis Template Generation Note",
        "",
        "This Overleaf project was generated from a reference LaTeX ZIP.",
        "",
        f"Recognition report: `{report_relative_path}`",
        "",
        "Placeholderized files:",
    ]
    lines.extend(f"- `{path}`" for path in changed_files)
    note.write_text("\n".join(lines), encoding="utf-8")


def copy_report(project_dir: Path, report_path: str | None) -> str | None:
    if not report_path:
        return None
    source = Path(report_path)
    if not source.exists():
        return None
    target = project_dir / "thesis-template-recognition-report.md"
    shutil.copy2(source, target)
    return target.name


def package_project(project_dir: Path, output_zip: Path) -> Path:
    if output_zip.exists():
        output_zip.unlink()
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in project_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(project_dir))
    return output_zip


def build_reference_project(reference_zip: str | None, output_dir: str, report_path: str | None = None) -> Path | None:
    reference = find_reference_zip(reference_zip)
    if reference is None:
        return None

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    project_dir = output_root / "reference_project"
    extract_reference_zip(reference, project_dir)
    remove_build_directories(project_dir)
    remove_compiled_artifacts(project_dir)
    changed_files = placeholderize_project(project_dir)
    report_relative = copy_report(project_dir, report_path) or ""
    write_generation_note(project_dir, report_relative, changed_files)
    return package_project(project_dir, output_root / "thesis_template_overleaf.zip")
