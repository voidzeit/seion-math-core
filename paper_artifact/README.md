# Reproducibility artifact

Three files, `numpy` only, under a minute total. They reproduce every constant
in the manuscript without cloning the 628-module research repository.

```bash
bash reproduce_all.sh
```

| file | reproduces |
|---|---|
| `verify_k2_and_scope.py` | `C_{2,*} = 1`; M8's three equality conditions, each broken in turn to show necessity; **and the mandatory TT/HT scope comparison** |
| `verify_k3.py` | the SOS identity behind `4 - 3 eta^2`; `W_3` as an upper bound; the equality geometry `u = v = sqrt2 <=> q = s = sqrt(2/3)`; the attaining witness |
| `verify_rebracketing.py` | `J_2 = 2`, `H_2 = 2` (one law, one projector, dim 3), and `S_2 = Sigma_2(eta)` with `A = 0` exactly |

Each exits non-zero on failure, so `reproduce_all.sh` is usable as a gate.

---

## Proof versus numerical role

**Nothing here is the primary evidence for any theorem.** Every constant below
is proved analytically; these scripts audit the transcription. A referee who
distrusts the numbers should read the proofs, and a referee who distrusts the
proofs will not be reassured by the numbers.

| result | proof | numerical role here |
|---|---|---|
| `C_{2,*} = 1` | analytic (universal bound + two witnesses) | sanity only |
| M8 saturation *iff* | analytic (chain of equalities) | necessity of each condition, by construction |
| `W_3(eta)` upper | analytic (Gram lemma + SOS identity) | audit of the SOS identity and of the feasible-square maximum |
| `W_3(eta)` attainment | analytic (explicit witness) | witness verification, `2.2e-16` |
| equality geometry | analytic (SOS has two squares) | audit that `u = v = sqrt2` maps to `q = s = sqrt(2/3)` |
| `J_2 = 2`, `H_2 = 2` | analytic (explicit witness) | witness audit, exact zeros |
| `S_2 = Sigma_2(eta)` | analytic (Thm 5.1 + Cor 5.2) | witness audit, `2.2e-16` over 9 values of `eta` |
| M24 / M25 ordering | analytic (induction + Cauchy–Schwarz) | strictness checks, not in this artifact |
| all-`k` asymptotics | analytic (2-D witness family) | numerical regression, not in this artifact |
| **TT/HT scope** | — | **executed comparison**; its conclusion is scoping, not sharpness |

The last row is the exception that proves the rule: it is the only place where
a number is doing primary work, and what it establishes is a **limitation**.

---

## Theorem dependency graph

The main line is linear. Everything else hangs off it.

```
                       Definitions  (class lattice, eps_r convention)
                                |
                    Exact local expansion   E_amb^2 = E_proj^2 + E_normal^2
                                |
                       Universal  E_proj <= (k-1) rho M^(k-1) L_T
                                |
              +-----------------+-----------------+
              |                                   |
            k = 2                               k = 3
              |                                   |
        C_{2,free} = 1                    Reduction Lemma (Gram)
              |                                   |
        M8  saturation iff                Geometric Constraint (Pythagoras)
              |                                   |
              |                           Scalar Optimization  (SOS)
              |                                   |
              |                                W_3(eta)
              |                                   |
              |                           Equality Conditions
              |                                   |
              |                              Extremizer (M14)
              |
              +--> J_2 = 2, H_2 = 2  (same + sharedP witness)
                                |
                          Sigma_2(eta)  =  S_2^free
                                |
                    certificate  ||PA|| >= ||A_hat|| - Sigma_2 rho M L
```

Off the main line, in appendices: `U_3` (M9) and its non-attainment (M10),
compactness and support compression (M10b/c), branching (M15), class
corollaries (M16, M20, M21, M22, M23), asymptotic sharpness (M18, M19), the
gated-rotation exact families (M3b/c/d), and the certificate line M24/M25 —
which lives in the **other root convention** and must not be mixed in.

---

## Scope, in one paragraph

Let `T` be a finite rooted ordered tree whose internal vertices carry bounded
multilinear maps between finite-dimensional Hilbert spaces, with an orthogonal
projector applied after every internal operation. Each law has operator norm at
most `M`, and its normal output **on already-projected inputs** is at most
`rho`; write `eta = rho/M`. That is the entire setting. No further vocabulary is
required to read the manuscript.

Canonical isometric TT/HT is a special regime of this setting in which stronger
exact identities apply — `verify_k2_and_scope.py` measures exactly how much
better. What this work studies is the non-isometric regime, where those
identities fail.

---

## What is not here

`S_2^same-mu` is **open**, with zero valid numerical evidence in either
direction after the frozen-gradient retraction. `C_4(eta)` is open. Novelty is
`NOVELTY_UNADJUDICATED` pending a blind recall panel and independent human
review; see `claims/novelty_protocol_v6.yaml` for why those two cannot be
discharged by the authors.
