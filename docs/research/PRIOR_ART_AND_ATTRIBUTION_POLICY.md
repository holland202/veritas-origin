# Prior-art, originality, and attribution protocol — v0.01

**Purpose:** avoid unattributed borrowing and unsupported originality claims while building VERITAS ORIGIN and its associated research interfaces.

**Status:** METHOD PROPOSAL; initial source scan is neither exhaustive nor legal advice. The companion `research/prior_art_register.json` is an inspectable inventory, **not** a certificate of legal clearance, novelty or non-infringement.

## First: distinct questions

1. **Does a comparable implementation already exist?** Search source, releases, tests, issues, PRs and discussions. Determine behavior from code and tests, not README claims alone.
2. **Is an idea new?** Compare it with software, publications, open standards, conference talks, patents, preprints, and older implementations. Finding no GitHub match cannot prove novelty.
3. **Are we allowed to reuse specific code, assets, text or datasets?** Read the exact license for the files at a pinned revision. A public repository is not automatically open source.
4. **Are we going to copy anything?** Separate *learning from an approach*, *independent implementation*, *dependency usage*, *ported/adapted code*, and *literal inclusion*. Different use modes require different traceability and approvals.
5. **Can we prove our claimed differentiator?** Define a falsifier and test it against relevant controls. A distinct product narrative is not the same as a novel mechanism.

## Process for every component and PR

### A. Register the question before modifying code

Open a small design note: component name, exact invariant, adverse scenario, success/failure criteria, why our existing components don't already solve it, and which assertions must remain `UNKNOWN`.

### B. Check our own repositories and work first

Inspect original commits, existing tests, issue histories, and licenses in Sovereign Veritas, EACE, Evidence Ledger, Veritas Companion, Eunoia and VERITAS ORIGIN. Avoid reinventing or silently relabeling an earlier negative result. An internal dependency is a separate interface, not implicit code reuse.

### C. Search outside our work, not just GitHub

GitHub file/issue/PR/commit searches (including language and older commits), official project docs, package registries, preprints and published papers. For commercially important novelty questions, consult appropriate professional patent/trademark/legal research; a GitHub sweep is incomplete.

Record **exact source permalink at a full commit SHA**, repository name, intended reference behavior, strongest observed test or gap, project maintenance state if verified, and whether the source was actually read. A README statement cannot be silently promoted to a code-level verification.

### D. Validate reuse rights separately

- Read the exact LICENSE, NOTICE, copyright header, and relevant `third_party`/data-specific terms at the revision being used; root license alone may not cover all contents.
- If missing, conflicting, unclear or under an unknown license: `LICENSE_UNVERIFIED` / `NO_ROOT_LICENSE` / `AUTHOR_DECISION_REQUIRED`. **No source copying** without explicit clearance.
- MIT/Apache licenses are *not* excuses to omit required notices; copied/adapted content and dependencies still need compliance review. Preserve original notices when conditions require it.
- Specs, APIs, data, model weights, fonts, photographs, research diagrams, brand names and software code may have **different rights**. Check each actual artifact.
- Attribution for ideas/design influence is appropriate even when no source is copied. Attribution does not itself grant permission to copy.
- The register's `STUDY_ONLY` designation authorizes citation/research only. A future reuse request needs a reviewed license and a **new version of the manifest schema**, explicit approval, and an attribution manifest.
- AI-assisted coding must be disclosed as a development method where relevant. No blanket claim of independently authored code or originality based solely on AI output.

### E. Design to contribute a testable difference, or explicitly reuse

Decision fields: reference(s); overlaps; alternatives; exact behavior that is *not* in scope of cited work or is intentionally composed; negative controls; estimated effort/cost; unresolved uncertainty. Mark `NOT_ESTABLISHED` for novelty until wider research supports a narrower statement.

Prefer importing a maintained dependency under an accepted license over silently recreating it. Prefer **independent minimal interfaces** over copying whole reference implementations. Never imply that using an existing algorithm (e.g., UCB1, greedy information gain, SHA-256, Merkle transparency, policy-as-code, container isolation) is itself a novel contribution.

### F. Verify, archive and publish honestly

Freeze the experiment protocol and checks before confirmatory work; version code and model artifacts; retain all failed cases and negative outcomes; run negative controls, mutants and an independent replay; preserve raw evidence under a unique path and pin its digest.

In review: summarize what is borrowed/cited, what is newly implemented, what remains uncertain, and whether *license compatibility* and *novelty* were actually assessed by a qualified reviewer. A passing CI gate cannot verify copyright ownership, freedom to operate, or non-infringement.

## Current verified licensing observations (GitHub public source)

| Source | Initial licensing observation | Result for copying |
|---|---|---|
| [Sovereign Veritas](https://github.com/holland202/sovereign-veritas/blob/main/LICENSE) | Root MIT | Review actual imported files and preserve notices |
| [VERITAS ORIGIN](https://github.com/holland202/veritas-origin) | No root LICENSE found on checked revision | Do not presume third-party reuse rights; owner decision |
| [Evidence Ledger](https://github.com/holland202/evidence-ledger/blob/main/README.md) | README says unlicensed, no root LICENSE found | No automatic cross-repo copy; owner decision |
| [EACE](https://github.com/holland202/eace/blob/main/LICENSE) | Root MIT | Review file notices and provenance |
| [Veritas Companion](https://github.com/holland202/veritas-companion/blob/main/LICENSE) | Root MIT | Review file notices and provenance |
| [Eunoia](https://github.com/holland202/eunoia/blob/main/LICENSE) | Root text says rights reserved, license not selected | Do not presume code copying is authorized |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/LICENSE) | Root MIT | Study only, no imported source in this branch |
| [OPA](https://github.com/open-policy-agent/opa/blob/main/LICENSE), [Cedar](https://github.com/cedar-policy/cedar/blob/main/LICENSE), [Anthropic sandbox runtime](https://github.com/anthropics/sandbox-runtime/blob/main/LICENSE), [gVisor](https://github.com/google/gvisor/blob/master/LICENSE), [Codex](https://github.com/openai/codex/blob/main/LICENSE), [in-toto](https://github.com/in-toto/in-toto/blob/develop/LICENSE), [Rekor](https://github.com/sigstore/rekor/blob/main/LICENSE) | Root Apache-2.0 | Study only; any import needs separate recorded compliance check |
| [SLSA spec repository](https://github.com/slsa-framework/slsa/blob/main/README.md) | README mentions Apache-2.0 for specification, but root LICENSE not found under requested path | **UNVERIFIED for copying** |

These observations reflect a limited source check on 2026-10-08, not a comprehensive license or patent analysis. For persistent exact revisions and source locations consult `research/prior_art_register.json`. Licenses may change and some files may have separate terms.

## Checks and their limits

```bash
python3 tools/check_prior_art.py
python3 -m unittest discover -s tests -p 'test_prior_art_gate.py' -v
```

The checker accepts **only study-only** current entries. It verifies declared URLs are full-commit pinned, source record fields exist, reviewed license state is not silently promoted, and novelty cannot be marked proven. Tests deliberately tamper with declarations to confirm failure behavior.

It **does not query the network, prove a claimed license is correct, compare source files for copying, or perform patent/ownership analysis**. Human review and independent legal diligence remain required where appropriate. Do not elevate `STRUCTURALLY_CONSISTENT` to `LICENSE_CLEARED`.

## Source-usage declaration for this design branch

Source code imported from third-party projects for this branch: **none declared**. External material was consulted and cited as references; the local Python gate is an original project implementation developed with AI assistance. This statement documents the operations of this change, not a guarantee that any text or idea is legally free of all third-party rights.
