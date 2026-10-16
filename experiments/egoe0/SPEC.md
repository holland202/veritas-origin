# EGOE-0: Evidence-Governed Ontology Evolution, specification revision 1

**Status: REGISTERED DESIGN. NOT IMPLEMENTED. NOT RUN. NOT VALIDATED.**
Revision 1, 2026-10-16. It replaces the 2026-10-15 design handoff, which is not in this repository. That handoff's SHA-256 is
`c7785a01d626b3cc5b96ca53b27f4adccebb9c7019f8c79cbed8c8d0abc36cb6`, and the owner holds the file.

Nothing in this file is a result. No code exists yet, and nothing here authorizes implementation, a run, an AI
proposer, or any change to another experiment. Section 11 lists what the owner has to approve.

## 0. What broke in the previous draft (failures lead)

The 2026-10-15 draft could not have failed. These four defects are why it was rewritten:

| # | Defect in the 2026-10-15 draft | Consequence | Fix in this revision |
|---|---|---|---|
| D1 | **Circular split.** The verifier checks candidates against "a withheld evaluation set", and the secondary endpoint scores held-out accuracy on that same set. | Held-out accuracy measures how well the verifier fits the set it was given. That is not generalization. | Three disjoint splits (§4): proposal evidence, verifier validation, sealed test. The verifier never reads the test split. |
| D2 | **Vacuous primary endpoint.** If the verifier can see which relations are true, its false-admission count is 0 by construction, and accept-all's is 4/4. | The primary result was known before running: a log line, not a measurement. | The verifier is truth-blind (§5), and that is demonstrated by a label-invariance test (P2). The primary endpoint (§7) is computed only on false candidates written to look valid. |
| D3 | **Strawman rival.** H0 compared the verifier with accept-all. | Any check beats accepting everything. | The simplest real rival is arm B2: type checks plus byte-verified citations (§6). The primary comparison is C against B2. |
| D4 | **n = 4, one graph, self-authored labels.** One omitted relation and four false candidates, with test-writer independence optional. | No denominator could separate the arms, and the labels would be the implementer's. | Two tiers (§8): a seeded self-test tier for spec conformance, and a blind tier with at least 3 graphs and at least 16 false candidates, written and sealed by someone other than the implementer. |

## 1. Research question

When a verifier cannot see the truth labels, does it reject false relationships that **look supported** (well-typed and
backed by an existing, byte-intact evidence artifact) better than a cheap provenance check does? And does it do that
without losing the true relationships that a frozen graph left out?

That is a narrower question than "does governed ontology evolution work". It is the part of that question that can be
measured with what exists today.

- **H0:** On the blind tier's hard false candidates, C's false-admission rate is no lower than B2's.
- **H1:** C admits at least 25 percentage points fewer hard false candidates than B2, and admits at least 80% of the
  true candidates that have supporting evidence.

H1 becomes a claim only if P4 (§9) holds on a sealed run, and even then it is labeled owner-authored and not
independently replicated (§10).

## 2. No ontology is needed

A typed, immutable fact graph with four constraints and one derived query is enough. Nothing here needs an OWL
reasoner, a graph database, an LLM, self-modifying code or online learning. Everything is stdlib Python, run with `-I`.

## 3. Substrate

**Entity types:** `Supply`, `Component`, `Sensor`. Identifiers are synthetic (`S1`, `C4`, `N2`). They describe no real
plant, PLC, certification or spacecraft hardware.

**Predicates and signatures (K1):**

| Predicate | Subject | Object | Meaning |
|---|---|---|---|
| `feeds` | `Supply` or `Component` | `Component` | the subject supplies the object |
| `depends_on` | `Component` | `Component` | the subject fails if the object fails |
| `monitors` | `Sensor` | `Component` | the sensor observes the object |

**Constraints:**
- **K1** Type signatures, as in the table.
- **K2** The propagation graph is acyclic. It has an edge `x → y` for each `feeds(x, y)` and each `depends_on(y, x)`.
- **K3** `monitors` is functional: each `Sensor` monitors at most one `Component`.
- **K4** No relation has the same entity as subject and object.

**Derived queries.** These are what the questions ask about:
- `affected(x, y)`: is there a path `x → … → y` of length 1 or more in the propagation graph?
- `watched_by(x)`: the set of sensors that monitor some component `c` where `c = x` or `affected(x, c)`.

**Version record (immutable):** `{version_id, parent_hash, schema_hash, facts, constraints_hash, artifact_hashes}`.
`version_id` is the SHA-256 of the canonical JSON of everything else in the record.

**Evidence artifact:** canonical JSON `{artifact_id, source_label, asserts: [[s, p, o], …], body}`, stored under the
SHA-256 of its exact bytes. `source_label` is free text and carries no trust weight. Some artifacts in every task are
**planted**: byte-intact and well-formed, but asserting a false relation. Byte integrity is not truth.

**Proposal:** `{proposal_id, parent_version, operation, subject, predicate, object, cited_artifact_hash, proposer_id}`.
The only admissible `operation` is `ADD_FACT`.

## 4. Splits and who may read them

| Split | Contents | Proposer | Verifier (all arms) | Scorer | Implementer before reveal |
|---|---|---|---|---|---|
| Public release | `G0` (the true graph `G*` minus the omitted relations), evidence store `E`, proposal stream | read | read | read | blind tier: **no** |
| Validation `S_val` | questions with answers computed on `G*` | **no** | read | read | blind tier: **no** |
| Sealed test `S_test` | questions with answers computed on `G*` | **no** | **no** | read after reveal | **no** |
| Sealed labels | `G*` and a TRUE/FALSE label for each proposal | **no** | **no** | read after reveal | **no** |

`S_val` and `S_test` contain no question in common, and each question is answered on `G*`. A verifier may use `S_val`
answers. That is legitimate partial evidence about `G*`, and it is how coverage limits get measured (P5). It may not
use `S_test` or the sealed labels.

**Authoring order (blind tier).** The author writes `G*` first. Next they write `S_val` and `S_test` and commit the
hash of both. Only after that do they write the proposal stream and the planted artifacts. A validation set written
before the candidates cannot be tailored to catch them.

## 5. Verifier checks (arm C)

Each proposal is checked against `G0` alone, in this order. The first failing check decides the verdict.

| Check | Rule | Verdict and reason on failure |
|---|---|---|
| V1 | well-formed JSON, `operation == ADD_FACT`, known entities and predicate | `REJECT MALFORMED` or `REJECT RULE_CHANGE` |
| V2 | `parent_version` equals the release `version_id`; `proposal_id` not seen before | `REJECT PARENT_MISMATCH` or `REJECT REPLAY` |
| V3 | K1 type signature | `REJECT TYPE` |
| V4 | a citation is present; the cited hash is in `E`; the stored bytes re-hash to it | missing: `DEFER NO_EVIDENCE`. Absent or altered: `REJECT FABRICATED_EVIDENCE` |
| V5 | the cited artifact's `asserts` contains exactly `[s, p, o]` | `REJECT CITATION_MISMATCH` |
| V6 | `G0` plus the candidate satisfies K2–K4 | `REJECT CONSTRAINT` |
| V7 | no `S_val` question answered correctly on `G0` is answered wrongly on `G0` plus the candidate | `REJECT VALIDATION_REGRESSION` |
| V8 | joint check: go through the candidates that passed V1–V7 in ascending `proposal_id` order, keeping a running set. A candidate that breaks V6 or V7 together with that running set is demoted. | `DEFER JOINT_CONFLICT` |

Otherwise the verdict is `ALLOW_CANDIDATE`. That verdict does **not** apply anything. Adoption is simulated as
`G0 ∪ {ALLOW_CANDIDATE}` for scoring only, and real adoption stays with the owner.

`VOID` means the verifier's own inputs failed integrity: the release hash does not match, the store is unreadable, or
the schema hash is wrong. A VOID run is kept and scored as VOID, not as zero.

V8 is also run in descending order. Proposals whose verdict changes between the two orders are reported as
order-sensitive (control 5), not hidden.

## 6. Arms

All arms receive the same proposal stream.

| Arm | Checks | Role |
|---|---|---|
| A | none; the graph stays `G0` | frozen baseline |
| B | V1 only | accept every well-formed proposal |
| **B2** | V1–V4 | **simplest real rival**: types plus byte-verified citations |
| **C** | V1–V8 | the governed verifier |
| M-accept | always `ALLOW_CANDIDATE` | anti-vacuity mutant |
| M-reject | always `REJECT` | anti-vacuity mutant |
| C−V3, C−V5, C−V6, C−V7 | C with one check removed | ablations: shows whether each check is load-bearing |

## 7. Endpoints

Admission means a final verdict of `ALLOW_CANDIDATE` after V8. Each endpoint is reported as an exact count with its
denominator, a Clopper–Pearson 95% interval, and a case-level record.

- **E1 (primary).** Hard false candidates are false candidates the author marked, while writing them, as *intended to
  look supported and consistent*. E1 is the false-admission rate on those, for B2 and for C, and Δ = FA(B2) − FA(C).
- **E2.** True-admission rate for C among TRUE candidates that have a supporting artifact.
- **E3.** For TRUE candidates with no artifact, the proportion C defers. Every one should be `DEFER NO_EVIDENCE`.
- **E4.** `S_test` accuracy of the adopted graph for arms A, B, B2 and C.
- **E5 (overfitting).** Candidates C admits that pass `S_val` but turn a correct `S_test` answer wrong.
- **E6.** Proposals that are order-sensitive under V8.
- **E7.** Verdict-file SHA-256 under the label-invariance conditions (P2).

## 8. Tiers

**Tier 1: self-tested conformance.** Claude writes a seeded generator using seeds 0–199. It builds `G*`, `G0`, `E`,
the splits and every candidate class below, and checks that the code does what §5 says. The generator and the verifier
come from the same author, so every Tier 1 number is **SELF-TESTED** and is true by construction where the class was
defined by a check. Tier 1 tests conformance, not discrimination.

Candidate classes the generator must produce in every seed:

| Class | Construction | C should give |
|---|---|---|
| T-ev | omitted true relation, cited to a true artifact | `ALLOW_CANDIDATE` unless V7 or V8 fires |
| T-none | omitted true relation, no citation | `DEFER NO_EVIDENCE` |
| F-fab | false relation, cited hash not in `E` | `REJECT FABRICATED_EVIDENCE` |
| F-mis | false relation, cited to a real artifact that asserts something else | `REJECT CITATION_MISMATCH` |
| F-type | type-invalid relation | `REJECT TYPE` |
| F-con | well-typed, planted artifact, breaks K2–K4 | `REJECT CONSTRAINT` |
| F-val | well-typed, planted artifact, consistent, flips an `S_val` answer | `REJECT VALIDATION_REGRESSION` |
| F-blind | well-typed, planted artifact, consistent, touches no `S_val` question | **`ALLOW_CANDIDATE`**: C has no signal |
| F-rule | `operation` targets constraints or questions | `REJECT RULE_CHANGE` |
| F-replay | reused `proposal_id` or stale `parent_version` | `REJECT REPLAY` or `PARENT_MISMATCH` |

Test method, following the standing procedure: spec-derived property tests across all 200 seeds, with no answer key
and registered before running. The named mutants in §6, plus any further mutants, are run against the suite, and kill
counts and line coverage are reported.

**Tier 2: blind.** A label author who is not the implementer writes the cases. That is the owner by default, or a
named party the owner chooses. Minimum size:
- at least 3 graphs of 8–12 entities, each with at least 12 relations in `G*` and at least 2 omitted;
- across the tier: at least 6 T-ev, at least 2 T-none, and at least 16 false candidates, of which **at least 8 are hard**
  (author-intended to look supported and consistent);
- at least 10 `S_val` and at least 10 `S_test` questions per graph.

The author does not classify candidates by verifier check. The table above is Claude's taxonomy, and Claude may suggest
attack ideas to the author, but Claude writes no Tier 2 case and no expected answer.

**Pre-seal integrity gate (checker-free, run by the author before sealing).** This gate does not use the verifier. It
uses a separate reference evaluator, pinned at the frozen commit, which:
1. recomputes every `S_val` and `S_test` answer from `G*`;
2. re-hashes every artifact;
3. confirms that no omitted relation is already present in `G0`;
4. confirms that `G*` satisfies K1–K4;
5. confirms that no question appears in both splits.

Any mismatch is fixed before sealing. DPC-001 blind run 1 lost a case to a test-author oracle error that a gate like
this would have caught. The gate's output is shown only to the author.

## 9. Registered predictions

| ID | Prediction | Refuted if | Tier |
|---|---|---|---|
| P1 | Anti-vacuity: M-accept admits 100% of false candidates. M-reject admits 0% of T-ev. Each ablation changes at least one verdict relative to C. | Any part fails. An ablation that changes nothing means that check is **inert on this task set**, and it is recorded as a vacuity finding, not a pass. | 1 and 2 |
| P2 | Truth-blindness: C's verdict file is byte-identical in three conditions: sealed files absent from the filesystem, present, and present with labels permuted. | Any difference. The run is then **VOID**, and E1 is not reported. | 1 and 2 |
| P3 | Conformance: on all 200 Tier 1 seeds, every class gets the verdict in the §8 table. | Any seed or class differs. | 1 (SELF-TESTED) |
| **P4** | **Primary:** Δ ≥ 0.25 on hard false candidates **and** E2 ≥ 0.80. | Δ < 0.25 or E2 < 0.80. | 2 |
| P5 | Coverage floor: if at least 4 hard false candidates touch no `S_val` question, C admits at least 1 of them. | C rejects all of them. That would imply a signal C is not supposed to have, so P2 and the code are audited before anything is concluded. | 2 |
| P6 | Adopted-graph `S_test` accuracy: acc(C) ≥ acc(A) > acc(B). | Either inequality fails. | 2 |
| P7 | **Unrun door:** an AI proposer arm, given only the public release, produces at least one hard false candidate that C admits. | Not run in EGOE-0. It needs Gate 2 (§10) and separate owner approval. | none |

On P4: with 8 hard false candidates, a difference of 0.25 is 2 candidates, and the 95% intervals overlap widely. A
pass at the minimum size is weak evidence and will be reported as weak. A larger Tier 2 strengthens it, but the size is
fixed before sealing, not after looking.

**Stopping rule.** Each sealed Tier 2 set is run exactly once. A defect found after reveal is recorded, the code is
fixed under a new revision, and confirmation needs a **new** sealed set. The revealed set becomes exploratory.

## 10. Separation protocol and gates

**Commit–reveal (Tier 2):**
1. Code freeze. Verifier, arms, scorer and the reference evaluator are committed, and their file SHA-256 values are
   recorded. Tier 1 has passed at this commit.
2. The author writes the Tier 2 set on their own device, after the freeze, in the order given in §4, and runs the
   pre-seal gate.
3. The author publishes two SHA-256 values in this repository: one for the public part (`G0`, `E`, `S_val`, the
   proposal stream) and one for the sealed part (`G*`, labels, `S_test` with answers). Nothing else is published yet.
4. The author runs all arms on the public part and commits the verdict files' hashes.
5. Reveal. The author releases the sealed part. The scorer checks it against the hash from step 3 and then scores.

The implementer never holds the sealed part before step 5, so blindness comes from physical separation, not from a
sandbox. Phase 1 needs no proposer isolation, because the proposer is a fixed file the author wrote.

**Gates:**
- **Gate 0 (existing capability): done on 2026-10-16.** No graph, versioning or ontology code was found in this
  repository. EXP003's DEFERRED-on-invalid gate pattern and DPC-001's sealed-run record are reused as **patterns**,
  not as code. This is not an integration with EXP003, DPC-001 or Sovereign Veritas.
- **Gate 1 (spec freeze):** this file, once the owner approves it and it is merged. Thresholds change only by a dated
  amendment made before any Tier 2 seal.
- **Gate 2 (proposer isolation):** **blocked** for any AI proposer. On Android without root there is no enforceable
  sandbox, and EXP003's external adapter is explicitly not one. P7 stays unrun until a real sandbox exists or the
  proposer runs on separate infrastructure with no access to the sealed part.
- **Gate 3 (controls):** P1 and P2 must hold before E1 is read.
- **Gate 4 (owner authority):** no real ontology adoption, repository mutation outside this experiment, publication of
  results or paid compute without specific approval.

**Independence.** Tier 2 is blind with respect to the implementer, not independent of the owner. If the owner writes
the labels, the result is **owner-authored, implementer-blind** and has not been independently replicated. Replication
by a second author on a fresh sealed set is a separate future run.

## 11. Recommendation and what approval covers

**Recommendation:** go ahead with Phase 1 (scripted proposer, Tiers 1 and 2) once this spec is approved. Hold the AI
proposer (P7) at Gate 2.

| Item | Estimate |
|---|---|
| Compute | stdlib Python, runs in seconds on the S25 or in CI, no paid services |
| Implementation and Tier 1 | about 2 Claude sessions (an estimate, not measured) |
| Tier 2 authoring | several hours of the author's time by hand (not estimated more closely) |
| Blockers | owner approval of this spec; a named Tier 2 author; Gate 2 for P7 only |

Approving this file approves implementing Phase 1 and the Tier 1 self-tests. Running Tier 2 needs a second approval
once a Tier 2 author is named.

## 12. Answers to the questions in the 2026-10-15 draft

| Question | Answer |
|---|---|
| Is an ontology needed? | No. See §2. |
| What can be reused without claiming integration? | EXP003's gate pattern and DPC-001's seal-and-record procedure, as patterns. No code import. |
| What is the smallest falsifiable contract? | P4 on Tier 2, guarded by P1 and P2. One missing relation could not be falsified, because n was too small. |
| Who writes which tests? | Claude: Tier 1 and the code. The Tier 2 author: every blind case, label and answer. |
| How is oracle separation demonstrated? | P2's label-invariance test, plus commit–reveal with the sealed part physically off the implementer's side. Neither proves there is no side channel. Together they make dependence on labels detectable. |
| PROCEED, DEFER or REJECT? | PROCEED for Phase 1 after approval. DEFER the AI proposer. |

## Provenance

Revision 1 was drafted by Claude (Anthropic, Opus 5.5) from the 2026-10-15 design handoff, whose author is not recorded
in that document, and from Claude's own Gate 0 review of this repository on 2026-10-16. Chain: AI drafting → human
validation: not performed → human editing/curation: direction by Chad Holland, 2026-10-16 → human responsibility: Chad
Holland. Human review level: direction only. No experiment was run and no code was written.
