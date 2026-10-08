# VSC-001 — Public-fixture exploratory pilot (October 8, 2026)

**STATUS: EXPLORATORY_SIMULATED — NOT VALIDATED.** This is a five-seed *toy mathematical* experiment. It is neither a held-out external benchmark nor evidence of solving the data wall, model collapse, recursive LLM training, or real-world generalization.

## Preservation and provenance

- Frozen exploratory protocol: [`experiments/vsc001/PROTOCOL.md`](../../experiments/vsc001/PROTOCOL.md), committed before the study.
- Code, independent verifier, tests, and full experiment configuration: [`src/origin/vsc001.py`](../../src/origin/vsc001.py), [`tools/verify_vsc001.py`](../../tools/verify_vsc001.py) and [`tests/test_vsc001.py`](../../tests/test_vsc001.py).
- **GitHub run:** [37850327563](https://github.com/holland202/veritas-origin/actions/runs/37850327563).
- Tested branch revision: `33c2aa370876f0f031158e1dd1dd16306c4c3d3f`.
- Public test seed base `20261008`; seeds `20261008..20261012`; ten rounds; 24 candidate examples per round; six policies; 5 seeds × 6 policies × 240 = **7200 candidate events**.
- Raw complete evidence archive: GitHub Actions artifact **`vsc001-public-fixture-evidence`**, ID `11581966445`, attached to the above run. **Retention is 30 days; it is not yet a permanent repository archive.** Preserve/downstream-copy with independent digest before expiration if the run becomes central evidence.
- Raw JSON **SHA-256:** `81dc4c71059a18429c4e1800092771ff3f6511ef4c7d9a174df498cd5021ae9f`. This digest is a byte-integrity reference, not proof of independent truth, oracle isolation, or data rights.
- GitHub CI: **33/33 tests passed**, independent VSC-001 semantic replay passed, original EXP003-P0 evidence hash/replay passed.
- Earlier, much smaller **two-seed engineering smoke** run and debugging revisions are visible in workflow history, not promoted to independent confirmation. An intermediate CI failed because the new oracle-accounting fields were added to the runner before its independent verifier was updated; subsequent workflow runs passed after a separate verifier update. No failed record was erased.

## Measured outcomes

Five public synthetic seeds; lower final test MSE is better. All values below are means over five seeds, *not inferential estimates*.

| Policy | Final macro test MSE ↓ | Change from initial MSE (positive=improvement) | Training-oracle calls / seed | Total allocated oracle calls / seed | Mean accepted / 240 | Mean rejected / 240 | Mean intentionally corrupted labels admitted |
|---|---:|---:|---:|---:|---:|---:|---:|
| oracle_balanced | 0.064245 | +0.028154 | 272 | 720 | 240 | 0 | 0 |
| oracle_natural | 0.066748 | +0.025651 | 272 | 720 | 240 | 0 | 0 |
| noisy_natural | 0.134006 | −0.041608 | 272 | 720 | 240 | 0 | 55.2 |
| verified_natural | 0.068666 | +0.023732 | 512 | 960 | 184.8 | 55.2 | 0 |
| verified_progress | 0.061947 | +0.030452 | 512 | 960 | 185.2 | 54.8 | 0 |
| recursive_natural | 0.116508 | −0.024110 | 32 | 480 | 240 | 0 | 0 injected |

**Accounting note:** each policy starts from 32 trustworthy training labels. Direct-oracle candidates use one oracle call each; generated-label verified candidates use two; recursive candidates use no further training-oracle calls. Each policy is allocated the *same fixed* selection (64), conformal (128) and final test (256) reference labels—448 reference labels—not 448 independent extra calls per arm when executed in the shared simulator. Repeated scoring of cached selection examples is recorded separately, not counted as repeated oracle calls. Total allocated oracle counts are a **comparison proxy**, not actual cloud billing or independently controlled environment costs.

### Per-seed final held-out macro MSE

| Public seed | oracle_balanced | verified_natural | verified_progress |
|---|---:|---:|---:|
| 20261008 | 0.065995 | 0.064294 | 0.058453 |
| 20261009 | 0.066902 | 0.060221 | 0.061194 |
| 20261010 | 0.066507 | 0.083889 | 0.062532 |
| 20261011 | 0.058980 | 0.066355 | 0.064399 |
| 20261012 | 0.062840 | 0.068574 | 0.063157 |

`verified_progress` had a slightly lower **mean** MSE than the balanced-oracle control (0.061947 vs 0.064245), but beat it on only **3/5** seeds while using **512 vs 272** training oracle calls. It beat `verified_natural` on **4/5** seeds at the same nominal training-oracle budget but with a different candidate-sampling distribution. **No superiority or efficiency claim is justified.**

The injected corruption test operated: the unchecked synthetic arm admitted 55.2 intentionally corrupted examples on average and had much worse test error under this deliberately adverse corruption mechanism. The verified arms admitted zero of these injected faults *under an exact mathematical oracle*. That does **not** imply similarly reliable detection of subtle or real-world label errors.

The recursively pseudolabeled baseline worsened relative to its initialization in this toy domain. This is not evidence that language models universally collapse when trained on synthetic data.

### Uncertainty diagnostic

Mean nominal-90% split-conformal test coverage: balanced oracle 0.9250, verified natural 0.9234, verified progress 0.9188, noisy natural 0.9367 and recursive natural 0.9117. These are *empirical metrics on shared simulated distributions*. Coverage alone doesn't establish soundness under covariate shift, adversarial dependence, nonexchangeable data or live observations.

## Research implications and limitations

The most defensible conclusions are **engineering claims**: (1) deterministic study and independent replay agree under this specification; (2) deliberately corrupted synthetic labels degrade a low-capacity learner here; (3) exact-oracle rejection blocks this particular injected corruption; (4) progress-weighted generation works mechanically but is not shown to be cost-effective over strong baselines.

A stronger result is **NOT SUPPORTED** because:
- Student is a toy per-band polynomial predictor, not a language model; generation is a mathematical simulator, not novel human-level knowledge.
- Simulator truth is exposed to the host process and the generator itself; this is *not independent oracle security* or synthetic-data truth certification.
- At fixed proposal counts the policies use unequal true-oracle calls; verifying by additional oracle access can cost more than direct oracle labels.
- We chose a tiny five-seed public sample after earlier exploratory engineering smoke and did not freeze a confirmatory threshold, power analysis or a previously unseen task distribution.
- The "recursive collapse" baseline is a deliberately weak self-pseudolabel method with noise; comparing only to it would be misleading.
- Need adversarially subtle corruptions, strong cost-matched controls, held-out distribution changes and multiple true domains before extending conclusions.

## Next falsification experiment proposal: VSC-002 (NOT RUN)

1. Freeze a distinct held-out family and larger seed count **before** seeing its outcomes.
2. Force identical oracle-call budgets: compare verified-progress to verified-natural, gold labels at same cost, gold-balanced, active-learning, progress-only *without verification*, and a direct-oracle prioritization baseline.
3. Vary corruption from zero through deliberately subtle shifts, selection/calibration distribution shifts, and rare-case prevalence; report false rejection and coverage degradation as primary endpoints.
4. Make learning-progress decisions on a fixed separate selection set; test whether natural-candidate imbalance and exploration floor cause rare-case starvation.
5. Replicate on a pinned QUASAR simulator through a **separate adapter**, after revisiting specific source/license and integrity checks. No code copied yet.
6. Preserve positive and negative evidence, cost, runtime and artifacts. A C1 confirmatory protocol is distinct from VSC-002 exploratory exploration.

**Prior art:** established supervised simulation, active curricula, self-training, label validation, and conformal uncertainty. QUASAR (MIT) and Coverage-Preserving Synthesis (**all rights reserved**) are credited conceptual influences. No third-party code is imported here; novelty **NOT ESTABLISHED**.
