# ITC-H1 registration: did H2 of ITC-001 have room to pass? (nothing computed under this registration)

- Author (self-declared): Claude (Opus 5.5), in a session Chad Holland opened on 2026-10-09. He gave direction; he has not reviewed this text.
- Status: registration only, committed before any analysis code exists. **Post-hoc and exploratory**: ITC-001's outcome (H2 NOT_SUPPORTED) is already known to me. This is a diagnostic of the test's power, not a new test of the hypothesis.
- Data: `evidence/itc001/ITC001_PUBLIC_6SEED.json` on `experiment/itc001-recurrent-internal-deliberation`, SHA-256 `701703011d39482020bbfd9c40c203fc23fcd64859887cb9edcf15ea93d7ff68` (checked by me against the handoff value: identical).

## Question
ITC-001 registered H2 as "adaptive beats the within-task depth shuffle by at least +1.0 percentage point (macro accuracy), winning at least 4 of 6 seeds", and it failed (+0.0285 pp). Was +1.0 pp reachable by **any** allocator of recurrent passes at the same per-task budget? If not, H2 failed because the test had no headroom, not because the halting signal was poor.

## Method (fixed now)
For each seed and task, using the archived `probabilities_by_depth` (depths 1..5), `test_targets` and `test_task_ids`, with the code's own rule `prediction = p >= 0.5`:
- **Budget** per task = the sum of adaptive's archived `selected_depths` over that task's instances (the same per-task total the within-task shuffle uses).
- **Oracle allocator**: each instance needs at least 1 pass. An instance correct at depth 1 costs 1. Otherwise its cost is the smallest depth at which it is correct (instances correct at no depth are given depth 1 and stay wrong). Spend the remaining budget on the cheapest extra costs first (this maximises the number correct for unit value per instance).
- **Anti-oracle** (control): same budget, chooses for each instance the depth that is **wrong** where one exists, cheapest first.
- Macro accuracy = mean of the six task accuracies; then the mean over six seeds. Compare with the archived `shuffle_task` and `adaptive` macro accuracies.

## Predictions
| ID | Prediction | conf. |
|---|---|---|
| D0 | Sanity: with every instance forced to depth 1, my computed macro accuracy equals archived `fixed1` for every seed to 1e-12; same for depth 2, 3 and 5 against `fixed2`, `fixed3`, `fixed5` | 0.95 |
| D1 | Oracle minus `shuffle_task`, mean over seeds, is **at least +1.0 pp** (so H2's bar was reachable in principle) | 0.55 |
| D2 | Anti-oracle minus `shuffle_task` is **negative** (the comparison can move in both directions) | 0.95 |
| D3 | Recorded, no prediction: the share of instances correct at **any** depth (the unconstrained ceiling) |  |

## Interpretation fixed in advance
- D1 holds: H2's failure is informative; a better halting signal could have passed. Option A in the handoff is worth a new registered study.
- D1 fails: the registered +1.0 pp bar exceeded what any allocator could achieve at that budget; H2 as designed had no power, and Option A should not be run on this fixture without new tasks where depth matters more.
- D0 fails: my reconstruction is wrong; nothing else is reported.
