"""CLI: build standalone Overleaf thesis template from Word/PDF requirements."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from analyzer import analyze_structure
from extractor import ThesisSpec, extract_specs_from_clusters
from format_rule_parser import parse_format_rule
from packager import package_zip
from profile_extractor import extract_school_profile
from profile_yaml import loads_profile_yaml
from reader import read_document
from standalone_project import generate_standalone_project


def create_parser():
    parser = argparse.ArgumentParser(description="Build standalone thesis Overleaf ZIP from Word/PDF formatting requirements.")
    parser.add_argument("input", help="Input .doc, .docx, or .pdf file")
    parser.add_argument("--backend", default="auto", choices=["auto", "pywin32", "docx"], help="Word parser backend")
    parser.add_argument("--output", default=None, help="Output ZIP path")
    parser.add_argument("--chapters", type=int, default=3, help="Number of chapter placeholders")
    parser.add_argument("--profile", default=None, help="Editable profile.yaml override file")
    parser.add_argument("--school-name", default=None, help="Override recognized school name")
    parser.add_argument("--thesis-type", default=None, help="Override recognized thesis type")
    return parser


def parse_args():
    return create_parser().parse_args()


def build_label_map(cluster_result) -> dict[int, str]:
    label_map = {}
    for cluster in cluster_result.clusters:
        for example in cluster.examples:
            rule = parse_format_rule(example)
            if rule and rule.semantic_label:
                label_map[cluster.cluster_id] = rule.semantic_label
                break
        if cluster.cluster_id in label_map:
            continue
        if cluster.suggested_label and cluster.suggested_label_confidence >= 0.80:
            label_map[cluster.cluster_id] = cluster.suggested_label

    body_candidates = [
        c for c in cluster_result.clusters
        if c.alignment in {"justify", "left"}
        and c.font_size_pt is not None
        and 10 <= c.font_size_pt <= 13
        and (c.first_line_indent_pt or 0) > 10
    ]
    if body_candidates:
        body = max(body_candidates, key=lambda c: (c.count, c.first_line_indent_pt or 0))
        label_map[body.cluster_id] = "正文段落"
    return label_map


def apply_profile_overrides(profile, args):
    if getattr(args, "profile", None):
        profile_path = Path(args.profile)
        profile = loads_profile_yaml(profile_path.read_text(encoding="utf-8"), profile)
    if getattr(args, "school_name", None):
        profile.school_name = args.school_name
    if getattr(args, "thesis_type", None):
        profile.thesis_type = args.thesis_type
    return profile


def main() -> int:
    args = parse_args()
    output_zip = Path(args.output or Path(tempfile.gettempdir()) / "thesis_template_overleaf.zip")
    work_dir = Path(tempfile.mkdtemp(prefix="thesis_standalone_"))
    project_dir = work_dir / "project"

    parsed = read_document(args.input, backend=args.backend)
    structure, cluster_result = analyze_structure(parsed)
    label_map = build_label_map(cluster_result)
    spec = extract_specs_from_clusters(cluster_result, label_map) if label_map else ThesisSpec()
    profile = extract_school_profile(parsed)
    profile = apply_profile_overrides(profile, args)

    generate_standalone_project(
        spec,
        str(project_dir),
        chapter_count=max(args.chapters, structure.chapter_count or 0),
        profile=profile,
    )
    package_zip(str(project_dir), str(output_zip))
    shutil.rmtree(work_dir)

    print(f"[完成] ZIP: {output_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
