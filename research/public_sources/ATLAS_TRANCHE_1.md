# Veritas-Origin Public Research Atlas — tranche 1

**Date:** 2026-10-10 (US Central)  
**Status:** `SOURCE_DISCOVERY_ONLY / NO_EXPERIMENT / NOT_INDEPENDENTLY_REPRODUCED`  
**Author:** ChatGPT (GPT-6), at the owner's request to systematically use public internet literature, code repositories, failures and benchmark reports.

**Boundary:** This atlas lives on a separate research branch. It changes no DPC-001 v0.2 frozen bytes or v0.1 negative results, and does not implement or execute DPC-001-M2, v0.3 or any outside attack. It is *not* a literature systematic review, licensed-data import, source-authenticity certification, or replication. Publicly posted assertions and leaderboards are hypotheses/evidence to inspect, not automatic ground truth.

## 1. Where we can retrieve knowledge

| Source class | Platform / canonical starting point | Use | Observed access in this pass |
|---|---|---|---|
| Distributed open source | [GitHub](https://github.com), [Codeberg](https://codeberg.org), [Forgejo](https://forgejo.org) | Read exact commits, tests, issues, negative reports, implementation changes. Cross-host repos are NOT presumed mirrored or identical. | GitHub project pages/docs retrievable. **Direct Codeberg repository content ACCESS_UNVERIFIED**: web retrieval hit robots denial; [Codeberg's own Git guide](https://docs.codeberg.org/git/) read, but that does not establish access to a particular repo. |
| Models, datasets, research | [Hugging Face Hub](https://huggingface.co), [HF model cards](https://huggingface.co/docs/hub/main/en/model-cards), [HF dataset cards](https://huggingface.co/docs/hub/main/datasets-cards) | Model revisions, licensing, intended uses, data splits, evaluations and limitations. Cards are *author descriptions*, not independent audit. | Official documentation read; particular model/dataset artifacts NOT fetched. |
| Paper origins | [arXiv](https://arxiv.org), [ACL Anthology](https://aclanthology.org), [OpenReview](https://openreview.net), [ACM Digital Library](https://dl.acm.org) | Primary papers, preprint history, methods, venue reviews and revisions. Distinguish preprint, peer-reviewed and retracted/corrected versions. | Selected arXiv abstracts/metadata and publication-site docs retrieved; full text/version hashes NOT captured. |
| Scholarly discovery graph | [OpenAlex works](https://help.openalex.org/api/endpoints/), [Papers with Code](https://paperswithcode.com/about) | Discover references, citing work, evaluation datasets and code. This is secondary indexing, not proof of a paper's results. | Official OpenAlex API / Papers with Code documentation accessible. |
| Archived experimental artifacts | [Zenodo](https://zenodo.org), [Zenodo GitHub archiving docs](https://help.zenodo.org/docs/github/) | Immutable, citable releases; verify DOI version, attached files and file digests, not DOI alone. | Official archival workflow documentation read; particular DOI artifact NOT fetched. |
| Background / alternate PDFs | [Wikipedia](https://en.wikipedia.org), [Academia.edu](https://www.academia.edu) | Vocabulary and discovery; follow citations back to original documents. Academia may involve account/paywall restrictions; a posted PDF is not automatically official. | A Wikipedia article and Academia help page accessible; Academia research-paper content NOT fetched. Do not use Wikipedia/Academia summaries as sole empirical evidence. |
| Standards and risk frameworks | [in-toto](https://github.com/in-toto/attestation), [SLSA](https://slsa.dev/spec/v1.2/), [Sigstore](https://docs.sigstore.dev/), [TUF](https://theupdateframework.io/docs/metadata/), [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) | Prefer an existing explicit verification contract to custom pseudo-attestation or unbounded governance claims. | Relevant current official specification/docs inspected; downstream integration NOT verified. |

## 2. Primary-source starting set, ranked for our research

Source page accessibility labels describe **this reconnaissance only**. `PAGE_READ` means source landing / relevant documentation excerpt inspected; it does **not** mean full PDF, history, code and benchmarks reproduced. A new `SOURCE_MANIFEST.tsv` with exact revision, retrieval UTC timestamp, access and local SHA-256 is required *before* relying on an implementation or making a reproducibility claim.

| ID | Primary source | Access | Why it matters / caution |
|---|---|---|---|
| A01 | [in-toto Attestation Framework v1.2](https://github.com/in-toto/attestation/blob/main/spec/README.md), [Statement subject digest](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md) | PAGE_READ | Envelope authentication + subject digest + typed predicate + bundle. Candidate for verifiable bound artifacts. IMPORTANT: in-toto **intentionally ignores unrecognized fields** by default for extensibility; a closed application-specific contract schema remains a *separate* policy decision. |
| A02 | [Sigstore cosign blob verification](https://docs.sigstore.dev/quickstart/quickstart-cosign/) | PAGE_READ | Verify signature, certificate identity and artifact with a bundle. For an offline-first design compare verification using pinned trust roots/bundles rather than requiring cloud on every action. A correctly signed **false claim stays false**. |
| A03 | [SLSA specification v1.2](https://slsa.dev/spec/v1.2/), [provenance](https://github.com/slsa-framework/slsa/blob/main/spec/build-provenance.md) | PAGE_READ | Verifiable build/source process is different from a true scientific claim. Provenance controls should not be mistaken for the trustworthiness of a declarant's `facts`. |
| A04 | [TUF metadata roles](https://theupdateframework.io/docs/metadata/) | PAGE_READ | Threshold keys, targets with hashes and sizes, root/snapshot/timestamp roles. Candidate study of rollback/rotation/freeze resistance for locally updated verification policy. |
| A05 | [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) and GenAI profile | PAGE_READ | Inventory, measurement, risk framing and scope-based controls. Guidance, not an implementation or a proof that our execution gate cannot be bypassed. |
| A06 | [Lewis et al., RAG (2020)](https://arxiv.org/abs/2005.11401) | ABSTRACT_READ | External retriever + parametric generation; supports local literature retrieval strategy, not verified attribution or immunity to incorrect retrieved material. |
| A07 | [Asai et al., Self-RAG](https://arxiv.org/abs/2310.11511) | ABSTRACT_READ | Adaptive retrieval and self-reflection, with author-reported evaluation gains. Critique tokens/self-checking are not independent evidence. |
| A08 | [Yao et al., ReAct](https://arxiv.org/abs/2210.03629) | ABSTRACT_READ | Iterative reasoning/action/observation; useful orchestration pattern, but tool outputs form an untrusted input boundary. |
| A09 | [Debenedetti et al., AgentDojo](https://arxiv.org/abs/2406.13352), [code](https://github.com/ethz-spylab/agentdojo) | ABSTRACT_AND_REPO_READ | Realistic tool-based prompt-injection evaluation, attacks/defenses. Use separate user-task completion and safety outcomes, not a single green score. |
| A10 | [UK AI Security Institute, Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai), [Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals) | REPO_PAGE_READ | Existing eval infrastructure and logging, helpful for fully reproducible multi-model runs. Choose local-compatible subset; no assumption that every benchmark can run on Snapdragon or without a model provider. |
| A11 | [Liu, Passing the Test You Trained On (2026 preprint)](https://arxiv.org/abs/2610.03448) | ABSTRACT_READ | Author reports poor cross-benchmark transfer of prompt-injection detector rankings. Direct warning for any M2 or LDE detection result that overfits its own constructed error mix. Not independently replicated. |
| A12 | [Jimenez et al., SWE-bench](https://arxiv.org/abs/2310.06770) | ABSTRACT_READ | Real GitHub issues/patches for agent evaluation; report original paper/date/version because modern leaderboard outcomes are not those of the 2023 paper. |
| A13 | [HF Model Cards](https://huggingface.co/docs/hub/main/en/model-cards), [Dataset Cards](https://huggingface.co/docs/hub/main/datasets-cards) | DOCS_READ | Require model weights revision, tokenizer, quantization, license, evaluation split and dataset exact revision before comparing edge inference or discovery performance. |
| A14 | [OpenAlex works API](https://help.openalex.org/api/endpoints/) | DOCS_READ | Traverse cited-by/reference graph for relevant follow-up research with automated bibliographic metadata; abstract/title indexing alone is no validation. |
| A15 | [Zenodo archive a GitHub release](https://help.zenodo.org/docs/github/archive-software/github-upload/) | DOCS_READ | Citable archive of a completed evidence bundle, with independent file-manifest hashes. Repository `main` is not an immutable experiment version. |
| A16 | [Codeberg Git repositories](https://docs.codeberg.org/git/) | DOCS_READ | A Git origin has meaningful revision identifiers and can be cloned over SSH/HTTPS; **actual Codeberg repo access and hash presently unverified** in this environment. |

## 3. Proposed cross-project research questions (NOT approved experimental preregistration)

### H1 — Is the Veritas-Origin v0.2 READY declaration bound to genuine evidence?
- Existing counterexample: v0.2 accepts a fabricated `bound_artifact` string as READY, as explicitly documented in PR #25.
- Design candidate: application-specific attestation with artifact SHA-256, signer identity/role, signed predicate, bound study ID, authorization scope, expiry and offline-verifiable trust root. Compare with in-toto/Sigstore rather than writing an ad hoc signing scheme.
- Positive: correct authenticated artifact and matching declared facts; negatives: nonexistent artifact, digest mismatch, untrusted signer, altered predicate, stale/rollback evidence, proof content contradicting declared fact.
- **Important failure mode:** authentic signatures on a false statement do not establish truth; validating *content* against empirical record requires an independent rule/reviewer.

### H2 — Does a portable literature-retrieval agent improve factual source claims?
- Independent fixed corpus: papers/repo files archived with revision and SHA, including deliberate conflicting versions and known negative findings.
- Controls: no retrieval, random retrieval, BM25 only, dense retrieval, and/or citation-verified retrieval; same held-out questions, identical token/resource budgets.
- Measure citation support, abstention calibration, source/version retrieval, fabricated citations, poisoned pages and wall-time/energy on edge device.
- A self-assessed answer or matching its own retrieval context is **not** a correctness oracle.

### H3 — Do governance controls generalize beyond in-house mutants?
- Independent adversarial cases inspired by AgentDojo, plus real tools/logged action boundaries.
- Measure user task completion, unauthorized execution, provenance fidelity, false-refusal cost and test-suite reachability independently.
- Maintain clear division: action gate decisions are **not** proof all possible execution paths are mediated.

### H4 — How much does the DPC-001-M2 pre-seal gate really catch?
- Keep [DPC-001-M2 PR #28](https://github.com/holland202/veritas-origin/pull/28) separate. Review its prospective `AMENDMENT_1_DRAFT.md` before implementing or executing.
- Measure per error class and test target-mechanism attribution, rather than pooling easily caught malformed inputs with semantically wrong but well-typed oracles.
- Use the transfer warning in A11 as reason **not** to generalize internal planted-error catch rates to real author mistakes.

## 4. Operational retrieval contract for future tranches

For **each** external claim and planned imported artifact, record:

`source_id, platform, canonical_url, publication_status, author_or_publisher, stated_date, retrieved_utc, access_status, original_revision_or_version, local_path, sha256, claim_excerpt_location, test_reproducibility_status, conflict_sources, license_notes`.

Controlled statuses: `PAGE_READ`, `ABSTRACT_READ`, `DOCS_READ`, `REPO_PAGE_READ`, `FULL_TEXT_READ`, `SOURCE_FETCHED_AND_HASHED`, `REPRODUCED`, `ACCESS_UNVERIFIED`, `BLOCKED`. Never promote a paper's abstract into a replicated numerical outcome. Cite the original source for claims; assign `SOURCE_FETCHED_AND_HASHED` only when actual bytes are retrieved and digested; assign `REPRODUCED` only when the procedure, parameters, substrate, output and exit status are preserved.

**Priority:** close evidence-authentication limitations with falsifiable external controls **before** increasing agent autonomy or adding unnecessary LLM-specific architecture. Everything in this map is a candidate input, never authority to weaken a frozen gate.
