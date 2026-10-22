# Scientific-research-agent prior art — focused initial review

**Date:** 2026-10-08  
**Status:** INITIAL CODE/DOCUMENT REVIEW; no originality or legal clearance finding. No third-party code imported.

## Why this scan is essential

**Automated idea generation, hypothesis planning, experimentation, paper generation, multi-agent orchestration, greedy experiment selection and Bayesian optimization are not new ideas.** VERITAS ORIGIN cannot claim to have invented any of those categories. A contribution, if demonstrated, must be narrower: e.g. a verifiable permission/evidence boundary under adversarial, falsifiable conditions.

## Sources inspected at pinned revisions

| Project | Direct source evidence read | What overlaps VERITAS ORIGIN | License/reuse conclusion |
|---|---|---|---|
| [Sakana AI — AI Scientist](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/README.md) | [`generate_ideas.py`](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/ai_scientist/generate_ideas.py), [`perform_experiments.py`](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/ai_scientist/perform_experiments.py) | Implements idea/novelty-check routines and iterative LLM-generated experimental code execution | **Custom AI Scientist Source Code License**, NOT assumed MIT/Apache; **STUDY ONLY**, no code porting or importing |
| [Sakana AI — AI Scientist-v2](https://github.com/SakanaAI/AI-Scientist-v2/blob/96bd51617cfdbb494a9fc283af00fe090edfae48/README.md) | README overview describes agentic tree search, hypothesis generation, experiments and paper writing | Very broad functional overlap with an autonomous scientist | **Custom AI Scientist Source Code License**; study only, source license conditions not cleared |
| [BoTorch](https://github.com/meta-pytorch/botorch/blob/da00e04015c0118f1b9383f32cab17bdcc0944ff/README.md) | README explains Bayesian models and acquisition functions | Learning-guided experiment selection and optimizing experiment choices | Root MIT; exact file conditions still require review if copied; no code imported |
| [Optuna](https://github.com/optuna/optuna/blob/bfdd420a54fd80993012a8f8393f190b5de882e5/README.md) | [Trial state definitions](https://github.com/optuna/optuna/blob/bfdd420a54fd80993012a8f8393f190b5de882e5/optuna/trial/_state.py) distinguish running, complete, pruned, fail, waiting | Study/trial bookkeeping and optimization are prior art | Root MIT with additional third-party notices documented in repo; no imported code |
| [Microsoft AutoGen](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/README.md) | README describes autonomous/human-in-the-loop multi-agent workflows | Agent/task orchestration already exists | **Mixed rights**: documentation states CC BY 4.0 for documentation and MIT for code (`LICENSE-CODE`); actual file-level clearance required; study only |

The Sakana code evidence is concrete but narrow: `check_idea_novelty` handles research novelty search, and `perform_experiments` iterates a coder/experiment driver. **We have not replicated or audited the entire codebase**, and this document cannot rule on its correctness or safety. v2's tree-search characterization is based here on its published README, not a full independent reproduction.

The license descriptions are observations, not legal interpretations. Source license conditions and dependency assets may differ from a project's root files.

## Position relative to existing work (all hypotheses, not claims)

| Proposed VERITAS ORIGIN emphasis | Prior-art relation | What must be tested before making any differentiator claim |
|---|---|---|
| A model proposes experiments but cannot authorize execution | General authorization engines and sandboxed agents already exist | Cross-repo authorization bridge, real denial evidence, adversarial OS-level access tests, one-key/two-effects attack |
| Result and negative-trial preservation with independent verifier | in-toto, transparency logs, Inspect evaluations and the owner's EACE/Evidence Ledger overlap | Semantic forgery mutations, omitted failed trials, signer/clock trust, independent replay and anti-vacuity |
| Experiment selection under a cost budget | UCB1, greedy information gain, Bayesian optimization (BoTorch), Optuna prior art | Compare to strong conventional baselines on preregistered held-out tasks, total token/cost per correct task |
| Scientific hypothesis invention by models | Sakana AI Scientist and v2 explicitly precede this research | Demonstrate an evaluated problem and method that isn't already covered; credit earlier researchers and preserve negative results |
| "Self-evolving" autonomous researcher | General self-improving agent workflows are established or explored elsewhere | Separate proposed learning from authorized state/policy updates and prove no evaluator feedback contamination |

**Current defensible description:** an independent, AI-assisted *experimental prototype investigating evidence-bounded proposal authorization, independent replay and controlled model experimentation*. Not a first-ever autonomous AI scientist and not an established new scientific discovery system.

## Scientific validity gate for next phase

1. Select a precise falsifiable property, such as "a proposer unable to read the oracle cannot alter the recorded verdict by forging its request."
2. Compare code-level controls against relevant existing implementations; do not treat vague similarity or a README as equivalent functionality.
3. Determine what *would count as proof of the narrow property* (independent OS access tests, fully measured budget, durable idempotent reservations).
4. Measure difficulty distributions and include greedy/information-gain and optimized non-LLM controls.
5. Register confirmatory thresholds before results; retain failures and publish limits. Do not reinterpret P0/P1 synthetic smoke tests as evidence of model novelty.
6. If copying actual third-party material becomes necessary, stop: file-specific licensing, notices, explicit approval and source mapping are mandatory.

## Unperformed research

No comprehensive academic novelty review, citation graph, patent search, dependency transitive licensing audit, or independent replication of the external AI Scientist projects has been conducted. No freedom-to-operate or non-infringement guarantee is provided.

**Reference register:** `research/prior_art_register.json` entries PA-018 through PA-022. All marked `STUDY_ONLY`, `NOT_ESTABLISHED` novelty and `INITIAL_REVIEW`.
