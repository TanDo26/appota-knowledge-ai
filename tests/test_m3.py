"""Mission 3 — pipeline behaviour for the five improvement requirements (R1–R5)."""
from datetime import date

from core.access import filter_for
from core.answer import ABSTAIN_TEXT, content_hash
from core.models import ABSTAIN, ANSWERED, ANSWERED_WITH_NOTE, CLARIFY, CONFLICT, OUT_OF_SCOPE
from core.pipeline import _versions, ask, is_personal_data
from core.resolver import resolve

from tests.conftest import AS_OF, kb_with, make_doc
from tests.test_answer import FakeLLM


def cited(r):
    return [c.section_id for c in r.citations]


# --- R1: versions and validity time ---

def test_archived_version_is_used_inside_its_window(kb):
    keys = filter_for(kb, kb.users["linh"], date(2025, 6, 1)).doc_keys
    assert "A-LEAVE-01@2" in keys and "A-LEAVE-01@3" not in keys
    assert "A-LEAVE-01@2" not in filter_for(kb, kb.users["linh"], AS_OF).doc_keys


def test_archived_without_end_date_is_never_used(kb):
    doc = make_doc("X-01", status="archived", effective_from="2025-01-01", effective_to="null")
    assert "X-01@1" not in filter_for(kb_with(kb, doc), kb.users["linh"], date(2025, 6, 1)).doc_keys


def test_draft_is_never_used_even_for_its_own_dates(kb):
    assert "A-LEAVE-01@4" not in filter_for(kb, kb.users["linh"], date(2027, 6, 1)).doc_keys
    r = ask(kb, kb.users["linh"], "Năm 2027 tôi được bao nhiêu ngày phép?", as_of=AS_OF)
    assert cited(r) == ["A-LEAVE-01@3#1"] and "16" not in r.answer


def test_question_year_sets_the_date_and_tells_what_applies_today(kb):
    r = ask(kb, kb.users["linh"], "Năm 2025 tôi được bao nhiêu ngày phép?", as_of=AS_OF)
    assert r.query.as_of == date(2025, 1, 1) and r.query.base_date == AS_OF
    assert cited(r) == ["A-LEAVE-01@2#1"]
    assert r.answer.startswith("_Theo các tài liệu có hiệu lực ngày 01/01/2025")
    assert any("đang áp dụng hôm nay" in n and "14 ngày" in n for n in r.notes)


def test_no_shift_means_mission2_behaviour(kb):
    r = ask(kb, kb.users["linh"], "Tôi được làm việc từ xa mấy ngày một tuần?", as_of=AS_OF)
    assert not r.query.shifted and r.context_lines == []
    assert cited(r) == ["GRP-REM-01@2#1"] and any(n.startswith("Sắp thay đổi") for n in r.notes)


# --- R2: access by context ---

def test_lookup_never_widens_permission(kb):
    hoa = kb.users["hoa"]
    fr = filter_for(kb, hoa, AS_OF, unit="CO_A/ENG/PLATFORM")
    assert "A-PLT-01@1" in fr.doc_keys
    assert dict(fr.excluded)["A-PLT-02@1"] == "acl"  # Platform-only document stays hidden from the manager
    assert dict(fr.excluded)["A-SAL-01@1"] == "acl"


def test_lookup_answer_says_it_does_not_apply_to_the_asker(kb):
    r = ask(kb, kb.users["hoa"], "Phụ cấp trực on-call của nhóm Platform là bao nhiêu?", as_of=AS_OF)
    assert r.status == ANSWERED and cited(r) == ["A-PLT-01@1#1"]
    assert "không áp dụng cho bạn" in r.answer.split("\n")[0]


def test_other_company_refusal_is_the_generic_one(kb):
    minh = kb.users["minh"]
    r = ask(kb, minh, "Nhân viên chính thức Công ty A được mấy ngày phép năm?", as_of=AS_OF)
    assert r.status == ABSTAIN and r.answer == ABSTAIN_TEXT and r.citations == []
    assert r.context_lines  # the reason is shown beside the answer, from the question's own words


def test_probation_lookup_does_not_flag_the_full_time_faq(kb):
    r = ask(kb, kb.users["tuan"], "Nhân sự thử việc ở Công ty A có được nghỉ phép năm không?", as_of=AS_OF)
    assert cited(r) == ["A-LEAVE-01@3#5"] and r.flags == [] and r.notes == []


# --- R3: conflicts across levels ---

def test_child_below_parent_floor_is_a_conflict(kb):
    floor = make_doc("G-01", scope_unit="GROUP", acl_units=("GROUP",), precedence="floor",
                     sections="## 1. Sàn\n<!-- topic: t -->\nTối thiểu 12 ngày.\n")
    child = make_doc("C-01", scope_unit="CO_A", sections="## 1. Phép\n<!-- topic: t -->\nĐược 10 ngày.\n")
    res = resolve(floor.sections + child.sections, kb, kb.users["linh"])
    assert res.conflict and {s.id for s in res.winners} == {"G-01@1#1", "C-01@1#1"}
    assert res.conflict_reasons


def test_child_at_or_above_floor_is_not_a_conflict(kb):
    r = ask(kb, kb.users["minh"], "Nhân viên chính thức được mấy ngày phép năm?", as_of=AS_OF)
    assert r.status == ANSWERED and cited(r) == ["B-LEAVE-01@1#1"]  # 12 = floor 12


def test_floor_breach_only_for_the_audience_the_floor_protects(kb):
    quan = ask(kb, kb.users["quan"], "Tôi được bao nhiêu ngày phép năm?", as_of=AS_OF)
    nam = ask(kb, kb.users["nam"], "Tôi được bao nhiêu ngày phép năm?", as_of=AS_OF)
    assert quan.status == CONFLICT and {f.doc_key for f in quan.flags} == {"B-GAME-01@1", "GRP-HR-01@2"}
    assert "Lý do:" in quan.answer
    assert nam.status == ANSWERED and cited(nam) == ["B-LEAVE-01@1#4"]


# --- R4: not enough evidence ---

def test_thin_match_asks_instead_of_answering(kb):
    r = ask(kb, kb.users["linh"], "Tuần này tôi không lên công ty vài ngày được không?", as_of=AS_OF)
    assert r.status == CLARIFY and r.citations == [] and r.context_sections == []
    assert r.evidence["matched"] == ["lên", "ngày"] and r.evidence["missing"] == ["tuần"]
    assert 1 <= len(r.candidates) <= 3 and r.contact


def test_clarify_never_calls_the_llm(kb):
    llm = FakeLLM({"answer": "x [S1]", "citations": ["S1"], "insufficient": False})
    r = ask(kb, kb.users["linh"], "Tuần này tôi không lên công ty vài ngày được không?", as_of=AS_OF,
            mode="gemini", llm=llm)
    assert r.status == CLARIFY and llm.prompts == []


def test_child_is_not_mistaken_for_remaining_balance():
    assert not is_personal_data("Con ốm thì tôi được nghỉ chăm con mấy ngày?")
    assert is_personal_data("Tôi còn mấy ngày phép?")
    assert is_personal_data("toi con may ngay phep")  # unaccented: folded check as in Mission 2


def test_every_answer_shows_which_question_words_the_source_contains(kb):
    r = ask(kb, kb.users["linh"], "Hạn nộp hồ sơ hoàn ứng là bao lâu?", as_of=AS_OF)
    assert r.evidence == {"matched": ["hạn nộp hồ sơ hoàn ứng"], "missing": []}
    synonym = ask(kb, kb.users["linh"], "Muốn làm ở nhà vài hôm thì có được không?", as_of=AS_OF)
    assert synonym.evidence == {"matched": ["làm việc từ xa"], "missing": ["hôm"]}  # document's spelling


# --- R5: verification ---

def test_citations_carry_verbatim_text_and_fingerprint(kb):
    r = ask(kb, kb.users["linh"], "Phép năm chưa dùng có được chuyển sang năm sau không?", as_of=AS_OF)
    section = next(s for s in kb.sections if s.id == "A-LEAVE-01@3#2")
    c = r.citations[0]
    assert c.body == section.body and c.content_hash == content_hash(section.body)


def test_considered_sources_and_version_history(kb):
    r = ask(kb, kb.users["linh"], "Phép năm chưa dùng có được chuyển sang năm sau không?", as_of=AS_OF)
    considered = {c["section"]: c["reason"] for c in r.considered}
    assert "FAQ" in considered["A-FAQ-01@1#2"] and "gắn cờ" in considered["A-FAQ-01@1#2"]
    versions = {v["doc_key"]: v["label"] for v in r.versions}
    assert versions["A-LEAVE-01@3"] == "dùng trong câu trả lời"
    assert versions["A-LEAVE-01@2"] == "hết hiệu lực"
    assert versions["A-LEAVE-01@4"].startswith("bản nháp")


def test_version_history_lists_only_versions_the_asker_may_see(kb):
    hidden = make_doc("X-01", 1, effective_from="2025-01-01", effective_to="2025-12-31", status="archived",
                      acl_units=("CO_A/HR",))
    shown = make_doc("X-01", 2, effective_from="2026-01-01", supersedes="X-01@1")
    versions = _versions(kb_with(kb, hidden, shown), kb.users["linh"], shown.sections, AS_OF)
    assert [v["doc_key"] for v in versions] == ["X-01@2"]


# --- Gemini path ---

def test_gemini_answer_keeps_the_lookup_line(kb):
    llm = FakeLLM({"answer": "Bạn được 300.000 đồng mỗi ngày trực [S1].", "citations": ["S1"], "insufficient": False})
    r = ask(kb, kb.users["hoa"], "Phụ cấp trực on-call của nhóm Platform là bao nhiêu?", as_of=AS_OF,
            mode="gemini", llm=llm)
    assert r.trace.answer_mode == "gemini"
    assert r.answer.startswith("_Đây là quy định cho") and "không áp dụng cho bạn" in r.answer
    assert "<context>" in llm.prompts[0][1]


def test_gemini_may_repeat_the_year_asked_about(kb):
    llm = FakeLLM({"answer": "Năm 2025, bạn được 13 ngày phép năm [S1].", "citations": ["S1"], "insufficient": False})
    r = ask(kb, kb.users["linh"], "Năm 2025 tôi được bao nhiêu ngày phép?", as_of=AS_OF, mode="gemini", llm=llm)
    assert r.fallback is None, r.fallback
    assert r.status == ANSWERED_WITH_NOTE


def test_gemini_still_cannot_state_the_current_figure_for_a_past_year(kb):
    llm = FakeLLM({"answer": "Năm 2025, bạn được 14 ngày phép năm [S1].", "citations": ["S1"], "insufficient": False})
    r = ask(kb, kb.users["linh"], "Năm 2025 tôi được bao nhiêu ngày phép?", as_of=AS_OF, mode="gemini", llm=llm)
    assert r.fallback and "Kiểm 2" in r.fallback and "14" in r.fallback


def test_out_of_scope_unchanged(kb):
    r = ask(kb, kb.users["linh"], "Tôi còn bao nhiêu ngày phép?", as_of=AS_OF)
    assert r.status == OUT_OF_SCOPE and cited(r) == ["A-LEAVE-01@3#1"]
