from core.access import filter_for
from core.resolver import resolve

from tests.conftest import AS_OF, make_doc

TOPIC = "leave.annual_days"


def sec(body, applies_to=None, topic=TOPIC):
    meta = f"topic: {topic}" + (f" | applies_to: {applies_to}" if applies_to else "")
    return f"## 1. Mục\n<!-- {meta} -->\n{body}\n"


def two_sec(general_body, targeted_body, targeted_for):
    return (f"## 1. Chung\n<!-- topic: {TOPIC} -->\n{general_body}\n"
            f"## 2. Riêng\n<!-- topic: {TOPIC} | applies_to: {targeted_for} -->\n{targeted_body}\n")


def ids(sections):
    return [s.id for s in sections]


# R1 — version

def test_r1_keeps_highest_version_and_warns(kb):
    v1 = make_doc("X-01", 1, sections=sec("10 ngày"))
    v2 = make_doc("X-01", 2, sections=sec("12 ngày"))
    r = resolve(v1.sections + v2.sections, kb, kb.users["linh"])
    assert ids(r.winners) == ["X-01@2#1"]
    assert r.warnings


# R2 — audience inside one document

def test_r2_targeted_section_replaces_general(kb):
    doc = make_doc(sections=two_sec("12 ngày phép", "chưa có phép, nghỉ không lương 3 ngày", "probation"))
    r = resolve(doc.sections, kb, kb.users["nam"])
    assert ids(r.winners) == ["X-01@1#2"]


def test_r2_does_not_touch_other_documents(kb):
    a = make_doc("X-01", sections=two_sec("12 ngày", "3 ngày", "probation"))
    b = make_doc("Y-01", scope_unit="CO_B", acl_units=("CO_B",), sections=sec("12 ngày"))
    r = resolve(a.sections + b.sections, kb, kb.users["nam"])
    assert "X-01@1#1" not in ids(r.winners)
    assert "Y-01@1#1" in ids(r.winners)


def test_r2_on_real_data_for_probation(kb):
    candidates = [s for s in filter_for(kb, kb.users["nam"], AS_OF).sections if s.topic == TOPIC]
    r = resolve(candidates, kb, kb.users["nam"])
    assert ids(r.winners) == ["B-LEAVE-01@1#4"]


# R3 — document type

def test_r3_policy_beats_faq_and_flags_disagreement(kb):
    policy = make_doc("P-01", sections=sec("tối đa 3 ngày, trước 31/03"))
    faq = make_doc("F-01", doc_type="faq", sections=sec("tối đa 5 ngày, trước 31/03"))
    r = resolve(policy.sections + faq.sections, kb, kb.users["linh"])
    assert ids(r.winners) == ["P-01@1#1"]
    assert [d.section.id for d in r.deviations] == ["F-01@1#1"]
    assert r.deviations[0].numbers == {"5"}


def test_r3_agreeing_faq_is_dropped_silently(kb):
    policy = make_doc("P-01", sections=sec("14 ngày, cộng 1 ngày mỗi 5 năm"))
    faq = make_doc("F-01", doc_type="faq", sections=sec("14 ngày, mỗi 5 năm thêm 1 ngày"))
    r = resolve(policy.sections + faq.sections, kb, kb.users["linh"])
    assert ids(r.winners) == ["P-01@1#1"]
    assert r.deviations == []


def test_r3_faq_alone_is_used(kb):
    faq = make_doc("F-01", doc_type="faq", sections=sec("5 ngày"))
    assert ids(resolve(faq.sections, kb, kb.users["linh"]).winners) == ["F-01@1#1"]


# R4 — organisational level

def test_r4_override_more_specific_wins(kb):
    group = make_doc("G-01", scope_unit="GROUP", acl_units=("GROUP",), sections=sec("2 ngày"))
    team = make_doc("T-01", scope_unit="CO_B/GAME", acl_units=("CO_B",), sections=sec("0 ngày"))
    r = resolve(group.sections + team.sections, kb, kb.users["nam"])
    assert ids(r.winners) == ["T-01@1#1"]


def test_r4_parent_floor_child_wins(kb):
    floor = make_doc("G-01", scope_unit="GROUP", acl_units=("GROUP",), precedence="floor", sections=sec("12 ngày"))
    child = make_doc("A-01", scope_unit="CO_A", sections=sec("14 ngày"))
    r = resolve(floor.sections + child.sections, kb, kb.users["linh"])
    assert ids(r.winners) == ["A-01@1#1"]
    assert any("mức sàn" in s for s in r.steps)


def test_r4_supplement_merges_child_first(kb):
    parent = make_doc("E-01", scope_unit="CO_A/ENG", acl_units=("CO_A/ENG",), sections=sec("lịch trực theo tuần"))
    child = make_doc("P-01", scope_unit="CO_A/ENG/PLATFORM", acl_units=("CO_A/ENG",), precedence="supplement",
                     sections=sec("nhóm Platform trực 2 người"))
    r = resolve(parent.sections + child.sections, kb, kb.users["linh"])
    assert ids(r.winners) == ["P-01@1#1", "E-01@1#1"]
    assert not r.conflict


def test_r4_on_real_data_company_beats_group_floor(kb):
    candidates = [s for s in filter_for(kb, kb.users["linh"], AS_OF).sections if s.topic == TOPIC]
    r = resolve(candidates, kb, kb.users["linh"])
    assert ids(r.winners) == ["A-LEAVE-01@3#1"]
    assert r.deviations == []  # FAQ agrees on annual days


# R5 — same level, different documents

def test_r5_different_figures_is_conflict(kb):
    a = make_doc("A-01", doc_type="procedure", sections=sec("nộp trong 30 ngày", topic="expense.claim_deadline"))
    b = make_doc("B-01", doc_type="procedure", sections=sec("nộp trong 15 ngày", topic="expense.claim_deadline"))
    r = resolve(a.sections + b.sections, kb, kb.users["linh"])
    assert r.conflict
    assert set(ids(r.winners)) == {"A-01@1#1", "B-01@1#1"}


def test_r5_same_figures_is_consensus(kb):
    a = make_doc("A-01", doc_type="procedure", sections=sec("nộp trong 30 ngày"))
    b = make_doc("B-01", doc_type="procedure", sections=sec("hạn 30 ngày"))
    r = resolve(a.sections + b.sections, kb, kb.users["linh"])
    assert not r.conflict
    assert len(r.winners) == 2


def test_r5_on_real_data_expense_deadline(kb):
    candidates = [s for s in filter_for(kb, kb.users["linh"], AS_OF).sections if s.topic == "expense.claim_deadline"]
    r = resolve(candidates, kb, kb.users["linh"])
    assert r.conflict
    assert {s.doc.key for s in r.winners} == {"A-EXP-01@2", "A-EXP-02@1"}


def test_single_candidate(kb):
    doc = make_doc(sections=sec("10 ngày"))
    r = resolve(doc.sections, kb, kb.users["linh"])
    assert ids(r.winners) == ["X-01@1#1"] and not r.conflict
