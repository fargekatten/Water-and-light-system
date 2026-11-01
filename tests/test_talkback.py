import io
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from hub import Hub
from lighting import WHITE, WARM, CINEMA, OFF
from manual_demo import command
from talkback import TalkBack, poll_loop
from webapp import run_controller, create_app


class TalkBackTests(unittest.TestCase):
    def setUp(self):
        self.hub = Hub(demo=True, manual_only=True)
        self.clock = Mock(return_value=1000)
        self.consumer = TalkBack(self.hub, '12', 'test-only-key', self.clock)
        self.clock.return_value = 1010

    def payload(self, mode='WHITE', identifier=1, created=1005):
        return dict(id=identifier, command_string=mode,
                    created_at=datetime.fromtimestamp(created, timezone.utc).isoformat())

    def test_commands_auto_expiry_and_no_sensors(self):
        for index, (mode, state) in enumerate(
                [('WHITE', WHITE), ('WARM', WARM), ('CINEMA', CINEMA), ('OFF', OFF)], 1):
            self.assertTrue(self.consumer.accept(self.payload(mode, index)))
            self.assertEqual(self.hub.desired()[0], state)
        self.assertTrue(self.consumer.accept(self.payload('AUTO', 5)))
        self.assertIsNone(self.hub.override)
        self.assertIsNone(self.hub.desired()[0])
        self.hub.manual('warm', now=0)
        self.assertEqual(self.hub.desired(now=899)[0], WARM)
        self.assertIsNone(self.hub.desired(now=900)[0])
        self.assertIsNone(self.hub.override)

    def test_screen_priority_cancels_and_never_resumes_override(self):
        self.consumer.accept(self.payload())
        command(self.hub, 'SCREEN DOWN')
        self.assertFalse(self.consumer.accept(self.payload('OFF', 2)))
        self.assertEqual(self.hub.desired()[0], CINEMA)
        self.assertTrue(self.consumer.accept(self.payload('AUTO', 3)))
        self.assertEqual(self.hub.desired()[0], CINEMA)
        command(self.hub, 'SCREEN UP')
        self.assertIsNone(self.hub.desired()[0])

    def test_normal_mode_requires_fresh_sensors(self):
        hub = Hub(demo=True)
        consumer = TalkBack(hub, '12', 'test', self.clock)
        self.assertFalse(consumer.accept(self.payload(created=1010)))
        hub.observe(dict(motion=0, screen_down=0, light_bright=0))
        self.assertTrue(consumer.accept(self.payload(identifier=2, created=1010)))
        self.assertEqual(hub.desired()[0], WHITE)
        hub.policy.last_sample -= 4
        self.assertIsNone(hub.desired()[0])
        self.assertIsNone(hub.desired(now=hub.override_until)[0])
        self.assertIsNone(hub.override)

    def test_reject_old_prestartup_future_duplicate_and_out_of_order(self):
        for created in (999, 1011):
            self.assertFalse(self.consumer.accept(self.payload(created=created)))
            self.assertIsNone(self.hub.override)
            self.consumer.last_id = 0
        self.clock.return_value = 1200
        self.assertFalse(self.consumer.accept(self.payload(created=1005)))
        self.clock.return_value = 1010
        self.assertTrue(self.consumer.accept(self.payload(identifier=3)))
        self.assertFalse(self.consumer.accept(self.payload('OFF', 3)))
        self.assertFalse(self.consumer.accept(self.payload('OFF', 2)))
        self.assertEqual(self.hub.desired()[0], WHITE)
        restarted = TalkBack(self.hub, '12', 'test', self.clock)
        self.assertFalse(restarted.accept(self.payload(identifier=4)))

    def test_malformed_and_unknown_inputs(self):
        for payload in (None, [], {}, dict(id=True), self.payload('white'),
                        self.payload('WHITE;OFF'), dict(self.payload(), created_at='2026-01-01'),
                        dict(self.payload(), created_at=None)):
            with self.subTest(payload=payload):
                self.consumer.last_id = 0
                self.assertFalse(self.consumer.accept(payload))
        self.assertIsNone(self.hub.override)
        with self.assertRaises(ValueError):
            TalkBack(self.hub, '../evil', 'test')

    def test_https_post_timeout_and_empty_queue(self):
        with patch('talkback.urlopen', return_value=io.BytesIO(json.dumps(self.payload()).encode())) as call:
            self.assertTrue(self.consumer.poll())
            request = call.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.thingspeak.com/talkbacks/12/commands/execute.json')
            self.assertEqual(request.method, 'POST')
            self.assertEqual(request.data, b'api_key=test-only-key')
            self.assertEqual(call.call_args.kwargs['timeout'], 5)
        for body in (b'', b'0', b'{}'):
            with patch('talkback.urlopen', return_value=io.BytesIO(body)):
                self.assertFalse(self.consumer.poll())
        with patch('talkback.urlopen', return_value=io.BytesIO(b'x' * 16385)):
            with self.assertRaises(ValueError):
                self.consumer.poll()

    def test_network_failure_does_not_change_lights_or_leak_key(self):
        self.hub.manual('warm')
        stop = Mock()
        stop.is_set.return_value = False
        stop.wait.return_value = True
        with patch.object(self.consumer, 'poll', side_effect=OSError('secret-key')):
            with patch('builtins.print') as output:
                poll_loop(self.consumer, stop)
                self.assertNotIn('secret-key', str(output.call_args_list))
        stop.wait.assert_called_once_with(16)
        self.assertEqual(self.hub.desired()[0], WARM)

    def test_talkback_to_real_controller_boundary(self):
        # Exercise the production Hue path, replacing only the physical HTTP call.
        self.hub.demo = False
        stop = Mock()
        for index, (mode, expected) in enumerate(
                [('WHITE', WHITE), ('WARM', WARM), ('CINEMA', CINEMA), ('OFF', OFF)], 1):
            with patch('talkback.urlopen', return_value=io.BytesIO(
                    json.dumps(self.payload(mode, index)).encode())):
                self.assertTrue(self.consumer.poll())
            stop.wait.side_effect = [False, True]
            with patch('control_hue.set_light') as send:
                run_controller(self.hub, stop)
                self.assertEqual(send.call_count, 3)
                for call in send.call_args_list:
                    self.assertEqual(call.args[1], expected)
        self.consumer.accept(self.payload('AUTO', 5))
        stop.wait.side_effect = [False, True]
        with patch('control_hue.set_light') as send:
            run_controller(self.hub, stop)
            send.assert_not_called()

    def test_manual_only_web_labels_and_controls(self):
        from werkzeug.security import generate_password_hash
        app = create_app(self.hub, dict(secret_key='x' * 48,
                                       password_hash=generate_password_hash('test-password')))
        client = app.test_client()
        with client.session_transaction() as session:
            session.update(authenticated=True, csrf='test-csrf')
        self.assertIn('Manuell styring uten sensorer', client.get('/').text)
        response = client.post('/mode', data={'mode': 'warm', 'csrf': 'test-csrf'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.hub.desired()[0], WARM)


if __name__ == '__main__':
    unittest.main()
