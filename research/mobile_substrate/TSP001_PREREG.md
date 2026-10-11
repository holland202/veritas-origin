# TSP-001 — portable Termux/Linux substrate evidence, prospective registration

**Status: REGISTERED BEFORE IMPLEMENTATION / NOT_RUN / NOT_VALIDATED.**
**Owner request:** assimilate the useful official Termux and bounded security-spec techniques into our AI research builds.
**Date:** 2026-10-11 US Central. **Location:** independent Veritas-Origin research branch based on main `19efdc5fc7a0f2c90226a836e0cc9163e4692b3c`.
**Scope:** read-only, passive, stdlib-only capability observation and an explicit fail-closed *research readiness* decision; no OS permissions changed, no Android API invoked, no Termux add-ons installed, no network, no subprocess, no filesystem mutations. **Sovereign Veritas stays maintenance-only** (no feature PR); DPC-001 v0.2 frozen sources stay byte-identical. The Codeberg LDE project is not modified or claimed integrated.

## External source grounding — fixed heads at design time

| Primary source | Pinned Git commit | Adoptable conclusion | Boundary |
|---|---|---|---|
| [termux/termux-app](https://github.com/termux/termux-app) | `8629e632fcb95da272221be327db653fb24befe9` | Android terminal + sandbox; Android 12+ can terminate background processes under constraints | Source docs; not a device test |
| [termux/termux-packages](https://github.com/termux/termux-packages) | `538b6e77f1aec908dad15d5e80d5015dff2bc7a5` | Package ecosystem distinct from Termux app | No package install |
| [termux/termux-api](https://github.com/termux/termux-api) | `fc26ce17e3badf85d4df191af364fcf7798047f1` | Add-on API uses Android app + helper and matching signatures/permissions | A binary existing does NOT prove add-on installed or API authorized |
| [termux/termux-boot](https://github.com/termux/termux-boot) | `a8493bd6ba016bc370af34aa65fcbe065cc00ced` | Boot scripts may run after startup | No automatic boot scripts; no persistence |
| [termux/termux-tasker](https://github.com/termux/termux-tasker) | `dbf685fe2973c3490a27cbd37f31909ad5eb3bb3` | Tasker can trigger shell commands | Not a secure authorization boundary |
| [termux/termux-widget](https://github.com/termux/termux-widget) | `b3aacb8175fb2d7167ce8d1ad6817087498aa044` | Launcher shortcuts can execute scripts | Not installed/used; user invocation != verified permission |
| [termux/termux-x11](https://github.com/termux/termux-x11) | `fa3a8b430e2896a19f44c99a9cb056254615ae06` | Optional X server with Android foreground CPU / APK-signature caveats | Not a requirement for headless research |
| [TEKIMAX/speckit-security](https://github.com/TEKIMAX/speckit-security) | `48312d105dfffecbdd5c963ab707a70e7de72ea6` | Explicit security gates and threat modeling at spec stage | Third-party alpha; not installed/endorsed; adapt idea only |
| [Linux kernel seccomp/Landlock/cgroups](https://github.com/torvalds/linux) | See prior MTA-001 source map | OS facilities require platform support AND confinement installation | `Seccomp: 2` on our observer DOES NOT prove an action broker is confined |

A Git revision is not an independently archived SHA-256 of source bytes. Site popularity, repository stars and screenshot descriptions are NOT experimental validation.

## Narrow prospective design

Implement a single Python module `substrate_probe.py` with **pure** `assess_snapshot(snapshot)` using injected synthetic data and a `capture_live()` that passively reads a fixed set of OS virtual files. Do not read arbitrary disk files, home directory, location, wifi, clipboard, notifications, personal data or app credentials. No subprocess and no app API calls. Manifest categories:

- Host identification: Python platform machine, `platform.system()`, and environment-based `TERMUX_VERSION` / `PREFIX` / `ANDROID_ROOT` hints only, explicitly **UNTRUSTED_HINTS** (not a verified Android identity).
- `/proc/self/status`: `Seccomp` (0, 1, 2) and `NoNewPrivs` (0, 1), scoped **to the observing process**, not agent/broker. Unknown/malformed/missing treated `UNKNOWN`, not enforced.
- `/proc/self/mountinfo` marker for a `cgroup2` mount and bounded `/sys/fs/cgroup/cgroup.controllers` for named controllers: observable presence is **not proof of delegation or active resource limits**.
- `/sys/kernel/security/lsm` Landlock name if readable: `LSM_LISTED` is not an ABI check or confirmation of an installed effective per-process ruleset.
- Passive PATH lookup for allowed `termux-battery-status`, `termux-sensor`, `termux-job-scheduler`; `COMMAND_FOUND` is NOT add-on/plugin authorization or proof the command actually works.
- Always separate `observations`, `limitations`, and `readiness`. Readiness for any `execution`, `sensor`, `background_job` or `filesystem_confinement` intent must be **DEFER_UNVERIFIED** absent authenticated evidence of actual applied restrictions. This instrument has no attestation verifier, so it can NEVER emit ALLOW. With no requested intents return `OBSERVATION_ONLY` and still do not authorize anything.

**Limits:** each virtual source limited to 32 KiB, no raw contents emitted (only parsed controls), OS exceptions collapsed to UNKNOWN, no personal/private state copied. Machine-readable JSON, stable sorted keys, one SHA-256 digest of the manifest excluding the digest field; the digest is an **integrity fingerprint**, not a signature or independent trust proof. Provide a safe, portable CLI `python substrate_probe.py [--require ...]` with exit 0 on observation-only, exit 2 when requirements are requested but unavailable/unverified, exit 3 on invalid requests/internal instrument errors.

## Frozen self-test predictions (author-designed; not independent)

| ID | Scenario | Expected |
|---|---|---|
| P00 | Linux snapshot, `Seccomp:2`, `NoNewPrivs:1`, cgroup2 mounted, controllers set | observe current-process confinement hints; NO action authorization |
| P01 | Android/Termux environment indicators plus three command names | Android/Termux = HINT_ONLY; commands FOUND not verified APIs; readiness DEFER for sensor |
| N01 | all virtual sources unavailable | UNKNOWN, not a fabricated disabled/success status |
| N02 | malformed Seccomp or NoNewPrivs fields | UNKNOWN for malformed field |
| N03 | `Seccomp:0` | OBSERVED_NONE (doesn't prove host incapable) |
| N04 | `Seccomp:2` with `NoNewPrivs:0` | OBSERVED_FILTER_SELF; execution intent still DEFER |
| N05 | cgroup2 mount but controller file unreadable | MOUNT_OBSERVED, controller UNKNOWN; no limit claim |
| N06 | controller names present with mountinfo missing | mount UNKNOWN; no successful confinement claim |
| N07 | `landlock` in LSM list | LSM_LISTED only; requirement DEFER |
| N08 | `landlock` not in readable LSM list | NOT_LISTED, not global impossible |
| N09 | `termux-sensor` binary present | COMMAND_FOUND, sensor still DEFER |
| N10 | `termux-sensor` absent | COMMAND_NOT_FOUND, not proof Android has no sensor |
| N11 | only forged environment variables hint Android | identity HINT_ONLY, no elevation |
| N12 | requested execution with all source hints affirmative | DEFER_UNVERIFIED |
| N13 | requested background job with all command hints affirmative | DEFER_UNVERIFIED |
| N14 | no requested intents | OBSERVATION_ONLY, never ALLOW |
| N15 | unknown requested intent | INVALID_REQUIREMENT, CLI exit 3 |
| N16 | repeated identical injected snapshot | byte-identical canonical manifest & fingerprint |

Anti-vacuity: P00/P01 must produce *positive observational detections*; refuse-all/missing-readings must fail. No experimental statistic, performance portability, APK permission or device security claim from synthetic input.

## Execution rules

Commit this preregistration **before** verifier/module/test code. CI execution on x86_64 Linux validates only the module's synthetic fixtures and local passive observation. Android 17 S25/Termux execution remains `NOT_RUN` until the device itself provides captured stdout, Python/platform and exit code. Preserve early failing CI runs, and any repairs as separate evidence; don't retune preregistered predictions silently. Never print or upload environment variable values, process IDs, file paths in PATH, hardware serial, tokens or location.

## Proposed follow-on that is NOT implemented

A separately preregistered portable audit package usable by LDE, and a spec-threat-model precheck for unpinned source/model revisions and unsafe autostart features. This is a research-substrate instrument, **not** a self-installing agent, OS sandbox or operational ALLOW gate.
