# COLD-REVIEW-001, run 1: null run. No call reached the model. Predictions are not evaluable.

| | |
|---|---|
| Registration | [`PREREG.md`](PREREG.md), commit `3ebcc03`, committed before the run |
| Execution | **One.** Authorized directly by Chad Holland on 2026-10-13. Started 2026-10-13T11:02:24Z |
| Environment | Chad's Samsung Galaxy S25 Ultra, Termux, Python 3.14. Not run in the container |
| Script / prompt | script sha256 `085c53a6…30b7`, prompt sha256 `9102cbd9…fe4e11`, both as registered |
| Evidence | `results/run1/`, unedited. `SHA256SUMS` as printed on the phone |

Written by Claude (Sonnet 5.5), which also wrote the script and the registration, at Chad Holland's direction.
Chad has not reviewed it line by line. Not independent.

## Failures first

- **All 9 calls failed with HTTP 401 `authentication_error: invalid x-api-key`.** No model saw any file. This run
  says nothing about whether a model can find the SV-ATTACK-001 defect.
- **The script printed `VERDICT P1 FAIL  P2 FAIL  P3 FAIL  P4 FAIL`.** That follows the registered rules mechanically
  (P2 and P3 require no failed call, P1 and P4 require HITs or parseable replies), but it is misleading. The right
  label is **INCONCLUSIVE**. The script's verdict code has no case for "no call reached the model". That is a defect
  in my script, not in the experiment's design, and it is kept here as a failure of mine.
- **Cause, as reported from the owner's terminal.** The environment variable that should have held the key held the
  text of a shell command (80 characters, beginning `echo; [`), not a key. The key prompt consumed the next pasted
  line, and the script's only check was "variable is non-empty", which that text passed. The real key was never
  entered. So the API was sent a junk string, which is why it answered 401 and not something worse.
- **The one registered execution is spent.** The script refuses to overwrite `results/run1/`. A second execution
  needs a separate written authorization from the owner. None has been given.

## Results (pasted from `results/run1/run.log`)

```
A#1 http 401 CALL_FAILED findings 0 usage {}
A#2 http 401 CALL_FAILED findings 0 usage {}
A#3 http 401 CALL_FAILED findings 0 usage {}
B#1 http 401 CALL_FAILED findings 0 usage {}
B#2 http 401 CALL_FAILED findings 0 usage {}
B#3 http 401 CALL_FAILED findings 0 usage {}
C#1 http 401 CALL_FAILED findings 0 usage {}
C#2 http 401 CALL_FAILED findings 0 usage {}
C#3 http 401 CALL_FAILED findings 0 usage {}
VERDICT P1 FAIL  P2 FAIL  P3 FAIL  P4 FAIL
```

| ID | Registered prediction | Observed | Reading |
|---|---|---|---|
| P1 | at least 2 of 3 HITs on A | 0 of 3 calls returned a reply | **Not evaluable** (script says FAIL) |
| P2 | 0 HITs on B and no failed call | 3 of 3 failed | **Not evaluable** (script says FAIL) |
| P3 | 0 HITs on C and no failed call | 3 of 3 failed | **Not evaluable** (script says FAIL) |
| P4 | at least 8 of 9 parseable | 0 of 9 | **Not evaluable** (script says FAIL) |
| P5 | not registered, not run | | still the open door |

Raw replies are all of the form `{"type":"error","error":{"type":"authentication_error","message":"invalid x-api-key"}…}`.
The evidence contains no key-like string; a search for `sk-ant` over `results/run1/` finds nothing.

## How the evidence got here

Chad exported `results/run1/` from the phone as a base64 tar archive and pasted it. I rebuilt the files and checked
all 11 against the `SHA256SUMS` printed on the phone: **11 of 11 OK**, and the checksum list itself is identical to
the one he pasted. Files are committed byte-for-byte. A person who wants to confirm can rerun the checksums.

## What it taught

- A check that only asks "is the variable non-empty" is vacuous for a key. The guard needs an expected shape.
- The run-level verdict must separate "the instrument returned a negative" from "the instrument never ran". That is
  the same lesson as the anti-vacuity rule, and the script broke it.
- Both fixes are registered separately in [`AMENDMENT1.md`](AMENDMENT1.md). Neither changes a prediction or a
  scoring rule.

## What this does not establish

Nothing about reviewer quality. Not P1, not P2, not P3. The test is still open and unrun.
