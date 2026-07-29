# Spectral snapping under a gap

For a Hermitian matrix \(A\), define

\[
S_{1/2}(A)=\mathbf 1_{[1/2,\infty)}(A).
\]

Let \(\widetilde P=S_{1/2}(A)\), and suppose

\[
\gamma=\operatorname{dist}(1/2,\sigma(A))>0.
\]

For a Hermitian perturbation \(E\) with
\(\lVert E\rVert_2\leq\gamma/2\), the ranks are unchanged and the
Davis--Kahan spectral-subspace estimate gives the conservative threshold
bound

\[
\lVert S_{1/2}(A+E)-S_{1/2}(A)\rVert_2
\leq \min\left\{1,\frac{4\lVert E\rVert_2}{\gamma}\right\}. \tag{S1}
\]

The constant \(4\) is deliberately a safe one-sided threshold constant for
the regime \(\lVert E\rVert_2\leq\gamma/2\); it is not claimed to be sharp.
For Frobenius norm, the dimension-dependent conversion is

\[
\lVert S_{1/2}(A+E)-S_{1/2}(A)\rVert_F
\leq \sqrt{2r}\,
\lVert S_{1/2}(A+E)-S_{1/2}(A)\rVert_2,
\]

where \(r\) is the common selected rank.

The result is a standard spectral-projector perturbation consequence, not a
new theorem. The gap is essential. With

\[
A_\delta=\operatorname{diag}(1/2-\delta,1/2+\delta),
\quad
E_\delta=\operatorname{diag}(2\delta,-2\delta),
\]

one has \(\lVert E_\delta\rVert_2=2\delta\to0\), while the two snapped
rank-one projectors exchange coordinate axes and remain distance one apart.
Thus no modulus of continuity independent of a positive gap can hold.

Status: ESTABLISHED_KNOWN_RESULT plus a registered exact counterexample.
