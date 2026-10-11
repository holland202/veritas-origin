# VEC-003 — prospective parser budgets and bounded-resource evaluation

**Status: PREREGISTERED / IMPLEMENTATION NOT STARTED / NOT RUN / NOT INDEPENDENTLY VALIDATED.**
**Date:** 2026-10-11 US Central. Author: GPT-6. Parent repair VEC-002-R1 commit `e35cdf740b93b4b47d5e78f84cfaef7375d75885`. Current verifier Git blob `8169d018e164f4241f243e7d061d6a69db152a69`. Exact original failure `VEC002_ORIGINAL_FINDINGS.md`, original failures never overwritten. Frozen DPC-001 v0.2 never touched.

## Motivation and limited hypothesis

VEC-002 found three `RecursionError` crashes for bounded input; R1 catches that exception. VEC-003 asks whether an **iterative, byte-level, quote-aware preflight** can proactively enforce maximum JSON nesting and punctuation budgets before invoking Python's recursive decoder, without false rejection of legitimate JSON strings, while existing size, signature and arithmetic behavior remains unchanged.

This is an author-designed parser-hardening experiment, not a claim of arbitrary input totality, hard real-time enforcement, zero-allocation streaming parsing, or protection against a malicious `trust_map` object. Hard CPU and memory budgets require **process isolation by the host**; a pure Python function cannot guarantee them.

## Freeze of predictions and new limits

- `MAX_JSON_DEPTH = 64`: at most 64 simultaneously open arrays/objects **outside strings**. Depth 65 is rejected before `json.loads`. Scanner tracks JSON string quoting and backslash escapes iteratively in **raw byte** order. Brackets inside quoted strings and escaped quotes do not increase depth.
- `MAX_JSON_PUNCTUATION = 4096`: number of commas or colons **outside strings**; 4097 refused before `json.loads`. This bounds breadth of lists/objects, not all CPU or memory allocations. Both limits apply independently to envelope, signed Statement payload, and signed artifact.
- For new depth/breadth rejections, preserve existing public `REFUSED/MALFORMED_JSON` reason code for backwards compatibility with R1. Catch `RecursionError` is retained as last defense. **No signature, trust policy, scientific classifier, execution permission, or schema change**.
- Byte caps remain `MAX_BYTES=65536`, `MAX_PAYLOAD=32768`; all existing 21 original VEC-001 and 15 VEC-002-R1 cases must continue with original exact outcomes.
- Scanner may conservatively reject syntactically invalid JSON for exceeding budget; it never treats malformed JSON as valid. It only rejects or passes to Python decoder; it is **not** a replacement parser.

## Registered new fixture matrix

| ID | Input | Expected result |
|---|---|---|
| P00 | baseline valid signed artifact | BINDING_VERIFIED / BOUND_FINITE_SET_MATCHES |
| D01 | 64-deep JSON **envelope**, JSON array (not profile) | REFUSED / ENVELOPE_SCHEMA_INVALID |
| D02 | 65-deep JSON envelope | REFUSED / MALFORMED_JSON |
| D03 | correctly signed 64-deep JSON **payload** array | REFUSED / STATEMENT_SCHEMA_INVALID |
| D04 | correctly signed 65-deep JSON payload array | REFUSED / MALFORMED_JSON |
| D05 | correctly signed artifact of 64-deep JSON array | REFUSED / EVIDENCE_SCHEMA_INVALID |
| D06 | correctly signed artifact of 65-deep JSON array | REFUSED / MALFORMED_JSON |
| D07 | legitimate signed evidence with 100+ bracket characters **inside JSON string** | BINDING_VERIFIED |
| D08 | legitimate signed evidence with escaped quote/backslash followed by many brackets in string | BINDING_VERIFIED |
| D09 | a 1,500-level raw envelope, signed payload and signed artifact (three separate calls) | 3 × REFUSED / MALFORMED_JSON |
| R01 | original signed envelope padded with JSON whitespace to **exactly 65,536 bytes** | BINDING_VERIFIED |
| R02 | same at **65,537 bytes** | REFUSED / INPUT_TOO_LARGE |
| R03 | signed evidence artifact padded with JSON whitespace to **65,536 bytes** | BINDING_VERIFIED |
| R04 | same at **65,537 bytes** | REFUSED / INPUT_TOO_LARGE |
| R05 | signed Statement payload padded with whitespace to **32,768 decoded bytes** | BINDING_VERIFIED |
| R06 | signed Statement payload padded to **32,769 decoded bytes** | REFUSED / PAYLOAD_TOO_LARGE |
| R07 | correctly signed artifact with 4,097 commas outside strings (flat array) | REFUSED / MALFORMED_JSON |
| R08 | correctly signed artifact with exactly 4,096 commas outside strings (flat array) | REFUSED / EVIDENCE_SCHEMA_INVALID (complexity boundary accepted; schema rejects) |
| R09 | correctly signed evidence with a literal 6,000-digit JSON integer contrast | REFUSED / MALFORMED_JSON (CPython 3.11 integer conversion cap; different Python versions outside scope) |
| R10 | 100 in-process consecutive calls on valid signed fixture | all BINDING_VERIFIED, no unhandled exceptions |

Each fixture checks `execution_authorized is False`. All results must preserve reason codes; unhandled exceptions FAIL. If any construction cannot meet size and signature requirements, declare the specific case INCONCLUSIVE rather than silently adjust its expected outcome. P00 prevents vacuous refusal.

## Resource-isolation control

Run R10 in a **separate child Python process** on Linux x86_64/CPython 3.11, with `resource.RLIMIT_AS = 256 MiB`, `resource.RLIMIT_CPU = 8s`, and a **15-second parent `subprocess.run(..., timeout=15)` watchdog**. Child exit nonzero or timeout is a FAIL (or environment INCONCLUSIVE if the platform cannot supply these limits), not a PASS. This demonstrates completion under these **specific** constraints, not a proof that arbitrary untrusted work is always bounded. Code load and crypto library allocations are inside this limit; measure and log child exit and wall time. GitHub job global timeout remains 10 minutes.

## Controls and decision procedure

- Before the first new run, commit preregistration, code and immutable tests. Preserve target baseline blob and order of commits in PR.
- The 21 original VEC-001 fixtures and 15 VEC-002-R1 repair fixtures are required separate controls. The *historical* VEC-002 predictive runner that expected crashes remains untouched; its post-fix mismatch is not a security regression.
- If any new case mismatches or crashes: overall FAIL, report ID, expected/actual, exit status; retain negative outputs. No retrospective retuning; subsequent improvements require a dated amendment.
- No production merge from passing author-derived cases. Independent reviewer and cross-parser/generator tests remain necessary.
