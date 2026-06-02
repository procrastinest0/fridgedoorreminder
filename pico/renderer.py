"""
renderer.py — Draw the dashboard onto the e-ink framebuffer.

The Waveshare Pico-ePaper-2.9 driver gives us an `EPD_2in9_Landscape` (or
similar) class whose framebuffer is a `framebuf.FrameBuffer` we can draw into
with the standard `text(s, x, y, color)`, `line()`, `rect()`, etc.

Built-in font is 8x8. Display is 296x128 in landscape:
  - 37 chars wide max
  - 16 lines tall max

Layout (with 2 px padding):
  Row 0:    "Wed 06 May              14:32"           header
  Row 1:    ───────────────────────────────           divider
  Row 2:    "> 16:00  Standup"                        next event (highlighted)
  Row 3:    "  Tomorrow ALL DAY  Mom's birthday"
  Row 4:    "  Sun 10:00  Dentist"
  Row 5:    ───────────────────────────────           divider
  Row 6-7:  Two rows of two reminders each (4 total)

`epd` is the display object. We draw, then call epd.display(epd.buffer).
"""

# These constants are in pixels
WIDTH = 296
HEIGHT = 128
LINE_H = 10           # 8px font + 2px gap
PAD = 2

BLACK = 0x00
WHITE = 0xFF


def _truncate(s, max_chars):
    """Truncate a string with '..' if too long."""
    if len(s) <= max_chars:
        return s
    return s[:max_chars - 2] + ".."


def render(epd, data):
    """
    epd: Waveshare display object (framebuffer-compatible)
    data: dict from the server's /widget.json — keys: now, now_time, events, reminders
    """
    epd.fill(WHITE)

    # ─── Header ─────────────────────────────────────────────
    y = PAD
    now_str = data.get("now", "")
    time_str = data.get("now_time", "")
    epd.text(now_str, PAD, y, BLACK)
    # Right-align time: each char is 8 px wide
    time_x = WIDTH - PAD - len(time_str) * 8
    epd.text(time_str, time_x, y, BLACK)
    y += LINE_H

    # Divider
    epd.hline(PAD, y + 1, WIDTH - 2 * PAD, BLACK)
    y += 4

    # ─── Events ─────────────────────────────────────────────
    events = data.get("events", []) or []
    if not events:
        epd.text("No upcoming events", PAD, y, BLACK)
        y += LINE_H
    else:
        # First (next) event gets a "▶" marker (using ">" since 8x8 font is ASCII)
        for i, ev in enumerate(events[:3]):
            if y > HEIGHT - LINE_H * 4:
                break
            prefix = "> " if i == 0 else "  "
            day = ev.get("day", "")
            t = ev.get("time", "")
            title = ev.get("title", "")

            # Build line: "> Today 16:00  Standup" — but skip "Today" if it IS today
            # to save space (everyone knows "today")
            if i == 0 and day == "Today":
                head = f"{prefix}{t}  "
            else:
                head = f"{prefix}{day} {t}  "

            # Trim title to fit remaining width (37 chars total)
            available = 37 - len(head)
            line = head + _truncate(title, max(0, available))
            epd.text(line, PAD, y, BLACK)
            y += LINE_H

    # ─── Divider ────────────────────────────────────────────
    if y < HEIGHT - LINE_H * 2:
        epd.hline(PAD, y + 1, WIDTH - 2 * PAD, BLACK)
        y += 4

    # ─── Reminders (2 columns × up to 2 rows = 4 max) ───────
    reminders = data.get("reminders", []) or []
    if not reminders:
        epd.text("No reminders", PAD, y, BLACK)
    else:
        col_w = (WIDTH - 2 * PAD) // 2
        max_chars_per_col = (col_w // 8) - 2  # leave room for "[] " prefix
        for i, r in enumerate(reminders[:4]):
            row = i // 2
            col = i % 2
            x = PAD + col * col_w
            ry = y + row * LINE_H
            if ry > HEIGHT - LINE_H:
                break

            # Checkbox: 6x6 square outline
            epd.rect(x, ry + 1, 6, 6, BLACK)

            # Build label. Due suffix is short — use a leading "!" for overdue
            # and abbreviate to save space.
            title = r.get("title", "")
            due = r.get("due", "")
            if due == "overdue":
                # Prefix "!" marker; overdue is the most important signal
                title = "! " + title
                suffix = ""
            elif due == "today":
                suffix = " *"
            elif due == "tomorrow":
                suffix = " >"
            elif due:
                suffix = " " + due  # date like "06 May"
            else:
                suffix = ""

            # Reserve space for suffix when truncating
            label_max = max_chars_per_col - len(suffix)
            label = _truncate(title, max(1, label_max)) + suffix
            epd.text(label, x + 10, ry, BLACK)

    # Push to display
    epd.display(epd.buffer)


# Legend for the symbols used in reminder labels:
#   "!"  prefix  → overdue
#   " *" suffix  → due today
#   " >" suffix  → due tomorrow
#   " 06 May"    → other date
