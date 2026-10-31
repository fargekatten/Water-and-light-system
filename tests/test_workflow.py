from contextlib import redirect_stdout
import io
import json
import os
import unittest
from unittest.mock import patch

import control_hue
import read_thingspeak
import read_sensors
from settings import required


class WorkflowTests(unittest.TestCase):
    def test_missing_and_placeholder_config(self):
        for value in ('', 'YOUR_READ_API_KEY'):
            with patch.dict(os.environ, {'TEST_CONFIG': value}):
                with self.assertRaises(ValueError):
                    required('TEST_CONFIG')

    def test_thingspeak_request_and_sensor_mapping(self):
        payload = {'field1': '12', 'field2': '450', 'field3': '120'}
        with patch.dict(os.environ, {'THINGSPEAK_CHANNEL_ID': '123',
                                    'THINGSPEAK_READ_API_KEY': 'test key&'}):
            with patch('read_thingspeak.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())) as request:
                self.assertEqual(control_hue.get_latest_readings(), (450.0, 120.0))
                self.assertEqual(request.call_args.args[0],
                                 'https://api.thingspeak.com/channels/123/feeds/last.json?api_key=test+key%26')

    def test_all_light_modes_and_sound_priority(self):
        self.assertEqual(control_hue.choose_state(100, 101)[0], {'on': True, 'bri': 127, 'ct': 454})
        self.assertEqual(control_hue.choose_state(100, 100)[0], {'on': True, 'bri': 254, 'ct': 222})
        self.assertEqual(control_hue.choose_state(500, 0)[0], {'on': True, 'bri': 254, 'ct': 454})

    def test_serial_skips_bad_rows_and_parses_csv(self):
        from unittest.mock import MagicMock
        port = MagicMock()
        port.readline.side_effect = [b"bad row\n", b"100,200,300\n", KeyboardInterrupt]
        output = io.StringIO()
        with patch('read_sensors.serial.Serial') as serial_port, patch('read_sensors.time.sleep'):
            serial_port.return_value.__enter__.return_value = port
            with redirect_stdout(output), self.assertRaises(KeyboardInterrupt):
                read_sensors.main()
        self.assertIn('Temp raw=100', output.getvalue())
        self.assertIn('Light=200 (TOO DARK)', output.getvalue())
        self.assertIn('Sound=300 (SOUND)', output.getvalue())

    def test_hue_request_and_api_errors(self):
        with patch.dict(os.environ, {'HUE_BRIDGE_HOST': 'bridge.example', 'HUE_USERNAME': 'test-user'}):
            for response, fails in [([{'success': {'/lights/4/state/on': True}}], False),
                                    ([{'error': {'description': 'unauthorized'}}], True)]:
                with patch('control_hue.urlopen', return_value=io.BytesIO(json.dumps(response).encode())) as call:
                    if fails:
                        with self.assertRaises(RuntimeError):
                            control_hue.set_light(4, {'on': True})
                    else:
                        control_hue.set_light(4, {'on': True})
                    request = call.call_args.args[0]
                    self.assertEqual(request.method, 'PUT')
                    self.assertEqual(json.loads(request.data), {'on': True})
                    self.assertTrue(call.call_args.kwargs['context'].check_hostname)


if __name__ == '__main__':
    unittest.main()
