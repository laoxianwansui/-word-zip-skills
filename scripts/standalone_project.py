"""Generate standalone Overleaf thesis projects with a generated class file."""

from pathlib import Path

from class_generator import render_class
from extractor import ThesisSpec
from profile import DeclarationPage, FrontmatterPage, SchoolProfile
from profile_report import render_profile_report
from profile_yaml import dumps_profile_yaml


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_standalone_project(spec: ThesisSpec, output_dir: str, chapter_count: int = 3, profile: SchoolProfile | None = None) -> str:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    profile = profile or SchoolProfile()

    (root / "frontmatter").mkdir(exist_ok=True)
    (root / "chapters").mkdir(exist_ok=True)
    (root / "figures").mkdir(exist_ok=True)
    _write(root / "figures" / ".keep", "")

    _write(root / "school-thesis.cls", render_class(spec))
    _write(root / "main.tex", _main_tex(chapter_count, profile))
    _write(root / "latexmkrc", "$pdflatex = 'xelatex';\n$pdf_mode = 1;\n$bibtex = 'biber';\n")
    _write(root / "README.md", _readme(profile))
    _write(root / "references.bib", _references_bib())
    _write(root / "profile.yaml", dumps_profile_yaml(profile))
    _write(root / "profile_report.md", render_profile_report(profile))

    _write(root / "frontmatter" / "cover.tex", _cover(profile))
    for page in sorted(profile.frontmatter_pages, key=lambda item: item.order):
        if page.key != "cover":
            _write(root / "frontmatter" / f"{page.key}.tex", _frontmatter_page(page))
    for declaration in sorted(profile.declaration_pages, key=lambda item: item.order):
        _write(root / "frontmatter" / f"{declaration.key}.tex", _declaration_page(declaration))

    _write(root / "chapters" / "abstract_cn.tex", _abstract_cn())
    _write(root / "chapters" / "abstract_en.tex", _abstract_en())
    for i in range(1, chapter_count + 1):
        _write(root / "chapters" / f"chapter{i}.tex", _chapter(i))
    _write(root / "chapters" / "conclusion.tex", _simple_chapter("结论", "请输入结论内容。"))
    _write(root / "chapters" / "acknowledgement.tex", "\\ThesisAcknowledgementTitle\n\n<<< 请输入谢辞内容 >>>\n")
    _write(root / "chapters" / "references.tex", "\\ThesisPrintBibliography\n")
    _write(root / "chapters" / "appendix.tex", "\\ThesisAppendixTitle\n\n<<< 请输入附录内容 >>>\n")
    return str(root)


def _main_tex(chapter_count: int, profile: SchoolProfile) -> str:
    frontmatter_inputs = ["\\input{frontmatter/cover}"]
    for page in sorted(profile.frontmatter_pages, key=lambda item: item.order):
        if page.key != "cover":
            frontmatter_inputs.append(f"\\input{{frontmatter/{page.key}}}")
    for declaration in sorted(profile.declaration_pages, key=lambda item: item.order):
        frontmatter_inputs.append(f"\\input{{frontmatter/{declaration.key}}}")

    frontmatter_block = "\n".join(frontmatter_inputs)
    chapter_inputs = "\n".join(f"\\input{{chapters/chapter{i}}}" for i in range(1, chapter_count + 1))
    return rf"""\documentclass{{school-thesis}}
\addbibresource{{references.bib}}

\ThesisSetSchoolName{{{profile.school_name}}}
\ThesisSetType{{{profile.thesis_type}}}
\ThesisSetTitle{{{profile.document_title}}}
\ThesisSetAuthor{{<<< 作者姓名 >>>}}
\ThesisSetStudentId{{<<< 学号 >>>}}
\ThesisSetCollege{{<<< 学院 >>>}}
\ThesisSetMajor{{<<< 专业 >>>}}
\ThesisSetSupervisor{{<<< 指导教师 >>>}}
\ThesisSetDate{{<<< 日期 >>>}}

\begin{{document}}

\ThesisFrontMatter
{frontmatter_block}
\input{{chapters/abstract_cn}}
\input{{chapters/abstract_en}}
\ThesisContents

\ThesisMainMatter
{chapter_inputs}
\input{{chapters/conclusion}}
\input{{chapters/acknowledgement}}
\input{{chapters/references}}
\input{{chapters/appendix}}

\end{{document}}
"""


def _cover(profile: SchoolProfile) -> str:
    fields = "\n".join(f"\\ThesisCoverField{{{field.label}}}{{{field.placeholder}}}" for field in profile.cover_fields)
    return f"\\MakeThesisProfileCover{{%\n{fields}\n}}\n"


def _frontmatter_page(page: FrontmatterPage) -> str:
    toc = "true" if page.include_in_toc else "false"
    return f"\\ThesisFrontmatterPage{{{page.title}}}{{{toc}}}{{%\n{page.body_placeholder}\n}}\n"


def _declaration_page(declaration: DeclarationPage) -> str:
    signatures = "\\par\n".join(f"\\noindent {field}：\\hfill" for field in declaration.signature_fields)
    if signatures:
        signatures = f"\n\\vspace{{4em}}\n{signatures}\n"
    toc = "true" if declaration.include_in_toc else "false"
    return f"\\ThesisDeclarationPage{{{declaration.title}}}{{{toc}}}{{%\n{declaration.body_text_or_placeholder}\n}}{{%\n{signatures}}}\n"


def _abstract_cn() -> str:
    return r"""\begin{ChineseAbstract}
<<< 请输入中文摘要内容 >>>

\ChineseKeywords{<<< 关键词1；关键词2；关键词3 >>>}
\end{ChineseAbstract}
"""


def _abstract_en() -> str:
    return r"""\begin{EnglishAbstract}
<<< Please input English abstract. >>>

\EnglishKeywords{<<< keyword 1; keyword 2; keyword 3 >>>}
\end{EnglishAbstract}
"""


def _chapter(index: int) -> str:
    return rf"""\chapter{{第{index}章标题}}

<<< 请输入第{index}章正文内容 >>>

\section{{小节标题}}

<<< 请输入小节内容 >>>
"""


def _simple_chapter(title: str, body: str) -> str:
    return f"\\chapter{{{title}}}\n\n<<< {body} >>>\n"


def _references_bib() -> str:
    return """@book{example,
  author = {作者},
  title = {示例参考文献},
  publisher = {出版社},
  year = {2026}
}
"""


def _readme(profile: SchoolProfile) -> str:
    title = profile.output_identity.readme_title
    if title == "Generated Thesis Template" and not profile.school_name.startswith("<<<"):
        title = f"{profile.school_name} Thesis Template"
    return f"""# {title}

Upload this ZIP to Overleaf and select XeLaTeX. Replace all `<<< >>>` placeholders with your thesis content.

This project was generated from a profile-driven school template workflow. Edit files in `frontmatter/` for school-specific pages and `chapters/` for thesis content.
"""
