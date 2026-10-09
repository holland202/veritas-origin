# 001: NOT_RUN is not FAIL, and neither is PASS

*Taught with a real event: the Sovereign Veritas v0.2.0 release, 2026-10-09.*

## Understand

A test can end in three different ways, and they mean different things:

| Outcome | What happened | What it tells you about the software |
|---|---|---|
| **PASS** | The test ran and the software did what was expected | A little evidence it works, in that situation |
| **FAIL** | The test ran and the software did something wrong | Evidence of a problem |
| **NOT_RUN** | The test never got to the software | **Nothing** |

The tempting mistake is to squash NOT_RUN into one of the other two:
- Calling it **PASS** hides a gap. You claim a check you never did.
- Calling it **FAIL** invents a bug. You blame the software for something that never touched it.

Keeping three outcomes separate is how a record stays honest.

## Build: what actually happened

Sovereign Veritas runs its tests on six kinds of computer, called "legs" (Linux, macOS, Windows, ARM, and two IBM-style chips emulated with a tool called QEMU: s390x and ppc64le).

1. Before the release, the two QEMU legs had to download a helper image from Docker Hub. Docker Hub refused ("toomanyrequests", HTTP 429) or timed out. **The tests never started.** Result: NOT_RUN, not FAIL.
2. The release tag was created anyway. That was recorded as a **deviation**: the agreed rule was "all tests green on the exact version *before* tagging".
3. Later the same day the two legs were rerun on the exact released commit (`ecd4de9`). This time they ran. The log proves they ran on the right chip, because it prints the platform:
   ```
   Linux-6.17.0-1022-azure-s390x-with-glibc2.39 s390x big 3.12.3
   Linux-6.17.0-1022-azure-ppc64le-with-glibc2.39 ppc64le little 3.12.3
   ```
   The cross-leg comparison then printed `VERDICT  P2+P3 HOLD on 6 legs`.
4. The record kept all of it: NOT_RUN at tag time, the deviation, and the later PASS. The later PASS did **not** erase the deviation.

Where to look: `coordination/p001/CLOSEOUT_RECORD.md` on the `project/p001-hardening` branch of `holland202/sovereign-veritas`, and its xplat workflow run `37990718927` (attempts 1–3).

**Vocabulary**
- *CI (continuous integration):* GitHub runs the tests automatically on every change.
- *Exact SHA:* the commit's unique fingerprint. "Passed on `ecd4de9`" is a claim about that exact code, not about "roughly the same code".
- *Anti-vacuity:* proving a check *can* fail. The comparison job includes a self-test line, `selftest  pinned digest missing on both legs: P2 failure reported`. A check that can never fail is a log line, not a check.

## Challenge

1. The same two legs also passed on PR #69, which changed only two Markdown files on top of `ecd4de9`. Is that the same evidence as passing on `ecd4de9` itself? Write one sentence on why it is or isn't. (Hint: what would have to be true for the answer to change?)
2. Find a test in any of your repositories whose result you have been treating as PASS when it was really NOT_RUN: skipped, cached, or never collected. `pytest -rs` lists skips.
3. Try to break this lesson: can you think of an outcome that is none of the three? (Real answers exist, for example *flaky*: it passes and fails on the same code. How should that be recorded?)

---
*Not evidence. Written by Claude (Opus 5.5) at Chad Holland's direction, 2026-10-09; Chad has not reviewed it line by line.*
