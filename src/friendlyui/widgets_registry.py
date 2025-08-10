# src/friendlyui/widgets_registry.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

def load_widget_groups(lvgl_version: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    Возвращает словарь {group_name: [(widget_type, tag), ...], ...}
    tag — короткая подпись на плитке.
    """
    fname = "widgets_v9.json" if str(lvgl_version).lower().startswith("v9") else "widgets_v8.json"
    path = ASSETS_DIR / fname
    if not path.exists():
        # fallback на v8
        path = ASSETS_DIR / "widgets_v8.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    groups = {}
    for group in data.get("groups", []):
        gname = group["name"]
        items = []
        for w in group.get("widgets", []):
            items.append((w["type"], w.get("tag", w["type"][:4].upper())))
        groups[gname] = items
    return groups
