# VEC-001 — registered fixture results and negative findings

**Status:** `VISIBLE_DEVELOPER_FIXTURES_PASSED / SELF_TESTED / NOT_INDEPENDENTLY_VALIDATED / NOT_DEPLOYED`
**Registration:** `VEC001_PREREG.md`, first committed `b513e4ae19c873303dd7899824f1bb449aa78c90` before code or test script.
**Code under test:** `vec001.py`, committed after registration; this report refers to PR #30 branch head `ac183c939888535f1a7c4fef4e7d167469fc4b5a`. No frozen v0.2 files changed.

## Execution 1 — failed before fixtures (preserved)

- GitHub Actions run: https://github.com/holland202/veritas-origin/actions/runs/38107053357
- Job: `114374668892`; outcome **FAIL**, shell exit **1**.
- Substrate: Ubuntu 24.04.5, Python 3.11.17 x86_64, cryptography==46.0.4 successfully installed.
- Error: `ModuleNotFoundError: No module named 'vec001'` at `test_vec001.py:19`.
- Reason: `python -I` excludes the source script directory from `sys.path`. **ZERO P0/P1/N01–N19 cases executed.** This is a runner integration fault, not evidence that the verifier rejected or accepted anything.
- Change made afterward, strictly in test runner: `ac183c939888535f1a7c4fef4e7d167469fc4b5a` explicitly inserts the checked-out local test directory to allow importing the exact `vec001.py` under `-I`. The verifier source, preregistered fixture predictions and test mutations stayed unchanged.

## Execution 2 — all visible, preregistered cases matched

- GitHub Actions run: https://github.com/holland202/veritas-origin/actions/runs/38107086671
- Job: `114374769109`; outcome **SUCCESS**, shell exit **0**.
- Substrate: Ubuntu 24.04.5, CPython 3.11.17 x86_64, `cryptography==46.0.4`.
- Command: `python -I test_vec001.py` within `research/evidence_circuit`.
- Reported program verdict: `VERDICT PASS   matched 21/21 registered cases`.
- P0 and P1: `BINDING_VERIFIED/BOUND_FINITE_SET_MATCHES`, `execution=False`.
- N01–N19: 19/19 `REFUSED` with registered reason codes, `execution=False`.
- P0 finite maximum=5, threshold=6, so observed finite list **does not reach** the threshold. P1 manufactured values have finite maximum=8, threshold=6, so the **synthetic list** reaches the threshold. P1 proves no fact about real measurements; valid signatures did not certify any such measurement.
- Control pairing prevents vacuous refuse-all success, and N14 supplies a properly **re-signed** artifact whose arithmetic is inconsistent. At this visible fixture scope, both mechanisms were exercised.

## Limits and open evaluation questions

1. **Not independent.** ChatGPT wrote specification, verifier, fixtures and result interpretation; one GitHub runner check is execution evidence on a distinct substrate, not independent authorship or correctness verification.
2. **N06 coverage nuance:** the test changes `payloadType` to a disallowed type. The adapter refuses at the application type check **before** signature verification. Thus N06 demonstrates type rejection but **does not independently prove DSSE PAE protects valid type substitution**. A separate positive/negative protocol-level vector suite and independent DSSE test vectors remain needed. Do not claim N06 exercised the signature verification path.
3. **Standards subset:** a single application predicate/subject/signature, closed application JSON, local Ed25519 key map. It is **not** a general in-toto or Sigstore verifier; local additional-key rejection differs from in-toto extension parsing behavior.
4. **Scientific support:** finite max over *observed* values cannot prove max achievable, unbiased sampling, independent calibration or truth of a signed statement. `BINDING_VERIFIED` is not a study `READY` label and never authorizes an action.
5. **Threats not tested:** hostile arbitrary Python object types, exhaustion/very large JSON nested structures, key theft, compromised trust roots, malicious reviewer, collusion, revocation, clock spoofing, signed rollback, conflicting evidence and real execution bypass.
6. **Portability:** Python 3.11 x86_64 Linux only in this recorded run; S25 aarch64/Termux, Android, hardware security, and offline operational workflows **NOT VALIDATED**.
7. **Source authenticity:** neither OpenAI/Anthropic research papers nor public repositories confer validation. They are design inputs, not a trusted oracle. No privileged or private institutional data was used.

## Promotion decision

**HOLD / EXPERIMENTAL.** Keep PR #30 draft pending independent cryptographic/protocol-level negative vectors, separate provenance checks, resource limits and evidence-to-action architecture review. Preserve both workflow executions (including the failed one). Do not merge this prototype as an authority-enforcing component on the strength of these self-tests alone.
