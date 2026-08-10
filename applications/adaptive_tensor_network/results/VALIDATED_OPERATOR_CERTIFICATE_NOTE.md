# Finite-batch operator-norm certificate

The tensor-network application now exposes
`TensorNetwork.validated_error_certificate`. For each core tensor it uses the
Frobenius norm as a valid upper enclosure of the multilinear operator norm.
It propagates value bounds from the leaf batch and evaluates the deterministic
sup-norm recurrence

\[
D_v\le C_v+M_v\sum_i\left(\prod_{j\ne i}U_{v_j}\right)D_{v_i},
\]

with `C_root=0` because the root is not projected. The certificate is valid for
the supplied finite batch and rank allocation; its bound is intentionally
conservative. It does not certify arbitrary inputs, and it does not claim that
the empirical path factors used by the exploratory allocator are operator
norms.

The accompanying tests compare the bound with the actual held-out root error
for several random finite batches and verify exact zero at full rank.

For small networks, `small_case_validated_certificate_allocation` exhaustively
minimizes this bound under the rank budget. It is a certificate-driven policy,
but its combinatorial search cost means that scalability and true-error
superiority remain unestablished.

Because the bounded-domain recurrence separates into fixed downstream gains and
rank-dependent local normal costs, `global_certificate_optimal_allocation`
solves the same certificate objective by dynamic programming without
enumerating all rank vectors. The resulting certificate applies to every input
whose leaf norms satisfy the supplied domain bounds.
