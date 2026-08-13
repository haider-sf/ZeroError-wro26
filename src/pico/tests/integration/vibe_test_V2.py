# =============================================================================
# vibe_test.py  v2  --  Team Zero Error, WRO 2026 Future Engineers
#
# Car on a block, wheels free. Motor runs through a ladder of duty cycles while
# the senses layer reads. Question: does the motor degrade the sensors, and if
# so, WHICH effect does it (vibration / switching noise / current transient)?
#
# Each effect gets its own phase, so the answer is separable.
#
# WHAT THIS DOES NOT PROVE: wheels-up means almost no motor load. Real driving
# current is several times higher. A pass here does NOT clear the load-current
# risk -- that stays open until the first on-floor run.
#
# CHANGES FROM v1:
#   - Stats class rewritten (Welford). v1 reported sigma = 0.00 because
#     single-precision floats cancelled catastrophically.
#   - Single ToF config.
#   - FORWARD = -1 (measured: direction B drives the car forward).
#   - MIN_DUTY = 15 recorded (measured floor in chassis at 5 V, 1 kHz).
# =============================================================================

from machine import Pin, I2C, PWM, ADC
import time, os, math
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import bno055

# ------------------------------------------------------------------ 1. CONFIG

SHUT_PINS   = [10]
TOF_ADDRS   = [0x30]
REF_TOF     = 0
IMU_ADDR    = 0x28
BUS_FREQ    = 100_000

# --- measured constants. Do not guess these; they were established by test. ---
FORWARD     = -1      # direction B drives the car forward
REVERSE     = +1
MIN_DUTY    = 15      # lowest duty that actually turns the wheels, in chassis

PIN_PWMA, PIN_AIN1, PIN_AIN2, PIN_STBY = 2, 3, 4, 5
MOTOR_FREQ  = 1000

LOOP_HZ     = 50
LOG_EVERY   = 2
LOG_PATH    = "/vibe_log.csv"
MIN_FREE_KB = 400

IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

# (label, duty_percent, direction, seconds)
# direction: FORWARD / REVERSE / 0 = STBY low / 9 = alternate every 1 s
PHASES = [
    ("P0_off",       0,       0, 20),
    ("P1_stby_d0",   0, FORWARD, 15),
    ("P2_duty20",   20, FORWARD, 15),
    ("P3_duty40",   40, FORWARD, 15),
    ("P4_duty70",   70, FORWARD, 15),
    ("P5_reversal", 60,       9, 12),
    ("P6_recover",   0,       0, 20),
]

# ------------------------------------------------------------- 2. SMALL TOOLS

def ang_diff(new, old):
    """Wrap-safe heading difference, folded into +/-180."""
    d = new - old
    if d > 180:  d -= 360
    if d < -180: d += 360
    return d

def free_kb():
    s = os.statvfs("/")
    return (s[0] * s[3]) // 1024

class Stats:
    """Streaming mean/sigma, Welford's method.
    Never subtracts two large nearly-equal numbers, so it survives the Pico's
    single-precision floats. The naive sum-of-squares formula does not."""
    def __init__(self):
        self.n = 0; self.mean_ = 0.0; self.m2 = 0.0
    def add(self, x):
        self.n += 1
        d = x - self.mean_
        self.mean_ += d / self.n
        self.m2 += d * (x - self.mean_)
    def mean(self):
        return self.mean_
    def sigma(self):
        return math.sqrt(self.m2 / (self.n - 1)) if self.n > 1 else 0.0

# --------------------------------------------------------------- 3. HARDWARE

pwma = PWM(Pin(PIN_PWMA)); pwma.freq(MOTOR_FREQ)
ain1 = Pin(PIN_AIN1, Pin.OUT)
ain2 = Pin(PIN_AIN2, Pin.OUT)
stby = Pin(PIN_STBY, Pin.OUT)

def motor(duty_pct, direction):
    if direction == 0:
        stby.value(0); pwma.duty_u16(0)
        ain1.value(0); ain2.value(0)
        return
    stby.value(1)
    ain1.value(1 if direction > 0 else 0)
    ain2.value(0 if direction > 0 else 1)
    pwma.duty_u16(int(65535 * max(0, min(100, duty_pct)) / 100))

motor(0, 0)      # guaranteed safe state before anything else

vsys_adc = ADC(3)
def read_vsys():
    # ADC3 sits on an internal /3 divider from VSYS on a genuine Pico.
    return vsys_adc.read_u16() * 3 * 3.3 / 65535

print("free flash: {} KB".format(free_kb()))
if free_kb() < MIN_FREE_KB:
    raise SystemExit("Not enough flash. Delete " + LOG_PATH)

shut = [Pin(p, Pin.OUT) for p in SHUT_PINS]
for s in shut:
    s.value(0)
time.sleep_ms(100)

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
print("bus, ToF held off:", [hex(a) for a in i2c.scan()])     # expect ['0x28']

tofs = []
for i in range(len(shut)):
    shut[i].value(1)
    time.sleep_ms(100)
    s = PiicoDev_VL53L1X(bus=0, freq=BUS_FREQ, sda=8, scl=9, address=0x29)
    s.change_addr(TOF_ADDRS[i])
    time.sleep_ms(50)
    tofs.append(s)
    print("  ToF", i, "->", hex(TOF_ADDRS[i]))

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
print("bus, all up:", [hex(a) for a in i2c.scan()])           # expect 0x28,0x30

imu = bno055.BNO055(i2c, address=IMU_ADDR)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
imu.set_offsets(IMU_OFFSETS);  time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
print("IMU mode:", imu.mode(), "cal[g,a]:", list(imu.cal_status())[1:3])

# --------------------------------------------------------------- 4. THE RUN

DT = 1.0 / LOOP_HZ
log = open(LOG_PATH, "w")
log.write("t_ms,phase,duty,dir,hdg,roll,pitch,cg,ca,vsys,d0,ok0\n")

results = []
t0 = time.ticks_ms()
loop_n = 0

try:
    for label, duty, direction, secs in PHASES:
        st_d = [Stats() for _ in tofs]
        st_roll = Stats(); st_pitch = Stats()
        ok_cnt = [0] * len(tofs)
        samples = 0; errs = 0
        vsys_min = 99.0; cal_a_min = 3
        hdg_unwrapped = 0.0; hdg_prev = None

        print("\n--- {}  duty={}%  dir={}  {}s ---".format(label, duty, direction, secs))
        phase_start = time.ticks_ms()
        last_flip = phase_start
        cur_dir = FORWARD if direction == 9 else direction
        motor(duty, cur_dir)
        next_tick = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), phase_start) < secs * 1000:

            if direction == 9 and time.ticks_diff(time.ticks_ms(), last_flip) > 1000:
                cur_dir = -cur_dir
                motor(0, 0); time.sleep_ms(20)
                motor(duty, cur_dir)
                last_flip = time.ticks_ms()

            try:
                h, r, p = imu.euler()
                cal = imu.cal_status()
                cg, ca = cal[1], cal[2]
            except Exception:
                errs += 1; h = r = p = 0.0; cg = ca = -1

            dists = []; oks = []
            for i, t in enumerate(tofs):
                try:
                    d = t.read(); ok = 1 if t.status == "OK" else 0
                except Exception:
                    errs += 1; d = -1; ok = 0
                dists.append(d); oks.append(ok)
                if ok and d > 0:
                    st_d[i].add(d); ok_cnt[i] += 1

            v = read_vsys()

            samples += 1
            st_roll.add(r); st_pitch.add(p)
            if v < vsys_min: vsys_min = v
            if 0 <= ca < cal_a_min: cal_a_min = ca
            if hdg_prev is not None: hdg_unwrapped += ang_diff(h, hdg_prev)
            hdg_prev = h

            loop_n += 1
            if loop_n % LOG_EVERY == 0:
                log.write("{},{},{},{},{:.2f},{:.2f},{:.2f},{},{},{:.3f},{},{}\n".format(
                    time.ticks_diff(time.ticks_ms(), t0), label, duty, cur_dir,
                    h, r, p, cg, ca, v, dists[0], oks[0]))

            next_tick = time.ticks_add(next_tick, int(DT * 1000))
            slack = time.ticks_diff(next_tick, time.ticks_ms())
            if slack > 0:
                time.sleep_ms(slack)

        motor(0, 0)
        results.append({
            "label": label, "secs": secs, "n": samples,
            "drift_per_min": hdg_unwrapped / secs * 60.0,
            "ref_mean": st_d[REF_TOF].mean(), "ref_sigma": st_d[REF_TOF].sigma(),
            "ok_pct": 100.0 * ok_cnt[REF_TOF] / samples if samples else 0,
            "roll_sig": st_roll.sigma(), "pitch_sig": st_pitch.sigma(),
            "vsys_min": vsys_min, "cal_a_min": cal_a_min, "errs": errs,
        })
        time.sleep(1)

finally:
    motor(0, 0)
    log.close()
    print("\nmotor off, log closed:", LOG_PATH)

# ------------------------------------------------------------- 5. SUMMARY

print("\n================ PER-PHASE SUMMARY ================")
print("phase        drift/min  refmean  refsig  OK%   rollsig pitchsig  vsysmin cal_a err")
for r in results:
    print("{:<12} {:>8.2f}  {:>7.1f} {:>7.2f} {:>5.1f}  {:>7.3f} {:>8.3f}  {:>7.3f} {:>5} {:>3}"
          .format(r["label"], r["drift_per_min"], r["ref_mean"], r["ref_sigma"],
                  r["ok_pct"], r["roll_sig"], r["pitch_sig"],
                  r["vsys_min"], r["cal_a_min"], r["errs"]))

base = results[0]
print("\n---- verdict vs. P0 baseline ----")
for r in results[1:]:
    flags = []
    if abs(r["drift_per_min"]) > 5:                    flags.append("DRIFT")
    if base["ref_sigma"] > 0 and r["ref_sigma"] > 3 * base["ref_sigma"]:
                                                       flags.append("TOF_NOISE")
    if r["ok_pct"] < 90:                               flags.append("TOF_STATUS")
    if r["vsys_min"] < 4.6:                            flags.append("VSYS_SAG")
    if r["cal_a_min"] <= 1:                            flags.append("ACCEL_CAL_LOST")
    if r["errs"] > 0:                                  flags.append("I2C_ERR")
    print("  {:<12} {}".format(r["label"], " ".join(flags) if flags else "ok"))
print("\nP6 vs P0: if P6 does NOT return to baseline, the damage is persistent, "
      "not just concurrent -- a different and worse failure.")