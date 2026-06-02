"""
epaper2in13bwr.py — MicroPython driver for Waveshare 2.13" BWR (V4) e-ink display.

Controller: SSD1680
Resolution: 122 x 250 (portrait), 250 x 122 (landscape)
Colors: Black, White, Red

Pico W default SPI1 pin assignments:
  DC=8, CS=9, CLK=10, DIN=11, RST=12, BUSY=13
"""

from machine import Pin, SPI
import framebuf
import time

DC_PIN = 8
CS_PIN = 9
RST_PIN = 12
BUSY_PIN = 13

EPD_WIDTH = 122
EPD_HEIGHT = 250


class EPD_2in13_BWR_Landscape(framebuf.FrameBuffer):
    """
    Landscape-oriented driver (250 wide x 122 tall).

    Inherits FrameBuffer so callers can use .text(), .line(), .rect(), etc.
    The inherited framebuffer is the BLACK layer. Use .red_fb for red drawing.
    After drawing, call .display() to push both layers to the panel.
    """

    def __init__(self):
        self.width = EPD_HEIGHT   # 250 in landscape
        self.height = EPD_WIDTH   # 122 in landscape

        self.spi = SPI(1, baudrate=4_000_000)
        self.dc = Pin(DC_PIN, Pin.OUT)
        self.cs = Pin(CS_PIN, Pin.OUT)
        self.rst = Pin(RST_PIN, Pin.OUT)
        self.busy = Pin(BUSY_PIN, Pin.IN)

        buf_size = (EPD_WIDTH * EPD_HEIGHT + 7) // 8
        self.buffer_black = bytearray(buf_size)
        self.buffer_red = bytearray(buf_size)

        # Main framebuffer is the black layer (landscape)
        super().__init__(self.buffer_black, self.width, self.height,
                         framebuf.MONO_HLSB)

        # Red layer framebuffer — same geometry
        self.red_fb = framebuf.FrameBuffer(
            self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)

        self._init_display()

    def _send_command(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)

    def _send_data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytes([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)

    def _wait_busy(self):
        while self.busy.value() == 1:
            time.sleep_ms(10)

    def _hw_reset(self):
        self.rst.value(1)
        time.sleep_ms(20)
        self.rst.value(0)
        time.sleep_ms(2)
        self.rst.value(1)
        time.sleep_ms(20)

    def _init_display(self):
        self._hw_reset()
        self._wait_busy()

        # Software reset
        self._send_command(0x12)
        self._wait_busy()

        # Driver output control: MUX = 249 (0xF9), gate scan direction
        self._send_command(0x01)
        self._send_data(0xF9)
        self._send_data(0x00)
        self._send_data(0x00)

        # Data entry mode: X increment, Y increment
        self._send_command(0x11)
        self._send_data(0x03)

        # RAM X address range: 0 to (122/8 - 1) = 0 to 15
        self._send_command(0x44)
        self._send_data(0x00)
        self._send_data((EPD_WIDTH - 1) // 8)

        # RAM Y address range: 0 to 249
        self._send_command(0x45)
        self._send_data(0x00)
        self._send_data(0x00)
        self._send_data((EPD_HEIGHT - 1) & 0xFF)
        self._send_data(((EPD_HEIGHT - 1) >> 8) & 0xFF)

        # Border waveform control
        self._send_command(0x3C)
        self._send_data(0x05)

        # Temperature sensor: internal
        self._send_command(0x18)
        self._send_data(0x80)

        # Display update control: red normal, black normal
        self._send_command(0x21)
        self._send_data(0x80)
        self._send_data(0x80)

        # Set RAM cursor to origin
        self._send_command(0x4E)
        self._send_data(0x00)
        self._send_command(0x4F)
        self._send_data(0x00)
        self._send_data(0x00)

        self._wait_busy()

    def _set_cursor(self):
        self._send_command(0x4E)
        self._send_data(0x00)
        self._send_command(0x4F)
        self._send_data(0x00)
        self._send_data(0x00)

    def _rotate_buf(self, src):
        """Rotate landscape HLSB buffer to portrait column-major for the panel."""
        w = self.width    # 250
        h = self.height   # 122
        pw = EPD_WIDTH    # 122 (portrait width)
        row_bytes = (pw + 7) // 8
        out = bytearray(row_bytes * EPD_HEIGHT)

        for y in range(h):
            for x in range(w):
                byte_idx = y * ((w + 7) // 8) + x // 8
                bit_pos = 7 - (x % 8)
                pixel = (src[byte_idx] >> bit_pos) & 1

                # Map landscape (x, y) to portrait column
                px = h - 1 - y
                py = x
                out_idx = py * row_bytes + px // 8
                out_bit = 7 - (px % 8)
                if pixel:
                    out[out_idx] |= (1 << out_bit)

        return out

    def display(self, buf=None):
        """Send both black and red buffers to the panel and refresh."""
        black_rotated = self._rotate_buf(self.buffer_black)
        red_rotated = self._rotate_buf(self.buffer_red)

        # Write black data
        self._set_cursor()
        self._send_command(0x24)
        self._send_data(black_rotated)

        # Write red data
        self._set_cursor()
        self._send_command(0x26)
        self._send_data(red_rotated)

        # Trigger display refresh
        self._send_command(0x20)
        self._wait_busy()

    def clear(self, color=0xFF):
        """Fill both layers to white (no black, no red)."""
        for i in range(len(self.buffer_black)):
            self.buffer_black[i] = color
            self.buffer_red[i] = 0x00  # 0 = no red
        self.display()

    def sleep(self):
        """Put the panel into deep sleep to save power."""
        self._send_command(0x10)
        self._send_data(0x01)
        time.sleep_ms(100)
        self.rst.value(0)
