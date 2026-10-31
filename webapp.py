"""Authenticated local dashboard. Never expose this port to the Internet."""
import argparse
from collections import deque
from datetime import timedelta
import json
from pathlib import Path
import secrets
import threading
import time

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from hub import Hub


def create_app(hub, config=None):
    if config is None:
        config = json.loads(Path('instance/web.json').read_text())
    if len(config['secret_key']) < 32 or not config['password_hash'].startswith('scrypt:'):
        raise ValueError('Kjør python tools/setup_web.py først')
    app = Flask(__name__)
    app.config.update(SECRET_KEY=config['secret_key'], MAX_CONTENT_LENGTH=4096,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_REFRESH_EACH_REQUEST=False, SESSION_COOKIE_SAMESITE='Strict',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
                      TRUSTED_HOSTS=['localhost', '127.0.0.1'])
    attempts = deque()
    login_lock = threading.Lock()

    @app.before_request
    def protect():
        if request.routing_exception is not None:
            raise request.routing_exception
        if request.method == 'POST':
            token = session.get('csrf', '')
            if not token or not secrets.compare_digest(token, request.form.get('csrf', '')):
                abort(403)
        if request.endpoint not in ('login', 'static') and not session.get('authenticated'):
            if request.path.startswith('/api/'):
                abort(401)
            return redirect(url_for('login'))

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'none'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            with login_lock:
                now = time.monotonic()
                while attempts and now-attempts[0] >= 60:
                    attempts.popleft()
                if len(attempts) >= 5:
                    abort(429)
                attempts.append(now)
            if check_password_hash(config['password_hash'], request.form.get('password', '')):
                session.clear()
                session.update(authenticated=True, csrf=secrets.token_urlsafe(32))
                session.permanent = True
                return redirect(url_for('index'))
            error = 'Feil passord'
        session.setdefault('csrf', secrets.token_urlsafe(32))
        return render_template('login.html', error=error)

    @app.get('/')
    def index():
        return render_template('dashboard.html', status=hub.status(), message=request.args.get('message', ''))

    @app.get('/api/status')
    def status():
        return jsonify(hub.status())

    @app.post('/mode')
    def mode():
        try:
            hub.manual(request.form.get('mode'))
        except ValueError as error:
            return str(error), 400
        return redirect(url_for('index'))

    @app.post('/simulate')
    def simulate():
        # A simulation changes neither measured moisture nor the physical dry warning.
        with hub.lock:
            hub.simulation_until = time.monotonic()+5
        return redirect(url_for('index', message='Fem sekunders vanning SIMULERES på serveren; ingen pumpe eller fysisk LED styres her.'))

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    return app


def run_controller(hub, stop):
    from control_hue import LIGHT_IDS, set_light
    last = None
    while not stop.wait(0.1):
        state, mode = hub.desired()
        if state is None or state == last:
            continue
        try:
            if not hub.demo:
                for light in LIGHT_IDS:
                    set_light(light, state)
            last = state
            with hub.lock:
                hub.applied = mode
                hub.error = None
        except Exception:
            with hub.lock:
                hub.error = 'Hue-kall feilet; sjekk nettverk, sertifikat og lokal konfigurasjon'
            stop.wait(1)


def demo_loop(hub, stop):
    while not stop.is_set():
        hub.observe(dict(motion=0, screen_down=0, soil_raw=800, soil_percent=0,
                         needs_water=1, watering_simulated=0))
        stop.wait(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='No MQTT or Hue connections')
    parser.add_argument('--cloud', action='store_true', help='Opt-in soil-only ThingSpeak export')
    args = parser.parse_args()
    if args.demo and args.cloud:
        parser.error('Demo-data skal ikke eksporteres til skyen')
    hub = Hub(demo=args.demo)
    app = create_app(hub)
    stop = threading.Event()
    client = None
    if args.demo:
        threading.Thread(target=demo_loop, args=(hub, stop), daemon=True).start()
    else:
        from settings import required
        required('HUE_BRIDGE_HOST')
        required('HUE_USERNAME')
        from mqtt_input import connect
        client = connect(hub)
    if args.cloud:
        from settings import required
        required('THINGSPEAK_WRITE_API_KEY')
        from cloud_export import export_loop
        threading.Thread(target=export_loop, args=(hub, stop), daemon=True).start()
    threading.Thread(target=run_controller, args=(hub, stop), daemon=True).start()
    from waitress import serve
    try:
        serve(app, host='127.0.0.1', port=8765, threads=4, clear_untrusted_proxy_headers=True)
    finally:
        stop.set()
        if client:
            client.disconnect()
            client.loop_stop()


if __name__ == '__main__':
    main()
