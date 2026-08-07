# Gate 14 — Structural Specificity and True Triadic SEION

Status: design only. No Gate 14 training run has been launched.

Gate 13.5 remains frozen historical evidence. Gate 14 must not rewrite its
metrics, checkpoints, or causal interpretation.

## P0 implementation gates

1. SEION's three factor maps remain distinct:

   ```text
   q_seion(h,r,c) = O[(A h) ⊙ (B r) ⊙ (C c)]
   ```

   The current implementation passes the B/C gradient and perturbation audit.
2. Standalone Path and standalone SEION use the same score normalization:

   ```text
   score = scale_r * <LayerNorm(q), LayerNorm(t)> / sqrt(dim)
   ```

   Existing W1/W2 results are labeled `WARM_STARTED_STANDALONE_V1` and are not
   modified. New matched-normalization runs must use a new configuration ID.
3. Resume checkpoints must preserve and restore Python RNG, Torch CPU/CUDA
   RNG, NumPy RNG, DataLoader generator, geometry generator, optimizer state,
   best-validation state, epoch, and global step. The CPU integration test
   must match continuous training in losses, metrics, and model tensors.

## Gate 14A — true triadicity

Define a third, query-dependent structural context:

```text
c_(h,r) = G(neighborhood(h), r)
```

The queried edge and its reciprocal are excluded before context construction.
SEION-v2 and Generic-v2 receive exactly the same `(h, r, c_(h,r))`, rank,
parameter budget, checkpoint, batch order, optimizer, and evaluation policy.

```text
SEION-v2:   O[(A h) ⊙ (B r) ⊙ (C c)]
Generic-v2: O[tanh(A h + B r + C c)]
```

The primary contrast is multiplicative triadic composition versus additive
matched composition. Test remains closed.

## Gate 14B — structural regularization factorial

| Arm | FI | Associator |
|---|---:|---:|
| S0 | OFF | OFF |
| S1 | ON  | OFF |
| S2 | OFF | ON  |
| S3 | ON  | ON  |

Use validation-only lambda selection from a preregistered set such as
`{1e-4, 1e-3, 1e-2}`. Report MRR, FI defect, associator defect, closure defect,
rank stability, and parameter count together. Do not select lambdas using test.

## Gate 14C — kernel specificity

Screen one seed across:

```text
E8_exact
random_scale_matched
permuted_indices
sign_shuffled
zero_kernel
```

Only preregistered candidates may advance to three seeds. Report predictive,
associator, closure, perturbation, certification, and rank/compression metrics.

## Path diagnostics

Every standalone Path run must report target reachability, frontier size,
reachable-candidate fraction, unreached-candidate fraction, global MRR, and
reachable-only MRR/Hits. A low global MRR must not be interpreted as a weak
Path scorer without separating coverage from conditional ranking quality.

## Budget and test policy

Use a common maximum budget of 50 epochs, evaluation every 2–3 epochs, and
patience 8–10 evaluations, with identical stopping rules across matched arms.
Start with one seed; advance frozen configurations to three seeds. Test stays
closed until the architecture, optimizer, metrics, and artifact manifests are
frozen.
