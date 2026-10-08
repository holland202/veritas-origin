# EXP002 — Independent strategy evaluation

Status: PREREGISTERED; NOT YET EXECUTED

## Hypothesis
UCB1 adaptive selection will obtain a higher mean reward than
both a fixed-medium policy and a uniformly random policy in
a stationary three-arm Bernoulli environment.

## Environment
Arms: low=0.2, medium=0.5, high=0.8.
Trials: 100 per policy per seed.
Seeds: 0 through 99 inclusive.
Policies: fixed-medium, uniformly random, UCB1.

## Randomization
For each seed, generate 100 independent Bernoulli potential
outcomes per arm, using separate seeded streams. All policies
receive the same potential-outcome table for that seed.
A policy choosing an arm for its nth pull receives that arm's
nth outcome. Random policy choices use a separate seeded stream.

## Primary endpoint
Mean total reward per 100 trials across 100 seeds.

## Decision criterion
Support for the narrow hypothesis requires UCB1 mean reward
to exceed both baselines by at least 5 rewards per 100 trials.
Report differences and per-seed results regardless of outcome.
This is a descriptive preregistered threshold, not a
statistical significance test.

## Limitations
Synthetic stationary environment; known arm probabilities;
one specified UCB1 implementation; no model learning,
independent replication, or generalization claim.
No post-hoc tuning of seeds, policies, or thresholds.

## Preservation
Keep all results, including failures, unchanged.
Save a new file per run. Never replace Pilot 001.
