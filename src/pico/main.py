# =============================================================================
# main.py  --  Team Zero Error, WRO 2026 Future Engineers
# Raspberry Pi Pico (non-W) -- real-time vehicle control
#
# LAYERS, innermost first. Each degrades to the one below it.
#
#   1  heading hold      IMU + P controller          PROVEN, 9 logged runs
#   2  wall stop         front ToF                   PROVEN
#   3  corner turn       front ToF + IMU 90 deg      [UNTESTED]
#   4  corridor centre   side ToF pairs              [UNTESTED]
#   5  pillar bias       camera over UART            [UNTESTED]
#
# If the camera goes silent the car still corners. If the side sensors fail
# it still holds heading. If the IMU throws it steers straight and stops at
# the wall. Nothing above layer 2 can prevent the car completing a lap.
#
# RULE COMPLIANCE
#   9.9   no data entered by vehicle orientation; target captured in code
#   9.11  power on first, ONE button press starts the run
#   9.18  open challenge: must not touch the OUTER wall
#   11.10 Pico is non-W, no radio. Pi 5 radios disabled separately.
#
# THE TWO CONVENTIONS, BOTH MEASURED, BOTH OPPOSITE
#   Heading:     turning RIGHT increases it   (clockwise-positive)
#   Pulse width: increasing it steers LEFT
#   So the gain enters with a MINUS sign. Getting this wrong does not make
#   the car wander -- it makes the car steer INTO every deviation.
# =============================================================================

from machine import Pin, I2C, PWM, UART
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import bno055

# ========================================================= MEASURED CONSTANTS
# Every value here came from a measurement with conditions recorded.
# Do not change one without re-running the test that produced it.

# --- steering ----------------------------------------------------------
CENTRE_US       = 1262  # backlash band ~1226-1284; this sits near midpoint
LEFT_MAX_US     = 1480  # 20 us inside the measured strain point
RIGHT_MAX_US    = 1010  # 20 us inside the measured strain point
KP_US_PER_DEG   = 15    # 9 runs: 1.2-1.6 deg peak error over 3 m
KI_US_PER_DEG_S = 0.0   # REMOVED. Integral limit-cycles across the backlash
                        # deadzone. 4 runs at KI=6 oscillated +6 to -15 us
                        # with a period longer than the run. Log entry 29.
MAX_ERR_DEG     = 30    # cap so a wild reading cannot slam full lock

# --- drive -------------------------------------------------------------
FORWARD    = -1
KICK_DUTY  = 45         # break-away from standstill
KICK_MS    = 300
CRUISE     = 35         # NOT a fixed speed: still accelerating at 2.5 m.
                        # 0.30 m/s at 0.5 m rising to 0.54 m/s at 2.5 m.
TURN_DUTY  = 45         # 35 STALLS at full lock -- front tyres scrub
BRAKE_MS   = 300

# --- distance ----------------------------------------------------------
TRIGGER_MM = 700        # braking measured 210-250 mm; ~3x margin
MAX_JUMP   = 120        # caught a real 178 mm phantom in run 16
BAD_LIMIT  = 5
LOOP_MS    = 20         # commanded; real period ~26 ms. dt is timed.

# --- geometry (Gate 1) -------------------------------------------------
TRACK_MM  = 90          # calipers
L_F_MM    = 210         # [RE-MEASURE] deck trimmed 15 mm since this
TURN_R_MM = 501.5       # worse direction (right), tape error corrected
# Single-arc 90 deg cornering in a 600 mm corridor is NOT FEASIBLE at this
# radius. 1000 mm corridors are fine. See NARROW_BACK below.

# --- corner ------------------------------------------------------------
CORNER_DEG      = 90.0
CORNER_TOL_DEG  = 5.0
CORNERS_PER_LAP = 4
TOTAL_LAPS      = 3
NARROW_MM       = 750   # side reading below this => 600 mm corridor

# --- IMU ---------------------------------------------------------------
IMU_ADDR  = 0x28        # ADR to GND plus bridged solder pads
GYRO_AXIS = 2           # confirmed twice: gravity vector and rotation peak
GYRO_SIGN = 1           # MEASURED +1. Right-hand rule predicted -1 and was
                        # wrong. Log entry 24.
IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

# --- camera link -------------------------------------------------------
CAM_BAUD       = 115200
CAM_STALE_MS   = 200    # no line for this long => ignore the camera
KP_CAM_DEG     = 18.0   # [UNTUNED] bias per unit of normalised x error
CAM_MAX_BIAS   = 25.0   # camera can never command more than this
RED_TARGET_X   = 0.25   # red passes RIGHT  -> hold it left of frame
GREEN_TARGET_X = 0.75   # green passes LEFT -> hold it right of frame

# --- pins --------------------------------------------------------------
PIN_SERVO = 0
PIN_PWMA, PIN_AIN1, PIN_AIN2, PIN_STBY = 2, 3, 4, 5
PIN_SDA, PIN_SCL, I2C_BUS = 6, 7, 1
PIN_BTN = 15
PIN_TX, PIN_RX = 16, 17
# GP8 is a deliberate buffer. GP9 is DEAD (short-circuit casualty).
SHUT_PINS = {"front": 10, "fl": 11, "fr": 12, "rl": 13, "rr": 14, "rear": 18}
ADDRS     = {"front": 0x30, "fl": 0x31, "fr": 0x32,
             "rl": 0x33, "rr": 0x34, "rear": 0x35}
# Only sensors listed here are brought up. Add "rear" once the six-sensor
# sequence has been proven on its own.
ACTIVE = ["front", "fl", "fr", "rl", "rr"]


# ============================================================== SMALL TOOLS

def ang_diff(new, old):
    """Wrap-safe heading difference folded into +/-180.
    Without this a 359.9 -> 0.1 transition reads as -359.8 degrees instead
    of +0.2 and the controller slams full lock.
    Confirmed live: 359.94 -> 31.81 returned +31.88."""
    d = new - old
    if d > 180:  d -= 360
    if d < -180: d += 360
    return d

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def wrap360(a):
    while a >= 360: a -= 360
    while a < 0:    a += 360
    return a


# ================================================================= HARDWARE

led   = Pin("LED", Pin.OUT)
btn   = Pin(PIN_BTN, Pin.IN, Pin.PULL_UP)
servo = PWM(Pin(PIN_SERVO)); servo.freq(50)
pwma  = PWM(Pin(PIN_PWMA));  pwma.freq(1000)
ain1  = Pin(PIN_AIN1, Pin.OUT)
ain2  = Pin(PIN_AIN2, Pin.OUT)
stby  = Pin(PIN_STBY, Pin.OUT)

def steer_us(v):
    """Every steering command goes through here, so the servo can never be
    driven against its mechanical stop."""
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
    stby.value(1); ain1.value(1); ain2.value(1)
    pwma.duty_u16(65535)
    time.sleep_ms(BRAKE_MS)
    motor(0, 0)

motor(0, 0)
steer_us(CENTRE_US)
time.sleep_ms(300)


# ================================================================== SENSORS
# ToF sensors FIRST, then rebuild I2C, then the IMU LAST.
#
# Every PiicoDev_VL53L1X() call reinitialises the I2C peripheral and
# silently breaks anything constructed before it. The symptom is heading
# frozen at 0.00 with no exception raised. This ordering is not stylistic.
#
# The address change is RAM-only: a full POWER CYCLE is required between
# runs. A soft reboot leaves each sensor at its previous address and the
# sequence below then finds nothing at 0x29.

shut = {}
tof  = {}

for name in ACTIVE:
    shut[name] = Pin(SHUT_PINS[name], Pin.OUT)
    shut[name].value(0)            # hold every sensor in reset
time.sleep_ms(150)

for name in ACTIVE:
    shut[name].value(1)            # release exactly one
    time.sleep_ms(120)
    try:
        s = PiicoDev_VL53L1X(bus=I2C_BUS, freq=100_000,
                             sda=PIN_SDA, scl=PIN_SCL, address=0x29)
        s.change_addr(ADDRS[name])
        time.sleep_ms(60)
        tof[name] = s
        print("tof %-6s -> 0x%02X" % (name, ADDRS[name]))
    except Exception as e:
        print("tof %-6s FAILED: %s" % (name, e))
        tof[name] = None

i2c = I2C(I2C_BUS, sda=Pin(PIN_SDA), scl=Pin(PIN_SCL), freq=100_000)
imu = bno055.BNO055(i2c, address=IMU_ADDR)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
imu.set_offsets(IMU_OFFSETS);  time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(500)

uart = UART(0, baudrate=CAM_BAUD, tx=Pin(PIN_TX), rx=Pin(PIN_RX),
            bits=8, parity=None, stop=1, timeout=5)


# ================================================================== READING

_prev = {}
_bad  = {}

def read_tof(name):
    """One filtered reading in mm, or None.

    MAX_JUMP rejects physically impossible steps. At ~14 mm of travel per
    loop, 120 mm is still an order of magnitude above real motion. The old
    value of 300 let a 178 mm phantom through in run 16."""
    s = tof.get(name)
    if s is None:
        return None
    try:
        d, st = s.read(), s.status
    except Exception:
        _bad[name] = _bad.get(name, 0) + 1
        return None

    if d <= 0 or st != "OK":
        _bad[name] = _bad.get(name, 0) + 1
        return None

    p = _prev.get(name)
    if p is not None and abs(d - p) > MAX_JUMP:
        _bad[name] = _bad.get(name, 0) + 1
        return None

    _prev[name] = d
    _bad[name] = 0
    return d

def read_rate():
    """Angular rate in deg/s, clockwise-positive to match the heading
    convention. Read from the gyro directly rather than by differencing
    euler angles -- euler is quantised to 1/16 deg, which at a 20 ms loop
    injects 3.1 deg/s of phantom rate per LSB."""
    try:
        return GYRO_SIGN * imu.gyro()[GYRO_AXIS]
    except Exception:
        return 0.0


# =============================================================== CAMERA LINK

_cam_buf  = b""
_cam_last = 0
_cam_col  = None
_cam_x    = 0.5
_cam_h    = 0

def poll_camera():
    """Consume whatever the Pi has sent. One line: colour,x_norm,height_px

    The camera is an OVERRIDE on a working controller, never a replacement.
    If it stops sending, cam_bias() returns 0 and the car reverts to plain
    wall following."""
    global _cam_buf, _cam_last, _cam_col, _cam_x, _cam_h
    try:
        if uart.any():
            _cam_buf += uart.read()
            while b"\n" in _cam_buf:
                line, _cam_buf = _cam_buf.split(b"\n", 1)
                parts = line.decode().strip().split(",")
                if len(parts) != 3:
                    continue
                col = parts[0].upper()
                if col not in ("R", "G", "N"):
                    continue
                _cam_col  = None if col == "N" else col
                _cam_x    = float(parts[1])
                _cam_h    = int(parts[2])
                _cam_last = time.ticks_ms()
    except Exception:
        pass                       # a corrupt line must never stop the car

def cam_bias():
    """Heading-setpoint offset in degrees, from the pillar's bearing.

    This is visual servoing: the controller never computes where the car is
    in the corridor. It drives a pixel coordinate to a target value. Red
    held left of frame passes on the right; green held right passes left."""
    if _cam_col is None:
        return 0.0
    if time.ticks_diff(time.ticks_ms(), _cam_last) > CAM_STALE_MS:
        return 0.0
    tgt = RED_TARGET_X if _cam_col == "R" else GREEN_TARGET_X
    return clamp(KP_CAM_DEG * (_cam_x - tgt), -CAM_MAX_BIAS, CAM_MAX_BIAS)


# ================================================================ RUN NUMBER

try:
    with open("/run_n.txt") as f:
        run_n = int(f.read()) + 1
except Exception:
    run_n = 1
with open("/run_n.txt", "w") as f:
    f.write(str(run_n))


# ============================================================= WAIT FOR START
# Rule 9.11: power on first, then ONE button press starts the run.
# Rule 9.9: nothing about the vehicle's placement is entered as data. The
# heading target is captured by the program at the moment of the press.

while btn.value() == 1:
    led.toggle()
    time.sleep_ms(300)
time.sleep_ms(50)
while btn.value() == 0:
    time.sleep_ms(10)
led.on()
time.sleep(2)

target = imu.euler()[0]


# ====================================================================== RUN

log = open("/run_log.csv", "a")
log.write("# run {}, centre {}, Kp {}, cruise {}, target {:.2f}\n".format(
          run_n, CENTRE_US, KP_US_PER_DEG, CRUISE, target))
log.write("t_ms,state,front,fl,fr,rl,rr,heading,err,bias,steer,corners\n")

STRAIGHT, TURN, NARROW_BACK, DONE = 0, 1, 2, 3

state      = STRAIGHT
corners    = 0
turn_dir   = 0            # +1 right, -1 left. Decided at the first corner.
turn_start = 0.0
turn_lock  = CENTRE_US
back_until = 0
first_leg  = 0            # ms from start to first corner; used to find home
done_at    = 0
t0         = time.ticks_ms()
reason     = "timeout"
MAX_RUN_MS = 170000       # 3 min rule limit, with margin

try:
    motor(KICK_DUTY, FORWARD)
    time.sleep_ms(KICK_MS)
    motor(CRUISE, FORWARD)

    while True:
        now = time.ticks_ms()
        el  = time.ticks_diff(now, t0)
        if el > MAX_RUN_MS:
            reason = "timeout"
            break

        poll_camera()

        front = read_tof("front")
        fl    = read_tof("fl")
        fr    = read_tof("fr")
        rl    = read_tof("rl")
        rr    = read_tof("rr")

        # ------------------------------------------------------ STEERING
        bias = 0.0
        try:
            heading = imu.euler()[0]

            # Camera bias is an offset on the setpoint, not a separate
            # controller. Layer 5 riding on layer 1.
            bias = cam_bias()

            # [UNTESTED] Corridor centring from the side pair. Applied only
            # when BOTH sides read, so one dead sensor disables centring
            # rather than steering the car on half a measurement.
            if state == STRAIGHT and fl and fr:
                bias += clamp((fr - fl) * 0.02, -8.0, 8.0)

            err = clamp(ang_diff(target + bias, heading),
                        -MAX_ERR_DEG, MAX_ERR_DEG)
            cmd = steer_us(CENTRE_US - KP_US_PER_DEG * err)
        except Exception:
            heading = -999.0
            err = 0.0
            cmd = steer_us(CENTRE_US)      # lost the IMU: go straight

        # -------------------------------------------------- STATE MACHINE

        if state == STRAIGHT:
            if front is not None and front < TRIGGER_MM:
                if corners == 0:
                    first_leg = el
                    # Direction is drawn after check time, so the car works
                    # it out: turn toward whichever side is more open.
                    turn_dir = (-1 if (fl and fr and fl > fr) else 1)
                turn_lock = LEFT_MAX_US if turn_dir < 0 else RIGHT_MAX_US

                # [UNTESTED] R = 501.5 mm cannot arc a 90 deg corner inside
                # a 600 mm corridor. If the corridor reads narrow, reverse
                # first to buy room. Rule 9.21 permits reversing.
                narrow = ((fl is not None and fl < NARROW_MM) or
                          (fr is not None and fr < NARROW_MM))
                if narrow:
                    state = NARROW_BACK
                    back_until = time.ticks_add(now, 600)
                    steer_us(CENTRE_US)
                    motor(TURN_DUTY, -FORWARD)
                else:
                    state = TURN
                    turn_start = heading
                    steer_us(turn_lock)
                    motor(TURN_DUTY, FORWARD)

        elif state == NARROW_BACK:
            if time.ticks_diff(back_until, now) <= 0:
                state = TURN
                turn_start = heading
                steer_us(turn_lock)
                motor(TURN_DUTY, FORWARD)

        elif state == TURN:
            steer_us(turn_lock)
            if abs(ang_diff(heading, turn_start)) >= CORNER_DEG - CORNER_TOL_DEG:
                corners += 1
                target = wrap360(turn_start + turn_dir * CORNER_DEG)
                motor(CRUISE, FORWARD)
                if corners >= CORNERS_PER_LAP * TOTAL_LAPS:
                    state   = DONE
                    done_at = now
                else:
                    state = STRAIGHT

        elif state == DONE:
            # Rule 9.16: the vehicle must stop in the section it started
            # from. Without encoders the only estimate available is how
            # long the first leg took. Speed is not constant -- the car is
            # still accelerating at 2.5 m -- so this is approximate.
            # Encoders were descoped for the 2026 season.
            if time.ticks_diff(now, done_at) > first_leg:
                reason = "finished"
                break
            if front is not None and front < TRIGGER_MM:
                reason = "finished_wall"
                break

        log.write("{},{},{},{},{},{},{},{:.2f},{:.2f},{:.2f},{},{}\n".format(
            el, state, front, fl, fr, rl, rr, heading, err, bias, cmd, corners))

        if _bad.get("front", 0) >= BAD_LIMIT:
            reason = "blind"
            break

        time.sleep_ms(LOOP_MS)

finally:
    brake()
    steer_us(CENTRE_US)
    motor(0, 0)
    log.write(",,,,,,,,,,,{}\n\n".format(reason))
    log.close()
    led.off()
    print("run %d ended: %s, %d corners" % (run_n, reason, corners))
