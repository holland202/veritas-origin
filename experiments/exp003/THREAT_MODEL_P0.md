# EXP003-P0 — Threat model and confirmatory blockers

**Status: OPEN LIMITATIONS — NOT VALIDATED.** This is prospective risk documentation, not evidence of a completed red-team evaluation.

## T1 — Deterministic oracle leakage (HIGH)

The pilot generator and seed-based truth selection are public. Its optional external-proposer JSON context currently includes `task_seed`. A proposer with source access could deterministically reconstruct the hidden truth without collecting observations. Even removing `task_seed` is insufficient on its own: small candidate sets can be matched to enumerated seeds, and model exposure to evidence, task files, or the host filesystem breaks experimental blinding.

**Interpretation:** A high external-proposer score in P0 does not demonstrate information-seeking autonomy, even if it exceeds fixed/random baselines. Mark any such result `LEAKAGE_RISK` until an independently controlled oracle separation is implemented.

**C1 blocker:** Generate evaluation tasks on an isolated evaluator under a withheld seed or secret, keep oracle assignments inaccessible to the proposer, and expose only pre-approved observation interfaces. Preregister a digest commitment before evaluation; disclose held-out task generation details after the run. Do not commit secret keys or private oracle tables to a public repository.

## T2 — External subprocess is not a sandbox (HIGH)

The optional proposer executes as an ordinary OS subprocess with the calling user's filesystem/network permissions. The stdout-length check runs only after the process exits, so output memory is not hard-limited. The 60-second cap is per proposal, not per experiment, and the API does not enforce global CPU, memory, or cloud-cost caps.

**C1 blocker:** Separate unprivileged identity/container; network egress policy; cgroup/OS limits; global run budget; robust cancellation; and independent tests of attempted boundary crossing. P0 must only execute manually approved local proposer binaries.

## T3 — Synthetic task realism (HIGH)

Eight public binary predicates, four candidates per task, integer domain 0..31, and noiseless outcomes form a small toy environment. Greedy information gain is strong and is an essential comparison control. Model parity with greedy is not an improvement over a deterministic algorithm. Unseen domains, harder tasks, and independent replication are required for any wider claim.

## T4 — Verifier independence (MEDIUM)

The independent verifier does not import the generator but shares Python RNG behavior, predicate definitions, and task assumptions. Its PASS asserts consistency with that deterministic specification; it does not prove empirical truth, unseen generalization, or tamper resistance against an adversary able to rewrite both evidence and verifier.

## T5 — Governance/authorization (HIGH)

`--pilot` is an explicit consent flag, **not** a cryptographic capability or hardened permission gate. The current engine does not apply the separate Sovereign Veritas gate, enforce capability tokens, or provide a network-isolated execution sandbox. Do not claim integration of separate research projects or safety properties not actually tested.

**Disposition:** Treat EXP003-P0 as an exploratory engineering substrate. Freeze a separate EXP003-C1 protocol only after these blockers are addressed, reviewed, and tested. Preserve all negative controls and pilot outputs.
