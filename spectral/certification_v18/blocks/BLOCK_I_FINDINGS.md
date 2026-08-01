# Block I (reduced tensor extraction) — v18 findings

Extraction-only, artifact-integrity block, as mission section 2I requires
(no compactness/persistence/significance claim). Two independently-coded
extraction paths (`reduced_law_tensor_loops` — explicit index loops;
`reduced_law_tensor_einsum` — CP-exploiting einsum, including the cyclic
average over all 3 rotations) agree to <1e-10 relative difference at
float64 and <1e-4 at float32 (n=12, rank=3, cp_rank=4, seed=0). An exact
rational small case (n=2, r=1, hand-expanded arithmetic over
`fractions.Fraction`, zero floating point) matches the general formula's
output exactly (`t_000 == 1` exactly, not approximately).

Not attempted this pass: Torch CUDA parity and CP-vs-dense-tensor-network
contraction parity (both listed in mission section 2I) — the einsum path
already runs on whichever device the input tensors live on, so a CUDA run
is a configuration choice rather than new code, but it was not executed
this pass; tracked as follow-up alongside the GPU sweep phase.

## Gate status

`mathematical_proof_gate` contribution (block I's ceiling per
GATE_TAXONOMY.md): `EXACT_CERTIFICATE` for the rational small case;
`VALIDATED_NUMERICAL_CERTIFICATE`-tier evidence (float64, two independent
implementations, tight tolerance) for the general-case parity claim,
extraction-correctness scope only.
