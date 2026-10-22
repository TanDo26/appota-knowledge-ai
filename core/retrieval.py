"""BM25 over the sections that survived the hard filter (pipeline step 3).

The index is built per question from the asker's filtered sections only, so document frequencies,
scores and the abstain decision are never influenced by documents the asker cannot see.

Two numbers per hit:
- `score`: BM25, used for ranking.
- `coverage`: share of the question's information (IDF-weighted terms) found in the section, in
  [0, 1]. A term absent from the asker's whole corpus gets the maximum IDF: an unknown concept in
  the question is strong evidence that the corpus cannot answer it. Used for ABSTAIN.

Mission 3 adds a third signal, `thin`: the hit matches no phrase (adjacent-syllable bigram) of the
question and not every word of it either. Coverage can be high on such a hit when one rare syllable
matches by coincidence after diacritics are folded ("lên công ty" vs "trở lên"); the pipeline then asks
instead of answering (CLARIFY). The rule has no parameter to tune; it was checked against the
calibration set, where it changes no decision (eval/results/m3/calibration.md).
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from core.models import Section
from core.text import STOPWORDS, doc_terms, fold, query_terms, rewrite_query

K1 = 1.5
B = 0.75

# Chosen once from eval/calibration.yaml (a question set separate from the test cases) before the
# first evaluation run: 17/18 correct. Rationale in docs/DECISIONS.md, data in eval/results/calibration.md.
MIN_COVERAGE = 0.59


def section_text(section: Section) -> str:
    return f"{section.doc.title}\n{section.heading}\n{section.body}"


@dataclass
class Hit:
    section: Section
    score: float
    coverage: float
    matched: list[str]
    terms: list[str] = field(default_factory=list)  # all terms of the question

    @property
    def thin(self) -> bool:
        """Matched on scattered syllables only: no phrase of the question, and not all of its words."""
        if any("_" in t for t in self.matched):
            return False
        words = [t for t in self.terms if "_" not in t]
        return not all(w in self.matched for w in words)


class BM25Index:
    def __init__(self, sections: list[Section]):
        self.sections = sections
        self.docs = [Counter(doc_terms(section_text(s))) for s in sections]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0
        self.df: Counter = Counter()
        for d in self.docs:
            self.df.update(d.keys())

    def idf(self, term: str) -> float:
        n, df = len(self.docs), self.df.get(term, 0)
        return math.log((n - df + 0.5) / (df + 0.5) + 1.0)

    def _bm25(self, terms: list[str], i: int) -> float:
        doc, length = self.docs[i], self.lengths[i]
        score = 0.0
        for t in terms:
            tf = doc.get(t, 0)
            if tf:
                norm = K1 * (1 - B + B * length / self.avg_len) if self.avg_len else K1
                score += self.idf(t) * tf * (K1 + 1) / (tf + norm)
        return score

    def search(self, question: str, top_k: int = 5) -> list[Hit]:
        terms = list(dict.fromkeys(query_terms(question)))  # unique, order kept
        if not terms or not self.docs:
            return []
        weights = {t: self.idf(t) for t in terms}
        total = sum(weights.values())
        hits = []
        for i, section in enumerate(self.sections):
            score = self._bm25(terms, i)
            if score <= 0:
                continue
            matched = [t for t in terms if t in self.docs[i]]
            coverage = sum(weights[t] for t in matched) / total if total else 0.0
            hits.append(Hit(section, score, coverage, matched, terms))
        hits.sort(key=lambda h: (-h.score, h.section.id))
        return hits[:top_k]


def search(question: str, sections: list[Section], top_k: int = 5) -> list[Hit]:
    return BM25Index(sections).search(question, top_k)


def _display_words(question: str) -> dict[str, str]:
    """Folded syllable -> the asker's own wording, to show matches in the question's spelling."""
    words = re.findall(r"\w+", unicodedata.normalize("NFC", question.lower()))
    out: dict[str, str] = {}
    for w in words:
        out.setdefault(fold(w), w)
    return out


def explain(question: str, retrieval_text: str, sections: list[Section]) -> dict:
    """Question words found / not found in `sections`, for the "Căn cứ" line under every answer.

    Runs of adjacent matched syllable pairs are shown as one phrase ("phụ cấp trực on call"); single
    words only when not already inside a matched phrase.
    """
    terms = list(dict.fromkeys(query_terms(retrieval_text)))
    present: set[str] = set()
    for s in sections:
        present |= set(doc_terms(section_text(s)))
    # The asker's spelling first; words that came from the synonym table take the document's spelling.
    show = {**_display_words(" ".join(section_text(s) for s in sections)), **_display_words(question)}

    def content(syl: str) -> bool:
        return len(syl) > 1 and syl not in STOPWORDS

    runs: list[list[str]] = []
    current: list[str] = []
    syls = rewrite_query(retrieval_text).split()
    for a, b in zip(syls, syls[1:]):
        if content(a) and content(b) and f"{a}_{b}" in present:
            current = current + [b] if current else [a, b]
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    covered = {syl for run in runs for syl in run}
    singles = [t for t in terms if "_" not in t and t in present and t not in covered]
    missing = [t for t in terms if "_" not in t and t not in present]
    return {
        "matched": list(dict.fromkeys([" ".join(show.get(s, s) for s in run) for run in runs]
                                      + [show.get(t, t) for t in singles])),
        "missing": [show.get(t, t) for t in missing],
    }
