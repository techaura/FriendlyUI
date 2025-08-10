# src/friendlyui/widgets_registry.py
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple

# .../src/friendlyui  -> parents[2] == корень FriendlyUI
ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

def _abs_icon(rel: Optional[str]) -> Optional[str]:
    if not rel:
        return None
    p = ASSETS_DIR / rel
    return str(p) if p.exists() else None

def load_widget_groups(lvgl_version: str):
    """
    Возвращает словарь {group_name: [(widget_type, tag, icon_path|None), ...]}
    """
    fname = "widgets_v9.json" if str(lvgl_version).lower().startswith("v9") else "widgets_v8.json"
    path = ASSETS_DIR / fname
    if not path.exists():
        path = ASSETS_DIR / "widgets_v8.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    groups = {}

    # v8: группы как ключи словаря
    if fname.endswith("v8.json"):
        for gname, items_raw in data.items():
            items = []
            for w in items_raw:
                icon_path = ASSETS_DIR / w["icon"] if "icon" in w else None
                items.append((w["type"], w.get("tag", w["type"][:4].upper()), icon_path))
            groups[gname] = items

    # v9: "groups" — список объектов
    else:
        for group in data.get("groups", []):
            gname = group["name"]
            items = []
            for w in group.get("widgets", []):
                icon_path = ASSETS_DIR / w["icon"] if "icon" in w else None
                items.append((w["type"], w.get("tag", w["type"][:4].upper()), icon_path))
            groups[gname] = items

    return groups
