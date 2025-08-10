# src/friendlyui/dock_left.py
from __future__ import annotations
from typing import Callable, Dict
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QGroupBox, QListWidget, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, QMimeData, QByteArray, QPoint

class WidgetsTree(QTreeWidget):
    def __init__(self, get_screen_cb, add_widget_cb):
        super().__init__()
        self.get_screen_cb = get_screen_cb
        self.add_widget_cb = add_widget_cb
        self.setHeaderLabels(["Widget", "Type", "id"])
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat("application/x-lvgl-widget"):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat("application/x-lvgl-widget"):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        if not e.mimeData().hasFormat("application/x-lvgl-widget"):
            e.ignore(); return
        wtype = bytes(e.mimeData().data("application/x-lvgl-widget")).decode("utf-8")
        pos = e.position().toPoint() if hasattr(e, "position") else e.pos()
        target_item = self.itemAt(pos)
        parent_id = target_item.text(2) if target_item else None
        self.add_widget_cb(wtype, parent_id)
        e.acceptProposedAction()

    def populate(self, screen: dict):
        self.clear()
        def add_node(parent_item, node):
            it = QTreeWidgetItem([node.get("props",{}).get("name", node["type"]), node["type"], node["id"]])
            if parent_item: parent_item.addChild(it)
            else: self.addTopLevelItem(it)
            for ch in node.get("children", []):
                add_node(it, ch)
        for w in screen.get("widgets", []):
            add_node(None, w)
        self.expandToDepth(1)

class LeftDock(QDockWidget):
    def __init__(self, get_project_dict, get_screen_cb, add_widget_cb, parent=None):
        super().__init__("Project")
        self.get_project_dict = get_project_dict
        self.get_screen_cb = get_screen_cb
        self.add_widget_cb = add_widget_cb

        root = QWidget(); self.setWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(6,6,6,6); lay.setSpacing(8)

        self.gb1 = QGroupBox("Windows"); l1 = QVBoxLayout(self.gb1)
        self.list_windows = QListWidget(); l1.addWidget(self.list_windows)
        lay.addWidget(self.gb1)

        self.gb2 = QGroupBox("Widgets (selected window)"); l2 = QVBoxLayout(self.gb2)
        self.tree_widgets = WidgetsTree(self.get_screen_cb, self.add_widget_cb)
        l2.addWidget(self.tree_widgets)
        lay.addWidget(self.gb2, 1)

        self.gb3 = QGroupBox("Variables (context)"); l3 = QVBoxLayout(self.gb3)
        l3.addWidget(QListWidget())
        lay.addWidget(self.gb3)

    def refresh_windows(self):
        proj = self.get_project_dict()
        self.list_windows.clear()
        for s in proj["screens"]:
            self.list_windows.addItem(f"{s['title']} ({s['c_name']})")

    def populate_widgets(self):
        self.tree_widgets.populate(self.get_screen_cb())
