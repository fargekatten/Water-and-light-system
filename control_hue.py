import json
import ssl
import time
from urllib.request import Request, urlopen

# Fyll inn verdiene dine. Ikke del API-nøklene eller Hue-brukernavnet.


SOUND_THRESHOLD = 00
DARK_THRESHOLD = 500
LIGHT_IDS = [4, 5, 6]  # Spilevegg 3, 2 og 1
POLL_SECONDS = 20

# Hue Bridge kan ha et lokalt HTTPS-sertifikat Python ikke kjenner igjen.
# Dette brukes bare for forbindelsen til Hue Bridge på hjemmenettverket.
HUE_SSL_CONTEXT = ssl._create_unverified_context()



def get_latest_readings():
    url = (
        f"https://api.thingspeak.com/channels/{CHANNEL_ID}"
        f"/feeds/last.json?api_key={READ_API_KEY}"
    )

    with urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    light = float(data["field2"])
    sound = float(data["field3"])
    return light, sound


def set_light(light_id, state):
    url = (
        f"https://{BRIDGE_IP}/api/{HUE_USERNAME}"
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
        context=HUE_SSL_CONTEXT,
        timeout=10,
    ) as response:
        result = json.loads(response.read().decode("utf-8"))

    if any("error" in item for item in result):
        raise RuntimeError(f"Hue svarte med en feil: {result}")


print("Leser lys og lyd fra ThingSpeak. Trykk Ctrl+C for å stoppe.")

last_state = None

while True:
    try:
        light, sound = get_latest_readings()

        if sound > SOUND_THRESHOLD:
            state = {"on": True, "bri": 127, "ct": 454}
            mode = "gult, halv styrke"
        elif light < DARK_THRESHOLD:
            state = {"on": True, "bri": 254, "ct": 222}
            mode = "hvitt, full styrke"
        else:
            state = {"on": True, "bri": 254, "ct": 454}
            mode = "gult, full styrke"

        print(f"Lys: {light:g} | Lyd: {sound:g} | Modus: {mode}")

        if state != last_state:
            for light_id in LIGHT_IDS:
                set_light(light_id, state)
                print(f"Lys {light_id} oppdatert")

            last_state = state

    except Exception as error:
        print(f"Feil: {error}")

    time.sleep(POLL_SECONDS)