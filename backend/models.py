from dataclasses import dataclass, field
from typing import Any


@dataclass
class Assignment:
    id: int
    name: str
    course_id: int
    course_name: str
    duedate: str | None = None
    intro: str = ""
    format: str = "pdf"


@dataclass
class WorkflowResult:
    assignment_id: int
    assignment_name: str
    output_path: str
    format: str
    status: str  # generated | submitted | error
    message: str = ""