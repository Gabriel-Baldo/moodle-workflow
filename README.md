# Moodle Workflow — UTFPR

Automatiza trabalhos acadêmicos do Moodle da UTFPR. Lê assignments, gera conteúdo com IA, formata em PDF/Word e submete.

## Stack

- Python 3.11+
- FastAPI + httpx (Moodle API)
- python-docx + weasyprint (export)
- OpenRouter (IA gratuita)

## Setup rápido

```bash
# 1. Clone
git clone https://github.com/seu-usuario/moodle-workflow.git
cd moodle-workflow

# 2. Instale dependências
pip install -r requirements.txt

# 3. Configure suas credenciais
cp .env.example .env
# Edite .env com seu token Moodle e chave OpenRouter

# 4. Execute
python3 backend/main.py
```

## Uso

### Via opencode (recomendado)

Ative a skill `moodle-workflow` e diga:
- "faz o trabalho de [disciplina]"
- "lista meus trabalhos"
- "gera relatório do assignment 123"

### Via CLI

```bash
# Listar assignments
python3 scripts/workflow.py --list

# Gerar trabalho
python3 scripts/workflow.py --assignment-id 123 --format pdf

# Submeter
python3 scripts/workflow.py --submit --assignment-id 123 --file trabalho.pdf
```

## Estrutura

```
moodle-workflow/
├── .env.example
├── requirements.txt
├── backend/
│   ├── main.py
│   ├── moodle_client.py
│   ├── generator.py
│   ├── formatter.py
│   └── models.py
├── frontend/
│   ├── index.html
│   └── app.js
├── scripts/
│   ├── setup.sh
│   └── workflow.py
└── docs/
    └── usage.md
```

## License

MIT
