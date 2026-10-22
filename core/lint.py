"""Metadata linter (plan §4.4). Runs at load time; warnings are shown in the "Dữ liệu" tab."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.access import in_subtree
from core.loader import KnowledgeBase
from core.models import DOC_TYPES, PRECEDENCES, SENSITIVITIES, STATUSES
from core.numbers import first_number

REQUIRED_FIELDS = ("id", "version", "title", "doc_type", "scope_unit", "status", "precedence", "sensitivity", "owner")


@dataclass(frozen=True)
class LintWarning:
    code: str
    doc_key: str
    message: str


def _window(doc) -> tuple[date, date]:
    return (doc.effective_from or date.min, doc.effective_to or date.max)


def lint(kb: KnowledgeBase) -> list[LintWarning]:
    out: list[LintWarning] = []

    def warn(code: str, doc, message: str) -> None:
        out.append(LintWarning(code, doc.key, message))

    for doc in kb.docs:
        missing = [f for f in REQUIRED_FIELDS if doc.raw_meta.get(f) in (None, "", [], {})]
        if missing:
            warn("missing_field", doc, f"Thiếu trường bắt buộc: {', '.join(missing)}")
        if doc.status == "active" and doc.effective_from is None:
            warn("missing_field", doc, "Tài liệu active nhưng thiếu effective_from")
        if doc.status == "archived" and (doc.effective_from is None or doc.effective_to is None):
            warn("missing_field", doc, "Tài liệu archived cần đủ effective_from và effective_to để tra cứu theo thời điểm")
        for name, value, allowed in (
            ("doc_type", doc.doc_type, DOC_TYPES),
            ("status", doc.status, STATUSES),
            ("precedence", doc.precedence, PRECEDENCES),
            ("sensitivity", doc.sensitivity, SENSITIVITIES),
        ):
            if value and value not in allowed:
                warn("invalid_value", doc, f"{name} = '{value}' không hợp lệ")
        if doc.scope_unit not in kb.org:
            warn("unknown_unit", doc, f"scope_unit '{doc.scope_unit}' không có trong cây tổ chức")
        for unit in doc.acl_units:
            if unit not in kb.org:
                warn("unknown_unit", doc, f"acl.units chứa '{unit}' không có trong cây tổ chức")
        if doc.supersedes and doc.supersedes not in kb.docs_by_key:
            warn("supersedes_missing", doc, f"supersedes trỏ tới '{doc.supersedes}' không tồn tại trong kho")
        if doc.sensitivity == "restricted" and not doc.acl_units:
            warn("restricted_without_acl", doc, "Tài liệu restricted nhưng không khai báo acl.units")
        for section in doc.sections:
            if not section.topic:
                warn("section_without_topic", doc, f"Mục '{section.heading}' không khai báo topic")
        if doc.injection_lines:
            warn("injection", doc, f"Đã tách {len(doc.injection_lines)} dòng có dạng chỉ thị cho AI khỏi nội dung")

    # Two non-draft versions of the same document whose validity windows overlap.
    by_id: dict[str, list] = {}
    for doc in kb.docs:
        if doc.status != "draft":
            by_id.setdefault(doc.id, []).append(doc)
    for versions in by_id.values():
        versions.sort(key=lambda d: d.version)
        for i, a in enumerate(versions):
            for b in versions[i + 1:]:
                (a_from, a_to), (b_from, b_to) = _window(a), _window(b)
                if a_from <= b_to and b_from <= a_to:
                    warn("overlapping_versions", b, f"Cửa sổ hiệu lực chồng với {a.key}")

    out.extend(_floor_checks(kb))
    return out


def _floor_checks(kb: KnowledgeBase) -> list[LintWarning]:
    """A child unit's figure must not be below a `floor` set by a parent unit for the same topic and audience."""
    out = []
    active = [d for d in kb.docs if d.status == "active"]
    for parent in (d for d in active if d.precedence == "floor"):
        for floor_sec in parent.sections:
            floor_value = first_number(floor_sec.body)
            if floor_value is None or not floor_sec.topic:
                continue
            for child in active:
                if child is parent or child.scope_unit == parent.scope_unit:
                    continue
                if not in_subtree(kb, child.scope_unit, parent.scope_unit):
                    continue
                for sec in child.sections:
                    if sec.topic != floor_sec.topic:
                        continue
                    if floor_sec.audience and sec.audience and not set(floor_sec.audience) & set(sec.audience):
                        continue
                    value = first_number(sec.body)
                    if value is not None and value < floor_value:
                        out.append(LintWarning(
                            "below_floor", child.key,
                            f"Mục '{sec.heading}' ghi {value:g}, thấp hơn mức sàn {floor_value:g} của {parent.key}",
                        ))
    return out
