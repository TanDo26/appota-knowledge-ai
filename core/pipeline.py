"""Pipeline: persona -> query context -> hard filter -> retrieval -> resolver -> answer, with a trace of every step."""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date

from core.access import audience_ok, can_view, filter_for, in_effect
from core.answer import (
    ABSTAIN_TEXT,
    DOC_TYPE_LABELS,
    clarify_text,
    extractive_answer,
    fmt_date,
    gemini_answer,
    make_citations,
)
from core.context import build_query
from core.loader import KnowledgeBase
from core.models import (
    ABSTAIN,
    ANSWERED,
    ANSWERED_WITH_NOTE,
    CLARIFY,
    CONFLICT,
    EMPLOYMENT_LABELS,
    OUT_OF_SCOPE,
    Flag,
    QueryContext,
    Result,
    Section,
    Trace,
    User,
)
from core.resolver import resolve
from core.retrieval import MIN_COVERAGE, Hit, explain, search
from core.text import fold

# Questions about the asker's own records (remaining leave, own payslip). Matched on folded text.
# They need a first-person marker so policy questions like "phép còn lại có được chuyển không" pass.
PERSONAL_DATA_PATTERNS = [
    re.compile(p)
    for p in (
        r"\b(toi|minh|em) da (dung|nghi|su dung|lay) (bao nhieu|may|het chua)\b",
        r"\b(luong|thu nhap|phieu luong|bang luong|thue)( thang nay| hien tai)? cua (toi|minh|em)\b",
        r"\bso du\b",
    )
]
# "còn mấy" (how many left) and "con mấy" (child) fold to the same text. Questions typed with diacritics
# are checked on their own spelling (Mission 3: "nghỉ chăm con mấy ngày" was taken for a balance question).
_REMAINING_FOLDED = re.compile(r"\b(toi|minh|em)\b[^?]*\bcon( lai)? (bao nhieu|may)\b")
_REMAINING_ACCENTED = re.compile(r"\b(tôi|mình|em)\b[^?]*\bcòn( lại)? (bao nhiêu|mấy)\b")

# Shown in "Nguồn đã xem xét nhưng không dùng" (resolver reasons start with the rule number).
CONSIDERED_REASONS = {
    "R1": "Phiên bản cũ hơn của cùng tài liệu",
    "R2": "Mục chung; tài liệu có mục riêng cho đúng đối tượng",
    "R3": "Loại tài liệu xếp sau",
    "R4": "Đơn vị cấp cao hơn; quy định của đơn vị cụ thể hơn được ưu tiên",
}

MAX_CANDIDATES = 3


def choose_topic(hits: list[Hit]) -> tuple[str, str]:
    """Main topic = the topic with the highest summed BM25 score among relevant top hits.

    Taking only the top hit's topic was a coin flip when sections of one document nearly tie
    (eval run 1, TC01/TC02); a topic backed by several sections (policy + FAQ) is more reliable.
    """
    votes: dict[str, float] = defaultdict(float)
    for h in hits:
        if h.coverage >= MIN_COVERAGE:
            votes[h.section.topic] += h.score
    first = hits[0].section.topic
    best = max(votes, key=lambda t: (votes[t], t == first))
    ranked = sorted(votes.items(), key=lambda kv: -kv[1])
    return best, " > ".join(f"{t} {v:.2f}" for t, v in ranked)


def _accented(text: str) -> bool:
    return fold(text) != text.lower()


def is_personal_data(question: str) -> bool:
    folded = fold(question)
    if any(p.search(folded) for p in PERSONAL_DATA_PATTERNS):
        return True
    if _accented(question):
        return bool(_REMAINING_ACCENTED.search(unicodedata.normalize("NFC", question.lower())))
    return bool(_REMAINING_FOLDED.search(folded))


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


def context_lines(kb: KnowledgeBase, user: User, q: QueryContext) -> list[str]:
    """Plain-language statement of WHEN and FOR WHOM the answer holds, when that is not simply "you, today"."""
    lines = []
    if q.time_ambiguous:
        lines.append(f"Câu hỏi nhắc nhiều mốc thời gian ({q.time_phrase}); mình trả lời theo ngày tra cứu "
                     f"{fmt_date(q.base_date)}.")
    elif q.shifted:
        lines.append(f"Theo các tài liệu có hiệu lực ngày {fmt_date(q.as_of)} (câu hỏi nhắc tới “{q.time_phrase}”), "
                     f"không phải ngày tra cứu {fmt_date(q.base_date)}.")
    if q.other_company:
        lines.append(f"Câu hỏi nhắc tới “{', '.join(q.subject_phrases)}”, thuộc công ty khác với công ty của bạn; "
                     "mình chỉ tra cứu quy định trong công ty của bạn.")
    elif q.lookup:
        who = []
        if q.subject_employment != user.employment_type:
            who.append(f"nhân sự {EMPLOYMENT_LABELS.get(q.subject_employment, q.subject_employment).lower()}")
        if q.subject_unit != user.unit:
            who.append(f"đơn vị {kb.unit_label(q.subject_unit)}")
        mine = []
        if q.subject_employment != user.employment_type:
            mine.append(EMPLOYMENT_LABELS.get(user.employment_type, user.employment_type))
        if q.subject_unit != user.unit:
            mine.append(kb.unit_label(user.unit))
        lines.append(f"Đây là quy định cho {' thuộc '.join(who)} — không áp dụng cho bạn ({', '.join(mine)}). "
                     "Chỉ gồm tài liệu bạn được quyền xem.")
    return lines


def _candidates(hits: list[Hit], question: str, retrieval_text: str) -> list[dict]:
    """Nearest sections on distinct topics, for CLARIFY. Only sections the asker may see are ever here."""
    seen, out = set(), []
    for h in hits:
        if h.section.topic in seen:
            continue
        seen.add(h.section.topic)
        s = h.section
        out.append({
            "section": s.id, "doc_key": s.doc.key, "title": s.doc.title, "version": s.doc.version,
            "heading": f"{s.number}. {s.heading}", "body": s.body,
            "matched": explain(question, retrieval_text, [s])["matched"],
        })
        if len(out) == MAX_CANDIDATES:
            break
    return out


def _considered(res) -> list[dict]:
    deviating = {d.section.id: d.numbers for d in res.deviations}
    out = []
    for s, reason in res.dropped:
        text = CONSIDERED_REASONS.get(reason[:2], reason)
        if reason.startswith("R3"):
            text += f" ({DOC_TYPE_LABELS.get(s.doc.doc_type, s.doc.doc_type)})"
        if s.id in deviating:
            text += f"; ghi số liệu khác ({', '.join(sorted(deviating[s.id]))}), đã gắn cờ cho chủ sở hữu"
        out.append({"section": s.id, "doc_key": s.doc.key, "title": s.doc.title, "version": s.doc.version,
                    "heading": f"{s.number}. {s.heading}", "reason": text})
    return out


def _versions(kb: KnowledgeBase, user: User, winners: list[Section], as_of: date) -> list[dict]:
    """Every version of each cited document that the asker is allowed to see, with how it was treated."""
    used = {s.doc.key for s in winners}
    out = []
    for doc_id in dict.fromkeys(s.doc.id for s in winners):
        for d in sorted((d for d in kb.docs if d.id == doc_id), key=lambda d: d.version):
            if not can_view(kb, user, d):
                continue
            if d.key in used:
                label = "dùng trong câu trả lời"
            elif d.status == "draft":
                label = "bản nháp, chưa phê duyệt — không dùng"
            elif in_effect(d, as_of):
                label = "có hiệu lực, không phải bản được chọn"
            elif d.effective_from is not None and d.effective_from > as_of:
                label = f"chưa hiệu lực (từ {fmt_date(d.effective_from)})"
            else:
                label = "hết hiệu lực"
            out.append({"doc_key": d.key, "doc_id": d.id, "version": d.version, "status": d.status,
                        "effective_from": fmt_date(d.effective_from), "effective_to": fmt_date(d.effective_to),
                        "label": label, "used": d.key in used})
    return out


def _quote_sections(sections: list[Section]) -> str:
    return "; ".join(f"{s.doc.title} phiên bản {s.doc.version}: “{s.body}”" for s in sections)


def ask(
    kb: KnowledgeBase,
    user: User,
    question: str,
    as_of: date | None = None,
    mode: str = "extractive",
    llm=None,
) -> Result:
    base = as_of or date.today()

    # Step 1 — query context: who asks (permission) vs when and about whom (applicability)
    query, retrieval_text, query_steps = build_query(kb, user, question, base)
    trace = Trace(as_of=query.as_of, persona=user.id, threshold=MIN_COVERAGE, query_steps=query_steps)
    lines = context_lines(kb, user, query)

    def finish(result: Result) -> Result:
        result.query, result.context_lines, result.trace = query, lines, trace
        return result

    if query.other_company:
        trace.resolver_steps.append("Câu hỏi về đơn vị thuộc công ty khác: không tra cứu.")
        return finish(Result(status=ABSTAIN, answer=ABSTAIN_TEXT, contact=route_contact(kb, user, question)))

    # Step 2 — hard filter (ACL for the asker; scope and audience for the subject; validity on query.as_of)
    fr = filter_for(kb, user, query.as_of, query.subject_unit, query.subject_employment)
    trace.excluded_counts = fr.counts()
    trace.excluded_docs = list(fr.excluded)
    trace.excluded_sections = list(fr.excluded_sections)
    trace.candidate_sections = len(fr.sections)

    # Step 3 — retrieval over the filtered sections only (dates removed from the query: they are context)
    hits = search(retrieval_text, fr.sections, top_k=5)
    trace.retrieved = [
        {
            "section": h.section.id,
            "heading": h.section.heading,
            "topic": h.section.topic,
            "score": round(h.score, 3),
            "coverage": round(h.coverage, 3),
            "matched": " ".join(h.matched),
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
            return finish(_out_of_scope(kb, user, question, []))
        return finish(Result(status=ABSTAIN, answer=ABSTAIN_TEXT, contact=route_contact(kb, user, question)))

    if top.thin:
        trace.resolver_steps.append(
            f"Căn cứ mỏng: mục đầu ({top.section.id}) chỉ khớp các âm tiết rời ({', '.join(top.matched)}), "
            "không khớp cụm từ nào của câu hỏi và không đủ mọi từ → hỏi lại, không trả lời."
        )
        if personal:
            return finish(_out_of_scope(kb, user, question, []))
        evidence = explain(question, retrieval_text, [top.section])
        candidates = _candidates(hits, question, retrieval_text)
        return finish(Result(status=CLARIFY, answer=clarify_text(evidence, candidates), evidence=evidence,
                             candidates=candidates, contact=route_contact(kb, user, question)))

    # Step 4 — resolver on the main topic
    topic, tally = choose_topic(hits)
    trace.main_topic = topic
    trace.resolver_steps.append(f"Chọn chủ đề theo tổng điểm các mục liên quan trong top {len(hits)}: {tally}.")
    candidates = [s for s in fr.sections if s.topic == topic]
    res = resolve(candidates, kb, user, query.subject_employment)
    trace.resolver_steps.extend(res.steps + res.warnings)

    notes: list[str] = []
    flags: list[Flag] = []
    winner_ids = {s.doc.id for s in res.winners}
    for doc in fr.upcoming:
        if doc.id not in winner_ids:
            continue
        if query.shifted and doc.effective_from <= query.base_date:
            continue  # already in force on the lookup date: covered by the "today" note below
        for s in doc.sections:
            if s.topic == topic and audience_ok(s.audience, query.subject_employment):
                notes.append(
                    f"Sắp thay đổi: từ {fmt_date(doc.effective_from)}, {doc.title} phiên bản {doc.version} "
                    f"có hiệu lực và quy định: “{s.body}”"
                )
    if query.shifted:
        now = filter_for(kb, user, query.base_date, query.subject_unit, query.subject_employment)
        current = resolve([s for s in now.sections if s.topic == topic], kb, user, query.subject_employment).winners
        if {s.id for s in current} != {s.id for s in res.winners}:
            if current:
                notes.append(f"Quy định đang áp dụng hôm nay ({fmt_date(query.base_date)}): {_quote_sections(current)}")
            else:
                notes.append(f"Vào ngày tra cứu {fmt_date(query.base_date)} không còn tài liệu nào quy định nội dung này.")
        if query.as_of > query.base_date:
            notes.append(f"Câu trả lời dựa trên các tài liệu đã phê duyệt đến ngày {fmt_date(query.base_date)}; "
                         f"quy định tại {fmt_date(query.as_of)} vẫn có thể thay đổi.")
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
                              f"Mâu thuẫn về '{topic}' với tài liệu khác ({'; '.join(res.conflict_reasons)})"))

    citations = make_citations(res.winners)
    if personal:
        result = _out_of_scope(kb, user, question, res.winners)
        result.notes, result.flags = notes, flags
    else:
        status = CONFLICT if res.conflict else (ANSWERED_WITH_NOTE if notes else ANSWERED)
        result = Result(status=status, answer="", citations=citations, notes=notes, flags=flags,
                        context_sections=list(res.winners), conflict_reasons=list(res.conflict_reasons))
        if status == CONFLICT:
            result.contact = ", ".join(sorted({f"{f.owner_team} ({f.owner_contact})" for f in flags}))
    result.evidence = explain(question, retrieval_text, res.winners)
    result.considered = _considered(res)
    result.versions = _versions(kb, user, res.winners, query.as_of)
    finish(result)

    # Step 5 — answer. Gemini only rewrites clear answers; CONFLICT, CLARIFY and OUT_OF_SCOPE stay deterministic
    # so the model can neither pick a side in a conflict nor produce a personal figure.
    trace.answer_mode = "extractive"
    if mode == "gemini" and result.status in (ANSWERED, ANSWERED_WITH_NOTE):
        if llm is None:
            result.answer = extractive_answer(result)
            result.fallback = "Chưa cấu hình GEMINI_API_KEY"
            trace.answer_mode = "extractive (dự phòng)"
            trace.postcheck.append("Không có key Gemini → trích nguyên văn")
        else:
            result = gemini_answer(result, user, kb.unit_label(user.unit), question, llm)
            if result.status == ABSTAIN:
                result.contact = route_contact(kb, user, question)
    else:
        result.answer = extractive_answer(result)
    return result


def _out_of_scope(kb: KnowledgeBase, user: User, question: str, rule_sections) -> Result:
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
    )
