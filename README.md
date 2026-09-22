# Moodle Workflow — UTFPR

Gera trabalhos acadêmicos do Moodle com IA: lista seus assignments, cria o conteúdo,
aguarda sua validação e submete. Também gera resumos para estudo a partir da matéria.

> **Este projeto não é publicado em lugar nenhum — cada pessoa usa localmente.**
> Você recebe a pasta do projeto (clone ou cópia), configura na sua máquina
> e usa. Nada seu sai do seu computador, exceto as chamadas ao Moodle e à IA.
>
> **Escolha sua trilha:**
> - 🟢 **[Nunca mexi com programação? Comece aqui](#-trilha-a--começando-do-zero)** —
>   passo a passo com terminal, Python e assistente, para Windows, Mac e Linux.
> - 🔵 **[Já tenho opencode, Claude ou outro assistente?](#-trilha-b--já-tenho-assistente)** —
>   versão curta, direto ao ponto.

## Como funciona (resumo)

1. Você pede: "quais trabalhos pendentes?"
2. O workflow lista tudo do Moodle e salva resumos da matéria em `.md`
3. Você escolhe um → ele gera um **rascunho** e te mostra
4. Você aprova → ele salva como final **e envia no Moodle**
5. Para estudar: "resume [matéria]" → resumo em PDF/slides a partir dos `.md`

---

## 🟢 Trilha A — Começando do zero

> Você não precisa ser da área de TI. Se sabe abrir um programa, copiar e colar
> e seguir uma receita, consegue. Reserve ~20 minutos.

### A0. O que é o "terminal"?

É aquela tela (geralmente preta) onde se digita comandos:

- **Windows:** procure **"Terminal"** ou **"PowerShell"** no menu Iniciar
- **Mac:** procure **"Terminal"** no Spotlight (`Cmd + Espaço`)
- **Linux:** `Ctrl + Alt + T`

Todo bloco de código deste guia é um comando para colar no terminal e apertar Enter.

### A1. Pegue a pasta do projeto

Copie a pasta `moodle-workflow-project` para o seu computador
(receba de quem te passou, ou `git clone` se tiver o endereço).
Depois entre nela no terminal:

```bash
cd moodle-workflow-project
```

### A2. Instale o Python

Teste primeiro:

```bash
python3 --version
```

Apareceu `Python 3.11` (ou maior)? Pule para o A3. Deu erro? Instale:

- **Windows:** baixe em [python.org/downloads](https://www.python.org/downloads/).
  ⚠️ Na instalação, marque **"Add python.exe to PATH"** antes de clicar em Install.
- **Mac:** digite `brew install python3` no terminal
  (sem `brew`? instale por [brew.sh](https://brew.sh/) ou baixe em python.org).
- **Linux (Ubuntu/Debian):** `sudo apt install python3 python3-pip`

Teste de novo com `python3 --version`. Agora instale as dependências:

```bash
pip install -r requirements.txt
```

### A3. Instale o assistente (opencode — recomendado)

O assistente conversa com você ("quais pendentes?", "faz o trabalho X").
Sem ele dá para usar, mas digitando comandos — bem menos amigável.

- **Mac e Linux:**
  ```bash
  curl -fsSL https://opencode.ai/install | bash
  ```
- **Windows:** o recomendado é o **WSL**
  (guia: [opencode.ai/docs/windows-wsl](https://opencode.ai/docs/windows-wsl)).
  Sem WSL: `choco install opencode`, `scoop install opencode`
  ou `npm install -g opencode-ai`.

Abra o assistente dentro da pasta do projeto:

```bash
cd moodle-workflow-project
opencode
```

Na primeira vez, digite `/connect` e siga a tela para ligar um provedor de IA
(para iniciantes, o **Zen** do próprio opencode é o mais simples).

### A4. Conecte o Moodle da UTFPR

No terminal, dentro da pasta do projeto:

```bash
bash scripts/setup-utfpr.sh
```

Ele pede seu **RA** e **senha** (a senha não fica salva — só o token de acesso).

> **Windows sem WSL:** se o comando `bash` não existir, rode dentro do
> **Git Bash** ([git-scm.com/downloads](https://git-scm.com/downloads)).
> Alternativa: gere o token em `https://moodle.utfpr.edu.br/login/token.php`
> e cole no arquivo `.env` (copie antes: `cp .env.example .env`).

### A5. Primeiro uso — as 4 frases mágicas

Com o assistente aberto na pasta do projeto, diga:

1. **"quais pendentes?"** → mostra trabalhos e salva resumos da matéria
2. **"faz o trabalho X"** → gera rascunho e mostra para você revisar
3. **"aprova [draft]"** → salva final **e envia no Moodle**
4. **"resume [matéria]"** → resumo para estudar (PDF ou slides)

⚠️ **Regra de ouro:** NADA é enviado sem o seu "aprova". Revise tranquilo.

### A6. (Opcional) Conteúdo real com IA

Sem chave de IA, os textos saem como modelo simples. Para conteúdo completo,
crie uma chave grátis em [openrouter.ai/keys](https://openrouter.ai/keys)
e coloque no arquivo `.env`:

```env
OPENROUTER_API_KEY=sua_chave
```

---

## 🔵 Trilha B — Já tenho assistente

Você com opencode, Claude Code/Desktop, Cursor, Windsurf, Codex ou similar:

```bash
cd moodle-workflow-project
pip install -r requirements.txt
bash scripts/setup-utfpr.sh      # RA + senha → token (só o token é salvo)
bash scripts/setup-mcp.sh        # liga os MCPs no seu harness (opcional)
```

Ative a skill **`moodle-workflow`** no seu harness e use:

| Fala | Acontece |
|---|---|
| "quais pendentes?" | Lista assignments + atualiza resumos da matéria |
| "faz o trabalho X" | Gera rascunho em `drafts/` e mostra para validar |
| "aprova [draft]" | Move p/ `final/` + envia no Moodle |
| "rejeita [draft]" | Descarta p/ refazer |
| "resume [matéria]" | Resumo p/ estudo (md/pdf/pptx + diagrama) |

Env (`.env`, a partir do `.env.example`):

```env
MOODLE_URL=https://moodle.utfpr.edu.br
MOODLE_TOKEN=
OPENROUTER_API_KEY=          # texto (free) + imagens
OPENROUTER_IMAGE_MODEL=bytedance-seed/seedream-4.5
OPENAI_API_KEY=              # fallback de imagens (opcional)
IMAGE_PROVIDERS=openrouter,openai
OUTPUT_DIR=~/Documentos/moodle-workflows
```

> Nota: a API do Claude não gera imagens (só interpreta) — a geração no backend
> é OpenRouter → OpenAI. Via harness, o próprio agente pode gerar com as ferramentas dele.

---

## Referência

### Onde ficam os arquivos

Tudo em `~/Documentos/moodle-workflows/` (muda via `OUTPUT_DIR`):

- `drafts/` — rascunhos aguardando seu aval
- `final/` — aprovados e enviados
- `conhecimento/` — um `.md` por módulo da matéria (base dos resumos)
- `resumos/`, `imagens/`, `diagramas/` — estudo e assets

### Formatos de saída

`pdf` · `docx` · `pptx` · `xlsx` · `sql` · `java` · `c` · `py` · `md`

### Via CLI (sem assistente)

```bash
python3 scripts/workflow.py --list                                        # pendentes (+ sync resumos)
python3 scripts/workflow.py --generate --assignment-id 123 --format pdf   # rascunho
python3 scripts/workflow.py --drafts                                      # ver rascunhos
python3 scripts/workflow.py --approve <draft_id>                          # aprovar + enviar
python3 scripts/workflow.py --sync-knowledge                              # atualizar resumos
```

### Via API

```bash
python3 -m uvicorn backend.main:app --port 8000
# GET  /checklist      → pendentes (+ sync de resumos)
# POST /generate       → rascunho (assignment_id, format, use_ai)
# POST /approve        → aprova + envia (draft_id, submit)
# POST /reject         → rejeita (draft_id, motivo)
# POST /study-summary  → resumo (course_id, topic, format)
# POST /generate-image / POST /generate-diagram
```

### Regras importantes

- **Nada é enviado sem seu "aprova" explícito.**
- Sem `OPENROUTER_API_KEY`, o conteúdo sai como template (placeholder).
- Imagens geradas usam créditos (OpenRouter/OpenAI); diagramas Mermaid são grátis.

### Se algo der errado

| Sintoma | O que fazer |
|---|---|
| `python3: comando não encontrado` | Refaça o passo A2 (no Windows, marcando o PATH) |
| `bash: comando não encontrado` (Windows) | Use Git Bash ou WSL |
| `token inválido` / erro de login | Refaça o passo A4, confira RA e senha |
| Texto com `[placeholder]` | Falta chave de IA — passo A6 |
| `Falha ao submeter` | Envie manualmente o arquivo de `final/` pelo site do Moodle |
| `Assignment não encontrado` | Confira o ID com `--list` ou "quais pendentes?" |

### Detalhes técnicos

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

## License

MIT
