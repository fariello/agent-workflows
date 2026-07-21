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


class TomlParserTests(unittest.TestCase):
    """Characterization + C4 regression for the minimal TOML list parser (IPD 20260721-1851-01).

    Step 0 hardened `_parse_simple_toml_lists` so a `]` (or the other quote char) inside a
    quoted string is not mistaken for structure. These pin both the pre-existing valid shapes
    and the bug class the wizard depends on.
    """

    def _p(self, text):
        return ls._parse_simple_toml_lists(text)

    # Characterization: shapes that worked before must still parse identically.
    def test_empty_array(self):
        self.assertEqual(
            self._p("allow_line_substrings = []"), {"allow_line_substrings": []}
        )

    def test_two_values(self):
        self.assertEqual(
            self._p('fail_patterns = ["a", "b"]'), {"fail_patterns": ["a", "b"]}
        )

    def test_multiline_array(self):
        self.assertEqual(
            self._p('fail_patterns = [\n  "a",\n  "b",\n]'),
            {"fail_patterns": ["a", "b"]},
        )

    def test_commented_key_is_ignored(self):
        self.assertEqual(self._p('# fail_patterns = ["x"]'), {})

    def test_bool_line_is_not_a_list(self):
        self.assertEqual(self._p("ip_enabled = true"), {})

    # C4 regression: bracket-containing values used to truncate to [] (the whole point).
    def test_char_class_pattern_round_trips(self):
        self.assertEqual(
            self._p('fail_patterns = ["/home/[a-z]+/x"]'),
            {"fail_patterns": ["/home/[a-z]+/x"]},
        )

    def test_bracket_substring_round_trips(self):
        self.assertEqual(
            self._p('allow_line_substrings = ["see [docs]"]'),
            {"allow_line_substrings": ["see [docs]"]},
        )

    def test_value_may_contain_the_other_quote(self):
        # A double-quoted value may contain a single quote (dual-quote-select writer, OQ4).
        got = self._p('allow_line_substrings = ["it' + chr(39) + 's fine"]')
        self.assertEqual(got, {"allow_line_substrings": ["it" + chr(39) + "s fine"]})


class ConfigWriterTests(unittest.TestCase):
    """Round-trip + rejection for the config writers (IPD 20260721-1851-01 CP1)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "r"
        self.repo.mkdir(parents=True)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        self._tmp.cleanup()

    def test_repo_allowlist_round_trips_including_brackets(self):
        ls.write_repo_allowlist(
            self.repo,
            allow_line_substrings=["see [docs]", "MY-OK"],
            fail_patterns=["/home/[a-z]+/x", "ses_[0-9A-Za-z]{8,}"],
            ip_enabled=True,
            hostname_fail=False,
        )
        lists = ls.load_repo_allowlist(self.repo)
        bools = ls.load_repo_config_bools(self.repo)
        self.assertEqual(lists["allow_line_substrings"], ["see [docs]", "MY-OK"])
        self.assertEqual(
            lists["fail_patterns"], ["/home/[a-z]+/x", "ses_[0-9A-Za-z]{8,}"]
        )
        self.assertTrue(bools["ip_enabled"])
        self.assertFalse(bools["hostname_fail"])

    def test_empty_lists_round_trip(self):
        ls.write_repo_allowlist(
            self.repo,
            allow_line_substrings=[],
            fail_patterns=[],
            ip_enabled=False,
            hostname_fail=False,
        )
        lists = ls.load_repo_allowlist(self.repo)
        self.assertEqual(lists.get("allow_line_substrings"), [])
        self.assertEqual(lists.get("fail_patterns"), [])

    def test_value_with_one_quote_uses_other_delimiter(self):
        val = (
            "it" + chr(39) + "s a /home/[x]/p"
        )  # contains a single quote AND a bracket
        ls.write_repo_allowlist(
            self.repo,
            allow_line_substrings=[val],
            fail_patterns=[],
            ip_enabled=False,
            hostname_fail=False,
        )
        self.assertEqual(
            ls.load_repo_allowlist(self.repo)["allow_line_substrings"], [val]
        )

    def test_value_with_both_quotes_is_rejected_before_writing(self):
        bad = "has " + chr(34) + " and " + chr(39)  # both a double and a single quote
        with self.assertRaises(ls.ConfigValueError):
            ls.write_repo_allowlist(
                self.repo,
                allow_line_substrings=[bad],
                fail_patterns=[],
                ip_enabled=False,
                hostname_fail=False,
            )
        # Nothing was written (rejected before the atomic write).
        self.assertFalse((self.repo / ls.REPO_ALLOWLIST_REL).exists())

    def test_user_hints_round_trip_and_lands_in_config_dir_not_repo(self):
        ls.write_user_hints(tokens=["MyCodename"], patterns=["/srv/[a-z]+/private"])
        hints = ls.load_user_hints()
        self.assertEqual(hints.get("tokens"), ["MyCodename"])
        self.assertEqual(hints.get("patterns"), ["/srv/[a-z]+/private"])
        # It must NOT be written into the repo tree.
        self.assertFalse((self.repo / ls.USER_HINTS_FILENAME).exists())
        self.assertTrue((ls._config_dir() / ls.USER_HINTS_FILENAME).is_file())


class WizardCoreTests(unittest.TestCase):
    """The interactive wizard core via injected prompt/confirm (IPD 20260721-1851-01 CP2)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "r"
        self.repo.mkdir(parents=True)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")
        from agent_workflows import leak_sanitizer_config as lsc

        self.lsc = lsc

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        self._tmp.cleanup()

    def _run(self, prompt_answers, confirm_answers):
        pa = iter(prompt_answers)
        ca = iter(confirm_answers)
        return self.lsc.configure(
            self.repo,
            prompt=lambda q: next(pa, ""),
            confirm=lambda q: next(ca, False),
            emit=lambda line: None,
        )

    def test_add_allowlist_entry_and_write(self):
        # Add one allowlist substring; keep everything else empty/off; confirm the write.
        # Prompt order: allow_line_substrings loop, fail_patterns loop, tokens loop, patterns loop.
        summary = self._run(
            prompt_answers=["PUBLIC-OK", "", "", "", ""],
            confirm_answers=[False, False, True],  # ip off, hostname off, write yes
        )
        self.assertTrue(summary["changed"])
        self.assertTrue(summary["wrote"])
        self.assertEqual(
            ls.load_repo_allowlist(self.repo)["allow_line_substrings"], ["PUBLIC-OK"]
        )

    def test_flip_ip_toggle(self):
        summary = self._run(
            prompt_answers=["", "", "", ""],
            confirm_answers=[True, False, True],  # ip ON, hostname off, write yes
        )
        self.assertTrue(summary["changed"])
        self.assertTrue(ls.load_repo_config_bools(self.repo)["ip_enabled"])

    def test_add_personal_token_writes_hints_not_repo(self):
        summary = self._run(
            prompt_answers=["", "", "MyCodename", ""],  # add one token
            confirm_answers=[False, False, True],
        )
        self.assertTrue(summary["changed"])
        self.assertEqual(ls.load_user_hints().get("tokens"), ["MyCodename"])
        # personal hints never land in the repo
        self.assertFalse((self.repo / ls.USER_HINTS_FILENAME).exists())

    def test_decline_writes_nothing(self):
        summary = self._run(
            prompt_answers=["PUBLIC-OK", "", "", ""],
            confirm_answers=[False, False, False],  # decline the final write
        )
        self.assertEqual(summary["wrote"], [])
        self.assertFalse((self.repo / ls.REPO_ALLOWLIST_REL).exists())

    def test_no_change_run_writes_nothing(self):
        # Everything blank/kept and toggles unchanged -> no diff -> no write, no confirm needed.
        summary = self._run(
            prompt_answers=["", "", "", ""],
            confirm_answers=[False, False],  # ip off, hostname off (both already off)
        )
        self.assertFalse(summary["changed"])
        self.assertEqual(summary["wrote"], [])

    def test_bracket_pattern_round_trips_through_wizard(self):
        summary = self._run(
            prompt_answers=[
                "",
                "/home/[a-z]+/secret",
                "",
                "",
            ],  # add a char-class fail pattern
            confirm_answers=[False, False, True],
        )
        self.assertTrue(summary["wrote"])
        self.assertEqual(
            ls.load_repo_allowlist(self.repo)["fail_patterns"], ["/home/[a-z]+/secret"]
        )


class ConfigReconciliationTests(unittest.TestCase):
    def test_one_canonical_tracked_config_no_competing_file(self):
        # PR-003: the tracked config is .agents/local-leaks-allowlist.toml and there is NO
        # second competing leak-sanitizer allow file in the repo.
        self.assertTrue((REPO_ROOT / ls.REPO_ALLOWLIST_REL).exists())
        stray = list(REPO_ROOT.glob(".agents/leak-sanitizer-allow*"))
        self.assertEqual(stray, [], f"competing config file present: {stray}")


if __name__ == "__main__":
    unittest.main()
