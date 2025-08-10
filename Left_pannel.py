# left_panel.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re, json
from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal, QMimeData, QByteArray, QDataStream, QIODevice
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QDockWidget, QMenu, QGroupBox, QPushButton, QHBoxLayout, QInputDialog, QMessageBox
)

# ------------------ Модель проекта ------------------

def normalize_c_identifier(s: str) -> str:
    # Превращает произвольный заголовок в C-идентификатор: ui_Main_Screen -> ui_main_screen
    s = s.strip()
    s = re.sub(r'[^0-9A-Za-z_]+', '_', s)
    if re.match(r'^[0-9]', s):
        s = '_' + s
    return s.lower()

@dataclass
class VarDef:
    name: str            # display name
    c_name: str          # code name (normalized)
    vtype: str           # 'int', 'bool', 'float', 'string', 'lv_obj_t*', ...
    init: Optional[str] = None

@dataclass
class WidgetNode:
    id: str
    type: str            # lv_btn, lv_label, lv_line, ...
    props: Dict[str, Any] = field(default_factory=dict)
    children: List['WidgetNode'] = field(default_factory=list)
    vars: List[VarDef] = field(default_factory=list)

@dataclass
class ScreenDef:
    title: str
    c_name: str
    bg_color: str = "#101010"
    widgets: List[WidgetNode] = field(default_factory=list)
    vars: List[VarDef] = field(default_factory=list)

@dataclass
class ProjectModel:
    name: str = "untitled"
    screens: List[ScreenDef] = field(default_factory=list)

    @staticmethod
    def new_default() -> 'ProjectModel':
        return ProjectModel(
            name="untitled",
            screens=[ScreenDef(title="Main", c_name="screen_main")]
        )

    def to_json(self) -> dict:
        def ser_w(w: WidgetNode):
            return {
                "id": w.id, "type": w.type, "props": w.props,
                "children": [ser_w(c) for c in w.children],
                "vars": [vars(v) for v in w.vars],
            }
        return {
            "project": {"name": self.name},
            "screens": [{
                "title": s.title, "c_name": s.c_name, "bg_color": s.bg_color,
                "widgets": [ser_w(w) for w in s.widgets],
                "vars": [vars(v) for v in s.vars],
            } for s in self.screens]
        }

    @staticmethod
    def from_json(d: dict) -> 'ProjectModel':
        def de_w(x):
            return WidgetNode(
                id=x["id"], type=x["type"], props=x.get("props", {}),
                children=[de_w(c) for c in x.get("children", [])],
                vars=[VarDef(**v) for v in x.get("vars", [])],
            )
        pm = ProjectModel(name=d.get("project", {}).get("name", "untitled"))
        for s in d.get("screens", []):
            pm.screens.append(ScreenDef(
                title=s["title"],
                c_name=s.get("c_name", normalize_c_identifier(s["title"])),
                bg_color=s.get("bg_color", "#101010"),
                widgets=[de_w(w) for w in s.get("widgets", [])],
                vars=[VarDef(**v) for v in s.get("vars", [])],
            ))
        return pm

# ------------------ Виджеты UI слева ------------------

class ScreensList(QListWidget):
    """Верхний блок: список окон. Drag&drop для reorder. Верхнее — стартовый экран."""
    order_changed = Signal(list)           # список индексов в новом порядке
    screen_selected = Signal(int)
    request_context_action = Signal(int, str)  # (index, action)

    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(16,16))
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.itemSelectionChanged.connect(self._emit_selected)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def dropEvent(self, e):
        super().dropEvent(e)
        # собрать новый порядок
        idxs = []
        for i in range(self.count()):
            item = self.item(i)
            idxs.append(item.data(Qt.UserRole))
        self.order_changed.emit(idxs)

    def populate(self, screens: list[ScreenDef], current_idx: int|None):
        self.clear()
        for i, s in enumerate(screens):
            it = QListWidgetItem(f"{s.title} ({s.c_name})")
            # цветной маркер иконки — цвет фона окна
            pm = QIcon()
            it.setIcon(_color_icon(s.bg_color))
            it.setData(Qt.UserRole, i)
            self.addItem(it)
        if current_idx is not None and 0 <= current_idx < self.count():
            self.setCurrentRow(current_idx)

    def _emit_selected(self):
        row = self.currentRow()
        if row >= 0:
            self.screen_selected.emit(row)

    def _menu(self, pos):
        item = self.itemAt(pos)
        m = QMenu(self)
        act_new = m.addAction("New Screen")
        if item:
            act_ren = m.addAction("Rename…")
            act_del = m.addAction("Delete")
        act = m.exec(self.mapToGlobal(pos))
        if act is None: return
        if act.text() == "New Screen":
            self.request_context_action.emit(-1, "new")
        elif item and act.text() == "Rename…":
            self.request_context_action.emit(item.data(Qt.UserRole), "rename")
        elif item and act.text() == "Delete":
            self.request_context_action.emit(item.data(Qt.UserRole), "delete")

class WidgetsTree(QTreeWidget):
    """Средний блок: древовидные виджеты выбранного окна."""
    widget_selected = Signal(object)           # QTreeWidgetItem
    request_add_widget = Signal(object)        # к кому добавить (узел/корень)
    request_context_action = Signal(object, str)

    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Widget", "Type", "id"])
        self.itemSelectionChanged.connect(self._sel)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def _sel(self):
        items = self.selectedItems()
        if items:
            self.widget_selected.emit(items[0])

    def populate(self, screen: ScreenDef):
        self.clear()
        def add_node(parent, w: WidgetNode):
            it = QTreeWidgetItem([w.props.get("name", w.type), w.type, w.id])
            it.setData(0, Qt.UserRole, w)
            (parent.addChild(it) if parent else self.addTopLevelItem(it))
            for c in w.children:
                add_node(it, c)
        for w in screen.widgets:
            add_node(None, w)
        self.expandToDepth(1)

    def current_widget_node(self) -> Optional[WidgetNode]:
        it = self.currentItem()
        return it.data(0, Qt.UserRole) if it else None

    def _menu(self, pos):
        it = self.itemAt(pos)
        m = QMenu(self)
        act_add = m.addAction("Add →")
        sub = QMenu("Widget", m)
        # Подтипов много — это пример. Список можно расширять/конфигурировать.
        for typ in ["lv_btn", "lv_label", "lv_line", "lv_img", "lv_arc", "lv_bar"]:
            sub.addAction(typ)
        act_add.setMenu(sub)
        if it:
            m.addSeparator()
            act_ren = m.addAction("Rename…")
            act_del = m.addAction("Delete")
        act = m.exec(self.viewport().mapToGlobal(pos))
        if act is None: return
        if act.parent() == sub:
            self.request_context_action.emit(it, f"add:{act.text()}")
        elif it and act.text() == "Rename…":
            self.request_context_action.emit(it, "rename")
        elif it and act.text() == "Delete":
            self.request_context_action.emit(it, "delete")

class VarsList(QListWidget):
    """Нижний блок: переменные контекста (окно или выбранный виджет)."""
    request_context_action = Signal(str)   # 'add','rename','delete','type'

    def __init__(self):
        super().__init__()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def populate(self, vars_: list[VarDef]):
        self.clear()
        for v in vars_:
            it = QListWidgetItem(f"{v.name} : {v.vtype}  ({v.c_name})")
            it.setData(Qt.UserRole, v)
            self.addItem(it)

    def _menu(self, pos):
        m = QMenu(self)
        a_add = m.addAction("Add variable…")
        a_ren = m.addAction("Rename…")
        a_typ = m.addAction("Change type…")
        a_del = m.addAction("Delete")
        act = m.exec(self.mapToGlobal(pos))
        if not act: return
        if act == a_add: self.request_context_action.emit("add")
        elif act == a_ren: self.request_context_action.emit("rename")
        elif act == a_typ: self.request_context_action.emit("type")
        elif act == a_del: self.request_context_action.emit("delete")

def _color_icon(hex_color: str) -> QIcon:
    from PySide6.QtGui import QPixmap, QPainter, QColor
    pm = QPixmap(16,16); pm.fill(Qt.transparent)
    p = QPainter(pm); p.fillRect(0,0,16,16, QColor(hex_color)); p.end()
    return QIcon(pm)

# ------------------ Сборка док-панели ------------------

class LeftDock(QDockWidget):
    screen_changed = Signal(int)     # индекс выбранного экрана
    widget_changed = Signal(object)  # выбранный виджет (WidgetNode) или None
    vars_context_changed = Signal(object)  # текущий контекст для переменных

    def __init__(self, proj_path: Path):
        super().__init__("Project")
        self.model = ProjectModel.new_default()
        self.path = proj_path

        root = QWidget(); self.setWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(6,6,6,6); lay.setSpacing(8)

        # Блок 1: Окна
        gb1 = QGroupBox("Windows")
        l1 = QVBoxLayout(gb1)
        self.screens = ScreensList()
        l1.addWidget(self.screens)
        lay.addWidget(gb1)

        # Блок 2: Виджеты
        gb2 = QGroupBox("Widgets (selected window)")
        l2 = QVBoxLayout(gb2)
        self.widgets = WidgetsTree()
        l2.addWidget(self.widgets)
        lay.addWidget(gb2, 1)

        # Блок 3: Переменные
        gb3 = QGroupBox("Variables (context)")
        l3 = QVBoxLayout(gb3)
        self.varslist = VarsList()
        l3.addWidget(self.varslist)
        lay.addWidget(gb3)

        # связи
        self.screens.screen_selected.connect(self._on_screen_selected)
        self.screens.order_changed.connect(self._on_reorder_screens)
        self.screens.request_context_action.connect(self._on_screen_menu)

        self.widgets.widget_selected.connect(self._on_widget_selected)
        self.widgets.request_context_action.connect(self._on_widget_menu)

        self.varslist.request_context_action.connect(self._on_vars_menu)

        # первичное заполнение
        self.current_screen_idx: int = 0
        self.current_widget_node: Optional[WidgetNode] = None
        self.refresh_all()

    # ---------- Заполнение UI из модели ----------
    def refresh_all(self):
        self.screens.populate(self.model.screens, self.current_screen_idx)
        self._refresh_widgets()
        self._refresh_vars()

    def _refresh_widgets(self):
        screen = self.model.screens[self.current_screen_idx]
        self.widgets.populate(screen)

    def _refresh_vars(self):
        # контекст = выбранный виджет, иначе окно
        vars_ = (self.current_widget_node.vars if self.current_widget_node
                 else self.model.screens[self.current_screen_idx].vars)
        self.varslist.populate(vars_)
        self.vars_context_changed.emit(self.current_widget_node or self.model.screens[self.current_screen_idx])

    # ---------- Callbacks ----------
    def _on_screen_selected(self, idx: int):
        self.current_screen_idx = idx
        self.current_widget_node = None
        self._refresh_widgets()
        self._refresh_vars()
        self.screen_changed.emit(idx)

    def _on_reorder_screens(self, new_order_idx_list: list[int]):
        # Пересобираем список экранов согласно новому порядку:
        new_screens = [self.model.screens[i] for i in new_order_idx_list]
        self.model.screens = new_screens
        self.current_screen_idx = 0  # верхний — стартовый
        self.save_project()
        self.refresh_all()

    def _on_screen_menu(self, idx: int, action: str):
        if action == "new":
            title, ok = QInputDialog.getText(self, "New screen", "Title:")
            if not ok or not title: return
            self.model.screens.append(ScreenDef(title=title, c_name=normalize_c_identifier(f"screen_{title}")))
        elif action == "rename":
            s = self.model.screens[idx]
            title, ok = QInputDialog.getText(self, "Rename screen", "Title:", text=s.title)
            if ok and title:
                s.title = title
                # c_name не трогаем автоматически, чтобы не ломать привязки; добавим кнопку «Rename code name» отдельно при желании
        elif action == "delete":
            if len(self.model.screens) <= 1:
                QMessageBox.warning(self, "Can't delete", "At least one screen is required.")
                return
            del self.model.screens[idx]
            self.current_screen_idx = 0
        self.save_project()
        self.refresh_all()

    def _on_widget_selected(self, item: QTreeWidgetItem):
        self.current_widget_node = item.data(0, Qt.UserRole)
        self.widget_changed.emit(self.current_widget_node)
        self._refresh_vars()

    def _on_widget_menu(self, item: QTreeWidgetItem|None, action: str):
        screen = self.model.screens[self.current_screen_idx]
        parent_node = (item.data(0, Qt.UserRole) if item else None)
        if action.startswith("add:"):
            wtype = action.split(":",1)[1]
            new_id = normalize_c_identifier(f"{wtype}_{len(screen.widgets)+1}")
            node = WidgetNode(id=new_id, type=wtype, props={"name": wtype})
            if parent_node:
                parent_node.children.append(node)
            else:
                screen.widgets.append(node)
        elif action == "rename" and item:
            node = item.data(0, Qt.UserRole)
            new_name, ok = QInputDialog.getText(self, "Rename widget", "Display name:", text=node.props.get("name", node.type))
            if ok and new_name:
                node.props["name"] = new_name
        elif action == "delete" and item:
            node = item.data(0, Qt.UserRole)
            # удалить node из дерева
            def remove_from(lst: List[WidgetNode]) -> bool:
                for i, n in enumerate(lst):
                    if n is node:
                        del lst[i]; return True
                    if remove_from(n.children): return True
                return False
            remove_from(screen.widgets)
        self.save_project()
        self._refresh_widgets()
        self._refresh_vars()

    def _on_vars_menu(self, action: str):
        # контекст — виджет или окно
        ctx = self.current_widget_node or self.model.screens[self.current_screen_idx]
        var_list = ctx.vars
        if action == "add":
            name, ok = QInputDialog.getText(self, "Add variable", "Name:")
            if not ok or not name: return
            vtype, ok2 = QInputDialog.getText(self, "Type", "Type (e.g. int, bool, float, string):", text="int")
            if not ok2: return
            var_list.append(VarDef(name=name, c_name=normalize_c_identifier(name), vtype=vtype))
        elif action in ("rename","type","delete"):
            it = self.varslist.currentItem()
            if not it: return
            v: VarDef = it.data(Qt.UserRole)
            if action == "rename":
                name, ok = QInputDialog.getText(self, "Rename variable", "Name:", text=v.name)
                if ok and name:
                    v.name = name
                    # code name не меняем автоматически
            elif action == "type":
                vtype, ok = QInputDialog.getText(self, "Type", "Type:", text=v.vtype)
                if ok and vtype: v.vtype = vtype
            elif action == "delete":
                var_list.remove(v)
        self.save_project()
        self._refresh_vars()

    # ---------- IO ----------
    def save_project(self):
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / ".lvproj").mkdir(exist_ok=True)
        (self.path / "project.json").write_text(json.dumps(self.model.to_json(), indent=2), encoding="utf-8")