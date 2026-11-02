"""Priority rules for the Hue lights."""
from datetime import datetime
import os


def cinema_preset():
    state = {"on": True, "bri": 64, "transitiontime": 0}
    value = os.environ.get("HUE_CINEMA_CT", "").strip()
    if not value:
        return dict(state, xy=[0.55, 0.42])
    try:
        temperature = int(value)
    except ValueError:
        raise ValueError("HUE_CINEMA_CT må være et heltall mellom 153 og 500") from None
    if not 153 <= temperature <= 500:
        raise ValueError("HUE_CINEMA_CT må være et heltall mellom 153 og 500")
    return dict(state, ct=temperature)

WHITE = {"on": True, "bri": 254, "ct": 153, "transitiontime": 0}
WARM = {"on": True, "bri": 127, "ct": 454, "transitiontime": 0}
CINEMA = cinema_preset()
CINEMA_DESCRIPTION = "hvitt, 25 %" if "ct" in CINEMA else "oransje, 25 %"
OFF = {"on": False, "transitiontime": 0}
HOLD_SECONDS = 30 * 60
SENSOR_TIMEOUT_SECONDS = 3


class LightingPolicy:
    def __init__(self, now):
        self.last_motion = None
        self.screen_down = False
        self.light_bright = None
        self.last_sample = None

    def observe(self, motion, screen_down, light_bright, now):
        if motion:
            self.last_motion = now
        self.screen_down = screen_down
        self.light_bright = light_bright
        self.last_sample = now

    def desired(self, local_time: datetime, now):
        if self.last_sample is None or now - self.last_sample > SENSOR_TIMEOUT_SECONDS:
            return None, "sensordata mangler; beholder gjeldende lys"
        if self.screen_down:
            return CINEMA.copy(), "lerret nede: " + CINEMA_DESCRIPTION
        if self.last_motion is not None and now - self.last_motion < HOLD_SECONDS:
            return WARM.copy(), "bevegelse: gult, 50 %"
        if not 7 <= local_time.hour < 23:
            return OFF.copy(), "utenfor 07–23: av"
        if self.light_bright:
            return OFF.copy(), "nok dagslys: av"
        return WHITE.copy(), "mørkt innenfor 07–23: hvitt, 100 %"
