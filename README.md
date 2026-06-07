# Thesis Template Skill

[简体中文](#简体中文) | [English](#english)

## 简体中文

用于 Claude Code 的实验性技能：根据 Word/PDF 格式要求文档，生成可直接上传到 Overleaf 的 LaTeX 论文模板项目 ZIP。

### 功能说明

该技能会读取 Word 或 PDF 格式的论文要求/示例文档，并生成一个独立的 Overleaf 项目 ZIP。

处理流程：

```text
Word/PDF 输入
  -> ParsedDocument
  -> ThesisSpec      # 格式规则
  -> SchoolProfile   # 学校相关结构
  -> school-thesis.cls + frontmatter + chapters
  -> profile.yaml + profile_report.md
  -> Overleaf ZIP
```

### 主要功能

- 解析 Word `.doc` / `.docx` 文件；在 Windows 且可用 Microsoft Word 时，支持通过 COM 获得更好的 Word 格式识别精度
- 支持 PDF 文本提取
- 格式聚类与论文章节分类
- 生成 `school-thesis.cls`
- 提取学校名称、封面字段和前置页结构
- 生成可手动修正的 `profile.yaml`
- 生成带质量评分的 `profile_report.md` 诊断报告
- 支持通过 CLI 覆盖学校名称和论文类型
- 打包为 Overleaf 兼容 ZIP

### 识别率与准确率

当前指标是工程目标和实际使用预期，不是覆盖所有学校模板的公开基准测试结果。准确率会受到源文档质量、Word/PDF 类型、是否保留真实格式、是否可用 Microsoft Word COM 后端等因素影响。

| 项目 | 当前目标/预期 |
| --- | --- |
| Word 原始格式读取 | 对结构清晰的学校 Word 填写样板，通常目标为 90%+ |
| 自动语义识别 | 对章节角色、封面字段、前置页结构等，目标为 82%–88% |
| 人工确认后模板可用度 | 阅读 `profile_report.md` 并修正 `profile.yaml` 后，目标为 90%+ |

生成项目中的 `profile_report.md` 会给出质量评分、缺失项提示和低置信度信息；如果报告中低置信度内容较多，应先修正 `profile.yaml` 再重新生成。PDF 输入通常更依赖文本和版式提取质量，准确率可能低于可编辑 Word 文档。

### 安装

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

在 Windows 上，如果安装了 `pywin32` 并且本机有 Microsoft Word，Word 格式识别效果最好。

### 使用方法

生成独立的 Overleaf ZIP：

```bash
python scripts/build_standalone.py "path/to/input.docx" --backend auto --output "path/to/thesis_template_overleaf.zip"
```

当源文档中学校信息不清晰时，可以手动指定学校名称和论文类型：

```bash
python scripts/build_standalone.py "path/to/input.docx" \
  --backend auto \
  --school-name "Example University" \
  --thesis-type "Undergraduate Thesis" \
  --output "path/to/thesis_template_overleaf.zip"
```

使用编辑后的配置文件重新生成：

```bash
python scripts/build_standalone.py "path/to/input.docx" \
  --backend auto \
  --profile "path/to/profile.yaml" \
  --output "path/to/thesis_template_overleaf.zip"
```

将生成的 ZIP 上传到 Overleaf，并选择 XeLaTeX 编译。

### 生成的项目文件

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

### 当前状态

这是一个实验性 alpha 项目。它适合用于生成论文模板的高质量初稿，但不能保证完全像素级复刻每个学校的官方模板。

推荐流程：

1. 生成 ZIP。
2. 阅读 `profile_report.md`。
3. 如果识别有遗漏，编辑 `profile.yaml`。
4. 使用 `--profile` 重新生成。
5. 在 Overleaf 中使用 XeLaTeX 编译。

### 隐私说明

不要公开真实论文样例、学校内部文档、生成的私有 ZIP，或任何包含个人信息的文档。

## English

Experimental Claude Code skill for generating Overleaf-ready LaTeX thesis templates from Word/PDF university formatting requirements.

### What it does

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

### Features

- Word `.doc` / `.docx` parsing, with Microsoft Word COM support on Windows when available
- PDF text extraction support
- Format clustering and thesis section classification
- Generated `school-thesis.cls`
- School profile extraction for cover fields and frontmatter
- Editable `profile.yaml` for manual correction
- `profile_report.md` diagnostics with a quality score
- CLI overrides for school name and thesis type
- Overleaf-compatible ZIP packaging

### Recognition and accuracy

The numbers below are engineering targets and practical-use expectations, not a public benchmark across every university template. Accuracy depends on source document quality, Word/PDF type, whether real formatting is preserved, and whether the Microsoft Word COM backend is available.

| Area | Current target/expectation |
| --- | --- |
| Raw Word format extraction | Typically targets 90%+ for well-structured university Word samples |
| Automatic semantic recognition | Targets 82%–88% for section roles, cover fields, and frontmatter structure |
| Template usability after review | Targets 90%+ after reading `profile_report.md` and correcting `profile.yaml` |

Generated projects include `profile_report.md` with a quality score, missing-item hints, and low-confidence information. If the report shows many low-confidence items, edit `profile.yaml` and regenerate. PDF input usually depends more heavily on text/layout extraction quality, so it may be less accurate than editable Word input.

### Installation

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

On Windows, installing `pywin32` and having Microsoft Word available gives the best Word-format accuracy.

### Usage

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

### Generated project files

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

### Status

This is an experimental alpha project. It is useful for generating a strong first draft of a thesis template, but it does not guarantee pixel-perfect reproduction of every school's official template.

Recommended workflow:

1. Generate the ZIP.
2. Read `profile_report.md`.
3. Edit `profile.yaml` if recognition missed anything.
4. Regenerate with `--profile`.
5. Compile in Overleaf with XeLaTeX.

### Privacy

Do not publish real thesis samples, school-internal documents, generated private ZIPs, or documents containing personal information.
