# Mixed-mask dynamic program and residual path sums

For each node (v), record (M_v), (m_v), (ho_v), and, when available,
the block norms obtained by restricting every input slot to its projected
(`P`) or normal (`N`) subspace and the output to full, projected, or normal
coordinates.  Decompose every child error orthogonally as
(Delta_i=P_i\Delta_i+(I-P_i)\Delta_i).

The exact subset identity then has three possible states per slot:

- `R`: the recursively projected child;
- `DP`: its projected error;
- `DN`: its normal error.

For every state vector other than all `R`, multiply the corresponding child
bounds and the certified mixed-block norm.  This gives subset bounds
(S_v^F,S_v^P,S_v^N).  With
(lambda_v=ho_v\prod_iB_{c_i}^R), define

\[
\begin{aligned}
B_v^F&=M_v\prod_iB_{c_i}^F,\\
B_v^R&=m_v\prod_iB_{c_i}^R,\\
B_v^P&\le S_v^P,\\
B_v^N&\le\lambda_v+S_v^N,\\
B_v^A&\le\min\{\lambda_v+S_v^F,
  \sqrt{(B_v^P)^2+(B_v^N)^2}\}.
\end{aligned}
\]

The implementation also computes arbitrary, left/right, and provably optimal
telescoping certificates and takes a minimum only among independently valid
upper bounds.  The subset cost is (O(3^{a_v})); hence total complexity is
(O(|T|3^{a_{\max}}+|T|a_{\max}\log a_{\max})), linear in (|T|) for the
declared bounded arities two through four.

## Path-sum form

Fix an optimal telescoping order at each ancestor.  If child (j) is replaced
at ancestor (a), define

\[
h_{a,j}=G_{a,j}
\prod_{i\text{ before }j}B_{c_i}^R
\prod_{i\text{ after }j}B_{c_i}^F.
\]

Expanding the scalar recurrence gives the rigorous source-resolved certificate

\[
B_{T,\mathrm{path}}^A
=\sum_{v\in\operatorname{Int}T}
\lambda_v\prod_{(a,j)\in\operatorname{path}(v,\mathrm{root})}h_{a,j}.
\]

For projected-root error, the source (v=\mathrm{root}) is omitted and the
last propagation gain is the projected-output gain.  For normal-root error it
is retained with the normal-output gain.  The artifact table records every
source contribution rather than only their sum.

The path-sum, mixed-subset, and optimized telescoping bounds use different
information and are not asserted to dominate one another universally.  The
engine reports observed dominance cell by cell and proves only minima of valid
certificates.
