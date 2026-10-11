# TAPI-001 — Owner-reported Termux API pilot closeout

Date: 2026-10-11
Research owner: Chad Holland — Research Director, Orchestrator, and Project Owner.
Evidence class: Owner-reported Termux execution; not independently reproduced.

## Passive preflight
Python shutil.which located termux-info, termux-battery-status, termux-sensor, termux-telephony-deviceinfo, and rish. Termux PREFIX directory present. This is command discovery, not execution proof for each command.

## TAPI-001B: functional battery API
Owner reported termux-battery-status exit 0, JSON fields charge_counter, current, current_average, cycle, health, level, percentage, plugged, present, scale, status, technology, temperature, voltage. Required percentage, status, temperature present; schema valid; GATE PASS.

## TAPI-001C: repeated sampling and failure controls
Three termux-battery-status calls, each exit 0 and valid JSON schema. Malformed JSON rejected; nonexistent command raised FileNotFoundError. All three checks true; GATE PASS.

## Limitations
No independently authenticated telemetry or sensor accuracy verification, no thermal stress, prolonged availability, permission matrix, sensor sampling, rish privilege test, or fail-closed authorization integration. No location or telephony data read. No native OSS-Fuzz, Atheris, or Inspect AI result is implied.

## Decision
TAPI-001 scoped pilot PASS, owner-reported. Five-tool intake experiments completed within limited scopes; further integration and independent validation remain OPEN.
