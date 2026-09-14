# Results: projected rebracketing geometry, and the TT certificate line

Consolidated state as of 2026-08-18, branch `campaign/gate13-closeout`.
Every number below is executed, not modelled, unless the line says otherwise.

| line | status |
|---|---|
| `J_2 = 2`, strictest class (M40) | **PROVED**, witness verified |
| `H_2 = 2`, strictest class (M41) | **PROVED**, same witness |
| `S_2 = Sigma_2(eta) < 2`, free laws (M42) | **PROVED**, witness verified |
| `S_2^same-mu` | **OPEN**, zero valid numerical evidence |
| gradient geometry of the search harness | **FIXED**, closed by structural tests |
| `gamma_v` = TT discarded Frobenius mass | **CONFIRMED**, exact |
| Pythagorean certificate on TT chains | **RETRACTED** — exact, hence vacuous |
| certification tax as a commercial quantity | **RETRACTED** — artifact |
| certified allocator as a product | **DEAD** |
| `kappa_intrinsic = 1` for TT chains (G0/G1/G2) | **ESTABLISHED** |
| branching amplification survives canonicalization | **RETRACTED** — artifact of local truncation |
| `tau = sqrt(r1 r2 / r_p)` under LOCAL truncation | **CONFIRMED**, 33 configurations |
| same, under HT-SVD matricized truncation | **collapses to ~1.01** |

---

## Part I — The `k = 2` constants

For projected multilinear trees, `C_T^P(eta) = sup E_T^P / (rho M^{k-1} L_T)`
with `eta = rho / M`, three constants over rebracketing pairs `A = F_T - F_T'`,
`Ahat = R_T - R_T'`:

| constant | meaning | value | attained | class |
|---|---|---|---|---|
| `C_2^P` | error inside one tree | `1` | yes | prior (M8) |
| `J_2` | distortion between trees | `2` | yes | free / same-`mu` / same-`mu`+shared-`P` |
| `H_2` | concealment of genuine defect | `2` | yes | same witness as `J_2` |
| `S_2` | fabrication of spurious defect | `Sigma_2(eta) < 2` | yes | free (same-law **OPEN**) |

with

```
Sigma_2(eta) = sin( min(2 arcsin eta, pi/2) ) / eta
             = 2 sqrt(1 - eta^2)   for 0 < eta <= 1/sqrt(2)
             = 1/eta               for 1/sqrt(2) <= eta <= 1
```

continuous, `Sigma_2(1/sqrt(2)) = sqrt(2)`, `Sigma_2(1) = 1`. The active
constraint switches at the crossover: below `eta_c^{S_2}` the closure budget
binds (`d = d' = eta`), above it the norm budget does (`d^2 + d'^2 = 1`).

**Two distinct transitions; do not conflate them.**

```
eta_c^{S_2} = 1/sqrt(2)   ~ 0.707107     transition of Sigma_2  (this file, k=2)
eta_c^{W_3} = sqrt(2/3)   ~ 0.816497     transition of W_3 = C_3^P   (k=3)
```

`W_3(eta) = sqrt(4 - 3 eta^2)` below `sqrt(2/3)` and `2/(sqrt(3) eta)` above.
That constant is unaffected by anything in this file. Every occurrence of
`sqrt(2/3)` in the repository belongs to the `k = 3` line and is correct.

> A projection can conceal an arbitrarily large rebracketing defect entirely,
> but it cannot fabricate one of the same size: concealment is sharp at
> `2 rho M L`, fabrication is sharp at `Sigma_2(eta) rho M L < 2 rho M L`.

**Verification.** 123 witness audits, all pass, 19-28 checks each, over 41
values of `eta` in `[0.025, 1.0]`. Operator norms and closure defects are
*measured* (alternating maximization, 400 restarts, brute sweep as stall
detector) and matched to analytic values at `1e-9`.

```
max | S_2 measured  -  Sigma_2(eta) analytic |  =  4.44e-16     (41 witnesses)
```

This sharpened the usable certificate threshold from `2 rho M L` to
`Sigma_2(eta) rho M L`.

---

## Part II — The instrument that nearly faked a constant

The fused GPU search normalized its objective by a feasibility factor computed
under `no_grad`. The forward pass was scale invariant; the backward pass was
not. `J(c mu) = c^2 J(mu)` forces `<grad J, mu> = 2J > 0`, while
`F(c mu) = F(mu)` forces `DF(mu)[mu] = 0` — freezing `F` leaves the radial
component uncancelled, and the optimizer climbs a direction the constraint
should have removed.

Measured, `D = 3`, rank 2:

| mode | radial `|DF[mu]|` | `|F(c.mu) - F(mu)|` | max FD rel err |
|---|---|---|---|
| frozen, `eta=0.3` | `5.443e-01` | `1.388e-16` | `1.072e+01` |
| **differentiable**, `eta=0.3` | `7.633e-17` | `1.388e-16` | `9.115e-06` |
| frozen, `eta=1.0` | `5.434e-01` | `2.220e-16` | `7.686e+00` |
| **differentiable**, `eta=1.0` | `1.249e-16` | `2.220e-16` | `5.127e-08` |

Envelope theorem restored on the operator norm: `|<grad N, mu> - N| = 2.665e-15`.

The forward column is scale invariant in *both* modes — the bug is invisible to
any forward check, which is why it survived so long. Two of my own hypotheses
were refuted before the real cause was found: the Adam step size (the lr sweep
was non-monotonic, `lr=1e-3` gave 1.328 versus `lr=0.05` giving 1.686) and a
non-converged estimator (the converged loop gave 1.6862 versus 1.6858).

**Consequence.** All same-law landscape evidence produced before commit
`8843022` is invalid. `rg_fused_regraded_raw.json` records
`differentiable: False`; its 72 same-law cells (medians `J` 0.846, `H` 0.842,
`S` 0.835 of ceiling) are **not evidence** and must not be cited. Its 72
free-class cells still corroborate the theorems: `J` and `H` reach
0.9989-0.9997 of `2`, `S` reaches 0.9156-0.9984 of `Sigma_2(eta)`.

`S_2^same-mu` therefore remains OPEN with *no* valid numerical evidence either
way. The CAL2-DIFF-v1 calibration campaign was never run.

---

## Part III — The TT line, and its retraction

### What was built

A bridge from TT-SVD telemetry to the M24 certificate, on 200 instances:

| gate | result | verdict |
|---|---|---|
| projector idempotent | `1.78e-15` | pass |
| projector self-adjoint | `3.33e-15` | pass |
| reconstruction | `0.0` | pass |
| `gamma_v` vs **Frobenius tail** | `1.10e-15` | **exact match** |
| `gamma_v` vs spectral residual | `0.381` | rejected |
| `gamma_v` vs unsquared sum | `1244.8` | rejected |

So the object TT truncation already reports — the discarded Frobenius mass —
*is* M24's realized leakage `gamma_v`, exactly. That identification stands.

A block lemma was then proved. With `A_v = Ran(P_{v-1}) (x) R^n` and
`D_v = Ran(Q_{v-1}) (x) R^n`, left-to-right contraction with left-index
truncation puts `a_v = M_v delta_{v-1}` in `D_v` and `b_v = Q_v Rtilde_v` in
`A_v`. They are orthogonal because they live in complementary *blocks*, not
because `P_v a_v = 0`. This licenses

```
H_v = sqrt( m_v^2 H_{v-1}^2 + gamma_v^2 ),      H_r = m_r H_{r-1}
```

Confirmed numerically: birth layers stay mutually orthogonal through transport
(Gram off-diagonal `p50 = 6.67e-16`), so `||delta||^2 = sum_i ||e_i||^2`
exactly, and the layered certificate collapses onto this one.

Two sub-lines closed **negative**:

- **REACH-1**: restricting `M_v` to the reachable subspace does not lower the
  gain, `p50 = 0.9999999994`. `M_v` contracts the bond index while the
  constraint sits on the left index, so it cannot bind.
- **LAYER-GAIN**: per-layer gains are not smaller than `m_v`; closed
  analytically after the first numerical version was found invalid (it measured
  the realized 1-D vector, not the reachable subspace).

Measured tightening on the corpus: `tau` from `7.573` to `3.958`, **-47.7%**.

### The falsification (run today)

The whole measurement was made on **non-orthogonalized** trains. Standard
TT-SVD right-orthogonalizes first. Rerunning identical code on the
right-orthogonalized representation of the *same* tensors (reconstruction
agreement `2.12e-15`):

| quantity | non-orthogonalized | right-orthogonalized |
|---|---|---|
| `tau` M24 (p50) | `13.62` | `1.333` |
| `tau` Pythagorean (p10 / p50 / p90) | `4.71 / 9.49 / 17.08` | **`1.0000 / 1.0000 / 1.0000`** |

Over 20 240 numerically meaningful rows, `cert/error` lies in
`[1 - 3.8e-13, 1 + 2.4e-12]`. (240 further rows sit at `error ~ 1e-16`, full
rank, where the ratio is float noise.)

The certificate is **exact**. And exactness makes it commercially vacuous — it
selects precisely the oracle rank:

| eps | certified per-bond cost | uniform-oracle cost | max `cert/error` |
|---|---|---|---|
| `3.0e-01` | **1.0000** | 1.3393 | `1.000000` |
| `1.0e-01` | **1.0000** | 1.1500 | `1.000000` |
| `3.0e-02` | **1.0000** | 1.1667 | `1.000000` |
| `1.0e-02` | **1.0000** | 1.1230 | `1.000000` |

The reason is elementary in hindsight: after right-orthogonalization each slot
map is an *isometry* on the Frobenius norm (`G G^T = I` gives
`||X G||_F = ||X||_F`), so the recursion is an equality, not a bound. This is
Oseledets' TT-SVD error identity. The "Pythagorean certificate" is a
rediscovery of it on chains.

### The baseline was also a strawman

`threshold_ranks` used a per-bond *relative* cutoff `= eps`. That is not the
field rule. Oseledets uses `delta = eps ||T|| / sqrt(d-1)` on discarded
Frobenius mass — which is exactly the `beta_i <= eps/sqrt(k)` budget split
proposed in this thread. On orthogonalized trains:

| eps | my cutoff: within tol | med `E/eps` | Oseledets: within tol | med `E/eps` | cost vs mine |
|---|---|---|---|---|---|
| `3.0e-01` | 37.5% | 1.103 | **100.0%** | 0.610 | 1.220x |
| `1.0e-01` | 55.0% | 0.953 | **100.0%** | 0.519 | 1.220x |
| `3.0e-02` | 70.0% | 0.788 | **100.0%** | 0.515 | 1.118x |
| `1.0e-02` | 67.5% | 0.911 | **100.0%** | 0.503 | 1.109x |

The real standard is already certified, already exact, already 100% reliable,
at 1.11-1.22x the cost of a heuristic that misses tolerance a third to
two-thirds of the time.

### What is retracted

Everything downstream of the non-orthogonalized corpus:

- `tau_M24 = 7.66`, `tau_Pyth = 3.96`, and the `-47.7%` tightening as
  statements about TT (they remain correct statements about the
  non-orthogonalized representation, which nobody uses);
- the certification tax tables in `tt_econ_frontier_v1.csv`,
  `tt_econ_poly_*.csv`, `tt_econ_exp_0.5.csv` (taxes 1.00-3.75, "recovered"
  0-14.1%);
- the allocation split of `tt_allocation_split_v1.json` (uniform 1.36,
  certified per-bond 2.40, threshold 1.11, allocation gain ceiling 1.196x);
- the derived reading that "the tax is caused by the certificate, not by
  uniform ranks", **and** its predecessor "the margin is in allocation";
- the product thesis in all three forms it took: *certified allocator beats
  threshold*, *certification premium collapses at tight tolerance*, and
  *threshold + verifier + cheap repair*. The verifier has nothing to verify.

### What survives

- `gamma_v` = discarded Frobenius mass, exactly. Representation-independent.
- The block lemma and the Pythagorean recursion as **PMT** statements, for
  general projected multilinear trees where slot maps are *not* isometries and
  the graph is not a chain. On that object the recursion is a genuine bound
  and M24/M25 still apply. Nothing measured today touches it — but nothing
  measured today supports it either.
- The negative closures REACH-1 and LAYER-GAIN.

---

## Part V — The gauge battery, and where the line may still live

`tau` collapsed under a change of representation, so the first question is
whether it was ever a property of the object. A bond gauge

```
core_v -> core_v . A          core_{v+1} -> A^{-1} . core_{v+1}
```

is the identity on the represented tensor. 200 instances, chain of 5 cores,
rank 3, gauge condition number `1e3`; worst relative tensor drift across every
gauge applied: `< 1e-8`, checked before any reading is taken.

| | p10 | p50 | p90 | max |
|---|---|---|---|---|
| slot gains, canonical | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| slot gains, after G1 *(same tensor)* | 1.0000 | 1.0000 | 741.40 | 979.03 |
| **tau** canonical | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **tau** G0 orthogonal gauge | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **tau** G1 ill-conditioned gauge | 5.0226 | 14.140 | 30.848 | 75.065 |
| **tau** G2 re-canonicalized | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

G0 leaves `tau` untouched, G1 moves it by more than an order of magnitude on a
tensor that has not changed at all, and G2 restores it exactly. So for TT
chains, with `kappa_intrinsic := inf over admissible gauges of the
non-isometric amplification`,

```
kappa_intrinsic (TT chain)  =  1
```

and the retracted slack is formally a gauge artifact. This is the theorem-shaped
version of the retraction in Part III.

### Branching does not collapse the same way

At a branching node the parent-directed unfolding is `G : R^{r_1 r_2} ->
R^{r_v}` with `r_v < r_1 r_2` generically. Canonicalization can make its columns
orthonormal — a strict **co-isometry** — but `rank(G) <= r_v < r_1 r_2` means it
cannot be an isometry out of the full child product, for dimension reasons that
no gauge can repair. It therefore discards part of a generic child error while
the certificate still charges gain 1.

Measured, node gain exactly `1.000000`, both children truncated, 300 instances:

| node | certificate | tau p10 | tau p50 | tau p90 |
|---|---|---|---|---|
| **square**, `parent = bond^2` (true isometry) | sibling-aware | **1.0000** | **1.0000** | **1.0000** |
| square, same | naive | 1.0052 | 1.0052 | 1.0052 |
| **reduced**, `parent = bond` (co-isometry) | sibling-aware | 2.6158 | **2.8416** | 3.1564 |
| reduced, same | naive | 2.6295 | 2.8565 | 3.1729 |

The square-node control is what makes this readable: with a genuine isometry the
certificate is exact to `1.0000`, so `tau = 2.84` at the reduced node is the
dimension reduction and **not** a mis-specified certificate. (The naive
certificate, which ignores the sibling branch's norm, is wrong by 0.5%; both
versions are reported so the effect cannot be attributed to that.)

A random search over bond gauges — 30 instances, 400 admissible gauges each,
12 000 samples, every one verified to preserve the tensor — never lowered `tau`
below `2.4079`, and never improved on the canonical form at all.

### The mechanism, and its closed form

The node does not amplify: it **projects away**. After canonicalization
`U^T U = I`, so transport is `x -> U^T x` and `||U^T x|| = ||P x||` with
`P = U U^T` the orthogonal projector onto an `r_p`-dimensional subspace of
`R^{r_1 r_2}`. For an error generic relative to that subspace,
`E||Px||^2 = (r_p / r_1 r_2) ||x||^2`, while the certificate still charges gain
`1`. Hence

```
tau  =  sqrt( r_1 r_2 / r_p )
```

Measured across **33 configurations** — bond sizes 6, 8, 10; ranks 2, 3, 5;
parent dimensions `r_p`, `2 r_p`, `4 r_p`, `r_1 r_2` — node gain exactly
`1.0000` throughout:

| bond | `r_1 r_2` | `r_p` | reachable dim | tau measured | law | ratio |
|---|---|---|---|---|---|---|
| 8 | 64 | 8 | 30 | 2.8228 | 2.8284 | 0.9980 |
| 8 | 64 | 16 | 30 | 2.0004 | 2.0000 | 1.0002 |
| 8 | 64 | 32 | 30 | 1.4127 | 1.4142 | 0.9989 |
| 8 | 64 | **64** | 30 | **1.0000** | **1.0000** | **1.0000** |
| 10 | 100 | 10 | 42 | 3.1771 | 3.1623 | 1.0047 |
| 10 | 100 | 100 | 42 | **1.0000** | **1.0000** | **1.0000** |

Worst relative departure over all 33: **1.8%**. The law's falsifiable edge —
`r_p = r_1 r_2` makes the node a true isometry, so `tau` must be exactly `1` —
holds in **all 9** such cases.

**A chain is the `r_p = r_1 r_2` corner of this law.** The Part III collapse and
the branching survival are one statement, not two: chains have no compression at
the node, so nothing is projected away and the certificate is exact.

**Why no gauge removes it.** A bond gauge is an invertible `A`, and invertible
maps do not change dimensions, so `r_1 r_2`, `r_p` and their ratio are gauge
invariant. The reachable error subspace has dimension `(r_1-k)k + k(r_2-k)`
(24-50 in the table above), which exceeds `r_p` wherever the node compresses, so
it cannot be embedded in `Ran(U)` under any gauge either.

### And it dies to the same control the chain died to

The law above truncates each child by the SVD of the **child map alone**. HT-SVD
and every TTN implementation do not do that: they truncate using the SVD of the
tensor **matricized at that edge**, `T[(a) x (b,p)]`, which already folds in the
node and the sibling. Rerunning with that truncation, everything else identical:

| bond | `r_p` | rank | tau LOCAL | tau MATRICIZED |
|---|---|---|---|---|
| 8 | 8 | 3 | 2.8897 | **1.0122** |
| 8 | 16 | 3 | 2.0028 | **1.0078** |
| 8 | 64 | 3 | 1.0000 | **1.0052** |
| 10 | 10 | 3 | 3.1916 | **1.0118** |
| 10 | 20 | 3 | 2.2298 | **1.0076** |
| 6 | 6 | 2 | 2.4652 | **1.0222** |

`tau` collapses to `1.005-1.022` at every node dimension. **The branching
amplification is a property of HOW YOU TRUNCATE, not of the branching
structure.** Truncating a child in ignorance of its environment throws away mass
the node was going to project out anyway; the environment-aware truncation the
standard algorithm actually performs does not.

This is the third retraction of the same shape in one day, and the first two are
why it was caught:

| # | claim | invariance it failed |
|---|---|---|
| 1 | same-law landscape gap | scale invariance of the backward pass |
| 2 | TT certification tax | gauge / canonicalization |
| 3 | branching amplification | choice of truncation rule |

REACH-2 is retracted with it. It did answer YES where REACH-1 answered NO —
`||U^T||` restricted to the reachable subspace is `0.83-0.96 < 1`, and a
certificate charging it stays sound — but it recovered only 10-15% of a gap that
does not exist under the standard truncation.

**This is a lead, not a theorem.** Random search is weak evidence about an
infimum, and the fact that it never beat canonical is equally consistent with
canonical being optimal and with the search being uninformative. What *is*
established is the closed form above, its mechanism, and the gauge invariance of
the ratio that drives it. What is NOT established is `kappa_intrinsic > 1` as an
infimum: the law is generic, and whether a gauge can steer a *specific realized*
error into `Ran(U)` for a given instance remains open. That is the
reachable-error subspace question at a branching node — the same question
REACH-1 answered negatively for chains, and the one that would turn this into a
theorem.

---

## Part IV — What is open

1. **`S_2^same-mu` and `S_2^same-mu,shared-P`.** The `S_2` witness uses three
   different laws. Whether one tagged law reaches `Sigma_2(eta)` is unknown.
   The falsification harness is `rg_fused_search.py --differentiable`.
   **Not** `rg4_s2_search.py`: that script computes feasibility under
   `torch.no_grad()` and therefore carries the very bug of Part II. It is
   quarantined.
2. **RG-6**: `J_3` versus `2 W_3(eta)`, and `S_3`, `H_3`. `H_3 = 2 W_3` should
   follow from the same two-anti-aligned-witnesses argument; `S_3` needs a new
   coupling argument.
3. **Does the Pythagorean bound stay non-trivial off the chain?** The only
   question that could revive the certificate line: exhibit a projected
   multilinear tree whose slot maps are provably non-isometric after every
   admissible canonicalization, and measure `tau` there. If canonicalization
   always restores isometry, the line is closed for good.
4. **Gauge battery G0/G1/G2.** Now the priority falsifier, since
   right-orthogonalization turned out to be exactly such a gauge change and it
   annihilated the result.
5. RG-7 (`Delta_geom`), RG-8 (anchor dependence), RG-9 (continuum).

Deliberately not attempted: `delta^2 = 0`, GJI, Hodge, `E8`, fractal manifolds,
or any claim that a differential curvature has been discovered.

---

## Verification

```
tests/math_closure/test_m40_m42_rebracketing_geometry.py     55 tests
tests/math_closure/test_m40_m42_gradient_pipeline.py          9 tests
tests/math_closure/test_m40_m42_harness_calibration.py        8 tests
                                                             72 passed

full suite: 740 passed in 459.99s (0 failures, 0 skips)
```

The gradient pipeline file includes `test_frozen_normalization_is_detectably_wrong`,
which fails if the bug is reintroduced, and the calibration file includes
`test_harness_reproduces_the_exact_witness` at four values of `eta` — the
near-witness recovery gate.

**Hardware.** RTX PRO 5000 Blackwell Laptop (24 GB, 82 SMs, CC 12.0, CUDA 12.8,
torch 2.12) and Intel Core Ultra 9 285HX (24 cores, 127 GB). All arithmetic
`float64`. Fusing objective, class, rank and `eta` into per-element vectors took
the sweep from 42% GPU utilization at 2.0/24 GB to 100% at 24 GB. The witness
audit runs 123 audits over 41 `eta` values in 15 s on 24 cores.
