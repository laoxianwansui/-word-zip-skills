"""CLI: build an Overleaf ZIP from an input thesis-format document and optional reference ZIP."""

import argparse
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from analyzer import analyze_structure
from extractor import ThesisSpec
from generator import generate_template
from packager import package_zip
from reader import read_document
from reference_project import build_reference_project
from reporter import write_report


def parse_args():
    parser = argparse.ArgumentParser(description="Build thesis LaTeX template ZIP from Word/PDF format document.")
    parser.add_argument("input", help="Input .doc, .docx, or .pdf file")
    parser.add_argument("--backend", default="auto", choices=["auto", "pywin32", "docx"], help="Word parser backend")
    parser.add_argument("--reference", default=None, help="Optional reference LaTeX ZIP")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--chapters", type=int, default=3, help="Chapter count for fallback Jinja generator")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output or tempfile.mkdtemp(prefix="thesis_template_"))
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = read_document(args.input, backend=args.backend)
    structure, cluster_result = analyze_structure(parsed)
    report_path = write_report(parsed, cluster_result, str(output_dir / "thesis-template-report.md"))

    zip_path = build_reference_project(args.reference, str(output_dir), report_path)
    if zip_path is None:
        fallback_dir = output_dir / "jinja_project"
        generate_template(ThesisSpec(), str(fallback_dir), chapter_count=max(args.chapters, structure.chapter_count or 0))
        zip_path = Path(package_zip(str(fallback_dir)))

    print(f"[完成] ZIP: {zip_path}")
    print(f"[完成] 报告: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
