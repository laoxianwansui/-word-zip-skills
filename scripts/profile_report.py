"""Render diagnostic reports for SchoolProfile."""

from profile import SchoolProfile


def _is_placeholder(value: str) -> bool:
    return not value or value.startswith("<<<")


def profile_quality_score(profile: SchoolProfile) -> int:
    score = 100
    if _is_placeholder(profile.school_name):
        score -= 25
    if _is_placeholder(profile.thesis_type):
        score -= 15
    if len(profile.cover_fields) < 4:
        score -= 20
    if not any(page.key == "cover" for page in profile.frontmatter_pages):
        score -= 10
    return max(0, min(100, score))


def render_profile_report(profile: SchoolProfile) -> str:
    missing = []
    for field in ["school_name", "thesis_type", "degree_level", "document_title"]:
        if _is_placeholder(getattr(profile, field)):
            missing.append(field)
    cover_lines = "\n".join(f"{index}. {field.label}" for index, field in enumerate(profile.cover_fields, start=1)) or "无"
    missing_lines = "\n".join(f"- {field}" for field in missing) or "无"
    return f"""# School Profile Report

## Summary

- School name: {profile.school_name}
- Thesis type: {profile.thesis_type}
- Degree level: {profile.degree_level}
- Cover fields: {len(profile.cover_fields)}
- Declaration pages: {len(profile.declaration_pages)}
- Frontmatter pages: {len(profile.frontmatter_pages)}
- Quality score: {profile_quality_score(profile)}/100

## Cover Fields

{cover_lines}

## Missing or Placeholder Values

{missing_lines}

## Notes

Edit `profile.yaml` and rerun with `--profile profile.yaml` to override recognition results.
"""
