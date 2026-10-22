"""Hard filter (pipeline step 2): permission, scope, audience, status, validity window, supersedes.

Runs BEFORE retrieval, so hidden documents are never scored and the system cannot reveal that a
restricted document "matches your question". Two separate ideas (plan §4.3):

- scope (`scope_unit`, `applies_to`): who the document APPLIES to
- permission (`acl`, `sensitivity`): who may SEE it

A document must pass both to become a candidate. Since Mission 3 the two can be about different people:
permission is always checked for the asker, applicability for the subject of the question (the asker
unless the question names another unit or contract type, see core/context.py). A lookup can therefore
only narrow what the asker sees, never widen it.

Status and time (Mission 3): `draft` is never used. `archived` means "no longer in force", not "never
was": an archived version is used for a lookup date inside its validity window (a question about 2025
gets the 2025 policy), and needs `effective_to` for that (linted).
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


def in_scope(kb: KnowledgeBase, unit_id: str, doc: Doc) -> bool:
    """A document applies to a unit and every unit above it, never to siblings or children."""
    return doc.scope_unit in ancestors_or_self(kb, unit_id)


def audience_ok(audience: tuple[str, ...], employment_type: str) -> bool:
    return not audience or employment_type in audience


def status_ok(doc: Doc, as_of: date) -> bool:
    """Active, or archived with `as_of` inside its (closed) validity window."""
    if doc.status == "active":
        return True
    return doc.status == "archived" and doc.effective_to is not None and window_reason(doc, as_of) is None


def in_effect(doc: Doc, as_of: date) -> bool:
    return status_ok(doc, as_of) and window_reason(doc, as_of) is None


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


def doc_reason(kb: KnowledgeBase, user: User, doc: Doc, as_of: date, superseded: set[str],
               unit: str | None = None, employment_type: str | None = None) -> str | None:
    if not can_view(kb, user, doc):
        return "acl"
    if not in_scope(kb, unit or user.unit, doc):
        return "scope"
    if not audience_ok(doc.applies_to, employment_type or user.employment_type):
        return "audience"
    if not status_ok(doc, as_of):
        return "status"
    reason = window_reason(doc, as_of)
    if reason:
        return reason
    if doc.key in superseded:
        return "superseded"
    return None


def filter_for(kb: KnowledgeBase, user: User, as_of: date,
               unit: str | None = None, employment_type: str | None = None) -> FilterResult:
    """Sections `user` may see that apply to (`unit`, `employment_type`) — the asker by default — on `as_of`."""
    result = FilterResult()
    # Only versions the asker may see can retire another one: a hidden new version must not change what the
    # asker is shown, or the change itself reveals that it exists (Change Request B2; linted as visibility_gap).
    superseded = superseded_keys([d for d in kb.docs if can_view(kb, user, d)], as_of)
    employment_type = employment_type or user.employment_type
    for doc in kb.docs:
        reason = doc_reason(kb, user, doc, as_of, superseded, unit, employment_type)
        if reason is not None:
            result.excluded.append((doc.key, reason))
            if reason == "not_yet_effective":
                result.upcoming.append(doc)
            continue
        for section in doc.sections:
            if audience_ok(section.audience, employment_type):
                result.sections.append(section)
            else:
                result.excluded_sections.append((section.id, "section_audience"))
    return result
