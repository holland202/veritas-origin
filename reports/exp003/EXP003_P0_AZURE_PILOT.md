# EXP003-P0 — Azure exploratory pilot analysis

**Project:** VERITAS ORIGIN  
**Observed run (UTC):** 2026-10-08 20:27:05 (from evidence filename)  
**Status:** `EXPLORATORY_SIMULATED — NOT VALIDATED`  
**Disposition:** Preserve outcome and ceiling effect. Do not reclassify as confirmatory.

## Immutable evidence and source lineage

- Evidence: `evidence/exp003/exp003-p0-20261008T202705724022Z-146bee1a.json`
- Reported Azure SHA-256: `627eb778e8eef80d9d664c9ac6f3b7743d51e6a97a677eea8cac51e79b467333`
- Experiment runner/replay worktree source: `5807d7bd3fb6582239a77b4730fdcf42cfa71d62`
- Original evidence archive commit: `3a749351dea260b8fe3812e3c0b35ac04b94cbf3`
- Input seeds: 0..11 inclusive.
- Strategies: fixed, random, greedy.
- Four hypotheses per task, maximum six binary probes, 12 tasks per strategy.

The SHA-256 was printed by the Azure experiment and successfully checked by the stand-alone verifier on Azure before archival. This report recomputes descriptive values from the JSON published to GitHub. These steps are consistency checks, **not an independent physical-world oracle**.

## Observed descriptive results

| Strategy | Tasks solved | Total probes | Mean probes/task | Mean hypotheses remaining | Deferred |
|---|---:|---:|---:|---:|---:|
| Fixed | 12/12 | 35 | 2.9167 | 1.0 | 0 |
| Random | 12/12 | 27 | 2.2500 | 1.0 | 0 |
| Greedy information gain | 12/12 | 24 | 2.0000 | 1.0 | 0 |

**Post-hoc diagnostic:** mean probes/task was not the designated success criterion in P0; it is reported to understand the observed 100% completion ceiling. Do not promote it into a confirmatory endpoint after seeing outcomes.

Relative to fixed, greedy used 11 fewer probes (31.43% fewer) on the same 12 seeds. Relative to random, greedy used 3 fewer probes (11.11% fewer). These comparisons are descriptive and unadjusted.

## Individual seed results

| Seed | Fixed | Random | Greedy |
|---|---:|---:|---:|
| 0 | 3 | 2 | 2 |
| 1 | 3 | 4 | 2 |
| 2 | 4 | 3 | 2 |
| 3 | 2 | 3 | 2 |
| 4 | 5 | 1 | 2 |
| 5 | 3 | 3 | 2 |
| 6 | 3 | 1 | 2 |
| 7 | 3 | 2 | 2 |
| 8 | 2 | 2 | 2 |
| 9 | 3 | 1 | 2 |
| 10 | 2 | 2 | 2 |
| 11 | 2 | 3 | 2 |

Paired outcomes: greedy vs fixed was better/equal/worse on **8/4/0** seeds; greedy vs random was **5/4/3**. Random sometimes selected an informative probe that isolated the true hypothesis immediately, despite a worse average.

## Replay and analysis commands

From the archived EXP003-P0 Git tree:

```bash
FILE=evidence/exp003/exp003-p0-20261008T202705724022Z-146bee1a.json
SHA=627eb778e8eef80d9d664c9ac6f3b7743d51e6a97a677eea8cac51e79b467333
printf '%s  %s\n' "$SHA" "$FILE" | sha256sum -c -
python3 tools/verify_exp003_p0.py "$FILE" --sha256 "$SHA"
python3 - "$FILE" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
for p in data["policies"]:
    rows = sorted((r for r in data["results"] if r["policy"] == p),
                  key=lambda r: r["seed"])
    counts = [len(r["records"]) for r in rows]
    print(p, "count=", len(rows), "probes=", sum(counts),
          "mean=", sum(counts)/len(counts), "by_seed=", counts)
PY
```

The standalone verifier reported `CONSISTENT WITH EXP003-P0 SPECIFICATION` across **36 task/policy evaluations and 86 probes**, after the evidence digest matched. Earlier EXP003-P0 behavioral/adversarial tests passed 17/17 on Azure. The GitHub CI suite also passed.

## Falsification, failure and scope controls

1. **Outcome ceiling:** all policies solved all tasks within six probes. The original completion metric is nondiscriminative on this sample.
2. **No model evaluated:** fixed, random, and greedy are deterministic programmatic selection strategies. These observations do not establish AI hypothesis generation or autonomous scientific research.
3. **Small public task space:** only eight public predicates, four candidates per task, deterministic fixtures, 12 seeds and noiseless binary observations. Sampling/generator artifacts or oracle leakage can distort conclusions.
4. **Greedy is not uniformly superior to random per seed:** on three individual seeds, random used fewer probes.
5. **No post-hoc success claim:** means and percentages here are descriptive diagnostics discovered after the observed ceiling. No p-values, confidence-interval-based guarantees, extrapolation or threshold promotion are asserted.
6. **Verifier limitation:** the verifier independently implements checks but shares task specification and Python RNG assumptions. A consistency result does not prove generalization, oracle isolation, or authenticity of the real world.
7. **No external model sandbox:** the external command adapter is only a local subprocess. Do not give it secrets or privileged tools, and do not confuse `--pilot` with a strong capability gate.

## Next experiment gate

Retain the original P0 result unchanged. Before a new confirmatory model comparison, specify and freeze: harder tasks and appropriate probe budgets, held-out evaluation distribution, oracle isolation, model artifact hash/decoding settings, token/latency/resource costs, a greedy baseline, primary efficiency and correctness endpoints, rejection/timeout criteria, and versioned verifier. P0 remains exploratory even if later protocols change.
