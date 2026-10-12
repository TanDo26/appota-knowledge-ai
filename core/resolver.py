"""Rule-based resolver (pipeline step 4, plan §3.3).

Input: every candidate section the asker may see that shares the question's topic key.
Rules, in order:
  R1 version   - per document id keep only the highest version still in the pool
  R2 audience  - within one document, a section targeted at the asker's contract type replaces the
                 general section
  R3 doc type  - policy > procedure > guideline > faq = announcement; lower types leave the answer
                 and are flagged to their owner if their figures disagree with the final answer
  R4 org level - the most specific unit wins (override / floor); a `supplement` child is merged
                 with its parent, child first
  R5 conflict  - two or more documents left at the same level: same figures -> consensus,
                 different figures -> CONFLICT (the system does not choose)
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from core.loader import KnowledgeBase
from core.models import EMPLOYMENT_LABELS, Section, User
from core.numbers import extract_numbers

TYPE_RANK = {"policy": 0, "procedure": 1, "guideline": 2, "faq": 3, "announcement": 3}


@dataclass
class Deviation:
    section: Section
    numbers: set[str]  # figures in the lower-ranked source that the answer does not contain


@dataclass
class Resolution:
    winners: list[Section] = field(default_factory=list)
    conflict: bool = False
    dropped: list[tuple[Section, str]] = field(default_factory=list)
    deviations: list[Deviation] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _numbers(sections: list[Section]) -> set[str]:
    out: set[str] = set()
    for s in sections:
        out |= extract_numbers(s.body)
    return out


def _ids(sections: list[Section]) -> str:
    return ", ".join(s.id for s in sections)


def resolve(candidates: list[Section], kb: KnowledgeBase, user: User) -> Resolution:
    res = Resolution()
    pool = list(candidates)
    if len(pool) <= 1:
        res.winners = pool
        res.steps.append("Chỉ có 1 nguồn, không cần phân xử." if pool else "Không có nguồn ứng viên.")
        return res

    def drop(sections: list[Section], reason: str) -> None:
        for s in sections:
            pool.remove(s)
            res.dropped.append((s, reason))

    # R1 — version
    by_id: dict[str, list[Section]] = defaultdict(list)
    for s in pool:
        by_id[s.doc.id].append(s)
    for doc_id, secs in by_id.items():
        top = max(s.doc.version for s in secs)
        older = [s for s in secs if s.doc.version != top]
        if older:
            drop(older, "R1 phiên bản cũ hơn")
            res.steps.append(f"R1 Phiên bản: giữ {doc_id}@{top}, bỏ {_ids(older)}.")
            res.warnings.append(f"Lint: {doc_id} có nhiều phiên bản cùng hiệu lực; tạm lấy bản {top}.")

    # R2 — audience within one document
    by_key: dict[str, list[Section]] = defaultdict(list)
    for s in pool:
        by_key[s.doc.key].append(s)
    for key, secs in by_key.items():
        targeted = [s for s in secs if s.targeted]
        general = [s for s in secs if not s.targeted]
        if targeted and general:
            drop(general, "R2 có mục dành riêng cho đối tượng của người hỏi")
            label = EMPLOYMENT_LABELS.get(user.employment_type, user.employment_type)
            res.steps.append(f"R2 Đối tượng: {key} có mục riêng cho {label} ({_ids(targeted)}), bỏ mục chung {_ids(general)}.")

    # R3 — document type
    best = min(TYPE_RANK.get(s.doc.doc_type, 9) for s in pool)
    lower = [s for s in pool if TYPE_RANK.get(s.doc.doc_type, 9) > best]
    if lower:
        winner_type = next(s.doc.doc_type for s in pool if TYPE_RANK.get(s.doc.doc_type, 9) == best)
        drop(lower, f"R3 loại tài liệu thấp hơn {winner_type}")
        res.steps.append(f"R3 Loại tài liệu: {winner_type} được ưu tiên, bỏ {_ids(lower)}.")

    # R4 — organisational level
    def depth(s: Section) -> int:
        return len(kb.unit_chain(s.doc.scope_unit))

    levels = sorted({depth(s) for s in pool}, reverse=True)
    selected = [levels[0]]
    for child_level, parent_level in zip(levels, levels[1:]):
        child = [s for s in pool if depth(s) == child_level]
        if all(s.doc.precedence == "supplement" for s in child):
            selected.append(parent_level)
            res.steps.append(
                f"R4 Cấp tổ chức: {child[0].doc.scope_unit} là bổ sung (supplement), gộp với cấp trên, cấp con đứng trước."
            )
        else:
            break
    outranked = [s for s in pool if depth(s) not in selected]
    if outranked:
        specific = [s for s in pool if depth(s) == selected[-1]]
        floors = [s for s in outranked if s.doc.precedence == "floor"]
        how = "cấp cha chỉ đặt mức sàn" if floors else "cấp cụ thể hơn ghi đè"
        drop(outranked, "R4 cấp tổ chức cao hơn")
        res.steps.append(f"R4 Cấp tổ chức: {specific[0].doc.scope_unit} thắng ({how}), bỏ {_ids(outranked)}.")
    pool.sort(key=lambda s: (-depth(s), s.doc.key, s.number))

    # R5 — same level, different documents
    for level in selected:
        at_level = [s for s in pool if depth(s) == level]
        per_doc: dict[str, list[Section]] = defaultdict(list)
        for s in at_level:
            per_doc[s.doc.key].append(s)
        if len(per_doc) < 2:
            continue
        figures = {k: _numbers(v) for k, v in per_doc.items()}
        summary = "; ".join(f"{k}: {', '.join(sorted(v)) or '—'}" for k, v in figures.items())
        if len({frozenset(v) for v in figures.values()}) == 1:
            res.steps.append(f"R5 Đồng thuận: {len(per_doc)} tài liệu cùng cấp, cùng loại, cùng số liệu ({summary}).")
        else:
            res.conflict = True
            res.steps.append(f"R5 Mâu thuẫn: tài liệu cùng cấp, cùng loại nhưng khác số liệu ({summary}). Không tự chọn.")

    res.winners = pool

    # Lower-ranked sources that state figures the final answer does not contain are flagged.
    answer_figures = _numbers(pool)
    for s in lower:
        extra = extract_numbers(s.body) - answer_figures
        if extra:
            res.deviations.append(Deviation(s, extra))
            res.steps.append(f"R3 Lệch: {s.id} ghi {', '.join(sorted(extra))}, khác nguồn thắng → gắn cờ cho chủ sở hữu.")
    return res
