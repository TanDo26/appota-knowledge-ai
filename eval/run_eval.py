"""Run the test cases and the leak matrix.

    python -m eval.run_eval --mode extractive   # runs anywhere, no key needed
    python -m eval.run_eval --mode gemini       # needs GEMINI_API_KEY

Writes eval/results/<mode>.json and eval/results/<mode>.md. Results are recorded as they come out;
expectations in eval/cases.yaml are never edited to match them.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from core.llm import get_llm
from core.loader import KnowledgeBase, load_kb
from core.models import ABSTAIN, Result
from core.pipeline import ask

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def load_cases() -> dict:
    return yaml.safe_load((ROOT / "cases.yaml").read_text(encoding="utf-8"))


def check(result: Result, expect: dict) -> list[str]:
    """Failed expectations, as human-readable strings (empty list = pass)."""
    fails = []
    cited = {c.doc_key for c in result.citations}
    cited_sections = {c.section_id for c in result.citations}
    notes = "\n".join(result.notes)
    flagged = {f.doc_key for f in result.flags}

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
    for text in expect.get("answer_not_contain", []):
        if text.lower() in result.answer.lower():
            fails.append(f"câu trả lời chứa '{text}'")
    for pattern in expect.get("answer_not_match", []):
        if re.search(pattern, result.answer, re.I):
            fails.append(f"câu trả lời khớp mẫu cấm /{pattern}/")
    if "contact_contains" in expect and expect["contact_contains"] not in (result.contact or ""):
        fails.append(f"đầu mối '{result.contact}' không chứa '{expect['contact_contains']}'")
    return fails


def cached_ask(kb: KnowledgeBase, user, question: str, cfg: dict, mode: str, llm, memo: dict | None) -> Result:
    """One pipeline run per (persona, question), shared by the cases and the leak matrix (saves LLM quota)."""
    if memo is None:
        return ask(kb, user, question, as_of=cfg["as_of"], mode=mode, llm=llm)
    key = (user.id, question)
    if key not in memo:
        memo[key] = ask(kb, user, question, as_of=cfg["as_of"], mode=mode, llm=llm)
    return memo[key]


def run_cases(kb: KnowledgeBase, cfg: dict, mode: str, llm=None, memo: dict | None = None) -> list[dict]:
    rows = []
    for case in cfg["cases"]:
        missing_ingest = [k for k in case.get("expect_ingest_flags", []) if not kb.docs_by_key[k].injection_lines]
        for run in case["runs"]:
            user = kb.users[run["persona"]]
            result = cached_ask(kb, user, case["question"], cfg, mode, llm, memo)
            fails = check(result, run["expect"]) + [f"lớp nạp không gắn cờ injection cho {k}" for k in missing_ingest]
            t = result.trace
            rows.append({
                "case": case["id"],
                "type": case["type"],
                "persona": user.id,
                "question": case["question"],
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
                "passed": not fails,
                "failures": fails,
            })
    return rows


def run_leak_matrix(kb: KnowledgeBase, cfg: dict, mode: str, llm=None, memo: dict | None = None) -> dict:
    questions = list(dict.fromkeys([c["question"] for c in cfg["cases"]] + cfg["leak_matrix"]["attack_questions"]))
    restricted = cfg["leak_matrix"]["restricted"]
    leaks, runs = [], 0
    for user in kb.users.values():
        for q in questions:
            result = cached_ask(kb, user, q, cfg, mode, llm, memo)
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
    return {"runs": runs, "questions": len(questions), "personas": len(kb.users), "leaks": leaks}


def metrics(rows: list[dict], leak: dict) -> dict:
    by_type: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r["passed"])
    with_sources = [r for r in rows if r["expect"].get("cite_all")]
    source_ok = [r for r in with_sources if set(r["expect"]["cite_all"]) <= {c.split("#")[0] for c in r["cited"]}]
    status_ok = [r for r in rows if r["status"] in r["expect"].get("status", [r["status"]])]
    want_abstain = [r for r in rows if r["expect"].get("status") == [ABSTAIN]]
    got_abstain = [r for r in want_abstain if r["status"] == ABSTAIN]
    false_abstain = [r for r in rows if r["status"] == ABSTAIN and ABSTAIN not in r["expect"].get("status", [])]
    return {
        "runs_passed": f"{sum(r['passed'] for r in rows)}/{len(rows)}",
        "cases_passed": f"{sum(all(x['passed'] for x in rows if x['case'] == c) for c in dict.fromkeys(r['case'] for r in rows))}"
                        f"/{len(dict.fromkeys(r['case'] for r in rows))}",
        "pass_rate_by_type": {t: f"{sum(v)}/{len(v)}" for t, v in by_type.items()},
        "source_accuracy": f"{len(source_ok)}/{len(with_sources)}",
        "status_accuracy": f"{len(status_ok)}/{len(rows)}",
        "correct_abstain": f"{len(got_abstain)}/{len(want_abstain)}",
        "false_abstain": len(false_abstain),
        "gemini_answers": sum(1 for r in rows if r.get("answer_mode") == "gemini"),
        "fallbacks": sum(1 for r in rows if r.get("fallback")),
        "leaks": len(leak["leaks"]),
        "leak_runs": leak["runs"],
    }


def git_head() -> str:
    try:
        # "-dirty" marks runs made with uncommitted changes, so the header never claims a commit it was not.
        return subprocess.run(["git", "describe", "--always", "--dirty"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    except OSError:
        return "?"


def to_markdown(mode: str, cfg: dict, rows: list[dict], leak: dict, m: dict, run_at: str) -> str:
    out = [
        f"# Kết quả eval — chế độ `{mode}`",
        "",
        f"Chạy lúc {run_at} · commit `{git_head()}` · ngày tra cứu {cfg['as_of']}",
        "",
        "## Tổng hợp",
        "",
        f"- Lượt chạy đạt: **{m['runs_passed']}** · case đạt (mọi lượt của case): **{m['cases_passed']}**",
        f"- Đúng trạng thái: {m['status_accuracy']} · nguồn kỳ vọng nằm trong nguồn trích: {m['source_accuracy']}",
        f"- Từ chối đúng: {m['correct_abstain']} · từ chối nhầm: {m['false_abstain']}",
        f"- Ma trận rò rỉ: **{m['leaks']} rò rỉ** trên {m['leak_runs']} lượt ({leak['personas']} persona × {leak['questions']} câu hỏi)",
        f"- Câu trả lời do Gemini viết: {m['gemini_answers']} · rơi về trích nguyên văn: {m['fallbacks']}",
        "- Theo loại: " + " · ".join(f"{t} {v}" for t, v in m["pass_rate_by_type"].items()),
        "",
        "## Từng lượt chạy",
        "",
        "| Case | Loại | Persona | Kỳ vọng | Thực tế | Nguồn trích | Kết quả |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        exp = " / ".join(r["expect"].get("status", []))
        cited = ", ".join(r["cited"]) or "—"
        verdict = "Đạt" if r["passed"] else "**Chưa đạt**: " + "; ".join(r["failures"])
        out.append(f"| {r['case']} | {r['type']} | {r['persona']} | {exp} | {r['status']} | {cited} | {verdict} |")
    out += ["", "## Ma trận rò rỉ", ""]
    if leak["leaks"]:
        out += ["| Persona | Câu hỏi | Tài liệu | Dấu hiệu | Ở trường |", "|---|---|---|---|---|"]
        out += [f"| {x['persona']} | {x['question']} | {x['doc']} | {x['marker']} | {x['field']} |" for x in leak["leaks"]]
    else:
        out.append("Không phát hiện ID tài liệu giới hạn hay canary token nào trong context, nguồn trích, câu trả lời, "
                   "ghi chú, cờ và đầu mối của persona không có quyền.")
    out += ["", "## Chi tiết", ""]
    for r in rows:
        out += [
            f"### {r['case']} · {r['persona']} — {'Đạt' if r['passed'] else 'Chưa đạt'}",
            "",
            f"**Câu hỏi:** {r['question']}  ",
            f"**Trạng thái:** {r['status']} · **chủ đề:** {r['topic']} · **độ phủ:** {r['coverage']}  ",
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


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["extractive", "gemini"], default="extractive")
    args = parser.parse_args(argv)

    kb = load_kb()
    cfg = load_cases()
    llm = None
    if args.mode == "gemini":
        # Retries on 429 and a gap between calls keep a batch run inside free-tier per-minute limits.
        llm = get_llm(max_retries=2, min_interval=6.5)
        if llm is None:
            print("Chưa cấu hình GEMINI_API_KEY (biến môi trường hoặc .streamlit/secrets.toml).")
            return 2
        print(f"Gemini model: {llm.model}")
    memo: dict = {}
    rows = run_cases(kb, cfg, args.mode, llm, memo)
    leak = run_leak_matrix(kb, cfg, args.mode, llm, memo)
    m = metrics(rows, leak)
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    RESULTS.mkdir(exist_ok=True)
    payload = {"mode": args.mode, "model": llm.model if llm else None, "run_at": run_at, "commit": git_head(), "as_of": str(cfg["as_of"]),
               "metrics": m, "rows": rows, "leak_matrix": leak}
    (RESULTS / f"{args.mode}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (RESULTS / f"{args.mode}.md").write_text(to_markdown(args.mode, cfg, rows, leak, m, run_at), encoding="utf-8")

    for r in rows:
        mark = "ĐẠT " if r["passed"] else "CHƯA"
        print(f"{mark} {r['case']:5} {r['persona']:5} {r['status']:19} {r['answer_mode']:22} {', '.join(r['cited']) or '—'}")
        for f in r["failures"]:
            print(f"        - {f}")
    print(json.dumps(m, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
