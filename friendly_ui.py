# friendly_ui.py
import sys, json, re
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QDialog, QFormLayout,
    QDialogButtonBox, QComboBox, QSpinBox, QDockWidget, QGroupBox, QListWidget,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QListWidgetItem
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QDrag
from PySide6.QtCore import Qt, QMimeData, QByteArray, QSize, QPoint

# ------------------ Project defaults ------------------
DEFAULT_PROJECT = {
    "project": {
        "name": "FriendlyUI",
        "lvgl_version": "v8",
        "target": {"resX": 320, "resY": 240, "colorDepth": 16}
    },
    "ui": {"theme": "system"},
    "screens": [{"title":"Main","c_name":"screen_main","bg_color":"#101010","widgets":[], "vars":[]}]
}

def normalize_c_identifier(s: str) -> str:
    s = s.strip()
    s = re.sub(r'[^0-9A-Za-z_]+', '_', s)
    if re.match(r'^[0-9]', s):
        s = '_' + s
    return s.lower()

# ------------------ Settings dialog ------------------
class ProjectSettingsDialog(QDialog):
    def __init__(self, project_dict: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Settings")
        p = project_dict.get("project", {})
        tgt = p.get("target", {}) or {}

        self.lvgl = QComboBox()
        self.lvgl.addItems(["v8", "v9"])
        self.lvgl.setCurrentText(p.get("lvgl_version", "v8"))

        self.w = QSpinBox(); self.w.setRange(64, 8192); self.w.setValue(int(tgt.get("resX", 320)))
        self.h = QSpinBox(); self.h.setRange(64, 8192); self.h.setValue(int(tgt.get("resY", 240)))
        self.bpp = QSpinBox(); self.bpp.setRange(1, 32); self.bpp.setValue(int(tgt.get("colorDepth", 16)))

        form = QFormLayout(self)
        form.addRow("LVGL version:", self.lvgl)
        form.addRow("Width (px):", self.w)
        form.addRow("Height (px):", self.h)
        form.addRow("Color depth (bpp):", self.bpp)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

    def patch(self) -> dict:
        return {
            "lvgl_version": self.lvgl.currentText(),
            "target": {
                "resX": self.w.value(),
                "resY": self.h.value(),
                "colorDepth": self.bpp.value(),
            }
        }

# ------------------ Theme ------------------
def apply_theme(app: QApplication, theme: str):
    """theme: 'system' | 'dark'"""
    from PySide6.QtGui import QPalette, QColor
    if theme == "system":
        app.setStyle(None)
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet("")
        return

    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(32, 32, 36))
    pal.setColor(QPalette.WindowText, Qt.white)
    pal.setColor(QPalette.Base, QColor(22, 22, 24))
    pal.setColor(QPalette.AlternateBase, QColor(36, 36, 40))
    pal.setColor(QPalette.ToolTipBase, QColor(36,36,40))
    pal.setColor(QPalette.ToolTipText, Qt.white)
    pal.setColor(QPalette.Text, Qt.white)
    pal.setColor(QPalette.Button, QColor(40, 40, 45))
    pal.setColor(QPalette.ButtonText, Qt.white)
    pal.setColor(QPalette.BrightText, Qt.red)
    pal.setColor(QPalette.Highlight, QColor(53, 132, 228))
    pal.setColor(QPalette.HighlightedText, Qt.white)
    pal.setColor(QPalette.Link, QColor(85, 170, 255))
    pal.setColor(QPalette.PlaceholderText, QColor(200,200,200,128))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor(180,180,180))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(160,160,160))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor(160,160,160))
    app.setPalette(pal)
    app.setStyleSheet("""
    QMenuBar { background-color:#26262a; color:white; border:none; }
    QMenuBar::item { background:transparent; padding:4px 8px; }
    QMenuBar::item:selected { background:#35363a; border-radius:6px; }
    QMenu { background-color:#2a2a2e; color:white; border:1px solid #3a3a3f; padding:4px; }
    QMenu::item { padding:6px 18px 6px 24px; background:transparent; }
    QMenu::item:selected { background-color:#35363a; border-radius:6px; }
    QMenu::separator { height:1px; background:#3a3a3f; margin:6px 8px; }
    QToolTip { color:white; background-color:#35363a; border:1px solid #3a3a3f; }
    """)

# ------------------ LVGL palette (right dock) ------------------
# Группы виджетов, близко к docs.lvgl.io (v8/v9 — общая часть)
LVGL_WIDGET_GROUPS = {
    "Basic": [
        ("lv_obj", "OBJ"),
        ("lv_label", "LBL"),
        ("lv_btn", "BTN"),
        ("lv_img", "IMG"),
        ("lv_line", "LINE"),
        ("lv_bar", "BAR"),
        ("lv_arc", "ARC"),
        ("lv_slider", "SLDR"),
        ("lv_switch", "SW"),
        ("lv_led", "LED"),
        ("lv_canvas", "CNV"),
        ("lv_table", "TBL"),
        ("lv_span", "SPAN"),
    ],
    "Selectors": [
        ("lv_checkbox", "CHK"),
        ("lv_btnmatrix", "BMAT"),
        ("lv_dropdown", "DD"),
        ("lv_roller", "RLL"),
        ("lv_spinbox", "SPB"),
        ("lv_msgbox", "MSG"),
        ("lv_calendar", "CAL"),
        ("lv_colorwheel", "CWH"),
    ],
    "Inputs": [
        ("lv_textarea", "TA"),
        ("lv_keyboard", "KBD"),
    ],
    "Containers": [
        ("lv_tabview", "TAB"),
        ("lv_tileview", "TV"),
        ("lv_list", "LIST"),
        ("lv_menu", "MENU"),
        ("lv_meter", "MTR"),
        ("lv_chart", "CHT"),
        ("lv_animimg", "AIMG"),
        ("lv_spinner", "SPIN"),
    ],
}

def icon_from_tag(tag: str) -> QIcon:
    pm = QPixmap(72, 56); pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.fillRect(0, 0, 72, 56, QColor(58, 60, 66))
    p.setPen(QColor(230,230,230))
    p.drawText(pm.rect(), Qt.AlignCenter, tag)
    p.end()
    return QIcon(pm)

class WidgetList(QListWidget):
    """Иконки-источники drag с mime 'application/x-lvgl-widget' -> widget type."""
    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(72, 56))
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
    """Правая колонка: Properties (top), Palette (bottom)."""
    def __init__(self, parent=None):
        super().__init__("Library")
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        root = QWidget(); self.setWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(6,6,6,6); lay.setSpacing(8)

        gb_top = QGroupBox("Properties")
        ltop = QVBoxLayout(gb_top)
        ltop.addWidget(QLabel("Пока заглушка. Тут будет инспектор свойств выделенного элемента."))
        lay.addWidget(gb_top)

        gb_bottom = QGroupBox("Widgets palette")
        lbot = QVBoxLayout(gb_bottom)
        self.tabs = QTabWidget()
        for group, items in LVGL_WIDGET_GROUPS.items():
            wl = WidgetList()
            for wtype, tag in items:
                it = QListWidgetItem(icon_from_tag(tag), wtype)
                it.setData(Qt.UserRole, wtype)
                wl.addItem(it)
            self.tabs.addTab(wl, group)
        lbot.addWidget(self.tabs)
        lay.addWidget(gb_bottom, 1)

# ------------------ Left dock (now with widgets tree & drops) ------------------
class WidgetsTree(QTreeWidget):
    """Дерево виджетов выбранного окна. Принимает drop из палитры."""
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
        # куда вставлять: под выделенный узел или в корень экрана
        pos = e.position().toPoint() if hasattr(e, "position") else e.pos()
        target_item = self.itemAt(pos)
        parent_id = None
        if target_item:
            parent_id = target_item.text(2)  # id в колонке 3
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

# ------------------ Main window ------------------
class MainWindow(QMainWindow):
    def __init__(self, project_path: Path, app: QApplication):
        super().__init__()
        self.app = app
        self.setWindowTitle("FriendlyUI (PySide6) — LVGL Editor")
        self.resize(1400, 820)
        self.project_path = project_path
        self.data = self._load_or_create_project()

        # theme on start
        theme = self.data.get("ui", {}).get("theme", "system")
        apply_theme(self.app, theme)

        # Center placeholder
        center = QWidget()
        lay = QVBoxLayout(center)
        lay.addWidget(QLabel("Центральная область редактора (Preview/Editor)"))
        self.setCentralWidget(center)

        # Left dock (3 blocks, middle is tree with drops)
        left = QDockWidget("Project", self)
        left.setAllowedAreas(Qt.LeftDockWidgetArea)
        lw = QWidget(); left.setWidget(lw)
        ll = QVBoxLayout(lw); ll.setContentsMargins(6,6,6,6); ll.setSpacing(8)

        gb1 = QGroupBox("Windows"); l1 = QVBoxLayout(gb1); self.list_windows = QListWidget(); l1.addWidget(self.list_windows)
        gb2 = QGroupBox("Widgets (selected window)"); l2 = QVBoxLayout(gb2)
        self.tree_widgets = WidgetsTree(self._get_current_screen, self._add_widget_from_palette)
        l2.addWidget(self.tree_widgets)
        gb3 = QGroupBox("Variables (context)"); l3 = QVBoxLayout(gb3); l3.addWidget(QListWidget())

        ll.addWidget(gb1); ll.addWidget(gb2, 1); ll.addWidget(gb3)
        self.addDockWidget(Qt.LeftDockWidgetArea, left)

        # Right dock: properties + palette
        self.right = RightDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right)

        # ---- Menu: File ----
        menu_file = self.menuBar().addMenu("File")
        act_file_new = QAction("New", self);   act_file_new.triggered.connect(self.on_file_new)
        act_file_open = QAction("Open", self); act_file_open.triggered.connect(self.on_file_open)
        act_file_save = QAction("Save", self); act_file_save.triggered.connect(self.on_file_save)
        act_file_export = QAction("Export", self); act_file_export.triggered.connect(self.on_file_export)
        act_file_import = QAction("Import", self); act_file_import.triggered.connect(self.on_file_import)
        menu_file.addActions([act_file_new, act_file_open, act_file_save, act_file_export, act_file_import])

        # ---- Menu: Project ----
        menu_project = self.menuBar().addMenu("Project")
        act_proj_new = QAction("New", self);      act_proj_new.triggered.connect(self.on_project_new)
        act_proj_build = QAction("Build", self);  act_proj_build.triggered.connect(self.on_project_build)
        act_proj_check = QAction("Check", self);  act_proj_check.triggered.connect(self.on_project_check)
        act_proj_export = QAction("Export", self); act_proj_export.triggered.connect(self.on_project_export)
        act_settings = QAction("Settings…", self); act_settings.triggered.connect(self.on_settings)
        menu_project.addActions([act_proj_new, act_proj_build, act_proj_check, act_proj_export])
        menu_project.addSeparator(); menu_project.addAction(act_settings)

        # ---- Menu: View → Theme ----
        menu_view = self.menuBar().addMenu("View")
        menu_theme = menu_view.addMenu("Theme")
        self.act_theme_system = QAction("System", self, checkable=True)
        self.act_theme_dark = QAction("Dark", self, checkable=True)
        self.act_theme_system.triggered.connect(lambda: self._set_theme("system"))
        self.act_theme_dark.triggered.connect(lambda: self._set_theme("dark"))
        menu_theme.addAction(self.act_theme_system); menu_theme.addAction(self.act_theme_dark)
        if theme == "dark": self.act_theme_dark.setChecked(True)
        else: self.act_theme_system.setChecked(True)

        # fill windows list + widgets tree
        self._refresh_windows()
        self.list_windows.currentRowChanged.connect(self._on_window_changed)
        self.list_windows.setCurrentRow(0)

    # ------------------ Data helpers ------------------
    def _load_or_create_project(self) -> dict:
        pj = self.project_path / "project.json"
        if pj.exists():
            try:
                return json.loads(pj.read_text(encoding="utf-8"))
            except Exception:
                pass
        self.project_path.mkdir(parents=True, exist_ok=True)
        pj.write_text(json.dumps(DEFAULT_PROJECT, indent=2), encoding="utf-8")
        return json.loads(json.dumps(DEFAULT_PROJECT))

    def _save_project(self):
        pj = self.project_path / "project.json"
        pj.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def _get_current_screen(self) -> dict:
        idx = self.list_windows.currentRow()
        if idx < 0: idx = 0
        return self.data["screens"][idx]

    # ------------------ Left UI updates ------------------
    def _refresh_windows(self):
        self.list_windows.clear()
        for s in self.data["screens"]:
            self.list_windows.addItem(f"{s['title']} ({s['c_name']})")

    def _on_window_changed(self, _row: int):
        self._refresh_widgets_tree()

    def _refresh_widgets_tree(self):
        self.tree_widgets.populate(self._get_current_screen())

    # ------------------ DnD add ------------------
    def _add_widget_from_palette(self, wtype: str, parent_id: str|None):
        screen = self._get_current_screen()
        new_id = normalize_c_identifier(f"{wtype}_{len(screen['widgets'])+1}")
        node = {"id": new_id, "type": wtype, "props": {"name": wtype}, "children": []}

        def find_and_add(lst):
            for n in lst:
                if n["id"] == parent_id:
                    n.setdefault("children", []).append(node); return True
                if find_and_add(n.get("children", [])): return True
            return False

        if parent_id and find_and_add(screen["widgets"]):
            pass
        else:
            screen["widgets"].append(node)

        self._save_project()
        self._refresh_widgets_tree()

    # ------------------ Theme ------------------
    def _set_theme(self, theme: str):
        if theme == "dark":
            self.act_theme_dark.setChecked(True); self.act_theme_system.setChecked(False)
        else:
            self.act_theme_system.setChecked(True); self.act_theme_dark.setChecked(False)
        apply_theme(self.app, theme)
        self.data.setdefault("ui", {})["theme"] = theme
        self._save_project()

    # ------------------ Menu stubs ------------------
    def on_file_new(self): pass
    def on_file_open(self): pass
    def on_file_save(self): self._save_project()
    def on_file_export(self): pass
    def on_file_import(self): pass
    def on_project_new(self): pass
    def on_project_build(self): pass
    def on_project_check(self): pass
    def on_project_export(self): pass
    def on_settings(self):
        dlg = ProjectSettingsDialog(self.data, self)
        if dlg.exec() == QDialog.Accepted:
            proj = self.data.setdefault("project", {})
            patch = dlg.patch()
            proj["lvgl_version"] = patch["lvgl_version"]
            proj.setdefault("target", {}).update(patch["target"])
            self._save_project()

# ------------------ Run ------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow(Path("./proj_demo"), app)
    w.show()
    sys.exit(app.exec())
    