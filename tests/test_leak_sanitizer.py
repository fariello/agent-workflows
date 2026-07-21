"""Tests for the unified leak-sanitizer engine (IPD 20260721-1353-01, Set leak-sanitizer).

Covers the capabilities added on top of the D92/D93 local_leaks detection (which has its own
regression suite in tests/test_local_leaks.py): --fix (interactive vs --yes, dry-run,
unfixable-token reporting), --agent parseable output, the IP ruleset off-by-default + opt-in,
binary-blob flagging (E4), the staged-blob scan mode, the hostname warn/fail toggle (OQ4), the
one-canonical-config reconciliation (PR-003), and engine source self-cleanliness. Leak tokens
are synthesized at runtime so this test file holds no literal leak. Stdlib unittest only.
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.support import REPO_ROOT
from agent_workflows import leak_sanitizer as ls


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    return path


def _commit(repo: Path, rel: str, content: str, msg: str) -> None:
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], check=True)


class SelfCleanTests(unittest.TestCase):
    def test_engine_source_is_self_clean(self):
        text = (REPO_ROOT / "agent_workflows" / "leak_sanitizer.py").read_text(
            encoding="utf-8"
        )
        rs = ls.build_ruleset(REPO_ROOT)
        found = ls.scan_text(text, "leak_sanitizer.py", rs)
        self.assertEqual([f.rule for f in found], [], f"self-leak: {found}")

    def test_this_repo_tree_clean(self):
        fails, _ = ls.run(REPO_ROOT)
        self.assertEqual([f"{f.location}: {f.rule}" for f in fails], [])


class FixTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_fix_rewrites_home_path_with_yes(self):
        leak = "/home/" + "fixuser" + "/proj/file"
        _commit(self.repo, "a.md", f"path is {leak} here\n", "add")
        changed, unfixable = ls.fix_working_tree(self.repo, assume_yes=True)
        self.assertIn("a.md", changed)
        self.assertEqual(unfixable, [])
        text = (self.repo / "a.md").read_text()
        self.assertIn("~/proj/file", text)
        self.assertNotIn("fixuser", text)

    def test_fix_dry_run_does_not_write(self):
        leak = "/home/" + "dryuser" + "/x"
        _commit(self.repo, "a.md", f"{leak}\n", "add")
        changed, _ = ls.fix_working_tree(self.repo, dry_run=True)
        self.assertIn("a.md", changed)
        # File unchanged on disk.
        self.assertIn("dryuser", (self.repo / "a.md").read_text())

    def test_fix_interactive_declined_leaves_file(self):
        leak = "/home/" + "declineuser" + "/x"
        _commit(self.repo, "a.md", f"{leak}\n", "add")
        changed, _ = ls.fix_working_tree(
            self.repo, assume_yes=False, confirm=lambda rel, preview: False
        )
        self.assertEqual(changed, [])
        self.assertIn("declineuser", (self.repo / "a.md").read_text())

    def test_fix_reports_unfixable_identity_token(self):
        # A private-repo token has no safe generic rewrite: reported, never auto-changed.
        _commit(self.repo, "a.md", f"see {ls._R1} repo\n", "add")
        changed, unfixable = ls.fix_working_tree(self.repo, assume_yes=True)
        self.assertEqual(changed, [])
        self.assertTrue(any(f.rule == "private-repo" for f in unfixable), unfixable)
        self.assertIn(ls._R1, (self.repo / "a.md").read_text())


class AgentModeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def _run_main(self, argv):
        import contextlib

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ls.main(argv)
        return code, out.getvalue()

    def test_agent_output_is_parseable_and_prose_free(self):
        leak = "/home/" + "agentuser" + "/x"
        _commit(self.repo, "a.md", f"{leak}\n", "add")
        code, text = self._run_main([str(self.repo), "--agent"])
        self.assertEqual(code, 1)
        lines = [ln for ln in text.splitlines() if ln.strip()]
        self.assertTrue(lines, "expected at least one finding line")
        for ln in lines:
            parts = ln.split("\t")
            self.assertEqual(len(parts), 3, f"not path\\trule\\tseverity: {ln!r}")
            self.assertIn(parts[2], ("fail", "warn"))
        # No human prose footer.
        self.assertNotIn("Remove or abstract", text)

    def test_agent_clean_tree_exit_zero(self):
        _commit(self.repo, "ok.md", "nothing\n", "add")
        code, text = self._run_main([str(self.repo), "--agent"])
        self.assertEqual(code, 0)


class IpRulesetTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_ip_off_by_default(self):
        _commit(self.repo, "a.md", "server at 203.0.113.7 online\n", "add")
        fails, _ = ls.run(self.repo)
        self.assertFalse(any(f.rule == "ipv4" for f in fails), fails)

    def test_ip_opt_in_flags_ipv4(self):
        _commit(
            self.repo,
            ".agents/local-leaks-allowlist.toml",
            "ip_enabled = true\n",
            "cfg",
        )
        _commit(self.repo, "a.md", "server at 203.0.113.7 online\n", "add")
        fails, _ = ls.run(self.repo)
        self.assertTrue(any(f.rule == "ipv4" for f in fails), fails)

    def test_loopback_and_private_never_flagged_even_when_enabled(self):
        _commit(
            self.repo,
            ".agents/local-leaks-allowlist.toml",
            "ip_enabled = true\n",
            "cfg",
        )
        _commit(self.repo, "a.md", "use 127.0.0.1 and 192.168.1.5\n", "add")
        fails, _ = ls.run(self.repo)
        self.assertFalse(any(f.rule == "ipv4" for f in fails), fails)


class HostnameTierTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_hostname_warn_only_by_default(self):
        # A derived token (forced via $USER) is warn, never fail, with default config.
        os.environ["USER"] = "hn-probe-user"
        try:
            _commit(self.repo, "d.md", "ref hn-probe-user here\n", "add")
            fails, warns = ls.run(self.repo, include_warn=True)
            self.assertFalse(any("hn-probe-user" in f.snippet for f in fails))
            self.assertTrue(any(w.severity == "warn" for w in warns), warns)
        finally:
            os.environ.pop("USER", None)


class BinaryScanTests(unittest.TestCase):
    def test_binary_blob_leak_is_flagged_in_wheel(self):
        # E4: a leak inside binary-ish content must still be flagged (decode with replace).
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        wheel = Path(tmp.name) / "pkg.whl"
        payload = b"\x00\x01binary /home/" + b"binuser" + b"/x\x00\n"
        with zipfile.ZipFile(wheel, "w") as z:
            z.writestr("pkg/blob.bin", payload)
        fails, _ = ls.run(REPO_ROOT, wheel=wheel)
        self.assertTrue(any(f.rule == "home-path" for f in fails), fails)


class StagedScanTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_staged_flags_only_staged_content(self):
        # Commit clean, then STAGE a leak without committing: --staged flags it; tree does not.
        _commit(self.repo, "a.md", "clean\n", "add")
        leak = "/home/" + "staged" + "/x"
        (self.repo / "a.md").write_text(f"{leak}\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "a.md"], check=True)
        staged_fails, _ = ls.run(self.repo, staged=True)
        self.assertTrue(any(f.rule == "home-path" for f in staged_fails), staged_fails)


class ConfigReconciliationTests(unittest.TestCase):
    def test_one_canonical_tracked_config_no_competing_file(self):
        # PR-003: the tracked config is .agents/local-leaks-allowlist.toml and there is NO
        # second competing leak-sanitizer allow file in the repo.
        self.assertTrue((REPO_ROOT / ls.REPO_ALLOWLIST_REL).exists())
        stray = list(REPO_ROOT.glob(".agents/leak-sanitizer-allow*"))
        self.assertEqual(stray, [], f"competing config file present: {stray}")


if __name__ == "__main__":
    unittest.main()
