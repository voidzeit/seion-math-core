# Independent truth audit — 2026-07-29

## Status of this audit

This is an **advisory, non-canonical** review. Per `AGENTS.md`, AI-generated
findings remain advisory until a deterministic gate or human review accepts
them; nothing here edits `claims/`, `governance/`, or any registry that the
release gate reads. It sits alongside the existing v1-v4 tracks as an
independent second look, not a replacement for them.

Scope reviewed: branch `program/seion-canonical-repository-v4`, commit
`427ad52` (see git log at audit time). Method: direct reading of registries,
docs, source, and tests, cross-checked by four independent research passes
(finite-core theorem audit, curvature/associator audit, frontier-scope
overreach scan, governance/novelty audit), plus direct verification of
`src/seion_core` module contents for the object registry below.

## Files in this audit

- [priority_a_finite_core.md](priority_a_finite_core.md) — audit of the v3
  finite-canonical-core theorems (typed n-ary laws, exact restriction,
  projector closure, tree error bounds, telescoping order, signed forests)
  against their proof files, tests, and evidence-matrix citations.
- [curvature_associator.md](curvature_associator.md) — audit of the
  curvature/associator/identity claims (Priority B).
- [frontier_scope.md](frontier_scope.md) — a scan for Seionic Hodge
  Program / D-module / Riemann-Hilbert / E8 / G-ASUn overreach (Priority E),
  and the finite cohomology claims that are legitimately in scope
  (Priority C).
- [governance_and_novelty.md](governance_and_novelty.md) — current release
  blockers, novelty-registry status, and a check for application-evidence
  misuse.
- [priority_d_kernels.md](priority_d_kernels.md) — kernel-integrated law
  track (Priority D): finite/exact, honestly self-limiting, near-zero test
  coverage.
- [priority_c_operators_and_cohomology_remainder.md](priority_c_operators_and_cohomology_remainder.md)
  — curried operators/Laplacians/heat semigroups, plus the three
  cohomology modules the first pass left unreviewed.
- [priority_d_multiscale.md](priority_d_multiscale.md) — multiscale
  transport/alignment/persistence track: defensively scoped, untested.
- [priority_c_variational_energies.md](priority_c_variational_energies.md)
  — **the most substantive finding of this audit**: no gradient path
  exists for any variational energy, two energies are unimplemented
  stubs, and the trainable-combination mechanism is unwired dead code.
- [mathematical_object_registry.yaml](mathematical_object_registry.yaml) —
  a registry of the typed objects that actually exist as code in
  `src/seion_core`, each tagged with whether a registered theorem backs it.
- [final_truth_report.md](final_truth_report.md) — best-effort answers to
  the 22 closing questions, using only evidence gathered in this audit (no
  new proof work was attempted).

## What this audit does not include, and why

The full mission also calls for a machine-readable dependency graph
(JSON/GraphML), separate notation/assumption/open-problem registries, and
five to six standalone papers. Those were not attempted in this pass:

- A dependency graph or additional registries built from this repo's
  current state would either duplicate `claims/theorem_dependency_matrix_v3.csv`
  and `claims/scope_registry_v4.yaml` (which already do this job) or would
  require fabricating edges/assumptions not yet derived from an actual
  proof — which is the exact failure mode this mission exists to prevent.
- New papers require new proof work, not just reorganization; none was
  attempted here since none was requested beyond the audit.

## Headline finding

The repository does **not** need to be talked down from an inflated
narrative. Every track examined (v1 through v4) is already fail-closed by
its own governance: `artifacts/release_v4/final_canonical_handoff.md`
records status `FAIL_CLOSED_BLOCKED_PENDING_HUMAN_REVIEW`, and the same
blockers (sharpness, novelty, extended grid, independent review) recur
honestly from v2 through v4 rather than being quietly dropped. The
mission's feared frontier overreach (Hodge conjecture, D-modules, E8,
G-ASUn) is simply not present in the current repo state.

A second pass covering the previously-unreviewed modules (kernels,
operators, remaining cohomology, multiscale, variational energies) found
the same pattern for four of five: honestly self-limiting claims,
undermined mainly by near-zero test coverage rather than by overclaiming.
The fifth, **variational energies, is the one place this audit recommends
caution**: no gradient path exists for any energy anywhere in the source
tree, two named energies (`gji`, `fi`) are hardcoded-zero stubs, and
`total_energy` — the only mechanism that would make energies trainable —
is dead, unwired code. See
[priority_c_variational_energies.md](priority_c_variational_energies.md).
This is adjacent to, but more basic than, the specific failure mode the
mission warns about in section 1.18 (a diagnostic with a structurally-zero
gradient masquerading as a trainable loss) — here there is no gradient
machinery in the loop at all to have that bug.
