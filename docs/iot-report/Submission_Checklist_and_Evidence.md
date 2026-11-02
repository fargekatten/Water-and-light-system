# Submission checklist and evidence collection

All documentation is in English. The report is an editable draft based on session evidence, not a claim that unperformed tests passed.

## Files
- IoT_Project_Report_Draft.docx: template-aligned report, numbered sections, tables, diagrams and appendix inventory.
- Group_Need_to_Know.docx: responsibilities, rules, common code questions and demo/run instructions.
- 01_system_architecture and 02_arduino_wiring: PNG for slides, SVG for editing, PDF for printing.

## Required before submission
- [ ] Group names, course, date and honest individual contributions.
- [ ] Final hardware photograph and model/revision checks.
- [ ] Final working source files from BOTH computers; redact credentials.
- [ ] Capture final commit/status; local changes are not confirmed committed.
- [ ] Screenshot dashboard and feeds without keys; capture actual light states.
- [ ] Time at least 10 end-to-end response trials.
- [ ] Verify 30 min activity hold and 15 min manual expiry with timed evidence.
- [ ] Isolate screen-versus-manual priority and touch-only actuation tests.
- [ ] Verify stale data >75 s hold output and fresh data restore operation.
- [ ] Verify rejection of old/invalid TalkBack commands in final code.
- [ ] Report failure cases honestly and check references/citation style.
- [ ] Acknowledge AI assistance if required by course policy.

## Evidence already available from session
|ID|Evidence|Status|
|---|---|---|
|E1|Light entry 404: sofa 36, screen 25, light 47, touch 0, age 2 s|Supplied output|
|E2|Entry 409: screen 594, light 556, age 2 s|Supplied output|
|E3|Automatic OFF physically switched Hue off|User-confirmed|
|E4|Sofa warm response; screen response after >200 threshold|User-confirmed|
|E5|Hotspot-to-home-Hue end-to-end operation|User-confirmed|
|E6|Dashboard raw 598, age 62 s, fresh|Supplied dashboard text|

## Latency measurement sheet
Use synchronised clocks and record how lamp-change time was observed. “Age” in the feed is not end-to-end latency.

|Trial|Sensor event time|Cloud created_at|Mac receive time|Lamp-change time|End-to-end seconds|Success / anomaly|
|---|---|---|---|---|---|---|
|1|||||||
|2|||||||
|3|||||||
|4|||||||
|5|||||||
|6|||||||
|7|||||||
|8|||||||
|9|||||||
|10|||||||

Report sample count, median, minimum, maximum, failures, network and sensor conditions. Do not label ideal 0–25 s scheduling delay as measured maximum latency.

## Source and secret handling
Collect the final local Arduino sketches, three new thingspeak_*.py files, modified lighting.py/hub.py/webapp.py/dashboard.html, and their project dependencies. Keep source code as a separate sanitised archive. This documentation package is not that source archive.
Exclude .env, .env.save, arduino_secrets.h, instance/web.json, instance/hue_pairing.json and key-bearing backups. Do not remove working local files merely to sanitise a submission; create a clean export.

## Final implementation caveats
- Local web access only; remote demonstration uses ThingSpeak TalkBack.
- Plant reading is raw; no dry-soil alarm calibration, no automatic watering.
- New ThingSpeak data bypass old combined SQLite history.
- Old MQTT files remain in the repository and are not the demonstrated firmware.
- HUE_CINEMA_CT=454 is required for the demonstrated warm-white cinema configuration.
- Verify exact physical cable pinout; colours shown apply only to the tested Sharp cable.
