# PMTFormal — machine-checked pieces of Theorem R (v2)

Lean 4 `v4.33.1`, Mathlib `v4.33.1` (pinned in `lakefile.toml` and `lean-toolchain`).

Only the two self-contained pieces are formalised. The upper-bound core
(O2, tensor angle inequality, Lemma 3) is under human review first; it is **not**
formalised here.

| Lean declaration | statement in `review/theorem_R_v2/THEOREM_R_v2.md` |
|---|---|
| `PMT.cos_sum_le_prod_cos` | Lemma 6.1 |
| `PMT.prod_cos_le_cos_mean_pow` | Lemma 6.2 (closed interval `[0, π/2]`, proved via Jensen for `cos` and AM–GM) |
| `PMT.diagonal_capped` | Lemma 6.3, "moreover" part: the capped form used by Theorem 7.1 |
| `PMT.diagonal_lemma` | Lemma 6.3: every `θ ∈ [0,α]^n` is dominated by a diagonal point |
| `PMT.rootError_eq` | Theorem 8.1, evaluation: `E^P = ‖1 − ∏_{v≠r} w(θ_v)‖` for every finite tree |
| `PMT.rootError_equal_angles` | Corollary 8.2, evaluation: equal angles give `‖1 − w(t)^{k−1}‖` |

## Modelling notes

* `w θ := cos θ · e^{iθ}`. Norms are those of `ℂ ≅ ℝ²`, and `Complex.normSq` is
  the squared norm.
* The witness model encodes the evaluation algebra of Theorem 8.1:
  * a tree is its internal-node skeleton `WTree.node θ children`;
  * each leaf slot contributes the factor `Re(e₀) = 1` and is omitted;
  * the root has `P_r = I`.

  Admissibility of the laws (operator norm 1, closure `sin θ_v`) is the
  elementary argument in Theorem 8.1 and is not formalised.
* The Diagonal Lemma is formalised in its "there exists a diagonal point `t`"
  form, which is equivalent to the equality of maxima.

## Build

```bash
lake exe cache get
```

```bash
lake build
```

A successful build with no `sorry` is the check. The CI-free verification record
is in `BUILD_LOG.md`.
