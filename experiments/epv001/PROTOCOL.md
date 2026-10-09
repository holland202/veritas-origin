# EPV-001 — Evidence lineage, decisive dissent and corrupt authority in multiagent reports

**PROSPECTIVELY REGISTERED BEFORE code, tests or evaluation results.**

**Status:** proposed deterministic synthetic benchmark; not an LLM evaluation, not a claim of model intelligence, human reasoning, biology, stable AI epistemics or production security. Research motivation comes from publicly reported Anthropic Frontier Red Team findings, not from importing their private systems or reproducing their numerical experiments:
https://www.anthropic.com/research/multiagent-systems

## Why this particular experiment?

Anthropic reports opposing multiagent epistemic failures: a listener can be misled by an untrustworthy repeated source, while a group can also overlook an independently decisive minority fact. A **global trust/skepticism scalar** cannot solve both problems. Reports can be dependent copies rather than independent votes; and authentic-looking evidence may be bound to a *corrupted reference*.

We will measure evidence-fusion **policy behavior**, keeping the truth oracle, shared-data source and purported evidence anchor explicitly distinct.

## Exact synthetic design

- Pure Python standard library, no LLMs, outside targets, network, credentials or executables from agents.
- **Eight preregistered seeds:** 260801..260808.
- **Six experimental situations:** `INDEPENDENT_LIAR`, `CORRELATED_FALSE_MAJORI` (internal spelling retained), `CORRELATED_UNPROVEN_DISSENT`, `FORGED_DISSENT_PROOF`, `POISONED_AUTHORITY`, `CONFLICTING_AUTHORITIES`.
- **64 independently generated binary world states** per situation and seed = 3,072 four-report trials. One binary truth each trial. Truth is uniformly generated, independent of the presentation order of reports.
- Exactly **four synthetic scouts**, each carrying: `id`, `lineage`, `claim` (0/1), `claimed_verified`, optional `witness`. The same lineage signifies a common upstream observation; 3 repeated messages may share only one actual observational lineage.
- The independent fixture generates an **8-bit parity witness** for the true world state; a different 8-bit witness can be generated for the false claim in negative controls. An anchor is the SHA-256 of a canonical JSON object `{"trial_id","bits","claim"}`.
- `trusted_anchors` is a **fixture-authoritative** mapping keyed by scout id. Its assumed authenticity is *not* established by hashing it again or by self-attestation. The ability of the decision policy to validate parity and a matching pinned anchor is distinct from the fixture oracle's knowledge of actual world truth.
- All policies receive exactly the same reports and anchor registry; none receives the `truth` field as a policy argument. The oracle is used only for post-decision metrics.

## Frozen six situations

| Situation | Four reports | Registry status | Expected critical observation |
|---|---|---|---|
| INDEPENDENT_LIAR | three independently sourced true reports; one independently sourced false | no certified witness | majority and independent-lineage count should choose true |
| CORRELATED_FALSE_MAJORI | three repeated false reports sharing one lineage; one independently sourced true report with a valid witness | true witness anchored | majority false, verified evidence rescues minority |
| CORRELATED_UNPROVEN_DISSENT | same 3:1 false majority, but no witness | no anchored witness | lineage-aware tie should **ABSTAIN**, not invent truth |
| FORGED_DISSENT_PROOF | three independently true reports; one false report advertises a fabricated certificate | registry for forged source binds to a *different* true witness | naive trust of a `claimed_verified` flag is wrong, evidence checker rejects |
| POISONED_AUTHORITY | three independently true reports; one wrong report has a mathematically valid witness anchored by the fixture **to the wrong claim** | corrupted reference expressly marked **known false** | evidence policy falsely trusts the corrupted anchor, a **preserved false positive** |
| CONFLICTING_AUTHORITIES | three true, one false; two independently anchored mutually inconsistent parity witnesses | both anchors match their separate reports | evidence policy cannot establish which authority is truthful; **ABSTAIN** |

The last two situations are deliberate **negative limits**, not successes. The fixture's intended authority has been poisoned; a clean hash + mathematical consistency cannot guarantee world truth.

## Frozen four policies

1. `majority`: each reported vote counts equally, tie => ABSTAIN.
2. `lineage`: count one vote per unique lineage; if one lineage contains contradictory reports, treat that lineage as UNKNOWN/ABSTAIN, tie => ABSTAIN.
3. `claimed_certificate`: trust the first scout advertising `claimed_verified` without checking witness or registry, else fall back to majority. This is a deliberately weak negative control.
4. `evidence_first`: verify a report's 8-bit witness claim (parity), exact commitment and pinned anchor. If multiple anchored valid witnesses conflict, **ABSTAIN**. If one supported claim survives, choose it; otherwise use deduplicated lineages, abstaining on ties. Self-attested labels alone confer no authority.

NO policy may query true label, world oracle, future report, other policy score, or use an unregistered retry to make a favorable selection.

## Metrics registered in advance

- **All episodes retained**: per situation / per policy (number accepted correct, accepted incorrect, abstained), coverage = accepted/64 per seed, error-per-total and error-per-accepted (undefined if coverage zero; encode `null`, not zero).
- Whole study summary equally weights the six situations rather than optimizing over a custom favorable mixture.
- Explicit negative acceptance count in `POISONED_AUTHORITY`, contradiction refusal count in `CONFLICTING_AUTHORITIES`, abstentions in unknown-source cases, and forced failure of a self-attested certificate.
- No science-of-reasoning superiority claim from this deterministic exercise. It tests **design invariants**, not whether a learned AI invents the correct rule.
- A fair future LLM study must separately preregister frozen prompts, cost, report ordering, blind held-outs, an independently controlled witness verifier and an independent oracle, including ambiguous and corruption cases. Do not transfer toy percentages as expected production rates.

## Falsification and nonvacuity controls

- All 3,072 trials generated; every mode results for every trial. No case or negative discarded.
- In `INDEPENDENT_LIAR`, accepting correct majority is required: detector cannot simply abstain on everything.
- In `CORRELATED_FALSE_MAJORI`, naive majority must give incorrect answer and `evidence_first` must give correct one; otherwise test fixture does not exercise expected mechanisms.
- In `FORGED_DISSENT_PROOF`, claimed-certificate policy must fail, evidence-first must ignore it.
- In `POISONED_AUTHORITY`, evidence-first *must exhibit its expected false acceptance*; hiding it invalidates the experiment.
- In `CONFLICTING_AUTHORITIES`, evidence-first must abstain; it may not silently prefer the first witness or defer to majority as if witness conflict were irrelevant.
- Mutation controls: corrupted anchors, changed bits, duplicated JSON keys, nonfinite JSON numeric values, removed episodes, rehashed wrong policy outputs or falsified world states must fail independent replay.
- CLI must require `--pilot`, create a new artifact using exclusive-open, print SHA256, and not modify original files.
- Independent verifier uses a **separate reconstruction**, never imports the producer. Source hashes and limits are recorded. A replayable mathematical fixture does not authenticate the human/OS trust anchor.
- No GitHub main merge or automatic SV permission is justified by a passing test. All evidence and failures remain in Git draft history.

## Stop condition

The work is complete once the narrow benchmark, mutation tests, replay and full raw evidence have passed CI under read-only access, with a report that accurately labels its **known poisoned-authority false positive**. If any condition fails, retain failed CI and fix explicitly; do not call the mechanism a validated AI trust protocol.
