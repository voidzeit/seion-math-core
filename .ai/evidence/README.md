# Governance evidence ledger

`ledger.jsonl` is an append-only operational ledger emitted by the local
governance controls. It records audit and postflight events with authority,
commit, artifacts, and limitations. Mathematical evidence remains in
`claims/evidence_ledger.jsonl`; the two ledgers must not be conflated.
