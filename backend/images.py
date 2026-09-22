"""Geração de imagens: Mermaid local (diagramas/mapas mentais) + OpenRouter (imagens generativas).

Recomendação implementada:
- Mapas mentais, fluxogramas, diagramas de estudo → Mermaid local via `mmdc`
  (grátis, offline, determinístico, PNG/SVG/PDF).
- Imagens generativas (ex: "mar com sol") → OpenRouter Images API
  (POST /api/v1/images, mesma OPENROUTER_API_KEY, ~$0.01-0.05/imagem).
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path


DEFAULT_IMAGE_MODEL = os.environ.get(
    "OPENROUTER_IMAGE_MODEL", "bytedance-seed/seedream-4.5"
)


# ---------------------------------------------------------------------------
# Mermaid (local, grátis)
# ---------------------------------------------------------------------------

def render_mermaid(source: str, output_path: str, fmt: str = "png", scale: float = 2.0) -> str:
    """Renderiza Mermaid → PNG/SVG/PDF via `mmdc` (pip install mmdc).

    Raises RuntimeError com instrução se mmdc não instalado.
    """
    try:
        try:
            import mermaidx as mmdc
        except ImportError:
            import mmdc
    except ImportError as e:
        raise RuntimeError(
            "mermaidx/mmdc não instalado. Rode: pip install mermaidx"
        ) from e

    out = Path(output_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    diagram = mmdc.render(source)
    if fmt == "png" or out.suffix == ".png":
        diagram.save(str(out), scale=scale)
    else:
        diagram.save(str(out))
    return str(out)


def mindmap_from_topics(title: str, topics: list[str]) -> str:
    """Gera sintaxe Mermaid mindmap a partir de título + tópicos."""
    safe_title = _mermaid_escape(title)
    lines = ["mindmap", f"  root(({safe_title}))"]
    for t in topics:
        lines.append(f"    {_mermaid_escape(t)}")
    return "\n".join(lines) + "\n"


def flowchart_from_steps(title: str, steps: list[str]) -> str:
    lines = ["graph TD"]
    for i, s in enumerate(steps):
        node = _mermaid_escape(s)[:60]
        lines.append(f'    S{i}["{node}"]')
        if i > 0:
            lines.append(f"    S{i-1} --> S{i}")
    return "\n".join(lines) + "\n"


def _mermaid_escape(text: str) -> str:
    return re.sub(r'[#"<>()]', "", text.strip())[:80]


def extract_mermaid_blocks(markdown_text: str) -> list[str]:
    """Extrai blocos ```mermaid do markdown."""
    return re.findall(r"```mermaid\s*\n(.*?)```", markdown_text, re.DOTALL)


def extract_image_prompts(markdown_text: str) -> list[str]:
    """Extrai marcadores [IMAGE: prompt] do markdown.

    Convenção: o agente/gerador insere `[IMAGE: um mar com sol ao pôr-do-sol]`
    onde o trabalho pede imagem. Esta função coleta os prompts.
    """
    return re.findall(r"\[IMAGE:\s*(.+?)\]", markdown_text)


# ---------------------------------------------------------------------------
# OpenRouter Images API (generativa, PNG/JPEG)
# ---------------------------------------------------------------------------

async def generate_image_openrouter(
    prompt: str,
    output_path: str,
    model: str | None = None,
    aspect_ratio: str = "1:1",
    output_format: str = "png",
) -> str:
    """Gera imagem via OpenRouter POST /api/v1/images. Salva PNG/JPG local.

    Retorna caminho do arquivo. Requer OPENROUTER_API_KEY.
    """
    import httpx

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY não definida — não dá pra gerar imagem.")

    model = model or DEFAULT_IMAGE_MODEL
    body = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/moodle-workflow",
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/images", json=body, headers=headers
        )
        r.raise_for_status()
        data = r.json()

    # Resposta: {"data": [{"b64_json": "..."}]} ou [{"url": "..."}]
    items = data.get("data", [])
    if not items:
        raise RuntimeError(f"OpenRouter não retornou imagem: {data}")

    out = Path(output_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    first = items[0]
    if first.get("b64_json"):
        out.write_bytes(base64.b64decode(first["b64_json"]))
    elif first.get("url"):
        url = first["url"]
        if url.startswith("data:"):
            _, b64 = url.split(",", 1)
            out.write_bytes(base64.b64decode(b64))
        else:
            import httpx as hx
            async with hx.AsyncClient(timeout=120.0) as c2:
                rr = await c2.get(url)
                rr.raise_for_status()
                out.write_bytes(rr.content)
    else:
        raise RuntimeError(f"Formato de resposta desconhecido: {list(first.keys())}")

    return str(out)


async def materialize_assets(
    markdown_text: str,
    assets_dir: str,
    image_model: str | None = None,
) -> dict:
    """Varre markdown, gera PNGs de mermaid + imagens [IMAGE:].
    Retorna {"diagrams": [...paths], "images": [...paths]}.
    Falhas individuais não abortam (retornam em errors).
    """
    dest = Path(assets_dir).expanduser()
    dest.mkdir(parents=True, exist_ok=True)

    diagrams: list[str] = []
    images: list[str] = []
    errors: list[str] = []

    for i, block in enumerate(extract_mermaid_blocks(markdown_text)):
        try:
            p = render_mermaid(block, str(dest / f"diagram_{i+1}.png"))
            diagrams.append(p)
        except Exception as e:
            errors.append(f"mermaid {i+1}: {e}")

    for i, prompt in enumerate(extract_image_prompts(markdown_text)):
        try:
            p = await generate_image_openrouter(
                prompt, str(dest / f"image_{i+1}.png"), model=image_model
            )
            images.append(p)
        except Exception as e:
            errors.append(f"imagem {i+1} ('{prompt[:40]}'): {e}")

    return {"diagrams": diagrams, "images": images, "errors": errors}
