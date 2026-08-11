# Frozen mathematical core V5 — candidate for external review

Date: 2026-08-11. Branch `campaign/gate13-closeout`.
Working title: **Projected Multilinear Trees: Sharp Error Constants Under Approximate Closure**

This document freezes the $k \le 3$ core after a line-by-line review pass that
found three real defects. It is a *candidate for external review*, not an
approved result: novelty remains unestablished and no independent human review
exists (see §7).

---

## 1. Corrections applied in this freeze

Three defects were found by review and are corrected here. All were in
statements or quantifiers; none changed a proved value.

### C1 — Witness closure residuals do not saturate above $\eta_c$

Previously written: *"all closure residuals exactly at cap."*

False for $\eta > \sqrt{2/3}$. The M14 witness sets $t = \min\{\eta,\sqrt{2/3}\}$,
so above the critical value the active leakage is $t = \sqrt{2/3} < \eta$ and the
budget is deliberately underused. The verification table already showed
$0.8165$ rather than $\eta$ for $\eta \in \{0.85, 0.90, 1.00\}$; the prose
contradicted its own data, and the accompanying assertion only tested
$\rho \le \eta$, which is true but weaker than what was claimed.

**Corrected statement.** All operator norms equal $1$; all closure defects
satisfy the prescribed cap; the active defects saturate it precisely for
$\eta \le \sqrt{2/3}$, and for $\eta > \sqrt{2/3}$ the extremiser operates at the
smaller effective leakage $t = \sqrt{2/3}$.

### C2 — M20 cannot claim equality for each fixed dimension and rank

Previously written: *"arbitrary finite ambient dimensions and arbitrary
orthogonal-projector ranks ... $C_T^P(\eta) = W_3(\eta)$."*

Read as a per-realization claim this is false. Any realization with $P_v = I$ at
every internal vertex has $(I-P_v) = 0$, hence $R \equiv F$ and $E_T^P \equiv 0$,
so its constant is $0$, not $W_3(\eta)$. Verified numerically: over 300 random
admissible configurations at dimensions $1$ and $4$ with full-rank projectors,
$\sup E_T^P = 0.000\mathrm{e}{+}00$, against $W_3(0.5) = 1.802776$.

A related observation from the same check: a realization in which **only the
root** projects also gives $E_T^P \equiv 0$. The root projector alone never
generates error — which is precisely the geometric content of the exponent
$k-1$ rather than $k$.

**Corrected statement.** The bound $C_T^P(\eta) \le W_3(\eta)$ holds *uniformly*
over all finite-dimensional Hilbert realizations and all orthogonal projectors,
and is sharp over the *union*:
$$C_T^{\mathfrak{A}_T^{\mathrm{fin}}}(\eta) = W_3(\eta), \qquad \mathfrak{A}_T^{\mathrm{fin}}(\eta) := \bigcup_{\text{finite-dim. realizations}} \mathfrak{A}_T(\eta),$$
with equality already attained in a two-dimensional real realization with
rank-one projectors. The constant is dimension- and rank-**independent**; it is
not attained in every fixed realization.

### C3 — The scaling lemma needs per-leaf factors

A single common $\nu$ cannot normalise leaves of differing norms. Multilinearity
acts independently on each leaf slot, so the correct statement uses $\nu_\ell$
per leaf: with $\mu_v \mapsto \lambda\mu_v$ and $z_\ell \mapsto \nu_\ell z_\ell$,
$$E_T^P \mapsto \lambda^{k}\Bigl(\prod_\ell \nu_\ell\Bigr)E_T^P, \qquad L_T \mapsto \Bigl(\prod_\ell \nu_\ell\Bigr)L_T,$$
so the normalised ratio is invariant and $\nu_\ell := \|z_\ell\|^{-1}$ achieves
$\|z_\ell\| = 1$ for every $\ell$ when all leaves are nonzero. A zero leaf makes
the whole evaluation vanish and does not contribute to the supremum.

---

## 2. Additional changes adopted in this freeze

- **Extended projector** $\widehat P_w := P_w$ for internal $w$, $I_{H_w}$ for
  leaves, promoted into the setup so the closure definition is unambiguous when
  a child is a leaf.
- **Projected-input closure defect** promoted from a convention at the end to a
  primary definition, with the ambient defect defined alongside purely for
  contrast, and $\rho^{\mathrm{proj}} \le \rho^{\mathrm{amb}}$ stated. Every
  theorem controls $\rho^{\mathrm{proj}}$.
- **Universal bound** proved by explicit induction on
  $\|F_v - R_v\| \le k_v\rho M^{k_v-1}L_v$, with argument-wise telescoping inside
  each multilinear map, rather than by a two-line sketch. Numerically checked:
  over 4,000 random admissible $k=3$ configurations the internal and root ratios
  peaked at $0.234$ and $0.041$, both $\le 1$.
- **Notation**: tangent variables renamed $\xi,\zeta$ so they no longer collide
  with the orthonormal vectors $u,v$ in the Gram lemma.
- Title corrected to **Approximate**.

---

## 3. The frozen ladder

$$C_1^P(\eta) = 0 \quad\text{(any realization)}$$

$$\sup_{\text{general }k=2\text{ class}} C_2^P(\eta) = 1, \quad\text{with equality iff EQ1}\wedge\text{EQ2}\wedge\text{EQ3}$$

$$C_T^P(\eta) \le W_3(\eta) \ \text{ uniformly}, \qquad \sup_{\text{finite-dim. realizations}} C_T^P(\eta) = W_3(\eta)$$

for **every** ordered rooted tree $T$ with exactly three internal vertices and
arities $\ge 2$, where

$$W_3(\eta) = \begin{cases}\sqrt{4-3\eta^2}, & 0 < \eta \le \sqrt{2/3},\\[2mm] \dfrac{2}{\sqrt3\,\eta}, & \sqrt{2/3} \le \eta \le 1;\end{cases}$$

$$C_T^P(\eta) \le k-1, \qquad \lim_{\eta\downarrow 0} C_T^P(\eta) = k-1 \quad (\text{any finite tree}).$$

**Asymptotics.** $W_3(\eta) = 2 - \tfrac34\eta^2 - \tfrac{9}{64}\eta^4 + O(\eta^6)$,
verified to three significant figures at $\eta \in \{0.02,0.05,0.1,0.2\}$.

**Two distinct critical numbers**, not to be conflated:
$\eta_\star = \sqrt{(\sqrt5-1)/2} \approx 0.786151$ with $U_3(\eta_\star) = \varphi$
is a transition of the *preliminary triangle-inequality envelope*;
$\eta_c = \sqrt{2/3} \approx 0.816497$ with $W_3(\eta_c) = \sqrt2$ is the *true
extremiser transition*. The golden ratio belongs to the discarded bound, not to
the answer, and should not appear in the abstract or a theorem headline.

**Phase interpretation.** With $G_3(\eta) := \eta W_3(\eta)$ the absolute
extremal error ($M = L_T = 1$),
$$G_3(\eta) = \begin{cases}\eta\sqrt{4-3\eta^2}, & \eta \le \eta_c \quad\text{(budget-limited)},\\[2mm] 2/\sqrt3, & \eta \ge \eta_c \quad\text{(geometry-limited)}.\end{cases}$$
Above $\eta_c$ the absolute worst-case projected error has saturated; the decay
of the dimensionless $W_3$ reflects division by a growing closure budget.
Verified: $G_3 = 1.1547005384 = 2/\sqrt3$ constant for $\eta \ge \eta_c$.

---

## 4. Scope of the freeze

Frozen: definitions, the universal theorem, $k=2$ with equality conditions,
$U_3$, the Gram coupling lemma, $W_3$ with attainment, the $k=3$ universality
over all arities and topologies, asymptotic $(k-1)$ sharpness, the DAG
linearisation with $K(G)$ as an $\eta\downarrow 0$ limit only, and the growing-tree
obstruction.

Not frozen and deferred to an appendix or a later paper: same-law and
rank-one reductions (M21–M23), which matter for the programme but interrupt the
main narrative.

---

## 5. Standing hypotheses

Every result above assumes, and fails without: finite-dimensional Hilbert
spaces; **orthogonal** projectors ($P = P^* = P^2$ — the Pythagorean coupling and
hence the whole $k=3$ sharpening collapses for oblique projectors);
independently selectable node laws unless stated otherwise; and the
**projected-input** closure defect $\rho^{\mathrm{proj}}$, not the ambient one.

Quantified sensitivity to the last: under the ambient convention the M14
witness would exceed its own cap by a factor $20$ at $\eta = 0.05$
($0.9987$ versus $0.05$). This is the single load-bearing modelling choice and
deserves a defended paragraph, not a setup line.

---

## 6. What computation is and is not used for

Explicit constructions and symbolic identities are checked numerically; the
$2.2\times10^{-16}$ agreement of the M14 witness is a sanity check against a
transcription error, not evidence of the theorem. No result here rests on
floating-point evidence.

---

## 7. Why this is not yet a reviewed result

- **Novelty: 0 of 41 registry entries established.** The prior-art registry
  honestly names Higham (compositional backward error), Combettes–Pesquet
  (layered Lipschitz certificates), Hackbusch–Kühn (hierarchical tensor
  formats) and Loday–Vallette (operads). The general framework sits close to
  known work; what looks new are the exact constants. The defensible paper is
  about $W_3$, $K(G)$ and the obstruction — not about the framework.
- **Independent human review: none.** The review that produced the corrections
  above followed this project's own thread and had access to its registry; it is
  a useful assisted audit, not independence. The next epistemic milestone is two
  external mathematicians reconstructing the proofs from statements and
  hypotheses alone.
- A prior version of M10 inferred a strict supremum gap from non-attainment,
  which is invalid; it was downgraded to `PROVED_NON_ATTAINMENT`. The strict gap
  now follows from M14/M15's exact values instead. This is recorded because the
  same inference pattern is easy to repeat.

That one review pass found three real defects is the argument for obtaining
several more before submission, not for treating the core as settled.
