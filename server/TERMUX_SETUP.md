# Running the server on Android (Termux)

A step-by-step guide for hosting the widget server on an old / spare Android
phone. The whole thing takes ~1 evening if it's your first time with Termux.

## 1. Install Termux from F-Droid (NOT the Play Store)

The Play Store version of Termux has been abandoned since 2020 and many
packages won't work on it. You need the F-Droid version.

1. On the phone, open a browser and go to https://f-droid.org
2. Download the F-Droid APK. Install it (you'll need to allow installs from
   "unknown sources" — Android prompts you).
3. Open F-Droid, search for **Termux**, install.
4. Also install **Termux:Boot** (separate app on F-Droid) — needed in
   step 8 to auto-start the server when the phone reboots.
5. Open Termux. You'll see a Linux-ish prompt. You're in.

## 2. Install Python and dependencies

In Termux:

```bash
pkg update && pkg upgrade -y
pkg install -y python git openssh nano libffi openssl rust
```

The `rust` package is needed because some Python crypto deps build native
code on Termux. Takes a few minutes the first time.

```bash
pip install --upgrade pip
pip install flask google-auth google-auth-oauthlib google-api-python-client caldav
```

> **Heads up:** `caldav` pulls in `lxml`, which can be slow to build on
> Termux. If it fails, run `pkg install libxml2 libxslt` first, then retry
> the pip install.

## 3. Get the project onto the phone

Easiest: SSH-in from your laptop. In Termux:

```bash
pkg install openssh
sshd                         # starts the SSH daemon on port 8022
passwd                       # set a password for SSH
ifconfig | grep inet          # find the phone's IP, e.g. 192.168.1.42
```

From your laptop:

```bash
scp -P 8022 -r calendar-widget-termux/server u0_a123@192.168.1.42:~/widget
```

(`u0_a123` is your Termux username — `whoami` in Termux shows it.)

Or just `git clone` directly from Termux if you've pushed the project to a repo.

## 4. Get your Google + iCloud credentials

### Google OAuth

Run `auth_setup.py` on your **laptop** (Termux can't easily open a browser
for the OAuth dance):

```bash
cd server
pip install google-auth-oauthlib google-api-python-client
python auth_setup.py
```

Browser opens, sign in, approve. `token.json` is written.

Now copy `token.json` to the phone:

```bash
scp -P 8022 token.json u0_a123@192.168.1.42:~/widget/
```

### Apple app password

Generate at https://appleid.apple.com → Sign-In and Security →
App-Specific Passwords. Save the string somewhere; you'll paste it
into `~/widget/.env` next.

## 5. Configure the server

In Termux (or over SSH from your laptop):

```bash
cd ~/widget
nano .env
```

Paste:

```
ICLOUD_USERNAME=your_apple_id@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
WIDGET_TOKEN=your-long-random-string-here
TIMEZONE=Asia/Kolkata
GOOGLE_CALENDAR_IDS=primary
REMINDER_LISTS=
```

Generate a `WIDGET_TOKEN` with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Save the same string for the Pico's `secrets.py`.

`Ctrl+O`, `Enter`, `Ctrl+X` to save in nano.

```bash
chmod 600 .env token.json
```

## 6. Test it locally

```bash
cd ~/widget
set -a && . ./.env && set +a
python -m flask --app src.app run --host=0.0.0.0 --port=8000
```

`--host=0.0.0.0` is critical — without it, Flask only listens on `localhost`
and the Pico can't reach it.

From your laptop on the same Wi-Fi:

```bash
curl http://<phone-ip>:8000/health
# → ok

curl http://<phone-ip>:8000/widget.json?dry=1
# → fake JSON

curl -H "X-Widget-Token: your-token" http://<phone-ip>:8000/widget.json
# → real JSON
```

If it works from the laptop, the Pico will work too.

## 7. Battery & wake-lock

Without these, Android will freeze Termux within minutes of the screen
going off and the widget will go stale.

**a. Acquire a wake-lock in Termux:**

```bash
termux-wake-lock
```

(You'll see a persistent notification — that's normal. It tells Android
"I'm doing something important, don't kill me.")

**b. Disable battery optimization for Termux:**

Android Settings → Apps → Termux → Battery → "Unrestricted" (or
"Don't optimize" depending on Android version). Do the same for **Termux:Boot**.

**c. Optional but recommended — keep the screen lock-screen instead of off:**

Settings → Display → Screen timeout. Some phones aggressively suspend Wi-Fi
when the screen is fully off. If you see the widget go stale every few
hours, this is usually why. A 30-second timeout that just locks (not
sleeps) often helps.

## 8. Auto-start on reboot

You installed **Termux:Boot** in step 1 — now we use it. Termux:Boot runs
scripts in `~/.termux/boot/` when the phone boots.

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-widget.sh
```

Paste:

```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/widget
set -a && . ./.env && set +a
exec python -m flask --app src.app run --host=0.0.0.0 --port=8000 \
    >> ~/widget/server.log 2>&1
```

Make it executable:

```bash
chmod +x ~/.termux/boot/start-widget.sh
```

**Important:** Open the Termux:Boot app at least once (just tap its icon
in your launcher) — Android won't run boot scripts until the app has been
launched manually after install. This trips up everyone.

Now reboot the phone. Server should auto-start.

## 9. Reserve the phone's IP in your router

Phones get a new IP from the router every time they reconnect. If the IP
changes, the Pico can't find the server.

Two fixes:

**Easier — DHCP reservation:** Log into your router (usually
`http://192.168.1.1` or `192.168.0.1`). Find DHCP/LAN settings, look for
"DHCP reservation" or "static lease". Find the phone in the connected
clients list, copy its MAC address, and reserve a fixed IP for it
(e.g., `192.168.1.50`). From now on the phone always gets that IP.

**Alternative — mDNS:** Termux doesn't ship mDNS by default, and Android's
own mDNS can be flaky. Skip this unless you can't access your router.

## 10. Verify it survives a reboot

1. Reboot the phone.
2. Wait 30 seconds.
3. From your laptop: `curl http://<phone-ip>:8000/health` should return `ok`.

If not:
- Open Termux manually — does the boot script log show errors?
  `cat ~/widget/server.log`
- Did you open Termux:Boot at least once?
- Is battery optimization actually off for both Termux apps?

## 11. Configure the Pico

Edit `pico/secrets.py`:

```python
WIFI_SSID = "YourWiFi"
WIFI_PASSWORD = "..."
WIDGET_URL = "http://192.168.1.50:8000/widget.json"  # <-- phone's IP, http not https
WIDGET_TOKEN = "your-long-random-string-here"        # <-- same as .env
REFRESH_INTERVAL = 15 * 60
```

Note `http://` (not `https://`) — local network, no TLS needed. The Pico's
TLS stack would actually struggle with self-signed certs anyway.

## Common problems

**Pico can't reach phone, but laptop can.**
The Pico is on a different Wi-Fi band/network. Some routers segment 2.4GHz
and 5GHz into different subnets, or have "guest network isolation" enabled.
Make sure both devices are on the same SSID and that "AP isolation" is
disabled.

**Server dies overnight.**
Usually one of three things: wake-lock dropped (re-run `termux-wake-lock`),
battery optimization turned itself back on (some phones do this after OS
updates — re-disable it), or the phone unplugged and ran out of charge.

**`pip install caldav` fails.**
Install `pkg install libxml2 libxslt` first, then retry.

**OAuth fails on first run with "redirect_uri_mismatch".**
Run `auth_setup.py` on your laptop, not on the phone. Only `token.json`
needs to live on the phone.

**Logs.**
`tail -f ~/widget/server.log` to watch live. Flask prints each request,
so you'll see the Pico's hits in real time.
