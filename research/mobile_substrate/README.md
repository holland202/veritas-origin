# TSP-001 — Portable Substrate Observer

**Status:** EXPERIMENTAL / PASSIVE / NOT A SANDBOX / NOT A DEVICE AUTHORITY

This is a small, stdlib-only Python command intended for research on your Android/Termux device and on Linux. It implements the methods registered in [TSP001_PREREG.md](TSP001_PREREG.md). It **does not** require installing a Termux extension, root access or any package beyond the Python interpreter already used to run the research projects.

## What it actually does

Read only a bounded set of local virtual files: `/proc/self/status`, `/proc/self/mountinfo`, `/sys/fs/cgroup/cgroup.controllers`, `/sys/kernel/security/lsm`. Inspect the presence of three allowlisted commands with PATH lookup. Return a normalized manifest and a SHA-256 **fingerprint** of its normalized observations. A fingerprint is not a signature, authorization, certification, proof of identity or independent provenance.

**Nothing is executed on the Android side**: no sensor, battery API, camera, GPS, clipboard, Tasker, Widget, network, login, shell command, activity launch, background schedule, boot script, package install, permission change or OS security policy installation.

The manifest explicitly separates:

- Observed seccomp status **of this Python observer** vs. a proof that any future AI-action broker is sandboxed.
- `cgroup2` mount/controller names vs. applied or delegated limits.
- `landlock` listed among LSMs vs. supported ABI and an installed Landlock ruleset.
- Termux binary existence vs. a working, signed, permitted Termux:API installation.
- Local Android-like environment markers vs. an authenticated device identity.

Every requested intent returns `DEFER_UNVERIFIED` and `execution_authorized=false`. The command does **not** add to the Sovereign Veritas runtime or create an alternate `ALLOW` path.

## Try it locally in Termux — explicitly optional

The branch is experimental and unmerged. On your phone, **only if you want to run a passive inspection**, in Termux:

```sh
git clone --depth 1 --branch experiment/termux-substrate-intake-20261011 \
  https://github.com/holland202/veritas-origin.git ~/veritas-origin-tsp001
python ~/veritas-origin-tsp001/research/mobile_substrate/substrate_probe.py
```

No Android permissions are requested. The command prints only coarse, normalized results and a digest, rather than raw process/environment records. It is safe to inspect locally before deciding whether to share the manifest. It may report `UNKNOWN` where Android prohibits `/proc` or `/sys` reads; **UNKNOWN is not a failure of the device and not evidence of security**.

To ask about a contemplated operation without executing it:

```sh
python ~/veritas-origin-tsp001/research/mobile_substrate/substrate_probe.py --require sensor
echo $?
```

The requested intent intentionally gives exit code **2** (`DEFER_UNVERIFIED`), even if the command exists. Without `--require`, an observation-only report exits 0 if generated; that does not mean a secure application passed a gate.

## Integration plan for our builds

| Build | What we may adopt | Current state |
|---|---|---|
| **Veritas-Origin** | Read-only source-of-evidence manifest to accompany externally preregistered runs | **Experimental Python source + synthetic fixtures** in this branch |
| **LDE (Codeberg)** | Pin snapshot manifest beside separate ARM64/Azure evidence; prevent a missing cgroup/seccomp observation from being called sandboxed | **NOT INTEGRATED / Codeberg not written** |
| **Evidence Circuit VEC** | Optional future observation-side appendix; not a new signer/trust proof or action permit | **NOT INTEGRATED** |
| **Sovereign Veritas** | Conceptual distinction between application authorization and actual process confinement | **MAINTENANCE-ONLY / NO NEW FEATURES** |

### Future gated work, NOT implemented

- **Termux:API sensors/battery:** run only if the device owner explicitly enables the matching signed Android extension and approves an exact sensor data request. A helper command being present is not enough to authorize it.
- **Termux:Widget/Tasker:** possible *human-invoked* research collection; would need a separate immutable action descriptor, single-use authorization and safe simulated effects first.
- **Termux:Boot:** intentionally **not enabled**. Always-on background loops and wake locks can impact phone power, thermals and Android process behavior.
- **Termux:X11:** graphics option, not a prerequisite for headless inference or evidence reproducibility; optional only.
- **Third-party automated red-team, brute-force, root/ADB installers:** not adopted; popularity is not trust, and they are not required for the research.
- **Spec-driven security gates:** a later candidate can lint spec artifacts for missing source revision, unverified evidence, unauthorized external action or accidental background execution. Third-party Spec Kit extensions were not installed or treated as an enforcement mechanism.

## Executable evidence and limits

```sh
python -I research/mobile_substrate/test_tsp001.py
python -I research/mobile_substrate/substrate_probe.py
python -I research/mobile_substrate/substrate_probe.py --require execution
```

The tests use **synthetic** snapshots, not actual Android hardware. A green GitHub Actions build on Ubuntu **does not validate Termux/Android behavior**. To validate actual S25 results, preserve exact device OS/architecture and Python version, complete stdout/stderr, exit code, branch head SHA and any unobserved/UNKNOWN fields. Do not claim that an installed or hinted security feature is enforced for an agent until an independently witnessed action-boundary experiment proves it.

This project is a bounded research instrument, not a deployment, security claim or independent audit. It should not be allowed to run real actions and doesn't.
