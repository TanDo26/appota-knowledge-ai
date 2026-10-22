"""Streamlit UI — Tri thức nội bộ (Mission 3). Run: streamlit run app.py"""
from __future__ import annotations

from datetime import date

import streamlit as st

from core.access import REASON_LABELS, filter_for
from core.answer import DOC_TYPE_LABELS, fmt_date
from core.lint import lint
from core.llm import get_llm
from core.loader import KnowledgeBase, load_kb
from core.models import (
    ABSTAIN,
    ANSWERED,
    ANSWERED_WITH_NOTE,
    CLARIFY,
    CONFLICT,
    EMPLOYMENT_LABELS,
    OUT_OF_SCOPE,
    ROLE_LABELS,
    Result,
    User,
)
from core.pipeline import ask
from eval.run_eval import RESULTS, load_cases, metrics, run_cases, run_leak_matrix, run_question

st.set_page_config(page_title="Tri thức nội bộ — Mission 3", page_icon="📚", layout="wide")

STATUS_UI = {
    ANSWERED: ("green", "Đã trả lời"),
    ANSWERED_WITH_NOTE: ("blue", "Trả lời kèm ghi chú"),
    CONFLICT: ("orange", "Mâu thuẫn — không tự chọn"),
    ABSTAIN: ("gray", "Từ chối — không đủ căn cứ"),
    CLARIFY: ("red", "Chưa đủ căn cứ — cần hỏi rõ hơn"),
    OUT_OF_SCOPE: ("violet", "Ngoài phạm vi kho tài liệu"),
}


@st.cache_resource
def get_kb() -> KnowledgeBase:
    return load_kb()


@st.cache_resource
def get_gemini():
    return get_llm()


@st.cache_resource
def answer_cache() -> dict:
    """Shared across sessions: the same (persona, question, date, mode) never spends quota twice."""
    return {}


MAX_GEMINI_PER_SESSION = 20


def answer(asker: User, question: str, day: date, mode: str) -> Result:
    if mode == "gemini":
        used = st.session_state.get("gemini_calls", 0)
        if used >= MAX_GEMINI_PER_SESSION:
            result = ask(kb, asker, question, as_of=day)
            result.fallback = f"Đã dùng hết {MAX_GEMINI_PER_SESSION} câu hỏi Gemini cho phiên này"
            return result
    key = (asker.id, question.strip(), day, mode)
    cache = answer_cache()
    if key in cache:
        return cache[key]
    result = ask(kb, asker, question, as_of=day, mode=mode, llm=get_gemini())
    if mode == "gemini" and result.trace and result.trace.answer_mode == "gemini":
        st.session_state["gemini_calls"] = st.session_state.get("gemini_calls", 0) + 1
    if not result.quota_hit:  # retry later instead of caching a quota failure
        cache[key] = result
    return result


@st.cache_resource
def get_lint():
    return lint(get_kb())


@st.cache_data
def sample_questions() -> list[str]:
    """Mission 3 questions first, then Mission 2."""
    questions = []
    for suite in ("m3", "m2"):
        cfg = load_cases(suite)
        questions += [run_question(c, r) for c in cfg["cases"] for r in c["runs"]]
    return list(dict.fromkeys(questions))


kb = get_kb()


def persona_line(user: User) -> str:
    return (f"{user.name} · {kb.unit_label(user.unit)} · "
            f"{EMPLOYMENT_LABELS.get(user.employment_type, user.employment_type)}")


def persona_label(uid: str) -> str:
    u = kb.users[uid]
    return f"{u.name} — {u.title} ({kb.unit_label(u.unit)})"


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Người hỏi")
    persona_id = st.selectbox("Persona (thay cho SSO)", list(kb.users), format_func=persona_label)
    user = kb.users[persona_id]
    with st.container(border=True):
        st.markdown(f"**{user.name}** — {user.title}")
        st.caption(
            f"Đơn vị: {kb.unit_label(user.unit)}  \n"
            f"Vai trò: {ROLE_LABELS.get(user.role, user.role)}  \n"
            f"Hợp đồng: {EMPLOYMENT_LABELS.get(user.employment_type)}  \n"
            f"Thâm niên: {user.seniority_years} năm · {user.location}"
        )
    st.divider()
    gemini_ready = get_gemini() is not None
    use_gemini = st.toggle(
        "Dùng Gemini", value=gemini_ready, disabled=not gemini_ready,
        help=("Gemini viết câu trả lời từ đúng các nguồn đã chọn; hậu kiểm không đạt thì hiện trích nguyên văn."
              if gemini_ready else "Chưa cấu hình GEMINI_API_KEY nên trả lời bằng trích nguyên văn."),
    )
    mode = "gemini" if use_gemini else "extractive"
    if use_gemini:
        st.caption(f"Đã dùng {st.session_state.get('gemini_calls', 0)}/{MAX_GEMINI_PER_SESSION} câu hỏi Gemini trong phiên này.")
    as_of = st.date_input("Ngày tra cứu", value=date.today(), format="DD/MM/YYYY",
                          help="Đổi ngày để xem phiên bản nào có hiệu lực vào thời điểm đó.")
    audit = st.toggle("Chế độ kiểm định", value=False,
                      help="Dành cho người chấm: hiện tên tài liệu bị ẩn và lý do loại. Người dùng thường chỉ thấy số lượng.")
    st.caption("Toàn bộ tổ chức, người và số liệu đều là **giả lập**.")


# ---------------------------------------------------------------- rendering
def render_result(result: Result, asker: User) -> None:
    color, label = STATUS_UI[result.status]
    st.caption(f"Đang trả lời cho: **{persona_line(asker)}**")
    st.markdown(f":{color}-background[**{label}**] `{result.status}`")
    if result.context_lines and not result.answer.startswith("_"):
        st.info("\n\n".join(result.context_lines), icon="🧭")
    if result.fallback and mode == "gemini":
        if result.quota_hit:
            st.warning("Gemini tạm hết hạn mức — đang hiện **trích nguyên văn** từ nguồn.", icon="⚠️")
        else:
            st.caption(f"Hiện trích nguyên văn thay cho câu trả lời của Gemini: {result.fallback}")
    st.markdown(result.answer)
    ev = result.evidence or {}
    if ev.get("matched") or ev.get("missing"):
        st.caption(
            "Căn cứ — từ trong câu hỏi có trong nguồn: " + (", ".join(f"“{w}”" for w in ev.get("matched", [])) or "—")
            + (" · không có trong nguồn: " + ", ".join(f"“{w}”" for w in ev["missing"]) if ev.get("missing") else "")
        )
    for c in result.candidates:
        with st.expander(f"Mục gần nhất (chưa chắc đúng): {c['heading']} — {c['title']} v{c['version']}"):
            st.markdown(c["body"])
            st.caption(f"`{c['section']}` · khớp: {', '.join(c['matched']) or '—'}")
    for note in result.notes:
        st.info(note, icon="📝")
    if result.contact:
        st.markdown(f"**Đầu mối liên hệ:** {result.contact}")
    if result.flags:
        st.warning("Đã gắn cờ gửi chủ sở hữu tài liệu:\n\n" + "\n".join(
            f"- **{f.doc_key}** → {f.owner_team} ({f.owner_contact}): {f.message}" for f in result.flags), icon="🚩")
    if result.citations:
        st.markdown("**Nguồn** — bấm để xem nguyên văn đã dùng")
        for c in result.citations:
            with st.container(border=True):
                st.markdown(f"**[{c.label}] {c.title}** · phiên bản {c.version} · mục {c.heading}")
                st.caption(
                    f"{DOC_TYPE_LABELS.get(c.doc_type, c.doc_type)} · phạm vi {kb.unit_label(c.scope_unit)} · "
                    f"hiệu lực {fmt_date(c.effective_from)} → {fmt_date(c.effective_to)} · chủ sở hữu {c.owner_team} · `{c.section_id}`"
                )
                with st.expander("Nguyên văn đã dùng"):
                    st.markdown(c.body)
                    st.caption(f"Mã nội dung `{c.content_hash}` — đổi một chữ trong mục này thì mã đổi theo.")
    if result.versions:
        with st.expander("Lịch sử phiên bản của tài liệu được trích"):
            st.dataframe(
                [{"Phiên bản": v["doc_key"], "Trạng thái": v["status"], "Hiệu lực từ": v["effective_from"],
                  "Đến": v["effective_to"], "Trong câu trả lời này": v["label"]} for v in result.versions],
                hide_index=True, width="stretch",
            )
    if result.considered:
        with st.expander(f"Nguồn đã xem xét nhưng không dùng ({len(result.considered)})"):
            st.dataframe(
                [{"Mục": c["section"], "Tài liệu": f"{c['title']} v{c['version']}", "Mục tên": c["heading"],
                  "Vì sao không dùng": c["reason"]} for c in result.considered],
                hide_index=True, width="stretch",
            )
    render_trace(result)


def render_trace(result: Result) -> None:
    t = result.trace
    if t is None:
        return
    with st.expander("Trace — hệ thống đã làm gì"):
        q = result.query
        if q is not None:
            who = f"{EMPLOYMENT_LABELS.get(q.subject_employment, q.subject_employment)} · {kb.unit_label(q.subject_unit)}"
            st.markdown(f"**1. Ngữ cảnh** — quyền xem: người hỏi · áp dụng cho: {who}"
                        f"{' (tra cứu cho đối tượng khác)' if q.lookup else ''} · tính theo ngày {fmt_date(q.as_of)}")
            if t.query_steps:
                st.markdown("\n".join(f"- {s}" for s in t.query_steps))
        st.markdown(f"**2. Lọc cứng** (ngày {fmt_date(t.as_of)}): còn **{t.candidate_sections}** mục ứng viên.")
        if t.excluded_counts:
            st.markdown("\n".join(f"- {REASON_LABELS.get(k, k)}: {v}" for k, v in t.excluded_counts.items()))
        if audit:
            st.markdown("_Chế độ kiểm định — tài liệu / mục bị loại:_")
            st.dataframe(
                [{"Tài liệu / mục": k, "Lý do": REASON_LABELS.get(r, r)} for k, r in t.excluded_docs + t.excluded_sections],
                hide_index=True, width="stretch",
            )
        st.markdown(f"**3. Tìm kiếm (BM25 trên mục đã lọc)** — độ phủ mục đầu {t.coverage:.2f}, ngưỡng từ chối {t.threshold:.2f}")
        if t.retrieved:
            st.dataframe(t.retrieved, hide_index=True, width="stretch")
        st.markdown(f"**4. Resolver** — chủ đề chính: `{t.main_topic or '—'}`")
        st.markdown("\n".join(f"- {s}" for s in t.resolver_steps) or "—")
        st.markdown(f"**5. Trả lời** — chế độ `{t.answer_mode}`")
        if t.postcheck:
            st.markdown("\n".join(f"- {s}" for s in t.postcheck))


def question_input(key: str, default: str = "") -> str:
    samples = sample_questions()
    pick = st.selectbox("Câu hỏi mẫu", ["— tự nhập —"] + samples, key=f"{key}_sample",
                        index=(samples.index(default) + 1) if default in samples else 0)
    value = pick if pick != "— tự nhập —" else ""
    return st.text_input("Câu hỏi", value=value, key=f"{key}_q_{pick}")


# ---------------------------------------------------------------- tabs
tab_qa, tab_cmp, tab_eval, tab_data = st.tabs(["Hỏi đáp", "So sánh 2 persona", "Kiểm thử", "Dữ liệu"])

with tab_qa:
    q = question_input("qa")
    if st.button("Hỏi", type="primary", key="qa_go") and q.strip():
        render_result(answer(user, q, as_of, mode), user)

with tab_cmp:
    st.caption("Cùng một câu hỏi, hai người hỏi khác nhau → hai câu trả lời đúng khác nhau.")
    ids = list(kb.users)
    c1, c2 = st.columns(2)
    left = c1.selectbox("Persona trái", ids, index=ids.index("linh"), format_func=persona_label, key="cmp_left")
    right = c2.selectbox("Persona phải", ids, index=ids.index("minh"), format_func=persona_label, key="cmp_right")
    q2 = question_input("cmp", default="Quy định nghỉ phép của tôi như thế nào?")
    if st.button("So sánh", type="primary", key="cmp_go") and q2.strip():
        col_l, col_r = st.columns(2)
        for col, uid in ((col_l, left), (col_r, right)):
            with col:
                with st.container(border=True):
                    render_result(answer(kb.users[uid], q2, as_of, mode), kb.users[uid])

with tab_eval:
    before_after = RESULTS / "before_after.md"
    if before_after.exists():
        with st.expander("Trước / sau: Mission 2 → Mission 3 (`eval/results/m3/before_after.md`)", expanded=True):
            st.markdown(before_after.read_text(encoding="utf-8").split("\n## Bộ Mission 3, từng lượt")[0])
    suite = st.radio("Bộ kiểm thử", ["m3", "m2"], horizontal=True,
                     format_func={"m3": "Mission 3 — cải tiến (cases_m3.yaml)",
                                  "m2": "Mission 2 — hồi quy (cases.yaml)"}.get)
    cfg = load_cases(suite)
    st.markdown(
        f"Chạy {sum(len(c['runs']) for c in cfg['cases'])} lượt của {len(cfg['cases'])} case (kỳ vọng viết trước khi code) "
        f"và ma trận rò rỉ. Ngày tra cứu mặc định: **{fmt_date(cfg['as_of'])}**."
    )
    st.caption("Nút dưới chạy chế độ trích nguyên văn để không tốn hạn mức Gemini. "
               "Chế độ Gemini: `python -m eval.run_eval --mode gemini`.")
    if st.button("Chạy bộ kiểm thử (trích nguyên văn)", type="primary"):
        with st.spinner("Đang chạy..."):
            rows = run_cases(kb, cfg, "extractive")
            leak = run_leak_matrix(kb, cfg, "extractive")
            m = metrics(rows, leak)
        a, b, c, d, e = st.columns(5)
        a.metric("Lượt đạt", m["runs_passed"])
        b.metric("Đúng trạng thái", m["status_accuracy"])
        c.metric("Nguồn đúng", m["source_accuracy"])
        d.metric("Rò rỉ", m["leaks"], help=f"Trên {m['leak_runs']} lượt persona × câu hỏi")
        e.metric("Giao thoa", m["interference"],
                 help=f"Trên {m['interference_runs']} lượt: tài liệu giới hạn có làm thay đổi bất cứ thứ gì "
                      "người không được xem nó nhìn thấy không (so với kho không có tài liệu đó)")
        st.dataframe(
            [{
                "Case": r["case"], "Loại": r["type"], "Persona": r["persona"], "Câu hỏi": r["question"],
                "Kỳ vọng": " / ".join(r["expect"].get("status", [])), "Thực tế": r["status"],
                "Nguồn trích": ", ".join(r["cited"]) or "—",
                "Kết quả": (f"Đổi kỳ vọng có chủ đích → {r['changed']}" if r.get("changed")
                            else "Đạt" if r["passed"] else "Chưa đạt: " + "; ".join(r["failures"])),
            } for r in rows],
            hide_index=True, width="stretch",
        )
        if leak["leaks"]:
            st.error("Phát hiện rò rỉ:")
            st.dataframe(leak["leaks"], hide_index=True, width="stretch")
        if leak["interference"]["diffs"]:
            st.error("Tài liệu giới hạn làm thay đổi kết quả của người không được xem:")
            st.dataframe(leak["interference"]["diffs"], hide_index=True, width="stretch")
        st.caption("Đạt theo tiêu chí tự động chưa chắc đúng nội dung — xem `MISSION3.md` và "
                   "`eval/results/m3/m3_extractive.md` cho phần đọc từng câu trả lời.")
        if m["changed_by_design"]:
            st.caption(f"{m['changed_by_design']} lượt đổi kỳ vọng có chủ đích (không tính đạt/chưa đạt).")

with tab_data:
    st.subheader("Cây tổ chức")
    tree = []
    for unit in kb.org.values():
        depth = len(kb.unit_chain(unit.id)) - 1
        tree.append(f"{'  ' * depth}- **{unit.short}** `{unit.id}` — {unit.name}")
    st.markdown("\n".join(tree))

    st.subheader("Persona")
    st.dataframe(
        [{"ID": u.id, "Tên": u.name, "Chức danh": u.title, "Đơn vị": kb.unit_label(u.unit),
          "Vai trò": ROLE_LABELS.get(u.role), "Hợp đồng": EMPLOYMENT_LABELS.get(u.employment_type),
          "Thâm niên": u.seniority_years} for u in kb.users.values()],
        hide_index=True, width="stretch",
    )

    st.subheader("Tài liệu")
    visible = filter_for(kb, user, as_of)
    hidden_keys = {k for k, r in visible.excluded if r == "acl"}
    docs = kb.docs if audit else [d for d in kb.docs if d.key not in hidden_keys]
    if not audit:
        st.caption(f"Đang hiện các tài liệu {user.name} được quyền xem ({len(docs)}/{len(kb.docs)}). "
                   "Bật **Chế độ kiểm định** để xem toàn bộ kho và cảnh báo linter.")
    st.dataframe(
        [{"Tài liệu": d.key, "Tên": d.title, "Loại": d.doc_type, "Phạm vi": d.scope_unit,
          "Trạng thái": d.status, "Hiệu lực từ": fmt_date(d.effective_from), "Đến": fmt_date(d.effective_to),
          "Ưu tiên": d.precedence, "Độ nhạy": d.sensitivity,
          "ACL": ", ".join(d.acl_units) + (f" [{', '.join(d.acl_roles)}]" if d.acl_roles else ""),
          "Thay thế": d.supersedes or "", "Số mục": len(d.sections), "Chủ sở hữu": d.owner_team}
         for d in docs],
        hide_index=True, width="stretch",
    )

    if audit:
        st.subheader("Cảnh báo linter")
        warnings = get_lint()
        if warnings:
            st.dataframe([{"Mã": w.code, "Tài liệu": w.doc_key, "Nội dung": w.message} for w in warnings],
                         hide_index=True, width="stretch")
        else:
            st.success("Không có cảnh báo.")
        flagged = [d for d in kb.docs if d.injection_lines]
        if flagged:
            st.subheader("Dòng bị tách vì có dạng chỉ thị cho AI")
            for d in flagged:
                st.markdown(f"**{d.key}** → báo {d.owner_team} ({d.owner_contact})")
                st.code("\n".join(d.injection_lines), language=None)
