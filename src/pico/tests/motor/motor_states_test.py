# motor_states_test.py — test forward, reverse, coast, brake.
# Wheels OFF the ground. Buck 5V on VM. Grounds common.

from machine import Pin, PWM
import time

STBY = Pin(5, Pin.OUT, value=0)
AIN1 = Pin(3, Pin.OUT, value=0)
AIN2 = Pin(4, Pin.OUT, value=0)
pwma = PWM(Pin(2))
pwma.freq(1000)
pwma.duty_u16(0)

RUN_DUTY = 60000   # ~45% — well above your 13% floor, easy to see

def forward(duty):
    AIN1.value(1); AIN2.value(0)
    pwma.duty_u16(duty)

def reverse(duty):                 # <-- opposite diagonal
    AIN1.value(0); AIN2.value(1)
    pwma.duty_u16(duty)

def coast():                       # <-- all switches open, slow spin-down
    pwma.duty_u16(0)
    AIN1.value(0); AIN2.value(0)

def brake():                       # <-- bottom switches short motor, hard stop
    AIN1.value(1); AIN2.value(1)
    pwma.duty_u16(0)

def stop():
    pwma.duty_u16(0)
    AIN1.value(0); AIN2.value(0)
    STBY.value(0)

STBY.value(1)
try:
    print("FORWARD")
    forward(RUN_DUTY)
    time.sleep(2)

    print("COAST — watch how long it spins down")
    coast()
    time.sleep(3)                  # give it room to freewheel

    print("REVERSE")
    reverse(RUN_DUTY)
    time.sleep(2)

    print("BRAKE — should stop hard")
    brake()
    time.sleep(3)

finally:
    stop()
    print("stopped")