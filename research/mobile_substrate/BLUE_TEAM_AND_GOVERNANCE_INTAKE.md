# Blue-team and external-tool research intake — 2026-10-11

**Status:** `SOURCES_INSPECTED / METHODS_ONLY / NO_EXTERNAL_TOOL_EXECUTED / NO_INDEPENDENT_VALIDATION`. This is a method review, not a vulnerability assessment of any upstream project.

The user's screenshots show blue-team GitHub repositories and an older list of Termux offensive/defensive tools. The correct response is to import **bounded defensive methods**, not download and execute every listed script.

## Primary source review

| Public repository | Pinned public commit at review | Appropriate research use | Exclusions and qualifications |
|---|---|---|---|
| [A-poc/BlueTeam-Tools](https://github.com/A-poc/BlueTeam-Tools/tree/1bca7fd57c4a0a72f4aeb3fc1ea93ddfa63f1e7c) | `1bca7fd57c4a0a72f4aeb3fc1ea93ddfa63f1e7c` | Defensive tool categorization: evidence acquisition, incident response, logs, threat hunting and hardening; choose one category-specific experiment at a time | A curated list is not a peer-reviewed efficacy comparison; original test suites and licenses must be checked per tool |
| [Purp1eW0lf/Blue-Team-Notes](https://github.com/Purp1eW0lf/Blue-Team-Notes/tree/abfcebd04e34ca91a5d8a8a7ea8f67d72ef43038) | `abfcebd04e34ca91a5d8a8a7ea8f67d72ef43038` | Document observed host state, collect normalized process/log evidence, record exact commands and failure outcomes | Notes and shell examples are not substitutes for on-host authorization or complete forensic chain of custody |
| [fabacab/awesome-cybersecurity-blueteam](https://github.com/fabacab/awesome-cybersecurity-blueteam/tree/d2231996bf67d4b5f86f09825a128b951324f915) | `d2231996bf67d4b5f86f09825a128b951324f915` | Build an evidence lifecycle: collection, parsing, event correlation, detection, triage, preservation | List is broad and may include licensed, intrusive or unmaintained software. Do not automatically install |
| [ION28/BLUESPAWN](https://github.com/ION28/BLUESPAWN/tree/984cc9af389c965e1f30181252c5a589f79bfc1c) | `984cc9af389c965e1f30181252c5a589f79bfc1c` | Separate host-monitor observations from remediation authority, and enumerate expected detection modes | Windows-oriented; do not claim Android/Termux compatibility or copy in-process remediation practices |
| [cisagov/RedEye](https://github.com/cisagov/RedEye/tree/417c69dc8fabc09b7d818c02e90e7fa494e5e53f) | `417c69dc8fabc09b7d818c02e90e7fa494e5e53f` | Distinguish event chronology, investigative evidence, and analyst conclusions | Repo is archived and oriented to interpreting adversary emulation data; not a current Android security agent |
| [may215/awesome-termux-hacking](https://github.com/may215/awesome-termux-hacking) | Screenshot-led; no full source audit here | Threat taxonomy only: parser testing, forensic analysis, static analysis, sandboxing, provenance | Many dead/stale references and offensive tools; do not run bulk installer, password attacks, keyloggers, RATs or DoS |
| [mishakorzik/AllHackingTools](https://github.com/mishakorzik/AllHackingTools/tree/def693c66c49519225b3010c72a674cc24f4487c) | `def693c66c49519225b3010c72a674cc24f4487c` | Negative example for unattended installers and trust-boundary review; **never an umbrella dependency** | `Install.sh` installs Python 2 and packages; `src/InstallMenu.py` invokes shell commands; `fix.sh` runs `chmod +x *` and copies arbitrary Tool files into Termux's executable PATH; uninstall script deletes styles and fetches other repositories. Main scripts and docs show legacy assumptions and broad state changes |

## Machine-checkable transfer requirements (PROPOSED / NOT IMPLEMENTED)

1. **Inventory requirement:** each AI agent, external service, repository, API connector, host process or OS bridge must have a stable ID, pinned revision when applicable, accountable owner, trust tier and allowed effects.
2. **Data boundary:** explicit input sensitivity labels, egress destinations, data retention and whether evidence comes from local observations, external logs, or owner-reported statuses.
3. **Policy test:** replace aspirational text like “keep data safe” with concrete rules such as “untrusted agent can never invoke `termux-sensor` or send raw process telemetry without an owner-authorized session descriptor.” Each rule needs one valid control and at least one negative case.
4. **Response evidence:** record time-local source revision, command, exit code, bounded redacted stdout/stderr, witness (if applicable), confidence and missing provenance. A log entry is not a cryptographic truth certificate.
5. **Authority split:** monitoring, incident investigation, scientific interpretation and external side-effect authority are separate. No monitoring observation can implicitly become an `ALLOW`.
6. **Supply-chain posture:** third-party scripts are treated as code requiring review. No automatic `curl | sh`, unpinned clone+execute, background service, password-attack stack, or network tunnel on the S25.

## Social-post governance idea — conditional transfer

The provided Martin Guerin post argues for an inventory of AI usage, accountable ownership and testable rules before deploying runtime controls. This is useful as a **design hypothesis**, not quantified research: its survey percentages were not traced to an original survey here, so their validity remains `ACCESS_UNVERIFIED` and they should not appear as established statistics.

For Sovereign Veritas, inventory governance should sit **upstream** of the maintenance-only runtime. For Veritas-Origin, the inventory links each scientific/evidence claim to a source and rule. For LDE, the inventory distinguishes agent candidate/hidden judge and recorded substrate. None of this grants independent data truth or command execution authority.

## Scope and disposition

Current implementation in this branch is **only** TSP-001 passive observation and an optional, separate terminal theme. GitHub CI results are development evidence, not independent authoring. No third-party blue-team tool was installed, no remote target was scanned, and no external network tunnel or persistent device agent was started. A future `GOV-001` inventory preflight needs its own preregistration and test matrix before implementation; keep this record separate from frozen DPC-001 files.
