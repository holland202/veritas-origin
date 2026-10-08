# EBA-001 — An internally consistent experiment can conceal evaluator contamination

**PUBLIC EXPLORATORY TOY SIMULATION — NOT VALIDATED.** This is an engineered counterexample against treating *mathematical replay* as evidence of *proposer isolation*. It is not a practical exploit, an isolated-model evaluation, or a claimed new discovery.

## Protocol and immutable provenance

- Prospective registration: [`experiments/eba001/PROTOCOL.md`](../../experiments/eba001/PROTOCOL.md) first committed `b03dc91cc3b145577938352d128579e4b8092ac1`, **before any EBA-001 implementation or test runs**.
- Registered **A0 addition before implementation**: known-false-clean scenario `E9`, committed `719e97e0ae4628d11c3fc4be03fc94fda46ebdd8`. The first protocol version remains in Git history.
- Source: [`src/origin/eba001.py`](../../src/origin/eba001.py); independently authored replay: [`tools/verify_eba001.py`](../../tools/verify_eba001.py); negative controls: [`tests/test_eba001.py`](../../tests/test_eba001.py); visualization [`tools/plot_eba001.py`](../../tools/plot_eba001.py).
- First exploratory CI attempt [37860125396](https://github.com/holland202/veritas-origin/actions/runs/37860125396) **FAILED** because the EBA verifier rejected ordinary concrete `PosixPath` objects with `type(root) is Path`. Fixed by changing to `isinstance(root, Path)` in new commit `b03bc948930e2064a210d9ae04b359e82d7fc1a0`. This is a verifier implementation error retained as historical negative engineering evidence, not a model failure.
- **First successful run:** [GitHub Actions 37860177492](https://github.com/holland202/veritas-origin/actions/runs/37860177492). Existing EXP003-P0 suite **17/17 passed**, RA-001 assurance suite **28/28 passed**, EBA-001 suite **24/24 passed**, total **69** unit tests. Historical EXP003-P0 archive integrity/replay also passed.
- Original EBA-001 24-task, 10-scenario JSON **SHA-256**: `a8b5a251872cea38e81be03f886f94c065250257fd386b061c987a16c360c6d4`.
- GitHub Actions artifact `eba001-raw-evidence-and-figures`, ID **`11585776781`**, retains that exact public JSON and two replay-qualified SVGs for **30 days**; archive elsewhere before expiration. Re-running deterministic code reproduces substantive content but file timestamps/names differ.
- Original historical EXP003-P0 archive remains byte-for-byte unchanged with SHA-256 `627eb778e8eef80d9d664c9ac6f3b7743d51e6a97a677eea8cac51e79b467333`.

## Mechanism: two truthful transcripts, different access paths

The original EXP003-P0 task uses four public candidate predicates and a hidden true predicate, with up to six integer probes. Two **pure mathematical selector functions**, not model agents, were applied to the identical twelve *previously published* seeds:

1. `clean_greedy`: selects the integer probe maximizing expected eliminated hypotheses, using only public candidate functions and prior outcomes.
2. `oracle_informed`: illegally reads the hidden true predicate and chooses a probe minimizing how many hypotheses remain *given that already-known hidden truth*.

Both make legal probes and write truthful observations, so the unchanged, independently implemented `tools/verify_exp003_p0.py` reports **CONSISTENT WITH EXP003-P0 SPECIFICATION** for both synthetic `external`-policy transcripts. That is **not a bug in this verifier's stated contract**: its external policy does not attest the information the proposer received, nor does it enforce evaluator/proposer separation.

### Probe efficiency — descriptive and invalid for claiming improvement

| Original public P0 sample, 12 tasks | Context-only greedy | Oracle-informed (inadmissible) |
|---|---:|---:|
| Total probes | **24** | **13** |
| Mean probes/task | 2.000 | 1.083 |
| Seeds where oracle-informed used fewer probes | — | 11/12 |
| Seeds tied | — | 1/12 |
| Seeds where oracle-informed used more probes | — | 0/12 |
| Independently replayed mathematical record | CONSISTENT | CONSISTENT |
| Clean information provenance established? | **NO — fixture declaration only** | **NO — forbidden oracle knowledge** |

An externally sourced hidden answer appears to offer `(24-13)/24 = 45.8%` fewer probes, but this is *an information leak*, **not a valid advance in experiment selection, a model capability, or a fair research comparison**. These task seeds, predicate source and registry are public and reused; there was no withheld-task confirmation.

### Registered scenario matrix

| ID | Injected simulated condition | Mathematical replay | Bounded declared-methodology disposition |
|---|---|---|---|
| E0 | Untouched original public P0 archive | CONSISTENT | `EXPLORATORY_ONLY` |
| E1 | Honest context-only algorithm with a declared complete receipt | CONSISTENT | `CLEAN_WITHIN_DECLARED_FIXTURE` |
| E2 | Oracle-informed algorithm **with visible read event** | CONSISTENT | `INVALID_OBSERVED_ORACLE_LEAK` |
| E3 | Oracle-informed algorithm **with missing read history** | CONSISTENT | `UNOBSERVABLE_ACCESS_PROVENANCE` |
| E4 | The observation schema contains a hidden `truth` field | CONSISTENT | `INVALID_PROPOSER_CONTEXT` |
| E5 | The observation schema contains `task_seed` / evaluator file location | CONSISTENT | `INVALID_PROPOSER_CONTEXT` |
| E6 | Evaluator identity differs from the pinned evaluator Git blob | CONSISTENT | `INVALID_EVALUATOR_IDENTITY` |
| E7 | A self-resealed hash claims independent artifact authenticity | CONSISTENT | `NOT_ESTABLISHED_SELF_ATTESTED_INTEGRITY` |
| E8 | Missing complete access/proposer provenance | CONSISTENT | `UNOBSERVABLE_ACCESS_PROVENANCE` |
| E9 | Oracle-informed algorithm **forges a clean complete access declaration** | CONSISTENT | `CLEAN_WITHIN_DECLARED_FIXTURE` — **KNOWN FALSE CLEAN** |

The scripted methodological classifier flagged **4 explicit invalid conditions**, returned **2 unobservable** outcomes and **1 self-attested/not-established** outcome, but also had **1 known false-clean outcome E9**. There is one legitimate clean *declaration* E1 and one archived exploratory E0.

**E9 is the key negative result.** A detector cannot establish provenance by trusting an access log that the potentially compromised process itself can forge. E9 was preregistered, not discovered then quietly added. Even this experiment's `synthetic_true_oracle_access` field is an assertion under an independently scripted fixture, not real OS-measured telemetry.

## Why this matters for Sovereign Veritas

Sovereign Veritas's Gate is not fundamentally broken by either transcript: it was never designed to prove world truth or evaluator process isolation. A record with `verification.status=PASS` does not make a research claim `SUPPORTED`, and cannot itself establish a human-authorized publishing capability.

RA-001's read-only SV bridge still outputs `capability.authorized=false`, `human_approval_verified=false`, and an unknown runtime. **Do not promote either EBA transcript to publication authority.** The existing RA suite tested actual pinned Sovereign Veritas Gate source: a synthetic ALLOW fixture is *only* proof that the gate is non-vacuous, not a real authenticated approval.

EBA-001 builds on [EACE](https://github.com/holland202/eace) (integrity not truth; negative controls) and [Evaluation Harness](https://github.com/holland202/veritas-eval-harness) (answer laundering; false positives in honest evaluation). Neither project implementation was imported.

## What was and was not tested

**SUPPORTED within this mathematical simulation:**
- A contaminated proposer can emit a transcript that mathematically agrees with every observable outcome and passes the original P0 consistency verifier.
- The extra observation schema and explicitly logged oracle contact can be detected by a narrow declared-evidence checker.
- Missing provenance can be returned as `UNOBSERVABLE` instead of a false `PASS`.
- A fake *complete clean* access declaration can still fool that checker (E9). This is an intentional counterexample to its protection claim.
- Recorded byte hashes, original history, expected scenario classification and summary are independently reconstructed; rehashed tampering fails the standalone EBA-001 verifier under its fixed source.

**NOT VALIDATED:**
- Physical or process isolation of the proposer from evaluator;
- prevention/detection of unlogged file, env, log, network, or side-channel access;
- an independent trusted access monitor or signed human approval;
- actual LLM dishonesty, tool misuse, performance, or covert leak strategies;
- confidentiality of public, trivially enumerable deterministic seed assignments;
- experimental superiority or scientific novelty.

## Next stop/go decision

Do **not** declare evaluator isolation solved. The next engineering step is a genuinely separate and restricted evaluator service with a proposer restricted to serialized declarative probes. The service must protect hidden evaluator data using OS identities, filesystem permissions and network policy, enforce resource limits, and record access events under independent authority. Model-output metadata cannot attest its own cleanliness. Demonstrate both attempts that are **blocked** and an *honest successful run*, and report uninstrumented paths as unknown.

Before adding untrusted model code, require a separate threat model, security review and allowed host-level containment. Without that, EXP003-C1 remains unready.

## Preservation and publication

GitHub remains the development source; draft PRs and the unprotected `main` ruleset status are not treated as permanent tamperproof storage. Original EBA JSON lives in a time-limited CI artifact, with its exact digest pinned here. Chart scripts and two figures are reproducible from the original artifact. No files were uploaded to Hugging Face or Codeberg. No historical result was overwritten, no autonomy or deployment action added, and **nothing was merged to `main`**.
