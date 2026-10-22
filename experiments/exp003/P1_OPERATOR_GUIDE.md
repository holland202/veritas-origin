# EXP003-P1 — Operator guide and run boundaries

**Current state:** exploratory engineering implementation. No real language model evaluated. Oracle process isolation remains UNMET. No scientific performance claims.

The entire P0 evidence and its published report are preserved unchanged in GitHub. P1 is a separate branch and a separate hypothesis space. P0's findings must not be relabeled.

## Read-only verification first

From the repository root:

```bash
python3 -m unittest discover -s tests -p 'test_exp003_p1_*.py' -v
```

The tests use known public fixture secrets and a trivial test stub for the external proposer. The stub is NOT an LLM, and its score cannot be presented as an LLM result.

## Pilot run (explicitly authorized, no model)

Run this only when intentionally performing an exploratory baseline pilot:

```bash
python3 src/origin/exp003_p1.py --pilot --task-count 8
```

The runner samples a fresh private secret from the Python OS random interface, constructs 16 hypotheses with 24 binary response positions and sets a hard cap of five observations per policy/task. The only default policies are fixed, random, greedy. No Azure or Hugging Face deployment is required.

An evidence JSON file is exclusively created in `evidence/exp003/` with a new name; it is not overwritten. The output prints the *actual* file path and hash. The secret is revealed in the archived evidence so anyone can independently replay the generator. **Do not reuse tasks from a published secret as held-out tests**.

Inspect the output and independently verify using the *actual* values, for example:

```bash
python3 tools/verify_exp003_p1.py ACTUAL_FILE.json --sha256 ACTUAL_SHA256
```

The verifier recomputes the full generator, hidden truth, recorded observations, trajectory and statistics without importing the runner. It detects corrupt evidence, but cannot establish oracle isolation or whether the external world was faithfully represented.

## Explicit public fixture smoke test

This is for engineering tests, never for a research claim:

```bash
python3 src/origin/exp003_p1.py --pilot --task-count 2 \
  --test-secret-hex 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --allow-public-test-secret
```

That same fixture is used in GitHub Actions. Outputs are labeled `PUBLIC_TEST_SECRET`.

## External model connection (NOT YET READY FOR CLAIMS)

A trusted proposer must accept a JSON dictionary over stdin and return precisely `{"probe": INTEGER}` to stdout, selecting a novel available probe. The input contains a 16×24 hypothesis/response matrix, candidate names, observations and remaining budget but no hidden truth or evaluator secret.

**Do not run an untrusted model process under the same identity as the evaluator.** The flag `--acknowledge-unisolated-proposer` acknowledges risk only; it does not sandbox the process. Inference validation is pending. The runner requires operator-reported model id and artifact SHA-256, but does not independently validate those claims; models, prompts, inference configuration and token/cost tracking require an additional adapter and audit.

Unauthorized or invalid responses must result in `DEFERRED`, not silent substitution of greedy/fixed. Do not attach network actions, file writes, self-modification or real-world actuator permissions to a proposer.

## Scientific falsification priorities

- Can a prover reconstruct truth without observation by inspecting the host, stdout/stderr, environment, file handles, metadata, or deterministic test fixtures?
- Can an external proposer sneak a boolean, duplicate JSON key, NaN, repeated probe or forbidden field into its response?
- Can any mutation to the evidence evade the independent verifier if the attacker recalculates the file digest?
- Does the task distribution still exhibit the P0 completion ceiling? Record failed design as a valid result.
- Does an LLM offer any benefit over the strong deterministic greedy control *per correct task per model token and cost*? No model has answered this yet.

**Next gate:** reproduce GitHub CI results, close evaluator isolation gaps, pin exact runtime and model artifacts, then conduct a separate explicitly exploratory model pilot. The later confirmatory C1 protocol is distinct and not established by this document.
