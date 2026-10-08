# C1-001 — Measured Linux evaluator/proposer DAC boundary

**Recorded result:** `PARTIAL_DAC_DEMONSTRATED_NOT_SANDBOXED`. On one GitHub-hosted Ubuntu 24.04 Linux runner, a known honest proposer under a separate non-root UID successfully interrogated an evaluator through a bounded AF_UNIX protocol while direct reads of private answer material and an unauthorized peer-UID socket access were denied. This is **not** a complete agent sandbox, real LLM evaluation or independent scientific replication.

## Preregistration, lineage and design controls

- Frozen prospective test protocol: [`experiments/c1001/PROTOCOL.md`](../../experiments/c1001/PROTOCOL.md), first commit `b5fc90b960a3796f7421ffe85022e332add51824`, before any C1-001 implementation or run.
- Base: EBA-001 draft PR #11, commit `a80948d76fb289c9a7d381d09546749af8c111cb`. It is itself based on RA-001 draft PR #10. Original EXP003-P0 and EBA-001 evidence remain unchanged.
- Tested code: [Linux evaluator](../../experiments/c1001/evaluator.py), [known restricted-UID proposer](../../experiments/c1001/proposer.py), [live Linux controller](../../experiments/c1001/run_linux_smoke.py), [separate mathematical receipt verifier](../../tools/verify_c1001.py), [29 independent replay/protocol controls](../../tests/test_c1001.py).
- Two security mechanisms are explicitly distinct:
  1. **Linux DAC / Unix credentials** provide an actual OS-backed negative-control result for designated files and users.
  2. **Protocol parser / mathematical verifier** reject illegitimate requests and inconsistent receipts, but cannot establish OS capability restrictions.
- An evaluator-private random 32-byte salt binds the disclosed truth/identity in a SHA-256 commitment. The salt and actual true predicate are **not** in the proposer-visible protocol. The root test harness discloses them only **after** the known proposer has finished.
- No network model calls, paid APIs, cloud training, outside security targets, real secrets, or untrusted-model commands were used.

## Registered controls: actual result

| Control | Mechanism under test | Outcome on GitHub CI |
|---|---|---|
| P0 | Legal HELLO / unique probe exchange from UID 32002 | **COMPLETED** a fresh randomized task, within 6 legal probes |
| N1 | UID 32002 attempts read of evaluator UID 32001 private answer file | **EACCES**, Linux access denied |
| N2 | UID 32002 attempts read of evaluator-only 0700 directory | **EACCES** |
| N3 | Proposer tries unsupported actions `GET_SECRET`, `READ_FILE` | **SCHEMA_DENIED** |
| N4 | UID 32004, deliberately same socket group GID 32003, tries connection | **UNAUTHORIZED_PEER** via `SO_PEERCRED` |
| N5 | Duplicate, Boolean and invalid probe values | **DENIED** |
| N6 | Forged `truth`/`approval` command fields | **SCHEMA_DENIED** |
| N7 | Rehashed forged outcome, commitment or scope mutation | **REJECTED** by separate mathematical verifier |
| N8 | Missing history, duplicate JSON keys, nonfinite numbers | **REJECTED** |
| N9 | Proposer self-reported clean access log | **NOT ACCEPTED AS ISOLATION PROOF** |
| N10 | Wrong UID, wrong directory/socket mode, unsupported Linux prerequisites | **FAIL-CLOSED SETUP**, demonstrated in unit tests / provisioning checks |

**Anti-vacuity:** a legitimate proposer session and receipt replay succeeded. The verifier did not indiscriminately refuse all inputs, and denials did not prevent legal probes.

## GitHub evidence and measured scope

- **Passing integration workflow:** [Actions run 37861793489](https://github.com/holland202/veritas-origin/actions/runs/37861793489), completed October 8, 2026.
- **Passing tests:** existing EXP003 **17/17**, RA-001 **28/28**, EBA-001 **24/24**, new C1-001 **29/29** = **98/98**.
- **Live Linux integration:** runner reported `private_file: EACCES`, `unauthorized_socket: DENIED`, `honest_completion: true`, `replay: CONSISTENT`, `scope: PARTIAL_DAC_DEMONSTRATED_NOT_SANDBOXED`.
- **Actual receipt SHA-256:** `ea60a6cc2a83a7be47e5596e4f89e9ee5231518b06e1d700a28dc8f10bca9b2e`.
- **Original post-session receipt and OS-control report:** [artifact 11585724715](https://github.com/holland202/veritas-origin/actions/runs/37861793489/artifacts/11585724715), expected 30-day retention. The receipt includes the fully disclosed *synthetic* true predicate and random salt for independent replay; it is safe to share only because the study has ended.
- Historical EXP003-P0 original still verified at hash `627eb778e8eef80d9d664c9ac6f3b7743d51e6a97a677eea8cac51e79b467333`; no mutation or deletion.

The evaluator writes its private receipt before root reads it. The mathematical verifier replays the salt commitment and all reported transitions without importing the evaluator. However, **neither the local root controller nor the evaluator is a trusted third party**: they could fabricate a self-consistent transcript. The CI job's checked process exit codes and restricted UID execution offer distinct engineering evidence, not a cryptographically independent attestation or a guarantee under root compromise.

## Development failures retained, not reclassified

Three GitHub Action attempts failed **before** the full OS integration succeeded:

1. [Run 37861652774](https://github.com/holland202/veritas-origin/actions/runs/37861652774): 1 of 29 new unit tests failed due to a false-positive source-text search matching the independent verifier's docstring, not an actual import. Changed to a Python AST import check; original failure retained.
2. [Run 37861692397](https://github.com/holland202/veritas-origin/actions/runs/37861692397): all 98 unit tests passed, but the evaluator's process could not read its program from GitHub's checkout directory after dropping to UID 32001. Instead of weakening permissions, the launcher began staging **only reviewed public scripts** under a temporary 0755 program directory.
3. [Run 37861755910](https://github.com/holland202/veritas-origin/actions/runs/37861755910): all 98 unit tests passed, but the restricted proposer still referenced the inaccessible checkout path. The last program path was corrected in an additional commit.
4. [Run 37861793489](https://github.com/holland202/veritas-origin/actions/runs/37861793489): **all 98 tests and actual OS controls passed**. The previous failures remain visible in GitHub Actions; nothing was rewritten or claimed to have passed retrospectively.

These are engineering and environment integration defects, not automatically research hypotheses confirmed or refuted.

## Security interpretation: strongest supported claim

<escape>**SUPPORTED IN THIS CI ENVIRONMENT:** Linux discretionary file permissions denied a known restricted process's read of evaluator-only task material; the kernel's Unix-socket peer identity rejected a separate UID; a legal responder succeeded; and a separately written mathematical verifier checked the disclosed synthetic transcript.</escape>

**NOT ESTABLISHED:** containment of arbitrary hostile Python, privileged escalation resistance, cross-user ptrace behavior, kernel/proc mount isolation, process namespace separation, network egress restriction, resource-exhaustion limits, covert-channel detection, independent access telemetry under root compromise, protection against leaking sensitive information in model-visible text, secure external attestation, real model generalization, human publication authorization, or applicability to Android/Termux.

**Residual EBA-001 failure:** An adversary could forge a complete, clean self-reported log. This experiment reduces the scope of trust by using Linux-enforced file ownership and kernel-reported peer UID for specific controls; it does **not** eliminate false-clean attestations from uninstrumented channels. Security approval must never rely solely on the proposer's declaration.

## Relationship to Sovereign Veritas and research integrity

The MIT Sovereign Veritas Gate continues to assess proposed actions from **supplied evidence/capability/policy/runtime** under `sv.gate/0`. C1-001 does not edit the Gate or its conformance vectors; RA-001's bridge continues to generate **unauthorized publication intents**. A successful probe session is evidence of the bounded DAC test only, **not an authorization to deploy or publish an unreviewed scientific claim**.

## Next research threshold — do not promote prematurely

Before attempting real autonomous or externally powered proposers: review a narrower executable sandbox (user namespace/container, read-only filesystem, no network, resource limits), independent event collection, authenticated immutable receipts and an evaluator that holds genuinely secret tasks across repeat trials. A known test executable is not adequate evidence for containing malicious code. Preserve P0, EBA-001 and this first C1 result as distinct records with their original digests.

**GitHub main still needs a branch ruleset** to prevent force-push/deletion and require trusted CI checks. CI itself is not an immutable authority when an administrator can edit both source and pins. This branch remains draft and shall not merge automatically.
