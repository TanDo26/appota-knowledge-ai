"""Pipeline: persona -> hard filter -> retrieval -> resolver -> answer, with a trace of every step."""
from __future__ import annotations

import re
from datetime import date

from core.access import audience_ok, filter_for
from core.answer import extractive_answer, fmt_date, make_citations
from core.loader import KnowledgeBase
from core.models import (
    ABSTAIN,
    ANSWERED,
    ANSWERED_WITH_NOTE,
    CONFLICT,
    OUT_OF_SCOPE,
    Flag,
    Result,
    Trace,
    User,
)
from core.resolver import resolve
from core.retrieval import MIN_COVERAGE, search
from core.text import fold

# Questions about the asker's own records (remaining leave, own payslip). Matched on folded text.
# They need a first-person marker so policy questions like "phép còn lại có được chuyển không" pass.
PERSONAL_DATA_PATTERNS = [
    re.compile(p)
    for p in (
        r"\b(toi|minh|em)\b[^?]*\bcon( lai)? (bao nhieu|may)\b",
        r"\b(toi|minh|em) da (dung|nghi|su dung|lay) (bao nhieu|may|het chua)\b",
        r"\b(luong|thu nhap|phieu luong|bang luong|thue)( thang nay| hien tai)? cua (toi|minh|em)\b",
        r"\bso du\b",
    )
]

ABSTAIN_TEXT = (
    "Mình chưa tìm thấy quy định nào trả lời được câu hỏi này trong các tài liệu áp dụng cho bạn, "
    "nên không đưa ra câu trả lời để tránh sai."
)


def is_personal_data(question: str) -> bool:
    folded = fold(question)
    return any(p.search(folded) for p in PERSONAL_DATA_PATTERNS)


def company_of(kb: KnowledgeBase, user: User) -> str:
    chain = kb.unit_chain(user.unit)
    return chain[1].id if len(chain) > 1 else chain[0].id


def route_contact(kb: KnowledgeBase, user: User, question: str) -> str:
    """Contact chosen from the question's wording and the asker's company only, never from hidden documents."""
    cfg = kb.contacts
    company = company_of(kb, user)
    folded = fold(question)
    team = cfg.get("default_team", "hr")
    for route in cfg.get("routes", []):
        if any(re.search(rf"\b{re.escape(fold(k))}\b", folded) for k in route["keywords"]):
            if company in cfg["teams"].get(route["team"], {}):
                team = route["team"]
                break
    entry = cfg["teams"][team].get(company) or cfg["teams"][cfg.get("default_team", "hr")][company]
    return f"{entry['team']} ({entry['contact']})"


def ask(
    kb: KnowledgeBase,
    user: User,
    question: str,
    as_of: date | None = None,
    mode: str = "extractive",
    llm=None,
) -> Result:
    as_of = as_of or date.today()
    trace = Trace(as_of=as_of, persona=user.id, threshold=MIN_COVERAGE)

    # Step 2 — hard filter
    fr = filter_for(kb, user, as_of)
    trace.excluded_counts = fr.counts()
    trace.excluded_docs = list(fr.excluded)
    trace.excluded_sections = list(fr.excluded_sections)
    trace.candidate_sections = len(fr.sections)

    # Step 3 — retrieval over the filtered sections only
    hits = search(question, fr.sections, top_k=5)
    trace.retrieved = [
        {
            "section": h.section.id,
            "heading": h.section.heading,
            "topic": h.section.topic,
            "score": round(h.score, 3),
            "coverage": round(h.coverage, 3),
        }
        for h in hits
    ]
    top = hits[0] if hits else None
    trace.coverage = round(top.coverage, 3) if top else 0.0
    personal = is_personal_data(question)

    if top is None or top.coverage < MIN_COVERAGE:
        trace.resolver_steps.append(
            f"Độ phủ câu hỏi {trace.coverage:.2f} < ngưỡng {MIN_COVERAGE:.2f}: không có mục đủ liên quan."
        )
        if personal:
            return _out_of_scope(kb, user, question, trace, [])
        return Result(status=ABSTAIN, answer=ABSTAIN_TEXT, contact=route_contact(kb, user, question), trace=trace)

    # Step 4 — resolver on the main topic
    topic = top.section.topic
    trace.main_topic = topic
    candidates = [s for s in fr.sections if s.topic == topic]
    res = resolve(candidates, kb, user)
    trace.resolver_steps.extend(res.steps + res.warnings)

    notes: list[str] = []
    flags: list[Flag] = []
    winner_ids = {s.doc.id for s in res.winners}
    for doc in fr.upcoming:
        if doc.id not in winner_ids:
            continue
        for s in doc.sections:
            if s.topic == topic and audience_ok(s.audience, user):
                notes.append(
                    f"Sắp thay đổi: từ {fmt_date(doc.effective_from)}, {doc.title} phiên bản {doc.version} "
                    f"có hiệu lực và quy định: “{s.body}”"
                )
    for d in res.deviations:
        doc = d.section.doc
        notes.append(
            f"{doc.title} ({doc.key}) ghi khác: “{d.section.body}”. Câu trả lời theo nguồn có thứ bậc cao hơn; "
            f"đã gắn cờ để {doc.owner_team} cập nhật."
        )
        flags.append(Flag("deviation", doc.key, doc.owner_team, doc.owner_contact,
                          f"{d.section.id} lệch với nguồn thắng (số liệu: {', '.join(sorted(d.numbers))})"))
    if res.conflict:
        for key in dict.fromkeys(s.doc.key for s in res.winners):
            doc = kb.docs_by_key[key]
            flags.append(Flag("conflict", key, doc.owner_team, doc.owner_contact,
                              f"Mâu thuẫn về '{topic}' với tài liệu cùng cấp khác"))

    citations = make_citations(res.winners)
    if personal:
        result = _out_of_scope(kb, user, question, trace, res.winners)
        result.notes, result.flags = notes, flags
    else:
        status = CONFLICT if res.conflict else (ANSWERED_WITH_NOTE if notes else ANSWERED)
        result = Result(status=status, answer="", citations=citations, notes=notes, flags=flags,
                        context_sections=list(res.winners), trace=trace)
        if status == CONFLICT:
            result.contact = ", ".join(sorted({f"{f.owner_team} ({f.owner_contact})" for f in flags}))

    # Step 5 — answer
    trace.answer_mode = "extractive"
    result.answer = extractive_answer(result)
    return result


def _out_of_scope(kb: KnowledgeBase, user: User, question: str, trace: Trace, rule_sections) -> Result:
    pd = kb.contacts.get("personal_data", {})
    text = (
        "Đây là thông tin cá nhân của bạn, không có trong kho tài liệu nên mình không đưa ra con số. "
        f"Bạn xem trên {pd.get('system', 'hệ thống nhân sự')} ({pd.get('url', '')}). {pd.get('hint', '')}"
    ).strip()
    return Result(
        status=OUT_OF_SCOPE,
        answer=text,
        citations=make_citations(rule_sections),
        context_sections=list(rule_sections),
        contact=route_contact(kb, user, question),
        trace=trace,
    )
