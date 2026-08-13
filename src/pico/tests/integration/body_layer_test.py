# body_layer_test.py — servo + drive motor together, one firmware.
# Wheels OFF the ground. Both bucks verified. Grounds common at star node.
# Goal: prove the two actuators run simultaneously without interfering.

from machine import Pin, PWM
import time

# ---------- SERVO (steering) on GP0, 50 Hz ----------
servo = PWM(Pin(0))
servo.freq(50)

# --- PASTE YOUR CALIBRATED VALUES HERE (duty_u16) ---
SERVO_CENTER = 4915     # your nominal center
SERVO_LEFT   = 5540     # <-- your saved LEFT_MAX
SERVO_RIGHT  = 3865     # <-- your saved RIGHT_MAX

def steer(duty):
    servo.duty_u16(duty)

# ---------- DRIVE MOTOR on GP2-GP5, 1 kHz ----------
STBY = Pin(5, Pin.OUT, value=0)
AIN1 = Pin(3, Pin.OUT, value=0)
AIN2 = Pin(4, Pin.OUT, value=0)
pwma = PWM(Pin(2))
pwma.freq(1000)
pwma.duty_u16(0)

DRIVE_DUTY = 25000      # ~38%, above your ~13% floor, gentle

def forward(duty):
    AIN1.value(1); AIN2.value(0)
    pwma.duty_u16(duty)

def reverse(duty):
    AIN1.value(0); AIN2.value(1)
    pwma.duty_u16(duty)

def motor_stop():
    pwma.duty_u16(0)
    AIN1.value(0); AIN2.value(0)

def all_stop():
    motor_stop()
    STBY.value(0)
    steer(SERVO_CENTER)

# ---------- TEST SEQUENCE ----------
STBY.value(1)
try:
    # 1. Center steering, motor off — baseline
    print("center, motor off")
    steer(SERVO_CENTER)
    time.sleep(1)

    # 2. Steering only — sweep with motor OFF (isolates steering)
    print("steer left"); steer(SERVO_LEFT);   time.sleep(1)
    print("center");     steer(SERVO_CENTER); time.sleep(1)
    print("steer right"); steer(SERVO_RIGHT); time.sleep(1)
    print("center");     steer(SERVO_CENTER); time.sleep(1)

    # 3. Motor only — drive with steering CENTERED (isolates motor)
    print("motor forward, centered")
    forward(DRIVE_DUTY); time.sleep(2)
    motor_stop();        time.sleep(1)

    # 4. BOTH together — the real test: steer while driving
    print("forward + steer left")
    forward(DRIVE_DUTY); steer(SERVO_LEFT);   time.sleep(1.5)
    print("forward + steer right")
    steer(SERVO_RIGHT);  time.sleep(1.5)
    print("forward + center")
    steer(SERVO_CENTER); time.sleep(1)

    # 5. Reverse while centered
    print("reverse, centered")
    motor_stop(); time.sleep(0.3)
    reverse(DRIVE_DUTY); time.sleep(1.5)

finally:
    all_stop()
    print("all stop")