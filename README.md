# Moodle Workflow — UTFPR

Gera trabalhos acadêmicos do Moodle com IA: lista seus assignments, cria o conteúdo,
aguarda sua validação e submete. Também gera resumos para estudo a partir da matéria.

## Como funciona (resumo)

1. Você pede: "quais trabalhos pendentes?"
2. O workflow lista tudo do Moodle e salva resumos da matéria em `.md`
3. Você escolhe um → ele gera um **rascunho** e te mostra
4. Você aprova → ele salva como final **e envia no Moodle**
5. Para estudar: "resume [matéria]" → resumo em PDF/slides a partir dos `.md`

## Passo a passo

### 1. Instalar

```bash
pip install -r requirements.txt
```

### 2. Conectar no Moodle (UTFPR)

Automático (pede RA + senha, salva só o token):

```bash
bash scripts/setup-utfpr.sh
```

Ou manual: gere um token em `https://moodle.utfpr.edu.br/login/token.php`
e coloque no `.env`:

```bash
cp .env.example .env
# edite: MOODLE_URL, MOODLE_TOKEN
```

### 3. (Opcional) Ativar IA e imagens

Sem chave, o workflow funciona com template local. Para conteúdo real com IA:

```env
OPENROUTER_API_KEY=sua_chave        # texto + imagens (modelo free p/ texto)
OPENAI_API_KEY=sua_chave            # fallback de imagens (opcional)
```

Chave OpenRouter grátis: `https://openrouter.ai/keys`

### 4. Usar

**Via chat (opencode, com a skill `moodle-workflow`):**

| Fala | Acontece |
|---|---|
| "quais pendentes?" | Lista assignments + atualiza resumos da matéria |
| "faz o trabalho X" | Gera rascunho e te mostra para validar |
| "aprova [draft]" | Salva final + envia no Moodle |
| "resume [matéria]" | Resumo para estudo (PDF/slides) |

**Via CLI:**

```bash
python3 scripts/workflow.py --list                                        # pendentes
python3 scripts/workflow.py --generate --assignment-id 123 --format pdf   # rascunho
python3 scripts/workflow.py --drafts                                      # ver rascunhos
python3 scripts/workflow.py --approve <draft_id>                          # aprovar + enviar
python3 scripts/workflow.py --sync-knowledge                              # atualizar resumos
```

**Via API:**

```bash
python3 -m uvicorn backend.main:app --port 8000
# GET  /checklist  → pendentes (+ sync de resumos)
# POST /generate   → rascunho (assignment_id, format)
# POST /approve    → aprova + envia (draft_id)
# POST /study-summary → resumo (course_id, topic, format)
```

## Onde ficam os arquivos

Tudo em `~/Documentos/moodle-workflows/` (configurável via `OUTPUT_DIR`):

- `drafts/` — rascunhos aguardando seu aval
- `final/` — aprovados e enviados
- `conhecimento/` — um `.md` por módulo da matéria (base dos resumos)
- `resumos/`, `imagens/`, `diagramas/` — estudo e assets

## Formatos de saída

`pdf` · `docx` · `pptx` · `xlsx` · `sql` · `java` · `c` · `py` · `md`

## Regras importantes

- **Nada é enviado sem seu "aprova" explícito.**
- Sem `OPENROUTER_API_KEY`, o conteúdo sai como template (placeholder).
- Imagens geradas usam créditos (OpenRouter/OpenAI); diagramas Mermaid são grátis.

## Problemas comuns

| Erro | Causa |
|---|---|
| `Assignment não encontrado` | ID errado — confira com `--list` |
| `OPENROUTER_API_KEY não definida` | Sem chave IA — sai template; adicione a chave p/ conteúdo real |
| `Falha ao submeter` | Faça upload manual do arquivo em `final/` |
| `mermaid/mermaidx não instalado` | `pip install mermaidx` |

## Detalhes técnicos

<details>
<summary>Estrutura do projeto</summary>

```
backend/
  main.py          ← API FastAPI
  moodle_client.py ← integração Moodle (+ upload e submissão)
  generator.py     ← IA (OpenRouter) com fallback p/ template
  formatter.py     ← PDF/DOCX + merge/split
  slides.py        ← PPTX
  spreadsheets.py  ← XLSX
  code_files.py    ← .sql/.java/.c/.py...
  images.py        ← Mermaid + imagens (OpenRouter/OpenAI)
  knowledge.py     ← cache .md por módulo
  drafts.py        ← pipe drafts/ → final/
scripts/workflow.py ← CLI
```

</details>

<details>
<summary>Configurar MCP no seu harness (opcional)</summary>

```bash
bash scripts/setup-mcp.sh   # Claude Code, Desktop, Cursor, Windsurf, Codex
```

Ou manual — o `mcp.json` do projeto tem os 5 servidores
(`moodle`, `slides`, `spreadsheets`, `filesystem`, `pdf-tools`).

</details>

## License

MIT
