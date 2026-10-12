from datetime import date

from core.access import filter_for

from tests.conftest import AS_OF, kb_with, make_doc


def visible_docs(kb, persona, as_of=AS_OF):
    return filter_for(kb, kb.users[persona], as_of).doc_keys


def reasons(kb, persona, as_of=AS_OF):
    return dict(filter_for(kb, kb.users[persona], as_of).excluded)


# --- Scope follows the org tree: own unit and every unit above, never siblings or children ---

def test_scope_includes_ancestors(kb):
    linh = visible_docs(kb, "linh")
    assert {"GRP-HR-01@2", "A-LEAVE-01@3", "A-ENG-01@1", "A-PLT-01@1"} <= linh


def test_scope_excludes_other_company(kb):
    assert not any(k.startswith("B-") for k in visible_docs(kb, "linh"))
    assert not any(k.startswith("A-") for k in visible_docs(kb, "minh"))


def test_scope_excludes_child_unit_even_when_permitted(kb):
    # Hoa may SEE A-PLT-01 (acl CO_A/ENG) but it applies only to the Platform team below her.
    assert reasons(kb, "hoa")["A-PLT-01@1"] == "scope"


def test_scope_excludes_sibling_unit(kb):
    # B-REM-01 belongs to CO_B/GAME; Minh is in the sibling CO_B/MKT.
    assert reasons(kb, "minh")["B-REM-01@1"] == "scope"


# --- Permission by unit and by role ---

def test_restricted_salary_only_for_company_a_hr(kb):
    holders = {p for p in kb.users if "A-SAL-01@1" in visible_docs(kb, p)}
    assert holders == {"tuan"}
    assert reasons(kb, "linh")["A-SAL-01@1"] == "acl"


def test_role_restricted_guideline(kb):
    assert "A-ENG-02@1" in visible_docs(kb, "hoa")
    assert reasons(kb, "linh")["A-ENG-02@1"] == "acl"  # right unit, wrong role
    assert reasons(kb, "tuan")["A-ENG-02@1"] == "acl"  # wrong unit


def test_hidden_document_is_only_ever_reported_as_acl(kb):
    # A-LEAVE-01@4 is a draft, but for a Company B persona the reason must not reveal that.
    assert reasons(kb, "minh")["A-LEAVE-01@4"] == "acl"


# --- Status, validity window, supersedes ---

def test_draft_and_archived_are_excluded(kb):
    r = reasons(kb, "linh")
    assert r["A-LEAVE-01@4"] == "status"
    assert r["A-LEAVE-01@2"] == "status"
    assert r["GRP-REM-01@1"] == "status"


def test_future_version_is_upcoming_not_candidate(kb):
    fr = filter_for(kb, kb.users["linh"], AS_OF)
    assert "GRP-REM-01@3" not in fr.doc_keys
    assert [d.key for d in fr.upcoming] == ["GRP-REM-01@3"]


def test_window_moves_with_as_of(kb):
    later = date(2027, 1, 2)
    assert "GRP-REM-01@3" in visible_docs(kb, "linh", later)
    assert reasons(kb, "linh", later)["GRP-REM-01@2"] == "expired"


def test_superseded_version_excluded_even_if_status_not_updated(kb):
    old = make_doc("X-01", 1, status="active", effective_from="2025-01-01")
    new = make_doc("X-01", 2, status="active", effective_from="2026-01-01", supersedes="X-01@1")
    synthetic = kb_with(kb, old, new)
    assert reasons(synthetic, "linh")["X-01@1"] == "superseded"
    assert "X-01@2" in visible_docs(synthetic, "linh")


def test_supersedes_by_future_version_does_not_remove_current(kb):
    current = make_doc("X-01", 1, effective_from="2025-01-01")
    future = make_doc("X-01", 2, effective_from="2027-01-01", supersedes="X-01@1")
    synthetic = kb_with(kb, current, future)
    assert "X-01@1" in visible_docs(synthetic, "linh")


def test_supersedes_by_draft_does_not_remove_current(kb):
    assert "A-LEAVE-01@3" in visible_docs(kb, "linh")  # A-LEAVE-01@4 is a draft superseding @3


# --- applies_to at document and section level ---

def test_document_audience(kb):
    assert reasons(kb, "minh")["B-LEAVE-01@1"] == "audience"  # intern; policy is full_time + probation
    assert reasons(kb, "nam")["B-INT-01@2"] == "audience"  # probation; handbook is intern-only
    assert "B-INT-01@2" in visible_docs(kb, "minh")


def test_section_audience(kb):
    nam = filter_for(kb, kb.users["nam"], AS_OF)
    ids = {s.id for s in nam.sections}
    assert {"B-LEAVE-01@1#1", "B-LEAVE-01@1#4"} <= ids
    assert ("GRP-HR-01@2#2", "section_audience") in nam.excluded_sections  # floor is full_time only

    linh = {s.id for s in filter_for(kb, kb.users["linh"], AS_OF).sections}
    assert "A-LEAVE-01@3#1" in linh
    assert "A-LEAVE-01@3#5" not in linh  # probation-only section


def test_counts_expose_numbers_not_names(kb):
    fr = filter_for(kb, kb.users["minh"], AS_OF)
    counts = fr.counts()
    assert counts["acl"] >= 2
    assert all(isinstance(v, int) for v in counts.values())
