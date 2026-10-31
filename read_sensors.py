import time
import serial

with serial.Serial("COM7", 115200, timeout=1) as arduino:
    time.sleep(2)

    print("Reading sensors. Press Ctrl+C to stop.")

    while True:
        line = arduino.readline().decode("utf-8", errors="replace").strip()

        try:
            temperature, light, sound = map(int, line.split(","))
        except ValueError:
            continue

        darkness = "TOO DARK" if light < 500 else "LIGHT OK"
        sound_state = "SOUND" if sound > 100 else "QUIET"

        print(
            f"Temp raw={temperature} | "
            f"Light={light} ({darkness}) | "
            f"Sound={sound} ({sound_state})"
        )