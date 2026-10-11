# VEC-003 — implementation and execution report

**Status:** `VISIBLE_REGISTERED_MATRIX_PASS / ORIGINAL_NEGATIVE_PRESERVED / NOT_INDEPENDENTLY_VALIDATED`  
**Owner**: research branch only; no production merge, no change to frozen DPC-001 v0.2.  
**Pre-run registration** `VEC003_PREREG.md` first committed `585996f5653eabf13850a3a247a1ad2ee478df7d`, before implementation `b458f22f58eddd2a9f97905d425dcee95c2d927c` and test harness `538722a30cea8b50ca734bf3e1507627b8c5f66a`. Target parent is VEC-002-R1 at `e35cdf7`.

## Result timeline (negative first)

1. **Instrument failure, no VEC-003 fixtures executed:** workflow [38131734568](https://github.com/holland202/veritas-origin/actions/runs/38131734568), job `114447287834`, exit 1, `ModuleNotFoundError: No module named 'test_vec002'`. Isolated `python -I` test helper path omitted sibling `vec002` folder. Owner report preserved in PR #33 comment [6108037209](https://github.com/holland202/veritas-origin/pull/33#issuecomment-6108037209). This run is **INCONCLUSIVE** for parser behavior, not a passing test.
2. **Repair to harness only:** commit `a569207ac4b197debfc08c6d505698346361efb2` added the explicitly local `vec002` helper directory to test runner `sys.path`. The VEC-003 verifier code and preregistered expected outputs **did not change**.
3. **First actual VEC-003 run:** workflow [38131778353](https://github.com/holland202/veritas-origin/actions/runs/38131778353), job `114447416024`, exit **0**; printed `VERDICT PASS 22/22`, `FAIL_CASES NONE` on CPython 3.11.17, Linux x86_64 and `cryptography==46.0.4`. Counts: P00=1; D01–D08=8; D09a/b/c=3; R01–R09=9; R10 child=1. All expected result codes held; `execution_authorized=false` in every verifier call.
4. **Earlier regression controls:** workflow [38131778352](https://github.com/holland202/veritas-origin/actions/runs/38131778352), original VEC-001 suite **21/21 PASS**; workflow [38131778355](https://github.com/holland202/veritas-origin/actions/runs/38131778355), original regression **21/21 PASS**, prior VEC-002-R1 fixed-version suite **15/15 PASS**.

## Positive / negative boundary observations

- D01/D02: 64-deep envelope array was *parsed* (then rejected by application envelope schema); 65-deep returned `REFUSED/MALFORMED_JSON`.
- D03/D04: signed payload array 64-deep parsed then refused for Statement schema; 65-deep rejected by preflight. D05/D06 similarly for signed artifact schema.
- D07/D08 quoted/escaped bracket-rich strings remained accepted with valid signed evidence.
- D09a/b/c original 1,500-nesting attacks all `REFUSED/MALFORMED_JSON`.
- R01/R02 envelope 65536/65537-byte boundary accepted/refused; R03/R04 signed artifact 65536/65537-byte boundary accepted/refused.
- R05/R06 signed Statement payload 32768/32769 decoded byte boundary accepted/refused.
- R07/R08 signed array with 4097/4096 commas: complexity refusal at 4097; 4096 passed preflight but rejected by evidence schema.
- R09 6,000-digit JSON integer: `REFUSED/MALFORMED_JSON` on tested Python 3.11 build.
- R10 child 100/100 valid verifications under `RLIMIT_AS=256MiB`, `RLIMIT_CPU=8 seconds`, parent `timeout=15 seconds`: exit 0, program reported `wall_ms=18.409`, `peak_rss_kib=28040`. The measured wall time applies only to the **inner 100-call loop** (not process startup); it is not an absolute verifier SLA.

## Threat and scope caveats

- An iterative lexical quota scan is **not** full JSON grammar parsing. It intentionally enforces a strict, application-specific acceptance profile; the Python decoder validates grammar afterward. The old `RecursionError` handler remains as a second defensive boundary.
- Punctuations/quoting are counted on raw UTF-8 bytes outside strings. No claim of universal UTF-8/parser differential safety without external parser vectors.
- Host-supplied `trust_map`, context, clock and signer remain trust boundaries. The verifier does not establish artifact fact truth or study authorization, nor any replay/rollback resistance.
- **Resource isolation only demonstrated for valid repeated input** under a child process; no hard memory/CPU bound can be inferred for arbitrary adversarial inputs. Further hostile-input child runs need a prospective separate protocol.
- All tests and code were written by ChatGPT. GitHub Actions provides a separate execution substrate but **not independent authorship or external security review**. Android S25 and other Python runtimes not exercised.

**Disposition:** Retain PR #33 as draft for review; the registered visible tests passed, but production promotion and merge-to-main remain HOLD. The original VEC-002 S1 negative result remains valid for its frozen pre-repair revision.
