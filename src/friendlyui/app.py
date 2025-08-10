# src/friendlyui/app.py
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from .themes import apply_theme
from .settings_dialog import ProjectSettingsDialog
from .models import load_or_create_project, save_project, normalize_c_identifier
from .dock_left import LeftDock
from .dock_right import RightDock

class MainWindow(QMainWindow):
    def __init__(self, project_path: Path, app: QApplication):
        super().__init__()
        self.app = app
        self.project_path = project_path
        self.data = load_or_create_project(self.project_path)

        self.setWindowTitle("FriendlyUI — LVGL Editor")
        self.resize(1400, 820)

        # theme
        apply_theme(self.app, self.data.get("ui", {}).get("theme", "system"))

        # center placeholder
        center = QWidget(); lay = QVBoxLayout(center)
        lay.addWidget(QLabel("Центральная область редактора (Preview/Editor)"))
        self.setCentralWidget(center)

        # left dock
        self.left = LeftDock(
            get_project_dict=lambda: self.data,
            get_screen_cb=self._get_current_screen,
            add_widget_cb=self._add_widget_from_palette
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left)
        self.left.refresh_windows()
        self.left.list_windows.currentRowChanged.connect(lambda _: self.left.populate_widgets())
        self.left.list_windows.setCurrentRow(0)

        # right dock (palette uses current lvgl_version)
        self.right = RightDock(get_lvgl_version=lambda: self.data.get("project", {}).get("lvgl_version", "v8"))
        self.addDockWidget(Qt.RightDockWidgetArea, self.right)

        # Menus
        self._make_menus()

    # ---- helpers ----
    def _get_current_screen(self) -> dict:
        idx = self.left.list_windows.currentRow()
        if idx < 0: idx = 0
        return self.data["screens"][idx]

    def _add_widget_from_palette(self, wtype: str, parent_id: str|None):
        screen = self._get_current_screen()
        new_id = normalize_c_identifier(f"{wtype}_{len(screen['widgets'])+1}")
        node = {"id": new_id, "type": wtype, "props": {"name": wtype}, "children": []}

        def add_under(lst):
            for n in lst:
                if n["id"] == parent_id:
                    n.setdefault("children", []).append(node); return True
                if add_under(n.get("children", [])): return True
            return False

        if parent_id and add_under(screen["widgets"]):
            pass
        else:
            screen["widgets"].append(node)

        save_project(self.project_path, self.data)
        self.left.populate_widgets()

    # ---- menus ----
    def _make_menus(self):
        # File
        m_file = self.menuBar().addMenu("File")
        for title, handler in [
            ("New", self.on_file_new),
            ("Open", self.on_file_open),
            ("Save", self.on_file_save),
            ("Export", self.on_file_export),
            ("Import", self.on_file_import),
        ]:
            act = QAction(title, self); act.triggered.connect(handler); m_file.addAction(act)

        # Project
        m_proj = self.menuBar().addMenu("Project")
        for title, handler in [
            ("New", self.on_project_new),
            ("Build", self.on_project_build),
            ("Check", self.on_project_check),
            ("Export", self.on_project_export),
        ]:
            act = QAction(title, self); act.triggered.connect(handler); m_proj.addAction(act)
        m_proj.addSeparator()
        act_settings = QAction("Settings…", self); act_settings.triggered.connect(self.on_settings); m_proj.addAction(act_settings)

        # View → Theme
        m_view = self.menuBar().addMenu("View")
        m_theme = m_view.addMenu("Theme")
        self.act_theme_system = QAction("System", self, checkable=True)
        self.act_theme_dark = QAction("Dark", self, checkable=True)
        self.act_theme_system.triggered.connect(lambda: self._set_theme("system"))
        self.act_theme_dark.triggered.connect(lambda: self._set_theme("dark"))
        m_theme.addAction(self.act_theme_system); m_theme.addAction(self.act_theme_dark)
        t = self.data.get("ui", {}).get("theme", "system")
        (self.act_theme_dark if t=="dark" else self.act_theme_system).setChecked(True)

    # ---- settings / theme ----
    def on_settings(self):
        dlg = ProjectSettingsDialog(self.data, self)
        if dlg.exec():
            proj = self.data.setdefault("project", {})
            patch = dlg.patch()
            proj["lvgl_version"] = patch["lvgl_version"]
            proj.setdefault("target", {}).update(patch["target"])
            save_project(self.project_path, self.data)
            # перезагрузим палитру под новую версию
            self.right.reload_palette()

    def _set_theme(self, theme: str):
        self.act_theme_dark.setChecked(theme=="dark")
        self.act_theme_system.setChecked(theme!="dark")
        apply_theme(self.app, theme)
        self.data.setdefault("ui", {})["theme"] = theme
        save_project(self.project_path, self.data)

    # ---- stubs ----
    def on_file_new(self): pass
    def on_file_open(self): pass
    def on_file_save(self): save_project(self.project_path, self.data)
    def on_file_export(self): pass
    def on_file_import(self): pass
    def on_project_new(self): pass
    def on_project_build(self): pass
    def on_project_check(self): pass
    def on_project_export(self): pass

def main():
    app = QApplication(sys.argv)
    w = MainWindow(Path("./proj_demo"), app)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    