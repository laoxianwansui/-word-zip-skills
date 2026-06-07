# Thesis Template Skill

Experimental Claude Code skill for generating Overleaf-ready LaTeX thesis templates from Word/PDF university formatting requirements.

## What it does

This skill reads a Word or PDF thesis requirement/sample document and generates a standalone Overleaf project ZIP.

Pipeline:

```text
Word/PDF input
  -> ParsedDocument
  -> ThesisSpec      # formatting rules
  -> SchoolProfile   # school-specific structure
  -> school-thesis.cls + frontmatter + chapters
  -> profile.yaml + profile_report.md
  -> Overleaf ZIP
```

## Features

- Word `.doc` / `.docx` parsing, with Microsoft Word COM support on Windows when available
- PDF text extraction support
- Format clustering and thesis section classification
- Generated `school-thesis.cls`
- School profile extraction for cover fields and frontmatter
- Editable `profile.yaml` for manual correction
- `profile_report.md` diagnostics with a quality score
- CLI overrides for school name and thesis type
- Overleaf-compatible ZIP packaging

## Installation

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

On Windows, installing `pywin32` and having Microsoft Word available gives the best Word-format accuracy.

## Usage

Generate a standalone Overleaf ZIP:

```bash
python scripts/build_standalone.py "path/to/input.docx" --backend auto --output "path/to/thesis_template_overleaf.zip"
```

Override school identity when the source document does not expose it clearly:

```bash
python scripts/build_standalone.py "path/to/input.docx" \
  --backend auto \
  --school-name "Example University" \
  --thesis-type "Undergraduate Thesis" \
  --output "path/to/thesis_template_overleaf.zip"
```

Use an edited profile:

```bash
python scripts/build_standalone.py "path/to/input.docx" \
  --backend auto \
  --profile "path/to/profile.yaml" \
  --output "path/to/thesis_template_overleaf.zip"
```

Upload the generated ZIP to Overleaf and select XeLaTeX.

## Generated project files

```text
main.tex
school-thesis.cls
latexmkrc
README.md
references.bib
profile.yaml
profile_report.md
frontmatter/cover.tex
chapters/
figures/.keep
```

## Status

This is an experimental alpha project. It is useful for generating a strong first draft of a thesis template, but it does not guarantee pixel-perfect reproduction of every school's official template.

Recommended workflow:

1. Generate the ZIP.
2. Read `profile_report.md`.
3. Edit `profile.yaml` if recognition missed anything.
4. Regenerate with `--profile`.
5. Compile in Overleaf with XeLaTeX.

## Privacy

Do not publish real thesis samples, school-internal documents, generated private ZIPs, or documents containing personal information.
