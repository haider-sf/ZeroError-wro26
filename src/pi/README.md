# Raspberry Pi 5 vision software

This directory now contains the first submitted Pi 5 application:

- `vision.py` captures 640 × 480 RGB frames from Camera Module 3 Wide at a target 15 FPS.
- It thresholds red and green pillars in HSV, filters candidate blobs by area, frame position and
  aspect ratio, and selects the nearer candidate by apparent height.
- It sends one human-readable UART line per frame to the Pico:
  `colour,x_norm,height_px`.
- If no pillar is detected it sends `N,0.50,0`.

The program is an integration candidate, not a validated competition pipeline. Its HSV gates,
minimum blob area, camera target positions and visual-servo gain are still untuned on the track.
Open/Obstacle strategy, autostart, run logging and a complete Pi state machine are not present.

## Dependencies

The target is Raspberry Pi OS on a Raspberry Pi 5 with Camera Module 3 Wide. The program imports:

- Picamera2
- OpenCV (`cv2`)
- NumPy
- pySerial for normal UART operation

The default serial port is `/dev/ttyAMA0` at 115200 baud. Pi TX/RX must be connected to Pico
GP17/GP16 with a common ground, crossing TX to RX.

## Running

```bash
python3 src/pi/vision.py --debug
python3 src/pi/vision.py
```

Debug mode prints protocol lines and does not require a serial port. Normal mode opens the UART and
continues running the camera if serial setup or writes fail; the Pico is expected to discard stale
camera data after 200 ms.

Stop with `Ctrl+C` so Picamera2 releases the camera cleanly.

## Still required

- Calibrate and record HSV thresholds under track and venue lighting.
- Measure detection range, false-positive rate, frame cadence and Pi-to-Pico latency.
- Verify the UART wiring and protocol on the assembled vehicle.
- Tune the Pico's camera target positions and heading-bias gain.
- Implement the remaining challenge strategy, logging and autostart.
- Disable Wi-Fi and Bluetooth persistently and provide a quick judge-verification procedure for
  Rule 11.10.
