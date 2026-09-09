#!/usr/bin/env python3
"""CLI workflow para moodle-workflow.

Uso:
    python3 scripts/workflow.py --list
    python3 scripts/workflow.py --assignment-id 123 --format pdf
    python3 scripts/workflow.py --generate --assignment-id 123 --format docx
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from moodle_client import MoodleClient, get_env, extract_requirements, generate_content
from formatter import format_pdf, format_docx


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
        reqs["format"] = fmt
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
        else:
            out_path.write_text(content, encoding="utf-8")

        print(f"Gerado: {out_path}")
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="Moodle Workflow CLI")
    parser.add_argument("--list", action="store_true", help="Listar assignments")
    parser.add_argument("--assignment-id", type=int, help="ID do assignment")
    parser.add_argument("--format", choices=["pdf", "docx", "md"], default="pdf")
    parser.add_argument("--output", help="Caminho de saída")
    parser.add_argument("--generate", action="store_true", help="Gerar trabalho")

    args = parser.parse_args()

    if args.list:
        await cmd_list()
    elif args.generate and args.assignment_id:
        await cmd_generate(args.assignment_id, args.format, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())