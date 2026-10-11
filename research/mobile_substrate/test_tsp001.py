"""TSP-001 preregistered behavioral probes (17 cases), no device permissions.

All snapshots are synthetic and do not prove the S25 Android runtime status.
"""
import dataclasses
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from substrate_probe import COMMAND_NAMES, Snapshot, assess_snapshot


def linux():
    return Snapshot(
        os_name="Linux", architecture="x86_64",
        termux_hint=False, android_hint=False,
        proc_status="Name:\tpython\nNoNewPrivs:\t1\nSeccomp:\t2\n",
        mountinfo="36 26 0:32 / /sys/fs/cgroup rw - cgroup2 cgroup rw\n",
        controllers="cpu memory io cpuset\n",
        lsm="capability,landlock,selinux\n",
        commands={name: False for name in COMMAND_NAMES},
    )


def termux():
    return dataclasses.replace(
        linux(), architecture="aarch64", termux_hint=True, android_hint=True,
        commands={name: True for name in COMMAND_NAMES},
    )


class RegisteredTSP001(unittest.TestCase):
    def check_no_action(self, result, expected):
        self.assertEqual(result["readiness"]["status"], expected)
        self.assertIs(result["readiness"]["execution_authorized"], False)
        self.assertEqual(result["scope"], "PASSIVE_SELF_OBSERVATION")

    def test_P00_linux_controls_observed_not_proven(self):
        r = assess_snapshot(linux())
        self.assertEqual(r["host"]["identity"], "LINUX_REPORTED")
        o = r["observations"]
        self.assertEqual(o["seccomp_self"], "OBSERVED_FILTER_SELF")
        self.assertEqual(o["no_new_privs_self"], "OBSERVED_YES_SELF")
        self.assertEqual(o["cgroup_v2_mount"], "MOUNT_OBSERVED")
        self.assertEqual(o["cgroup_controllers"]["status"], "CONTROLLERS_LISTED")
        self.assertEqual(o["landlock_lsm"], "LSM_LISTED")
        self.check_no_action(r, "OBSERVATION_ONLY")

    def test_P01_termux_hints_and_binary_not_permission(self):
        r = assess_snapshot(termux(), ("sensor",))
        self.assertEqual(r["host"]["identity"], "ANDROID_TERMUX_HINT")
        self.assertEqual(r["host"]["identity_confidence"], "UNTRUSTED_HINTS")
        self.assertEqual(r["observations"]["termux_commands"]["termux-sensor"], "COMMAND_FOUND")
        self.check_no_action(r, "DEFER_UNVERIFIED")

    def test_N01_missing_is_unknown_not_disabled(self):
        x = dataclasses.replace(
            linux(), proc_status=None, mountinfo=None, controllers=None, lsm=None,
            commands={name: None for name in COMMAND_NAMES},
        )
        o = assess_snapshot(x)["observations"]
        self.assertEqual(o["seccomp_self"], "UNKNOWN")
        self.assertEqual(o["no_new_privs_self"], "UNKNOWN")
        self.assertEqual(o["cgroup_v2_mount"], "UNKNOWN")
        self.assertEqual(o["landlock_lsm"], "UNKNOWN")
        self.assertEqual(o["termux_commands"]["termux-sensor"], "UNKNOWN")

    def test_N02_malformed_proc_fields_unknown(self):
        x = dataclasses.replace(linux(), proc_status="Seccomp: FAIL\nNoNewPrivs:3\n")
        o = assess_snapshot(x)["observations"]
        self.assertEqual(o["seccomp_self"], "UNKNOWN")
        self.assertEqual(o["no_new_privs_self"], "UNKNOWN")

    def test_N03_seccomp_zero_not_no_capability(self):
        x = dataclasses.replace(linux(), proc_status="Seccomp:0\nNoNewPrivs:0\n")
        o = assess_snapshot(x)["observations"]
        self.assertEqual(o["seccomp_self"], "OBSERVED_NONE")
        self.assertEqual(o["no_new_privs_self"], "OBSERVED_NO_SELF")

    def test_N04_filtered_self_but_request_deferred(self):
        x = dataclasses.replace(linux(), proc_status="Seccomp:2\nNoNewPrivs:0\n")
        r = assess_snapshot(x, ("execution",))
        self.assertEqual(r["observations"]["seccomp_self"], "OBSERVED_FILTER_SELF")
        self.check_no_action(r, "DEFER_UNVERIFIED")

    def test_N05_cgroup_mount_controllers_unavailable(self):
        o = assess_snapshot(dataclasses.replace(linux(), controllers=None))["observations"]
        self.assertEqual(o["cgroup_v2_mount"], "MOUNT_OBSERVED")
        self.assertEqual(o["cgroup_controllers"]["status"], "UNKNOWN")

    def test_N06_cgroup_controllers_no_mountinfo(self):
        o = assess_snapshot(dataclasses.replace(linux(), mountinfo=None))["observations"]
        self.assertEqual(o["cgroup_v2_mount"], "UNKNOWN")
        self.assertIs(o["cgroup_controllers"]["memory"], True)

    def test_N07_landlock_listed_but_not_applied(self):
        r = assess_snapshot(linux(), ("filesystem_confinement",))
        self.assertEqual(r["observations"]["landlock_lsm"], "LSM_LISTED")
        self.check_no_action(r, "DEFER_UNVERIFIED")

    def test_N08_landlock_not_listed_not_global_failure(self):
        x = dataclasses.replace(linux(), lsm="capability,selinux\n")
        self.assertEqual(assess_snapshot(x)["observations"]["landlock_lsm"], "NOT_LISTED")

    def test_N09_binary_present_api_still_unverified(self):
        r = assess_snapshot(termux(), ("sensor",))
        self.assertEqual(r["observations"]["termux_commands"]["termux-sensor"], "COMMAND_FOUND")
        self.check_no_action(r, "DEFER_UNVERIFIED")

    def test_N10_no_command_does_not_prove_no_hardware(self):
        r = assess_snapshot(dataclasses.replace(termux(), commands={}))
        self.assertEqual(r["observations"]["termux_commands"]["termux-sensor"], "UNKNOWN")

    def test_N11_environment_spoof_remains_hint(self):
        r = assess_snapshot(dataclasses.replace(linux(), android_hint=True))
        self.assertEqual(r["host"]["identity"], "ANDROID_HINT")
        self.assertEqual(r["host"]["identity_confidence"], "UNTRUSTED_HINTS")
        self.check_no_action(r, "OBSERVATION_ONLY")

    def test_N12_enforcement_hints_cannot_authorize_execution(self):
        r = assess_snapshot(termux(), ("execution",))
        self.check_no_action(r, "DEFER_UNVERIFIED")

    def test_N13_job_binary_cannot_authorize_background_job(self):
        r = assess_snapshot(termux(), ("background_job",))
        self.assertEqual(r["observations"]["termux_commands"]["termux-job-scheduler"], "COMMAND_FOUND")
        self.check_no_action(r, "DEFER_UNVERIFIED")

    def test_N14_empty_requirement_is_observation_only(self):
        r = assess_snapshot(termux())
        self.check_no_action(r, "OBSERVATION_ONLY")
        self.assertEqual(r["readiness"]["requested_intents"], [])

    def test_N15_unknown_requirement_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_REQUIREMENT"):
            assess_snapshot(termux(), ("force_allow",))

    def test_N16_deterministic_fingerprint(self):
        a = assess_snapshot(termux())
        b = assess_snapshot(termux())
        self.assertEqual(a, b)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual(len(a["fingerprint_sha256"]), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
