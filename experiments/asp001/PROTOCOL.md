# ASP-001 — Internally regulated synaptic plasticity in a real small neural network

**PROSPECTIVE EXPLORATORY REGISTRATION — recorded BEFORE implementation, training, or outcomes.**
**Status:** `NOT_VALIDATED / NO_CLAIM_OF_NOVELTY`. This is a small numerical neural-network experiment, not an artificial organism, consciousness, a human-brain model, self-evolving AI, or a production learning controller.

## Central question

Can a small, real, backpropagation-trained neural network regulate its own **weight-update magnitude** using signals computed from its own previous errors and gradient directions, improving stability and adaptation relative to conventional training?

The biological analogy is **functional, not literal**: a mathematically computed modulatory factor is not a neurotransmitter, an emotion, or proof of brain-like function. This study uses actual learned neural-network weights and a differentiable two-layer model; it is not a scored rule system masquerading as a network.

### Relevant established research; not a novelty claim

- Thomas Miconi, Kenneth Stanley and Jeff Clune, [*Differentiable plasticity* (ICML 2018)](https://proceedings.mlr.press/v80/miconi18a.html).
- Miconi et al., [*Backpropamine: neuromodulated plasticity* (2020)](https://arxiv.org/abs/2002.10585).
- Kirkpatrick et al., [*Overcoming catastrophic forgetting in neural networks* (PNAS 2017)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5380101/).
- QUASAR and the VSC-001/002/003 negative findings from the owner's separate repositories/experimental branches are **motivation**, not imported source or evidence that regulation helps.

## Frozen implementation and data plan

- `numpy==2.2.6` on GitHub Actions with Python 3.12. NumPy 2.x on Termux is permitted for local educational replication; **byte-exact replay across NumPy versions/architectures is not assumed**.
- Network: real fully connected `1 → 16 tanh → 1 linear` architecture, 49 trainable scalar parameters: weights `W1[1,16]`, `b1[16]`, `W2[16,1]`, `b2[1]`. All baselines use exactly the same architecture/initialization per seed.
- Forward: `h=tanh(x @ W1+b1)`; `ŷ=h @ W2+b2`. Loss: minibatch mean squared error; gradients via explicitly implemented chain-rule backpropagation, not a mock improvement function.
- Initialization: seeded PCG64 NumPy generator; `W1` normal sd 0.5; `b1` zero; `W2` normal sd 0.25; `b2` zero. All arms begin from identical copies; trainable parameters never reset across task phases.
- Train sequence `A → B → A`, exactly **64 minibatches/phase**, **16 examples/batch**, **192 training updates** per seed per arm. No validation data reaches learner, optimizer, regulator, curriculum selector or parameter updates.
- Function A: `0.8 sin(2πx) + 0.2x`. Function B: `0.8 sin(4πx+0.3) - 0.2x + 0.15 cos(πx)`. Inputs train iid continuous uniform `[-1,1]`. All policies get identical numerical training inputs, labels, task order and noisy labels per seed.
- B-phase training label corruption: independently seeded Bernoulli(0.15) additive outlier `±0.75` with equal signs; A is clean. Do not silently treat corrupted B labels as true.
- Held-out evaluation: same fixed 129-point numerical grid on `[-1,1]`, with noise-free exact A/B function values; **never used by training or modulation**. It measures function interpolation on a fixed grid, not fresh unseen stochastic task generalization. All 24 seeds use the same grid but independently initialized models/train draws.
- Public registered full seeds `20261101..20261124`, 24 paired repeats. Initial *engineering smoke only* uses seed `20330101`, 8 steps/phase with the same frozen parameter settings; it has no confirmatory meaning.
- Four checkpoints: init, after first A, after B, after final A. Also report training-loss/modulator traces every 16 updates, and gradient-clip counts.
- Shared Euclidean gradient clipping global norm 5.0 **before** optimizer/regulator for all arms. NaN/Inf fails closed and no data is silently dropped.

## Six frozen arms, equal label/update budget

| Arm | Weight update | Additional nontrainable memory |
|---|---|---|
| `sgd_001` | SGD, constant learning rate 0.01 | none |
| `sgd_003` | SGD, constant learning rate 0.03 | none |
| `sgd_009` | SGD, constant learning rate 0.09 | none |
| `scheduled_sgd` | SGD `η_t=0.03 * (0.75+0.25 cos(πt/192))`, zero-based update index | clock only |
| `adam_001` | Adam, rate 0.01, β₁=0.9, β₂=0.999, ε=1e−8, bias correction | first/second moments |
| `regulated_sgd` | SGD `η_t = 0.03 × m_t` using formula below | prior gradient and exponential loss mean |

Regulator **not permitted** to read task ID, task transitions, held-out score, oracle clean B label, future samples, reference source or other arms' gradients:

- `g_t` is current global-norm-clipped minibatch gradient and `L_t` current minibatch loss computed from labels available to all arms.
- `c_t = dot(g_t,g_(t−1)) / (||g_t||||g_(t−1)|| + 1e−12)`; first batch `c_0=0`. The previous gradient is state carried across task boundaries.
- Prior loss EMA `E_(t−1)` initialized from the first batch `L_0` (first modulation `m_0=1`). For subsequent batches compute `shock_t = clip((L_t-E_(t−1))/(E_(t−1)+0.05), -2,2)`.
- `m_t = clip(1 + 0.35 c_t − 0.30 max(shock_t,0), 0.35,1.4)`.
- **After** applying update `W ← W − 0.03m_t g_t`, set EMA `E_t=0.9 E_(t−1)+0.1 L_t`, prior gradient `g_(t−1)=g_t` (copy). Modulator has no trainable parameters and no access to future labels.
- Record actual modulator min/mean/max, fraction at bounds, gradient cosine, and compute overhead. No claim of fixed equal arithmetic/FLOP/energy cost between algorithms; **number of minibatch labels and optimizer update opportunities** is exactly matched.
- The fixed `sgd_003` arm is the `m_t≡1` ablation; `scheduled_sgd` is a time-only variation control; `adam_001` is a strong off-the-shelf adaptive optimizer baseline.

## Outcome plan registered before running

**Primary endpoint:** after training phase B (after 128 shared updates), `joint_B = (MSE_A + MSE_B)/2` on the untouched clean held-out grids, measured for all arms/seeds. Smaller is better. This forces a stability/adaptation tradeoff rather than rewarding only retention or only learning B.

**H1 exploratory criterion, not proof of superiority:** `regulated_sgd` has lower *paired mean* `joint_B` than **both** `sgd_003` and `adam_001`, and beats each baseline on at least 13 of 24 seed pairs. If any fails, report `H1_NOT_SUPPORTED_IN_THIS_FIXTURE`. The mean effect is compared against every control too; do not select a weaker control after seeing results.

**Secondary endpoints:** A forgetting `MSE_A(after B)−MSE_A(after A1)` (may be negative), clean B MSE after B, A recovery after A2, B retention after A2, whole run minimum/maximum and final MSE, numeric update-budget equality, regulated modulation's actual variability (anti-vacuity), and aggregate paired-seed comparisons. Include per-seed values, negative results, and each arm's valid/invalid seed count. No post-hoc hyperparameter selection, metric replacement or cherry-picked favorable seed.

**Uncertainty:** report paired signed differences for 24 public exploratory seeds, counts of wins/ties/losses, paired mean and a **descriptive** 95% paired bootstrap percentile interval with exactly 2,000 bootstrap replicates and NumPy PCG64 seed 7741. This is not a confirmatory p-value or a generalization guarantee.

**Engineering fail criteria:** inconsistent training samples, asymmetric update exposure, NaN/Inf, held-out data leakage, unchanged weights, constant regulated modulator after initial update, missing seed, rehashed outcome/trace, mismatch against independently implemented numerical replay, or an attempted `VALIDATED` status must fail tests/CI. Report if the anti-vacuity check fails rather than quietly renaming regulator.

## Reproducibility, conservation of history, and limits

- Standalone independent producer/verification programs using NumPy but **no import of each other's model/training implementation**. The verifier reconstructs independently all six arms ×24 seeds ×192 updates and tests full per-phase outcomes, weights and regulator traces to numerical tolerance. It cannot establish external truth; same NumPy implementation and public formulas are common-mode assumptions.
- Generate raw full JSON **exclusively** and print its SHA-256; separate summary and source-linked plots after independent replay; no rewriting prior evidence.
- CI on GitHub `ubuntu-24.04` with read-only permissions and SHA-pinned actions. Also rerun existing EXP003 tests and protect original evidence hash.
- `main` was last observed unprotected. This branch is a **draft PR**. Existing experiments, Sovereign Veritas kernel, and other repos are left unchanged. An authorized external reviewer/owner is required for any research-promotion action.
- No real brain chemistry, consciousness, intentionality, self-authorized mutation, or general-purpose continuous learning has been demonstrated. The mechanism is internally calculated *adaptive learning-rate control*, not Hebbian synaptic plasticity or a biological neurotransmitter. The title is a **functional analogy**, not a claim of biological equivalence.
