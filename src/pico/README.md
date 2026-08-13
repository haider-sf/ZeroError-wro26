# Raspberry Pi Pico firmware and test tools

This directory contains the team's Pico MicroPython work up to 2026-08-13. It is an engineering
record as well as a code directory: early smoke tests, calibration tools, later integration tests
and third-party-compatible drivers are retained so the development path remains visible.

There is **no production `main.py` yet**. None of the motor tests should be renamed to `main.py`
until its direction, duty limits and stop behaviour have been reviewed, because `main.py` starts
automatically when the Pico powers up.

## Directory map

```text
src/pico/
├── lib/                    Drivers copied to `/lib` on the Pico
│   ├── bno055.py
│   ├── bno055_base.py
│   ├── PiicoDev_Unified.py
│   └── PiicoDev_VL53L1X.py
├── tools/                  Interactive calibration utilities
│   ├── calibrate_imu_offsets.py
│   └── steering_calibrate.py
├── tests/
│   ├── i2c/                Bus and XSHUT scan
│   ├── imu/                IMU smoke, drift and heading-sign tests
│   ├── tof/                Single- and five-sensor bring-up
│   ├── motor/              Driver states, polarity, duty floor and floor run
│   ├── steering/           Free-air and linkage sweep tests
│   └── integration/        Combined Body and wheels-up interference tests
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
| Shared sensor bus | I2C0: GP8 SDA, GP9 SCL |
| ToF shutdown pins | GP10–GP14 |
| ToF reassigned addresses | `0x30`–`0x34` |
| BNO055 address | `0x28` |
| Safe sensor initialisation | Wake and readdress every ToF sensor, then construct the BNO055 last |
| Run button | GP15, internal pull-up, active low |

The saved BNO055 offsets in the later tests belong to the sensor and mounting used during those
tests. Recalibrate after moving the IMU or changing the vehicle.

## Deploying a test to the Pico

1. Flash MicroPython to the Pico.
2. Copy all four files from `src/pico/lib/` to `/lib/` on the Pico. Their filenames and flat
   placement are required by imports such as `import bno055` and
   `from PiicoDev_VL53L1X import PiicoDev_VL53L1X`.
3. Copy **one** required tool or test to the Pico root and run it from Thonny or `mpremote`.
4. For any motor or steering test, put the vehicle on blocks first and keep the wheels clear.
5. Stop the test normally and confirm PWM and STBY return to the safe state.

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
  `tools/steering_calibrate.py` and use the current mechanism's measured values.
- **I2C speed:** the imported sensor scripts use 100 kHz, while the earlier loop-rate experiment
  was recorded at 400 kHz. This must be deliberately standardised in production firmware.
- **GPIO conflict:** `experiments/Multiple_LEDs.py` drives GP13–GP15, which are now ToF shutdown
  and run-button pins. Do not run it on the assembled vehicle.
- **Broken historical experiments:** `experiments/servo_teaching.py` has an indentation syntax
  error, and `experiments/VL53L1X_rng_vrfy.py` imports a driver that is not present. They remain
  only as development-history evidence.

## Source filename changes during import

Two files were renamed to remove spaces and one typo was clarified:

| Original working filename | Repository filename |
| --- | --- |
| `servo calibration tool.py` | `tools/steering_calibrate.py` |
| `servo testing init.py` | `tests/steering/servo_freeair_check.py` |
| `imu_calibration_ofsts.py` | `tools/calibrate_imu_offsets.py` |

The code contents were preserved during import. Known defects are documented rather than silently
rewritten so test results can still be traced to the script that produced them.
