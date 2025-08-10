# src/friendlyui/settings_dialog.py
from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QSpinBox

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
            "target": {"resX": self.w.value(), "resY": self.h.value(), "colorDepth": self.bpp.value()}
        }
