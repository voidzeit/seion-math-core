# Adversarial pure-mathematics review — v2 draft

Recommendation: major revision / do not submit as a novelty paper.

## Summary

The finite-dimensional exact reduction statement is correct under the stated
typed closure hypothesis. The proof is a straightforward induction on full
ordered trees, and the polynomial-identity corollary follows by linearity.
The approximate-closure recurrence is also correct for the repository's
specific convention: the reduced evaluation projects every internal output,
the law has a uniform operator-norm bound `M`, and the closure residual is
uniformly bounded by `rho` on projected inputs. The resulting coefficient is
the number of internal nodes, so the associator bound is the sum of the two
tree bounds rather than an unspecified constant.

The spectral-snapping statement is a conservative consequence of standard
spectral-projector perturbation theory. The no-gap two-dimensional example is
valid and shows why the gap assumption cannot be removed.

## Major concerns

1. The exact restriction theorem, operadic inheritance, and gap estimate are
   standard consequences of known structures. The current record therefore
   does not support a theorem-level novelty claim.
2. The tree recurrence is useful as an explicit certificate, but its novelty
   has not been established against the full literature on multilinear
   stability and structure-preserving reduction.
3. The paper must not imply that the numerical matrix proves a new continuous,
   infinite-dimensional, or universal result.
4. A verified author email and ORCID are still absent. This is an editorial
   blocker, not a mathematical assumption.

## Required revisions

- Either prove a genuinely new theorem with a precise literature distinction,
  or publish the current work as a reproducibility/verification companion.
- State all norm, field, slot-order, and output-projection conventions in the
  theorem statement, not only in the appendix.
- Add a sharpness analysis or lower-bound family if the approximate recurrence
  is to be positioned as more than an implementation certificate.
- Keep `RESEARCH_BLOCKED.md` and the draft watermark until the novelty gate is
  resolved.

## Verdict

The mathematics is internally coherent and honestly scoped, but the present
evidence supports a rigorous finite verification suite—not a submission-grade
claim of a new central theorem.
