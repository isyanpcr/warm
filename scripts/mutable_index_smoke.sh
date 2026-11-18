#!/usr/bin/env bash
# Builds a wheel with `maturin build --features python` into a private venv and runs
# examples/mutable_index_smoke.py against it. Usage: scripts/mutable_index_smoke.sh [n] [dim] [metric]
# Env: CARGO_TARGET_DIR (default <repo>/.target), SMOKE_VENV (default a fresh temp dir), PROFILE (default release).
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
venv=${SMOKE_VENV:-$(mktemp -d)/venv}
export CARGO_TARGET_DIR=${CARGO_TARGET_DIR:-$repo/.target}
uv venv -q --python 3.11 "$venv"
uv pip install -q --python "$venv/bin/python" maturin numpy
wheels=$(dirname "$venv")/wheels
rm -rf "$wheels"
(cd "$repo" && "$venv/bin/maturin" build --release --features python -i "$venv/bin/python" -o "$wheels")
uv pip install -q --python "$venv/bin/python" --force-reinstall --no-deps "$wheels"/*.whl
cd "$(dirname "$venv")"  # keep the repo's source tree off sys.path
"$venv/bin/python" -I "$repo/examples/mutable_index_smoke.py" "$@"
