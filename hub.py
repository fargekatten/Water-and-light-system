"""Shared local controller. Network callbacks never talk directly to Hue."""
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from lighting import LightingPolicy, WHITE, WARM, CINEMA

PRESETS = {'white': WHITE, 'warm': WARM, 'cinema': CINEMA,
           'off': {'on': False, 'transitiontime': 0}}


class Hub:
    def __init__(self, demo=False):
        self.lock = threading.RLock()
        self.policy = LightingPolicy(time.monotonic())
        self.demo = demo
        self.sample = None
        self.override = None
        self.override_until = 0
        self.simulation_until = 0
        self.applied = None
        self.error = None

    def observe(self, data, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            if self.policy.last_sample is None or now-self.policy.last_sample > 3:
                self.policy.last_activity = now
            # Physical screen always cancels manual mode, including after raising it.
            if data['screen_down'] or self.policy.screen_down:
                self.override = None
            self.sample = dict(data)
            self.policy.observe(bool(data['motion']), bool(data['screen_down']), now)

    def manual(self, mode, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            if mode == 'auto':
                self.override = None
                # Resume conservatively rather than flashing white after manual mode.
                self.policy.last_activity = now
                return
            if mode not in PRESETS:
                raise ValueError('Ukjent lysmodus')
            if self.policy.last_sample is None or now-self.policy.last_sample > 3:
                raise ValueError('Ferske sensordata kreves før manuell styring')
            if self.policy.screen_down:
                raise ValueError('Lerretet er nede; fysisk kinomodus har prioritet')
            self.override = mode
            self.override_until = now + 15*60

    def desired(self, now=None, local_time=None):
        now = time.monotonic() if now is None else now
        local_time = local_time or datetime.now(ZoneInfo('Europe/Oslo'))
        with self.lock:
            automatic, mode = self.policy.desired(local_time, now)
            if automatic is None or self.policy.screen_down:
                return automatic, mode
            if self.override and now < self.override_until:
                return PRESETS[self.override].copy(), 'manuell: ' + self.override
            if self.override:
                self.override = None
                self.policy.last_activity = now
                return self.policy.desired(local_time, now)
            return automatic, mode

    def status(self):
        now = time.monotonic()
        with self.lock:
            _, mode = self.desired(now)
            return dict(demo=self.demo, mode=mode, sample=self.sample,
                        fresh=self.policy.last_sample is not None and now-self.policy.last_sample <= 3,
                        manual_seconds=max(0, int(self.override_until-now)) if self.override else 0,
                        watering_simulated=now < self.simulation_until,
                        applied=self.applied, error=self.error)
