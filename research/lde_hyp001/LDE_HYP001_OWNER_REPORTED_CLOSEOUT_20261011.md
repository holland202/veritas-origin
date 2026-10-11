# LDE-HYP-001 — Owner-reported local closeout (2026-10-11)

**Status:** Local test evidence hash-verified by owner; independent reproduction NOT performed. This record is a summary, not an archive of the executable runner or results JSON.

## Source and environment
- LDE source: `https://codeberg.org/badatchess/local-discovery-engine`
- Frozen revision: `f979705293849de48e4b40aa8988c046fa5871da` (owner reported matching HEAD)
- Device: Android ARM64 Termux; Hypothesis 6.155.7 in isolated `~/venvs/hyp001` environment.
- Frozen LDE source not intentionally modified. Known pre-existing untracked file `azure_environment.txt` left untouched.

## Owner-reported results
- HYP-001A: 6/6 deterministic ranking checks PASS, including detection of an ascending-sort mutant.
- HYP-001B: 8/8 blackboard selection integration checks PASS; additional empty-board smoke test PASS.
- HYP-001C: 100 Hypothesis-generated ranking examples PASS; one fixed ascending-order mutant detected.
- HYP-001D: 100 generated stable-tie/insertion-order examples PASS.
- HYP-001E: 100 generated duplicate-ID rejection examples PASS; malformed inputs NOT tested.
- HYP-001F: 100 generated urgency/cost metamorphic examples PASS.
- HYP-001G: one fixed ranking mutant detected (1/1); Hypothesis shrinking NOT tested.
- HYP-001H: local JSON serialization digest repeatability and single-byte tamper check PASS; cross-substrate reproduction NOT tested. Local payload digest: `a240aeccc58882e181ed2bf7d5ee39f15c6c4ae9202de3a8a0f2a0d00bf440e4`.

## Owner-reported artifact provenance
- Runner path on device: `~/lde-hyp001-batch/run.py`
- Runner SHA-256: `4a0a5a5be3d7ae6ef88a4afc2a510fe0b443d34912cbc00b854c1dcfac3fe367`
- Result path on device: `~/lde-hyp001-batch/results.json`
- Result SHA-256: `ae77224417b352079d5c62c4dca352597fb31b9bd73a54298d32949388520a05`
- Owner's local read-only verification returned both `HASH_MATCH=True`, each D/E/F `examples=100`, all five D–H groups PASS, and `GATE=EVIDENCE_VERIFIED`.

## Claim boundaries and follow-up
- These tests assess implementation consistency with the documented scoring heuristic, not scientific optimality or world truth.
- No previously unknown LDE defect reported from these runs.
- Native Atheris, OSS-Fuzz, and Inspect AI are not established by this LDE experiment.
- The runner and results JSON remain on the owner's device and are **not attached to this GitHub note**. Their bytes, source integrity, and reproducibility have **not** been independently checked by the author of this note.
- Remaining: archive exact runner and results; review malformed-input contract; validate shrinking with a planted defect; expand mutation controls; reproduce independently on Azure or another substrate.
- No changes authorized to frozen LDE source or DPC-001 checker/spec.
