"""Robotics Master Schedule application entry point."""
import sys
from datetime import date, timedelta
from pathlib import Path
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QSplitter, QToolBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from gantt_widget import GanttWidget
from models import Project, SECTIONS, Task
from storage import load_project, save_project
from styles import NAVY, ROW_HEIGHT, STYLE
from task_dialog import TaskDialog

ROLE = Qt.UserRole

def starter_project():
    today = date.today(); project = Project(engineers=["Alex", "Daniel", "Emma", "Jason", "Sarah"])
    drive = Task("Drivetrain", "Mechanical", today, today + timedelta(days=18), "Jason")
    project.tasks = [drive,
        Task("CAD Chassis", "Mechanical", today, today + timedelta(days=6), "Alex", drive.id, completion=65),
        Task("Machine Chassis", "Mechanical", today + timedelta(days=7), today + timedelta(days=13), "Sarah", drive.id, True, 20),
        Task("Assemble Chassis", "Mechanical", today + timedelta(days=14), today + timedelta(days=18), "Jason", drive.id),
        Task("Power Distribution", "Electrical", today + timedelta(days=3), today + timedelta(days=12), "Emma", critical_path=True, completion=30),
        Task("Odometry", "Software", today + timedelta(days=2), today + timedelta(days=15), "Daniel", completion=45),
        Task("Engineering Portfolio", "Notebook", today, today + timedelta(days=24), "Alex", completion=25)]
    return project

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.project = starter_project(); self.path = None; self.dirty = False
        self.resize(1380, 820); self.setMinimumSize(900, 560); self.build_ui(); self.rebuild()
    def build_ui(self):
        toolbar = QToolBar(); toolbar.setMovable(False); self.addToolBar(toolbar)
        for text, callback in (("＋ Add Task", self.add), ("↳ Add Child", self.add_child), ("✎ Edit", self.edit),
                               ("Delete", self.delete), ("Expand All", self.expand_all), ("Collapse All", self.collapse_all)):
            action = QAction(text, self); action.triggered.connect(callback); toolbar.addAction(action)
        file_menu = self.menuBar().addMenu("&File")
        for text, shortcut, callback in (("New Project", "Ctrl+N", self.new), ("Open…", "Ctrl+O", self.open),
                                         ("Save", "Ctrl+S", self.save), ("Save As…", "Ctrl+Shift+S", self.save_as)):
            action = QAction(text, self); action.setShortcut(shortcut); action.triggered.connect(callback); file_menu.addAction(action)
        root = QWidget(); layout = QVBoxLayout(root); layout.setContentsMargins(14, 12, 14, 12)
        title = QLabel("ROBOTICS MASTER SCHEDULE"); title.setStyleSheet(f"color:{NAVY};font-size:22px;font-weight:800")
        controls = QHBoxLayout(); controls.addStretch(); controls.addWidget(QLabel("Timeline scale"))
        self.scale = QComboBox(); self.scale.addItems(("Day", "Week", "Month")); self.scale.setCurrentText("Week"); controls.addWidget(self.scale)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(("Task", "Responsible Engineer", "Progress")); self.tree.setColumnCount(3)
        self.tree.setAlternatingRowColors(True); self.tree.setUniformRowHeights(True); self.tree.setVerticalScrollMode(QTreeWidget.ScrollPerPixel)
        self.tree.setColumnWidth(0, 290); self.tree.setColumnWidth(1, 150)
        self.gantt = GanttWidget(); self.gantt.set_scale("Week"); splitter = QSplitter(); splitter.addWidget(self.tree); splitter.addWidget(self.gantt)
        splitter.setSizes((520, 820)); splitter.setChildrenCollapsible(False)
        layout.addWidget(title); layout.addLayout(controls); layout.addWidget(splitter, 1); self.setCentralWidget(root)
        self.scale.currentTextChanged.connect(self.gantt.set_scale)
        self.tree.itemExpanded.connect(self.rebuild_chart); self.tree.itemCollapsed.connect(self.rebuild_chart)
        self.tree.itemSelectionChanged.connect(self.from_tree); self.tree.itemDoubleClicked.connect(lambda *_: self.edit())
        self.gantt.taskSelected.connect(self.from_chart)
        left, right = self.tree.verticalScrollBar(), self.gantt.canvas.verticalScrollBar()
        left.valueChanged.connect(right.setValue); right.valueChanged.connect(left.setValue)
        self.statusBar().showMessage("Ready")
    def all_items(self):
        result = []
        def visit(item):
            result.append(item)
            for index in range(item.childCount()): visit(item.child(index))
        for index in range(self.tree.topLevelItemCount()): visit(self.tree.topLevelItem(index))
        return result
    def selected_id(self):
        items = self.tree.selectedItems(); return items[0].data(0, ROLE) if items else None
    def selected_task(self): return self.project.task(self.selected_id())
    def rows(self):
        result = []
        def visit(item):
            result.append(self.project.task(item.data(0, ROLE)))
            if item.isExpanded():
                for index in range(item.childCount()): visit(item.child(index))
        for index in range(self.tree.topLevelItemCount()):
            section = self.tree.topLevelItem(index); result.append(section.text(0))
            if section.isExpanded():
                for child in range(section.childCount()): visit(section.child(child))
        return result
    def rebuild(self, *_):
        expanded = {item.data(0, ROLE) for item in self.all_items() if item.isExpanded()}; selected = self.selected_id()
        self.project.roll_up_dates(); self.tree.blockSignals(True); self.tree.clear()
        for section in SECTIONS:
            root = QTreeWidgetItem((section.upper(), "", "")); root.setData(0, ROLE, f"section:{section}"); root.setSizeHint(0, QSize(0, ROW_HEIGHT))
            root.setBackground(0, Qt.lightGray); self.tree.addTopLevelItem(root); root.setExpanded(not expanded or f"section:{section}" in expanded)
            def add_children(parent_item, parent_id=None):
                for task in self.project.children(parent_id, section):
                    item = QTreeWidgetItem((task.name, task.responsible_engineer or "—", f"{task.completion}%")); item.setData(0, ROLE, task.id)
                    item.setToolTip(0, task.notes); item.setSizeHint(0, QSize(0, ROW_HEIGHT)); parent_item.addChild(item); item.setExpanded(task.id in expanded)
                    add_children(item, task.id)
                    if task.id == selected: item.setSelected(True)
            add_children(root)
        self.tree.blockSignals(False); self.rebuild_chart(); self.update_title()
    def rebuild_chart(self, *_): self.gantt.set_rows(self.rows())
    def from_tree(self): self.gantt.canvas.selected_id = self.selected_id(); self.gantt.canvas.viewport().update()
    def from_chart(self, task_id):
        for item in self.all_items():
            if item.data(0, ROLE) == task_id: self.tree.setCurrentItem(item); break
    def show_dialog(self, task=None, parent=None):
        dialog = TaskDialog(self.project, task, parent, self)
        if dialog.exec():
            values = dialog.values()
            if task:
                for key, value in values.items(): setattr(task, key, value)
                for task_id in self.project.descendants(task.id): self.project.task(task_id).section = task.section
            else: self.project.tasks.append(Task(**values))
            engineer = values["responsible_engineer"]
            if engineer and engineer not in self.project.engineers: self.project.engineers.append(engineer)
            self.dirty = True; self.rebuild()
    def add(self): self.show_dialog()
    def add_child(self):
        task = self.selected_task()
        if task: self.show_dialog(parent=task)
        else: QMessageBox.information(self, "Select a task", "Select the parent task first.")
    def edit(self):
        if self.selected_task(): self.show_dialog(task=self.selected_task())
    def delete(self):
        task = self.selected_task()
        if task and QMessageBox.question(self, "Delete task", f"Delete '{task.name}' and all child tasks?") == QMessageBox.Yes:
            self.project.remove(task.id); self.dirty = True; self.rebuild()
    def expand_all(self): self.tree.expandAll(); self.rebuild_chart()
    def collapse_all(self): self.tree.collapseAll(); self.rebuild_chart()
    def update_title(self): self.setWindowTitle(f"{'*' if self.dirty else ''}{self.project.name} — {self.path.name if self.path else 'Untitled'}")
    def discard_ok(self):
        return not self.dirty or QMessageBox.question(self, "Unsaved changes", "Discard unsaved changes?", QMessageBox.Discard | QMessageBox.Cancel) == QMessageBox.Discard
    def new(self):
        if self.discard_ok(): self.project = Project(); self.path = None; self.dirty = False; self.rebuild()
    def open(self):
        if not self.discard_ok(): return
        path, _ = QFileDialog.getOpenFileName(self, "Open schedule", "", "Robotics schedules (*.json)")
        if path:
            try: self.project = load_project(path); self.path = Path(path); self.dirty = False; self.rebuild()
            except Exception as error: QMessageBox.critical(self, "Could not open", str(error))
    def save(self):
        if not self.path: return self.save_as()
        try: save_project(self.project, self.path); self.dirty = False; self.update_title(); self.statusBar().showMessage(f"Saved {self.path}", 4000); return True
        except Exception as error: QMessageBox.critical(self, "Could not save", str(error)); return False
    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save schedule", str(self.path or "robotics_schedule.json"), "Robotics schedules (*.json)")
        if not path: return False
        self.path = Path(path); return self.save()
    def closeEvent(self, event): event.accept() if self.discard_ok() else event.ignore()

def main():
    app = QApplication(sys.argv); app.setApplicationName("Robotics Master Schedule"); app.setStyle("Fusion"); app.setStyleSheet(STYLE)
    window = MainWindow(); window.show(); sys.exit(app.exec())
if __name__ == "__main__": main()
