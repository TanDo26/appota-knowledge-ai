"""Before/after: run both test suites against the Mission 2 code and the current code.

    python -m eval.compare                    # baseline = Mission 2 commit d40d1df
    python -m eval.compare --baseline <ref>

The Mission 2 `core/` is extracted from git into a temporary folder (the working tree is not touched).
Both versions read the SAME data (data/ of the working tree) and are judged by the SAME checker
(eval/run_eval.py), so the difference comes from the code only. Extractive mode, no LLM.
Writes eval/results/m3/before_after.md and .json.
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "eval" / "results" / "m3"
M2_COMMIT = "d40d1df"


def extract_core(ref: str, dest: Path) -> None:
    tar_bytes = subprocess.run(["git", "archive", "--format=tar", ref, "core"], cwd=REPO,
                               capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        tar.extractall(dest, filter="data")


def run_worker(core_dir: Path, suite: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "eval.compare", "--worker", str(core_dir), "--suite", suite],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return json.loads(proc.stdout)


def worker(core_dir: str, suite: str) -> None:
    sys.path.insert(0, core_dir)  # `import core` now resolves to the version under test
    from eval.run_eval import evaluate

    _, rows, leak, m = evaluate(suite, "extractive")
    keep = ("case", "req", "type", "persona", "question", "as_of", "status", "cited", "passed", "behaviour_passed",
            "failures", "changed")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"metrics": m, "rows": [{k: r.get(k) for k in keep} for r in rows], "leaks": leak["leaks"]},
                     ensure_ascii=False, default=str))


def mark(r: dict) -> str:
    if r.get("changed"):
        return "đổi có chủ đích"
    if r["passed"]:
        return "Đạt"
    return "Chưa đạt (hành vi đúng, thiếu thông tin)" if r.get("behaviour_passed") else "Chưa đạt"


def to_markdown(baseline: str, results: dict, run_at: str) -> str:
    out = [
        "# Trước / sau: Mission 2 → Mission 3",
        "",
        f"Chạy lúc {run_at}. Cùng dữ liệu (`data/` hiện tại), cùng bộ kiểm (`eval/run_eval.py`), chế độ trích nguyên văn.",
        f"Code \"trước\" = `core/` của commit `{baseline}` (Mission 2). Code \"sau\" = `core/` hiện tại.",
        "",
        "## Tổng hợp",
        "",
        "| Bộ kiểm thử | Code | Lượt đạt | Hành vi đúng* | Đúng trạng thái | Từ chối nhầm | Rò rỉ | Giao thoa** |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for suite, label in (("m3", "Mission 3 (mới)"), ("m2", "Mission 2 (hồi quy)")):
        for version in ("M2", "M3"):
            m = results[version][suite]["metrics"]
            changed = f" (+{m['changed_by_design']} đổi có chủ đích)" if m["changed_by_design"] else ""
            out.append(f"| {label} | {version} | **{m['runs_passed']}**{changed} | {m['behaviour_passed']} | "
                       f"{m['status_accuracy']} | {m['false_abstain']} | {m['leaks']} / {m['leak_runs']} | "
                       f"{m['interference']} / {m['interference_runs']} |")
    out += ["", "\* *Hành vi đúng*: mọi kỳ vọng về trạng thái, nguồn, nội dung câu trả lời/ghi chú và cờ; bỏ qua các "
            "kỳ vọng về thông tin Mission 2 không hề xuất ra (ngày tính, tra cứu cho ai, nguyên văn, lịch sử phiên bản, "
            "nguồn đã xem xét). Cột này tách \"trả lời sai\" khỏi \"không báo thông tin\".",
            "",
            "\*\* *Giao thoa* (Change Request B2): số lượt mà một tài liệu giới hạn làm thay đổi bất cứ thứ gì người "
            "không được xem nó nhìn thấy (so với kho không có tài liệu đó)."]
    m2, m3 = results["M2"]["m3"]["metrics"], results["M3"]["m3"]["metrics"]
    out += ["", "Theo yêu cầu cải tiến (bộ Mission 3):", "",
            "| Yêu cầu | Code M2: đạt · hành vi đúng | Code M3: đạt · hành vi đúng |", "|---|---|---|"]
    names = {"R1": "R1 Phiên bản & thời điểm", "R2": "R2 Quyền theo bối cảnh", "R3": "R3 Mâu thuẫn giữa các cấp",
             "R4": "R4 Chưa đủ căn cứ", "R5": "R5 Kiểm chứng nguồn", "CR": "CR B2 Khác quyền truy cập"}
    for req in sorted(set(m2["pass_rate_by_req"]) | set(m3["pass_rate_by_req"])):
        out.append(f"| {names.get(req, req)} | {m2['pass_rate_by_req'].get(req, '—')} · {m2['behaviour_by_req'].get(req, '—')} | "
                   f"{m3['pass_rate_by_req'].get(req, '—')} · {m3['behaviour_by_req'].get(req, '—')} |")

    out += ["", "## Bộ Mission 3, từng lượt", "",
            "| Case | YC | Loại | Persona | Câu hỏi | M2 | M3 |", "|---|---|---|---|---|---|---|"]
    before = {(r["case"], r["persona"], r["question"]): r for r in results["M2"]["m3"]["rows"]}
    for r in results["M3"]["m3"]["rows"]:
        b = before[(r["case"], r["persona"], r["question"])]
        day = f" _(ngày {r['as_of']})_" if r["as_of"] != "2026-10-15" else ""
        out.append(f"| {r['case']} | {r['req']} | {r['type']} | {r['persona']} | {r['question']}{day} | "
                   f"{mark(b)} · `{b['status']}` | {mark(r)} · `{r['status']}` |")

    out += ["", "### Vì sao code M2 chưa đạt", ""]
    for b in results["M2"]["m3"]["rows"]:
        if not b["passed"]:
            out.append(f"- **{b['case']} · {b['persona']}** — {'; '.join(b['failures'])}")
    still = [r for r in results["M3"]["m3"]["rows"] if not r["passed"]]
    out += ["", "### Code M3 còn chưa đạt", ""]
    out += [f"- **{r['case']} · {r['persona']}** — {'; '.join(r['failures'])}" for r in still] or ["Không có."]

    out += ["", "## Bộ Mission 2 (hồi quy): các lượt có kết quả khác nhau", ""]
    before2 = {(r["case"], r["persona"]): r for r in results["M2"]["m2"]["rows"]}
    diff = [(before2[(r["case"], r["persona"])], r) for r in results["M3"]["m2"]["rows"]
            if (before2[(r["case"], r["persona"])]["status"], before2[(r["case"], r["persona"])]["cited"])
            != (r["status"], r["cited"])]
    if diff:
        out += ["| Case | Persona | M2 | M3 | Ghi chú |", "|---|---|---|---|---|"]
        for b, a in diff:
            note = f"Đổi có chủ đích → {a['changed']}" if a.get("changed") else ("; ".join(a["failures"]) or "—")
            out.append(f"| {a['case']} | {a['persona']} | `{b['status']}` {', '.join(b['cited']) or '—'} | "
                       f"`{a['status']}` {', '.join(a['cited']) or '—'} | {note} |")
    else:
        out.append("Không có: mọi lượt cho cùng trạng thái và cùng nguồn trích.")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", default=M2_COMMIT)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--suite", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        worker(args.worker, args.suite)
        return 0

    sys.stdout.reconfigure(encoding="utf-8")
    results: dict = {"M2": {}, "M3": {}}
    with tempfile.TemporaryDirectory() as tmp:
        extract_core(args.baseline, Path(tmp))
        for suite in ("m2", "m3"):
            results["M2"][suite] = run_worker(Path(tmp), suite)
            results["M3"][suite] = run_worker(REPO, suite)
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "before_after.json").write_text(json.dumps({"baseline": args.baseline, "run_at": run_at, **results},
                                                      ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md = to_markdown(args.baseline, results, run_at)
    (OUT / "before_after.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
