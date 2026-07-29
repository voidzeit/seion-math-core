# Typed trees and exact root-error relationships

Let (Tau) be finite.  For each color (	au), let (V_	au) be a
finite-dimensional real or complex Hilbert space and let
(P_	au=Q_	au Q_	au^*), where (Q_	au:W_	au\to V_	au) is an isometry.
A typed ordered tree assigns to every internal vertex (v) a bounded
(a_v)-linear map


\[
  \mu_v:\prod_{j=1}^{a_v}V_{\tau(v,j)}\longrightarrow V_{\tau(v)}.
\]

For reduced leaf data (z_\ell\in W_{\tau(\ell)}), define

\[
F_\ell=R_\ell=Q_{\tau(\ell)}z_\ell,
\quad
F_v=\mu_v(F_{c_1},\ldots,F_{c_{a_v}}),
\quad
R_v=P_{\tau(v)}\mu_v(R_{c_1},\ldots,R_{c_{a_v}}).
\]

At the root put (Delta=F-R).  Since (R\in\operatorname{ran}P),

\[
  \Delta=P\Delta+(I-P)\Delta
        =(PF-R)+(I-P)F,
\]

and the two summands are orthogonal.  Consequently the four named errors obey
the exact identities

\[
 (E_T^{\rm amb})^2=(E_T^{\rm proj})^2+(E_T^{\rm normal})^2,
 \qquad E_T^{\rm red}=E_T^{\rm proj}.
\]

The second equality follows from
(Q^*F-Q^*R=Q^*(PF-R)) and the fact that (Q^*) is an isometry on
(operatorname{ran}P).  These are identities, not bounds.  The implementation
checks both residuals in
`src/seion_core/research_v3/projected_evaluation.py` against independent
coordinate-loop and NumPy evaluations.

Every edge is checked against the input color declared by its node law before
evaluation.  A type-invalid tree has no numerical semantics and is rejected.
