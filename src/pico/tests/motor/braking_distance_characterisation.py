# =============================================================================
# main.py  --  BRAKING DISTANCE CHARACTERISATION
# Team Zero Error, WRO 2026 Future Engineers
#
# Fifteen runs across three duty levels, five each. The script holds the
# schedule; one button press executes the next run. No laptop between runs.
#
#   Runs  1-5   duty 25%   START FROM 1.5 m MARK
#   Runs  6-10  duty 35%   START FROM 1.5 m MARK
#   Runs 11-15  duty 45%   START FROM 2.0 m MARK
#
# The 2 m start for the fast set exists for two reasons: braking distance
# grows with speed, and the car needs enough approach to reach steady speed
# before the trigger fires. A car still accelerating at the trigger gives a
# braking figure that means nothing.
#
# KEEP A PAPER TALLY. The car does not tell you which run it is on. Tick one
# box per run so your tape measurements land against the right run number.
#
# The log APPENDS. Delete /run_log.csv and /run_n.txt before starting a fresh
# set of fifteen, or the numbering carries over from the previous session.
# =============================================================================

from machine import Pin, PWM
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X

# ---------------------------------------------------------------- SCHEDULE

SCHEDULE = [25]*5 + [35]*5 + [45]*5

# ---------------------------------------------------------------- CONSTANTS

FORWARD    = -1
KICK_DUTY  = 45      # must exceed the highest cruise duty in the schedule
KICK_MS    = 300
TRIGGER_MM = 500     # held constant across all fifteen runs
MAX_RUN_MS = 10000
BAD_LIMIT  = 5
MAX_JUMP   = 300
BRAKE_MS   = 300
LOOP_MS    = 20

# ----------------------------------------------------------------- HARDWARE

led  = Pin("LED", Pin.OUT)
btn  = Pin(15, Pin.IN, Pin.PULL_UP)
pwma = PWM(Pin(2)); pwma.freq(1000)
ain1 = Pin(3, Pin.OUT)
ain2 = Pin(4, Pin.OUT)
stby = Pin(5, Pin.OUT)

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

shut = Pin(10, Pin.OUT)
shut.value(0); time.sleep_ms(100)
shut.value(1); time.sleep_ms(100)
tof = PiicoDev_VL53L1X(bus=0, freq=100_000, sda=8, scl=9, address=0x29)
time.sleep_ms(100)

# ------------------------------------------------------- RUN NUMBER, PERSISTENT
# Survives power cycles so the schedule advances across battery swaps.

try:
    with open("/run_n.txt") as f:
        run_n = int(f.read()) + 1
except Exception:
    run_n = 1
with open("/run_n.txt", "w") as f:
    f.write(str(run_n))

if run_n > len(SCHEDULE):
    # Schedule exhausted. Refuse to run rather than guess at a duty.
    for _ in range(20):
        led.toggle(); time.sleep_ms(80)
    led.off()
    raise SystemExit("schedule complete")

CRUISE = SCHEDULE[run_n - 1]

# ------------------------------------------------------------ WAIT FOR START

while btn.value() == 1:
    led.toggle()
    time.sleep_ms(300)

time.sleep_ms(50)
while btn.value() == 0:
    time.sleep_ms(10)

led.on()
time.sleep(2)

# --------------------------------------------------------------------- RUN

log = open("/run_log.csv", "a")          # APPEND
log.write("# run {} of {}, duty {}, trigger {}\n".format(
          run_n, len(SCHEDULE), CRUISE, TRIGGER_MM))
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
    time.sleep_ms(500)                   # let the car settle before measuring
    # The car measures its own stopping distance. Removes the tape measure
    # from the loop and gives a cross-check against it.
    for _ in range(5):
        try:
            log.write(",{},{},final\n".format(tof.read(), tof.status))
        except Exception:
            log.write(",-1,EXC,final\n")
        time.sleep_ms(100)
    log.write(",,,{}\n\n".format(reason))
    log.close()
    led.off()
