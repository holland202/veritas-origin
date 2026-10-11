# OSF-001 — Owner-run corpus pilot closeout

Owner: Chad Holland — Research Director, Orchestrator, and Project Owner.
Date: 2026-10-11.
Evidence status: **owner-reported Termux output, not independently reproduced**.
Repository branch: research/five-tool-intake-20261011.

## Phase 1: corpus creation
Directory: `$HOME/osf001-evidence/corpus`. Three SHA-256-addressed files:
- Original ATH-001D, 22 bytes: `5ed6dc194a9dae6085f86c2fb9c87ba4fee53d811f7bb4af15b53ab88cdb7384`. Reference false; mutant true.
- Minimized ATH-001E, 2 bytes: `f6ddf237cd4dec7fd3140ed809a4edda8ac44fd31d58a479ee20301532438764`. Reference false; mutant true.
- Inert `OK`, 2 bytes: `565339bc4d33d72817b583024112eb7f5cdf3e5eef0252d6ec1b9c9a94e12bb3`. Reference true; mutant true.

Owner output: `FAILURES=[]`, `GATE=PASS`.

## Phase 2: read-only integrity and tamper
Owner output: `MODE=READ_ONLY`, all seven checks true: `deduplication`, `inert_integrity`, `minimized_integrity`, `no_unexpected_files`, `original_integrity`, `replay`, `tamper_detected`. `GATE=PASS`.

## Phase 3: fresh-process replay and simulated duplicate ingestion
Owner output: `MODE=READ_ONLY`, `INPUTS_INGESTED=5`, `UNIQUE_INPUTS=3`; `all_sources_valid=true`, `corpus_unchanged=true`, `duplicate_ingestion=true`, `fresh_process_replay=true`; `GATE=PASS`.

## Boundaries and negative findings
This is an OSS-Fuzz-*inspired* local standard-library workflow, **not an OSS-Fuzz run**. No hosted integration, native engine, coverage guidance, corpus minimization algorithm validation, concurrency testing, disk-write race testing, or independent verification. Phase 2's 'deduplication' only checked distinct stored hashes. Phase 3 demonstrated in-memory duplicate collapsing by hash, not repeated on-disk ingestion. Phase 2's tamper test mutated a disposable in-memory copy and verified digest mismatch; it did not tamper with the saved corpus. The replay occurred in a new Python invocation on the same owner device, not a second machine or independent implementation. Original files left untouched.

## Decision
**OSF-001 scoped pilot gate PASS (owner-reported).** Ready to proceed to Inspect AI evaluation pilot without modifying frozen LDE or DPC-001 artifacts.
