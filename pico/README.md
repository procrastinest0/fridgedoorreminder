# Pico W code

## What you need

- Raspberry Pi Pico W (with headers soldered on)
- Waveshare Pico-ePaper-2.9 (V4) — the one designed to plug into the Pico
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
- `epaper2in9.py` — Waveshare display driver

### 4. Get the e-ink driver

Download `Pico_ePaper-2.9.py` from Waveshare's wiki:
https://www.waveshare.com/wiki/Pico-ePaper-2.9

Rename to `epaper2in9.py` and copy to the Pico. (We import it as that name.)

### 5. Plug the e-ink onto the Pico

The Waveshare 2.9" Pico-ePaper has the Pico's pin header on the back. Just
press the Pico into it. No wiring.

### 6. First boot

After copying files: in Thonny, Run `main.py`. Watch the REPL output. First
boot will fail until `secrets.py` is filled in — that's expected.

## Layout reference (296×128)

The display module's framebuffer uses 8×8 built-in font. Each char is 8 px
wide, 8 px tall. So:
- 296/8 = **37 chars per line max**
- 128/8 = **16 lines tall**

We use 2 px padding so usable area is more like 36 chars × 14 rows.
