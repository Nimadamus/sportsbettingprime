#!/bin/bash
# Run truth_gate on each staged HTML file and report which actually FAIL (exit 1)
TG="C:/Users/Nima/truth_gate.py"
FAIL_COUNT=0
PASS_COUNT=0
FAILED_FILES=()

while IFS= read -r f; do
    if [ -f "$f" ]; then
        out=$(python "$TG" "$f" 2>&1)
        rc=$?
        if [ $rc -ne 0 ]; then
            FAIL_COUNT=$((FAIL_COUNT+1))
            FAILED_FILES+=("$f")
        else
            PASS_COUNT=$((PASS_COUNT+1))
        fi
    fi
done < <(git diff --cached --name-only --diff-filter=ACM | grep -E '\.html$')

echo ""
echo "PASS: $PASS_COUNT"
echo "FAIL: $FAIL_COUNT"
echo ""
if [ $FAIL_COUNT -gt 0 ]; then
    echo "Failed files:"
    for f in "${FAILED_FILES[@]}"; do
        echo "  - $f"
    done
fi
