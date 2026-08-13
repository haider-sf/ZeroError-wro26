# main.py — first untethered floor run, button-started
from machine import Pin, PWM
import time

FORWARD    = -1
MAX_DUTY   = 40
MAX_RUN_MS = 3000

led  = Pin("LED", Pin.OUT)
btn  = Pin(15, Pin.IN, Pin.PULL_UP)      # pressed reads 0

pwma = PWM(Pin(2)); pwma.freq(1000)
ain1 = Pin(3, Pin.OUT); ain2 = Pin(4, Pin.OUT); stby = Pin(5, Pin.OUT)

def motor(duty_pct, direction):
    if direction == 0:
        stby.value(0); pwma.duty_u16(0); ain1.value(0); ain2.value(0); return
    stby.value(1)
    ain1.value(1 if direction > 0 else 0)
    ain2.value(0 if direction > 0 else 1)
    pwma.duty_u16(int(65535 * min(duty_pct, MAX_DUTY) / 100))

motor(0, 0)                               # safe state first, always

# --- wait for the button, blinking slowly so you know it's alive ---
while btn.value() == 1:
    led.toggle()
    time.sleep_ms(300)

time.sleep_ms(50)                         # debounce: ignore contact bounce
while btn.value() == 0:                   # wait for release before moving
    time.sleep_ms(10)

led.on()                                  # solid = running
time.sleep(2)                             # hands clear

t0 = time.ticks_ms()
try:
    motor(40, FORWARD)
    while time.ticks_diff(time.ticks_ms(), t0) < MAX_RUN_MS:
        time.sleep_ms(20)
finally:
    motor(0, 0)
    led.off()