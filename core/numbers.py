"""Extract the figures a section states, for conflict detection, the floor lint and the LLM post-check."""
from __future__ import annotations

import re

# Dates first (31/03, 01/01/2027) so their parts are not read as separate numbers.
_DATE = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?![\d/])")
_TIME = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
# 300.000 / 1.200.000 / 4,5 / 15
_NUMBER = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?)(?![\w])")


def _norm_number(raw: str) -> str:
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw):
        raw = raw.replace(".", "")
    raw = raw.replace(",", ".")
    value = float(raw)
    return str(int(value)) if value.is_integer() else str(value)


def extract_numbers(text: str) -> set[str]:
    """Normalised figures in `text`: '31/3' for dates, '17:00' for times, '300000' for '300.000', '4.5' for '4,5'."""
    found: set[str] = set()

    def take_date(m: re.Match) -> str:
        day, month, year = m.group(1), m.group(2), m.group(3)
        found.add(f"{int(day)}/{int(month)}" + (f"/{int(year)}" if year else ""))
        return " "

    def take_time(m: re.Match) -> str:
        found.add(f"{int(m.group(1))}:{m.group(2)}")
        return " "

    rest = _TIME.sub(take_time, _DATE.sub(take_date, text))
    for m in _NUMBER.finditer(rest):
        found.add(_norm_number(m.group(1)))
    return found


def first_number(text: str) -> float | None:
    rest = _TIME.sub(" ", _DATE.sub(" ", text))
    m = _NUMBER.search(rest)
    return float(_norm_number(m.group(1))) if m else None
