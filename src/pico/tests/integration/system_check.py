# =============================================================================
# system_check.py  --  full system, WHEELS UP ON THE BLOCK
# Team Zero Error, WRO 2026 Future Engineers
#
# Everything on the rebuilt car, exercised in one pass. This is the last check
# before the car touches the floor again after the rebuild.
#
# CAR MUST BE RESTRAINED. The motor runs at 45% during the last phase.
# =============================================================================

from machine import Pin, I2C, PWM
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import bno055

BUS, SDA_PIN, SCL_PIN = 1, 6, 7
SHUT_PIN = 10

FORWARD      = -1
CENTRE_US    = 1275
LEFT_MAX_US  = 1480
RIGHT_MAX_US = 1010

IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

def ang_diff(new, old):
    d = new - old
    if d > 180:  d -= 360
    if d < -180: d += 360
    return d

# ------------------------------------------------------------- HARDWARE

led   = Pin("LED", Pin.OUT)
btn   = Pin(15, Pin.IN, Pin.PULL_UP)
servo = PWM(Pin(0)); servo.freq(50)
pwma  = PWM(Pin(2)); pwma.freq(1000)
ain1  = Pin(3, Pin.OUT); ain2 = Pin(4, Pin.OUT); stby = Pin(5, Pin.OUT)

def steer_us(v):
    v = max(RIGHT_MAX_US, min(LEFT_MAX_US, v))
    servo.duty_u16(int(65535 * v / 20000))

def motor(duty, direction):
    if direction == 0:
        stby.value(0); pwma.duty_u16(0); ain1.value(0); ain2.value(0); return
    stby.value(1)
    ain1.value(1 if direction > 0 else 0)
    ain2.value(0 if direction > 0 else 1)
    pwma.duty_u16(int(65535 * duty / 100))

motor(0, 0)
steer_us(CENTRE_US)
time.sleep_ms(300)

# ------------------------------------------------------- 1. SENSORS UP
# ToF FIRST, then rebuild I2C, then IMU LAST. Each PiicoDev constructor
# reinitialises the peripheral and silently breaks anything made before it.

print("--- sensors")
shut = Pin(SHUT_PIN, Pin.OUT)
shut.value(0); time.sleep_ms(100)
shut.value(1); time.sleep_ms(100)
tof = PiicoDev_VL53L1X(bus=BUS, freq=100_000, sda=SDA_PIN, scl=SCL_PIN,
                       address=0x29)
time.sleep_ms(100)

i2c = I2C(BUS, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=100_000)
print("  bus:", [hex(a) for a in i2c.scan()], " expect ['0x28', '0x29']")

imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
imu.set_offsets(IMU_OFFSETS);  time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(500)
cal = list(imu.cal_status())
print("  IMU mode:", imu.mode(), " cal[g,a]:", cal[1:3], " expect 8, [3, 3]")

# ------------------------------------------------------- 2. BUTTON
print("\n--- button: press it (LED blinking)")
while btn.value() == 1:
    led.toggle(); time.sleep_ms(300)
time.sleep_ms(50)
while btn.value() == 0:
    time.sleep_ms(10)
led.on()
print("  pressed")

# ------------------------------------------------------- 3. SERVO SWEEP
print("\n--- servo: watch the wheels, listen for strain")
for v, name in ((CENTRE_US, "centre"), (LEFT_MAX_US, "left max"),
                (CENTRE_US, "centre"), (RIGHT_MAX_US, "right max"),
                (CENTRE_US, "centre")):
    print("  {} ({} us)".format(name, v))
    steer_us(v)
    time.sleep(1.5)

# ------------------------------------------------- 4. MOTOR + LIVE SENSORS
# The real question: do the sensors still behave with the motor running?
# This repeats the interference test in miniature on the rebuilt wiring.

print("\n--- motor phases, sensors live")
zero = imu.euler()[0]

for duty, secs in ((0, 3), (25, 4), (35, 4), (45, 4), (0, 3)):
    print("\n  duty {}%".format(duty))
    motor(duty, FORWARD) if duty else motor(0, 0)
    t0 = time.ticks_ms()
    bad = 0; n = 0
    while time.ticks_diff(time.ticks_ms(), t0) < secs * 1000:
        try:
            h = imu.euler()[0]
            d = tof.read(); st = tof.status
        except Exception:
            bad += 1; n += 1; time.sleep_ms(100); continue
        n += 1
        if not (d > 0 and st == "OK"):
            bad += 1
        if n % 5 == 0:
            print("    hdg={:7.2f} drift={:+6.2f} dist={:5d} {}".format(
                  h, ang_diff(h, zero), d, st))
        time.sleep_ms(100)
    print("    bad reads: {}/{}".format(bad, n))

motor(0, 0)
steer_us(CENTRE_US)
led.off()

print("\n--- done. Motor off, servo centred.")
print("Check: driver cool? servo cool? heading drift near zero?")
