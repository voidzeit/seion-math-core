"""Replay every recorded violation with (i) the proof angle theta* (sin theta* = |Qy|/prod rho),
(ii) a 4001-point theta grid, and (iii) the law rescaled by a fine certified norm bound.
A violation is CONFIRMED only if it survives all three.
usage: python replay_violations.py outputs/random_*.jsonl
"""
import glob, json, math, sys
import numpy as np
from states import contract, opnorm, gram_state, o1_violation, o2_violation

files = sys.argv[1:] or sorted(glob.glob("outputs/random_*.jsonl"))
report = []
for fn in files:
    lines = [json.loads(l) for l in open(fn)]
    order = "O1" if "_O1_" in fn else "O2"
    for rec in lines:
        if "summary" in rec or "lemma3" not in rec.get("type", ""):
            continue
        m, eta = rec["m"], rec["eta"]
        T = np.array(rec["mu"]); d = T.shape[0]
        _, ub = opnorm(T, m, fine=True)
        T = T / max(ub, 1.0)
        P = np.diag([1.0] * rec["P_rank"] + [0.0] * (d - rec["P_rank"]))
        F = [np.array(f) for f in rec["F"]]; R = [np.array(r) for r in rec["R"]]
        x = contract(T, F); y = contract(T, R)
        a, r, c, psi = gram_state(x, P @ y)
        zs = rec["child_chain_states_rho_chi"]
        rho_in = float(np.prod([z[0] for z in zs])); chi_in = float(np.sum([z[1] for z in zs]))
        TH = math.asin(eta)
        qy = float(np.linalg.norm(y - P @ y))
        ths = list(np.linspace(0, TH, 4001))
        if rho_in > 1e-15 and qy / rho_in <= eta + 1e-12:
            ths.append(math.asin(min(1.0, qy / rho_in)))
        best = np.inf; best_th = None; best_arg = None
        for th in ths:
            ro, co = rho_in * math.cos(th), chi_in + th
            if order == "O1":
                v, lam, phi = o1_violation(a, r, psi, ro, co); arg = (lam, phi)
            else:
                v = o2_violation(a, r, c, ro, co); arg = None
            if v < best:
                best, best_th, best_arg = v, th, arg
        report.append({"file": fn, "order": order, "m": m, "eta": eta, "recorded_v": rec["v_lemma3"],
                       "replayed_v": best, "theta": best_th, "lam_phi": best_arg,
                       "confirmed": bool(best > 1e-9), "law_kind": rec["law_kind"],
                       "out_state_a_r_c_psi": [a, r, c, psi], "child_chain_states": zs,
                       "child_states_a_r_psi": rec["child_states_a_r_psi"]})
json.dump(report, open("outputs/replay_report.json", "w"), indent=1)
conf = [r for r in report if r["confirmed"]]
print(json.dumps({"replayed": len(report), "confirmed": len(conf),
                  "confirmed_by_order": {o: sum(1 for r in conf if r["order"] == o) for o in ("O1", "O2")},
                  "max_replayed_v": max([r["replayed_v"] for r in report], default=None)}))
for r in conf[:10]:
    print(json.dumps({k: r[k] for k in ("order", "m", "eta", "replayed_v", "theta", "lam_phi", "law_kind", "out_state_a_r_c_psi", "child_chain_states", "child_states_a_r_psi")}))
