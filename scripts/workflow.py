#!/usr/bin/env python3
"""CLI workflow para moodle-workflow.

Uso:
    python3 scripts/workflow.py --list
    python3 scripts/workflow.py --generate --assignment-id 123 --format pdf
    python3 scripts/workflow.py --merge-pdfs --pdfs a.pdf b.pdf --output merged.pdf
    python3 scripts/workflow.py --split-pdf --pdf-path doc.pdf --output-dir ./pages
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from moodle_client import MoodleClient, get_env, extract_requirements, generate_content
from formatter import format_pdf, format_docx, merge_pdfs, split_pdf
from slides import presentation_from_markdown
from spreadsheets import spreadsheet_from_markdown
from code_files import code_from_markdown


async def cmd_list():
    env = get_env()
    client = MoodleClient(env["MOODLE_URL"], env["MOODLE_TOKEN"])
    try:
        assignments = await client.list_assignments()
        if not assignments:
            print("Nenhum assignment encontrado.")
            return
        for a in assignments:
            due = a.get("duedate", 0)
            due_str = f"vence: {datetime.fromtimestamp(due).strftime('%Y-%m-%d')}" if due else "sem prazo"
            print(f"  [{a['id']}] {a['name']} — {a.get('_course_name', '')} ({due_str})")
    finally:
        await client.close()


async def cmd_generate(assignment_id: int, fmt: str, output: str | None):
    env = get_env()
    client = MoodleClient(env["MOODLE_URL"], env["MOODLE_TOKEN"])
    try:
        assignments = await client.list_assignments()
        assignment = next((a for a in assignments if a["id"] == assignment_id), None)
        if not assignment:
            print(f"Assignment {assignment_id} não encontrado.")
            return

        reqs = extract_requirements(assignment)
        fmt = fmt if fmt else reqs.get("format", "pdf")
        content = generate_content(reqs)

        out_dir = Path(env["OUTPUT_DIR"]).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)

        if output:
            out_path = Path(output).expanduser()
        else:
            safe = assignment["name"].replace(" ", "_").replace("/", "_")[:50]
            out_path = out_dir / f"{safe}.{fmt}"

        if fmt == "pdf":
            format_pdf(content, str(out_path))
        elif fmt == "docx":
            format_docx(content, str(out_path))
        elif fmt == "pptx":
            presentation_from_markdown(content, str(out_path))
        elif fmt == "xlsx":
            spreadsheet_from_markdown(content, str(out_path))
        elif fmt in ("sql", "java", "c", "py", "js", "ts", "cpp"):
            code_from_markdown(content, fmt, str(out_path))
        else:
            out_path.write_text(content, encoding="utf-8")

        print(f"Gerado: {out_path}")
    finally:
        await client.close()


async def cmd_merge_pdfs(pdf_paths: list[str], output: str):
    result = merge_pdfs(pdf_paths, output)
    print(f"PDFs mergeados: {result}")


async def cmd_split_pdf(pdf_path: str, output_dir: str):
    results = split_pdf(pdf_path, output_dir)
    print(f"PDF dividido em {len(results)} páginas: {results}")


async def main():
    parser = argparse.ArgumentParser(description="Moodle Workflow CLI")
    parser.add_argument("--list", action="store_true", help="Listar assignments")
    parser.add_argument("--assignment-id", type=int, help="ID do assignment")
    parser.add_argument("--format", choices=["pdf", "docx", "pptx", "xlsx", "sql", "java", "c", "py", "js", "ts", "cpp", "md"], default="pdf")
    parser.add_argument("--output", help="Caminho de saída")
    parser.add_argument("--generate", action="store_true", help="Gerar trabalho")
    parser.add_argument("--merge-pdfs", action="store_true", help="Merge de PDFs")
    parser.add_argument("--pdfs", nargs="+", help="PDFs para merge")
    parser.add_argument("--split-pdf", action="store_true", help="Dividir PDF")
    parser.add_argument("--pdf-path", help="Caminho do PDF")
    parser.add_argument("--output-dir", help="Dir de saída")

    args = parser.parse_args()

    if args.list:
        await cmd_list()
    elif args.generate and args.assignment_id:
        await cmd_generate(args.assignment_id, args.format, args.output)
    elif args.merge_pdfs and args.pdfs:
        await cmd_merge_pdfs(args.pdfs, args.output or "merged.pdf")
    elif args.split_pdf and args.pdf_path:
        await cmd_split_pdf(args.pdf_path, args.output_dir or "./pages")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())