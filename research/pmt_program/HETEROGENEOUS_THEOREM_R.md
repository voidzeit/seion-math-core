# Heterogeneous Theorem R — research specification

## Status

This document freezes the mathematical target and the implementation boundary.
The heterogeneous upper bound, its sharpness statement, and the capped-equal-
angle reduction are research hypotheses until independently proved. Numerical
optimization is evidence and a source of counterexamples, not a proof.

## 1. Admissible nodewise data

Let (T) be a finite projected multilinear tree. For every internal node (v),
assume

\[
\lVert\mu_v\rVert_{\rm op}\le M_v,
\qquad
\lVert Q_v\mu_v(x_1,\ldots,x_m)\rVert
\le \rho_v\prod_i\lVert x_i\rVert.
\]

For each active non-root node define

\[
\eta_v=\rho_v/M_v,
\qquad
\alpha_v=\arcsin(\eta_v).
\]

The natural scale is

\[
\Lambda_T=
\left(\prod_{v\in V_{\rm int}(T)}M_v\right)
\left(\prod_{\ell\in L(T)}\lVert z_\ell\rVert\right).
\]

## 2. Scalar target

Put

\[
w(\theta)=\cos\theta\,e^{i\theta}.
\]

For (n=|V^\circ|), define

\[
G_{\rm box}(\boldsymbol\eta)=
\max_{0\le\theta_v\le\alpha_v}
\left|1-\prod_{v\in V^\circ}w(\theta_v)\right|.
\]

The proposed heterogeneous upper bound is

\[
E_T^P\le \Lambda_TG_{\rm box}(\boldsymbol\eta).
\tag{H1}
\]

The corresponding sharpness claim is

\[
\sup_{\rm admissible\ PMTs}
\frac{E_T^P}{\Lambda_T}
=G_{\rm box}(\boldsymbol\eta).
\tag{H4}
\]

The implementation does not silently treat H1 or H4 as established.

## 3. Conservative fallback

Let

\[
\widehat M=\max_v M_v,
\qquad
\widehat\rho=\max_v\rho_v,
\qquad
\widehat\eta=\widehat\rho/\widehat M.
\]

Applying the uniform theorem gives the safe fallback

\[
E_T^P\le
\widehat M^{|V_{\rm int}(T)|}
\left(\prod_\ell\lVert z_\ell\rVert\right)
G_n(\widehat\eta),
\tag{U}
\]

where (G_n) is the uniform scalar expression with (n) active factors.
This is the bound used by the discrete allocator to decide feasibility.

## 4. Capped-equal-angle hypothesis

The optimization candidate is

\[
\theta_v(\tau)=\min(\alpha_v,\tau).
\]

After sorting (alpha_1\le\cdots\le\alpha_n), the candidate can be
evaluated interval by interval. On

\[
\alpha_j\le\tau\le\alpha_{j+1}
\]

the scalar product is

\[
Z_j(\tau)=
\left(\prod_{i\le j}w(\alpha_i)\right)w(\tau)^{n-j}.
\]

An interior stationary point satisfies, when the denominator is nonzero,

\[
\tan\theta_i=
\frac{\sin\Phi}{R-\cos\Phi},
\qquad
R=\prod_i\cos\theta_i,
\quad \Phi=\sum_i\theta_i.
\]

This supports the hypothesis that all unsaturated coordinates agree. It does
not by itself exclude global maxima on boundary faces or exceptional phase
regimes. The code therefore reports this curve as a candidate only.

## 5. Required proof checkpoints

1. Establish H1 from the spherical-lift and nodewise propagation argument.
2. Prove that the reduction is valid for arbitrary tree placement.
3. Prove H4 by an admissible planar construction for every defect vector.
4. Prove or refute the capped-equal-angle reduction.
5. If true, derive a certified one-dimensional evaluator.
6. Formalize the accepted statements in Lean without introducing a project-
   specific axiom.

## 6. Computational interpretation

For rank choices (r_v), the data become (M_v(r_v)) and

\[
\eta_v(r_v)=\rho_v(r_v)/M_v(r_v).
\]

The intended planner solves

\[
\min_{T,\{r_v\}}\operatorname{Cost}(T,\{r_v\})
\quad\text{subject to}\quad
E_T^P\le\varepsilon.
\]

Until H1 is proved, the production-safe constraint is (U), while the
heterogeneous box value is used for diagnostics, gap estimates, and
counterexample searches.
