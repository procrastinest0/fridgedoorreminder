"""
sim_render.py — Local simulator of what the Pico will draw.

Not deployed anywhere. Run on your laptop with Pillow installed to preview
the layout before flashing the Pico:

    cd server
    python -m flask --app src.app run --port 8000 &
    cd ../tools
    python sim_render.py

Generates `sim_preview.png` matching the actual 296x128 panel dimensions
and 8x8 monospace font that the MicroPython framebuf uses.
"""

import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 296, 128
SCALE = 3  # upscale for visibility


def fetch_dry_data():
    """Fetch the dry-run JSON from a locally running server."""
    with urllib.request.urlopen("http://localhost:8000/widget.json?dry=1") as r:
        return json.loads(r.read())


# We mimic MicroPython's framebuf 8x8 font using a real monospace TTF
# at size 8. Pillow doesn't ship the exact same font, but the *cell size*
# is what matters for layout — 8 px wide × 8 px tall.

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


def render_sim(data):
    img = Image.new("1", (WIDTH, HEIGHT), 1)  # 1 = white
    draw = ImageDraw.Draw(img)
    font = _find_mono_font()

    PAD = 2
    LINE_H = 10

    def text(s, x, y):
        draw.text((x, y - 1), s, font=font, fill=0)

    def hline(x, y, w):
        draw.line([(x, y), (x + w - 1, y)], fill=0, width=1)

    def rect(x, y, w, h):
        draw.rectangle([(x, y), (x + w - 1, y + h - 1)], outline=0, width=1)

    def truncate(s, max_chars):
        if len(s) <= max_chars:
            return s
        return s[:max_chars - 2] + ".."

    # Header
    y = PAD
    text(data.get("now", ""), PAD, y)
    time_str = data.get("now_time", "")
    text(time_str, WIDTH - PAD - len(time_str) * 8, y)
    y += LINE_H
    hline(PAD, y + 1, WIDTH - 2 * PAD)
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
            prefix = "> " if i == 0 else "  "
            day = ev.get("day", "")
            t = ev.get("time", "")
            title = ev.get("title", "")
            if i == 0 and day == "Today":
                head = f"{prefix}{t}  "
            else:
                head = f"{prefix}{day} {t}  "
            available = 37 - len(head)
            line = head + truncate(title, max(0, available))
            text(line, PAD, y)
            y += LINE_H

    if y < HEIGHT - LINE_H * 2:
        hline(PAD, y + 1, WIDTH - 2 * PAD)
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
            rect(x, ry + 1, 6, 6)
            title = r.get("title", "")
            due = r.get("due", "")
            if due == "overdue":
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
            text(label, x + 10, ry)

    # Upscale for visibility
    img = img.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.NEAREST)
    return img


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--inline":
        # Use inline fake data instead of hitting server
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
