# M5 — assumptions table

| ID | Statement | Role in proof | What breaks if dropped |
|---|---|---|---|
| H1 | $\|J_N\mu_{v,N}(x)-\mu_v(J_Nx)\|\to0$ uniformly on bounded sets | Controls the "discretization-of-law" error term at each node | Without it, the discretized law need not approximate the continuum law at all — no convergence possible |
| H2 | $\|J_NP_{\tau,N}-P_\tau J_N\|_{op}\to0$ | Controls the projector-discretization error, needed for the reduced/projected evaluation | Without it, $R_{T,N}$ can converge to something other than $R_T$ even if $F_{T,N}\to F_T$ |
| H3 | $\sup_N\|\mu_{v,N}\|_{op}\le M<\infty$ | Bounds the finite product factors in the multilinear telescoping sum, so each term $\to0$ (not just bounded) | Without uniform boundedness, the telescoping sum's factors could blow up faster than the error terms shrink, breaking the finite-sum convergence argument |
| H4 | $\sup_N\rho_{v,N}\le\rho<\infty$, $\rho_N\to\rho_\infty$ | Lets the fixed-$N$ $(k-1)$ bound pass to the limit with a well-defined limiting constant | Without it, the bound's right-hand side may not converge, only the left-hand side would (a weaker, less useful statement) |

All four are exactly as listed in the mission brief; none were weakened
or strengthened here. The proof (`fixed_tree_convergence.tex`) uses each
one exactly once, at the step named in column 3 — none are vacuous or
unused.
