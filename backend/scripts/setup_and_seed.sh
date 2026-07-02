#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Créez un fichier .env à partir de .env.example avec votre MONGODB_URI."
  exit 1
fi

# python3.11 sur cette machine n'a pas ensurepip ; utiliser python3 (Anaconda 3.13)
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python scripts/seed.py
python scripts/verify.py
