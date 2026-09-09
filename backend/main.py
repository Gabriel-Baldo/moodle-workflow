from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.moodle_client import MoodleClient, get_env, extract_requirements, generate_content
from backend.formatter import format_pdf, format_docx, merge_pdfs, split_pdf
from backend.slides import create_presentation, presentation_from_markdown
from backend.spreadsheets import create_spreadsheet, spreadsheet_from_markdown
from backend.code_files import generate_code, code_from_markdown, get_code_extension
from backend.models import Assignment, WorkflowResult
from pathlib import Path

app = FastAPI(title="Moodle Workflow", version="0.2.0")

env = get_env()
moodle = MoodleClient(env["MOODLE_URL"], env["MOODLE_TOKEN"])


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


class MergePdfsRequest(BaseModel):
    pdf_paths: list[str]
    output_path: str


class SplitPdfRequest(BaseModel):
    pdf_path: str
    output_dir: str


@app.post("/generate", response_model=WorkflowResult)
async def generate(req: GenerateRequest):
    assignments = await moodle.list_assignments()
    assignment = next((a for a in assignments if a["id"] == req.assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment {req.assignment_id} não encontrado")

    reqs = extract_requirements(assignment)
    fmt = req.format if req.format else reqs.get("format", "pdf")
    content = generate_content(reqs)

    output_dir = Path(env["OUTPUT_DIR"]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = assignment["name"].replace(" ", "_").replace("/", "_")[:50]
    output_path = output_dir / f"{safe_name}.{fmt}"

    if fmt == "pdf":
        format_pdf(content, str(output_path))
    elif fmt == "docx":
        format_docx(content, str(output_path))
    elif fmt == "pptx":
        presentation_from_markdown(content, str(output_path))
    elif fmt == "xlsx":
        spreadsheet_from_markdown(content, str(output_path))
    elif fmt in ("sql", "java", "c", "py", "js", "ts", "cpp"):
        code_from_markdown(content, fmt, str(output_path))
    else:
        output_path.write_text(content, encoding="utf-8")

    return WorkflowResult(
        assignment_id=req.assignment_id,
        assignment_name=assignment["name"],
        output_path=str(output_path),
        format=fmt,
        status="generated",
        message=f"Salvo em {output_path}",
    )


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


class SubmitRequest(BaseModel):
    assignment_id: int


@app.post("/submit", response_model=WorkflowResult)
async def submit(req: SubmitRequest):
    try:
        result = await moodle.submit_assignment(req.assignment_id)
        return WorkflowResult(
            assignment_id=req.assignment_id,
            assignment_name="",
            output_path="",
            format="",
            status="submitted",
            message=f"Submetido: {result}",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=f"Submissão falhou: {e}. Token sem permissão? Salve o arquivo e suba manualmente.")