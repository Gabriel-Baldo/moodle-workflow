#!/usr/bin/env bash
set -e

echo "========================================="
echo "  Moodle Workflow — Setup UTFPR"
echo "========================================="
echo ""

# 1. Check dependencies
echo "[1/4] Verificando dependências..."
pip3 install -q httpx python-docx weasyprint pypdf python-pptx openpyxl mcp 2>/dev/null
echo "  ✓ Dependências OK"

# 2. Get Moodle token via Python (secure - password never in args)
echo ""
echo "[2/4] Token Moodle..."
echo "  Vai autenticar com seu RA e senha da UTFPR."
echo "  A senha nunca é salva — só o token."
echo ""

read -p "  RA (ex: a2759993): " RA

TOKEN=$(python3 - << PYEOF
import sys
sys.path.insert(0, '/home/gabriel-baldo/.pyenv/versions/3.11.14/lib/python3.11/site-packages')
from moodle_mcp.get_token import method_local
import getpass

password = getpass.getpass("  Senha: ")
token = method_local('https://moodle.utfpr.edu.br', '$RA')
if token:
    print(token)
else:
    sys.exit(1)
PYEOF
)

if [ -z "$TOKEN" ]; then
    echo "  ✗ Falha ao obter token. Verifique RA/senha."
    exit 1
fi

# 3. Save .env
echo ""
echo "[3/4] Salvando config..."
cat > ~/moodle-workflow-project/.env << EOF
MOODLE_URL=https://moodle.utfpr.edu.br
MOODLE_TOKEN=$TOKEN
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/z-ai/glm-5.2:free
OUTPUT_DIR=~/Documentos/moodle-workflows
DEFAULT_FORMAT=pdf
PORT=8765
EOF
chmod 600 ~/moodle-workflow-project/.env
echo "  ✓ .env salvo (chmod 600)"

# 4. Create output folder
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
echo "  1. Edite .env e adicione sua OPENROUTER_API_KEY"
echo "  2. Reinicie o opencode"
echo "  3. Teste: 'lista meus trabalhos'"
echo ""