"""Choose the ABSTAIN coverage threshold from eval/calibration.yaml (NOT from the test cases).

    python -m eval.calibrate

Prints the top hit's coverage for every calibration question and the threshold that best separates
answerable from unanswerable questions (midpoint of the widest gap among the best-accuracy cuts).
Writes eval/results/calibration.md. The chosen value is then fixed in core/retrieval.py by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from core.access import filter_for
from core.loader import load_kb
from core.retrieval import search

ROOT = Path(__file__).resolve().parent


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    kb = load_kb()
    cfg = yaml.safe_load((ROOT / "calibration.yaml").read_text(encoding="utf-8"))
    rows = []
    for q in cfg["questions"]:
        user = kb.users[q["persona"]]
        hits = search(q["question"], filter_for(kb, user, cfg["as_of"]).sections)
        top = hits[0] if hits else None
        rows.append({
            **q,
            "coverage": round(top.coverage, 3) if top else 0.0,
            "top": top.section.id if top else "—",
            "top_ok": (top is not None and q.get("expected_doc") == top.section.doc.key) if q["answerable"] else None,
        })

    values = sorted({r["coverage"] for r in rows})
    cuts = [(a + b) / 2 for a, b in zip(values, values[1:])] or [0.5]

    def accuracy(t: float) -> int:
        return sum((r["coverage"] >= t) == r["answerable"] for r in rows)

    best_acc = max(accuracy(t) for t in cuts)
    best = [t for t in cuts if accuracy(t) == best_acc]
    # Among equally accurate cuts, prefer the one sitting in the widest gap between observed values.
    def gap(t: float) -> float:
        below = max((v for v in values if v < t), default=0.0)
        above = min((v for v in values if v >= t), default=1.0)
        return above - below

    threshold = round(max(best, key=gap), 2)

    lines = [
        "# Hiệu chỉnh ngưỡng ABSTAIN",
        "",
        f"Bộ câu hỏi: `eval/calibration.yaml` ({len(rows)} câu, tách riêng khỏi bộ kiểm thử).",
        "",
        "| Persona | Câu hỏi | Trả lời được? | Độ phủ mục đầu | Mục đầu | Đúng tài liệu? |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda r: r["coverage"]):
        ok = "—" if r["top_ok"] is None else ("có" if r["top_ok"] else "không")
        lines.append(
            f"| {r['persona']} | {r['question']} | {'có' if r['answerable'] else 'không'} | "
            f"{r['coverage']:.3f} | {r['top']} | {ok} |"
        )
    lines += ["", f"**Ngưỡng đề xuất: {threshold}** (phân loại đúng {best_acc}/{len(rows)} câu)."]
    out = ROOT / "results" / "calibration.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
