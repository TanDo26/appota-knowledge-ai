from core.models import ABSTAIN, OUT_OF_SCOPE
from core.pipeline import ask, is_personal_data, route_contact

from tests.conftest import AS_OF


def test_topic_vote_picks_annual_days_for_generic_leave_question(kb):
    # Regression from eval run 1: top-1 hit was the unpaid-leave section by a hair.
    for q in ("toi duoc nghi phep bao nhieu ngay", "Quy định nghỉ phép của tôi như thế nào?"):
        r = ask(kb, kb.users["linh"], q, as_of=AS_OF)
        assert r.trace.main_topic == "leave.annual_days", q
        assert [c.section_id for c in r.citations] == ["A-LEAVE-01@3#1"]


def test_personal_data_needs_first_person_and_balance_words():
    assert is_personal_data("Tôi còn bao nhiêu ngày phép?")
    assert is_personal_data("Lương của tôi tháng này là bao nhiêu")
    assert not is_personal_data("Quy định nghỉ phép của tôi như thế nào?")
    assert not is_personal_data("Phép năm còn lại có được chuyển sang năm sau không?")


def test_out_of_scope_never_states_a_balance(kb):
    r = ask(kb, kb.users["linh"], "Tôi còn bao nhiêu ngày phép?", as_of=AS_OF)
    assert r.status == OUT_OF_SCOPE
    assert "hrm.example.com" in r.answer


def test_abstain_text_and_contact_do_not_depend_on_hidden_documents(kb):
    # Minh cannot see the salary policy; the refusal must look exactly like "no data at all".
    hidden = ask(kb, kb.users["minh"], "Khung lương kỹ sư Công ty A là bao nhiêu?", as_of=AS_OF)
    missing = ask(kb, kb.users["minh"], "Lương thử nghiệm sao Hỏa là bao nhiêu?", as_of=AS_OF)
    assert hidden.status == missing.status == ABSTAIN
    assert hidden.answer == missing.answer
    assert hidden.contact == missing.contact == route_contact(kb, kb.users["minh"], "lương")
