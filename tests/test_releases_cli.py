"""Tests for the `aw releases` owner verb (IPD w0ln4q E-02..E-05).

Covers:
  * E-02 / V-02 - the three command runners (`run_list`, `run_show`, `run_new`) in human, `--json`,
    and `--agent` modes, their exit codes (0 clean, 2 on a bad selector / missing required flag), and
    the PREVIEW-BY-DEFAULT contract for `new` (asserted by a byte-identical directory listing before
    and after a non-`--apply` run).
  * E-03 / V-03 - parser registration and dispatch: bare `aw releases` defaults to `list` (OQ-01), the
    `release` alias, `show` defaulting to `next`, and the ADVERSARIAL assertion that `aw releases
    check` is NOT a subcommand (the canonical validator stays `aw check releases`, check_engine.py).
  * E-04 / V-04 - dynamic release-selector completion for `aw releases show`.

Every test runs against a controlled temp repo (never the live tree) so expected counts are stable.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli, completion, releases


def _args(**kw) -> argparse.Namespace:
    """A Namespace with the flags every runner reads, so getattr defaults are never exercised
    accidentally. Individual tests override what they care about."""
    base = dict(
        dir=None,
        agent=False,
        json=False,
        no_color=True,
        selector=None,
        version=None,
        summary=None,
        status=None,
        apply=False,
    )
    base.update(kw)
    ns = argparse.Namespace()
    for k, v in base.items():
        setattr(ns, k, v)
    return ns


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _capture(fn, *a, **kw):
    """Run `fn`, returning (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = fn(*a, **kw)
    return rc, out.getvalue(), err.getvalue()


def _listing(d: Path):
    """A stable, content-sensitive snapshot of a directory (name -> bytes)."""
    if not d.is_dir():
        return {}
    return {p.name: p.read_bytes() for p in sorted(d.iterdir()) if p.is_file()}


class _ReleasesRepoFixture(unittest.TestCase):
    """A temp repo with ONE planned release (`next` resolves) and two live gating items."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.rec = self.root / ".aw" / "records"
        self.releases_dir = self.rec / "releases"
        _write(
            self.releases_dir / "20260101-aaaaaa-01-aaaaaa-2-0-0.release.md",
            "# Release: 2.0.0\n\n- Id: aaaaaa\n- Status: planned\n- Version: 2.0.0\n"
            "- Summary: the planned one\n\n## Workflow history\n\n"
            "- 2026-01-01 created (aw releases): seeded\n",
        )
        _write(
            self.rec / "backlog" / "open" / "20260102-g-01-gate01-blocker.backlog.md",
            "- Id: gate01\n- Status: open\n- Set: g\n- Priority: high\n- Kind: bug\n"
            "- Summary: gates the release\n- Blocks-Release: next\n",
        )
        _write(
            self.rec / "plans" / "pending" / "20260102-g-01-gate03-a-plan.ipd.md",
            "# IPD: p\n\n- Id: gate03\n- Status: approved\n- Set: g (g)\n"
            "- Blocks-Release: aaaaaa\n\n## Goal\n\nx\n",
        )
        _write(
            self.rec / "backlog" / "open" / "20260102-g-01-free01-nogate.backlog.md",
            "- Id: free01\n- Status: open\n- Set: g\n- Priority: low\n- Kind: chore\n"
            "- Summary: gates nothing\n",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()


# --------------------------------------------------------------------------------------
# E-02 / V-02: run_list
# --------------------------------------------------------------------------------------


class RunListTests(_ReleasesRepoFixture):
    def test_human_output_names_id6_and_version(self) -> None:
        rc, out, err = _capture(releases.run_list, _args(dir=str(self.root)))
        self.assertEqual(rc, 0, err)
        self.assertIn("aaaaaa", out)
        self.assertIn("2.0.0", out)
        self.assertIn("planned", out)
        self.assertIn("next -> 2.0.0 (aaaaaa)", out)

    def test_json_record_count_matches_list_releases(self) -> None:
        rc, out, err = _capture(releases.run_list, _args(dir=str(self.root), json=True))
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertEqual(
            len(payload["data"]["releases"]), len(releases.list_releases(self.root))
        )
        self.assertEqual(payload["data"]["count"], 1)
        self.assertEqual(payload["data"]["next"], {"id": "aaaaaa", "version": "2.0.0"})
        self.assertEqual(payload["exit_code"], 0)

    def test_agent_emits_aw_agent_v1_jsonl(self) -> None:
        rc, out, err = _capture(
            releases.run_list, _args(dir=str(self.root), agent=True)
        )
        self.assertEqual(rc, 0, err)
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertTrue(lines, "agent mode must emit at least one JSONL record")
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "releases list")
        self.assertEqual(rec["exit"], 0)

    def test_empty_tree_is_clean_with_guidance(self) -> None:
        empty = Path(self._tmp.name) / "emptyrepo"
        (empty / ".aw" / "records" / "releases").mkdir(parents=True)
        rc, out, err = _capture(releases.run_list, _args(dir=str(empty)))
        self.assertEqual(rc, 0, err)
        self.assertIn("no release records", out)
        self.assertIn("aw releases new", out)


# --------------------------------------------------------------------------------------
# E-02 / V-02: run_show
# --------------------------------------------------------------------------------------


class RunShowTests(_ReleasesRepoFixture):
    def test_show_next_names_release_and_lists_blockers(self) -> None:
        rc, out, err = _capture(
            releases.run_show, _args(dir=str(self.root), selector="next")
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("2.0.0", out)
        self.assertIn("aaaaaa", out)
        self.assertIn("release-blockers (2)", out)
        # each blocker's id6 AND its native status appear
        self.assertIn("gate01", out)
        self.assertIn("open", out)
        self.assertIn("gate03", out)
        self.assertIn("approved", out)
        self.assertNotIn("free01", out)

    def test_show_defaults_to_next_when_no_selector(self) -> None:
        rc, out, err = _capture(releases.run_show, _args(dir=str(self.root)))
        self.assertEqual(rc, 0, err)
        self.assertIn("aaaaaa", out)

    def test_show_blockers_match_get_release_blockers(self) -> None:
        rc, out, err = _capture(
            releases.run_show, _args(dir=str(self.root), selector="next", json=True)
        )
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        expected = {b["id"] for b in releases.get_release_blockers(self.root, "next")}
        self.assertEqual({b["id"] for b in payload["data"]["blockers"]}, expected)
        self.assertEqual(payload["data"]["blocker_count"], len(expected))

    def test_show_bad_selector_exits_2(self) -> None:
        rc, out, err = _capture(
            releases.run_show, _args(dir=str(self.root), selector="nosuch")
        )
        self.assertEqual(rc, 2)
        self.assertIn("does not resolve", err)

    def test_show_bad_selector_agent_mode_exits_2(self) -> None:
        rc, out, err = _capture(
            releases.run_show,
            _args(dir=str(self.root), selector="nosuch", agent=True),
        )
        self.assertEqual(rc, 2)
        rec = json.loads([line for line in out.splitlines() if line.strip()][0])
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(rec["kind"], "error")

    def test_show_renders_history(self) -> None:
        rc, out, err = _capture(
            releases.run_show, _args(dir=str(self.root), selector="aaaaaa")
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("workflow history", out)
        self.assertIn("created (aw releases): seeded", out)


# --------------------------------------------------------------------------------------
# E-02 / V-02: run_new
# --------------------------------------------------------------------------------------


class RunNewTests(_ReleasesRepoFixture):
    def test_preview_writes_nothing_and_leaves_dir_identical(self) -> None:
        before = _listing(self.releases_dir)
        rc, out, err = _capture(
            releases.run_new,
            _args(dir=str(self.root), version="9.9.9", summary="probe"),
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("would write", out)
        self.assertIn("- Version: 9.9.9", out)
        self.assertEqual(
            _listing(self.releases_dir),
            before,
            "a preview must leave the releases directory byte-identical",
        )

    def test_apply_creates_a_record_that_check_releases_passes(self) -> None:
        rc, out, err = _capture(
            releases.run_new,
            _args(dir=str(self.root), version="9.9.9", summary="probe", apply=True),
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("wrote", out)
        created = [
            p for p in self.releases_dir.glob("*.release.md") if "9-9-9" in p.name
        ]
        self.assertEqual(len(created), 1)
        text = created[0].read_text(encoding="utf-8")
        self.assertIn("- Version: 9.9.9", text)
        self.assertIn("- Status: planned", text)
        # The canonical validator (the one `aw check releases` calls) accepts it.
        self.assertEqual(releases.validate_release(created[0], text), [])
        from agent_workflows import check_engine as _ce

        drift = _ce.check_type(self.root, "releases")
        self.assertEqual(
            [d for d in drift if "9-9-9" in d.location],
            [],
            "a record created by `aw releases new --apply` must pass `aw check releases`",
        )

    def test_missing_version_exits_2(self) -> None:
        rc, out, err = _capture(
            releases.run_new, _args(dir=str(self.root), summary="probe")
        )
        self.assertEqual(rc, 2)
        self.assertIn("--version is required", err)

    def test_missing_summary_exits_2(self) -> None:
        rc, out, err = _capture(
            releases.run_new, _args(dir=str(self.root), version="9.9.9")
        )
        self.assertEqual(rc, 2)
        self.assertIn("--summary is required", err)

    def test_bad_status_exits_2_and_writes_nothing(self) -> None:
        before = _listing(self.releases_dir)
        rc, out, err = _capture(
            releases.run_new,
            _args(
                dir=str(self.root),
                version="9.9.9",
                summary="probe",
                status="bogus",
                apply=True,
            ),
        )
        self.assertEqual(rc, 2)
        self.assertIn("--status must be one of", err)
        self.assertEqual(_listing(self.releases_dir), before)

    def test_json_preview_reports_applied_false(self) -> None:
        rc, out, err = _capture(
            releases.run_new,
            _args(dir=str(self.root), version="9.9.9", summary="probe", json=True),
        )
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertFalse(payload["data"]["applied"])
        self.assertEqual(len(payload["changes"]), 1)
        self.assertFalse(payload["changes"][0]["applied"])


# --------------------------------------------------------------------------------------
# E-03 / V-03: parser registration, dispatch, aliases, and the anti-duplication guard
# --------------------------------------------------------------------------------------


class ReleasesParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = cli._build_parser()
        action = next(
            a for a in self.parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        self.choices = action.choices

    def test_releases_and_release_alias_registered(self) -> None:
        self.assertIn("releases", self.choices)
        self.assertIn("release", self.choices)
        # An argparse alias shares the parent's parser object.
        self.assertIs(self.choices["releases"], self.choices["release"])

    def test_subcommands_are_exactly_list_show_new(self) -> None:
        sub = next(
            a
            for a in self.choices["releases"]._actions
            if isinstance(a, argparse._SubParsersAction)
        )
        self.assertEqual(set(sub.choices), {"list", "show", "new"})

    def test_no_releases_check_subcommand(self) -> None:
        """ADVERSARIAL (PR-002): `aw check releases` is the canonical validator (check_engine ->
        validate_release). A `releases check` subcommand would be a second entry point to the same
        validator, so it must NOT exist - now or after any future refactor."""
        sub = next(
            a
            for a in self.choices["releases"]._actions
            if isinstance(a, argparse._SubParsersAction)
        )
        self.assertNotIn("check", sub.choices)
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stderr(io.StringIO()):
                self.parser.parse_args(["releases", "check"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertFalse(hasattr(releases, "run_check"))

    def test_bare_releases_parses_with_no_subcommand(self) -> None:
        args = self.parser.parse_args(["releases"])
        self.assertEqual(args.command, "releases")
        self.assertIsNone(getattr(args, "releases_command", None))

    def test_show_selector_is_optional(self) -> None:
        args = self.parser.parse_args(["releases", "show"])
        self.assertIsNone(args.selector)
        args = self.parser.parse_args(["releases", "show", "next"])
        self.assertEqual(args.selector, "next")

    def test_new_flags_registered(self) -> None:
        args = self.parser.parse_args(
            ["releases", "new", "--version", "3.0.0", "--summary", "s", "--apply"]
        )
        self.assertEqual(args.version, "3.0.0")
        self.assertEqual(args.summary, "s")
        self.assertTrue(args.apply)
        self.assertEqual(args.status, "planned")


class ReleasesDispatchTests(_ReleasesRepoFixture):
    def _dispatch(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_bare_releases_lists(self) -> None:
        rc, out, err = self._dispatch(["releases", "--dir", str(self.root)])
        self.assertEqual(rc, 0, err)
        self.assertIn("aaaaaa", out)
        self.assertIn("2.0.0", out)

    def test_release_alias_lists(self) -> None:
        rc, out, err = self._dispatch(["release", "--dir", str(self.root)])
        self.assertEqual(rc, 0, err)
        self.assertIn("aaaaaa", out)

    def test_explicit_list(self) -> None:
        rc, out, err = self._dispatch(["releases", "list", "--dir", str(self.root)])
        self.assertEqual(rc, 0, err)
        self.assertIn("aaaaaa", out)

    def test_show_next_via_cli(self) -> None:
        rc, out, err = self._dispatch(
            ["releases", "show", "next", "--dir", str(self.root)]
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("release-blockers", out)

    def test_new_preview_via_cli_writes_nothing(self) -> None:
        before = _listing(self.releases_dir)
        rc, out, err = self._dispatch(
            [
                "releases",
                "new",
                "--version",
                "9.9.9",
                "--summary",
                "probe",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("would write", out)
        self.assertEqual(_listing(self.releases_dir), before)

    def test_unknown_selector_via_cli_exits_2(self) -> None:
        rc, out, err = self._dispatch(
            ["releases", "show", "nosuch", "--dir", str(self.root)]
        )
        self.assertEqual(rc, 2)


# --------------------------------------------------------------------------------------
# E-04 / V-04: completion
# --------------------------------------------------------------------------------------


class ReleasesCompletionTests(_ReleasesRepoFixture):
    def test_static_scripts_carry_the_verb(self) -> None:
        for shell in ("bash", "zsh", "fish"):
            script = completion.generate(shell)
            self.assertIn(
                "releases", script, f"{shell} completion must carry the releases verb"
            )

    def test_static_scripts_carry_the_subcommands(self) -> None:
        tree = completion.introspect_cli_tree(cli._build_parser())
        self.assertIn("releases", tree["subcommands"])
        self.assertEqual(
            set(tree["subcommands"]["releases"]["subcommands"]),
            {"list", "show", "new"},
        )

    def test_dynamic_show_selector_resolves_id6_version_and_next(self) -> None:
        got = completion.complete_query(["aw", "releases", "show", ""], 3, self.root)
        self.assertIn("aaaaaa", got)
        self.assertIn("2.0.0", got)
        self.assertIn("next", got)

    def test_dynamic_show_selector_honors_the_alias(self) -> None:
        got = completion.complete_query(["aw", "release", "show", ""], 3, self.root)
        self.assertIn("aaaaaa", got)
        self.assertIn("next", got)

    def test_dynamic_show_selector_prefix_filters(self) -> None:
        got = completion.complete_query(["aw", "releases", "show", "aa"], 3, self.root)
        self.assertEqual(got, ["aaaaaa"])

    def test_next_absent_when_no_single_planned_release(self) -> None:
        # Flip the only planned release to shipped: `next` no longer resolves, so it is not offered.
        p = next(self.releases_dir.glob("*.release.md"))
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "- Status: planned", "- Status: shipped"
            ),
            encoding="utf-8",
        )
        got = completion.complete_query(["aw", "releases", "show", ""], 3, self.root)
        self.assertIn("aaaaaa", got)
        self.assertNotIn("next", got)

    def test_release_selector_candidates_reuses_list_releases(self) -> None:
        got = set(completion.release_selector_candidates(self.root))
        expected = {r.id6 for r in releases.list_releases(self.root)} | {
            r.version for r in releases.list_releases(self.root)
        }
        self.assertTrue(expected.issubset(got))

    def test_dunder_complete_wire_protocol(self) -> None:
        import os

        prev = Path.cwd()
        out = io.StringIO()
        try:
            os.chdir(self.root)
            with redirect_stdout(out):
                rc = cli.main(
                    ["__complete", "--cword", "3", "--", "aw", "releases", "show"]
                )
        finally:
            os.chdir(prev)
        self.assertEqual(rc, 0)
        tokens = out.getvalue().split()
        self.assertIn("aaaaaa", tokens)
        self.assertIn("next", tokens)


# --------------------------------------------------------------------------------------
# E-05 / V-05: documentation + no-regression
# --------------------------------------------------------------------------------------


class ReleasesDocsTests(unittest.TestCase):
    def test_releases_readme_documents_the_owner_verb(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        readme = repo_root / ".aw" / "records" / "releases" / "README.md"
        self.assertTrue(readme.is_file(), f"missing {readme}")
        text = readme.read_text(encoding="utf-8")
        self.assertIn("aw releases", text)
        for token in ("aw releases list", "aw releases show", "aw releases new"):
            self.assertIn(token, text)
        # The README must ALSO point at the canonical validator, not invent `aw releases check`.
        self.assertIn("aw check releases", text)
        self.assertNotIn("aw releases check", text)


if __name__ == "__main__":
    unittest.main()
