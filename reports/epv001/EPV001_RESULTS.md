# EPV-001 — Multiagent evidence vigilance: majority, dissent, and a poisoned authority

**STATUS: PUBLIC SYNTHETIC EVIDENCE-FUSION BENCHMARK / EXPLORATORY / NOT VALIDATED.**
This is **not** an actual LLM, agent swarm, human reasoning simulation, security penetration test or scientific validation of AI epistemics.

## Question and provenance

When four agents report potentially correlated evidence about an unobserved binary state, can a decision policy avoid (a) mistaking repeated reports for independent confirmation, (b) discarding a lone verifiable dissent, and (c) accepting self-attested forged evidence? What happens if the **trusted verification anchor itself is wrong**?

Motivated by independently reported Anthropic [*Patterns and problems in emerging multiagent systems* (Aug 13, 2026)](https://www.anthropic.com/research/multiagent-systems), specifically opposite failures from unreliable overlapping scouts and missed hidden-profile minority facts. This is a **new, much smaller synthetic fixture**, not a reproduction of Anthropic's models or their experiments.

- Prospectively frozen **before code/test/results:** [protocol](../../experiments/epv001/PROTOCOL.md), original commit `f5c37769745900ec5a494d1abec58dbadac257dd`.
- Base: VERITAS ORIGIN original `main` `2131d9166deea94811155a746e57fb597491f53a` on independent draft branch `experiment/epv001-multiagent-evidence-vigilance`. No historical, experimental or other repository file was modified.
- Runner [`src/origin/epv001.py`](../../src/origin/epv001.py); independently implemented mathematical reconstructor [`tools/verify_epv001.py`](../../tools/verify_epv001.py); explicit adversarial and non-vacuity tests [`tests/test_epv001.py`](../../tests/test_epv001.py).
- Passing [GitHub Actions **37871992687**](https://github.com/holland202/veritas-origin/actions/runs/37871992687): 27 EPV tests + 17 historical EXP003 tests = **44/44 PASSED**, independent full 3,072-trial replay passed, original EXP003-P0 evidence SHA unchanged.
- Original **3,072-trial raw JSON SHA-256**: `5867b9ea49b97065dafd96d190daba53cb2417e4a13ff6c4e1f9a99521d10368`.
- [Original full JSON and compact source-linked summary, GitHub artifact ID 11590892458](https://github.com/holland202/veritas-origin/actions/runs/37871992687/artifacts/11590892458), GitHub Actions retention until approximately **2026-11-08 01:54 UTC**. Archive separately before expiration; a PDF/this report is not a substitute.
- GitHub-generated summary SHA-256: `c36709438229abcc9c1383c3dd984c761409b6fee76c94087ba76f56c4bb547a`.
- **Permanent original raw JSON:** [exact SHA-verified EPV001_PUBLIC_ORIGINAL.json in this research draft branch](../../evidence/epv001/EPV001_PUBLIC_ORIGINAL.json), copied from the first successful published Actions artifact **without numerical regeneration**. The [one-time archive job 37872210659](https://github.com/holland202/veritas-origin/actions/runs/37872210659) checked both the recorded byte SHA-256 and independent semantic replay before committing only the new artifact. The [first archive attempt 37872154497](https://github.com/holland202/veritas-origin/actions/runs/37872154497) refused to proceed because the archival script initially pinned Git commit IDs rather than actual blob IDs; this failed run is retained. The one-time archive workflow has since been disabled.

## Actual engineered setup and registered limitations

Eight public seeds 260801–260808 × six frozen situations × 64 trials each = **3,072** deterministic synthetic episodes. Each has four simulated scouts, a binary truth known to the fixture generator, source-lineage labels, optional eight-bit parity witnesses, and **fixture-declared** SHA-256 reference anchors. Four fixed decision functions are tested on *the same messages and anchors*:

- **Majority:** all four reports counted as independent, even if three are copies of one source.
- **Lineage:** one vote per registered origin, ties become `ABSTAIN`.
- **Claimed-certificate:** deliberately unsafe rule trusts any self-reported `claimed_verified` label.
- **Evidence-first:** checks witnessed parity and exact anchored claim; if two valid anchors contradict, abstains; otherwise falls back to independent-lineage votes.

**This is a proof-of-mechanism test by construction**, not evidence that a trained LLM can learn this behavior. The verifier is independent *code*, but uses the same disclosed RNG family/mathematical facts. No source identities, anchor registry or world truth are authenticated by a real OS/human/remote trusted party.

## Full results, including failures

Each row represents 512 constructed trials. Counts refer to wrong **accepted** answers; a refusal is recorded separately, not silently treated as correct.

| Frozen case | Simple majority wrong | Evidence-first wrong | Evidence-first ABSTAIN | Interpretation |
|---|---:|---:|---:|---|
| INDEPENDENT_LIAR | 0 | 0 | 0 | Legitimate majority still succeeds; detector is not all-refuse |
| CORRELATED_FALSE_MAJORI | **512** | **0** | 0 | One anchored dissenter beats three copies of a false claim |
| CORRELATED_UNPROVEN_DISSENT | **512** | **0** | **512** | Without proof, tied independent lineages remain unknown; refusing is not truth recovery |
| FORGED_DISSENT_PROOF | 0 | 0 | 0 | Matching authenticated fixture anchor rejects a source's self-attested forged witness |
| POISONED_AUTHORITY | 0 | **512** | 0 | **REGISTERED FALSE POSITIVE**: wrong but internally valid authoritative reference is trusted |
| CONFLICTING_AUTHORITIES | 0 | 0 | **512** | Conflicting independently anchored witnesses require an explicit unresolved status |

The deliberately unsafe claimed-certificate policy accepted the forged wrong claim **512/512 times** in `FORGED_DISSENT_PROOF`. The evidence-first policy avoided that specific attack only because a pinned fixture anchor was *assumed reliable*; it did **not** prove the anchor was true.

Across all 3,072 constructed trials, evidence-first makes **512 known wrong accepted decisions** (all poisoned-reference), **1,024 abstentions** (uninformative dissent and conflicting references), and **1,536 correct accepted decisions**. Correctness **conditional on acceptance** is 1,536 / (1,536 + 512) = **75%**; coverage is 2,048 / 3,072 = **66.7%**. These figures reflect an **engineered balanced fixture**, not an estimate for real multiagent deployments or published Anthropic models. Do not describe abstentions as successes.

Simple majority made **1,024 known wrong accepted decisions**, with no abstentions. That does not establish evidence-first as generally statistically superior: the synthetic situations were explicitly constructed to exercise particular rules, and the benchmark explicitly contains a failing trusted reference.

## What this tells us and what it cannot

**SUPPORTED in this synthetic implementation:** dependence among source reports can make majority vote misleading; a computational witness can be checked without trusting a self-reported verification flag; verified disagreement should not silently be resolved by row order; and a poisoned but internally coherent trusted anchor can defeat an otherwise consistent evidence-first policy.

**NOT ESTABLISHED:** a real model's ability to assess another agent's honesty, identify malicious intent, use unique information, detect forged identity, evaluate world truth, or autonomously authorize an action. Hashing a false claim does not make it true; source-authenticity and oracle provenance remain critical trust assumptions.

**Cross-project implication:** EACE's integrity-versus-truth distinction, EBA-001's known false-clean telemetry, and Sovereign Veritas's evidence-versus-authorization distinction apply here—but no code was imported or copied from those other repos. A deterministic decision-policy PASS cannot create a real publication authorization capability.

## Next falsifiable step, separately registered if undertaken

A fresh **LLM-based EPV-002** needs a trusted oracle kept outside agents' prompts/process access, genuine model-written conflicting reports, randomized report ordering, proper independent source identities, withheld new scenarios, frozen token/time budgets and baselines including trust-everyone, majority, arbitrary skepticism, witness-checking and unconditional refusal.

Primary metrics must separate:
1. correctness **among accepted decisions**,
2. coverage / rate of deferral,
3. invalid or malicious source acceptance,
4. undetected poisoned reference acceptance, and
5. wall-clock/token costs.

No model self-report, hidden-answer leakage or jointly authored answer keys are accepted as independent evaluator provenance. No real agent test has been performed yet.

## Link to the broader research agenda

[Frontier Red Team research extrapolation](../../docs/FRONTIER_RED_TEAM_RESEARCH_EXTRAPOLATION.md) separately identifies multiagent resource contention, conflict between concurrent goals, the security-review pipeline's unverified reports and end-to-end physical control as **future** protocol questions. EPV-001 addresses only a narrow mathematical **evidence fusion** subproblem. The strongest safety result remains its **known false-positive boundary**.
