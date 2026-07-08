# SECTION 1 — Project Zero Error
We are Team Zero Error, a team of three students from St. Francis Schools and Colleges in Sara-i-alamgir, Pakistan, competing in the WRO 2026 Future Engineers category. For this challenge, we developed an autonomous 1:16 scale self-driving car that independently navigates a three-lap track, avoids obstacles, and parks itself without any remote control. 

# Section 2 — The Challenge
**Competition Overview**

The World Robot Olympiad (WRO) Future Engineers category is an advanced robotics competition focused on the design and implementation of autonomous, self-driving cars. The challenge requires engineering a scale vehicle capable of navigating complex, dynamic environments using real-time sensor data, computer vision, and advanced steering algorithms without any human intervention.
**Challenge Architecture**

The competition is divided strictly into two distinct challenges, each with a maximum time limit of 3 minutes. Note: Parking is integrated into the second challenge rather than existing as a standalone event.
1. Open Challenge: The vehicle must autonomously complete 3 full laps on a walled track. The robot must identify the correct driving direction, maintain lane control, and successfully bring itself to a complete stop upon crossing the finish line after the final lap.
 2.  Obstacle Challenge: This phase increases complexity by adding traffic obstacles. The vehicle must complete 3 laps while dynamically navigating around red and green pillars. The routing logic must strictly follow the traffic rules:

   - Red Pillars: Must be passed on the right.
   - Green Pillars: Must be passed on the left.
 
3. Upon completing the final lap, the vehicle must locate a designated magenta parking lot and execute a precise parallel parking maneuver.
**Field Specifications**
The physical environment consists of a 3.2 m × 3.2 m mat featuring an inner 3 m × 3 m racetrack. The track boundaries are defined by 100 mm high walls. The primary driving corridors are 1000 mm wide, though certain specialized sections of the Open Challenge may narrow down to 600 mm, demanding highly responsive steering adjustments.
**Scoring Breakdown**
The total evaluation comprises a maximum of 122 points, distributed across the following core metrics:

| Assessment Area | Maximum Points |
| --- | --- |
| Open Challenge | 30 Points |
| Obstacle Challenge | 62 Points |
| Technical Documentation | 30 Points |
| **Total** | **122 Points** |

# SECTION 3 — The Team
**Student Biographies**
- Abiha Zainab
   - Assigned Role: *Software* 
   - Role Description: : Responsible for architecting the vehicle's autonomous navigation logic and decision-making frameworks. Implements robust finite state machines (FSM) to handle dynamic real-time track environments, integrates sensor fusion algorithms, and optimizes steering control feedback loops for precise lane-keeping and obstacle avoidance.
   - Technical Interest: Focused on advanced software development, control algorithms, and optimizing system logic.

- Tawassal Zahra
   - Assigned Layer: *Hardware*
   - Role Description: Responsible for the physical chassis assembly, structural integrity, and mechanical integration of the vehicle. Manages the layout and secure mounting of the microcontroller, drive motors, steering servos, and power distribution systems, ensuring a robust and reliable hardware platform for autonomous testing.
   - Technical Interest:Interested in exploring mechanical engineering principles, chassis dynamics, and robust hardware design.
 
     
- Marva Irfan
   - Assigned Layer: *Documentation*
   - Role Description:Responsible for authoring the comprehensive technical documentation and managing data-logging protocols. Oversees the integration of environmental perception records—tracking data inputs from ToF sensors, IMUs, and encoder odometry—ensuring a well-documented and clear architectural record of the vehicle's design and testing performance. 
   - Technical Interest:Aiming to deepen understanding of engineering documentation standards, sensor data log analysis, and physical hardware deployment structures.
     
Coaching & Guidance

 **Haider Abbas** provides organizational oversight and strategic guidance as the team coach. His role encompasses administrative facilitation and milestone tracking, ensuring that the student engineering team retains complete autonomy over both hardware fabrication and codebase execution. 

 

# SECTION 4 — Our Vehicle

This section covers the physical setup and the computer setup of our autonomous car.
a) **Chassis**
The foundation of our autonomous vehicle relies on a carefully selected mechanical platform that balances scale, maneuverability, and reliability.
**Mechanical Specifications**
Scale and Configuration: The vehicle is built upon a 1:16 scale, two-wheel drive (2WD) remote-controlled (RC) car chassis.

**Drivetrain and Steering:** 
 It utilizes a rear-wheel drive setup for propulsion, combined with a front-wheel steering mechanism. This classic layout closely mirrors the dynamics of full-sized consumer vehicles, providing an ideal testing ground for standard autonomous navigation and steering control algorithms.

**Sourcing and Redundancy Strategy**
**Local Sourcing:**
 The chassis was procured from local suppliers, ensuring that replacement parts or hardware adjustments can be managed quickly without long shipping delays.

**Hardware Redundancy:**
 To safeguard against hardware failures, accidents, or wear-and-tear during testing, an identical second chassis is kept completely untouched as a backup. This guarantees minimal downtime for the project, as any mechanical failure can be resolved by immediately swapping parts or transitioning components to the identical backup frame.





b) **Compute Architecture**
We split the processing power into a two-layer compute architecture to handle high-level logic and low-level physical control separately.
- **Raspberry Pi 5 (The Brain):** Runs Linux and handles high-level intelligence. It manages the vehicle's state machine, processes camera vision data for navigation, calculates complex driving decisions, and directly interfaces with the Inertial Measurement Unit (IMU) to track heading orientation


- **Raspberry Pi Pico (The Body):** Acts as a dedicated real-time controller in constant serial communication with the Pi 5. It executes time-critical physical tasks, including PWM control for steering and drive motors, polling Time-of-Flight (ToF) sensors for wall distances, and tracking wheel encoder pulses via hardware interrupts.
**Why two layers?**
   A standard Linux board like the Pi 5 is great for heavy thinking, but it operates on a "best-effort" time schedule. Because the operating system is constantly juggling background tasks, it can't guarantee the exact, microsecond timing needed for smooth, stable motor control. If the Pi 5 gets bogged down processing a camera frame, a slight delay in updating the motor speed could cause the car to stutter or overshoot a turn. The Pico fixes this by bringing deterministic, real-time control to the table. It runs a single, dedicated loop that executes instructions instantly and predictably every single time. This division of labor ensures the car's physical reactions are perfectly timed, while the Pi 5 is left free to focus entirely on the big picture without breaking a sweat. 

c) **Steering** 
Getting the steering right was our toughest mechanical hurdle. We had to completely re-engineer the stock setup to get the precision an autonomous car needs.

- **The Upgrade:** The chassis originally came with a basic DC-motor-driven geared steering system, which lacked precision. We converted this to servo-controlled steering to achieve precise, repeatable angle control. We mounted an upright servo right into the old motor pocket so its horn rotates horizontally.
  
- **Smart Mechanical Design:** The original steering yoke stays on its original pivot post. This is crucial because the post takes all the physical side-loads from the wheels, meaning the servo only has to supply the pure rotating force (torque).
  
- **The Bicycle Spoke Hack:** To link them, a bicycle spoke drops down from a slot in the servo horn to the steering yoke. The clever bit here is the slot—it absorbs the physical "arc mismatch" between the servo's rotation and the yoke's movement, keeping the steering from binding up at sharp angles.
  
- **Why We Built It This Way:** We explicitly avoided making the servo shaft the actual pivot point. If we had, all the bumps and side-shocks from driving would have slammed right into the servo's internal gears and stripped them. Keeping the pivot and the drive mechanism separate protects our hardware.

- **Software Safeguards:** To add an extra layer of safety, we programmed steering limits (end-stops) directly into the software. This ensures the servo can never be accidentally driven past its safe physical range.
**d) Drive** 
The drivetrain focuses on efficient power management and protecting the physical hardware while maximizing performance.
- **The Motor Setup:** We kept the stock small brushed DC motor, which drives the rear axle through the vehicle's built-in toy gearbox.
- **Why the Stock Motor?** We chose to stay with the original stock motor because modifying the chassis to fit a larger or different motor wasn't feasible without compromising the structural integrity of the vehicle. Keeping it stock preserves the chassis strength.
- **Control Method:** The motor is controlled by a TB6612FNG motor driver using Pulse Width Modulation (PWM) signals sent from our controller.
- **Smart Power Management (The PWM Cap):** Our main power rail sits at $11.1\text{ V}$, but the stock motor is a toy component designed for much lower voltages. To prevent frying it, we cap the PWM duty cycle in software to around 45% (0.45). This keeps the average voltage delivered to the motor at a safe ~5 V (approximately 5 Volts) . The beauty of this setup is that the high 11.1 Volts rail gives us plenty of instant torque headroom for acceleration, while the software cap safely protects the motor from burning out.
- **Why the TB6612FNG over the L298N?** We chose the TB6612FNG driver specifically for its efficiency. It uses modern MOSFET transistors, which have a tiny voltage drop and generate very little heat, allowing it to run beautifully without a bulky heatsink. In contrast, the older L298N driver relies on wasteful BJT transistors that drop significant voltage (stealing power from the motor) and get so hot they require a massive, heavy heatsink.

**e) Power**
A stable power delivery system is critical for an autonomous vehicle. We designed a dual-rail power distribution setup to ensure both the heavy compute boards and the high-draw motors get exactly what they need without interfering with each other.
- **Battery Specifications:** The vehicle runs on two 3S LiPo batteries (11.1 V , 3200mAh), which were sourced locally.
- **The Dual-Rail Layout:** We split our power architecture into two separate paths tied together with a common ground:
   - **Rail 1 (Compute & Logic):** Battery 1 feeds into a TPS5450 buck converter, stepping the voltage down to a stable 5V to power the Raspberry Pi 5, Raspberry Pi Pico, sensors, and steering servo.
   - **Rail 2 (Drivetrain):** Battery 2 connects directly to the motor driver at a raw 11.1 V to drive the rear DC motor.
- **Why Use a Dual-Rail System?** Electric motors create massive electrical noise and sudden current spikes when they start up or change direction. If the entire car shared one battery, these spikes could cause the voltage dropping to the Pi 5 to dip momentarily. By completely isolating the motor power from the logic power, the Pi 5 gets a stable, "stiff” 5V supply and is protected from brownouts or unexpected crashes.
- **Why 3S LiPo? (Rejected Alternatives):** We carefully weighed our battery choices before settling on a 3S setup:
   - **Rejected Power Banks:** A standard USB power bank provides a "soft" 5V that can't handle the sudden, spiky power demands of a Raspberry Pi 5 under heavy computational load.
   - **Rejected 4S/Camera Batteries:** A 4S pack provides too much voltage for our primary motor driver and adds unnecessary weight. However, we do keep a high-power BTS7960 motor driver in reserve as a measured contingency plan if we ever need to step up to a 4S system in the future.
- **Maintenance:** To maintain battery health and ensure safe operation, the LiPo packs are charged using a professional SkyRC iMax B6 balance charger.

**f) Sensors** 

To safely navigate and track its own movement, the vehicle relies on an array of spatial and positional sensors that feed data directly back to the compute layer. 

**VL53L0X Time-of-Flight (ToF) Sensors:** We integrated these laser-ranging sensors on both the front and rear of the vehicle. The front sensor constantly measures the precise distance to oncoming walls or obstacles, while the rear sensor serves as a critical parking and reversing failsafe. 
**BNO055 Inertial Measurement Unit (IMU):** This sensor provides real-time data on the vehicle's heading and orientation. It is the key component for tracking which direction the car is facing and detecting changes in its trajectory. 

**Optical Wheel Encoder:** Built using a slotted IR sensor paired with an axle disc, this encoder tracks the rotations of the drive wheels to calculate the exact physical distance the vehicle has traveled.

**The Camera :** The vehicle includes a Raspberry Pi camera as a perception sensor, intended to handle the colour-based parts of the Obstacle Challenge that distance sensors alone cannot.

**Pillar colour detection:** In the Obstacle Challenge, the car must pass red pillars on their right and green pillars on their left. Distance sensors can detect that an obstacle is present, but they cannot tell red from green — and the correct passing side depends entirely on the colour. The camera's primary job is to identify each pillar's colour as the car approaches, so the decision layer can choose the correct side to pass. The camera feed is processed to isolate the red and green colour ranges (the rules specify red as RGB 238,39,55 and green as RGB 68,214,44), locate the pillar in the frame, and report its colour and rough position to the Brain layer.

**Lane / boundary line reading:** The mat has orange and blue boundary lines marking the section divisions. The camera can detect these line crossings, providing a reference for lap counting and for knowing which section of the track the car is in.

# SECTION 5 — How It Works (three-layer architecture)

**How It Works — Three-Layer Architecture**
Our car is organised into three layers, and each member of the team owns one. Splitting the system this way lets each of us become the expert on our part, keeps the parts testable on their own, and makes the whole system easier to understand and debug. We call the three layers the Senses, the Brain, and the Body — by analogy with how a person navigates: you sense the world around you, your brain decides what to do, and your body carries it out.

- **The Senses layer** is responsible for measuring the world around the car. It gathers the raw information the car needs to navigate: how far away the walls are, which direction the car is facing, and how far it has travelled. Distance to the walls comes from time-of-flight sensors that measure how far the car is from the track borders. Heading and orientation come from an IMU (inertial measurement unit), which tells the car which way it is pointing. A wheel encoder tracks how far the car has driven. If the camera is used, it also belongs to this layer, adding the ability to see colour — distinguishing the red and green obstacle pillars and reading the lines on the mat. The Senses layer's job is to turn all of this into clean, usable information and pass it on.

- **The Brain layer** is where decisions are made. It takes the information from the Senses layer and works out what the car should do next: stay centred in the corridor, recognise that a corner is coming and turn, count how many laps have been completed, decide which side to pass an obstacle pillar (red on the right, green on the left), and run the parking manoeuvre at the end. The Brain is built as a state machine — the car is always in one defined state (for example, "following the corridor" or "turning a corner" or "parking"), and it moves between states based on what the sensors report. We kept this design modular so that a new behaviour can be added as a new state without rewriting everything — which is important because the competition includes a surprise rule we cannot plan for in advance.

- **The Body layer** carries out the decisions. It controls the physical movement of the car: setting the steering servo to the angle the Brain asked for, and driving the motor at the requested speed. It works within safe limits built into its code — the steering never exceeds the mechanical end-stops, and the motor speed is capped so the car stays controllable. The Body layer also reports back what it is doing, so the rest of the system knows the car's actual state.
**How the layers work together.** The three layers form a continuous loop that runs throughout each round:

*Senses measure → Brain decides → Body acts → (repeat).*

The Senses report what the car can detect, the Brain decides what to do about it, and the Body makes it happen — then the cycle repeats many times per second. Because the layers communicate through clear, simple hand-offs (the Senses give readings, the Brain gives commands), each can be developed and tested separately and then connected together. This separation is also how we divide the work as a team: each of us builds and owns one layer, and we agree on how the layers talk to each other so our parts fit together.

# SECTION 6 — Repository Map

**src/** – Contains the codebase, split into pico/ for low-level vehicle firmware and pi/ for high-level computing and vision software.

**schemes/** – Contains the electrical wiring and power distribution diagrams for the vehicle's hardware components.
models/ – Stores the 3D-printing and laser-cutting design files used to fabricate the physical chassis.

**t-photos/** – Features a collection of official and casual photographs documenting our team throughout the project.
# Project Team Photos:
   ## Our Team Members:
   <img width="250"  alt="image" src="https://github.com/user-attachments/assets/96e58d9f-c717-41da-b9e8-fdeeb896548c" />
     <br>
     <br>
   <img width="250"  alt="image" src="https://github.com/user-attachments/assets/c9df0817-d718-4fe2-9a3a-0ed28814bbd9" />

   <br>
    <br>
   <img width="250"  alt="image" src="https://github.com/user-attachments/assets/1adec247-04cc-4810-a3d7-a5084946ddcb" />



**v-photos/** – Includes six mandatory technical photographs showcasing the vehicle from every required angle.

**video/** – Contains the video.md file with YouTube links demonstrating our autonomous runs for the competition challenges.

**other/** – Houses auxiliary reference materials, including component datasheets, communication protocols, and software setup guides.





