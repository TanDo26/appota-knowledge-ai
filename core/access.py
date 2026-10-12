"""Hard filter (pipeline step 2): permission, scope, audience, status, validity window, supersedes.

Runs BEFORE retrieval, so hidden documents are never scored and the system cannot reveal that a
restricted document "matches your question". Two separate ideas (plan §4.3):

- scope (`scope_unit`, `applies_to`): who the document APPLIES to
- permission (`acl`, `sensitivity`): who may SEE it

A document must pass both to become a candidate.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from core.loader import KnowledgeBase
from core.models import Doc, Section, User

# Checked in this order; the first failing check is the reported reason. Permission goes first so
# a hidden document is only ever counted as "no permission", never described further.
REASON_LABELS = {
    "acl": "Không có quyền xem",
    "scope": "Ngoài phạm vi đơn vị",
    "audience": "Không áp dụng cho loại hợp đồng",
    "status": "Bản nháp hoặc đã lưu trữ",
    "not_yet_effective": "Chưa đến ngày hiệu lực",
    "expired": "Đã hết hiệu lực",
    "superseded": "Đã có bản mới thay thế",
    "section_audience": "Mục không áp dụng cho loại hợp đồng",
}


def ancestors_or_self(kb: KnowledgeBase, unit_id: str) -> list[str]:
    return [u.id for u in kb.unit_chain(unit_id)]


def in_subtree(kb: KnowledgeBase, unit_id: str, root_id: str) -> bool:
    return root_id in ancestors_or_self(kb, unit_id)


def can_view(kb: KnowledgeBase, user: User, doc: Doc) -> bool:
    units = doc.acl_units or (doc.scope_unit,)
    if not any(in_subtree(kb, user.unit, u) for u in units):
        return False
    return not doc.acl_roles or user.role in doc.acl_roles


def in_scope(kb: KnowledgeBase, user: User, doc: Doc) -> bool:
    """A document applies to the asker's own unit and every unit above it, never to siblings or children."""
    return doc.scope_unit in ancestors_or_self(kb, user.unit)


def audience_ok(audience: tuple[str, ...], user: User) -> bool:
    return not audience or user.employment_type in audience


def in_effect(doc: Doc, as_of: date) -> bool:
    return window_reason(doc, as_of) is None and doc.status == "active"


def window_reason(doc: Doc, as_of: date) -> str | None:
    if doc.effective_from is not None and as_of < doc.effective_from:
        return "not_yet_effective"
    if doc.effective_to is not None and as_of > doc.effective_to:
        return "expired"
    return None


def superseded_keys(docs: list[Doc], as_of: date) -> set[str]:
    """Versions replaced by a version that is in effect, even if their own status was never updated."""
    return {d.supersedes for d in docs if d.supersedes and in_effect(d, as_of)}


@dataclass
class FilterResult:
    sections: list[Section] = field(default_factory=list)
    excluded: list[tuple[str, str]] = field(default_factory=list)  # (doc key, reason)
    excluded_sections: list[tuple[str, str]] = field(default_factory=list)  # (section id, reason)
    # Approved versions the asker could see and that apply to them, but are not in effect yet.
    upcoming: list[Doc] = field(default_factory=list)

    @property
    def doc_keys(self) -> set[str]:
        return {s.doc.key for s in self.sections}

    def counts(self) -> dict[str, int]:
        c = Counter(reason for _, reason in self.excluded)
        c.update(reason for _, reason in self.excluded_sections)
        return dict(c)


def doc_reason(kb: KnowledgeBase, user: User, doc: Doc, as_of: date, superseded: set[str]) -> str | None:
    if not can_view(kb, user, doc):
        return "acl"
    if not in_scope(kb, user, doc):
        return "scope"
    if not audience_ok(doc.applies_to, user):
        return "audience"
    if doc.status != "active":
        return "status"
    reason = window_reason(doc, as_of)
    if reason:
        return reason
    if doc.key in superseded:
        return "superseded"
    return None


def filter_for(kb: KnowledgeBase, user: User, as_of: date) -> FilterResult:
    result = FilterResult()
    superseded = superseded_keys(kb.docs, as_of)
    for doc in kb.docs:
        reason = doc_reason(kb, user, doc, as_of, superseded)
        if reason is not None:
            result.excluded.append((doc.key, reason))
            if reason == "not_yet_effective":
                result.upcoming.append(doc)
            continue
        for section in doc.sections:
            if audience_ok(section.audience, user):
                result.sections.append(section)
            else:
                result.excluded_sections.append((section.id, "section_audience"))
    return result
