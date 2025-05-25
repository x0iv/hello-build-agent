#!/usr/bin/env bash
# quickstart.sh — bootstrap script for hello-build-agent
set -e

echo "=============================================="
echo "   hello-build-agent • Bootstrap Script"
echo "=============================================="

# ---------- 1. Detect OS ----------
OS_RAW="$(uname -s)"
case "${OS_RAW}" in
  Linux*)   OS="Linux";;
  Darwin*)  OS="macOS";;
  CYGWIN*|MINGW*|MSYS*) OS="Windows (WSL/GitBash)";;
  *)        OS="Unknown";;
esac
echo "Detected OS : ${OS}"
echo

# ---------- 2. Check Docker ----------
if command -v docker >/dev/null 2>&1; then
  echo "Docker CLI  : ✅  $(docker --version)"
  HAS_DOCKER=true
else
  echo "Docker CLI  : ❌  not found"
  HAS_DOCKER=false
fi
echo

# ---------- 3. Check docker-compose ----------
# • plugin: `docker compose`
# • standalone binary: `docker-compose`
if docker compose version >/dev/null 2>&1; then
  echo "docker compose (plugin) : ✅  $(docker compose version | head -1)"
  HAS_COMPOSE=true
elif command -v docker-compose >/dev/null 2>&1; then
  echo "docker-compose (binary) : ✅  $(docker-compose --version)"
  HAS_COMPOSE=true
else
  echo "docker-compose          : ❌  not found"
  HAS_COMPOSE=false
fi
echo

install_help () {
  echo "─────────────────────────────────────────────────────"
  echo "Installation hints for ${OS}:"
  if [[ ${OS} == "macOS" ]]; then
    echo "  brew install --cask docker   # Docker Desktop (includes compose)"
  elif [[ ${OS} == "Linux" ]]; then
    echo "  curl -fsSL https://get.docker.com | sudo sh"
    echo "  sudo usermod -aG docker \$USER && newgrp docker"
    echo "  # docker compose v2 is included as a plugin in recent Docker versions"
  else
    echo "  Download Docker Desktop from https://www.docker.com/products/docker-desktop"
  fi
  echo "─────────────────────────────────────────────────────"
}



# ---------- 4. Offer to install Docker ----------
if [ "${HAS_DOCKER}" = false ]; then
  read -p "Docker is missing. Show installation instructions? [y/N] " ans
  if [[ ${ans,,} == "y" ]]; then
    install_help
  fi
  echo "Please install Docker, then rerun this script."
  exit 1
fi

# ---------- 5. Offer to install docker-compose ----------
if [ "${HAS_COMPOSE}" = false ]; then
  read -p "docker-compose is missing. Show installation instructions? [y/N] " ans2
  if [[ ${ans2,,} == "y" ]]; then
    install_help
  fi
  echo "Please install docker-compose, then rerun this script."
  exit 1
fi

# ---------- 6. Copy .env.example → .env ----------
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"

  # First run checkings
  for host in deb.debian.org security.debian.org archive.ubuntu.com security.ubuntu.com \
              pypi.org files.pythonhosted.org \
              registry-1.docker.io auth.docker.io production.cloudflare.docker.com; do
      echo -n "Checking outbound network connectivity (DNS → $host): "    
      if getent hosts $host >/dev/null 2>&1; then
          echo  "✅ OK"
      else
          echo -n "❌ FAILED"
      fi
  done

  echo "Run an in-container network test (busybox → deb.debian.org)"
  docker run --rm busybox sh -c \
      "wget -q --spider http://deb.debian.org && echo 'Container network: ✅ OK' || echo 'Container network: ❌ FAILED'"
  echo    # line break

  
  EDITOR_CMD=${EDITOR:-nano}
  read -p "Open .env with ${EDITOR_CMD}? [Y/n] " edit_ans
  if [[ -z "${edit_ans}" || ${edit_ans,,} == "y" ]]; then
    ${EDITOR_CMD} .env
  fi
else
  echo ".env already exists — skipping copy"
fi


# ---------- 7. Run containers ----------
echo
echo "🚢  Running \`docker compose build\` …"
docker compose build
echo "🚢  Running \`docker compose up -d --remove-orphans qdrant dind\` …"
docker compose up -d --remove-orphans qdrant dind
echo "🚢  Running example: \`docker compose run core python -m hello_build_agent.cli https://github.com/x0iv/rust-by-example\` …"
echo "Run with your repo: \`docker compose run core python -m hello_build_agent.cli <your_repo_link>\`"

docker compose run core python -m hello_build_agent.cli https://github.com/x0iv/rust-by-example

echo "Shutdown"
docker compose down
