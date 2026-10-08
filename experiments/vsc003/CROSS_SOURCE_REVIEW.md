# VSC-003 cross-source research inventory (read-only)

Status: **SOURCE DISCOVERY / NOT VALIDATED / NO CODE IMPORT**. This note distinguishes exact source material inspected from user-supplied metadata and unverified external repository pages. It is not a validation of originality.

## Hugging Face material accessible for metadata review

1. [`holland202/sovereign-evidence-bench`](https://huggingface.co/datasets/holland202/sovereign-evidence-bench): public dataset describes **39 cases, 11 categories, three verdicts** (`SUPPORTED`, `REFUTED`, `NOT_SUPPORTED`) across provenance, freshness, admissibility and prompt-injection boundaries, with mechanically generated reference labels. The available Hugging Face tool returned its dataset description and MIT tag, **not the actual rows or complete oracle implementation**. It is a candidate **future external evaluation benchmark**, not a source of training labels for VSC-003. Before any later use, retrieve the exact version, verify complete files/license, preregister evaluation and prevent train/test overlap.
2. [`holland202/lde-cross-substrate-research`](https://huggingface.co/datasets/holland202/lde-cross-substrate-research): public dataset metadata indicates an October 8, 2026 update, fewer than 1,000 records and a cross-substrate research focus. Actual experiment files and integrity manifest were **not retrieved through the current tool**. Use for future **reproducibility** and substrate-drift comparisons only after reading and hashing source files. An additional Hugging Face model repository with the same name also exists but has not been established to contain executable data relevant to VSC-003.

The Hugging Face integration exposed **read** credentials (`read-repos` etc.), but no publishing/upload function here. **Nothing has been written to Hugging Face.**

## Codeberg material identified by repository activity (not inspected)

The user supplied these exact repository and commit identifiers:

- [`badatchess/local-discovery-engine`](https://codeberg.org/badatchess/local-discovery-engine) — reported recent commit `19ddc163c6`, `Add advanced evidence research curriculum`; `81c6578f5c`, Azure cross-substrate LDE-2G report; `f979705293` confirmatory implementation; `001a3e6ca6` preregistration; earlier LDE-2F adversarial interaction, LDE-2E collaboration, LDE-2D communication, LDE-1 and LDE-0.
- [`badatchess/sv-lab-vk2`](https://codeberg.org/badatchess/sv-lab-vk2) — user-reported commit `37001e3794`, deterministic VK-2 lab.

**Verification blocker:** The current available web/container fetch paths could not open Codeberg repository content, nor validate exact commit SHA, license, source, evidence or tests. Metadata here is explicitly **USER-REPORTED / UNVERIFIED**. The current GitHub connector has no Codeberg read/write action, and no Codeberg write credentials were presented. No code was imported or pushed. Never mistake a repository name or reported commit message for a verified functional mechanism.

**Future improvement opportunity:** LDE information-priority selection, adversarial interaction, and VK-2 deterministic verification may offer stronger baselines or independent audits, but no cross-source implementation is justified until exact source files, hashes, licenses, and behavior can be inspected. Preserve both Codeberg repositories; do not force-merge, rewrite, or mirror over them.

## Why VSC-003 stays independent now

VSC-003 tests a preregistered low-cost binary-check-versus-truth-label budget comparison, with full independent replay and intentional negative controls. Adding uninspected LDE or Hugging Face records as training inputs would contaminate its source and harm interpretability. The separate public benchmark and source-adapter experiment should be defined **after** this toy test, with the same evidence/provenance standards.

## Publishing plan, not completed

GitHub is the sole editable development source in this phase. After separate review and explicit safe destination selection, a new **versioned** research artifact can be uploaded to Hugging Face and an additive branch/mirror to Codeberg if suitable write access becomes available. This does **not** authorize overwriting or force-pushing existing Codeberg projects or publishing copyrighted external datasets.
