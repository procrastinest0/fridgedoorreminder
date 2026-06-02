"""
config.py — Reads settings from environment variables.

In Termux, these are loaded from `.env` by the boot script (`set -a && . ./.env`).
For local dev, you can also export them manually before running.
"""

import os

# --- iCloud / Apple Reminders ---
ICLOUD_USERNAME = os.environ.get("ICLOUD_USERNAME", "")
ICLOUD_APP_PASSWORD = os.environ.get("ICLOUD_APP_PASSWORD", "")

# Comma-separated. Empty = all lists.
REMINDER_LISTS = [
    s.strip() for s in os.environ.get("REMINDER_LISTS", "").split(",")
    if s.strip()
]

# --- Google Calendar ---
GOOGLE_CALENDAR_IDS = [
    s.strip() for s in os.environ.get("GOOGLE_CALENDAR_IDS", "primary").split(",")
    if s.strip()
]

# --- Auth on the API itself ---
# The Pico must send this in the X-Widget-Token header.
# Generate something like: python -c "import secrets; print(secrets.token_urlsafe(32))"
WIDGET_TOKEN = os.environ.get("WIDGET_TOKEN", "")

# --- Output shape ---
MAX_EVENTS = int(os.environ.get("MAX_EVENTS", "5"))
MAX_REMINDERS = int(os.environ.get("MAX_REMINDERS", "6"))
DAYS_AHEAD = int(os.environ.get("DAYS_AHEAD", "7"))

# --- Locale ---
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")

# --- Cache ---
# Cache the digested JSON for this many seconds before refetching.
# 2 minutes is fine on a local server; bump up if you want to reduce
# Google API calls.
CACHE_TTL = int(os.environ.get("CACHE_TTL", "120"))
