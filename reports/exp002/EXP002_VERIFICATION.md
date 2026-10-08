# EXP002 — Verification Record

Research project: VERITAS ORIGIN
Date: 2026-10-08

## Evidence

Original evidence:
evidence/exp002/exp002-20261008T194950169959Z-fccc3f26.json

SHA-256:
a5fe362571ea600485cabd6759542314f0e6562e36ea6330feeb06db187faf6c

Frozen runner SHA-256:
0735ad604ce5d45f5f277894615382d855187c2d2af4490b94b44c84edcea44b

## Observations

Fixed-medium mean: 49.84
Random mean: 49.72
UCB1 mean: 66.90

UCB1 minus fixed-medium: +17.06
UCB1 minus random: +17.18

Preregistered minimum: +5.00 against each baseline.

Criterion met: YES

## Verification

Behavioral tests: 10/10 passed.

A separate inline Python verifier reconstructed
30,000 trial records and matched the recorded
policy means and decision criterion.

Reported verdict:
CONSISTENT WITH EXP002 SPECIFICATION

The verifier did not import the frozen runner,
but used the same Python randomization behavior
and mathematical policy specification.

The verifier source has not yet been archived
as a standalone executable file.

## Methodological disclosure

The behavioral test suite invoked the complete
run() computation in memory before the designated
evidence-producing execution.

No evidence was saved during that earlier test.

The preregistered evaluation parameters were
not changed after observing the results.

## Limitations

Synthetic stationary Bernoulli environment.
No cross-runtime replication.
No demonstrated autonomous hypothesis generation.
No real-world generalization claim.
No statistical significance claim.

Consistency with the recorded specification
does not establish external truth.

Research status:
NARROW PREREGISTERED CRITERION MET.
FULL SYSTEM NOT VALIDATED.
