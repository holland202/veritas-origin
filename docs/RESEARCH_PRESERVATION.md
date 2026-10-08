# Research preservation policy (RA-001)

**Status:** Proposed enforceable repo checks + human governance; **NOT PRODUCTION SECURITY**.

VERITAS ORIGIN is a research archive, not a rolling leaderboard. The following controls preserve negative findings and distinguish what records establish.

## Rules

1. Original **evidence**, preregistrations, historical source snapshots, standalone verifiers, and dated reports never change in place once frozen. A Git commit plus recorded content digest is the initial identity.
2. An error is corrected by creating a **new** `corrections/<ID>.json` and accompanying report, citing original path, SHA-256/Git blob SHA-1, exact source/protocol revisions, reason, new record SHA, author and date. Do not delete or alter the original. Any changed interpretation keeps the old claim visible and states the cause.
3. Failure, timeout, interruption, invalid/contaminated run, vacuous check, and negative outcome all receive explicit statuses. No silent deletion, cherry-picking, or rewriting a preregistration to match results.
4. Research records retain source commit, protocol ref/hash, evaluator identity/revision, exact parameters/seeds, environment, generated inputs, outputs, explicit evidence state, cost measurements if present, and data hashes. If unavailable, write `UNKNOWN` rather than making up a value.
5. Research candidates are `PROPOSED` → `FROZEN` → `EVALUATED` → `REVIEW_REQUIRED`. Human approval requires **independent authorization** and a fresh exact-hash match; publication/deployment does not follow automatically from successful verification.
6. A published mirror is identified by exact source revision and manifest hash. `SIGNED`, `CONSISTENT`, and `LATEST_WITNESSED` have different meanings, as demonstrated by [Sovereign Veritas](https://github.com/holland202/sovereign-veritas).
7. VSC-001, VSC-002 and VSC-003 remain **draft branch** studies, not assumed part of GitHub `main`. Their public-fixture artifacts have retention limits; publishing follow-up work does not convert their original results into confirmation.

## Existing immutable baseline (current historical release)

At the RA-001 registration, `main` = `2131d9166deea94811155a746e57fb597491f53a`. An independent code pinning file binds the Git blob IDs of all historical records listed below, plus SHA-256 where independently recorded.

- `evidence/pilot-20261008T191115896136Z-e361d9a5.json` (pilot)
- `evidence/exp002/exp002-20261008T194950169959Z-fccc3f26.json`
- `evidence/exp003/exp003-p0-20261008T202705724022Z-146bee1a.json`
- `experiments/exp002/PREREG.md`, `experiments/exp003/PROTOCOL_P0.md` and `experiments/exp003/THREAT_MODEL_P0.md`
- `reports/exp002/EXP002_VERIFICATION.md` and `reports/exp003/EXP003_P0_AZURE_PILOT.md`
- `src/origin/exp003.py`, `tools/verify_exp002.py`, `tools/verify_exp003_p0.py`

These original files are *never* replaced by RA-001. New versions should live in new paths with separate registries.

## What CI can and cannot enforce

`python3 tools/research_assurance.py` recomputes pinned identities and EXP003-P0 outcome counts. It exits nonzero for original-file tampering, deletion and claim misclassification. Tests mutate temporary records to prove specific checks can fail.

However, **GitHub `main` was observed unprotected**, with zero rulesets. An administrator or an attacker with suitable write authority could rewrite the guard and its pins. CI itself is not a trust anchor. A separate GitHub repository ruleset, restricted bypass and human reviews are needed for tamper-evidence to survive changes to the checker. Protected-branch history and signatures can raise assurance but still do not guarantee world truth.

### Human owner action — GitHub settings

After the CI job exists, visit [repository settings → Rules → Rulesets](https://github.com/holland202/veritas-origin/settings/rules) to protect `main`. Block force pushes and deletion; require PRs and the specific passing research-assurance status; limit bypass. Add independent human review when collaborators can genuinely provide it. If an approval rule would make solo development impossible, disclose the lack of a separate reviewer instead of manufacturing an approval. Also prevent removal of the CI policy without review.

**Current status: RULESET NOT APPLIED BY RA-001.** The connected GitHub tool cannot mutate protection settings.

## Maintenance of negative outcomes

An adverse result is data, not a failed collaboration. The system must never silently promote `EXPLORATORY` to `CONFIRMATORY`, `CONSISTENT` to `TRUE`, or `SUPPORTED` to `AUTHORIZED`. A legitimate correction adds a linked record and retains the original for independent comparison.
