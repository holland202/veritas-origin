# DPC-001 visual guide — experimental checker candidate

> **Not a scientific result, not authorization, and not evidence of validity.**
> Frozen specification: `d05501013c7b2d0c602893e44d157620b55f12ff`.
> Checker candidate: `coordination/checkers/dpc001_checker.py`.
> Six withheld cases remain entirely outside this branch and ChatGPT's context.

## Simple view

```mermaid
flowchart TD
  A["Study contract (proposed plan)"] --> B{"Missing, inconsistent or misleading?"}
  B -->|Yes| X["CONTRACT_INVALID"]
  B -->|No| C{"Valid bounded structural check?"}
  C -->|Yes| S["STRUCTURAL_TEST"]
  C -->|No| D{"Proven unattainable margin?"}
  D -->|Yes| N["NONDISCRIMINATING_ENDPOINT"]
  D -->|No| E{"Known demonstration / weak rival?"}
  E -->|Yes| M["DEMONSTRATION"]
  E -->|No| F{"Evidence for feasibility missing?"}
  F -->|Yes| I["INSUFFICIENT_INFORMATION"]
  F -->|No| R["READY_FOR_COMPARISON"]
  R --> H["Owner authorization STILL required"]
```

## Technical view

The checker consumes a **declared contract**, not experiment outputs. Classification follows the frozen ordering in specification §2. Natural-language detection rules are intentionally limited and may misclassify unforeseen wording; any matching of an analytic bound is a check of a **declared** bound, not an independent mathematical proof.

```mermaid
sequenceDiagram
  participant Owner as Owner (Chad)
  participant Spec as Frozen specification
  participant Checker as ChatGPT checker
  participant Visible as Visible tests
  participant Custodian as Withheld custodian (Claude/Chad)
  Owner->>Spec: Approve fixed revision
  Spec->>Checker: Define rule requirements
  Checker->>Visible: Run predeclared visible fixtures
  Visible-->>Owner: Raw failures and pass counts
  Owner->>Checker: Freeze exact implementation SHA
  Checker-->>Custodian: Fixed version only
  Custodian-->>Owner: One held-out result, unchanged
  Note over Owner,Custodian: Neither two-AI agreement nor hidden-test pass is external independent validation
```

**Review gate:** This branch is a draft implementation for critique. The visible harness is in PR #20, not merged into main. Do not run or reveal withheld cases until the separate owner-approved freeze and acceptance step. Preserve all mistakes and revisions in Git history.
