# src/friendlyui/models.py
import re, json
from pathlib import Path

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

def load_or_create_project(path: Path) -> dict:
    pj = path / "project.json"
    if pj.exists():
        try:
            return json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            pass
    path.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps(DEFAULT_PROJECT, indent=2), encoding="utf-8")
    return json.loads(json.dumps(DEFAULT_PROJECT))

def save_project(path: Path, data: dict):
    (path / "project.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
