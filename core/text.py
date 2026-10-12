"""Vietnamese text normalisation, tokenisation and a small synonym table.

Terms are diacritic-folded syllables (so "nghi phep" matches "nghỉ phép") plus adjacent syllable
bigrams, which restore most of the meaning folding loses ("khung luong" vs a stray "luong").
Stopwords, query stop-phrases and synonyms were written before the first evaluation run and are
not tuned to individual test cases (see docs/DECISIONS.md).
"""
from __future__ import annotations

import re
import unicodedata

_TOKEN = re.compile(r"[a-z0-9]+")


def fold(text: str) -> str:
    """Lowercase and strip Vietnamese diacritics. `đ` has no Unicode decomposition, so map it by hand."""
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# Function words and question words, in folded form. Folding merges some content words into these
# (e.g. "đăng" and "đang" both become "dang"); that cost is accepted for a small corpus. Words whose
# folded form collides with frequent content words are left out ("họ"/"hồ sơ", "chị"/"chi phí",
# "bao"/"báo", "chúng"/"chứng từ"); question phrases containing them are removed below instead.
STOPWORDS = frozenset("""
    toi minh em anh ban ta
    la co khong duoc cua cho va thi the nao nhu gi nhieu may vai mot cac nhung
    nay do o ve voi khi neu de se da dang can phai hay hoac muon nhe a vay sao ai dau chu
    nhi oi ha roi cung con lai bi vi ma nen nua rat biet xem hoi giup vui
""".split())

# Removed from questions only (applied after synonyms):
# - question phrases whose syllables are not all stopwords;
# - generic words that say nothing about WHICH rule is asked for.
QUERY_STOP_PHRASES = (
    "bao nhieu", "bao lau", "bao gio", "ra sao", "lam sao",
    "quy dinh", "chinh sach", "che do", "thong tin", "huong dan", "quy trinh", "cong ty", "tap doan",
)

# Alias -> wording used in the documents. Applied to questions only, on folded text.
SYNONYMS: tuple[tuple[str, str], ...] = (
    (r"lam (viec )?(o|tai) nha", "lam viec tu xa"),
    (r"work from home|wfh|lam remote|remote", "lam viec tu xa"),
    (r"nhan vien", "nhan su"),
    (r"thu nhap", "luong"),
    (r"hoan tien|hoan chi phi|thanh toan chi phi", "hoan ung"),
    (r"intern", "thuc tap sinh"),
    (r"probation", "thu viec"),
    (r"oncall", "on call"),
    (r"check in", "cham cong"),
    (r"engineer", "ky su"),
    (r"kpi|danh gia nang luc", "danh gia hieu suat"),
    (r"(?<!su )dung", "su dung"),
)
_SYNONYMS = tuple((re.compile(rf"\b(?:{alias})\b"), canonical) for alias, canonical in SYNONYMS)
_STOP_PHRASES = tuple(re.compile(rf"\b{p}\b") for p in QUERY_STOP_PHRASES)


def syllables(text: str) -> list[str]:
    return _TOKEN.findall(fold(text))


def _content(token: str) -> bool:
    return len(token) > 1 and token not in STOPWORDS


def terms_from_syllables(syls: list[str]) -> list[str]:
    """Content unigrams plus bigrams of adjacent content syllables ("nghi_phep")."""
    out = [s for s in syls if _content(s)]
    out += [f"{a}_{b}" for a, b in zip(syls, syls[1:]) if _content(a) and _content(b)]
    return out


def doc_terms(text: str) -> list[str]:
    return terms_from_syllables(syllables(text))


def rewrite_query(question: str) -> str:
    """Folded question with synonyms mapped to document wording and generic phrases removed."""
    q = " ".join(syllables(question))
    for pattern, canonical in _SYNONYMS:
        q = pattern.sub(canonical, q)
    for pattern in _STOP_PHRASES:
        q = pattern.sub(" | ", q)  # "|" is not a content token, so no bigram forms across the gap
    return " ".join(q.split())


def query_terms(question: str) -> list[str]:
    return terms_from_syllables(rewrite_query(question).split())
