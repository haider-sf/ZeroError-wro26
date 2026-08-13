from machine import Pin, PWM
from time import sleep

# Set up PWM on the servo's signal pin at 50 Hz (standard for servos)
servo = PWM(Pin(0))
servo.freq(50)

# A VARIABLE controls the angle — same idea as blink_speed, but now it's ANGLE
# These duty numbers set the pulse width → the servo angle
CENTER = 4915     # roughly middle
LEFT   = 3400     # one side
RIGHT  = 6400     # other side


for duty in range(3400, 6400, 50):
    servo.duty_u16(duty)
    sleep(0.02)
    
    for duty in range(6400, 3400, 50):
    servo.duty_u16(duty)
    sleep(0.02)