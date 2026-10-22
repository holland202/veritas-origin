# EXP003-P1 — Threat model, attack surface and blocked claims

**Status:** OPEN SECURITY / VALIDITY GAPS. This document records untested assumptions; it does not assert that attacks were demonstrated or mitigated.

## Boundary inventory

| Boundary | Implemented | What remains unproven |
|---|---|---|
| JSON proposer payload omits evaluator secret and hidden truth | Yes, tested syntactically | An external process may still access operating-system resources, source code, logs and parent process state |
| Secret-salted response matrix and independent truth selection | Yes, deterministic replay tests | Whether candidate matrix allows side-channel inference or held-out leakage through host access |
| Reject invalid/duplicate/repeated model probes | Yes, tested with representative negative cases | Exhaustive parser hardening, resource exhaustion, subprocess descendant cancellation |
| Independent consistency replay, adversarial rehash mutations | Yes, 14 verifier tests | Authentication, independent experimental truth, evaluator/model isolation, malicious dual rewrite |
| Bounded task and probe counts; per-proposal wall timeout | Yes | Total campaign cost, peak RAM/CPU, network egress, process tree lifetime and token budgets |
| Genuine local/remote LLM hypothesis proposer | No | No model artifacts, inference hash, token/latency results or comparison established |

## T1: Host oracle access — HIGH, OPEN

The external command is executed with the evaluator's OS user privileges. Not including `truth` and `evaluator_secret_hex` in the proposal JSON reduces direct leakage but **does not** create a confidentiality boundary. A process with access to evaluator files, process APIs, interpreter state or preserved evidence may be able to recover the oracle.

**Required before held-out model claims:** separate evaluator host or hardened isolated identity with tested filesystem, process and network boundaries; evaluator secrets stored outside model privilege domain; challenge committed before outcome inspection; concrete adversarial probes run and archived.

## T2: Resource exhaustion — HIGH, OPEN

`subprocess.run(capture_output=True, timeout=...)` buffers stdout and stderr in memory before the post-exit 4,096-character stdout check. A malicious or defective proposer could exhaust memory before the check, spawn descendants, or consume network/remote credits not charged against an enforced global budget.

**Required before untrusted execution:** operating-system resource limits or cgroups, bounded streaming I/O, process-group cancellation, deny-by-default network access, total experiment budget, and negative tests.

## T3: Research validity and benchmark leakage — HIGH, OPEN

16 synthetic 24-bit vectors are not scientific hypotheses about the real world. A public test secret, once revealed, is **not held out**. The generated task space may still be trivially separable, and one-step greedy is an intentionally strong baseline. A language model's selection score alone does not show hypothesis generation, novelty, causality, understanding or autonomous discovery.

**Required:** separate preregistered C1 with withheld evaluation generator, task difficulty diagnostics and optimal/greedy controls, pinned model and decoding, cost-per-correct-task, failure accounting, held-out replication and preserved negative results.

## T4: Recorded bytes versus independent truth — MEDIUM, OPEN

Independent replay proves agreement with the published generator and trajectory rules, assuming trusted verifier source and pinned hash. It does not authenticate who ran the experiment, prove the environment was isolated, or prove that real-world observations matched simulated outcomes. Once exposed, the secret can be used to regenerate a consistent artifact; hashes alone do not disprove malicious wholesale regeneration.

**Required:** separate evidence provenance, independently controlled attestation where warranted, witnessable run commitments, verifier diversity, and audit of both positive and negative trials.

## T5: Authorization and policy — HIGH, OPEN

P1's `--pilot` flag, choice validation, and explicit acknowledgement gate are input controls, not a hardened AI permission system. The separate Sovereign Veritas Gate is **not integrated or tested** here. No permission or production safety claim follows from P1's test suite.

**Disposition:** P1 source may be evaluated as an exploratory software substrate. Model execution under the current shared-account subprocess is not approved for safety or confirmatory claims merely because unit tests pass.

**Evidence classifications:** `EXPLORATORY_SIMULATED` = synthetic pilot; `CONSISTENT` = internal specification checks; `NOT VALIDATED` = external model isolation, real-world truth and scientific generalization unproven.
