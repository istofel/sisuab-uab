#!/usr/bin/env bash
set -euo pipefail
fail() { echo "Erro: $*" >&2; exit 1; }

wait_ready() {
  local label="$1" attempts="$2" attempt
  shift 2
  for ((attempt = 0; attempt < attempts; attempt++)); do
    if "$@"; then return; fi
    sleep 2
  done
  fail "$label não ficou disponível. Confira a instalação e tente novamente."
}

docker_ready() { docker info >/dev/null 2>&1; }

ensure_docker() {
  command -v docker >/dev/null 2>&1 || fail "Instale o Docker com Compose antes de iniciar."
  if ! docker_ready; then
    echo "Iniciando Docker..."
    if ! docker desktop start --detach >/dev/null 2>&1; then
      if [[ "$(uname -s)" == Darwin ]]; then
        open -a Docker || fail "Não foi possível abrir o Docker Desktop."
      elif command -v systemctl >/dev/null 2>&1; then
        if [[ "$(docker context show)" == desktop-linux ]]; then
          systemctl --user start docker-desktop || fail "Não foi possível iniciar o Docker Desktop."
        elif [[ $EUID -eq 0 ]]; then
          systemctl start docker || fail "Não foi possível iniciar o serviço Docker."
        else
          echo "O Linux pode pedir sua senha para iniciar o serviço Docker."
          sudo systemctl start docker || fail "Não foi possível iniciar o serviço Docker."
        fi
      else
        fail "Não foi possível iniciar o Docker automaticamente neste sistema."
      fi
    fi
    wait_ready Docker 60 docker_ready
  fi
  docker compose version >/dev/null 2>&1 || fail "Instale o plugin Docker Compose."
}

ollama_ready() { curl -fsS --noproxy '*' --max-time 2 "$OLLAMA_BASE_URL/api/version" >/dev/null 2>&1; }

ensure_ollama() {
  command -v curl >/dev/null 2>&1 || fail "Instale curl para verificar o Ollama."
  if [[ ! "$OLLAMA_BASE_URL" =~ ^http://(localhost|127\.0\.0\.1|\[::1\]):([0-9]{1,5})$ ]]; then
    fail "OLLAMA_BASE_URL deve apontar para localhost ou 127.0.0.1, com a porta."
  fi
  local port=$((10#${BASH_REMATCH[2]}))
  ((port > 0 && port <= 65535)) || fail "Porta do Ollama inválida."
  if ollama_ready; then return; fi
  echo "Iniciando Ollama..."
  if command -v ollama >/dev/null 2>&1; then
    OLLAMA_HOST="${OLLAMA_BASE_URL#http://}" nohup ollama serve >/dev/null 2>&1 &
  elif [[ "$(uname -s)" == Darwin ]]; then
    open -g -a Ollama || fail "Instale o Ollama: https://ollama.com/download"
  else
    fail "Instale o Ollama: https://ollama.com/download"
  fi
  wait_ready Ollama 30 ollama_ready
}

read_environment() {
  [[ -f .env ]] || cp .env.example .env
  local key value
  while IFS='=' read -r key value || [[ -n "$key" ]]; do
    case "$key" in
      APP_PORT|OLLAMA_BASE_URL|OLLAMA_DOCKER_URL)
        value="${value%$'\r'}"
        value="${value#\"}"; value="${value%\"}"
        value="${value#\'}"; value="${value%\'}"
        export "$key=$value"
        ;;
    esac
  done < .env
  export APP_PORT="${APP_PORT:-8501}" OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
  OLLAMA_BASE_URL="${OLLAMA_BASE_URL%/}"
}

main() {
  cd "$(dirname "${BASH_SOURCE[0]}")"
  read_environment
  ensure_docker
  if [[ "$(uname -s)" == Linux || "${OLLAMA_DOCKER_URL:-}" == http://ollama:11434 ]]; then
    export OLLAMA_DOCKER_URL=http://ollama:11434
    docker compose --profile ollama up -d ollama
    wait_ready Ollama 60 docker compose exec -T ollama ollama list
  else
    ensure_ollama
  fi
  docker compose up -d --build app
  echo "Aplicação disponível em http://127.0.0.1:$APP_PORT"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
