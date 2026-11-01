"""Outbound-only ThingSpeak TalkBack consumer. Never log API keys or responses."""
from datetime import datetime, timezone
import json
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from settings import required

COMMANDS = frozenset(('WHITE', 'WARM', 'CINEMA', 'OFF', 'AUTO'))
MAX_AGE_SECONDS = 120
POLL_SECONDS = 16


class TalkBack:
    def __init__(self, hub, talkback_id, api_key, clock=time.time):
        if not re.fullmatch(r'[1-9][0-9]*', talkback_id):
            raise ValueError('THINGSPEAK_TALKBACK_ID må være et positivt heltall')
        if not api_key or api_key.startswith('YOUR_'):
            raise ValueError('TalkBack API-nøkkel mangler')
        self.hub = hub
        self.url = f'https://api.thingspeak.com/talkbacks/{talkback_id}/commands/execute.json'
        self.api_key = api_key
        self.clock = clock
        self.started = clock()
        self.last_id = 0

    def accept(self, command):
        """Validate server creation time, order and allowlist before touching the hub."""
        if not isinstance(command, dict):
            return False
        try:
            identifier = str(command['id'])
            if not re.fullmatch(r'[1-9][0-9]*', identifier):
                return False
            identifier = int(identifier)
            created = datetime.fromisoformat(command['created_at'].replace('Z', '+00:00'))
            if created.tzinfo is None:
                return False
            created = created.astimezone(timezone.utc).timestamp()
        except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
            return False
        now = self.clock()
        if identifier <= self.last_id:
            return False
        self.last_id = identifier
        mode = command.get('command_string')
        if (not isinstance(mode, str) or mode not in COMMANDS
                or created < self.started or not 0 <= now - created <= MAX_AGE_SECONDS):
            return False
        try:
            self.hub.manual(mode.lower())
        except ValueError:
            return False  # Screen priority / missing fresh sensors; never queue locally.
        return True

    def poll(self):
        request = Request(self.url, data=urlencode({'api_key': self.api_key}).encode(),
                          headers={'Content-Type': 'application/x-www-form-urlencoded'},
                          method='POST')
        with urlopen(request, timeout=5) as response:
            body = response.read(16385)
        if len(body) > 16384:
            raise ValueError('For stort TalkBack-svar')
        if not body.strip() or body.strip() == b'0':
            return False
        return self.accept(json.loads(body))


def from_environment(hub):
    return TalkBack(hub, required('THINGSPEAK_TALKBACK_ID'),
                    required('THINGSPEAK_TALKBACK_API_KEY'))


def poll_loop(consumer, stop):
    while not stop.is_set():
        try:
            if consumer.poll():
                print('TalkBack: lyskommando godtatt')
        except Exception:
            # URL errors can contain credentials; never print exception text.
            print('TalkBack utilgjengelig eller ugyldig svar; lokal styring fortsetter')
        if stop.wait(POLL_SECONDS):
            break
