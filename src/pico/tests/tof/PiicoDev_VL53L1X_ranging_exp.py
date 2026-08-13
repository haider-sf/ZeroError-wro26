from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import time

tof = PiicoDev_VL53L1X(bus=0, sda=8, scl=9)

try:
    while True:
        d = tof.read()
        print(d, "mm", "|", tof.status)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("stopped")