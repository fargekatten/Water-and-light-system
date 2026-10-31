"""Lighting decisions independent of hardware and HTTP."""
from datetime import datetime

WHITE = {"on": True, "bri": 254, "ct": 153, "transitiontime": 0}
WARM = {"on": True, "bri": 127, "ct": 454, "transitiontime": 0}
CINEMA = {"on": True, "bri": 64, "xy": [0.55, 0.42], "transitiontime": 0}
HOLD_SECONDS = 30 * 60


class LightingPolicy:
    def __init__(self, now):
        # A restart must not suddenly dazzle people who are sitting still.
        self.last_activity = now
        self.screen_down = False
        self.last_sample = None
        self.outside_mode = "off"

    def observe(self, motion, screen_down, now):
        if motion or (self.screen_down and not screen_down):
            self.last_activity = now
        self.screen_down = screen_down
        self.last_sample = now

    def desired(self, local_time: datetime, now):
        if self.last_sample is None or now - self.last_sample > 3:
            return None, "sensordata mangler; beholder lyset"
        if self.screen_down:
            return CINEMA.copy(), "kino"
        in_hours = 7 <= local_time.hour < 11
        if not in_hours and self.outside_mode != "same":
            if self.outside_mode == "off":
                return {"on": False, "transitiontime": 0}, "av"
            return None, "utenfor 07–11; beholder lyset"
        # Cinema exit starts a new full 30-minute warm-light interval.
        if now - self.last_activity < HOLD_SECONDS:
            return WARM.copy(), "gult, halv styrke"
        return WHITE.copy(), "hvitt, full styrke"
