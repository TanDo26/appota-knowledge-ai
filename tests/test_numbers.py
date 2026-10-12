from core.numbers import extract_numbers, first_number


def test_dates_are_single_tokens():
    assert extract_numbers("tối đa 3 ngày, dùng trước ngày 31/03") == {"3", "31/3"}
    assert extract_numbers("Từ ngày 01/11/2026") == {"1/11/2026"}


def test_thousand_separators_and_decimals():
    assert extract_numbers("300.000 đồng và 1.200.000 đồng") == {"300000", "1200000"}
    assert extract_numbers("4,5 giờ") == {"4.5"}


def test_times_and_codes():
    assert extract_numbers("trước 17:00, sự cố P1 trong 15 phút, 20%") == {"17:00", "15", "20"}


def test_first_number_skips_dates():
    assert first_number("Từ 01/01/2027 được tối thiểu 12 ngày") == 12
    assert first_number("không có số") is None
