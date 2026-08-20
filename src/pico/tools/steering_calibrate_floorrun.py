# =============================================================================
# main.py  --  SERVO CENTRE CALIBRATION, FLOOR RUN
# Team Zero Error, WRO 2026 Future Engineers
#
# The servo is held at one fixed pulse width for the whole run. The car drives
# straight and the floor tells you whether that pulse width is really centre.
#
# WHY THE FLOOR AND NOT THE WHEELS
#   Visual inspection could not distinguish 1250 from 1300 us -- both looked
#   parallel. That is 10% of full lock. Over 2 m, a steering error that small
#   becomes tens of millimetres of lateral drift, which is measurable. The car
#   is a better instrument than the eye here.
#
# PROCEDURE
#   1. Tape a line on the floor marking BOTH front wheels at the start.
#      A single mark gives position but not heading.
#   2. Run from the 2 m mark.
#   3. Measure the SIDEWAYS offset where it stops, not the total distance.
#   4. Drifts RIGHT -> INCREASE CENTRE_US   (higher us steers left)
#      Drifts LEFT  -> DECREASE CENTRE_US
#   5. Repeat in 25 us steps, then 10 us. Done when drift < 50 mm over 2 m.
#
# The wall-stop is retained purely as a backstop so the car does not hit the
# wall while you are watching its path rather than the car itself.
#
# REBUILD NOTE: I2C1 on GP6/GP7. GP9 was destroyed and GP8 is left empty.
# =============================================================================

from machine import Pin, PWM
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X

# ---------------------------------------------------------------- CONSTANTS

BUS, SDA_PIN, SCL_PIN = 1, 6, 7
SHUT_PIN = 10

# --- steering, measured ------------------------------------------------
CENTRE_US    = 1262   # PROVISIONAL -- this is what the run is testing
LEFT_MAX_US  = 1480   # 20 us inside the 1500 us strain point
RIGHT_MAX_US = 1010   # 20 us inside the 990 us strain point
# Increasing pulse width steers LEFT. This runs OPPOSITE to the heading
# convention (clockwise-positive, right increases) -- an easy place for a
# sign error to hide once a controller is added.

# --- drive, measured ---------------------------------------------------
FORWARD    = -1       # direction B drives forward (re-confirmed after rebuild)
KICK_DUTY  = 45       # 35% cannot break away from rest on the floor
KICK_MS    = 300
CRUISE     = 35       # 0.34 m/s; braking distance 126 +/- 9 mm
TRIGGER_MM = 500
MAX_RUN_MS = 8000
BAD_LIMIT  = 5        # consecutive rejected reads -> stop. Never drive blind.
MAX_JUMP   = 300      # car moves ~7 mm per loop; bigger steps are phantoms
BRAKE_MS   = 300
LOOP_MS    = 20

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
    mechanical limits means the servo can never be driven against its stop --
    a stalled servo draws full current and cooks its plastic gears."""
    v = max(RIGHT_MAX_US, min(LEFT_MAX_US, v))
    servo.duty_u16(int(65535 * v / 20000))

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
    """Both direction pins HIGH shorts the motor across itself, so its own
    generated voltage opposes rotation. Released afterwards."""
    stby.value(1)
    ain1.value(1); ain2.value(1)
    pwma.duty_u16(65535)
    time.sleep_ms(BRAKE_MS)
    motor(0, 0)

motor(0, 0)
steer_us(CENTRE_US)
time.sleep_ms(500)                    # let the servo settle before driving

shut = Pin(SHUT_PIN, Pin.OUT)
shut.value(0); time.sleep_ms(100)
shut.value(1); time.sleep_ms(100)
tof = PiicoDev_VL53L1X(bus=BUS, freq=100_000, sda=SDA_PIN, scl=SCL_PIN,
                       address=0x29)
time.sleep_ms(100)

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

while btn.value() == 1:               # blink = waiting
    led.toggle()
    time.sleep_ms(300)

time.sleep_ms(50)                     # debounce
while btn.value() == 0:               # wait for release
    time.sleep_ms(10)

led.on()                              # solid = running
time.sleep(2)                         # hands clear

# --------------------------------------------------------------------- RUN

log = open("/run_log.csv", "a")
log.write("# run {}, centre {} us, duty {}\n".format(run_n, CENTRE_US, CRUISE))
log.write("t_ms,dist,status,rejected\n")

reason     = "timeout"
bad_streak = 0
prev       = None
t0         = time.ticks_ms()

try:
    motor(KICK_DUTY, FORWARD)
    time.sleep_ms(KICK_MS)
    motor(CRUISE, FORWARD)

    while time.ticks_diff(time.ticks_ms(), t0) < MAX_RUN_MS:

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

        log.write("{},{},{},{}\n".format(
            time.ticks_diff(time.ticks_ms(), t0), d, st, rejected))

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
    time.sleep_ms(500)                # let it settle before measuring
    for _ in range(5):                # the car records its own stop distance
        try:
            log.write(",{},{},final\n".format(tof.read(), tof.status))
        except Exception:
            log.write(",-1,EXC,final\n")
        time.sleep_ms(100)
    log.write(",,,{}\n\n".format(reason))
    log.close()
    led.off()
