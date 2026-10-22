"""Change Request B2 — same question, but one asker may not see the document that holds the full answer."""
from core.lint import lint
from core.pipeline import ask
from eval.run_eval import kb_without, public_diff

from tests.conftest import AS_OF, kb_with, make_doc

RAISE = "Khi nào được xét tăng lương và mức tăng tối đa là bao nhiêu?"
SECTION = "## 1. Phụ cấp thử nghiệm\n<!-- topic: test.allowance -->\nPhụ cấp thử nghiệm là {} đồng mỗi tháng.\n"
ALLOWANCE = "Phụ cấp thử nghiệm mỗi tháng là bao nhiêu?"


def cited(r):
    return [c.section_id for c in r.citations]


def gaps(kb):
    return {w.doc_key for w in lint(kb) if w.code == "visibility_gap"}


def hidden_doc(doc_id="X-01", version=1, **kw):
    return make_doc(doc_id, version, acl_units=("CO_A/HR",), sensitivity="restricted", **kw)


def test_full_answer_for_hr_partial_answer_for_others(kb):
    tuan = ask(kb, kb.users["tuan"], RAISE, as_of=AS_OF)
    linh = ask(kb, kb.users["linh"], RAISE, as_of=AS_OF)
    assert cited(tuan) == ["A-SAL-01@1#2"] and "15%" in tuan.answer
    assert cited(linh) == ["A-FAQ-02@1#1"] and "15%" not in linh.answer


def test_hidden_document_changes_nothing_the_others_see(kb):
    linh = kb.users["linh"]
    full = ask(kb, linh, RAISE, as_of=AS_OF)
    assert public_diff(full, ask(kb_without(kb, ["A-SAL-01@1"]), linh, RAISE, as_of=AS_OF), 1) == []


def test_hidden_new_version_does_not_retire_the_version_others_see(kb):
    """A restricted v2 replacing a public v1 must not make v1 disappear for people who cannot see v2:
    their answer would change because of a document they cannot see, which reveals that it exists."""
    v1 = make_doc("X-01", 1, sections=SECTION.format("500.000"))
    v2 = hidden_doc("X-01", 2, supersedes="X-01@1", sections=SECTION.format("700.000"))
    full, without = kb_with(kb, v1, v2), kb_with(kb, v1)
    linh = kb.users["linh"]
    assert public_diff(ask(full, linh, ALLOWANCE, as_of=AS_OF), ask(without, linh, ALLOWANCE, as_of=AS_OF), 1) == []
    assert cited(ask(full, kb.users["tuan"], ALLOWANCE, as_of=AS_OF)) == ["X-01@2#1"]


# --- what the system cannot tell the asker is reported to the owners, at publish time ---

def test_visible_source_stating_other_figures_than_a_hidden_one_is_reported(kb):
    faq = make_doc("X-02", doc_type="faq", sections=SECTION.format("500.000"))
    assert gaps(kb_with(kb, hidden_doc(sections=SECTION.format("700.000")), faq)) == {"X-02@1"}


def test_visible_partial_answer_is_not_a_gap(kb):
    faq = make_doc("X-02", doc_type="faq",
                   sections="## 1. Phụ cấp\n<!-- topic: test.allowance -->\nMức phụ cấp do Phòng Nhân sự thông báo riêng.\n")
    assert gaps(kb_with(kb, hidden_doc(sections=SECTION.format("700.000")), faq)) == set()


def test_no_gap_when_everyone_it_applies_to_can_see_it(kb):
    hr_only = make_doc("X-01", scope_unit="CO_A/HR", sections=SECTION.format("700.000"))
    general = make_doc("X-02", sections=SECTION.format("500.000"))
    assert gaps(kb_with(kb, hr_only, general)) == set()


def test_new_version_seen_by_fewer_people_is_reported(kb):
    v1 = make_doc("X-01", 1, sections=SECTION.format("500.000"))
    v2 = hidden_doc("X-01", 2, supersedes="X-01@1", sections=SECTION.format("700.000"))
    assert "X-01@1" in gaps(kb_with(kb, v1, v2))
