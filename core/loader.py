"""Read org tree, personas, contacts and Markdown documents into the knowledge base.

Each document is Markdown with YAML front-matter. Every `##` heading starts a section and is
followed by a comment declaring its topic, optionally with a section-level audience:

    ## 5. Nhân sự thử việc
    <!-- topic: leave.annual_days | applies_to: probation -->

Lines that look like instructions aimed at an AI are removed at load time and recorded on the
document so the owner can be told (plan §3.4).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.models import Doc, Section, Unit, User
from core.text import fold

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
_HEADING = re.compile(r"^##\s+(?:(\d+)\.\s*)?(.+?)\s*$")
_META = re.compile(r"^<!--\s*(.*?)\s*-->$")

# Matched against diacritic-folded, lowercased lines.
INJECTION_PATTERNS = [
    re.compile(p)
    for p in (
        r"\bbo qua (moi |tat ca |cac |toan bo )?(huong dan|chi dan|chi thi|quy tac|yeu cau)",
        r"\bignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts|rules)",
        r"\bdisregard (all |any |the )?(previous|prior|above|earlier)",
        r"\b(you are now|system prompt|developer mode)\b",
        r"\b(print|reveal|dump|output) (every|all|the) (source|document)",
        r"\bin (ra )?toan bo (nguon|tai lieu)",
    )
]


@dataclass
class KnowledgeBase:
    org: dict[str, Unit]
    users: dict[str, User]
    docs: list[Doc]
    contacts: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.docs_by_key = {d.key: d for d in self.docs}

    @property
    def sections(self) -> list[Section]:
        return [s for d in self.docs for s in d.sections]

    def unit_chain(self, unit_id: str) -> list[Unit]:
        """Units from the root down to `unit_id`."""
        chain = []
        current = unit_id
        while current is not None and current in self.org:
            chain.append(self.org[current])
            current = self.org[current].parent
        return list(reversed(chain))

    def unit_label(self, unit_id: str) -> str:
        """Breadcrumb without the group root, e.g. 'Công ty A › Kỹ thuật › Platform'."""
        chain = [u.short for u in self.unit_chain(unit_id) if u.parent is not None]
        return " › ".join(chain) or self.org[unit_id].short


def is_injection(line: str) -> bool:
    folded = fold(line)
    return any(p.search(folded) for p in INJECTION_PATTERNS)


def _as_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(v.strip() for v in value.split(",") if v.strip())
    return tuple(str(v) for v in value)


def _parse_meta_comment(text: str) -> dict[str, str]:
    meta = {}
    for part in text.split("|"):
        if ":" in part:
            k, v = part.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def parse_document(text: str, path: str = "<memory>") -> Doc:
    text = text.replace("\r\n", "\n")
    m = _FRONT_MATTER.match(text)
    if not m:
        raise ValueError(f"{path}: missing YAML front-matter")
    meta = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]

    acl = meta.get("acl") or {}
    owner = meta.get("owner") or {}
    applies = meta.get("applies_to") or {}
    doc = Doc(
        id=str(meta.get("id", "")),
        version=int(meta.get("version", 0) or 0),
        title=str(meta.get("title", "")),
        doc_type=str(meta.get("doc_type", "")),
        scope_unit=str(meta.get("scope_unit", "")),
        applies_to=_as_tuple(applies.get("employment_types") if isinstance(applies, dict) else applies),
        status=str(meta.get("status", "")),
        effective_from=meta.get("effective_from"),
        effective_to=meta.get("effective_to"),
        supersedes=meta.get("supersedes"),
        precedence=str(meta.get("precedence", "override")),
        acl_units=_as_tuple(acl.get("units")),
        acl_roles=_as_tuple(acl.get("roles")),
        sensitivity=str(meta.get("sensitivity", "internal")),
        owner_team=str(owner.get("team", "")),
        owner_contact=str(owner.get("contact", "")),
        path=path,
        raw_meta=meta,
    )

    current: dict | None = None
    ordinal = 0

    def flush() -> None:
        if current is None:
            return
        doc.sections.append(
            Section(
                doc=doc,
                number=current["number"],
                heading=current["heading"],
                topic=current["topic"],
                applies_to=current["applies_to"],
                body="\n".join(current["lines"]).strip(),
            )
        )

    for line in body.split("\n"):
        heading = _HEADING.match(line)
        if heading:
            flush()
            ordinal += 1
            current = {
                "number": heading.group(1) or str(ordinal),
                "heading": heading.group(2),
                "topic": None,
                "applies_to": None,
                "lines": [],
            }
            continue
        if current is None:
            continue  # title and preamble are not indexed
        comment = _META.match(line.strip())
        if comment and current["topic"] is None and not current["lines"]:
            info = _parse_meta_comment(comment.group(1))
            current["topic"] = info.get("topic") or None
            if "applies_to" in info:
                current["applies_to"] = _as_tuple(info["applies_to"])
            continue
        if line.strip() and is_injection(line):
            doc.injection_lines.append(line.strip())
            continue
        current["lines"].append(line)
    flush()
    return doc


def load_org(path: Path) -> dict[str, Unit]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        u["id"]: Unit(id=u["id"], parent=u.get("parent"), name=u["name"], short=u["short"],
                      aliases=tuple(u.get("aliases") or ()))
        for u in data["units"]
    }


def load_users(path: Path) -> dict[str, User]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        u["id"]: User(
            id=u["id"],
            name=u["name"],
            title=u.get("title", ""),
            unit=u["unit"],
            role=u["role"],
            employment_type=u["employment_type"],
            seniority_years=int(u.get("seniority_years", 0)),
            location=u.get("location", ""),
        )
        for u in data["users"]
    }


def load_docs(directory: Path) -> list[Doc]:
    docs = []
    for path in sorted(directory.glob("*.md")):
        docs.append(parse_document(path.read_text(encoding="utf-8"), path=str(path.name)))
    return docs


def load_kb(data_dir: Path | str = DATA_DIR) -> KnowledgeBase:
    data_dir = Path(data_dir)
    return KnowledgeBase(
        org=load_org(data_dir / "org.yaml"),
        users=load_users(data_dir / "users.yaml"),
        docs=load_docs(data_dir / "docs"),
        contacts=yaml.safe_load((data_dir / "contacts.yaml").read_text(encoding="utf-8")),
    )
