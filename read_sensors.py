"""Show soil warnings/simulation without controlling Hue."""
import os
import time
from sensor_stream import SensorStream


def main():
    with SensorStream(os.environ.get('ARDUINO_PORT', 'COM7')):
        while True:
            time.sleep(1)


if __name__ == '__main__':
    main()
