"""
main.py — Wakes, fetches JSON from the server, renders, sleeps.

Runs after boot.py has connected Wi-Fi and synced time.

Power note:
  Pico W deep sleep isn't great (machine.deepsleep doesn't fully power down
  Wi-Fi). For most setups, time.sleep() between refreshes is fine if you're
  USB-powered. For battery, see comments at the bottom.
"""

import gc
import time
import json
import machine

import urequests as requests
import secrets
import renderer

# Import the Waveshare driver. The exact class name depends on the file
# you downloaded — check the bottom of Waveshare's Pico_ePaper-2.9.py
# for the example. The 2.9" V4 driver typically exposes:
#   EPD_2in9_Landscape  — for 296x128 landscape
# If your driver uses a different name, change this line.
from epaper2in9 import EPD_2in9_Landscape as EPD


def fetch_data():
    headers = {"X-Widget-Token": secrets.WIDGET_TOKEN}
    print(f"[main] GET {secrets.WIDGET_URL}")
    r = requests.get(secrets.WIDGET_URL, headers=headers, timeout=30)
    try:
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:100]}")
        data = r.json()
    finally:
        r.close()
    return data


def show_error(epd, message):
    """Render an error message centred, in case the fetch fails."""
    epd.fill(0xFF)
    epd.text("Widget error:", 4, 4, 0)
    # Wrap the message at ~36 chars per line
    y = 24
    for i in range(0, len(message), 36):
        epd.text(message[i:i + 36], 4, y, 0)
        y += 10
        if y > 110:
            break
    epd.display(epd.buffer)


def refresh_once():
    """One full cycle: init display, fetch, render, sleep display."""
    epd = EPD()
    try:
        data = fetch_data()
        renderer.render(epd, data)
        print("[main] Rendered OK")
    except Exception as e:
        print(f"[main] Error: {e}")
        try:
            show_error(epd, str(e))
        except Exception as inner:
            print(f"[main] Could not show error: {inner}")

    # Put the display to sleep — saves power, prolongs panel life.
    try:
        epd.sleep()
    except Exception:
        pass

    # Free any leftover buffers
    del epd
    gc.collect()


def main():
    while True:
        try:
            refresh_once()
        except Exception as e:
            print(f"[main] Unhandled error: {e}")

        print(f"[main] Sleeping for {secrets.REFRESH_INTERVAL}s")
        time.sleep(secrets.REFRESH_INTERVAL)


if __name__ == "__main__":
    main()


# ─── Battery / deep sleep notes ───────────────────────────────────────────
#
# To run on battery for weeks instead of days, replace `time.sleep(...)` with
# a deep sleep + reboot. The trick on Pico W: full Wi-Fi-off deep sleep needs
# `machine.deepsleep(ms)` which resets the chip on wake, so main.py runs
# again from scratch (boot.py reconnects Wi-Fi).
#
#   import machine
#   machine.deepsleep(secrets.REFRESH_INTERVAL * 1000)
#
# The catch: deep sleep on Pico W isn't as power-efficient as on dedicated
# low-power MCUs. Expect days-to-weeks on a 2000mAh LiPo, not months.
