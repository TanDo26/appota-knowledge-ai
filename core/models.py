"""Data model shared by every pipeline stage."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

EMPLOYMENT_LABELS = {"full_time": "Chính thức", "probation": "Thử việc", "intern": "Thực tập"}
ROLE_LABELS = {"employee": "Nhân viên", "manager": "Quản lý", "hr": "Nhân sự"}

DOC_TYPES = ("policy", "procedure", "guideline", "faq", "announcement")
STATUSES = ("active", "draft", "archived")
PRECEDENCES = ("override", "floor", "supplement")
SENSITIVITIES = ("internal", "restricted")

# Output states (plan §3.2)
ANSWERED = "ANSWERED"
ANSWERED_WITH_NOTE = "ANSWERED_WITH_NOTE"
CONFLICT = "CONFLICT"
ABSTAIN = "ABSTAIN"
OUT_OF_SCOPE = "OUT_OF_SCOPE"


@dataclass(frozen=True)
class Unit:
    id: str
    parent: str | None
    name: str
    short: str


@dataclass(frozen=True)
class User:
    id: str
    name: str
    title: str
    unit: str
    role: str
    employment_type: str
    seniority_years: int
    location: str


@dataclass(eq=False)
class Section:
    doc: Doc = field(repr=False)
    number: str
    heading: str
    topic: str | None
    applies_to: tuple[str, ...] | None  # None = inherit from the document
    body: str

    @property
    def id(self) -> str:
        return f"{self.doc.key}#{self.number}"

    @property
    def audience(self) -> tuple[str, ...]:
        """Employment types this section targets; empty tuple means everyone."""
        return self.applies_to if self.applies_to is not None else self.doc.applies_to

    @property
    def targeted(self) -> bool:
        """True when the section declares its own audience (e.g. a probation-only section)."""
        return self.applies_to is not None


@dataclass(eq=False)
class Doc:
    id: str
    version: int
    title: str
    doc_type: str
    scope_unit: str
    applies_to: tuple[str, ...]
    status: str
    effective_from: date | None
    effective_to: date | None
    supersedes: str | None
    precedence: str
    acl_units: tuple[str, ...]
    acl_roles: tuple[str, ...]
    sensitivity: str
    owner_team: str
    owner_contact: str
    path: str
    raw_meta: dict = field(repr=False, default_factory=dict)
    sections: list[Section] = field(default_factory=list)
    injection_lines: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.id}@{self.version}"


@dataclass
class Citation:
    label: str  # "S1", "S2", ...
    section_id: str
    doc_key: str
    title: str
    version: int
    heading: str
    doc_type: str
    scope_unit: str
    effective_from: date | None
    effective_to: date | None
    owner_team: str


@dataclass
class Flag:
    """Something the document owner should hear about (shown to the asker only for docs they can see)."""
    kind: str  # deviation | conflict
    doc_key: str
    owner_team: str
    owner_contact: str
    message: str


@dataclass
class Trace:
    as_of: date
    persona: str
    # Public: counts only, never names of hidden documents.
    excluded_counts: dict[str, int] = field(default_factory=dict)
    candidate_sections: int = 0
    # Sections the asker is allowed to see, with retrieval scores.
    retrieved: list[dict] = field(default_factory=list)
    coverage: float = 0.0
    threshold: float = 0.0
    main_topic: str | None = None
    resolver_steps: list[str] = field(default_factory=list)
    answer_mode: str = "extractive"
    postcheck: list[str] = field(default_factory=list)
    # Auditor-only ("Chế độ kiểm định"): which documents were excluded and why.
    excluded_docs: list[tuple[str, str]] = field(default_factory=list)
    excluded_sections: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Result:
    status: str
    answer: str
    citations: list[Citation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)
    contact: str | None = None
    # Exactly what would be sent to the LLM; checked by the leak matrix.
    context_sections: list[Section] = field(default_factory=list)
    trace: Trace | None = None
    # Set when Gemini was requested but the extractive text was shown instead (and why).
    fallback: str | None = None
    quota_hit: bool = False

    def public_view(self) -> dict:
        """Everything a normal (non-auditor) user can see. Used by the UI and the leak matrix."""
        t = self.trace
        return {
            "status": self.status,
            "answer": self.answer,
            "citations": [c.__dict__ for c in self.citations],
            "notes": list(self.notes),
            "flags": [f.__dict__ for f in self.flags],
            "contact": self.contact,
            "fallback": self.fallback,
            "context": [{"id": s.id, "heading": s.heading, "body": s.body} for s in self.context_sections],
            "trace": None if t is None else {
                "excluded_counts": t.excluded_counts,
                "candidate_sections": t.candidate_sections,
                "retrieved": t.retrieved,
                "coverage": t.coverage,
                "threshold": t.threshold,
                "main_topic": t.main_topic,
                "resolver_steps": t.resolver_steps,
                "answer_mode": t.answer_mode,
                "postcheck": t.postcheck,
            },
        }
