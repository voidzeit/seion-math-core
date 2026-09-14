# Exact certificates for the chain Gram SDP

Status: **CERTIFIED** at the listed rational points, in the following precise
sense: a standard-library-only verifier checks, in exact rational arithmetic, a
dual certificate whose validity for PMT-A (and PMT-A[C]) is proved below, and
checks a matching admissible witness. This is an independent machine check of
Theorem C at those points, not a proof of Theorem C for all `η`.

Pipeline (as requested):

```
floating SDP → rational reconstruction → exact polynomial (linear) identity → exact PSD verification
```

---

## 1. The model and why it is valid for the original class

Use the operator reduction of `CHAIN_ALL_K.md` §2.1 (`n = k−1` active stages,
`A_1(1) = f`, `P_0 = I`, contractions `A_j`, `‖Q_jA_jP_{j−1}‖ ≤ η`).

**Sources.** `d_i := Q_iA_iR_{i−1}` is born at stage `i`;
`u_i^{(j)} := A_j⋯A_{i+1}d_i` is its transport to stage `j`. By induction
`e_j = A_je_{j−1} + d_j = Σ_{i≤j} u_i^{(j)}`. The **state list**
`X_j := (R_j, u_1^{(j)}, …, u_j^{(j)})` obeys

```
X_j = (P_jA_jR_{j−1}, A_ju_1^{(j−1)}, …, A_ju_{j−1}^{(j−1)}, Q_jA_jR_{j−1}).
```

**Gram variables.** `GP_j := Gram(P_jX_j)`, `GQ_j := Gram(Q_jX_j)`
(size `j+1`). The stage-`j` input list is
`L_j := (P_{j−1}X_{j−1}, Q_{j−1}X_{j−1})` (length `2j`), and
`HP_j := Gram(P_jA_jL_j)`, `HQ_j := Gram(Q_jA_jL_j)` (size `2j`).

**Lemma V (necessity).** For every admissible chain realization (real or
complex; in the complex case take real parts of the Hermitian Grams):

1. `HP_j ⪰ 0`, `HQ_j ⪰ 0`;
2. `HP_j + HQ_j ⪯ diag(GP_{j−1}, GQ_{j−1})`;
3. `(HQ_j)_{[1..j],[1..j]} ⪯ η² GP_{j−1}`;
4. `GP_j = T_P^{(j)ᵀ} HP_j T_P^{(j)}`, `GQ_j = T_Q^{(j)ᵀ} HQ_j T_Q^{(j)}` with the
   fixed 0/1 selector matrices of `k4_exploration/chain_gram_sdp.py::selectors`;
5. `GP_0 = [1]`, `GQ_0 = [0]`, and `‖e_n‖² = aᵀ(GP_n + GQ_n)a`, `a = (0,1,…,1)`.

*Proof.* (1) Gram matrices. (2) `P_{j−1}X ⊥ Q_{j−1}X`, so
`Gram(L_j) = diag(GP_{j−1}, GQ_{j−1})`; `HP_j + HQ_j = Gram(A_jL_j) =
L_j^*A_j^*A_jL_j ⪯ L_j^*L_j` since `‖A_j‖ ≤ 1`. (3) For every coefficient vector
`c`, `‖Q_jA_j Σ c_i P_{j−1}x_i‖ ≤ η‖Σ c_i P_{j−1}x_i‖` by closure on **all of**
`Ran P_{j−1}`. (4) `R_{j−1} ∈ Ran P_{j−1}` gives `P_{j−1}R_{j−1} = R_{j−1}`,
`Q_{j−1}R_{j−1} = 0`; `A_ju = A_jP_{j−1}u + A_jQ_{j−1}u`; read off `P_j` and
`Q_j` parts. (5) `X_0 = (x)`, `x = 1`, `P_0 = I`; `e_n = Σ u_i`. Real parts
preserve (1)–(5) because every matrix coefficient is real. `□`

So the SDP value `Val_n(η) := max aᵀ(GP_n+GQ_n)a` subject to 1–5 is `≥ G_{k,chain}(η)²`
for PMT-A and PMT-A[C]. (The converse — that the SDP is *exact* — is the
sufficiency argument of `CHAIN_GRAM_REPORT.md` §7; it is **not** needed for an
upper-bound certificate and is not used here.)

The SDP is *not* a relaxation of the multilinear class of any other skeleton:
bilinear vertices impose projective-norm constraints that are not Gram
constraints. A certificate for BBR or STAR would need a different model.

## 2. The dual as a backward recursion

Multipliers: `Z3_j ⪰ 0` (size `2j`) for (2), `Z4_j ⪰ 0` (size `j`) for (3).
Eliminate the multipliers of (1):

```
Z1_j := Z3_j − T_P (Z3_{j+1}[PP] + η² Z4_{j+1}) T_Pᵀ ,        Z1_n := Z3_n − T_P aaᵀ T_Pᵀ,
Z2_j := Z3_j + emb(Z4_j) − T_Q Z3_{j+1}[QQ] T_Qᵀ ,           Z2_n := Z3_n + emb(Z4_n) − T_Q aaᵀ T_Qᵀ,
```

(`[PP]` = leading `(j+1)×(j+1)` block, `[QQ]` = trailing block, `emb` pads
`Z4_j` into the leading block).

**Lemma D (weak duality, exact identity).** For any symmetric `Z3, Z4` and any
point satisfying 4–5,

```
V − aᵀ(GP_n+GQ_n)a = Σ_j [⟨Z3_j, slack2_j⟩ + ⟨Z4_j, slack3_j⟩ + ⟨Z1_j, HP_j⟩ + ⟨Z2_j, HQ_j⟩],
V := Z3_1[0,0] + η² Z4_1[0,0].
```

*Proof.* Expand the right side; `⟨T X Tᵀ, H⟩ = ⟨X, TᵀHT⟩` turns every
`Z3_{j+1}, Z4_{j+1}` term into a pairing with `GP_j, GQ_j`, the `HP_j + HQ_j` and
`emb(Z4_j)` pairings cancel, the sum telescopes, and only the `j = 1` constants
`GP_0 = [1]`, `GQ_0 = [0]` and the terminal `aaᵀ` pairing survive. `□`

Hence if `Z1_j, Z2_j, Z3_j, Z4_j ⪰ 0` for all `j`, every feasible point has
objective `≤ V`: **a certificate is a list of rational PSD matrices, with no
equality constraints besides the definitions above.** Structurally this is a
backward LMI recursion `Z_j ⪰ Ψ_η(Z_{j+1})` from the terminal data `aaᵀ` — the
dual counterpart of the forward state recursion (`RECURSION.md`).

## 3. Reconstruction procedure (`certificates/generate_certificate.py`)

1. Choose `η = t` with `t² + c² = 1`, `t, c ∈ ℚ` (Pythagorean), below the
   critical leakage, so the planar witness is rational and
   `V* = E_k(t²) ∈ ℚ`.
2. Solve the dual SDP (Clarabel, tolerances `10⁻¹²`).
3. **Facial constraints from the witness.** Build the witness primal point
   `HP_j, HQ_j` exactly (rational rank-one Grams). Complementary slackness forces
   `Z1_j HP_j = 0` and `Z2_j HQ_j = 0` at any dual optimum; these are exact linear
   equations in the entries of `Z3, Z4`. Add `V = V*`.
4. Round the floating dual to rationals (denominators `≤ 10⁶`) and project it
   exactly onto the affine space of step 3 (minimum-norm correction over `ℚ`).
5. Verify exact PSD of every `Z1_j, Z2_j, Z3_j, Z4_j`: all coefficients of
   `det(xI + Z)` (sums of principal minors) are `≥ 0`.

No floating-point step is trusted: step 5 and the separate verifier decide.
For all seven points below, the witness-induced face of step 3 sufficed: the
rounded-and-projected point passed step 5 on the first attempt, with no further
facial reduction.

## 4. Results

`python research/pmt_program/certificates/verify_certificates.py`
(stdlib only; ≈1.6 s):

| k | η | certified `G² = V` (upper = witness) | `C²` | `C` |
|---|---|---|---|---|
| 3 | 3/5 | 657/625 | 73/25 | 1.708800749 |
| 3 | 4/5 | 832/625 | 52/25 | 1.442220510 |
| 4 | 3/5 | 25353/15625 | 2817/625 | 2.123016722 |
| 4 | 5/13 | 4951225/4826809 | 198049/28561 | 2.633295654 |
| 4 | 8/17 | 32186944/24137569 | 502921/83521 | 2.453872776 |
| 5 | 5/13 | 1255624225/815730721 | 50224969/4826809 | 3.225743136 |
| 5 | 8/17 | 12746146816/6975757441 | 199158544/24137569 | 2.872451517 |

Each `C²` equals `E_k(η²)/η²` from Theorem C exactly (e.g. `k=4, η=3/5`:
`9 − 15·9/25 + 7·81/625 = 2817/625`).

**Negative controls** (all rejected by the verifier): lowering `Z3_1[0,0]` by
`10⁻⁹`; perturbing one off-diagonal entry of `Z3_3` by `10⁻³` (breaks PSD — the
certificate sits on the PSD boundary, as a tight certificate must); changing `η`
to `4/5` with the same matrices.

## 5. Scope and limits

* Certifies `C^P_{k,chain}(η)` exactly at the seven listed points, for PMT-A and
  PMT-A[C], independently of the analytic proof.
* Does not certify other `η` (a parametric certificate in `t` would need
  polynomial matrix entries; the backward recursion suggests they exist).
* Does not apply to non-chain skeletons (§1). For BBR/STAR the analogous
  exact object would be an LP/SDP hierarchy certificate for real `2×2`
  bilinear/trilinear norm balls; not attempted.
* Above the critical leakage the witness uses `t = √s_c` (irrational for
  `k ≥ 4`); certificates there would need algebraic-number arithmetic.
