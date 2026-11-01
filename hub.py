"""Shared local controller for Hue, dashboard, and stored sensor readings."""
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from history_store import SensorHistory
from lighting import LightingPolicy, WHITE, WARM, CINEMA, OFF

PRESETS = {'white': WHITE, 'warm': WARM, 'cinema': CINEMA, 'off': OFF}


class Hub:
    def __init__(self, demo=False, manual_only=False):
        self.lock = threading.RLock()
        self.policy = LightingPolicy(time.monotonic())
        self.demo = demo
        self.manual_only = manual_only
        self.sample = None
        self.override = None
        self.override_until = 0
        self.simulation_until = 0
        self.applied = None
        self.error = None
        self.storage_error = None
        self.history = SensorHistory()

    def observe(self, data, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            self.sample = dict(data)
            self.policy.observe(bool(data['motion']), bool(data['screen_down']),
                                bool(data['light_bright']), now)
            if data['screen_down']:
                self.override = None
            if not self.demo:
                try:
                    self.history.record(data)
                    self.storage_error = None
                except Exception:
                    self.storage_error = 'Lokal sensorhistorikk kunne ikke lagres; sjekk diskplass og filrettigheter.'

    def manual(self, mode, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            if mode == 'auto':
                self.override = None
                return
            if mode not in PRESETS:
                raise ValueError('Ukjent lysmodus')
            if not self.manual_only and (self.policy.last_sample is None or now - self.policy.last_sample > 3):
                raise ValueError('Ferske sensordata kreves før manuell styring')
            if self.policy.screen_down:
                raise ValueError('Lerretet er nede; fysisk kinomodus har prioritet')
            self.override = mode
            self.override_until = now + 15 * 60

    def desired(self, now=None, local_time=None):
        now = time.monotonic() if now is None else now
        local_time = local_time or datetime.now(ZoneInfo('Europe/Oslo'))
        with self.lock:
            if self.override and now >= self.override_until:
                self.override = None
            automatic, mode = self.policy.desired(local_time, now)
            if self.manual_only:
                if self.policy.screen_down:
                    return CINEMA.copy(), 'lerret nede: oransje, 25 %'
                automatic, mode = None, 'manuell modus uten sensorer: beholder gjeldende lys'
            if (automatic is None and not self.manual_only) or self.policy.screen_down:
                return automatic, mode
            if self.override and now < self.override_until:
                return PRESETS[self.override].copy(), 'manuell: ' + self.override
            return automatic, mode

    def status(self):
        now = time.monotonic()
        with self.lock:
            try:
                history = [] if self.demo else self.history.recent(48)
            except Exception:
                history = []
                self.storage_error = 'Lokal sensorhistorikk kunne ikke leses; sjekk filrettigheter.'
            _, mode = self.desired(now)
            return dict(demo=self.demo, manual_only=self.manual_only, mode=mode, sample=self.sample,
                        fresh=self.policy.last_sample is not None and now - self.policy.last_sample <= 3,
                        manual_seconds=max(0, int(self.override_until - now)) if self.override else 0,
                        watering_simulated=now < self.simulation_until,
                        applied=self.applied, error=self.error,
                        storage_error=self.storage_error, history=history)
