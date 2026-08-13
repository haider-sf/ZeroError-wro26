# AGENT.md — Documentation Agent Brief

**Repository:** WRO 2026 Future Engineers — Team Zero Error
**Working with:** Tawassal Zahra (Body layer)

You are the documentation assistant for this repository. Your job is to help finish and improve
the engineering documentation so it scores well against the WRO judging rubric.

**Start by reading the repository as it actually is.** A `README.md` already exists with real
content in it. Do not assume it is empty, and do not overwrite it — read it first, work out what
it already covers, then build from there. Use this brief for project background, the rules you
must respect, and the standard the documentation has to meet.

Keep a running ledger (§7). Update it every session.

---

## 1. First actions in any session

Do these before writing anything:

1. **Read `README.md` in full.** Note which sections exist, what they cover well, and where the gaps are.
2. **Survey the repo tree.** Which directories exist? Is there code in `src/`? Photos? Videos?
3. **Reconcile with the ledger (§7).** Update it to match what you actually found. The ledger is the
   shared source of truth between sessions — an accurate one is worth more than an optimistic one.
4. **State your plan** for the session before making changes.

**Never overwrite existing README content wholesale.** Extend, restructure and improve it — the
student has already written real material there and it must not be lost. If a section genuinely
needs rewriting, show the proposed replacement and say why before replacing it.

---

## 2. What this project is

**Team Zero Error** is a school robotics team from **St. Francis Schools and Colleges,
Sara-i-Alamgir, Pakistan**, competing in **WRO 2026 Future Engineers (Self-Driving Cars)**,
targeting **September 2026**.

The team is building a **fully autonomous 1:16 scale self-driving car** that must complete:

1. **Open Challenge** — three laps of a track with a randomised inner-wall configuration.
2. **Obstacle Challenge** — the same track plus red/green pillars (traffic signs), which must be
   passed on the correct side: **red = pass on the right, green = pass on the left**.
3. **Parallel parking** — park in a lot marked by two magenta limiters.

**Three students, three layers:**

| Student | Layer | Responsibility |
|---|---|---|
| Tawassal Zahra | **Body** | Physical wiring, mechanical setup, chassis, steering linkage |
| Nukhba Tanveer | **Senses** | Sensors, power, data logging, build documentation |
| Abiha Zainab | **Brain** | Code logic, state machine, unit testing |

Coach: Haider (principal architect).

### Vehicle architecture — document this, don't redesign it

- **Chassis:** 1:16 RC car, servo-converted Ackermann steering (SG90 servo, bicycle-spoke linkage to
  the original yoke, centering spring removed)
- **Compute:** Raspberry Pi 5 (brain — vision + strategy) + Raspberry Pi Pico (body controller —
  real-time fast loop, MicroPython)
- **Motor driver:** TB6612FNG. `FORWARD = -1` (direction B drives forward). `MIN_DUTY = 15%` at 5 V / 1 kHz
- **Power:** Two 3S LiPo packs; dedicated regulated 5 V TPS5450 buck for the motor rail; TPS5450 for
  the compute rail; star-ground topology; DPDT switch for simultaneous rail isolation.
  **The EN pin on the TPS5450 must float-to-run, never be tied to VIN.**
- **Sensors:** Five VL53L1X ToF distance sensors (confirmed L1X — model-ID register `0x010F` = `0xEACC`),
  BNO055 IMU, reflective optical encoder (TCRT5000-based), RPi Camera Module 3 Wide
- **Sensor offset:** `SENSOR_OFFSET_MM = -10` (sensor sits 10 mm ahead of the bumper)
- **Heading convention:** clockwise-positive — a right turn increases heading
- **Bus:** all ToF + IMU on one I²C bus (I2C0, GP8/GP9). IMU at `0x28` (ADR soldered to GND, pads
  bridged). ToF sensors readdressed to `0x30`–`0x34` by SHUT-sequencing.

### Pico pin map

| Pin | Function |
|---|---|
| GP0 | Servo PWM (50 Hz) |
| GP2 | Motor PWMA |
| GP3 | Motor AIN1 |
| GP4 | Motor AIN2 |
| GP5 | Motor STBY |
| GP8 | I2C0 SDA |
| GP9 | I2C0 SCL |
| GP10–GP14 | ToF SHUT lines |
| GP15 | Run button (internal pull-up, active low) |
| GP16 | Encoder (planned) |
| VSYS (phys 39) | External 5 V in |
| 3V3 (phys 36) | Sensor power out |

---

## 3. Rules you must respect

From the WRO 2026 General Rules. Breaking these costs real points.

### Rule 7 — Repository requirements
- Repo must be **public** from submission, and stay public **12 months** after the competition.
- **`README.md` must be at least 5000 characters**, in English.
- It must clarify **which modules the code consists of**, **how they relate to the electromechanical
  components**, and **the process to build / compile / upload the code** to the vehicle's controllers.
- Commit history must contain **at least 3 commits**:
  - First: **≥2 months before** the competition, containing **≥1/5 of the final code**
  - Second: **≥1 month before**
  - Third: **≥2 weeks before** — *this is the commit used for scoring*
- Required content: mobility / power / sense / obstacle-management discussion; **photos of the vehicle
  from every side, top and bottom**; a **team photo**; **YouTube links** (public or link-accessible)
  showing autonomous driving, **≥30 seconds** of driving footage, **one video per challenge**.
- Official template: https://github.com/World-Robot-Olympiad-Association/wro2022-fe-template

### Rule 3.3 — Own work
Substantive commits come from **student accounts**. The coach owns the repo as admin but does not
commit engineering content. Co-author trailers in extended commit descriptions preserve shared
attribution where students worked together.

### Vehicle constraints to state in the documentation
- Max dimensions **300 × 200 mm, 300 mm height** (rule 9.17); max **1.5 kg**
- **Rule 11.3 permits FWD, RWD and 4WD.** It prohibits **only differential drive** (steering by
  independent left/right motor speed). Do **not** write that 4WD is prohibited — that is a
  previously-corrected error and must not reappear.

---

## 4. What the documentation must cover

Organise around the **Appendix C engineering-journal rubric**. Judges score evidence of an
engineering *process*, not just a finished car. Check the existing README against this list and
fill the gaps.

### 4.1 Required sections

**Mobility management**
- Chassis choice, drivetrain, steering mechanism (Ackermann conversion, servo linkage, removed
  centering spring)
- Motor selection and driver (TB6612FNG), speed control, the `MIN_DUTY` finding
- Steering calibration: LEFT / CENTER / RIGHT endpoints and how they were found — the largest wheel
  deflection reached at **idle servo current**, *not* by driving into the mechanical stop. Note the
  left/right asymmetry.
- Turning radius, measured empirically (`R = s/Δθ` from encoder + IMU)

**Power and sense management**
- Battery architecture, buck converters, star ground, rail isolation
- Every sensor: what it is, why it was chosen, what it measures, how it's mounted
- **Include the measurements** — see §4.2. This is where most teams lose points, by asserting instead
  of showing.

**Obstacle management**
- Pillar detection: **geometry-based is primary; camera colour detection is the upgrade layer**
- Red/green passing logic (red → right, green → left)
- Parking approach
- Wall-following and corner strategy

**Software**
- Three-layer **Body / Senses / Brain** architecture split across the Pi 5 and the Pico
- State machine description
- Module list, and how each module maps to hardware
- Build/upload process for **both** controllers (explicitly required by Rule 7)

### 4.2 Measurements to include — show the data

The team has taken real measurements. The documentation must show them, not just conclusions:

- **ToF noise vs distance:** σ ≈ 1.5 mm @ 500 mm → 2.4 mm @ 1000 mm → 3.2 mm @ 1200 mm
- **ToF accuracy:** +13 mm @ 500, +1 mm @ 1000, −12 mm @ 1200 — a sign-changing scale/linearity effect,
  not a fixed offset (partly tape-reference error; measure from the optical window)
- **ToF field of view:** ~27° cone — reports the nearest object anywhere within the cone
- **Loop rate:** ~555 loops/sec for 2 sensors; ~185 predicted for 6. This measurement **retired** the
  need for an I²C mux, a second Pico, and timing-budget tuning. Document that reasoning —
  evidence-driven decisions are exactly what the rubric rewards.
- **IMU drift:** ~40°/min with the accelerometer *uncalibrated*; ~0°/min *calibrated* (stationary).
  On-car drift under motion is still to be measured.
- **Power:** 5.00 V at rest, 4.88–4.90 V startup inrush, 4.93–4.95 V steady; stall minimum
  ~4.87–4.89 V with the pack at ~12.1 V
- **Wheels-up interference test:** 0.00°/min heading drift across all motor duty phases including 70%
  and 1 Hz reversal; ToF stable within 0.5 mm; 100% valid reads; zero I²C errors

### 4.3 Reversed-decisions log

Maintain a section in the README documenting design changes and why earlier approaches were retired.
Judges reward visible iteration. Already on record:

- **LiDAR (RPLidar A1) rejected** — scan-plane geometry: the walls are only 100 mm tall
  (rules 13.3 / 13.5), as are the pillars (13.19) and parking limiters (13.25). Note this was **not** a
  black-surface issue: the A1 uses triangulation (reflectivity-sensitive), while the VL53L1X uses direct
  ToF/SPAD sensing (black-tolerant). Different physics.
- **I²C mux and second Pico rejected** — retired by the loop-rate measurement (§4.2)
- **Encoder pivots** — optical disc → magnetic → back to reflective optical (TCRT5000). Driven by the
  ~10 mm/pulse resolution requirement for parking.
- **Driver choice** — PiicoDev VL53L1X chosen over alternatives specifically for its per-reading
  **validity status flag** and `change_addr()` support

### 4.4 Engineering findings worth documenting

Hard-won, and good evidence of a real debugging process:

- **IMU initialisation order is load-bearing** — the BNO055 must be constructed **last**. Each VL53L1X
  instantiation reinitialises the I²C peripheral and **silently** breaks a previously constructed IMU
  object, with no error raised.
- **IMU calibration needs a quiet bus** — the accelerometer will not reach calibration level 3 while
  five ToF sensors are streaming. Calibrate before waking the ToF sensors, or load saved offsets.
- **BNO055 configuration latches at power-on** — both ADR-low *and* the bridged pads must be true
  *before* power is applied. Changes made after boot appear to work but do not survive a power cycle.
- **Heading wraparound** — 0° and 360° are the same point. Every heading comparison must fold the
  difference into ±180, or a 0.1° drift reads as a 359.9° rotation.
- **Fail-safe over fail-forward** — any sensor read inside a control loop must be wrapped in exception
  handling. A bare `tof.read()` that throws causes the stop condition never to fire.
- **ToF short-distance mode** used exclusively — WRO corridor geometry falls within the 1.3 m ceiling;
  ambient-light vulnerability in long mode is a configuration issue, not a hardware one.
- **Paired dual-sensor baseline** — two ToF sensors on one side at a known separation extract wall
  angle. Structurally impossible with single ultrasonic sensors.

---

## 5. Repository structure

Follow the official WRO template naming — judges look for it:

```
/
├── README.md              # ≥5000 chars — the main scored document
├── AGENT.md               # this brief
├── src/                   # all code
│   ├── pico/              # MicroPython — body/senses fast loop
│   │   ├── main.py
│   │   ├── drivers/       # PiicoDev_VL53L1X.py, PiicoDev_Unified.py, bno055.py, bno055_base.py
│   │   └── ...
│   └── pi/                # Python — vision + strategy
├── models/                # 3D print / laser / CNC files
├── schemes/               # wiring diagrams, electromechanical schematics
├── t-photos/              # team photos
├── v-photos/              # vehicle photos — every side, top, bottom
├── video/                 # video.md with YouTube links
├── docs/                  # engineering journal, test logs, measurement data
│   ├── journal/           # dated build-log entries
│   └── data/              # raw measurement logs / CSVs
└── other/                 # datasheets, references
```

Propose structural changes before making them — reorganising affects the whole team's work.

---

## 6. How to work

- **Read before writing.** The README has existing content. Extend it; don't replace it blindly.
- **Never invent measurements or results.** If a section needs a number the team hasn't measured, write
  `TODO: measure` and log it in §7.5. **Fabricated data is worse than an obvious gap** — a judge who
  spots invented evidence will distrust the whole document.
- **Explain why, not just what.** "We chose X" scores poorly. "We chose X because we measured Y, which
  ruled out Z" is what the rubric rewards. Every significant choice should show its reasoning.
- **Flag rule violations.** If content contradicts the rules, say so and cite the rule number.
- **Write in English** (Rule 7 requirement for the international final).

### Photo handling
- **Resize to ~1600 px on the long edge, under 500 KB** before adding. Git history is permanent — a
  5 MB photo stays in the repo forever.
- **Commit photos before the README references them**, or links render broken.
- **Case sensitivity matters** — GitHub runs Linux. `Photo.JPG` ≠ `photo.jpg`.

---

## 7. Running Ledger

**Maintain this section. Reconcile it with the actual repo at the start of each session, and update it
at the end. Keep it honest — an accurate list of gaps is more useful than an optimistic one.**

### 7.1 Done
*(Surveyed 2026-08-13.)*

- [x] **README.md exists and is substantial** — ~96 775 characters (well above Rule 7’s 5000). English.
- [x] **Mobility management** written in depth (chassis choice, Ackermann conversion iterations,
  servo current-based end-stop method, TB6612FNG vs L298N, motor rail regulation vs duty-cap).
- [x] **Power architecture** written (dual 3S, three TPS5450 bucks, star ground, EN-pin caution,
  charge protocol).
- [x] **Sense management** written (VL53L1X verification, SHORT mode, XSHUT addressing, loop-rate
  ~555/s and retired workarounds, paired-baseline plan, LiDAR/ultrasonic rejection reasoning).
- [x] **Obstacle / parking / wall-follow strategy** sketched (geometry-primary, Rule 9.19 sides,
  state-machine ASCII, parking bay scaling argument).
- [x] **Software architecture** — Body / Senses / Brain; module map; Pi↔Pico intent; build/flash
  outline for both controllers.
- [x] **Reversed-decisions log** present (Section 8 + “Decisions reversed after measurement”).
- [x] **Rule 11.3 / differential-drive** correctly stated (4WD not prohibited).
- [x] **WRO template folders** present: `src/`, `schemes/`, `models/`, `t-photos/`, `v-photos/`,
  `video/`, plus `docs/` placeholders.
- [x] **Team photos added 2026-08-13** — group photo and labelled portraits for Abiha Zainab,
  Tawassal Zahra and Nukhba Tanveer stored locally in `t-photos/`, indexed in its README and
  embedded in the main README.
- [x] Multiple git commits exist on `main` (mostly README / skeleton).
- [x] **Steering build-process photos added 2026-08-13** — ten resized/source-compliant images in
  `v-photos/`, indexed in `v-photos/README.md`, with selected chronological evidence embedded in
  README Sections 4a and 4c. These do not count as the six mandatory final-vehicle views.

### 7.2 In progress

- [ ] **README Section 4 structure** — `## e) Power` and `## f) Sensors` currently sit *after*
  Section 12 (end of file), not under Section 4 with a–d. Part-merge order needs fixing without
  losing content.
- [ ] **Pin assignment table (§4g)** — servo/motor pins still marked `PENDING` in README while
  this brief lists confirmed GP0 / GP2–GP5. Needs team confirmation before editing.
- [ ] **Measurement data tables** — loop rate is in README; ToF noise/accuracy, IMU stationary
  drift, rail voltage under load, wheels-up interference from brief §4.2 are **not** yet shown as
  data tables.
- [ ] Pi 5 / Pico setup checklists partially `DONE`, deployment scripts still `PENDING`.

### 7.3 To do — blocking / high priority

- [ ] **Upload code to `src/`**
  - [ ] Pico MicroPython: `main.py`, sensor bring-up, drivers — **dirs empty** (placeholder README only)
  - [ ] Pi 5: vision pipeline — **empty**
  - [ ] Check against the first-commit deadline: **≥1/5 of final code, ≥2 months before competition**
- [ ] **Finished-vehicle photos** — front, rear, left, right, top and bottom → `v-photos/`.
  Build-process photos now exist, but they do not satisfy the six-view Rule 7 requirement.
- [ ] **Videos** — one per challenge, ≥30 s autonomous driving, YouTube links → `video/video.md`
  (placeholder only)
- [ ] Create `other/` (datasheets, `calibration_log.md`, `test_log.md` are referenced but folder
  missing)
- [ ] Wiring / mechanical / state-machine diagrams → `schemes/` (placeholder only)
- [ ] Align `docs/` naming with brief (`journal/`, `data/`) **or** document the current layout —
  propose before renaming

### 7.4 To do — documentation content

- [x] Mobility management section *(present; some measured values still PENDING)*
- [x] Power and sense management section *(present but misplaced after §12)*
- [x] Obstacle management section *(strategy present; implementation PENDING)*
- [x] Software architecture section *(present)*
- [ ] Wiring diagrams / schematics → `schemes/`
- [x] Reversed-decisions log in the README
- [ ] Measurement data tables → `docs/data/` (or equivalent)
- [ ] Engineering journal entries → `docs/engineering-journal/` (placeholder only)
- [ ] Fill Body-layer PENDING numbers: track width, L×W×H, mass, servo LEFT/CENTER/RIGHT,
  turning radius, motor stall current
- [ ] Nukhba bio still has `[NUKHBA TO WRITE…]` placeholder
- [ ] Confirm second-chassis redundancy claim before publishing
- [ ] Resolve **MIN_DUTY** discrepancy: brief says **15%**, README says **~13%** at 5 V / 1 kHz —
  do not invent; ask team which is authoritative
- [ ] Document `FORWARD = -1`, heading clockwise-positive, `SENSOR_OFFSET_MM = -10` when confirmed
- [ ] Add engineering findings from brief §4.4 (IMU init order, quiet-bus calibration, heading wrap,
  fail-safe reads) once verified by the team

### 7.5 Blocked / waiting on the team

- [ ] On-car IMU drift under motion — not yet measured (needs a driving car)
- [ ] Encoder bring-up and turning-radius measurement — hardware pending
- [ ] Camera / CV pipeline — in development
- [ ] Competition videos — cannot be filmed until the car drives autonomously
- [ ] Black-wall reflectivity test — gates ultrasonic redundancy decision
- [ ] Confirm Pico pin map (GP0, GP2–GP5, GP15, GP16) before writing into README §4g
- [ ] Confirm MIN_DUTY 13% vs 15%

### 7.6 Open questions

- [ ] Should Power/Sensors (§4e/4f) be moved up under Section 4 now, or wait for Nukhba to own the edit?
- [ ] Prefer renaming `docs/engineering-journal` → `docs/journal` and adding `docs/data/`, or keep
  current names and update the brief?
- [ ] This session focus for Tawassal (Body): pin map + mobility PENDING fields, or README
  restructure first?

---

## 8. End-of-session protocol

1. Update §7 — move completed items to Done with dates, add newly discovered gaps.
2. Summarise what changed in the repo.
3. Note any rule-compliance concerns you found.
4. List anything you marked `TODO: measure`, so the team knows what data to collect.

---

*Team Zero Error · WRO 2026 Future Engineers · Self-Driving Cars*
