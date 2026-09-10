from datetime import date
import pytest
from models import Project, Task
from storage import load_project, save_project

def test_round_trip_keeps_parent_and_child_dates_independent(tmp_path):
    parent = Task("Robot", "Mechanical", date(2026, 1, 1), date(2026, 1, 1))
    one = Task("CAD", "Mechanical", date(2026, 2, 1), date(2026, 2, 4), parent_id=parent.id)
    two = Task("Build", "Mechanical", date(2026, 2, 5), date(2026, 2, 12), parent_id=parent.id)
    path = tmp_path / "schedule.json"; save_project(Project(tasks=[parent, one, two]), path); loaded = load_project(path)
    assert (loaded.task(parent.id).start_date, loaded.task(parent.id).end_date) == (date(2026, 1, 1), date(2026, 1, 1))
    assert (loaded.task(two.id).start_date, loaded.task(two.id).end_date) == (date(2026, 2, 5), date(2026, 2, 12))

def test_changing_child_dates_does_not_change_parent():
    parent = Task("Robot", "Mechanical", date(2026, 1, 1), date(2026, 1, 10))
    child = Task("CAD", "Mechanical", date(2026, 1, 2), date(2026, 1, 3), parent_id=parent.id)
    project = Project(tasks=[parent, child])
    child.start_date, child.end_date = date(2026, 3, 1), date(2026, 3, 15)
    project.validate()
    assert (parent.start_date, parent.end_date) == (date(2026, 1, 1), date(2026, 1, 10))
def test_validation_and_cascade_delete():
    with pytest.raises(ValueError): Task("Bad", "Software", date(2026, 2, 2), date(2026, 2, 1))
    parent = Task("Parent", "Notebook", date.today(), date.today()); child = Task("Child", "Notebook", date.today(), date.today(), parent_id=parent.id)
    project = Project(tasks=[parent, child]); project.remove(parent.id); assert not project.tasks
