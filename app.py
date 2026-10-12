"""Streamlit UI — Tri thức nội bộ (MVP). Run: streamlit run app.py"""
from __future__ import annotations

from datetime import date

import streamlit as st

from core.access import REASON_LABELS, filter_for
from core.answer import DOC_TYPE_LABELS, fmt_date
from core.lint import lint
from core.loader import KnowledgeBase, load_kb
from core.models import (
    ABSTAIN,
    ANSWERED,
    ANSWERED_WITH_NOTE,
    CONFLICT,
    EMPLOYMENT_LABELS,
    OUT_OF_SCOPE,
    ROLE_LABELS,
    Result,
    User,
)
from core.pipeline import ask
from eval.run_eval import load_cases, metrics, run_cases, run_leak_matrix

st.set_page_config(page_title="Tri thức nội bộ — MVP", page_icon="📚", layout="wide")

STATUS_UI = {
    ANSWERED: ("green", "Đã trả lời"),
    ANSWERED_WITH_NOTE: ("blue", "Trả lời kèm ghi chú"),
    CONFLICT: ("orange", "Mâu thuẫn — không tự chọn"),
    ABSTAIN: ("gray", "Từ chối — không đủ căn cứ"),
    OUT_OF_SCOPE: ("violet", "Ngoài phạm vi kho tài liệu"),
}


@st.cache_resource
def get_kb() -> KnowledgeBase:
    return load_kb()


@st.cache_resource
def get_lint():
    return lint(get_kb())


@st.cache_data
def sample_questions() -> list[str]:
    cfg = load_cases()
    return list(dict.fromkeys(c["question"] for c in cfg["cases"]))


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
    st.toggle("Dùng Gemini", value=False, disabled=True,
              help="Chế độ Gemini sẽ được bật ở bước tiếp theo. Hiện trả lời bằng trích nguyên văn.")
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
    st.markdown(result.answer)
    for note in result.notes:
        st.info(note, icon="📝")
    if result.contact:
        st.markdown(f"**Đầu mối liên hệ:** {result.contact}")
    if result.flags:
        st.warning("Đã gắn cờ gửi chủ sở hữu tài liệu:\n\n" + "\n".join(
            f"- **{f.doc_key}** → {f.owner_team} ({f.owner_contact}): {f.message}" for f in result.flags), icon="🚩")
    if result.citations:
        st.markdown("**Nguồn**")
        for c in result.citations:
            with st.container(border=True):
                st.markdown(f"**[{c.label}] {c.title}** · phiên bản {c.version} · mục {c.heading}")
                st.caption(
                    f"{DOC_TYPE_LABELS.get(c.doc_type, c.doc_type)} · phạm vi {kb.unit_label(c.scope_unit)} · "
                    f"hiệu lực {fmt_date(c.effective_from)} → {fmt_date(c.effective_to)} · chủ sở hữu {c.owner_team} · `{c.section_id}`"
                )
    render_trace(result)


def render_trace(result: Result) -> None:
    t = result.trace
    if t is None:
        return
    with st.expander("Trace — hệ thống đã làm gì"):
        st.markdown(f"**1–2. Lọc cứng** (ngày tra cứu {fmt_date(t.as_of)}): còn **{t.candidate_sections}** mục ứng viên.")
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
        render_result(ask(kb, user, q, as_of=as_of), user)

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
                    render_result(ask(kb, kb.users[uid], q2, as_of=as_of), kb.users[uid])

with tab_eval:
    cfg = load_cases()
    st.markdown(
        f"Chạy {len(cfg['cases'])} test case trong `eval/cases.yaml` (kỳ vọng viết trước khi code) và ma trận rò rỉ. "
        f"Ngày tra cứu cố định: **{fmt_date(cfg['as_of'])}**."
    )
    if st.button("Chạy bộ kiểm thử (trích nguyên văn)", type="primary"):
        with st.spinner("Đang chạy..."):
            rows = run_cases(kb, cfg, "extractive")
            leak = run_leak_matrix(kb, cfg, "extractive")
            m = metrics(rows, leak)
        a, b, c, d = st.columns(4)
        a.metric("Lượt đạt", m["runs_passed"])
        b.metric("Đúng trạng thái", m["status_accuracy"])
        c.metric("Nguồn đúng", m["source_accuracy"])
        d.metric("Rò rỉ", m["leaks"], help=f"Trên {m['leak_runs']} lượt persona × câu hỏi")
        st.dataframe(
            [{
                "Case": r["case"], "Loại": r["type"], "Persona": r["persona"],
                "Kỳ vọng": " / ".join(r["expect"].get("status", [])), "Thực tế": r["status"],
                "Nguồn trích": ", ".join(r["cited"]) or "—",
                "Kết quả": "Đạt" if r["passed"] else "Chưa đạt: " + "; ".join(r["failures"]),
            } for r in rows],
            hide_index=True, width="stretch",
        )
        if leak["leaks"]:
            st.error("Phát hiện rò rỉ:")
            st.dataframe(leak["leaks"], hide_index=True, width="stretch")
        st.caption("Đạt theo tiêu chí tự động chưa chắc đúng nội dung — xem `docs/TEST_REPORT.md` cho phần đọc từng câu trả lời.")

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
