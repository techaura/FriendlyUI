# tools/generate_icons.py
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 96, 72  # базовый размер
BG = "#3a3c42"
FG = "#e6e6e6"
ACCENT = "#3584e4"
MUTED = "#c0c0c0"

def svg_wrap(body):
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="{W}" height="{H}" rx="8" ry="8" fill="{BG}"/>
{body}
</svg>'''

def save(name, body):
    p = OUT / f"{name}.svg"
    p.write_text(svg_wrap(body), encoding="utf-8")
    print("wrote", p)

# --- primitives ---
def text_lines(y0=22, lines=2, gap=10, w1=60, w2=40):
    parts = []
    for i in range(lines):
        width = w1 if i == 0 else w2
        parts.append(f'<rect x="18" y="{y0+i*gap}" width="{width}" height="6" rx="3" fill="{FG}" opacity="0.9"/>')
    return "\n".join(parts)

def button(x=18,y=22,w=60,h=20):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{ACCENT}"/>' \
           f'<rect x="{x+12}" y="{y+7}" width="{w-24}" height="6" rx="3" fill="white" opacity="0.9"/>'

def slider():
    return f'''
<rect x="16" y="{H//2-2}" width="{W-32}" height="4" rx="2" fill="{MUTED}"/>
<circle cx="{W//2+10}" cy="{H//2}" r="9" fill="{ACCENT}"/>
'''

def switch():
    return f'''
<rect x="26" y="{H//2-10}" width="{W-52}" height="20" rx="10" fill="{MUTED}"/>
<circle cx="{W//2+18}" cy="{H//2}" r="9" fill="{ACCENT}"/>
'''

def checkbox():
    return f'''
<rect x="20" y="22" width="18" height="18" rx="4" stroke="{FG}" fill="none" stroke-width="2"/>
<path d="M24 30 L28 34 L36 24" stroke="{ACCENT}" stroke-width="3" fill="none" stroke-linecap="round"/>
<rect x="42" y="24" width="34" height="6" rx="3" fill="{FG}"/>
'''

def roller():
    return f'''
<rect x="{W//2-20}" y="14" width="40" height="{H-28}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<rect x="{W//2-18}" y="{H//2-10}" width="36" height="20" rx="4" fill="{ACCENT}"/>
<rect x="{W//2-14}" y="{H//2-2}" width="28" height="4" rx="2" fill="white" opacity="0.9"/>
'''

def dropdown():
    return f'''
<rect x="16" y="24" width="{W-32}" height="22" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<rect x="24" y="32" width="46" height="6" rx="3" fill="{FG}"/>
<path d="M {W-34} 32 l 6 0 l -3 6 z" fill="{FG}"/>
'''

def label():
    return text_lines(y0=30, lines=1, gap=10, w1=60)

def line():
    return f'<path d="M 18 {H-18} L {W-18} 18" stroke="{ACCENT}" stroke-width="4" stroke-linecap="round"/>'

def img():
    return f'''
<rect x="16" y="16" width="{W-32}" height="{H-32}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<path d="M 24 {H-24} L 42 40 L 54 {H-32} L {W-28} {H-24} L {W-36} 28 Z"
      stroke="{ACCENT}" fill="none" stroke-width="2"/>
<circle cx="36" cy="30" r="4" fill="{FG}"/>
'''

def bar():
    return f'''
<rect x="20" y="20" width="8" height="32" fill="{MUTED}"/>
<rect x="34" y="28" width="8" height="24" fill="{ACCENT}"/>
<rect x="48" y="24" width="8" height="28" fill="{MUTED}"/>
<rect x="62" y="18" width="8" height="34" fill="{MUTED}"/>
'''

def arc():
    return f'''
<path d="M 24 {H-24} A 24 24 0 1 1 {W-24} {H-24}" stroke="{MUTED}" stroke-width="6" fill="none" opacity="0.5"/>
<path d="M 24 {H-24} A 24 24 0 0 1 {W//2} 18" stroke="{ACCENT}" stroke-width="6" fill="none"/>
'''

def table():
    return f'''
<rect x="16" y="16" width="{W-32}" height="{H-32}" rx="4" fill="#2f3136" stroke="#4b4e55"/>
<path d="M 16 {H//2} H {W-16} M {W//2} 16 V {H-16}" stroke="{FG}" opacity="0.5"/>
'''

def canvas(): return img()
def span():   return text_lines(y0=24, lines=3, gap=10, w1=56, w2=40)
def keyboard():
    keys = []
    x0, y0, w, h, gap = 16, 28, 10, 8, 4
    for r in range(3):
        for c in range(7):
            x = x0 + c*(w+gap); y = y0 + r*(h+gap)
            keys.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{FG}" opacity="0.8"/>')
    return "\n".join(keys)

def textarea():
    return f'''
<rect x="16" y="16" width="{W-32}" height="{H-32}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
{ text_lines(y0=26, lines=3, gap=12, w1=56, w2=46) }
'''

def btnmatrix():
    # сетка кнопок 3x4
    cells = []
    x0, y0, w, h, gap = 14, 14, 14, 10, 4
    for r in range(4):
        for c in range(3):
            x = x0 + c*(w+gap); y = y0 + r*(h+gap)
            fill = ACCENT if (r==1 and c==1) else FG
            op = "0.95" if (r==1 and c==1) else "0.85"
            cells.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" opacity="{op}"/>')
    return "\n".join(cells)

def spinbox():
    return f'''
<rect x="18" y="{H//2-12}" width="{W-36}" height="24" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<rect x="26" y="{H//2-5}" width="32" height="10" rx="3" fill="{FG}" opacity="0.9"/>
<rect x="{W-34}" y="{H//2-10}" width="18" height="8" rx="2" fill="{MUTED}"/>
<rect x="{W-34}" y="{H//2+2}"  width="18" height="8" rx="2" fill="{MUTED}"/>
<path d="M {W-25} {H//2-7} l 4 0" stroke="white" stroke-width="2"/>
<path d="M {W-25} {H//2+6} l 4 0 M {W-27} {H//2+6} l 8 0" stroke="white" stroke-width="2"/>
'''

def msgbox():
    return f'''
<rect x="12" y="16" width="{W-24}" height="{H-32}" rx="8" fill="#2f3136" stroke="#4b4e55"/>
{ text_lines(y0=28, lines=2, gap=10, w1=56, w2=44) }
<rect x="{W//2-18}" y="{H-30}" width="36" height="12" rx="6" fill="{ACCENT}"/>
'''

def calendar():
    return f'''
<rect x="14" y="16" width="{W-28}" height="{H-30}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<rect x="14" y="16" width="{W-28}" height="16" rx="6" fill="{ACCENT}"/>
<g fill="{FG}">
  <rect x="22" y="40" width="10" height="8" rx="2"/><rect x="36" y="40" width="10" height="8" rx="2"/>
  <rect x="50" y="40" width="10" height="8" rx="2"/><rect x="64" y="40" width="10" height="8" rx="2"/>
  <rect x="22" y="52" width="10" height="8" rx="2"/><rect x="36" y="52" width="10" height="8" rx="2"/>
  <rect x="50" y="52" width="10" height="8" rx="2"/><rect x="64" y="52" width="10" height="8" rx="2"/>
</g>
'''

def colorwheel():
    # стилизованный круг с сегментами
    return f'''
<circle cx="{W//2}" cy="{H//2}" r="22" fill="none" stroke="#4b4e55"/>
<path d="M {W//2} {H//2} m -22 0 a 22 22 0 0 1 22 -22" stroke="#ff4d4d" stroke-width="6" fill="none"/>
<path d="M {W//2} {H//2} m 0 -22 a 22 22 0 0 1 22 22" stroke="#ffd24d" stroke-width="6" fill="none"/>
<path d="M {W//2} {H//2} m 22 0 a 22 22 0 0 1 -22 22" stroke="#4dff88" stroke-width="6" fill="none"/>
<path d="M {W//2} {H//2} m 0 22 a 22 22 0 0 1 -22 -22" stroke="#4da6ff" stroke-width="6" fill="none"/>
'''

def tabview():
    return f'''
<rect x="12" y="28" width="{W-24}" height="{H-40}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<rect x="12" y="16" width="34" height="16" rx="6" fill="{ACCENT}"/>
<rect x="48" y="16" width="34" height="16" rx="6" fill="#3a3c42"/>
<rect x="84" y="16" width="34" height="16" rx="6" fill="#3a3c42"/>
'''

def tileview():
    return f'''
<rect x="14" y="16" width="{W-28}" height="{H-32}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<rect x="20" y="22" width="28" height="20" rx="4" fill="#3a3c42"/>
<rect x="52" y="22" width="28" height="20" rx="4" fill="#3a3c42"/>
<rect x="84" y="22" width="28" height="20" rx="4" fill="#3a3c42"/>
<rect x="20" y="46" width="28" height="20" rx="4" fill="{ACCENT}"/>
'''

def list_():
    return f'''
<rect x="14" y="16" width="{W-28}" height="{H-32}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
{ text_lines(y0=24, lines=3, gap=12, w1=64, w2=56) }
'''

def menu():
    return f'''
<rect x="18" y="18" width="28" height="{H-36}" rx="4" fill="#2f3136" stroke="#4b4e55"/>
<rect x="48" y="18" width="{W-66}" height="{H-36}" rx="4" fill="#2f3136" stroke="#4b4e55"/>
<rect x="22" y="24" width="20" height="6" rx="3" fill="{FG}"/>
<rect x="52" y="24" width="40" height="6" rx="3" fill="{FG}"/>
<rect x="52" y="36" width="50" height="6" rx="3" fill="{FG}" opacity="0.8"/>
'''

def meter():
    return f'''
<circle cx="{W//2}" cy="{H//2+6}" r="20" fill="none" stroke="{MUTED}" stroke-width="6" opacity="0.5"/>
<path d="M {W//2} {H//2+6} m -20 0 a 20 20 0 0 1 40 0" stroke="{ACCENT}" stroke-width="6" fill="none"/>
<line x1="{W//2}" y1="{H//2+6}" x2="{W//2+10}" y2="{H//2-2}" stroke="white" stroke-width="2"/>
'''

def chart():
    return f'''
<rect x="14" y="16" width="{W-28}" height="{H-32}" rx="4" fill="#2f3136" stroke="#4b4e55"/>
<polyline points="20,56 28,44 36,48 44,36 52,40 60,26 68,30 76,22" fill="none" stroke="{ACCENT}" stroke-width="2"/>
<rect x="20" y="40" width="8" height="16" fill="{MUTED}"/>
<rect x="36" y="34" width="8" height="22" fill="{MUTED}"/>
<rect x="52" y="28" width="8" height="28" fill="{MUTED}"/>
'''

def animimg():
    return f'''
<rect x="16" y="16" width="{W-32}" height="{H-32}" rx="6" fill="#2f3136" stroke="#4b4e55"/>
<rect x="24" y="24" width="18" height="14" fill="{ACCENT}" opacity="0.6"/>
<rect x="46" y="30" width="18" height="14" fill="{ACCENT}" opacity="0.8"/>
<rect x="68" y="36" width="18" height="14" fill="{ACCENT}" opacity="1.0"/>
'''

def spinner():
    return f'''
<circle cx="{W//2}" cy="{H//2}" r="16" stroke="{MUTED}" stroke-width="6" fill="none" opacity="0.35"/>
<path d="M {W//2} {H//2-16} a 16 16 0 0 1 16 16" stroke="{ACCENT}" stroke-width="6" fill="none"/>
'''


ICON_DRAWERS = {
    "lv_obj":     lambda: button(22,22,52,28),           # условно пустой контейнер
    "lv_label":   label,
    "lv_btn":     button,
    "lv_img":     img,
    "lv_line":    line,
    "lv_bar":     bar,
    "lv_arc":     arc,
    "lv_slider":  slider,
    "lv_switch":  switch,
    "lv_led":     lambda: '<circle cx="48" cy="36" r="10" fill="#3aff6e"/>',
    "lv_canvas":  canvas,
    "lv_table":   table,
    "lv_span":    span,
    "lv_textarea": textarea,
    "lv_keyboard": keyboard,
    "lv_checkbox": checkbox,
    "lv_dropdown": dropdown,
    "lv_roller":   roller,
    "lv_btnmatrix": btnmatrix,
    "lv_spinbox":    spinbox,
    "lv_msgbox":     msgbox,
    "lv_calendar":   calendar,
    "lv_colorwheel": colorwheel,
    "lv_tabview":    tabview,
    "lv_tileview":   tileview,
    "lv_list":       list_,
    "lv_menu":       menu,
    "lv_meter":      meter,
    "lv_chart":      chart,
    "lv_animimg":    animimg,
    "lv_spinner":    spinner,
}

def main():
    for name, fn in ICON_DRAWERS.items():
        save(name, fn())

if __name__ == "__main__":
    main()
    