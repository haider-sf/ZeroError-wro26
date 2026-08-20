# pin_test.py — GPIO health check. NOTHING may be connected to these pins.
# Disconnect the driver, servo, and button before running. An external
# pull-up or pull-down will produce a false result.
from machine import Pin
import time

PINS = (0, 2, 3, 4, 5, 6, 7, 10, 15)

print("Confirm nothing is wired to any of these pins.\n")
bad = []
for gp in PINS:
    p = Pin(gp, Pin.OUT)
    p.value(0); time.sleep_ms(20); lo = Pin(gp, Pin.IN).value()
    p = Pin(gp, Pin.OUT)
    p.value(1); time.sleep_ms(20); hi = Pin(gp, Pin.IN).value()
    ok = (lo == 0 and hi == 1)
    if not ok: bad.append(gp)
    print("  GP{:<3} low={} high={}  {}".format(gp, lo, hi, "OK" if ok else "<-- FAULT"))

# GP9 is known dead (1.08 V when driven low). Included as a control:
# if this test does NOT flag it, the test itself is not sensitive enough.
p = Pin(9, Pin.OUT)
p.value(0); time.sleep_ms(20); lo = Pin(9, Pin.IN).value()
p = Pin(9, Pin.OUT)
p.value(1); time.sleep_ms(20); hi = Pin(9, Pin.IN).value()
print("  GP9   low={} high={}  (known dead — control)".format(lo, hi))

print("\nfaults: {}".format(bad if bad else "none"))
