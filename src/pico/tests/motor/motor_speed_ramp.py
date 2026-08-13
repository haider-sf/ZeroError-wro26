# motor_pwm_ramp.py — find the minimum duty the motor actually starts at.
# Wheels OFF the ground. Buck 5V on VM. Grounds common.

from machine import Pin, PWM
import time

STBY = Pin(5, Pin.OUT, value=0)
AIN1 = Pin(3, Pin.OUT, value=0)
AIN2 = Pin(4, Pin.OUT, value=0)
pwma = PWM(Pin(2))
pwma.freq(1000)
pwma.duty_u16(0)

def forward(duty):
    AIN1.value(0); AIN2.value(1)
    pwma.duty_u16(duty)

def stop():
    pwma.duty_u16(0)
    AIN1.value(0); AIN2.value(0)
    STBY.value(0)

STBY.value(1)
try:
    # ramp all the way up in small steps, printing each
    for duty in range(0, 65535, 2000):   # ~33 steps, full range
        forward(duty)
        pct = round(duty / 65535 * 100)
        print("duty:", duty, " (~", pct, "%)")
        time.sleep(0.4)
    time.sleep(1)
finally:
    stop()
    print("stopped")