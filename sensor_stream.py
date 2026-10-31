"""Read serial continuously so Hue requests never queue old motion events."""
import json
import threading
import time

import serial


def parse_sample(line):
    data = json.loads(line)
    for key in ('motion', 'screen_down', 'needs_water', 'watering_simulated'):
        if type(data.get(key)) is not int or data[key] not in (0, 1):
            raise ValueError(f'Invalid {key}')
    for key, maximum in (('soil_raw', 1023), ('soil_percent', 100)):
        if type(data.get(key)) is not int or not 0 <= data[key] <= maximum:
            raise ValueError(f'Invalid {key}')
    return data


class SensorStream:
    def __init__(self, port, policy=None):
        self.port_name = port
        self.policy = policy
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = None

    def __enter__(self):
        self.port = serial.Serial(self.port_name, 115200, timeout=0.2)
        # Opening a serial port can reset an Arduino; discard partial startup bytes.
        self.port.reset_input_buffer()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return self

    def run(self):
        previous_status = None
        while not self.stop.is_set():
            try:
                line = self.port.readline()
                if not line:
                    continue
                sample = parse_sample(line)
            except (ValueError, UnicodeError):
                continue
            except serial.SerialException:
                print('Serieporten ble koblet fra. Koble til og start programmet på nytt.')
                return
            with self.lock:
                if self.policy:
                    self.policy.observe(bool(sample['motion']), bool(sample['screen_down']), time.monotonic())
            status = (sample['needs_water'], sample['watering_simulated'])
            if status != previous_status:
                print(f"Jordfuktighet: {sample['soil_percent']} % (kalibrert anslag). "
                      + ('TRENGER VANN. ' if status[0] else 'Fuktighet OK. ')
                      + ('SIMULERT vanning pågår; ikke ekte vann.' if status[1] else 'Ingen simulering.'))
                previous_status = status

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(timeout=1)
        self.port.close()
