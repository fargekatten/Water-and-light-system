"""Verify real startup configuration reaches manual, sensor and Hue paths."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = '''
import io
import json
from datetime import datetime
from unittest.mock import patch
from hub import Hub
from lighting import LightingPolicy
from control_hue import set_light

hub = Hub(demo=True, manual_only=True)
hub.manual("cinema", now=0)
manual = hub.desired(now=1)[0]
hub.policy.screen_down = True
screen, description = hub.desired(now=1)
try:
    hub.manual("off", now=1)
except ValueError:
    rejected = True
else:
    rejected = False
policy = LightingPolicy(0)
policy.observe(False, True, False, 0)
automatic = policy.desired(datetime(2026, 1, 1, 8), 1)[0]
with patch("control_hue.urlopen", return_value=io.BytesIO(b'[{"success":{}}]')) as send:
    set_light(4, manual)
    payload = json.loads(send.call_args.args[0].data)
    verified = send.call_args.kwargs["context"].check_hostname
print(json.dumps(dict(manual=manual, screen=screen, automatic=automatic,
                     description=description, rejected=rejected,
                     payload=payload, verified=verified)))
'''


class HueProfileTests(unittest.TestCase):
    def run_configured(self, value, script=SCRIPT):
        env = dict(os.environ, HUE_BRIDGE_HOST='bridge.example', HUE_USERNAME='test-only')
        env.pop('HUE_CA_FILE', None)
        env.pop('HUE_CINEMA_CT', None)
        if value is not None:
            env['HUE_CINEMA_CT'] = value
        with tempfile.TemporaryDirectory() as directory:
            env['HISTORY_DB_PATH'] = str(Path(directory) / 'history.sqlite3')
            return subprocess.run([sys.executable, '-c', script], env=env,
                                  cwd=Path(__file__).resolve().parents[1],
                                  capture_output=True, text=True)

    def test_temperature_only_lights_receive_no_xy_in_all_cinema_paths(self):
        result = self.run_configured('454')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        expected = dict(on=True, bri=64, ct=454, transitiontime=0)
        for key in ('manual', 'screen', 'automatic', 'payload'):
            self.assertEqual(data[key], expected)
        self.assertTrue(data['rejected'])
        self.assertTrue(data['verified'])
        self.assertIn('hvitt', data['description'])

    def test_color_lights_keep_orange_cinema_by_default(self):
        result = self.run_configured(None)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        expected = dict(on=True, bri=64, xy=[0.55, 0.42], transitiontime=0)
        for key in ('manual', 'screen', 'automatic', 'payload'):
            self.assertEqual(data[key], expected)
        self.assertTrue(data['rejected'])
        self.assertIn('oransje', data['description'])

    def test_invalid_temperature_stops_startup(self):
        for value in ('abc', '152', '501'):
            with self.subTest(value=value):
                result = self.run_configured(value, script='import lighting')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('HUE_CINEMA_CT', result.stderr)


if __name__ == '__main__':
    unittest.main()
