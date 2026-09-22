# Moodle Workflow — Trabalhos Acadêmicos UTFPR

> Skill: gera trabalhos a partir de assignments do Moodle, com pipe de validação.

## Pastas de saída (`~/Documentos/moodle-workflows/`)
- `drafts/` — rascunhos aguardando validação
- `final/` — aprovados e submetidos
- `conhecimento/` — .md por módulo, atualizados a cada análise
- `resumos/`, `imagens/`, `diagramas/`

## Estado da conversa (ctx)

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

## Fluxo

1. User pede trabalho / ver pendentes → GET /checklist (lista + sync .md)
2. User escolhe → lê descrição, extrai requisitos
3. Se team_members ou format faltando → PERGUNTE
4. POST /generate → rascunho em drafts/ (IA com fallback)
5. Mostra rascunho → aguarda aval do usuário
6. POST /approve → move p/ final/ + anexa e submete no Moodle (ou /reject p/ refazer)
7. Confirma ao user

## Regra principal

**Nunca assuma info ausente.** Se falta algo, pergunte antes de gerar.
**Nunca submeta sem approve explícito do usuário.**

## Comandos
- "quais pendentes?" → GET /checklist
- "faz o trabalho X" → inicia workflow
- "aprova [draft]" → POST /approve
- "resume [matéria]" → POST /study-summary (usa cache .md)
- "integrantes: fulano, ciclano" → atualiza ctx
- "formato: pdf" → atualiza ctx

## Endpoints
- `GET /checklist` — lista com status + sync conhecimento
- `GET /drafts` — rascunhos pendentes
- `POST /generate` — gera rascunho (assignment_id, format, use_ai)
- `POST /approve` — aprova + submete (draft_id, submit)
- `POST /reject` — rejeita (draft_id, motivo)
- `POST /study-summary` — resumo p/ estudo (usa .md cacheados)
- `POST /generate-image` / `POST /generate-diagram`
- `POST /chat` — message + file opcional
