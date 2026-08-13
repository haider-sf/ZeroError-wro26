# steering_drive.py — smooth steering sweep
from machine import Pin, PWM
from time import sleep

# --- 1. Hardware ---
servo = PWM(Pin(0))      # servo signal on GP0 (physical pin 1)
servo.freq(50)           # hobby servos run at 50 Hz

# --- 2. Your calibrated numbers (paste YOUR real values here) ---
STEERING_CENTER    = 4665    
STEERING_LEFT_MAX  = 5640
STEERING_RIGHT_MAX = 3765

LO = min(STEERING_LEFT_MAX, STEERING_RIGHT_MAX)   # lower safe limit
HI = max(STEERING_LEFT_MAX, STEERING_RIGHT_MAX)   # upper safe limit

# --- 3. Send one position to the servo (with a safety clamp) ---
_current = STEERING_CENTER          # remembers where the servo is now

def set_steering(duty):
    global _current
    duty = max(LO, min(HI, int(duty)))   # never past the safe limits
    servo.duty_u16(duty)
    _current = duty

# --- 4. Glide smoothly from where we are to a target ---
def move_to(target, step=10, delay=0.02):
    target = max(LO, min(HI, int(target)))
    direction = step if target >= _current else -step
    for d in range(_current, target, direction):   # the tiny in-between steps
        set_steering(d)
        sleep(delay)
    set_steering(target)             # land exactly on target

# --- 5. The full smooth sweep ---
def smooth_sweep():
    move_to(STEERING_CENTER);    sleep(0.4)
    move_to(STEERING_LEFT_MAX);  sleep(0.4)
    move_to(STEERING_RIGHT_MAX); sleep(0.4)
    move_to(STEERING_CENTER)

# --- 6. Run it ---
smooth_sweep()