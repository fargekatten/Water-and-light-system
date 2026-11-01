# Wi-Fi, MQTT og lokal webapp

PC-en hjemme fungerer som lokal MQTT-broker, Python-kontroller, webserver og lagring for sensorhistorikk. Arduino kobles til hjemmenettets Wi-Fi, og Hue Bridge brukes lokalt. ThingSpeak er valgfritt; det trengs ikke for lysstyringen. Ikke start USB-kontrolleren og webapp-kontrolleren samtidig.

## Lyslogikk

Styringen bruker denne prioriteten:

1. Lerret nede: oransje, 25 %.
2. Bevegelse nå eller de siste 30 minuttene: gult, 50 %.
3. Utenfor kl. 07–23: av.
4. Lyst nok ved vinduet: av.
5. Ellers: hvitt, 100 %.

Lyssensoren leses på A1 og skal plasseres ved vinduet, ikke ved lampene. Grensen står i sensor_config.h: verdi under 500 betyr mørkt; 500 eller høyere betyr lyst nok. Juster etter måling med sensoren på riktig sted. Jordfuktighetssensoren bruker A0 og må kalibreres med tørr og våt jord.

Arduino leser sensorene hvert 100 ms. MQTT publiserer raskt når bevegelse, lerret eller lyst/mørkt-status endres, og ellers omtrent én gang per sekund. Hvis sensor- eller nettverksdata blir gamle, lysstyringen beholder gjeldende lys i stedet for å velge en ny tilstand.

## Prøv webappen uten utstyr

Kjør fra prosjektmappen:

    python -m pip install -r requirements.txt
    python tools/setup_web.py
    python webapp.py --demo

Åpne http://127.0.0.1:8765 på PC-en som kjører programmet. Opprett webpassord ved første kjøring. Demoen viser simulerte målinger, og ingen Hue- eller MQTT-forbindelse startes.

Manuelle lysvalg varer opptil 15 minutter. Lerret nede overstyrer manuelle valg. Sensorhistorikk lagres lokalt i instance/sensor_history.sqlite3, og opptil 30 dager beholdes. Demoverdier lagres ikke.

## Åpne webappen fra en annen enhet hjemme

Standard er at webappen bare lytter på PC-en selv. For å åpne den på mobil eller nettbrett koblet til samme hjemmenett, angi dette i PowerShell før oppstart:

    $env:WEB_BIND_HOST = "0.0.0.0"
    $env:WEB_ALLOWED_HOSTS = "localhost,127.0.0.1,192.168.1.20"

Bytt 192.168.1.20 med hjemme-PC-ens lokale IP-adresse. Tillat port 8765 bare på privat hjemmenett i Windows-brannmuren. Ikke sett opp portvideresending eller åpne dette mot internett. Den lokale nettsiden bruker HTTP, så bruk den bare på et nettverk du stoler på.

## Sett opp lokal MQTT-broker

Installer Mosquitto 2.x på hjemme-PC-en. Repoet har konfigurasjonseksempler i mqtt/.

1. Lag et serversertifikat med riktig lokalt DNS-navn eller IP-adresse i SAN, samt en CA. Oppbevar privatnøkkel og passordfiler lokalt, utenfor Git.
2. Opprett to egne MQTT-brukere, én for Arduino-sensoren og én for Python-kontrolleren. Eksempelkontoene i ACL-filen viser tillatt lesing og skriving.
3. Tilpass mqtt/acl.example og mqtt/mosquitto.conf.example. Oppsettet bruker TLS-port 8883, avviser anonyme brukere og skal ikke ha en ukryptert offentlig listener.
4. Start Mosquitto og tillat port 8883 bare fra nødvendige enheter på hjemmenettet.
5. Konfigurer Uno WiFi Rev2 sitt sertifikatlager med CA-en. Arduino må validere brokerens TLS-sertifikat.

## Bygg og konfigurer Arduino

Installer Arduino CLI-kjernen og bibliotekene:

    arduino-cli core install arduino:megaavr@1.8.8
    arduino-cli lib install "WiFiNINA@1.9.1" "PubSubClient@2.8"
    python tools/build_arduino.py --sketch wifi_sensor

Kopier firmware/wifi_sensor/arduino_secrets.example.h til arduino_secrets.h i samme mappe. Sett Wi-Fi-navn/passord, brokerens lokale navn, sensorens MQTT-bruker/passord, klient-ID og tema. Ikke legg de faktiske verdiene i GitHub. For Arduino IDE skal wifi_sensor.ino, network.h, arduino_secrets.h, sensor_node.h og sensor_config.h ligge sammen i skissemappen. Velg Arduino Uno WiFi Rev2.

## Start webappen med ekte utstyr

Opprett webpassord med tools/setup_web.py. Sett disse verdiene lokalt i PowerShell før du starter webappen:

    $env:HUE_BRIDGE_HOST = "YOUR_BRIDGE_HOSTNAME"
    $env:HUE_USERNAME = "YOUR_HUE_USERNAME"
    $env:HUE_LIGHT_IDS = "4,5,6"
    $env:MQTT_HOST = "YOUR_MQTT_DNS_HOSTNAME"
    $env:MQTT_PORT = "8883"
    $env:MQTT_ROOM = "rom101"
    $env:MQTT_USERNAME = "controller-rom101"
    $env:MQTT_PASSWORD = "YOUR_UNIQUE_CONTROLLER_PASSWORD"
    $env:MQTT_CA_FILE = "C:\private\mqtt-ca.pem"
    python webapp.py

Hvis Hue-broens CA ikke er systemgodkjent, sett HUE_CA_FILE til den betrodde sertifikatfilen. Hue-vertsnavnet må samsvare med sertifikatet. Webpassordet er separat fra MQTT- og Hue-innloggingen.

Valgfri ThingSpeak-eksport startes med python webapp.py --cloud etter at en privat ThingSpeak-nøkkel er satt lokalt. Den sender bare jordfuktighetsanslag og vanningsbehov.