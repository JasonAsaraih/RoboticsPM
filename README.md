# RoboticsPM

RoboticsPM is a polished, navy-themed PySide6 Gantt application for planning a robotics team's Mechanical, Electrical, Software, and Notebook work.

## Install and run

Python 3.10 or newer is required:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Projects are saved locally as readable JSON through the **File** menu. The initial view contains sample tasks; choose **File → New Project** for a blank schedule.

## Highlights

- Resizable, synchronized hierarchy and Gantt timeline
- Multi-level tasks with automatic parent date roll-up
- Expandable engineering-section groups for quickly showing or hiding subteams
- Responsible Engineer, progress, notes, and critical-path fields
- Day, week, and month scales with a today marker
- Local JSON Open, Save, and Save As support
- Independent engineering-section filters
- Responsible Engineer, progress, notes, and critical-path fields
- Day, week, and month scales with a today marker
- Local JSON Open, Save, and Save As support
RoboticsPM is a desktop project-management application for planning a robotics team's engineering schedule.

Development changes should be proposed on a feature branch and merged into `main` through a pull request.
