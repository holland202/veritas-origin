# Veritas-Origin Research Architecture Roadmap (design-only)

Status: PROPOSAL — NOT ACTIVE IMPLEMENTATION. Date 2026-10-09. Owner authorization presently allows **architecture planning only**, while Sovereign Veritas P-001 remains unfinished. This roadmap creates no permission to run, merge, deploy or rewrite frozen experiments.

## Research hypothesis
An experimental scientific agent may achieve reproducible improvement in hypothesis discrimination while maintaining externally checkable limits on consequential actions. Separate demonstration of **useful science**, **authorization compliance**, and **effect verification**; successful component tests must not be promoted to integrated success.

## Proposed stages and release gates
| Stage | Minimum future deliverable | Baseline / negative control | Gate |
|---|---|---|---|
| 0: custody / inventory (now, planning) | This audit and provenance/gap list; identify source/PR state | Check every assertion against immutable refs; explicitly mark unavailable artifacts | Claude critique only; VO remains parked |
| 1: research precheck | DPC-001 results under **already frozen** spec/test custody | 20 visible/6 withheld cases, simple checkers, leak/tie/ambiguous cases | Separate owner approval of checker author and acceptance run |
| 2: reproducible research loop | Strict schemas for questions/proposals/observations; toy orchestrator, sandboxed external agents | Random, fixed, heuristic baselines; agent critic vs none; failure+timeout preservation | Preregister metrics, budgets, sources, seeds and stop rule |
| 3: evaluator independence | Versioned independent judge and custody boundaries | Oracle-leakage, evaluator contamination, correlated-critic counterexamples | Held-out review and provenance; no model agreement substitution |
| 4: protected action pilot | SV adapter on a toy consequential tool with forced refusal | Compare ordinary policy+logs to SV; bypass, forged credentials, stale action, replay, race | Independent verifier and executor receipts; no production claims |
| 5: effects / integration | Correlate approved action to execution and measured outcome | Missing/duplicate/forged receipts, partial failure, tampered observations | End-to-end replay by independent operator; limitation register |
| 6: read-only research interface | Outcome-level dashboard with exact provenance links and honest statuses | Deliberately failed record displayed, not hidden | Owner approval of publication and security review |

## Experimental acceptance design (requires preregistration, NOT approved now)
- **Discovery quality**: held-out correct predictions, discriminating information gain, improvement against each baseline, uncertainty intervals. Avoid selection on hidden answer.
- **Utility/cost**: time, tokens, compute, experiment count, human interventions, cost per validated discovery.
- **Security/governance**: unauthorized tool calls (including bypass), false refusals, DEFER resolution, stale authorization, exact action/target binding, concurrency, retry behavior.
- **Evidence quality**: trace completeness, independent replay success, contradictory artifacts, preservation of failed/time-out/inconclusive cases.
- **Failure semantics**: all outcomes labelled PASS / FAIL / INCONCLUSIVE / NOT_RUN / ACCESS_UNVERIFIED; a missing log cannot be counted as a pass.
- Confirmatory N, thresholds, effect sizes and statistics must be frozen *before* runs; this document does not choose them post hoc.

## Research roles and autonomy
- Claude: implementation on owned branch after approval, runnable fixtures and raw evidence.
- ChatGPT: independent critical code/evidence inspection, separately owned negative-case design when appropriate, avoid touching withheld tests.
- External/held-out evaluator or Chad: outcome judgment; AI-to-AI agreement is not independent scientific verification.
- Chad: accepts scope/criteria amendments, irreversibility, protected merges, releases, exception acceptance and project resumption.
- Bounded reviews: two critique rounds per item; unresolved scope/safety/acceptance decisions escalate to Chad.
- GitHub handoff uses one immutable commit and concise evidence links; avoid duplicate agent notes and extra paid services.

## Specific Claude review questions
1. Does the audit accurately distinguish `main` from work solely in PRs? What substantive code was missed?
2. Which layers can collapse into one component without losing trust boundaries?
3. Are the seven suggested record interfaces minimal, or do some create misleading attestations?
4. What independent baseline would most strongly falsify a claimed SV advantage versus standard OPA/Cedar-style policy checks?
5. Where might held-out DPC-001 custody be compromised by a shared GitHub account?
6. Which declared prerequisites are technically impossible or unnecessarily costly?
7. Can each future stage be stopped cleanly with a preserved negative result?

## Stop condition
Do not implement an autonomous agent, integrate SV, run DPC-001, consume held-out secrets, modify frozen specs or merge documents on the strength of this roadmap. Resume only after SV P-001 owner close-out and a separately scoped VO authorization. **EXPERIMENTAL, NOT PRODUCTION-READY, NOT INDEPENDENTLY SECURITY-VALIDATED.**
