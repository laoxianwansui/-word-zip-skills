"""LaTeX 模板生成器。

使用 Jinja2 引擎，根据提取的格式规格 (ThesisSpec) 渲染所有 LaTeX 模板文件，
生成完整的 Overleaf 项目目录。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extractor import ThesisSpec

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    raise ImportError("需要安装 Jinja2: pip install Jinja2")


# 模板文件与输出路径的映射
_TEMPLATE_MAP = [
    ("base.tex.j2", "main.tex"),
    ("packages.sty.j2", "packages.sty"),
    ("cover.tex.j2", "chapters/cover.tex"),
    ("abstract_cn.tex.j2", "chapters/abstract_cn.tex"),
    ("abstract_en.tex.j2", "chapters/abstract_en.tex"),
    ("conclusion.tex.j2", "chapters/conclusion.tex"),
    ("acknowledgement.tex.j2", "chapters/acknowledgement.tex"),
    ("references.tex.j2", "chapters/references.tex"),
    ("appendix.tex.j2", "chapters/appendix.tex"),
]

# 章节模板（需要传入 chapter_num 参数）
_CHAPTER_TEMPLATE = "chapter.tex.j2"


def generate_template(spec: ThesisSpec, output_dir: str,
                      template_dir: str = None,
                      chapter_count: int = 3) -> str:
    """根据格式规格生成完整的 LaTeX 项目。

    Args:
        spec: ThesisSpec 格式规格对象
        output_dir: 输出目录路径
        template_dir: Jinja2 模板目录路径（默认使用相对路径找到 templates/）
        chapter_count: 生成的章节数量

    Returns:
        输出目录的路径
    """
    if template_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(os.path.dirname(script_dir), "templates")

    print(f"[生成] 加载模板: {template_dir}")

    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    chapters_dir = os.path.join(output_dir, "chapters")
    figures_dir = os.path.join(output_dir, "figures")
    os.makedirs(chapters_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    # 渲染固定模板
    for template_name, output_name in _TEMPLATE_MAP:
        print(f"[生成] {template_name} -> {output_name}")
        template = env.get_template(template_name)
        rendered = template.render(spec=spec)

        output_path = os.path.join(output_dir, output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered)

    # 渲染各章模板
    chapter_template = env.get_template(_CHAPTER_TEMPLATE)
    for ch_num in range(1, chapter_count + 1):
        rendered = chapter_template.render(spec=spec, chapter_num=ch_num)
        output_path = os.path.join(
            chapters_dir, f"chapter{ch_num}.tex"
        )
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered)
        print(f"[生成] chapter.tex.j2 -> chapters/chapter{ch_num}.tex")

    # 同时更新 base.tex 中的章节引用（已经硬编码引用 chapter1-3）

    # 生成示例 .bib 文件
    _generate_sample_bib(output_dir)

    # 生成 .latexmkrc (Overleaf 编译配置)
    _generate_latexmkrc(output_dir)

    print(f"[生成] 完成。输出目录: {output_dir}")
    return output_dir


def _generate_sample_bib(output_dir: str):
    """生成示例参考文献 .bib 文件 (GB/T 7714 格式)"""
    bib_content = """% 参考文献数据库 (BibTeX)
% 引用方式: \\cite{key}
% 编译顺序: XeLaTeX → BibTeX → XeLaTeX → XeLaTeX

@article{ref_journal,
  author  = {张三 and 李四 and 王五},
  title   = {示例期刊论文标题},
  journal = {期刊名称},
  year    = {2024},
  volume  = {1},
  number  = {1},
  pages   = {1-10},
}

@book{ref_book,
  author    = {作者},
  title     = {示例专著标题},
  publisher = {出版社},
  year      = {2024},
  address   = {出版地},
}

@inproceedings{ref_conference,
  author    = {作者一 and 作者二},
  title     = {示例会议论文标题},
  booktitle = {会议名称},
  year      = {2024},
  pages     = {100-110},
}

@mastersthesis{ref_thesis,
  author = {作者},
  title  = {示例学位论文标题},
  school = {大学名称},
  year   = {2024},
  type   = {硕士学位论文},
}

@patent{ref_patent,
  author = {发明人},
  title  = {示例专利名称},
  nationality = {中国},
  number = {CN123456789A},
  year   = {2024},
}
"""
    bib_path = os.path.join(output_dir, "bibliography.bib")
    with open(bib_path, 'w', encoding='utf-8') as f:
        f.write(bib_content)


def _generate_latexmkrc(output_dir: str):
    """生成 Overleaf 编译配置文件"""
    latexmkrc = """# Overleaf 编译配置
$latex = 'xelatex';
$bibtex = 'bibtex';
$pdf_mode = 1;
$recorder = 1;
"""
    rc_path = os.path.join(output_dir, "latexmkrc")
    with open(rc_path, 'w', encoding='utf-8') as f:
        f.write(latexmkrc)
