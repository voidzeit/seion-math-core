#!/usr/bin/env bash
# Reproduces every constant in the manuscript. numpy only, under a minute.
set -e
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=============================================================="
echo " SEION / PMT reproducibility artifact"
echo " python: $(python --version 2>&1)   numpy: $(python -c 'import numpy;print(numpy.__version__)')"
echo "=============================================================="
for f in verify_k2_and_scope.py verify_k3.py verify_rebracketing.py; do
    echo
    echo "--------------------------------------------------------------"
    echo " $f"
    echo "--------------------------------------------------------------"
    python "$here/$f"
done
echo
echo "=============================================================="
echo " ALL CHECKS PASSED"
echo "=============================================================="
