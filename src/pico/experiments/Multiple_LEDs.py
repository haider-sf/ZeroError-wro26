from machine import Pin
from time import sleep

# Three LEDs on three different pins
led1 = Pin(15, Pin.OUT)
led2 = Pin(14, Pin.OUT)
led3 = Pin(13, Pin.OUT)

# A VARIABLE that controls the timing — change ONE number, change everything
blink_speed = 0.3      # seconds

while True:
    led1.value(1); sleep(blink_speed); led1.value(0)
    led2.value(1); sleep(blink_speed); led2.value(0)
    led3.value(1); sleep(blink_speed); led3.value(0)