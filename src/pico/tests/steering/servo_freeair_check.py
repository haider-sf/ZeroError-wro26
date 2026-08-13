# servo_freeair_check.py — servo health, NO linkage attached
from machine import Pin, PWM
from time import sleep

servo = PWM(Pin(0))
servo.freq(50)

def go(duty):
    print("duty =", duty)
    servo.duty_u16(duty)
    sleep(0.6)

go(4650)             # electrical center (~1.5 ms)
go(3600); go(4650)   # toward one side and back
go(6200); go(4650)   # the other side and back