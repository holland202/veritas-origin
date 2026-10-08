# VSC-002 — Longitudinal synthetic learning, diversity, and oracle-budget controls

**PROSPECTIVE EXPLORATORY ENGINEERING PROTOCOL — NOT CONFIRMATORY / NOT VALIDATED.** Written before VSC-002 outcomes are generated. VSC-001 evidence, figures, and conclusions remain unchanged.

## Research question

Can a learner benefit from **verification-aware selection of synthetic training examples** across repeated generations without quietly consuming more reference-label information, hiding rare-case regressions, or mistaking self-reinforcing pseudolabels for new knowledge?

This is a bounded mathematical simulator experiment, **not** model collapse in an LLM, human data substitution, or a claim of invention. All data and code are public after experimental runs.

## Fixed exploratory design

- **Reference task:** four seeded scalar mathematical families on x ∈ [-1,1] including an irreducible-for-this-model oscillatory **rare band** (band 3). Training learner: four separate quadratic linear models with fixed feature map [1, x, x²]; no neural network.
- **Natural prevalence:** band weights 0.50, 0.25, 0.20, **0.05**. Each generation offers the same 24 **unlabeled** candidate x values to every arm: six per band. The candidate pool is artificially balanced to ensure fair access to rare cases; this is **not** a measurement of a natural data distribution.
- **Shared reference sets per seed:** initial 8 trusted labeled x examples/band (32), fixed curriculum-selection 16/band (64), independent final in-domain test 48/band (192), and independent shifted-domain test 48/band (192) sampled from x ∈ [-1.45,1.45]. The student and curriculum must not see labels from final test sets before final reporting.
- **Budget:** 12 generations; up to **8 new oracle label queries/generation** for each oracle-assisted arm, therefore exactly 96 total, with **no extra oracle calls** to validate the same queried example. Once the oracle is asked about a candidate, using the answer is permitted and costed explicitly. `pseudo_only` has 0 new training oracle calls. Additional replay/pseudolabel training steps are recorded as separate compute work.
- **Randomness:** 24 publicly reproducible seed instances for exploratory CI, seed base `20261009`. A 2-seed public deterministic smoke precedes the full 24-seed run. Both are **public-test fixtures**, NOT held-out confirmation.
- **Learning:** initial trusted anchors receive 4 training passes. Each generation's selected oracle examples train in a deterministic order with learning rate 0.08; optional pseudolabel/replay steps follow, using explicitly recorded counts. All arms begin with identical initial weights.
- **Selection:** `natural` draws bands using natural prevalence and available candidates; `balanced` queries exactly two examples/band; `error` uses relative selection-validation per-band MSE (minimum weight 0.03); `progress` uses only *positive decreases* in separate selection-validation MSE, blended 60% progress and 40% natural, and a 0.03 minimum weight before normalizing. Never use final test MSE or hidden shift-test results to set selection probabilities.
- **Pseudolabel control:** a proposed y is model prediction plus zero-mean seeded Gaussian noise σ=0.20; `checked_progress` spends its **same eight oracle calls** comparing proposed y with true y. It accepts pseudo-y only when absolute error ≤0.30, otherwise rejects without replacement. **Ground truth from the paid query is intentionally not used as the training label**, so `gold_progress` is a direct, fair, strong comparator.

## Eight arms

| Arm | Oracle labels per generation | Learner updates per generation | Specific purpose |
|---|---:|---:|---|
| `gold_natural` | 8 | 8 | Direct ground-truth natural sampling |
| `gold_balanced` | 8 | 8 | Direct ground-truth uniform band coverage |
| `gold_error` | 8 | 8 | Strong high-error curriculum rival |
| `gold_progress` | 8 | 8 | Strong signed-learning-progress curriculum |
| `checked_progress` | 8 | 0–8 | Same-budget pseudo-label **admission** via oracle checking |
| `mixed_pseudo` | 8 | 24 | Direct-natural oracle plus 16 unchecked pseudolabel updates |
| `gold_replay` | 8 | 24 | Direct-natural oracle plus 16 existing genuine-anchor replay updates; controls extra compute |
| `pseudo_only` | 0 | 24 | No new oracle labels; recursive self-pseudolabel comparator |

Every arm gets the same unlabeled candidate pool; gold_natural, mixed_pseudo and gold_replay use identical natural-band oracle picks for each seed and generation. The progress and checked-progress arms use the same policy family but learner states may diverge; per-arm trace records selection.

## Primary **descriptive** metrics (all 13 checkpoints: initialization and 12 generations)

1. Final and per-generation **macro in-domain held-out MSE**, 4 equal-weight bands.
2. Final and per-generation **shifted-domain macro MSE**.
3. Final and per-generation **rare-band MSE** (band 3), to detect gains that erase rare cases.
4. Accumulating **trusted-label training diversity**: fraction of occupied (band, eight x-bucket) cells, 0..1, and per-generation **selected-label band entropy** (0..1 normalized); measure this on **new oracle-queried candidates**, separately from pseudolabels.
5. Training oracle queries, pseudolabel updates, anchor replay updates, and rejected checked-pseudolabel examples; report all. The 32 initial, 64 selection and 384 test reference labels are **shared fixed data per seed**, not free to create in actual-world experimentation, and not repeatedly charged to each arm.
6. All per-generation values and selected candidate identities logged. No final-test adaptation.

A pointwise model improvement in a publicly seeded toy simulation is not a statistical discovery. Report paired per-seed differences, direction counts, and cases where gold_balanced/gold_progress defeat checked_progress. No post-hoc claims about overall superiority.

## Required failures / anti-vacuity controls

- `checked_progress` must **actually reject** some inaccurate pseudo-labels; do not consider zero admitted samples a successful learner.
- Worse performance on shifted/rare heldout data cannot be obscured by an improved aggregate mean.
- Replaying initial trusted examples is an explicit extra training cost, not a free new label.
- Oracle-assisted arms **must use exactly the same 8×12 new-label budget**; test counting through every generation.
- Changing held-out labels or disabling the independent verifier must not alter *training decisions*. A modified held-out score or selected x must be rejected by a standalone verifier even if the evidence file digest is recomputed.
- Independent deterministic replay must reconstruct candidate pools, policy choices, student updates, per-generation scores, diversity and oracle/compute costs **without importing the experimental runner**. Duplicate JSON keys, NaN, falsified metrics and missing arms must fail.
- A vacuous always-reject admission method and a method that changes its training examples after viewing test outcomes do not qualify.

## Evidence and visualization

- `--pilot` explicit; source writes a new exclusive-create JSON file and prints SHA-256, never overwrites earlier evidence.
- GitHub Actions runs tests, a small public fixture and the predeclared 24-seed exploratory run. Archive raw evidence and independently validated **SVG** graphics (longitudinal in-domain/shifted error, rare-band retention, diversity/label cost) as CI artifacts. Charts must say **EXPLORATORY / SIMULATED / NOT VALIDATED** and show the reproducible seed counts.
- The VSC-002 report must retain all arms and negative outcomes. Evidence SHA-256 needs independent pinning; matching digest by itself does not prove real-world truth, authorship or oracle independence.

## Sources, non-novelty, and rights

- VSC-001, the user's previous verified toy synthetic-curriculum experiment, is the immediate control.
- QUASAR's self-generated simulated examples and progress-curriculum failure modes are prior research ([MIT source](https://github.com/holland202/quasar/blob/ba050b640b791d79d4cfcf5266f01cfd406124a7/LICENSE)); **no code copied**.
- Coverage-Preserving Synthesis is an earlier project with **all-rights-reserved** source; concept-only attribution, no code copied.
- Self-training, teacher checking, active learning, replay, domain randomization, and adaptive curriculum learning are established research topics. Originality and patent non-infringement **NOT ESTABLISHED**.

**STOP line:** Before a confirmatory claim, freeze a separate independent holdout, preregister a minimum effect with paired inference and correction for multiple comparisons, test realistic corruption/shift, and validate a real model and external oracle trust boundary. No production or commercial-safety claims.
