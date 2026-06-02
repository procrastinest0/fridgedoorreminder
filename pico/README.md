# Pico W code

## What you need

- Raspberry Pi Pico W (with headers soldered on)
- Waveshare 2.13" e-Paper HAT (B) V4 — BWR (Black/White/Red), 250×122
- A USB cable for flashing

## One-time Pico setup

### 1. Flash MicroPython

Download the latest **Pico W MicroPython UF2** from
https://micropython.org/download/RPI_PICO_W/

Hold BOOTSEL on the Pico while plugging in USB → Pico mounts as a USB drive →
drag the .uf2 file onto it. Pico reboots.

### 2. Install a tool to copy files

Easiest: **[Thonny IDE](https://thonny.org)**. Free. Works on Mac/Windows/Linux.
View → Files. Bottom-right interpreter selector → "MicroPython (Raspberry Pi Pico)".

Alternative: **[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html)**
on the command line — `pip install mpremote` then `mpremote cp file.py :file.py`.

### 3. Copy these files to the Pico

- `boot.py` — runs at boot, connects Wi-Fi, syncs time via NTP
- `main.py` — the widget loop
- `secrets.py` — Wi-Fi + server URL + token (copy from `secrets_example.py`)
- `epaper2in13bwr.py` — display driver (included in this repo)
- `renderer.py` — dashboard layout and drawing logic

### 4. Wiring / pin connections

The driver uses SPI1 with the standard Waveshare Pico e-Paper pin mapping:

| Signal | GPIO |
|--------|------|
| DC     | 8    |
| CS     | 9    |
| CLK    | 10   |
| DIN    | 11   |
| RST    | 12   |
| BUSY   | 13   |

If you're using a Waveshare Pico e-Paper HAT, just plug the Pico into the
header — no manual wiring needed.

### 5. First boot

After copying files: in Thonny, Run `main.py`. Watch the REPL output. First
boot will fail until `secrets.py` is filled in — that's expected.

## Layout reference (250×122)

The display's framebuffer uses 8×8 built-in font. Each char is 8 px wide,
8 px tall. So:
- 250/8 = **31 chars per line max**
- 122/8 = **15 lines tall**

We use 2 px padding so usable area is more like 30 chars × 13 rows.

Red is used for: divider lines, the next-event marker, and overdue reminders.
