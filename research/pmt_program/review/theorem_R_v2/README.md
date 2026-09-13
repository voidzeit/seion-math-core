# Theorem R — canonical source v2 (frozen)

`THEOREM_R_v2.md` is the single canonical statement and proof of Theorem R
(real PMT-A): `C^P_T(η) = max_{θ ≤ arcsin η} |1 − (cos θ e^{iθ})^{k−1}| / η`,
where `k` is the number of internal nodes. Status `ADVISORY_PROOF_DRAFT`.

| file | purpose |
|---|---|
| `THEOREM_R_v2.md` | canonical proof (GitHub renders the math) |
| `CHANGELOG_v2.md` | what changed from v1 (mathematics unchanged) |
| `diagonal_lemma_check.py` | Diagonal Lemma control and the `Θ > π` counterexample |
| `sharp_witness_check.py` | exact attainment of the universal sharp witness on 4000 random trees |
| `edge_cases_v2.py` | 8000 degenerate cases for O2 preservation and root reading |
| `asymptotic_vs_sharp.py` | asymptotic witness vs sharp value |
| `outputs/` | results of the four scripts |
| `FREEZE_v2.json` | SHA-256 of the committed blobs |

The frozen v1 package (`../theorem_R_v1/`) remains for provenance. A PDF of this
note awaits a TeX toolchain; no LaTeX, pandoc or Lean is installed on the
authoring machine.
