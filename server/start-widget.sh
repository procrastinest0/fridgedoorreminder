#!/data/data/com.termux/files/usr/bin/bash
#
# start-widget.sh — Auto-starts the widget server when the phone boots.
#
# INSTALL:
#   1. Install the Termux:Boot app from F-Droid
#   2. Open Termux:Boot once (just tap its icon — required by Android)
#   3. Copy this file to ~/.termux/boot/start-widget.sh
#   4. chmod +x ~/.termux/boot/start-widget.sh
#   5. Make sure ~/widget/.env exists and is filled in
#
# After a phone reboot, the server will be running on port 8000.
# Logs go to ~/widget/server.log.

# Acquire wake-lock so Android doesn't suspend us
termux-wake-lock

cd ~/widget || exit 1

# Load .env into environment
set -a
. ./.env
set +a

# Start the server. Using exec so this script becomes the server process.
exec python -m flask --app src.app run --host=0.0.0.0 --port=8000 \
    >> ~/widget/server.log 2>&1
