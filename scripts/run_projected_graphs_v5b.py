"""Execute the deterministic V5-B scalar extremal analysis."""

from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from seion_core.research_v5.v5b_extremal import (
    conditional_scalar_reduction_upper_bound,
    optimize_scalar_k3_family,
    repeated_law_k2_band,
    scalar_k3_objective,
    v5a_piecewise_lower_bound_closed_form,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "research_v5" / "v5b_extremal_analysis.json"


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def grid_upper_sanity(eta: float, points: int = 10001) -> dict[str, float | bool]:
    result = optimize_scalar_k3_family(eta)
    upper = result.q_upper
    values = [scalar_k3_objective(upper * i / (points - 1)) for i in range(points)]
    sampled_max = max(values)
    return {
        "points": points,
        "sampled_max": sampled_max,
        "analytic_max": result.objective_at_q_star,
        "sampled_does_not_exceed_analytic": sampled_max
        <= result.objective_at_q_star + 1e-10,
    }


def main() -> None:
    etas = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0 / math.sqrt(2.0), 0.8, 0.9, 1.0]
    rows = []
    for eta in etas:
        result = optimize_scalar_k3_family(eta)
        conditional = conditional_scalar_reduction_upper_bound(eta)
        repeated = repeated_law_k2_band(eta)
        rows.append(
            {
                "eta": eta,
                "regime": result.regime,
                "rho": result.rho,
                "q_star": result.q_star,
                "projected_error_lower_witness": result.objective_at_q_star,
                "L3_lower_bound": result.normalized_by_rho_M2,
                "closed_form_L3": v5a_piecewise_lower_bound_closed_form(eta),
                "universal_k3_upper_bound": result.universal_bound,
                "gap_to_universal": result.gap_to_universal,
                "conditional_scalar_upper_bound": conditional.bound,
                "repeated_law_lower_bound": repeated.known_lower_bound,
                "repeated_law_upper_bound": repeated.universal_upper_bound,
                "scalar_grid_sanity": grid_upper_sanity(eta),
            }
        )

    payload = {
        "schema": "projected-graphs-v5b-extremal-analysis-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_head(),
        "scope": {
            "k3": "real binary rank-one independent-law V5-A witness family",
            "k2_repeated": "known repeated/shared-law band only",
        },
        "closed": [
            "exact scalar maximizer q*=min(rho,M/sqrt(2))",
            "piecewise V5-A lower curve L3(eta)",
            "asymptotic squeeze lim eta->0 C_3,ind^P(eta)=2",
        ],
        "conditional": [
            "candidate k=3 upper envelope under the unproved scalar reduction",
        ],
        "open": [
            "fixed-eta global k=3 sharpness",
            "universal proof of E_proj<=2AB with the required scalar constraints",
            "fixed-eta repeated-law k=2 sharpness",
        ],
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
