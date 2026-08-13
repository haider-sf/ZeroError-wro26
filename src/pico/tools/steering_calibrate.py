# steering_calibrate.py — interactive steering calibration (Pico + servo)
# Run in Thonny, then type commands in the Shell.

from machine import Pin, PWM

# ---- Section 1: hardware + safety ----
servo = PWM(Pin(0))        # servo signal on GP0 (physical pin 1)
servo.freq(50)             # hobby servos run at 50 Hz

# Typo fence: whatever you type, the servo is never commanded outside this.
# Normal hobby range is ~3277-6554; this is just a guardrail against fat-fingers.
DUTY_MIN, DUTY_MAX = 2500, 7500
STEP = 25                  # how far each +/- nudge moves the servo

pos = 4915                 # start at nominal center (~1.5 ms)
center = left = right = None

def apply(duty):
    duty = max(DUTY_MIN, min(DUTY_MAX, duty))   # clamp to the fence
    servo.duty_u16(duty)
    return duty

# ---- Section 2: interactive loop ----
def calibrate():
    global pos, center, left, right
    pos = apply(pos)
    print("Commands: +/- nudge | ++/-- big nudge | a number = jump there")
    print("          c=center  l=left  r=right  0=relax  s=show  q=quit")
    while True:
        cmd = input("cmd> ").strip()
        if   cmd == "+":  pos = apply(pos + STEP)
        elif cmd == "-":  pos = apply(pos - STEP)
        elif cmd == "++": pos = apply(pos + STEP * 4)
        elif cmd == "--": pos = apply(pos - STEP * 4)
        elif cmd == "c":  center = pos; print("CENTER =", center)
        elif cmd == "l":  left   = pos; print("LEFT   =", left)
        elif cmd == "r":  right  = pos; print("RIGHT  =", right)
        elif cmd == "0":  servo.duty_u16(0); print("relaxed (no pulse)"); continue
        elif cmd == "s":  print("pos", pos, "| C", center, "L", left, "R", right); continue
        elif cmd == "q":  break
        else:
            try:    pos = apply(int(cmd))
            except ValueError: print("?"); continue
        print("  duty =", pos)
    print("\n--- paste these into your drive file ---")
    print("STEERING_CENTER    =", center)
    print("STEERING_LEFT_MAX  =", left)
    print("STEERING_RIGHT_MAX =", right)

calibrate()
