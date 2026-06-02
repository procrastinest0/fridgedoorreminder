"""
boot.py — Runs once at power-on. Connects Wi-Fi and syncs time via NTP.

We isolate Wi-Fi setup here so main.py can assume it's online and the
RTC has the correct UTC time.
"""

import network
import ntptime
import time
import machine

import secrets


def connect_wifi(timeout_s=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("[boot] Already connected:", wlan.ifconfig())
        return wlan

    print(f"[boot] Connecting to {secrets.WIFI_SSID}...")
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)

    deadline = time.ticks_add(time.ticks_ms(), timeout_s * 1000)
    while not wlan.isconnected():
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            raise RuntimeError("Wi-Fi connect timed out")
        time.sleep(0.5)

    print("[boot] Wi-Fi connected:", wlan.ifconfig())
    return wlan


def sync_time(retries=3):
    """Set Pico's RTC to UTC via NTP. Pico has no battery-backed clock."""
    for attempt in range(retries):
        try:
            ntptime.settime()
            now = time.localtime()
            print(f"[boot] NTP synced: {now}")
            return True
        except Exception as e:
            print(f"[boot] NTP attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    print("[boot] NTP sync failed; continuing anyway")
    return False


# Run on import (boot.py executes automatically before main.py)
try:
    connect_wifi()
    sync_time()
except Exception as e:
    print(f"[boot] FATAL: {e}")
    # Sleep 30s and reboot — let the watchdog/restart loop handle it
    time.sleep(30)
    machine.reset()
