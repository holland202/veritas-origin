# TSP-001 — GitHub CI evidence and first scoped disposition

**State:** `VISIBLE_SYNTHETIC_TEST_PASS / LIVE_LINUX_OBSERVATION_OK / S25_NOT_RUN / NOT_INDEPENDENTLY_VALIDATED / UNMERGED`.
**Preregistration:** `TSP001_PREREG.md` committed `5934b273c2b2900fbaf607cdbbe4f99574b2e330` before code `80612541fa5f22f0cd4f3e03fda0f4db4b47a8ea`; same registered predictions; the synthetic test runner's missing-binary fixture was corrected **before first execution** at `3427f17ad9f753ba394829ee57886eaa51746943`.
**Workflow:** [GitHub Actions 38135634082](https://github.com/holland202/veritas-origin/actions/runs/38135634082), job `114458799987`, concluded **SUCCESS**.
**Substrate:** GitHub-hosted Ubuntu 24.04 Linux x86_64, CPython 3.11.17, source branch `experiment/termux-substrate-intake-20261011`.

## Observed outcomes (first actual run)

1. `python -I research/mobile_substrate/test_tsp001.py`: **Ran 18 tests in 0.003s — OK**. Registered P00, P01 and N01–N16 each returned the expected model-data classifications.
2. `python -I research/mobile_substrate/substrate_probe.py`: successful live **observation-only** report (not an evaluation of action security). GitHub runner indicated Linux x86_64; no untrusted raw `/proc` text or secret env values were printed. The report includes a SHA-256 **fingerprint, not a signature**.
3. `python -I research/mobile_substrate/substrate_probe.py --require execution`: reported `DEFER_UNVERIFIED`, `execution_authorized: false`, exited **2**. The workflow checks for exactly that exit code and passed.
4. No test launched an Android API, scheduler, Tasker task, OS seccomp/Landlock filter, shell-executed agent command, vehicle action or actual constrained agent.

## Remaining barriers

- The Android/Termux case is **synthetic injected data only**. A Linux CI pass does not establish the S25's exact Seccomp, Landlock, cgroup controller, temperature, API permission, key store or process limits.
- The read-only probe does not install or verify controls. `Seccomp:2` measured on the *observer* does not establish coverage of an AI agent or any action broker.
- A command found via PATH is not a verified Termux:API add-on, permission or reachable service. App plugin signatures require consideration.
- `UNKNOWN` when virtual files are inaccessible is correct and must not be silently promoted to either enforcement success or global feature absence.
- Tests and implementation were authored by the same model. CI is a separate execution environment, **not independent review**.
- The code is reusable as a standalone stdlib module but is **not automatically integrated** into LDE on Codeberg, VEC's attestation verifier, or Sovereign Veritas's maintenance-only runtime.
- Only author-designed input classes were tested, not arbitrary hostile proc file content, stress/fuzzing, Android runtime, or resource-exhaustion impact of repeated probing.

**Disposition:** draft PR #36, do not merge as a production or authorization component. Invite independent negative fixtures. Device follow-on requires explicit owner-run passive command with stdout/exit/environment provenance; make no assumptions about Android based on Ubuntu CI.
