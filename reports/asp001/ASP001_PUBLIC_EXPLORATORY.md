# ASP-001 — Internally regulated weight updates in a real small neural network

**Final verdict: `H1_NOT_SUPPORTED_IN_THIS_FIXTURE`.**
**Scope:** EXPLORATORY / NOT VALIDATED / NOT BIOLOGICAL CHEMISTRY / NO NOVELTY CLAIM.

## Exact research question and lineage

Can a real small neural network produce an internal scalar from its own loss history and gradient direction, use it to modify how strongly its connections learn, and outperform ordinary training on stability plus adaptation?

- Prospectively registered **before implementation or results**: [`experiments/asp001/PROTOCOL.md`](../../experiments/asp001/PROTOCOL.md), original commit **`5e1f9918ddd7adbb2e890e418b25241ade96959e`**.
- The study lives **in VERITAS ORIGIN**, on branch `experiment/asp001-internal-plasticity-regulation`, based directly on original unmodified `main` `2131d9166deea94811155a746e57fb597491f53a`. It does not merge the QUASAR, EACE or Sovereign Veritas repositories.
- First successful full public study: [GitHub Actions run 37865918399](https://github.com/holland202/veritas-origin/actions/runs/37865918399), executed with Python 3.12 and NumPy **2.2.6** at source revision **`1c97f887191fece105fcdd347a852a89fb6a3069`**. Its independently reproduced data are pinned below. Later documentation-only commits do not retroactively change this original result.

## Frozen six-policy experiment

Network: **1 input → 16 tanh neurons → 1 linear output**, **49 actual trainable scalar parameters** updated by backpropagation. Common training sequence **A → B → A**, 64 minibatches of 16 samples per phase, **192 weight updates and 3,072 training-label exposures per seed/policy**. Phase B has registered 15% additive ±0.75 training-label outliers; held-out A/B scores use exact, clean functions on a separate 129-point grid.

Six paired controls: constant SGD learning rate **0.01**, **0.03**, **0.09**; time-only scheduled SGD; Adam rate **0.01**; and **regulated SGD base rate 0.03**.

The regulator uses *only* its own prior batch-loss EMA and cosine similarity between current/previous clipped gradients. It does not see held-out answers, a task identifier, future examples, or another policy's states. Fixed modulation:
`m=clip(1+0.35*cosine−0.30*max(positive_relative_loss_shock,0), 0.35,1.4)`, and `effective_lr=0.03*m`.
This is a **globally modulated backpropagation rate**, not authentic per-synapse Hebbian plasticity or an artificial neurotransmitter.

Primary endpoint was frozen as the mean of clean A and B held-out errors **after phase B**, so both stability and adaptation count. The criterion required better mean than *both* SGD 0.03 and Adam 0.01, with at least 13/24 paired seed wins against each.

## Measured 24-seed public results

![Real neural network experimental negative result: mean joint errors across six policies](figures/asp001_public_24seed_joint_mse.svg)

| Policy | Mean joint A/B MSE after B ↓ | Mean A forgetting (change in A MSE after B) | Mean clean B MSE after B ↓ | Mean A MSE after final A2 ↓ |
|---|---:|---:|---:|---:|
| **SGD 0.01** | **0.30122894** | **0.00459143** | 0.32215156 | 0.27136005 |
| SGD 0.03 | 0.30506120 | 0.01701934 | 0.32136035 | 0.27028128 |
| SGD 0.09 | 0.30764581 | 0.01889523 | 0.32341484 | 0.26717381 |
| Scheduled SGD | 0.30385522 | 0.01535499 | 0.32070575 | 0.27036555 |
| Adam 0.01 | 0.30343219 | 0.01844743 | **0.32022258** | **0.25159946** |
| **Regulated SGD** | 0.30548563 | 0.01730924 | 0.32179593 | 0.27060034 |

Lower MSE is better. A forgetting is `A_MSE(after B) − A_MSE(after A1)`: more positive means larger measured forgetting on the older task, although baseline A1 quality can differ.

The proposed regulator was **nonconstant on 191/192 steps per seed on average**, so it genuinely altered weight updates. But its primary mean error **did not beat the stronger conventional controls**.

### Paired public-seed comparisons

Signed values are `regulated_sgd − baseline` joint MSE, where positive values mean regulation did *worse*. The 95% intervals are preregistered **descriptive bootstrap percentiles, not confirmatory statistical proof** (2,000 paired resamples, seed 7741).

| Baseline | Regulated minus baseline | Regulated wins / 24 | Descriptive paired-bootstrap 95% |
|---|---:|---:|---|
| SGD 0.01 | +0.00425670 | **3/24** | [0.00290854, 0.00576915] |
| SGD 0.03 | +0.00042443 | **9/24** | [−0.00002439, 0.00096722] |
| SGD 0.09 | −0.00216018 | **15/24** | [−0.00457068, 0.00002859] |
| Scheduled SGD | +0.00163042 | **4/24** | [0.00084242, 0.00256132] |
| Adam 0.01 | +0.00205344 | **9/24** | [−0.00126014, 0.00558928] |

The regulator improved over the weakest of the registered fixed-learning-rate settings (SGD 0.09) on mean error, but **that is not the registered benchmark for success**. It does not justify changing the study's verdict.

[All 24 original paired seed scores in Git](ASP001_PUBLIC_SEED_PAIRS.csv) — values rounded to ten decimals for human inspection. For full-precision weights, training trajectories, labels/inputs digests and confidence intervals, inspect the original artifact.

## Verification and original evidence

- **32 ASP-001 tests PASSED:** numerical finite-difference gradient checks, learned-weight changes, matched training budgets, real modulator anti-vacuity, deterministic seeds, negative controls, rehashed tampered metrics and weights, duplicate JSON keys and false validation states.
- **17 historical EXP003-P0 tests PASSED** and the original pilot's exact hash and independent verifier still passed; **49 tests** across the two executed suites, plus full independent simulation replay.
- Full public experiment record **SHA-256**: `065c266864c1337e204488c1e01e71f69560c6db30cede6e10e98a908502e2a0`.
- Separate source-and-evidence manifest SHA-256: `4f837ab3163a1e1c5045b274039162fb4bed505ecaf0640959f37661f344de10`.
- CI-generated graphic digests: `asp001_joint_mse.svg` = `204fd4d71f843021602f8d2aa21f61bcca553b4b88037edbce91659d9af3007d`; `asp001_modulation.svg` = `6cb5495bfec9c8ede932f42f09aa1c91e4b6016f66f64170179fabbd9514370e`.
- Original raw **10,687,752-byte** full JSON + source manifest + two generated figures: [GitHub Actions artifact `asp001-neural-plasticity-full-evidence` ID `11588132315`](https://github.com/holland202/veritas-origin/actions/runs/37865918399/artifacts/11588132315). **Expires 2026-11-08 UTC** under Actions retention; archive exact bytes separately beforehand.
- The plotted public graphic and the compact all-seed CSV are **permanently committed to this draft branch**; they are derivative records, not substitutes for the original full evidence.
- Numerical replayer independently implemented backpropagation, learning signals, checkpoints and registered aggregate comparisons without importing the producer. Its scope is **`INDEPENDENT_NUMERICAL_REPLAY_CONSISTENT_ONLY`**, not evidence of true biochemical equivalence.

## What was learned and what remains unknown

**Supported within the defined toy setup:** a functional internal regulatory factor can be computed from a network's recent training dynamics and used to change its real neural weights; it changes its value over sequential training; and the full process can be reproduced independently to bounded numerical tolerance.

**Not supported:** the hypothesis that this particular loss-and-gradient driven regulator better balances retention and adaptation than the registered SGD 0.03 *and* Adam 0.01 controls on these tasks. It also was worse in mean than time-only scheduling and conservative SGD 0.01.

**Not established:** consciousness, living AI, neurotransmitters, biological analogy as equivalence, per-synapse Hebbian plasticity, real-world model improvement, novelty over established neuromodulation/continual-learning literature, privacy/security isolation, production authorization, true energy or compute-cost equality, fresh unseen-task generalization, and meaningful differences beyond the public toy distributions.

This is one small setting. Failure does not refute artificial neuromodulation generally; prior work already studied improved plastic architectures, including Miconi et al. and Synaptic Consolidation / EWC.

## Next steps without retrospective tuning

1. Preserve this exact negative result and its registered protocol.
2. Freeze a separate ASP-002 hypothesis **before** using new data: investigate genuine per-synapse eligibility/plasticity traces rather than a global update-rate scalar; compare at least SGD, Adam, an unmodulated plasticity control, and an established continual-learning reference such as EWC.
3. Use new hidden task families and seed ranges; measure total compute overhead, resource usage and any benefit against the strongest relevant baseline.
4. Keep actual model research separate from Sovereign Veritas's **external permission gate**. No automatic model mutation, production effect or research promotion is authorized.

This report should remain `EXPLORATORY_NOT_VALIDATED` even if subsequent experiments improve.
