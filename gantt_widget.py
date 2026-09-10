from datetime import date, timedelta
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QAbstractScrollArea, QFrame, QVBoxLayout, QWidget
from models import Task
from styles import BLUE, NAVY, RED, ROW_HEIGHT

class TimelineHeader(QWidget):
    def __init__(self, canvas): super().__init__(); self.canvas = canvas; self.setFixedHeight(36)
    def paintEvent(self, event):
        p = QPainter(self); p.fillRect(self.rect(), QColor(NAVY)); p.setPen(Qt.white)
        for day in range(0, self.canvas.total_days + 1, self.canvas.label_step):
            x = day * self.canvas.day_width - self.canvas.horizontalScrollBar().value()
            if -150 < x < self.width() + 150:
                label = (self.canvas.timeline_start + timedelta(days=day)).strftime(self.canvas.label_format)
                p.drawText(QRectF(x + 5, 0, max(50, self.canvas.label_step * self.canvas.day_width - 6), 36), Qt.AlignVCenter, label)

class GanttCanvas(QAbstractScrollArea):
    taskSelected = Signal(str)
    def __init__(self):
        super().__init__(); self.rows = []; self.selected_id = None
        self.timeline_start, self.total_days = date.today() - timedelta(days=7), 30
        self.day_width, self.label_step, self.label_format = 12, 7, "%b %d"
        self.setFrameShape(QFrame.NoFrame)
        self.horizontalScrollBar().valueChanged.connect(lambda _: self.viewport().update())
    def set_scale(self, scale):
        self.day_width, self.label_step, self.label_format = {"Day": (34, 1, "%b %d"), "Week": (12, 7, "%b %d"), "Month": (4, 30, "%b %Y")}[scale]
        self.update_ranges(); self.viewport().update()
    def set_rows(self, rows):
        self.rows = rows; tasks = [row for row in rows if isinstance(row, Task)]
        if tasks:
            self.timeline_start = min(t.start_date for t in tasks) - timedelta(days=3)
            self.total_days = max(30, (max(t.end_date for t in tasks) + timedelta(days=10) - self.timeline_start).days)
        self.update_ranges(); self.viewport().update()
    def update_ranges(self):
        self.horizontalScrollBar().setRange(0, max(0, self.total_days * self.day_width - self.viewport().width()))
        self.horizontalScrollBar().setPageStep(self.viewport().width())
        self.verticalScrollBar().setRange(0, max(0, len(self.rows) * ROW_HEIGHT - self.viewport().height()))
        self.verticalScrollBar().setPageStep(self.viewport().height())
    def resizeEvent(self, event): super().resizeEvent(event); self.update_ranges()
    def paintEvent(self, event):
        p = QPainter(self.viewport()); p.setRenderHint(QPainter.Antialiasing); p.fillRect(self.viewport().rect(), Qt.white)
        xs, ys = self.horizontalScrollBar().value(), self.verticalScrollBar().value()
        first = max(0, ys // ROW_HEIGHT); last = min(len(self.rows), (ys + self.viewport().height()) // ROW_HEIGHT + 2)
        for index in range(first, last):
            y = index * ROW_HEIGHT - ys; row = self.rows[index]
            p.fillRect(0, y, self.viewport().width(), ROW_HEIGHT, QColor("#f5f8fb" if index % 2 else "#ffffff"))
            p.setPen(QColor("#e2e8ef")); p.drawLine(0, y + ROW_HEIGHT - 1, self.viewport().width(), y + ROW_HEIGHT - 1)
            if isinstance(row, str): p.fillRect(0, y, self.viewport().width(), ROW_HEIGHT, QColor("#e7eef4")); continue
            x = (row.start_date - self.timeline_start).days * self.day_width - xs
            width = max(self.day_width, ((row.end_date - row.start_date).days + 1) * self.day_width)
            bar = QRectF(x, y + 7, width, ROW_HEIGHT - 14); p.setPen(QPen(QColor(NAVY), 2) if row.id == self.selected_id else Qt.NoPen)
            p.setBrush(QColor(RED if row.critical_path else BLUE)); p.drawRoundedRect(bar, 5, 5)
            if row.completion:
                p.setBrush(QColor(16, 52, 75, 155)); p.drawRoundedRect(QRectF(x, y + 7, width * row.completion / 100, ROW_HEIGHT - 14), 5, 5)
            p.setPen(Qt.white); p.setFont(QFont(p.font().family(), 9, QFont.DemiBold)); p.drawText(bar.adjusted(7, 0, -3, 0), Qt.AlignVCenter, f"{row.name}  {row.completion}%")
        today_x = (date.today() - self.timeline_start).days * self.day_width - xs
        p.setPen(QPen(QColor(RED), 2)); p.drawLine(today_x, 0, today_x, self.viewport().height())
    def mousePressEvent(self, event):
        index = int((event.position().y() + self.verticalScrollBar().value()) // ROW_HEIGHT)
        if 0 <= index < len(self.rows) and isinstance(self.rows[index], Task):
            self.selected_id = self.rows[index].id; self.taskSelected.emit(self.selected_id); self.viewport().update()

class GanttWidget(QWidget):
    taskSelected = Signal(str)
    def __init__(self):
        super().__init__(); self.canvas = GanttCanvas(); self.header = TimelineHeader(self.canvas)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0); layout.addWidget(self.header); layout.addWidget(self.canvas)
        self.canvas.taskSelected.connect(self.taskSelected); self.canvas.horizontalScrollBar().valueChanged.connect(self.header.update)
    def set_rows(self, rows): self.canvas.set_rows(rows); self.header.update()
    def set_scale(self, scale): self.canvas.set_scale(scale); self.header.update()
