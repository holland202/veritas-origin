# DPC-001 v0.2 — Blind Run 2 evidence-status record

Recorded 2026-10-10 as documentation reconciliation, based on owner-run terminal outputs relayed in PR #25. **OWNER-REPORTED / SEALED / NOT INDEPENDENTLY REPRODUCIBLE FROM THIS REPOSITORY.** This is not a new execution, claim of verification, or retroactive modification of the blind test.

## Reported outcome

- Primary-label result: **PASS 24/24**, from Chad's Termux execution (not reproduced for this record).
- Frozen target: `bc43adf3b51633dfb831ce420afe90ec3ac04ab7`.
- Cases commitment: `6ea0e754aa11d2f123c5eaca86ea3e114b48aec75b8d3440cce51acbaf7547e8`; oracle commitment: `e2927f1195ee3f1a6c76391b4bc803b716e5853bc52b62d969af1970479911c6`. These full values were posted before the run in owner-reported [comment 6092201967](https://github.com/holland202/veritas-origin/pull/25#issuecomment-6092201967). The sealed inputs and nonce remain unavailable here.
- Runner SHA-256: `e28f620804ba0a1dc95273c36499382f4bdeb20bacb855c9f9a88a1600fe76ef`, **different from run 1** runner `fce88394…`. The run-2 runner is not committed in PR #25 and its implementation cannot be independently reviewed here.
- Evidence SHA-256: `78bca603554611668443abffefc7f74daf0243ac1b171c14e599565cb2662075`. The owner reported a 4,580-byte result file with mode `0600` at `$HOME/.local/share/veritas-origin/dpc001-v02-blind-run2/evidence/blind_run_v1.json`; the evidence bytes remain unavailable in this repository.
- Owner's pre-seal gate output on first draft: `FAIL  G4 T03: oracle requires STUDY_ID_MISSING but study_id is present`; `PRESEAL_GATE FAIL (1 fail, 0 warn, 24 cases)`.
- Owner's corrected case-set gate output: `PRESEAL_GATE PASS (0 fail, 0 warn, 24 cases)`.
- Reported gate source at commit `45ccccc`: SHA-256 `c407364c990ef819e6ca8937d4395d3f4bc6d36bef8ac25210776d02bf24cdd6`; owner reportedly matched both copies.
- The failed draft is preserved in the owner's private run-2 folder per [FINDING_M1.md](../FINDING_M1.md); this PR does not contain it.

## Provenance and time ordering

Owner outputs were relayed in [PR #25 comment 6092201967](https://github.com/holland202/veritas-origin/pull/25#issuecomment-6092201967) at **2026-10-10 01:30:43 UTC**, and [comment 6092240694](https://github.com/holland202/veritas-origin/pull/25#issuecomment-6092240694) at **01:35:27 UTC**. These are comment posting times, not independently established local execution timestamps. The commitment was posted before the result. See [pre-merge review, note 050](https://github.com/holland202/veritas-origin/pull/25#issuecomment-6097051085) for the evidence inventory and provenance assessment.

## What would be required for independent reconciliation

With separate owner authorization and access to the actual bytes: recover the sealed run-2 cases, oracle, nonce/manifest, runner and result, compare full file hashes/commitments against the posted pre-run commitment, check timestamps and runner code, hash-check the two frozen files, and rescore once against frozen `bc43adf`. Until then, **do not upgrade owner-reported PASS to independently verified PASS**. Do not rerun or unseal as a consequence of this record alone.

## Negative findings preserved

Run 1 **FAIL 23/24** remains independently recorded at [../blind_run_1/evidence/blind_run_v1.json](../blind_run_1/evidence/blind_run_v1.json). The pre-seal gate's detection of the run-2 authoring error is one observed process result, not evidence of a general interception rate or of factual correctness of the checker.
