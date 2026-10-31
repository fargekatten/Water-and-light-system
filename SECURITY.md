# Privat nett og sikkerhet

Dette er et lokalt, enkeltbruker-eksempel for undervisning. Det er ikke en
ferdig flerbrukertjeneste for skolens produksjonsnett. Ingen offentlig
publisering, ruterendringer eller kontakt med din private Hue Bridge er gjort.

## Grenser og standardvalg

- Webserveren binder **bare 127.0.0.1:8765**, ikke 0.0.0.0. Ingen port forwarding,
  UPnP eller offentlige tunneler skal åpnes. Andre enheter på Wi-Fi kan derfor
  ikke koble seg direkte til webappen.
- Demo må velges eksplisitt med `--demo`. Den bruker virtuelle sensorer og gjør
  ingen MQTT-, Hue- eller skykall. `--demo --cloud` avvises.
- En lokal konfigurasjonsfil inneholder tilfeldig signeringsnøkkel og scrypt-hash
  av et eget passord på minst 14 tegn. Ingen standardpassord. Maks fem
  innloggingsforsøk per minutt per serverprosess; innlogging varer opptil én time.
- Endringer krever innlogging og CSRF-token. Cookies har HttpOnly og SameSite
  Strict. Hostnavn begrenses til localhost/127.0.0.1. Sider cachelagres ikke;
  CSP blokkerer scripts og innramming. Ikke bruk Flask debugserver.
- Cookies har ikke Secure-flagget i denne **loopback HTTP**-konfigurasjonen.
  Ikke flytt appen til ukryptert HTTP på LAN. For tilgang fra egen annen PC,
  bruk en autentisert SSH-tunnel til loopback på serveren. Ved en framtidig
  HTTPS-proxy må Secure-cookies, vertsliste og proxy-tillit konfigureres eksplisitt.
- Hue-nøkkel og MQTT-passord finnes kun på serveren eller sensornoden, aldri
  i nettleseren. Nettleseren kan velge navngitte moduser, ikke vilkårlige URL-er,
  lys-ID-er eller Hue-payloads.
- MQTT har TLS, server-sertifikatkontroll, avvist anonym tilgang og egne
  brukere/ACL-er per rom. Sensoren har bare skrivetilgang til eget sensortema;
  kontrolleren har bare lesetilgang. Ingen kommandotema eller MQTT-websocket
  åpnes. Passord må være forskjellige per enhet og ulike webpassordet.
- Målinger publiseres uten retain. Kontrolleren bruker ren sesjon og forkaster
  retained, feil tema, ugyldige og store pakker. Ved bortfall eller gamle data
  beholdes lyset; etter ny forbindelse starter en forsiktig ventetid.
- Manuell overstyring varer maksimalt 15 minutter. Fysisk senket lerret avbryter
  den. Webvanning er uttrykkelig en serversimulering, ikke en pumpekommando.
- Skyeksport er avslått som standard. `--cloud` sender bare fuktighetsanslag og
  vanningsbehov til ThingSpeak over HTTPS. Bruk en egen **privat** kanal; ikke
  send bevegelse, lerretstatus, Hue-adresse eller nøkler til et dashboard.

## Hjemmenettet ditt

Kjør broker på lokal server/PC. Tillat kun TLS-port 8883 fra sensorens og
kontrollerens adresser i brannmuren. Bind til riktig privat adresse. Ikke åpne
8883/8765 mot internett. Gjestenett og IoT-VLAN kan isolere utstyret, men må ha
uttrykkelige regler for sensor → broker og kontroller → Hue. De fleste
isolerte gjestenett blokkerer ellers også nødvendig lokal trafikk.

Hold firmware og avhengigheter oppdatert. Ikke kopier ekte nøkler inn i
`.env.example`, README, oppgaverapport, skjermbilder eller Git. `instance/`,
`mqtt/private/`, `.env` og lokale `arduino_secrets.h` ignoreres av Git. Gitignore
beskytter ikke nøkler som allerede er lagt inn eller tvangstilføyes. Tilbakekall
publiserte nøkler. Begrens filtilgang til din egen bruker; på Windows må du
kontrollere mappens NTFS-rettigheter i tillegg til Python chmod.

Den som har administrator-/filtilgang på PC-en, kan fortsatt lese lokale
konfigurasjoner. Scrypt-hash erstatter ikke et sterkt passord. Signerte cookies
kan ikke tilbakekalles individuelt før utløp; ved mistanke om lekkasje stopp
serveren og regenerer `instance/web.json` med ny signeringsnøkkel og passord.
Bevegelsesdata er personopplysninger i et faktisk klasserom; bruk demo eller
avklar skolens krav til behandling, tilgang og lagring før reell utplassering.

## Sertifikater

Kontrolleren verifiserer MQTT mot `MQTT_CA_FILE`, Hue mot systemets betrodde CA-er
eller `HUE_CA_FILE`. Broker/Hue-vertsnavn må samsvare med sertifikatets SAN.
WiFiNINA bruker sin egen sertifikatlagring, ikke PC-ens. Brokerens CA/sertifikatkjede
må støttes og være lagt inn i NINA med egnet Arduino firmware-/sertifikatverktøy.
En privat CA kan kreve særskilt rotsertifikatprovisjonering; dette må testes på
kortet. Ikke løs TLS-feil ved å slå av verifikasjon eller bruke ukryptert MQTT.
TLS og ACL er testet mellom lokale programvareklienter; det er ikke bevis på at
ditt fysiske NINA-kort eller Hue-sertifikat allerede er konfigurert riktig.
