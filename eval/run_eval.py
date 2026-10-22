"""Run a test suite and its leak matrix.

    python -m eval.run_eval --mode extractive                     # Mission 3 suite (cases_m3.yaml)
    python -m eval.run_eval --suite m2 --mode extractive          # Mission 2 suite = regression check
    python -m eval.run_eval --mode gemini                         # needs GEMINI_API_KEY

Writes eval/results/m3/<suite>_<mode>.json and .md. Results are recorded as they come out;
expectations in the case files are never edited to match them.

The checker reads results only through attributes, with defaults for fields Mission 2 did not have,
so the same suite can also be run against the Mission 2 code (`python -m eval.compare`).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA_DIR = REPO / "data"
RESULTS = ROOT / "results" / "m3"
SUITES = {"m2": "cases.yaml", "m3": "cases_m3.yaml"}
# Expectations on information Mission 2 did not produce at all. "Behaviour" = every other expectation
# (status, sources, answer and note content, flags), so the before/after comparison can separate
# "answered wrongly" from "did not report the date / lookup / verbatim text".
FIELD_KEYS = {"query_as_of", "lookup", "subject_unit", "subject_employment",
              "considered_include", "versions_include", "verifiable_citations"}


def load_cases(suite: str = "m2") -> dict:
    return yaml.safe_load((ROOT / SUITES[suite]).read_text(encoding="utf-8"))


def _query(result):
    return getattr(result, "query", None)


def check(result, expect: dict, kb=None) -> list[str]:
    """Failed expectations, as human-readable strings (empty list = pass)."""
    fails = []
    cited = {c.doc_key for c in result.citations}
    cited_sections = {c.section_id for c in result.citations}
    notes = "\n".join(result.notes)
    flagged = {f.doc_key for f in result.flags}
    query = _query(result)

    if "status" in expect and result.status not in expect["status"]:
        fails.append(f"trạng thái {result.status}, kỳ vọng {' / '.join(expect['status'])}")
    for key in expect.get("cite_all", []):
        if key not in cited:
            fails.append(f"thiếu nguồn {key}")
    for key in expect.get("cite_none", []):
        if key in cited:
            fails.append(f"trích nguồn không được phép {key}")
    for sid in expect.get("cite_sections_all", []):
        if sid not in cited_sections:
            fails.append(f"thiếu mục {sid}")
    for sid in expect.get("cite_sections_none", []):
        if sid in cited_sections:
            fails.append(f"trích mục không được phép {sid}")
    if expect.get("no_citations") and result.citations:
        fails.append(f"không được trích nguồn nhưng có {sorted(cited)}")
    for text in expect.get("notes_contain", []):
        if text not in notes:
            fails.append(f"ghi chú thiếu '{text}'")
    for key in expect.get("flags_include", []):
        if key not in flagged:
            fails.append(f"không gắn cờ {key}")
    for key in expect.get("flags_exclude", []):
        if key in flagged:
            fails.append(f"gắn cờ sai {key}")
    for text in expect.get("answer_contains", []):
        if text.lower() not in result.answer.lower():
            fails.append(f"câu trả lời thiếu '{text}'")
    for text in expect.get("answer_not_contain", []):
        if text.lower() in result.answer.lower():
            fails.append(f"câu trả lời chứa '{text}'")
    for pattern in expect.get("answer_not_match", []):
        if re.search(pattern, result.answer, re.I):
            fails.append(f"câu trả lời khớp mẫu cấm /{pattern}/")
    if "contact_contains" in expect and expect["contact_contains"] not in (result.contact or ""):
        fails.append(f"đầu mối '{result.contact}' không chứa '{expect['contact_contains']}'")

    # Mission 3 fields
    if "query_as_of" in expect:
        got = getattr(query, "as_of", None)
        if str(got) != str(expect["query_as_of"]):
            fails.append(f"tính theo ngày {got or 'không rõ'}, kỳ vọng {expect['query_as_of']}")
    for field, label in (("lookup", "tra cứu cho đối tượng khác"), ("subject_unit", "đơn vị áp dụng"),
                         ("subject_employment", "loại hợp đồng áp dụng")):
        if field in expect:
            got = getattr(query, field, None)
            if got != expect[field]:
                fails.append(f"{label} = {got if query is not None else 'không có thông tin'}, kỳ vọng {expect[field]}")
    considered = {c["section"] for c in getattr(result, "considered", []) or []}
    for sid in expect.get("considered_include", []):
        if sid not in considered:
            fails.append(f"không liệt kê {sid} trong nguồn đã xem xét")
    versions = {v["doc_key"] for v in getattr(result, "versions", []) or []}
    for key in expect.get("versions_include", []):
        if key not in versions:
            fails.append(f"lịch sử phiên bản thiếu {key}")
    if expect.get("verifiable_citations"):
        if not result.citations:
            fails.append("không có nguồn để kiểm chứng")
        for c in result.citations:
            body, fingerprint = getattr(c, "body", None), getattr(c, "content_hash", None)
            if not body or not fingerprint:
                fails.append(f"{c.section_id} thiếu nguyên văn hoặc mã nội dung")
                continue
            if kb is not None:
                section = next((s for s in kb.sections if s.id == c.section_id), None)
                if section is None or section.body != body:
                    fails.append(f"nguyên văn của {c.section_id} khác nội dung tài liệu")
    return fails


def run_question(case: dict, run: dict) -> str:
    return run.get("question") or case["question"]


def kb_without(kb, keys):
    """The same knowledge base as if these documents had never been written (non-interference baseline)."""
    drop = set(keys)
    return type(kb)(org=kb.org, users=kb.users, docs=[d for d in kb.docs if d.key not in drop], contacts=kb.contacts)


def _comparable(result) -> dict:
    return json.loads(json.dumps(result.public_view(), ensure_ascii=False, default=str))


def public_diff(full, without, removed: int) -> list[str]:
    """Fields a user sees that differ between the full knowledge base and the one without `removed` hidden documents.

    The only expected difference is the question-independent total of documents hidden from the user (the
    "Không có quyền xem" count), which must drop by exactly the number of documents removed. Answers that stop
    before the filter (a question about another company) have no counts on either side.
    """
    a, b = _comparable(full), _comparable(without)
    ta, tb = a.pop("trace", None) or {}, b.pop("trace", None) or {}
    diff = [k for k in a if a[k] != b.get(k)]
    ca, cb = ta.pop("excluded_counts", {}), tb.pop("excluded_counts", {})
    if (ca or cb) and (ca.pop("acl", 0) - removed != cb.pop("acl", 0) or ca != cb):
        diff.append("trace.excluded_counts")
    diff += [f"trace.{k}" for k in ta if ta[k] != tb.get(k)]
    return diff


def cached_ask(ask, kb, user, question: str, as_of: date, mode: str, llm, memo: dict | None):
    """One pipeline run per (persona, question, date), shared by the cases and the leak matrix (saves LLM quota)."""
    if memo is None:
        return ask(kb, user, question, as_of=as_of, mode=mode, llm=llm)
    key = (user.id, question, as_of)
    if key not in memo:
        memo[key] = ask(kb, user, question, as_of=as_of, mode=mode, llm=llm)
    return memo[key]


def _ask():
    from core.pipeline import ask

    return ask


def run_cases(kb, cfg: dict, mode: str, llm=None, memo: dict | None = None) -> list[dict]:
    ask = _ask()
    rows = []
    for case in cfg["cases"]:
        missing_ingest = [k for k in case.get("expect_ingest_flags", []) if not kb.docs_by_key[k].injection_lines]
        for run in case["runs"]:
            user = kb.users[run["persona"]]
            question = run_question(case, run)
            as_of = run.get("as_of", cfg["as_of"])
            result = cached_ask(ask, kb, user, question, as_of, mode, llm, memo)
            interference = []
            if keys := run["expect"].get("same_as_without"):
                plain = result if mode == "extractive" else ask(kb, user, question, as_of=as_of)
                fields = public_diff(plain, ask(kb_without(kb, keys), user, question, as_of=as_of), len(keys))
                if fields:
                    interference.append(f"khác kết quả khi kho không có {', '.join(keys)}: {', '.join(fields)}")
            fails = (check(result, run["expect"], kb) + interference
                     + [f"lớp nạp không gắn cờ injection cho {k}" for k in missing_ingest])
            behaviour = not check(result, {k: v for k, v in run["expect"].items() if k not in FIELD_KEYS}, kb)
            behaviour = behaviour and not interference
            t = result.trace
            query = _query(result)
            rows.append({
                "case": case["id"],
                "req": case.get("req", ""),
                "type": case["type"],
                "persona": user.id,
                "question": question,
                "as_of": str(as_of),
                "query_as_of": str(getattr(query, "as_of", "")) if query is not None else None,
                "expect": run["expect"],
                "status": result.status,
                "cited": [c.section_id for c in result.citations],
                "notes": result.notes,
                "flags": [f"{f.kind}:{f.doc_key}" for f in result.flags],
                "contact": result.contact,
                "answer": result.answer,
                "coverage": t.coverage if t else None,
                "topic": t.main_topic if t else None,
                "resolver_steps": t.resolver_steps if t else [],
                "postcheck": t.postcheck if t else [],
                "answer_mode": t.answer_mode if t else None,
                "fallback": result.fallback,
                "changed": case.get("changed_in_m3"),
                "passed": not fails,
                "behaviour_passed": behaviour and not missing_ingest,
                "failures": fails,
            })
    return rows


def run_leak_matrix(kb, cfg: dict, mode: str, llm=None, memo: dict | None = None) -> dict:
    ask = _ask()
    case_questions = [run_question(c, r) for c in cfg["cases"] for r in c["runs"]]
    questions = list(dict.fromkeys(case_questions + cfg["leak_matrix"]["attack_questions"]))
    restricted = cfg["leak_matrix"]["restricted"]
    leaks, runs = [], 0
    for user in kb.users.values():
        for q in questions:
            result = cached_ask(ask, kb, user, q, cfg["as_of"], mode, llm, memo)
            view = result.public_view()
            runs += 1
            for r in restricted:
                if user.id in r["allowed_personas"]:
                    continue
                for field, value in view.items():
                    blob = json.dumps(value, ensure_ascii=False, default=str)
                    for marker in (r["canary"], r["doc"]):
                        if marker in blob:
                            leaks.append({"persona": user.id, "question": q, "doc": r["doc"], "marker": marker, "field": field})
    return {"runs": runs, "questions": len(questions), "personas": len(kb.users), "leaks": leaks,
            "interference": run_noninterference(kb, cfg, questions)}


def run_noninterference(kb, cfg: dict, questions: list[str]) -> dict:
    """Change Request B2: a restricted document must not change ANYTHING a person who may not see it is shown.

    Stronger than looking for IDs and canaries: a paraphrased figure, a different status, a missing source or
    an extra note would all reveal that a hidden document exists. Extractive mode only (deterministic, no quota).
    """
    ask = _ask()
    full: dict = {}
    diffs, runs = [], 0
    for r in cfg["leak_matrix"]["restricted"]:
        keys = [d.key for d in kb.docs if d.id == r["doc"]]
        other = kb_without(kb, keys)
        for user in kb.users.values():
            if user.id in r["allowed_personas"]:
                continue
            for q in questions:
                runs += 1
                if (user.id, q) not in full:
                    full[(user.id, q)] = ask(kb, user, q, as_of=cfg["as_of"])
                fields = public_diff(full[(user.id, q)], ask(other, user, q, as_of=cfg["as_of"]), len(keys))
                if fields:
                    diffs.append({"persona": user.id, "question": q, "doc": r["doc"], "fields": fields})
    return {"runs": runs, "diffs": diffs}


def metrics(rows: list[dict], leak: dict) -> dict:
    from core.models import ABSTAIN

    scored = [r for r in rows if not r.get("changed")]
    by_type: dict[str, list[bool]] = defaultdict(list)
    by_req: dict[str, list[bool]] = defaultdict(list)
    by_req_behaviour: dict[str, list[bool]] = defaultdict(list)
    for r in scored:
        by_type[r["type"]].append(r["passed"])
        if r.get("req"):
            by_req[r["req"]].append(r["passed"])
            by_req_behaviour[r["req"]].append(r["behaviour_passed"])
    with_sources = [r for r in scored if r["expect"].get("cite_all")]
    source_ok = [r for r in with_sources if set(r["expect"]["cite_all"]) <= {c.split("#")[0] for c in r["cited"]}]
    status_ok = [r for r in scored if r["status"] in r["expect"].get("status", [r["status"]])]
    want_abstain = [r for r in scored if r["expect"].get("status") == [ABSTAIN]]
    got_abstain = [r for r in want_abstain if r["status"] == ABSTAIN]
    false_abstain = [r for r in scored if r["status"] == ABSTAIN and ABSTAIN not in r["expect"].get("status", [])]
    cases = list(dict.fromkeys(r["case"] for r in scored))
    interference = leak.get("interference") or {"runs": 0, "diffs": []}
    return {
        "runs_passed": f"{sum(r['passed'] for r in scored)}/{len(scored)}",
        "behaviour_passed": f"{sum(r['behaviour_passed'] for r in scored)}/{len(scored)}",
        "cases_passed": f"{sum(all(x['passed'] for x in scored if x['case'] == c) for c in cases)}/{len(cases)}",
        "changed_by_design": len(rows) - len(scored),
        "pass_rate_by_type": {t: f"{sum(v)}/{len(v)}" for t, v in by_type.items()},
        "pass_rate_by_req": {t: f"{sum(v)}/{len(v)}" for t, v in sorted(by_req.items())},
        "behaviour_by_req": {t: f"{sum(v)}/{len(v)}" for t, v in sorted(by_req_behaviour.items())},
        "source_accuracy": f"{len(source_ok)}/{len(with_sources)}",
        "status_accuracy": f"{len(status_ok)}/{len(scored)}",
        "correct_abstain": f"{len(got_abstain)}/{len(want_abstain)}",
        "false_abstain": len(false_abstain),
        "gemini_answers": sum(1 for r in rows if r.get("answer_mode") == "gemini"),
        "fallbacks": sum(1 for r in rows if r.get("fallback")),
        "leaks": len(leak["leaks"]),
        "leak_runs": leak["runs"],
        "interference": len(interference["diffs"]),
        "interference_runs": interference["runs"],
    }


def git_head() -> str:
    try:
        # "-dirty" marks runs made with uncommitted changes, so the header never claims a commit it was not.
        return subprocess.run(["git", "describe", "--always", "--dirty"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    except OSError:
        return "?"


def verdict(r: dict) -> str:
    if r.get("changed"):
        return f"Đổi kỳ vọng có chủ đích → {r['changed']}" + ("" if r["passed"] else " (kỳ vọng cũ không còn đúng)")
    return "Đạt" if r["passed"] else "**Chưa đạt**: " + "; ".join(r["failures"])


def to_markdown(title: str, mode: str, cfg: dict, rows: list[dict], leak: dict, m: dict, run_at: str, code: str) -> str:
    out = [
        f"# {title} — chế độ `{mode}`",
        "",
        f"Chạy lúc {run_at} · code `{code}` · ngày tra cứu mặc định {cfg['as_of']}",
        "",
        "## Tổng hợp",
        "",
        f"- Lượt chạy đạt: **{m['runs_passed']}** · case đạt (mọi lượt của case): **{m['cases_passed']}**"
        + (f" · đổi kỳ vọng có chủ đích: {m['changed_by_design']} lượt" if m["changed_by_design"] else ""),
        f"- Đúng trạng thái: {m['status_accuracy']} · nguồn kỳ vọng nằm trong nguồn trích: {m['source_accuracy']}",
        f"- Từ chối đúng: {m['correct_abstain']} · từ chối nhầm: {m['false_abstain']}",
        f"- Ma trận rò rỉ: **{m['leaks']} rò rỉ** trên {m['leak_runs']} lượt ({leak['personas']} persona × {leak['questions']} câu hỏi)",
        f"- Không giao thoa (Change Request B2): **{m['interference']} khác biệt** trên {m['interference_runs']} lượt "
        "(người không có quyền × câu hỏi, có và không có tài liệu giới hạn trong kho)",
        f"- Câu trả lời do Gemini viết: {m['gemini_answers']} · rơi về trích nguyên văn: {m['fallbacks']}",
        "- Theo loại: " + " · ".join(f"{t} {v}" for t, v in m["pass_rate_by_type"].items()),
    ]
    if m["pass_rate_by_req"]:
        out.append("- Theo yêu cầu: " + " · ".join(f"{t} {v}" for t, v in m["pass_rate_by_req"].items()))
    out += [
        "",
        "## Từng lượt chạy",
        "",
        "| Case | Loại | Persona | Câu hỏi | Kỳ vọng | Thực tế | Nguồn trích | Kết quả |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        exp = " / ".join(r["expect"].get("status", []))
        cited = ", ".join(r["cited"]) or "—"
        day = f" _(ngày {r['as_of']})_" if r["as_of"] != str(cfg["as_of"]) else ""
        out.append(f"| {r['case']} | {r['type']} | {r['persona']} | {r['question']}{day} | {exp} | {r['status']} | {cited} | {verdict(r)} |")
    out += ["", "## Ma trận rò rỉ", ""]
    if leak["leaks"]:
        out += ["| Persona | Câu hỏi | Tài liệu | Dấu hiệu | Ở trường |", "|---|---|---|---|---|"]
        out += [f"| {x['persona']} | {x['question']} | {x['doc']} | {x['marker']} | {x['field']} |" for x in leak["leaks"]]
    else:
        out.append("Không phát hiện ID tài liệu giới hạn hay canary token nào trong bất kỳ trường công khai nào "
                   "(context, nguồn trích, câu trả lời, ghi chú, cờ, đầu mối, trace, ngữ cảnh truy vấn, nguồn đã xem xét, "
                   "lịch sử phiên bản, gợi ý) của persona không có quyền.")
    diffs = (leak.get("interference") or {}).get("diffs", [])
    out += ["", "## Không giao thoa", "",
            "Với mỗi tài liệu giới hạn và mỗi persona không được xem nó: chạy mọi câu hỏi trên kho đầy đủ và trên kho "
            "bỏ tài liệu đó, so sánh mọi thứ persona thấy. Chỉ được phép khác tổng số tài liệu bị ẩn (giảm đúng số "
            "tài liệu đã bỏ).", ""]
    if diffs:
        out += ["| Persona | Câu hỏi | Tài liệu | Trường khác |", "|---|---|---|---|"]
        out += [f"| {x['persona']} | {x['question']} | {x['doc']} | {', '.join(x['fields'])} |" for x in diffs]
    else:
        out.append("Không có khác biệt nào.")
    out += ["", "## Chi tiết", ""]
    for r in rows:
        out += [
            f"### {r['case']} · {r['persona']} — {verdict(r)}",
            "",
            f"**Câu hỏi:** {r['question']}  ",
            f"**Trạng thái:** {r['status']} · **chủ đề:** {r['topic']} · **độ phủ:** {r['coverage']}"
            + (f" · **tính theo ngày:** {r['query_as_of']}" if r.get("query_as_of") else "") + "  ",
            f"**Đầu mối:** {r['contact'] or '—'} · **chế độ trả lời:** {r['answer_mode']}"
            + (f" · **dự phòng vì:** {r['fallback']}" if r.get("fallback") else ""),
            "",
            "**Resolver / trace:**",
            "",
            *[f"- {s}" for s in r["resolver_steps"] + r["postcheck"]],
            "",
            "**Câu trả lời:**",
            "",
            r["answer"],
            "",
        ]
        if r["notes"]:
            out += ["**Ghi chú:**", "", *[f"- {n}" for n in r["notes"]], ""]
        if r["failures"]:
            out += ["**Chưa đạt vì:**", "", *[f"- {f}" for f in r["failures"]], ""]
    return "\n".join(out) + "\n"


def evaluate(suite: str, mode: str, llm=None) -> tuple[dict, list[dict], dict, dict]:
    from core.loader import load_kb

    kb = load_kb(DATA_DIR)
    cfg = load_cases(suite)
    memo: dict = {}
    rows = run_cases(kb, cfg, mode, llm, memo)
    leak = run_leak_matrix(kb, cfg, mode, llm, memo)
    return cfg, rows, leak, metrics(rows, leak)


SUITE_TITLES = {"m2": "Bộ kiểm thử Mission 2 (hồi quy)", "m3": "Bộ kiểm thử Mission 3"}


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["extractive", "gemini"], default="extractive")
    parser.add_argument("--suite", choices=sorted(SUITES), default="m3")
    args = parser.parse_args(argv)

    from core.llm import get_llm

    llm = None
    if args.mode == "gemini":
        # Retries on 429 and a gap between calls keep a batch run inside free-tier per-minute limits.
        llm = get_llm(max_retries=2, min_interval=6.5)
        if llm is None:
            print("Chưa cấu hình GEMINI_API_KEY (biến môi trường hoặc .streamlit/secrets.toml).")
            return 2
        print(f"Gemini model: {llm.model}")
    cfg, rows, leak, m = evaluate(args.suite, args.mode, llm)
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    code = git_head()

    RESULTS.mkdir(parents=True, exist_ok=True)
    stem = f"{args.suite}_{args.mode}"
    payload = {"suite": args.suite, "mode": args.mode, "model": llm.model if llm else None, "run_at": run_at,
               "commit": code, "as_of": str(cfg["as_of"]), "metrics": m, "rows": rows, "leak_matrix": leak}
    (RESULTS / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (RESULTS / f"{stem}.md").write_text(
        to_markdown(SUITE_TITLES[args.suite], args.mode, cfg, rows, leak, m, run_at, code), encoding="utf-8")

    for r in rows:
        mark = "ĐỔI " if r.get("changed") else ("ĐẠT " if r["passed"] else "CHƯA")
        print(f"{mark} {r['case']:6} {r['persona']:5} {r['status']:19} {r['answer_mode'] or '':22} {', '.join(r['cited']) or '—'}")
        for f in r["failures"]:
            print(f"        - {f}")
    print(json.dumps(m, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
