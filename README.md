# Water-and-light-system

Arduino leser analoge sensorer. `watering_system.ino` sender råverdier til
ThingSpeak over Wi-Fi; Python kan lese dem og styre Philips Hue.
Koden styrer foreløpig ingen vannpumpe eller ventil.

## Arduino Uno WiFi Rev2

Byggmålet er foreløpig Uno WiFi Rev2 (`arduino:megaavr:uno2018`). Kontroller
modellnavnet på kortet. Vanlig Uno og Uno R4 WiFi krever et annet oppsett.

Installer Arduino CLI, deretter:

```sh
arduino-cli core update-index
arduino-cli core install arduino:megaavr@1.8.8
arduino-cli lib install "WiFiNINA@1.9.1" "ThingSpeak@2.1.1"
python tools/build_arduino.py
```

Kopier `arduino_secrets.example.h` til `arduino_secrets.h` og fyll inn Wi-Fi,
kanalnummer og **write** API key. Den lokale filen ignoreres av Git. Uten filen
bygges skissen med plassholdere; den kan da ikke koble seg til tjenestene.
Kontroller WiFiNINA-firmware og sertifikat for `api.thingspeak.com` med Arduino
IDEs firmware-/sertifikatverktøy dersom HTTPS feiler på kortet.

De to skissene må bygges separat. Byggehjelperen lager automatisk en midlertidig
skissemappe. Ved bruk av Arduino IDE, kopier `watering_system.ino` og
konfigurasjonshodene til en egen mappe kalt `watering_system`.

`Arduino` er en alternativ skisse for serieport, bygges med:

```sh
python tools/build_arduino.py --sketch Arduino
```

**Koblingene er forskjellige:** Wi-Fi-skissen bruker temperatur A2, lys A1,
lyd A0. Serieskissen bruker temperatur A0, lys A1, lyd A2. Kontroller koblingene
før du bytter skisse. Verdiene er rå ADC-verdier, ikke grader Celsius.

## Python på PC-en

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

`.env.example` viser variabelnavn; filen lastes ikke automatisk. Sett verdiene
i terminalen før oppstart. Eksempel i PowerShell (bruk dine egne verdier lokalt):

```powershell
$env:THINGSPEAK_CHANNEL_ID = "YOUR_CHANNEL_ID"
$env:THINGSPEAK_READ_API_KEY = "YOUR_READ_API_KEY"
$env:HUE_BRIDGE_HOST = "YOUR_BRIDGE_HOSTNAME"
$env:HUE_USERNAME = "YOUR_HUE_USERNAME"
$env:ARDUINO_PORT = "COM7"
```

- `python read_sensors.py`: leser CSV over serieport fra skissen `Arduino`.
- `python read_thingspeak.py`: viser siste ThingSpeak-måling hvert 20. sekund.
- `python control_hue.py`: styrer lys 4, 5 og 6. Tilpass `LIGHT_IDS` ved behov.

Hue krever nettverkstilgang til broen og et pålitelig HTTPS-sertifikat.
`HUE_CA_FILE` kan peke til en betrodd CA-fil; `HUE_BRIDGE_HOST` må stemme med
sertifikatet. Sertifikatkontroll er på. API-brukernavnet opprettes lokalt ved
paring med broen. ThingSpeak read- og write-nøkler er forskjellige.

Lyd over `SOUND_THRESHOLD` (standard 100) gir varmt lys på halv styrke.
Ellers gir lysverdi under 500 kaldt lys på full styrke; øvrige verdier gir varmt
lys på full styrke. Kalibrer tersklene mot sensorene dine.

Testene bruker simulerte HTTP-svar og ingen ekte nøkler. Fysisk sensoravlesning,
Wi-Fi, ThingSpeak og Hue må i tillegg testes med ditt utstyr og lokale nøkler.
Ikke legg ekte nøkler i Git. Hvis en nøkkel tidligere er publisert, tilbakekall
og erstatt den; sletting fra siste filversjon fjerner den ikke fra Git-historikken.
