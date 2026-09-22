from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from backend.moodle_client import MoodleClient, get_env, extract_requirements, generate_content
from backend.formatter import format_pdf, format_docx, merge_pdfs, split_pdf
from backend.slides import create_presentation, presentation_from_markdown
from backend.spreadsheets import create_spreadsheet, spreadsheet_from_markdown
from backend.code_files import generate_code, code_from_markdown, get_code_extension
from backend.models import Assignment, WorkflowResult
from backend.generator import generate_with_fallback, assignment_prompt, study_prompt
from backend import drafts as draft_store
from backend import knowledge as knowledge_store
from backend.images import (
    render_mermaid,
    mindmap_from_topics,
    generate_image_openrouter,
    generate_image,
    image_provider_chain,
    materialize_assets,
)
from pathlib import Path
import time
import uuid

app = FastAPI(title="Moodle Workflow", version="0.3.0")

env = get_env()
moodle = MoodleClient(env["MOODLE_URL"], env["MOODLE_TOKEN"])


def _output_dir() -> Path:
    p = Path(env["OUTPUT_DIR"]).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _render_to(fmt: str, content: str, output_path: Path) -> str:
    if fmt == "pdf":
        return format_pdf(content, str(output_path))
    elif fmt == "docx":
        return format_docx(content, str(output_path))
    elif fmt == "pptx":
        return presentation_from_markdown(content, str(output_path))
    elif fmt == "xlsx":
        return spreadsheet_from_markdown(content, str(output_path))
    elif fmt in ("sql", "java", "c", "py", "js", "ts", "cpp"):
        return code_from_markdown(content, fmt, str(output_path))
    else:
        output_path.write_text(content, encoding="utf-8")
        return str(output_path)


@app.get("/health")
async def health():
    try:
        info = await moodle.site_info()
        return {"status": "ok", "site": env["MOODLE_URL"], "user": info.get("username")}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


class GenerateRequest(BaseModel):
    assignment_id: int
    format: str = "pdf"
    language: str = ""
    use_ai: bool = True


class MergePdfsRequest(BaseModel):
    pdf_paths: list[str]
    output_path: str


class SplitPdfRequest(BaseModel):
    pdf_path: str
    output_dir: str


class ApproveRequest(BaseModel):
    draft_id: str
    submit: bool = True


class RejectRequest(BaseModel):
    draft_id: str
    motivo: str = ""


class SyncKnowledgeRequest(BaseModel):
    course_id: int | None = None


class StudySummaryRequest(BaseModel):
    course_id: int | None = None
    topic: str = ""
    format: str = "pdf"  # md | pdf | pptx
    with_diagram: bool = True
    with_images: bool = False
    use_ai: bool = True


class ImageRequest(BaseModel):
    prompt: str
    output_name: str | None = None
    aspect_ratio: str = "1:1"
    output_format: str = "png"
    provider: str | None = None  # openrouter | openai | None (tenta cadeia)


class DiagramRequest(BaseModel):
    mermaid: str | None = None
    title: str = ""
    topics: list[str] = []
    output_name: str | None = None


@app.post("/generate", response_model=WorkflowResult)
async def generate(req: GenerateRequest):
    """Gera trabalho em drafts/ aguardando validação (pipe)."""
    assignments = await moodle.list_assignments()
    assignment = next((a for a in assignments if a["id"] == req.assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment {req.assignment_id} não encontrado")

    reqs = extract_requirements(assignment)
    fmt = req.format if req.format else reqs.get("format", "pdf")
    fallback = generate_content(reqs)
    content, source = await generate_with_fallback(
        assignment_prompt(reqs["title"], reqs.get("summary", ""), reqs.get("topics", []), fmt),
        fallback,
        api_key=env.get("OPENROUTER_API_KEY", ""),
        model=env.get("OPENROUTER_MODEL", ""),
        institution=env.get("INSTITUTION_NAME", ""),
    ) if req.use_ai else (fallback, "template")

    base, drafts_dir, _ = draft_store._dirs(env["OUTPUT_DIR"])
    safe_name = assignment["name"].replace(" ", "_").replace("/", "_")[:50]
    draft_id = f"{req.assignment_id}_{uuid.uuid4().hex[:6]}"
    output_path = drafts_dir / f"{safe_name}.{fmt}"

    # Gera assets (mermaid/imagens) se o conteúdo pedir
    try:
        assets = await materialize_assets(content, str(drafts_dir / f"{draft_id}_assets"))
        _ = assets
    except Exception:
        pass

    _render_to(fmt, content, output_path)
    draft_store.register_draft(
        env["OUTPUT_DIR"], draft_id, req.assignment_id,
        assignment["name"], str(output_path), fmt,
    )

    return WorkflowResult(
        assignment_id=req.assignment_id,
        assignment_name=assignment["name"],
        output_path=str(output_path),
        format=fmt,
        status="draft",
        message=f"Rascunho {draft_id} [{source}] aguardando validação em {output_path}",
    )


@app.get("/drafts")
async def list_drafts():
    return {"drafts": draft_store.list_drafts(env["OUTPUT_DIR"])}


@app.post("/approve")
async def approve(req: ApproveRequest):
    try:
        entry = draft_store.approve_draft(env["OUTPUT_DIR"], req.draft_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    submission: dict = {}
    if req.submit:
        try:
            final_path = entry.get("final_path", "")
            if final_path and Path(final_path).exists():
                submission["saved"] = await moodle.save_submission_with_file(
                    entry["assignment_id"], final_path
                )
                submission["attached"] = final_path
            else:
                submission["saved"] = await moodle.save_submission(entry["assignment_id"])
            submission["submitted"] = await moodle.submit_for_grading(entry["assignment_id"])
        except Exception as e:
            submission["error"] = (
                f"{e}. Faça upload manual de {entry.get('final_path')} no Moodle."
            )
    return {"status": "approved", "draft": entry, "submission": submission}


@app.post("/reject")
async def reject(req: RejectRequest):
    try:
        entry = draft_store.reject_draft(env["OUTPUT_DIR"], req.draft_id, req.motivo)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "rejected", "draft": entry}


@app.post("/merge-pdfs", response_model=dict)
async def merge_pdfs_endpoint(req: MergePdfsRequest):
    try:
        result = merge_pdfs(req.pdf_paths, req.output_path)
        return {"status": "merged", "output": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/split-pdf", response_model=dict)
async def split_pdf_endpoint(req: SplitPdfRequest):
    try:
        results = split_pdf(req.pdf_path, req.output_dir)
        return {"status": "split", "pages": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assignments")
async def list_assignments():
    return await moodle.list_assignments()


@app.get("/courses")
async def list_courses():
    return await moodle.list_courses()


@app.post("/chat")
async def chat(message: str = Form(...), file: UploadFile = File(None)):
    file_info = None
    if file:
        content = await file.read()
        file_info = {"name": file.filename, "size": len(content), "type": file.content_type}
    response = generate_content({"title": message, "summary": message, "topics": [], "format": "text"})
    return {"response": response, "file": file_info, "message": "Processado"}


@app.get("/checklist")
async def checklist():
    """Lista assignments E atualiza cache .md por módulo (conhecimento)."""
    assignments = await moodle.list_assignments()
    result = []
    for a in assignments:
        result.append({
            "id": a["id"],
            "name": a["name"],
            "course": a.get("_course_name", ""),
            "due": a.get("_due_date", 0),
            "status": a.get("_submission_status", "none"),
        })
    # Sync conhecimento em background best-effort (não quebra a lista)
    synced: list[str] = []
    try:
        seen: dict[int, str] = {}
        for a in assignments:
            cid = a.get("_course_id")
            if cid and cid not in seen:
                seen[cid] = a.get("_course_name", f"curso_{cid}")
        for cid, cname in seen.items():
            try:
                contents = await moodle.get_course_contents(cid)
                synced += knowledge_store.sync_course(contents, cname, cid, env["OUTPUT_DIR"])
            except Exception:
                continue
    except Exception:
        pass
    return {"checklist": result, "knowledge_synced": synced}


@app.post("/sync-knowledge")
async def sync_knowledge(req: SyncKnowledgeRequest):
    if req.course_id is not None:
        courses = await moodle.list_courses()
        name = next((c["fullname"] for c in courses if c["id"] == req.course_id), f"curso_{req.course_id}")
        contents = await moodle.get_course_contents(req.course_id)
        written = knowledge_store.sync_course(contents, name, req.course_id, env["OUTPUT_DIR"])
        return {"status": "synced", "files": written}
    courses = await moodle.list_courses()
    all_written: list[str] = []
    for c in courses:
        try:
            contents = await moodle.get_course_contents(c["id"])
            all_written += knowledge_store.sync_course(contents, c["fullname"], c["id"], env["OUTPUT_DIR"])
        except Exception as e:
            all_written.append(f"ERRO {c['id']}: {e}")
    return {"status": "synced", "files": all_written}


@app.get("/knowledge")
async def get_knowledge(course_id: int | None = None):
    text = knowledge_store.read_knowledge(course_id, env["OUTPUT_DIR"])
    base = knowledge_store.knowledge_base_dir(env["OUTPUT_DIR"])
    files = [str(f) for f in sorted(base.rglob("*.md"))] if base.exists() else []
    if course_id is not None:
        files = [f for f in files if f"/{course_id}_" in f]
    return {"files": files, "combined_chars": len(text), "preview": text[:3000]}


@app.post("/study-summary")
async def study_summary(req: StudySummaryRequest):
    """Resumo para estudo a partir do cache .md (+ diagrama/imagens opcionais)."""
    cached = knowledge_store.read_knowledge(req.course_id, env["OUTPUT_DIR"])
    if not cached.strip():
        raise HTTPException(
            status_code=404,
            detail="Sem cache de conhecimento. Rode POST /sync-knowledge ou GET /checklist primeiro.",
        )
    scope = req.topic or "toda a matéria cacheada"
    fallback = generate_content({
        "title": f"Resumo de estudo — {scope}",
        "summary": f"Baseado no cache do Moodle ({len(cached)} chars). Tópico: {scope}",
        "topics": [],
        "format": "text",
    })
    ai_text, source = await generate_with_fallback(
        study_prompt(scope, cached),
        fallback,
        api_key=env.get("OPENROUTER_API_KEY", ""),
        model=env.get("OPENROUTER_MODEL", ""),
        institution=env.get("INSTITUTION_NAME", ""),
    ) if req.use_ai else (fallback, "template")
    full = f"{ai_text}\n\n---\n\n## Base do Moodle (cache)\n\n{cached[:12000]}"
    _ = source

    out_dir = _output_dir() / "resumos"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = (req.topic or f"curso_{req.course_id or 'geral'}").replace(" ", "_").replace("/", "_")[:40]
    ts = int(time.time())

    assets: dict = {"diagrams": [], "images": []}
    if req.with_diagram:
        try:
            mm = mindmap_from_topics(scope, [l.strip("- *")[:60] for l in ai_text.split("\n") if l.strip().startswith(("-", "*"))][:8] or ["Conceitos", "Exemplos", "Revisão"])
            dp = str(out_dir / f"{safe}_{ts}_mapa.png")
            render_mermaid(mm, dp)
            assets["diagrams"].append(dp)
        except Exception as e:
            assets["diagram_error"] = str(e)
    if req.with_images:
        try:
            mat = await materialize_assets(full, str(out_dir / f"{safe}_{ts}_assets"))
            assets["images"] = mat["images"]
            if mat.get("errors"):
                assets["image_errors"] = mat["errors"]
        except Exception as e:
            assets["image_error"] = str(e)

    fmt = req.format
    out_path = out_dir / f"{safe}_{ts}.{fmt if fmt != 'md' else 'md'}"
    if fmt == "md":
        out_path.write_text(full, encoding="utf-8")
    else:
        _render_to(fmt, full, out_path)

    return {
        "status": "generated",
        "output": str(out_path),
        "format": fmt,
        "assets": assets,
    }


@app.post("/generate-image")
async def generate_image_endpoint(req: ImageRequest):
    out_dir = _output_dir() / "imagens"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = req.output_name or f"img_{uuid.uuid4().hex[:8]}.{req.output_format}"
    if not name.endswith(f".{req.output_format}"):
        name += f".{req.output_format}"
    chain = [req.provider] if req.provider in ("openrouter", "openai") else None
    try:
        path, used = await generate_image(
            req.prompt, str(out_dir / name), providers=chain,
            aspect_ratio=req.aspect_ratio, output_format=req.output_format,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "generated", "output": path, "provider": used}


@app.post("/generate-diagram")
async def generate_diagram(req: DiagramRequest):
    out_dir = _output_dir() / "diagramas"
    out_dir.mkdir(parents=True, exist_ok=True)
    source = req.mermaid or mindmap_from_topics(req.title or "Mapa mental", req.topics or ["Tópico 1"])
    name = req.output_name or f"diagram_{uuid.uuid4().hex[:8]}.png"
    try:
        path = render_mermaid(source, str(out_dir / name))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "generated", "output": path, "mermaid": source}


@app.post("/shutdown")
async def shutdown():
    await moodle.close()
    return {"status": "ok"}
