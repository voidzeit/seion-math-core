"""Is the same-law S_2 shortfall a landscape deficit, or an unconverged optimizer?

The differentiable sweep of 2026-08-18 put `S_2^same-mu` at 0.936-0.985 of
`Sigma_2(eta)` in D=2 -- far above the 0.835 the frozen-gradient harness
reported, but still short. A shortfall from a MAXIMIZER is a lower bound and
proves nothing on its own: the same-law class is a constrained problem, so it
converges more slowly than the free class by construction.

WHAT THIS CAN AND CANNOT SHOW. Even a perfect plateau does NOT establish
`S_2^same-mu < Sigma_2`. It establishes only

    a persistent class-specific search deficit under the tested
    optimizer and budget

which is a statement about this instrument, not about the constant. Turning it
into a strict inequality needs an analytic upper bound, an exact reduction, or a
global certification -- never a stubborn maximizer. The outcome labels below are
worded to keep that line visible.

METHOD. The free class is the calibration: it attains `Sigma_2` by Theorem 5.1,
witness-verified, so its shortfall at each effort level is pure optimizer
residual -- an empirical noise floor for the instrument at that budget. Writing

    d_f(E) = 1 - S_free(E) / Sigma_2        d_s(E) = 1 - S_same(E) / Sigma_2

the informative quantities are not `d_s` alone but

    Delta(E) = d_s(E) - d_f(E)              excess over the demonstrated floor
    R(E)     = d_s(E) / max(d_f(E), eps)    how many noise floors it sits at

`R` is reported alongside `Delta` and never alone, because it diverges as
`d_f -> 0`.

Because the search is stochastic, a bigger budget can return a worse draw. All
gates therefore use the BEST-SO-FAR ENVELOPE

    dbar(E_j) = min over i <= j of d(E_i)

which is monotone by construction and is the honest reading of "resolution
demonstrated by this instrument at budget E_j or below".

Effort is measured in effective evaluations, `restarts * steps * cells`, and in
wall time -- not in `steps` alone, since a rung that doubles restarts and one
that doubles steps are not the same experiment.

PRE-REGISTERED, before any same-mu number is read:

    CALIBRATION_GATE   dbar_f(E_last) / dbar_f(E_first) < 0.25
                       The control's demonstrated resolution must improve at
                       least 4x across the ladder. If it does not, the ladder is
                       too short to resolve anything and NO reading about
                       same-mu is licensed, however flat same-mu looks.

    OPTIMIZATION_LIMITED           dbar_s decays at a rate comparable to dbar_f
                                   -> S_2^same-mu = Sigma_2 remains plausible
    PERSISTENT_RESTRICTED_DEFICIT  dbar_f collapses while dbar_s plateaus
                                   -> a same-law rigidity-gap CANDIDATE

The label `RIGIDITY_GAP` is deliberately not available to this script.

The harness itself is NOT reimplemented here -- `rg_fused_search.py` is invoked
as a subprocess with `--differentiable` and its JSON is read back. One
mathematical engine, many campaigns interrogating it; reimplementing the search
to study the search is how the frozen gradient survived as long as it did.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NUMERICAL_FLOOR = 1e-12


def run_search(steps, per_cell, dims, etas, extra):
    """Invoke the verified harness; return (runs, wall_seconds)."""
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "sweep.json"
        command = [sys.executable, str(HERE / "rg_fused_search.py"),
                   "--objectives", "S",
                   "--classes", "free", "same_law_same_P",
                   "--dims", *[str(d) for d in dims],
                   "--etas", *[repr(e) for e in etas],
                   "--steps", str(steps),
                   "--per-cell", str(per_cell),
                   "--differentiable",
                   "--json", str(target)]
        command += extra
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=str(HERE), capture_output=True,
                                   text=True)
        elapsed = time.perf_counter() - started
        if completed.returncode != 0:
            print(completed.stdout[-3000:])
            print(completed.stderr[-3000:], file=sys.stderr)
            raise SystemExit(f"search failed at steps={steps} "
                             f"per_cell={per_cell}")
        written = target if target.exists() else HERE / target.name
        return json.loads(written.read_text(encoding="utf-8"))["runs"], elapsed


def shortfalls(runs, class_name):
    """Per-cell relative shortfall, keyed by (dim, eta)."""
    return {(row["dim"], round(row["eta"], 6)):
            1.0 - row["best"] / row["ceiling"]
            for row in runs if row["class"] == class_name
            and row["ceiling"] > 0}


def envelope(values):
    """Best-so-far: monotone by construction, immune to a bad stochastic draw."""
    out, best = [], float("inf")
    for value in values:
        best = min(best, value)
        out.append(best)
    return np.array(out)


def fit_floor(effort, deficit):
    """Diagnostic only: does d(E) = d_inf + a E^-p want d_inf > 0?

    Three or four points against three parameters is fragile by construction.
    Reported as a discriminator between two shapes, never as a statistical test.
    """
    try:
        from scipy.optimize import curve_fit
    except ImportError:
        return None
    effort = np.asarray(effort, dtype=float)
    deficit = np.asarray(deficit, dtype=float)
    if effort.size < 3 or not np.all(np.isfinite(deficit)):
        return None
    scale = effort / effort[0]

    def with_floor(x, floor, amplitude, power):
        return floor + amplitude * x ** (-power)

    def to_zero(x, amplitude, power):
        return amplitude * x ** (-power)

    result = {}
    try:
        popt, _ = curve_fit(to_zero, scale, deficit,
                            p0=[max(deficit[0], 1e-9), 0.5],
                            bounds=([0, 0], [np.inf, 5]), maxfev=20000)
        residual = deficit - to_zero(scale, *popt)
        result["to_zero"] = {"amplitude": float(popt[0]),
                             "power": float(popt[1]),
                             "sse": float((residual ** 2).sum())}
    except Exception:
        result["to_zero"] = None
    if effort.size >= 4:
        try:
            popt, _ = curve_fit(with_floor, scale, deficit,
                                p0=[min(deficit) * 0.5,
                                    max(deficit[0], 1e-9), 0.5],
                                bounds=([0, 0, 0], [np.inf, np.inf, 5]),
                                maxfev=20000)
            residual = deficit - with_floor(scale, *popt)
            result["with_floor"] = {"floor": float(popt[0]),
                                    "amplitude": float(popt[1]),
                                    "power": float(popt[2]),
                                    "sse": float((residual ** 2).sum())}
        except Exception:
            result["with_floor"] = None
    else:
        result["with_floor"] = None
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dims", type=int, nargs="+", default=[2])
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.35, 0.5, 0.7071067811865476])
    parser.add_argument("--efforts", type=int, nargs="+",
                        default=[300, 600, 1200, 2400])
    parser.add_argument("--per-cell", type=int, nargs="+",
                        default=[2048, 4096, 8192, 16384])
    parser.add_argument("--grade-strength", type=int, nargs=2,
                        default=[64, 40])
    parser.add_argument("--finalists", type=int, default=24)
    parser.add_argument("--calibration-q", type=float, default=0.25,
                        help="PRE-REGISTERED: required improvement factor in "
                             "the control's best-so-far resolution")
    parser.add_argument("--json", type=str, default="rg_s2_convergence.json")
    args = parser.parse_args()

    if len(args.efforts) != len(args.per_cell):
        raise SystemExit("--efforts and --per-cell must have the same length")

    extra = ["--grade-strength", *[str(v) for v in args.grade_strength],
             "--finalists", str(args.finalists)]
    cells = len(args.dims) * len(args.etas)

    print(f"dims {args.dims}, etas {args.etas}")
    print(f"PRE-REGISTERED calibration gate: dbar_free must improve by "
          f"{1 / args.calibration_q:.0f}x across the ladder.")
    print("free is the CALIBRATION: it attains Sigma_2, so its shortfall is "
          "the instrument's noise floor.\n")
    print(f"{'steps':>7} {'restarts':>9} {'evals':>12} {'wall_s':>8} "
          f"{'d_free':>11} {'d_same':>11} {'Delta':>11} {'R':>9}")

    records, free_curve, same_curve, efforts = [], [], [], []
    detail = {}
    for steps, restarts in zip(args.efforts, args.per_cell):
        runs, elapsed = run_search(steps, restarts, args.dims, args.etas, extra)
        free_cells = shortfalls(runs, "free")
        same_cells = shortfalls(runs, "same_law_same_P")
        free = float(np.median(list(free_cells.values())))
        same = float(np.median(list(same_cells.values())))
        evaluations = restarts * steps * cells
        gap = same - free
        ratio = same / max(free, NUMERICAL_FLOOR)
        free_curve.append(free)
        same_curve.append(same)
        efforts.append(evaluations)
        detail[str(steps)] = {
            "free": {str(k): v for k, v in free_cells.items()},
            "same_law_same_P": {str(k): v for k, v in same_cells.items()}}
        print(f"{steps:7d} {restarts:9d} {evaluations:12,d} {elapsed:8.1f} "
              f"{free:11.3e} {same:11.3e} {gap:11.3e} {ratio:8.0f}x")
        records.append({"steps": steps, "restarts": restarts,
                        "effective_evaluations": evaluations,
                        "wall_seconds": elapsed,
                        "d_free": free, "d_same": same,
                        "delta": gap, "ratio": ratio})

    free_bar = envelope(free_curve)
    same_bar = envelope(same_curve)

    print("\nbest-so-far envelopes (monotone by construction)")
    print(f"{'evals':>12} {'dbar_free':>12} {'dbar_same':>12} {'Delta_bar':>12}")
    for evaluations, low, high in zip(efforts, free_bar, same_bar):
        print(f"{evaluations:12,d} {low:12.3e} {high:12.3e} {high - low:12.3e}")

    free_improvement = free_bar[-1] / free_bar[0] if free_bar[0] > 0 else 1.0
    same_improvement = same_bar[-1] / same_bar[0] if same_bar[0] > 0 else 1.0

    print("\nCALIBRATION GATE (pre-registered)")
    print(f"  dbar_free improved by {1 / max(free_improvement, 1e-300):.1f}x "
          f"(required {1 / args.calibration_q:.0f}x)")
    calibrated = free_improvement < args.calibration_q

    verdict = None
    if not calibrated:
        verdict = "CALIBRATION_FAIL"
        print("\n  VERDICT: CALIBRATION_FAIL")
        print("  The control's resolution did not improve enough across this")
        print("  ladder, so it cannot certify that extra budget resolves")
        print("  anything. NO CONCLUSION ABOUT SAME-MU is licensed, however")
        print("  flat the same-law curve looks. Extend the ladder and rerun.")
    else:
        print("  passed: extra budget demonstrably sharpens the instrument.\n")
        fit = fit_floor(efforts, same_bar)
        print("READING")
        print(f"  dbar_free shrank to {100 * free_improvement:.2f}% of its "
              f"starting value")
        print(f"  dbar_same shrank to {100 * same_improvement:.2f}% of its "
              f"starting value")
        if fit and fit.get("with_floor") and fit.get("to_zero"):
            floor = fit["with_floor"]["floor"]
            print(f"\n  diagnostic shape fit (FRAGILE: "
                  f"{len(efforts)} points, 3 parameters)")
            print(f"    d_s = a E^-p            sse {fit['to_zero']['sse']:.3e}")
            print(f"    d_s = d_inf + a E^-p    sse "
                  f"{fit['with_floor']['sse']:.3e}, d_inf {floor:.3e}")

        if same_improvement > 0.7 and free_improvement < 0.5:
            verdict = "PERSISTENT_RESTRICTED_DEFICIT"
            print("\n  VERDICT: PERSISTENT_RESTRICTED_DEFICIT")
            print("  The same-law shortfall plateaus while the control's floor")
            print("  collapses under identical budget. This is valid numerical")
            print("  evidence for a same-law rigidity-gap CANDIDATE -- a")
            print("  persistent class-specific search deficit under the tested")
            print("  optimizer and budget. It is NOT the inequality")
            print("  S_2^same-mu < Sigma_2, which needs an analytic upper")
            print("  bound or an exact reduction.")
        elif same_improvement < 0.5:
            verdict = "OPTIMIZATION_LIMITED"
            print("\n  VERDICT: OPTIMIZATION_LIMITED")
            print("  The same-law shortfall falls at a rate comparable to the")
            print("  control's. It reads as optimizer residual, not rigidity;")
            print("  S_2^same-mu = Sigma_2 remains plausible.")
        else:
            verdict = "INCONCLUSIVE"
            print("\n  VERDICT: INCONCLUSIVE at this ladder. Extend it before")
            print("  reading anything into the shortfall.")

    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "verdict": verdict,
         "calibrated": bool(calibrated),
         "curve": records,
         "envelope": {"effective_evaluations": efforts,
                      "dbar_free": free_bar.tolist(),
                      "dbar_same": same_bar.tolist()},
         "shape_fit": fit_floor(efforts, same_bar) if calibrated else None,
         "per_cell": detail}, indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
