"""Small local SQLite history for plant and room sensor readings."""
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


class SensorHistory:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get(
            'HISTORY_DB_PATH', 'instance/sensor_history.sqlite3'))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.last_saved = 0.0
        self.last_state = None
        self.last_cleanup = 0.0
        with self._connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observed_at TEXT NOT NULL,
                motion INTEGER NOT NULL,
                screen_down INTEGER NOT NULL,
                light_raw INTEGER NOT NULL,
                light_bright INTEGER NOT NULL,
                soil_raw INTEGER NOT NULL,
                soil_percent INTEGER NOT NULL,
                needs_water INTEGER NOT NULL
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_sensor_readings_time '
                       'ON sensor_readings(observed_at)')

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def record(self, sample):
        state = tuple(sample[key] for key in
                      ('motion', 'screen_down', 'light_bright', 'soil_percent', 'needs_water'))
        now = time.time()
        with self.lock:
            if self.last_state == state and now - self.last_saved < 60:
                return
            observed_at = datetime.now(ZoneInfo('Europe/Oslo')).isoformat(timespec='seconds')
            with self._connect() as db:
                db.execute('''INSERT INTO sensor_readings
                    (observed_at, motion, screen_down, light_raw, light_bright,
                     soil_raw, soil_percent, needs_water)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (observed_at, sample['motion'], sample['screen_down'],
                     sample['light_raw'], sample['light_bright'], sample['soil_raw'],
                     sample['soil_percent'], sample['needs_water']))
                if now - self.last_cleanup >= 3600:
                    cutoff = datetime.fromtimestamp(
                        now - 30 * 86400, ZoneInfo('Europe/Oslo')).isoformat()
                    db.execute('DELETE FROM sensor_readings WHERE observed_at < ?', (cutoff,))
                    self.last_cleanup = now
            self.last_saved = now
            self.last_state = state

    def recent(self, limit=48):
        with self.lock, self._connect() as db:
            rows = db.execute('''SELECT observed_at, motion, screen_down, light_raw,
                light_bright, soil_raw, soil_percent, needs_water
                FROM sensor_readings ORDER BY id DESC LIMIT ?''', (limit,)).fetchall()
        return [dict(row) for row in rows]
