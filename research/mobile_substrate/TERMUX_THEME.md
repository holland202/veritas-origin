# Optional Sovereign Research Console — Termux visual theme

**Experimental, opt-in, reversible.** The banner is decorative only. It does not authenticate your device, measure thermal safety, verify a vault sync, or authorize an action.

## What installation changes

The installer writes a banner at `~/.config/sovereign-research-console/banner.sh` and appends one managed, interactive-only block to `~/.bashrc`. It first backs up your existing `.bashrc` as `~/.bashrc.before-sovereign-theme.<timestamp>.<pid>`. Existing aliases (including `sovereign-chat`) and other shell configuration stay in place.

On startup, the new managed block clears the visible terminal before showing the new header; the previous decorative header's code is left intact. Its earlier side effects still occur before the new header, if any. It does not change your current Git repository or use root.

If both `~/health_monitor.py` and `~/Sovereign-Manifold/health_monitor.py` are missing, an exact standalone `python3 health_monitor.py` call is *commented out* so Bash no longer prints the known missing-file error. No other monitor command is disabled. A commented-out monitor is **not fixed or running**.

## Termux commands — only when you choose

The branch in your existing checkout needs to be updated first. This does not touch local `.bashrc` until you explicitly issue `install`.

```bash
cd ~/veritas-origin-tsp001
git status --short
git pull --ff-only

# See the styling without changing any local configuration
python research/mobile_substrate/termux_theme.py preview

# Apply with an automatic .bashrc backup
python research/mobile_substrate/termux_theme.py install

# Reload interactively to view the startup banner
exec bash
```

To remove only the managed block (other configuration is preserved):

```bash
python ~/veritas-origin-tsp001/research/mobile_substrate/termux_theme.py uninstall
exec bash
```

Uninstall intentionally leaves all backup files and the inert banner file behind. It also leaves the commented-out missing-monitor command in place: **do not revive a missing monitor until its exact file and behavior have been independently inspected.** To restore an earlier `.bashrc` in full, inspect the timestamped backup first and restore it manually; automatic wholesale replacement could lose newer user changes.

## Test evidence

The first header installer commit was followed by GitHub Actions [38136556631](https://github.com/holland202/veritas-origin/actions/runs/38136556631), showing **6/6 isolated-home header tests PASS** and the existing **18/18 substrate probe tests PASS** on Linux Python 3.11. A further preview-only rendering change is a separate commit and requires checking the new head CI before claiming that exact source passed.

The tests ran in temporary directories, not against your device's actual `.bashrc`. Running the commands above on S25 is an owner action. A visual header is no proof of software or model security.
