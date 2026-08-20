# =============================================================================
# main.py  --  STRAIGHT-LINE HOLD, PI CONTROLLER
# Team Zero Error, WRO 2026 Future Engineers
#
# THE TWO CONVENTIONS, BOTH MEASURED, BOTH OPPOSITE
#   Heading:      turning RIGHT increases it   (clockwise-positive)
#   Pulse width:  increasing it steers LEFT
# Because they run opposite ways, the gain enters with a MINUS sign.
#
#   Car drifts right -> heading up -> error negative -> minus a negative
#     raises the pulse width -> steers left -> back on line.
#
# WHY THERE IS AN INTEGRAL TERM (entry 26)
#   The steering linkage has ~60 us of backlash. Runs 8-10 starting from
#   1290 settled at command ~1226; run 6 starting from 1262 settled at
#   ~1286. Same car, same day, 60 us apart -- the wheel angle depends on
#   which way the command last moved, so NO single CENTRE_US is correct.
#   P alone cannot remove a constant bias: it needs standing error to
#   produce standing correction. The integral accumulates that correction
#   and drives the error to zero. 1262 sits near the middle of the
#   backlash band, which is why it outperformed 1290.
#
# START: 2 m mark, car squared to the wall by its BODY. The rear wheels are
# fixed, so the chassis defines the direction of travel, not the front wheels.
# =============================================================================

from machine import Pin, I2C, PWM
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import bno055

# ---------------------------------------------------------------- CONSTANTS

BUS, SDA_PIN, SCL_PIN = 1, 6, 7
SHUT_PIN = 10

# --- steering, measured ------------------------------------------------
CENTRE_US    = 1262   # band midpoint ~1256; 1290 sits OUTSIDE the band
LEFT_MAX_US  = 1480   # 20 us inside the 1500 us strain point
RIGHT_MAX_US = 1010   # 20 us inside the 990 us strain point

# --- the controller ----------------------------------------------------
KP_US_PER_DEG   = 15     # proportional. Too small = lazy. Too big = weave.
MAX_ERR_DEG     = 30     # cap the error so a wild reading cannot slam full lock

KI_US_PER_DEG_S = 0.0    # LADDER: 0 (baseline), then 3, 6, 12
I_MAX_US        = 90.0   # authority clamp, ~1.5x the observed 60 us band
I_FREEZE_DEG    = 10.0   # above this error, stop integrating (corners)
MAX_DT_S        = 0.2    # a longer gap means a stall: skip, don't integrate it

# --- drive, measured ---------------------------------------------------
FORWARD    = -1
KICK_DUTY  = 45
KICK_MS    = 300
CRUISE     = 35       # NOT a fixed speed: still accelerating at 2.5 m
TRIGGER_MM = 700      # was 500. Runs 8-10 braked in 197-223 mm, not 126.
MAX_RUN_MS = 8000
BAD_LIMIT  = 5
MAX_JUMP   = 120      # was 300 = 21x a physically possible step; too loose
BRAKE_MS   = 300
LOOP_MS    = 20       # commanded. Measured period is ~26 ms -- dt is timed.

IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

# ------------------------------------------------------------- SMALL TOOLS

def ang_diff(new, old):
    """Wrap-safe heading difference, folded into +/-180.
    Without this, a 359.9 -> 0.1 transition reads as -359.8 degrees of
    rotation instead of +0.2, and the controller slams full lock."""
    d = new - old
    if d > 180:  d -= 360
    if d < -180: d += 360
    return d

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ----------------------------------------------------------------- HARDWARE

led   = Pin("LED", Pin.OUT)
btn   = Pin(15, Pin.IN, Pin.PULL_UP)
servo = PWM(Pin(0)); servo.freq(50)
pwma  = PWM(Pin(2)); pwma.freq(1000)
ain1  = Pin(3, Pin.OUT)
ain2  = Pin(4, Pin.OUT)
stby  = Pin(5, Pin.OUT)

def steer_us(v):
    """Every steering command goes through here. Clamping to the measured
    mechanical limits means the servo can never be driven against its stop."""
    v = clamp(int(v), RIGHT_MAX_US, LEFT_MAX_US)
    servo.duty_u16(int(65535 * v / 20000))
    return v

def motor(duty, direction):
    if direction == 0:
        stby.value(0); pwma.duty_u16(0)
        ain1.value(0); ain2.value(0)
        return
    stby.value(1)
    ain1.value(1 if direction > 0 else 0)
    ain2.value(0 if direction > 0 else 1)
    pwma.duty_u16(int(65535 * duty / 100))

def brake():
    stby.value(1)
    ain1.value(1); ain2.value(1)
    pwma.duty_u16(65535)
    time.sleep_ms(BRAKE_MS)
    motor(0, 0)

motor(0, 0)
steer_us(CENTRE_US)
time.sleep_ms(300)

# ------------------------------------------------------------- SENSORS
# ToF FIRST, rebuild I2C, IMU LAST. Each PiicoDev constructor reinitialises
# the peripheral and silently breaks anything built before it -- the symptom
# is heading frozen at 0.00 with no error raised.

shut = Pin(SHUT_PIN, Pin.OUT)
shut.value(0); time.sleep_ms(100)
shut.value(1); time.sleep_ms(100)
tof = PiicoDev_VL53L1X(bus=BUS, freq=100_000, sda=SDA_PIN, scl=SCL_PIN,
                       address=0x29)
time.sleep_ms(100)

i2c = I2C(BUS, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=100_000)
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
imu.set_offsets(IMU_OFFSETS);  time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(500)

# ------------------------------------------------------------- RUN NUMBER

try:
    with open("/run_n.txt") as f:
        run_n = int(f.read()) + 1
except Exception:
    run_n = 1
with open("/run_n.txt", "w") as f:
    f.write(str(run_n))

# ------------------------------------------------------------ WAIT FOR START
# Rule 9.11: power on first, then ONE button press starts the run.

while btn.value() == 1:
    led.toggle()
    time.sleep_ms(300)

time.sleep_ms(50)
while btn.value() == 0:
    time.sleep_ms(10)

led.on()
time.sleep(2)

# The target is captured HERE, by the program, on the button press.
# Nothing about the car's placement enters as data (Rule 9.9).
target = imu.euler()[0]

# --------------------------------------------------------------------- RUN

log = open("/run_log.csv", "a")
log.write("# run {}, centre {}, Kp {}, Ki {}, duty {}, target {:.2f}\n".format(
          run_n, CENTRE_US, KP_US_PER_DEG, KI_US_PER_DEG_S, CRUISE, target))
log.write("t_ms,dist,status,rejected,heading,error,integral,steer\n")

reason      = "timeout"
bad_streak  = 0
prev        = None
integral_us = 0.0                      # accumulated bias correction
t0          = time.ticks_ms()
t_prev      = t0                       # for measured dt

try:
    motor(KICK_DUTY, FORWARD)
    time.sleep_ms(KICK_MS)
    motor(CRUISE, FORWARD)

    while time.ticks_diff(time.ticks_ms(), t0) < MAX_RUN_MS:

        # ------------------------------------------------ MEASURED dt
        # Timed, not assumed. LOOP_MS is 20 but the real period is ~26 ms
        # because the I2C reads take time. Integrating with the wrong dt
        # scales KI by 30% and makes the ladder meaningless.
        now    = time.ticks_ms()
        dt     = time.ticks_diff(now, t_prev) / 1000.0
        t_prev = now
        if dt > MAX_DT_S:
            dt = 0.0

        # ---------------------------------------------------- STEER
        try:
            heading = imu.euler()[0]
            # target - current, wrap-safe. Drifted right -> negative.
            err = clamp(ang_diff(target, heading), -MAX_ERR_DEG, MAX_ERR_DEG)

            # Integrate only near the target. A deliberate 90 deg turn would
            # otherwise wind this to the clamp and take seconds to unwind.
            if abs(err) < I_FREEZE_DEG:
                integral_us += KI_US_PER_DEG_S * err * dt
                integral_us = clamp(integral_us, -I_MAX_US, I_MAX_US)

            # BOTH terms carry the MINUS: heading and pulse width run in
            # opposite directions, and the integral pushes the same way as P.
            cmd = steer_us(CENTRE_US
                           - KP_US_PER_DEG * err
                           - integral_us)
        except Exception:
            heading = -999.0; err = 0.0
            cmd = steer_us(CENTRE_US)   # lost the IMU: go straight, don't guess

        # ---------------------------------------------------- WALL STOP
        try:
            d  = tof.read()
            st = tof.status
        except Exception:
            d = -1; st = "EXC"

        rejected = ""
        good = (d > 0 and st == "OK")

        if good and prev is not None and abs(d - prev) > MAX_JUMP:
            good = False
            rejected = "jump"
        elif not good:
            rejected = "status"

        log.write("{},{},{},{},{:.2f},{:.2f},{:.1f},{}\n".format(
            time.ticks_diff(time.ticks_ms(), t0), d, st, rejected,
            heading, err, integral_us, cmd))

        if good:
            prev = d
            bad_streak = 0
            if d < TRIGGER_MM:
                reason = "wall"
                break
        else:
            bad_streak += 1
            if bad_streak >= BAD_LIMIT:
                reason = "blind"
                break

        time.sleep_ms(LOOP_MS)

finally:
    brake()
    steer_us(CENTRE_US)
    time.sleep_ms(500)
    for _ in range(5):
        try:
            log.write(",{},{},final,,,,\n".format(tof.read(), tof.status))
        except Exception:
            log.write(",-1,EXC,final,,,,\n")
        time.sleep_ms(100)
    log.write(",,,{},,,,\n\n".format(reason))
    log.close()
    led.off()
