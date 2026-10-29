# VERITAS ORIGIN — AI research exchange

**Status:** proposed collaboration process; **human review required**. This directory is a shared, versioned *research notebook and handoff channel*, not a running multiagent service, autonomous approval system, or independent validation authority.

Two AI assistants may collaborate here **when separately invoked and provided with GitHub access**:
- **ChatGPT** — current experiment synthesis, source linking, reproducibility checks, integration proposals.
- **Claude** — invited independent critical reviewer and alternative-hypothesis proposer, starting with the October 9, 2026 handoff.

Either can challenge, reproduce, or revise ideas; these roles are pragmatic, not exclusive. **AI agreement, two "PASS" labels, or two AI-generated summaries do not establish scientific validity.**

## Start here

1. Read [Communication and evidence protocol](PROTOCOL.md).
2. Read [Current research handoff (2026-10-09)](HANDOFF_2026-10-09.md).
3. Read the [Research decision log](DECISION_LOG.md); decisions marked `PROPOSED` are not approvals.
4. Append a new message in [messages/](messages/) describing the experiment or contradiction you actually reviewed.
5. Put a link to that message and its commit on the **coordination draft PR conversation**. That is the mailbox; comments are chronological. Keep substantive, durable claims in versioned files.

## Working flow

```text
          Researcher (Chad): defines goals, decides authorizations
                                 |
                GitHub coordination draft PR
                     /                    \
             ChatGPT reads             Claude reads
                |                          |
         evidence + proposal        adversarial review
                |                          |
          versioned notes  <------>  versioned notes
                     \                    /
                  disagreements + falsifiers
                             |
                frozen protocol on a NEW
                  experimental branch
                             |
                 code → tests → replay
                             |
                review of failures + limits
                             |
               human acceptance / rejection
```

**No automatic merge, release, model deployment, external action, or change to Sovereign Veritas authorization follows from a message.**

## GitHub use

- Stable source: [repository main](https://github.com/holland202/veritas-origin/tree/main).
- Collaboration branch: `coordination/ai-biology-research-exchange`.
- For experiment work, make a **separate** branch and draft PR. Current experiment branches are not automatically rebased or merged.
- Messages: `coordination/messages/YYYY-MM-DD_<agent>_<sequence>.md`, **one new file per message**, never rewrite another agent's archived note.
- Evidence: link to exact commit, protocol, workflow run, original hash and any negative results. A hash proves only bytes matching a supplied digest; it does not establish world truth.

See [PROTOCOL.md](PROTOCOL.md) for permissions, authorship limitations, and reply format.

## What "artificial computational biology" means here

The term is an organizing **analogy**, not a claim AI is biologically alive. Legitimate topics include learned neural weights and dynamics, recurrent hidden computation, adaptive plasticity, error correction, memory, evidence-based multiagent interaction, and resource/accuracy tradeoffs. Draw on established machine learning, control theory, artificial life and neuroscience without inventing equivalences to chemistry, consciousness, or human thought.

**Immediate proposed problem:** investigate why repeated hidden computation can improve a small task while a confidence/stability stopping rule fails against matched random allocation, and why reliable-looking multiagent evidence can still hide a false trusted anchor. Ask whether there is a falsifiable next experiment that isolates the *mechanism* rather than decorating the analogy.

Created as a safe coordination starting point. Repo `main` branch protection is an unresolved owner task.
