#!/usr/bin/env bash
set -e

echo "=== Moodle Workflow — Configurar MCP para harness ==="
echo ""
echo "Harnesses suportados:"
echo "  1) Claude Code"
echo "  2) Claude Desktop"
echo "  3) Cursor"
echo "  4) Windsurf"
echo "  5) Codex"
echo "  6) Todos"
echo ""
read -p "Escolha: " choice

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MCP_JSON="$PROJECT_DIR/mcp.json"

case "$choice" in
  1|claude)
    CONFIG="$HOME/.claude.json"
    echo "Configurando Claude Code..."
    if [ -f "$CONFIG" ]; then
      python3 -c "
import json, sys
with open('$CONFIG') as f:
    data = json.load(f)
with open('$MCP_JSON') as f:
    mcp = json.load(f)
data['mcpServers'] = mcp.get('mcpServers', {})
with open('$CONFIG', 'w') as f:
    json.dump(data, f, indent=2)
print('Claude Code configurado!')
"
    else
      echo "Erro: $CONFIG não encontrado. Execute: claude mcp add"
    fi
    ;;
  2|desktop)
    echo "Configurando Claude Desktop..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
      CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    else
      CONFIG="$HOME/AppData/Roaming/Claude/claude_desktop_config.json"
    fi
    python3 -c "
import json
with open('$MCP_JSON') as f:
    mcp = json.load(f)
config = {'mcpServers': mcp.get('mcpServers', {})}
with open('$CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
print('Claude Desktop configurado!')
"
    ;;
  3|cursor)
    CONFIG="$HOME/.cursor/mcp.json"
    echo "Configurando Cursor..."
    python3 -c "
import json
with open('$MCP_JSON') as f:
    mcp = json.load(f)
with open('$CONFIG', 'w') as f:
    json.dump(mcp, f, indent=2)
print('Cursor configurado!')
"
    ;;
  4|windsurf)
    CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
    echo "Configurando Windsurf..."
    mkdir -p "$(dirname "$CONFIG")"
    python3 -c "
import json
with open('$MCP_JSON') as f:
    mcp = json.load(f)
with open('$CONFIG', 'w') as f:
    json.dump(mcp, f, indent=2)
print('Windsurf configurado!')
"
    ;;
  5|codex)
    CONFIG="$HOME/.codex/mcp.json"
    echo "Configurando Codex..."
    mkdir -p "$(dirname "$CONFIG")"
    python3 -c "
import json
with open('$MCP_JSON') as f:
    mcp = json.load(f)
with open('$CONFIG', 'w') as f:
    json.dump(mcp, f, indent=2)
print('Codex configurado!')
"
    ;;
  6|all)
    echo "Configurando todos..."
    for harness in claude desktop cursor windsurf codex; do
      echo "$harness"
    done
    ;;
  *)
    echo "Opção inválida"
    exit 1
    ;;
esac

echo ""
echo "=== Feito! Reinicie o harness ==="