# VERITAS ORIGIN — Cross-platform publication plan

**Status: PLANNED; mirrors are not automatically verified or synchronized.**

## Authority and release boundaries

| Platform | Job | Authority |
|---|---|---|
| GitHub \`holland202/veritas-origin\` | Canonical commits, sources, preregistration, immutable evidence and verifier | Version control; does not establish world truth |
| Codeberg \`badatchess/veritas-origin\` (candidate) | Independent Git mirror | Confirm repo identity, remote URL and matching \`main\` SHA before reporting mirrored |
| Hugging Face \`holland202/veritas-origin-evidence\` (candidate dataset) | Downloadable versioned evidence bundles and dataset cards | Publish only checksummed evidence + full lineage + limitations, verify downloaded hashes |
| Vercel | Read-only public research interface | Read only version-pinned release manifests; never compute the scientific verdict on the client |
| Azure | Experiment execution and independent checks | Resource-constrained, operator-authorized execution; no secret credential publication |

## Release gate

1. Freeze preregistration before outcome access and capture runner/model digests.
2. Execute and preserve an original evidence file without overwrite; retain negative outcomes.
3. Independently replay the evidence and save verifier source and complete stdout/stderr.
4. Commit evidence, verification report and source to GitHub. Record the full commit SHA.
5. Mirror only **confirmed commits**, with checksummed downloads. Never call a mirror current solely because a remote name exists.
6. Publish the dataset card on Hugging Face with \`EXPLORATORY\`, \`CONSISTENT\`, \`NOT VALIDATED\` or another **accurate** evidence status; avoid overclaiming.
7. Vercel reads only a pinned manifest of verified artifacts; display both successful and failed tests, with explicit date, hash, negative evidence and limitations.
8. Compare Codeberg SHA and Hugging Face file hashes to originals; report stale/unavailable destinations visibly.

## Authorization and connectivity

The Hugging Face connector session observed on 2026-10-08 had read permissions and did not find the three candidate VERITAS ORIGIN repo names. Publishing will require the owner to create the intended repository and authorize a write-capable workflow.

Codeberg target repository and push credentials for the Azure VM are **not verified**. Do not force-push, overwrite remote history, or assume the Termux Codeberg credential is present on Azure.

Vercel account registration is not the same as an accessible Vercel team/project in the connected integration. Confirm team/project scope and cost before deployment. A static first release is preferred: no Azure control-plane access, no exposed tokens, and no automatic promotion of experimental outcomes.

## Visual status design

The public dashboard should show: (a) evidence status and as-of timestamp, (b) means and differences with study limitations, (c) SHA-256 and frozen commit, (d) reproducibility commands, (e) redacted verifier output, (f) historical negative/control results, and (g) mirror freshness. Never label a zero-test or missing-evidence state as passed.
