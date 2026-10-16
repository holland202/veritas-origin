# 002: A checker that has seen the answers proves nothing

*Taught with a real event: the EGOE-0 spec rewrite, 2026-10-16 ([experiments/egoe0/SPEC.md](../experiments/egoe0/SPEC.md)).*

## Understand

Picture a teacher who grades a test while holding the answer key, and then reports, "My grading caught every wrong
answer." That is true, and it tells you nothing, because it could not have come out any other way.

The first EGOE-0 draft had this shape. Its verifier was allowed to look at the set of withheld answers, and then the
experiment measured how many false facts the verifier let through. With the answers in hand, that count was zero
before anything ran.

A measurement is worth something only when it could have come out the other way. There are two ways to make sure it
can:
1. **Keep the checker away from the answers it is graded on.** Give it some evidence to work with (a validation set),
   and grade it on a different set it has never seen (the test set).
2. **Prove it cannot see them.** Run it with the answer files removed, and again with the answers shuffled. If its
   output changes, it was peeking.

## Build: what changed in the spec

| Before | After |
|---|---|
| One withheld set, used by the verifier **and** for scoring | Three sets: proposal evidence, verifier validation, sealed test |
| Verifier could see which facts were true | Verifier is truth-blind, checked by running it with the labels absent, present and shuffled (prediction P2) |
| Compared against "accept everything" | Compared against the simplest real rival: types plus byte-checked citations (arm B2) |
| 4 false facts, written by the same author as the code | At least 16, at least 8 of them written to look valid, by someone other than the coder, sealed before the run |

**Vocabulary**
- *Held-out / test set:* data kept away from whatever is being evaluated, so that a score on it means something.
- *Validation set:* data the system is allowed to use to make decisions. It is not the test set.
- *Leakage:* information from the test set reaching the system some other way. Even an innocent-looking file path can
  be enough.
- *Commit–reveal:* publish a fingerprint (SHA-256) of the sealed answers first, run, and only then reveal them. The
  fingerprint shows the answers were not changed after the results came in.
- *By construction:* true because of how the thing was built, not because of anything observed. Such results belong in
  a self-test, not a finding.

## Challenge

Take any check you trust, in this repository or another one, and ask: **what would it print if the thing it checks
were broken?** Then break it on purpose, in a copy, and see. If the output does not change, the check was a log line.

A harder one: in EGOE-0, prediction P5 says the verifier *will* let through at least one false fact that touches no
validation question. Why would a result where it caught every one of them be a warning sign rather than good news?
(Hint: what could the verifier have used to catch them?)
