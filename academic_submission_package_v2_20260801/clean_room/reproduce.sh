#!/usr/bin/env bash
# Executed inside the clean-room container (see Containerfile). Writes
# everything to /out, which the host mounts to clean_room/reproduction_run/.
set -uo pipefail

OUT=/out
mkdir -p "$OUT"

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$OUT/commands.log"; }

{
  echo "=== environment ==="
  python3 --version
  pip freeze
  uname -a
} > "$OUT/environment.json.txt" 2>&1
python3 -c "
import json, platform, sys
info = {
    'python_version': sys.version,
    'platform': platform.platform(),
    'processor': platform.processor(),
}
json.dump(info, open('$OUT/environment.json', 'w'), indent=2)
"

FAIL=0

log "Running core test suite (tests/)..."
python3 -m pytest tests -q > "$OUT/test_report_core.txt" 2>&1
CORE_STATUS=$?
tail -5 "$OUT/test_report_core.txt" | tee -a "$OUT/commands.log"
[ $CORE_STATUS -ne 0 ] && FAIL=1

log "Running spectral test suite (spectral/certification_v18/tests)..."
python3 -m pytest spectral/certification_v18/tests -q > "$OUT/test_report_spectral.txt" 2>&1
SPECTRAL_STATUS=$?
tail -5 "$OUT/test_report_spectral.txt" | tee -a "$OUT/commands.log"
[ $SPECTRAL_STATUS -ne 0 ] && FAIL=1

log "Running adaptive_tensor_network application test suite..."
python3 -m pytest applications/adaptive_tensor_network/tests -q > "$OUT/test_report_ai_app.txt" 2>&1
AI_STATUS=$?
tail -5 "$OUT/test_report_ai_app.txt" | tee -a "$OUT/commands.log"
[ $AI_STATUS -ne 0 ] && FAIL=1

log "Running M1 GJI symbolic verification..."
python3 scripts/math_closure_m1_gji_symbolic.py > "$OUT/m1_gji_output.json" 2>"$OUT/m1_gji_stderr.txt"
M1_STATUS=$?
[ $M1_STATUS -ne 0 ] && FAIL=1

log "Running M2 k=2 exact closed-form verification..."
python3 research/math_closure/k2/exact_examples/chain_gated_rotation_eta_squared.py > "$OUT/m2_output.txt" 2>&1
M2_STATUS=$?
[ $M2_STATUS -ne 0 ] && FAIL=1

log "Running M3 k=3 exact closed-form verification..."
python3 research/math_closure/k3/certificates/chain_and_branching_closed_forms.py > "$OUT/m3_output.txt" 2>&1
M3_STATUS=$?
[ $M3_STATUS -ne 0 ] && FAIL=1

log "Running M6 verified Markov construction example..."
python3 research/math_closure/markov/examples/finite_sinusoidal_kernel.py > "$OUT/m6_output.txt" 2>&1
M6_STATUS=$?
[ $M6_STATUS -ne 0 ] && FAIL=1

log "Re-running the Level 1 AI campaign (fresh, independent execution)..."
python3 applications/adaptive_tensor_network/experiments/run_level1_campaign.py > "$OUT/level1_rerun.log" 2>&1
LEVEL1_STATUS=$?
[ $LEVEL1_STATUS -ne 0 ] && FAIL=1
cp applications/adaptive_tensor_network/results/level1_raw.json "$OUT/level1_raw_clean_room.json" 2>/dev/null

log "Comparing clean-room Level 1 output hash against the host-committed raw file..."
python3 -c "
import hashlib, json, sys
clean_room = open('$OUT/level1_raw_clean_room.json', 'rb').read()
committed = open('applications/adaptive_tensor_network/results/level1_raw.json', 'rb').read()
clean_hash = hashlib.sha256(clean_room).hexdigest()
committed_hash = hashlib.sha256(committed).hexdigest()
result = {
    'clean_room_sha256': clean_hash,
    'committed_sha256': committed_hash,
    'byte_identical': clean_hash == committed_hash,
}
json.dump(result, open('$OUT/hash_comparison.json', 'w'), indent=2)
print(json.dumps(result, indent=2))
" | tee -a "$OUT/commands.log"

log "Verifying academic_submission_package checksums..."
python3 -c "
import hashlib, json
from pathlib import Path

pkg = Path('academic_submission_package')
recorded = {}
checksums_file = pkg / 'checksums.sha256'
if checksums_file.exists():
    for line in checksums_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            recorded[parts[1].strip().lstrip('*')] = parts[0]

mismatches = []
checked = 0
for rel_path, expected_hash in recorded.items():
    full_path = pkg / rel_path if not rel_path.startswith('academic_submission_package') else Path(rel_path)
    candidates = [pkg / rel_path, Path(rel_path)]
    found = next((c for c in candidates if c.exists()), None)
    if found is None:
        mismatches.append({'path': rel_path, 'issue': 'file not found'})
        continue
    actual = hashlib.sha256(found.read_bytes()).hexdigest()
    checked += 1
    if actual != expected_hash:
        mismatches.append({'path': rel_path, 'expected': expected_hash, 'actual': actual})

result = {'checksums_recorded': len(recorded), 'checked': checked, 'mismatches': mismatches}
json.dump(result, open('$OUT/checksum_verification.json', 'w'), indent=2)
print(json.dumps(result, indent=2))
" | tee -a "$OUT/commands.log"

log "Writing final reproduction report..."
python3 -c "
import json
report = {
    'core_tests_exit_code': $CORE_STATUS,
    'spectral_tests_exit_code': $SPECTRAL_STATUS,
    'ai_app_tests_exit_code': $AI_STATUS,
    'm1_gji_exit_code': $M1_STATUS,
    'm2_exit_code': $M2_STATUS,
    'm3_exit_code': $M3_STATUS,
    'm6_exit_code': $M6_STATUS,
    'level1_campaign_exit_code': $LEVEL1_STATUS,
    'overall_pass': $FAIL == 0,
}
json.dump(report, open('$OUT/summary.json', 'w'), indent=2)
print(json.dumps(report, indent=2))
"

exit $FAIL
