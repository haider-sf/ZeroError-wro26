# Raspberry Pi Pico firmware and test tools

This directory contains the team's Pico MicroPython work up to 2026-08-17. It is an engineering
record as well as a code directory: early smoke tests, calibration tools, later integration tests
and third-party-compatible drivers are retained so the development path remains visible.

There is **no production `main.py` yet**. The imported files keep descriptive test and tool names
so measured session routines remain distinct from the final production program. The team may use
a new Pico for the final build.

## Directory map

```text
src/pico/
├── lib/                    Drivers copied to `/lib` on the Pico
│   ├── bno055.py
│   ├── bno055_base.py
│   ├── PiicoDev_Unified.py
│   └── PiicoDev_VL53L1X.py
├── tools/                  Interactive IMU/steering calibration, including floor-run centre testing
│   ├── calibrate_imu_offsets.py
│   ├── steering_calibrate.py
│   └── steering_calibrate_floorrun.py
├── tests/
│   ├── i2c/                Bus/XSHUT scans and disconnected-pin GPIO health test
│   ├── imu/                IMU smoke, drift and rebuilt-car heading-sign tests
│   ├── tof/                Single- and five-sensor bring-up
│   ├── motor/              Driver checks, duty/floor runs and legacy braking characterization
│   ├── steering/           Free-air and linkage sweep tests
│   └── integration/        System/wall-stop, P/PI straight-line hold and turn-radius tests
└── experiments/            Superseded or currently broken prototypes
```

## What the current code establishes

| Finding | Evidence |
| --- | --- |
| Motor pins | GP2 PWMA, GP3 AIN1, GP4 AIN2, GP5 STBY |
| Motor PWM | 1 kHz |
| Measured forward direction | `FORWARD = -1`: direction B, AIN1 low and AIN2 high |
| Measured chassis duty floor | `MIN_DUTY = 15%` at 5 V / 1 kHz |
| Steering signal | GP0, 50 Hz |
| Current rebuilt sensor bus | I2C1: GP6 SDA, GP7 SCL |
| Retired sensor pins | GP9 is known damaged; GP8 is unused on the rebuilt vehicle |
| ToF shutdown pins | GP10–GP14 |
| ToF reassigned addresses | `0x30`–`0x34` |
| BNO055 address | `0x28` |
| Safe sensor initialisation | Wake and readdress every ToF sensor, then construct the BNO055 last |
| Run button | GP15, internal pull-up, active low |

The saved BNO055 offsets in the later tests belong to the sensor and mounting used during those
tests. Recalibrate after moving the IMU or changing the vehicle.

The current rebuilt vehicle uses I2C1 on GP6/GP7. The imported `wall_stop.py` and
`braking_distance_characterisation.py` are preserved historical tests from measured sessions and
still use the old I2C0 GP8/GP9 wiring. Their pins are evidence, not the current hardware authority.
If a new Pico is used for final production, the final bus assignment will be confirmed again.

Current steering evidence is also a progression, not one universal centre value. The P-only
straight-line test records a 1290 us baseline; later floor and PI work uses 1262 us near the
backlash-band midpoint. The measured safe endpoints are 1480 us left and 1010 us right. Runs
approaching centre from opposite directions settled about 60 us apart, demonstrating linkage
backlash. Recalibrate for the current mechanism and approach direction.

## Deploying a test to the Pico

1. Flash MicroPython to the Pico.
2. Copy all four files from `src/pico/lib/` to `/lib/` on the Pico. Their filenames and flat
   placement are required by imports such as `import bno055` and
   `from PiicoDev_VL53L1X import PiicoDev_VL53L1X`.
3. Copy **one** required tool or test to the Pico root and run it from Thonny or `mpremote`.
4. For any motor or steering test, put the vehicle on blocks first and keep the wheels clear.
5. Stop the test normally and confirm PWM and STBY return to the safe state.

The rebuilt vehicle's GP9 fault is the important compatibility distinction: routines written after
the rebuild use GP6/GP7, while preserved wall-stop and braking-session routines still record the
earlier GP8/GP9 setup.

Example with `mpremote`:

```bash
mpremote fs cp src/pico/lib/bno055.py :/lib/bno055.py
mpremote fs cp src/pico/lib/bno055_base.py :/lib/bno055_base.py
mpremote fs cp src/pico/lib/PiicoDev_Unified.py :/lib/PiicoDev_Unified.py
mpremote fs cp src/pico/lib/PiicoDev_VL53L1X.py :/lib/PiicoDev_VL53L1X.py
mpremote fs cp src/pico/tests/tof/sensor_bringup_final.py :/sensor_bringup_final.py
mpremote run src/pico/tests/tof/sensor_bringup_final.py
```

## Known inconsistencies — read before running

- **Motor direction:** newer measured scripts use `FORWARD = -1`. Some early files
  (`motor_init.py`, `motor_states_test.py`, `body_layer_test.py`) call the opposite polarity
  “forward”. They are historical tests, not the authority for vehicle direction.
- **Duty units:** newer scripts use percentages; some early scripts pass raw 16-bit PWM values.
  `60000` is about 91.5%, despite an old comment describing it as approximately 45%.
- **Steering calibration:** several endpoint sets record different linkage stages. Re-run
  the calibration tools and use the current mechanism's measured values. The ~60 us backlash
  evidence means a single centre value cannot be assumed independent of steering history.
- **Straight-line controllers:** the P and PI straight-line-hold routines are retained as confirmed
  tested-session evidence. They remain under `tests/integration/` so they are not confused with the
  future final `main.py`.
- **I2C speed:** the imported sensor scripts use 100 kHz, while the earlier loop-rate experiment
  was recorded at 400 kHz. This must be deliberately standardised in production firmware.
- **GPIO conflict:** `experiments/Multiple_LEDs.py` drives GP13–GP15, which are now ToF shutdown
  and run-button pins. Do not run it on the assembled vehicle.
- **Broken historical experiments:** `experiments/servo_teaching.py` has an indentation syntax
  error, and `experiments/VL53L1X_rng_vrfy.py` imports a driver that is not present. They remain
  only as development-history evidence.

## Source filename changes during import

Repository names normalize spaces, abbreviations and working-session filenames:

| Original working filename | Repository filename |
| --- | --- |
| `servo calibration tool.py` | `tools/steering_calibrate.py` |
| `servo testing init.py` | `tests/steering/servo_freeair_check.py` |
| `imu_calibration_ofsts.py` | `tools/calibrate_imu_offsets.py` |
| `heading_sign.py` | `tests/imu/heading_sign.py` |
| `pin_test.py` | `tests/i2c/pin_test.py` |
| `motor_check.py` | `tests/motor/motor_check.py` |
| `system_check.py` | `tests/integration/system_check.py` |
| `servo_calibration_floorrun.py` | `tools/steering_calibrate_floorrun.py` |
| `wall_stop.py` | `tests/integration/wall_stop.py` |
| `braking_dist_chrctrztn.py` | `tests/motor/braking_distance_characterisation.py` |
| `main_strght_line_hold.py` | `tests/integration/straight_line_hold_p.py` |
| `straight_line_hold_PIctrlr.py` | `tests/integration/straight_line_hold_pi.py` |
| `turn_radius.py` | `tests/integration/turn_radius.py` |

The code contents were preserved during import so test results remain traceable to the exact
session routines.
