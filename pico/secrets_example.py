"""
Copy this file to `secrets.py` on the Pico and fill in your values.
secrets.py is gitignored.
"""

WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"

# Your Termux phone's local IP and port. Use plain http on the local
# network — the Pico's TLS stack struggles with self-signed certs and
# you don't need encryption for traffic that never leaves your house.
# Example: http://192.168.1.50:8000/widget.json
WIDGET_URL = "http://192.168.1.50:8000/widget.json"

# Must match WIDGET_TOKEN in the phone's .env file
WIDGET_TOKEN = "paste-your-token-here"

# How often to refresh, in seconds. The Pico sleeps between refreshes.
REFRESH_INTERVAL = 15 * 60  # 15 minutes
