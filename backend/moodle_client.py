from __future__ import annotations

import html
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def get_env() -> dict[str, str]:
    return {
        "MOODLE_URL": os.environ.get("MOODLE_URL", "").rstrip("/"),
        "MOODLE_TOKEN": os.environ.get("MOODLE_TOKEN", ""),
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY", ""),
        "OPENROUTER_MODEL": os.environ.get("OPENROUTER_MODEL", "openrouter/z-ai/glm-5.2:free"),
        "OUTPUT_DIR": os.environ.get("OUTPUT_DIR", "~/Documentos/moodle-workflows"),
        "DEFAULT_FORMAT": os.environ.get("DEFAULT_FORMAT", "pdf"),
        "IMAGE_PROVIDERS": os.environ.get("IMAGE_PROVIDERS", "openrouter,openai"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "OPENAI_IMAGE_MODEL": os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1-mini"),
    }


class MoodleClient:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def call(self, fn: str, **params: Any) -> Any:
        payload = {
            "wstoken": self.token,
            "wsfunction": fn,
            "moodlewsrestformat": "json",
            **params,
        }
        r = await self._client.post(f"{self.url}/webservice/rest/server.php", data=payload)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and data.get("exception"):
            raise RuntimeError(f"Moodle error: {data.get('message')} ({data.get('errorcode')})")
        return data

    async def site_info(self) -> dict:
        return await self.call("core_webservice_get_site_info")

    async def list_courses(self) -> list[dict]:
        me = await self.site_info()
        courses = await self.call("core_enrol_get_users_courses", userid=me["userid"])
        return [{"id": c["id"], "shortname": c.get("shortname"), "fullname": c.get("fullname")} for c in courses]

    async def list_assignments(self, course_ids: list[int] | None = None) -> list[dict]:
        if course_ids is None:
            courses = await self.list_courses()
            course_ids = [c["id"] for c in courses]
        data = await self.call("mod_assign_get_assignments", courseids=course_ids)
        assignments = []
        for course in data.get("courses", []):
            for a in course.get("assignments", []):
                a["_course_id"] = course["id"]
                a["_course_name"] = course.get("fullname", "")
                sub = (a.get("submissions") or [{}])[0]
                a["_submission_status"] = sub.get("status", "none")
                a["_submitted_time"] = sub.get("timemodified", 0)
                a["_due_date"] = a.get("duedate", 0)
                assignments.append(a)
        return assignments

    async def get_course_contents(self, course_id: int) -> list[dict]:
        return await self.call("core_course_get_contents", courseid=course_id)

    async def download_file(self, file_url: str, save_path: str) -> int:
        if "token=" not in file_url:
            sep = "&" if "?" in file_url else "?"
            file_url = f"{file_url}{sep}token={self.token}"
        dest = Path(save_path).expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = await self._client.get(file_url, follow_redirects=True)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return len(r.content)

    # -- Submissão (chamado apenas após approve do usuário) --
    async def get_submission_status(self, assignment_id: int) -> dict:
        return await self.call("mod_assign_get_submission_status", assignid=assignment_id)

    async def save_submission(self, assignment_id: int, plugindata: dict | None = None) -> dict:
        params: dict[str, Any] = {"assignmentid": assignment_id}
        if plugindata:
            params["plugindata"] = plugindata
        return await self.call("mod_assign_save_submission", **params)

    async def submit_for_grading(self, assignment_id: int, accept_terms: bool = True) -> dict:
        return await self.call(
            "mod_assign_submit_for_grading",
            assignmentid=assignment_id,
            acceptsubmissionstatement=accept_terms,
        )

    async def upload_to_draft(self, file_path: str) -> int:
        """Sobe arquivo p/ área de rascunho do usuário. Retorna o itemid."""
        dest = Path(file_path).expanduser()
        if not dest.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        url = f"{self.url}/webservice/upload.php?token={self.token}"
        with open(dest, "rb") as f:
            files = {"file": (dest.name, f, "application/octet-stream")}
            data = {"filepath": "/", "filearea": "draft", "itemid": "0"}
            r = await self._client.post(url, data=data, files=files)
        r.raise_for_status()
        payload = r.json()
        if isinstance(payload, dict) and payload.get("exception"):
            raise RuntimeError(f"Moodle upload error: {payload.get('message')}")
        return payload[0]["itemid"]

    async def save_submission_with_file(self, assignment_id: int, file_path: str) -> dict:
        """Anexa arquivo ao assignment (upload + save_submission)."""
        itemid = await self.upload_to_draft(file_path)
        return await self.save_submission(
            assignment_id, plugindata={"files_filemanager": itemid}
        )


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(text or "")).strip()


def extract_requirements(assignment: dict) -> dict:
    name = assignment.get("name", "")
    intro = strip_html(assignment.get("intro", ""))
    full_text = f"{name}\n{intro}"
    requirements = {"title": name, "summary": intro[:500], "format": "pdf", "topics": []}
    lower = full_text.lower()
    if any(w in lower for w in ["word", "docx", ".doc", "documento"]):
        requirements["format"] = "docx"
    if any(w in lower for w in ["pdf", "exportar pdf"]):
        requirements["format"] = "pdf"
    for line in intro.split("\n"):
        line = line.strip()
        if line.startswith(("•", "-", "*", "1.", "2.", "3.")):
            requirements["topics"].append(strip_html(line))
    return requirements


def generate_content(requirements: dict) -> str:
    lines = [
        f"# {requirements['title']}",
        "",
        f"**Gerado em:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Resumo", "", requirements.get("summary", "Sem descrição."), "",
        "## Desenvolvimento", "", "[Conteúdo a ser gerado pelo agente]", "",
    ]
    if requirements["topics"]:
        lines.append("## Tópicos identificados")
        for t in requirements["topics"]:
            lines.append(f"- {t}")
        lines.append("")
    return "\n".join(lines)