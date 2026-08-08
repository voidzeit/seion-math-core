# Gate 14 — Structural Specificity and True Triadic SEION

Status: Gate 14A seed-1 screening completed and audited for promotion to the
pre-registered multi-seed stage. Seeds 2–3 have not been launched.

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

### Frozen context builder

The only context builder permitted in Gate 14A is the following deterministic
function. It uses the training split only, after the repository's mandatory
reciprocal closure has been added:

```text
c_(h,r) = G(neighborhood(h), r)
```

Frozen values:

| Field | Frozen value |
|---|---|
| graph source | reciprocal-closed training triples only |
| direction | outgoing edges from `h` in that graph |
| queried edge exclusion | exclude `(h,r,t)` before selection |
| reciprocal exclusion | exclude `(t,r_inverse,h)` before selection |
| maximum neighbors | `32` |
| selection | lexicographic `(relation_id,target_id)`, first 32 |
| aggregation | arithmetic mean of `entity_embedding(target) + relation_embedding(edge_relation)` |
| normalization | affine-free LayerNorm, `eps=1e-5` |
| context dimension | model dimension, `64` for Gate 14A |
| trainable context parameters | none |
| empty neighborhood | all-zero vector before normalization; remains zero |
| target leakage | validation/test edges are never in the context graph |

The same context tensor is passed to SEION-v2 and Generic-v2. The builder is
not a learned module; gradients may flow through the shared entity/relation
embeddings used to construct `c`, but it introduces no trainable parameters.
The query edge and reciprocal are removed before the neighbor budget is
applied.

```text
SEION-v2:   O[(A h) ⊙ (B r) ⊙ (C c)]
Generic-v2: O[tanh(A h + B r + C c)]
```

The only scientific difference is the multiplicative Hadamard composition
versus the additive bounded composition. The base checkpoint, optimizer reset,
learning rate, router learning-rate multiplier, negative samples, batch
order, evaluator, and stopping policy are matched.

### Frozen Gate 14A run policy

```text
dataset             = full FB15K-237
source checkpoint   = campaigns/gate13/gate13_5/runs/pilot/seed1_A0/best.pt
seed                = 1
dim                 = 64
batch_size          = 256
neg_k               = 64
adversarial_temp    = 1.0
n3_weight           = 1e-3
lr                  = 1e-3
weight_decay        = 0.0
router_lr_multiplier= 5.0
gate_init          = 0.1 (same non-zero residual initialization in both arms)
max_epochs          = 50
eval_every          = 2 epochs
early_stopping      = 8 evaluations without strict MRR improvement
early_min_epochs    = 16
early_min_delta     = 0.0
screening_seed      = 1
test                 = closed
```

Promotion from seed 1 to seeds 2–3 is engineering-gated, not MRR-selected:
both arms must complete with finite metrics, zero test rows, the same source
checkpoint and context specification, equal parameter counts, matched batch
and negative hashes, valid best checkpoints, and identical stopping policy.
The sign or magnitude of the seed-1 MRR contrast cannot block promotion.

The primary contrast is fixed as:

```text
Delta_triadic = best_valid_MRR(T14-S) - best_valid_MRR(T14-G)
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

Use validation-only lambda selection from the frozen sets
`FI_lambda ∈ {1e-4, 1e-3, 1e-2}` and
`Assoc_lambda ∈ {1e-4, 1e-3, 1e-2}`. Report MRR, FI defect, associator defect, closure defect,
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

Use the frozen Gate 14A budget and stopping policy above for matched arms.
Gate 14B/14C inherit `max_epochs=50`, `eval_every=2`, `patience=8`, and
`early_min_epochs=16` unless a new preregistration supersedes this document.
Start with one seed; advance frozen configurations to three seeds. Test stays
closed until the architecture, optimizer, metrics, and artifact manifests are
frozen.
