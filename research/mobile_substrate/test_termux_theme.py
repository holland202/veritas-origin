"""Local-only tests for the optional terminal cosmetics installer."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from termux_theme import BANNER_RELATIVE, END, START, install, uninstall


class ThemeInstallTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.home = Path(self.td.name)
        self.rc = self.home / ".bashrc"
        self.original = (
            '# User config\n'
            'echo "Old decorative header"\n'
            'python3 health_monitor.py\n'
            'alias sovereign-chat="echo keep-this-alias"\n'
        )
        self.rc.write_text(self.original, encoding="utf-8")

    def test_backup_retain_alias_and_disable_only_missing_monitor(self):
        result = install(self.home)
        self.assertIn("Installed", result)
        after = self.rc.read_text()
        self.assertIn(START, after)
        self.assertIn(END, after)
        self.assertIn('alias sovereign-chat="echo keep-this-alias"', after)
        self.assertIn('# [SOVEREIGN-THEME] disabled missing health_monitor.py:', after)
        self.assertIn('echo "Old decorative header"', after)
        self.assertEqual(after.count("python3 health_monitor.py"), 1)
        self.assertTrue((self.home / BANNER_RELATIVE).is_file())
        backups = list(self.home.glob(".bashrc.before-sovereign-theme.*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), self.original)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_idempotent(self):
        install(self.home)
        after = self.rc.read_bytes()
        second = install(self.home)
        self.assertIn("Already installed", second)
        self.assertEqual(after, self.rc.read_bytes())
        self.assertEqual(len(list(self.home.glob(".bashrc.before-sovereign-theme.*"))), 1)

    def test_keep_existing_health_monitor(self):
        (self.home / "Sovereign-Manifold").mkdir()
        (self.home / "Sovereign-Manifold" / "health_monitor.py").write_text("# demo\n")
        install(self.home)
        self.assertIn("\npython3 health_monitor.py\n", self.rc.read_text())
        self.assertNotIn("disabled missing", self.rc.read_text())

    def test_uninstall_removes_only_managed_block(self):
        install(self.home)
        result = uninstall(self.home)
        after = self.rc.read_text()
        self.assertIn("Removed", result)
        self.assertNotIn(START, after)
        self.assertNotIn(END, after)
        self.assertIn("alias sovereign-chat", after)
        # A restored missing file would need a separate review before
        # deliberately re-enabling a startup command.
        self.assertIn("disabled missing", after)

    def test_refuse_symlink_rc(self):
        target = self.home / "realrc"
        target.write_text(self.original)
        self.rc.unlink()
        self.rc.symlink_to(target)
        with self.assertRaises(ValueError):
            install(self.home)
        self.assertEqual(target.read_text(), self.original)

    def test_incomplete_marker_is_not_overwritten(self):
        self.rc.write_text(self.original + "\n" + START + "\n")
        with self.assertRaises(ValueError):
            install(self.home)
        self.assertEqual(len(list(self.home.glob(".bashrc.before-sovereign-theme.*"))), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
