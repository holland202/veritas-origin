# VSC-001 — Verifiable Synthetic Curriculum: prospective exploratory protocol

**Registration status:** prospective **EXPLORATORY ENGINEERING DESIGN**, before first VSC-001 execution. **Not confirmatory. Not validated. Not a solution to human-text scarcity or model collapse.**

**Question:** When mathematical simulation provides independently checkable training labels, does checking synthetic labels and allocating generation budget by measured *positive learning progress* outperform naive recursive pseudolabel training and simpler verified controls under matched proposal budgets?

## Sources and intellectual-property boundary

- [QUASAR @ ba050b640b791d79d4cfcf5266f01cfd406124a7](https://github.com/holland202/quasar/tree/ba050b640b791d79d4cfcf5266f01cfd406124a7) — self-generated simulated trajectories, learning-progress curriculum and negative result F16. MIT root license. Referenced as prior research; **no QUASAR code copied into this experiment**.
- [Coverage-Preserving Synthesis @ a90f8dbd4e4ac736226ceb04119a996fd641d46d](https://github.com/holland202/coverage-preserving-synthesis/tree/a90f8dbd4e4ac736226ceb04119a996fd641d46d) — split-conformal and synthetic-residual hypothesis. **All rights reserved** in its LICENSE; referenced conceptually, **no source copied**.
- [Veritas Companion](https://github.com/holland202/veritas-companion) — cost-aware inference; no adapter or code use in VSC-001.
- Established prior art: supervised simulation/domain randomization, self-training, self-training collapse risks, active curriculum learning (including Graves et al. 2017), data validation, conformal prediction (Vovk et al.), residual bootstrapping (Efron), and experimental design. **No originality or patent clearance established by this survey.**

## Threat to the hypothesis

A verifying policy might look better only because it uses more simulator calls, gets privileged evaluation feedback, discards hard samples, or is compared only with a weak recursive-self-label condition. **Therefore include strong direct-oracle and verified-nonadaptive controls, report actual simulator calls, and keep final held-out data out of selection.**

## Frozen toy domain and budgets for the exploratory smoke

- Four deterministic scalar response families on x ∈ [-1,1]. Three polynomial-like bands of different difficulty and one high-frequency oscillatory band. Domain selection/parameters are **synthetic mathematical exercises**, not natural-language understanding or real-world observations.
- Student is a deliberately limited independent per-band polynomial predictor with a three-dimensional fixed feature map [1, x, x²]. This low-capacity model is not an LLM.
- Per experimental seed: initial trusted labeled pool: 8 per band; curriculum-selection validation pool: 16 per band; *separate* conformal-calibration pool: 32 per band; final untouched test pool: 64 per band. Validation data cannot train the model, and conformal/test data cannot choose samples.
- Ten rounds, twenty-four candidate training examples per round, deterministic pseudo-random task splits and proposal streams. Six policies, each with identical starting weights and initial training examples. See source constants for all exact numeric values.
- Natural candidate distribution: [0.50, 0.25, 0.15, 0.10]. Strong balanced oracle control: uniform band probabilities.
- Controlled generated-label corruption probability: 0.22; a selected candidate may be shifted by ±1.8 (a specified injected defect, not representative natural model hallucination).
- Verification accepts offered labels only if they match the independent simulator oracle within tolerance 1e−9; rejected examples are logged and **not silently replaced**. This verifier knows the ground-truth function: its calls **must be counted** as privileged oracle access.
- Adaptive allocation uses **positive decreases** in curriculum-validation squared error from the previous round, never absolute error changes. It allocates 60% to normalized positive progress and 40% to the natural candidate distribution; if all progress values are zero, use the natural distribution. The test labels cannot influence these weights.
- Do not promise that verification-aware adaptive wins. A uniform verified or oracle-labeled control may be superior.

## Arms

| Policy | Candidates and label source | Verification | Candidate distribution |
|---|---|---|---|
| `oracle_natural` | Direct trusted simulator labels | Native ground truth; no separate check | Natural |
| `oracle_balanced` | Direct trusted simulator labels | Native ground truth | Uniform |
| `noisy_natural` | Simulator-derived synthetic labels, with injected faults | None | Natural |
| `verified_natural` | Same synthetic generation and injected faults as noisy_natural | Additional independent oracle check, rejects faults | Natural |
| `verified_progress` | Synthetic generation and injected faults | Same oracle check | Positive validation-progress allocation |
| `recursive_natural` | Learner predictions + stochastic pseudo-label noise | None; never accesses oracle for new candidates | Natural |

Every policy gets the same **number of proposed examples**, same initial oracle-labeled set and same fixed calibration/test split. **They do not get the same oracle-call cost**: direct-oracle costs one simulator call/candidate, generated-label checked policies use two, recursive uses none after initialization. Report separately rather than falsely claiming comparable ground-truth budgets.

## Outcomes (descriptive, not confirmation)

For each policy and seed record: final held-out macro MSE, worst-band/oscillatory-band MSE, signed improvement from initial state, examples accepted/rejected, false-labels admitted, full oracle call count, mean compute-cost proxy, and nominal 90% split-conformal held-out coverage and interval width. Calibration is separate from curriculum selection; nominal coverage is not guaranteed under distribution shift.

Report per-seed paired differences with both directions and retain **all negative results**. No post-hoc superiority threshold. Before a future C1, freeze distributions, seeds, benchmarks, target effect, uncertainty analysis, artifact hashes, resource/cost constraints and statistical inference policy.

## Reproducibility and preservation

- Default CLI is dry unless `--pilot` explicitly opts into simulated execution.
- Evidence only created with a unique path using exclusive create (never overwrite). Default `evidence/vsc001/`.
- SHA-256 printed for independently pinned evidence, not inferred authentication.
- Standalone checker must reject malformed JSON, duplicate keys, missing arms, impossible aggregate values, mislabeled evidence states, corrupted oracle labels and altered trajectories, including rehashed forgeries.
- GitHub CI runs all positive/negative controls and a **PUBLIC_TEST_SEED** engineering smoke. These smoke fixtures are not unseen holdout scientific evidence.

## Limits and release gates

**Unmet**: real-data transfer, recursive foundation-model training, human-data replacement, distribution shift, oracle secrecy from hostile co-resident processes, source/license clearance beyond the reviewed references, LLM token/cost accounting, energy-efficiency claims, human/general intelligence, and independence of the oracle outside this simulation.

A successful toy pilot means only that *this mathematical experiment* is replayable and the measured outcomes hold for its stated conditions. Original repositories and historical evidence are kept unchanged. Model training, Azure use and third-party imports require a separate decision.
