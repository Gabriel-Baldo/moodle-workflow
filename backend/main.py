from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.moodle_client import MoodleClient, get_env, extract_requirements, generate_content
from backend.formatter import format_pdf, format_docx
from backend.generator import ContentGenerator
from backend.models import Assignment, WorkflowResult
from pathlib import Path

app = FastAPI(title="Moodle Workflow", version="0.1.0")

env = get_env()
moodle = MoodleClient(env["MOODLE_URL"], env["MOODLE_TOKEN"])
generator = ContentGenerator(env["OPENROUTER_API_KEY"], env["OPENROUTER_MODEL"])


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


@app.post("/generate", response_model=WorkflowResult)
async def generate(req: GenerateRequest):
    assignments = await moodle.list_assignments()
    assignment = next((a for a in assignments if a["id"] == req.assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment {req.assignment_id} não encontrado")

    reqs = extract_requirements(assignment)
    reqs["format"] = req.format
    content = generate_content(reqs)

    output_dir = Path(env["OUTPUT_DIR"]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = assignment["name"].replace(" ", "_").replace("/", "_")[:50]
    ext = req.format
    output_path = output_dir / f"{safe_name}.{ext}"

    if req.format == "pdf":
        format_pdf(content, str(output_path))
    elif req.format == "docx":
        format_docx(content, str(output_path))
    else:
        output_path.write_text(content, encoding="utf-8")

    return WorkflowResult(
        assignment_id=req.assignment_id,
        assignment_name=assignment["name"],
        output_path=str(output_path),
        format=req.format,
        status="generated",
        message=f"Salvo em {output_path}",
    )


@app.get("/assignments")
async def list_assignments():
    return await moodle.list_assignments()


@app.get("/courses")
async def list_courses():
    return await moodle.list_courses()


@app.post("/shutdown")
async def shutdown():
    await moodle.close()
    await generator.close()
    return {"status": "ok"}