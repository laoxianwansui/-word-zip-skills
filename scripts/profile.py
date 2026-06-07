"""School-specific structure profile for standalone thesis templates."""

from dataclasses import dataclass, field


@dataclass
class CoverField:
    label: str
    placeholder: str
    required: bool = True
    source_text: str = ""


@dataclass
class FrontmatterPage:
    key: str
    title: str
    body_placeholder: str
    include_in_toc: bool = False
    order: int = 0


@dataclass
class DeclarationPage:
    key: str
    title: str
    body_text_or_placeholder: str
    signature_fields: list[str] = field(default_factory=list)
    include_in_toc: bool = True
    order: int = 0


@dataclass
class SectionRequirement:
    key: str
    title: str
    kind: str
    required: bool = True
    order: int = 0


@dataclass
class AssetPlaceholder:
    key: str
    description: str
    target_path: str


@dataclass
class OutputIdentity:
    class_name: str = "school-thesis"
    package_title: str = "Generated Thesis Template"
    readme_title: str = "Generated Thesis Template"


@dataclass
class SchoolProfile:
    school_name: str = "<<< 学校名称 >>>"
    thesis_type: str = "<<< 论文类型 >>>"
    degree_level: str = "<<< 学位层次 >>>"
    document_title: str = "<<< 论文题目 >>>"
    cover_fields: list[CoverField] = field(default_factory=lambda: [
        CoverField("题目", "<<< 论文题目 >>>"),
        CoverField("学号", "<<< 学号 >>>"),
        CoverField("姓名", "<<< 作者姓名 >>>"),
        CoverField("学院", "<<< 学院 >>>"),
        CoverField("专业", "<<< 专业 >>>"),
        CoverField("指导教师", "<<< 指导教师 >>>"),
    ])
    frontmatter_pages: list[FrontmatterPage] = field(default_factory=lambda: [
        FrontmatterPage("cover", "封面", "", include_in_toc=False, order=0),
    ])
    declaration_pages: list[DeclarationPage] = field(default_factory=list)
    required_sections: list[SectionRequirement] = field(default_factory=lambda: [
        SectionRequirement("abstract_cn", "摘要", "abstract", True, 10),
        SectionRequirement("abstract_en", "Abstract", "abstract", True, 20),
        SectionRequirement("contents", "目录", "contents", True, 30),
        SectionRequirement("chapters", "正文", "body", True, 40),
        SectionRequirement("conclusion", "结论", "chapter", True, 50),
        SectionRequirement("acknowledgement", "谢辞", "chapter", True, 60),
        SectionRequirement("references", "参考文献", "references", True, 70),
        SectionRequirement("appendix", "附录", "appendix", False, 80),
    ])
    optional_sections: list[SectionRequirement] = field(default_factory=list)
    asset_placeholders: list[AssetPlaceholder] = field(default_factory=list)
    output_identity: OutputIdentity = field(default_factory=OutputIdentity)

    def frontmatter_inputs(self) -> list[str]:
        pages = sorted(self.frontmatter_pages, key=lambda page: page.order)
        return [page.key for page in pages if page.key != "cover"]
