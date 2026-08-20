#!/usr/bin/env python3
# =============================================================================
# vision.py  --  Team Zero Error, WRO 2026 Future Engineers
# Raspberry Pi 5 + Camera Module 3 Wide (imx708_wide)
#
# WHAT THIS DOES
#   Finds the nearest red or green pillar and reports its BEARING to the
#   Pico. It does not compute where the car is. That distinction is the
#   whole design: the Pico already has a working heading controller, and
#   this only nudges its setpoint.
#
#   One line per frame, newline terminated:
#
#       R,0.62,48\n      red pillar, 62% across frame, 48 px tall
#       G,0.31,72\n      green pillar
#       N,0.50,0\n       nothing seen
#
#   Human readable on purpose -- it can be watched in a terminal with no
#   decoder, and a student can debug it by eye.
#
# RULE NOTES
#   11.10  The Pi 5 has Wi-Fi and Bluetooth. Both MUST be off during a run
#          and a judge may inspect. See disable_radios.sh. Running this
#          script does not satisfy that requirement by itself.
#   Colours per section 13: red RGB (238,39,55), green RGB (68,214,44).
#   Pillars are 50 x 50 x 100 mm.
#   Appendix A section 5: passing on the wrong side is recoverable until
#   the vehicle crosses the radius line at that pillar. Late correction is
#   legal, so this does not need to commit early.
#
# RUN
#   python3 vision.py            normal
#   python3 vision.py --debug    prints to console, no serial required
# =============================================================================

import sys
import time

import cv2
import numpy as np
from picamera2 import Picamera2

DEBUG = "--debug" in sys.argv

# ================================================================ CONSTANTS

PORT = "/dev/ttyAMA0"
BAUD = 115200

WIDTH, HEIGHT = 640, 480      # small on purpose: latency beats resolution
TARGET_FPS    = 15            # 67 ms cadence, well inside the Pico's needs

# --- colour gates, HSV -------------------------------------------------
# [UNTUNED ON TRACK] Derived from the rule book RGB values. Competition
# lighting will differ from the workshop. Re-run calibrate_colour.py under
# venue lighting before the first round and record the numbers.
#
# Red wraps around the hue origin, so it needs two ranges.
RED_LO_1  = np.array([  0, 120,  70])
RED_HI_1  = np.array([ 10, 255, 255])
RED_LO_2  = np.array([170, 120,  70])
RED_HI_2  = np.array([180, 255, 255])
GREEN_LO  = np.array([ 40,  80,  60])
GREEN_HI  = np.array([ 85, 255, 255])

MIN_AREA_PX  = 300            # ignore specks
ROI_TOP      = 0.35           # ignore the top of the frame: ceiling, walls
MIN_ASPECT   = 0.8            # pillar is 50 x 100 mm, so taller than wide
MAX_ASPECT   = 4.0


# ================================================================== SERIAL

class Link:
    """Serial writer that never raises. If the port dies the vision loop
    keeps running and the Pico falls back to wall following on its own
    staleness timeout."""

    def __init__(self):
        self.ser = None
        if DEBUG:
            return
        try:
            import serial
            self.ser = serial.Serial(PORT, BAUD, timeout=0.05)
            time.sleep(0.3)
            self.ser.reset_output_buffer()
            print("serial up on %s" % PORT)
        except Exception as e:
            print("serial FAILED (%s) -- continuing without it" % e)

    def send(self, text):
        if self.ser is None:
            if DEBUG:
                print(text.strip())
            return
        try:
            self.ser.write(text.encode())
        except Exception:
            pass


# ================================================================ DETECTION

def largest_blob(mask, y_floor):
    """Return (x_centre, height_px, area) of the biggest valid blob, or None.

    Blobs are filtered on area, vertical position and aspect ratio. The
    aspect test is what rejects the mat's own coloured markings, which are
    flat on the floor and therefore wide rather than tall."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_area = MIN_AREA_PX

    for c in contours:
        area = cv2.contourArea(c)
        if area < best_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if y + h < y_floor:
            continue                       # too high in frame to be a pillar
        if w == 0:
            continue
        aspect = h / float(w)
        if aspect < MIN_ASPECT or aspect > MAX_ASPECT:
            continue
        best = (x + w / 2.0, h, area)
        best_area = area

    return best


def find_pillar(frame):
    """Nearest pillar as (colour, x_norm, height_px), or None.

    'Nearest' is approximated by blob height. The pillar is a known 100 mm
    tall object, so a taller blob is a closer one -- no range sensor
    needed. When both colours are visible the taller one wins, because
    that is the one the car must act on first."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    y_floor = int(HEIGHT * ROI_TOP)

    red = cv2.bitwise_or(cv2.inRange(hsv, RED_LO_1, RED_HI_1),
                         cv2.inRange(hsv, RED_LO_2, RED_HI_2))
    green = cv2.inRange(hsv, GREEN_LO, GREEN_HI)

    # Opening removes speckle; closing fills gaps where a pillar edge is
    # shaded. Both use a small kernel so a distant pillar is not erased.
    k = np.ones((5, 5), np.uint8)
    red   = cv2.morphologyEx(red,   cv2.MORPH_OPEN,  k)
    red   = cv2.morphologyEx(red,   cv2.MORPH_CLOSE, k)
    green = cv2.morphologyEx(green, cv2.MORPH_OPEN,  k)
    green = cv2.morphologyEx(green, cv2.MORPH_CLOSE, k)

    r = largest_blob(red,   y_floor)
    g = largest_blob(green, y_floor)

    if r is None and g is None:
        return None
    if g is None or (r is not None and r[1] >= g[1]):
        return ("R", r[0] / float(WIDTH), int(r[1]))
    return ("G", g[0] / float(WIDTH), int(g[1]))


# ====================================================================== MAIN

def main():
    link = Link()

    cam = Picamera2()
    cfg = cam.create_video_configuration(
        main={"size": (WIDTH, HEIGHT), "format": "RGB888"},
        controls={"FrameDurationLimits": (int(1e6 / TARGET_FPS),
                                          int(1e6 / TARGET_FPS))})
    cam.configure(cfg)
    cam.start()
    time.sleep(1.0)                # let auto-exposure settle
    print("camera up at %dx%d, %d fps" % (WIDTH, HEIGHT, TARGET_FPS))

    frames = 0
    hits = 0
    t_report = time.time()

    try:
        while True:
            frame = cam.capture_array()
            frames += 1

            found = find_pillar(frame)
            if found is None:
                link.send("N,0.50,0\n")
            else:
                colour, x_norm, h_px = found
                hits += 1
                link.send("%s,%.3f,%d\n" % (colour, x_norm, h_px))

            # One status line per 5 s. Useful over SSH during development,
            # harmless when nothing is attached during a run.
            if time.time() - t_report > 5.0:
                print("%d frames, %d with a pillar (%.0f%%)"
                      % (frames, hits, 100.0 * hits / max(frames, 1)))
                frames = hits = 0
                t_report = time.time()

    except KeyboardInterrupt:
        # Ctrl-C only. pkill -9 leaves the camera resource locked and needs
        # a reboot to clear.
        print("\nstopping")
    finally:
        cam.stop()
        cam.close()


if __name__ == "__main__":
    main()
