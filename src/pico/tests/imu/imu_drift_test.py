# imu_drift_test.py — measure gyro drift properly
# Put the board on a RIGID surface. Don't touch it or the desk once it starts.

from machine import Pin, I2C
import bno055, time

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100000)
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE)
time.sleep_ms(100)

# ---- Phase 1: wait for gyro calibration ----

print("Calibrate: hold STILL for gyro, then TILT through several faces for accel...")
while True:
    c = imu.cal_status()
    print("  sys:{} gyro:{} accel:{} mag:{}".format(c[0], c[1], c[2], c[3]))
    if c[1] == 3 and c[2] == 3:        # BOTH gyro and accel
        print("Gyro + accel calibrated.")
        break
    time.sleep(0.5)
# ---- Phase 2: settle ----
print("Settling for 5 s — hands off...")
time.sleep(5)

# ---- Phase 3: 60 s drift measurement ----
start_heading = imu.euler()[0]
t_start = time.ticks_ms()
print("START heading: {:.2f}".format(start_heading))
print("Measuring 60 s — DO NOT TOUCH\n")

last_report = 0
while True:
    elapsed = time.ticks_diff(time.ticks_ms(), t_start) / 1000

    if elapsed >= 60:
        break

    # report every 10 s
    if elapsed - last_report >= 10:
        h = imu.euler()[0]
        # handle 359/0 wraparound
        d = h - start_heading
        if d > 180:  d -= 360
        if d < -180: d += 360
        print("  t={:4.0f}s   heading={:7.2f}   drift={:+7.2f} deg".format(elapsed, h, d))
        last_report = elapsed

    time.sleep(0.1)

# ---- Result ----
end_heading = imu.euler()[0]
drift = end_heading - start_heading
if drift > 180:  drift -= 360
if drift < -180: drift += 360

c = imu.cal_status()
print("\n" + "="*45)
print("START heading : {:.2f}".format(start_heading))
print("END heading   : {:.2f}".format(end_heading))
print("DRIFT in 60 s : {:+.2f} degrees".format(drift))
print("DRIFT RATE    : {:+.2f} deg/min".format(drift))
print("cal at end    : sys:{} gyro:{} accel:{} mag:{}".format(c[0], c[1], c[2], c[3]))
print("="*45)