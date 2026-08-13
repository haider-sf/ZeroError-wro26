from machine import Pin, I2C
import bno055, time

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100000)
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE)
time.sleep_ms(50)

try:
    while True:
        heading, roll, pitch = imu.euler()
        print("heading: {:7.2f}   roll: {:6.1f}   pitch: {:6.1f}".format(heading, roll, pitch))
        time.sleep(0.2)
except KeyboardInterrupt:
    print("stopped")