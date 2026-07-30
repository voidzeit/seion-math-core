# Block K (HOSVD compactness) — v18 findings

Real reduced tensor (n=16, rank=4, cp_rank=4, seed=0, 99% energy
threshold): mode ranks needed = [3, 4, 4] out of a full rank-4 subspace —
only mildly more compact than the ambient rank. Tucker reconstruction
error at that truncation: 4.5%. Held-out generalization (applying the SAME
truncation ranks to an independently-seeded instance's own tensor, not the
same basis): 6.6% — comparable to the in-sample error, i.e. the *rank*
choice generalizes even though the specific basis is instance-specific
(expected, since each instance has an independently random CP law).
Perturbation stability (1e-4 relative noise): max principal angle of the
dominant mode-0 subspace = 0.138 rad (~7.9 degrees) — a real, non-trivial
figure meaning the dominant subspace is measurably but not wildly
sensitive to small perturbations at this scale.

**Random-tensor control**: a same-shape, same-norm i.i.d. random tensor
needs full rank-4 in every mode to hit 99% energy, vs [3,4,4] for the real
tensor — the real tensor IS more compact than the random-tensor null in
mode 0, confirmed by `real_tensor_more_compact_than_random=True`. This is
real, if modest, evidence against "no structure" — but a difference of 1
rank out of 4 (mode 0 only; modes 1 and 2 tie the random baseline) is a
long way from "99% energy in one mode" claims that would license "canonical
low-dimensional structure" language.

## Gate status

`persistence_gate` contribution: `EMPIRICAL_SCREENING_PASS` for
"more compact than a random-tensor null in at least one mode, at this
single seed/dimension" — explicitly not `STATISTICALLY_VALIDATED_PASS`
(single seed only; a cross-seed distribution, listed as a requirement, was
not run at scale this pass — tracked as follow-up for the sweep phase).
