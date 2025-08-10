# src/friendlyui/dock_right.py
from __future__ import annotations
from typing import Callable, Dict, List, Tuple
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QGroupBox, QLabel, QTabWidget, QListWidget, QListWidgetItem
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QDrag
from PySide6.QtCore import Qt, QMimeData, QByteArray, QSize, QPoint
from .widgets_registry import load_widget_groups

def make_tile_icon(tag: str) -> QIcon:
    pm = QPixmap(72, 56); pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.fillRect(0, 0, 72, 56, QColor(58, 60, 66))
    p.setPen(QColor(230,230,230))
    p.drawText(pm.rect(), Qt.AlignCenter, tag)
    p.end()
    return QIcon(pm)

class PaletteList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(72,56))
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(8)
        self.setDragEnabled(True)
        self.setMovement(QListWidget.Static)
        self.setUniformItemSizes(True)

    def startDrag(self, supportedActions):
        it = self.currentItem()
        if not it: return
        mime = QMimeData()
        mime.setData("application/x-lvgl-widget", QByteArray(it.data(Qt.UserRole).encode("utf-8")))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setHotSpot(QPoint(36, 28))
        drag.setPixmap(it.icon().pixmap(72,56))
        drag.exec(Qt.CopyAction)

class RightDock(QDockWidget):
    """Правая колонка: Properties (top), Widgets palette (bottom)."""
    def __init__(self, get_lvgl_version: Callable[[], str], parent=None):
        super().__init__("Library")
        self.get_lvgl_version = get_lvgl_version

        root = QWidget(); self.setWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(6,6,6,6); lay.setSpacing(8)

        gb_top = QGroupBox("Properties")
        ltop = QVBoxLayout(gb_top)
        ltop.addWidget(QLabel("Пока заглушка. Тут будет инспектор свойств выделенного элемента."))
        lay.addWidget(gb_top)

        gb_bottom = QGroupBox("Widgets palette")
        lbot = QVBoxLayout(gb_bottom)
        self.tabs = QTabWidget()
        lbot.addWidget(self.tabs)
        lay.addWidget(gb_bottom, 1)

        self.reload_palette()

    def reload_palette(self):
        self.tabs.clear()
        groups = load_widget_groups(self.get_lvgl_version())
        for group, items in groups.items():
            wl = PaletteList()
            for wtype, tag in items:
                it = QListWidgetItem(make_tile_icon(tag), wtype)
                it.setData(Qt.UserRole, wtype)
                wl.addItem(it)
            self.tabs.addTab(wl, group)
