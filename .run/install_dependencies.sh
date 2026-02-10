#!/usr/bin/env bash
# Install BSR and rebuild DSO cython extensions
# Run from srbench root: bash .run/install_dependencies.sh

set -e

# Initialize conda if needed
if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "/raid/hussein/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/raid/hussein/miniconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
    source "/opt/conda/etc/profile.d/conda.sh"
fi

echo "=========================================="
echo "Installing BSR in srbench environment"
echo "=========================================="
cd /raid/hussein/project/srbench/z_codes/BSR
eval "$(conda shell.bash hook)"
conda activate srbench
pip install -e .

echo ""
echo "=========================================="
echo "Rebuilding DSO cython extensions in dso_env"
echo "=========================================="
cd /raid/hussein/project/srbench/z_codes/DSR
conda activate dso_env
pip install -e ./dso --force-reinstall --no-deps

echo ""
echo "=========================================="
echo "Done! BSR and DSO should now work."
echo "=========================================="
