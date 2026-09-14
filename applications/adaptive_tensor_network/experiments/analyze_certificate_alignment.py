"""Analysis for M36: certificate-objective alignment.

Four levels, in increasing order of what an allocator actually needs:
  A. prediction   R^2 of the certificate delta against the true delta
  B. ranking      Spearman, Kendall
  C. decision     top-1 agreement, top-3 / top-5 overlap
  D. regret       dE(argmin certificate) - min dE, normalized by the spread

Plus sign agreement, which asks whether a certificate can detect that adding
rank may make the true objective worse.

The hierarchy under test is G <= B <= A in tightness. If ranking fidelity
follows tightness, rho(A) < rho(B) < rho(G) and Papers B and C connect. If it
does not, tight upper bounds and good decision surrogates are distinct objects
-- which is also a clean result.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import bootstrap_ci, spearman_corr  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
SURROGATES = ("dA", "dB", "dG")
LABELS = {"dA": "A scalar/Frobenius", "dB": "B restricted (M24)",
          "dG": "G Gram-aware (M25)"}


def kendall_tau(x, y) -> float:
    n = len(x)
    concordant = discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            a = (x[i] - x[j]) * (y[i] - y[j])
            if a > 0:
                concordant += 1
            elif a < 0:
                discordant += 1
    total = concordant + discordant
    return (concordant - discordant) / total if total else float("nan")


def evaluate_state(state: dict, key: str) -> dict:
    truth = np.array([c["dE"] for c in state["candidates"]])
    pred = np.array([c[key] for c in state["candidates"]])
    order_t = np.argsort(truth)
    order_p = np.argsort(pred)

    ss_tot = float(np.sum((truth - truth.mean()) ** 2))
    ss_res = float(np.sum((truth - pred) ** 2))
    spread = float(truth.max() - truth.min())
    regret = (truth[order_p[0]] - truth[order_t[0]]) / spread if spread > 0 else 0.0

    result = {
        "r2": 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan"),
        "spearman": spearman_corr(list(pred), list(truth)),
        "kendall": kendall_tau(list(pred), list(truth)),
        "top1": 1.0 if order_p[0] == order_t[0] else 0.0,
        "top3": len(set(order_t[:3]) & set(order_p[:3])) / 3.0,
        "top5": len(set(order_t[:5]) & set(order_p[:5])) / 5.0,
        "regret": regret,
        "sign_agree": float(np.mean(np.sign(pred) == np.sign(truth))),
        "frac_pred_negative": float(np.mean(pred < 0)),
        "frac_true_negative": float(np.mean(truth < 0)),
    }
    values = [c.get("V") for c in state["candidates"]]
    if all(v is not None for v in values):
        result["spearman_vs_terminal"] = spearman_corr(list(pred), values)
    return result


def main() -> None:
    payload = json.loads((RESULTS_DIR / "certificate_alignment_raw.json").read_text(encoding="utf-8"))
    states = payload["states"]
    print(f"Loaded {len(states)} probed states "
          f"({len(states[0]['candidates'])} candidates each).\n")

    # How well does the one-step objective itself track terminal value?
    e_terminal = []
    for state in states:
        values = [c.get("V") for c in state["candidates"]]
        if all(v is not None for v in values):
            e_terminal.append(spearman_corr([c["dE"] for c in state["candidates"]], values))

    grouped = defaultdict(lambda: defaultdict(list))
    for state in states:
        for key in SURROGATES:
            for metric, value in evaluate_state(state, key).items():
                if value == value:
                    grouped[key][metric].append(value)

    rows = []
    print("=== certificate vs true one-step objective (all states pooled) ===")
    print(f"{'surrogate':>22} {'R2':>8} {'Spearman':>20} {'Kendall':>8} "
          f"{'top1':>6} {'top3':>6} {'top5':>6} {'regret':>7} {'sign':>6}")
    for key in SURROGATES:
        data = grouped[key]
        mean, lo, hi = bootstrap_ci(data["spearman"])
        entry = {"surrogate": LABELS[key]}
        entry.update({metric: statistics.fmean(values)
                      for metric, values in data.items()})
        entry["spearman_ci"] = [lo, hi]
        rows.append(entry)
        print(f"{LABELS[key]:>22} {entry['r2']:8.3f} "
              f"{mean:+.3f} [{lo:+.3f},{hi:+.3f}] {entry['kendall']:8.3f} "
              f"{entry['top1']:6.2f} {entry['top3']:6.2f} {entry['top5']:6.2f} "
              f"{entry['regret']:7.3f} {entry['sign_agree']:6.2f}")

    print("\n=== non-monotonicity detection ===")
    print(f"{'surrogate':>22} {'frac delta<0 predicted':>24} {'frac true<0':>13}")
    for key in SURROGATES:
        entry = grouped[key]
        print(f"{LABELS[key]:>22} {statistics.fmean(entry['frac_pred_negative']):24.3f} "
              f"{statistics.fmean(entry['frac_true_negative']):13.3f}")

    if e_terminal:
        print("\n=== alignment with TERMINAL value V(r+a), m=8 ===")
        mean, lo, hi = bootstrap_ci(e_terminal)
        print(f"{'true one-step dE':>22} {mean:+.3f} [{lo:+.3f},{hi:+.3f}]")
        for key in SURROGATES:
            values = grouped[key].get("spearman_vs_terminal")
            if values:
                mean, lo, hi = bootstrap_ci(values)
                print(f"{LABELS[key]:>22} {mean:+.3f} [{lo:+.3f},{hi:+.3f}]")

    with (RESULTS_DIR / "m36_alignment_table.csv").open("w", newline="",
                                                        encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (RESULTS_DIR / "m36_analysis.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    print("\nWrote results/m36_analysis.json and results/m36_alignment_table.csv")


if __name__ == "__main__":
    main()
