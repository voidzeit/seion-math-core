# Exact invariant reduction and partial composition

## Statement

Let \(V\) and \(W\) be finite-dimensional Hilbert spaces and let
\(Q:W\to V\) be an isometry. Put \(P=QQ^*\). Let

\[
\mu:V^{\otimes n}\longrightarrow V
\]

be an \(n\)-linear law satisfying the invariant-subspace hypothesis

\[
\mu(\operatorname{ran}P,\ldots,\operatorname{ran}P)
\subseteq \operatorname{ran}P. \tag{H1}
\]

Define the reduced law

\[
\bar\mu(z_1,\ldots,z_n)
 =Q^*\mu(Qz_1,\ldots,Qz_n). \tag{1}
\]

Then

\[
Q\bar\mu(z_1,\ldots,z_n)
 =\mu(Qz_1,\ldots,Qz_n). \tag{2}
\]

If \(\nu\) is another law and the dimensions match, then for every declared
operadic slot \(i\),

\[
Q(\bar\mu\circ_i\bar\nu)
 =(\mu\circ_i\nu)(Q\,\cdot,\ldots,Q\,\cdot), \tag{3}
\]

provided the corresponding invariant-subspace hypotheses hold for both
laws. The same assertion holds for a finite rooted ordered tree of partial
compositions.

## Proof

By (H1), the vector on the right of (1) belongs to \(\operatorname{ran}P\).
Since \(QQ^*\) is the orthogonal identity on this range,

\[
Q\bar\mu(z_1,\ldots,z_n)
 =QQ^*\mu(Qz_1,\ldots,Qz_n)
 =\mu(Qz_1,\ldots,Qz_n),
\]

which proves (2).

For (3), evaluate the two sides at arbitrary reduced inputs. The inner
factor is equal after lifting by the induction hypothesis. The outer law is
then evaluated on the same vectors, and (2) applies once more. Induction on
the number of internal vertices proves the tree statement. In tensor
coordinates, the statement is exactly contraction by \(Q\) on every input
mode and by \(Q^*\) on the output mode, followed by the ordinary contraction
associated with the tree.

## Status and novelty boundary

ESTABLISHED_KNOWN_RESULT. This is the restriction of an algebraic law to an
invariant subspace, expressed in the partial-composition language used by the
software. The result is not claimed as a new operad theorem. The v2
contribution is instead an explicit, independently tested finite-dimensional
certificate and a precise record of what additional theorem would be needed
for a novelty claim.

## Machine evidence

- Reference implementation: src/seion_core/research_v2/reference.py.
- Vectorized implementation: src/seion_core/research_v2/accelerated.py.
- Exact examples: artifacts/symbolic_v2/.
- Parity tests: tests/research_v2/.
