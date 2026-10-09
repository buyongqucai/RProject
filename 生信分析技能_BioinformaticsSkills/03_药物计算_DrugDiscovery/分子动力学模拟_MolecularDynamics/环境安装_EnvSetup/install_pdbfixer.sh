#!/usr/bin/env bash
set -euo pipefail
source ~/activate-md.sh
uv pip install --python "$HOME/md-venv/bin/python3" pdbfixer openmm
"$HOME/md-venv/bin/python3" -c "import pdbfixer, openmm; print('ok', openmm.__version__)"
