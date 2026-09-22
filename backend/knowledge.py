"""Cache de conhecimento por módulo/tópico em .md.

Estrutura:
  OUTPUT_DIR/conhecimento/<curso_seguro>/<modulo_seguro>.md

Cada .md guarda resumo da seção do curso para alimentar /study-summary
sem precisar re-chamar o Moodle toda vez.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path


def safe_slug(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text or "sem-nome", flags=re.UNICODE)
    text = re.sub(r"[\s]+", "_", text.strip())[:max_len]
    return text or "sem-nome"


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(text or "")).strip()


def knowledge_base_dir(output_dir: str) -> Path:
    p = Path(output_dir).expanduser() / "conhecimento"
    p.mkdir(parents=True, exist_ok=True)
    return p


def module_markdown(course_name: str, section: dict) -> str:
    """Gera .md de uma seção (módulo) do core_course_get_contents."""
    title = section.get("name", "Sem nome")
    summary = strip_html(section.get("summary", ""))
    lines = [
        f"# {course_name} — {title}",
        "",
        f"_Atualizado em: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]
    if summary:
        lines += ["## Resumo da seção", "", summary, ""]
    modules = section.get("modules", []) or []
    if modules:
        lines += ["## Materiais", ""]
        for m in modules:
            name = m.get("name", "?")
            modname = m.get("modname", "")
            desc = strip_html(m.get("description", ""))[:300]
            lines.append(f"- **{name}** ({modname})" + (f" — {desc}" if desc else ""))
            for c in (m.get("contents") or []):
                fname = c.get("filename", "")
                furl = c.get("fileurl", "")
                if fname:
                    lines.append(f"  - arquivo: {fname} | url: {furl}")
        lines.append("")
    return "\n".join(lines)


def sync_course(contents: list[dict], course_name: str, course_id: int, output_dir: str) -> list[str]:
    """Persiste um .md por seção. Retorna caminhos escritos."""
    base = knowledge_base_dir(output_dir) / f"{course_id}_{safe_slug(course_name)}"
    base.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for i, section in enumerate(contents):
        name = section.get("name") or f"secao_{i}"
        path = base / f"{i:02d}_{safe_slug(name)}.md"
        path.write_text(
            module_markdown(course_name, section), encoding="utf-8"
        )
        written.append(str(path))
    return written


def read_knowledge(course_id: int | None, output_dir: str, limit_chars: int = 20000) -> str:
    """Concatena .mds cacheados (filtro opcional por course_id)."""
    base = knowledge_base_dir(output_dir)
    if not base.exists():
        return ""
    files = sorted(base.rglob("*.md"))
    if course_id is not None:
        files = [f for f in files if f.parent.name.startswith(f"{course_id}_")]
    chunks: list[str] = []
    total = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        if total + len(text) > limit_chars:
            break
        chunks.append(f"\n\n<!-- fonte: {f} -->\n" + text)
        total += len(text)
    return "\n".join(chunks)
