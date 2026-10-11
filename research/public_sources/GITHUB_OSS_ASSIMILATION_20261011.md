# OSS Methods Assimilation — GitHub screenshot research intake, 2026-10-11

**Status:** `PUBLIC_SOURCE_TRIAGE / DESIGN_TRANSFER_ONLY / NO_EXTERNAL_TESTS_RUN / NO_VALIDATION_CLAIM`

Prepared by GPT-6 from the user's GitHub screenshots and a read-only inspection of primary repositories. This is a candidate architecture and experiment inventory, **not** an endorsement, an independent audit, an imported dependency, or a finding of scientific correctness. Each snapshot below is the inspected GitHub branch HEAD at research time; the README blob SHA is a **Git SHA-1 object name**, not a SHA-256 source-materialization manifest. Re-fetch pinned commits and hash actual artifact bytes before any reproduction.

## A. Evidence-weighted source intake

| ID | Public source (pinned revision) | Inspected README blob | Relevance | Safely reusable method, not a claim of success |
|---|---|---|---|---|
| G01 | [tiwai/kernel-review-agent](https://github.com/tiwai/kernel-review-agent/tree/c73abd688005ab8170b1c875599125e6395e7b19) | `62e09c63e1216b4759521dfe2f80b4a90846dae5` | HIGH | Commit-scoped, subsystem-specific reviews; verify proposed bugs against reachable code paths; structure findings and filter false positives |
| G02 | [OpenRSI-Foundation/OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/dcfbc43b117b92d276837aa0d48f291d544fcf7a) | `a780bb20a847b4fc587cd763ef438498ab166065` | VERY HIGH | Independent isolated Work/Judge environment and hidden evaluation tests; restrict agent access to grading files; preserve submissions and feedback |
| G03 | [github/spec-kit](https://github.com/github/spec-kit/tree/0443760542e7e5269724744a2ac55c4bd386d095) | `4b463b2e599a2e8881b898ac7a4701fb23c0c91c` | HIGH | Specification→plan→tasks→implementation→convergence; separate bug-fix and idea-assessment tracks; document an explicit project constitution |
| G04 | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec/tree/9111a7654d7800391459431fff4eaf66e33a3d2e) | `f7a4e5e06e11b1ef15d99dd577afd372a3e015ea` | HIGH | Changes tracked as separately reviewable specs, designs and artifacts; cross-repo requirements stored outside implementations; non-linear change lifecycle |
| G05 | [microsoft/AIOpsLab](https://github.com/microsoft/AIOpsLab/tree/ccf08d0d1d5fa5b30f120e2e8549662d44411b35) | `53a1921c6d9a83f9611fdbbad2942a2be329424b` | HIGH (cloud, not phone-first) | Controlled service faults, telemetry, agent recovery actions and repeatable scoring; test task outcome independently from monitoring quality |
| G06 | [arndb/syscalls-table](https://github.com/arndb/syscalls-table/tree/29ae949694f77f95682e15f7c0fce8d33ad6a224) | `677875a38572b8aa39da0937ca1b944c20fad717` | HIGH for enforcement portability | Syscall numbers vary by architecture: never reuse x86_64 seccomp numeric assumptions on Android/aarch64 |
| G07 | [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands/tree/2d174175cedeac45a0bd7c776728464d7c1140a7) | `a69cedcc732da7954f3f60d25ef9ad1e7836365b` | MEDIUM | Compare agent orchestration with its Docker sandbox **scope limitation**: sandboxing conversation execution does not imply the full automation service is confined |
| G08 | [obra/superpowers](https://github.com/obra/superpowers) | `e40ddfa8f87a374e1b9a3663b80c1aa954cf8eec` | MEDIUM | Reproducible red/green testing, dedicated review, clean worktrees, and post-failure debugging; structured software practice is not scientific preregistration |
| G09 | [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | `b19b2861261e21782fa13d887b6303fc0472d07a` | MEDIUM | Scale workflow to the task instead of forcing a heavyweight process; explicit requirements ownership |
| G10 | [Haris16-code/KryonOS](https://github.com/Haris16-code/KryonOS) | `8a10edbd133bb33ca65e39ee7bd0cdce745f436d` | LOW-MEDIUM | Potential embedded-system test patterns; an ESP32 GUI/app OS is **not** evidence that its small-model behavior transfers to our S25 Termux runtime |

### Linux developer screenshots: how to classify them

The profiles for `andy-shev`, `davem330`, `arndb`, `broonie`, and `tiwai` point toward experienced Linux subsystem work in platform/firmware, networking, cross-architecture syscalls, audio/regulators, and kernel commit review, respectively. **A developer's profile or fork alone is not a source-level test or a technical claim.** Inspect upstream commits, exact file revisions, issue histories and current maintainer documentation before adopting any mechanism. Forked `linux`, `u-boot`, `net-next` and `sound` repositories can be historical or personal trees, and should not be treated as canonical release or deployment evidence.

The GitHub screenshots also contain 69.7k search-result pages, broad “AI development” code hits, and unverified discussions. **Search ranking, stars, recent updates, or a post title do not establish correctness, safety, reproducibility, licensing rights, or fit for our research.** The screenshots' code-search counts do not describe a coherent dataset and must not be included as experiment input without a defined sampling procedure.

Other shown projects such as `tiwai/hda-emu`, `broonie/tinyhardware`, `microsoft/RD-Agent`, `openchamber`, `Fission-AI/OpenSpec`, `OpenHands`, and general “AI agent” frameworks are discovery leads only until exact source and evaluation material is examined. No direct source evidence was inspected for every listed screenshot hit.

## B. Two methodological cautions found in source

### B1. Same-zero findings do not establish review equivalence

The `tiwai/kernel-review-agent` source includes [Prompt Set Verification Results](https://github.com/tiwai/kernel-review-agent/blob/c73abd688005ab8170b1c875599125e6395e7b19/docs/dev/PROMPT_SET_VERIFICATION.md) comparing large and small prompt sets. It reports cases where both configurations returned **zero findings** for fix commits, and calls them equivalent. That supports a narrow *same-observed-output-on-these-cases* statement. It does **not** establish equal sensitivity to planted regressions or calibrated confidence, because a refuse-everything/detect-nothing reviewer could also score zero on those particular cases.

**Assimilate the process, not the inference:** require seeded actual defects, known clean negatives, open negative findings, positive/negative precision and recall, and independent adjudication of code-path reachability. Treat “no defect reported” as a result, not proof of safety.

### B2. Hidden tests reduce leakage but do not eliminate score-driven overfitting

[OpenRSI's RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/blob/dcfbc43b117b92d276837aa0d48f291d544fcf7a/RSI-Harness/README.md) starts a persistent isolated Work container, keeps private tests unmounted, snapshots submissions, and evaluates each in a fresh isolated Judge. The agent receives score feedback and may submit again. This protects direct test-file access under the described mechanism, but repeated evaluation feedback can still let a developer optimize to a fixed judge. A final, **unused held-out evaluation** and explicit submission budget are needed for a stronger generalization claim.

An [ACE playbook repair task](https://github.com/OpenRSI-Foundation/OpenRSI-Index/blob/dcfbc43b117b92d276837aa0d48f291d544fcf7a/rsi-tasks/ace-playbook-repair/README.md) explicitly reports a single-seed lightweight protocol and warns that it loses between-seed variance estimation. That caution is especially important for LDE: matching one seed or budget does not establish transfer across worlds, models or architectures.

## C. What to assimilate, by project

| Target | Architecture or method | Proposed acceptance test (NOT IMPLEMENTED) | Authority boundary |
|---|---|---|---|
| **Veritas-Origin** | `Claim → source revision → artifact digest → exact evidence rows → inference limits → versioned status`; structured case review using independent bug reachability checks | Blindly authored defects in a copy of the claim audit; measure detection *and* false accusation rate; enforce no automatic promotion from internal consistency to scientific truth | Existing DPC-001 v0.2 frozen. MTA-001 PR #34 remains its own experimental instrument. |
| **LDE** | Separate agent Work from hidden Judge; frozen seed-generation and resource budgets; a final, never-seen evaluation set | Fixed prereg worlds and false-solution controls; score discovery, held-out accuracy, repeat stability, oracle leakage, seed variance and substrate portability independently | Keep original LDE baseline/confirmatory source immutable; do not infer x86 reproduction from stdout digests alone. |
| **Sovereign Veritas (new separate prototype only)** | Spec-first immutable action descriptor; broker sole authority; OS-level confinement where available; subsystem-style adversarial code reviews | Denial bypass through alternate process/API path, descriptor mutation, fd reuse, symlink, replay, crash windows; count mock effects and refusals separately | **Main Sovereign Veritas remains maintenance-only; do not add features there.** Actual effects and shell privileges must be absent from initial experiments. |
| **Evidence Circuit VEC** | Offline signature verifier plus independently reviewed parsing/resource design; separate verifier status from action permission | Cross-implementation DSSE vectors; new external malformed evidence generator; positive genuine signature and negative false-yet-signed content | VEC PRs #30–#33 experimental. Earlier author-designed pass rates do not independently certify security. |

## D. One reusable integration pattern

```text
PUBLIC SOURCE (untrusted)
  → pinned revision + license + byte digest + access status
  → METHOD HYPOTHESIS (not a borrowed success claim)
  → independently adjudicated failure/positive controls
  → preregistration + immutable source and budget
  → isolated Work environment ────────┐
  → frozen hidden Judge / holdout <─────┘
  → structured outputs with exit statuses and negative findings
  → claim/evidence drift audit (MTA-001 compatible)
  → separate epistemic verdict: supported / unresolved / contradicted
  → separate action authorization (Sovereign Veritas) — NEVER implicit
```

## E. Proposed next studies (NOT YET PREREGISTERED)

1. **OSS-RV-001 — review sensitivity.** Compare blind code-review prompts derived from Kernel Review Agent with a baseline reviewer on pinned known-good/known-bad synthetic changes to *our* research code. Predeclare bug reachability, reviewer conflict adjudication and per-class precision/recall before running. Include refuse-all/always-bug controls.
2. **OSS-JG-001 — isolated judging.** Reproduce a minimal no-network Work/Judge separation for *inert LDE-generated rules*, with a fresh untouched final holdout distinct from development feedback. Test if the agent can read the hidden oracle, forge a score, alter committed test code, or leak task identity through file metadata. No external credentials.
3. **OSS-SP-001 — spec-to-evidence drift.** Use a small subset of Spec Kit/OpenSpec artifact-linked rules to record contract changes *without changing frozen contracts*. Inject missing tasks, inaccurate verification reports and stale documentation; check for both detections and false positives.
4. **OSS-OS-001 — portability matrix.** Compare Linux seccomp/Landlock/cgroups capabilities on unprivileged S25 Termux versus a disposable Linux VM, using read-only detection first; no live security policy installed until a separate permissioned study.

**Ranking:** OSS-JG-001 and OSS-RV-001 offer the strongest improvement in evidence independence. OSS-SP-001 may reuse most of existing DPC-001/MTA-001 work. OSS-OS-001 requires platform-specific capability discovery; avoid assuming Android userland has unrestricted Linux confinement interfaces.

## Research disposition

**Assimilated:** source-level engineering ideas, known limits, candidate testable questions.  
**Not assimilated:** upstream code, promises of performance, third-party benchmark scores as our results, broad search result claims, or a claim that any repo has validated Sovereign Veritas, Veritas-Origin or LDE.

**No original experiment executed, no sandbox enabled, no repository source outside this research-note branch changed.** 
