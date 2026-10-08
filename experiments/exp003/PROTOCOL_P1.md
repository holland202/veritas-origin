# EXP003-P1 — Blinded-oracle exploratory substrate protocol

**Status: PROSPECTIVE EXPLORATORY ENGINEERING PROTOCOL — NOT CONFIRMATORY, NOT VALIDATED.**

This document is written after EXP003-P0's documented 100% completion ceiling and before P1 pilot results. P0's frozen evidence and negative limits are immutable. Do not rename P0 outcomes or treat P1 pilot performance as preregistered confirmation.

## Question and falsification target

**Question:** Can an experiment proposer discriminate a hidden hypothesis from 16 distinct binary hypotheses on a 24-probe synthetic domain within at most five observations? How do fixed, random, one-step greedy information gain, and an explicitly configured trusted model proposer compare?

**Primary *descriptive* pilot measurements:** tasks solved by budget; mean probes executed per task; mean terminal candidate count; deferred/invalid proposal rate. Hypothesis rows, truth, probe transcript and policy identity must be recoverable for audit. Report *all* baselines including failures. Compute paired comparisons by task, not just aggregated reward.

**No victory criterion is preregistered for P1**: because it is exploratory engineering. A later C1 preregistration must freeze distributions, held-out task count, primary endpoint, error handling, baseline superiority threshold, analysis code, inference configuration, and disclosure of negative evidence **before** outcome observation.

## Task design and surprise separation

- 16 candidate hypotheses H00..H15; 24 possible binary tests indexed 0..23; at most 5 tests per task.
- Every hypothesis has a 24-bit response vector, generated from a 256-bit secret using SHA-256 domain-separated counters; duplicate vectors are rejected and regenerated deterministically with increasing retry counter. A separate SHA-256 domain chooses the hidden truth.
- The default pilot secret is created by `secrets.token_hex(32)`. It is **not included in external proposer messages**. The matrix of candidate responses is shown; this is necessary for informed experimental design. A public hypothesis matrix alone does not disclose the separately selected truth.
- Secret, hidden truth, raw observations and decisions are recorded in the final evidence **after** the pilot. The secret becomes public after archival, so do **not reuse** that task instance as held-out model evaluation material. For test reproducibility, a deliberately fixed `--test-secret-hex` is allowed only with an explicit `--allow-public-test-secret`; the resulting artifact is labeled `PUBLIC_TEST_SECRET`.
- The evaluator and proposer currently run on the same operating-system identity when the optional external adapter is enabled. The secrecy of the challenge before and during the run is **not secured against filesystem/process inspection by the proposer**. True oracle blinding is **UNMET** until separated user accounts/containers/hosts and explicit egress controls are tested. Merely hiding the secret in JSON is not a sandbox.

## Policies

1. `fixed`: earliest unused probe index.
2. `random`: domain-separated SHA-256 draw using evaluator secret, task index and decision index to select an unused probe; independent of the truth domain.
3. `greedy`: choose a probe maximizing `n^2 - sum(outcome_bin_size^2)`, tied by smallest index. A strong one-step information-gain control.
4. `external` (optional): trusted local command receives one UTF-8 JSON request and returns precisely `{"probe": INTEGER}`. A proposed probe is admitted only if it is a previously unused integer 0..23. Any parse error, invalid value, failed exit or timeout is a `DEFERRED` trial. **No silent fallback.**

The external proposer must be deliberately opted into using a separate `--acknowledge-unisolated-proposer` flag; enabling the model process is not equivalent to sandboxing it. Pilot CLI refuses to run without `--pilot`. Max 20 tasks per invocation; max five binary observations per policy per task; maximum proposer timeout 10 seconds each. There is no enforceable global CPU/network/cost cap on the external process; use a proper OS sandbox and budget gate before untrusted agents.

## Evidence and replay

- One new JSON evidence file per invocation using exclusive `xb` creation; no updates or deletion of earlier files. CLI prints SHA-256 to save in a separate immutable commit or log.
- Evidence contains the full secret **only at end of run**, the complete task matrix, truth, proposal history, outcomes, candidate-set transitions, terminal status, summary, and limitations.
- A standalone verifier must independently derive the matrix and truth from the committed secret, check uniqueness, validate all control selections, replay state transitions and recompute aggregate statistics. It must reject tampering *even when the attacker recalculates the file SHA-256* for an altered field.
- A digest check protects the bytes against changes relative to an independently pinned digest. It **does not** prove the evidence was collected honestly or the hidden oracle was inaccessible during execution.

## Research interpretation

P1 offers a harder-than-P0 synthetic exercise and a model integration **interface**. It does not test hypothesis invention, discovery of natural laws, real-world experimentation, or independent autonomous science. Running deterministic baselines does not constitute an LLM benchmark. Even a future model score in P1 is exploratory unless the oracle-isolation threat is resolved.

## C1 release gate (must be satisfied before claims)

- Independent red-team isolation tests, held-out commitment, auditable evaluator separate from model, secret not exposed via process environment/logs and filesystem.
- Model artifact SHA-256, model version, quantization, tokenizer, inference/runtime version, decoding parameters and resource limits.
- Strong greedy baseline and paired statistical analysis preregistered; measured wall time, total model tokens, failure/timeout count, and cost per correct task.
- Independent verifier and negative-control corruption suite; preserve negative outcomes and failed trials.
- No automatic authorization for network actions, file modification, model self-updates, or permission changes. The proposal is not execution authority.

**Source of record:** GitHub repository `holland202/veritas-origin`. Codeberg/Hugging Face/Vercel mirrors and dashboard are separate publication tasks whose synchronization must be verified.
