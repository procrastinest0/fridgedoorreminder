"""apple_reminders.py — Fetch incomplete reminders from iCloud via CalDAV."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

import caldav

ICLOUD_URL = "https://caldav.icloud.com/"


@dataclass
class Reminder:
    summary: str
    due: Optional[dt.datetime]
    list_name: str
    priority: int = 0

    def __lt__(self, other: "Reminder") -> bool:
        sk = (
            0 if self.due else 1,
            self.due or dt.datetime.max.replace(tzinfo=dt.timezone.utc),
            self.priority or 99,
        )
        ok = (
            0 if other.due else 1,
            other.due or dt.datetime.max.replace(tzinfo=dt.timezone.utc),
            other.priority or 99,
        )
        return sk < ok


def _extract_due(component, tz: dt.tzinfo) -> Optional[dt.datetime]:
    due = component.get("due")
    if due is None:
        return None
    val = due.dt
    if isinstance(val, dt.datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=dt.timezone.utc)
        return val.astimezone(tz)
    elif isinstance(val, dt.date):
        return dt.datetime.combine(val, dt.time(23, 59), tzinfo=tz)
    return None


def fetch_reminders(
    username: str,
    password: str,
    list_filter: List[str],
    max_reminders: int,
    tz: dt.tzinfo,
) -> List[Reminder]:
    if not username or not password:
        print("[apple_reminders] No credentials configured; skipping.")
        return []

    client = caldav.DAVClient(url=ICLOUD_URL, username=username, password=password)

    try:
        principal = client.principal()
    except Exception as e:
        print(f"[apple_reminders] Failed to connect: {e}")
        return []

    reminders: List[Reminder] = []

    for cal in principal.calendars():
        list_name = (cal.name or "").strip()
        if list_filter and list_name not in list_filter:
            continue

        try:
            todos = cal.todos(include_completed=False)
        except Exception:
            continue  # not a VTODO calendar

        for todo in todos:
            try:
                component = todo.icalendar_component
                summary = str(component.get("summary") or "(no title)")
                due = _extract_due(component, tz)
                priority = int(component.get("priority") or 0)
                if str(component.get("status") or "").upper() == "COMPLETED":
                    continue
                reminders.append(Reminder(summary, due, list_name, priority))
            except Exception as e:
                print(f"[apple_reminders] Skipping todo: {e}")
                continue

    reminders.sort()
    return reminders[:max_reminders]
