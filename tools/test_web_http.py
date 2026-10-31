"""Exercise the real HTTP server locally with ephemeral test credentials."""
import http.cookiejar
import json
from pathlib import Path
import re
import secrets
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from waitress import create_server
from werkzeug.security import generate_password_hash
from hub import Hub
from webapp import create_app, demo_loop, run_controller

hub = Hub(demo=True)
password = secrets.token_urlsafe(24)
app = create_app(hub, dict(secret_key=secrets.token_urlsafe(48),
                          password_hash=generate_password_hash(password)))
stop = threading.Event()
server = create_server(app, host='127.0.0.1', port=0)
for target, args in [(server.run, ()), (demo_loop, (hub, stop)), (run_controller, (hub, stop))]:
    threading.Thread(target=target, args=args, daemon=True).start()
base = 'http://127.0.0.1:'+str(server.effective_port)
# This test makes only local requests to its own server; no proxy or private bridge.
client = build_opener(ProxyHandler({}), HTTPCookieProcessor(http.cookiejar.CookieJar()))
try:
    try:
        client.open(base+'/api/status')
        raise AssertionError('Anonymous status access')
    except HTTPError as error:
        assert error.code == 401
    login = client.open(base+'/login').read().decode()
    csrf = re.search(r'name="csrf" value="([^"]+)"', login).group(1)
    dashboard = client.open(base+'/login', urlencode(dict(csrf=csrf, password=password)).encode()).read().decode()
    assert 'DEMO' in dashboard
    csrf = re.search(r'name="csrf" value="([^"]+)"', dashboard).group(1)
    client.open(base+'/mode', urlencode(dict(csrf=csrf, mode='cinema')).encode()).read()
    deadline = time.monotonic()+3
    while hub.applied != 'manuell: cinema' and time.monotonic()<deadline:
        time.sleep(.1)
    status = json.load(client.open(base+'/api/status'))
    assert status['demo'] and status['applied'] == 'manuell: cinema'
    client.open(base+'/simulate', urlencode(dict(csrf=csrf)).encode()).read()
    assert json.load(client.open(base+'/api/status'))['watering_simulated']
    print('PASS: real HTTP login, authorization, manual demo lighting and watering simulation; no Hue calls.')
finally:
    stop.set()
    server.close()
    server.task_dispatcher.shutdown()
