# Moodle Workflow — UTFPR

Automatiza trabalhos acadêmicos do Moodle da UTFPR. Lê assignments, gera conteúdo com IA, formata em PDF/Word/Slides/Planilhas/Código e submete.

## Stack

- Python 3.11+
- FastAPI + httpx (Moodle API)
- python-docx + weasyprint + pypdf (export)
- python-pptx (slides)
- openpyxl (spreadsheets)
- OpenRouter (IA gratuita)

## Formatos suportados

| Formato | Extensão | Módulo |
|---|---|---|
| PDF | `.pdf` | weasyprint |
| Word | `.docx` | python-docx |
| Slides | `.pptx` | python-pptx |
| Planilha | `.xlsx` | openpyxl |
| SQL | `.sql` | code_files |
| Java | `.java` | code_files |
| C | `.c` | code_files |
| Python | `.py` | code_files |

## MCP — Disponível para qualquer harness

O projeto inclui `mcp.json` com todos os MCPs configurados. Use o script de setup:

```bash
# Configura para o harness que você usa
bash scripts/setup-mcp.sh
```

### Configuração manual por harness

#### Claude Code
```bash
claude mcp add moodle --env MOODLE_URL=https://moodle.utfpr.edu.br --env MOODLE_TOKEN=$MOODLE_TOKEN -- uvx mcp-moodle
claude mcp add slides -- python3 -m office_automation_mcp
claude mcp add spreadsheets -- python3 -m excel_ops_mcp
```

#### Claude Desktop
Edite `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "moodle": { "command": "mcp-moodle", "args": [], "env": { "MOODLE_URL": "https://moodle.utfpr.edu.br", "MOODLE_TOKEN": "<token>" } },
    "slides": { "command": "python3", "args": ["-m", "office_automation_mcp"] },
    "spreadsheets": { "command": "python3", "args": ["-m", "excel_ops_mcp"] },
    "filesystem": { "command": "uvx", "args": ["@modelcontextprotocol/server-filesystem", "/home/seu-usuario"] }
  }
}
```

#### Cursor
Crie `.cursor/mcp.json`:
```json
{ "mcpServers": { ... } }
```

#### Windsurf / Codex
Crie `~/.codeium/windsurf/mcp_config.json` ou `~/.codex/mcp.json`.

## Setup rápido

```bash
pip install -r requirements.txt
cp .env.example .env
python3 backend/main.py
```

## Uso

### Via opencode
Ative a skill `moodle-workflow` e diga:
- "faz o trabalho de [disciplina]"
- "lista meus trabalhos"
- "gera apresentação do assignment 123"

### Via CLI
```bash
python3 scripts/workflow.py --list
python3 scripts/workflow.py --generate --assignment-id 123 --format pptx
python3 scripts/workflow.py --merge-pdfs --pdfs a.pdf b.pdf --output merged.pdf
```

## Estrutura

```
moodle-workflow/
├── .env.example
├── mcp.json              ← config MCP universal
├── requirements.txt
├── backend/
│   ├── main.py
│   ├── moodle_client.py
│   ├── generator.py
│   ├── formatter.py
│   ├── slides.py
│   ├── spreadsheets.py
│   ├── code_files.py
│   └── models.py
├── frontend/
│   └── index.html
├── scripts/
│   ├── setup.sh
│   ├── setup-mcp.sh      ← configura harness
│   └── workflow.py
└── docs/
    └── usage.md
```

## License

MIT