# ITC-001 — Recurrent internal computation and self-terminated inference (preregistered)

**Registered BEFORE implementation, pilot, training, or analysis.** Status: `EXPLORATORY / NOT VALIDATED`. Frozen base: ASP-001 draft branch commit `905021915ae1cb32027f8ffcac60d2efb675f055`. GitHub `main` original evidence will not be edited. No claims of consciousness, human thoughts, cognition, self-awareness, or novel architecture.

## Scientific and conceptual motivation

"Thinking" is not an empirically justified label for these states. Operational term: **latent iterative computation**, where a neural network repeatedly transforms a hidden vector before emitting one prediction. A separate rule may choose how many iterations to execute from *only internal, available signals*. This is a genuine, previously investigated ML concept (Graves ACT; Universal Transformers; recurrent-depth language models), not an invention of ITC-001.

Primary sources:
- Alex Graves (2016), *Adaptive Computation Time for Recurrent Neural Networks* — https://arxiv.org/abs/1603.08983
- Dehghani et al. (ICLR 2019), *Universal Transformers* — https://research.google/pubs/universal-transformers/
- Geiping et al. (NeurIPS 2025), *Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach* — https://proceedings.nips.cc/paper_files/paper/2025/hash/3b01972cf31e6fa0fe29e4b8b5c2a0a1-Abstract-Conference.html
- Bai, Kolter and Koltun (NeurIPS 2019), *Deep Equilibrium Models* — https://arxiv.org/abs/1909.01377
- Miconi et al. (ICML 2018), *Differentiable plasticity* — https://proceedings.mlr.press/v80/miconi18a.html

**Important distinction:** ITC-001 does **not** implement ACT's learned differentiable halting policy, a Transformer, equilibrium inference, or synapse-specific plasticity. It investigates a much smaller *fixed trained recurrent network* under explicit stopping policies, with no text intermediate reasoning or symbolic chain-of-thought.

## Frozen research question and hypotheses

*Can a small learned recurrent network perform more accurate synthetic decisions when given additional silent hidden-state updates, and can a threshold rule based on its own output confidence and stability save inference computation without worse accuracy than allocating the same number of updates randomly?*

- **H1 depth utility:** pooled task-macro test accuracy at fixed depth 5 is at least **2 percentage points** higher than at depth 1, using **6 paired model seeds**. Otherwise report `H1_NOT_SUPPORTED`.
- **H2 adaptive benefit:** compared with a **within-task shuffled depth-allocation control using the same exact distribution of update counts**, adaptive halting yields at least **1 percentage point** higher pooled task-macro test accuracy, wins on at least **4/6 model seeds**, uses **at most 4.0** average hidden updates per test instance, and is at most **1 percentage point** worse than fixed depth 5. Every clause must hold. Otherwise `H2_NOT_SUPPORTED`. Per-seed shuffle baseline mean over **100 predetermined permutations**.
- **H3 safety/uncertainty diagnostic (not a win condition):** report the fraction of samples terminated early but incorrectly predicted, split by each task, and count confidently incorrect early decisions. A stability or confidence signal cannot prove correctness.
- No post-hoc metric replacement, adjusting thresholds, removing hard tasks, reusing test answers for stopping, or selecting successful model seeds. Report all six seeds and all controls even if all hypotheses fail.

## Network architecture, input classes and real training

**Input:** 16 independent binary bits encoded as -1/+1 plus six-dimensional one-hot task identifier (22 scalar inputs). **Exactly six tasks**, each equally represented, with labels in {0,1}:
0 = copy first bit; 1 = logical AND first two bits; 2 = XOR first two bits; 3 = parity of first four bits; 4 = majority of first five bits; 5 = parity of first eight bits. This explicitly mixes easy and hard compositional tasks; per-task results mandatory.

**Network:** shared recurrent core with input-to-hidden weights `Win[22,24]`, recurrent weights `Wr[24,24]`, `b[24]`, readout `Wout[24,1]`, output bias `bout[1]`, **1153 learned scalars**. Set `h0=0`, `s=x@Win+b`, and for `t=1..5` compute `h_t=tanh(s+h_(t-1)@Wr)`, `p_t=sigmoid(h_t@Wout+bout)`. Five latent steps use **weight tying**, without producing any user-visible text or external action.

**Initialization per model seed:** NumPy PCG64 `default_rng(seed)`; `Win = normal(0,0.7/sqrt(22))`, `Wr=0.55*I+normal(0,0.012)`, `Wout = normal(0,0.25/sqrt(24))`, biases zero. Train all parameters by five-step backpropagation through time (BPTT). Cross-entropy losses at each step with frozen weights **[0.10,0.10,0.15,0.25,0.40]**. This explicitly provides auxiliary shallow supervision; **the same trained network and weights** are evaluated under every stopping policy.

**Training:** 640 Adam updates, batch 96 with exactly 16 samples per task, learning rate 0.012, beta1=.9, beta2=.999, epsilon=1e-8, global gradient norm clipped to 5.0. Training examples are freshly drawn from `np.random.default_rng(seed+100_000)` with a deterministic rejection split; no test labels, hidden test loss, or shuffled reference scores influence learning. One update uses all 5 recurrent passes; *training compute is shared across inference policies*, avoiding unequal additional model fitting.

**Exact input pattern holdout**: encode the 16 raw bits as a 16-bit integer `v`. The split table for all 65536 possibilities uses `sha256(b"ITC001_SPLIT_V1:"+v.to_bytes(2,"big")).digest()[0] < 32` (roughly 12.5%) to mark held-out bit patterns. Train draws reject all held-out values, test draws accept **only held-out** values, regardless of task. Consequently no exact 16-bit pattern can appear in training and testing. This is only *synthetic withheld-pattern* separation, not proof of generalization to a different task family.

**Six model seeds** `20261161..20261166`. Test generator uses `default_rng(seed+800_000)`, generates **512 test instances per task** from the held-out partition (3072 per seed). The same test instances and learned parameters are used by every inference policy; test labels used only in scoring after stopping decisions are frozen. All source bits/draw methods and seeds are public after release.

## Registered stopping/inference policies

- Fixed latent depths **1, 2, 3 and 5**.
- **Adaptive:** first possible stop is **t=2**; stop if `abs(p_t-0.5)>=0.18` AND `abs(p_t-p_(t-1))<=0.08`, otherwise compute until t=5. No test labels/answers read in the halt rule. Latent "confidence" is numerical distance from decision threshold, **not calibrated probability of truth**.
- **Budget-matched shuffled depths:** use the *exact adaptive per-task depth histogram*, but for each task permute which held-out items receive those depths with `np.random.default_rng(99117+seed*1000+repetition)` for repetitions 0..99. Compute/predict from already available `p_1..p_5`, without rerunning training. This ensures **identical per-task mean computation** while destroying depth's association with each example. Averaging 100 predefined assignments reduces shuffle noise; it is a comparison of an allocation mechanism, **not a blind external competitor**.
- **Globally shuffled depths** (secondary): same whole-test depth histogram, permuted with `default_rng(77117+seed*1000+repetition)`, repetitions 0..99.
- No oracle stopping or answer-dependent policy is reported as a legitimate control.

## Registered outcomes and diagnostics

Primary: macro-accuracy = mean of the six task accuracies, averaged equally across all six model seeds. **Fixed-depth5 vs1** for H1; **adaptive vs per-task budget-matched shuffle** for H2. Note individual task error, pooled accuracy, mean/min/max latent passes, per-task depth histogram, cross-entropy and Brier per policy, adaptive-early false-decision count (denominator = number stopped before step 5), and fixed5-versus-adaptive disagreements. Hidden trajectory probes include mean `L2(h_t-h_(t-1))` per iteration and probability changes; no layer activity is labeled an internal human thought.

Training compute: actual 640 * 5 recurrent unrolls per seed and 96 examples/batch. Inference compute proxy: **24-neuron recurrent passes** per test input, plus overhead of confidence/stability checks. Match the number of recurrent state transitions; do NOT claim equal full FLOPs or measured joules. All methods evaluate the **same trained parameters**.

Paired differences and **descriptive** bootstrap 95% percentile interval: 2000 *paired seed* draws with PCG64 seed 88019. No p-value or confirmatory novelty claim. Positive and negative findings retained.

## Adversarial and anti-vacuity tests (precommitted)

1. Actual trainable weights change and five-step BPTT gradients match numerical finite differences for a small sample.
2. No overlap between train/test 16-bit patterns; fail if any held-out pattern enters training.
3. Both a one-step and a five-step output exist, and the repeated latent states are not universally identical.
4. Adaptive depth is never outside `[2,5]`, and fixed policies use exactly their named depths.
5. All adaptive/within-task shuffled comparisons spend the **same per-task total latent passes**, each seed; no mutable metric allocation.
6. A known correct easy example and known wrong hard example are retained as positive/negative scoring controls; no always-right reporting.
7. Input validation forbids duplicated JSON keys, NaN/Infinity, missing tasks/seeds, fabricated best policy, changed retained weights/gradient traces or relabeled `VALIDATED` status.
8. Independent verifier **does not import the producer** and reconstructs training, predictions, stopping decisions and summary with separately written numerical code. Its acceptance means internal agreement, **not independent scientific confirmation**.
9. CI pinned version Python 3.12/NumPy 2.2.6, read-only permissions, historical EXP003-P0 SHA intact, original evidence uniquely created, SHA256 and full immutable run artifact archived. New raw evidence never overwrites original.
10. If CI cannot run due to memory, environment, or performance, record failed run and follow up with a **dated prereg amendment**; do not silently shrink seed count/steps or call partial output the registered result.

**Acceptance:** no automatic PR merge, no GitHub mirror overwrite, no Sovereign Veritas approval token, no claim that unobserved internal representations are experiences or that a deliberately chosen latent recurrent task establishes novel intelligence. If both H1 and H2 fail, the engineering may still be complete but **the conceptual claim remains NOT SUPPORTED**.

## Limitations declared in advance

- Task family is small, binary, public, artificial and partly memorization-friendly.
- Stability can imply wrong confidence; task identities are observable, so depth heuristics may allocate based on easy task properties rather than instance reasoning.
- The same NumPy/RNG ecosystem is shared by runner and verifier; algorithm reconstruction does not establish independent physical truth.
- Parameter count and training examples are matched across inference policies, but different recurrent-pass counts have different computation costs.
- Latent cycles are computational operations, **not human thoughts, brain chemistry, consciousness, biology, genuine explanatory chains or authorization to act**.
