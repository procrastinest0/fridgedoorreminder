"""
google_calendar.py — Fetch upcoming events.

Reads OAuth credentials from token.json in the project root.
You generate this once on your laptop with auth_setup.py, then scp it
to the phone.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = PROJECT_ROOT / "token.json"


@dataclass
class CalendarEvent:
    summary: str
    start: dt.datetime
    end: dt.datetime
    all_day: bool

    def __lt__(self, other: "CalendarEvent") -> bool:
        return self.start < other.start


def _load_credentials() -> Credentials:
    """Load creds from token.json. Refresh access token if needed."""
    if not TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"{TOKEN_PATH} not found. Run auth_setup.py on your laptop, then "
            f"scp token.json to ~/widget/ on the phone."
        )

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    if not creds.valid:
        raise RuntimeError("Google credentials are invalid; re-run auth_setup.py")

    return creds


def _parse_event_time(time_dict: dict, tz: dt.tzinfo) -> tuple[dt.datetime, bool]:
    if "dateTime" in time_dict:
        iso = time_dict["dateTime"].replace("Z", "+00:00")
        return dt.datetime.fromisoformat(iso).astimezone(tz), False
    else:
        d = dt.date.fromisoformat(time_dict["date"])
        return dt.datetime.combine(d, dt.time(0, 0), tzinfo=tz), True


def fetch_events(
    calendar_ids: List[str],
    days_ahead: int,
    max_events: int,
    tz: dt.tzinfo,
) -> List[CalendarEvent]:
    creds = _load_credentials()
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    now = dt.datetime.now(tz=dt.timezone.utc)
    time_min = now.isoformat()
    time_max = (now + dt.timedelta(days=days_ahead)).isoformat()

    events: List[CalendarEvent] = []

    for cal_id in calendar_ids:
        try:
            result = service.events().list(
                calendarId=cal_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_events * 2,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            for item in result.get("items", []):
                summary = item.get("summary", "(no title)")
                start, all_day = _parse_event_time(item["start"], tz)
                end, _ = _parse_event_time(item["end"], tz)
                events.append(CalendarEvent(summary, start, end, all_day))
        except HttpError as e:
            print(f"[google_calendar] Error fetching {cal_id}: {e}")
            continue

    events.sort()
    return events[:max_events]
