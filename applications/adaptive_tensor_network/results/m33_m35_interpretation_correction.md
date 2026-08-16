# Interpretation corrections to M33, M34 and M35

This note corrects **interpretations**. No historical raw data or numbers are
altered; every prior findings file and raw JSON is preserved unchanged.

## M35 — FAILED METRIC / VALID STRUCTURAL FINDING

**Discarded.** The repair coefficient `A_T = 1 − R_T^term / Σ_t R_t^inst` is
ill-posed: the numerator accumulates along the method's own trajectory while
the denominator compares against a state reached by a different trajectory. The
two are not related by any conservation law, and the measured values (−116.4 to
+4.69, including `nan`) reflect that rather than noise. `A_T` is not to be used
again.

**Retained as real empirical results.**

1. The one-step greedy policy is **not** a terminal lower bound. Concrete
   counterexamples at m = 8, 14 and 23, where policies making locally worse
   choices ended with lower terminal error.
2. Therefore `one-step optimality ≠ terminal optimality` for this problem.
3. A reproducibility bug was found and fixed: RNG seeds derived from
   `hash(method)` are salted per process in Python, so candidate pools differed
   between runs. Seeds must be explicit deterministic integers.

## M34 — valid as stated, with terminology pinned

M34 asked a strictly **one-step** question, so its reference was appropriate.
Pinning the vocabulary:

- `E_oracle` in M34 means the **one-step pool optimum** — the best bundle in a
  sampled candidate pool evaluated at a single state.
- `C_I` measures the fraction of the **one-step** headroom above measured first
  order that the pairwise term recovers.
- Neither quantity makes any claim about finite-horizon or terminal
  optimality. The M34 conclusion "`C_I ≈ 1` at every m" is a statement about
  single decisions only.

## M33 — numbers valid, one interpretation withdrawn

The trajectory numbers stand. What must be withdrawn:

- the policy labelled `oracle` was a **step-greedy** policy and is renamed as
  such;
- `E_FO − E_oracle` was described as the terminal "headroom". It is not: M35
  shows the step-greedy trajectory can be beaten, so that difference is not a
  bound on what any policy could achieve;
- consequently the derived statement that the pairwise term "captures ~24% of
  the headroom" refers to a quantity that is not a headroom. The underlying
  terminal errors are unchanged; only the normalization is withdrawn.

## Naming convention adopted from M35b onward

| term | meaning |
|---|---|
| `step_greedy` | exhaustive minimization of the immediate objective at one state. Never called an oracle. |
| one-step pool optimum | best candidate in a sampled pool at one state |
| `E_terminal_star` | exact finite-horizon optimum over all admissible terminal profiles. Available at m = 8 only. |
| best observed policy | best terminal error seen among the policies actually run |

Any quantity called a regret must name its reference explicitly.
