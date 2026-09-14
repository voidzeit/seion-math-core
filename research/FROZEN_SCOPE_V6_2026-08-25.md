# Frozen scope V6 — classes, conventions, and the theorem-by-theorem table

Date: 2026-08-25. Branch `campaign/gate13-closeout`.
Status: **P1/P2 gate artifact.** This file freezes definitions and theorem
scopes. It proves nothing new; it makes every existing statement quantifier-
complete so that no two of them can appear to contradict.

---

## 0. Why this file exists

Two statements currently coexist in the repository:

```
M2-A     C^P = 1  for k = 2
PT-O-001 exact fixed-eta constant C_T^P(eta) for general k = 2 is OPEN
```

They are **not** in conflict. M2-A is a statement about **Class A** — the
finite-dimensional real binary *chain*. PT-O-001 is about **general** `k = 2`:
higher arity, infinite dimension, broader gated-planar subclasses. The conflict
is manufactured entirely by writing `C_2^P = 1` **without its class subscript**,
which several downstream summaries do.

The fix is notational and mandatory, not mathematical.

---

## 1. Mandatory notation

Every constant carries a class subscript. No exceptions, no abbreviations.

```
                              E_T^P(X)
C_{T, cls}^P(eta)  :=   sup   ------------------------
                     X in cls(eta)   rho * M^(k-1) * L_T
```

where `X` ranges over **realizations**: a choice of ambient space, laws,
projectors, and leaf data satisfying the class constraints at leakage `eta`.

Writing `C_2^P` bare is a scope error. Writing `C_{2,free}^P` is not.

---

## 2. The class lattice

A realization `X` is a tuple `(V, {mu_v}, {P_v}, {z_l})`. Four independent
binary constraints generate the lattice:

| symbol | constraint |
|---|---|
| `free` | laws independently selectable per vertex; projectors independently selectable per vertex |
| `same` | **one** law repeated at every internal vertex, **no tags** — the strict shared-law class |
| `tagged` | one law repeated, but projected leaf directions may carry finitely many **orthogonal tags** that the law may read |
| `sharedP` | **one** projector at every internal vertex |

Since `tagged` relaxes `same` (tags are extra freedom) and both are special
cases of `free` (all laws equal is a particular choice of laws), the constants
are ordered by inclusion of the classes:

```
C_{T, same}^P  <=  C_{T, tagged}^P  <=  C_{T, free}^P
C_{T, cls + sharedP}^P  <=  C_{T, cls}^P
```

**This ordering is the whole content of several open problems.** A theorem that
closes `free` says nothing about `same` unless a witness inside `same` attains
it.

---

## 3. Two root conventions — formally separated

The repository uses two, and the split is real, not sloppiness. Introduce an
explicit flag `eps_r in {0,1}` for whether the root projects.

### `PMT^P` — convention A, `eps_r = 1`

```
R_r = P_r Rtilde_r            E_T^P = || P_r F_r - R_r ||
```

Home of: the `(k-1)` bound, `C_{2,*}`, `W_3`, `U_3`, and the entire
rebracketing hierarchy `J_2, H_2, S_2`.

The `k-1` (rather than `k`) coefficient is a **theorem of this convention
only**: it exists because the root projection removes the root's own normal
defect exactly.

### `PMT^cert` — convention B, `eps_r = 0`

```
R_r = Rtilde_r                E = F_r - Rtilde_r
```

Home of: M24, M25, and the finite-batch certificate line, where the discrepancy
is measured in the root's own space because that is what a deployed computation
returns.

**Rule.** No statement may be moved between conventions without re-deriving it.
A reader who sees `k-1` in a `PMT^cert` context is entitled to conclude the
author lost track, because in convention B the root contributes.

---

## 4. Theorem-by-theorem scope table

`R` = real, `C` = complex. `sup`/`max` records whether attainment is proved.

### 4.1 `k = 2`, convention A

| ID | class | field | dim | rank | topology | arity | laws | proj | value | sup/max | extra hypotheses |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M2-A | `free` restricted to Class A | R | any finite `n>=2` | `1<=r<=n-1` | chain | 2 | independent | independent | `1` | **max** | inner node in first slot of outer; mirror class identified |
| M2-B | `same` + `sharedP` | R | any `n>=2` | any `1<=r<=n-1` | chain | 2 | one gated-planar rotation | one coordinate projector | `eta^2` (value, not constant) | **max** | unit leaves, `M=1`, `rho=eta` exactly |
| M8 | `free` | R (see §6.1) | any finite | any | chain | 2 | independent **or** shared | independent | saturation **iff** EQ1∧EQ2∧EQ3 | characterization | none beyond `k=2` chain |
| M17 | `same` | R | finite | any | chain | 2 | repeated gated contraction `mu_A(x,y)=Ax<e0,y>` | orthogonal, contains `e0` | `1` | **max** | `A` planar contraction, fixed `e0` gate |

**PT-O-001 stands open** for: higher-arity `k=2`, infinite-dimensional
attainment, and gated-planar subclasses outside Class A.

### 4.2 `k = 3`, convention A

| ID | class | field | dim | rank | topology | arity | laws | proj | value | sup/max | extra hypotheses |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M9 | `free` | R and C (proof survives, §6.1) | any finite | any | chain **and** branching | 2 | independent | independent orthogonal | `<= U_3(eta)` | upper only | none |
| M10 | `free` | R and C | any finite | any | chain | 2 | independent | any orthogonal `P_2` | `U_3` **not attained** | non-attainment | none |
| M13 | `free` | R | any finite | any | chain | 2 | independent | independent | `<= W_3(eta)` | upper only | none |
| M14 | `free` | **R** (see §6.1) | any finite | any | chain | 2 | independent | independent | `W_3(eta)` | **max** | witness is 2-D, rank-one |
| M15 | `free` | **R** | any finite | any | branching | 2 | independent | independent | `W_3(eta)` | **max** | witness is 2-D, rank-one |
| M16 | `free` | R | any finite | any | both binary | 2 | independent | independent | `W_3(eta)` | **max** | corollary of M14/M15 |
| M20 | `free` | R | any finite | any | **every** 3-node shape | **any finite** | independent | independent | `W_3(eta)` | **max** | unit `e0` gates inserted in extra leaf slots |
| M21 | **`tagged`** | R | finite | one fixed coordinate projector | chain and branching | 2 | **one** repeated bilinear law | **one** shared | `W_3(eta)` | **max** | projected leaves carry finitely many orthogonal tags |
| M22 | `same`, rank-one/common-leaf | R | finite | rank 1 | chain | 2 | one repeated | one | `2/(sqrt3 eta)` | **max** | **only** `sqrt(2/3) <= eta <= 1` |
| M23 | `same`, rank-one | R | finite | rank 1 | chain | 2 | one repeated | one | reduces to `\|<e0,A^3e0>-<e0,Ae0>^3\|` | equivalence | `A` any finite-dim contraction with `\|QAe0\|<=eta` |
| M10b | `free` | R | **fixed** `n` | **fixed** `r` | chain and branching | 2 | independent | independent | `< U_3(eta)` by `delta_{n,r}(eta)>0` | strict gap | compactness of the fixed class |
| M10c | `free` | R | compresses to `<= 2(leaves+2 nodes)` per type; **20** for binary `k=3` | any | chain and branching | 2 | independent | independent | global strict gap below `U_3` | strict gap | support compression |
| M10d | `free` | R | any finite | any | chain and branching | 2 | independent | independent | `C(1) = 2/sqrt3 < sqrt2` | endpoint | `eta = 1` only |

### 4.3 All `k`, convention A

| ID | class | field | dim | topology | arity | laws | value | sup/max |
|---|---|---|---|---|---|---|---|---|
| PT-003/004 | `free` | R and C | any finite | any | any | independent | `E_amb <= k`, `E_proj <= (k-1)` | upper only |
| M18 | `free` | R | 2 suffices | every fixed full-binary shape | 2 | independent | `lim_{eta->0} C = k(T)-1` | asymptotic |
| M19 | `free` | R | 2 suffices | every fixed arity-compatible shape | any finite | independent | `lim_{eta->0} C = k(T)-1` | asymptotic |
| M3b | `same` | R | any finite | left comb | 2 | one gated-planar rotation | `\|T_k(c) - c^k\|`, `c=sqrt(1-eta^2)` | exact value |
| M3c | `same` | R | any finite | every ordered full-binary | 2 | one gated-planar rotation | `\|a(T)cos(d(T)theta) - cos(theta)^k\|` | exact value |
| M3d | `same` | R | any finite | every ordered arity-compatible | any finite | one gated-planar rotation | same recurrence | exact value |

### 4.4 Rebracketing hierarchy, convention A, `k = 2`

| ID | class | field | dim | rank | value | sup/max | extra hypotheses |
|---|---|---|---|---|---|---|---|
| M40 | `same` + `sharedP` | R | **3** suffices | 2 | `J_2 = 2` | **max** | one ternary law, one projector, all four vertices, all leaves in `Ran(P)` |
| M41 | `same` + `sharedP` | R | 3 | 2 | `H_2 = 2` | **max** | same witness as M40 |
| M42 upper | `free` | R | any finite | any | `\|Ahat\| <= \|PA\| + Sigma_2(eta) rho M L` | upper only | none |
| M42 attain | **`free`** | R | 2 | 1 | `S_2^free = Sigma_2(eta)` | **max** | witness uses **three distinct laws**; `A = 0` exactly |
| Cor 5.5 | all three | R | — | — | `chi = -1` at every extremizer | equality geometry | — |

**`S_2^same` and `S_2^same+sharedP` are OPEN.** Zero valid numerical evidence
in either direction (§7.2).

### 4.5 Certificates, convention B

| ID | class | field | dim | topology | arity | laws | value | sup/max |
|---|---|---|---|---|---|---|---|---|
| M24 | `free` | R and C | any finite | any finite ordered rooted tree | any | independent | `\|delta_v\| <= B_v` per sample | sound bound |
| M24.1 | `free` | R and C | any | any | any | independent | `max_n \|E\| <= max_n B_r` | sound reduction |
| M24.2 | `free` | R and C | any | any | any | independent | `max_n B_v <= Bbar_v` | ordering, generally strict |
| M25 | `free` | R and C | any | any | any | independent | `\|delta_v\| <= G_v <= B_v` | sound, monotone |
| M25.1 | `free` | R and C | any | any | any | independent | strict **iff** `gamma_v>0` and `nu_v<pi_v` | characterization |

All five are **finite-batch**: quantified over a fixed finite leaf family and a
fixed rank assignment. Neither is a computational shortcut — both evaluations
are needed to form the bound.

---

## 5. The M21 adjudication

**Question a referee will ask immediately.** M21 uses tags to make one law
behave as three. Why does that close `k=3` same-law but not `S_2^same-mu`?

**What M21 proves.** Exactly `C_{3,tagged}^P(eta) = W_3(eta)`. Its own source
states the boundary: *"It does not close the stricter rank-one/common-leaf
same-law class."* The sandwich

```
C_{3,same}^P  <=  C_{3,tagged}^P  =  C_{3,free}^P  =  W_3(eta)
```

leaves `C_{3,same}^P` **open below `W_3`**. M22 closes it only on
`sqrt(2/3) <= eta <= 1`, and only for the rank-one/common-leaf subclass.

**Never write `same-mu` unqualified for M21.** Write `tagged`.

**Why tagging does not transfer to `S_2`.** The disanalogy is structural, and
it is worth stating in the paper because the question is obvious.

M21's tags distinguish *positions inside one tree*, letting one law act as
three on orthogonal blocks; the target is a single tree's value, so the blocks
may be chosen independently. `J_2` and `H_2` reach `2` under `same + sharedP`
by exactly this mechanism — M40's witness feeds the shared law's
slot-antisymmetric monomial in opposite orders, which is slot-order tagging.

`S_2` is different: it requires `A = 0` **exactly**, a constraint that
**couples the two trees**. A tagged direct-sum construction builds blocks
independently and then must additionally satisfy a cross-tree equation the
construction does not control. Tagging removes law-sharing as an obstruction;
it does not remove the coupling constraint.

This explains why the question is open rather than closed. **It is not a
proof that `S_2^same < Sigma_2`,** and must not be cited as one.

---

## 6. Scope contradictions found

### 6.1 UNRESOLVED — the field of the `k = 3` theorem

**The gap is a single proof step in M16, and it propagates to the abstract.**

| source | field declared | field proved |
|---|---|---|
| `papers/paper_a/main.tex` abstract | real **or complex** | inherits from M16 |
| `m16_general_binary_class_corollary.tex` | *"finite-dimensional real **or complex** projected-root class"* | see below |
| `m14_exact_chain_constant.tex` | — | *"independently chosen **real** bilinear laws"*, witness *"two-dimensional **real** construction"* |
| `m15`, `m13`, `m20` | silent | silent |

M16 declares its class `A_{3,bin}` over `R` **or** `C`, then proves the
corollary by the step *"the chain component of `A_{3,bin}` is the M14 class"*.
That identification fails on the complex part of its own declared class,
because M14's class is real. **The complex case is asserted, not proved**, and
the abstract inherits the assertion.

The theorem is very likely true over `C`. The upper-bound machinery does not
use realness: M9 uses only Cauchy–Schwarz and Pythagoras, and M10 explicitly
handles the complex case (*"the complex case gives `lambda-bar ||S_1'||^2`,
same conclusion"*). A real witness embeds isometrically in `C^2` and still
attains. But "very likely true" is not the standard this file enforces, and a
referee reading M16's proof will find the step that does not close.

**Two admissible fixes, pick one and record it.**

1. Re-derive M13/M14/M15 over `C` — likely a short remark each — and keep the
   abstract as is.
2. Narrow M16 and the abstract to `R`, and demote the complex case to a stated
   conjecture.

Recommended: (1) if the re-derivation is as short as it looks, since the
complex class is genuinely covered; otherwise (2). What is **not** admissible
is leaving M16's proof step as it stands while the abstract claims `C`.

### 6.2 RESOLVED — `C_2^P = 1` versus "general `k=2` open"

Not a contradiction; a missing subscript. See §0. Enforced by §1.

### 6.3 RESOLVED — M20 per-realization reading

Already corrected in the V5 freeze (defect C2): M20 is a **class-supremum**
statement, not per-realization. Any realization with `P_v = I` everywhere has
`E_T^P = 0`. Recorded here so it cannot regress.

### 6.4 RESOLVED — witness saturation above `eta_c`

Already corrected in the V5 freeze (defect C1): the M14 witness sets
`t = min{eta, sqrt(2/3)}`, so **above** `sqrt(2/3)` the active leakage is
`sqrt(2/3) < eta` and the closure budget is deliberately underused. Earlier
prose claimed "all closure residuals exactly at cap" and contradicted its own
verification table.

### 6.5 RESOLVED — the two `eta_c`

```
eta_c^{S_2} = 1/sqrt(2)  ~ 0.707107     transition of Sigma_2   (k = 2)
eta_c^{W_3} = sqrt(2/3)  ~ 0.816497     transition of W_3       (k = 3)
```

Every occurrence of `sqrt(2/3)` in the repository belongs to the `k=3` line and
is correct.

### 6.6 OPEN ITEM — root convention not flagged in prose

Convention A and B are both in use (§3) and no current document states which is
active. Every theorem statement must carry `eps_r`.

---

## 7. Scope of the negative results

### 7.1 The `(k-1)` bound versus canonical TT/HT — mandatory scoping

Executed by gate D1 (`research/novelty/d1_reduce_to_standard.py`). On the
canonically orthogonalised hierarchical format the standard identity
`||E||^2 = sum_v eps_v^2` is **exact** (`tau = 1.000`, 100% sound at every `k`
tested), while the `(k-1)` bound is sound but looser by up to `3.47x` at
`k = 8`, coinciding only at `k = 2`.

Off that ground the standard bound becomes **unsound** — 26.7% sound at
isometry defect 0.15 and `k=3`, 0.0% at defect 0.50 and `k>=4` — while the
`(k-1)` bound stays sound throughout.

**Required in Introduction, Related Work and Discussion, not an appendix:**
canonical isometric TT/HT is a special regime where stronger exact identities
apply; what `PMT` studies is **non-isometric recursively projected multilinear
computation under approximate closure**.

### 7.2 `S_2^same` evidence status

All same-law landscape evidence produced before commit `8843022` is **void**
(frozen feasibility gradients). The partial differentiable campaign of
2026-08-18 recovered 70 of 84 cells and is preserved as
`rg_s2_samemu_diff_v1_PARTIAL.json`, but its same-law rows **violate
dimensional monotonicity by up to 11%** — a `D=2` instance embeds into `D=4` by
zero-padding, so the supremum cannot decrease with `D` — while the free control
violates by at most 0.6%. Those rows are valid **lower bounds** and nothing
more.

**Unverified assumption.** That `same + sharedP` is closed under isometric
embedding is assumed from the form of the constraints and **has not been
checked in the code**. The monotonicity reading depends on it.

---

## 8. What this file does not do

It freezes scope. It does not: produce the single canonical `W_3` proof
(priority 3), close `S_2^same` (priority 2), build the minimal reproducibility
artifact (priority 5), or adjudicate novelty (priority 7, blocked on a human
panel per `claims/novelty_protocol_v6.yaml`).
