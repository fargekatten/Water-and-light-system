import json
import ssl
import time
from urllib.request import Request, urlopen
import os

from settings import required
from read_thingspeak import get_latest_reading

# Fyll inn verdiene dine. Ikke del API-nøklene eller Hue-brukernavnet.


SOUND_THRESHOLD = int(os.environ.get("SOUND_THRESHOLD", "100"))
DARK_THRESHOLD = 500
LIGHT_IDS = [4, 5, 6]  # Spilevegg 3, 2 og 1
POLL_SECONDS = 20

def get_latest_readings():
    data = get_latest_reading()
    return float(data["field2"]), float(data["field3"])


def choose_state(light, sound):
    if sound > SOUND_THRESHOLD:
        return {"on": True, "bri": 127, "ct": 454}, "gult, halv styrke"
    if light < DARK_THRESHOLD:
        return {"on": True, "bri": 254, "ct": 222}, "hvitt, full styrke"
    return {"on": True, "bri": 254, "ct": 454}, "gult, full styrke"


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
    for name in ("THINGSPEAK_CHANNEL_ID", "THINGSPEAK_READ_API_KEY",
                 "HUE_BRIDGE_HOST", "HUE_USERNAME"):
        required(name)
    print("Leser lys og lyd fra ThingSpeak. Trykk Ctrl+C for å stoppe.")
    last_state = None
    while True:
        try:
            light, sound = get_latest_readings()
            state, mode = choose_state(light, sound)
            print(f"Lys: {light:g} | Lyd: {sound:g} | Modus: {mode}")
            if state != last_state:
                for light_id in LIGHT_IDS:
                    set_light(light_id, state)
                last_state = state
        except Exception as error:
            # Exception strings from HTTP clients can contain credential-bearing URLs.
            print(f"Forespørselen mislyktes ({type(error).__name__}); sjekk nettverk og konfigurasjon.")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
