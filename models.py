"""Project domain objects, independent from the user interface."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import date
from uuid import uuid4

SECTIONS = ("Mechanical", "Electrical", "Software", "Notebook")

@dataclass(slots=True)
class Task:
    name: str
    section: str
    start_date: date
    end_date: date
    responsible_engineer: str = ""
    parent_id: str | None = None
    critical_path: bool = False
    completion: int = 0
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        if self.section not in SECTIONS: raise ValueError(f"Unknown section: {self.section}")
        if self.end_date < self.start_date: raise ValueError("End date cannot be before start date")
        if not 0 <= self.completion <= 100: raise ValueError("Completion must be between 0 and 100")

    def to_dict(self):
        result = asdict(self)
        result.update(start_date=self.start_date.isoformat(), end_date=self.end_date.isoformat())
        return result

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        value["start_date"] = date.fromisoformat(value["start_date"])
        value["end_date"] = date.fromisoformat(value["end_date"])
        return cls(**value)

@dataclass
class Project:
    name: str = "Robotics Master Schedule"
    tasks: list[Task] = field(default_factory=list)
    engineers: list[str] = field(default_factory=list)

    def task(self, task_id): return next((task for task in self.tasks if task.id == task_id), None)
    def children(self, parent_id, section=None):
        return [task for task in self.tasks if task.parent_id == parent_id and (section is None or task.section == section)]
    def descendants(self, task_id):
        found, pending = set(), [task_id]
        while pending:
            for child in self.children(pending.pop()):
                if child.id not in found: found.add(child.id); pending.append(child.id)
        return found
    def remove(self, task_id):
        removed = self.descendants(task_id) | {task_id}
        self.tasks = [task for task in self.tasks if task.id not in removed]
    def validate(self):
        ids = {task.id for task in self.tasks}
        if len(ids) != len(self.tasks): raise ValueError("Task IDs must be unique")
        for task in self.tasks:
            if task.parent_id and task.parent_id not in ids: raise ValueError(f"Missing parent for {task.name}")
            if task.parent_id and self.task(task.parent_id).section != task.section: raise ValueError("Parent and child sections must match")
            if task.id in self.descendants(task.id): raise ValueError("Task hierarchy contains a cycle")
