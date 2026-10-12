from core.access import filter_for
from core.retrieval import BM25Index, search

from tests.conftest import AS_OF, make_doc


def sections_for(kb, persona):
    return filter_for(kb, kb.users[persona], AS_OF).sections


def test_ranks_the_relevant_section_first(kb):
    hits = search("Hạn nộp hồ sơ hoàn ứng", sections_for(kb, "linh"))
    assert hits[0].section.topic == "expense.claim_deadline"


def test_searches_only_the_given_sections(kb):
    hits = search("Khung lương kỹ sư", sections_for(kb, "minh"))
    assert all(not h.section.doc.id.startswith("A-") for h in hits)


def test_coverage_is_one_when_every_term_matches():
    doc = make_doc(sections="## 1. Nghỉ phép\n<!-- topic: t -->\nNghỉ phép năm 12 ngày.\n"
                            "## 2. Khác\n<!-- topic: u -->\nVăn phòng phẩm.\n")
    hits = search("nghỉ phép", doc.sections)
    assert hits[0].coverage == 1.0


def test_unknown_terms_lower_coverage():
    doc = make_doc(sections="## 1. Nghỉ phép\n<!-- topic: t -->\nNghỉ phép năm 12 ngày.\n"
                            "## 2. Khác\n<!-- topic: u -->\nVăn phòng phẩm.\n")
    known = search("nghỉ phép", doc.sections)[0].coverage
    unknown = search("nghỉ phép học phí MBA", doc.sections)[0].coverage
    assert unknown < known and unknown < 0.5


def test_idf_uses_only_visible_sections(kb):
    # A term that exists only in a hidden document is "unknown" to the asker.
    index = BM25Index(sections_for(kb, "minh"))
    assert index.df.get("khung_luong", 0) == 0
    assert BM25Index(sections_for(kb, "tuan")).df.get("khung_luong", 0) > 0


def test_empty_question_or_corpus():
    assert search("là gì", make_doc().sections) == []
    assert search("nghỉ phép", []) == []
