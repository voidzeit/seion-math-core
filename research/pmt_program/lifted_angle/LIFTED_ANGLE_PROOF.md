# Lifted-angle proof of the Theorem R upper bound

```
DATE:          2026-09-14
STATUS:        MACHINE-CHECKED (Lean 4 / Mathlib v4.33.1), normalised single-space form
               — see ../lean/README.md for the exact formal statement and the specification gap
RELATION:      alternative proof of THEOREM_R_v2 §§2–5 (O2, tensor angle lemma, Lemma 3, envelope);
               v2 is frozen and unchanged; this is not a correction of v2
NOVELTY:       not claimed for the auxiliary lemmas (see §7); Theorem R novelty still not established
```

---

## 1. The lifted angle

Let $G$ be a real inner product space and $B = \{f : \lVert f\rVert \le 1\}$ its closed unit ball.

**Definition.** For $f \in B$, the hemisphere lift is
$L(f) := (f, \sqrt{1-\lVert f\rVert^2}) \in G \oplus \mathbb R$ (L² norm). It is a unit vector. For
$f, g \in B$,
$$\varphi(f,g) := \angle\big(L(f), L(g)\big) = \arccos\Big(\langle f,g\rangle + \sqrt{1-\lVert f\rVert^2}\,\sqrt{1-\lVert g\rVert^2}\Big) \in [0,\pi].$$

- **A (metric).** $\varphi$ is the spherical distance between lifts. Hence
  $\varphi(f,h) \le \varphi(f,g) + \varphi(g,h)$ and $\varphi(f,f) = 0$.
  *Lean:* `phi_triangle`, `phi_self`.
- **B (N−).** If $\varphi(f,g) \le S \le \pi$ and $t \ge 0$, then
  $\lVert f - tg\rVert^2 \le 1 + t^2 - 2t\cos S = \lvert 1 - te^{iS}\rvert^2$.
  *Proof.* Let $a = \sqrt{1-\lVert f\rVert^2}$ and $b = \sqrt{1-\lVert g\rVert^2}$. Then
  $\cos S \le \langle f,g\rangle + ab$, so RHS $-$ LHS $\ge a^2 + t^2b^2 - 2tab = (a-tb)^2 \ge 0$.
  *Lean:* `normSq_sub_le`.

## 2. Contraction monotonicity

**Lemma C.** Let $f,g \in G$ and $x,y \in H$ with $\lVert x\rVert, \lVert y\rVert \le 1$ and
$\lVert sf + tg\rVert \le \lVert sx + ty\rVert$ for all real $s,t$. Then $f,g \in B$ and
$\varphi(f,g) \le \varphi(x,y)$.

*Proof.*
- Put $\alpha = \lVert x\rVert^2 - \lVert f\rVert^2$, $\beta = \lVert y\rVert^2 - \lVert g\rVert^2$
  and $\gamma = \langle x,y\rangle - \langle f,g\rangle$. The hypothesis says the form
  $s^2\alpha + t^2\beta + 2st\gamma$ is PSD. So $\alpha, \beta \ge 0$ and $\gamma^2 \le \alpha\beta$.
- With $a, b$ for $x, y$ and $a', b'$ for $f, g$: $a'^2 = a^2 + \alpha$ and $b'^2 = b^2 + \beta$.
- By Cauchy–Schwarz on $(a, \sqrt\alpha)$ and $(b, \sqrt\beta)$:
  $ab + \gamma \le ab + \sqrt{\alpha\beta} \le a'b'$.
- Hence $\cos\varphi(x,y) \le \cos\varphi(f,g)$. $\square$

*Lean:* `phi_le_of_contr`.

## 3. Tensor angle lemma, multilinear form

**Theorem D.** Let $\mu : E^m \to G$ be continuous multilinear with $\lVert\mu\rVert \le 1$, and
$x_i, y_i \in B_E$. Then
$$\varphi\big(\mu(x), \mu(y)\big) \le \sum_i \varphi(x_i, y_i).$$

*Proof.*
- Let $z^{(k)}$ take slots $< k$ from $y$ and the rest from $x$.
- Consecutive tuples differ in slot $k$ only. The map $v \mapsto \mu(\dots, v, \dots)$ (other
  slots in $B$) satisfies the hypothesis of Lemma C by multilinearity and
  $\lVert\mu(z)\rVert \le \prod\lVert z_i\rVert$.
- Telescope with Lemma A. $\square$

*Lean:* `phi_multilinear_le`.

**Recovering Theorem 3.1 of v2.**
- Take unit $u_i, v_i$, so $\varphi(u_i,v_i) = \angle(u_i,v_i)$.
- Theorem D gives $\varphi(\mu u, \mu v) \le \min(S, \pi)$.
- Lemma B gives $\lVert\mu u - t\mu v\rVert \le \lvert 1 - te^{i\min(S,\pi)}\rvert$ for every
  contractive $\mu$. This is Theorem 3.1 in its dual (multilinear) form, which is the only form
  the upper bound uses.
- The projective tensor norm is never needed.

## 4. Lemma 3 and the root

**Domination (definition).** $\mathrm{Dom}(F, R; \rho, \chi)$ means $\lVert F\rVert \le 1$,
$\rho \ge 0$, and $R = \rho\hat R$ with $\hat R \in B$ and $\varphi(F, \hat R) \le \chi$.

**Proposition (equivalence with O2, Definition 2.1 of v2).** For $\rho \ge 0$ and $\chi \ge 0$:
$$\mathrm{Gram}(F,R) \preceq K(\rho,\psi') \text{ for some } \psi' \in [0,\min(\chi,\pi)] \iff \mathrm{Dom}(F,R;\rho,\chi).$$

*Proof.*
- **$\rho = 0$.** Both sides say $\lVert F\rVert \le 1$ and $R = 0$. For "⇐", take $\hat R = F$.
- **$\rho > 0$.** Congruence by $\mathrm{diag}(1, 1/\rho)$ reduces to $\rho = 1$ with $\hat R = R/\rho$.
  - $K(1,\psi) - G \succeq 0$ iff the diagonal is $\le 1$ and
    $\cos\psi \in [G_{12} - m, G_{12} + m]$, where $m = \sqrt{(1-G_{11})(1-G_{22})}$
    (v2, Lemma 2.3, step 3).
  - Some $\psi \le \min(\chi,\pi)$ exists iff $G_{12} + m \ge \cos\min(\chi,\pi)$, i.e. iff
    $\varphi \le \chi$ (recall $\varphi \le \pi$). $\square$

This equivalence is **not** needed by the Lean proof. It only relates the two texts. Numerical
check T6, with 0 mismatches, is in `lifted_angle_check.py`.

**Lemma E (projection).** Let $P$ be an orthogonal projector, $g \in B$, $q = \lVert g - Pg\rVert$
and $c = \sqrt{1-q^2} > 0$. Then $h = c^{-1}Pg \in B$ and $\varphi(g, h) = \arcsin q$.

*Proof.* With $p = \lVert Pg\rVert$: $\langle g,h\rangle = p^2/c$, $1 - \lVert g\rVert^2 = c^2 - p^2$
and $1 - \lVert h\rVert^2 = (c^2-p^2)/c^2$. So $\cos\varphi = p^2/c + (c^2-p^2)/c = c = \cos\arcsin q$. $\square$

*Lean:* `phi_proj` (the $\le$ direction, which is all that is used).

**Lemma F (Lemma 3).** At an internal node with $\lVert\mu\rVert \le 1$, orthogonal $P$, children
$\mathrm{Dom}(F_i, R_i; \rho_i, \chi_i)$, and trajectory closure
$\lVert Q\mu(R_c)\rVert \le \eta\prod\lVert R_i\rVert$, there is $\theta \in [0, \arcsin\eta]$ with
$\mathrm{Dom}\big(\mu(F_c), P\mu(R_c); \cos\theta\prod\rho_i, \theta + \sum\chi_i\big)$.

*Proof.*
- Write $R_i = \rho_i\hat R_i$, $f = \mu(F_c)$, $g = \mu(\hat R_c)$ and $\rho = \prod\rho_i$.
  Then $\mu(R_c) = \rho g$, and Theorem D gives $\varphi(f,g) \le \sum\chi_i$.
- If $\rho = 0$, then $P\mu(R_c) = 0$; take $\theta = 0$.
- Otherwise closure gives $q = \lVert g - Pg\rVert \le \eta$; put $\theta = \arcsin q$.
  - If $c = \cos\theta = 0$, then $Pg = 0$.
  - Else $P\mu(R_c) = (c\rho)\,h$ with $h$ from Lemma E, and
    $\varphi(f,h) \le \varphi(f,g) + \varphi(g,h) \le \sum\chi_i + \theta$. $\square$

*Lean:* `node_step`.

**Lemma G (root).** $\lVert P_r(\mu F_c) - P_r(\mu R_c)\rVert^2 \le 1 - 2\rho\cos(\min(\sum\chi_i, \pi)) + \rho^2$.
*Proof:* $P_r$ is a contraction; then apply Theorem D and Lemma B. *Lean:* `root_step`.

**Leaves.** $\mathrm{Dom}(z, z; 1, 0)$ for $\lVert z\rVert \le 1$. Leaf slots therefore need no
freezing (design D3), and nodes with mixed leaf and internal children are handled uniformly.

**Envelope and upper bound.**
- By induction, every non-root subtree $T_v$ is dominated by
  $(\prod_{u\in T_v}\cos\theta_u,\ \sum_{u\in T_v}\theta_u)$ with $\theta_u \in [0, \arcsin\eta]$
  (*Lean:* `envelope`).
- At the root, Lemma G combined with the Diagonal Lemma (`diagonal_capped`, already formalised)
  gives $E^P_T \le \lvert 1 - w(\tau)^{k-1}\rvert$ for some $\tau \in [0, \arcsin\eta]$
  (*Lean:* `upper_bound`, `theorem_R_upper`).

## 5. Lower bound and sharp constant

The universal witness of v2 Theorem 8.1 is formalised in `WitnessAdm.lean` in the same tree model:
- operator norms $\le 1$;
- $\mathrm{Re}$ and $\mathrm{id}$ are orthogonal projectors;
- **full closure** for arbitrary leaf-slot inputs;
- exact error $\lvert 1 - w(\tau)^{k-1}\rvert$.

With the upper bound this gives `theorem_R_sSup`.

## 6. Numerical checks (post hoc, not preregistered)

`lifted_angle_check.py` (seed 20260914, CPU); output in `outputs/lifted_angle_check.json`:

| Check | Cases | Max violation / error |
|---|---|---|
| T1 triangle | 20 000 | 9.6e-13 |
| T2 contraction (angle) / (cosine) | 20 000 | 2.1e-08 / 2.2e-16 |
| T3 multilinear (random) | 6 000 | 2.1e-08 |
| T3 adversarial hill-climbing | 300 × 400 steps | best = −7.2e-04 (no violation found) |
| T4 projection identity | 20 000 | 4.7e-08 |
| T5 (N−) | 20 000 | 1.8e-15 |
| T6 O2 ⇔ Dom | 20 000 | 0 mismatches |

The angle-level residuals of order $10^{-8}$ are rounding amplified by `arccos` near 1: the
cosine-level check T2 is at $10^{-16}$. These checks are supporting evidence only; the proof is
the Lean development.

## 7. Prior art to check before any novelty statement

- $\cos\varphi(f,g) = \langle f,g\rangle + \sqrt{1-\lVert f\rVert^2}\sqrt{1-\lVert g\rVert^2}$ has
  the form of the **generalized fidelity** for subnormalized pure states.
- $\arccos$ of that fidelity, and the **purified distance** (Tomamichel, Colbeck, Renner), are
  known metrics that are monotone under trace-non-increasing maps. Lemmas A and C are very likely
  the real-Hilbert-space analogue of those facts.
- The telescoping argument (Theorem D) resembles standard hybrid arguments.
- Any statement of novelty for the auxiliary lemmas is therefore excluded until checked. The
  candidate contribution remains Theorem R itself: an exact, topology-independent constant with an
  explicit extremizer. `NOVELTY_NOT_ESTABLISHED` still applies.

## 8. What changes epistemically

| Before (2026-09-13) | After (2026-09-14) |
|---|---|
| Risk concentrated in the human review of Tensor Angle + Lemma 3 (v2 §§2–4) | Upper bound, witness admissibility and sharp constant **machine-checked** in normalised single-space form, via a different and shorter proof |
| Witness admissibility not formalised | Formalised, including full closure |
| Review target: the proof | Review target: the **specification** (Lean definitions of PMT-A, `err`, the sup) and two elementary reductions (scaling N1; per-node spaces → one ambient space), both in `../lean/README.md` |

The v2 dilation/Riesz argument itself remains unreviewed. It is no longer load-bearing for
Theorem R.
