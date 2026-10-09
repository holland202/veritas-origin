# Artificial Computational Biology — research program within VERITAS ORIGIN

**Working framework, not a newly established discipline or a claim that AI is biologically alive.** The phrase *artificial computational biology* is used here as a practical organizing metaphor: study the measurable structure and dynamics of computational learning systems. Existing fields—machine learning, dynamical systems, information theory, neural computation, artificial life, control theory, and mechanistic interpretability—provide the scientific foundations.

## Core premise, stated in testable terms

Humans use electrochemical processes in biological nervous tissue. Artificial neural networks instead use numerical states, parameterized functions, electronic circuits and algorithms. Both can implement learning, signaling and feedback **without being the same physical mechanism**.

This research program asks:

> Can a small artificial neural network generate internal regulatory variables from its own measurable learning dynamics, use those variables to change weight updates, and thereby exhibit better sequential adaptation/stability than ordinary optimizers under matched input and training opportunities?

That is an empirical question, **not a presumption of success**.

A second, independent question concerns **internal computation at inference time**, not weight learning: can a trained recurrent system use extra hidden-state updates and allocate them effectively under an actual runtime budget? ITC-001 studies that separately and preserves the failures of adaptive allocation and actual wall-time speedup.

## Layers of the artificial system

| Working analogy | Actual technical objects | Measurement |
|---|---|---|
| Anatomy | Network layers, tensor sizes, parameter graph | Parameter count and exact architecture |
| Signaling | Activations, gradients, transient state | Forward/backward traces and norms |
| Plasticity | Weight changes induced by training | Model weights, update magnitudes, loss |
| Regulation | Mathematical gain computed from recent gradient/loss state | Modulator trajectory and ablations |
| Memory | Retention of previously learned input-output behavior | Earlier-task error after switching tasks |
| Resource use | FLOPs, energy, bandwidth, temperature | Must be measured, not assumed from step count |
| Experimental integrity | Frozen seeds, genuine held-outs, unedited artifacts | Independent replay, separate assessment |
| Authorization | External human approval of interventions | Not a built-in neuron/chemical, no automatic permission |

A gate such as [Sovereign Veritas](https://github.com/holland202/sovereign-veritas) belongs to the **external authorization layer**, not the artificial neuron physiology. It can prohibit unauthorized learning/deployment actions; its internal consistency result is neither world truth nor a description of the learning mechanism.

## Experiments in this repository

| Project | Question | Status |
|---|---|---|
| [ASP-001](../experiments/asp001/PROTOCOL.md) | Does error/gradient-based self-generated update modulation improve sequential learning? | **Prospectively registered exploratory NumPy experiment; not validated** |
| [ITC-001](../experiments/itc001/PROTOCOL.md) | Do repeated latent neural updates and a confidence-based stop rule improve accuracy per unit of computation? | **H1 depth benefit met exploratory threshold; H2 adaptive allocation NOT SUPPORTED; masked runtime slower in post-hoc test** |
| [EXP003-P0](../experiments/exp003/README.md) | How efficiently do known policies disambiguate a controlled hypothesis set? | **Archived exploratory mathematical pilot, 100% completion ceiling** |
| [VSC-001](https://github.com/holland202/veritas-origin/pull/7) | Does verified synthetic curriculum improve a simple student? | **Draft exploratory study** |
| [VSC-002](https://github.com/holland202/veritas-origin/pull/8) | Does validation help under matched exact-label budgets over generations? | **Draft exploratory negative result** |
| [VSC-003](https://github.com/holland202/veritas-origin/pull/9) | Do low-cost imperfect binary checks outperform exact truth acquisition? | **Draft exploratory negative result** |
| [RA-001](https://github.com/holland202/veritas-origin/pull/10) | Can historical claims be pinned and kept distinct from authorization? | **Draft engineering-assurance work** |
| [EBA-001](https://github.com/holland202/veritas-origin/pull/11) | Can mathematical transcript validity conceal evaluator contamination? | **Draft synthetic research** |
| [C1-001](https://github.com/holland202/veritas-origin/pull/12) | Can Linux DAC deny known illegal access while legal probes still work? | **Draft bounded Linux engineering test** |

These pull requests are **not on `main` until merged** and do not collectively establish scientific confirmation. Their separate branch histories and negative outcomes remain intact.

## Related independent source repositories

- [QUASAR](https://github.com/holland202/quasar) — mathematical generator/learner/curriculum work; its previously published negative results motivate strong baselines, not a reason to assume plasticity helps.
- [Sovereign Veritas](https://github.com/holland202/sovereign-veritas) — fail-closed gate for externally authorized actions; not model consciousness or artificial chemistry.
- [EACE](https://github.com/holland202/eace) — evidence can be fabricated even when internally consistent.
- [Veritas Evaluation Harness](https://github.com/holland202/veritas-eval-harness) — evaluator contamination and honest-method false accusations.

These retain separate identities and licenses. This research program **does not copy or absorb** entire external repositories as if all code shared the same license.

## Scientific guardrails

- Draw analogies only when they lead to operational definitions and falsifiable predictions.
- Do not claim intelligence, conscious experience, real neurotransmitters, biological equivalence, emergent organisms, model immunity, or safe autonomy without matching evidence.
- Compare against fixed SGD, adaptive Adam, time-only schedules and constant-gain ablations; report all outcomes, not only the best.
- Separate mathematical simulation from training an actual network; separate either from a real-world model.
- Keep hidden evaluations out of optimizer feedback and keep code/protocol/evidence pinned.
- Store a known negative as a known negative; results and labels are not upgraded after observation.
- Tests and byte hashes establish bounded integrity/consistency, **not** independent world truth, scientific novelty, or human authorization.

**Next threshold only after ASP-001:** if modulation passes credible controls, preregister an unseen-task replication using a new seed range and at least one qualitatively different network/data setting. If it fails, preserve the failure, investigate causal mechanisms, and do not retroactively tune the registered hypothesis.
