---
name: thesis-template
description: |
  读取学术论文/报告/公文等文档（Word .doc/.docx 或 PDF），自动识别其格式要求和文档结构，
  生成干净的、内容可填写的 LaTeX 模板，并打包为 Overleaf 可上传的 ZIP 文件。

  **触发条件**: 用户提到以下任一情况时使用此技能：
  - "生成 LaTeX 模板"、"论文模板"、"毕业论文格式"、"Overleaf 模板"
  - 上传或指定 .doc/.docx/.pdf 文件，要求"整理格式"、"做成模板"、"转成 LaTeX"
  - 需要从格式规范文档中提取排版要求并生成可直接填写内容的 .tex 文件
  - 准备投 Overleaf 但需要符合学校/期刊格式要求

  **不适用**: 简单的文档格式转换（如 docx 转 pdf）、普通的文件读取、不涉及 LaTeX 模板生成的场景。
license: Proprietary. LICENSE.txt has complete terms
compatibility:
  requires: ["python-docx", "PyMuPDF", "pywin32", "jinja2"]
  notes: "pywin32 + Microsoft Word gives highest Word format accuracy on Windows; python-docx is fallback."
---

# 论文模板生成器 (Thesis Template)

从任意格式的论文/报告文档中智能提取结构和格式要求，生成干净的 LaTeX 模板，打包为 Overleaf ZIP。

## 工作流

核心理念：**高精度输入 + Profile 驱动的学校专属输出**。Word 文档优先通过 Windows Microsoft Word COM 读取真实渲染格式；不可用时降级到 python-docx。无参考 LaTeX ZIP 时，主路径会从 Word/PDF 中提取 `ThesisSpec`（格式规则）和 `SchoolProfile`（学校名称、论文类型、封面字段、声明页、前置页面、章节顺序），生成不硬编码具体学校、但输出效果学校专属的 Overleaf ZIP。参考 ZIP 支持可以作为可选增强，但不再是 standalone 主路径的前提。

当前方案 A 的目标：对学校 Word 填写样板，原始格式读取通常可达 90%+；自动语义识别目标为 82%–88%；生成报告后人工确认低置信度簇，最终模板可用度目标为 90%+。

当前 standalone 主路径会优先解析格式说明文字，例如“三号黑体居中”“小四号宋体首行缩进两个字”“关键词：(小四号、黑体、顶格)”，把它们转成结构化 `ThesisSpec`，再写入生成的 `school-thesis.cls`。这能避免把说明文字自身的渲染样式误当成目标样式。

### SchoolProfile 学校专属结构层

standalone 主路径会同时生成两个结构：

- `ThesisSpec`：负责字号、字体、页边距、标题、正文、摘要、目录、参考文献、图表、附录等格式规则。
- `SchoolProfile`：负责学校名称、论文类型、封面字段、原创性/授权声明、任务书/开题报告等前置页面、章节骨架和输出项目标题。

生成器应通过 `SchoolProfile` 渲染学校专属 `.tex` 文件，而不是在代码中写 `if school == "某大学"` 这样的分支。原则是：**输出可以像某个学校的模板，实现不能硬编码某个学校。**

按以下步骤执行，不要跳过。

### 步骤 1: 读取文档

```python
from reader import read_document

doc = read_document("用户提供的文件路径", backend="auto")
# backend="auto": Windows+Word 优先 pywin32；否则 python-docx fallback
# backend="pywin32": 强制 Word COM 高精度解析
# backend="docx": 强制 python-docx fallback
```

### 步骤 2: 格式聚类

调用聚类引擎，按段落的格式属性（字体、字号、加粗、对齐、缩进、行距）自动分组：

```python
from analyzer import analyze_structure
structure, cluster_result = analyze_structure(doc)
```

这会打印每个格式簇的统计信息。输出示例：
```
[簇 0] 35段 | 宋体 12pt | 未指定 → 大量相同格式的正文类段落
[簇 1] 15段 | 宋体 16pt | center → 居中标题类
[簇 2] 7段  | 宋体 12pt | 加粗   → 加粗的子标题
...
```

### 步骤 3: LLM 标注格式簇

**这是关键步骤**。阅读上一步打印的簇统计表，为每个簇标注语义角色。

可用的语义标签：
- `论文大标题`, `封面信息`
- `中文摘要标题`, `中文摘要正文`, `中文关键词标签`, `中文关键词正文`
- `英文摘要标题`, `英文摘要正文`, `英文关键词标签`, `英文关键词正文`
- `目录标题`
- `一级标题`, `二级标题`, `三级标题`
- `正文段落`
- `结论标题`, `谢辞标题`, `参考文献标题`, `参考文献条目`, `附录标题`
- `图题`, `表题`, `公式`
- `页眉`, `页脚`
- `格式说明` (格式说明文本，可忽略)
- `其他` (示例内容，可忽略)

标注格式（Python dict）：
```python
label_map = {
    0: "中文摘要正文",      # 35段 宋体 12pt → 摘要和格式说明
    1: "中文摘要标题",      # 15段 宋体 16pt center → 各种居中标题
    2: "二级标题",          # 7段 宋体 12pt 加粗 → 节标题
    # ... 为每个簇标注
}
```

**标注原则**：
1. 看簇的**格式特征**（字体+字号+对齐+加粗）而不是示例文本
2. 同名格式簇（如两个簇都是 宋体12pt）要结合示例区分：正文有首行缩进，格式说明没有
3. 标签为"格式说明""其他"的簇会被忽略，不进入最终模板
4. 同一语义标签可以分配给多个簇（如果文档中同种内容用了不同格式）

### 步骤 4: 生成格式规格

```python
from extractor import extract_specs_from_clusters
spec = extract_specs_from_clusters(cluster_result, label_map)
```

这一步直接将每个簇的格式统计（字号pt、字体、对齐、缩进）转为 `ThesisSpec` 中的对应字段，无需任何正则匹配。

### 步骤 5: 生成 LaTeX 模板

```python
from generator import generate_template
import tempfile, os

output_dir = os.path.join(tempfile.gettempdir(), "thesis_template_output")
generate_template(spec, output_dir, chapter_count=3)
```

### 步骤 6: 打包 ZIP

```python
from packager import package_zip
zip_path = package_zip(output_dir)
```

### 步骤 7: 呈现结果

向用户说明：
1. ZIP 文件的位置
2. 使用方法：Overleaf → New Project → Upload Project → 上传 ZIP
3. 编译器选择 **XeLaTeX**
4. 所有 `<<< >>>` 占位符替换为实际内容即可

## 新架构 vs 旧架构

| 方面 | 旧架构 (正则) | 新架构 (聚类) |
|------|-------------|-------------|
| 核心逻辑 | 正则逐段猜文本类型 | 格式属性自动聚类 |
| "居中"识别 | 依赖文本提到"居中"二字 | 直接读取 alignment 属性 |
| 换学校模板 | 需重写正则 | 无需修改，自动适配 |
| 准确率 | ~50% (正则漏洞多) | 90%+ (聚类+LLM标注) |
```

这一步会自动：
1. 对所有段落进行分类：**格式注解**（"三号黑体居中"）vs **内容占位符**（"摘  要"）vs **正文内容**
2. 识别章节边界：封面、中文摘要、英文摘要、目录、各章、结论、谢辞、参考文献、附录
3. 提取每个章节的实际格式特征
4. 打印分析结果摘要

**分析完成后，向用户报告识别结果**：识别到哪些章节、格式注解比例、低置信度段落数量。如果有大量低置信度段落（>20%），提醒用户可能需要人工检查。

### 步骤 3: 提取格式规格

调用 `scripts/extractor.py` 的 `extract_specs()` 函数：

```python
from extractor import extract_specs
spec = extract_specs(structure)
```

这将生成 `ThesisSpec` 对象，包含每个章节类型的完整格式规格（字体、字号、对齐、缩进、页面设置），以中国本科论文国标为默认值，并用文档中提取的规格覆盖。

### 步骤 4: 生成 LaTeX 模板

调用 `scripts/generator.py` 的 `generate_template()` 函数：

```python
from generator import generate_template
import tempfile, os

output_dir = os.path.join(tempfile.gettempdir(), "thesis_template_output")
generate_template(spec, output_dir, chapter_count=N)
```

`chapter_count` 参数控制生成的章节文件数量。默认 3 章。可根据原文识别的章节数量调整。

生成的目录结构：
```
output/
├── main.tex                 # 主文件 (ctexrep)
├── packages.sty             # 自定义格式/样式
├── bibliography.bib         # 示例参考文献
├── latexmkrc                # Overleaf 编译配置
├── chapters/
│   ├── cover.tex            # 封面 (含字段表格)
│   ├── abstract_cn.tex      # 中文摘要
│   ├── abstract_en.tex      # 英文摘要
│   ├── chapter1.tex         # 第1章 (含图/表/公式示例)
│   ├── chapter2.tex         # 第2章
│   ├── chapter3.tex         # 第3章
│   ├── conclusion.tex       # 结论
│   ├── acknowledgement.tex  # 谢辞
│   ├── references.tex       # 参考文献
│   └── appendix.tex         # 附录
└── figures/                 # 图片目录
```

模板特点：
- 使用 `ctexrep` 文档类（中文论文标准，支持 XeLaTeX 编译）
- 所有需填内容的区域用 `<<< 提示文字 >>>` 占位符标记，直观易找
- 格式已全部设置好，用户只需替换占位符内容
- 图表和公式编号自动生成（图X.Y、表X.Y、(X-Y)）
- 仅使用 CTAN 标准宏包，Overleaf 零配置编译

### 步骤 5: 打包 ZIP

调用 `scripts/packager.py` 的 `package_zip()` 函数：

```python
from packager import package_zip
zip_path = package_zip(output_dir)
```

这会将 `output_dir` 打包为 Overleaf 兼容的 ZIP 文件。**ZIP 路径是最终产物，告知用户此路径。**

### 步骤 6: 呈现结果

向用户说明：
1. ZIP 文件的位置
2. 使用方法：在 Overleaf 上"New Project" → "Upload Project"，上传 ZIP 文件
3. 编译设置：编译器选择 **XeLaTeX**
4. 各章节文件的用途和 <<< >>> 占位符的使用方式

## 格式识别原理

技能内部使用三层规则区分格式注解和内容占位符：

1. **关键词匹配** (处理 80% 段落): 检测"字号+字体+格式词"组合（如"三号黑体居中"）→ 格式注解；检测章节标题关键词（"摘  要"、"目录"、"第X章"）→ 内容占位符
2. **字号一致性检验** (处理 15%): 文本描述的字号与实际渲染字号是否一致。不一致 → 格式注解
3. **LLM 语义判断** (处理 5% 边界情况): 无法自动确定的段落，根据上下文语义判断

每个段落标记了置信度。低置信度的分类会在控制台输出中注明。

## 边界情况处理

### .doc 文件 (旧格式)
通过 pywin32 COM 自动化先转换为 .docx 再解析。如果转换失败，使用降级方案直接提取纯文本（精度较低，只保留文本信息）。

### PDF 是扫描版/图片
PyMuPDF 提取文本可能为空或极少。提示用户这是扫描版 PDF，建议使用 OCR 预处理。不要尝试继续生成模板。

### 文档仅有格式说明无内容
不会报错。所有内容区域使用泛型占位符 `<<< 请输入... >>>`。

### 文档不含任何格式说明
从实际渲染格式反推规格（字号、字体、对齐等），使用这些反推值生成模板。

### 加密/受保护的文档
python-docx 和 PyMuPDF 可能无法读取。提示用户先解除保护。

### 超大文档 (>200 页)
分页处理 PDF，避免内存问题。对于 .docx，按需流式读取。

## 推荐 CLI

### 情况 2：只有 Word/PDF 格式要求，无 LaTeX 参考 ZIP

这是当前主流程。它会从输入文档识别格式，生成自带 `school-thesis.cls` 的独立 Overleaf 项目：

```bash
python scripts/build_standalone.py "输入文档.docx" --backend auto --output "输出目录/thesis_template_overleaf.zip"
```

可选覆盖参数：

```bash
python scripts/build_standalone.py "输入文档.docx" --backend auto --school-name "学校名称" --thesis-type "论文类型" --output "输出目录/thesis_template_overleaf.zip"
```

如果自动识别结果需要人工修正，先使用生成项目中的 `profile.yaml` 修改学校名称、论文类型、学位层次和封面字段，再通过 `--profile` 重新生成：

```bash
python scripts/build_standalone.py "输入文档.docx" --backend auto --profile "profile.yaml" --output "输出目录/thesis_template_overleaf.zip"
```

生成项目会包含 `profile_report.md`，用于查看 `SchoolProfile` 识别摘要、缺失占位符和质量评分。

输出结构：

```text
main.tex
school-thesis.cls
latexmkrc
README.md
references.bib
chapters/
figures/
```

### 情况 1：用户提供学校 LaTeX 参考 ZIP

当用户明确提供参考 ZIP 且想保留该模板工程结构时，使用 reference ZIP 流程：

```bash
python scripts/build_from_reference.py "输入文档.docx" --backend auto --output "输出目录"
```

可指定参考模板：

```bash
python scripts/build_from_reference.py "输入文档.docx" --reference "学校LaTeX模板.zip" --output "输出目录"
```

默认参考 ZIP：`path/to/reference-template.zip`。

如果参考 ZIP 不存在，才使用旧的 Jinja2 从零生成流程。

### Aspose.Words

本轮不强依赖 Aspose.Words。未来如果需要 Mac/Linux 商业级格式识别，可增加 `backend="aspose"`，但当前默认路线是 `pywin32` 优先、`python-docx` 兜底。

## 文件清单

```
skills/thesis-template/
├── SKILL.md                        # 本文件
├── LICENSE.txt
├── scripts/
│   ├── reader.py                   # 统一文档读取入口（auto/pywin32/docx 后端）
│   ├── build_from_reference.py     # reference ZIP 工作流 CLI
│   ├── reference_project.py        # 参考 LaTeX ZIP 清理/占位符化/打包
│   ├── reporter.py                 # 格式识别报告生成
│   ├── parsers/
│   │   ├── docx_parser.py          # .docx 解析 (python-docx fallback)
│   │   ├── word_com_parser.py      # .doc/.docx 高精度 Word COM 解析
│   │   ├── pdf_parser.py           # .pdf 解析 (PyMuPDF + pdfplumber)
│   │   └── doc_parser.py           # .doc 旧转换/降级解析
│   ├── classifier.py               # 段落分类器
│   ├── analyzer.py                 # 文档结构分析
│   ├── extractor.py                # 格式规格提取
│   ├── format_rule_parser.py       # 中文格式说明 → 结构化 TextFormat 规则
│   ├── generator.py                # Jinja2 模板生成
│   ├── class_generator.py          # standalone school-thesis.cls 生成
│   ├── standalone_project.py       # standalone Overleaf 项目生成
│   └── packager.py                 # ZIP 打包器
├── templates/                      # Jinja2 LaTeX 模板
│   ├── base.tex.j2                 # 主文件
│   ├── packages.sty.j2             # 宏包/样式
│   ├── cover.tex.j2                # 封面
│   ├── abstract_cn.tex.j2          # 中文摘要
│   ├── abstract_en.tex.j2          # 英文摘要
│   ├── chapter.tex.j2              # 章节
│   ├── conclusion.tex.j2           # 结论
│   ├── acknowledgement.tex.j2      # 谢辞
│   ├── references.tex.j2           # 参考文献
│   └── appendix.tex.j2             # 附录
└── references/
    ├── format_mapping.md            # 字号→pt→LaTeX 对照表
    └── overleaf_requirements.md     # Overleaf 上传规范
```
