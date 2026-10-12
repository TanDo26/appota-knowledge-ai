from core.text import doc_terms, fold, query_terms, rewrite_query


def test_fold_strips_diacritics_and_maps_d_stroke():
    assert fold("Đăng ký nghỉ phép") == "dang ky nghi phep"
    assert fold("ĐƯỜNG đi") == "duong di"
    assert fold("Hỗ trợ học phí") == "ho tro hoc phi"


def test_unaccented_question_gives_same_terms():
    assert query_terms("toi duoc nghi phep bao nhieu ngay") == query_terms("Tôi được nghỉ phép bao nhiêu ngày?")


def test_bigrams_only_between_adjacent_content_syllables():
    terms = doc_terms("Khung lương kỹ sư")
    assert {"khung_luong", "luong_ky", "ky_su"} <= set(terms)
    assert "toi_duoc" not in query_terms("tôi được nghỉ phép")


def test_stopwords_removed_from_questions():
    assert query_terms("Tôi được nghỉ phép không?") == ["nghi", "phep", "nghi_phep"]


def test_folding_collisions_kept_as_content():
    terms = set(doc_terms("chi phí, hồ sơ, chứng từ, báo trước"))
    assert {"chi_phi", "ho_so", "chung_tu", "bao_truoc"} <= terms


def test_question_phrase_removal_does_not_join_neighbours():
    terms = query_terms("nghỉ phép bao nhiêu ngày")
    assert "phep_ngay" not in terms
    assert "bao" not in terms


def test_generic_policy_words_removed_from_questions():
    assert query_terms("Quy định nghỉ phép") == query_terms("nghỉ phép")


def test_synonyms_map_to_document_wording():
    assert "tu_xa" in query_terms("Tôi muốn WFH")
    assert "tu_xa" in query_terms("làm ở nhà được không")
    assert rewrite_query("phép chưa dùng") == "phep chua su dung"
    assert rewrite_query("đã sử dụng") == "da su dung"  # no double "su su"
