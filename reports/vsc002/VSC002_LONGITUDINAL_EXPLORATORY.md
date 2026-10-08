# VSC-002 — Longitudinal synthetic learning, evidence diversity, and matched oracle budgets

**PUBLIC EXPLORATORY SIMULATION — NOT VALIDATED.** This experiment investigates a *toy mathematical learner*. It does not establish general language-model collapse, human-text data replacement, production reliability, model independence, or a novel training method.

## Original evidence and reproducibility

- Protocol: [`experiments/vsc002/PROTOCOL.md`](../../experiments/vsc002/PROTOCOL.md), committed *before first VSC-002 run* at `80a288d0b6e88ace4505b028073558eaeb4f674b`.
- Pre-run clarification: oracle-checked **pseudolabels are never called true-gold labels**; separate oracle-queried, accepted-for-training, and true-gold label coverage. This amendment was committed before CI runs as `7bd18f6095ae986a544301dc95b54cb2b8b1f1ef`.
- Experiment: [`src/origin/vsc002.py`](../../src/origin/vsc002.py); independent replay: [`tools/verify_vsc002.py`](../../tools/verify_vsc002.py); negative controls: [`tests/test_vsc002.py`](../../tests/test_vsc002.py); standalone figures: [`tools/plot_vsc002.py`](../../tools/plot_vsc002.py).
- Source revision of completed first VSC-002 CI run: `26e65f08112fa8dbd19c777f565c1655823b9c29`.
- Completed CI: [GitHub Actions run 37855187413](https://github.com/holland202/veritas-origin/actions/runs/37855187413) — passed **33 VSC-001 tests + 38 VSC-002 tests**, independent VSC-002 full trajectory replay, and preserved EXP003-P0 replay.
- **Raw 24-seed evidence SHA-256:** `30377002245f2bb8df6454ecbc4f36ddb0e3114f7c7d9f682d8e658ef568f90c`.
- GitHub Actions artifact: `vsc002-public-seed-evidence-and-figures`, artifact ID `11583064547`, associated with the run. It contains full 24-seed JSON and **six replay-qualified SVG plots**. It is **not permanent**: expires **2026-11-07**, and requires a separate archival decision before expiration. Do not silently substitute this document for the original JSON.
- An earlier two-seed, three-generation smoke test was included in the same workflow; its hash `b7bcabbf71ccf9db29dec3ffacc49e5e84de2d6905f2c67c626bfed523d83484` is **engineering evidence only**, not a separate confirmation.
- The public seeds are integer identifiers `20261009` through `20261032`, not dates, and the source and protocol are public.

## Research design (all public synthetic conditions)

- 24 seeds, 12 generations, 8 policies, four scalar response families including an oscillatory rare band. Independent per-band quadratic student, not an LLM.
- Shared, fixed initial 32 trusted labels; 64 curriculum-selection labels; 192 in-domain final-test labels; 192 shifted-domain final-test labels per seed.
- Each oracle-assisted policy used exactly **96 new truth-label queries / seed** (8/generation × 12 generations). `pseudo_only` used **0 new truth-label queries** after the initial anchors. The 480 initial/selection/test references are generated *once per seed and shared*, not newly created 480 times per policy.
- Candidate pool balanced at six unlabeled examples per band per generation; **natural allocation weights** [0.50, 0.25, 0.20, 0.05] and balanced/error/progress allocation comparators.
- Held-out in-domain and shifted-domain test labels are **never** consulted by training or curriculum selection. The separately fixed curriculum-selection labels are used for adaptive policy decisions and must be included in oracle-access accounting.
- Direct oracle, gold replay and mixed pseudolabel arms use different numbers of **training updates**, carefully separated from truth-label query counts.
- The exact mathematical reference oracle shares a process with the models, not a confidential independently privileged subsystem.

## Measured 24-seed averages

Lower macro MSE is better. These are descriptive arithmetic means of the completed publicly seeded runs, **not significance or superiority tests**.

| Arm | Final in-domain MSE ↓ | Shifted-domain MSE ↓ | Rare-band MSE ↓ | New truth queries / seed | Training updates / seed | Rejected / seed |
|---|---:|---:|---:|---:|---:|---:|
| `gold_natural` | **0.083416** | **0.171133** | 0.291986 | 96 | 96 | 0 |
| `gold_balanced` | 0.084934 | 0.178317 | 0.288228 | 96 | 96 | 0 |
| `gold_error` | 0.086338 | 0.188734 | **0.278041** | 96 | 96 | 0 |
| `gold_progress` | 0.084902 | 0.180427 | 0.295505 | 96 | 96 | 0 |
| `checked_progress` | 0.099573 | 0.212315 | 0.314101 | 96 | **67.42** | **28.58** |
| `mixed_pseudo` | 0.090075 | 0.185261 | 0.298590 | 96 | **288** | 0 |
| `gold_replay` | 0.091157 | 0.182781 | 0.332550 | 96 | **288** | 0 |
| `pseudo_only` | 0.137718 | 0.272113 | 0.345949 | **0** | **288** | 0 |

The average initial in-domain MSE was `0.106079` across every arm. The ordinary direct-`gold_natural` policy beat `checked_progress` in **23/24 seeds** on final in-domain MSE. The proposed checked policy beat direct `gold_progress` in only **4/24 seeds**. No defensible claim of improved label efficiency follows.

**Negative finding:** In this toy setting, using the exact simulator as a label checker and then training on an admitted *noisy pseudolabel* wastes observable information compared with directly training on the queried oracle's true answer. Label rejection reduced checked-policy training updates to ≈67/96 while consuming the same 96 truth queries. The direct gold policy retains the superior information path. The protocol remains **NOT VALIDATED for real models**.

**Rare-case exception to the aggregate ranking:** The `gold_error` arm produced the lowest *mean rare-band MSE*, despite trailing `gold_natural` on macro in-domain error. This is a resource-allocation tradeoff and illustrates why the rare-band metric must not be hidden.

**Compute ablation:** `gold_replay` and `mixed_pseudo` consumed 288 model updates vs 96 for direct oracle arms, and their mean errors did not beat the simplest oracle policy here. Extra computation without additional truth did not produce a consistent improvement on this fixture.

## Provenance-aware coverage: a useful post-run observation

The following interpretation is **exploratory post hoc**, not a registered proof of novelty.

The fixed initial truth-labeled anchor examples cover a mean **0.6458** of the 32 band-by-x cells. By generation 12:

| Arm | Directly gold-labeled training-cell coverage | All accepted training-cell coverage | Oracle-queried input-cell coverage |
|---|---:|---:|---:|
| `gold_balanced` | 0.9909 | 0.9909 | 0.9909 |
| `gold_natural` | 0.9466 | 0.9466 | 0.9466 |
| `checked_progress` | **0.6458** | **0.8750** | 0.9284 |
| `mixed_pseudo` | 0.9466 | **1.0000** | 0.9466 |
| `pseudo_only` | **0.6458** | **1.0000** | **0.6458** |

The pseudolabel-only arm reaches full **input-cell representation in its training updates**, but it gains no new true-gold label coverage. This demonstrates why *dataset diversity alone* is insufficient as a measure of acquired reliable evidence in this experiment. `checked_progress` queried new oracle evidence but elected to train on admitted pseudolabels instead; its gold-label *training* coverage remained at the initial level. A checked pseudolabel is not automatically a true measurement.

This separation was defined in the preregistered amendment before outcomes; focusing on it as the main explanation after seeing results is still exploratory.

## Figures and availability

Six generated, replay-qualified SVG charts are stored with the raw JSON in the GitHub Actions artifact:

1. `vsc002_in_domain_mse.svg`: macro in-domain learning trajectory, generations 0–12.
2. `vsc002_shifted_mse.svg`: shifted-domain error versus generation.
3. `vsc002_rare_band_mse.svg`: rare-band retention and regression.
4. `vsc002_gold_label_diversity.svg`: direct truth-labeled coverage, not simply accepted synthetic examples.
5. `vsc002_accepted_label_diversity.svg`: all accepted-example coverage, explicitly not necessarily truth.
6. `vsc002_oracle_vs_compute.svg`: equal oracle-call limits versus unequal training-update costs.

Each graphic labels the work **PUBLIC / EXPLORATORY / NOT VALIDATED / NO LLM**, and is generated only after independent semantic replay. Artifacts expire in 30 days; the generator and digest allow reproduction, but exact original bytes should be retained outside short-lived CI artifacts if cited as historical evidence.

## Claims supported, refuted, and untested

**SUPPORTED IN THIS SIMULATION:** fixed new-label budgets, separate final test sets, independent deterministic replay, exercised invalid-evidence mutation rejection, practical divergence of checked vs true gold training, longitudinal rare/shift MSE reporting, and provenance-separated training coverage.

**NOT SUPPORTED AS A BENEFIT:** the verification-aware checked-pseudolabel curriculum did **not** beat direct gold learning at the same new-label budget in this run. Pure pseudolabel training worsened error in this configuration. These are negative results retained in public view.

**UNTESTED / CANNOT INFER:** open-ended human text generation, semantic knowledge acquisition, recursive pretraining, language-model collapse resistance, true oracle isolation, real-world data scarcity, causal robustness of future training algorithms, and novelty/non-infringement.

The record passes an independent implementation of the same mathematical assumptions. That is **consistency, not world truth**, and both code paths can share a conceptual error.

## Next decision before VSC-003 (proposal only)

Do **not** silently alter VSC-002 after seeing its results. Instead, preregister a new experiment targeting the failure:

1. `checked_gold_fallback`: when the oracle label has already been purchased, compare training on admitted pseudo-y versus the **actual oracle label** and an explicit refusal-only control at equal costs.
2. **Quality per truth-query and per model-update:** separate selection value from rejection-induced loss of training opportunity; compare oracle-labeled progress and natural/balanced allocations.
3. Independent oracle scarcity model: a verification query may cost less than labeling, or may return only a reject/pass bit. **Without a distinct cost/information asymmetry, the original checking mechanism has little reason to outperform direct gold.**
4. Document the meaningful causal claim and predeclare strong attacks/negative outcomes before fresh runs.
5. Add realistic shift, rare-case subsampling, and *separate* uncertainty calibration if data allow. For a real language model, first establish OS-level evaluator isolation.

## Rights and historical preservation

This experiment references ideas from [QUASAR](https://github.com/holland202/quasar) (root MIT) and [Coverage-Preserving Synthesis](https://github.com/holland202/coverage-preserving-synthesis) (all rights reserved; **no code imported**). Other relevant prior art includes pseudolabel self-training, active curricula, replay, conformal prediction, and label validation. Novelty is **NOT ESTABLISHED**.

No Azure credits, OpenAI API tokens, large-model execution, third-party source imports, historical evidence overwrites, or merges to `main` occurred in this VSC-002 work.
