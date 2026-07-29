# Explicit approximate-closure bound

## Hypotheses

Let \(V\) be a finite-dimensional Hilbert space, \(Q:W\to V\) an isometry,
\(P=QQ^*\), and \(\mu:V^n\to V\) an \(n\)-linear law. Let

\[
M=\lVert\mu\rVert_{\mathrm{op}},
\qquad
\rho=\lVert (I-P)\mu(P\,\cdot,\ldots,P\,\cdot)\rVert_{\mathrm{op}}.
\]

Thus, for all \(x_1,\ldots,x_n\),

\[
\lVert(I-P)\mu(Px_1,\ldots,Px_n)\rVert
\leq \rho\prod_{j=1}^n\lVert x_j\rVert. \tag{A1}
\]

Define \(\bar\mu=Q^*\mu(Q\cdot,\ldots,Q\cdot)\) without assuming exact
closure. For a full ordered \(n\)-ary tree \(T\), let \(F_T\) be the ambient
evaluation of \(\mu\), and let \(R_T\) be the lifted reduced evaluation in
which every internal output is projected back to \(\operatorname{ran}P\):

\[
R_{\mathrm{leaf}}=Qz,
\qquad
R_v=P\mu(R_{v_1},\ldots,R_{v_n}). \tag{A2}
\]

Let \(k(T)\) be the number of internal nodes and let \(z_\ell\) be the leaf
inputs. Then

\[
\lVert P F_T(Qz_1,\ldots,Qz_s)-R_T(z_1,\ldots,z_s)\rVert
\leq
\lVert F_T-R_T\rVert
\leq
k(T)\rho M^{k(T)-1}\prod_{\ell=1}^s\lVert z_\ell\rVert. \tag{A3}
\]

The first inequality is contractivity of \(P\). For \(k(T)=0\) the left-hand
side is zero; for \(k(T)\geq1\), the displayed expression has its usual
meaning.

## Proof

For a node \(v\), write \(F_v\) and \(R_v\) for the corresponding ambient and
projected values, \(k_v\) for its internal-node count, and \(L_v\) for the
product of its leaf norms. We prove simultaneously

\[
\lVert F_v\rVert,\lVert R_v\rVert\leq M^{k_v}L_v,
\qquad
\lVert F_v-R_v\rVert\leq k_v\rho M^{k_v-1}L_v. \tag{A4}
\]

The leaf case is immediate. At an internal node, multilinearity and a
telescoping replacement of \(F_{v_i}\) by \(R_{v_i}\) give

\[
\begin{aligned}
\lVert F_v-R_v\rVert
&=\lVert \mu(F_{v_1},\ldots,F_{v_n})
       -P\mu(R_{v_1},\ldots,R_{v_n})\rVert\\
&\leq M\sum_{i=1}^n \lVert F_{v_i}-R_{v_i}\rVert
       \prod_{j\ne i}\max(\lVert F_{v_j}\rVert,\lVert R_{v_j}\rVert)\\
&\qquad+\lVert(I-P)\mu(R_{v_1},\ldots,R_{v_n})\rVert. \tag{A5}
\end{aligned}
\]

Every \(R_{v_i}\) lies in \(\operatorname{ran}P\), so (A1) applies to the last
term. Since \(k_v=1+\sum_i k_{v_i}\) and \(L_v=\prod_iL_{v_i}\), substitution
of the induction hypotheses into (A5) yields

\[
\lVert F_v-R_v\rVert
\leq \left(\sum_i k_{v_i}+1\right)\rho M^{k_v-1}L_v
=k_v\rho M^{k_v-1}L_v.
\]

The norm bound in (A4) follows from the same recurrence and \(P\)'s
contractivity. This proves (A3).

## Polynomial residual corollary

For \(F=\sum_a c_aT_a\), with \(k_a=k(T_a)\),

\[
\lVert QF_{\bar\mu}(z)-PF_\mu(Qz)\rVert
\leq \sum_a |c_a|\,k_a\rho M^{k_a-1}\prod_\ell\lVert z_\ell\rVert. \tag{A6}
\]

For the five-input ternary associator, both trees have two internal nodes;
therefore

\[
\lVert QA_{\bar\mu}(z_1,\ldots,z_5)
      -PA_\mu(Qz_1,\ldots,Qz_5)\rVert
\leq 4M\rho\prod_{j=1}^5\lVert z_j\rVert. \tag{A7}
\]

An \(n\)-Lie fundamental-identity polynomial has \(n+1\) signed terms, each
with two internal nodes, so the same bookkeeping gives the conservative
bound \(2(n+1)M\rho\prod\lVert z_j\rVert\) for the difference of the reduced
and projected ambient residuals, under the exact convention used by the
implementation. A different normalization or symmetry convention must be
registered separately.

## Status and novelty boundary

PROVED_AUXILIARY. The recurrence is explicit, typed, and mechanically
testable. It is not promoted to a major novelty claim: its induction is
elementary, and the prior-art review does not establish that the underlying
perturbation idea is new. A future paper would need a sharper result, a
strictly broader class of typed trees, or a lower-bound/sharpness theorem that
survives comparison with existing multilinear perturbation and model-reduction
literature.
