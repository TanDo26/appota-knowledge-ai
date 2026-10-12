from core.lint import lint

from tests.conftest import kb_with, make_doc


def codes(kb):
    return {(w.code, w.doc_key) for w in lint(kb)}


def test_real_dataset_has_only_expected_warnings(kb):
    # A-EXP-01@2 names a v1 that was purged from the store; GRP-ANN-01 carries planted injections.
    assert codes(kb) == {("supersedes_missing", "A-EXP-01@2"), ("injection", "GRP-ANN-01@1")}


def test_unknown_scope_unit(kb):
    assert ("unknown_unit", "X-01@1") in codes(kb_with(kb, make_doc(scope_unit="CO_Z", acl_units=("CO_A",))))


def test_restricted_without_acl(kb):
    assert ("restricted_without_acl", "X-01@1") in codes(kb_with(kb, make_doc(sensitivity="restricted", acl_units=())))


def test_section_without_topic(kb):
    doc = make_doc(sections="## 1. Không có chủ đề\nNội dung.\n")
    assert ("section_without_topic", "X-01@1") in codes(kb_with(kb, doc))


def test_invalid_enum_value(kb):
    assert ("invalid_value", "X-01@1") in codes(kb_with(kb, make_doc(doc_type="memo")))


def test_missing_effective_from_on_active(kb):
    assert ("missing_field", "X-01@1") in codes(kb_with(kb, make_doc(effective_from="null")))


def test_overlapping_versions(kb):
    a = make_doc("X-01", 1, effective_from="2026-01-01", effective_to="2026-12-31")
    b = make_doc("X-01", 2, effective_from="2026-06-01")
    assert ("overlapping_versions", "X-01@2") in codes(kb_with(kb, a, b))


def test_adjacent_versions_do_not_overlap(kb):
    a = make_doc("X-01", 1, effective_from="2026-01-01", effective_to="2026-06-30")
    b = make_doc("X-01", 2, effective_from="2026-07-01")
    assert not any(c == "overlapping_versions" for c, _ in codes(kb_with(kb, a, b)))


def test_child_below_parent_floor(kb):
    floor = make_doc("P-01", scope_unit="GROUP", precedence="floor",
                     sections="## 1. Sàn\n<!-- topic: leave.annual_days -->\nTối thiểu 12 ngày.\n")
    child = make_doc("C-01", scope_unit="CO_A",
                     sections="## 1. Phép\n<!-- topic: leave.annual_days -->\nĐược 10 ngày.\n")
    assert ("below_floor", "C-01@1") in codes(kb_with(kb, floor, child))


def test_floor_ignores_disjoint_audience(kb):
    floor = make_doc("P-01", scope_unit="GROUP", precedence="floor",
                     sections="## 1. Sàn\n<!-- topic: leave.annual_days | applies_to: full_time -->\nTối thiểu 12 ngày.\n")
    child = make_doc("C-01", scope_unit="CO_A",
                     sections="## 1. Thử việc\n<!-- topic: leave.annual_days | applies_to: probation -->\nNghỉ tối đa 2 ngày.\n")
    assert not any(c == "below_floor" for c, _ in codes(kb_with(kb, floor, child)))
