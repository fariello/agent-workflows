"""Tests for the local-leaks detection engine (DECISIONS D93).

Covers: fail-severity structural patterns, warn-only auto-derivation (cross-platform +
missing-source degradation), repo allowlist + user hints, the three scan modes
(working tree / history / wheel), a bounded history scan, public-identifier negatives,
and that THIS repo's tracked tree is clean. Leak tokens are synthesized at runtime so
this test file holds no literal leak. Stdlib unittest only.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.support import REPO_ROOT
from agent_workflows import local_leaks as ll


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


class ThisRepoTests(unittest.TestCase):
    def test_this_repo_working_tree_is_clean(self):
        fails, _warns = ll.run(REPO_ROOT)
        self.assertEqual(
            [f"{f.location}: {f.rule}" for f in fails],
            [],
            "local-leak fail findings in tracked files",
        )

    def test_module_source_is_self_clean(self):
        # The engine assembles tokens from fragments, so its own file must be leak-free.
        text = (REPO_ROOT / "agent_workflows" / "local_leaks.py").read_text(
            encoding="utf-8"
        )
        rs = ll.build_ruleset(REPO_ROOT)
        found = ll.scan_text(text, "local_leaks.py", rs)
        self.assertEqual([f.rule for f in found], [], f"self-leak: {found}")


class ScanModeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_working_tree_flags_home_path(self):
        leak = "/home/" + "someuser" + "/secret/path"
        _commit(self.repo, "a.md", f"see {leak}\n", "add")
        fails, _ = ll.run(self.repo)
        self.assertTrue(any(f.rule == "home-path" for f in fails), fails)

    def test_windows_home_recognized(self):
        leak = "C:\\Users\\" + "someone" + "\\proj"
        _commit(self.repo, "w.md", f"path {leak}\n", "add")
        fails, _ = ll.run(self.repo)
        self.assertTrue(any(f.rule == "windows-home" for f in fails), fails)

    def test_history_flags_leak_removed_from_head(self):
        # Leak in an OLD commit, removed at HEAD: working tree clean, history dirty.
        leak = "/home/" + "ghostuser" + "/x"
        _commit(self.repo, "h.md", f"{leak}\n", "add leak")
        _commit(self.repo, "h.md", "clean now\n", "scrub")
        tree_fails, _ = ll.run(self.repo)
        self.assertEqual(
            [f.rule for f in tree_fails], [], "working tree should be clean"
        )
        hist_fails, _ = ll.run(self.repo, history=True)
        self.assertTrue(any(f.rule == "home-path" for f in hist_fails), hist_fails)

    def test_history_max_commits_bound(self):
        leak = "/home/" + "oldu" + "/x"
        _commit(self.repo, "h.md", f"{leak}\n", "old leak")
        for i in range(3):
            _commit(self.repo, f"pad{i}.md", "clean\n", f"pad {i}")
        # Bounding to the most recent 2 commits should NOT reach the old leak.
        bounded, _ = ll.run(self.repo, history=True, max_commits=2)
        self.assertEqual(
            [f.rule for f in bounded], [], f"bound leaked older commits: {bounded}"
        )

    def test_wheel_scan_flags_leak(self):
        wheel = Path(self._tmp.name) / "pkg.whl"
        with zipfile.ZipFile(wheel, "w") as z:
            z.writestr("pkg/mod.py", "x = '/home/" + "wheeluser" + "/p'\n")
        fails, _ = ll.run(self.repo, wheel=wheel)
        self.assertTrue(any(f.rule == "home-path" for f in fails), fails)


class AllowlistAndHintsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        self._tmp.cleanup()

    def test_public_identifiers_not_flagged(self):
        # The package name, author email, and remote URL must never be flagged.
        content = (
            "name = 'agent-workflows'\n"
            f"email = '{ll._EMAIL}'\n"
            f"origin = '{ll._REMOTE}'\n"
        )
        _commit(self.repo, "meta.toml", content, "meta")
        fails, _ = ll.run(self.repo)
        self.assertEqual([f.rule for f in fails], [], f"false positive: {fails}")

    def test_repo_allowlist_exempts_a_line(self):
        marker = "MY-INTERNAL-HOST-OK"
        leak = "/home/" + "svcacct" + "/run"
        _commit(
            self.repo,
            ".agents/local-leaks-allowlist.toml",
            f'allow_line_substrings = ["{marker}"]\n',
            "allowlist",
        )
        _commit(self.repo, "note.md", f"{leak}  # {marker}\n", "note")
        fails, _ = ll.run(self.repo)
        self.assertEqual([f.rule for f in fails], [], f"allowlist not honored: {fails}")

    def test_user_hint_token_is_flagged(self):
        cfg = Path(self._tmp.name) / "cfg" / "agent-workflows"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / ll.USER_HINTS_FILENAME).write_text(
            json.dumps({"tokens": ["ZzMyCodenameZz"]}), encoding="utf-8"
        )
        _commit(self.repo, "n.md", "ref ZzMyCodenameZz here\n", "add")
        fails, _ = ll.run(self.repo)
        self.assertTrue(any(f.rule.startswith("user-hint") for f in fails), fails)

    def test_missing_user_hints_is_noop(self):
        # No hints file present -> no error, no extra findings.
        _commit(self.repo, "n.md", "totally clean\n", "add")
        fails, _ = ll.run(self.repo)
        self.assertEqual(fails, [])


class AutoDeriveTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_derive_is_warn_only_never_fails_gate(self):
        # A derived token appearing in content must NOT be a fail finding (only warn).
        derived = ll.derive_warn_tokens(self.repo)
        # Pick any derived token if present; else synthesize the env so one exists.
        os.environ["USER"] = "ci-derive-probe-user"
        try:
            _commit(self.repo, "d.md", "hello ci-derive-probe-user\n", "add")
            fails, warns = ll.run(self.repo, include_warn=True)
            self.assertFalse(
                any("ci-derive-probe-user" in f.snippet for f in fails),
                "derived token wrongly failed the gate",
            )
            self.assertTrue(
                any(f.severity == "warn" for f in warns),
                f"expected a warn finding; warns={warns}",
            )
        finally:
            os.environ.pop("USER", None)
        _ = derived  # derived may be empty in some envs; not asserted

    def test_missing_sources_degrade_without_error(self):
        # Strip likely sources; derivation must not raise and must return a dict.
        saved = {k: os.environ.pop(k, None) for k in ("USER", "USERNAME")}
        try:
            tokens = ll.derive_warn_tokens(self.repo)
            self.assertIsInstance(tokens, dict)
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_cli_exit_zero_on_clean_tree(self):
        from agent_workflows import cli

        _commit(self.repo, "ok.md", "nothing to see\n", "add")
        self.assertEqual(
            cli.main(["check-local-leaks", str(self.repo), "--no-color"]), 0
        )

    def test_cli_exit_one_on_leak(self):
        from agent_workflows import cli

        leak = "/home/" + "cliuser" + "/x"
        _commit(self.repo, "bad.md", f"{leak}\n", "add")
        self.assertEqual(
            cli.main(["check-local-leaks", str(self.repo), "--no-color"]), 1
        )


class SelfDocClarityTests(unittest.TestCase):
    """assess-self-documentation S1-S4: the aw CLI teaches at the point of use."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def _capture(self, argv):
        import contextlib
        import io
        from agent_workflows import cli

        out, err = io.StringIO(), io.StringIO()
        code = None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli.main(argv)
            except SystemExit as exc:  # argparse --help / usage errors
                code = exc.code
        return code, out.getvalue() + err.getvalue()

    def test_s1_bad_status_teaches_valid_set(self):
        (self.repo / ".agents" / "plans" / "pending").mkdir(parents=True)
        code, text = self._capture(
            ["plans", str(self.repo), "--status", "pendign", "--no-color"]
        )
        self.assertEqual(code, 2)
        # names at least one real status; does not silently succeed
        for s in ("draft", "approved", "executed"):
            self.assertIn(s, text)

    def test_s1_valid_status_still_works(self):
        (self.repo / ".agents" / "plans" / "pending").mkdir(parents=True)
        code, _ = self._capture(
            ["plans", str(self.repo), "--status", "approved", "--no-color"]
        )
        self.assertEqual(code, 0)

    def test_s2_no_decision_ids_in_help(self):
        import re

        for argv in (["--help"], ["check-local-leaks", "--help"]):
            _, text = self._capture(argv)
            self.assertIsNone(
                re.search(r"\(D\d+", text),
                f"decision-id jargon in help for {argv}: leaked",
            )

    def test_s2_no_decision_ids_in_local_leaks_messages(self):
        import re

        leak = "/home/" + "s2user" + "/x"
        _commit(self.repo, "bad.md", f"{leak}\n", "add")
        _, text = self._capture(["check-local-leaks", str(self.repo), "--no-color"])
        self.assertIsNone(
            re.search(r"\(D\d+", text), f"decision-id jargon in message: {text}"
        )

    def test_s3_install_all_discoverable_in_top_level_help(self):
        _, text = self._capture(["--help"])
        self.assertIn("install all", text)

    def test_s4_clean_run_prints_confirmation(self):
        _commit(self.repo, "ok.md", "nothing to see\n", "add")
        code, text = self._capture(["check-local-leaks", str(self.repo), "--no-color"])
        self.assertEqual(code, 0)
        self.assertIn("No local leaks found.", text)


if __name__ == "__main__":
    unittest.main()
