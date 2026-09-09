#!/usr/bin/env bash
set -e

echo "=== Moodle Workflow — Setup ==="
echo ""

# Install dependencies
echo "[1/3] Instalando dependências..."
pip3 install -q httpx python-docx weasyprint fastapi uvicorn mcp pydantic
echo "  ✓ Dependências instaladas"

# Create output directory
echo "[2/3] Criando pasta de saída..."
mkdir -p ~/Documentos/moodle-workflows
echo "  ✓ ~/Documentos/moodle-workflows/"

# Check Moodle token
echo "[3/3] Verificando token Moodle..."
if [ -z "$MOODLE_TOKEN" ]; then
  echo "  ⚠ MOODLE_TOKEN não definido."
  echo "  Crie um token em: https://moodle.utfpr.edu.br/login/token.php"
  echo "  Depois: export MOODLE_TOKEN=seu_token"
fi

echo ""
echo "=== Setup completo! ==="
echo ""
echo "Para rodar o servidor:"
echo "  cd backend && python3 main.py"
echo ""
echo "Ou use a CLI:"
echo "  python3 scripts/workflow.py --list"