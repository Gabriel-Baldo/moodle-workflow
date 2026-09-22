#!/usr/bin/env bash
# Setup genérico para qualquer Moodle (UTFPR é só o padrão).
# Uso: bash scripts/setup-moodle.sh [--url https://seu.moodle.br]
set -e

MOODLE_URL="https://moodle.utfpr.edu.br"
if [ "$1" = "--url" ] && [ -n "$2" ]; then
  MOODLE_URL="$2"
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================="
echo "  Moodle Workflow — Setup"
echo "========================================="
echo ""

# 1. Dependências
echo "[1/4] Verificando dependências..."
pip3 install -q httpx python-docx weasyprint pypdf python-pptx openpyxl mermaidx mcp 2>/dev/null
echo "  ✓ Dependências OK"

# 2. Token via login (senha nunca é salva — só o token)
echo ""
echo "[2/4] Token Moodle..."
echo "  Moodle: $MOODLE_URL"
echo ""
read -p "  URL do Moodle (Enter = $MOODLE_URL): " CUSTOM_URL
if [ -n "$CUSTOM_URL" ]; then
  MOODLE_URL="$CUSTOM_URL"
fi
read -p "  Usuário (ex: RA, matrícula, login): " MOODLE_USER

TOKEN=$(MOODLE_URL="$MOODLE_URL" MOODLE_USER="$MOODLE_USER" python3 - <<'PYEOF'
import os, sys, getpass
try:
    from moodle_mcp.get_token import method_local
except ImportError:
    sys.exit("mcp-moodle não instalado (pip install mcp)")

password = getpass.getpass("  Senha: ")
token = method_local(os.environ["MOODLE_URL"], os.environ["MOODLE_USER"], password)
if token:
    print(token)
else:
    sys.exit(1)
PYEOF
)

if [ -z "$TOKEN" ]; then
    echo "  ✗ Falha ao obter token. Verifique URL/usuário/senha."
    exit 1
fi

# 3. Salva .env (preserva chaves de IA já existentes)
echo ""
echo "[3/4] Salvando config..."
touch "$PROJECT_DIR/.env"
chmod 600 "$PROJECT_DIR/.env"
upsert() { # upsert KEY VALUE FILE
  if grep -q "^$1=" "$3"; then
    sed -i "s|^$1=.*|$1=$2|" "$3"
  else
    printf '%s=%s\n' "$1" "$2" >> "$3"
  fi
}
upsert MOODLE_URL "$MOODLE_URL" "$PROJECT_DIR/.env"
upsert MOODLE_TOKEN "$TOKEN" "$PROJECT_DIR/.env"
grep -q "^OUTPUT_DIR=" "$PROJECT_DIR/.env" || printf '%s\n' "OUTPUT_DIR=~/Documentos/moodle-workflows" >> "$PROJECT_DIR/.env"
grep -q "^DEFAULT_FORMAT=" "$PROJECT_DIR/.env" || printf '%s\n' "DEFAULT_FORMAT=pdf" >> "$PROJECT_DIR/.env"
read -p "  Nome da instituição (Enter = UTFPR): " INSTITUTION
upsert INSTITUTION_NAME "${INSTITUTION:-UTFPR}" "$PROJECT_DIR/.env"
echo "  ✓ .env salvo (chmod 600)"

# 4. Pasta de saída
echo ""
echo "[4/4] Pasta de saída..."
mkdir -p ~/Documentos/moodle-workflows
echo "  ✓ ~/Documentos/moodle-workflows/"

echo ""
echo "========================================="
echo "  Setup completo!"
echo "========================================="
echo ""
echo "Próximos passos:"
echo "  1. (Opcional) Adicione OPENROUTER_API_KEY no .env p/ conteúdo com IA"
echo "  2. No assistente: 'quais pendentes?'"
echo ""
