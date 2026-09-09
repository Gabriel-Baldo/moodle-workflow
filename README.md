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

## Setup rápido

```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env com seu token Moodle e chave OpenRouter
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
# Listar assignments
python3 scripts/workflow.py --list

# Gerar em qualquer formato
python3 scripts/workflow.py --generate --assignment-id 123 --format pptx
python3 scripts/workflow.py --generate --assignment-id 123 --format xlsx
python3 scripts/workflow.py --generate --assignment-id 123 --format sql

# Merge/split de PDFs
python3 scripts/workflow.py --merge-pdfs --pdfs a.pdf b.pdf --output merged.pdf
python3 scripts/workflow.py --split-pdf --pdf-path doc.pdf --output-dir ./pages
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
│   ├── formatter.py       # PDF + merge/split
│   ├── slides.py           # PPTX
│   ├── spreadsheets.py     # XLSX
│   ├── code_files.py       # SQL, Java, C, Py
│   └── models.py
├── frontend/
│   └── index.html
├── scripts/
│   ├── setup.sh
│   └── workflow.py
└── docs/
    └── usage.md
```

## License

MIT
