import io
import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch

from lighting import LightingPolicy, WHITE, WARM, CINEMA, OFF
from sensor_stream import parse_sample
from settings import required


class LightingTests(unittest.TestCase):
    def setUp(self):
        self.policy = LightingPolicy(0)
        self.day = datetime(2026, 10, 31, 8)

    def state(self, t, motion=False, screen=False, hour=8, bright=False):
        self.policy.observe(motion, screen, bright, t)
        return self.policy.desired(self.day.replace(hour=hour), t)[0]

    def test_dark_during_day_is_white_and_bright_day_is_off(self):
        self.assertEqual(self.state(0), WHITE)
        self.assertFalse(self.state(1, bright=True)['on'])

    def test_motion_stays_warm_for_30_minutes_then_returns_to_daylight_rule(self):
        self.assertEqual(self.state(100, motion=True, bright=True), WARM)
        self.assertEqual(self.state(1899, bright=True), WARM)
        self.assertFalse(self.state(1900, bright=True)['on'])
        self.assertEqual(self.state(2000, motion=True, hour=23), WARM)
        self.assertEqual(self.state(3799, hour=8), WARM)
        self.assertEqual(self.state(3800, hour=8), WHITE)

    def test_screen_has_priority_and_raising_it_returns_to_normal_rule(self):
        self.assertEqual(self.state(1, screen=True, hour=23, bright=True), CINEMA)
        self.assertEqual(self.state(2, hour=23, bright=True), OFF)
        self.assertEqual(self.state(3, screen=True, motion=True), CINEMA)

    def test_schedule_boundaries_and_daylight(self):
        self.assertFalse(self.state(0, hour=6)['on'])
        self.assertEqual(self.state(1, hour=7), WHITE)
        self.assertFalse(self.state(2, hour=7, bright=True)['on'])
        self.assertEqual(self.state(3, hour=22), WHITE)
        self.assertFalse(self.state(4, hour=23)['on'])

    def test_stale_data_does_not_choose_a_new_light_state(self):
        self.state(0)
        self.assertIsNone(self.policy.desired(self.day, 4)[0])


class IntegrationTests(unittest.TestCase):
    def test_placeholder_config(self):
        for value in ('', 'YOUR_HUE_USERNAME'):
            with patch.dict(os.environ, {'TEST_CONFIG': value}):
                with self.assertRaises(ValueError):
                    required('TEST_CONFIG')

    def test_sensor_sample_validation(self):
        data = dict(motion=1, screen_down=0, light_raw=400, light_bright=0,
                    soil_raw=800, soil_percent=0, needs_water=1, watering_simulated=1)
        self.assertEqual(parse_sample(json.dumps(data)), data)
        for key, value in [('motion', 4), ('light_raw', 1024),
                           ('light_bright', 2), ('soil_percent', 101), ('soil_raw', -1)]:
            with self.assertRaises(ValueError):
                parse_sample(json.dumps(dict(data, **{key: value})))
        with self.assertRaises(ValueError):
            parse_sample('100,200,300')


if __name__ == '__main__':
    unittest.main()
