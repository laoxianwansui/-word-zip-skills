# Architecture

The skill separates formatting from school-specific structure.

```text
Word/PDF input
  -> reader.py / parsers
  -> analyzer.py + cluster.py
  -> extractor.py       # ThesisSpec formatting rules
  -> profile_extractor.py # SchoolProfile structure
  -> standalone_project.py
  -> package_zip()
```

## Key modules

- `scripts/reader.py`: selects the parser backend.
- `scripts/parsers/`: parse Word and PDF files into `ParsedDocument`.
- `scripts/analyzer.py` and `scripts/cluster.py`: classify and cluster document formatting.
- `scripts/extractor.py`: converts clusters into `ThesisSpec` formatting values.
- `scripts/profile.py`: defines `SchoolProfile` and related dataclasses.
- `scripts/profile_extractor.py`: extracts school-specific structure.
- `scripts/profile_yaml.py`: serializes and loads editable profile overrides.
- `scripts/profile_report.py`: renders diagnostic profile reports.
- `scripts/class_generator.py`: renders `school-thesis.cls`.
- `scripts/standalone_project.py`: writes the Overleaf project tree.
- `scripts/build_standalone.py`: CLI entry point.

## Design principle

Output may look school-specific, but implementation should remain profile-driven and avoid hard-coded per-school branches.
