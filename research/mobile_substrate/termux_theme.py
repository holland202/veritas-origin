#!/usr/bin/env python3
"""Optional, reversible neon Termux header. Not part of TSP-001's verifier.

Commands: preview, install, uninstall. No network, external commands, Android
API calls, root, background process or repository modification. INSTALL writes
a new banner file and a marked block to the user's .bashrc after making a
dated backup; UNINSTALL only removes the marked block.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import sys
import time
from pathlib import Path

START = "# >>> SOVEREIGN-RESEARCH-CONSOLE (managed; backup before change) >>>"
END = "# <<< SOVEREIGN-RESEARCH-CONSOLE <<<"
MISSING_MONITOR_COMMENT = "# [SOVEREIGN-THEME] disabled missing health_monitor.py: "
MONITOR_LINE = re.compile(r"^(\s*)python3\s+health_monitor\.py(\s*)$", re.MULTILINE)
BANNER_RELATIVE = Path(".config/sovereign-research-console/banner.sh")
BANNER = r"""#!/data/data/com.termux/files/usr/bin/bash
# Decorative terminal art only; NOT runtime attestation or authorization.
[ -t 1 ] || return 0
printf '%b\n' '\033[1;35m   ╔════════════════════════════════════════════════════════════╗'
printf '%b\n' '\033[1;35m   ║\033[1;36m       S O V E R E I G N   //   V E R I T A S          \033[1;35m║'
printf '%b\n' '\033[1;35m   ╠════════════════════════════════════════════════════════════╣'
printf '%b\n' '\033[1;35m   ║\033[0;36m  ◈   EDGE RESEARCH NODE     S25 ULTRA / ARM64            \033[1;35m║'
printf '%b\n' '\033[1;35m   ║\033[0;32m  ◈   EVIDENCE FIRST         FAIL-CLOSED IS THE GOAL       \033[1;35m║'
printf '%b\n' '\033[1;35m   ║\033[0;37m  ◇   PROJECTS: SV / ORIGIN / LDE      EXPERIMENTAL     \033[1;35m║'
printf '%b\n' '\033[1;35m   ╠════════════════════════════════════════════════════════════╣'
printf '%b\n' '\033[1;35m   ║\033[1;33m  NOT AN ATTESTATION  •  NO ACTION AUTHORIZED BY BANNER   \033[1;35m║'
printf '%b\n' '\033[1;35m   ╚════════════════════════════════════════════════════════════╝\033[0m'
printf '%b' '\033[0;90m   '
date '+%Y-%m-%d  %H:%M:%S  %Z' 2>/dev/null || printf '\n'
printf '%b\n' '\033[0m'
"""
MANAGED = f"""{START}
# Interactive shell only. Clear the old decorative header from this screen,
# but do not delete earlier code, shell history, aliases or audit files.
case $- in
  *i*)
    if [ -t 1 ] && [ -r "$HOME/{BANNER_RELATIVE.as_posix()}" ]; then
      printf '\\033[2J\\033[H'
      . "$HOME/{BANNER_RELATIVE.as_posix()}"
    fi
    ;;
esac
{END}
"""


def unmark(text: str) -> str:
    starts, ends = text.count(START), text.count(END)
    if (starts, ends) == (0, 0):
        return text
    if (starts, ends) != (1, 1):
        raise ValueError("incomplete or duplicated managed markers in .bashrc")
    lo, hi = text.index(START), text.index(END) + len(END)
    if hi <= lo:
        raise ValueError("reversed managed markers")
    if hi < len(text) and text[hi:hi + 1] == "\n":
        hi += 1
    return text[:lo].rstrip("\n") + "\n" + text[hi:].lstrip("\n")


def ensure_regular_or_missing(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"refusing to write non-regular path: {path}")


def install(home: Path) -> str:
    rc = home / ".bashrc"
    banner = home / BANNER_RELATIVE
    ensure_regular_or_missing(rc)
    ensure_regular_or_missing(banner)
    if banner.parent.is_symlink():
        raise ValueError("refusing symlink banner directory")

    original = rc.read_text(encoding="utf-8") if rc.exists() else ""
    # Idempotency; allow rerunning after an already installed version.
    if original.count(START) == 1 and original.count(END) == 1:
        return "Already installed. No changes made."

    updated = unmark(original)
    # Only disable this exact startup call if BOTH plausible targets are absent.
    # Never touch other health/monitoring commands or shell aliases.
    if (not (home / "health_monitor.py").is_file()
            and not (home / "Sovereign-Manifold" / "health_monitor.py").is_file()):
        updated = MONITOR_LINE.sub(
            lambda m: m.group(1) + MISSING_MONITOR_COMMENT + "python3 health_monitor.py" + m.group(2),
            updated,
        )
    updated = updated.rstrip("\n") + "\n\n" + MANAGED

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = home / f".bashrc.before-sovereign-theme.{stamp}.{os.getpid()}"
    if rc.exists():
        shutil.copy2(rc, backup, follow_symlinks=False)
        os.chmod(backup, stat.S_IRUSR | stat.S_IWUSR)
    else:
        backup.write_text("", encoding="utf-8")
        os.chmod(backup, stat.S_IRUSR | stat.S_IWUSR)
    banner.parent.mkdir(parents=True, exist_ok=True)
    banner.write_text(BANNER, encoding="utf-8")
    os.chmod(banner, stat.S_IRUSR | stat.S_IWUSR)
    # Atomic replace so a crash cannot leave a partially truncated .bashrc.
    pending = home / f".bashrc.sovereign-pending.{os.getpid()}"
    try:
        pending.write_text(updated, encoding="utf-8")
        os.chmod(pending, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(pending, rc)
    finally:
        pending.unlink(missing_ok=True)
    return f"Installed. Original backup: {backup}"


def uninstall(home: Path) -> str:
    rc = home / ".bashrc"
    ensure_regular_or_missing(rc)
    if not rc.exists():
        return "No .bashrc found."
    original = rc.read_text(encoding="utf-8")
    revised = unmark(original)
    if revised == original:
        return "No managed banner block found."
    backup = home / f".bashrc.before-theme-uninstall.{time.strftime('%Y%m%d-%H%M%S')}.{os.getpid()}"
    shutil.copy2(rc, backup)
    os.chmod(backup, stat.S_IRUSR | stat.S_IWUSR)
    pending = home / f".bashrc.sovereign-pending.{os.getpid()}"
    try:
        pending.write_text(revised, encoding="utf-8")
        os.chmod(pending, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(pending, rc)
    finally:
        pending.unlink(missing_ok=True)
    return f"Removed managed banner. Current .bashrc backed up to {backup}. Original other edits retained."


def main():
    parser = argparse.ArgumentParser(description="Optional neon Termux banner; backed up and reversible")
    parser.add_argument("action", choices=("preview", "install", "uninstall"))
    args = parser.parse_args()
    try:
        if args.action == "preview":
            print("\x1b[1;35m   ╔════════════════════════════════════════════════════════════╗")
            print("\x1b[1;36m         S O V E R E I G N   //   V E R I T A S")
            print("\x1b[0;36m       ◈ EDGE RESEARCH NODE  /  S25 ULTRA  /  ARM64")
            print("\x1b[0;32m       ◈ EVIDENCE FIRST / FAIL-CLOSED IS THE GOAL")
            print("\x1b[1;33m       NOT AN ATTESTATION OR EXECUTION PERMISSION")
            print("\x1b[1;35m   ╚════════════════════════════════════════════════════════════╝\x1b[0m")
            print("PREVIEW ONLY: no files changed. This is decorative, not an attestation.")
        elif args.action == "install":
            print(install(Path.home()))
        else:
            print(uninstall(Path.home()))
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"THEME_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
