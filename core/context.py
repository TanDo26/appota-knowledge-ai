"""Query context (Mission 3): WHEN and ABOUT WHOM a question asks, kept apart from WHO asks it.

- Time. An explicit date ("01/01/2027"), month ("tháng 3 năm 2025") or year ("năm 2025") moves the date
  documents are evaluated at. The date or year is then removed from the retrieval query: it is context,
  not a keyword (Mission 2 counted "2025" as an unknown word and refused). Relative words ("năm sau",
  "năm trước") are NOT read as time: in this corpus they are usually what the question is about
  ("phép chuyển sang năm sau"), not when.
- Subject. A unit alias from org.yaml ("nhóm Platform") or a contract-type phrase ("thực tập sinh",
  "nhân sự thử việc") makes the answer about that unit / contract type. Permission never moves: the
  access filter keeps using the asker for ACL, so a lookup can only narrow, never widen, what is seen.
  A unit of another company is not looked up at all (see `other_company`).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from core.loader import KnowledgeBase
from core.models import QueryContext, User
from core.text import fold

# Matched on folded text. Each pattern may swallow a leading preposition and time word so that the
# words around a removed date do not form a bigram across the gap.
_LEAD = r"(?:\b(?:ke tu|tu|vao|trong|den|cho|ap dung)\s+)?"
_FULL_DATE = re.compile(_LEAD + r"(?:\bngay\s+)?(?<![\d/])(\d{1,2})/(\d{1,2})/(\d{4})(?![\d/])")
_WORDY_DATE = re.compile(_LEAD + r"\bngay (\d{1,2}) thang (\d{1,2}) nam (\d{4})\b")
_MONTH_YEAR = re.compile(_LEAD + r"(?:\bthang\s+)?(?<![\d/])(\d{1,2})(?:/| nam )(\d{4})(?![\d/])")
_YEAR = re.compile(_LEAD + r"(?:\bnam\s+)?(?<![\d/.,])((?:19|20)\d{2})(?![\d/.,])")

# Contract types named in a question. "chính thức" only counts next to a word for staff, so
# "khi nào ký hợp đồng chính thức" (a probation question) is not read as a question about full-time staff.
EMPLOYMENT_PATTERNS = {
    "intern": re.compile(r"\b(thuc tap sinh|thuc tap|intern)\b"),
    "probation": re.compile(r"\b(thu viec|probation)\b"),
    "full_time": re.compile(r"\b(nhan su|nhan vien|lao dong|nguoi) chinh thuc\b|\bfull ?time\b"),
}


@dataclass
class TimeRef:
    as_of: date
    phrase: str | None
    ambiguous: bool
    retrieval_text: str  # folded question without the time expressions


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _original(question: str, folded: str, start: int, end: int) -> str:
    """The question's own wording for a span found in its folded form (same length after NFC)."""
    nfc = _nfc(question)
    return nfc[start:end].strip() if len(nfc) == len(folded) else folded[start:end].strip()


def _safe_date(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def parse_time(question: str, base: date) -> TimeRef:
    folded = fold(_nfc(question))
    spans: list[tuple[int, int, date]] = []
    taken = [False] * len(folded)

    def scan(pattern: re.Pattern, make) -> None:
        for m in pattern.finditer(folded):
            if any(taken[m.start():m.end()]):
                continue
            d = make(m)
            if d is None:
                continue
            spans.append((m.start(), m.end(), d))
            for i in range(m.start(), m.end()):
                taken[i] = True

    scan(_FULL_DATE, lambda m: _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
    scan(_WORDY_DATE, lambda m: _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
    scan(_MONTH_YEAR, lambda m: base if (int(m.group(2)), int(m.group(1))) == (base.year, base.month)
         else _safe_date(int(m.group(2)), int(m.group(1)), 1))
    scan(_YEAR, lambda m: base if int(m.group(1)) == base.year else date(int(m.group(1)), 1, 1))

    # "|" keeps the words on both sides of a removed date from forming a bigram.
    rest = "".join(" | " if taken[i] and (i == 0 or not taken[i - 1]) else ("" if taken[i] else c)
                   for i, c in enumerate(folded))
    if not spans:
        return TimeRef(base, None, False, rest)
    spans.sort()
    phrases = [_original(question, folded, s, e) for s, e, _ in spans]
    dates = {d for _, _, d in spans}
    if len(dates) > 1:
        return TimeRef(base, ", ".join(phrases), True, rest)
    return TimeRef(dates.pop(), ", ".join(phrases), False, rest)


def company_of(kb: KnowledgeBase, unit_id: str) -> str:
    chain = kb.unit_chain(unit_id)
    return chain[1].id if len(chain) > 1 else chain[0].id


def _alias_pattern(alias: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(fold(alias))}\b")


def mentioned_units(kb: KnowledgeBase, question: str) -> list[tuple[str, str]]:
    """(unit id, wording) for every unit whose alias appears in the question."""
    folded = fold(_nfc(question))
    found = []
    for unit in kb.org.values():
        for alias in sorted(unit.aliases, key=len, reverse=True):
            m = _alias_pattern(alias).search(folded)
            if m:
                found.append((unit.id, _original(question, folded, m.start(), m.end())))
                break
    return found


def mentioned_employment(question: str) -> list[tuple[str, str]]:
    folded = fold(_nfc(question))
    out = []
    for etype, pattern in EMPLOYMENT_PATTERNS.items():
        m = pattern.search(folded)
        if m:
            out.append((etype, _original(question, folded, m.start(), m.end())))
    return out


def build_query(kb: KnowledgeBase, user: User, question: str, base: date) -> tuple[QueryContext, str, list[str]]:
    """Returns (context, retrieval text, trace lines)."""
    steps: list[str] = []
    time = parse_time(question, base)
    if time.ambiguous:
        steps.append(f"Thời điểm: câu hỏi nhắc nhiều mốc ({time.phrase}) → tính theo ngày tra cứu {base:%d/%m/%Y}.")
    elif time.phrase and time.as_of != base:
        steps.append(f"Thời điểm: “{time.phrase}” → tính theo tài liệu có hiệu lực ngày {time.as_of:%d/%m/%Y} "
                     f"(ngày tra cứu {base:%d/%m/%Y}).")
    elif time.phrase:
        steps.append(f"Thời điểm: “{time.phrase}” trùng kỳ hiện tại → tính theo ngày tra cứu {base:%d/%m/%Y}.")

    phrases: list[str] = []
    unit = user.unit
    other_company = False
    own_chain = {u.id for u in kb.unit_chain(user.unit)}
    named = [(u, w) for u, w in mentioned_units(kb, question) if u not in own_chain]
    if named:
        ids = {u for u, _ in named}
        # Several units on one branch ("nhóm Platform của phòng Kỹ thuật") name the deepest one.
        deepest = max(ids, key=lambda u: len(kb.unit_chain(u)))
        if all(u in {x.id for x in kb.unit_chain(deepest)} for u in ids):
            phrases += [w for _, w in named]
            if company_of(kb, deepest) != company_of(kb, user.unit):
                other_company = True
                steps.append(f"Đối tượng: “{', '.join(phrases)}” thuộc công ty khác → không tra cứu.")
            else:
                unit = deepest
                steps.append(f"Đối tượng: “{', '.join(phrases)}” → xét phạm vi theo đơn vị {kb.unit_label(unit)}.")
        else:
            steps.append(f"Đối tượng: câu hỏi nhắc nhiều đơn vị khác nhánh ({', '.join(w for _, w in named)}) "
                         "→ giữ đơn vị của người hỏi.")

    employment = user.employment_type
    types = mentioned_employment(question)
    if types and user.employment_type not in {t for t, _ in types}:
        if len({t for t, _ in types}) == 1:
            employment = types[0][0]
            phrases.append(types[0][1])
            steps.append(f"Đối tượng: “{types[0][1]}” → xét theo loại hợp đồng {employment}.")
        else:
            steps.append("Đối tượng: câu hỏi nhắc nhiều loại hợp đồng → giữ loại hợp đồng của người hỏi.")

    context = QueryContext(
        as_of=time.as_of,
        base_date=base,
        time_phrase=time.phrase,
        time_ambiguous=time.ambiguous,
        subject_unit=unit,
        subject_employment=employment,
        lookup=(unit != user.unit or employment != user.employment_type) and not other_company,
        subject_phrases=tuple(phrases),
        other_company=other_company,
    )
    return context, time.retrieval_text, steps
