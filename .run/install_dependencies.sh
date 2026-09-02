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
# Try both possible locations for BSR
for bsr_path in "/raid/hussein/project/srbench/z_codes/BSR" "/raid/hussein/project/z_codes/BSR"; do
    if [ -d "$bsr_path" ]; then
        cd "$bsr_path"
        eval "$(conda shell.bash hook)"
        conda activate srbench
        pip install -e .
        echo "BSR installed from: $bsr_path"
        break
    fi
done

echo ""
echo "=========================================="
echo "Rebuilding DSO cython extensions in dso_env"
echo "=========================================="
# Try both possible locations for DSR
for dsr_path in "/raid/hussein/project/srbench/z_codes/DSR" "/raid/hussein/project/z_codes/DSR"; do
    if [ -d "$dsr_path" ]; then
        cd "$dsr_path"
        eval "$(conda shell.bash hook)"
        conda activate dso_env
        pip install -e ./dso --force-reinstall --no-deps
        echo "DSO rebuilt from: $dsr_path"
        break
    fi
done

echo ""
echo "=========================================="
echo "Done! BSR and DSO should now work."
echo "=========================================="
