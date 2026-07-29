# Approximation plus projection

Let (widehat\mu_v) approximate (mu_v) with
(delta_v=\lVert\mu_v-widehat\mu_v\rVert_{\rm op}).  Insert the ambient
(widehat\mu)-tree between the exact ambient tree and the recursively
projected approximate tree.  The triangle inequality separates

\[
\lVert F_\mu-R_{\widehat\mu}\rVert
\le
\underbrace{\lVert F_\mu-F_{\widehat\mu}\rVert}_{\text{representation}}
+
\underbrace{\lVert F_{\widehat\mu}-R_{\widehat\mu}\rVert}_{\text{projection/closure}}.
\]

In the homogeneous case (lVert\mu\rVert\le M),
(lVert\mu-widehat\mu\rVert\le\delta), and (widehat M\le M+delta).
For (k) nodes the implemented transparent budget is

\[
\begin{aligned}
E_{\rm repr}&\le k\delta(M+\delta)^{k-1}L,\\
E_{\rm closure,base}&\le c\rho M^{k-1}L,\\
E_{\rm interaction}&\le c\rho\bigl[(M+\delta)^{k-1}-M^{k-1}\bigr]L,
\end{aligned}
\]

where (c=k) for ambient error and (c=k-1) for projected-root error.  The
interaction term is the extra recursive amplification of closure caused by
the representation perturbation.  CP reconstruction error, operator-output
error, and closure residual remain separate metrics; CP error is never folded
into (ho).
