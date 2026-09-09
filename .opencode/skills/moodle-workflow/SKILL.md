---
name: moodle-workflow
description: Resolve trabalhos acadêmicos do Moodle UTFPR. Use quando o usuário disser "faz o trabalho", "gera o trabalho", "resolve o assignment", "trabalho de", "trabalho da disciplina", OU quando quiser gerar e formatar um trabalho acadêmico com base em um assignment do Moodle. Lê o assignment, gera conteúdo, formata em PDF ou Word conforme exigido, e salva em ~/Documentos/moodle-workflows/.
---

# Moodle Workflow — Trabalhos Acadêmicos UTFPR

## Pasta de saída
Todos os trabalhos gerados vão para `~/Documentos/moodle-workflows/`

## Estado da conversa (ctx)

Rastreie num objeto `ctx`:

```
ctx = {
  assignment_id: null,
  assignment_name: null,
  team_members: null,
  format: null,
  topic: null,
  requirements: null,
  step: "idle"
}
```

## Regra principal

**Nunca assuma info ausente.** Se falta algo, pergunte ANTES de gerar.

Padrão:
```
"Preciso saber [campo] pra prosseguir. Me passa [exemplo]?"
```

## Fluxo completo

1. **Ler assignment** → usa `list_assignments` e `get_course_contents` do MCP moodle
2. **Analisar requisitos** → extrai formato, tema, critérios, prazo
3. **Verificar ctx** → se falta info (integrantes, formato), PERGUNTE antes de gerar
4. **Gerar conteúdo** → produz o texto/código/respostas
5. **Formatar** → PDF ou Word conforme o assignment pede
6. **Salvar** → em `~/Documentos/moodle-workflows/`

## Comandos

- "quais pendentes?" → GET /checklist
- "faz o trabalho de [disciplina]" → Workflow completo
- "integrantes: fulano, ciclano" → atualiza ctx
- "formato: pdf" → atualiza ctx

## Passo a passo

### 1. Identificar o assignment
```
list_assignments(course_ids=[...])
```
Encontre o assignment pelo nome/módulo que o usuário mencionou.

### 2. Puxar contexto
```
get_course_contents(course_id=...)
download_file(file_url=..., save_path="~/Documentos/moodle-workflows/context/...")
```
Baixe slides/docs de referência.

### 3. Analisar requisitos do assignment
Olhe a descrição (`intro`) e os `name` para saber:
- Formato exigido: PDF, Word, código, relatório
- Tema/questão
- Critérios de avaliação (rubric)
- Prazo

### 4. Verificar ctx
Se `ctx.team_members` ou `ctx.format` forem null, pergunte ao usuário antes de gerar.

### 5. Gerar conteúdo
Use o modelo de IA para gerar o conteúdo baseado nos requisitos.

### 6. Formatar e salvar
Salve em `~/Documentos/moodle-workflows/`.

## Endpoints

- `GET /checklist` — lista assignments com status (submission)
- `POST /chat` — mensagem + file opcional
- `POST /generate` — gera trabalho