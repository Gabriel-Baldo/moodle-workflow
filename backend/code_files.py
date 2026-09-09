from pathlib import Path
from typing import Any


CODE_TEMPLATES = {
    "sql": """-- Arquivo gerado pelo moodle-workflow
-- {title}

{content}
""",
    "java": """// Arquivo gerado pelo moodle-workflow
// {title}

{content}
""",
    "c": """/* Arquivo gerado pelo moodle-workflow
 * {title}
 */

{content}
""",
    "py": """# Arquivo gerado pelo moodle-workflow
# {title}

{content}
""",
}


def generate_code(
    language: str,
    title: str,
    content: str,
    output_path: str,
) -> str:
    """Generate a code file with proper header."""
    template = CODE_TEMPLATES.get(language, "{content}")
    formatted = template.format(title=title, content=content)

    out = Path(output_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(formatted, encoding="utf-8")
    return str(out)


def get_code_extension(language: str) -> str:
    """Get file extension for a programming language."""
    extensions = {
        "sql": "sql",
        "java": "java",
        "c": "c",
        "py": "py",
        "javascript": "js",
        "typescript": "ts",
        "html": "html",
        "css": "css",
        "cpp": "cpp",
        "python": "py",
    }
    return extensions.get(language.lower(), language.lower())


def code_from_markdown(markdown_text: str, language: str, output_path: str) -> str:
    """Extract code blocks from markdown and save to file."""
    import re

    pattern = r"```" + re.escape(language) + r"\s*\n(.*?)```"
    match = re.search(pattern, markdown_text, re.DOTALL)

    if match:
        code = match.group(1).strip()
    else:
        code = markdown_text.strip()

    ext = get_code_extension(language)
    if not output_path.endswith(f".{ext}"):
        output_path = f"{output_path}.{ext}"

    return generate_code(language, "Código gerado", code, output_path)