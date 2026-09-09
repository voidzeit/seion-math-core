# PMT fixed-eta `k >= 4` frontier

Status: `OPEN_PROBLEM` (2026-09-09).

## Closed input to the program

For a finite ordered rooted tree with `k` internal vertices, orthogonal
projectors, uniform law norm `M`, projected-input closure budget `rho`, and
leaf product `L_T`, the implemented theorem contract is

\[
E_T^P\le (k-1)\rho M^{k-1}L_T.
\]

For every fixed finite topology, the existing M18/M19 results establish the
small-`eta` asymptotic coefficient `k-1` in their declared independent-law
classes.  At `k=3`, the fixed-`eta` value is the exact `W_3(eta)` contract.

Neither result determines the fixed-`eta` value for `k>=4`.

## Topologies to keep separate

The first frontier matrix should include at least:

| id | internal skeleton | first question |
|---|---|---|
| K4-CHAIN | four internal vertices in a chain | does the two-variable Gram reduction generalize? |
| K4-BRANCH-BELOW | two lower siblings feeding an internal parent, then the root | how do two retained/normal pairs couple? |
| K4-MIXED | a two-node chain and one sibling feeding the root | can chain and branch terms share a root polar witness? |
| K4-STAR | three internal children feed a ternary root | what is the nuclear norm of the three-source coefficient tensor? |

Higher arities add leaf slots, but the effective-law reduction must be stated
before using it.  Same-law, common-leaf, rank-one, and gated subclasses are
separate problems and must not be silently identified with the independent-law
class.

## Allowed evidence levels

1. `PROVED_UPPER_BOUND`: an analytic inequality under written hypotheses.
2. `CERTIFIED_LOWER_BOUND`: an explicit admissible construction with analytic
   norm and closure checks.
3. `NUMERICAL_OBSERVATION`: a finite search or interval calculation whose
   result is preserved with seed, dimension, precision, and feasibility data.
4. `CONJECTURE`: a named equality or recurrence supported by the preceding
   evidence, pending proof.

The PMT API intentionally exposes no `exact_constant` field for a `k>=4`
search result.  A candidate above the universal bound is a failed feasibility
check, not a discovery.

## Minimum next mathematical work

* derive a source-resolved subset expansion for each K4 skeleton;
* identify the smallest Gram/PSD state that contains all retained and normal
  components at the next node;
* prove an upper envelope before optimizing a witness family;
* certify any proposed lower construction with operator-norm and closure
  inequalities independent of the optimizer;
* compare the fixed-eta envelope with the known small-eta coefficient `3`.

The existing torch search under `optimizer.py` is a discovery instrument only.
It must remain labelled numerical observation and cannot amend theorem or claim
registries by itself.
