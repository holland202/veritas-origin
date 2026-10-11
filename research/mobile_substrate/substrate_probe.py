#!/usr/bin/env python3
"""TSP-001: passive Termux/Linux substrate observations, NOT permissions.

Only captures allowlisted proc/sys virtual files and command *presence*.
The reported current-process seccomp status is NOT an action-broker proof.
No network, subprocess, sensors, app API invocation or filesystem writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

SCHEMA = "tsp-001"
MAX_CAPTURE_BYTES = 32 * 1024
COMMAND_NAMES = ("termux-battery-status", "termux-job-scheduler", "termux-sensor")
INTENTS = frozenset(("execution", "sensor", "background_job", "filesystem_confinement"))
VIRTUAL_SOURCES = {
    "proc_status": "/proc/self/status",
    "mountinfo": "/proc/self/mountinfo",
    "controllers": "/sys/fs/cgroup/cgroup.controllers",
    "lsm": "/sys/kernel/security/lsm",
}


@dataclass(frozen=True)
class Snapshot:
    """Injected test data or a bounded passive sample of THIS process."""
    os_name: str
    architecture: str
    termux_hint: bool
    android_hint: bool
    proc_status: str | None
    mountinfo: str | None
    controllers: str | None
    lsm: str | None
    commands: Mapping[str, bool | None]


def _read_virtual(path: str) -> str | None:
    # Paths supplied here are trusted constants, not untrusted caller input.
    try:
        with open(path, "rb") as handle:
            data = handle.read(MAX_CAPTURE_BYTES + 1)
        if len(data) > MAX_CAPTURE_BYTES:
            return None
        return data.decode("utf-8", "strict")
    except (OSError, UnicodeError):
        return None


def capture_live() -> Snapshot:
    """No operations besides local virtual-file reads and passive PATH lookup."""
    sources = {name: _read_virtual(path) for name, path in VIRTUAL_SOURCES.items()}
    seen = {}
    for name in COMMAND_NAMES:
        try:
            seen[name] = shutil.which(name) is not None
        except (OSError, ValueError):
            seen[name] = None
    prefix = os.environ.get("PREFIX", "")
    return Snapshot(
        os_name=platform.system(),
        architecture=platform.machine(),
        # Environment values are untrusted hints; never published verbatim.
        termux_hint=bool(os.environ.get("TERMUX_VERSION")) or
                    prefix.startswith("/data/data/com.termux/files/usr"),
        android_hint=bool(os.environ.get("ANDROID_ROOT")),
        proc_status=sources["proc_status"],
        mountinfo=sources["mountinfo"],
        controllers=sources["controllers"],
        lsm=sources["lsm"],
        commands=seen,
    )


def _status_value(text: str | None, key: str, allowed: frozenset[int]) -> int | None:
    if text is None:
        return None
    found = []
    for line in text.splitlines():
        lhs, sep, rhs = line.partition(":")
        if sep and lhs.strip() == key:
            found.append(rhs.strip())
    if len(found) != 1 or not re.fullmatch(r"[0-9]+", found[0]):
        return None
    value = int(found[0])
    return value if value in allowed else None


def _cgroup_mount(text: str | None) -> str:
    if text is None:
        return "UNKNOWN"
    # Match the kernel's " - fstype source options" mountinfo separator.
    return "MOUNT_OBSERVED" if any(
        " - cgroup2 " in line for line in text.splitlines()
    ) else "MOUNT_NOT_OBSERVED"


def _controllers(text: str | None) -> dict:
    if text is None or len(text) > MAX_CAPTURE_BYTES:
        return {"status": "UNKNOWN", "cpu": None, "memory": None}
    tokens = text.split()
    if not all(re.fullmatch(r"[a-z][a-z0-9_]*", item) for item in tokens):
        return {"status": "UNKNOWN", "cpu": None, "memory": None}
    names = set(tokens)
    return {
        "status": "CONTROLLERS_LISTED" if tokens else "NONE_LISTED",
        "cpu": "cpu" in names,
        "memory": "memory" in names,
    }


def _landlock(text: str | None) -> str:
    if text is None or len(text) > MAX_CAPTURE_BYTES:
        return "UNKNOWN"
    labels = [item.strip() for item in text.strip().split(",")]
    if not all(re.fullmatch(r"[a-z][a-z0-9_-]*", v) for v in labels if v):
        return "UNKNOWN"
    return "LSM_LISTED" if "landlock" in labels else "NOT_LISTED"


def assess_snapshot(snapshot: Snapshot, requirements=()) -> dict:
    """Interpret observables; never elevate observations to action authority."""
    if not isinstance(snapshot, Snapshot):
        raise ValueError("INVALID_SNAPSHOT")
    if isinstance(requirements, str):
        raise ValueError("INVALID_REQUIREMENT")
    try:
        required = tuple(requirements)
    except TypeError as exc:
        raise ValueError("INVALID_REQUIREMENT") from exc
    if any(type(name) is not str or name not in INTENTS for name in required):
        raise ValueError("INVALID_REQUIREMENT")
    if len(required) > len(INTENTS) or len(required) != len(set(required)):
        raise ValueError("INVALID_REQUIREMENT")
    required = tuple(sorted(required))

    seccomp = _status_value(snapshot.proc_status, "Seccomp", frozenset((0, 1, 2)))
    nnp = _status_value(snapshot.proc_status, "NoNewPrivs", frozenset((0, 1)))
    seccomp_label = {
        0: "OBSERVED_NONE",
        1: "OBSERVED_STRICT_SELF",
        2: "OBSERVED_FILTER_SELF",
    }.get(seccomp, "UNKNOWN")
    nnp_label = {0: "OBSERVED_NO_SELF", 1: "OBSERVED_YES_SELF"}.get(nnp, "UNKNOWN")
    if snapshot.termux_hint or snapshot.android_hint:
        host_hint = "ANDROID_TERMUX_HINT" if snapshot.termux_hint else "ANDROID_HINT"
    else:
        host_hint = "LINUX_REPORTED" if snapshot.os_name == "Linux" else "OTHER_REPORTED"

    commands = {}
    for name in COMMAND_NAMES:
        seen = snapshot.commands.get(name)
        commands[name] = (
            "COMMAND_FOUND" if seen is True
            else "COMMAND_NOT_FOUND" if seen is False
            else "UNKNOWN"
        )
    payload = {
        "schema": SCHEMA,
        "scope": "PASSIVE_SELF_OBSERVATION",
        "host": {
            "reported_os": snapshot.os_name,
            "architecture": snapshot.architecture,
            "identity": host_hint,
            "identity_confidence": "UNTRUSTED_HINTS",
        },
        "observations": {
            "seccomp_self": seccomp_label,
            "no_new_privs_self": nnp_label,
            "cgroup_v2_mount": _cgroup_mount(snapshot.mountinfo),
            "cgroup_controllers": _controllers(snapshot.controllers),
            "landlock_lsm": _landlock(snapshot.lsm),
            "termux_commands": commands,
        },
        "readiness": {
            "requested_intents": list(required),
            "status": "DEFER_UNVERIFIED" if required else "OBSERVATION_ONLY",
            "execution_authorized": False,
            "evidence_status": "NO_ATTESTED_EFFECTIVE_ENFORCEMENT",
        },
        "limitations": [
            "Local status cannot establish independent source authenticity",
            "Seccomp observation covers the probe process, not an action broker",
            "cgroup mount/controllers do not prove delegated limits",
            "Landlock LSM listing does not prove a ruleset was applied",
            "Termux executable lookup does not validate plugin permissions",
            "Android environment markers are untrusted hints",
            "No operational ALLOW or external action is supported",
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    payload["fingerprint_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    # Digest is an integrity fingerprint, not an attestation or signature.
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Passive Termux/Linux capability observer")
    parser.add_argument(
        "--require", action="append", default=[], metavar="INTENT",
        help="intent to assess, not to execute: execution, sensor, background_job, filesystem_confinement",
    )
    args = parser.parse_args(argv)
    try:
        report = assess_snapshot(capture_live(), args.require)
    except (ValueError, TypeError, OSError):
        print(json.dumps({"schema": SCHEMA, "error": "INVALID_REQUIREMENT_OR_INSTRUMENT"}))
        return 3
    print(json.dumps(report, sort_keys=True, indent=2))
    return 2 if args.require else 0


if __name__ == "__main__":
    sys.exit(main())
