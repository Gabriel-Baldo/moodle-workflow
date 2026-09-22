"""Pipe de validação: drafts/ → final/ com approve/reject.

- /generate salva em drafts/ com status `draft`.
- /approve move para final/ e (opcionalmente) submete no Moodle.
- /reject marca como rejeitado (mantém arquivo p/ refazer).
- Índice leve em drafts/index.json para listar sem varrer disco.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path


def _dirs(output_dir: str) -> tuple[Path, Path, Path]:
    base = Path(output_dir).expanduser()
    drafts = base / "drafts"
    final = base / "final"
    drafts.mkdir(parents=True, exist_ok=True)
    final.mkdir(parents=True, exist_ok=True)
    return base, drafts, final


def _index_path(output_dir: str) -> Path:
    _, drafts, _ = _dirs(output_dir)
    return drafts / "index.json"


def _load_index(output_dir: str) -> dict:
    p = _index_path(output_dir)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_index(output_dir: str, data: dict) -> None:
    _index_path(output_dir).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def register_draft(
    output_dir: str,
    draft_id: str,
    assignment_id: int,
    assignment_name: str,
    draft_path: str,
    fmt: str,
) -> dict:
    idx = _load_index(output_dir)
    entry = {
        "draft_id": draft_id,
        "assignment_id": assignment_id,
        "assignment_name": assignment_name,
        "draft_path": draft_path,
        "format": fmt,
        "status": "draft",
        "created_at": int(time.time()),
    }
    idx[draft_id] = entry
    _save_index(output_dir, idx)
    return entry


def list_drafts(output_dir: str) -> list[dict]:
    return sorted(
        _load_index(output_dir).values(),
        key=lambda e: e.get("created_at", 0),
        reverse=True,
    )


def get_draft(output_dir: str, draft_id: str) -> dict | None:
    return _load_index(output_dir).get(draft_id)


def approve_draft(output_dir: str, draft_id: str) -> dict:
    _, _, final = _dirs(output_dir)
    idx = _load_index(output_dir)
    entry = idx.get(draft_id)
    if not entry:
        raise KeyError(f"Draft {draft_id} não encontrado")
    if entry.get("status") == "approved":
        return entry
    src = Path(entry["draft_path"])
    dest = final / src.name
    if src.exists():
        shutil.copy2(src, dest)
    entry["final_path"] = str(dest)
    entry["status"] = "approved"
    idx[draft_id] = entry
    _save_index(output_dir, idx)
    return entry


def reject_draft(output_dir: str, draft_id: str, motivo: str = "") -> dict:
    idx = _load_index(output_dir)
    entry = idx.get(draft_id)
    if not entry:
        raise KeyError(f"Draft {draft_id} não encontrado")
    entry["status"] = "rejected"
    if motivo:
        entry["reject_reason"] = motivo
    idx[draft_id] = entry
    _save_index(output_dir, idx)
    return entry
