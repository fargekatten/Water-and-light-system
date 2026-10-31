# Lysstyring og jordfuktighet

For **Arduino Uno WiFi Rev2**, Philips Hue og en PC som kjører Python.
Arduino sender sensordata via USB hvert 100. millisekund. Python leser kontinuerlig
og styrer Hue-broen på lokalnettet. ThingSpeak brukes ikke til lysstyringen;
skyopplasting hvert 20. sekund ville gjort bevegelse og kinomodus for tregt.

## Lysregler

| Situasjon | Lys |
|---|---|
| Kl. 07:00–10:59, ingen bevegelse de siste 30 minuttene | 100 %, dagslyshvitt, ca. 6500 K |
| Bevegelse registrert | 50 %, varmt/gult, ca. 2200 K |
| Lerret nede | Kinomodus: 25 %, gul/oransje |
| Lerret heves | Gult halvlys, med en ny 30-minuttersperiode |
| Ny bevegelse i ventetiden | Starter 30 minutter på nytt |
| Oppstart i morgentidsrommet | Gult halvlys i minst 30 minutter |
| Manglende/eldre enn 3 sekunder sensordata | Beholder lyset; bytter ikke til hvitt |

Kinomodus har høyest prioritet hele døgnet. Den sendes til Hue ved neste
kontrollrunde, uten overgangstid og uten å vente på 30-minuttersfristen.
USB måles hver 0,1 s og Python kontrollerer hver 0,1 s; faktisk responstid avhenger
også av sensoren, Hue og nettverket. Et pågående nettverkskall kan forsinke en
endring. «Umiddelbart» er dermed rask reaksjon, ikke en sanntidsgaranti.

Utenfor 07–11 er standard **av**, eller kinomodus dersom lerretet er nede.
Heves lerretet utenfor tidsrommet, slås lyset av. Innenfor 07–11 starter det
med gult halvlys etter film og venter 30 minutter før hvitt.
Tidssonen er `Europe/Oslo`, inkludert sommer-/vintertid. Oppstart i morgentidsrommet
gir en forsiktig ventetid fordi tidligere bevegelse ikke er kjent.
`OUTSIDE_HOURS=off` er standard. Alternative innstillinger er `same` for
morgenreglene hele døgnet og `keep` for å beholde lyset utenfor tidsrommet.

## Jordfuktighet og simulert vanning

Sensorens råverdi omregnes til et **kalibrert anslag** på 0–100 %.
Dette er ikke en laboratoriemåling av jordens vanninnhold. Under 30 % tennes
varsel-LED på D7, og PC-en skriver «TRENGER VANN» når status endres.
En knapp på D4 simulerer fem sekunders vanning: D8-LED lyser og PC-en viser
«SIMULERT vanning». Ingen pumpe, ventil eller vann er koblet til.
Den målte fuktigheten og tørrvarslet endres ikke kunstig ved simulering;
er jorden fortsatt tørr, blir varslet stående. Knappen må slippes før ny simulering.

Kalibrer `SOIL_DRY_RAW` og `SOIL_WET_RAW` i `sensor_config.h` med sensoren i
henholdsvis tørr og gjennomvåt, avrent jord. Eksempelverdiene 800/350 må erstattes
med dine målte verdier. Tilpass også terskelen til planten.

## Komplett deleliste for dette oppsettet

Mengdene gjelder ett rom, én potte og tre styrte lys. Gjenbruk delene du har.

| Antall | Del | Krav/bruksområde |
|---:|---|---|
| 1 | Arduino Uno WiFi Rev2 | Bekreft modellnavnet på kortet; vanlig Uno og R4 er andre byggmål |
| 1 | USB A–B **datakabel** | Uno til PC; eventuelt USB-C-adapter til PC-en |
| 1 | PC med Python 3.10+ | Må være på og ikke i hvilemodus mens styringen kjører |
| 1 | HC-SR501 PIR-bevegelsessensor | Forsyning fra 5 V, OUT til D2; registrerer bevegelse, ikke sikker tilstedeværelse |
| 1 | Kapasitiv jordfuktighetssensor med analog utgang | 5 V-kompatibel modul, utgang innen 0–5 V, til A0; foretrekkes fremfor ubeskyttet resistiv probe |
| 1 sett | Magnet og normalt åpen reedkontakt | Kontakten lukkes når lerretets nedre kant er i nedeposisjon; lavspenningskontakt til D3/GND |
| 1 | Momentan trykknapp, normalt åpen | Simulert vanning, mellom D4 og GND |
| 2 | LED-er | Gjerne rød for tørr jord, blå for simulering |
| 2 | 330 ohm motstander, minst 0,125 W | Én i serie med hver LED |
| 1 | Breadboard | For kobling av sensorer, knapp og LED-er |
| Ca. 30 | Dupont-ledninger | Både hann–hann og hann–hunn, avhengig av modulene |
| Etter avstand | Isolert tolederkabel | Reedkontakt ved lerret; signal og GND |
| 1 sett | Festemateriell og strekkavlastning | Til magnet, kontakt, PIR og kabler |
| 1 | Philips Hue Bridge med strømforsyning | På samme lokale nettverk som PC-en |
| 1 | Nettverkskabel og ledig ruter-/switchport | Hue Bridge til lokalnettet |
| 3 | Hue **White and Color Ambiance**-lys | Eller tilsvarende Hue-støttede fargelys; må støtte både hvittemperatur og XY-farge for gul/oransje kino |
| Etter behov | Passende armaturer/strømforsyninger | Til de valgte pærene eller lysstripene; gjenbruk eksisterende Hue-oppsett |
| 1 | Plante/potte med jord | Fuktmåling; beskytt elektronikken mot vann |
| 1 | Eksisterende prosjektorlerret | Koden registrerer posisjon, den styrer ikke lerretsmotoren |

Ingen pumpe, motorrelé, vannventil, temperatur-, lyd- eller lyssensor trengs.
PIR kan overse en helt stillesittende person; 30-minuttersminnet reduserer dette,
men garanterer ikke tilstedeværelsesdeteksjon etter 30 minutter uten bevegelse.

## Kobling

| Arduino | Kobles til |
|---|---|
| 5V og GND | PIR og jordfuktighetssensorens forsyning etter modulens spesifikasjon |
| D2 | PIR OUT, aktiv HIGH |
| D3 | Reedkontakt mot GND, lukket bare når lerretet er nede |
| D4 | Trykknapp mot GND |
| A0 | Jordfuktighetssensorens analoge utgang |
| D7 | 330 ohm → varsel-LED anode; katode til GND |
| D8 | 330 ohm → simulerings-LED anode; katode til GND |

D3/D4 bruker interne pull-up-motstander. Monter magnet/kontakt slik at de møtes
ved ønsket nedeposisjon, og test logikken før lysstyringen startes. En brutt
kontaktledning tolkes som «lerret oppe»; dette er en enkel demonstrasjonsløsning.
Ikke koble Arduino til lerretets motor, styringsspenning eller strømnett.
PIR må få stabilisere seg etter oppstart (ofte 30–60 sekunder).

## Bygg og last opp Arduino

Installer Arduino CLI og kjør:

```sh
arduino-cli core update-index
arduino-cli core install arduino:megaavr@1.8.8
python tools/build_arduino.py
```

Ingen Wi-Fi-nøkler eller ThingSpeak-biblioteker trengs for den nye USB-skissen.
Byggehjelperen kopierer skissen og `sensor_config.h` til en midlertidig mappe.
For opplasting i Arduino IDE: legg `watering_system.ino` og `sensor_config.h`
i en mappe kalt `watering_system`, velg **Arduino Uno WiFi Rev2**, riktig port,
og last opp. Ikke legg den gamle `Arduino`-skissen i samme skissemappe.
Lukk seriemonitoren før du starter Python; bare ett program kan eie porten.

## Start på PC-en

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Sett lokale verdier i PowerShell (`.env.example` lastes ikke automatisk):

```powershell
$env:ARDUINO_PORT = "COM7"
$env:HUE_BRIDGE_HOST = "YOUR_BRIDGE_HOSTNAME"
$env:HUE_USERNAME = "YOUR_HUE_USERNAME"
$env:HUE_LIGHT_IDS = "4,5,6"
$env:ROOM_TIMEZONE = "Europe/Oslo"
$env:OUTSIDE_HOURS = "off"
# Ved egen CA for broen:
# $env:HUE_CA_FILE = "C:\path\to\trusted-hue-ca.pem"
python control_hue.py
```

Tilpass porten og lys-ID-ene. Hue-brukernavn opprettes ved lokal paring med broen.
Vertsnavnet må stemme med HTTPS-sertifikatet; `HUE_CA_FILE` kan peke til en betrodd
CA-fil. Sertifikatkontroll er på. Nøkler skal aldri legges i Git.
`python read_sensors.py` viser bare jordvarsler og simulering uten Hue; kjør det
som et alternativ, ikke samtidig med `control_hue.py` på samme port.
Varsel gis på PC og LED, ikke via SMS/e-post.

De eldre filene `Arduino` og `read_thingspeak.py` beholdes som separate eksempler.
De bruker andre dataformater og inngår ikke i det nye oppsettet. ThingSpeak-
plassholderne gjelder bare den gamle visningen.

## Kontroller med utstyret

1. Les jordverdier og kalibrer tørr/våt i `sensor_config.h`; bygg og last opp på nytt.
2. Bekreft tørrvarslet og at knappen tenner simulerings-LED i fem sekunder.
3. Kontroller at Hue-lysene støtter hvitt, gult og gul/oransje.
4. Utløs PIR, senk/heis lerretet og kontroller kino → gult halvlys.
5. La det gå 30 minutter uten bevegelse mellom 07 og 11; kontroller hvitt lys.
6. Koble fra USB og kontroller at systemet ikke automatisk bytter til hvitt.

Automatiske tester dekker tidsregler, kinoprioritet, manglende data, Hue-kall,
serieformat og skissens fukt-/knapp-/simuleringslogikk. Maskinvare og faktisk
nettverkstilgang må verifiseres lokalt. Firmware-simulering krever `g++` og
markeres som hoppet over hvis kompilatoren ikke finnes.
