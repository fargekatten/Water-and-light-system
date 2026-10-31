"""Opt-in integration check using Docker, OpenSSL and an isolated TLS broker."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import threading
import time
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paho.mqtt.client as mqtt
from hub import Hub
from mqtt_input import connect

IMAGE = 'eclipse-mosquitto:2.0.22@sha256:09b62ff32c2e7b64d4b431b9a89236073289b68db273de2b089edeb9b0d92b5c'


def run():
    docker_env = dict(os.environ)
    for name in ('DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'):
        docker_env.pop(name, None)
    docker = ['docker', '--host=unix:///var/run/docker.sock']
    name = 'room-mqtt-test-'+secrets.token_hex(4)
    password = secrets.token_urlsafe(24)
    clients = []
    with tempfile.TemporaryDirectory(prefix='room-mqtt-') as directory:
        root = Path(directory)
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', str(root/'server.key'), '-out', str(root/'server.crt'),
                        '-days', '1', '-subj', '/CN=localhost',
                        '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        (root/'passwords').write_text(f'sensor-rom101:{password}\ncontroller-rom101:{password}\n')
        (root/'acl').write_text('user sensor-rom101\ntopic write school/rom101/sensors\n'
                               'user controller-rom101\ntopic read school/rom101/sensors\n')
        (root/'broker.conf').write_text('listener 8883\nallow_anonymous false\n'
            'certfile /test/server.crt\nkeyfile /test/server.key\n'
            'password_file /test/passwords\nacl_file /test/acl\npersistence false\n')
        uid = f'{os.getuid()}:{os.getgid()}'
        subprocess.run(docker+['run', '--rm', '--user', uid, '-v', f'{root}:/test', IMAGE,
                              'mosquitto_passwd', '-U', '/test/passwords'], env=docker_env, check=True)
        subprocess.run(docker+['run', '-d', '--name', name, '--user', uid,
                              '-p', '127.0.0.1::8883', '-v', f'{root}:/test:ro', IMAGE,
                              'mosquitto', '-c', '/test/broker.conf'],
                       env=docker_env, check=True, stdout=subprocess.DEVNULL)
        try:
            port_text = subprocess.check_output(docker+['port', name, '8883'], env=docker_env, text=True)
            port = int(port_text.strip().rsplit(':', 1)[1])
            hub = Hub()
            original = {key: os.environ.get(key) for key in
                        ('MQTT_HOST', 'MQTT_PORT', 'MQTT_CA_FILE', 'MQTT_USERNAME', 'MQTT_PASSWORD')}
            os.environ.update(MQTT_HOST='localhost', MQTT_PORT=str(port),
                              MQTT_CA_FILE=str(root/'server.crt'), MQTT_USERNAME='controller-rom101',
                              MQTT_PASSWORD=password)
            try:
                receiver = connect(hub)
                clients.append(receiver)
            finally:
                for key, value in original.items():
                    if value is None: os.environ.pop(key, None)
                    else: os.environ[key] = value
            def publisher(user, passwd):
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                client.tls_set(str(root/'server.crt'))
                if user: client.username_pw_set(user, passwd)
                connected = threading.Event()
                codes = []
                def callback(client, data, flags, code, properties):
                    codes.append(code)
                    connected.set()
                client.on_connect = callback
                client.connect('localhost', port, 10)
                client.loop_start()
                clients.append(client)
                assert connected.wait(5), 'No CONNACK'
                return client, codes[0]
            unauthorized, code = publisher(None, None)
            assert code != 0, 'Anonymous client unexpectedly accepted'
            wrong, code = publisher('sensor-rom101', 'wrong-test-password')
            assert code != 0, 'Wrong password unexpectedly accepted'
            sensor, code = publisher('sensor-rom101', password)
            assert code == 0
            sample = dict(motion=1, screen_down=0, soil_raw=800, soil_percent=0,
                          needs_water=1, watering_simulated=0)
            deadline = time.monotonic()+8
            while hub.sample is None and time.monotonic()<deadline:
                sensor.publish('school/rom101/sensors', json.dumps(sample), qos=1).wait_for_publish(2)
                time.sleep(.2)
            assert hub.sample == sample, 'Authenticated TLS telemetry did not reach controller'
            # Broker ACL: sensor cannot write another room, verified by MQTT v5 reason code.
            denied = threading.Event()
            reasons = []
            forbidden = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
            forbidden.tls_set(str(root/'server.crt'))
            forbidden.username_pw_set('sensor-rom101', password)
            forbidden.on_publish = lambda c,u,mid,reason,props: (reasons.append(reason), denied.set())
            forbidden.connect('localhost', port)
            forbidden.loop_start()
            clients.append(forbidden)
            forbidden.publish('school/other/sensors', '{}', qos=1)
            assert denied.wait(5) and reasons[0].is_failure, 'Cross-room write unexpectedly allowed'
            print('PASS: TLS telemetry, anonymous rejection, wrong-password rejection and broker room ACL.')
        finally:
            for client in clients:
                client.disconnect()
                client.loop_stop()
            subprocess.run(docker+['rm', '-f', name], env=docker_env, check=True, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    run()
