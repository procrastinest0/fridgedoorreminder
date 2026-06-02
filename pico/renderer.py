"""
renderer.py — Draw the dashboard onto the e-ink framebuffer.

Targets Waveshare 2.13" BWR (V4) via EPD_2in13_BWR_Landscape.
Display is 250x122 in landscape. Built-in font is 8x8.
  - 31 chars wide max
  - 15 lines tall max

Red is used for: overdue reminders, the "next event" marker, dividers.

Layout (with 2 px padding):
  Row 0:    "Wed 06 May              14:32"           header
  Row 1:    ───────────────────────────────           divider (red)
  Row 2:    "> 16:00  Standup"                        next event (red marker)
  Row 3:    "  Tomorrow ALL DAY  Mom's birthday"
  Row 4:    "  Sun 10:00  Dentist"
  Row 5:    ───────────────────────────────           divider (red)
  Row 6-7:  Two rows of two reminders each (4 total)
"""

WIDTH = 250
HEIGHT = 122
LINE_H = 10
PAD = 2
MAX_CHARS = (WIDTH - 2 * PAD) // 8  # 30

BLACK = 0x00
WHITE = 0xFF


def _truncate(s, max_chars):
    if len(s) <= max_chars:
        return s
    return s[:max_chars - 2] + ".."


def render(epd, data):
    """
    epd: EPD_2in13_BWR_Landscape instance (black fb + epd.red_fb)
    data: dict from /widget.json — keys: now, now_time, events, reminders
    """
    epd.fill(WHITE)
    epd.red_fb.fill(0x00)

    red = epd.red_fb

    # ─── Header ─────────────────────────────────────────────
    y = PAD
    now_str = data.get("now", "")
    time_str = data.get("now_time", "")
    epd.text(now_str, PAD, y, BLACK)
    time_x = WIDTH - PAD - len(time_str) * 8
    epd.text(time_str, time_x, y, BLACK)
    y += LINE_H

    # Divider (red)
    red.hline(PAD, y + 1, WIDTH - 2 * PAD, 0xFF)
    y += 4

    # ─── Events ─────────────────────────────────────────────
    events = data.get("events", []) or []
    if not events:
        epd.text("No upcoming events", PAD, y, BLACK)
        y += LINE_H
    else:
        for i, ev in enumerate(events[:3]):
            if y > HEIGHT - LINE_H * 4:
                break
            day = ev.get("day", "")
            t = ev.get("time", "")
            title = ev.get("title", "")

            if i == 0:
                # Next event: red ">" marker, rest in black
                red.text(">", PAD, y, 0xFF)
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
            line = head + _truncate(title, max(0, available))
            epd.text(line, PAD, y, BLACK)
            y += LINE_H

    # ─── Divider (red) ─────────────────────────────────────
    if y < HEIGHT - LINE_H * 2:
        red.hline(PAD, y + 1, WIDTH - 2 * PAD, 0xFF)
        y += 4

    # ─── Reminders (2 columns × up to 2 rows = 4 max) ─────
    reminders = data.get("reminders", []) or []
    if not reminders:
        epd.text("No reminders", PAD, y, BLACK)
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

            # Checkbox: 6x6 square — red if overdue
            fb = red if overdue else epd
            color = 0xFF if overdue else BLACK
            fb.rect(x, ry + 1, 6, 6, color)

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
            label = _truncate(title, max(1, label_max)) + suffix

            if overdue:
                red.text(label, x + 10, ry, 0xFF)
            else:
                epd.text(label, x + 10, ry, BLACK)

    epd.display()
