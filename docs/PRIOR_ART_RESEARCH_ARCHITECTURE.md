# Veritas-Origin: Prior-Art-Informed Research Architecture (proposal v0.1)

Status: **DESIGN ONLY — NOT IMPLEMENTED OR VALIDATED**. This document is additive. It does not amend frozen DPC-001, approve checker implementation, or resume paused Veritas-Origin research. Sovereign Veritas P-001 close-out and owner decision remain the execution prerequisite.

## Purpose and claims
Explore whether a model-agnostic research system can (a) make discriminating discoveries, (b) preserve independently checkable experimental evidence, and (c) govern consequential actions through an external policy/evidence gate. Existing systems already automate hypothesis generation and parts of science; novelty of this combination is **unestablished**. Never label AI consensus as independent replication.

## Twelve architectural responsibilities
| Layer | Design responsibility | Maturity claim |
|---|---|---|
| 1 UI | Human questions, reviewable outcome cards, controls | Proposed integration |
| 2 Identity | Authenticated principal, roles, capabilities, tenancy | Not established by an LLM identity string |
| 3 Input/context safety | Schema validation, adversarial context boundaries | Partial research; not a general prompt-injection solution |
| 4 Data/retrieval/memory | Immutable evidence pointers, source manifest, versioned working hypotheses | Components exist, integration unverified |
| 5 Model/inference | Interchangeable cloud/local reasoning adapters | Not a bespoke model |
| 6 Orchestrator | Agent task graph, resource budget, step cap, retry/dedup | Proposed integration |
| 7 Planner/proposer | Hypothesis sets, falsifiable tests, action intents | Experimental components, not integrated |
| 8 Authorization/evidence | Separate Sovereign Veritas integration for protected actions; ALLOW/DEFER/REFUSE and verifier | SV component-level evidence, not VO integration |
| 9 Tool gateway | Verify permit, bind exact target/args, block bypasses | Proposed; fail closed |
| 10 External effects | Execution receipt, effect observation, reconciliation | Unverified requirement; ALLOW != effect |
| 11 Audit/evaluation | Negative results, independent judges, reproduction, telemetry | Existing research artifacts, not whole-platform validation |
| 12 Infrastructure | Sandbox, dependency pinning, CI, key management, substrate manifests | Project-specific, maturity unverified |

## Adaptations from prior art, not copied code
1. **Google Co-Scientist**: distinct generate, critical-reflect, rank, evolve roles. Require different evidence/custody roles and a non-LLM scoring oracle when possible. Control: one-agent, random-selection and fixed-policy baselines.
2. **Sakana AI Scientist-v2**: bounded tree search for experimental candidates, with maximum nodes, execution limits, and explicit failed branches. Compare with the simpler template baseline rather than assuming tree search helps. Agent-authored code runs only in isolated, resource-limited sandboxes; never by default on the host.
3. **FutureHouse Robin**: make the cycle hypothesis -> proposed test -> actual observation -> follow-up explicit. Separate simulated outcomes, AI interpretations, and externally observed effects; no biological-result claims from toy runs.
4. **METR**: evaluate task completion by independent grading across varied task lengths and hard negatives; report success rates with denominators, elapsed time, total attempts, interventions, budget and uncertainty. Avoid cherry-picked demonstrations.
5. **OPA decision logs**: include stable action/decision IDs, policy revision, input digest, actor, permitted operation and linked log provenance. Do not log secrets. Compare replay and incident reconstruction with a normal policy/logging baseline.
6. **Cedar authorization**: require explicit principal, action, resource and context; test denied, malformed, stale and privilege-changing cases. Benchmark against a conventional Cedar/OPA-like enforcement baseline before claiming SV adds measurable value.

## Proposed research loop (future, not activated)
1. Register a falsifiable research question, controls and stop criteria **before** seeing outcomes.
2. Generate >=2 rival hypotheses and mark unknowns, priors and source provenance.
3. Select discriminating tests using a preregistered estimator; preserve a random and simple heuristic baseline.
4. Execute only permitted experiments with immutable case IDs, pinned software/substrate and budget.
5. Capture raw observations, failures, timeouts and resource consumption before interpretation.
6. Evaluate held-out cases with a separate judge; a reviewing model may critique but is not a substitute for independent measurement.
7. Update confidence and publish a bounded result (supported/refuted/inconclusive); keep original claims and their revision history.

## Gate boundary contract to investigate
A proposed protected operation includes `action_id`, `principal`, `resource`, `arguments_digest`, `evidence_refs`, `policy_revision`, `expiry`, and `idempotency_key`. These are **design candidates**, not fields asserted to be in current SV schemas. Test an adapter without mutating the frozen SV contract. If DEFER or REFUSE, no executor call. If ALLOW, revalidate when action/environment changes. Record attempts and signed/attributable effects separately. Prevent replay and TOCTOU at the executor; do not claim current SV already guarantees exactly-once effects, power-loss durability, concurrency safety, source truth or genuine authority.

## Evaluation matrix / anti-vacuity
| Study | Baselines | Main measures | Critical negative cases |
|---|---|---|---|
| Hypothesis selection | random, first, simple oracle-free heuristic | held-out accuracy, discriminating power, budget | tied scores, oracle leakage, estimator manipulation, changed RNG |
| Multiagent science | single agent vs critic vs adversarial critic | independently graded correction, cost, diversity | collusion/identical blind spots, judge contamination |
| Authorization | conventional OPA/Cedar-style policy+logs vs proposed SV-gated executor | unauthorized execution, false refusal, latency, replay/reconstructability | missing identity, altered action, stale approval, concurrency, duplicate execute |
| End-to-end integrity | same agent with vs without gate | validated useful outcomes per resource, external receipt match | forged receipt, altered source, partial failure, no observation |

Pre-register sample sizes, split strategy, confidence intervals, effect thresholds, and falsification conditions before any confirmatory tests. Count unexecuted, timeout, inconclusive and adverse results. A digest match or successful process exit establishes neither authenticity nor scientific truth.

## Stewardship, sequencing, and deliverables
- **Now**: discuss/review this additive architecture proposal only. No deployment, science run, model agent, gate adapter, or DPC-001 checker created by this document.
- **SV first**: complete P-001 under its existing frozen acceptance and explicit owner final approval.
- **VO after approval**: preserve frozen DPC-001 spec at `d05501013c7b2d0c602893e44d157620b55f12ff` and PR #20's 20 visible/6 withheld custody; obtain separately required approvals before checker implementation or acceptance.
- **Next eligible VO deliverables**: audited component inventory; architecture interface schema; a toy research-loop prototype on a separate experimental branch; three-baseline preregistration; a separate SV integration pilot; independently graded result report. Each is future and separately scoped.
- Chad reviews consequential scope changes and final outcomes. Claude and ChatGPT may critique proposals, but model-to-model agreement is correlated review, not independent security validation.
- Always report **EXPERIMENTAL / NOT PRODUCTION-READY / NOT INDEPENDENTLY SECURITY-VALIDATED** unless new evidence supports a narrower revision.

## Primary prior art (accessed 2026-10-09)
- Google DeepMind, Co-Scientist: https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/
- Sakana AI, AI Scientist-v2: https://github.com/SakanaAI/AI-Scientist-v2
- FutureHouse, Robin: https://www.futurehouse.org/research/demonstrating-end-to-end-scientific-discovery-with-robin-a-multi-agent-system
- METR, Task Completion Time Horizons: https://metr.org/time-horizons/
- Open Policy Agent, Decision Logs: https://www.openpolicyagent.org/docs/management-decision-logs
- Cedar, Authorization: https://docs.cedarpolicy.com/auth/authorization.html
