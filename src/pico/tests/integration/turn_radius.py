# =============================================================================
# turn_radius.py  --  full lock, stop after 180 degrees of heading
#
# WHY THIS WORKS
#   Drive a constant circle and stop after exactly half a turn. The straight
#   line from start point to end point passes through the centre of that
#   circle, so it IS the diameter. Measure it, halve it, that is R.
#
# WHAT TO MARK
#   Two dots at the start: where each REAR tyre touches the floor.
#   Two dots at the end: same two features.
#   Midpoint of the first pair to midpoint of the second pair = 2R.
#   Averaging the two wheels gives the axle centre, so no corrections apply.
#
# NO ToF here at all -- this is pure geometry, and leaving the ToF out means
# the I2C construction-order trap cannot apply.
#
# Log is written to the Pico's own flash. Do all six runs, THEN connect USB
# once and read /turn_log.csv. Each run appends its own block.
# =============================================================================

from machine import Pin, PWM, I2C
import time, bno055

# --- set this per run --------------------------------------------------
LOCK_US = 1010        # 1480 = full LEFT, 1010 = full RIGHT

TARGET_DEG = 180.0
CRUISE     = 45       # raised from 35: full lock loads the drivetrain hard
KICK_DUTY  = 60
KICK_MS    = 400
FORWARD    = -1
MAX_RUN_MS = 12000
LOOP_MS    = 20
CENTRE_US  = 1262

IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

led   = Pin("LED", Pin.OUT)
btn   = Pin(15, Pin.IN, Pin.PULL_UP)
servo = PWM(Pin(0)); servo.freq(50)
pwma  = PWM(Pin(2)); pwma.freq(1000)
ain1  = Pin(3, Pin.OUT)
ain2  = Pin(4, Pin.OUT)
stby  = Pin(5, Pin.OUT)

def steer_us(v):
    servo.duty_u16(int(65535 * v / 20000))
    return v

def motor(duty, d):
    if d == 0:
        stby.value(0); pwma.duty_u16(0)
        ain1.value(0); ain2.value(0)
        return
    stby.value(1)
    ain1.value(1 if d > 0 else 0)
    ain2.value(0 if d > 0 else 1)
    pwma.duty_u16(int(65535 * duty / 100))

def brake():
    stby.value(1); ain1.value(1); ain2.value(1)
    pwma.duty_u16(65535); time.sleep_ms(300); motor(0, 0)

def ang_diff(new, old):
    d = new - old
    if d > 180:  d -= 360
    if d < -180: d += 360
    return d

motor(0, 0); steer_us(CENTRE_US); time.sleep_ms(300)

i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000)
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
imu.set_offsets(IMU_OFFSETS);  time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(500)

# --- run number --------------------------------------------------------
try:
    with open("/turn_n.txt") as f:
        run_n = int(f.read()) + 1
except Exception:
    run_n = 1
with open("/turn_n.txt", "w") as f:
    f.write(str(run_n))

# Pre-load the lock BEFORE the button so the backlash is already taken up.
# Otherwise the car travels straight for the first few centimetres while the
# slack is consumed, and that straight bit inflates the measured chord.
steer_us(LOCK_US)
print("turn run %d, lock %d us -- mark BOTH rear tyre contact points now"
      % (run_n, LOCK_US))

while btn.value() == 1:
    led.toggle(); time.sleep_ms(300)
time.sleep_ms(50)
while btn.value() == 0:
    time.sleep_ms(10)
led.on(); time.sleep(2)

log = open("/turn_log.csv", "a")
log.write("# turn run {}, lock {}, duty {}, target {}\n".format(
          run_n, LOCK_US, CRUISE, TARGET_DEG))
log.write("t_ms,heading,total,rate_dps\n")

total   = 0.0
prev    = imu.euler()[0]
t0      = time.ticks_ms()
t_prev  = t0
reason  = "timeout"

try:
    motor(KICK_DUTY, FORWARD); time.sleep_ms(KICK_MS)
    motor(CRUISE, FORWARD)

    while time.ticks_diff(time.ticks_ms(), t0) < MAX_RUN_MS:
        now = time.ticks_ms()
        dt  = time.ticks_diff(now, t_prev) / 1000.0
        t_prev = now

        h = imu.euler()[0]
        step = ang_diff(h, prev)
        total += step
        prev = h

        # rate tells you whether the arc was one steady circle. A rising
        # rate over the first second means the car was still straightening
        # out of the launch, and that part of the path is not on the circle.
        rate = step / dt if dt > 0 else 0.0

        log.write("{},{:.2f},{:.2f},{:.1f}\n".format(
            time.ticks_diff(now, t0), h, total, rate))

        if abs(total) >= TARGET_DEG:
            reason = "done"
            break
        time.sleep_ms(LOOP_MS)

finally:
    # STRAIGHTEN FIRST, then brake. If the wheels stay at lock through the
    # 300 ms brake the car keeps curving while it stops, and the end marks
    # land past 180 deg -- which makes the measured chord too long and R
    # too large. Centring first turns that into a straight coast instead.
    steer_us(CENTRE_US)
    time.sleep_ms(150)
    brake()

    # How far past 180 did it actually stop? This is the number that says
    # whether the measurement needs correcting at all.
    settle = total + ang_diff(imu.euler()[0], prev)
    log.write(",,{:.2f},{}\n\n".format(settle, reason))
    log.close()

    print("run %d: stopped at %.1f deg (%s)" % (run_n, settle, reason))
    print("  overshoot %.1f deg" % (abs(settle) - TARGET_DEG))
    print("  mark both rear contact points, measure midpoint to midpoint")
    led.off()
