# Projected Graphs V5 — review artifact manifest

This manifest identifies the exact review inputs by SHA-256 hash. It was
generated on 2026-08-09 from branch `campaign/gate13-closeout` at source
commit `cbb6ddb0a050882249054f9044c905e442a561ab`. The worktree was dirty;
the hashes, rather than the branch name alone, define this review snapshot.

The manifest is a reproducibility aid, not mathematical approval. If any input
changes, regenerate the hashes and create a new dated manifest before review.

| Relative path | SHA-256 |
|---|---|
| `papers/projected_graphs_v5/projected_multilinear_trees_v5.tex` | `25F31E9A1449E8BB3BDB0000CB6970C3DA8C41487A05E1A4D1D6AFCD9D32FDA0` |
| `claims/theorem_registry_v5.yaml` | `B08E94607581B7AD7A8105875F270729B8151A638D8FCBD3ADC95ECD85AFB92C` |
| `research/math_closure/k2/saturation_iff_theorem.tex` | `0B9B09D2FF51DEAFC3DDDC87C9CF119B3CE0199275AF5B63E5E564426C171B2A` |
| `research/math_closure/k3/m13_unconditional_chain_envelope.tex` | `636374DC70E3D3584221E42C6A6805640E7AAA94E1B3B621A691C6DF386C1024` |
| `research/math_closure/k3/m14_exact_chain_constant.tex` | `4D3D1B0F057A0ABDE39349146EDB03F464833C018525444538F3E239E2AF4D63` |
| `research/math_closure/k3/m15_exact_branching_constant.tex` | `0CC398F0B3540F8ABF35FD0B69E06D084F4003B4B1BA05CCED247AC4AAD648DF` |
| `research/math_closure/k3/m16_general_binary_class_corollary.tex` | `8D12CF1523E22A279CC7A50ED4860BE31F663B8FD7FF289AE501FCE5800D4C55` |
| `research/math_closure/k3/m18_binary_tree_asymptotic_sharpness.tex` | `84B346476306EAFA3BD51D1875D930973469F9D4BFAC48BE956354E29DEFE715` |
| `research/math_closure/k3/m19_finite_arity_asymptotic_sharpness.tex` | `FD310A7DDAEA3F60023DFA9992B16F970A05C1579D6EB2219972FB97BF675C93` |
| `research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.tex` | `55037074C640FF2C52165E8BBDE8EFEA9BB30CBC8F43235AD636A7C77CA68BC0` |
| `research/math_closure/k3/m21_same_law_tagged_exact_constant.tex` | `59B8AC63A4354BA9DE6A2A6F60F92EA205EEA3F23E29D7B555F936CBE59405A1` |
| `research/math_closure/k3/m22_same_law_rank_one_high_eta.tex` | `0E886D6CC761137758718AB965980701A836A978B94BD323F22202D6E468432B` |
| `research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.tex` | `56FC30BBB67E0C9CF5CAE589A0C708448DD194DDC983731BC786C7FA5EC40B6C` |
| `research/projected_trees_v5/review/REVIEW_PACKET_2026-08-08.md` | `BCB2A24F9C6F1C1B14641E91771CFEA8004DC5F9D0514524E7B63A137318B75C` |
| `research/projected_trees_v5/review/EXTERNAL_REVIEW_REQUEST_TEMPLATE.md` | `DFB50F9509C59606145A884060CA3441ECBD0A4148D2D9540B5E47F84CF1A184` |
| `research/projected_trees_v5/review/NORMALIZATION_SCOPE_SHEET_2026-08-09.md` | `2AA7CFB612525F7519AB06560A7B73AD48880E65E21646434AC436646AA32038` |
| `research/projected_trees_v5/review/OBJECTIVE_REQUIREMENTS_AUDIT_2026-08-09.md` | `D8240A36D3B58BD53883A9DC20C80FA8BDE6E93FBC67B97AC8728319285123D1` |
| `research/projected_trees_v5/novelty/TARGETED_AUDIT_2026-08-08.md` | `7E3F2C05225F89B25B32E1F0086EF3351450968CEB798A6044293F4766178BBD` |
| `research/projected_trees_v5/novelty/THEOREM_TO_THEOREM_MATRIX.md` | `13435E2F684624DDD8EB3C6AECA5DBD31045409801144BC3D9387573B09B8AFC` |

## Verification command

From the repository root, recompute each value with:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath <relative-path>
```

The deterministic repository gate is:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_projected_trees_v5_review_manifest.ps1
```

The reviewer should record the checked date, the exact manifest used, and any
file whose hash differs before issuing a verdict.

## Status

This snapshot remains an internal draft. The theorem registry continues to
record `PENDING_HUMAN_REVIEW`, and all novelty fields remain
`NOVELTY_NOT_ESTABLISHED`.
