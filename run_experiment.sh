#!/usr/bin/env bash

set -euo pipefail

INPUT_PATH="${1:-dados}"
SUMMARY_CSV="${2:-summary_by_n_tasks.csv}"
DETAILS_JSON="${3:-detailed_results.json}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXE="$PROJECT_ROOT/.venv/bin/python"
RUNNER="$PROJECT_ROOT/run_analysis.py"

if [[ ! -f "$PYTHON_EXE" ]]; then
    echo "Python da venv nao encontrado em: $PYTHON_EXE" >&2
    exit 1
fi

if [[ ! -f "$RUNNER" ]]; then
    echo "Script principal nao encontrado em: $RUNNER" >&2
    exit 1
fi

cd "$PROJECT_ROOT"

"$PYTHON_EXE" "$RUNNER" "$INPUT_PATH" \
    --summary-csv "$SUMMARY_CSV" \
    --details-json "$DETAILS_JSON"