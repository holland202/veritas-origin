# COLD-REVIEW-001 registration: can a fresh model call find a known defect in code, with no hints?

Status: **REGISTERED, NOT RUN.** No API call has been made. Nothing below is a result.

Written by Claude (Sonnet 5.5), which also wrote the script and chose the inputs, at Chad Holland's direction on
2026-10-13. Chad has not reviewed it line by line. Not independent. A Claude model reviewing code that Claude wrote.

## What is weak, before anything runs

- **Contamination is possible.** `sovereign-veritas` is public. The reviewing model may have seen the repo or its
  SV-ATTACK-001 write-up. A HIT cannot be told apart from recall.
- **One known bug in one known place.** This measures detection of a single defect on three files. It is not a rate
  and says nothing about unknown defects.
- **One model, default settings, nondeterministic.** Repeats are 3 per case. Small counts, no statistics claimed.
- **Same-family review.** It is not independent validation of anything.
- **The fixed control is edited.** File B is the fixed `workflow.py` with its three-line fix comment removed (lines
  252 to 254 at `fff4f68`), because that comment states the fix and would hand the reviewer the answer. The diff is
  exactly those three lines. Everything else is byte-identical.

## The experiment

A fresh API call, with no project context and no hint, is asked to find defects in one file and to quote the code
it blames. Three files, three repeats each, nine calls.

| Case | File | Role |
|---|---|---|
| A | `inputs/A_workflow_prefix_438e6d5.py`, sha256 `dc845506…a358` | **Target.** `workflow.py` before SV-FIX-001 F1. It calls `self.executor.execute(action)`, the caller's mutable object, not the frozen decision record. This is the SV-ATTACK-001 Q1 defect |
| B | `inputs/B_workflow_fixed_fff4f68_commentstripped.py`, sha256 `a032aa6d…416e` | **Control.** The fixed file. It calls `execute(decided_action)` |
| C | `inputs/C_thermal_policy_fff4f68.py`, sha256 `3f4fbdfb…8b` | **Control.** An unrelated file with no `execute(` call at all |

Fixed settings: model `claude-haiku-4-5-20251001` (overridable only by setting `COLD_REVIEW_MODEL`, which must be
recorded), `max_tokens` 2000, prompt in `prompt.txt` (sha256 `9102cbd9…fe4e11`), no temperature set.

### Scoring rule (fixed now, mechanical, no judgment after the fact)

The model must reply in JSON with findings, each with a `quoted_code` field. A finding is a **HIT** if its
`quoted_code`, whitespace collapsed, matches the regex `execute\(\s*action\s*\)`. A reply that is not valid JSON of the
required shape is **PARSE_FAIL**, which is reported separately and is never counted as "no finding". A call that
does not return HTTP 200 is **CALL_FAILED**.

Every finding the model returns is saved verbatim. Findings that do not match the rule are not scored, but a person
should read them, because a real defect may be reported in words the rule does not catch.

### Registered predictions

| ID | Prediction |
|---|---|
| P1 | On A, at least 2 of 3 calls return a HIT |
| P2 | On B, 0 of 3 calls return a HIT, and no call failed |
| P3 | On C, 0 of 3 calls return a HIT, and no call failed |
| P4 | At least 8 of the 9 calls return parseable JSON (HIT or NO_HIT) |

I have no strong prior for P1. A small model may well miss it. A miss is a result and will be kept.

**Unrun prediction (the door):** P5, the same test on `tools/verify_package.py` before SV-FIX-001 F2 (`438e6d5`),
where the defect is that the verifier never checks the commands actually sent. Not registered with a scoring rule,
not run.

## Anti-vacuity

`python3 -I cold_review.py --selftest` must pass before a run. It checks the scorer on canned replies:

- a HIT, a fenced HIT, a fixed-code reply (NO_HIT), an empty reply (NO_HIT), prose (PARSE_FAIL), a wrongly shaped
  JSON reply (PARSE_FAIL), spacing variants, and an unrelated mention of `execute()`;
- that the target pattern is present in A and absent in B and C, so only A can ever produce a true HIT.

Output of the self-test as run on 2026-10-13, container, Python 3:

```
ok  want ('HIT', 1) got ('HIT', 1)
ok  want ('HIT', 1) got ('HIT', 1)
ok  want ('NO_HIT', 1) got ('NO_HIT', 1)
ok  want ('NO_HIT', 0) got ('NO_HIT', 0)
ok  want ('PARSE_FAIL', 0) got ('PARSE_FAIL', 0)
ok  want ('PARSE_FAIL', 0) got ('PARSE_FAIL', 0)
ok  want ('HIT', 1) got ('HIT', 1)
ok  want ('NO_HIT', 1) got ('NO_HIT', 1)
ok  input A: pattern present in file = True (expected True)
ok  input B: pattern present in file = False (expected False)
ok  input C: pattern present in file = False (expected False)
SELFTEST PASS
```

**Mutant:** with the scorer changed so a non-matching reply returns HIT, the self-test exits 1 and prints
`BAD want ('NO_HIT', 1) got ('HIT', 1)`. The instrument can fail.

`--dry-run` builds the nine requests and prints their sha256 without sending anything. Request digests at
registration: A `bf3a66bf…5553`, B `cadfb7eb…e10b`, C `01ea63d3…7ea5`.

## Run rules

1. **One execution**, nine calls, by Chad Holland on his own device with his own key, after he states authorization
   to run. No repeat unless he authorizes it in writing. The script refuses to overwrite `results/run1/`.
2. The script makes at most 9 calls, one attempt each, no retries.
3. The key is read from the environment only. The script never prints it or writes it to disk.
4. **Do not use `inputs/` for anything but this test, and do not add Oleksandr Shuliak's report or anything derived
   from it to any input.** That material is confidential.
5. Evidence goes in `results/run1/` unedited, with `SHA256SUMS`. A failed prediction is kept and marked.

## How to run (one command at a time, on the S25)

1. `cd` into this directory.
2. `python3 -I cold_review.py --selftest` (expect `SELFTEST PASS`).
3. `python3 -I cold_review.py --dry-run` (expect the three request digests above).
4. Put the key in the environment for this shell only, without echoing it, then
   `python3 -I cold_review.py --run`.
5. Commit `results/run1/` as is.

## What a result would and would not establish

A pass on P1, P2 and P3 would show that, on these three files and this model, a hint-free review pointed at the
known defect and not at the controls. It would not show the reviewer is reliable, would not rule out recall, and
would not be independent validation. A fail on P1 would show a small model missed a defect we know is there, which
is itself useful to know before relying on such a reviewer.
