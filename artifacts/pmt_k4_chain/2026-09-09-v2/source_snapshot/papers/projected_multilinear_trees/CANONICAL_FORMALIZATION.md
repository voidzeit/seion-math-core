# Projected Multilinear Trees: Sharp Error Constants Under Approximate Closure

**Canonical mathematical formalization.** Frozen 2026-08-11.

Status: candidate for external review. Novelty not established; no independent
human review. See `research/math_closure/FROZEN_CORE_V5_2026-08-11.md`.

---

## 0. Scope

This work studies hierarchical evaluations obtained by composing multilinear
maps and projecting orthogonally after each internal operation. The central
problem is extremal: given a uniform budget on operator norm and on closure
defect, what is the largest error that can survive in the projected output of a
multilinear tree?

The theory is finite-dimensional, deterministic and purely operator-theoretic.
It presupposes no geometric, probabilistic or physical interpretation.

The closure hypothesis used throughout is **closure over already-projected
inputs**, not the unrestricted ambient closure defect.

---

## 1. Typed multilinear trees

**Definition 1.1 (Typed tree).** Let $T$ be a finite ordered rooted tree, with
internal vertices $V_{\mathrm{int}}(T)$, leaves $L(T)$, and
$k(T) := |V_{\mathrm{int}}(T)|$. Each vertex $w$ carries a finite-dimensional
Hilbert space $H_w$ over $\mathbb{K} \in \{\mathbb{R},\mathbb{C}\}$. Each
internal $v$ has ordered children $c_1(v),\dots,c_{m_v}(v)$ with $m_v \ge 2$.

**Definition 1.2 (Local multilinear law).**
$$\mu_v : H_{c_1(v)} \times \cdots \times H_{c_{m_v}(v)} \to H_v, \qquad
\|\mu_v\|_{\mathrm{op}} := \sup_{\|x_i\|\le 1} \|\mu_v(x_1,\dots,x_{m_v})\|.$$

**Definition 1.3 (Reduction data).** Each internal $v$ carries an orthogonal
projector $P_v : H_v \to H_v$ with $P_v^2 = P_v$, $P_v^* = P_v$. Hence
$\|P_v\|_{\mathrm{op}} \le 1$ and $H_v = \operatorname{Ran}(P_v) \oplus \ker(P_v)$
orthogonally.

**Definition 1.4 (Extended projector).**
$$\widehat P_w := \begin{cases} P_w, & w \in V_{\mathrm{int}}(T),\\ I_{H_w}, & w \in L(T).\end{cases}$$
Leaves are not reduced. This removes any ambiguity when a child of an internal
vertex is a leaf.

---

## 2. Ambient and projected evaluation

**Definition 2.1.** Each leaf $\ell$ carries a datum $z_\ell \in H_\ell$.

**Definition 2.2 (Ambient).** $F_\ell := z_\ell$; for internal $v$,
$F_v := \mu_v(F_{c_1(v)},\dots,F_{c_{m_v}(v)})$. No projection occurs.

**Definition 2.3 (Recursively projected).** $R_\ell := z_\ell$; for internal $v$,
$R_v := P_v\,\mu_v(R_{c_1(v)},\dots,R_{c_{m_v}(v)})$. In particular
$R_v \in \operatorname{Ran}(P_v)$.

---

## 3. Errors

Let $r$ be the root.

**Definition 3.1 (Ambient error).** $E_T^{\mathrm{amb}} := \|F_r - R_r\|$.

**Definition 3.2 (Projected error).**
$$\boxed{\,E_T^{P} := \|P_r F_r - R_r\|\,}$$
This is the fundamental extremal quantity of this work.

**Definition 3.3 (Normal error).** $E_T^{N} := \|(I-P_r)F_r\|$.

Since $P_rF_r - R_r \in \operatorname{Ran}(P_r)$ and
$(I-P_r)F_r \in \ker(P_r)$, the two are orthogonal, whence
$$\boxed{\,(E_T^{\mathrm{amb}})^2 = (E_T^{P})^2 + (E_T^{N})^2\,.}$$

---

## 4. Closure defects

**Definition 4.1 (Projected-input closure defect).**
$$\boxed{\;\rho_v^{\mathrm{proj}} := \Bigl\|(I-P_v)\,\mu_v\bigl(\widehat P_{c_1(v)}\,\cdot\,,\dots,\widehat P_{c_{m_v}(v)}\,\cdot\,\bigr)\Bigr\|_{\mathrm{op}}\;}$$
equivalently the supremum of $\|(I-P_v)\mu_v(x_1,\dots,x_{m_v})\|$ over unit
vectors with $x_i \in \operatorname{Ran}\widehat P_{c_i(v)}$.

**Definition 4.2 (Ambient defect).** $\rho_v^{\mathrm{amb}} := \|(I-P_v)\mu_v\|_{\mathrm{op}}$.

**Lemma 4.3.** $\rho_v^{\mathrm{proj}} \le \rho_v^{\mathrm{amb}}$.

*Proof.* The supremum defining $\rho_v^{\mathrm{proj}}$ ranges over a subset of
the inputs admissible for $\rho_v^{\mathrm{amb}}$. $\square$

The inequality can be strict by arbitrarily large factors in parametrized
families.

---

## 5. Admissible class

**Definition 5.1.** For $M > 0$, $0 < \rho \le M$, a realization is
$(M,\rho)$-**admissible** if $\|\mu_v\|_{\mathrm{op}} \le M$ and
$\rho_v^{\mathrm{proj}} \le \rho$ for every internal $v$. Set
$\eta := \rho/M \in (0,1]$ and $L_T := \prod_{\ell \in L(T)}\|z_\ell\|$.

**All closure theorems below use $\rho^{\mathrm{proj}}$, not $\rho^{\mathrm{amb}}$.**

---

## 6. Extremal constant

**Definition 6.1.** For a class $\mathfrak{C}_T$ of admissible realizations,
$$\boxed{\;C^{P}_{T,\mathfrak{C}_T}(\eta) := \sup \frac{E_T^{P}}{\rho\,M^{k(T)-1}L_T}\;}$$
over non-degenerate realizations with $\rho/M = \eta$. For the general
finite-dimensional class with independently selectable laws we write
$C_T^{P,\mathrm{fin}}(\eta)$.

This global constant must be distinguished from one obtained after fixing
dimensions and ranks in advance.

---

## 7. Homogeneity and normalization

**Lemma 7.1 (Scaling).** Let $\lambda > 0$ and $\nu_\ell > 0$ per leaf. Under
$\mu_v \mapsto \lambda\mu_v$ and $z_\ell \mapsto \nu_\ell z_\ell$:
$$M \mapsto \lambda M,\quad \rho \mapsto \lambda\rho,\quad L_T \mapsto \Bigl(\prod_\ell \nu_\ell\Bigr)L_T,\quad E_T^{P} \mapsto \lambda^{k(T)}\Bigl(\prod_\ell \nu_\ell\Bigr)E_T^{P},$$
so $E_T^P/(\rho M^{k-1}L_T)$ is invariant.

*Proof.* Each internal vertex contributes exactly one multilinear map, hence one
factor $\lambda$; each leaf appears multilinearly exactly once, contributing
$\nu_\ell$. The denominator acquires $\lambda\cdot\lambda^{k-1}\prod_\ell\nu_\ell
= \lambda^{k}\prod_\ell\nu_\ell$. $\square$

**Convention 7.2.** With all leaves nonzero we may take
$$\boxed{\,M = 1,\quad \rho = \eta,\quad \|z_\ell\| = 1,\quad L_T = 1\,.}$$
A zero leaf makes the evaluation vanish by multilinearity and does not affect the
non-degenerate supremum.

---

## 8. Subtree stability

For a vertex $v$ let $T_v$ be its subtree, $k_v := |V_{\mathrm{int}}(T_v)|$,
$L_v := \prod_{\ell \in L(T_v)}\|z_\ell\|$.

**Lemma 8.1.** $\|F_v\| \le M^{k_v}L_v$ and $\|R_v\| \le M^{k_v}L_v$.

*Proof.* Induction on $k_v$. Immediate at a leaf. For internal $v$,
$\|F_v\| \le M\prod_i\|F_{c_i}\| \le M^{1+\sum_i k_{c_i}}L_v = M^{k_v}L_v$. For
$R_v$ use additionally $\|P_v\| \le 1$. $\square$

---

## 9. Universal bound

**Theorem 9.1 (Subtree ambient discrepancy).**
$$\boxed{\;\|F_v - R_v\| \le k_v\,\rho\,M^{k_v-1}L_v\;}$$

*Proof.* Write $F_i := F_{c_i}$, $R_i := R_{c_i}$, $m := m_v$. Adding and
subtracting $\mu_v(R_1,\dots,R_m)$,
$$F_v - R_v = \bigl[\mu_v(F_1,\dots,F_m) - \mu_v(R_1,\dots,R_m)\bigr] + (I-P_v)\mu_v(R_1,\dots,R_m).$$
The second term has all inputs in $\operatorname{Ran}\widehat P_{c_i}$, so by
Definition 4.1 and Lemma 8.1 it is at most
$\rho\prod_i\|R_i\| \le \rho M^{\sum_i k_{c_i}}L_v = \rho M^{k_v-1}L_v$.

The first term telescopes over arguments into $m$ terms, each containing exactly
one factor $F_i - R_i$. By the inductive hypothesis and Lemma 8.1 the $i$-th
contributes at most $k_{c_i}\rho M^{k_v-1}L_v$. Summing,
$$\|F_v - R_v\| \le \Bigl(1 + \sum_i k_{c_i}\Bigr)\rho M^{k_v-1}L_v = k_v\,\rho M^{k_v-1}L_v,$$
since $k_v = 1 + \sum_i k_{c_i}$. $\square$

**Theorem 9.2 (Universal projected error bound).** For $k \ge 1$,
$$\boxed{\;E_T^{P} \le (k-1)\,\rho\,M^{k-1}L_T\;}\qquad\text{equivalently}\qquad \boxed{\;C_T^{P}(\eta) \le k-1\;}$$

*Proof.* At the root, $R_r = P_r\mu_r(R_1,\dots,R_m)$, so
$$P_rF_r - R_r = P_r\bigl[\mu_r(F_1,\dots,F_m) - \mu_r(R_1,\dots,R_m)\bigr];$$
the local defect $(I-P_r)\mu_r(R_1,\dots,R_m)$ vanishes precisely because
$P_r(I-P_r) = 0$. Telescoping the arguments and applying Theorem 9.1 to each
child gives $E_T^P \le (\sum_i k_{c_i})\rho M^{k-1}L_T = (k-1)\rho M^{k-1}L_T$. $\square$

---

## 10. The case $k = 1$

**Corollary 10.1.** $\boxed{C_1^{P}(\eta) = 0}$, since $R_r = P_rF_r$.

---

## 11. The case $k = 2$

Chain $(a,b) \xrightarrow{\mu_1} H_1$, $(H_1,d) \xrightarrow{\mu_2} H_2$. Put
$D := (I-P_1)\mu_1(a,b)$, $R_1 := P_1\mu_1(a,b)$.

**Lemma 11.1 (Exact identity).** $\boxed{E_T^{P} = \|P_2\mu_2(D,d)\|}$

*Proof.* From $F_1 = R_1 + D$, $F_2 = \mu_2(R_1,d) + \mu_2(D,d)$, while
$R_2 = P_2\mu_2(R_1,d)$. Hence
$$F_2 - R_2 = \mu_2(D,d) + (I-P_2)\mu_2(R_1,d).$$
Applying $P_2$ kills the second term; $P_2R_2 = R_2$ gives the claim. $\square$

Note that in general $F_2 - R_2 \ne \mu_2(D,d)$.

**Theorem 11.2 (Saturation characterization).** $E_T^{P} = \rho M\|a\|\|b\|\|d\|$
**iff** simultaneously

$$\boxed{\|\mu_2(D,d)\| = M\|D\|\|d\|}\;\text{(EQ1)},\quad \boxed{\|D\| = \rho\|a\|\|b\|}\;\text{(EQ2)},\quad \boxed{\mu_2(D,d) \in \operatorname{Ran}(P_2)}\;\text{(EQ3)}.$$

*Proof.* Lemma 11.1 gives
$E_T^P \le \|\mu_2(D,d)\| \le M\|D\|\|d\| \le M\rho\|a\|\|b\|\|d\|$. Equality of
the extremes forces equality at every step; these are EQ3, EQ1, EQ2. The
converse is immediate. $\square$

**Corollary 11.3.** $\boxed{C_2^{P}(\eta) = 1}$ for all $\eta \in (0,1]$.

---

## 12. Three vertices: basic geometry

**Lemma 12.1 (Pythagorean coupling).** $D_1 \perp R_1$, hence
$$\boxed{\|D_1\|^2 + \|R_1\|^2 = \|\mu_1(a,b)\|^2.}$$
With $M = 1$ and unit leaves, if $q := \|D_1\|$ then $q \le \eta$ and
$\|R_1\| \le \sqrt{1-q^2}$.

This is the first mechanism preventing simultaneous saturation of all local
error sources.

---

## 13. Preliminary envelope $U_3$

The triangle-inequality analysis yields $C_3^{P}(\eta) \le U_3(\eta)$ with
$$U_3(\eta) = \begin{cases}1+\sqrt{1-\eta^2}, & 0<\eta\le\eta_\star,\\[2mm] \dfrac{\sqrt{1+\eta^2}}{\eta}, & \eta_\star<\eta\le1,\end{cases}\qquad \boxed{\eta_\star = \sqrt{\tfrac{\sqrt5-1}{2}}}$$
and $U_3(\eta_\star) = \varphi = \tfrac{1+\sqrt5}{2}$.

This transition belongs to the preliminary envelope, **not** to the exact
extremal constant.

---

## 14. Gram lemma

**Lemma 14.1 (Projector-contraction Gram lemma).** Let $N : H \to K$ be linear
with $\|N\|_{\mathrm{op}} \le M$, let $u,v \in H$ be orthonormal, let $Q$ be an
orthogonal projector on $K$, and put $y := Nv$, $s := \|Qy\|$. Then
$$\boxed{\;|\langle Nu, Qy\rangle| \le M s \sqrt{1 - s^2/M^2}\;}$$

*Proof.* Put $\widetilde N := N/M$ and $K_0 := \widetilde N^* Q \widetilde N$, so
$0 \preceq K_0 \preceq I$. On $\operatorname{span}\{u,v\}$ write
$(K_0)_{vv} = \sigma^2$ with $\sigma := s/M$, $(K_0)_{uu} = \alpha$,
$(K_0)_{uv} = c$. Positivity of $K_0$ gives $|c|^2 \le \alpha\sigma^2$;
positivity of $I - K_0$ gives $|c|^2 \le (1-\alpha)(1-\sigma^2)$. The maximum of
the minimum occurs where the two agree, i.e. $\alpha = 1-\sigma^2$, giving
$|c| \le \sigma\sqrt{1-\sigma^2}$. Since $\langle Nu,QNv\rangle = M^2c$, the
claim follows. $\square$

No saturation of $\|N\|$ is assumed.

---

## 15. Exact constant for the $k=3$ chain

Take $M = L_T = 1$, $\rho = \eta$, $q = \|D_1\|$, $p = \|R_1\| \le \sqrt{1-q^2}$.
For $q,p > 0$ set $u_0 := D_1/q$, $v_0 := R_1/p$ (orthonormal). Freezing the
second node's sibling leaf gives a linear contraction $N$; put $Q := I - P_2$,
$x := Nu_0$, $y := Nv_0$, $s := \|Qy\| \le \eta$. The error reaching the third
node is $qx + pQy$, so by Lemma 14.1
$$\|qx+pQy\|^2 \le q^2 + p^2s^2 + 2qps\sqrt{1-s^2}.$$
The right side increases in $p$, so take $p = \sqrt{1-q^2}$. With
$q = \sin\alpha$, $s = \sin\beta$, $\xi := \tan\alpha$, $\zeta := \tan\beta$,
$$f(\xi,\zeta) = \frac{(\xi+\zeta)^2 + \xi^2\zeta^2}{(1+\xi^2)(1+\zeta^2)}.$$

**Fundamental extremal identity.**
$$\boxed{\;4(1+\xi^2)(1+\zeta^2) - 3\bigl[(\xi+\zeta)^2 + \xi^2\zeta^2\bigr] = (\xi\zeta-2)^2 + (\xi-\zeta)^2\;}$$

Hence $\boxed{f \le 4/3}$, with equality **iff** $\boxed{\xi = \zeta = \sqrt2}$,
i.e. $q = s = \sqrt{2/3}$.

**Theorem 15.1 (Sharp chain bound).**
$$\boxed{\;C_{3,\mathrm{chain}}^{P}(\eta) \le W_3(\eta) := \begin{cases}\sqrt{4-3\eta^2}, & 0<\eta\le\sqrt{2/3},\\[2mm] \dfrac{2}{\sqrt3\,\eta}, & \sqrt{2/3}\le\eta\le1.\end{cases}\;}$$

*Proof.* If $\eta \le \sqrt{2/3}$ then $\xi,\zeta \le \sqrt2$, where $f$ is
non-decreasing in each variable with stationary equality only at the extreme
corner; hence $q = s = \eta$ and $(E_T^{P})^2 \le \eta^2(4-3\eta^2)$. If
$\eta \ge \sqrt{2/3}$ the global equality point $q = s = \sqrt{2/3}$ is already
admissible, so $(E_T^{P})^2 \le 4/3$. $\square$

"Unconditional" applies here only in the sense that no additional saturation or
scalar-reduction hypothesis is assumed; the structural hypotheses of the
admissible class remain in force.

---

## 16. Explicit extremizer

**Theorem 16.1 (Attainment).** The bound is sharp for every $\eta \in (0,1]$; a
two-dimensional real realization suffices.

*Construction.* $H = \mathbb{R}^2$ with orthonormal $e_0,e_1$; $P = e_0e_0^*$;
$$t := \min\{\eta,\sqrt{2/3}\},\qquad p = c := \sqrt{1-t^2}.$$
All leaves are $e_0$. Set
$$\mu_1(x,y) = \langle x,e_0\rangle\langle y,e_0\rangle\,(te_1 + pe_0),$$
let $N_t$ be orthogonal with $N_te_0 = te_1 - ce_0$, $N_te_1 = ce_1 + te_0$, and
$\mu_2(x,y) = \langle y,e_0\rangle N_t x$. Then $D_1 = te_1$, $R_1 = pe_0$, and
the error after the second level is
$$v := tN_te_1 + pt\,e_1 = t^2e_0 + 2tp\,e_1, \qquad \|v\|^2 = t^4 + 4t^2p^2 = t^2(4-3t^2).$$
With $Ah := \langle v,h\rangle\|v\|^{-1}e_0$ and
$\mu_3(x,y) = \langle y,e_0\rangle Ax$, all three operator norms equal $1$, the
two active closure defects equal $t$, and the root defect is zero, so
$\rho_v^{\mathrm{proj}} \le \eta$ everywhere. Therefore
$$\boxed{E_T^{P} = t\sqrt{4-3t^2}},$$
giving $\sqrt{4-3\eta^2}$ for $\eta \le \sqrt{2/3}$ and
$E_T^P = 2/\sqrt3$, hence $2/(\sqrt3\eta)$, above. $\square$

---

## 17. Two extremal regimes

Define the absolute extremal error $G_3(\eta) := \eta\,W_3(\eta)$. Then
$$\boxed{\;G_3(\eta) = \begin{cases}\eta\sqrt{4-3\eta^2}, & 0<\eta\le\eta_c,\\[2mm] \dfrac{2}{\sqrt3}, & \eta_c\le\eta\le1,\end{cases}\qquad \eta_c := \sqrt{2/3}.\;}$$

**Proposition 17.1 (Budget-limited).** For $\eta \le \eta_c$ the extremizer uses
the whole budget, $t_{\mathrm{opt}} = \eta$, and the absolute error grows with $\eta$.

**Proposition 17.2 (Geometry-limited).** For $\eta \ge \eta_c$ the optimizer
freezes at $t_{\mathrm{opt}} = \sqrt{2/3}$ and $G_3(\eta) = 2/\sqrt3$. The
admissible set keeps growing but the worst absolute projected error does not.
The decay $W_3(\eta) = (2/\sqrt3)/\eta$ therefore reflects division by a growing
closure budget after the absolute error has already saturated.

---

## 18. Two distinct critical points

$$\boxed{\eta_\star = \sqrt{\tfrac{\sqrt5-1}{2}} \approx 0.786151},\qquad \boxed{\eta_c = \sqrt{\tfrac23} \approx 0.816497},$$
with $U_3(\eta_\star) = \varphi$ and $W_3(\eta_c) = \sqrt2$. Hence
$\boxed{\eta_\star \ne \eta_c}$: the first belongs to an intermediate
triangle-inequality bound, the second to the true extremal problem.

---

## 19. Branching topology

Two independent internal vertices feed the root. With $q_i := \|D_i\|$,
$p_i := \|R_i\| \le \sqrt{1-q_i^2}$, and the root law reduced to a contractive
bilinear map after freezing extra leaves, the relevant difference is represented
by
$$A = \begin{pmatrix} q_1q_2 & q_1p_2\\ p_1q_2 & 0\end{pmatrix}.$$
Operator-norm/nuclear-norm duality makes the maximum over contractive bilinear
forms equal $\|A\|_*$, and for $2\times2$ matrices
$\|A\|_*^2 = \|A\|_F^2 + 2|\det A|$. Saturating $p_i = \sqrt{1-q_i^2}$,
$$\|A\|_*^2 = q_1^2 + q_2^2 - q_1^2q_2^2 + 2q_1q_2\sqrt{1-q_1^2}\sqrt{1-q_2^2},$$
which in the tangent variables is again exactly $f(\xi,\zeta)$. The same SOS
identity of §15 applies.

**Theorem 19.1 (Branching sharpness).** $\boxed{C_{3,\mathrm{branch}}^{P}(\eta) = W_3(\eta)}$,
with the same transition $\eta_c = \sqrt{2/3}$.

*Numerically verified:* over 20,000 random $(q_1,q_2)$, both
$\bigl|\|A\|_* - \sqrt{\|A\|_F^2+2|\det A|}\bigr|$ and
$\bigl|\|A\|_*^2 - f\bigr|$ stay below $2.9\times10^{-15}$.

---

## 20. Universality at three internal vertices

After deleting leaves, an ordered tree with exactly three internal vertices has
only two skeletons: a three-vertex chain, or two sibling internal vertices
feeding the root. Extra arity corresponds only to leaf-occupied slots; fixing
unit inputs there reduces each law to an effective linear or bilinear map and
increases neither $\|\mu_v\|_{\mathrm{op}}$ nor $\rho_v^{\mathrm{proj}}$.

**Theorem 20.1 (Universal three-vertex bound).** For every finite ordered rooted
$T$ with exactly three internal vertices and arities $m_v \ge 2$, and every
admissible finite-dimensional realization,
$$\boxed{C_T^{P}(\eta) \le W_3(\eta),}$$
independently of arities, chain/branching skeleton, ambient dimensions and
projector ranks.

**Theorem 20.2 (Sharpness over the unrestricted finite-dimensional class).**
$$\boxed{C_T^{P,\mathrm{fin}}(\eta) = W_3(\eta).}$$

**Quantifier remark.** This does **not** mean equality holds for every fixed
dimension and rank. If $P_v = I$ at all vertices then $E_T^{P} = 0$. The correct
statement: $W_3$ is the best uniform dimension- and rank-independent constant for
the full finite-dimensional class, already attained by two-dimensional
realizations with rank-one projectors.

---

## 21. Small-leakage expansion

For $0 < \eta < \sqrt{2/3}$, $C_3^{P}(\eta) = \sqrt{4-3\eta^2}$, so
$$\boxed{\;C_3^{P}(\eta) = 2 - \tfrac34\eta^2 - \tfrac{9}{64}\eta^4 + O(\eta^6)\;}$$
and $2 - C_3^{P}(\eta) = \tfrac34\eta^2 + O(\eta^4)$: the first sharpening
against the universal constant is of second order.

---

## 22. Trees with $k \ge 4$: asymptotic sharpness

**Theorem 22.1.** For every finite ordered tree $T$ with $k$ internal vertices,
$$\boxed{\lim_{\eta\downarrow0} C_T^{P,\mathrm{fin}}(\eta) = k-1.}$$

*Proof.* The upper bound follows from Theorem 9.2. For the lower bound identify
$\mathbb{R}^2 \simeq \mathbb{C}$; at each non-root internal vertex take
$Pz = \operatorname{Re}(z)$ and $\mu_v(z_1,\dots,z_m) = e^{i\theta}\prod_j z_j$,
with all leaves $1$. On projected inputs every argument is real and the removed
component has norm $|\sin\theta|$; choose $\eta = \sin\theta$. In the ambient
evaluation each of the $k-1$ non-root vertices contributes a phase $e^{i\theta}$,
so the product reaching the root has total phase $e^{i(k-1)\theta}$. Define at
the root a contractive multilinear map extracting the imaginary part of that
product into a projected direction; on projected inputs this output is zero.
Hence $E_T^{P} = |\sin((k-1)\theta)|$ and
$$C_T^{P}(\eta) \ge \frac{|\sin((k-1)\arcsin\eta)|}{\eta} \longrightarrow k-1. \qquad\square$$

---

## 23. Extremal programme for $k \ge 4$

Sharpness at $\eta > 0$ is open. A natural formulation asks whether
$$\boxed{C_T^{P}(\eta) = (k-1) - a_T\eta^2 + o(\eta^2)}$$
for every fixed tree: is $\alpha_T = 2$ always; does
$a_T = \lim_{\eta\downarrow0}\bigl[(k-1)-C_T^{P}(\eta)\bigr]/\eta^2$ exist; and if
so, is it a combinatorial invariant of $T$? For $k = 3$, $a_T = 3/4$ for both
chain and branching.

---

## 24. DAGs: positive recurrence

Let $G$ be a finite DAG with root $r$, nonnegative local sources $s_v$ and
nonnegative edge gains $g_e$, with $d_v = s_v + \sum_{e:u\to v} g_e d_u$.

**Theorem 24.1 (Exact path expansion).**
$$\boxed{\;d_r = \sum_v s_v \sum_{\pi : v \rightsquigarrow r} \prod_{e\in\pi} g_e\;}$$

*Proof.* Acyclicity gives a topological order; recursive substitution makes each
$s_v$ appear once per directed path $v \rightsquigarrow r$, weighted by that
path's gain product. $\square$

If $0 \le s_v \le b_v$ the maximum is at $s_v = b_v$.

**Definition 24.2.** $K(G)$ is the sum of directed slot-path multiplicities from
each projected node to the root.

---

## 25. Multilinear DAGs

$$\boxed{K(G) \ne C_G^{P}(\eta)\ \text{in general for }\eta>0,}\qquad\text{but}\qquad \boxed{\lim_{\eta\downarrow0} C_G^{P}(\eta) = K(G).}$$

$K(G)$ is the exact constant of the positive recurrence and the
tangent/asymptotic constant of the multilinear geometry. Determining
$C_G^{P}(\eta)$ for $\eta > 0$ is open.

---

## 26. Dimensional obstruction

**Proposition 26.1.** For every $n \ge 1$ there is a binary chain with $n$
independent laws in $\mathbb{R}^{n+2}$, a **proper** orthogonal projector and
**zero** evaluated closure defect, whose leaf and internal-node values span
dimension $n+1$.

*Proof.* Let $P$ be the identity on $\operatorname{span}\{e_0,\dots,e_n\}$ and
zero on $e_{n+1}$; all leaves are $e_0$; for $j = 0,\dots,n-1$ set
$\mu_j(x,y) = e_{j+1}\langle e_j,x\rangle\langle e_0,y\rangle$, of operator norm
one. Induction gives value $e_{j+1}$ at node $j$; all values lie in
$\operatorname{Ran}(P)$ so the evaluated defect vanishes, yet
$e_0,\dots,e_n$ are orthonormal. The projector remains proper since
$e_{n+1} \notin \operatorname{Ran}(P)$. $\square$

**Corollary 26.2.** No depth-independent dimension bound preserves all nodewise
values of the independent-law class. This excludes neither root-only reduction,
nor modifying intermediate laws, nor same-law classes, nor fixed typed trees,
nor approximate compression that does not preserve all internal values.

---

## 27. Essential dependence on orthogonality

The $k=3$ sharpenings use $D_1 \perp R_1$, hence
$\|D_1\|^2 + \|R_1\|^2 = \|F_1\|^2$, essentially. For a merely idempotent
projector ($P^2 = P$, $P^* \ne P$) this identity can fail, so the exact theory
does not extend automatically to oblique projections.

---

## 28. Same-law classes

The independent-law class is the basic extremal class. At $k=2$, weight sharing
does not prevent attaining $1$: one map can saturate its norm on distinct input
pairs. At $k=3$, a direct-sum construction with orthogonal tags simulates
distinct nodewise laws by a single tagged law and recovers $W_3$ in a
sufficiently rich same-law class. This depends on the concrete tagging structure
and must be kept separate from the free-law theorem.

---

## 29. Rank-one same-law reduction

In the much stricter class — binary chain, rank-one projection, common leaves,
one repeated law — the problem reduces to a unary contraction problem with
extremal quantity
$$\bigl|\langle e_0, A^3 e_0\rangle - \langle e_0, Ae_0\rangle^3\bigr|$$
subject to $\|A\| \le 1$ and $\|QAe_0\| \le \eta$. The regime
$\eta \ge \sqrt{2/3}$ is closed; small leakage remains open.

---

## 30. Summary of constants

$$\boxed{\begin{aligned} k=1:\quad & C_1^{P}(\eta) = 0,\\ k=2:\quad & C_2^{P}(\eta) = 1,\\ k=3:\quad & C_3^{P,\mathrm{fin}}(\eta) = W_3(\eta),\\ k\ge4:\quad & C_T^{P}(\eta) \le k-1,\qquad C_T^{P,\mathrm{fin}}(\eta) \to k-1\ \ (\eta\downarrow0).\end{aligned}}$$

---

## 31. Open problems

**OP1** Sharp constants for $k \ge 4$ at $\eta > 0$.
**OP2** Second-order asymptotics $C_T^{P}(\eta) = (k-1) - a_T\eta^2 + o(\eta^2)$.
**OP3** Combinatorial interpretation of $a_T$.
**OP4** Finite-$\eta$ DAG constants $C_G^{P}(\eta)$.
**OP5** Small-$\eta$ rank-one same-law regime.
**OP6** Oblique projectors ($P^2 = P$, $P^* \ne P$).
**OP7** Infinite-dimensional limits.
**OP8** Continuum limits of growing tree/DAG families.

---

## 32. Epistemic scope

Three kinds of statement are distinguished. **Universal theorems**: proved for
the whole declared class. **Sharpness statements**: require both an upper bound
and an attaining construction. **Computational evidence**: verifies identities,
witnesses or implementations and never substitutes for proof. In particular the
machine-precision agreement of the $k=3$ witness with $W_3$ is an implementation
control; the mathematical equality follows from the analytic construction.

---

## 33. Principal conceptual result

The bound $(k-1)\rho M^{k-1}L_T$ is universal and asymptotically sharp as
$\eta \downarrow 0$. Yet at three internal vertices, orthogonality imposes a
geometric constraint making independent saturation of the local sources
impossible. The exact result is $W_3(\eta) < 2$ for every $\eta > 0$, while
$W_3(\eta) \to 2$ as $\eta \downarrow 0$. Therefore:

$$\boxed{\text{naive accumulation of local errors is correct to first order, but does not describe the extremal geometry at finite leakage.}}$$

The general Projected Multilinear Trees problem is to determine that extremal
geometry for arbitrary trees and DAGs.
