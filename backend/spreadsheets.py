from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from pathlib import Path
from typing import Any


def create_spreadsheet(
    sheets_data: list[dict],
    output_path: str,
) -> str:
    """Create an Excel spreadsheet from structured data.

    sheets_data: list of {"name": str, "headers": list[str], "rows": list[list]}
    """
    wb = Workbook()
    wb.remove(wb.active)  # type: ignore[arg-type]

    for sheet_def in sheets_data:
        ws = wb.create_sheet(title=sheet_def.get("name", "Sheet"))
        headers = sheet_def.get("headers", [])
        rows = sheet_def.get("rows", [])

        if headers:
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True, size=11)
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

        for row_idx, row_data in enumerate(rows, 2):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # Auto-width
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_length + 2, 40)

        # Add chart if data is numeric
        if rows and len(rows[0]) >= 2:
            chart = BarChart()
            chart.title = sheet_def.get("name", "Chart")
            chart.width = 15
            chart.height = 10
            data_ref = Reference(ws, min_col=1, max_col=len(headers), min_row=1, max_row=len(rows) + 1)
            chart.add_data(data_ref, titles_from_data=True)
            ws.add_chart(chart, "A" + str(len(rows) + 4))

    wb.save(output_path)
    return output_path


def spreadsheet_from_markdown(markdown_text: str, output_path: str) -> str:
    """Convert markdown tables to spreadsheet."""
    import re

    sheets_data = []
    current_sheet: dict[str, Any] | None = None

    for line in markdown_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            if current_sheet:
                sheets_data.append(current_sheet)
            current_sheet = {"name": line[3:], "headers": [], "rows": []}
        elif line.startswith("|") and current_sheet is not None:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if all(set(c) <= set("-:") for c in cells):
                continue
            if not current_sheet["headers"]:
                current_sheet["headers"] = cells
            else:
                current_sheet["rows"].append(cells)

    if current_sheet:
        sheets_data.append(current_sheet)

    return create_spreadsheet(sheets_data, output_path)