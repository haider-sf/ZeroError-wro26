from machine import Pin, I2C
import bno055, time

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100000)
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE)
time.sleep_ms(100)

print("Tilt through faces (accel), then hold still (gyro)...")
while True:
    c = imu.cal_status()
    print("  gyro:{} accel:{}".format(c[1], c[2]))
    if c[1] == 3 and c[2] == 3:
        break
    time.sleep(0.5)

offsets = imu.sensor_offsets()
print("\nCALIBRATION OFFSETS — copy this line:")
print(offsets)