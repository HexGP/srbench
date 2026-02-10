#!/usr/bin/env bash
# Recreate z_codes with DSR, AI-Feynman, and BSR repos.
# Run from project root: bash srbench/.run/recreate_z_file.sh

set -e
ZFILE="/raid/hussein/project/srbench/z_codes"
mkdir -p "$ZFILE"
cd "$ZFILE"

if [[ ! -d "$ZFILE/DSR" ]]; then
  echo "Cloning DSO (Deep Symbolic Optimization) into $ZFILE/DSR ..."
  git clone --depth 1 https://github.com/dso-org/deep-symbolic-optimization.git DSR
else
  echo "DSR already exists, skipping."
fi

if [[ ! -d "$ZFILE/AI-Feynman" ]]; then
  echo "Cloning AI-Feynman into $ZFILE/AI-Feynman ..."
  git clone --depth 1 https://github.com/SJ001/AI-Feynman.git AI-Feynman
else
  echo "AI-Feynman already exists, skipping."
fi

if [[ ! -d "$ZFILE/BSR" ]]; then
  echo "Cloning MCMC-SymReg (BSR) into $ZFILE/BSR ..."
  git clone --depth 1 https://github.com/ying531/MCMC-SymReg.git BSR
else
  echo "BSR already exists, skipping."
fi

echo "Done. Contents of $ZFILE:"
ls -la "$ZFILE"
