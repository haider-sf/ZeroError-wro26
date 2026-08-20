# =============================================================================
# main.py  --  WALL STOP
# Team Zero Error, WRO 2026 Future Engineers
#
# Drive forward. Stop before the wall. Log every sensor read so the run can be
# reconstructed afterwards, since there is no console when untethered.
#
# START POSITION: the 1.5 m tape mark.
# Stock sensor configuration (long mode). Short-mode register writes were
# tried and reverted -- they broke either the status flag or the distance
# calibration. The jump filter below is the real defence against bad reads.
# =============================================================================

from machine import Pin, PWM
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X

# ---------------------------------------------------------------- CONSTANTS
# All measured, not guessed. Do not change without repeating the measurement.

FORWARD    = -1      # direction B drives the car forward
KICK_DUTY  = 40      # brief burst to break away from rest
KICK_MS    = 300     # 25% alone cannot start the car from standstill
CRUISE     = 25      # ~0.31 m/s measured
TRIGGER_MM = 500     # brake command fires below this
MAX_RUN_MS = 8000    # hard timeout. ~1 m of travel needs ~3 s at cruise.
BAD_LIMIT  = 5       # consecutive rejected reads -> stop. Never drive blind.
MAX_JUMP   = 300     # mm. The car moves ~7 mm per loop; a bigger step than
                     # this is the sensor lying, not the car teleporting.
BRAKE_MS   = 300
LOOP_MS    = 20      # ~50 Hz

# ----------------------------------------------------------------- HARDWARE

led  = Pin("LED", Pin.OUT)
btn  = Pin(15, Pin.IN, Pin.PULL_UP)          # active low
pwma = PWM(Pin(2)); pwma.freq(1000)
ain1 = Pin(3, Pin.OUT)
ain2 = Pin(4, Pin.OUT)
stby = Pin(5, Pin.OUT)

def motor(duty, direction):
    """direction: FORWARD, -FORWARD, or 0 for standby (driver off)."""
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
    generated voltage fights its rotation. Released afterwards so nothing
    sits shorted."""
    stby.value(1)
    ain1.value(1); ain2.value(1)
    pwma.duty_u16(65535)
    time.sleep_ms(BRAKE_MS)
    motor(0, 0)

motor(0, 0)                                  # safe state before anything else

shut = Pin(10, Pin.OUT)
shut.value(0); time.sleep_ms(100)
shut.value(1); time.sleep_ms(100)
tof = PiicoDev_VL53L1X(bus=0, freq=100_000, sda=8, scl=9, address=0x29)
time.sleep_ms(100)

# ------------------------------------------------------------ WAIT FOR START
# Rule 9.11: power on first, then ONE button press starts the run.

while btn.value() == 1:                      # blink = waiting
    led.toggle()
    time.sleep_ms(300)

time.sleep_ms(50)                            # debounce
while btn.value() == 0:                      # wait for release
    time.sleep_ms(10)

led.on()                                     # solid = running
time.sleep(2)                                # hands clear

# --------------------------------------------------------------------- RUN

log = open("/run_log.csv", "w")
log.write("t_ms,dist,status,rejected\n")

reason     = "timeout"
bad_streak = 0
prev       = None
t0         = time.ticks_ms()

try:
    motor(KICK_DUTY, FORWARD)                # break away from static friction
    time.sleep_ms(KICK_MS)
    motor(CRUISE, FORWARD)

    while time.ticks_diff(time.ticks_ms(), t0) < MAX_RUN_MS:

        # --- read, fail SAFE not forward -------------------------------
        try:
            d  = tof.read()
            st = tof.status
        except Exception:
            d = -1; st = "EXC"

        rejected = ""
        good = (d > 0 and st == "OK")

        # The sensor's own status flag is not sufficient. In an earlier run a
        # 1000 mm jump arrived marked OK. Physics is the stronger check.
        if good and prev is not None and abs(d - prev) > MAX_JUMP:
            good = False
            rejected = "jump"
        elif not good:
            rejected = "status"

        log.write("{},{},{},{}\n".format(
            time.ticks_diff(time.ticks_ms(), t0), d, st, rejected))

        # --- decide ------------------------------------------------------
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
    brake()                                  # runs on every exit path
    log.write(",,,{}\n".format(reason))
    log.close()
    led.off()
