---
name: moodle-workflow
description: Resolve trabalhos acadêmicos do Moodle UTFPR. Use quando o usuário disser "faz o trabalho", "gera o trabalho", "resolve o assignment", "trabalho de", "trabalho da disciplina", OU quando quiser gerar e formatar um trabalho acadêmico com base em um assignment do Moodle. Lê o assignment, gera conteúdo com IA, formata, aguarda validação em drafts/ e submete após approve. Salva resumos por módulo para estudos.
---

# Moodle Workflow — Trabalhos Acadêmicos UTFPR

## Pastas de saída (`OUTPUT_DIR`, padrão `~/Documentos/moodle-workflows/`)
- `drafts/` — rascunhos aguardando validação
- `final/` — aprovados
- `conhecimento/<curso_id>_<nome>/` — .md por módulo, atualizados a cada análise
- `resumos/`, `imagens/`, `diagramas/` — estudo e assets

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
  step: "idle"  # idle | awaiting_members | awaiting_format | generating | awaiting_approval | done
}
```

## Regra principal

**Nunca assuma info ausente.** Se falta algo, pergunte ANTES de gerar.

Padrão:
```
"Preciso saber [campo] pra prosseguir. Me passa [exemplo]?"
```

## Fluxo completo (pipe com validação)

1. **Listar** → `GET /checklist` (lista tudo + atualiza `.md` por módulo em `conhecimento/`)
2. **Analisar requisitos** → formato, tema, critérios, prazo
3. **Verificar ctx** → se falta info (integrantes, formato), PERGUNTE antes de gerar
4. **Gerar** → `POST /generate` (IA via OpenRouter com fallback p/ template; salva em `drafts/`, status `draft`)
5. **Validar** → mostre o rascunho ao usuário, aguarde aval (step `awaiting_approval`)
6. **Aprovar** → `POST /approve {draft_id}` (move p/ `final/` + anexa e submete no Moodle) ou `POST /reject {draft_id, motivo}`

## Comandos

- "quais pendentes?" → GET /checklist
- "faz o trabalho de [disciplina]" → fluxo completo acima
- "aprova [draft]" → POST /approve (com submit no Moodle)
- "rejeita [draft]" → POST /reject
- "resume [matéria] para estudar" → POST /study-summary (usa cache .md; formatos md|pdf|pptx + diagrama + imagens)
- "integrantes: fulano, ciclano" → atualiza ctx
- "formato: pdf" → atualiza ctx

## Imagens e diagramas

- Mapas mentais/diagramas → Mermaid local (`POST /generate-diagram`, grátis, PNG).
- Imagens generativas → OpenRouter (`POST /generate-image`, usa créditos).
- Convenção no markdown: `[IMAGE: descrição em inglês]` vira PNG; blocos ` ```mermaid ` viram diagramas.

## Endpoints

- `GET /checklist` — lista + sync de conhecimento
- `GET /drafts` — rascunhos pendentes
- `POST /generate` — gera rascunho (body: assignment_id, format, use_ai=true)
- `POST /approve` — aprova + submete (body: draft_id, submit=true)
- `POST /reject` — rejeita (body: draft_id, motivo)
- `POST /sync-knowledge` — atualiza .md por módulo
- `GET /knowledge` — lista cache
- `POST /study-summary` — resumo p/ estudo (course_id, topic, format, with_diagram, with_images)
- `POST /generate-image` / `POST /generate-diagram`
- `POST /chat` — mensagem + file opcional
