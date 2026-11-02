# Styre Hue fra skolen med ThingSpeak TalkBack

Hjemme-PC-en henter kommandoer over utgående HTTPS fra ThingSpeak og sender dem
til Hue Bridge på hjemmenettet. PC-en må være på, våken og kjøre kontrolleren.
Ingen portvideresending, offentlig webapp eller innkommende tilgang til hjemmet trengs.
Kjør bare én kontroller mot Hue, og bare én konsument per TalkBack-kø.

## Klargjør lokalt

1. Opprett en TalkBack i ThingSpeak-kontoen din. Noter TalkBack ID og dens API Key.
   Dette er en egen nøkkel, ikke kanalens Read/Write API Key. Behold køen tom før start.
2. Installer Python-avhengighetene fra prosjektmappen:

       python -m venv .venv
       .venv\Scripts\python -m pip install -r requirements.txt

   På Linux/macOS brukes `.venv/bin/python` i stedet for `.venv\Scripts\python`.
3. Sett lokale miljøvariabler i PowerShell. Eksemplene er plassholdere:

       $env:THINGSPEAK_TALKBACK_ID = 'YOUR_TALKBACK_ID'
       $env:THINGSPEAK_TALKBACK_API_KEY = 'YOUR_TALKBACK_API_KEY'
       $env:HUE_BRIDGE_HOST = 'YOUR_BRIDGE_HOSTNAME'
       $env:HUE_USERNAME = 'YOUR_HUE_USERNAME'
       $env:HUE_LIGHT_IDS = '4,5,6'

   Bruk samme lokale Hue-oppsett og betrodde CA som beskrevet i WEB_MQTT.md.
   Sett `HUE_CA_FILE` dersom nødvendig. TLS-verifikasjon skal være på.
   `.env` ignoreres av Git, men lastes ikke automatisk. Hold alle virkelige nøkler
   i lokale miljøvariabler eller en lokal, ignorert konfigurasjon. Ikke legg dem i
   kildekode, skjermbilder, URL-er eller dokumentasjon. Ikke bruk en skole-PC til
   å lagre Hue-nøkkelen. TalkBack-nøkkelen gir kontroll over køen; del den ikke.

   Velg bare ID-ene til lampene du faktisk vil styre med `HUE_LIGHT_IDS`.
   Lamper av typen **Color temperature light** kan ikke vise oransje fargelys.
   For disse setter du også `HUE_CINEMA_CT=454` i det lokale miljøet før oppstart.
   CINEMA og senket lerret gir da varmhvitt lys (omtrent 2200 K) på 25 % uten
   å sende den ustøttede `xy`-parameteren. Innstillingen gjelder alle valgte lys;
   bruk en fargetemperatur lampene støtter (153–500 mired). I PowerShell brukes
   `$env:HUE_CINEMA_CT = '454'`; på Mac kan linjen `HUE_CINEMA_CT=454` legges i
   `.env`, som deretter lastes med `set -a`, `source .env`, `set +a`.

## Nå: demonstrasjon uten Arduino

Helt lokal tørrkjøring, uten nøkler eller nettverk:

    python manual_demo.py

Skriv `WHITE`, `WARM`, `CINEMA`, `OFF`, `AUTO`. Skriv `SCREEN DOWN`, deretter
`WHITE`: kommandoen avvises og CINEMA beholdes. `SCREEN UP` fjerner den simulerte
lerretskontakten. `QUIT` avslutter. Kontakten er kun simulert; ingen sensor finnes.

Tørrkjøring som faktisk henter TalkBack-kommandoer, men ikke styrer Hue:

    python manual_demo.py --talkback

For å styre de virkelige Hue-lysene uten Arduino, start eksplisitt:

    python manual_demo.py --hue --talkback

Denne modusen forutsetter manuell kontroll av lerretet: fysisk lerretsposisjon kan
ikke oppdages uten sensor. `SCREEN DOWN/UP` kan demonstrere prioriteten lokalt.
AUTO og utløpt overstyring lar siste lys stå; de later ikke som sensorer finnes.
OFF varer derfor heller ikke nødvendigvis bare 15 minutter fysisk: når perioden
utløper uten sensorer finnes ingen automatisk tilstand å sette i stedet.

Webappen kan også brukes uten sensorer og med ekte Hue:

    python tools/setup_web.py
    python webapp.py --manual-only --talkback

Webpassordet lagres lokalt under `instance/`. Denne modusen kobler ikke til MQTT
og skal ikke brukes som vanlig sensorautomatikk. Webappen åpnes lokalt hjemme.

## Fra skolen

Logg inn på ThingSpeak og åpne din TalkBack. **Legg til en ny kommando i køen**
med nøyaktig `WHITE`, `WARM`, `CINEMA`, `OFF` eller `AUTO` i command string.
Ikke bruk «Execute next command» selv: det fjerner kommandoen fra køen før
hjemme-PC-en henter den. Opprett en ny kommando ved hvert trykk; ikke rediger eller
gjenbruk gamle køelementer. WHITE er hvitt 100 %, WARM gult 50 %, CINEMA kinolys
25 % (oransje, eller varmhvitt med `HUE_CINEMA_CT`), OFF av, og AUTO avslutter
den manuelle overstyringen.

Kontrolleren poller umiddelbart og deretter med minst 16 sekunders mellomrom,
med fem sekunders nettverkstimeout. Dette passer den vanlige gratisgrensen;
sjekk gjeldende ThingSpeak-kvoter. En stor kø tømmes gradvis, ett element per kall.
Fjern gamle køelementer før demonstrasjonen. Meldingen «lyskommando godtatt»
betyr at policyen godtok kommandoen, ikke at Hue har bekreftet fysisk lysendring.

## Med sensorer senere

Følg Wi-Fi/MQTT-oppsettet i WEB_MQTT.md og kjør:

    python webapp.py --talkback

Dette krever ferske sensordata (høyst tre sekunder gamle), akkurat som lokal
manuell styring. USB-programmet `control_hue.py` har ikke TalkBack; ikke kjør
det samtidig. Jordfuktighetseksport `--cloud` er separat og valgfri.

Lerret nede har høyest prioritet og **sletter** overstyringen; den kommer ikke
tilbake når lerretet heves. Andre manuelle kommandoer avvises mens lerretet er
nede. AUTO kan alltid slette overstyringen. Hver godtatt lyskommando varer
15 minutter fra mottak med monoton klokke. Ny kommando starter en ny periode.
Deretter brukes de opprinnelige bevegelses-, tids- og dagslysreglene når sensorene
er ferske. Ved sensorbrudd beholdes lysene, uten å late som automatikk virker.

Bare de fem eksakte kommandoene godtas. Kommandoens serverfelt `created_at`
må ha tidssone, være opprettet etter at kontrolleren startet og være høyst
120 sekunder gammelt. Fremtidige tidsstempler avvises også; synkroniser PC-klokken.
Gamle, dupliserte og baklengs kommando-ID-er avvises. Omstart godtar ikke gamle
køkommandoer. Ukjent/manglende dato blir avvist, også for AUTO.

TalkBack markerer kommandoen som utført når den hentes, **før** Hue har bekreftet
den. Avviste kommandoer legges ikke tilbake. Nettverksfeil kan derfor miste en
kommando; send en ny etter at forbindelsen er tilbake. Lokal automatikk og
15-minuttersgrensen kjører videre selv om TalkBack er utilgjengelig. Nøkler og
feilsvar skrives ikke i TalkBack-loggen. Roter nøkkelen hos ThingSpeak ved lekkasje.

## Tester

    python -m unittest discover -s tests -v
    python tools/test_web_http.py

Testene bruker falske TalkBack-svar og Hue-kall. De kontrollerer tillatte
kommandoer, køalder, omstart, duplikater, lerretsprioritet, utløp, sensorbrudd,
HTTPS-POST, timeout, tom kø og nettverksfeil. Firmwaretesten kjører sketch-logikken
med vertsmaskinens C++-kompilator. Fysiske sensorer, Hue Bridge og ThingSpeak-konto
må sluttprøves hjemme; ingen virkelige nøkler behøves for testpakken.
