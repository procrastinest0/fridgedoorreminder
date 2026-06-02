"""
app.py — Flask service.

Endpoints:
  GET /health                Plaintext "ok". For uptime pingers.
  GET /widget.json           The data the Pico fetches. Auth: X-Widget-Token header.
  GET /widget.json?dry=1     Returns fake data; doesn't hit Google/iCloud. No auth.

Run locally:
  cd server
  pip install -r requirements.txt
  GOOGLE_TOKEN_JSON=...  ICLOUD_USERNAME=...  ICLOUD_APP_PASSWORD=... \
      WIDGET_TOKEN=devtoken  python -m flask --app src.app run --port 8000

Or use --dry-run mode (no auth needed):
  python -m flask --app src.app run --port 8000
  curl http://localhost:8000/widget.json?dry=1
"""

from __future__ import annotations

import datetime as dt
import time
import traceback
from typing import Any
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, abort

from . import config
from .google_calendar import CalendarEvent, fetch_events
from .apple_reminders import Reminder, fetch_reminders

app = Flask(__name__)

# Tiny in-process cache so we don't hammer Google/iCloud on every request.
_cache: dict[str, Any] = {"data": None, "expires_at": 0.0}


def _format_event_time(ev: CalendarEvent, tz: dt.tzinfo) -> str:
    """Return 'ALL DAY' or 'HH:MM' (24h)."""
    if ev.all_day:
        return "ALL DAY"
    return ev.start.astimezone(tz).strftime("%H:%M")


def _day_label(d: dt.date, today: dt.date) -> str:
    """'Today', 'Tomorrow', 'Fri', or '06 May'."""
    delta = (d - today).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    if 0 < delta < 7:
        return d.strftime("%a")
    return d.strftime("%d %b")


def _due_label(due: dt.datetime, now: dt.datetime) -> str:
    """'today', 'tomorrow', 'overdue', '06 May'."""
    today = now.date()
    if due < now:
        return "overdue"
    if due.date() == today:
        return "today"
    if due.date() == today + dt.timedelta(days=1):
        return "tomorrow"
    return due.strftime("%d %b")


def _build_payload(dry: bool = False) -> dict:
    tz = ZoneInfo(config.TIMEZONE)
    now = dt.datetime.now(tz)

    if dry:
        events = _fake_events(tz)
        reminders = _fake_reminders(tz)
        errors: list[str] = []
    else:
        events, reminders, errors = [], [], []
        try:
            events = fetch_events(
                calendar_ids=config.GOOGLE_CALENDAR_IDS,
                days_ahead=config.DAYS_AHEAD,
                max_events=config.MAX_EVENTS,
                tz=tz,
            )
        except Exception as e:
            traceback.print_exc()
            errors.append(f"calendar: {e}")

        try:
            reminders = fetch_reminders(
                username=config.ICLOUD_USERNAME,
                password=config.ICLOUD_APP_PASSWORD,
                list_filter=config.REMINDER_LISTS,
                max_reminders=config.MAX_REMINDERS,
                tz=tz,
            )
        except Exception as e:
            traceback.print_exc()
            errors.append(f"reminders: {e}")

    today = now.date()

    return {
        "now": now.strftime("%a %d %b"),         # "Wed 06 May"
        "now_time": now.strftime("%H:%M"),        # "14:32"
        "events": [
            {
                "time": _format_event_time(ev, tz),
                "day": _day_label(ev.start.astimezone(tz).date(), today),
                "title": ev.summary,
            }
            for ev in events
        ],
        "reminders": [
            {
                "title": r.summary,
                "due": _due_label(r.due, now) if r.due else "",
            }
            for r in reminders
        ],
        "errors": errors,
    }


def _fake_events(tz: dt.tzinfo) -> list[CalendarEvent]:
    now = dt.datetime.now(tz)
    today_4pm = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return [
        CalendarEvent("Standup", today_4pm, today_4pm + dt.timedelta(minutes=30), False),
        CalendarEvent("Mom's birthday",
                      today_4pm + dt.timedelta(days=1),
                      today_4pm + dt.timedelta(days=2), True),
        CalendarEvent("Dentist",
                      (today_4pm + dt.timedelta(days=2)).replace(hour=10),
                      (today_4pm + dt.timedelta(days=2)).replace(hour=11), False),
    ]


def _fake_reminders(tz: dt.tzinfo) -> list[Reminder]:
    now = dt.datetime.now(tz)
    return [
        Reminder("Buy groceries", now + dt.timedelta(hours=4), "Personal"),
        Reminder("Call dentist", now - dt.timedelta(days=1), "Personal"),
        Reminder("Reply to Sam", None, "Work"),
        Reminder("Renew passport", None, "Personal"),
    ]


# ─── Routes ───────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return "ok\n", 200, {"Content-Type": "text/plain"}


@app.route("/widget.json")
def widget():
    dry = request.args.get("dry") == "1"

    # Auth — except for dry mode (used for testing without secrets)
    if not dry:
        token = request.headers.get("X-Widget-Token", "")
        if not config.WIDGET_TOKEN or token != config.WIDGET_TOKEN:
            abort(401)

    # Cache (skip cache for dry mode so we always see fresh fake data)
    now_ts = time.time()
    if not dry and _cache["data"] is not None and now_ts < _cache["expires_at"]:
        return jsonify(_cache["data"])

    payload = _build_payload(dry=dry)

    if not dry:
        _cache["data"] = payload
        _cache["expires_at"] = now_ts + config.CACHE_TTL

    return jsonify(payload)


@app.route("/")
def index():
    return (
        "Calendar Widget API. "
        "Try /health, /widget.json (with X-Widget-Token), or /widget.json?dry=1\n",
        200, {"Content-Type": "text/plain"},
    )
