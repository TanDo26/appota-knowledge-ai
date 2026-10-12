"""Answer layer (pipeline step 5). This module holds the extractive mode: the winning sections are
returned verbatim with a header, so the core can be tested without an LLM and the demo survives
when the LLM quota runs out.
"""
from __future__ import annotations

from datetime import date

from core.models import ABSTAIN, CONFLICT, OUT_OF_SCOPE, Citation, Result, Section

DOC_TYPE_LABELS = {
    "policy": "Chính sách",
    "procedure": "Quy trình",
    "guideline": "Hướng dẫn",
    "faq": "FAQ",
    "announcement": "Thông báo",
}


def fmt_date(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "—"


def make_citations(sections: list[Section]) -> list[Citation]:
    return [
        Citation(
            label=f"S{i}",
            section_id=s.id,
            doc_key=s.doc.key,
            title=s.doc.title,
            version=s.doc.version,
            heading=f"{s.number}. {s.heading}",
            doc_type=s.doc.doc_type,
            scope_unit=s.doc.scope_unit,
            effective_from=s.doc.effective_from,
            effective_to=s.doc.effective_to,
            owner_team=s.doc.owner_team,
        )
        for i, s in enumerate(sections, start=1)
    ]


def source_header(c: Citation) -> str:
    return f"[{c.label}] {c.title} — phiên bản {c.version}, mục {c.heading}, hiệu lực từ {fmt_date(c.effective_from)}"


def _quote(body: str) -> str:
    return "\n".join(f"> {line}" if line.strip() else ">" for line in body.split("\n"))


def extractive_answer(result: Result) -> str:
    """Verbatim text of the winning sections. `result` must already carry status, citations and context."""
    if result.status == ABSTAIN:
        return result.answer  # already the generic refusal
    blocks = [f"{source_header(c)}\n{_quote(s.body)}" for c, s in zip(result.citations, result.context_sections)]
    if result.status == CONFLICT:
        owners = sorted({f.owner_team for f in result.flags})
        return (
            "Các tài liệu đang hiệu lực nói khác nhau về vấn đề này. Hệ thống **không tự chọn** bên nào:\n\n"
            + "\n\n".join(blocks)
            + f"\n\nĐã báo mâu thuẫn cho chủ sở hữu tài liệu: {', '.join(owners)}. "
            "Trong lúc chờ, bạn nên hỏi trực tiếp các đơn vị này trước khi làm theo."
        )
    if result.status == OUT_OF_SCOPE:
        prefix = result.answer
        if not blocks:
            return prefix
        return f"{prefix}\n\n**Quy định áp dụng cho bạn:**\n\n" + "\n\n".join(blocks)
    return "\n\n".join(blocks)
