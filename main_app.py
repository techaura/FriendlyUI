from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QAction
from settings_dialog import ProjectSettingsDialog
import json
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self, project_path: Path):
        super().__init__()
        self.project_path = project_path
        self.data = self._load_project()

        m = self.menuBar().addMenu("Project")
        act_settings = QAction("Settings…", self); m.addAction(act_settings)
        act_settings.triggered.connect(self.show_settings)

    def _load_project(self):
        pj = self.project_path / "project.json"
        if pj.exists():
            return json.loads(pj.read_text(encoding="utf-8"))
        # дефолт
        d = {
            "project": {
                "name": self.project_path.name,
                "lvgl_version": "v8",
                "target": {"resX": 320, "resY": 240, "colorDepth": 16}
            },
            "screens": [{"title":"Main","c_name":"screen_main","bg_color":"#101010","widgets":[], "vars":[]}]
        }
        pj.write_text(json.dumps(d, indent=2), encoding="utf-8")
        return d

    def _save_project(self):
        (self.project_path / "project.json").write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def show_settings(self):
        dlg = ProjectSettingsDialog(self.data, self)
        def on_applied(patch: dict):
            proj = self.data.setdefault("project", {})
            # name не трогаем, только lvgl_version/target
            proj["lvgl_version"] = patch["lvgl_version"]
            tgt = proj.setdefault("target", {})
            tgt.update(patch["target"])
            self._save_project()
            # тут можно дернуть перерисовку/пересбор предпросмотра
            # self.preview.reload_for_version(proj["lvgl_version"])
        dlg.applied.connect(on_applied)
        dlg.exec()

# запуск:
# app = QApplication([]); w = MainWindow(Path("./proj_demo")); w.show(); app.exec()
    