import json
import ssl
import time
from urllib.request import Request, urlopen
import os

from settings import required

from datetime import datetime
from zoneinfo import ZoneInfo
from lighting import LightingPolicy
from sensor_stream import SensorStream

LIGHT_IDS = [int(value) for value in os.environ.get("HUE_LIGHT_IDS", "4,5,6").split(",")]


def set_light(light_id, state):
    url = (
        f"https://{required('HUE_BRIDGE_HOST')}/api/{required('HUE_USERNAME')}"
        f"/lights/{light_id}/state"
    )

    body = json.dumps(state).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )

    with urlopen(
        request,
        context=ssl.create_default_context(cafile=os.environ.get("HUE_CA_FILE")),
        timeout=10,
    ) as response:
        result = json.loads(response.read().decode("utf-8"))

    if any("error" in item for item in result):
        raise RuntimeError(f"Hue svarte med en feil: {result}")


def main():
    for name in ("HUE_BRIDGE_HOST", "HUE_USERNAME"):
        required(name)
    timezone = ZoneInfo(os.environ.get("ROOM_TIMEZONE", "Europe/Oslo"))
    outside = os.environ.get("OUTSIDE_HOURS", "off")
    if outside not in {"keep", "same", "off"}:
        raise ValueError("OUTSIDE_HOURS må være keep, same eller off")
    policy = LightingPolicy(time.monotonic())
    policy.outside_mode = outside
    last_state = None
    last_mode = None
    with SensorStream(os.environ.get("ARDUINO_PORT", "COM7"), policy) as stream:
        print("Lysstyring startet; Ctrl+C stopper. Bare denne prosessen skal åpne serieporten.")
        while True:
            with stream.lock:
                state, mode = policy.desired(datetime.now(timezone), time.monotonic())
            if mode != last_mode:
                print(mode)
                last_mode = mode
            if state is not None and state != last_state:
                try:
                    for light_id in LIGHT_IDS:
                        set_light(light_id, state)
                    last_state = state
                    print(mode)
                except Exception as error:
                    print(f"Hue-feil ({type(error).__name__}); prøver igjen om ett sekund.")
                    time.sleep(1)
            time.sleep(0.1)


if __name__ == "__main__":
    main()
