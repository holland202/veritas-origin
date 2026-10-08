# EXP003-P1 — Offline proposer exchange prototype

**Status: ENGINEERING PROTOTYPE / NOT SECURITY ISOLATION / NOT VALIDATED**

**Research question:** Can evaluator-to-proposer transport be reduced to public JSON challenges and strictly validated JSON probe responses, while keeping hidden task truth and secret out of the transmitted message?

## Prior-art review (research only; no source copied)

The design deliberately borrows *ideas*, not implementation code, from:

- [Inspect AI sandbox separation](https://github.com/UKGovernmentBEIS/inspect_ai/blob/2c002827fa4c490bf5896269d4bbd84ff64ebcf6/docs/sandboxing.qmd): sandboxing tool work is separate from protecting the evaluator/agent itself (root MIT license observed; study only).
- [Anthropic sandbox runtime](https://github.com/anthropics/sandbox-runtime/blob/3f0bad7345238f47736435e3f2b064399c1cad74/README.md): filesystem and network restrictions are separate required controls (root Apache-2.0; study only).
- [OpenAI Codex sandbox policies](https://github.com/openai/codex/blob/14ff9c3a43ebf9bf543cf5f7c45cff2bfea2e512/codex-rs/core/README.md): explicit OS enforcement and policy failure behavior (root Apache-2.0; study only).
- [in-toto](https://github.com/in-toto/in-toto/blob/e352b43ad7cb8915d84c36d791aa61346152a0a3/README.md): authorized steps and attested artifact dependencies (root Apache-2.0; study only).

No novelty or copyright-clearance conclusion arises from these searches. Local API design and tests were created for this research branch with AI coding assistance.

## Implemented in `src/origin/p1_offline_exchange.py`

`issue_request(task, previous_observations, expires_at_unix)` constructs a **public allowlisted envelope** from a trusted evaluator task. It omits `truth`, `task_index`, `evaluator_secret_hex`, process IDs, host paths, secret seeds and credential fields. It carries candidate names, the public binary response matrix, observations, available probes, remaining budget, expiry and an opaque random request ID.

`request_digest(request)` computes SHA-256 over strictly canonicalized request data to help bind a response to the *exact* request bytes. **This is not authentication**: an attacker controlling both sides can replace the request and recompute the digest.

`admit_proposal(request, response_bytes, now_unix, spent_request_ids)` accepts **only** exact JSON shape `{"request_id": str, "request_sha256": str, "probe": int}`. It rejects duplicate JSON keys, NaN/Infinity, bool-as-int, wrong/expired/mismatched requests, repeated/invalid probes, malformed candidate state, impossible observation history, and exhausted budget. It returns `ADMISSIBLE_PROPOSAL_ONLY`, **not ALLOW or an executed effect**.

The `spent_request_ids` argument is explicitly **caller-supplied, in-memory and non-atomic**. It is a replay *check*, not durable reservation and not safe against concurrent races. There is no subprocess execution, host isolation, network transport, persistent task store or attached model in this module.

## Threats NOT mitigated

- A model running under the evaluator's OS account may still inspect files, memory, environment, `/proc` and prior evidence. **Transport field omission is not OS isolation.**
- SHA-256 is not a signature; request origin cannot be independently authenticated from it.
- A model/attacker can replay a request unless trusted, durable atomic reservation is enforced by an external capability service.
- The caller chooses `expires_at_unix` and `now_unix`; correctness depends on trusted wall-clock source.
- No global token/CPU/RAM/network budget is enforced here. No credential security, access-control list, network firewall or container boundary is provided.
- The response parser caps in-memory response length but does not limit an external process's output *before* bytes arrive.
- The 16×24 generator remains toy synthetic science and **does not invent hypotheses**.
- Tests passing with a known fixture do not demonstrate model performance or independent-world truth.

## Falsifiers / tests

The `tests/test_exp003_p1_exchange.py` suite exercises both accepted and rejected cases: a good response admitted, no oracle fields in the outbound JSON, correct observation state, wrong request binding, malformed or rehashed JSON, bool-as-int, unexpected commands, expired and replayed IDs, contradictory histories, and exhausted budget.

```bash
python3 -m unittest discover -s tests -p 'test_exp003_p1_exchange.py' -v
```

Unit tests are run in GitHub CI before any cloud work. **No real untrusted agent is executed.** If an attacker can access the secret through the host, this protocol does not claim to stop them. For that we must run separate OS-level boundary probes from `docs/architecture/B02_EXECUTION_BOUNDARY.md` when approved.

## Next acceptance gate

1. Independently control evaluator and proposer privilege domains; pass secret-file, process, network, descendant cleanup and resource exhaustion negative tests.
2. Make the challenge ID reservation durable and atomic across concurrency and interruption; test one key/two effects.
3. Add an authenticated transport and secure clock/budget service; model/proposer cannot self-issue request IDs or change policy.
4. Pin exact model SHA, inference implementation, decoding, tokens, wall time and cost. No real LLM is evaluated in this prototype.
5. Freeze a distinct confirmatory protocol before any held-out results are observed.

**Disposition:** Engineering evidence may support `STRICT_JSON_ADMISSION`, never `SANDBOXED`, `AUTHORIZED_TO_EXECUTE`, or `AUTONOMOUS_SCIENCE_VALIDATED`.
