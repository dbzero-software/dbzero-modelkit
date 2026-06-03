#!/bin/bash
set -e

export PYTHONIOENCODING=utf8

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

"${PYTHON_BIN}" -m pytest --capture=no "$@" -vv
