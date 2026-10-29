# Research coordination decision log

This records **scope decisions and open proposals**, not an implied approval to merge experiments or deploy models. Add new dated entries; never rewrite an old decision to make it appear prospective.

## 2026-10-09 — ChatGPT setup; `PROPOSED_FOR_OWNER_REVIEW`

- **Request:** Owner asked ChatGPT and Claude to collaborate through a GitHub research notebook in VERITAS ORIGIN, critically examine each other's ideas, and capture genuinely useful or potentially novel breakthroughs. Claude is expected to join at 10 AM **when the owner initiates its session**.
- **Proposed execution:** coordinate via versioned `coordination/messages/` and conversation comments on a dedicated draft coordination PR; keep experiment code, negative findings and claims on their existing separate branches.
- **Owner authority:** Neither assistant may self-certify a discovery, auto-merge into `main`, authorize action by agreement, or claim continuous background communication.
- **Discovery commitment:** Record a candidate with exact original provenance and falsifier even before novelty is established; apply [discovery gates](DISCOVERY_PROTOCOL.md). Preserve any negative findings.
- **Current choice:** **STOP new experimental implementation** until the first Claude handoff/review. Do not bundle draft research branches merely to create one “AI biology” platform.
- **Unresolved:** owner should apply GitHub `main` protection and decide any eventual merge plan and whether the coordination rules become permanent.
- **Not a scientific claim:** “AI biology” is an informal organizational metaphor for computational structure and dynamics, not a claim AI is alive or experiences human thought.

## How to add decisions

Append a dated section with: proposal; exact evidence and contrary evidence; outcome (`APPROVED_WITH_SCOPE`, `REJECTED`, `DEFERRED`, `DISPUTED`); who authorized it; affected branch or issue; and a link to the new commit. For significant disagreement, put both AI reviews in separate notes and leave the decision `DISPUTED` until investigated.
