# Automatisk plante- og Hue-lyssystem

Prosjektet bruker Arduino Uno WiFi Rev2, Grove-shield, lyssensor, bevegelsessensor, kontakt på prosjektorlerretet, jordfuktighetssensor, Hue Bridge og en PC hjemme. PC-en kan kjøre den lokale MQTT-brokeren, Python-kontrolleren, webappen og lagre sensorhistorikken.

## Lysregler

Reglene vurderes fortløpende. Prioriteten er:

1. Lerretet er nede: oransje lys på 25 %.
2. Bevegelse registreres: gult lys på 50 %. Dette varer til det har gått 30 minutter uten ny bevegelse.
3. Utenfor kl. 07.00–23.00: lysene er av.
4. Innenfor tidsrommet, men lyst nok ved vinduet: lysene er av.
5. Innenfor tidsrommet og mørkt ved vinduet: hvitt lys på full styrke.

Lerretet overstyrer alle andre regler. Bevegelse overstyrer dagslys og tidsplan. Etter bevegelsesperioden går styringen tilbake til tids- og lysmålingen. Sensoren skal stå ved vinduet, vendt mot dagslyset, og ikke slik at Hue-pærene lyser direkte på den. Mangler ferske sensordata i mer enn tre sekunder, venter kontrolleren og lar lysene stå som de er.

## Sensorer og tilkobling

| Port/pinne | Kobling |
|---|---|
| A0 | Kapasitiv jordfuktighetssensorens analoge utgang |
| A1 | Lyssensorens analoge utgang, plassert ved vinduet |
| D2 | PIR-bevegelsessensor, HIGH ved bevegelse |
| D3 | Normalt åpen reedkontakt til GND, lukket når lerretet er nede |
| D4 | Knapp som simulerer vanning |
| D7 | Varsel-LED for tørr jord, med 330 ohm motstand |
| D8 | LED mens vanning simuleres, med 330 ohm motstand |

Koble sensorer til tilsvarende porter på Grove-shieldet. Lyssensorgrensen i sensor_config.h starter på 500: råverdi under 500 tolkes som mørkt, og 500 eller høyere som lyst nok. Dette tar utgangspunkt i målingene du tidligere gjorde. Kontroller grensen når sensoren står ved vinduet, og juster før vanlig bruk om nødvendig.

Jordfuktighet vises som et kalibrert anslag fra 0 til 100 %, ikke som en laboratoriemåling. Mål råverdien i tørr jord og i gjennomvåt, avrent jord; oppdater SOIL_DRY_RAW og SOIL_WET_RAW i sensor_config.h. Varslingsgrensen starter på 30 % og kan tilpasses planten. Ingen pumpe er koblet til ennå. Knappen og nettsidens simulering er kun demonstrasjoner.

## Webapp og lokal lagring

Webappen viser siste lys- og jordmålinger, vanningsbehov og de siste målingene over tid. Målinger lagres lokalt på hjemme-PC-en i SQLite-filen instance/sensor_history.sqlite3. Den beholder opptil 30 dager med omtrent ett minutts mellomrom, og lagrer også når relevante sensorstatuser endres. Git ignorerer mappen instance, så sensorhistorikk og webpassord lastes ikke opp til repoet.

Webappen lytter som standard bare på server-PC-en. For å åpne den fra mobil eller en annen PC på hjemmenettet må serveren konfigureres til å lytte på privatnettet og tillate PC-ens lokale IP/vertsnavn. Ikke åpne webappen eller MQTT-porten mot internett, og ikke sett opp portvideresending i ruteren. Detaljer står i WEB_MQTT.md og SECURITY.md.

## Tilkobling til PC-en

Anbefalt oppsett for webappen er Wi-Fi/MQTT: Arduino sender målinger til en lokal MQTT-broker på PC-en, og Python-webappen styrer Hue og viser status. USB-serie er fortsatt tilgjengelig for enkel feilsøking med control_hue.py, men den kontrolleren viser ikke webappen. Kjør bare én Hue-kontroller om gangen.

Før sensorene kommer kan webappen vises uten fysisk utstyr:

    python -m pip install -r requirements.txt
    python tools/setup_web.py
    python webapp.py --demo

Demoen bruker oppdiktede verdier og styrer ikke Hue. For virkelig utstyr, følg den trinnvise oppskriften i WEB_MQTT.md. Legg aldri Wi-Fi-, MQTT- eller Hue-nøkler i GitHub.