#!/usr/bin/env bash
# Launches mcp-moodle with MOODLE_URL/MOODLE_TOKEN taken from the project .env.
# mcp-moodle hangs silently (no reply to tool calls) when MOODLE_TOKEN is missing,
# so fail fast here with a clear message instead.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

read_env() {
  [ -f "$ENV_FILE" ] || return 0
  grep -E "^$1=" "$ENV_FILE" | tail -n1 | cut -d= -f2- | sed -E 's/^["'\'']//; s/["'\'']$//' | tr -d '\r'
}

: "${MOODLE_URL:=$(read_env MOODLE_URL)}"
: "${MOODLE_TOKEN:=$(read_env MOODLE_TOKEN)}"

if [ -z "$MOODLE_URL" ] || [ -z "$MOODLE_TOKEN" ]; then
  echo "mcp-moodle: MOODLE_URL/MOODLE_TOKEN ausentes (defina em $ENV_FILE ou rode scripts/setup-moodle.sh)" >&2
  exit 1
fi

BIN="${MCP_MOODLE_BIN:-$(command -v mcp-moodle || true)}"
if [ -z "$BIN" ]; then
  # harnesses often start with a PATH without pyenv shims
  for candidate in "$HOME"/.pyenv/versions/*/bin/mcp-moodle; do
    [ -x "$candidate" ] && BIN="$candidate" && break
  done
fi
if [ -z "$BIN" ]; then
  echo "mcp-moodle: binário não encontrado (pip install mcp-moodle ou defina MCP_MOODLE_BIN)" >&2
  exit 1
fi

export MOODLE_URL MOODLE_TOKEN
exec "$BIN" "$@"
