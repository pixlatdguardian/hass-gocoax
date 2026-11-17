#!/usr/bin/env bash
# Isolated development environment only; no running HA installation is accessed.
set -euo pipefail
test_env="$HOME/.cache/gocoax-ha-tests-20261117"
if [ ! -x "$test_env/bin/python" ]; then
  uv venv --python 3.14 "$test_env"
fi
uv pip install --python "$test_env/bin/python" 'homeassistant==2026.10.4' 'pytest-homeassistant-custom-component==0.13.375'
echo "HA_TEST_ENV_READY=$test_env"
cd "$(dirname "$0")/.."
"$test_env/bin/python" -m pytest tests -q
