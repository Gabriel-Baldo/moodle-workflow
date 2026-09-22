#!/usr/bin/env python3
"""CLI workflow para moodle-workflow (pipe draft → approve + conhecimento + imagens)."""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from moodle_client import MoodleClient, get_env, extract_requirements, generate_content
from generator import generate_with_fallback, assignment_prompt
from formatter import format_pdf, format_docx, merge_pdfs, split_pdf
from slides import presentation_from_markdown
from spreadsheets import spreadsheet_from_markdown
from code_files import code_from_markdown
import drafts as draft_store
import knowledge as knowledge_store


def _render(fmt: str, content: str, out_path: Path):
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
        # sync conhecimento best-effort
        seen: dict[int, str] = {}
        for a in assignments:
            cid = a.get("_course_id")
            if cid and cid not in seen:
                seen[cid] = a.get("_course_name", f"curso_{cid}")
        for cid, cname in seen.items():
            try:
                contents = await client.get_course_contents(cid)
                files = knowledge_store.sync_course(contents, cname, cid, env["OUTPUT_DIR"])
                print(f"  [conhecimento] curso {cid}: {len(files)} .md atualizados")
            except Exception as e:
                print(f"  [conhecimento] curso {cid}: erro {e}")
    finally:
        await client.close()


async def cmd_generate(assignment_id: int, fmt: str, output: str | None):
    import uuid
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
        fallback = generate_content(reqs)
        content, source = await generate_with_fallback(
            assignment_prompt(reqs["title"], reqs.get("summary", ""), reqs.get("topics", []), fmt),
            fallback,
            api_key=env.get("OPENROUTER_API_KEY", ""),
            model=env.get("OPENROUTER_MODEL", ""),
            institution=env.get("INSTITUTION_NAME", ""),
        )
        print(f"fonte do conteúdo: {source}")
        _, drafts_dir, _ = draft_store._dirs(env["OUTPUT_DIR"])
        if output:
            out_path = Path(output).expanduser()
        else:
            safe = assignment["name"].replace(" ", "_").replace("/", "_")[:50]
            out_path = drafts_dir / f"{safe}.{fmt}"
        _render(fmt, content, out_path)
        draft_id = f"{assignment_id}_{uuid.uuid4().hex[:6]}"
        draft_store.register_draft(
            env["OUTPUT_DIR"], draft_id, assignment_id,
            assignment["name"], str(out_path), fmt,
        )
        print(f"Rascunho {draft_id} aguardando validação: {out_path}")
        print(f"Aprove com: python3 scripts/workflow.py --approve {draft_id}")
    finally:
        await client.close()


async def cmd_approve(draft_id: str, submit: bool):
    env = get_env()
    try:
        entry = draft_store.approve_draft(env["OUTPUT_DIR"], draft_id)
    except KeyError:
        print(f"Draft {draft_id} não encontrado.")
        return
    print(f"Aprovado: {entry.get('final_path')}")
    if submit:
        client = MoodleClient(env["MOODLE_URL"], env["MOODLE_TOKEN"])
        try:
            try:
                final_path = entry.get("final_path", "")
                if final_path and Path(final_path).exists():
                    saved = await client.save_submission_with_file(entry["assignment_id"], final_path)
                    print(f"arquivo anexado: {final_path}")
                else:
                    saved = await client.save_submission(entry["assignment_id"])
                print(f"save_submission: {saved}")
                submitted = await client.submit_for_grading(entry["assignment_id"])
                print(f"submit_for_grading: {submitted}")
            except Exception as e:
                print(f"Falha ao submeter ({e}). Faça upload manual de {entry.get('final_path')}")
        finally:
            await client.close()


async def cmd_merge_pdfs(pdf_paths: list[str], output: str):
    result = merge_pdfs(pdf_paths, output)
    print(f"PDFs mergeados: {result}")


async def cmd_split_pdf(pdf_path: str, output_dir: str):
    results = split_pdf(pdf_path, output_dir)
    print(f"PDF dividido em {len(results)} páginas: {results}")


async def cmd_sync_knowledge(course_id: int | None):
    env = get_env()
    client = MoodleClient(env["MOODLE_URL"], env["MOODLE_TOKEN"])
    try:
        if course_id is not None:
            contents = await client.get_course_contents(course_id)
            files = knowledge_store.sync_course(contents, f"curso_{course_id}", course_id, env["OUTPUT_DIR"])
            print(f"Sincronizados {len(files)} .md")
        else:
            courses = await client.list_courses()
            for c in courses:
                try:
                    contents = await client.get_course_contents(c["id"])
                    files = knowledge_store.sync_course(contents, c["fullname"], c["id"], env["OUTPUT_DIR"])
                    print(f"[{c['id']}] {len(files)} .md")
                except Exception as e:
                    print(f"[{c['id']}] erro: {e}")
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="Moodle Workflow CLI")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--assignment-id", type=int)
    parser.add_argument("--format", choices=["pdf", "docx", "pptx", "xlsx", "sql", "java", "c", "py", "js", "ts", "cpp", "md"], default="pdf")
    parser.add_argument("--output", help="Caminho de saída")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--merge-pdfs", action="store_true")
    parser.add_argument("--pdfs", nargs="+")
    parser.add_argument("--split-pdf", action="store_true")
    parser.add_argument("--pdf-path", help="Caminho do PDF")
    parser.add_argument("--output-dir", help="Dir de saída")
    parser.add_argument("--drafts", action="store_true", help="Lista rascunhos pendentes")
    parser.add_argument("--approve", metavar="DRAFT_ID", help="Aprova rascunho (e submete)")
    parser.add_argument("--no-submit", action="store_true", help="Aprova sem submeter no Moodle")
    parser.add_argument("--reject", metavar="DRAFT_ID", help="Rejeita rascunho")
    parser.add_argument("--motivo", default="", help="Motivo da rejeição")
    parser.add_argument("--sync-knowledge", action="store_true", help="Sincroniza .md por módulo")
    parser.add_argument("--course-id", type=int, help="Curso alvo")

    args = parser.parse_args()
    env = get_env()

    if args.list:
        await cmd_list()
    elif args.generate and args.assignment_id:
        await cmd_generate(args.assignment_id, args.format, args.output)
    elif args.merge_pdfs and args.pdfs:
        await cmd_merge_pdfs(args.pdfs, args.output or "merged.pdf")
    elif args.split_pdf and args.pdf_path:
        await cmd_split_pdf(args.pdf_path, args.output_dir or "./pages")
    elif args.drafts:
        for d in draft_store.list_drafts(env["OUTPUT_DIR"]):
            print(f"  [{d['draft_id']}] {d['assignment_name']} ({d['status']}) → {d['draft_path']}")
    elif args.approve:
        await cmd_approve(args.approve, submit=not args.no_submit)
    elif args.reject:
        try:
            e = draft_store.reject_draft(env["OUTPUT_DIR"], args.reject, args.motivo)
            print(f"Rejeitado: {e['draft_id']}")
        except KeyError:
            print(f"Draft {args.reject} não encontrado.")
    elif args.sync_knowledge:
        await cmd_sync_knowledge(args.course_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
