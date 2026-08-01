# Legacy A-N run dedup report

- Unique run names found: 19 (8 from the txt log, 18 directories on disk, overlap 7).
- Unique dedup groups (script_sha256, config_fingerprint, seed, dtype, checkpoint_sha256, audit_state_fingerprint): 19.

## Groups

### script=8d275fdbae84... seed=3 dtype=float32
members: REPRO_BOOTSTRAP_FROM_POLISH_R6

### script=UNKNOWN_SCRI... seed=None dtype=None
members: BLACKWELL_ASSOC_PASS_900_R6_FASTLOG

### script=UNKNOWN_SCRI... seed=3 dtype=float32
members: BLACKWELL_ULTRA_ASSOC_PASS_900_R6

### script=UNKNOWN_SCRI... seed=3 dtype=float64
members: BLACKWELL_ULTRA_FLOAT64_CERT_FROM_POLISH_R6

### script=UNKNOWN_SCRI... seed=4 dtype=float32
members: BLACKWELL_ULTRA_JM_PHASE_FROM_POLISH_R6

### script=UNKNOWN_SCRI... seed=3 dtype=float32
members: BLACKWELL_ULTRA_POLISH_ADFL_FROM_ASSOC_R6

### script=UNKNOWN_SCRI... seed=None dtype=None
members: REPRO_TENSOR_EXPLICIT_JM_R6

### script=UNKNOWN_SCRI... seed=0 dtype=float32
members: master_audit_A_to_N_v17_RTXPRO5000_CLOSURE_300_R6

### script=UNKNOWN_SCRI... seed=1 dtype=float32
members: master_audit_A_to_N_v17_RTXPRO5000_CLOSURE_600_R6

### script=UNKNOWN_SCRI... seed=0 dtype=float32
members: master_audit_A_to_N_v17_RTXPRO5000_ULTRAFAST_120

### script=UNKNOWN_SCRI... seed=None dtype=None
members: master_audit_A_to_N_v17_RTXPRO5000_closure_gji_300

### script=bb26ad3add48... seed=3 dtype=float64
members: REPRO_FLOAT64_CERT_FROM_BALANCED_3000

### script=bb26ad3add48... seed=3 dtype=float64
members: REPRO_FLOAT64_CERT_FROM_CONT_3200

### script=bb26ad3add48... seed=3 dtype=float64
members: REPRO_FLOAT64_CERT_FROM_JM_R6_2400

### script=bb26ad3add48... seed=3 dtype=float64
members: REPRO_FLOAT64_CERT_FROM_MICROPOLISH_3400

### script=bb26ad3add48... seed=3 dtype=float32
members: REPRO_TENSOR_EXPLICIT_JM_R6_BALANCED_3000

### script=bb26ad3add48... seed=3 dtype=float32
members: REPRO_TENSOR_EXPLICIT_JM_R6_BALANCED_MICROPOLISH_3400

### script=bb26ad3add48... seed=3 dtype=float32
members: REPRO_TENSOR_EXPLICIT_JM_R6_CONT_3200

### script=bb26ad3add48... seed=3 dtype=float32
members: REPRO_TENSOR_EXPLICIT_JM_R6_FIX_2400

## Cross-cutting findings
- Distinct seeds observed across all runs with a parsed config: [0, 1, 3, 4]
- Distinct reported script_sha256 values: 2 (['8d275fdbae84f2330aed8758539f71d29b454c2f6b00aef2ab4f5b25efeb70ba', 'bb26ad3add48083a788521db2a800a61323c5c078c1ebf3ed2aa00c6953951e8'])
- Current repo copy of the legacy script hashes to bb26ad3add48083a...; compare against reported script_sha256 values above to check whether the script in the repository today matches what actually produced the historical runs.
