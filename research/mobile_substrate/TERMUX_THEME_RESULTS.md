# TSP-001 adjunct — terminal theme and defensive-tool intake results

**Status:** `OPTIONAL_THEME_SELFTEST_PASS / NO_S25_INSTALL_REPORTED / PASSIVE_PROBE_UNCHANGED / EXTERNAL_TOOL_INTAKE_ONLY`.

## First evidence

- Theme implementation introduced at `9cea5dde2706f83dead8c3b0538824572937c6c2`.
- Six isolated-home theme tests introduced at `b478f3688bdd586694109dde9dba434b2f3409d0`.
- GitHub Actions [38136556631](https://github.com/holland202/veritas-origin/actions/runs/38136556631), success, ran **6 theme tests**, **18 substrate tests**, live Linux observation-only and requested-execution exit-code-2 refusal check. All passed.
- `termux_theme.py preview` rendering improved in later commit `bec511618b26fbe16a77613766f9be9ace9cd3ae`.
- Final head `4a5705453fe4a2cab1ed495bc05ec4f98a35a09c` retested through GitHub Actions [38136810880](https://github.com/holland202/veritas-origin/actions/runs/38136810880) job `114462251690`, **SUCCESS**. Execution on Linux/Python 3.11 does not establish Android-specific UI or Termux shell startup correctness.

## Historical device evidence already supplied by owner in chat

- Samsung Android/Termux `aarch64`, Python `3.14.6` on clone HEAD `3719eb367f009ee64e1432efb988359c03256b0b`.
- Read-only observation: seccomp self filter observed, `NoNewPrivs:0`, cgroup2 mount observed, controller and Landlock status UNKNOWN, Termux helper names found. Manifest fingerprint `fe83541c5c162414acae4e6c18cf761b9fab5b30f6a7e918ad4628db5ff7d101`.
- Owner invoked `--require execution`; output was `DEFER_UNVERIFIED`, `execution_authorized:false`, and **reported shell exit 2**. Requested-intent fingerprint `cd7db0c4c7937961798779affea27cd31adbb4e4f32b06509bf49e4e90e85b5f`.
- This is an **owner-supplied output**, not separately captured signed evidence or independent replication. Full device stdout/stderr and runtime hash manifest are not sealed here. These observations never prove an AI broker is confined or that Termux API commands are authorized.

## Installer design boundaries

Only if owner explicitly issues install on device: backup `.bashrc`; append uniquely marked interactive banner; optionally comment one exact missing `python3 health_monitor.py` startup call; preserve `sovereign-chat` alias. No source-level fix for the missing monitor, no background processes, no network. Six selftests cover backup preservation, no overwrite of inconsistent markers, symlink refusal, idempotency, optional exact-line disablement and uninstall. Full Android Bash presentation remains NOT_RUN until owner tests it.

## Additional source-review evidence

`BLUE_TEAM_AND_GOVERNANCE_INTAKE.md` records pinned public source revisions and limits for blue-team lists, defensive tools, and `mishakorzik/AllHackingTools`. In particular the latter's `Install.sh` installs legacy Python 2 and packages, `src/InstallMenu.py` invokes shell installers, `fix.sh` copies wildcards into the Termux executable directory, and the uninstall script deletes customizations. **No installation or reuse of its commands**. This is a supply-chain negative-design example, not an exploit reproduction or audit of every distributed package.

No frozen DPC-001 files, Codeberg LDE sources, or maintenance-only Sovereign Veritas files modified. PR #36 remains draft/unmerged pending reviewer scrutiny.
