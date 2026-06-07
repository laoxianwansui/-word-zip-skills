"""Dependency-free profile YAML subset."""

from profile import CoverField, SchoolProfile

_SCALAR_FIELDS = ["school_name", "thesis_type", "degree_level", "document_title"]


def dumps_profile_yaml(profile: SchoolProfile) -> str:
    lines = [f"{field}: {getattr(profile, field)}" for field in _SCALAR_FIELDS]
    lines.append("cover_fields:")
    for cover_field in profile.cover_fields:
        lines.append(f"  - {cover_field.label}")
    return "\n".join(lines) + "\n"


def loads_profile_yaml(text: str, base: SchoolProfile | None = None) -> SchoolProfile:
    profile = base or SchoolProfile()
    cover_labels = []
    in_cover_fields = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "cover_fields:":
            in_cover_fields = True
            continue
        if in_cover_fields and stripped.startswith("- "):
            label = stripped[2:].strip()
            if label:
                cover_labels.append(label)
            continue
        in_cover_fields = False
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in _SCALAR_FIELDS and value:
            setattr(profile, key, value)
    if cover_labels:
        profile.cover_fields = [CoverField(label, f"<<< {label} >>>") for label in cover_labels]
    return profile
