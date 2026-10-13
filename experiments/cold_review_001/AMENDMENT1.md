# COLD-REVIEW-001, Amendment 1: key-shape guard and an INCONCLUSIVE verdict

Registered 2026-10-13, after run 1 and before any second execution. Written by Claude (Sonnet 5.5) at Chad Holland's
direction. Chad has not reviewed it line by line. Not independent.

## Why

[`RESULTS_RUN1.md`](RESULTS_RUN1.md): run 1 made nine calls with a junk string as the key (HTTP 401 on all nine),
and the script printed `P1 FAIL … P4 FAIL` as if a reviewer had been tested.

## What changes (script only)

1. **`key_ok()` guard.** `--run` refuses to start unless the key starts with `sk-ant-`, is at least 40 characters, and
   contains no whitespace or line breaks. It prints the length of what it was given, never the value, and sends
   nothing.
2. **`overall()` verdict.** If no call returns HTTP 200 the run verdict is **INCONCLUSIVE** and the four predictions
   print as `n/a`. If some calls fail it is **PARTIAL**; the registered rules still apply and the failures stay
   visible. Otherwise **EVALUATED**. `summary.json` records the state.
3. **`--run [label]`.** The results folder name is now an argument, default `run1`. A second execution would use
   `--run run2`. The refusal to overwrite an existing folder is unchanged.

## What does not change

The three input files, `prompt.txt`, the request bodies, the model, `max_tokens`, the scoring rule, predictions
P1 to P4 and the unrun P5 are untouched. The dry-run request digests are identical to the registration: A `bf3a66bf…5553`,
B `cadfb7eb…e10b`, C `01ea63d3…7ea5`. Run 1's evidence is not edited.

## Checks (container, 2026-10-13)

- `--selftest` passes with the new cases: six key shapes (including the exact text that was sent in run 1, an empty
  string, a trailing line break, too short, and embedded whitespace) and three verdict cases.
- **Mutant 1**, `key_ok` always returning True: self-test exits 1, five `BAD` lines.
- **Mutant 2**, `overall` never returning INCONCLUSIVE: self-test exits 1, `BAD overall([401, 401, 401]) = EVALUATED`.
- `ANTHROPIC_API_KEY='echo; [ -n x ]' python3 -I cold_review.py --run run2` exits 2 with `REFUSED` and creates no folder.

New script sha256: `635d07fc2f85e97ced2d1d7c239036295ec3b3a91a79c28de96721f871c6163d`.

## Run 2 rules

One execution of nine calls, **only after the owner states in writing that he authorizes it**. Not authorized yet.
If it is authorized: put the key in the shell by running the `read` line **on its own**, paste the key, press Enter,
and only then run the next line. Do not paste two lines together, because the key prompt will take the second line as
the key. Evidence goes in `results/run2/` unedited with `SHA256SUMS`, and run 1 stays as it is.
