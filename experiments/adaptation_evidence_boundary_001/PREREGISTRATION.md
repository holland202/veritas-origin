# SV-ADAPT-BOUNDARY-001 — preregistration

Status: REGISTERED, NOT EXECUTED OR VERIFIED at publication. This is a boundary-demonstration protocol, not a scientific claim of novel learning.

## Decision
Determine whether a future evidence-bound LDE update executor can trust caller-supplied `verification.status=PASS` and required-evidence booleans without separately authenticating their origin and update/epoch binding. Use the *actual* Sovereign Veritas `Gate.evaluate()`, but no live action executor.

## Inspiration (not implementation)
NVIDIA LoGRA, https://arxiv.org/abs/2610.06647 : compact gradient sketches and bounded updates. This experiment does NOT implement LoGRA, RL, gradient sketching, parameter training or a KL budget. It uses a simple maximum predicted output change over five held-out points as a stand-in to motivate separate evidence verification.

## Frozen design
- Seeds: 0..31, deterministic affine simulation, 4 cases per seed = 128 cases.
- Probe x values: -10, -4, 2, 7, 25. Output difference budget: 2.
- Trusted-simulator flags: `independent_oracle`, `budget_ok`, `fresh_epoch`, each derived from simulator values.
- Forged flags: all True, supplied to the same actual Gate call.
- A declared authorized `apply_model_update` capability requires all three flags; only `simulate_update` is permitted.
- **benign** (truthful small intercept update): registered trusted ALLOW, forged ALLOW.
- **poisoned** (false proposed update): registered trusted DEFER, forged ALLOW.
- **stale** (correct update but stale epoch): registered trusted DEFER, forged ALLOW.
- **oversized** (correct but >2 output change): registered trusted DEFER, forged ALLOW.

## Registered predictions and anti-vacuity
P1 128 deterministic records. P2 benign acceptance with truthful flags; negative scenarios rejected/deferred. P3 forged truthy attestations are accepted by real Gate. P4 blanket-refusal must fail benign positive control; blanket-acceptance fails poisoned/stale/oversized negative controls.
Failures remain failures; execution errors marked NOT EVALUABLE; no after-the-fact expectation changes.

## Limits
The oracle is simulated and under the same custodian. The Gate is not claimed to authenticate evidence itself; it necessarily relies on upstream verified provenance. This probe does not demonstrate an actual product vulnerability, independent security validation, a policy learning improvement or end-to-end safety. Exact checkout revision and dirty worktree status must be recorded separately.

## Evidence / cost
Offline Python standard library. No paid model calls. No real commands on actuators; no model weights changed. New timestamped output folder with cases.jsonl, summary.json, SHA256SUMS. Preserve all failed runs, no automatic publication, no private third-party research material. Any paid follow-up requires separately frozen task, baseline, quantitative hypothesis, maximum spend, and owner go-ahead.
