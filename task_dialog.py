from datetime import date
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
                               QFormLayout, QLineEdit, QMessageBox, QSpinBox, QTextEdit, QVBoxLayout)
from models import SECTIONS

class TaskDialog(QDialog):
    def __init__(self, project, task=None, parent=None, owner=None):
        super().__init__(owner); self.project = project
        self.setWindowTitle("Edit task" if task else "Add task"); self.setMinimumWidth(440)
        self.name = QLineEdit(); self.section = QComboBox(); self.section.addItems(SECTIONS)
        self.start = QDateEdit(calendarPopup=True); self.end = QDateEdit(calendarPopup=True)
        for editor in (self.start, self.end): editor.setDisplayFormat("MMM d, yyyy")
        self.start.setDate(QDate.currentDate()); self.end.setDate(QDate.currentDate().addDays(7))
        self.engineer = QComboBox(); self.engineer.setEditable(True); self.engineer.addItems(project.engineers)
        self.parent = QComboBox(); self.parent.addItem("No parent", None)
        excluded = ({task.id} | project.descendants(task.id)) if task else set()
        for candidate in project.tasks:
            if candidate.id not in excluded: self.parent.addItem(f"{candidate.section} · {candidate.name}", candidate.id)
        self.critical = QCheckBox("Render this task in red")
        self.completion = QSpinBox(); self.completion.setRange(0, 100); self.completion.setSuffix("%")
        self.notes = QTextEdit(); self.notes.setMaximumHeight(90)
        form = QFormLayout()
        for label, widget in (("Task name", self.name), ("Section", self.section), ("Start date", self.start),
            ("End date", self.end), ("Responsible Engineer", self.engineer), ("Parent task", self.parent),
            ("Critical Path", self.critical), ("Completion", self.completion), ("Notes", self.notes)): form.addRow(label, widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self); layout.addLayout(form); layout.addWidget(buttons)
        if task:
            self.name.setText(task.name); self.section.setCurrentText(task.section)
            self.start.setDate(QDate(task.start_date.year, task.start_date.month, task.start_date.day))
            self.end.setDate(QDate(task.end_date.year, task.end_date.month, task.end_date.day))
            self.engineer.setCurrentText(task.responsible_engineer); self.parent.setCurrentIndex(max(0, self.parent.findData(task.parent_id)))
            self.critical.setChecked(task.critical_path); self.completion.setValue(task.completion); self.notes.setText(task.notes)
        elif parent:
            self.section.setCurrentText(parent.section); self.parent.setCurrentIndex(self.parent.findData(parent.id))

    def accept(self):
        if not self.name.text().strip(): QMessageBox.warning(self, "Missing name", "Enter a task name."); return
        if self.end.date() < self.start.date(): QMessageBox.warning(self, "Invalid dates", "End date cannot precede start date."); return
        parent = self.project.task(self.parent.currentData())
        if parent: self.section.setCurrentText(parent.section)
        super().accept()

    def values(self):
        convert = lambda value: date(value.year(), value.month(), value.day())
        return {"name": self.name.text().strip(), "section": self.section.currentText(),
                "start_date": convert(self.start.date()), "end_date": convert(self.end.date()),
                "responsible_engineer": self.engineer.currentText().strip(), "parent_id": self.parent.currentData(),
                "critical_path": self.critical.isChecked(), "completion": self.completion.value(),
                "notes": self.notes.toPlainText().strip()}
