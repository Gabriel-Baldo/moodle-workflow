# Moodle Workflow — Trabalhos Acadêmicos UTFPR

> Skill: gera trabalhos a partir de assignments do Moodle.

## Pasta de saída
`~/Documentos/moodle-workflows/`

## Estado da conversa (ctx)

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

## Fluxo

1. User pede trabalho → lista assignments
2. User escolhe → lê descrição
3. Se ctx.template.team_members ou ctx.template.format faltando → PERGUNTE
4. Gera conteúdo → formata → salva
5. Confirma ao user

## Regra principal

**Nunca assuma info ausente.** Se falta algo, pergunte antes de gerar.

## Comandos
- "quais pendentes?" → GET /checklist
- "faz o trabalho X" → inicia workflow
- "integrantes: fulano, ciclano" → atualiza ctx
- "formato: pdf" → atualiza ctx

## Endpoints
- `GET /checklist` — lista com status
- `POST /chat` — message + file opcional
- `POST /generate` — gera trabalho