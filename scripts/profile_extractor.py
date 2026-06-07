"""Conservative SchoolProfile extraction from parsed thesis documents."""

import re

from profile import CoverField, DeclarationPage, FrontmatterPage, OutputIdentity, SchoolProfile

_SCHOOL_PATTERN = re.compile(r"([一-龥]{2,}(大学|学院|学校))")
_THESIS_TYPES = [
    ("本科毕业设计（论文）", "本科"),
    ("本科毕业论文", "本科"),
    ("本科毕业设计", "本科"),
    ("硕士学位论文", "硕士"),
    ("博士学位论文", "博士"),
    ("课程设计", "课程"),
    ("开题报告", "开题"),
]
_COVER_LABELS = [
    "题目", "论文题目", "学生姓名", "姓名", "作者", "学号", "学院", "院系", "专业", "班级",
    "指导教师", "导师", "指导教师职称", "完成日期", "日期", "提交日期",
]
_DECLARATION_TITLES = ["原创性声明", "诚信声明", "授权声明", "使用授权声明", "版权声明"]
_FRONTMATTER_TITLES = ["任务书", "开题报告", "中期检查", "成绩评定", "评阅书"]
_SIGNATURE_LABELS = ["作者签名", "导师签名", "指导教师签名", "日期"]


def extract_school_profile(parsed_document) -> SchoolProfile:
    texts = [_clean_text(paragraph.text) for paragraph in getattr(parsed_document, "paragraphs", [])]
    texts = [text for text in texts if text]

    profile = SchoolProfile()
    profile.school_name = _extract_school_name(texts) or profile.school_name
    thesis_type, degree_level = _extract_thesis_type(texts)
    if thesis_type:
        profile.thesis_type = thesis_type
    if degree_level:
        profile.degree_level = degree_level

    table_texts = _table_texts(parsed_document)
    cover_fields = _extract_cover_fields(texts + table_texts)
    if cover_fields:
        profile.cover_fields = cover_fields

    declarations = _extract_declaration_pages(texts)
    if declarations:
        profile.declaration_pages = declarations

    frontmatter_pages = _extract_frontmatter_pages(texts)
    if frontmatter_pages:
        profile.frontmatter_pages.extend(frontmatter_pages)

    title = profile.school_name if not profile.school_name.startswith("<<<") else "Generated"
    profile.output_identity = OutputIdentity(
        class_name="school-thesis",
        package_title=f"{title} Thesis Template",
        readme_title=f"{title} Thesis Template",
    )
    return profile


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _table_texts(parsed_document) -> list[str]:
    values = []
    for table in getattr(parsed_document, "tables", []):
        for row in getattr(table, "cells", []):
            for cell in row:
                text = _clean_text(cell)
                if text:
                    values.append(text)
    return values


def _extract_school_name(texts: list[str]) -> str | None:
    for text in texts[:20]:
        match = _SCHOOL_PATTERN.search(text)
        if match:
            return match.group(1)
    return None


def _extract_thesis_type(texts: list[str]) -> tuple[str | None, str | None]:
    for text in texts[:30]:
        for phrase, degree in _THESIS_TYPES:
            if phrase in text:
                return phrase, degree
    return None, None


def _extract_cover_fields(texts: list[str]) -> list[CoverField]:
    fields = []
    seen = set()
    for text in texts[:80]:
        label = _cover_label_from_text(text)
        if not label or label in seen:
            continue
        seen.add(label)
        fields.append(CoverField(label=label, placeholder=f"<<< {label} >>>", source_text=text))
    return fields


def _cover_label_from_text(text: str) -> str | None:
    compact = text.replace(" ", "")
    for label in _COVER_LABELS:
        if re.match(rf"^{re.escape(label)}[:：_\-—]*$", compact):
            return label
        if re.match(rf"^{re.escape(label)}[:：_\-—].*", compact) and len(compact) <= len(label) + 24:
            return label
    return None


def _extract_declaration_pages(texts: list[str]) -> list[DeclarationPage]:
    pages = []
    for index, text in enumerate(texts):
        title = next((candidate for candidate in _DECLARATION_TITLES if candidate == text or candidate in text and len(text) <= 16), None)
        if not title:
            continue
        body_candidates = []
        signatures = []
        for following in texts[index + 1:index + 8]:
            signatures.extend(label for label in _SIGNATURE_LABELS if label in following and label not in signatures)
            if not any(label in following for label in _SIGNATURE_LABELS):
                body_candidates.append(following)
        body = "\n\n".join(body_candidates).strip() or f"<<< 请输入{title}正文 >>>"
        key = f"declaration_{len(pages) + 1}"
        pages.append(DeclarationPage(key=key, title=title, body_text_or_placeholder=body, signature_fields=signatures, order=100 + len(pages)))
    return pages


def _extract_frontmatter_pages(texts: list[str]) -> list[FrontmatterPage]:
    pages = []
    seen = set()
    for text in texts[:120]:
        title = next((candidate for candidate in _FRONTMATTER_TITLES if candidate == text or candidate in text and len(text) <= 20), None)
        if not title or title in seen:
            continue
        seen.add(title)
        key = _frontmatter_key(title)
        pages.append(FrontmatterPage(key=key, title=title, body_placeholder=f"<<< 请输入{title}内容 >>>", include_in_toc=False, order=10 + len(pages)))
    return pages


def _frontmatter_key(title: str) -> str:
    return {
        "任务书": "task_book",
        "开题报告": "proposal",
        "中期检查": "midterm_check",
        "成绩评定": "grade_evaluation",
        "评阅书": "review_form",
    }.get(title, f"frontmatter_{len(title)}")
