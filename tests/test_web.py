import io
import json
import os
import re
import secrets
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash
from hub import Hub
from lighting import CINEMA, WARM
from webapp import create_app

SAMPLE = dict(motion=0, screen_down=0, soil_raw=800, soil_percent=0,
              needs_water=1, watering_simulated=0)


class WebSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = dict(secret_key=secrets.token_urlsafe(48),
                          password_hash=generate_password_hash('test-only-long-password'))

    def setUp(self):
        self.hub = Hub(demo=True)
        self.hub.observe(SAMPLE)
        self.app = create_app(self.hub, self.config)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def token(self):
        with self.client.session_transaction() as session:
            return session['csrf']

    def login(self):
        self.client.get('/login')
        return self.client.post('/login', data={'csrf': self.token(),
                                               'password': 'test-only-long-password'})

    def test_anonymous_cannot_read_or_change(self):
        self.assertEqual(self.client.get('/api/status').status_code, 401)
        self.assertEqual(self.client.post('/mode', data={'mode': 'white'}).status_code, 403)
        self.assertIsNone(self.hub.override)

    def test_csrf_host_and_security_headers(self):
        self.login()
        self.assertEqual(self.client.post('/mode', data={'mode': 'white'}).status_code, 403)
        self.assertEqual(self.client.get('/', base_url='http://evil.example').status_code, 400)
        response = self.client.get('/')
        self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(self.client.get('/mode').status_code, 405)

    def test_login_throttled_and_password_not_leaked(self):
        self.client.get('/login')
        for _ in range(5):
            self.client.post('/login', data={'csrf': self.token(), 'password': 'wrong'})
        response = self.client.post('/login', data={'csrf': self.token(), 'password': 'wrong'})
        self.assertEqual(response.status_code, 429)
        self.assertNotIn(b'scrypt:', response.data)

    def test_manual_control_and_logout(self):
        self.assertEqual(self.login().status_code, 302)
        response = self.client.post('/mode', data={'csrf': self.token(), 'mode': 'warm'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.hub.override, 'warm')
        self.assertEqual(self.client.post('/mode', data={'csrf': self.token(), 'mode': 'arbitrary-url'}).status_code, 400)
        self.client.post('/logout', data={'csrf': self.token()})
        self.assertEqual(self.client.get('/api/status').status_code, 401)

    def test_watering_is_explicit_simulation_not_fake_moisture(self):
        self.login()
        self.client.post('/simulate', data={'csrf': self.token()})
        data = self.client.get('/api/status').json
        self.assertTrue(data['watering_simulated'])
        self.assertEqual(data['sample']['soil_percent'], 0)
        self.assertEqual(data['sample']['needs_water'], 1)


class HubTests(unittest.TestCase):
    def test_screen_cancels_override_and_exit_is_warm(self):
        hub = Hub()
        hub.observe(SAMPLE, now=0)
        hub.manual('white', now=1)
        hub.observe(dict(SAMPLE, screen_down=1), now=2)
        self.assertEqual(hub.desired(2, datetime(2026, 1, 1, 8))[0], CINEMA)
        with self.assertRaises(ValueError):
            hub.manual('white', now=2)
        hub.observe(SAMPLE, now=3)
        self.assertEqual(hub.desired(3, datetime(2026, 1, 1, 8))[0], WARM)

    def test_expired_override_and_stale_data(self):
        hub = Hub()
        hub.observe(SAMPLE, now=0)
        hub.manual('white', now=1)
        self.assertIsNone(hub.desired(10, datetime(2026, 1, 1, 8))[0])
        hub.observe(SAMPLE, now=902)
        self.assertEqual(hub.desired(902, datetime(2026, 1, 1, 8))[0], WARM)
        self.assertIsNone(hub.override)

    def test_cloud_export_contains_soil_only(self):
        from cloud_export import export_loop
        hub = Hub()
        hub.observe(SAMPLE)
        stop = MagicMock()
        stop.wait.side_effect = [False, True]
        with patch.dict(os.environ, {'THINGSPEAK_WRITE_API_KEY': 'test-key'}):
            with patch('cloud_export.urlopen', return_value=io.BytesIO(b'42')) as request:
                export_loop(hub, stop)
                from urllib.parse import parse_qs
                payload = parse_qs(request.call_args.args[0].data.decode())
                self.assertEqual(set(payload), {'api_key', 'field1', 'field2'})
                self.assertEqual(payload['field1'], ['0'])
                self.assertNotIn('motion', payload)

    def test_mqtt_tls_acl_topic_and_retained_handling(self):
        import mqtt_input
        hub = Hub()
        with patch.dict(os.environ, {'MQTT_HOST': 'broker.example', 'MQTT_USERNAME': 'controller-rom101',
                                     'MQTT_PASSWORD': 'test-only', 'MQTT_CA_FILE': '/test/ca.crt'}):
            with patch('mqtt_input.mqtt.Client') as factory:
                client = factory.return_value
                mqtt_input.connect(hub)
                client.tls_set.assert_called_once()
                self.assertTrue(factory.call_args.kwargs['clean_session'])
                good = MagicMock(topic='school/rom101/sensors', retain=False, payload=json.dumps(SAMPLE).encode())
                retained = MagicMock(topic=good.topic, retain=True, payload=good.payload)
                client.on_message(client, None, retained)
                self.assertIsNone(hub.sample)
                wrong = MagicMock(topic='school/other/sensors', retain=False, payload=good.payload)
                client.on_message(client, None, wrong)
                self.assertIsNone(hub.sample)
                client.on_message(client, None, good)
                self.assertEqual(hub.sample, SAMPLE)
                client.on_disconnect(client, None, None, None, None)
                self.assertIsNone(hub.policy.last_sample)


if __name__ == '__main__':
    unittest.main()
