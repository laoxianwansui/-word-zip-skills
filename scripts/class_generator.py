"""Generate a standalone LaTeX class from ThesisSpec."""

from extractor import TextFormat, ThesisSpec

_FONT_COMMANDS = {
    "\\songti": "\\songti",
    "\\heiti": "\\heiti",
    "\\kaishu": "\\kaishu",
    "\\fangsong": "\\fangsong",
    "\\rmfamily": "\\rmfamily",
}


def _font(fmt: TextFormat, english: bool = False) -> str:
    name = fmt.font_en if english else fmt.font_cn
    return _FONT_COMMANDS.get(name, "\\songti")


def _bold(fmt: TextFormat) -> str:
    return "\\bfseries" if fmt.bold else ""


def _size(fmt: TextFormat, fallback_line_multiplier: float = 1.5) -> tuple[str, str]:
    size = fmt.font_size_pt or 12.0
    line = max(size * fallback_line_multiplier, size + 2)
    return f"{size:g}pt", f"{line:g}pt"


def _align_prefix(alignment: str) -> str:
    return {
        "center": "\\centering",
        "right": "\\raggedleft",
        "left": "\\raggedright",
        "justify": "",
    }.get(alignment or "", "")


def render_class(spec: ThesisSpec) -> str:
    values = _class_values(spec)
    sections = [
        _render_preamble(),
        _render_parameter_macros(spec, values),
        _render_font_setup(),
        _render_page_layout(spec, values),
        _render_header_footer(values),
        _render_cover(values),
        _render_abstracts(spec, values),
        _render_contents_and_lists(spec, values),
        _render_titles(spec, values),
        _render_captions(),
        _render_bibliography(values),
        _render_appendix_acknowledgement(spec, values),
        _render_theorem_algorithm(),
        _render_declaration_placeholders(),
        _render_utilities(),
    ]
    return "\n\n".join(section.strip() for section in sections) + "\n"


def _class_values(spec: ThesisSpec) -> dict[str, str]:
    body_size, body_line = _size(spec.body_text)
    chapter_size, chapter_line = _size(spec.heading1)
    section_size, section_line = _size(spec.heading2)
    subsection_size, subsection_line = _size(spec.heading3)
    cn_abs_size, cn_abs_line = _size(spec.abstract_cn_title, 1.25)
    en_abs_size, en_abs_line = _size(spec.abstract_en_title, 1.25)
    toc_size, toc_line = _size(spec.toc_title, 1.25)
    ref_size, ref_line = _size(spec.references_body)
    ack_size, ack_line = _size(spec.acknowledgement_title)
    app_size, app_line = _size(spec.appendix_title)
    header_size, header_line = _size(spec.header_font, 1.2)
    cover_size, cover_line = _size(spec.cover_title, 1.6)
    return {
        "body_size": body_size,
        "body_line": body_line,
        "body_font": _font(spec.body_text),
        "body_indent": spec.body_text.first_line_indent,
        "chapter_size": chapter_size,
        "chapter_line": chapter_line,
        "section_size": section_size,
        "section_line": section_line,
        "subsection_size": subsection_size,
        "subsection_line": subsection_line,
        "cn_abs_size": cn_abs_size,
        "cn_abs_line": cn_abs_line,
        "en_abs_size": en_abs_size,
        "en_abs_line": en_abs_line,
        "toc_size": toc_size,
        "toc_line": toc_line,
        "ref_size": ref_size,
        "ref_line": ref_line,
        "ack_size": ack_size,
        "ack_line": ack_line,
        "app_size": app_size,
        "app_line": app_line,
        "header_size": header_size,
        "header_line": header_line,
        "cover_size": cover_size,
        "cover_line": cover_line,
        "cover_font": _font(spec.cover_title),
        "cover_bold": _bold(spec.cover_title),
        "cover_align": _align_prefix(spec.cover_title.alignment),
        "abstract_title_font": _font(spec.abstract_cn_title),
        "keyword_font": _font(spec.abstract_cn_keyword_label),
    }


def _render_preamble() -> str:
    return r"""
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{school-thesis}[2026/06/06 Generated universal thesis class]
\LoadClass[UTF8,a4paper,openany]{ctexrep}

\RequirePackage{geometry}
\RequirePackage{fontspec}
\RequirePackage{titlesec}
\RequirePackage{fancyhdr}
\RequirePackage{setspace}
\RequirePackage{tocloft}
\RequirePackage{caption}
\RequirePackage{subcaption}
\RequirePackage{graphicx}
\RequirePackage{float}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{amsthm}
\RequirePackage{booktabs}
\RequirePackage{longtable}
\RequirePackage{tabularx}
\RequirePackage{array}
\RequirePackage{enumitem}
\RequirePackage{appendix}
\RequirePackage{indentfirst}
\RequirePackage{lastpage}
\RequirePackage{nomencl}
\RequirePackage{algorithm}
\RequirePackage{algpseudocode}
\RequirePackage{hyperref}
\RequirePackage{cleveref}
\RequirePackage{etoolbox}
\RequirePackage[
  backend=biber,
  bibstyle=gb7714-2015,
  citestyle=gb7714-2015,
  doi=false,
  url=false,
  gbstrict=true,
  gbalign=center
]{biblatex}

\hypersetup{
  colorlinks=true,
  linkcolor=black,
  citecolor=black,
  urlcolor=black,
  bookmarksopen=true,
  bookmarksnumbered=true,
  pdfstartview=FitH
}
\makeindex
\makenomenclature
"""


def _render_parameter_macros(spec: ThesisSpec, values: dict[str, str]) -> str:
    return rf"""
% === Parameter Macros ===
\newcommand{{\ThesisBodySize}}{{{values["body_size"]}}}
\newcommand{{\ThesisBodyLine}}{{{values["body_line"]}}}
\newcommand{{\ThesisBodyFont}}{{{values["body_font"]}}}
\newcommand{{\ThesisBodyIndent}}{{{values["body_indent"]}}}
\newcommand{{\ThesisAbstractTitleSize}}{{{values["cn_abs_size"]}}}
\newcommand{{\ThesisAbstractTitleLine}}{{{values["cn_abs_line"]}}}
\newcommand{{\ThesisAbstractTitleFont}}{{{values["abstract_title_font"]}}}
\newcommand{{\ThesisKeywordFont}}{{{values["keyword_font"]}}}
\newcommand{{\ThesisChapterSize}}{{{values["chapter_size"]}}}
\newcommand{{\ThesisChapterLine}}{{{values["chapter_line"]}}}
\newcommand{{\ThesisSectionSize}}{{{values["section_size"]}}}
\newcommand{{\ThesisSectionLine}}{{{values["section_line"]}}}
\newcommand{{\ThesisSubsectionSize}}{{{values["subsection_size"]}}}
\newcommand{{\ThesisSubsectionLine}}{{{values["subsection_line"]}}}
\newcommand{{\ThesisReferenceSize}}{{{values["ref_size"]}}}
\newcommand{{\ThesisReferenceLine}}{{{values["ref_line"]}}}
\newcommand{{\ThesisHeaderSize}}{{{values["header_size"]}}}
\newcommand{{\ThesisHeaderLine}}{{{values["header_line"]}}}
\newcommand{{\ThesisCoverSize}}{{{values["cover_size"]}}}
\newcommand{{\ThesisCoverLine}}{{{values["cover_line"]}}}
\newcommand{{\ThesisLeftMargin}}{{{spec.page_setup.left_margin}cm}}
\newcommand{{\ThesisRightMargin}}{{{spec.page_setup.right_margin}cm}}
\newcommand{{\ThesisTopMargin}}{{{spec.page_setup.top_margin}cm}}
\newcommand{{\ThesisBottomMargin}}{{{spec.page_setup.bottom_margin}cm}}
\newcommand{{\ThesisLineSpread}}{{{spec.page_setup.line_spread}}}
\newcommand{{\ThesisFigureName}}{{图}}
\newcommand{{\ThesisTableName}}{{表}}
\newcommand{{\ThesisAlgorithmName}}{{算法}}
\newcommand{{\ThesisDefaultSchoolName}}{{<<< 学校名称 >>>}}
\newcommand{{\ThesisDefaultType}}{{<<< 论文类型 >>>}}
\newcommand{{\ThesisDefaultTitle}}{{<<< 论文题目 >>>}}
\newcommand{{\ThesisDefaultAuthor}}{{<<< 作者姓名 >>>}}
\newcommand{{\ThesisDefaultStudentId}}{{<<< 学号 >>>}}
\newcommand{{\ThesisDefaultCollege}}{{<<< 学院 >>>}}
\newcommand{{\ThesisDefaultMajor}}{{<<< 专业 >>>}}
\newcommand{{\ThesisDefaultSupervisor}}{{<<< 指导教师 >>>}}
\newcommand{{\ThesisDefaultDate}}{{<<< 日期 >>>}}
"""


def _render_font_setup() -> str:
    return r"""
% === Font Setup ===
\newcommand{\ThesisSongti}{\songti}
\newcommand{\ThesisHeiti}{\heiti}
\newcommand{\ThesisKaiti}{\kaishu}
\newcommand{\ThesisFangsong}{\fangsong}
\newcommand{\ThesisTimes}{\rmfamily}
\newcommand{\ThesisBodyStyle}{\ThesisBodyFont\fontsize{\ThesisBodySize}{\ThesisBodyLine}\selectfont}
\newcommand{\ThesisEnglishStyle}{\ThesisTimes\fontsize{\ThesisBodySize}{\ThesisBodyLine}\selectfont}
\newcommand{\ThesisSmallStyle}{\fontsize{10.5pt}{15.75pt}\selectfont}
\newcommand{\ThesisFootnoteStyle}{\fontsize{9pt}{12pt}\selectfont}
\newcommand{\ThesisHeaderStyle}{\fontsize{\ThesisHeaderSize}{\ThesisHeaderLine}\selectfont}
\AtBeginDocument{
  \ThesisBodyStyle
}
"""


def _render_page_layout(spec: ThesisSpec, values: dict[str, str]) -> str:
    return rf"""
% === Page Layout ===
\geometry{{
  left=\ThesisLeftMargin,
  right=\ThesisRightMargin,
  top=\ThesisTopMargin,
  bottom=\ThesisBottomMargin,
  headheight=15pt,
  headsep=0.8cm,
  footskip=1.0cm
}}
\setlength{{\parindent}}{{\ThesisBodyIndent}}
\setlength{{\parskip}}{{0pt}}
\linespread{{\ThesisLineSpread}}
\setlength{{\topskip}}{{0pt}}
\setlength{{\footskip}}{{1.0cm}}
\setlength{{\headheight}}{{15pt}}
\setlist{{nosep}}
\setlist[enumerate]{{label=\arabic*.}}
\setlist[itemize]{{leftmargin=2\ccwd}}
\setlength{{\intextsep}}{{10pt}}
\setlength{{\textfloatsep}}{{12pt}}
\setlength{{\floatsep}}{{10pt}}
\raggedbottom
"""


def _render_header_footer(values: dict[str, str]) -> str:
    return rf"""
% === Header and Footer ===
\pagestyle{{fancy}}
\fancyhf{{}}
\fancyhead[C]{{{{\ThesisHeaderStyle 毕业设计（论文）}}}}
\fancyfoot[C]{{{{\fontsize{{9pt}}{{10.8pt}}\selectfont\thepage}}}}
\renewcommand{{\headrulewidth}}{{0.4pt}}
\renewcommand{{\footrulewidth}}{{0pt}}
\fancypagestyle{{plain}}{{
  \fancyhf{{}}
  \fancyfoot[C]{{{{\fontsize{{9pt}}{{10.8pt}}\selectfont\thepage}}}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \renewcommand{{\footrulewidth}}{{0pt}}
}}
\newcommand{{\ThesisHeaderText}}[1]{{\fancyhead[C]{{{{\ThesisHeaderStyle #1}}}}}}
\newcommand{{\ThesisRomanPageNumbers}}{{\pagenumbering{{Roman}}}}
\newcommand{{\ThesisArabicPageNumbers}}{{\pagenumbering{{arabic}}}}
"""


def _render_cover(values: dict[str, str]) -> str:
    return rf"""
% === Cover ===
\newcommand{{\ThesisSchoolName}}{{\ThesisDefaultSchoolName}}
\newcommand{{\ThesisType}}{{\ThesisDefaultType}}
\newcommand{{\ThesisTitle}}{{\ThesisDefaultTitle}}
\newcommand{{\ThesisAuthor}}{{\ThesisDefaultAuthor}}
\newcommand{{\ThesisStudentId}}{{\ThesisDefaultStudentId}}
\newcommand{{\ThesisCollege}}{{\ThesisDefaultCollege}}
\newcommand{{\ThesisMajor}}{{\ThesisDefaultMajor}}
\newcommand{{\ThesisSupervisor}}{{\ThesisDefaultSupervisor}}
\newcommand{{\ThesisDate}}{{\ThesisDefaultDate}}
\newcommand{{\ThesisSetSchoolName}}[1]{{\renewcommand{{\ThesisSchoolName}}{{#1}}}}
\newcommand{{\ThesisSetType}}[1]{{\renewcommand{{\ThesisType}}{{#1}}}}
\newcommand{{\ThesisSetTitle}}[1]{{\renewcommand{{\ThesisTitle}}{{#1}}}}
\newcommand{{\ThesisSetAuthor}}[1]{{\renewcommand{{\ThesisAuthor}}{{#1}}}}
\newcommand{{\ThesisSetStudentId}}[1]{{\renewcommand{{\ThesisStudentId}}{{#1}}}}
\newcommand{{\ThesisSetCollege}}[1]{{\renewcommand{{\ThesisCollege}}{{#1}}}}
\newcommand{{\ThesisSetMajor}}[1]{{\renewcommand{{\ThesisMajor}}{{#1}}}}
\newcommand{{\ThesisSetSupervisor}}[1]{{\renewcommand{{\ThesisSupervisor}}{{#1}}}}
\newcommand{{\ThesisSetDate}}[1]{{\renewcommand{{\ThesisDate}}{{#1}}}}
\newcommand{{\ThesisCoverTitle}}[1]{{{{{values["cover_align"]} {values["cover_font"]} {values["cover_bold"]}\fontsize{{\ThesisCoverSize}}{{\ThesisCoverLine}}\selectfont #1\par}}}}
\newcommand{{\ThesisCoverField}}[2]{{{{\songti\zihao{{-3}} #1：}} & {{\songti\zihao{{-3}} #2}}\\[0.8em]}}
\newcommand{{\MakeThesisCover}}{{%
  \begin{{titlepage}}
  \centering
  \vspace*{{2.0cm}}
  \ThesisCoverTitle{{\ThesisTitle}}
  \vspace{{3.0cm}}
  \begin{{tabular}}{{rl}}
  \ThesisCoverField{{学号}}{{\ThesisStudentId}}
  \ThesisCoverField{{姓名}}{{\ThesisAuthor}}
  \ThesisCoverField{{学院}}{{\ThesisCollege}}
  \ThesisCoverField{{专业}}{{\ThesisMajor}}
  \ThesisCoverField{{指导教师}}{{\ThesisSupervisor}}
  \end{{tabular}}
  \vfill
  {{\songti\zihao{{-3}} \ThesisDate\par}}
  \end{{titlepage}}
  \clearpage
}}
\newcommand{{\MakeThesisProfileCover}}[1]{{%
  \begin{{titlepage}}
  \centering
  \vspace*{{1.5cm}}
  {{\heiti\zihao{{2}} \ThesisSchoolName\par}}
  \vspace{{1.0cm}}
  {{\heiti\zihao{{3}} \ThesisType\par}}
  \vspace{{1.5cm}}
  \ThesisCoverTitle{{\ThesisTitle}}
  \vspace{{2.0cm}}
  \begin{{tabular}}{{rl}}
  #1
  \end{{tabular}}
  \vfill
  {{\songti\zihao{{-3}} \ThesisDate\par}}
  \end{{titlepage}}
  \clearpage
}}
\newcommand{{\ThesisFrontmatterPage}}[3]{{%
  \cleardoublepage
  \phantomsection
  \begin{{center}}
    {{\heiti\zihao{{3}} #1}}
  \end{{center}}
  \ifdefstring{{#2}}{{true}}{{\addcontentsline{{toc}}{{chapter}}{{#1}}}}{{}}
  #3
  \clearpage
}}
\newcommand{{\ThesisDeclarationPage}}[4]{{%
  \cleardoublepage
  \phantomsection
  \begin{{center}}
    {{\heiti\zihao{{3}} #1}}
  \end{{center}}
  \ifdefstring{{#2}}{{true}}{{\addcontentsline{{toc}}{{chapter}}{{#1}}}}{{}}
  #3
  #4
  \clearpage
}}
"""


def _render_abstracts(spec: ThesisSpec, values: dict[str, str]) -> str:
    return rf"""
% === Abstracts and Keywords ===
\newenvironment{{ChineseAbstract}}{{%
  \cleardoublepage
  \phantomsection
  \begin{{center}}
    {{{_font(spec.abstract_cn_title)} {_bold(spec.abstract_cn_title)}\fontsize{{{values["cn_abs_size"]}}}{{{values["cn_abs_line"]}}}\selectfont 摘\quad 要}}
  \end{{center}}
  \addcontentsline{{toc}}{{chapter}}{{摘要}}
  {{{_font(spec.abstract_cn_body)}\fontsize{{{values["body_size"]}}}{{{values["body_line"]}}}\selectfont}}
}}{{\clearpage}}
\newcommand{{\ChineseKeywords}}[1]{{%
  \par\vspace{{1em}}\noindent
  {{{_font(spec.abstract_cn_keyword_label)} {_bold(spec.abstract_cn_keyword_label)}\fontsize{{{values["body_size"]}}}{{{values["body_line"]}}}\selectfont 关键词：}}
  {{{_font(spec.abstract_cn_keyword_body)}\fontsize{{{values["body_size"]}}}{{{values["body_line"]}}}\selectfont #1}}\par
}}
\newenvironment{{EnglishAbstract}}{{%
  \cleardoublepage
  \phantomsection
  \begin{{center}}
    {{{_font(spec.abstract_en_title, english=True)} {_bold(spec.abstract_en_title)}\fontsize{{{values["en_abs_size"]}}}{{{values["en_abs_line"]}}}\selectfont Abstract}}
  \end{{center}}
  \addcontentsline{{toc}}{{chapter}}{{Abstract}}
  {{{_font(spec.abstract_en_body, english=True)}\fontsize{{{values["body_size"]}}}{{{values["body_line"]}}}\selectfont}}
}}{{\clearpage}}
\newcommand{{\EnglishKeywords}}[1]{{%
  \par\vspace{{1em}}\noindent
  {{{_font(spec.abstract_en_keyword_label, english=True)} {_bold(spec.abstract_en_keyword_label)}\fontsize{{{values["body_size"]}}}{{{values["body_line"]}}}\selectfont Key words: }}
  {{{_font(spec.abstract_en_keyword_body, english=True)}\fontsize{{{values["body_size"]}}}{{{values["body_line"]}}}\selectfont #1}}\par
}}
"""


def _render_contents_and_lists(spec: ThesisSpec, values: dict[str, str]) -> str:
    return rf"""
% === Contents and Lists ===
\setcounter{{tocdepth}}{{2}}
\setcounter{{secnumdepth}}{{3}}
\renewcommand{{\contentsname}}{{{{{_font(spec.toc_title)} {_bold(spec.toc_title)}\fontsize{{{values["toc_size"]}}}{{{values["toc_line"]}}}\selectfont 目\quad 录}}}}
\renewcommand{{\listfigurename}}{{图目录}}
\renewcommand{{\listtablename}}{{表目录}}
\renewcommand{{\cftchapfont}}{{{_font(spec.heading1)}\fontsize{{{values["chapter_size"]}}}{{{values["chapter_line"]}}}\selectfont}}
\renewcommand{{\cftchappagefont}}{{\normalfont}}
\renewcommand{{\cftsecfont}}{{{_font(spec.heading2)}\fontsize{{{values["section_size"]}}}{{{values["section_line"]}}}\selectfont}}
\renewcommand{{\cftsecpagefont}}{{\normalfont}}
\renewcommand{{\cftchapleader}}{{\cftdotfill{{\cftdotsep}}}}
\setlength{{\cftbeforechapskip}}{{0.2em}}
\setlength{{\cftbeforesecskip}}{{0.1em}}
\setlength{{\cftchapindent}}{{0pt}}
\setlength{{\cftsecindent}}{{2em}}
\setlength{{\cftsubsecindent}}{{4em}}
\newcommand{{\ThesisContents}}{{%
  \cleardoublepage
  \phantomsection
  \tableofcontents
  \clearpage
}}
\newcommand{{\ThesisFigureList}}{{%
  \cleardoublepage
  \phantomsection
  \listoffigures
  \addcontentsline{{toc}}{{chapter}}{{图目录}}
  \clearpage
}}
\newcommand{{\ThesisTableList}}{{%
  \cleardoublepage
  \phantomsection
  \listoftables
  \addcontentsline{{toc}}{{chapter}}{{表目录}}
  \clearpage
}}
"""


def _render_titles(spec: ThesisSpec, values: dict[str, str]) -> str:
    return rf"""
% === Chapter and Section Titles ===
\titleformat{{\chapter}}[block]
  {{{_align_prefix(spec.heading1.alignment)} {_font(spec.heading1)} {_bold(spec.heading1)}\fontsize{{{values["chapter_size"]}}}{{{values["chapter_line"]}}}\selectfont}}
  {{\thechapter}}{{1em}}{{}}
\titlespacing*{{\chapter}}{{0pt}}{{0pt}}{{1em}}
\titleformat{{\section}}[block]
  {{{_align_prefix(spec.heading2.alignment)} {_font(spec.heading2)} {_bold(spec.heading2)}\fontsize{{{values["section_size"]}}}{{{values["section_line"]}}}\selectfont}}
  {{\thesection}}{{1em}}{{}}
\titlespacing*{{\section}}{{0pt}}{{0.8em}}{{0.5em}}
\titleformat{{\subsection}}[block]
  {{{_align_prefix(spec.heading3.alignment)} {_font(spec.heading3)} {_bold(spec.heading3)}\fontsize{{{values["subsection_size"]}}}{{{values["subsection_line"]}}}\selectfont}}
  {{\thesubsection}}{{1em}}{{}}
\titlespacing*{{\subsection}}{{0pt}}{{0.5em}}{{0.3em}}
\titleformat{{\subsubsection}}[runin]
  {{\heiti\fontsize{{\ThesisBodySize}}{{\ThesisBodyLine}}\selectfont}}
  {{\thesubsubsection}}{{1em}}{{}}
\titlespacing*{{\subsubsection}}{{0pt}}{{0.5em}}{{1em}}
\newcommand{{\ThesisUnnumberedTitle}}[2]{{%
  \cleardoublepage
  \phantomsection
  \begin{{center}}
    {{#1 #2}}
  \end{{center}}
}}
"""


def _render_captions() -> str:
    return r"""
% === Captions ===
\renewcommand{\figurename}{\ThesisFigureName}
\renewcommand{\tablename}{\ThesisTableName}
\captionsetup{
  font=small,
  labelfont=bf,
  labelsep=quad,
  justification=centering,
  singlelinecheck=false
}
\captionsetup[figure]{position=bottom,skip=6pt}
\captionsetup[table]{position=top,skip=6pt}
\captionsetup[subfigure]{font=small,labelformat=parens,labelsep=space}
\floatplacement{figure}{htbp}
\floatplacement{table}{htbp}
\numberwithin{figure}{chapter}
\numberwithin{table}{chapter}
\numberwithin{equation}{chapter}
\renewcommand{\thefigure}{\arabic{chapter}.\arabic{figure}}
\renewcommand{\thetable}{\arabic{chapter}.\arabic{table}}
\renewcommand{\theequation}{\arabic{chapter}-\arabic{equation}}
\AtBeginEnvironment{figure}{\def\@floatboxreset{\centering}}
\AtBeginEnvironment{table}{\def\@floatboxreset{\centering}}
\newcommand{\ThesisFigureCaption}[1]{\caption{#1}}
\newcommand{\ThesisTableCaption}[1]{\caption{#1}}
\newcolumntype{Y}{>{\centering\arraybackslash}X}
"""


def _render_bibliography(values: dict[str, str]) -> str:
    return rf"""
% === Bibliography ===
\renewcommand{{\bibfont}}{{\fontsize{{{values["ref_size"]}}}{{{values["ref_line"]}}}\selectfont}}
\defbibheading{{thesisbib}}[参考文献]{{%
  \cleardoublepage
  \phantomsection
  \chapter*{{#1}}
  \addcontentsline{{toc}}{{chapter}}{{#1}}
}}
\newcommand{{\ThesisPrintBibliography}}{{%
  \printbibliography[heading=thesisbib,title=参考文献]
}}
\newcommand{{\normcite}}{{\parencite}}
\DeclareFieldFormat{{url}}{{\newline\url{{#1}}}}
\setlength{{\bibitemsep}}{{0.3em}}
\setlength{{\bibhang}}{{2em}}
"""


def _render_appendix_acknowledgement(spec: ThesisSpec, values: dict[str, str]) -> str:
    return rf"""
% === Appendix and Acknowledgement ===
\newcommand{{\ThesisAcknowledgementTitle}}{{%
  \cleardoublepage
  \phantomsection
  \begin{{center}}
    {{{_font(spec.acknowledgement_title)} {_bold(spec.acknowledgement_title)}\fontsize{{{values["ack_size"]}}}{{{values["ack_line"]}}}\selectfont 谢\quad 辞}}
  \end{{center}}
  \addcontentsline{{toc}}{{chapter}}{{谢辞}}
}}
\newcommand{{\ThesisAppendixTitle}}{{%
  \cleardoublepage
  \phantomsection
  \begin{{center}}
    {{{_font(spec.appendix_title)} {_bold(spec.appendix_title)}\fontsize{{{values["app_size"]}}}{{{values["app_line"]}}}\selectfont 附\quad 录}}
  \end{{center}}
  \addcontentsline{{toc}}{{chapter}}{{附录}}
}}
\newcommand{{\ThesisBeginAppendix}}{{%
  \appendix
  \renewcommand{{\thechapter}}{{附录\Alph{{chapter}}}}
  \renewcommand{{\thesection}}{{\Alph{{chapter}}.\arabic{{section}}}}
  \renewcommand{{\theequation}}{{\alph{{chapter}}-\arabic{{equation}}}}
  \renewcommand{{\thetable}}{{\alph{{chapter}}-\arabic{{table}}}}
  \renewcommand{{\thefigure}}{{\alph{{chapter}}-\arabic{{figure}}}}
  \renewcommand{{\thetheorem}}{{\alph{{chapter}}.\arabic{{theorem}}}}
  \renewcommand{{\theaxiom}}{{\alph{{chapter}}.\arabic{{axiom}}}}
  \renewcommand{{\thecorollary}}{{\alph{{chapter}}.\arabic{{corollary}}}}
  \renewcommand{{\thelemma}}{{\alph{{chapter}}.\arabic{{lemma}}}}
  \renewcommand{{\thedefinition}}{{\alph{{chapter}}.\arabic{{definition}}}}
  \renewcommand{{\theexample}}{{\alph{{chapter}}.\arabic{{example}}}}
}}
\newenvironment{{ThesisAcknowledgement}}{{\ThesisAcknowledgementTitle}}{{\clearpage}}
\newenvironment{{ThesisAppendix}}{{\ThesisAppendixTitle}}{{\clearpage}}
"""


def _render_theorem_algorithm() -> str:
    return r"""
% === Theorem and Algorithm Environments ===
\newtheoremstyle{thesisplain}{0pt}{0pt}{\normalfont}{\ThesisBodyIndent}{\heiti}{}{ }{}
\theoremstyle{thesisplain}
\newtheorem{theorem}{定理}[chapter]
\newtheorem{axiom}[theorem]{公理}
\newtheorem{corollary}[theorem]{推论}
\newtheorem{lemma}[theorem]{引理}
\newtheorem{definition}[theorem]{定义}
\newtheorem{example}[theorem]{例}
\newtheorem{proposition}[theorem]{命题}
\newtheorem{assumption}[theorem]{假设}
\newtheorem{remark}[theorem]{注}
\renewcommand{\thetheorem}{\arabic{chapter}.\arabic{theorem}}
\renewcommand{\theaxiom}{\arabic{chapter}.\arabic{axiom}}
\renewcommand{\thecorollary}{\arabic{chapter}.\arabic{corollary}}
\renewcommand{\thelemma}{\arabic{chapter}.\arabic{lemma}}
\renewcommand{\thedefinition}{\arabic{chapter}.\arabic{definition}}
\renewcommand{\theexample}{\arabic{chapter}.\arabic{example}}
\renewcommand{\theproposition}{\arabic{chapter}.\arabic{proposition}}
\renewcommand{\theassumption}{\arabic{chapter}.\arabic{assumption}}
\renewcommand{\proofname}{证明}
\renewenvironment{proof}[1][\proofname]{\par
  \pushQED{\qed}
  \normalfont
  \topsep0pt \partopsep0pt
  \trivlist
  \item[\hskip\labelsep\heiti #1\@addpunct{:}]\ignorespaces
}{
  \popQED\endtrivlist\@endpefalse
}
\floatname{algorithm}{\ThesisAlgorithmName}
\renewcommand{\algorithmicrequire}{\textbf{输入：}}
\renewcommand{\algorithmicensure}{\textbf{输出：}}
\algrenewcommand\algorithmiccomment[1]{\hfill\textit{// ##1}}
\crefname{chapter}{第}{第}
\crefname{section}{节}{节}
\crefname{figure}{图}{图}
\crefname{table}{表}{表}
\crefname{equation}{式}{式}
\crefname{algorithm}{算法}{算法}
"""


def _render_declaration_placeholders() -> str:
    return r"""
% === Declaration Placeholders ===
\newcommand{\ThesisOriginalityDeclaration}{%
  \cleardoublepage
  \phantomsection
  \begin{center}
    {\heiti\zihao{3} 原创性声明}
  \end{center}
  \addcontentsline{toc}{chapter}{原创性声明}
  \vspace{2em}
  本人声明所呈交的毕业设计（论文）是本人在导师指导下进行的研究工作及取得的研究成果。
  \vspace{4em}
  \par\noindent 作者签名：\hfill 日期：\hspace{6em}\par
  \clearpage
}
\newcommand{\ThesisAuthorizationDeclaration}{%
  \cleardoublepage
  \phantomsection
  \begin{center}
    {\heiti\zihao{3} 授权声明}
  \end{center}
  \addcontentsline{toc}{chapter}{授权声明}
  \vspace{2em}
  本人同意学校保留并向有关部门或机构送交本论文的复印件和电子版，允许论文被查阅和借阅。
  \vspace{4em}
  \par\noindent 作者签名：\hfill 导师签名：\hspace{6em}\par
  \clearpage
}
"""


def _render_utilities() -> str:
    filler_lines = "\n".join(f"% reserved extension hook {index:03d}" for index in range(1, 75))
    return rf"""
% === Utilities ===
\newcommand{{\ThesisBlankPage}}{{%
  \clearpage
  \thispagestyle{{empty}}
  \mbox{{}}
  \clearpage
}}
\newcommand{{\ThesisPlaceholder}}[1]{{\textbf{{<<< #1 >>>}}}}
\newcommand{{\ThesisTodo}}[1]{{\par\noindent\fbox{{\parbox{{0.95\linewidth}}{{#1}}}}\par}}
\newcommand{{\ThesisFrontMatter}}{{\ThesisRomanPageNumbers}}
\newcommand{{\ThesisMainMatter}}{{\clearpage\ThesisArabicPageNumbers}}
\newcommand{{\ThesisBackMatter}}{{\clearpage}}
\newcommand{{\ThesisChapterInput}}[1]{{\input{{chapters/#1}}}}
\newcommand{{\ThesisFigurePath}}[1]{{figures/#1}}
\newcommand{{\ThesisPrintNomenclature}}{{\printnomenclature}}
\newcommand{{\ThesisMakeIndex}}{{\printindex}}
{filler_lines}
"""
