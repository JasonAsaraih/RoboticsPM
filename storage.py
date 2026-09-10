"""Human-readable JSON persistence."""
import json
from pathlib import Path
from models import Project, Task

def save_project(project: Project, path):
    project.roll_up_dates(); project.validate()
    data = {"format_version": 1, "name": project.name, "engineers": sorted(set(project.engineers)),
            "tasks": [task.to_dict() for task in project.tasks]}
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def load_project(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format_version", 1) != 1: raise ValueError("Unsupported project format")
    project = Project(data.get("name", "Robotics Master Schedule"),
                      [Task.from_dict(item) for item in data.get("tasks", [])], list(data.get("engineers", [])))
    project.validate(); project.roll_up_dates()
    return project
