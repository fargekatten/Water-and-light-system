"""Optional, outbound-only soil telemetry. No bridge keys or room occupancy."""
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from settings import required


def export_loop(hub, stop):
    key = required('THINGSPEAK_WRITE_API_KEY')
    while not stop.wait(60):
        status = hub.status()
        if not status['fresh']:
            continue
        sample = status['sample']
        body = urlencode({'api_key': key, 'field1': sample['soil_percent'],
                          'field2': sample['needs_water']}).encode()
        try:
            with urlopen(Request('https://api.thingspeak.com/update', data=body), timeout=10) as response:
                if int(response.read()) <= 0:
                    raise ValueError('Cloud rejected measurement')
        except Exception:
            print('Skyeksport feilet; lokal styring fortsetter.')
