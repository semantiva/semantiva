#!/usr/bin/env bash
set -euo pipefail

echo "==> Python version"
python --version

if ! command -v pdm >/dev/null 2>&1; then
  echo "PDM not found. Install with: pipx install pdm"
  exit 2
fi

echo "==> Ensuring project + docs dependencies are installed via PDM"
set +e
pdm install --dev -G docs
rc=$?
set -e

if [ $rc -ne 0 ]; then
  echo "WARN: 'docs' group not found in lockfile. Attempting recovery..."
  echo "      (Add a [tool.pdm.dev-dependencies].docs group and run 'pdm lock' to make this permanent.)"
  # Install base dev env so we have a venv, then add docs deps ad-hoc:
  pdm install --dev
  pdm run python -m pip install --upgrade pip
  pdm run python -m pip install sphinx myst-parser
fi

echo '==> Building Sphinx docs (warnings treated as errors)'
export SPHINXOPTS="-W --keep-going -n"
make -C docs clean
make -C docs html
echo '==> Done. Output: docs/_build/html'
