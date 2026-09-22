# Guia do Iniciante — Moodle Workflow

> **Você não precisa ser da área de TI para usar este projeto.**
> Se você sabe abrir um terminal, copiar e colar comandos e seguir uma receita de bolo,
> você consegue. Este guia explica tudo do zero, passo a passo, com comandos prontos
> para **Windows, Mac e Linux**.

## O que este projeto faz (em 30 segundos)

Ele conversa com o Moodle da UTFPR por você: mostra os trabalhos pendentes,
escreve o rascunho com ajuda de IA, espera você aprovar e só então envia.
Nada é enviado sem você dizer "aprova".

## Parte 0 — O que você vai precisar

1. Um computador com **Windows 10/11, Mac ou Linux**
2. Sua conta do Moodle da UTFPR (RA + senha)
3. ~20 minutos e paciência para copiar e colar comandos

> **O que é o "terminal"?** É aquela tela preta onde se digita comandos.
> - Windows: procure por **"Terminal"** ou **"PowerShell"** no menu Iniciar
> - Mac: procure por **"Terminal"** no Spotlight (Cmd + Espaço)
> - Linux: `Ctrl + Alt + T`

## Parte 1 — Instalar o Python

O projeto roda em Python. Teste primeiro — abra o terminal e digite:

```bash
python3 --version
```

Se apareceu algo como `Python 3.11...`, pule para a Parte 2. Se deu erro:

- **Windows:** baixe em [python.org/downloads](https://www.python.org/downloads/)
  (versão 3.11 ou maior). ⚠️ Na instalação, marque a caixinha
  **"Add python.exe to PATH"** antes de clicar em Install.
- **Mac:** no terminal, digite `brew install python3`
  (se não tem o `brew`, instale por [brew.sh](https://brew.sh/) primeiro).
  Alternativa sem brew: baixe em [python.org/downloads](https://www.python.org/downloads/).
- **Linux (Ubuntu/Debian):** `sudo apt install python3 python3-pip`

Teste de novo com `python3 --version`.

## Parte 2 — Baixar este projeto

No terminal, entre na pasta onde você guarda arquivos e baixe o projeto:

```bash
git clone <URL_DO_REPOSITORIO> moodle-workflow-project
cd moodle-workflow-project
```

> Não tem `git`? Instale ([git-scm.com](https://git-scm.com/downloads))
> ou baixe o ZIP do repositório e descompacte.

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Parte 3 — Instalar o opencode (recomendado)

O **opencode** é o assistente de IA que opera o workflow conversando com você.
É o jeito mais fácil de usar (você só digita frases como "quais pendentes?").

- **Mac e Linux:**
  ```bash
  curl -fsSL https://opencode.ai/install | bash
  ```
  Alternativa no Mac: `brew install anomalyco/tap/opencode`
- **Windows:** o recomendado é usar o **WSL**
  (subsistema Linux — guia oficial: [opencode.ai/docs/windows-wsl](https://opencode.ai/docs/windows-wsl)).
  Sem WSL, instale com `choco install opencode`, `scoop install opencode`
  ou `npm install -g opencode-ai`.

Depois, abra o opencode dentro da pasta do projeto e conecte um provedor de IA:

```bash
cd moodle-workflow-project
opencode
```

Dentro dele, digite `/connect` e siga as instruções na tela
(para iniciantes, o provedor **Zen** do próprio opencode é o mais simples).
Detalhes: [opencode.ai/docs](https://opencode.ai/docs).

> **Sem opencode?** Dá para usar só pela CLI (`scripts/workflow.py --list`),
> mas você perde a conversa guiada. Recomendamos o opencode.

## Parte 4 — Conectar o Moodle da UTFPR

No terminal, dentro da pasta do projeto:

```bash
bash scripts/setup-utfpr.sh
```

Ele vai pedir seu **RA** e sua **senha** (a senha não fica salva, só o token).
Pronto — pastas criadas e `.env` configurado.

> **Windows sem WSL/Git Bash:** o comando `bash` pode não existir.
> Instale o [Git para Windows](https://git-scm.com/downloads) (vem com Git Bash)
> e rode o comando dentro do Git Bash. Alternativa: gere o token manualmente em
> `https://moodle.utfpr.edu.br/login/token.php` e cole no arquivo `.env`.

## Parte 5 — Primeiro uso (as 4 frases mágicas)

Com o opencode aberto na pasta do projeto, diga:

1. **"quais pendentes?"** → ele mostra seus trabalhos e salva resumos da matéria
2. **"faz o trabalho X"** → ele gera um rascunho e mostra para você
3. **"aprova [draft]"** → ele salva como final **e envia no Moodle**
4. **"resume [matéria]"** → resumo para estudar (PDF ou slides)

⚠️ **Regra de ouro:** ele NUNCA envia nada sem o seu "aprova". Pode revisar tranquilo.

## Se algo der errado

| Sintoma | O que fazer |
|---|---|
| `python3: comando não encontrado` | Volte à Parte 1 e reinstale marcando o PATH (Windows) |
| `bash: comando não encontrado` (Windows) | Use o Git Bash ou o WSL |
| `token inválido` / erro de login | Refaça a Parte 4, confira RA e senha |
| Saiu texto com `[placeholder]` | Falta a chave de IA — crie em [openrouter.ai/keys](https://openrouter.ai/keys) e coloque `OPENROUTER_API_KEY=` no `.env` |
| `Falha ao submeter` | Envie manualmente o arquivo da pasta `final/` pelo site do Moodle |

Nada resolveu? Abra uma issue no repositório contando seu sistema
(Windows/Mac/Linux) e colando a mensagem de erro.
