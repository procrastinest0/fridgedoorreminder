"""
sim_render.py — Local simulator of what the Pico will draw on the 2.13" BWR display.

Run on your laptop with Pillow installed to preview the layout:

    cd server
    python -m flask --app src.app run --port 8000 &
    cd ../tools
    python sim_render.py

Generates `sim_preview.png` matching the actual 250x122 panel dimensions
and 8x8 monospace font that the MicroPython framebuf uses.
Red pixels are rendered in red to simulate the BWR panel.
"""

import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 250, 122
SCALE = 3
MAX_CHARS = (WIDTH - 4) // 8  # 30

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (200, 0, 0)


def fetch_dry_data():
    with urllib.request.urlopen("http://localhost:8000/widget.json?dry=1") as r:
        return json.loads(r.read())


def _find_mono_font():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/Library/Fonts/Andale Mono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, 8)
    return ImageFont.load_default()


def truncate(s, max_chars):
    if len(s) <= max_chars:
        return s
    return s[:max_chars - 2] + ".."


def render_sim(data):
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_WHITE)
    draw = ImageDraw.Draw(img)
    font = _find_mono_font()

    PAD = 2
    LINE_H = 10

    def text(s, x, y, color=COLOR_BLACK):
        draw.text((x, y - 1), s, font=font, fill=color)

    def hline(x, y, w, color=COLOR_BLACK):
        draw.line([(x, y), (x + w - 1, y)], fill=color, width=1)

    def rect(x, y, w, h, color=COLOR_BLACK):
        draw.rectangle([(x, y), (x + w - 1, y + h - 1)], outline=color, width=1)

    # Header
    y = PAD
    text(data.get("now", ""), PAD, y)
    time_str = data.get("now_time", "")
    text(time_str, WIDTH - PAD - len(time_str) * 8, y)
    y += LINE_H
    hline(PAD, y + 1, WIDTH - 2 * PAD, COLOR_RED)
    y += 4

    # Events
    events = data.get("events", []) or []
    if not events:
        text("No upcoming events", PAD, y)
        y += LINE_H
    else:
        for i, ev in enumerate(events[:3]):
            if y > HEIGHT - LINE_H * 4:
                break
            day = ev.get("day", "")
            t = ev.get("time", "")
            title = ev.get("title", "")
            if i == 0:
                text(">", PAD, y, COLOR_RED)
                if day == "Today":
                    head = f"  {t}  "
                else:
                    head = f"  {day} {t}  "
            else:
                if day == "Today":
                    head = f"  {t}  "
                else:
                    head = f"  {day} {t}  "
            available = MAX_CHARS - len(head)
            line = head + truncate(title, max(0, available))
            text(line, PAD, y)
            y += LINE_H

    if y < HEIGHT - LINE_H * 2:
        hline(PAD, y + 1, WIDTH - 2 * PAD, COLOR_RED)
        y += 4

    # Reminders
    reminders = data.get("reminders", []) or []
    if not reminders:
        text("No reminders", PAD, y)
    else:
        col_w = (WIDTH - 2 * PAD) // 2
        max_chars_per_col = (col_w // 8) - 2
        for i, r in enumerate(reminders[:4]):
            row = i // 2
            col = i % 2
            x = PAD + col * col_w
            ry = y + row * LINE_H
            if ry > HEIGHT - LINE_H:
                break
            title = r.get("title", "")
            due = r.get("due", "")
            overdue = due == "overdue"
            color = COLOR_RED if overdue else COLOR_BLACK
            rect(x, ry + 1, 6, 6, color)
            if overdue:
                title = "! " + title
                suffix = ""
            elif due == "today":
                suffix = " *"
            elif due == "tomorrow":
                suffix = " >"
            elif due:
                suffix = " " + due
            else:
                suffix = ""
            label_max = max_chars_per_col - len(suffix)
            label = truncate(title, max(1, label_max)) + suffix
            text(label, x + 10, ry, color)

    img = img.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.NEAREST)
    return img


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--inline":
        from datetime import datetime
        data = {
            "now": datetime.now().strftime("%a %d %b"),
            "now_time": datetime.now().strftime("%H:%M"),
            "events": [
                {"time": "16:00", "day": "Today", "title": "Standup"},
                {"time": "ALL DAY", "day": "Tomorrow", "title": "Mom's birthday"},
                {"time": "10:00", "day": "Sun", "title": "Dentist"},
            ],
            "reminders": [
                {"title": "Buy groceries", "due": "today"},
                {"title": "Call dentist", "due": "overdue"},
                {"title": "Reply to Sam", "due": ""},
                {"title": "Renew passport", "due": ""},
            ],
        }
    else:
        data = fetch_dry_data()

    img = render_sim(data)
    out = Path("sim_preview.png")
    img.save(out)
    print(f"Wrote {out.resolve()}")


if __name__ == "__main__":
    main()
