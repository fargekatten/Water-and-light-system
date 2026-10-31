import os
import re
import ssl
import paho.mqtt.client as mqtt
from sensor_stream import parse_sample
from settings import required


def connect(hub):
    room = os.environ.get('MQTT_ROOM', 'rom101')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,40}', room):
        raise ValueError('Ugyldig rom-ID')
    topic = f'school/{room}/sensors'
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='controller-'+room,
                         clean_session=True)
    client.username_pw_set(required('MQTT_USERNAME'), required('MQTT_PASSWORD'))
    client.tls_set(ca_certs=required('MQTT_CA_FILE'), tls_version=ssl.PROTOCOL_TLS_CLIENT)

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(topic, qos=1)
        else:
            with hub.lock:
                hub.error = 'MQTT-innlogging avvist'

    def on_message(client, userdata, message):
        if message.topic != topic or message.retain or len(message.payload) > 1024:
            return
        try:
            data = parse_sample(message.payload)
        except (ValueError, UnicodeError):
            return
        hub.observe(data)

    def on_disconnect(client, userdata, flags, reason_code, properties):
        with hub.lock:
            hub.policy.last_sample = None
            hub.error = 'MQTT frakoblet; beholder lyset'

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(1, 30)
    client.connect_async(required('MQTT_HOST'), int(os.environ.get('MQTT_PORT', '8883')), 30)
    client.loop_start()
    return client
