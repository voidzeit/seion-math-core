"""POST HOC (not preregistered): does the per-node angle expression bound the observed error?

Candidate heterogeneous forms with sin(theta_v) = eta_v on non-root nodes and uniform M_hat:
  corner : |1 - prod_v cos(theta_v) e^{i theta_v}|                (stored in every run as
           per_node_angle_expression_exploratory)
  boxmax : max_{0 <= t_v <= theta_v} |1 - prod_v cos(t_v) e^{i t_v}|
Checks E_obs <= expr * M_hat^k * L on all registered runs (corner), and boxmax on every frozen
F7 instance whose run violates the corner form (only best restarts were frozen).
Writes artifacts/pmt_tn_benchmark/<DATE>-v1/posthoc/heterogeneous_angle_check.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import certificate as cert  # noqa: E402
import families_f7 as f7  # noqa: E402
from pmt_eval import evaluate  # noqa: E402

CAMPAIGNS = ["F1", "F2", "F3", "F4", "F6", "F7", "F7R"]


def boxmax(alphas, trials=64, seed=0):
    rng = np.random.default_rng(seed)
    f = lambda th: -abs(1 - np.prod(np.cos(th) * np.exp(1j * th)))
    bounds = [(0.0, a) for a in alphas]
    best = 0.0
    for t in range(trials):
        x0 = np.array(alphas) if t == 0 else rng.uniform(0, 1, len(alphas)) * np.array(alphas)
        res = minimize(f, x0, bounds=bounds, method="L-BFGS-B")
        best = max(best, -res.fun)
    return float(best)


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else "2026-09-13"
    base = ROOT / "artifacts" / "pmt_tn_benchmark" / f"{date}-v1"
    out = {"status": "POST_HOC_EXPLORATORY", "inputs_sha256": {}, "corner": {}, "boxmax_frozen_checks": []}
    for c in CAMPAIGNS:
        p = base / c / "runs.jsonl"
        out["inputs_sha256"][c] = hashlib.sha256(p.read_bytes()).hexdigest()
        n = viol = 0
        worst = 0.0
        where = Counter()
        for line in p.open(encoding="utf-8"):
            r = json.loads(line)
            if r["label"] != "WITHIN_CERTIFICATE":
                continue
            expr = r["per_node_angle_expression_exploratory"] * r["M_hat"] ** r["k"] * r["leaf_product"]
            n += 1
            if expr <= 0:
                continue
            q = r["E_obs"] / expr
            worst = max(worst, q)
            if q > 1 + 1e-9:
                viol += 1
                where[f'{r.get("variant")}/{r.get("topology")}/k{r.get("k_param", r["k"])}'] += 1
                if c == "F7" and "frozen_instance" in r:
                    d = json.load(open(base / c / r["frozen_instance"], encoding="utf-8"))
                    topo = d["topology"]
                    W = [np.array(w) for w in d["W"]]
                    U = [None if u is None else np.array(u) for u in d["U"]]
                    Z = [[np.array(z) for z in zs] for zs in d["Z"]]
                    o = evaluate(f7.build_nodes(topo, W, U, Z, d["M_hat"], "posthoc"), "root")
                    etas = [e for v, e in o["eta_nodes"].items() if not o["records"][v]["is_root"]]
                    al = [math.asin(min(e, 1.0)) for e in etas]
                    scale = d["M_hat"] ** o["k"] * o["leaf_product"]
                    out["boxmax_frozen_checks"].append({
                        "instance": r["frozen_instance"], "variant": r["variant"], "topology": r["topology"],
                        "k": o["k"], "angle_sum_over_pi": sum(al) / math.pi, "E_over_scale": o["E_obs"] / scale,
                        "corner": abs(1 - np.prod([math.cos(a) * complex(math.cos(a), math.sin(a)) for a in al])),
                        "boxmax": boxmax(al), "G_k_eta_max": cert.G_k(o["k"], min(max(etas), 1.0))})
        out["corner"][c] = {"runs": n, "violations": viol, "max_E_over_corner_bound": worst, "violations_by_config": dict(where)}
    outdir = base / "posthoc"
    outdir.mkdir(exist_ok=True)
    with open(outdir / "heterogeneous_angle_check.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({c: {k: v for k, v in d.items() if k != "violations_by_config"} for c, d in out["corner"].items()}, indent=1))
    print(json.dumps(out["boxmax_frozen_checks"], indent=1))


if __name__ == "__main__":
    main()
