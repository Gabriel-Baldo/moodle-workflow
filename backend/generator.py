import os
import httpx


class ContentGenerator:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def generate(self, prompt: str) -> str:
        """Generate content using OpenRouter API."""
        if not self.api_key:
            return f"[SEM CHAVE IA] Prompt recebido:\n\n{prompt}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/moodle-workflow",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Você é um assistente acadêmico da UTFPR. Responda em português brasileiro, de forma clara e objetiva. Inclua código comentado quando aplicável."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 4096,
            "temperature": 0.3,
        }
        r = await self._client.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


async def generate_with_fallback(
    prompt: str, fallback: str, api_key: str = "", model: str = ""
) -> tuple[str, str]:
    """Gera via IA; em caso de erro/sem chave retorna fallback.

    Retorna (conteúdo, fonte) onde fonte ∈ {"ai", "template", "template-fallback"}.
    """
    if not api_key:
        return fallback, "template"
    gen = ContentGenerator(api_key, model)
    try:
        return await gen.generate(prompt), "ai"
    except Exception as e:
        return fallback + f"\n\n> Aviso: IA indisponível ({e}). Usado template local.", "template-fallback"
    finally:
        await gen.close()


def assignment_prompt(title: str, summary: str, topics: list[str], fmt: str) -> str:
    topicos = "\n".join(f"- {t}" for t in topics) if topics else "(não identificados — estruture você)"
    return f"""Gere o trabalho acadêmico COMPLETO em Markdown (sem placeholder, texto final):

Título: {title}
Descrição do professor: {summary}
Tópicos/critérios identificados:
{topicos}
Formato de entrega: {fmt}

Estrutura obrigatória:
1. # Título + linha de integrantes como "[Integrantes: ...]" (placeholder)
2. ## Introdução
3. ## Desenvolvimento (uma subseção por tópico)
4. ## Conclusão
5. ## Referências (5+ entradas ABNT plausíveis)

Regras:
- Português brasileiro, tom acadêmico, conteúdo pronto para entrega.
- Se o trabalho pedir imagem/ilustração, insira no local o marcador [IMAGE: descrição detalhada em inglês].
- Se um diagrama/mapa mental ajudar, insira um bloco ```mermaid válido.
"""


def study_prompt(scope: str, cached_excerpt: str) -> str:
    return f"""Gere um RESUMO DE ESTUDO completo em Markdown (texto final, sem placeholder):

Escopo: {scope}
Material base do Moodle (cache):
---
{cached_excerpt[:8000]}
---

Estrutura: # título, ## Conceitos-chave (bullets), ## Explicação por conceito,
## Exemplos, ## Resumo final de 5 linhas.
Feche com um bloco ```mermaid mindmap do escopo e, se houver conceito visual,
um marcador [IMAGE: descrição em inglês]."""