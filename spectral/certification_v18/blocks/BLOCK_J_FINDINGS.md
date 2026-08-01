# Block J (tensor interscale) — v18 findings (methodology pass)

## What was wrong with the legacy comparison

`spectral/legacy/v17/...py` block J (~1651) gauge-fixes each scale's
reduced tensor via `canonical_gauge_from_tensor` (a single Gram-matrix
eigenbasis heuristic) and reports one `tensor_diff_rel` number. Historical
normalized distances sit at 1.0-1.4 (mission brief). That is ambiguous
between two very different claims: "no persistence exists" and "these two
tensors are gauge-equivalent under some unitary, just not the one this
heuristic happens to find."

## What v18 builds instead

`gauge_utils.py`: `raw_distance`, `amplitude_ratio`,
`procrustes_aligned_distance` (closed-form optimal unitary realignment —
the actual gauge-invariant distance for general matrices), and
`permutation_aligned_distance` (exhaustive search for small dimensions),
reported **separately**, per mission section 2J's explicit requirement.
9 tests in `test_gauge_utils.py` confirm: raw distance is NOT gauge
invariant (sanity), Procrustes distance IS (recovers exact equivalence
under a random unitary and recovers the *exact* generating unitary itself),
permutation distance recovers row permutations, amplitude ratio is
reported independently of distance.

**Important scope boundary found and documented in code** (not just
here): `compare_with_gauge` is only valid for general matrices — applying
it to matrices whose columns are themselves an orthonormal basis (e.g.
subspace bases) is vacuous, because a free unitary can always map one
orthonormal frame to another regardless of any real relationship between
them. This was caught concretely while building block M (see
`BLOCK_M_FINDINGS.md`) and is now documented directly in `gauge_utils.py`
so it cannot recur when this module is reused for block L.

## Update: real multiresolution experiment now run (see BLOCK_E_FINDINGS.md)

Block E's interscale-transport experiment provides exactly the
independently-trained multi-resolution setup this section originally
listed as missing (three resolutions, frozen lift, principal angles,
random + interpolation baselines). Result: **no meaningful transport
signal** — all transported-subspace angles sit near the maximum possible
(pi/2), and the trained lift beats both required baselines in only 2 of 3
pairs, by a small margin. See BLOCK_E_FINDINGS.md for the full table and
diagnosis (most likely explanation: the same closure-objective
non-identifiability Block F independently found via basin instability).

## Gate status

`interscale_gate` (shared with block E): `FAIL` for "the comparison
methodology demonstrates persistent interscale tensor structure" — now
resolved with a real (negative) result rather than left as "not yet
evaluated." The methodology itself (raw / Procrustes-aligned /
permutation-aligned / amplitude-ratio, reported separately) remains a
genuine, tested improvement over the legacy single-heuristic comparison
and is reused as-is; what changed is that it has now actually been run.
