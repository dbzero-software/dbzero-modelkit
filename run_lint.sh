#!/bin/bash
set -e

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

echo "Running linters..."
echo "Running pylint..."
"${PYTHON_BIN}" -m pylint dbzero_modelkit tests
echo "All lint checks passed!"
