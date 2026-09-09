"""M39-A, hardware-fused: every (rank, eta) cell at a given D in one batch.

EXPERIMENTAL. Nothing here is a theorem.

Question unchanged: is J_2 = sup ||D_A|| / (rho M L) equal to 2, and does
sharing the law or the projectors lower it? Paper A gives J_2 <= 2 via
C_2^P = 1; a value above 2 + 1e-6 is a feasibility bug, not a discovery, and
is reported as such.

The reported number is always recomputed at high feasibility quality, so a
witness that only scored well under a cheap projection is graded on the
projection it actually satisfies.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from m39_gpu_kernels import (  # noqa: E402
    DTYPE, contract3, coordinate_projectors, make_feasible,
)


# Feasibility scaling is the expensive part: each make_feasible runs two
# alternating maximizations, so one objective evaluation costs ~1440 batched
# eigh calls. The scale factors move slowly under Adam, so they are recomputed
# every REFRESH steps and held fixed in between. The final reported value is
# always computed with a fresh high-quality projection, so a stale cache can
# only make the search less effective -- never inflate the number reported.
def objective(laws, leaves, P_root, P_L, P_M, eta, identity, quality):
    normal_root = identity - P_root
    mu_inner_L = make_feasible(laws, P_L, identity - P_L, eta, seed=11, quality=quality)
    mu_inner_M = make_feasible(laws, P_M, identity - P_M, eta, seed=23, quality=quality)
    mu_root_L = make_feasible(laws, P_root, normal_root, eta, restrict=P_L,
                              seed=37, quality=quality)
    mu_root_M = make_feasible(laws, P_root, normal_root, eta, restrict=P_M,
                              seed=53, quality=quality)

    unit = leaves / leaves.norm(dim=2, keepdim=True).clamp_min(1e-12)
    x1, x2, x3, x4, x5 = (unit[:, i, :] for i in range(5))

    D_L = torch.einsum("nij,nj->ni", identity - P_L, contract3(mu_inner_L, x1, x2, x3))
    D_M = torch.einsum("nij,nj->ni", identity - P_M, contract3(mu_inner_M, x2, x3, x4))
    e_T = torch.einsum("nij,nj->ni", P_root, contract3(mu_root_L, D_L, x4, x5))
    e_TM = torch.einsum("nij,nj->ni", P_root, contract3(mu_root_M, x1, D_M, x5))
    D_A = -e_T + e_TM
    return D_A.norm(dim=1) / eta, e_T, e_TM


BYTES_PER_ELEMENT = 640_000   # measured 583-635 KB at D = 3, 4, 5


def cells_per_group(per_cell: int, target_gb: float) -> int:
    """How many (rank, eta) cells fit in one launch at the VRAM target."""
    budget = int(target_gb * 1e9 / BYTES_PER_ELEMENT)
    return max(1, budget // max(per_cell, 1))


def run_dim(klass: str, dim: int, etas, per_cell: int, steps: int, device, seed: int,
            cell_group=None):
    """Fused batch over a group of (rank, eta) pairs at this dimension."""
    ranks = list(range(1, dim))
    cells = cell_group if cell_group is not None else [(r, e) for r in ranks for e in etas]
    total = len(cells) * per_cell
    generator = torch.Generator(device=device).manual_seed(seed)

    rank_vec = torch.tensor([r for r, _ in cells], device=device
                            ).repeat_interleave(per_cell)
    eta_vec = torch.tensor([e for _, e in cells], dtype=DTYPE, device=device
                           ).repeat_interleave(per_cell)
    identity = torch.eye(dim, dtype=DTYPE, device=device).expand(total, dim, dim)
    P_root = coordinate_projectors(rank_vec, dim, device)

    if klass == "same_law_same_P":
        P_L = P_M = P_root
    else:
        inner = torch.randint(1, dim, (2, total), device=device, generator=generator)
        P_L = coordinate_projectors(inner[0], dim, device)
        P_M = coordinate_projectors(inner[1], dim, device)

    laws = torch.randn(total, dim, dim, dim, dim, dtype=DTYPE, device=device,
                       generator=generator, requires_grad=True)
    leaves = torch.randn(total, 5, dim, dtype=DTYPE, device=device,
                         generator=generator, requires_grad=True)
    optimizer = torch.optim.Adam([laws, leaves], lr=0.05)

    for step in range(steps):
        optimizer.zero_grad(set_to_none=True)
        values, _, _ = objective(laws, leaves, P_root, P_L, P_M, eta_vec,
                                 identity, quality=1)
        (-values.sum()).backward()
        torch.nn.utils.clip_grad_norm_([laws, leaves], 10.0)
        optimizer.step()

    with torch.no_grad():
        values, e_T, e_TM = objective(laws, leaves, P_root, P_L, P_M, eta_vec,
                                      identity, quality=6)
        values = torch.nan_to_num(values, nan=-1.0)

    results = []
    for index, (rank, eta) in enumerate(cells):
        lo, hi = index * per_cell, (index + 1) * per_cell
        block = values[lo:hi]
        best = lo + int(torch.argmax(block))
        denominator = (e_T[best].norm() * e_TM[best].norm()).clamp_min(1e-14)
        results.append({
            "class": klass, "dim": dim, "rank": rank, "eta": eta,
            "J2": float(values[best]),
            "chi": float(torch.dot(e_T[best], e_TM[best]) / denominator),
            "eT_over_eta": float(e_T[best].norm() / eta),
            "eTM_over_eta": float(e_TM[best].norm() / eta),
            "restarts": per_cell,
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dims", type=int, nargs="+", default=[2, 3, 4, 5])
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0])
    parser.add_argument("--classes", type=str, nargs="+",
                        default=["same_law", "same_law_same_P"])
    parser.add_argument("--per-cell", type=int, default=8192)
    parser.add_argument("--steps", type=int, default=250)
    parser.add_argument("--target-vram-gb", type=float, default=20.0)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device} dtype=float64 restarts/cell={args.per_cell} "
          f"steps={args.steps}")
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"  {props.name}, {props.total_memory / 1e9:.1f} GB VRAM")

    records, start = [], time.time()
    print(f"\n{'class':>18} {'D':>3} {'r':>3} {'eta':>6} {'J2':>9} {'chi':>7} "
          f"{'|eT|/eta':>9} {'|eT2|/eta':>9}")
    group_size = cells_per_group(args.per_cell, args.target_vram_gb)
    print(f"  targeting {args.target_vram_gb:.0f} GB: {group_size} cells x "
          f"{args.per_cell:,} restarts = {group_size * args.per_cell:,} per launch")
    for klass in args.classes:
        for dim in args.dims:
            t0 = time.time()
            every = [(r, e) for r in range(1, dim) for e in args.etas]
            cells = []
            for start_index in range(0, len(every), group_size):
                cells.extend(run_dim(klass, dim, args.etas, args.per_cell,
                                     args.steps, device,
                                     seed=7717 + 31 * dim + start_index,
                                     cell_group=every[start_index:start_index + group_size]))
            records.extend(cells)
            for row in cells:
                print(f"{row['class']:>18} {row['dim']:3d} {row['rank']:3d} "
                      f"{row['eta']:6.2f} {row['J2']:9.5f} {row['chi']:+7.3f} "
                      f"{row['eT_over_eta']:9.4f} {row['eTM_over_eta']:9.4f}")
            peak = (torch.cuda.max_memory_allocated() / 1e9
                    if device.type == "cuda" else 0.0)
            print(f"  -> D={dim} fused batch of {len(cells) * args.per_cell:,} "
                  f"in {time.time() - t0:.0f}s, peak VRAM {peak:.2f} GB", flush=True)

    (HERE / "m39a_j2_fused_raw.json").write_text(
        json.dumps({"config": vars(args), "device": str(device), "runs": records},
                   indent=2), encoding="utf-8")
    print(f"\n{len(records)} cells in {time.time() - start:.0f}s")
    for klass in args.classes:
        values = [r["J2"] for r in records if r["class"] == klass]
        if values:
            print(f"  {klass:>18}: max J2 = {max(values):.6f}   "
                  f"min over cells = {min(values):.6f}")
    over = [r for r in records if r["J2"] > 2.0 + 1e-6]
    print(f"  cells above the proved bound of 2: {len(over)} "
          f"(any is a feasibility bug, not a discovery)")


if __name__ == "__main__":
    main()
