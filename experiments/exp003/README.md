# EXP003-P0 operator guide

**Exploratory substrate only. Never label this run confirmatory or independently scientifically validated.**

## Test, without executing a pilot

From the repository root on Ubuntu with Python >=3.12:

    python3 -m unittest discover -s tests -p 'test_exp003*.py' -v

The runner refuses to execute without explicit \`--pilot\`.

## Execute a small baseline-only pilot

    python3 src/origin/exp003.py --pilot --seed-start 0 --seed-count 12

Expected output includes a unique new evidence path, its SHA-256, per-policy summaries, and the label \`EXPLORATORY_SIMULATED — NOT VALIDATED\`. Baseline policies are fixed, random, and deterministic greedy information-gain. **No language model is involved in this command.** It is a test of the engineering substrate, not an AI discovery result.

## Offline check of that evidence

Copy the evidence filename and SHA-256 *as printed by the actual pilot run*, then:

    python3 tools/verify_exp003_p0.py evidence/exp003/ACTUAL_FILENAME.json --sha256 ACTUAL_64_HEX_DIGEST

The checker does not import the runner, and can reject modified checksums, false fixtures, unauthorized probes, inconsistent transitions, and aggregate discrepancies. It shares the deterministic task specification and Python RNG; therefore consistency is not independent-world truth.

## External proposer interface — optional, not yet model validated

Run only a **trusted local** executable that reads one JSON request from stdin and outputs a single JSON response of exactly \`{"probe": 7}\` (where 7 is an example; each response must be a novel, valid integer 0..31). Example interface:

    python3 src/origin/exp003.py --pilot --seed-start 0 --seed-count 3 --external-command "python3 /path/to/trusted/proposer.py"

The agent receives only candidate function names/definitions, prior observations, and remaining experiment budget. It is not given the hidden truth. Incorrect JSON, repeated/invalid probes, nonzero exits, and timeouts generate \`DEFERRED\` without baseline substitution.

**Security warning:** The configured external process is not sandboxed. It inherits the invoking user's OS authority and may have network access. Never point this at arbitrary untrusted code, and never assume the external process is an approved LLM. Avoid passing tokens/credentials or privileged execution contexts.

## Preservation

No command is provided that deletes any previous experiment or evidence. Each pilot creates a new exclusive \`xb\` file. Do not rewrite historical evidence, cherry-pick successful pilot seeds, or promote exploratory results to a future confirmatory claim.

## Next research requirements

Before an actual model comparison, record model SHA-256, quantization, inference binary/version, decoding settings, model response format, token count, latency, and estimated Azure resource costs. A separate EXP003-C1 preregistration must fix held-out seeds and controls before outcome observation. This P0 is not that confirmatory protocol.
