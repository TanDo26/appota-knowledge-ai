"""BM25 over the sections that survived the hard filter (pipeline step 3).

The index is built per question from the asker's filtered sections only, so document frequencies,
scores and the abstain decision are never influenced by documents the asker cannot see.

Two numbers per hit:
- `score`: BM25, used for ranking.
- `coverage`: share of the question's information (IDF-weighted terms) found in the section, in
  [0, 1]. A term absent from the asker's whole corpus gets the maximum IDF: an unknown concept in
  the question is strong evidence that the corpus cannot answer it. Used for ABSTAIN.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from core.models import Section
from core.text import doc_terms, query_terms

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
            hits.append(Hit(section, score, coverage, matched))
        hits.sort(key=lambda h: (-h.score, h.section.id))
        return hits[:top_k]


def search(question: str, sections: list[Section], top_k: int = 5) -> list[Hit]:
    return BM25Index(sections).search(question, top_k)
