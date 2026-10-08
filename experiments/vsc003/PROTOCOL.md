# VSC-003 — Costed weak verification: prospective exploratory protocol

**PREREGISTERED BEFORE ANY VSC-003 RUN.** Classification: `PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED`. This is a toy four-band mathematical learner, not an LLM, foundation-model synthetic data pipeline, or evidence of solving the data wall.

## Motivation and scientific question

VSC-002 found that checking a pseudolabel using an oracle that could directly supply the correct label was inferior to using that paid true label. VSC-003 introduces an explicit **information and cost asymmetry**: a *weak binary verification query* costs 1 unit and reveals only ACCEPT/REJECT; a *strong ground-truth label query* costs 6 units and reveals a numeric value. They **must not be treated as information-equivalent**.

**Question:** Under a fixed acquisition budget, does cheap imperfect binary verification of synthetic proposals yield better generalization or evidence quality than direct gold labels or simple strong alternatives?

**H1 (exploratory):** At least one weak-checking policy yields lower final in-domain macro MSE than `gold_natural`, subject to non-inferior rare-band MSE and transparently reported false acceptances. H1 may fail. **No post-hoc winner declaration or significance threshold.**

## Prior art and source rights

This problem is established, not a claim of algorithmic novelty:

- Zhang & Chaudhuri, **Active Learning from Weak and Strong Labelers** (NeurIPS 2015): https://papers.nips.cc/paper/5988-active-learning-from-weak-and-strong-labelers
- Kiyani et al., **When to Trust the Cheap Check: Weak and Strong Verification for Reasoning** (ICML 2026): https://proceedings.mlr.press/v306/kiyani26a.html
- Beck et al., **Beyond Active Learning: Leveraging the Full Potential of Human Interaction via Auto-Labeling, Human Correction, and Human Verification** (WACV 2024): https://openaccess.thecvf.com/content/WACV2024/html/Beck_Beyond_Active_Learning_Leveraging_the_Full_Potential_of_Human_Interaction_WACV_2024_paper.html
- User's VSC-001/VSC-002, QUASAR (MIT), Evidence Ledger (unlicensed until clarified), EACE (MIT); Coverage-Preserving Synthesis (all rights reserved). These are conceptual sources; **no existing or third-party source code copied**.
- A preliminary prior-art scan is neither exhaustive nor patent clearance. **Novelty NOT ESTABLISHED.**

## Frozen simulator, splits and costs

- Same broad family as VSC-002 but numerically distinct deterministic mathematical functions: four band-labeled scalar responses, including a high-frequency rare band (band 3). Each band has a low-capacity quadratic student predictor; real LLM behavior is **NOT TESTED**.
- Natural band weights: `[0.50, 0.25, 0.20, 0.05]`. Every generation gives each policy the same **24 unlabeled input candidates** (six per band), unshifted x range [-1,1]. Rare band intentionally underrepresented in natural selection.
- 24 **public engineering seeds** `20261033..20261056`, 10 generations, checkpoints 0..10. Two-seed, three-generation pilot is a smoke control only, followed by this 24-seed exploratory run.
- Per seed: 8 initial gold examples/band (32); **fixed separate curriculum-selection** 16/band (64); **separate final in-domain test** 48/band (192); **separate shifted final test** 48/band (192), with x in [-1.40,1.40]. All selection and evaluation reference labels are generated *once*, shared across policies and **accounted separately**; they are never free in a real setting. Final test labels never influence training.
- Student: fixed map [1,x,x²], per-band weights, learning rate 0.08, initial 4 epochs. Each arm starts identically. The simulator oracle and verifier execute in the same host process (security isolation **UNMET**).
- **Each generation exactly 12 available acquisition credits** per policy. New oracle gold-label query costs **6**, binary weak verification of a proposed label costs **1**. Unused credits are recorded, not silently spent or rolled over. Total ceiling: 120 credits per 10 generations. Strong gold policies acquire 2 labels/generation (12 credits). Weak policies can request 12 Boolean checks (12 credits). Hybrid buys 1 gold label + 6 checks (12 credits).
- Weak verifier internally compares proposed y with the true mathematical value at tolerance **0.30**, but returns only a Boolean to the learning policy. **Independent flip noise:** 8% chance to flip an otherwise correct binary answer, producing measurable false acceptance and rejection. Record and independently replay *both* false-accept and false-reject events; do not present the weak verifier as a truth certificate. Proposals = current-student prediction plus zero-mean Gaussian noise (σ=0.25); 15% inject an outlier ±1.0.
- Rejected queries do **not** obtain replacement labels. Verified but accepted pseudolabels are **not promoted to true-gold evidence**.
- Curricula: `natural` draws candidates by natural band weights; `balanced` covers bands uniformly; `error` weights by separate curriculum-selection MSE; `progress` uses **positive decreases** in selection MSE mixed 60% signed improvement with 40% natural base, fallback natural if no positive progress. This selection set is visible to policies (hence must be counted as external reliable data), never test labels.

## Arms and required controls

| Policy | Generation labels acquired | Credits / generation | Training updates |
|---|---|---:|---|
| `gold_natural` | 2 direct gold labels, natural selection | 12 | 2 |
| `gold_balanced` | 2 direct gold labels, balanced band rotation | 12 | 2 |
| `gold_error` | 2 direct gold labels, error priority | 12 | 2 |
| `gold_progress` | 2 direct gold labels, progress priority | 12 | 2 |
| `checked_natural` | 12 weak Boolean checks, natural selection | 12 | 0–12 accepted pseudolabels |
| `checked_balanced` | 12 weak Boolean checks, balanced selection | 12 | 0–12 accepted pseudolabels |
| `checked_progress` | 12 weak Boolean checks, progress selection | 12 | 0–12 accepted pseudolabels |
| `hybrid_progress` | 1 direct gold + 6 weak checks, progress selection | 12 | 1–7 |
| `gold_plus_pseudo` | 2 direct gold + 10 **unchecked** pseudolabel updates | 12 | 12 |
| `gold_replay` | 2 direct gold + 10 **real anchor replay** updates | 12 | 12 |
| `pseudo_only` | 12 unverified pseudolabel updates, 0 strong/weak queries | **0** | 12 |

All policies share the same candidate generation streams; differing dynamic model states affect proposed labels. Include *training compute* and oracle feedback costs separately. Do not claim the policies are matched in model-update cost.

## Fixed outcome measures and anti-vacuity controls

Report all 11 per-generation checkpoints for all 11 arms, including final per-seed paired results, means, and negative outcomes:

1. Macro in-domain held-out MSE; shifted macro MSE; rare-band MSE.
2. Exactly accounted `strong_label_queries`, `weak_binary_queries`, total credits spent, unused credits, model updates, and pseudolabel/trusted-anchor replay counts.
3. Weak-verifier **false accepts** (incorrect positive) and **false rejects** (incorrect negative) relative to internal simulator truth; independently verified from original candidate and proposal.
4. Band coverage and input-cell occupancy **separately** for (a) all queried inputs, (b) accepted training samples, and (c) gold-labeled training samples. Weak-checked pseudolabels never increase (c).
5. Acceptance rate, inspected examples with zero valid training opportunities, and rare-band selection counts; preserve signs of worsening.

The trial is informative only if the weak check sees both truly acceptable and truly unacceptable proposals and the injected bit-flip noise produces observable false decisions at the public-seed scale. If either anti-vacuity condition fails, report **UNINFORMATIVE**, not `PASS`.

## Evidence, verifier and visualization

- Implement deterministic runner and **separate independently written stdlib semantic replay**. The latter must reconstruct all 11×24×10 trajectories, proposed y, noisy weak feedback, student updates, selection weights, cost ledgers, evidence provenance, and outcomes **without importing the runner**.
- Reject duplicate JSON keys, NaN/Infinity, forged SHA, rehashed altered outcomes, forged verification answers and costs, and incorrect promotion of checked pseudo evidence to measured gold. SHA is byte integrity, not signature or truth.
- Store a unique exclusive-created evidence JSON. Preserve exact byte hash and raw CI artifact; if later copying to permanent storage, never overwrite earlier artifacts.
- Generate **labeled** trajectory SVGs showing in-domain/shifted/rare outcomes, query/credit budgets, and true-gold versus accepted-example coverage. All charts must say `EXPLORATORY SIMULATED — NOT VALIDATED`.
- Github Actions runs negative-control suite, public-smoke and full study, independent replay and historical EXP003-P0 recheck. No cloud model API, Azure, untrusted code, external installations, or network inference.

## Exit criteria and possible falsification

**Supporting evidence** would be a budget-matched weak-feedback method improving in-domain and rare-case performance **without** unaccounted label access, accompanied by honest imperfect-verifier errors. **Refuting evidence** includes gold or simpler hybrid control matching/beating the method; unacceptable false admission rates; omitted oracle information; or failure of independent replay. Even success only applies to the toy model and checked parameter regime. Future confirmatory trials need frozen unseen distribution, power/statistics, noise and cost sweeps, and real model/isolated verifier before any broader claim.
