# P6A status

`PROVED_UNDER_ASSUMPTIONS`

P6A is implemented in
`src/seion_core/research_v4/source_aware_dag.py` and tested by
`tests/research_v4/test_source_aware.py`.

Validated scope:

- finite acyclic graph;
- finite-dimensional real or complex numeric matrices;
- first-order source-linearized propagation;
- shared-source operators are aggregated before taking a norm;
- source-aware bound is no larger than the pathwise triangle certificate;
- projected root can omit its local source exactly;
- cycle and dimension mismatches are rejected.

Not closed by P6A:

- higher-order source interactions;
- full nonlinear multilinear DAG error expansion;
- correlation-aware probabilistic bounds;
- universal sharpness of any resulting certificate.
