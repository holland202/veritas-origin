# Claude handoff — 2026-10-11

**READ WHEN AVAILABLE. NO WORK REQUESTED WHILE ON HIATUS.**

Owner has reviewed PR #37 and marked it ready for review. Do not interpret GitHub mergeability as experimental validation. Do not start jobs, review, merge, or change files solely because of this note.

## What happened
- GitHub OSS methods triage: PR #35, research/oss-method-triage-20261011. Source reading of kernel-review-agent, OpenRSI Index, spec-kit, OpenSpec, AIOpsLab, syscalls-table, OpenHands, and other leads. Findings are methodological, not validation or imports. Key lessons: seeded defect sensitivity, avoid vacuous zero-finding equivalence, isolated Work/Judge, untouched final holdout, spec-to-evidence drift.
- Five-tool intake: PR #37, research/five-tool-intake-20261011, commit 9be14004805da957962f4130cc3ff00272863d66 at creation. Candidates: Hypothesis, Atheris, Inspect AI, official Termux API, OSS-Fuzz. One design-only research file; no dependency installations or integration tests performed.
- Additional screenshots reviewed: Termux utilities, offensive-security aggregators including may215/awesome-termux-hacking and mishakorzik/AllHackingTools, and blue-team lists. These are untrusted discovery indexes, not approved installation sources. Prefer upstream official packages and small, audited, permission-scoped components. No bulk installer, automatic exploitation, or remote scanning.
- TSP-001 device evidence from owner on S25 Android Termux/aarch64 Python 3.14.6: 18 registered tests passed and 6 theme tests passed as reported in terminal output. TSP-001 output observed self seccomp filter, cgroup v2 mount, unknown controllers/Landlock, commands found without API permission verification. --require execution yielded DEFER_UNVERIFIED and exit code 2. These are owner-provided observations, not independently reproduced or broker enforcement.
- Owner-reported substrate_probe.py SHA-256: 4f5fc3cf46ad79b70def00b437c341adf6f7e5290e17c2ec561899837ade3568 at HEAD 29958652e3cf5e5d22a680314609ae9feaa79c5d. Preserve exact revision provenance; do not conflate with earlier TSP-001 commit 3719eb367f009ee64e1432efb988359c03256b0b.
- Termux theme banner installed by owner; aesthetic only, not attestation or permission. Missing legacy health_monitor.py in .bashrc was identified.

## Next intended work (NOT an instruction to execute now)
1. Freeze baseline and source manifest, pinned upstream commits, licenses, dependency hashes.
2. Add isolated optional Hypothesis property tests with known-bad positive controls and inert negative controls, without touching frozen DPC checker/spec.
3. Bounded parser-only Atheris fuzzing and OSS-Fuzz-style crash corpus/regression protocol in disposable environment.
4. LDE Inspect AI adapter design with isolated scoring, no oracle leakage, untouched holdout, and provenance.
5. Termux API permission-aware passive observation, explicitly UNKNOWN where unverified; no external actions.

## Hard boundaries
Sovereign Veritas main maintenance-only. DPC-001 v0.2 frozen checker/spec untouched unless separate owner authorization. Research PRs remain unmerged until owner decision. Never claim source authenticity, security enforcement, scientific validity, or independent reproduction from local tests, hashes, GitHub mergeability, or screenshots alone. Preserve negative results and incomplete runs. No work requested from Claude until owner resumes collaboration.
