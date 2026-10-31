import io
import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch

import control_hue
from lighting import LightingPolicy, WHITE, WARM, CINEMA
from sensor_stream import parse_sample
from settings import required


class LightingTests(unittest.TestCase):
    def setUp(self):
        self.policy = LightingPolicy(0)
        self.morning = datetime(2026, 10, 31, 8)

    def state(self, t, motion=False, screen=False, hour=8):
        self.policy.observe(motion, screen, t)
        return self.policy.desired(self.morning.replace(hour=hour), t)[0]

    def test_startup_holds_warm_for_30_minutes(self):
        self.assertEqual(self.state(0), WARM)
        self.assertEqual(self.state(1799), WARM)
        self.assertEqual(self.state(1800), WHITE)

    def test_motion_restarts_full_hold(self):
        self.assertEqual(self.state(2000, motion=True), WARM)
        self.assertEqual(self.state(3799), WARM)
        self.assertEqual(self.state(3800), WHITE)

    def test_cinema_immediate_and_exit_always_warm(self):
        self.assertEqual(self.state(2000), WHITE)
        self.assertEqual(self.state(2001, screen=True), CINEMA)
        self.assertEqual(self.state(8000, screen=True), CINEMA)
        self.assertEqual(self.state(8001), WARM)
        self.assertEqual(self.state(9800), WARM)
        self.assertEqual(self.state(9801), WHITE)

    def test_hours_boundaries_and_cinema_override(self):
        self.assertFalse(self.state(2000, hour=6)['on'])
        self.assertEqual(self.state(2000, hour=7), WHITE)
        self.assertEqual(self.state(2000, hour=10), WHITE)
        self.assertFalse(self.state(2000, hour=11)['on'])
        self.assertEqual(self.state(2000, screen=True, hour=23), CINEMA)
        self.assertFalse(self.state(2001, hour=23)['on'])

    def test_morning_ends_even_with_recent_motion(self):
        self.assertEqual(self.state(100, motion=True, hour=10), WARM)
        self.assertFalse(self.state(101, motion=True, hour=11)['on'])

    def test_screen_stays_cinema_across_11(self):
        self.assertEqual(self.state(100, screen=True, hour=10), CINEMA)
        self.assertEqual(self.state(101, screen=True, hour=11), CINEMA)
        self.assertFalse(self.state(102, hour=11)['on'])

    def test_stale_data_never_causes_white(self):
        self.state(2000)
        self.assertIsNone(self.policy.desired(self.morning, 2004)[0])

    def test_outside_options(self):
        self.policy.outside_mode = 'same'
        self.assertEqual(self.state(2000, hour=23), WHITE)
        self.policy.outside_mode = 'off'
        self.assertFalse(self.state(2000, hour=23)['on'])


class IntegrationTests(unittest.TestCase):
    def test_placeholder_config(self):
        for value in ('', 'YOUR_HUE_USERNAME'):
            with patch.dict(os.environ, {'TEST_CONFIG': value}):
                with self.assertRaises(ValueError):
                    required('TEST_CONFIG')

    def test_serial_validation_and_simulation_fields(self):
        data = dict(motion=1, screen_down=0, soil_raw=800, soil_percent=0,
                    needs_water=1, watering_simulated=1)
        self.assertEqual(parse_sample(json.dumps(data)), data)
        for key, value in [('motion', 4), ('soil_percent', 101), ('soil_raw', -1)]:
            with self.assertRaises(ValueError):
                parse_sample(json.dumps(dict(data, **{key: value})))
        with self.assertRaises(ValueError):
            parse_sample('100,200,300')

    def test_hue_request_and_api_errors(self):
        with patch.dict(os.environ, {'HUE_BRIDGE_HOST': 'bridge.example', 'HUE_USERNAME': 'test-user'}):
            for response, fails in [([{'success': {'/lights/4/state/on': True}}], False),
                                    ([{'error': {'description': 'unauthorized'}}], True)]:
                with patch('control_hue.urlopen', return_value=io.BytesIO(json.dumps(response).encode())) as call:
                    if fails:
                        with self.assertRaises(RuntimeError):
                            control_hue.set_light(4, CINEMA)
                    else:
                        control_hue.set_light(4, CINEMA)
                    request = call.call_args.args[0]
                    self.assertEqual(request.method, 'PUT')
                    self.assertEqual(json.loads(request.data), CINEMA)
                    self.assertTrue(call.call_args.kwargs['context'].check_hostname)


if __name__ == '__main__':
    unittest.main()
