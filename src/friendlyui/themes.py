# src/friendlyui/themes.py
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

def apply_theme(app: QApplication, theme: str):
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
