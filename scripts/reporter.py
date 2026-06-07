"""Markdown recognition report for thesis-template runs."""

from pathlib import Path


def _fmt(value, suffix="") -> str:
    if value is None:
        return "?"
    if isinstance(value, float):
        value = f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value}{suffix}"


def estimate_quality(parsed_doc, cluster_result) -> str:
    backend = getattr(parsed_doc, "parser_backend", "")
    warnings = getattr(parsed_doc, "parser_warnings", [])
    if backend == "pywin32-word-com" and not warnings:
        return "预计格式读取准确率较高（约 90%–95% 可用度），语义标签仍需检查低置信度簇。"
    if "python-docx" in backend:
        return "预计格式读取准确率中等（约 70%–85% 可用度），继承样式和复杂段落格式可能需要人工复核。"
    return "预计格式读取准确率取决于输入文档质量，请重点检查报告中的低置信度项。"


def _classification_summary(cluster_result) -> dict[str, int]:
    summary = {}
    for cluster in cluster_result.clusters:
        for key, value in getattr(cluster, "classification_counts", {}).items():
            summary[key] = summary.get(key, 0) + value
    return summary


def _suggested_label_map_lines(cluster_result) -> list[str]:
    lines = ["```python", "label_map = {"]
    for cluster in sorted(cluster_result.clusters, key=lambda c: c.cluster_id):
        label = getattr(cluster, "suggested_label", "")
        confidence = getattr(cluster, "suggested_label_confidence", 0.0)
        if label and confidence >= 0.6:
            lines.append(f"    {cluster.cluster_id}: \"{label}\",  # {confidence:.2f}")
    lines.extend(["}", "```"])
    return lines


def write_report(parsed_doc, cluster_result, output_path: str, label_map: dict[int, str] | None = None) -> str:
    label_map = label_map or {}
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Thesis Template Recognition Report",
        "",
        "## Input",
        "",
        f"- File: `{parsed_doc.file_path}`",
        f"- Type: `{parsed_doc.file_type}`",
        f"- Parser backend: `{getattr(parsed_doc, 'parser_backend', '?')}`",
        f"- Paragraphs: {len(parsed_doc.paragraphs)}",
        f"- Tables: {len(parsed_doc.tables)}",
        f"- Estimated pages: {parsed_doc.total_pages_estimate}",
        "",
    ]

    warnings = getattr(parsed_doc, "parser_warnings", [])
    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.extend([
        "## Quality Estimate",
        "",
        estimate_quality(parsed_doc, cluster_result),
        "",
    ])

    summary = _classification_summary(cluster_result)
    lines.extend(["## Classification Summary", ""])
    for key in sorted(summary):
        lines.append(f"- {key}: {summary[key]}")
    lines.append("")

    lines.extend(["## Suggested Label Map", ""])
    lines.extend(_suggested_label_map_lines(cluster_result))
    lines.append("")

    lines.extend([
        "## Format Clusters",
        "",
    ])

    for cluster in sorted(cluster_result.clusters, key=lambda c: c.count, reverse=True):
        label = label_map.get(cluster.cluster_id, "未标注")
        lines.extend([
            f"### Cluster {cluster.cluster_id}: {label}",
            "",
            f"- Count: {cluster.count}",
            f"- suggested_label: {getattr(cluster, 'suggested_label', '') or '?'} ({getattr(cluster, 'suggested_label_confidence', 0.0):.2f})",
            f"- Classification counts: {getattr(cluster, 'classification_counts', {})}",
            f"- Low-confidence paragraphs: {getattr(cluster, 'low_confidence_count', 0)}",
            f"- Signature: `{getattr(cluster, 'format_signature', '')}`",
            f"- Font: {_fmt(cluster.font_name)} {_fmt(cluster.font_size_pt, 'pt')}",
            f"- Bold ratio: {cluster.bold_ratio:.2f}",
            f"- Alignment: {cluster.alignment or '?'} ({cluster.alignment_ratio:.2f})",
            f"- First-line indent: {_fmt(cluster.first_line_indent_pt, 'pt')}",
            f"- Line spacing: {_fmt(cluster.line_spacing)}",
            f"- Space before/after: {_fmt(cluster.space_before_pt, 'pt')} / {_fmt(cluster.space_after_pt, 'pt')}",
            f"- Word style: {cluster.style_name or '?'}",
            "",
            "Examples:",
        ])
        for example in cluster.examples:
            lines.append(f"- {example}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
