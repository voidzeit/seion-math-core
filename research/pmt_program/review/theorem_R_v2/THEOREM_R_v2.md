# Theorem R: the sharp projected-error constant of a PMT depends only on its number of internal nodes

**Canonical source, v2.** Written from scratch on 2026-09-13; it replaces
`../../THEOREM_R_DRAFT.md` and restructures the frozen
`../theorem_R_v1/REVIEW_PACKAGE_v1.md`. The mathematics of v1 is unchanged; see
`CHANGELOG_v2.md` for what changed. This file is frozen by `FREEZE_v2.json`, and
corrections go to `v3`.

**Status:** `ADVISORY_PROOF_DRAFT`. Author audit only; no independent review;
novelty not established. Class: real PMT-A. Nothing here concerns cosmology,
KGE, Hodge theory, VECTRA or applications.

**Terminology.** $k$ is the **number of internal nodes** of the tree, not its
depth. A chain with $k$ internal nodes has depth $k$; a star with $k$ internal
nodes has depth $2$.

**Dependency chain**

$$
\text{Definitions} \to \text{O2} \to \text{Tensor angle lemma} \to \text{Lemma 3} \to \text{Multiplicative envelope} \to \text{Diagonal Lemma} \to \text{Upper bound}
$$

$$
\text{Universal sharp witness} \to \text{Lower bound}, \qquad \text{Upper} + \text{Lower} \Rightarrow \text{Theorem R}.
$$

Sections 3 (tensor angle lemma) and 6 (Diagonal Lemma) use no PMT vocabulary
and can be read and cited on their own.

---

## 1. Definitions

### 1.1 The class PMT-A

1. **Tree.** $T$ is a finite rooted tree with internal nodes $V_{\rm int}$,
   $k := \lvert V_{\rm int}\rvert \ge 1$, root $r$, and leaves $L$. Each internal
   node $v$ has $m_v \ge 1$ ordered children; some may be leaves, some internal.
2. **Spaces.** Each node $w$ carries a finite-dimensional **real** Hilbert space
   $H_w$ of arbitrary dimension (dimension $2$ is allowed).
3. **Projectors.** Each internal $v$ carries an orthogonal projector $P_v$ of
   arbitrary rank, including rank $1$, rank $0$ and $P_v = I$ (also at the root).
   Write $Q_v := I - P_v$.
4. **Laws.** Each internal $v$ carries a multilinear map $\mu_v$ from the
   product of its children's spaces to $H_v$. Its operator norm
   $\lVert\mu_v\rVert := \sup\{\lVert\mu_v(x_1,\dots)\rVert : \lVert x_i\rVert \le 1\}$
   is at most $M$. Laws are chosen **independently** at different nodes.
5. **Evaluations.** Leaves carry nonzero data $z_\ell$. Set
   $F_\ell = R_\ell = z_\ell$, and for internal $v$
   $F_v = \mu_v(F_{\text{children}})$ and
   $R_v = P_v\,\mu_v(R_{\text{children}})$.
6. **Closure (full subspace).** For every internal $v$:
   $\lVert Q_v\mu_v(x_1,\dots)\rVert \le \rho\prod\lVert x_i\rVert$ whenever
   each internal-child slot receives a vector in that child's
   $\operatorname{Ran}P$. Leaf slots receive **arbitrary** vectors. Here
   $0 < \rho \le M$ and $\eta := \rho/M \in (0,1]$. The value $\eta = 0$ is not
   part of the class.
7. **Error and constant.**
   $$E^P_T := \lVert P_rF_r - R_r\rVert, \qquad C^P_T(\eta) := \sup\frac{E^P_T}{\rho\,M^{k-1}\prod_\ell\lVert z_\ell\rVert},$$
   the supremum taken over all admissible realizations, dimensions and ranks.

### 1.2 Normalization and trajectory closure

* **N1 (scaling).** The ratio is invariant under $\mu_v \mapsto \lambda\mu_v$ and
  $z_\ell \mapsto \nu_\ell z_\ell$, so we take $M = 1$, $\rho = \eta$ and unit
  leaves.
* **N2 (leaf freezing).** Fixing leaf arguments at the leaf data gives, at each
  internal $v$ with internal children $c_1,\dots,c_m$ ($m \ge 0$), a multilinear
  map on the internal slots. It has norm $\le 1$, leaves $F$ and $R$ unchanged,
  and satisfies **trajectory closure**:
  $$\textbf{(TC)}\qquad \lVert Q_v\mu_v(R_{c_1},\dots,R_{c_m})\rVert \le \eta\prod_i\lVert R_{c_i}\rVert,$$
  since $R_{c_i} \in \operatorname{Ran}P_{c_i}$. For $m = 0$, $\mu_v$ is a vector
  $f_v$ with $\lVert f_v\rVert \le 1$ and $\lVert Q_vf_v\rVert \le \eta$.
* **The upper bound uses only norms $\le 1$, orthogonality of each $P_v$, and
  (TC).** The witness satisfies the full closure of 1.1(6).

### 1.3 The constant and the theorem

$$w(\theta) := \cos\theta\, e^{i\theta} = \tfrac12\bigl(1 + e^{2i\theta}\bigr), \qquad C_k(\eta) := \frac1\eta\max_{0\le\theta\le\arcsin\eta}\bigl\lvert 1 - w(\theta)^{k-1}\bigr\rvert .$$

> **Theorem R.** For every finite rooted tree $T$ in real PMT-A with $k$
> internal nodes and every $\eta \in (0,1]$: $\;C^P_T(\eta) = C_k(\eta)$.

The number of internal nodes and the leakage determine the sharp constant; depth
and topology do not.

---

## 2. The order O2

For $\rho \ge 0$ and $\psi \in [0,\pi]$ let

$$K(\rho,\psi) := \begin{pmatrix} 1 & \rho\cos\psi \\ \rho\cos\psi & \rho^2 \end{pmatrix},$$

the Gram matrix of a unit vector and a vector of norm $\rho$ at angle $\psi$.
Angles are $\angle(a,b) = \arccos\bigl(\langle a,b\rangle/(\lVert a\rVert\lVert b\rVert)\bigr)$;
the angle is a metric on the unit sphere. $\preceq$ is the Löwner order.

**Definition 2.1 (O2).** A pair $(F,R)$ is *dominated by the label*
$(\rho,\chi)$, with $\rho \ge 0$ and $\chi \ge 0$, if

$$\operatorname{Gram}(F,R) \preceq K(\rho,\psi') \quad\text{for some } \psi' \in [0,\min(\chi,\pi)].$$

The label $\chi$ is a *cumulative* phase bookkeeping parameter. It is not
reconstructed from the Gram matrix, which only records an angle in $[0,\pi]$.

**Lemma 2.2 (realization).**
*Hypotheses:* $\operatorname{Gram}(F,R) \preceq K(\rho,\psi)$, $\rho \ge 0$,
$\psi \in [0,\pi]$.
*Conclusion:* for a 2-dimensional real space $X$ with unit $\hat F, \hat R$ at
angle $\psi$, there is $B : X \to H$ with $\lVert B\rVert \le 1$,
$B\hat F = F$ and $B(\rho\hat R) = R$. In particular $\lVert F\rVert \le 1$ and
$\lVert R\rVert \le \rho$.

*Proof.* For real $\alpha, \beta$,
$\lVert\alpha F + \beta R\rVert^2 \le \lVert\alpha\hat F + \beta\rho\hat R\rVert^2$.
So $B(\alpha\hat F + \beta\rho\hat R) := \alpha F + \beta R$ is well defined and
contractive on the span. Extend by $0$ on the orthogonal complement. This covers
$\rho = 0$ (forcing $R = 0$) and $\psi \in \{0,\pi\}$ (forcing $R = \pm\rho F$).
$\square$

**Lemma 2.3 ((N−) implies O2).**
*Hypotheses:* $S \in [0,\pi]$, and vectors $f, g$ with
$$\textbf{(N−)}\qquad \lVert af + bg\rVert \le \lvert ae^{iS} + b\rvert \quad \text{for all real } a,b \text{ with } ab \le 0.$$
*Conclusion:* $\operatorname{Gram}(f,g) \preceq K(1,\psi)$ for some $\psi \in [0,S]$.

*Proof.* Let $G = \operatorname{Gram}(f,g)$.

1. The cases $b = 0$ and $a = 0$ give $G_{11}, G_{22} \le 1$. Put
   $\mu := \sqrt{(1-G_{11})(1-G_{22})}$.
2. (N−) reads
   $a^2(1-G_{11}) + b^2(1-G_{22}) - 2\lvert ab\rvert(\cos S - G_{12}) \ge 0$.
   Minimizing over the ratio $\lvert a\rvert : \lvert b\rvert$, this holds for
   all $a, b$ iff $G_{12} + \mu \ge \cos S$.
3. $K(1,\psi) - G \succeq 0$ iff $\cos\psi \in [G_{12} - \mu,\, G_{12} + \mu]$,
   since the diagonal entries are $\ge 0$.
4. This interval meets $[\cos S, 1]$: we have $G_{12} - \mu \le 1$, and
   $\cos S \le G_{12} + \mu$ by step 2.
5. Take $\cos\psi$ in the intersection. Then $\psi \in [0,S]$. $\square$

*Why this is the heart of "extra alignment cannot help":* (N−) bounds the
alignment $G_{12}$ only from below. Any excess alignment is absorbed by a
dilation angle $\psi < S$.

---

## 3. The tensor angle lemma (PMT-free)

For real Hilbert spaces, $\lVert\cdot\rVert_\pi$ is the projective tensor norm,
the dual of the multilinear operator norm.

> **Theorem 3.1.** Let $u_i, v_i \in H_i$ be unit vectors,
> $\psi_i := \angle(u_i,v_i)$ and $S := \sum_{i=1}^m\psi_i$. For all real
> $a, b$ with $ab \le 0$:
> $$\Bigl\lVert a\bigotimes_{i=1}^m u_i + b\bigotimes_{i=1}^m v_i\Bigr\rVert_\pi \le \bigl\lvert ae^{i\min(S,\pi)} + b\bigr\rvert .$$

*Proof.*

*Reductions.*

* Take $a = 1$, $b = -t$ with $t \ge 0$.
* If $S \ge \pi$ the right side is $1 + t$ and the claim is the triangle
  inequality. So assume $S < \pi$.
* Embed $1$-dimensional factors isometrically into $\mathbb R^2$; projective
  norms are preserved.

*Induction on $m$.* For $m = 1$ the claim is the Hilbert identity
$\lVert u - tv\rVert^2 = 1 + t^2 - 2t\cos\psi_1$. For $m \ge 2$:

1. Put $X = \bigotimes_{i\ge2}u_i$, $Y = \bigotimes_{i\ge2}v_i$ and
   $S' = S - \psi_1$. By associativity of $\otimes_\pi$ and duality, the left
   side is $\sup_\beta[\beta(u_1,X) - t\beta(v_1,Y)]$ over bilinear $\beta$ on
   $H_1\times(\otimes_{i\ge2}H_i)$ with $\lvert\beta(z,W)\rvert \le \lVert z\rVert\lVert W\rVert_\pi$.
2. Fix a 2-plane $\Pi \ni u_1, v_1$. By Riesz,
   $\beta(z,W) = \langle z, \Lambda W\rangle$ for $z \in \Pi$, with
   $\lVert\Lambda W\rVert \le \lVert W\rVert_\pi$.
3. Put $p = \Lambda X$ and $q = \Lambda Y$. By induction,
   $\lVert\alpha p + \beta q\rVert \le \lvert\alpha e^{iS'} + \beta\rvert$ for
   $\alpha\beta \le 0$.
4. Lemmas 2.3 and 2.2 give unit $\hat p, \hat q$ at angle $\tilde\psi \le S'$
   and a contraction $C$ with $C\hat p = p$, $C\hat q = q$.
5. With $\mathrm{Rot}$ the rotation of $\Pi$ taking $v_1$ to $u_1$:
   $\beta(u_1,X) - t\beta(v_1,Y) = \langle u_1,\, C\hat p - t\,\mathrm{Rot}\,C\hat q\rangle \le \lVert C\hat p - t\,\mathrm{Rot}\,C\hat q\rVert$.
6. Let $V = (C, (I - C^*C)^{1/2})$, an isometry into $\Pi \oplus D$, and
   $\tilde R = \mathrm{Rot}\oplus I$. For unit $y$,
   $\langle y,\tilde Ry\rangle = \lVert y_\Pi\rVert^2\cos\psi_1 + \lVert y_D\rVert^2 \ge \cos\psi_1$,
   so $\angle(y,\tilde Ry) \le \psi_1$.
7. The $\Pi$-component of $V\hat p - t\tilde RV\hat q$ is
   $C\hat p - t\,\mathrm{Rot}\,C\hat q$. The vectors $V\hat p$ and
   $t\tilde RV\hat q$ have norms $1$ and $t$ and make an angle at most
   $\tilde\psi + \psi_1 \le S < \pi$.
8. Hence the quantity in step 5 is at most $\lvert 1 - te^{iS}\rvert$. $\square$

**Proposition 3.2 (sharpness).** If $S \le \pi$, equality holds.

*Proof.* Identify each $\Pi_i \cong \mathbb C$ with $v_i \mapsto 1$ and
$u_i \mapsto e^{i\psi_i}$. Let $\pi_i$ be the orthogonal projection onto
$\Pi_i$. For $\lvert\lambda\rvert = 1$ the form
$W(x) = \operatorname{Re}\bigl(\lambda\prod_i\pi_ix_i\bigr)$ has norm $\le 1$,
and $W(\otimes u_i) - tW(\otimes v_i) = \operatorname{Re}\bigl(\lambda(e^{iS} - t)\bigr)$.
Choose $\lambda$. $\square$

---

## 4. Lemma 3: O2 is preserved at every non-root internal node

**Lemma 4.1 (child substitution and closure normalization).**
*Hypotheses:* internal $v$ with internal children $c_1,\dots,c_m$, $m \ge 1$;
$\lVert\mu_v\rVert \le 1$; (TC) holds; each $(F_{c_i}, R_{c_i})$ is dominated by
$(\rho_i,\chi_i)$ via $\psi_i \in [0,\min(\chi_i,\pi)]$.
*Conclusion:* with $B_i$ from Lemma 2.2 (unit $\hat F_i, \hat R_i$ at angle
$\psi_i$), $\mu'(x) := \mu_v(B_1x_1,\dots,B_mx_m)$ and $\rho := \prod_i\rho_i$:

* (i) $\lVert\mu'\rVert \le 1$;
* (ii) $F_v = \mu'(\hat F_1,\dots)$ and $\mu_v(R_{c_1},\dots) = \rho\,\mu'(\hat R_1,\dots)$;
* (iii) if $\rho > 0$ then $\lVert Q_v\mu'(\hat R_1,\dots)\rVert \le \eta$;
* (iv) if $\rho = 0$ then $\mu_v(R_{c_1},\dots) = 0$.

*Proof.* (i) Composition with contractions. (ii) Multilinearity.
(iii) By (ii) and (TC),
$\lVert Q_v\mu'(\hat R)\rVert = \lVert Q_v\mu_v(R_c)\rVert/\rho \le \eta\prod\lVert R_{c_i}\rVert/\rho \le \eta$,
using $\lVert R_{c_i}\rVert \le \rho_i$. (iv) Some $R_{c_i} = 0$. $\square$

> **Lemma 4.2 (Lemma 3).** Let $v \ne r$ be internal, with $m \ge 0$ internal
> children satisfying the hypotheses of Lemma 4.1. Then there is
> $\theta_v \in [0,\arcsin\eta]$ such that $(F_v, R_v)$ is dominated by
> $$(\rho_v, \chi_v) := \Bigl(\cos\theta_v\prod_i\rho_i,\;\; \theta_v + \sum_i\chi_i\Bigr)$$
> (empty product $1$, empty sum $0$). When $\prod_i\rho_i > 0$ one can take
> $$\sin\theta_v = \frac{\lVert Q_v\mu_v(R_{c_1},\dots,R_{c_m})\rVert}{\prod_i\rho_i}.$$

*Proof.*

*Case $\prod_i\rho_i = 0$* ($m \ge 1$). By Lemma 4.1(iv) $R_v = 0$, and
$\lVert F_v\rVert \le 1$. So
$\operatorname{Gram}(F_v, 0) \preceq K(0,0)$. Take $\theta_v = 0$.

*Case $\rho := \prod_i\rho_i > 0$.*

1. **Raw output.** Put $f = \mu'(\hat F)$ and $g = \mu'(\hat R)$, so $F_v = f$
   and $R_v = \rho P_vg$. For $m = 0$ take $f = g = f_v$, $\rho = 1$, $S = 0$;
   otherwise $S = \sum\psi_i$.
2. **(N−).** With $S' = \min(S,\pi)$, for $ab \le 0$:
   $\lVert af + bg\rVert \le \lVert a\otimes\hat F + b\otimes\hat R\rVert_\pi \le \lvert ae^{iS'} + b\rvert$
   (Theorem 3.1; for $m = 0$ directly).
3. **Domination of the raw output.** Lemmas 2.3 and 2.2 give unit
   $\hat F', \hat E'$ at angle $\tilde\psi \le S'$ and a contraction $C$ with
   $C\hat F' = f$, $C\hat E' = g$.
4. **Dilation.** Let $V = (C, (I - C^*C)^{1/2})$, $P' = P_v \oplus I$,
   $\tilde F = V\hat F'$ and $\tilde R = \rho P'V\hat E'$. Their
   $H_v$-components are $F_v$ and $R_v$, so
   $\operatorname{Gram}(F_v,R_v) \preceq \operatorname{Gram}(\tilde F,\tilde R)$.
5. **Norms.** $\lVert\tilde F\rVert = 1$. Since
   $\lVert(I - P')V\hat E'\rVert = \lVert Q_vg\rVert \le \eta$ (Lemma 4.1(iii);
   N2 for $m = 0$), put $\theta_v := \arcsin\lVert Q_vg\rVert$. Then
   $\lVert\tilde R\rVert = \rho\cos\theta_v$, and
   $\lVert Q_vg\rVert = \lVert Q_v\mu_v(R_c)\rVert/\rho$ gives the displayed
   formula.
6. **Angle.** If $\tilde R = 0$, dominated by $K(0,0)$. Otherwise
   $\angle(\tilde F,\tilde R) \le \tilde\psi + \theta_v \le \chi_v$, since
   $\tilde\psi \le S' \le \sum\chi_i$. So
   $\operatorname{Gram}(\tilde F,\tilde R) = K(\rho_v, \angle(\tilde F,\tilde R))$. $\square$

---

## 5. The multiplicative envelope

Encode a label as $z = \rho e^{i\chi}$. Lemma 4.2 reads $z_v = w(\theta_v)\prod_i z_{c_i}$.

**Proposition 5.1 (unrolling).** Apply Lemma 4.2 bottom-up. For every non-root
internal $v$, $(F_v,R_v)$ is dominated by
$$z_v = \prod_{u \in V_{\rm int}(T_v)} w(\theta_u),$$
where $T_v$ is the subtree of $v$. The subtrees of the root's internal children
are pairwise disjoint and together contain every non-root internal node exactly
once. So the root's children together carry exactly $k-1$ factors:
$$\prod_i z_{c_i} = \prod_{u \in V_{\rm int}\setminus\{r\}} w(\theta_u).$$
$\square$

The "exactly once" uses that $T$ is a tree; for DAGs this step fails as stated.
Informally, O2 induces a commutative multiplicative envelope for tree states.

**Lemma 5.2 (root reading).**
*Hypotheses:* root with $m \ge 1$ internal children, dominated by
$(\rho_i,\chi_i)$ via angles $\psi_i$; $\lVert\mu_r\rVert \le 1$. No closure is
needed at the root.
*Conclusion:* $E^P_T \le \lvert 1 - \rho e^{i\min(S,\pi)}\rvert$, with
$\rho = \prod\rho_i$ and $S = \sum\psi_i$.

*Proof.* $E^P_T = \lVert P_r(\mu_r(F_c) - \mu_r(R_c))\rVert$. Substitute the
children (Lemma 4.1(i)–(ii)), scalarize with a unit $\omega \in \operatorname{Ran}P_r$,
and apply Theorem 3.1 with $a = 1$, $b = -\rho$. If $\rho = 0$ the bound is
$1 \ge \lVert F_r\rVert$. $\square$

**Corollary 5.3.** There are $\theta_u \in [0,\arcsin\eta]$, one for each
$u \in V_{\rm int}\setminus\{r\}$, with
$$E^P_T \le \Bigl\lvert 1 - R\,e^{i\min(\Theta,\pi)}\Bigr\rvert, \qquad R = \prod_{u\ne r}\cos\theta_u,\quad \Theta = \sum_{u\ne r}\theta_u ,$$
and for $\Theta \le \pi$ the right side equals $\bigl\lvert 1 - \prod_{u\ne r}w(\theta_u)\bigr\rvert$.

*Proof.* Lemma 5.2 with $S \le \Theta$; $\lvert 1 - Re^{i\varphi}\rvert$ is
nondecreasing in $\varphi \in [0,\pi]$ for $R \ge 0$. $\square$

---

## 6. The Diagonal Lemma (PMT-free)

Throughout, $n \ge 1$ and $\alpha \in (0,\pi/2]$.

**Lemma 6.1 (subadditivity of cosine products).** If $\theta_j \ge 0$ and
$\sum_j\theta_j \le \pi/2$, then $\prod_j\cos\theta_j \ge \cos\bigl(\sum_j\theta_j\bigr)$.

*Proof.* Induction on $n$. All partial sums lie in $[0,\pi/2]$, so the sines and
cosines involved are $\ge 0$. Then
$\cos(a+b) = \cos a\cos b - \sin a\sin b \le \cos a\cos b$, and multiplying the
inductive inequality by $\cos\theta_n \ge 0$ preserves it. $\square$

The hypothesis $\sum\theta_j \le \pi/2$ is essential for $\Theta > \pi$. With
$n = 4$ and $\theta_j = \pi/2 - \varepsilon$: $R = \sin^4\varepsilon \approx 0$
while $\cos\Theta \approx 1$ (`outputs/diagonal_lemma_check.json`). For
$\Theta \in (\pi/2,\pi]$ the conclusion $R \ge \cos\Theta$ holds trivially,
because $\cos\Theta \le 0 \le R$.

**Lemma 6.2 (Jensen for $\log\cos$).** $\log\cos$ is strictly concave on
$[0,\pi/2)$, since $(\log\cos)'' = -\sec^2 < 0$. Hence for
$\theta_j \in [0,\pi/2)$, $\prod_j\cos\theta_j \le \cos^n(\Theta/n)$, with
equality iff all $\theta_j$ are equal.

> **Lemma 6.3 (Diagonal Lemma).**
> $$\max_{\theta\in[0,\alpha]^n}\Bigl\lvert 1 - \prod_{j=1}^n w(\theta_j)\Bigr\rvert = \max_{\theta\in[0,\alpha]}\bigl\lvert 1 - w(\theta)^n\bigr\rvert .$$
> Moreover, for every $\theta \in [0,\alpha]^n$,
> $\bigl\lvert 1 - Re^{i\min(\Theta,\pi)}\bigr\rvert \le \max_{t\in[0,\alpha]}\lvert 1 - w(t)^n\rvert$,
> with $R = \prod\cos\theta_j$ and $\Theta = \sum\theta_j$.

*Proof.* "$\ge$" is the diagonal choice. For "$\le$", write
$\prod w(\theta_j) = Re^{i\Theta}$ and let $\varphi := \min(\Theta,\pi)$. Then
$\lvert 1 - Re^{i\varphi}\rvert^2 = f_\varphi(R) := 1 - 2R\cos\varphi + R^2$.
For $\Theta \le \pi$ this is also the value at the original point. For
$\Theta > \pi$ we bound the capped quantity, which dominates the true value:
$\lvert 1 - Re^{i\Theta}\rvert \le 1 + R$ in all cases.

*Case some $\theta_j = \pi/2$* (then $\alpha = \pi/2$). $R = 0$, the value is
$1$, and $t = \pi/2$ gives $\lvert 1 - w(\pi/2)^n\rvert = 1$. From now on all
$\theta_j < \pi/2$.

*Case $\Theta \le \pi$.*

1. $R \ge \cos\Theta$: by Lemma 6.1 if $\Theta \le \pi/2$, and trivially
   otherwise.
2. $f_\Theta'(R) = 2(R - \cos\Theta) \ge 0$ on $[R, \cos^n(\Theta/n)]$, so
   $f_\Theta(R) \le f_\Theta(\cos^n(\Theta/n))$ by Lemma 6.2.
3. $f_\Theta(\cos^n(\Theta/n)) = \lvert 1 - w(\Theta/n)^n\rvert^2$ and
   $\Theta/n \le \alpha$.

*Case $\Theta > \pi$.* Then $n\alpha > \pi$, so $n \ge 3$ and $\pi/n < \alpha$.
$$\lvert 1 - Re^{i\varphi}\rvert = 1 + R \le 1 + \cos^n(\Theta/n) \le 1 + \cos^n(\pi/n) = \lvert 1 - w(\pi/n)^n\rvert,$$
by Lemma 6.2, monotonicity of $\cos$ on $[0,\pi/2]$, and
$w(\pi/n)^n = -\cos^n(\pi/n)$. $\square$

The split at $\Theta = \pi$ is necessary: monotonicity in $R$ fails for
$\Theta > \pi$ (counterexample above).

---

## 7. Upper bound

> **Theorem 7.1.** $C^P_T(\eta) \le C_k(\eta)$.

*Proof.* Normalize (N1, N2). If $k = 1$, $R_r = P_rF_r$ and $E^P_T = 0$.
Otherwise Corollary 5.3 and the "moreover" part of Lemma 6.3, with $n = k-1$ and
$\alpha = \arcsin\eta$, give $E^P_T \le \eta\,C_k(\eta)$. $\square$

---

## 8. Universal sharp witness

> **Theorem 8.1 (UNIVERSAL_SHARP_WITNESS).** Let $T$ be any finite rooted tree
> with $k$ internal nodes, $\eta \in (0,1]$, and angles
> $\theta_v \in [0,\arcsin\eta]$ for the non-root internal nodes. The following
> realization is PMT-A-admissible with $M = 1$, $\rho = \eta$, unit leaves, and
> $$E^P_T = \Bigl\lvert 1 - \prod_{v\in V_{\rm int}\setminus\{r\}} w(\theta_v)\Bigr\rvert .$$

**Construction.**

* All spaces are $\mathbb R^2 \cong \mathbb C$, with $e_0 = 1$.
* All leaves carry $e_0$.
* For internal $v$ let $I_v$ be its internal-child slots and $L_v$ its leaf
  slots.
* **Non-root $v$:** $P_v(z) = \operatorname{Re}(z)$ (rank one) and
  $$\mu_v(x) = e^{i\theta_v}\prod_{j\in I_v}x_j\prod_{\ell\in L_v}\operatorname{Re}(x_\ell)\qquad\text{(complex product)}.$$
* **Root:** $P_r = I$ and $\mu_r(x) = \prod_{j\in I_r}x_j\prod_{\ell\in L_r}\operatorname{Re}(x_\ell)$.

**Admissibility.**

* *Norms.* $\lvert\prod x_j\rvert = \prod\lvert x_j\rvert$ and
  $\lvert\operatorname{Re}(x)\rvert \le \lvert x\rvert$, so every law has norm
  $1$.
* *Closure at non-root $v$.* Take internal slots in $\operatorname{Ran}P = \mathbb R$
  and arbitrary leaf slots. Every factor $x_j$ and $\operatorname{Re}(x_\ell)$
  is real, so the output is $e^{i\theta_v}t$ with $t$ real and
  $\lvert t\rvert \le \prod\lVert x\rVert$. Hence
  $\lVert Q_v\mu_v(x)\rVert = \lvert\sin\theta_v\rvert\lvert t\rvert \le \eta\prod\lVert x\rVert$.
* *Closure at the root.* $Q_r = 0$.

**Evaluation (induction).** For non-root $v$:
$$F_v = e^{i\Phi_v},\qquad R_v = A_v,\qquad \Phi_v = \sum_{u\in V_{\rm int}(T_v)}\theta_u,\qquad A_v = \prod_{u\in V_{\rm int}(T_v)}\cos\theta_u .$$

* *Leaf-only node:* $F_v = e^{i\theta_v}$ and $R_v = \operatorname{Re}(e^{i\theta_v}) = \cos\theta_v$.
* *Inductive step:* $F_v = e^{i\theta_v}\prod_j e^{i\Phi_{c_j}}$ and
  $R_v = \operatorname{Re}\bigl(e^{i\theta_v}\prod_jA_{c_j}\bigr) = \cos\theta_v\prod_jA_{c_j}$,
  since the $A$'s are real.
* *Root:* $F_r = e^{i\Theta}$ and $R_r = \prod_{v\ne r}\cos\theta_v$, with
  $\Theta = \sum_{v\ne r}\theta_v$ (disjoint subtrees). With $P_r = I$,
  $$E^P_T = \Bigl\lvert e^{i\Theta} - \prod\cos\theta_v\Bigr\rvert = \Bigl\lvert 1 - \prod\cos\theta_v\,e^{-i\Theta}\Bigr\rvert = \Bigl\lvert 1 - \prod w(\theta_v)\Bigr\rvert,$$
  where the last step uses $\lvert 1 - \bar z\rvert = \lvert 1 - z\rvert$. $\square$

> **Corollary 8.2 (lower bound).** $C^P_T(\eta) \ge C_k(\eta)$.

*Proof.* Take $\theta_v \equiv \theta_* \in \arg\max_{0\le\theta\le\arcsin\eta}\lvert 1 - w(\theta)^{k-1}\rvert$
in Theorem 8.1. $\square$

For $k = 1$ both sides are $0$.

*Checks* (`sharp_witness_check.py`): 4000 random trees, $k \le 10$, internal
arity $\le 4$, random leaf-slot counts, $\eta$ from $10^{-6}$ to $1$.

* $\bigl\lvert E^P_T - \lvert 1 - \prod w(\theta_v)\rvert\bigr\rvert \le 6.7\cdot10^{-16}$ for random per-node angles.
* $\lvert E^P_T/\eta - C_k(\eta)\rvert \le 3.6\cdot10^{-15}$ at $\theta_*$.
* The full-closure defect on random admissible inputs never exceeds
  $\sin\theta_v$ (excess $\le 1.2\cdot10^{-16}$).

### 8.3 The asymptotic witness (historical, not sharp)

The canonical formalization §22 used $e^{i\theta}\prod z_j$ **including leaf
slots** and read an imaginary part, giving $\lvert\sin((k-1)\theta)\rvert$.

* **Leaf-closure defect.** As written it violates leaf-slot closure: fixing all
  arguments but one leaf and rotating that leaf produces defect $1$. With leaves
  entering through $\operatorname{Re}(\cdot)$, as above, it becomes admissible.
* **Name.** We call that corrected family **ASYMPTOTIC_WITNESS**. It proves
  $\lim_{\eta\downarrow0}C^P_T(\eta) = k-1$, but for $k \ge 3$ it does not
  attain $C_k(\eta)$.
* **Exact gap.** Pointwise,
  $$\bigl\lvert 1 - w(\theta)^{n}\bigr\rvert^2 = \sin^2(n\theta) + \bigl(\cos^n\theta - \cos(n\theta)\bigr)^2 \ge \sin^2(n\theta).$$
  Numerically, the maxima differ at every tested $\eta \in [0.01, 1]$ for
  $3 \le k \le 10$ (gap up to $0.62$), and coincide for $k = 2$
  (`outputs/asymptotic_vs_sharp.json`).

---

## 9. Theorem R

*Proof.* Theorem 7.1 and Corollary 8.2. $\square$

---

## 10. Degenerate cases: where each is handled

* $\eta = 0$: outside PMT-A ($\rho > 0$); $C_k(\eta) \to k-1$ as $\eta \downarrow 0$.
* $\eta = 1$, some $\theta = \pi/2$, $\rho_i = 0$: Lemma 4.2 (case $\prod\rho_i = 0$) and Lemma 6.3 (first case).
* $R_v = 0$ or $\tilde R = 0$: Lemma 4.2, both cases.
* $P_v = 0$ or $P_v = I$: nothing divides by $\lVert P_vg\rVert$; $\theta_v = \arcsin\lVert Q_vg\rVert$.
* $\lVert F_v\rVert < 1$: allowed by O2 (Lemma 2.2 gives only $\le 1$).
* Angle labels above $\pi$: $\min(\cdot,\pi)$ in Definition 2.1, Lemma 5.2 and Corollary 5.3; Lemma 6.3, case $\Theta > \pi$.
* Collinear or $1$-dimensional factors: Theorem 3.1 reductions; Lemma 2.2.
* Arity $0$: Lemma 4.2 ($m = 0$ branch). Arbitrary arity: Theorem 3.1.
* Mixed leaf and internal children: N2 for the upper bound; $\operatorname{Re}$-gates for the witness.
* $k = 1$: Theorem 7.1, Corollary 8.2.

Numerical edge runs, each at the proof angle:

* `../theorem_R_v1/edge_cases.py`: 6000 cases.
* `edge_cases_v2.py`: 8000 cases, adding $\eta \in \{10^{-3},10^{-6}\}$ and explicit $\lVert F\rVert < 1$.

Both give maximum violation $\le 6.7\cdot10^{-16}$ and $0$ violations.

## 11. Scope

* **Complex spaces.** The upper bound plausibly transfers by realification, but
  this is not claimed here. The lower bound over $\mathbb C$ fails for this
  witness (complex-bilinear norm $\sqrt2$) and is open.
* **DAGs.** Proposition 5.1 fails as stated (shared nodes are counted once per
  slot); separate class and theorem needed.
* **Excluded.** Shared laws, fixed ranks and oblique projectors are outside PMT-A.

## 12. Formalization targets

Only the PMT-free, finite pieces are proposed for a proof assistant:

* the Diagonal Lemma (Lemmas 6.1–6.3);
* the witness evaluation of Theorem 8.1.

O2, Theorem 3.1 and Lemma 4.2 should be reviewed on paper first.

Suggested Lean 4 / Mathlib statements, **unchecked** because no Lean toolchain
was available on the authoring machine:

* `cos_prod_ge_cos_sum`: $\theta_j \ge 0$, $\sum\theta_j \le \pi/2$ ⟹ $\cos\sum\theta_j \le \prod\cos\theta_j$.
* `concaveOn_log_cos`: concavity of $\log\circ\cos$ on $[0,\pi/2)$.
* `prod_cos_le_cos_avg`: $\prod\cos\theta_j \le \cos^n(\Theta/n)$ on $[0,\pi/2)^n$.
* `diagonal_lemma`: `IsGreatest` of $\{\lvert 1 - \prod w(\theta_j)\rvert : \theta \in [0,\alpha]^n\}$ at the diagonal maximum.

Reduce $\prod w(\theta_j)$ to the real pair $(R,\Theta)$ before handling
`Complex.exp`.

## 13. Questions for the reviewer (functional analysis / operator theory)

1. Is Theorem 3.1 correct, and is it known (projective tensor norms, contractive
   dilations, scaled relative graphs)?
2. Is the O2 preservation (Lemma 2.3 plus Lemma 4.2) correct at arbitrary arity,
   in particular the step from the raw pair $(f,g)$ to a dilated chain pair with
   angle $\tilde\psi + \theta_v$?
3. Does any step use closure beyond the trajectory form (TC)?
