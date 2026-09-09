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