"""Final fail-closed gate evaluation for this campaign, executed (not
narrated). Block statuses below are transcribed directly from each
block's BLOCK_*_FINDINGS.md verdict — see that file for the evidence
behind each assignment. Run: `python -m spectral.certification_v18.final_gate_evaluation`.
"""

from __future__ import annotations

import json
from pathlib import Path

from spectral.certification_v18.gates import TypedStatus, combine_gate_status, evaluate_global_certificate

# One representative status per block, per its FINDINGS.md verdict.
BLOCK_STATUS = {
    "A_projector": TypedStatus.STRUCTURAL_IDENTITY_PASS,
    "B_commutator": TypedStatus.FAIL,
    "C_beals": TypedStatus.NUMERICAL_SANITY_PASS,
    "D_snapping": TypedStatus.EMPIRICAL_SCREENING_PASS,
    "E_interscale": TypedStatus.FAIL,
    "F_rigidity": TypedStatus.EMPIRICAL_SCREENING_PASS,  # basin instability is itself the informative empirical result
    "G_nary_closure": TypedStatus.STATISTICALLY_VALIDATED_PASS,
    "H_associator": TypedStatus.EMPIRICAL_SCREENING_PASS,  # sharpness itself OPEN, bound-holds is screening-tier
    "I_reduced_tensor": TypedStatus.EXACT_CERTIFICATE,  # rational small case; extraction-correctness scope only
    "J_tensor_interscale": TypedStatus.FAIL,
    "K_hosvd": TypedStatus.EMPIRICAL_SCREENING_PASS,
    "L_gauge_canonicalization": TypedStatus.EXACT_CERTIFICATE,  # residual-gauge detection logic itself
    "M_persistent_factorization": TypedStatus.FAIL,
    "N_cyclic_law": TypedStatus.STRUCTURAL_IDENTITY_PASS,  # symmetrized defect; GJI formula is EXACT but ratio sup is OPEN
}

GATE_STATUS = {
    "projector_gate": combine_gate_status({"A_projector": BLOCK_STATUS["A_projector"], "D_snapping": BLOCK_STATUS["D_snapping"]}),
    "algebra_gate": combine_gate_status(
        {"G_nary_closure": BLOCK_STATUS["G_nary_closure"], "H_associator": BLOCK_STATUS["H_associator"], "N_cyclic_law": BLOCK_STATUS["N_cyclic_law"]}
    ),
    "dynamic_explanation_gate": combine_gate_status({"B_commutator": BLOCK_STATUS["B_commutator"], "C_beals": BLOCK_STATUS["C_beals"]}),
    "interscale_gate": combine_gate_status({"E_interscale": BLOCK_STATUS["E_interscale"], "J_tensor_interscale": BLOCK_STATUS["J_tensor_interscale"]}),
    "gauge_gate": combine_gate_status({"L_gauge_canonicalization": BLOCK_STATUS["L_gauge_canonicalization"]}),
    "persistence_gate": combine_gate_status({"K_hosvd": BLOCK_STATUS["K_hosvd"], "M_persistent_factorization": BLOCK_STATUS["M_persistent_factorization"]}),
    "reproducibility_gate": TypedStatus.WARN,  # legacy lineage: non-strict resume, seed=3 throughout; v18 runs this pass were single-seed
    "mathematical_proof_gate": combine_gate_status({"F_rigidity": BLOCK_STATUS["F_rigidity"], "I_reduced_tensor": BLOCK_STATUS["I_reduced_tensor"]}),
}


def main() -> dict:
    result = evaluate_global_certificate(GATE_STATUS, eval_mode="screening")
    payload = {
        "block_status": {k: v.value for k, v in BLOCK_STATUS.items()},
        "gate_status": {k: v.value for k, v in GATE_STATUS.items()},
        "final_state": result.final_state,
        "passed_gates": list(result.passed_gates),
        "excluded_gates": list(result.excluded_gates),
        "failing_gates": list(result.failing_gates),
    }
    out_path = Path(__file__).parent / "artifacts" / "final_gate_evaluation.json"
    out_path.write_text(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
