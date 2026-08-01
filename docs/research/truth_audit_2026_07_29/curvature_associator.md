# Curvature / associator / identity audit (Priority B)

## The claim under scrutiny does not exist as posed

The mission asks whether an "anchored curvature-associator theorem" —
`R_induced(x,y)z = Assoc_e(x,y,z)` for the anchored binary reduction
`x∘y = μ(x,y,e)` — is a definition, elementary expansion, conditional
theorem, or false in the stated generality. No file in this repository
states or proves that identity. There is no registry entry, proof file, or
paper section that connects the anchored reduction to an induced curvature
operator.

## What is actually proved

`THM_STANDARD_CURVATURE_ASSOCIATOR_DIFFERENCE_V1`
(`claims/theorem_registry.yaml:2-8`, proof at
`docs/theorems/curvature_associator.md:1-27`, code
`src/seion_core/geometry/induced_curvature.py:15-27`, test
`tests/unit/test_curvature.py`):

- Statement: for *any* bilinear product `∘` on a finite-dimensional space
  (a generic binary product — not the anchored reduction of a ternary
  law), `R_standard(x,y)z = [L_x,L_y]z − L_{[x,y]}z = A(y,x,z) − A(x,y,z)`,
  where `A` is the ordinary binary associator.
- Hypotheses: finite-dimensional bilinear product, the stated bracket.
  Nothing about anchors, torsion, module compatibility, or symmetry.
- The doc explicitly disclaims the stronger identification: "does not
  identify R_standard with one raw associator without an additional
  hypothesis such as A(y,x,z)=0" (`docs/theorems/curvature_associator.md:23`).
- Status `PROVED` is justified — it is a finite algebraic expansion,
  symbolically checked (`artifacts/symbolic/curvature_identity.json`).

Two related but disconnected pieces exist:

- `src/seion_core/geometry/constitutive_curvature.py:6-8` is a **stipulated
  definition**, not a theorem: `"""Definition: the selected algebraic
  curvature is the selected associator."""`, and the function body literally
  returns `law.five_input_associator(*vectors)`. It is a naming choice for
  one associator convention, never composed with anything else, and never
  cited by a registered theorem.
- `anchored_product`/`anchored_associator`
  (`src/seion_core/algebra/ternary_law.py:28-42`) and
  `anchored_left_operator` (`src/seion_core/geometry/left_actions.py:18-21`)
  are implemented as standalone utilities but never composed into an
  `R_induced = Assoc_e` identity anywhere in the codebase.

`docs/definitions/associators.md:9` states the repository's own governing
policy directly: the five-input, anchored-binary, and operadic-partial-
composition associator objects "are implemented as different functions and
are never silently identified." This is an explicit anti-conflation
policy — the opposite of what the audited claim would require.

## Named identities: formally defined vs. prose-only

| Identity | Status |
|---|---|
| Binary/ternary Jacobiator, GJI | Formally coded, `src/seion_core/algebra/jacobi.py`, with a self-disclaimer (lines 18-22) that it is "one named GJI variant... not a universal synonym for every generalized Jacobi identity in the literature" |
| Filippov identity | Formally coded, `src/seion_core/algebra/filippov.py:6-9` |
| Akivis identity | Formally coded, `src/seion_core/algebra/akivis.py:10-21` |
| Cyclic / full symmetry | Named only in prose (`paper/sections/08_symmetry_identities.tex:3`); no separate registered theorem |

The paper is explicit about the exact labeling risk the mission warns
against: `paper/sections/06_associator.tex` states "The five-input and
anchored defects can disagree even for the same tensor," and
`08_symmetry_identities.tex` states "A low residual does not identify one
identity with another."

## Counterexamples on file

- `CE_CURVATURE_NOT_RAW_ASSOCIATOR` (`claims/counterexample_registry.yaml:6-8`,
  `docs/counterexamples/curvature_without_symmetry.md`): targets exactly
  the dropped hypothesis `A(y,x,z)=0` — a product with both ordered
  associators nonzero refutes the unqualified `R=A` statement.
- `REFUTED_SNAPPING_NO_GAP_V1` (`claims/claims_registry.yaml:47-52`,
  `docs/theorems_v2/spectral_snapping.md`) — this is the "no-gap
  counterexample" referenced in `.ai/CURRENT_STATE.md`, but it targets
  spectral-projector continuity under threshold snapping, a different
  theorem entirely, not the curvature-associator identity.
- No counterexample targets an anchored curvature-associator claim,
  because no such theorem is registered for one to refute.

## Overclaim check

None found for this area specifically. The one "functorial" claim in the
repository (`papers/foundations/main.tex:114`, "exact functoriality")
specifies its category precisely — finite-dimensional inner-product
spaces, isometries `Q`, the invariant-subspace hypothesis
`μ(QW,...,QW) ⊆ QW` — so it does not fall into the vague-functoriality
trap the mission warns about either.

## Verdict

The repository is atypically disciplined here. The strongest true
statement it makes is a modest, correctly-scoped, non-anchored curvature-
associator *difference* identity; the anchored/induced version the mission
asks about is neither claimed, proved, nor even attempted — it should
remain classified `NOT_YET_FORMALIZED` if the program wants to pursue it,
not silently assumed to already hold via name-similarity to
`constitutive_curvature.py`.
