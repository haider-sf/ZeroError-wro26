# steering_drive.py — uses the calibrated numbers
from machine import Pin, PWM
from time import sleep

servo = PWM(Pin(0)); servo.freq(50)

STEERING_CENTER    = 4665     # ← paste your calibrated values
STEERING_LEFT_MAX  = 5640
STEERING_RIGHT_MAX = 3765

LO = min(STEERING_LEFT_MAX, STEERING_RIGHT_MAX)
HI = max(STEERING_LEFT_MAX, STEERING_RIGHT_MAX)

def set_steering(duty):
    """Raw clamp — a command can never stall the servo into a stop."""
    servo.duty_u16(max(LO, min(HI, duty)))

def steer(fraction):
    """The interface the autonomy code will use.
       -1.0 = full left, 0 = straight, +1.0 = full right."""
    f = max(-1.0, min(1.0, fraction))
    span = (STEERING_RIGHT_MAX - STEERING_CENTER) if f >= 0 else (STEERING_CENTER - STEERING_LEFT_MAX)
    set_steering(int(STEERING_CENTER + f * span))

def verify_sweep():
    for d in (STEERING_CENTER, STEERING_LEFT_MAX, STEERING_CENTER, STEERING_RIGHT_MAX, STEERING_CENTER):
        set_steering(d); sleep(0.6)

verify_sweep()