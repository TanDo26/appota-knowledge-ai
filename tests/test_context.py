"""Mission 3 — reading WHEN and ABOUT WHOM a question asks (core/context.py)."""
from datetime import date

from core.context import build_query, parse_time
from core.text import query_terms

from tests.conftest import AS_OF


# --- time ---

def test_year_moves_lookup_date_to_its_first_day():
    t = parse_time("Năm 2025 tôi được bao nhiêu ngày phép?", AS_OF)
    assert t.as_of == date(2025, 1, 1) and t.phrase == "Năm 2025" and not t.ambiguous


def test_full_and_wordy_dates():
    assert parse_time("Từ ngày 01/01/2027 được làm từ xa mấy ngày?", AS_OF).as_of == date(2027, 1, 1)
    assert parse_time("ngày 5 tháng 3 năm 2025 thì sao", AS_OF).as_of == date(2025, 3, 5)
    assert parse_time("tháng 3 năm 2025", AS_OF).as_of == date(2025, 3, 1)
    assert parse_time("trong 03/2025", AS_OF).as_of == date(2025, 3, 1)


def test_current_year_does_not_shift():
    t = parse_time("Năm 2026 tôi được bao nhiêu ngày phép?", AS_OF)
    assert t.as_of == AS_OF and t.phrase == "Năm 2026"


def test_several_dates_are_ambiguous_and_do_not_shift():
    t = parse_time("Phép năm 2025 chưa dùng có chuyển sang 2027 được không?", AS_OF)
    assert t.ambiguous and t.as_of == AS_OF


def test_figures_and_day_month_without_year_are_not_time():
    for q in ("Phụ cấp 300.000 đồng mỗi ngày đúng không?", "Phép chuyển sang phải dùng trước 31/03 à?",
              "Nghỉ 5 ngày liên tục cần báo trước bao lâu?", "Phép chuyển sang năm sau được không?"):
        assert parse_time(q, AS_OF).phrase is None, q


def test_invalid_date_is_ignored():
    assert parse_time("ngày 31/02/2027", AS_OF).phrase is None


def test_date_is_removed_from_retrieval_without_joining_neighbours():
    t = parse_time("Từ ngày 01/01/2027 tôi được làm việc từ xa", AS_OF)
    terms = query_terms(t.retrieval_text)
    assert not any(c.isdigit() for term in terms for c in term)
    assert "tu_xa" in terms and "tu_ngay" not in terms


# --- subject ---

def q(kb, persona, question):
    return build_query(kb, kb.users[persona], question, AS_OF)[0]


def test_own_or_ancestor_unit_is_not_a_lookup(kb):
    for persona, question in (("linh", "Nhóm Platform được phụ cấp trực bao nhiêu?"),
                              ("linh", "Phòng Kỹ thuật trực on-call thế nào?"),
                              ("tuan", "Khung lương kỹ sư Công ty A là bao nhiêu?")):
        assert not q(kb, persona, question).lookup, question


def test_child_unit_in_same_company_is_a_lookup(kb):
    ctx = q(kb, "hoa", "Phụ cấp trực on-call của nhóm Platform là bao nhiêu?")
    assert ctx.lookup and ctx.subject_unit == "CO_A/ENG/PLATFORM" and ctx.subject_employment == "full_time"


def test_unit_of_another_company_is_not_looked_up(kb):
    ctx = q(kb, "minh", "Nhân viên chính thức Công ty A được mấy ngày phép năm?")
    assert ctx.other_company and not ctx.lookup


def test_contract_type_lookup(kb):
    ctx = q(kb, "tuan", "Nhân sự thử việc ở Công ty A có được nghỉ phép năm không?")
    assert ctx.lookup and ctx.subject_employment == "probation" and ctx.subject_unit == "CO_A/HR"
    assert q(kb, "minh", "Nhân viên chính thức được mấy ngày phép năm?").subject_employment == "full_time"


def test_own_contract_type_and_contract_words_are_not_lookups(kb):
    assert not q(kb, "nam", "Tôi đang thử việc thì có được nghỉ phép không?").lookup
    # "hợp đồng chính thức" is a probation question, not a question about full-time staff
    assert not q(kb, "nam", "Khi nào tôi được ký hợp đồng chính thức?").lookup
    # the asker's own type among several named types: answer for the asker
    assert not q(kb, "nam", "Thử việc và thực tập khác nhau thế nào?").lookup
