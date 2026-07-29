
# SECTION 1 — Project Zero Error

We are Team Zero Error, a team of three students from St. Francis Schools and Colleges in
Sara-i-Alamgir, Pakistan, competing in the WRO 2026 Future Engineers category. For this
challenge, we developed an autonomous 1:16 scale self-driving car that independently navigates a
three-lap track, avoids obstacles, and parks itself without any remote control.

This document records **how the car was designed, not only what it became**. Where a subsystem is
not yet finished, the heading exists with a status marker so our progress is visible rather than
hidden.

| Marker | Meaning |
| --- | --- |
| `DONE` | Built, measured, and the measurement is recorded here |
| `IN PROGRESS` | Hardware exists, characterisation not complete |
| `PENDING` | Designed on paper, not yet built or measured |

---

# SECTION 2 — The Challenge

**Competition Overview**

The World Robot Olympiad (WRO) Future Engineers category is an advanced robotics competition
focused on the design and implementation of autonomous, self-driving cars. The challenge requires
engineering a scale vehicle capable of navigating complex, dynamic environments using real-time
sensor data, computer vision, and steering algorithms without any human intervention.

**Challenge Architecture**

The competition is divided into two distinct challenges. Note: parking is integrated into the
second challenge rather than existing as a standalone event.

1. **Open Challenge:** The vehicle must autonomously complete 3 full laps on a walled track. The
   robot must identify the correct driving direction, maintain lane control, and bring itself to a
   complete stop in the correct section after the final lap.

2. **Obstacle Challenge:** This phase adds traffic signs. The vehicle must complete 3 laps while
   navigating around red and green pillars, following the passing rules:
   - **Red pillars:** must be passed on the right (Rule 9.19)
   - **Green pillars:** must be passed on the left (Rule 9.19)

3. Upon completing the final lap, the vehicle must locate the designated magenta parking lot and
   execute a parallel parking manoeuvre.

**Field Specifications**

| Property | Value | Rule |
| --- | --- | --- |
| Mat size | 3200 × 3200 mm | 13.1 |
| Inner racetrack | 3000 × 3000 mm | 13.1 |
| Wall height, exterior and interior | 100 mm | 13.3, 13.5 |
| Corridor width, Open Challenge | **1000 mm or 600 mm** (randomised per round) | §8 |
| Corridor width, Obstacle Challenge | Always 1000 mm | §8 |
| Traffic sign dimensions | 50 × 50 × 100 mm | 13.19 |
| Red sign colour | RGB (238, 39, 55) | 13.21 |
| Green sign colour | RGB (68, 214, 44) | 13.22 |
| Parking limitation colour | Magenta, RGB (255, 0, 255) | 13.27 |
| Parking lot width | 200 mm | §5 |
| Parking lot length | **1.5 × robot length** | §5 |
| Maximum vehicle dimensions | 300 × 200 mm, 300 mm height | 9.17 |

Two constraints from this table shaped our design more than any other:

- **The 600 mm corridor.** The Open Challenge corridor can be narrow, and the width is randomised
  before each round. Our vehicle must fit and turn inside 600 mm, which puts a hard ceiling on
  both our vehicle length and our minimum turning radius.
- **The parking lot scales with our own vehicle.** Because the bay is 1.5 × our robot's length,
  a longer robot does *not* get a proportionally easier park — the clearance stays at 0.5 × our
  length regardless. But a longer robot needs a larger turning radius to enter that bay. **Shorter
  is strictly better for parking.**

**Scoring Breakdown**

| Assessment Area | Maximum Points |
| --- | --- |
| Open Challenge | 30 |
| Obstacle Challenge | 62 |
| Technical Documentation | 30 |
| **Total** | **122** |

**Easily missed rules we have written into our checklist**

| Rule | What it means for us |
| --- | --- |
| 9.17 | Dimensions are checked. Exceeding them after a 3-minute repair window ends the round |
| 9.18 | In the Open Challenge the vehicle **may not touch the outer boundary wall** at all |
| 9.20 / 13.15 | A pillar may be touched only if it stays within an 85 mm circle around its seat |
| 9.24.7 | Touching a **parking lot limitation** stops the round |
| 9.21 | Driving opposite the round direction is allowed for two sections only |
| 13.18 | Mat and object colours may differ from spec — on-site colour recalibration is expected |
| §6 | A **surprise rule** is expected in the 2026 season. Our software must be modular enough to absorb a new behaviour |

---

# SECTION 3 — The Team

**Student Biographies**

- **Abiha Zainab — Brain layer (Software)**
  - Responsible for architecting the vehicle's autonomous navigation logic and decision-making
    frameworks. Implements the finite state machine that handles the track environment, integrates
    sensor data into decisions, and tunes the steering control feedback loop for lane-keeping and
    obstacle avoidance.
  - Technical interest: software development, control algorithms, and system logic.

- **Tawassal Zahra — Body layer (Hardware)**
  - Responsible for the physical chassis, structural integrity, and mechanical integration.
    Manages the layout and mounting of the controllers, drive motor, steering servo, and power
    distribution, and owns the steering conversion described in Section 4c.
  - Technical interest: mechanical engineering principles, chassis dynamics, and robust hardware
    design.

- **Nukhba Tanveer — Senses layer (Sensors, Power and Documentation)**
  - Owns the sensing and power subsystems: ToF sensor configuration and addressing, IMU
    integration, encoder odometry, power distribution and wiring. Also owns the data-logging
    protocol and the technical documentation record.
  - Technical interest: `[NUKHBA TO WRITE IN HER OWN WORDS — do not inherit the previous
    member's text. Judges may ask a student to explain their own subsystem.]`

The three roles map directly onto the three layers described in Section 5 — Body, Senses and
Brain. Each of us owns one layer end to end, from the hardware to the code that drives it.

**Coaching & Guidance**

**Haider Abbas** provides organisational oversight and strategic guidance as the team coach. His
role covers administrative facilitation and milestone tracking, ensuring that the student
engineering team retains complete autonomy over both hardware fabrication and codebase execution.

---

# SECTION 4 — Our Vehicle

This section covers the physical setup and the compute setup of our autonomous car.

## a) Chassis

**Mechanical Specifications**

| Property | Value | Status |
| --- | --- | --- |
| Scale | 1:16 RC car, converted | `DONE` |
| Drive configuration | Rear-wheel drive, single motor | `DONE` |
| Steering | Front-wheel Ackermann, servo actuated | `DONE` |
| Wheelbase | 160 mm | `DONE` |
| Track width | `[PENDING]` | `PENDING` |
| Overall L × W × H | `[PENDING — must be inside 300 × 200 × 300 mm, Rule 9.17]` | `PENDING` |
| Mass, race-ready | `[PENDING]` | `PENDING` |
| Minimum turning radius | `[PENDING — see §4d]` | `PENDING` |

**Why a converted RC chassis instead of a scratch build?**

We evaluated three options before committing.

- **Build from scratch (acrylic or aluminium plate, bought wheels and axles).** Maximum design
  freedom. Rejected because our team is code-strong and new to mechanical fabrication, and we do
  not have reliable access to machining. Building a rigid, square, low-backlash steering linkage
  from raw stock is a multi-week job with a high chance of a floppy result.
- **A kit robotics platform.** Fast and reliable, but the kits available to us are
  differential-drive. The category explicitly asks for kinematics *different* from differential
  drive, so this would have missed the point of the challenge.
- **Convert a commercial 1:16 RC car. — Chosen.** The chassis already gives us a rigid moulded
  frame, a proper Ackermann steering knuckle set, a rear differential and bearings that we could
  not fabricate to the same tolerance. The conversion work is bounded and specific: replace the
  radio receiver and the crude steering actuator with our own electronics.

**Trade-off accepted:** we lose control over the geometry. We inherit the manufacturer's
wheelbase, track and steering throw, and we must design our sensor and electronics mounting around
an existing shape. We judged this a good trade — mechanical rigidity is expensive to buy with
labour and cheap to buy with a donor chassis.

**Rule compliance — why a single motor and a mechanical differential are allowed**

The rules prohibit steering by commanding the left and right wheels at different speeds
(differential or skid steering). They do **not** restrict how many wheels are driven — front,
rear and four-wheel drive are all acceptable, provided direction of travel is set by a steering
mechanism.

Our chassis has a mechanical differential in the rear axle. This is not differential *drive*: it
passively splits torque between two wheels and is not commanded by the controller. Our single
motor physically cannot produce a commanded speed difference, which is exactly the property the
rule protects.

> We initially misread this rule during our own design discussion and nearly rejected a valid
> chassis option because of it. Re-reading the rule text — not a summary of it — corrected the
> mistake before it cost us anything.

**Sourcing and Redundancy Strategy**

- **Local sourcing.** The chassis was procured from local suppliers, so replacement parts can be
  obtained without long shipping delays. Given our competition timeline, a part that takes three
  weeks to arrive is effectively unavailable.
- **Hardware redundancy.** `[CONFIRM STATUS BEFORE PUBLISHING: does the second chassis physically
  exist and is it untouched? If it is still only planned, mark this PENDING rather than claiming
  it.]` Our intent is to keep an identical second chassis untouched as a backup so that a
  mechanical failure during testing can be resolved by swapping components rather than halting the
  project.

**Chassis modifications made so far**

| Modification | Reason | Status |
| --- | --- | --- |
| Radio receiver and ESC removed | Replaced by our own control electronics | `DONE` |
| Steering actuator replaced with SG90 servo | Original mechanism had no position feedback | `DONE` |
| Motor wired to TB6612FNG H-bridge | Bidirectional PWM control | `DONE` |
| Electronics deck | To carry Pi 5, Pico, power board | `PENDING` |
| Camera mast | Height set by Rule 9.17 envelope and pillar visibility | `PENDING` |
| ToF sensor brackets | Placement described in Section 4f | `PENDING` |
| Encoder disc and sensor mount | See Section 4f | `IN PROGRESS` |

> **Mechanical layout drawing to be added:** `schemes/mechanical_layout.png`
> Top view and side view showing wheelbase, track, sensor positions and centre of mass.
> *(Required for Criterion 1 above level 2.)*

---

## b) Compute Architecture

We split the processing into a two-layer compute architecture to handle high-level logic and
low-level physical control separately.

- **Raspberry Pi 5 (The Brain):** Runs Linux headless (Raspberry Pi OS Lite 64-bit) and handles
  high-level intelligence. It manages the state machine, processes camera vision for pillar
  colour, and calculates driving decisions.

- **Raspberry Pi Pico (The Body controller):** A dedicated real-time controller in constant serial
  communication with the Pi 5. It executes time-critical tasks: PWM for steering and drive, ToF
  sensor polling over I²C, IMU reads, and wheel encoder pulse counting.

**Why two layers?**

A Linux board like the Pi 5 is excellent for heavy computation, but it operates on a "best-effort"
schedule. The operating system is constantly juggling background tasks, so it cannot guarantee the
exact timing needed for stable motor control. Usually the interruption is microseconds.
Occasionally it is tens of milliseconds — and a control loop that should run every 5 ms but
occasionally runs 40 ms late produces a visible steering twitch.

The Pico fixes this with deterministic, real-time control. It runs a single dedicated loop that
executes predictably every time. This division of labour ensures the car's physical reactions are
correctly timed while the Pi 5 focuses on perception and strategy.

**Trade-off accepted:** two controllers means a serial link that can fail, two codebases and two
flashing procedures. We accepted this because the alternative — camera processing and hard
real-time motor control competing for one CPU — has a failure mode (intermittent control glitches)
that is far harder to diagnose than a link that is either up or down.

```
 ┌─────────────────────────────┐        ┌──────────────────────────────┐
 │      RASPBERRY PI 5         │        │      RASPBERRY PI PICO       │
 │                             │        │                              │
 │  Camera (pillar colour)     │ serial │  ToF sensors     (I²C)       │
 │  State machine / strategy   │<------>│  IMU heading     (I²C)       │
 │  Lap counting               │        │  Wheel encoder   (GPIO)      │
 │  Logging                    │        │  Motor PWM  (TB6612FNG)      │
 │                             │        │  Steering servo PWM          │
 └─────────────────────────────┘        └──────────────────────────────┘
          "think"                                  "act"
```

---

## c) Steering

Getting the steering right was our toughest mechanical hurdle. We had to completely re-engineer
the stock setup to get the precision an autonomous car needs. Because this subsystem went through
the most iteration, we document it as a sequence of versions rather than as a finished result.

### Version 0 — the stock mechanism

The chassis came with a DC motor driving a gear sector. The gear sector pushed a **yoke** — a
plastic arm with a slot in it, pinned to a pivot post on the chassis. The yoke pushed the track
rod, which turned both front knuckles together.

The critical limitation: **there is no position feedback anywhere in that chain.** The stock system
is a bang-bang actuator with exactly three achievable states — full left, centre, full right. A car
that can only steer at full lock cannot follow a wall at a controlled offset, and cannot execute a
parking manoeuvre that requires a specific radius.

> **Photo placeholder:** `v-photos/steering_v0_stock.jpg`
> *Stock gear-sector steering before modification, with the yoke visible.*

### Version 1 — direct servo-to-track-rod coupling (rejected on paper)

The obvious first idea was to remove the whole stock assembly and connect a servo horn directly to
the track rod. We rejected it before cutting anything, for two reasons:

1. **Geometry.** The track rod sits low and off-centre. Mounting a servo so its horn arc lines up
   with the required travel meant either cutting into the chassis floor or building a raised
   bracket that would conflict with the front suspension.
2. **Throw mismatch.** A servo horn sweeps an arc; the track rod needs near-linear lateral travel.
   Coupling them directly across a large angle gives a non-linear servo-angle-to-wheel-angle
   relationship, making calibration harder for no benefit.

This is the cheapest kind of iteration — the one done on paper.

### Version 2 — retain the yoke, drive it with the servo (current design)

We mounted an upright SG90 servo into the old steering motor pocket so its horn rotates
horizontally, and kept **the original steering yoke on its original pivot post**. A **bicycle
spoke** drops from a slot in the servo horn down to the yoke.

```
   SG90 servo (upright, in the old motor pocket)
      |
   [ horn, with slot ]
      |
   bicycle spoke push-rod
      |
   [ steering yoke ]  <-- still on its original chassis pivot post
      |
   [ track rod ]
      |
   front knuckles  --->  factory Ackermann geometry, unchanged
```

**Why we built it this way:**

- **The pivot post takes the side-loads, not the servo.** This is the most important decision in
  the mechanism. We explicitly avoided making the servo shaft the pivot point — if we had, every
  bump and side-shock from driving would transmit straight into the servo's internal plastic gears
  and strip them. Keeping the pivot and the drive mechanism separate means the servo only has to
  supply rotating force.
- **The slot absorbs arc mismatch.** The servo horn moves in an arc; the yoke moves through a
  different arc. The slot lets the spoke slide slightly as the angle changes, so the linkage does
  not bind at sharp steering angles.
- **The factory geometry is preserved.** The yoke was designed for that post and the track rod was
  designed to be pushed by that yoke, so we did not have to re-derive any Ackermann geometry.
- **The bicycle spoke is a good push-rod.** Stiff in tension and compression, thin, locally
  available, and bendable with pliers — which gives a free mechanical adjustment for centring
  without touching code.

**Trade-off accepted:** the slot that prevents binding is also clearance, and clearance is
backlash. We have not yet quantified how much steering deadband this introduces.

> **Photo placeholders:**
> - `v-photos/steering_v2_servo_mounted.jpg` — servo upright in the old motor pocket
> - `v-photos/steering_v2_spoke_linkage.jpg` — close-up of the spoke, horn slot and yoke
> - `v-photos/steering_v2_full_left.jpg` / `..._full_right.jpg` — both lock limits

### Iteration inside Version 2 — the hunting-noise problem

After assembly the servo made a continuous straining noise at large steering angles and drew
current continuously instead of settling.

**Our first instinct was wrong.** We assumed the SG90 was too weak and began looking at metal-gear
replacements. Before buying anything, we measured servo current across a range of commanded angles.

**What the measurement showed:** at moderate angles the servo settled to idle current
(~10–20 mA). At large angles the current stayed high indefinitely. That is not the signature of a
weak servo — a weak servo fails to reach position and spikes current *regardless of angle*. Current
that is normal in the middle and continuous at the extremes means the servo is being commanded
**past the mechanical steering limit** and is pushing against a hard stop forever.

**The fix was in software:** define `LEFT_MAX` and `RIGHT_MAX` end-stops and never command outside
them. Cost: zero. The servo we already had was adequate.

**The lesson we wrote down:** *an unexpected reading is a reason to measure, not a reason to buy.*
We named this failure mode "anxiety → addition" and we now check for it deliberately.

### Software safeguards

Steering end-stops are enforced in the Pico firmware, so the servo can never be driven past its
safe physical range regardless of what the Brain layer asks for. A mechanical constraint belongs
in the layer closest to the mechanism — the state machine should not have to know about it.

### Servo calibration procedure

**Criterion:** the usable steering limit is the largest wheel deflection at which servo current
returns to idle (~10–20 mA) and stays there.

1. Vehicle on blocks, wheels free, ammeter in the servo supply line.
2. Command a small angle from centre. Wait 2 s. Record current.
3. Increase the commanded angle in steps, repeating step 2.
4. The last angle at which current returns to idle is that side's mechanical limit.
5. **Approach the same angle from the opposite direction and repeat.** Any difference between the
   limit found going outward and coming inward *is* the linkage backlash.
6. Repeat independently for left and right. **Expect asymmetry** — the linkage is not symmetric,
   so there is no reason for the two limits to match.

| Parameter | Value | Status |
| --- | --- | --- |
| `SERVO_CENTRE` | `[PENDING]` | `PENDING` |
| `LEFT_MAX` | `[PENDING]` | `PENDING` |
| `RIGHT_MAX` | `[PENDING]` | `PENDING` |
| Measured backlash / deadband | `[PENDING]` | `PENDING` |

Tool: `src/pico/calibrate_servo.py` — interactive, steps the servo from the serial console so
values can be found without re-flashing.

### Version 3 — planned improvements `PENDING`

- **Backlash reduction.** If the measured deadband affects wall following, a light spring preload
  would take up the slack in one direction.
- **Mount rigidity check.** If the servo mount flexes under cornering load, steering angle will
  vary with speed — a bug that only appears on the field.

---

## d) Drive

- **The motor setup.** We kept the stock small brushed DC motor, which drives the rear axle
  through the vehicle's built-in gearbox.
- **Why the stock motor?** Fitting a larger motor would require modifying the chassis in ways that
  compromise its structural integrity. Keeping it stock preserves chassis strength, and our torque
  demand is low: the vehicle is light, drives on a flat mat, and never climbs.
- **Motor rating: 5 V.** This is the number that drives the whole power decision below.
- **Control method.** PWM from the Pico through a TB6612FNG motor driver, supplied from a
  **dedicated 5 V buck converter** — not from the raw battery.

**Why the TB6612FNG over the L298N?**

| | TB6612FNG | L298N |
| --- | --- | --- |
| Switching element | MOSFET | Bipolar (BJT) |
| Voltage drop at load | ~0.5 V total | ~2 V+ total |
| Waste heat | Low, no heatsink needed | High, large heatsink required |
| Mass and volume | Small | Bulky |

The deciding argument is voltage drop. Every volt lost in the driver is a volt not delivered to
the wheels, and it returns as heat that must be carried around as heatsink mass. **Trade-off
accepted:** the TB6612FNG has a lower continuous current rating, which is not binding for a 1:16
chassis but would need revisiting on a larger vehicle.

### Motor driver bring-up measurements `DONE`

| Measurement | Result | Conditions | What it tells us |
| --- | --- | --- | --- |
| Free-run current | ~140 mA | Test rail, no load | Baseline for the power budget |
| Minimum effective duty cycle | ~13 % | **5 V rail, 1 kHz PWM** | Below this the motor does not turn at all |

Because these figures were taken **at 5 V / 1 kHz, which is the rail the motor now actually runs
on**, they are valid operating numbers rather than bench approximations. This was not true of an
earlier version of our design — see below.

The minimum duty result feeds directly into the control software. Any speed controller that
outputs below the floor is commanding a stall, not a slow crawl. The Body layer clamps its output
above this floor rather than assuming duty maps linearly to speed down to zero.

### Motor voltage: iteration from duty-capping to rail regulation

This is a design change we made after examining our own reasoning, and it is worth recording in
full because the first version was defensible-sounding and wrong.

**Version 1 — raw battery, limited by duty cycle.** Our original plan ran the motor directly from
the 11.1 V pack and capped the PWM duty cycle in firmware to roughly 45 %, on the reasoning that
45 % of 11.1 V gives an average of about 5 V, which is what the motor is rated for.

**Why we abandoned it.** The argument confuses average voltage with what the motor actually
experiences.

- A duty cap reduces the *average* voltage. It does **not** reduce the peak. During every ON pulse
  the motor still sees the full 11.1 V across its windings.
- Motor heating depends on **RMS current, not average voltage**. At the same average voltage, a
  chopped 11.1 V supply produces higher peak and RMS current than a steady 5 V supply.
- The problem is worst exactly where it matters most — at stall or breakaway, back-EMF is zero and
  current is limited only by winding resistance. That is when a 5 V-rated motor sees 11.1 V pulses
  through a near-short.
- We had also written that the high rail "gives plenty of instant torque headroom." That
  contradicts the cap: headroom above the cap is headroom the software will never use. We cannot
  claim the cap as protection and as headroom simultaneously.

**Version 2 — dedicated 5 V buck converter (current design).** The motor is now supplied from its
own TPS5450 buck regulated to 5 V, matching the motor's rating. Duty cycle now controls **speed
only**, which is what PWM is actually for.

**What this bought us:**

| Benefit | Detail |
| --- | --- |
| The motor never sees over-voltage | Not on average, not on peaks, not at stall |
| Full duty range is usable | We regained the 55 % of control range the cap was discarding |
| Our bench measurements became valid | The 140 mA and 13 % figures were taken at 5 V — they now describe the real operating condition instead of needing to be redone |
| Better resolution at low speed | The usable band runs from ~13 % to 100 % instead of ~6 % to 45 % |

**Trade-off accepted:** one more buck converter — more mass, more board area, one more component
that can fail. We judged that acceptable against destroying the motor, especially since the motor
is stock and the chassis cannot easily accept a replacement.

**A new failure mode this introduces — and it is a real one.** A battery and a buck converter
behave very differently under a current surge. A battery **sags**; a buck converter **current-limits,
hiccups, or shuts down**. Our motor stall current is not yet measured, and if it exceeds the
converter's limit, the motor rail will collapse at exactly the moment the car needs torque most —
breakaway from standstill.

Mitigations planned:
- Measure stall current at 5 V and compare against the converter's rated limit `PENDING`
- Bulk capacitance at the TB6612FNG input to supply the surge locally, so the converter sees an
  averaged load rather than the raw transient `PENDING`
- Firmware soft-start: ramp duty from the floor rather than stepping to the target `PENDING`

**Honest note on the driver drop.** The TB6612FNG loses roughly 0.5 V across its output stage.
On a 12 V rail that was 4 % and negligible; on a 5 V rail it is about 10 %, so the motor sees
closer to 4.5 V than 5 V. This slightly reduces top speed. We accept it — the same drop on an
L298N would have been over 2 V, which on a 5 V rail would have been disqualifying for that part.

| Parameter | Value | Status |
| --- | --- | --- |
| Motor rated voltage | 5 V | `DONE` |
| Motor rail | 5 V, dedicated TPS5450 buck from the actuator pack | `DONE` |
| PWM frequency | 1 kHz | `DONE` |
| Duty floor (minimum effective) | ~13 % at 5 V | `DONE` |
| Duty cap | None — the rail sets the voltage. Any cap is now a *speed* choice, not protection | `DONE` |
| Motor stall current at 5 V | `[PENDING]` | `PENDING` |
| Buck converter current limit vs stall current | `[PENDING]` | `PENDING` |
| Motor case temperature after a 3-lap run | `[PENDING]` | `PENDING` |

### Torque and speed reasoning

The vehicle does not need to be fast. It needs to be *controllable*. Constraints that set our
target speed:

- **The 600 mm corridor.** Higher speed means more distance covered before a correction takes
  effect, so achievable steering error grows with speed. The narrow-corridor rounds set the ceiling.
- **Rule 9.18.** In the Open Challenge, touching the outer wall is not permitted at all. Speed that
  produces occasional wall contact is not a minor cost — it is a zero.
- **The parking phase.** Parallel parking has a far tighter geometric tolerance than open-corridor
  driving and requires low speed with repeatable distance control.

Torque demand is dominated by **breakaway from standstill**, which is why the duty floor matters
more to us than peak power.

| Quantity | Value | Status |
| --- | --- | --- |
| Target cruise speed, 1000 mm corridor | `[PENDING]` | `PENDING` |
| Target cruise speed, 600 mm corridor | `[PENDING]` | `PENDING` |
| Target speed, parking manoeuvre | `[PENDING]` | `PENDING` |

### Turning radius measurement procedure `PENDING`

The Brain layer's path planner needs the minimum turning radius **measured at the rear axle
centre**. We will not estimate it from wheelbase and a claimed steering angle — linkage backlash
and real mechanical limits make the theoretical figure unreliable.

Method (requires encoder and IMU working):

1. Command full lock to one side.
2. Drive a slow, steady arc.
3. Record arc length `s` from the encoder and heading change `Δθ` from the IMU.
4. Compute `R = s / Δθ` (radians).
5. Apply a track-width correction — the encoder is on one wheel, not on the centreline.
6. **Repeat for the other lock direction.** The two will differ. Record both.

| Quantity | Value | Status |
| --- | --- | --- |
| Minimum turning radius, left lock | `[PENDING]` | `PENDING` |
| Minimum turning radius, right lock | `[PENDING]` | `PENDING` |
| Turning circle vs 600 mm corridor — does it fit? | `[PENDING]` | `PENDING` |

The last row is a go/no-go check. If the turning circle does not fit inside a 600 mm corridor, the
Open Challenge is not completable and the steering throw or wheelbase must change. This is the
single most important unmeasured number on the vehicle.

---

<!-- END OF PART 1 — Tawassal Zahra (Body / Hardware). Part 2 continues below. -->
