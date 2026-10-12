from __future__ import annotations

from datetime import date
from textwrap import dedent

import pytest

from core.loader import KnowledgeBase, load_kb, parse_document

AS_OF = date(2026, 10, 15)


@pytest.fixture(scope="session")
def kb() -> KnowledgeBase:
    return load_kb()


def make_doc(
    doc_id="X-01",
    version=1,
    *,
    title="Tài liệu thử",
    doc_type="policy",
    scope_unit="CO_A",
    employment_types=("full_time", "probation", "intern"),
    status="active",
    effective_from="2026-01-01",
    effective_to="null",
    supersedes="null",
    precedence="override",
    acl_units=None,
    acl_roles=(),
    sensitivity="internal",
    sections="## 1. Mục một\n<!-- topic: test.topic -->\nNội dung 10 ngày.\n",
):
    acl_units = acl_units if acl_units is not None else (scope_unit,)
    text = dedent(f"""\
        ---
        id: {doc_id}
        version: {version}
        title: {title}
        doc_type: {doc_type}
        scope_unit: {scope_unit}
        applies_to:
          employment_types: [{", ".join(employment_types)}]
        status: {status}
        effective_from: {effective_from}
        effective_to: {effective_to}
        supersedes: {supersedes}
        precedence: {precedence}
        acl:
          units: [{", ".join(acl_units)}]
          roles: [{", ".join(acl_roles)}]
        sensitivity: {sensitivity}
        owner: {{ team: "Chủ sở hữu", contact: "owner@example.com" }}
        ---

        # {title}

        """) + sections
    return parse_document(text, path=f"{doc_id}_v{version}.md")


def kb_with(base: KnowledgeBase, *docs) -> KnowledgeBase:
    """The real org tree and personas with a synthetic set of documents."""
    return KnowledgeBase(org=base.org, users=base.users, docs=list(docs), contacts=base.contacts)
