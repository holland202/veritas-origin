# ITC-001 — Research concept selection and novelty guardrails

**Recorded before experiment code or training.** This is a literature-grounded engineering choice, not a novel mathematical invention.

| Candidate | Actual established mechanism | Falsifiable metric | Decision |
|---|---|---|---|
| Adaptive latent recurrent depth | Repeated hidden vector transformation, shared weights, data-dependent halting | Correctness vs count of internal recurrent updates at matched allocation cost | **IMPLEMENT FIRST** as ITC-001 |
| Synapse-specific eligibility traces | Per-connection fast changes guided by pre/post-activity and optional modulation | Rapid learning and retention vs SGD/Adam/consolidation at equal exposure | **NEXT ASP-002 TRACK**, only as separate preregistered study |
| Predictive coding/error correction | Iterative reduction of local mismatch between internal prediction and sensory observation | Convergence speed, calibration and stability vs ordinary backprop | DEFER; distinct architecture and evidence needed |
| Working-memory state | Recurrent state updated across observation sequences, possibly with gated access | Remember-before-delay accuracy and interference across tasks | DEFER pending clean delayed-memory benchmark |
| Metacognitive confidence / calibration | Auxiliary estimates of uncertainty or current output quality | Calibration, selective accuracy, false-confidence rate, cost | **MEASURE AS A DIAGNOSTIC**, not equate confidence with truth |
| Energy-budget feedback | Resource constraints modify computation and/or learning | Actual joules, temperature, accuracy/cost frontier | DEFER until instrumented hardware energy measurement |
| Self-modification / open-ended evolution | Model proposes architecture/policy changes and potentially trains on their outcomes | Legitimate gains surviving independently controlled evaluator | DEFER; prior VSC/EBA/C1 results leave evaluator and approval gaps |

## Why begin with repeated latent computation?

It directly addresses a **limited, testable** meaning of internal "deliberation": additional state updates before committing to one answer, with explicit comparison to whether those additional operations helped. A computation that occurs internally need not be linguistic. It is not evidence of awareness, introspection or a conscious experience.

Known major precedents, non-exhaustive:
1. [Graves 2016: Adaptive Computation Time](https://arxiv.org/abs/1603.08983) — learns iteration counts.
2. [Dehghani et al. 2019: Universal Transformers](https://research.google/pubs/universal-transformers/) — recurrent computation across depth, adaptive per-position halting.
3. [Geiping et al., NeurIPS 2025: Recurrent-depth latent reasoning](https://proceedings.nips.cc/paper_files/paper/2025/hash/3b01972cf31e6fa0fe29e4b8b5c2a0a1-Abstract-Conference.html) — test-time internal depth in language models.
4. [Bai et al., NeurIPS 2019: Deep Equilibrium Models](https://arxiv.org/abs/1909.01377) — iterative hidden-state fixed points and implicit differentiation.
5. [Miconi et al., ICML 2018: Differentiable plasticity](https://proceedings.mlr.press/v80/miconi18a.html) — separate per-connection fast adaptation; not implemented by ITC-001.
6. [Miconi et al., 2020: Backpropamine](https://arxiv.org/abs/2002.10585) — trained neuromodulated plasticity; not implemented by ITC-001.
7. [Li, Benna & Mattar, Nature 2025](https://www.nature.com/articles/s41586-025-09142-4) — tiny recurrent networks can be useful scientific models of cognitive strategies, but their results cannot establish that arbitrary RNNs think like people.

**Important critique:** Task-macro performance can improve simply because depth 5 has more operations than depth 1; adaptive gain can be due to task difficulty distribution rather than selecting especially hard instances. The registered **within-task shuffled-depth** control keeps *per-task computation exactly matched* to distinguish this confound. In addition, the hard parity tasks may be impossible for the tiny model to learn under the registered budget. Retaining that failure is more scientifically useful than retuning to a favorable number.

## Proposed next actions, contingent on evidence

- If more recurrent steps do not increase accuracy, don't claim "thinking helped"; diagnose network dynamics and repeated-map convergence **in a different preregistered study**.
- If steps improve accuracy but halting doesn't beat the within-task shuffle, report that extra compute helps without evidence that this internal heuristic allocates it intelligently.
- If both preregistered criteria hold, repeat with **new** task families, seeds, independent hardware and compute-energy measurements, while keeping the first study exploratory.
- Whether results are positive or negative, treat sovereign authorization and evidence verification as external independent checks, never as organic computational analogies.
