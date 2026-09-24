#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python_cmd=""
for candidate in python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 &&
    "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
    python_cmd="$candidate"
    break
  fi
done
if [[ -z "$python_cmd" ]]; then
  echo "Python 3.11 ou superior é necessário para iniciar o Importador SisUAB." >&2
  exit 1
fi

if [[ ! -f .venv/bin/python ]]; then
  "$python_cmd" -m venv .venv
fi
.venv/bin/pip install -r requirements.txt
if [[ ! -f .env ]]; then
  cp .env.example .env
fi
set -a
. ./.env
set +a
exec .venv/bin/python -m streamlit run app.py --server.port "${APP_PORT:-8501}"
