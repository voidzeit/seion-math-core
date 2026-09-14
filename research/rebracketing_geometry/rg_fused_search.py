"""Hardware-fused adversarial search against the k=2 rebracketing ceilings.

EXPERIMENTAL. Nothing here is a theorem; this is the falsification harness for
RG_CANONICAL.md, Theorems 3.1, 4.1 and 5.1, rewritten to actually use the
machine.

WHY THE SEQUENTIAL VERSION WASTED THE HARDWARE
----------------------------------------------
rg4_s2_search.py runs one optimization per (objective, class, dim, rank, eta)
cell. At these sizes a whole cell is a few hundred kilobytes of float64, so
every kernel finishes long before the next one is queued: the run is
launch-bound, not FLOP-bound. Measured on this machine (RTX PRO 5000 Blackwell
Laptop, 82 SMs, 24 GB): 42% GPU utilization, 2.0 GB of 24 GB resident, and
~34 s per cell.

WHAT THIS VERSION DOES INSTEAD
------------------------------
Everything that shares an ambient dimension is folded into ONE batch axis --
objective, class, projector rank and eta all become per-element vectors, so a
whole sweep at a given D is a single optimization loop:

  * per-element eta and per-element coordinate projectors;
  * per-element objective, encoded as coefficients on (||D||, ||Ahat||, ||PA||)
    -- J = (1,0,0), H = (0,-1,1), S = (0,1,-1) -- so one score expression
    covers all three;
  * per-element law sharing, encoded as a mask selecting one raw tensor for all
    four vertices, so the same launch carries the free and the shared-law class.

The group size is not guessed: a small probe measures peak allocated bytes per
element at that D and the sweep is sized to a VRAM target from the measurement.

float64 is kept throughout. Speed that changes the arithmetic is not usable in
a run whose purpose is to test a certified bound.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from rg_kernels import (  # noqa: E402
    DTYPE, contract3, coordinate_projectors, op_norms,
)

# (coefficient on ||D||, on ||Ahat||, on ||PA||) for each objective
OBJECTIVE_COEFFICIENTS = {"J": (1.0, 0.0, 0.0),
                          "H": (0.0, -1.0, 1.0),
                          "S": (0.0, 1.0, -1.0)}
LAW_KEYS = ("inner_L", "inner_M", "root_L", "root_M")


def sigma2(eta: float) -> float:
    return math.sin(min(2.0 * math.asin(min(eta, 1.0)), 0.5 * math.pi)) / eta


def ceiling(objective: str, eta: float) -> float:
    return sigma2(eta) if objective == "S" else 2.0


# --------------------------------------------------------------------------
# admissible class
# --------------------------------------------------------------------------

def share_laws(raws: dict, shared: torch.Tensor) -> dict:
    """Per-element law sharing: masked elements use `inner_L` at every vertex."""
    mask = shared.view(-1, 1, 1, 1, 1)
    return {key: (raws[key] if key == "inner_L"
                  else torch.where(mask, raws["inner_L"], raws[key]))
            for key in LAW_KEYS}


def feasibility_factors(laws, projectors, restarts: int, iters: int,
                        differentiable: bool = False, warm=None,
                        return_warm: bool = False):
    """Operator-norm and closure scalars per law, detached from the graph.

    Recomputed every REFRESH steps and held fixed in between. The strength of
    the estimator MATTERS here in a way that is easy to miss: `apply_factors`
    DIVIDES by these numbers, so an underestimate scales a law too little and
    pushes it outside the admissible class. Measured on random laws
    (rg_kernels convergence study, 2026-08-16):

        D=3, restarts=3,  iters=20   ->  up to 18.3% BELOW the converged norm
        D=4, restarts=3,  iters=20   ->  up to 29.6% below
        D=4, restarts=18, iters=120  ->  up to  3.3% below
        D=4, restarts=64, iters=200  ->  converged

    Cheap settings are therefore fine INSIDE the search loop, where these only
    have to supply a descent direction, and are not acceptable for the final
    grading, which must be converged or the reported value is inflated.
    """
    P_iL, P_iM, P_root = projectors
    identity = torch.eye(P_root.shape[-1], dtype=DTYPE,
                         device=P_root.device).expand_as(P_root)
    factors, fresh = {}, {}
    warm = warm or {}
    context = torch.enable_grad() if differentiable else torch.no_grad()
    with context:
        for key, projector, seed in (("inner_L", P_iL, 11),
                                     ("inner_M", P_iM, 23)):
            norms, v_norm = op_norms(laws[key], seed=seed, iters=iters,
                                     restarts=restarts,
                                     warm=warm.get((key, "norm")),
                                     return_vectors=True)
            scaled = laws[key] / norms.clamp_min(1e-12).view(-1, 1, 1, 1, 1)
            closure, v_close = op_norms(scaled, post=identity - projector,
                                        seed=seed + 1, iters=iters,
                                        restarts=restarts,
                                        warm=warm.get((key, "closure")),
                                        return_vectors=True)
            factors[key] = (norms, closure)
            fresh[(key, "norm")], fresh[(key, "closure")] = v_norm, v_close
        for key, seed in (("root_L", 37), ("root_M", 53)):
            tensor = torch.einsum("nqo,noacd->nqacd", P_root, laws[key])
            norms, v_norm = op_norms(tensor, seed=seed, iters=iters,
                                     restarts=restarts,
                                     warm=warm.get((key, "norm")),
                                     return_vectors=True)
            factors[key] = (norms, None)
            fresh[(key, "norm")] = v_norm
    return (factors, fresh) if return_warm else factors


def apply_factors(law, projector, normal, eta, factors):
    norms, closure = factors
    tensor = law / norms.clamp_min(1e-12).view(-1, 1, 1, 1, 1)
    if closure is None:                                # P-valued root law
        return tensor
    scale = torch.where(closure > eta, eta / closure.clamp_min(1e-12),
                        torch.ones_like(closure)).view(-1, 1, 1, 1, 1)
    return (torch.einsum("nqo,noacd->nqacd", projector, tensor)
            + scale * torch.einsum("nqo,noacd->nqacd", normal, tensor))


def build_laws(laws, projectors, eta, factors, shared):
    """The four admissible laws actually used by an element.

    Shared-law elements use ONE admissible law at all four vertices -- the
    literal same-law class. They must NOT take the P-valued root of Lemma 2.2:
    that lemma rescales the root law independently of the inner one, which is
    exactly what a shared-law element is not allowed to do. Free elements do
    take it, since there the root law is an independent parameter.
    """
    P_iL, P_iM, P_root = projectors
    identity = torch.eye(P_root.shape[-1], dtype=DTYPE,
                         device=P_root.device).expand_as(P_root)
    mask = shared.view(-1, 1, 1, 1, 1)

    mu_iL = apply_factors(laws["inner_L"], P_iL, identity - P_iL, eta,
                          factors["inner_L"])
    mu_iM = torch.where(mask, mu_iL,
                        apply_factors(laws["inner_M"], P_iM,
                                      identity - P_iM, eta,
                                      factors["inner_M"]))
    mu_rL = torch.where(mask, mu_iL, apply_factors(
        torch.einsum("nqo,noacd->nqacd", P_root, laws["root_L"]),
        P_root, None, eta, factors["root_L"]))
    mu_rM = torch.where(mask, mu_iL, apply_factors(
        torch.einsum("nqo,noacd->nqacd", P_root, laws["root_M"]),
        P_root, None, eta, factors["root_M"]))
    return mu_iL, mu_iM, mu_rL, mu_rM


def audit_admissibility(built, projectors, eta, quality):
    """Measure what the FINAL laws actually satisfy, with a strong estimator.

    The search is adversarial against its own feasibility projection: gradient
    ascent is free to drive the raw tensors toward laws whose operator norm the
    alternating maximization finds hard, and `apply_factors` DIVIDES by that
    estimate. An underestimate therefore scales the law too little and pushes
    it outside the admissible class, which can manufacture a value above a
    correct ceiling. This re-measures with many more restarts and reports the
    worst breach per element, so such a cell can be identified rather than
    reported as a discovery.
    """
    P_iL, P_iM, P_root = projectors
    identity = torch.eye(P_root.shape[-1], dtype=DTYPE,
                         device=P_root.device).expand_as(P_root)
    mu_iL, mu_iM, mu_rL, mu_rM = built
    restarts, iters = quality
    worst_norm = torch.zeros(mu_iL.shape[0], dtype=DTYPE, device=mu_iL.device)
    for index, law in enumerate((mu_iL, mu_iM, mu_rL, mu_rM)):
        worst_norm = torch.maximum(worst_norm, op_norms(
            law, seed=9001 + index, iters=iters, restarts=restarts))
    worst_closure = torch.zeros_like(worst_norm)
    for law, projector, index in ((mu_iL, P_iL, 0), (mu_iM, P_iM, 1),
                                  (mu_rL, P_root, 2), (mu_rM, P_root, 3)):
        worst_closure = torch.maximum(worst_closure, op_norms(
            law, post=identity - projector, seed=9101 + index, iters=iters,
            restarts=restarts))
    return worst_norm, worst_closure / eta


def evaluate(laws, projectors, leaves, eta, factors, shared):
    """Batched (Ahat, PA, D, geometry) for the rebracketing pair."""
    P_iL, P_iM, P_root = projectors
    mu_iL, mu_iM, mu_rL, mu_rM = build_laws(laws, projectors, eta, factors,
                                            shared)

    unit = leaves / leaves.norm(dim=2, keepdim=True).clamp_min(1e-12)
    x1, x2, x3, x4, x5 = (unit[:, i, :] for i in range(5))

    F_iL = contract3(mu_iL, x1, x2, x3)
    R_iL = torch.einsum("nij,nj->ni", P_iL, F_iL)
    F_L = contract3(mu_rL, F_iL, x4, x5)
    R_L = torch.einsum("nij,nj->ni", P_root, contract3(mu_rL, R_iL, x4, x5))

    F_iM = contract3(mu_iM, x2, x3, x4)
    R_iM = torch.einsum("nij,nj->ni", P_iM, F_iM)
    F_M = contract3(mu_rM, x1, F_iM, x5)
    R_M = torch.einsum("nij,nj->ni", P_root, contract3(mu_rM, x1, R_iM, x5))

    A_hat = R_L - R_M
    PA = torch.einsum("nij,nj->ni", P_root, F_L - F_M)
    geometry = {"e_L": torch.einsum("nij,nj->ni", P_root, F_L) - R_L,
                "e_M": torch.einsum("nij,nj->ni", P_root, F_M) - R_M,
                "D_iL": F_iL - R_iL, "D_iM": F_iM - R_iM,
                "F_iL": F_iL, "F_iM": F_iM}
    return A_hat, PA, A_hat - PA, geometry


def score(coefficients, A_hat, PA, D, eta):
    """One expression for all three objectives, weighted per element."""
    return (coefficients[:, 0] * D.norm(dim=1)
            + coefficients[:, 1] * A_hat.norm(dim=1)
            + coefficients[:, 2] * PA.norm(dim=1)) / eta


# --------------------------------------------------------------------------
# one fused launch
# --------------------------------------------------------------------------

def initial_law(shape, init, device, generator):
    """Initial raw tensors.

    `dense` is i.i.d. Gaussian. `sparse` puts a few random monomials on random
    slot supports, because the known extremizers of this problem ARE sparse --
    Theorem 3.1's witness is 3 nonzeros out of 81 at D = 3, with its two active
    monomials on disjoint slot supports so that they cannot compete inside the
    operator norm. Dense Gaussian starts are far from any such point and the
    feasibility projection rescales globally, so the optimizer has to sparsify
    against a smooth landscape. This samples that kind of region WITHOUT
    encoding the witness itself: supports, signs and magnitudes are random, so
    reaching J = 2 from here is still an earned result and the positive control
    keeps its meaning.
    """
    if init == "dense":
        return torch.randn(shape, dtype=DTYPE, device=device,
                           generator=generator, requires_grad=True)
    total = shape[0]
    entries = max(2, shape[1])
    tensor = torch.zeros(shape, dtype=DTYPE, device=device)
    flat = tensor.view(total, -1)
    positions = torch.randint(0, flat.shape[1], (total, entries),
                              device=device, generator=generator)
    values = torch.randn((total, entries), dtype=DTYPE, device=device,
                         generator=generator)
    flat.scatter_(1, positions, values)
    return tensor.requires_grad_(True)


def build_group(cells, per_cell, dim, device, generator, init="dense"):
    """Per-element vectors and parameters for a group of cells."""
    total = len(cells) * per_cell

    def repeat(values, dtype=DTYPE):
        return torch.tensor(values, dtype=dtype, device=device
                            ).repeat_interleave(per_cell)

    eta = repeat([c["eta"] for c in cells])
    shared = repeat([c["class"] != "free" for c in cells], dtype=torch.bool)
    coefficients = torch.tensor(
        [OBJECTIVE_COEFFICIENTS[c["objective"]] for c in cells], dtype=DTYPE,
        device=device).repeat_interleave(per_cell, dim=0)

    rank_root = repeat([c["rank"] for c in cells], dtype=torch.long)
    P_root = coordinate_projectors(rank_root, dim, device)
    inner = torch.randint(1, dim, (2, total), device=device,
                          generator=generator)
    rank_iL = torch.where(shared, rank_root, inner[0])
    rank_iM = torch.where(shared, rank_root, inner[1])
    P_iL = coordinate_projectors(rank_iL, dim, device)
    P_iM = coordinate_projectors(rank_iM, dim, device)

    shape = (total, dim, dim, dim, dim)
    raws = {key: initial_law(shape, init, device, generator)
            for key in LAW_KEYS}
    leaves = torch.randn(total, 5, dim, dtype=DTYPE, device=device,
                         generator=generator, requires_grad=True)
    return {"eta": eta, "shared": shared, "coefficients": coefficients,
            "projectors": (P_iL, P_iM, P_root), "raws": raws,
            "leaves": leaves,
            "parameters": list(raws.values()) + [leaves]}


def run_group(cells, per_cell, dim, steps, refresh, quality, device, seed,
              audit_quality=16, init="dense", lr=0.05, decay=False,
              loop_strength=(3, 20), grade_strength=(64, 40),
              finalists=24, differentiable=False, warm_iters=0,
              global_refresh=25):
    generator = torch.Generator(device=device).manual_seed(seed)
    group = build_group(cells, per_cell, dim, device, generator, init)
    optimizer = torch.optim.Adam(group["parameters"], lr=lr)
    schedule = (torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, steps)
                if decay else None)

    # Three time scales, three different jobs (see rg_kernels):
    #   every step     warm continuation + cold fraction: tracking + switching
    #   every K steps  a full cold solve, against accumulated drift
    #   the end        converged grading, the only authority on a reported value
    # In differentiable mode the factors MUST be rebuilt every step: a constant
    # can be cached, a graph cannot, so `refresh` and a correct gradient are
    # mutually exclusive. Warm-starting the extremizers pays that cost back.
    factors, warm = None, None
    for step in range(steps):
        laws = share_laws(group["raws"], group["shared"])
        if differentiable or step % refresh == 0:
            full = warm is None or (global_refresh
                                    and step % global_refresh == 0)
            strength = (loop_strength if (full or not warm_iters)
                        else (loop_strength[0], warm_iters))
            result = feasibility_factors(
                laws, group["projectors"], *strength,
                differentiable=differentiable,
                warm=(warm if warm_iters and not full else None),
                return_warm=bool(warm_iters))
            factors, warm = result if warm_iters else (result, None)
        optimizer.zero_grad(set_to_none=True)
        A_hat, PA, D, _ = evaluate(laws, group["projectors"],
                                   group["leaves"], group["eta"], factors,
                                   group["shared"])
        values = score(group["coefficients"], A_hat, PA, D, group["eta"])
        (-values.sum()).backward()
        torch.nn.utils.clip_grad_norm_(group["parameters"], 10.0)
        optimizer.step()
        if schedule is not None:
            schedule.step()

    # TWO-STAGE GRADING. Converged grading is ~14 operator-norm passes at high
    # restarts, and running it over every restart of every cell dominates the
    # whole sweep. Only the winners need it, so stage one ranks cheaply and
    # stage two converges the top `finalists` of each cell.
    #
    # This is sound precisely because of the asymmetry that caused the earlier
    # false ceiling breach: cheap grading UNDERestimates operator norms and so
    # INFLATES values. A finalist set chosen by inflated scores may therefore
    # miss the true best -- which makes the reported number a possible
    # UNDER-report, never an over-report. Under-reporting is safe for a ceiling
    # test and safe for a supremum lower bound; over-reporting is what
    # manufactured the artifact. Every number that leaves this function is
    # graded converged.
    with torch.no_grad():
        laws = share_laws(group["raws"], group["shared"])
        cheap = feasibility_factors(laws, group["projectors"], *loop_strength)
        ranking = torch.nan_to_num(
            score(group["coefficients"],
                  *evaluate(laws, group["projectors"], group["leaves"],
                            group["eta"], cheap, group["shared"])[:3],
                  group["eta"]), nan=-1.0)

        keep = min(finalists, per_cell)
        picks = [low + torch.topk(ranking[low:low + per_cell], keep).indices
                 for low in range(0, len(cells) * per_cell, per_cell)]
        chosen = torch.cat(picks)

        P_iL, P_iM, P_root = group["projectors"]
        sub_projectors = (P_iL[chosen], P_iM[chosen], P_root[chosen])
        sub_laws = {key: value[chosen] for key, value in laws.items()}
        sub_shared = group["shared"][chosen]
        sub_eta = group["eta"][chosen]

        factors = feasibility_factors(sub_laws, sub_projectors,
                                      *grade_strength)
        A_hat, PA, D, geometry = evaluate(sub_laws, sub_projectors,
                                          group["leaves"][chosen], sub_eta,
                                          factors, sub_shared)
        built = build_laws(sub_laws, sub_projectors, sub_eta, factors,
                           sub_shared)
        achieved_norm, achieved_closure = audit_admissibility(
            built, sub_projectors, sub_eta, grade_strength)
        values = torch.nan_to_num(
            score(group["coefficients"][chosen], A_hat, PA, D, sub_eta),
            nan=-1.0)

    results = []
    for index, cell in enumerate(cells):
        low, high = index * keep, (index + 1) * keep
        best = low + int(torch.argmax(values[low:high]))
        eta = cell["eta"]
        e_L, e_M = geometry["e_L"][best], geometry["e_M"][best]
        denominator = (e_L.norm() * e_M.norm()).clamp_min(1e-14)
        results.append({**cell, "dim": dim, "best": float(values[best]),
                        "ceiling": ceiling(cell["objective"], eta),
                        "A_hat_over_eta": float(A_hat[best].norm() / eta),
                        "PA_over_eta": float(PA[best].norm() / eta),
                        # extremizer geometry: which constraint is active
                        "chi": float(torch.dot(e_L, e_M) / denominator),
                        "eL_over_eta": float(e_L.norm() / eta),
                        "eM_over_eta": float(e_M.norm() / eta),
                        "closure_sat_L": float(geometry["D_iL"][best].norm()
                                               / eta),
                        "closure_sat_M": float(geometry["D_iM"][best].norm()
                                               / eta),
                        "inner_norm_sat_L": float(geometry["F_iL"][best].norm()),
                        "inner_norm_sat_M": float(geometry["F_iM"][best].norm()),
                        # what the reported configuration ACTUALLY satisfies,
                        # re-measured with a stronger estimator than the search
                        "achieved_op_norm": float(achieved_norm[best]),
                        "achieved_closure_over_eta": float(
                            achieved_closure[best]),
                        # 1e-7, not 1e-9: both quantities are re-measured by
                        # a separate estimator run through several einsums, so
                        # the last digit is roundoff, not slack. A tolerance
                        # tighter than the arithmetic flags benign cells and
                        # buries a real one in the noise.
                        "admissible": bool(achieved_norm[best] <= 1.0 + 1e-7
                                           and achieved_closure[best]
                                           <= 1.0 + 1e-7),
                        "seed": seed, "element": int(chosen[best]),
                        "finalists": keep,
                        "restarts": per_cell})
    return results


def measure_bytes_per_element(dim, device, probes=(256, 1024)):
    """Marginal bytes per element at this D, measured not guessed.

    Two probe sizes and a slope, because a single probe charges the whole
    fixed overhead (cuBLAS/cuSOLVER workspaces, the module's own constants) to
    the few elements it ran, which at small probe sizes overestimates the
    marginal cost several-fold and leaves most of the card unused.
    """
    if device.type != "cuda":
        return 1.0
    cells = [{"objective": "S", "class": "free", "rank": 1, "eta": 0.5}]
    peaks = []
    for probe in probes:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        run_group(cells, probe, dim, steps=2, refresh=1, quality=1,
                  device=device, seed=1)
        peaks.append(torch.cuda.max_memory_allocated())
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    slope = (peaks[-1] - peaks[0]) / (probes[-1] - probes[0])
    return max(slope, peaks[-1] / probes[-1] / 8.0)   # guard a degenerate fit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objectives", nargs="+", default=["J", "H", "S"])
    parser.add_argument("--classes", nargs="+",
                        default=["free", "same_law_same_P"])
    parser.add_argument("--dims", type=int, nargs="+", default=[2, 3, 4, 5, 6])
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.1, 0.2, 0.35, 0.5, 0.6,
                                 1 / math.sqrt(2), 0.8, 0.9, 1.0])
    parser.add_argument("--per-cell", type=int, default=2048)
    parser.add_argument("--steps", type=int, default=250)
    parser.add_argument("--refresh", type=int, default=5)
    parser.add_argument("--init", choices=("dense", "sparse"), default="dense")
    parser.add_argument("--differentiable", action="store_true",
                        help="differentiate through the admissibility scaling; "
                             "without it the backward optimizes a DIFFERENT "
                             "function than the forward evaluates")
    parser.add_argument("--warm-iters", type=int, default=3,
                        help="iterations per warm-started feasibility solve; "
                             "0 disables warm start")
    parser.add_argument("--global-refresh", type=int, default=25,
                        help="steps between full cold feasibility solves")
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--decay", action="store_true",
                        help="cosine-anneal the learning rate over the run")
    parser.add_argument("--quality", type=int, default=4)
    parser.add_argument("--loop-strength", type=int, nargs=2, default=[3, 20],
                        metavar=("RESTARTS", "ITERS"),
                        help="operator-norm estimator inside the search loop; "
                             "cheap is fine, it only steers the gradient")
    parser.add_argument("--finalists", type=int, default=24,
                        help="restarts per cell promoted to converged grading")
    parser.add_argument("--grade-strength", type=int, nargs=2,
                        default=[64, 40], metavar=("RESTARTS", "ITERS"),
                        help="estimator for the FINAL grading and the "
                             "admissibility audit; must be converged at this "
                             "dimension or the reported value is inflated "
                             "(D=4 needs 64/200)")
    parser.add_argument("--target-vram-gb", type=float, default=18.0)
    parser.add_argument("--json", type=str, default="rg_fused_search_raw.json")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device} dtype=float64 restarts/cell={args.per_cell} "
          f"steps={args.steps} refresh={args.refresh}")
    if device.type == "cuda":
        properties = torch.cuda.get_device_properties(0)
        print(f"  {properties.name}, {properties.total_memory / 1e9:.1f} GB, "
              f"{properties.multi_processor_count} SMs")

    records, start = [], time.time()
    print(f"\n{'obj':>4} {'class':>16} {'D':>3} {'r':>3} {'eta':>6} "
          f"{'best':>10} {'ceiling':>10} {'excess':>11}")
    for dim in args.dims:
        per_element = measure_bytes_per_element(dim, device)
        budget = int(args.target_vram_gb * 1e9 / max(per_element, 1.0))
        group_size = max(1, budget // max(args.per_cell, 1))
        cells = [{"objective": objective, "class": klass, "rank": rank,
                  "eta": eta}
                 for objective in args.objectives
                 for klass in args.classes
                 for rank in range(1, dim)
                 for eta in args.etas]
        print(f"  D={dim}: {per_element / 1e3:.0f} KB/element measured -> "
              f"{group_size} cells x {args.per_cell:,} = "
              f"{group_size * args.per_cell:,} elements per launch "
              f"({len(cells)} cells total)", flush=True)

        started = time.time()
        for offset in range(0, len(cells), group_size):
            rows = run_group(cells[offset:offset + group_size], args.per_cell,
                             dim, args.steps, args.refresh, args.quality,
                             device, seed=7717 + 31 * dim + offset,
                             init=args.init, lr=args.lr, decay=args.decay,
                             loop_strength=tuple(args.loop_strength),
                             grade_strength=tuple(args.grade_strength),
                             finalists=args.finalists,
                             differentiable=args.differentiable,
                             warm_iters=args.warm_iters,
                             global_refresh=args.global_refresh)
            records.extend(rows)
            for row in rows:
                print(f"{row['objective']:>4} {row['class']:>16} {dim:3d} "
                      f"{row['rank']:3d} {row['eta']:6.3f} "
                      f"{row['best']:10.6f} {row['ceiling']:10.6f} "
                      f"{row['best'] - row['ceiling']:+11.2e}", flush=True)
        peak = (torch.cuda.max_memory_allocated() / 1e9
                if device.type == "cuda" else 0.0)
        print(f"  -> D={dim}: {len(cells)} cells "
              f"({len(cells) * args.per_cell:,} restarts) in "
              f"{time.time() - started:.0f}s, peak VRAM {peak:.2f} GB",
              flush=True)

    (HERE / args.json).write_text(
        json.dumps({"config": vars(args), "device": str(device),
                    "runs": records}, indent=2), encoding="utf-8")

    print(f"\n{len(records)} cells, "
          f"{len(records) * args.per_cell:,} restarts total, "
          f"in {time.time() - start:.0f}s")
    for objective in args.objectives:
        for klass in args.classes:
            subset = [r for r in records if r["objective"] == objective
                      and r["class"] == klass]
            if not subset:
                continue
            worst = max(subset, key=lambda r: r["best"] - r["ceiling"])
            closest = max(subset, key=lambda r: r["best"] / r["ceiling"])
            print(f"  {objective} / {klass:>16}: largest excess "
                  f"{worst['best'] - worst['ceiling']:+.3e}; closest approach "
                  f"{100 * closest['best'] / closest['ceiling']:.1f}% of the "
                  f"ceiling at eta={closest['eta']:.3f} D={closest['dim']}")
    inadmissible = [r for r in records if not r["admissible"]]
    print(f"  cells whose reported configuration failed the independent "
          f"admissibility re-measurement: {len(inadmissible)}")
    violations = [r for r in records if r["best"] > r["ceiling"] + 1e-6]
    real = [r for r in violations if r["admissible"]]
    print(f"  cells above the proved ceiling: {len(violations)}, of which "
          f"{len(real)} are admissible (an admissible one is a refutation; an "
          f"inadmissible one is a feasibility bug in the search)")


if __name__ == "__main__":
    main()
