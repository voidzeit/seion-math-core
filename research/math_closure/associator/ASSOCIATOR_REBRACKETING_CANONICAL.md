# Associator and rebracketing: canonical formalization

**Scope.** Four objects, precisely typed, and one bridge theorem connecting
them to the projected-multilinear-tree error theory. Nothing here depends on
the six-term GJI, which is disproved in general
(`research/math_closure/gji/`), and nothing here requires a cohomological
differential.

Status labels follow the repository convention: **EXACT** for statements
proved here, **EXPERIMENTAL** for measured quantities, **OPEN** otherwise.

---

## 0. Why this file exists

The word *associator* has been used in this repository for at least four
different constructions. The modern track already separates them —
`signed_identities/conventions.md` distinguishes `ternary_associator` from
`anchored_binary_associator`, and `constants_table.csv` carries them as
separate rows — but legacy manuscripts under `docs/theorems/` and
`artifacts/` do not, and at least one of them is not well typed. This file
fixes the vocabulary and states what connects it to PMT.

---

## 1. The four objects

Let `V` be a finite-dimensional Hilbert space and `μ : V^n → V` multilinear.

### 1.1 Genuine reassociation, `A^(5)` — no anchor

For a ternary `μ`, two nested applications consume **five** free inputs, not
four. The three elementary composites are

```
T₁ = μ(μ(x₁,x₂,x₃), x₄, x₅)
T₂ = μ(x₁, μ(x₂,x₃,x₄), x₅)
T₃ = μ(x₁, x₂, μ(x₃,x₄,x₅))
```

and the elementary defects are

```
A₁₂ = T₁ − T₂ ,   A₂₃ = T₂ − T₃ ,   A₁₃ = A₁₂ + A₂₃ .
```

**General arity.** Two genuine applications of an `n`-ary law consume
`2n − 1` leaves: the outer law takes `n` arguments, one of which is replaced
by the inner law's `n` arguments. So `n = 2 → 3`, `n = 3 → 5`, `n = 4 → 7`.
Any statement of the form "rebracketing an `n`-ary law acts on `n + 1` inputs"
is fixing `n − 2` anchors implicitly and must say so.

### 1.2 Anchored four-input defect, `A_e^(4)`

Fix `e ∈ V` and define

```
A_e(x₁,x₂,x₃,x₄) = μ(μ(x₁,x₂,x₃), x₄, e) − μ(x₁, μ(x₂,x₃,x₄), e).
```

This is `A₁₂` with the fifth slot frozen at `e`. It is a legitimate object and
is what `anchored_binary_associator` computes, but it is **not** `A^(5)` and
must not be written `A` without the subscript.

A legacy manuscript writes `A(x,y,z;w) = (x⋆y⋆z)⋆w − x⋆(y⋆z⋆w)` while
declaring `⋆ : V³ → V`. Read literally that is ill-typed: after `x⋆y⋆z ∈ V`
two arguments are still missing before a ternary law can be applied again.
The expression only becomes well formed once an anchor is supplied, i.e. once
it is read as `A_e^(4)`.

### 1.3 Binary anchored associator, `Assoc_∘`

Fix `e` and define the binary product `x ∘ y := μ(x, y, e)`. Then

```
Assoc_∘(x,y,z) = (x∘y)∘z − x∘(y∘z)
               = μ(μ(x,y,e), z, e) − μ(x, μ(y,z,e), e).
```

Well typed, and a different object again from both of the above.

### 1.4 Projection-induced associator distortion, `Δ_A^P`

Defined in §2. This is the object the bridge is about.

---

## 2. The bridge to projected multilinear trees — **EXACT**

### Setup

Let `T` and `T'` be finite ordered rooted trees over the **same leaf data**,
with the same root space and the **same root projector `P`**. Their internal
laws and internal projectors may differ. Write, in the notation of
`CANONICAL_FORMALIZATION.md`:

- `F_T`, `F_{T'}` — ambient evaluations at the root;
- `R_T`, `R_{T'}` — recursively projected evaluations at the root;
- `e_T^P := P F_T − R_T`, so that `E_T^P = ‖e_T^P‖` is exactly the projected
  error of §3.2 there.

Define the **exact rebracketing defect** and its **observed** counterpart

```
A_{T,T'}  = F_T − F_{T'}          (what the uncompressed computation would show)
Â_{T,T'}  = R_T − R_{T'}          (what the compressed computation does show)
Δ_A^P     = Â_{T,T'} − P A_{T,T'} (the distortion attributable to projection)
```

### Theorem (associator fidelity under projection)

```
Δ_A^P = −e_T^P + e_{T'}^P                       (identity)

‖Â_{T,T'} − P A_{T,T'}‖ ≤ E_T^P + E_{T'}^P      (bound)
```

**Proof.** From `e_T^P := P F_T − R_T` we get `R_T = P F_T − e_T^P`, and
likewise for `T'`. Hence

```
Â = R_T − R_{T'} = (P F_T − e_T^P) − (P F_{T'} − e_{T'}^P)
                 = P(F_T − F_{T'}) − e_T^P + e_{T'}^P
                 = P A_{T,T'} − e_T^P + e_{T'}^P.
```

Subtracting `P A_{T,T'}` gives the identity; the triangle inequality gives the
bound. ∎

The identity is exact — no slack is introduced before the final triangle step —
so it holds in either root convention, provided `e_T^P` is *defined* as
`P F_T − R_T` in the convention used. Under the canonical PMT convention the
root is projected and `‖e_T^P‖` is literally `E_T^P`.

### What it buys

It separates two things that a compressed computation conflates:

- **genuine non-associativity**, `P A_{T,T'}`, a property of the law;
- **apparent non-associativity**, everything in `Δ_A^P`, manufactured by the
  projection.

An observed rebracketing defect smaller than `E_T^P + E_{T'}^P` is not
evidence of anything about `μ`.

---

## 3. Corollaries at fixed tree size — **EXACT**

### 3.1 Elementary associators are `k = 2`

Each of `T₁`, `T₂`, `T₃` in §1.1 has exactly **two** internal vertices, and so
does each branch of `A_e^(4)` and of `Assoc_∘`. This is already visible in the
repository's own numbers: `constants_table.csv` records
`triangle_upper_bound = 2.0` for both `five_input_ternary_associator` and
`anchored_associator`, and that bound is `Σ_α |c_α| (k_α − 1) = 1·1 + 1·1`
with `k_α = 2`.

Since `C₂^P(η) = 1` exactly (M8, and §11 of the canonical formalization),
`E_T^P ≤ ρ M L_T` for each branch, giving

```
‖Â − P A‖ ≤ 2 ρ M L                                    (k = 2 branches)
```

with `L` the common leaf-norm product. No part of `W₃` is needed.

### 3.2 Deeper rebracketings

If both trees have three internal vertices, `E_T^P ≤ ρ M² L · W₃(η)` by
M13/M14/M15/M20, so

```
‖Â − P A‖ ≤ 2 ρ M² L · W₃(η)                           (k = 3 branches)
```

with `W₃(η) = √(4 − 3η²)` below `η_c = √(2/3)` and `2/(√3 η)` above. For
general branch sizes the universal bound gives
`‖Â − P A‖ ≤ ρ M^{k−1} L (k_T − 1 + k_{T'} − 1)`.

---

## 4. Corrections to legacy statements

| Legacy claim | Status |
|---|---|
| `A(x,y,z;w)` for a ternary `⋆` | **ill-typed** without an anchor; read as `A_e^(4)` |
| rebracketing an `n`-ary law uses `n+1` inputs | **wrong**; it is `2n − 1` unless `n−2` anchors are fixed |
| `A` is *the unique* natural (1,4) tensor from two nested applications | **withdraw**; `T₁−T₂`, `T₂−T₃`, `T₁−T₃` and their combinations all qualify. Uniqueness needs an anchor, a chosen slot, a symmetry class, a formal notion of naturality and a normalization — none of which is currently fixed |
| `R_intr := A` proves "curvature equals associator" | **definition, not theorem**. It is a constitutive choice and should be labelled as such |
| `R(x,y)z = Assoc_∘(x,y,z)` under stated hypotheses | **conditional**, and the only version worth an independent proof and prior-art audit |
| `∇A = 0` follows from `∇μ = 0` | **correct but formal**: `A` is polynomial in `μ`, so a product-compatible connection preserves it. Not comparable to a Bianchi identity |
| universal `δ² = 0`, hence a cohomology | **not available**: the six-term GJI is disproved in general, so `δ² = 0` can only hold on the subclass `{μ : GJI(μ) = 0}`, or must be replaced by a curved structure `Ω := δ² ≠ 0` |
| the KGE rebracketing regularizer is associator evidence | **no**: it is `L_assoc^KGE`, an empirical penalty with its own sampling, contexts and scaling. It is not `A_e`, not `Assoc_∘`, and not the PMT associator |

---

## 5. What is open

The sharp extremal constants for the signed families are **OPEN**, with
certified gaps already recorded in `signed_identities/constants_table.csv`:

| family | arity | triangle bound | certified lower | ratio | verdict |
|---|---|---|---|---|---|
| five-input ternary associator | 3 | 2.0 | 1.3729 | 0.686 | exact constant open |
| anchored associator | 2 | 2.0 | 1.6575 | 0.829 | exact constant open |
| Jacobiator variants | 2 | 3.0 | 2.9828 | 0.994 | sharp |
| Filippov fundamental identity | 3 | 4.0 | 1.6635 | 0.416 | widest gap |

These measure a **difference between two trees**, which is a different
extremal problem from `W₃`, which measures error **inside one tree**. The
bridge of §2 relates them but does not reduce one to the other.

One caution carried from the constants table: the near-zero lower bound for
the six-term GJI comes from an adversarial search over rank-one (collinear)
leaves, where the identity provably vanishes. It is not evidence about the
general case, which is disproved separately.

---

## 6. Verification

`verify_associator_bridge.py` checks the §2 identity and the §3.1 corollary on
randomized instances. Under the theorem those checks are implementation
controls, not evidence for the statement.
