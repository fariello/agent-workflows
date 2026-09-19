"""Tests for the unified leak-sanitizer engine (IPD 20260721-1353-01, Set leak-sanitizer).

Covers the capabilities added on top of the D92/D93 local_leaks detection (which has its own
regression suite in tests/test_local_leaks.py): --fix (interactive vs --yes, dry-run,
unfixable-token reporting), --agent parseable output, the IP ruleset off-by-default + opt-in,
binary-blob flagging (E4), the staged-blob scan mode, the hostname warn/fail toggle (OQ4), the
one-canonical-config reconciliation (PR-003), and engine source self-cleanliness. Leak tokens
are synthesized at runtime so this test file holds no literal leak. Stdlib unittest only.

Most of this file is TABLE-DRIVEN, because most of it was one shape repeated: build a throwaway
git repository, commit one crafted file, call one engine entry point, and assert one outcome. The
tables group by SUBJECT (the fix pipeline, the machine-readable output, the config-gated rule
tiers, the TOML reader, the config writers, the wizard) rather than by which function implements
it.

THE RULE THAT SHAPES EVERY TABLE, and it is a security rule rather than a style one: A DETECTOR
TEST IS EVIDENCE ONLY IF THE DETECTOR WAS LOOKING. An assertion that some input is CLEAN, or that
some rule did NOT fire, passes trivially when detection is off. So every table below containing a
"not flagged" expectation also contains, IN THE SAME TEST, a planted row whose named rule MUST
fire. Those rows are labelled CONTROL in their reason string, and each table's failure message
states outright that its clean rows are vacuous while its control rows are broken.

WHERE A MERGE WOULD HAVE SEPARATED A CLEAN ASSERTION FROM ITS CONTROL, THE MERGE WAS NOT MADE.
The two repo-wide sweeps in `SelfCleanTests` are the case in point: they stay separate tests, at
full scope, and say why.

EVERY ROW NAMES ITS RULE AND SEVERITY rather than asserting that something was flagged. The rule
names are an interface (`--fix` keys rewrites off them, the config references them, the hook and
`--agent` output print them), so a rule answering under a new name is a breaking change.
"""

from __future__ import annotations

import pytest

import io
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from agent_workflows import leak_sanitizer as ls
from tests.support import REPO_ROOT

# Heavy subprocess/scan suite; excluded from the fast default run (see pyproject addopts
# `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow


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
    """The two repo-wide sweeps. DELIBERATELY NOT TABULATED, and deliberately NOT SAMPLED.

    These are the only tests in this file whose subject is the REAL REPOSITORY rather than a
    fixture, and they are the invariant the whole module exists to serve. They stay two separate
    tests, at full scope, for three reasons.

    FIRST, merging them would require a shared "expected findings" column whose value is `[]` for
    both, which is exactly the vacuous shape this file's docstring forbids. Their control is not
    absent, it is elsewhere and on the same engine build: every table below plants a leak and
    requires a NAMED rule to fire, so "this tree is clean" is being asserted against a detector
    that is demonstrably still looking.

    SECOND, NEITHER MAY BE NARROWED. A sweep over a SAMPLE of tracked files, or over the engine
    with a reduced ruleset, would still pass while missing the one file that leaks. So
    `test_this_repo_tree_clean` keeps calling `ls.run(REPO_ROOT)` over the entire tracked tree,
    and `test_engine_source_is_self_clean` keeps scanning the engine's whole source text with the
    full `build_ruleset`.

    THIRD, they fail for different reasons and need different messages. A tree finding means a
    tracked file must be scrubbed before it is published; a self-leak means the engine stopped
    assembling its sensitive literals from fragments and now contains one verbatim, which is the
    subtler bug because the scanner would then be reporting itself.
    """

    def test_engine_source_is_self_clean(self):
        """Kept separate: the subject is the engine's OWN source under the FULL ruleset.

        The module builds every sensitive literal from fragments (`_R1`, `_EMAIL`, `_VC` and
        friends) precisely so its own file is not a leak. This is what proves that assembly is
        still in place.
        """
        text = (REPO_ROOT / "agent_workflows" / "leak_sanitizer.py").read_text(
            encoding="utf-8"
        )
        rs = ls.build_ruleset(REPO_ROOT)
        found = ls.scan_text(text, "leak_sanitizer.py", rs)
        self.assertEqual([f.rule for f in found], [], f"self-leak: {found}")

    def test_this_repo_tree_clean(self):
        """Kept separate: scans THE WHOLE tracked tree. Must never be reduced to a sample."""
        fails, _ = ls.run(REPO_ROOT)
        self.assertEqual([f"{f.location}: {f.rule}" for f in fails], [])


class FixTests(unittest.TestCase):
    """`--fix`: rewrite what can be rewritten safely, report what cannot, and obey the consent mode.

    ONE table replaces four tests (`test_fix_rewrites_home_path_with_yes`,
    `test_fix_dry_run_does_not_write`, `test_fix_interactive_declined_leaves_file`,
    `test_fix_reports_unfixable_identity_token`). Every one committed one leaky file into a
    throwaway repo and called `fix_working_tree` with different keyword arguments, so THE CONSENT
    MODE IS A COLUMN (`--yes`, dry run, interactive-declined, interactive-accepted) and the LEAK
    CLASS is a second column (rewritable home path versus unrewritable identity token).

    Why the table beats the four: `fix_working_tree` returns a `(changed, unfixable)` pair and also
    has a side effect on disk, and the DANGEROUS failure is those two disagreeing - reporting a
    file as changed while leaving the leak in place, or rewriting a file it was told not to touch.
    Every row here asserts BOTH the return value AND the bytes on disk, which is what makes the
    dry-run and declined rows meaningful: each reports the file in `changed` while the leak must
    still be present, so a row that asserted only the return value would be identical to the
    `--yes` row and prove nothing.

    THE ROWS ALSO PIN WHAT MUST NOT BE REWRITTEN. The unfixable row plants a private-repo token
    that has no safe generic substitute: guessing one would silently alter meaning, so the engine
    must report it for a human instead. A `--fix` that "helpfully" rewrote it would pass a
    changed-file assertion and corrupt the file.

    THE CLEAN ROW IS PAIRED WITH ITS CONTROLS IN THIS SAME TEST. On its own, "a clean tree yields
    no changes" is satisfied by a fixer that does nothing at all; beside four rows that require
    detection and rewriting, it states that the fixer is idle only when there is nothing to do.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    #: (case, the committed file content, kwargs for `fix_working_tree`, expected `changed` list,
    #: the rule name that must appear in `unfixable` or "" for none, a substring the file MUST
    #: contain afterwards, a substring the file must NOT contain afterwards, why this row exists)
    FIXES = (
        (
            "a home path with --yes",
            "path is /home/" + "fixuser" + "/proj/file here\n",
            {"assume_yes": True},
            ["a.md"],
            "",
            "~/proj/file",
            "fixuser",
            "THE CONTROL AND THE HAPPY PATH: a home-style path is the one leak class with a safe "
            "portable rewrite, so `--fix` must actually perform it. The row asserts the TAIL "
            "SURVIVES (`~/proj/file`, not a bare `~`), because a rewrite that discarded the path "
            "tail would destroy the document's meaning while passing a 'no leak remains' check",
        ),
        (
            "the same leak in DRY RUN",
            "/home/" + "dryuser" + "/x\n",
            {"dry_run": True},
            ["a.md"],
            "",
            "dryuser",
            "",
            "DRY RUN MUST REPORT WITHOUT WRITING, and this row is only meaningful because it "
            "asserts BOTH halves: the file is listed in `changed` AND the leak is still on disk. "
            "Asserting the return value alone would make this row indistinguishable from the "
            "`--yes` row above. This is the mode a human uses to see what would happen, so a dry "
            "run that wrote would be a silent unrequested edit",
        ),
        (
            "interactive consent DECLINED",
            "/home/" + "declineuser" + "/x\n",
            {"assume_yes": False, "confirm": lambda rel, preview: False},
            [],
            "",
            "declineuser",
            "",
            "NO MEANS NO: declining must leave both the file and the `changed` list untouched. "
            "Note this differs from dry run, which still REPORTS the file; a decline records that "
            "the human looked and said no, so reporting it as changed would misrepresent their "
            "answer",
        ),
        (
            "interactive consent GRANTED",
            "/home/" + "acceptuser" + "/x\n",
            {"assume_yes": False, "confirm": lambda rel, preview: True},
            ["a.md"],
            "",
            "~/x",
            "acceptuser",
            "THE CONTROL FOR THE DECLINED ROW: without it, a `confirm` callback that was never "
            "consulted at all would satisfy the decline row perfectly (nothing changed, nothing "
            "reported). The two rows differ ONLY in what the callback returns, so together they "
            "prove the answer is actually read",
        ),
        (
            "a private-repo identity token with --yes",
            "see " + ls._R1 + " repo\n",
            {"assume_yes": True},
            [],
            "private-repo",
            ls._R1,
            "",
            "WHAT MUST NOT BE GUESSED: an identity token has no safe generic replacement, so "
            "`--fix` must REPORT it (in `unfixable`, naming the rule) and leave the bytes alone "
            "even under `--yes`. A fixer that invented a substitute would change the document's "
            "meaning; one that silently skipped it without reporting would let the leak ship "
            "while claiming the tree was fixed",
        ),
        (
            "a tree with nothing to fix",
            "nothing to see here\n",
            {"assume_yes": True},
            [],
            "",
            "nothing to see here",
            "",
            "THE IDLE ROW: a clean tree must produce no changes and no unfixable reports, so "
            "`--fix` cannot be run defensively-but-destructively. It is evidence only because of "
            "the rewriting rows above; alone it is satisfied by a fixer that does nothing",
        ),
    )

    def test_fix_rewrites_reports_or_refrains_according_to_mode_and_leak_class(self):
        wrong = []
        rewriting_controls_broken = False
        for (
            case,
            content,
            kwargs,
            expect_changed,
            unfixable_rule,
            must_contain,
            must_not_contain,
            why,
        ) in self.FIXES:
            repo = _init_repo(Path(self._tmp.name) / f"r{abs(hash(case))}")
            _commit(repo, "a.md", content, "add")
            changed, unfixable = ls.fix_working_tree(repo, **kwargs)
            after = (repo / "a.md").read_text(encoding="utf-8")
            problems = []
            if changed != expect_changed:
                if expect_changed and not changed:
                    rewriting_controls_broken = True
                problems.append(f"expected changed={expect_changed!r}, got {changed!r}")
            if unfixable_rule:
                if not any(f.rule == unfixable_rule for f in unfixable):
                    problems.append(
                        f"expected an unfixable finding with rule {unfixable_rule!r}; got "
                        f"{[(f.rule, f.severity) for f in unfixable]!r}. An unrewritable leak that "
                        "is not reported ships silently"
                    )
            elif unfixable:
                problems.append(
                    f"expected NO unfixable findings; got "
                    f"{[(f.rule, f.severity) for f in unfixable]!r}"
                )
            if must_contain and must_contain not in after:
                problems.append(
                    f"the file must contain {must_contain!r} afterwards; it reads {after!r}"
                )
            if must_not_contain and must_not_contain in after:
                problems.append(
                    f"the leak token {must_not_contain!r} must be GONE from disk; the file still "
                    f"reads {after!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if rewriting_controls_broken:
            note = (
                " A ROW THAT MUST REWRITE REPORTED NO CHANGES AT ALL, so detection or rewriting is "
                "off entirely; while that is true the dry-run, declined and idle rows are vacuous, "
                "because a fixer that does nothing satisfies all three."
            )
        self.assertEqual(
            wrong,
            [],
            f"fix_working_tree mishandled {len(wrong)} of {len(self.FIXES)} cases.{note} Every row "
            "asserts the RETURN VALUE and the BYTES ON DISK, so which half failed names the defect: "
            "a wrong `changed` list with correct bytes means the reporting drifted from the action, "
            "and correct reporting with wrong bytes means a mode is writing when it must not (dry "
            "run, declined) or not writing when it must. FIX: never resolve the unfixable row by "
            "inventing a replacement for an identity token; reporting it for a human IS the "
            f"designed behavior.\n" + "\n".join(wrong),
        )


class AgentModeTests(unittest.TestCase):
    """`--agent`: one machine-readable record per run, with no human prose.

    ONE table replaces two tests (`test_agent_output_is_parseable_and_prose_free`,
    `test_agent_clean_tree_exit_zero`). Both committed a file, ran `ls.main([repo, "--agent"])`,
    parsed the first line as JSON, and asserted a few envelope fields; they differed only in
    whether the file contained a leak. THE TREE STATE IS THEREFORE A COLUMN.

    Why the table beats the two: this is a machine CONTRACT, consumed by agents that branch on
    `outcome` and read `diagnostics`, and the realistic regression is one field being renamed or
    dropped in one branch only. Two tests report that as a lone KeyError in whichever branch
    changed; the table reports every field that moved in both branches at once, and pins the
    envelope (`schema`, `cmd`) identically for both states so a clean run and a dirty run cannot
    drift into two different shapes.

    THE LEAK ROW IS THE CONTROL FOR THE CLEAN ROW, and it is stricter than the test it replaces:
    it requires the exit code, the `findings` count, and the diagnostic's `location` AND `rule`, so
    a `--agent` mode that reported `outcome: findings` with an empty diagnostics array (telling an
    agent something is wrong but not what) fails here.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    @staticmethod
    def _run_main(argv):
        import contextlib

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ls.main(argv)
        return code, out.getvalue()

    #: (case, the committed content, expected exit code, expected `outcome`, expected `findings`
    #: count, the expected first diagnostic as (location, rule) or None, why this row exists)
    STATES = (
        (
            "a tree containing one home-path leak",
            "/home/" + "agentuser" + "/x\n",
            1,
            "findings",
            1,
            ("a.md:1", "home-path"),
            "THE CONTROL ROW: it is the only row that can prove the scanner ran, and it pins the "
            "DIAGNOSTIC rather than just the outcome. An agent that receives `outcome: findings` "
            "with no location or rule cannot act, so an empty diagnostics array is a failure even "
            "though the outcome field is correct. `location` carries the LINE NUMBER too, which is "
            "what makes the report actionable",
        ),
        (
            "a clean tree",
            "nothing\n",
            0,
            "clean",
            0,
            None,
            "THE CLEAN ROW: exit 0 and an explicit `clean` outcome, so a consuming agent can tell "
            "'scanned, nothing found' from 'did not scan'. It is evidence only because of the row "
            "above; on its own a `--agent` mode hardcoded to print `clean` would satisfy it",
        ),
    )

    def test_the_agent_envelope_is_identical_in_shape_for_both_tree_states(self):
        wrong = []
        control_broken = False
        for case, content, expect_code, outcome, count, diag, why in self.STATES:
            repo = _init_repo(Path(self._tmp.name) / f"r{abs(hash(case))}")
            _commit(repo, "a.md", content, "add")
            code, text = self._run_main([str(repo), "--agent"])
            problems = []
            lines = [ln for ln in text.splitlines() if ln.strip()]
            if not lines:
                problems.append("expected at least one output line; got nothing")
                rec = {}
            else:
                try:
                    rec = json.loads(lines[0])
                except json.JSONDecodeError as exc:
                    problems.append(
                        f"the first line must be parseable JSON; {exc} in {lines[0]!r}"
                    )
                    rec = {}
            if code != expect_code:
                if expect_code == 1:
                    control_broken = True
                problems.append(f"expected exit {expect_code}, got {code}")
            for key, expected in (
                ("schema", "aw.agent/v1"),
                ("cmd", "check-local-leaks"),
                ("outcome", outcome),
                ("findings", count),
            ):
                if rec.get(key) != expected:
                    if key in ("outcome", "findings") and expect_code == 1:
                        control_broken = True
                    problems.append(
                        f"record[{key!r}] must be {expected!r}; got {rec.get(key)!r}"
                    )
            if diag is not None:
                diags = rec.get("diagnostics") or []
                if not diags:
                    control_broken = True
                    problems.append(
                        "a findings record must carry diagnostics; the array was empty, so a "
                        "consuming agent is told something is wrong but not what"
                    )
                else:
                    got = (diags[0].get("location"), diags[0].get("rule"))
                    if got != diag:
                        problems.append(
                            f"the first diagnostic must be {diag!r} (path:line and rule); got "
                            f"{got!r}"
                        )
            # The human prose footer belongs to the default renderer, never to --agent output.
            if "Remove or abstract" in text:
                problems.append(
                    "human prose leaked into --agent output, which breaks line-oriented parsing: "
                    f"{text!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if control_broken:
            note = (
                " THE LEAK ROW FAILED, so `--agent` is not reporting findings and the clean row is "
                "vacuous: a mode hardcoded to print `clean` and exit 0 satisfies it."
            )
        self.assertEqual(
            wrong,
            [],
            f"the --agent envelope mishandled {len(wrong)} of {len(self.STATES)} tree states.{note} "
            "Both rows come out of one renderer, so BOTH failing on the same field means the "
            "envelope schema changed for every consumer at once, while one row failing means the "
            "branch for that outcome drifted. FIX: `schema` and `cmd` are how a consumer recognizes "
            "the record at all, and `diagnostics[].rule` is what it acts on; renaming any of them "
            f"is a breaking change to every agent reading this output.\n"
            + "\n".join(wrong),
        )


class RuleTierTests(unittest.TestCase):
    """The config-gated rule tiers: the IP ruleset (off by default) and the hostname severity.

    ONE table replaces four tests across two classes (`IpRulesetTests.test_ip_off_by_default`,
    `test_ip_opt_in_flags_ipv4`, `test_loopback_and_private_never_flagged_even_when_enabled`,
    `HostnameTierTests.test_hostname_warn_only_by_default`). All four committed a config file and a
    content file into a throwaway repo and ran the working-tree scan; they differed only in the
    config and the content. So THE CONFIG IS A COLUMN and the expected SEVERITY is a column.

    Why the table beats the four, and this is the strongest case in the file: these rules form a
    three-valued outcome (silent / warn / fail) that CONFIG moves between, and no single-config
    test can state that config is what moved it. The old IP tests came closest and still could not
    distinguish "the opt-in worked" from "IP was always on", because the off-by-default test used a
    DIFFERENT repository from the opt-in test. Here the same content is scanned under both configs.

    THE SEVERITY DISTINCTION IS THE POINT, NOT AN ASIDE. `warn` is advisory and ships; `fail`
    blocks the gate. A hostname guess promoted to `fail` blocks contributors whose machine name
    happens to appear in prose, and an IP rule left on by default floods every repository that
    documents an address. Both are how a security feature gets switched off wholesale, so each row
    names the tier it expects.

    EVERY SILENT ROW HAS A FIRING SIBLING IN THIS SAME TEST. The loopback row (never flagged even
    with IP enabled) sits beside the routable row (flagged when enabled) under the SAME config, so
    a scanner that stopped applying the IP patterns cannot satisfy the loopback row quietly.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    #: A routable documentation-range address (RFC 5737 TEST-NET-3): safe to write here, and the
    #: pattern deliberately does not exempt it, because exempting doc ranges would let a real
    #: address hide behind one.
    ROUTABLE_IP = "203.0.113.7"

    #: (case, the allowlist TOML body or "" for no config, the committed content, the rule that
    #: must fire at `fail` or "" for none, the rule that must fire at `warn` or "" for none, why
    #: this row exists)
    TIERS = (
        (
            "a routable IPv4 with NO config",
            "",
            "server at " + ROUTABLE_IP + " online\n",
            "",
            "",
            "OFF BY DEFAULT: addresses are rarely identifying and often documentation, so an "
            "IP rule on by default would fire on almost every repository and get the whole gate "
            "disabled. This row is meaningful only because the next row scans the SAME content "
            "with the rule enabled and requires it to fire",
        ),
        (
            "the same routable IPv4 with ip_enabled = true",
            "ip_enabled = true\n",
            "server at " + ROUTABLE_IP + " online\n",
            "ipv4",
            "",
            "THE CONTROL FOR THE ROW ABOVE, and the opt-in half of the pair: identical content, "
            "one config line different. Together the two rows state that CONFIG moved the verdict, "
            "which neither could state alone. `fail` severity is asserted because an opt-in the "
            "operator deliberately enabled must actually block",
        ),
        (
            "loopback and RFC1918 private addresses WITH ip_enabled = true",
            "ip_enabled = true\n",
            "use 127.0.0.1 and 192.168.1.5\n",
            "",
            "",
            "PERMANENT EXEMPTIONS: `127.0.0.1` and `192.168.x.x` are in every config example and "
            "identify nobody, so they must stay silent even with the ruleset ON. This row shares "
            "its config with the firing row above, so a scanner that had stopped applying the IP "
            "patterns entirely cannot satisfy it quietly",
        ),
        (
            "an IPv6 address with ip_enabled = true",
            "ip_enabled = true\n",
            "host 2001:0db8:85a3:0000:0000:8a2e:0370:7334 up\n",
            "ipv6",
            "",
            "THE SECOND IP PATTERN: v6 is a separate regex, so a v4-only test says nothing about "
            "it. A repository that documents v6 endpoints is exactly the case the opt-in exists "
            "for, and a rule family that covered only half of it would be a false sense of "
            "coverage",
        ),
        (
            "a derived HOSTNAME token with no config",
            "",
            None,  # resolved in the loop: the machine's own derived hostname token
            "",
            "derived",
            "WARN, NEVER FAIL, BY DEFAULT: a hostname is a GUESS about what identifies you, and a "
            "guess must not block a commit. The row asserts BOTH directions of the tier - present "
            "among warns, absent from fails - because a promotion to `fail` would block every "
            "contributor whose machine name appears in prose",
        ),
        (
            "the same derived HOSTNAME token with hostname_fail = true",
            "hostname_fail = true\n",
            None,
            "hostname",
            "",
            "THE CONTROL FOR THE TIER ABOVE: the same token, one config line different, must now "
            "block. Without it, 'warn only' is satisfied by derivation that produced nothing at "
            "all. Note the rule NAME changes with the tier (`derived:` to `hostname:`), which is "
            "how the report tells an operator which tier fired",
        ),
    )

    def test_config_moves_each_rule_between_silent_warn_and_fail(self):
        wrong = []
        firing_controls_broken = []
        for case, cfg, content, fail_rule, warn_rule, why in self.TIERS:
            repo = _init_repo(Path(self._tmp.name) / f"r{abs(hash(case))}")
            if cfg:
                _commit(repo, ".agents/local-leaks-allowlist.toml", cfg, "cfg")
            if content is None:
                # The hostname rows need a token this machine actually derives; a literal cannot
                # work, and a token no source produces would make both rows vacuously silent.
                hosts = [
                    tok
                    for tok, reason in ls.derive_warn_tokens(repo).items()
                    if reason in ls._HOSTNAME_REASONS
                ]
                if not hosts:
                    self.skipTest(
                        "this environment derives no hostname token, so the hostname tier rows "
                        "cannot be exercised here"
                    )
                token = hosts[0]
                body = f"machine {token} here\n"
            else:
                token = ""
                body = content
            _commit(repo, "a.md", body, "add")
            fails, warns = ls.run(repo, include_warn=True)
            fail_names = [(f.rule, f.severity) for f in fails]
            warn_names = [(w.rule, w.severity) for w in warns]
            problems = []
            if fail_rule:
                if not any(r.startswith(fail_rule) for r, _ in fail_names):
                    firing_controls_broken.append(f"{fail_rule} (fail)")
                    problems.append(
                        f"expected a `fail` finding whose rule starts with {fail_rule!r}; fails "
                        f"were {fail_names or 'EMPTY, so nothing blocks'}"
                    )
            elif fail_names:
                relevant = (
                    [f for f in fail_names if token and token in str(f)]
                    if token
                    else fail_names
                )
                if relevant:
                    problems.append(
                        f"this configuration must produce NO `fail` findings; got {relevant!r}. A "
                        "rule firing at fail severity when it should be silent or advisory blocks "
                        "commits it has no business blocking"
                    )
            if warn_rule:
                if not any(r.startswith(warn_rule) for r, _ in warn_names):
                    firing_controls_broken.append(f"{warn_rule} (warn)")
                    problems.append(
                        f"expected a `warn` finding whose rule starts with {warn_rule!r}; warns "
                        f"were {warn_names or 'EMPTY, so the advisory channel produced nothing'}"
                    )
            if problems:
                wrong.append(
                    f"  {case} [config={cfg.strip() or 'none'}]:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if firing_controls_broken:
            note = (
                f" THE FIRING CONTROL ROW(S) FOR {firing_controls_broken!r} FAILED, so a rule tier "
                "produced nothing at all; while that is true every SILENT row in this table is "
                "vacuous, because a scanner that finds nothing satisfies them. Fix the firing rows "
                "first."
            )
        self.assertEqual(
            wrong,
            [],
            f"the rule tiers mishandled {len(wrong)} of {len(self.TIERS)} configurations.{note} The "
            "rows are PAIRS over identical content differing by one config line, so the failing "
            "half names the defect: the enabled half means `load_repo_config_bools` is not reading "
            "the file (check `resolve_allowlist_path`), and the default half means a rule is on "
            "when it should be off. FIX: the severity is not cosmetic. `warn` ships and `fail` "
            "blocks, so promoting a guessed token to `fail` blocks innocent commits and demoting a "
            f"real rule to `warn` publishes the leak.\n" + "\n".join(wrong),
        )


class BinaryAndStagedScanTests(unittest.TestCase):
    """The two scan surfaces a text-and-tracked-files scan would miss: binary blobs and the index.

    ONE table replaces two tests from two classes (`BinaryScanTests`,
    `StagedScanTests.test_staged_flags_only_staged_content`). Both planted the same `home-path`
    leak somewhere the ordinary working-tree scan does not reach and asserted the rule fired, so
    the SURFACE is a column.

    Why the table beats the two: these are both answers to "where else can a leak hide?", and
    reading them as one set is what makes the answer auditable. They also share the failure mode
    that matters - a scan that silently reads nothing (an unreadable zip entry, an empty diff) and
    therefore reports clean - so one message covering both is more useful than two.

    NEITHER ROW IS A CLEAN ASSERTION: both REQUIRE a planted rule to fire, so this table is its own
    control and cannot pass with detection off.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    #: (case, the surface to build, the rule that MUST fire, why this row exists)
    SURFACES = (
        (
            "a leak inside a NUL-laden binary blob in a wheel",
            "binary-wheel",
            "home-path",
            "E4: BINARY IS NOT A REASON TO SKIP. A compiled artifact, a pickle, or a stale build "
            "product can carry a path, and the wheel is what reaches PyPI. The engine decodes with "
            "`errors=replace` rather than bailing out, so a human decides; a scanner that skipped "
            "undecodable content would clear exactly the artifact that ships",
        ),
        (
            "a leak STAGED in the index but never committed",
            "staged-index",
            "home-path",
            "THE PRE-COMMIT SURFACE: the hook must judge what is ABOUT TO BE COMMITTED, which is "
            "the index, not HEAD. A staged-mode scan that read HEAD instead would clear every new "
            "leak at exactly the moment it could still be stopped for free, and the operator would "
            "see a passing hook",
        ),
    )

    def test_each_hidden_surface_is_actually_scanned(self):
        wrong = []
        for case, surface, rule, why in self.SURFACES:
            problems = []
            if surface == "binary-wheel":
                wheel = Path(self._tmp.name) / "pkg.whl"
                payload = b"\x00\x01binary /home/" + b"binuser" + b"/x\x00\n"
                with zipfile.ZipFile(wheel, "w") as z:
                    z.writestr("pkg/blob.bin", payload)
                fails, _ = ls.run(REPO_ROOT, wheel=wheel)
            else:
                repo = _init_repo(Path(self._tmp.name) / "staged")
                _commit(repo, "a.md", "clean\n", "add")
                (repo / "a.md").write_text(
                    "/home/" + "staged" + "/x\n", encoding="utf-8"
                )
                subprocess.run(["git", "-C", str(repo), "add", "a.md"], check=True)
                fails, _ = ls.run(repo, staged=True)
            reported = [(f.rule, f.severity) for f in fails]
            if not any(r == rule for r, _ in reported):
                problems.append(
                    f"expected {rule!r} to fire on this surface; got "
                    f"{reported or 'NOTHING AT ALL, so this surface is not being read'}"
                )
            if problems:
                wrong.append(
                    f"  {case} [{surface}]:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SURFACES)} hidden scan surfaces reported nothing. Both rows "
            "plant the SAME rule through different readers, so BOTH failing means `scan_text` or "
            "the `home-path` pattern broke (shared), while one failing means that surface's reader "
            "did (the zip walk, or the `git diff --cached` invocation). FIX: the characteristic "
            "failure here is reading NOTHING and reporting clean, which looks identical to success; "
            "check that the reader actually produced bytes before concluding the pattern is at "
            f"fault.\n" + "\n".join(wrong),
        )


class TomlParserTests(unittest.TestCase):
    """Characterization + C4 regression for the minimal TOML list parser (IPD 20260721-1851-01).

    Step 0 hardened `_parse_simple_toml_lists` so a `]` (or the other quote char) inside a
    quoted string is not mistaken for structure. These pin both the pre-existing valid shapes
    and the bug class the wizard depends on.

    ONE table replaces eight tests. Every one called `_parse_simple_toml_lists` on a literal string
    and compared the whole returned dict, so they differed ONLY in data: input text in, expected
    mapping out. The old split (five "characterization" methods then three "C4 regression" methods)
    recorded WHEN each case was added, which is history rather than a property of the parser.

    Why the table beats the eight: this parser exists because the support floor is Python 3.9 and
    `tomllib` is 3.11+, so it is a hand-rolled reader of a format people already believe they
    understand, and its whole risk surface is which shapes it accepts. As a table that surface is
    readable in one screen, and a regression in the quote-scanning state machine (which decides
    almost every row) reports as one failure listing every shape it broke rather than as eight
    unrelated equality errors.

    THE BRACKET ROWS ARE LOAD-BEARING, NOT EDGE CASES. `fail_patterns` holds REGEXES, so a
    character class like `[a-z]` is normal input; the pre-hardening parser truncated such a value
    to `[]`, which silently DISABLED a user's custom leak pattern. A config that quietly stops
    matching is worse than one that errors, because the operator keeps believing they are covered.
    """

    #: (case, the TOML text, the exact expected mapping, why this row exists)
    SHAPES = (
        (
            "an empty array",
            "allow_line_substrings = []",
            {"allow_line_substrings": []},
            "CHARACTERIZATION: the shape a freshly written config has. It must parse to a present "
            "key with an empty list, not a missing key, because callers distinguish 'configured "
            "empty' from 'unconfigured'",
        ),
        (
            "two values on one line",
            'fail_patterns = ["a", "b"]',
            {"fail_patterns": ["a", "b"]},
            "CHARACTERIZATION: the ordinary inline array, and the baseline the bracket rows below "
            "are compared against. If this row breaks, every config in existence stops loading",
        ),
        (
            "an array spanning several lines with a trailing comma",
            'fail_patterns = [\n  "a",\n  "b",\n]',
            {"fail_patterns": ["a", "b"]},
            "CHARACTERIZATION: this is the shape the WRITER emits for readability, so the reader "
            "and the writer would disagree about the repository's own config file if this broke - "
            "the round trip in `ConfigWriterTests` depends on it",
        ),
        (
            "a commented-out key",
            '# fail_patterns = ["x"]',
            {},
            "A COMMENT IS NOT CONFIG. Hand-edited allowlists are full of commented examples, and a "
            "parser that read them would silently activate patterns the operator deliberately "
            "disabled",
        ),
        (
            "a boolean line",
            "ip_enabled = true",
            {},
            "SEPARATION OF READERS: booleans belong to `_parse_simple_toml_bools`, so the LIST "
            "reader must ignore them rather than coercing `true` into a one-element list. Returning "
            "`{'ip_enabled': ['true']}` here would silently register a junk pattern",
        ),
        (
            "a regex character class inside a value",
            'fail_patterns = ["/home/[a-z]+/x"]',
            {"fail_patterns": ["/home/[a-z]+/x"]},
            "THE C4 REGRESSION, AND THE REASON THE PARSER WAS HARDENED: `fail_patterns` holds "
            "REGEXES, so `[a-z]` is normal input. The old parser saw the inner `]` as the array "
            "terminator and truncated the value to `[]`, silently DISABLING a user's custom leak "
            "rule. A config that stops matching without saying so is the worst failure mode in "
            "this file, because the operator still believes they are covered",
        ),
        (
            "a bracketed phrase inside an allowlist substring",
            'allow_line_substrings = ["see [docs]"]',
            {"allow_line_substrings": ["see [docs]"]},
            "THE SAME BUG CLASS ON THE OTHER KEY, and with prose rather than a regex: markdown link "
            "text is a perfectly ordinary allowlist substring. Truncating it would UN-EXEMPT lines "
            "the operator allowlisted, which flips the error to a false positive; both directions "
            "of the same parser bug matter",
        ),
        (
            "a double-quoted value containing a single quote",
            'allow_line_substrings = ["it' + chr(39) + 's fine"]',
            {"allow_line_substrings": ["it" + chr(39) + "s fine"]},
            "THE DUAL-QUOTE-SELECT CONTRACT (OQ4): there is no escape syntax, so the writer picks "
            "the delimiter that avoids embedding itself and the reader must honor the other quote "
            "as ordinary text. This row is the reader's half of the deal that "
            "`ConfigWriterTests.test_value_with_one_quote_uses_other_delimiter` completes",
        ),
    )

    def test_every_supported_toml_shape_parses_to_exactly_its_mapping(self):
        wrong = []
        for case, text, expected, why in self.SHAPES:
            got = ls._parse_simple_toml_lists(text)
            if got != expected:
                wrong.append(
                    f"  {case}:\n"
                    f"    - parsed {text!r}\n"
                    f"      expected {expected!r}\n"
                    f"      got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"_parse_simple_toml_lists mishandled {len(wrong)} of {len(self.SHAPES)} shapes. Almost "
            "every row is decided by the same quote-scanning state machine, so SEVERAL ROWS FAILING "
            "TOGETHER means that scanner regressed rather than several shapes being independently "
            "wrong; in particular a bracket row plus a quote row failing together is the signature "
            "of the pre-hardening behavior returning. FIX: the dangerous direction is TRUNCATION to "
            "`[]`, because it silently disables a user's own leak pattern while the config still "
            f"looks correct on disk.\n" + "\n".join(wrong),
        )


class ConfigWriterTests(unittest.TestCase):
    """Round-trip + rejection for the config writers (IPD 20260721-1851-01 CP1).

    ONE table replaces three of the five tests here (`test_repo_allowlist_round_trips_including_brackets`,
    `test_empty_lists_round_trip`, `test_value_with_one_quote_uses_other_delimiter`). All three
    wrote a repo allowlist and read it back, differing only in the values written, so the values
    are the data and the assertion (read-back equals written) is identical.

    Why the table beats the three: the property is a ROUND TRIP, and the risk is a value class that
    survives the writer but not the reader (or vice versa). The values chosen are precisely the
    ones that broke historically - brackets, quotes, empties - and reading them as one set makes
    the writer's contract legible: any value the writer accepts must read back byte-identical.
    Seeing them apart invites adding a fourth quirky value without noticing it belongs to a family.

    THE BOOLEANS RIDE ALONG IN ONE ROW because they go through a different reader
    (`load_repo_config_bools`) on the same file: a writer that emitted the lists correctly while
    corrupting the `[ip]`/`[rules]` toggles would pass a lists-only round trip and silently change
    which RULE TIERS are active, which is the security-relevant half of this file.

    The rejection test stays separate (it asserts a RAISE plus a no-write side effect), and so does
    the user-hints test (different destination, and the assertion is about WHERE the file landed).
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "r"
        self.repo.mkdir(parents=True)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")
        self.addCleanup(self._restore_xdg)

    def _restore_xdg(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg

    QUOTE_AND_BRACKET = "it" + chr(39) + "s a /home/[x]/p"

    #: (case, allow_line_substrings written, fail_patterns written, ip_enabled, hostname_fail, why
    #: this row exists)
    ROUND_TRIPS = (
        (
            "bracketed prose, regex character classes, and both toggles set differently",
            ["see [docs]", "MY-OK"],
            ["/home/[a-z]+/x", "ses_[0-9A-Za-z]{8,}"],
            True,
            False,
            "THE FULL-FIDELITY ROW: every value class that broke historically at once (a bracketed "
            "phrase, a regex character class, a quantifier with braces) PLUS the two booleans, "
            "which are read by a DIFFERENT reader from the same file. The toggles are set to "
            "OPPOSITE values on purpose, so a writer that emitted a constant, or swapped them, "
            "cannot pass; they decide which rule tiers are active, so corrupting them silently "
            "changes what the scanner looks for",
        ),
        (
            "both lists empty",
            [],
            [],
            False,
            False,
            "EMPTY IS A VALUE, NOT AN ABSENCE: the keys must come back present and empty, because "
            "callers distinguish 'configured empty' from 'never configured'. A writer that omitted "
            "empty keys would make the first `--fix` or wizard run look unconfigured again",
        ),
        (
            "a value containing BOTH a single quote and a bracket",
            [QUOTE_AND_BRACKET],
            [],
            False,
            False,
            "THE DUAL-QUOTE-SELECT CONTRACT (OQ4), writer half: with no escape syntax the writer "
            "must pick the delimiter that avoids embedding its own quote, and the value must still "
            "read back byte-identical. It combines a quote with a bracket so the delimiter choice "
            "and the array-terminator scan are both exercised by one value",
        ),
    )

    def test_every_value_class_round_trips_through_write_and_load(self):
        wrong = []
        for case, allow, patterns, ip_enabled, hostname_fail, why in self.ROUND_TRIPS:
            # A fresh directory per row so a previous row's file cannot satisfy this one.
            repo = self.repo / f"cfg{abs(hash(case))}"
            repo.mkdir(parents=True, exist_ok=True)
            ls.write_repo_allowlist(
                repo,
                allow_line_substrings=allow,
                fail_patterns=patterns,
                ip_enabled=ip_enabled,
                hostname_fail=hostname_fail,
            )
            lists = ls.load_repo_allowlist(repo)
            bools = ls.load_repo_config_bools(repo)
            problems = []
            if lists.get("allow_line_substrings") != allow:
                problems.append(
                    f"allow_line_substrings wrote {allow!r} and read back "
                    f"{lists.get('allow_line_substrings')!r}"
                )
            if lists.get("fail_patterns") != patterns:
                problems.append(
                    f"fail_patterns wrote {patterns!r} and read back "
                    f"{lists.get('fail_patterns')!r}"
                )
            for key, expected in (
                ("ip_enabled", ip_enabled),
                ("hostname_fail", hostname_fail),
            ):
                if bools.get(key) != expected:
                    problems.append(
                        f"{key} wrote {expected!r} and read back {bools.get(key)!r}; this toggle "
                        "decides whether a whole rule tier is active"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the repo-allowlist round trip mishandled {len(wrong)} of {len(self.ROUND_TRIPS)} value "
            "sets. Writer and reader are two halves of one contract, so the failure pattern names "
            "the half: a LIST mismatch on a bracketed or quoted value points at the same "
            "quote-scanning code `TomlParserTests` covers (check there first, since it isolates the "
            "reader), while a BOOLEAN mismatch points at the writer's section emission, which no "
            "reader test would catch. FIX: a value that does not survive the round trip is a rule "
            f"the operator believes is active and is not.\n" + "\n".join(wrong),
        )

    def test_value_with_both_quotes_is_rejected_before_writing(self):
        """Kept separate: asserts a RAISE plus the absence of a side effect.

        The round-trip table asserts equality after a successful write; this asserts that an
        unwritable value (containing both quote chars, which the escape-free format cannot
        represent) is refused BEFORE the atomic write, leaving no file behind. Different assertion
        shape and a negative side-effect check, so it is not a row.
        """
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
        """Kept separate: the claim is WHERE the file lands, not what round-trips.

        Personal hints must never be committed, so this asserts the file appears under the user
        config dir AND is absent from the repo tree. That destination assertion has no analogue in
        the repo-allowlist rows, and folding it in would hide the one thing it exists to check.
        """
        ls.write_user_hints(tokens=["MyCodename"], patterns=["/srv/[a-z]+/private"])
        hints = ls.load_user_hints()
        self.assertEqual(hints.get("tokens"), ["MyCodename"])
        self.assertEqual(hints.get("patterns"), ["/srv/[a-z]+/private"])
        # It must NOT be written into the repo tree.
        self.assertFalse((self.repo / ls.USER_HINTS_FILENAME).exists())
        self.assertTrue((ls._config_dir() / ls.USER_HINTS_FILENAME).is_file())


class WizardCoreTests(unittest.TestCase):
    """The interactive wizard core via injected prompt/confirm (IPD 20260721-1851-01 CP2).

    ONE table replaces six tests. Every one drove `leak_sanitizer_config.configure` with a list of
    canned prompt answers and a list of canned confirm answers, then checked the returned summary
    and what landed on disk. The answers ARE the data, so they are columns: the prompt script, the
    confirm script, and the expected destination.

    Why the table beats the six: the wizard's contract is that NOTHING is written without the final
    confirmation and that each answer lands in the right FILE, and that contract is only visible by
    comparing rows. The declined row and the written rows differ solely in the last confirm answer,
    so together they state that the confirmation is actually read; apart, a wizard that ignored the
    final answer and wrote nothing at all would pass the declined test and fail the others with
    unrelated messages.

    THE DESTINATION COLUMN CARRIES A PRIVACY RULE, not just a path. A personal token must land in
    the USER config dir and never in the repository, because the repo allowlist is committed and
    travels; the row that adds a token therefore asserts both the presence in the hints file and
    the ABSENCE from the repo tree. That is the one row whose failure would publish something.

    THE NO-CHANGE ROW IS THE CONTROL FOR THE DECLINED ROW. Both end with nothing written, but for
    different reasons: the declined row must still report a computed `changed` diff (the wizard knew
    what it would have done and was told no), while the no-change row must report no diff at all. A
    wizard that computed nothing would satisfy the declined row's empty `wrote` list while being
    thoroughly broken.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "r"
        self.repo.mkdir(parents=True)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")
        self.addCleanup(self._restore_xdg)
        from agent_workflows import leak_sanitizer_config as lsc

        self.lsc = lsc

    def _restore_xdg(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg

    def _run(self, repo, prompt_answers, confirm_answers):
        pa = iter(prompt_answers)
        ca = iter(confirm_answers)
        return self.lsc.configure(
            repo,
            prompt=lambda q: next(pa, ""),
            confirm=lambda q: next(ca, False),
            emit=lambda line: None,
        )

    #: (case, prompt answers in order (allow_line_substrings loop, fail_patterns loop, tokens loop,
    #: patterns loop), confirm answers (ip toggle, hostname toggle, final write), expected
    #: `changed`, whether anything must be WRITTEN, expected repo-allowlist state as
    #: {key: value} to verify or None, expected hints tokens or None, why this row exists)
    SESSIONS = (
        (
            "adding one allowlist substring and confirming the write",
            ["PUBLIC-OK", "", "", "", ""],
            [False, False, True],
            True,
            True,
            {"allow_line_substrings": ["PUBLIC-OK"]},
            None,
            "THE BASELINE WRITE: a value typed at the prompt must reach the COMMITTED repo "
            "allowlist, which is how a team declares a string public-OK-here. Every 'nothing was "
            "written' row below is vacuous while this one is broken, because a wizard that never "
            "writes satisfies them all",
        ),
        (
            "flipping the ip toggle on",
            ["", "", "", ""],
            [True, False, True],
            True,
            True,
            {"ip_enabled": True},
            None,
            "A CONFIRM ANSWER DRIVES A BOOLEAN, not just a list, and it goes through a different "
            "writer path and a different reader (`load_repo_config_bools`). This toggle switches a "
            "whole rule tier on, so the wizard getting it wrong changes what the scanner looks for "
            "rather than merely what it ignores",
        ),
        (
            "adding a personal token",
            ["", "", "MyCodename", ""],
            [False, False, True],
            True,
            True,
            None,
            ["MyCodename"],
            "THE PRIVACY ROW: a personal token must land in the USER config dir and MUST NOT appear "
            "in the repo tree, because the repo allowlist is committed and would publish the very "
            "codename the hint exists to detect. This is the only row here whose failure leaks "
            "something",
        ),
        (
            "declining the final write after making a change",
            ["PUBLIC-OK", "", "", ""],
            [False, False, False],
            True,
            False,
            None,
            None,
            "NO MEANS NO, AND IT IS NOT THE SAME AS NOTHING TO DO: `changed` must still be True "
            "(the wizard computed a diff and offered it) while `wrote` is empty and no file exists. "
            "Contrast the row below, where `changed` is False. A wizard that computed nothing would "
            "satisfy the empty `wrote` half of this row while being useless",
        ),
        (
            "a session that changes nothing",
            ["", "", "", ""],
            [False, False],
            False,
            False,
            None,
            None,
            "THE CONTROL FOR THE DECLINED ROW: with everything blank and both toggles already off "
            "there is no diff, so `changed` must be False and no final confirmation should even be "
            "needed (only two confirm answers are supplied, and the wizard must not block waiting "
            "for a third). The pair distinguishes 'nothing to do' from 'told not to'",
        ),
        (
            "adding a regex character-class fail pattern",
            ["", "/home/[a-z]+/secret", "", ""],
            [False, False, True],
            True,
            True,
            {"fail_patterns": ["/home/[a-z]+/secret"]},
            None,
            "THE C4 REGRESSION END TO END: a bracketed regex typed at the prompt must survive the "
            "writer AND the reader. `TomlParserTests` covers the reader in isolation and "
            "`ConfigWriterTests` the round trip; this row proves the WIZARD path does not mangle it "
            "on the way in, which is where a real user's custom leak rule would be lost",
        ),
    )

    def test_the_wizard_writes_only_what_was_confirmed_and_only_where_it_belongs(self):
        wrong = []
        writing_controls_broken = False
        for (
            case,
            prompts,
            confirms,
            expect_changed,
            expect_wrote,
            repo_state,
            hint_tokens,
            why,
        ) in self.SESSIONS:
            repo = Path(self._tmp.name) / f"r{abs(hash(case))}"
            repo.mkdir(parents=True, exist_ok=True)
            hints_file = ls._config_dir() / ls.USER_HINTS_FILENAME
            if hints_file.exists():
                hints_file.unlink()
            summary = self._run(repo, prompts, confirms)
            problems = []
            if bool(summary["changed"]) != expect_changed:
                problems.append(
                    f"expected changed={expect_changed}, got {summary['changed']!r} (diff was "
                    f"{summary.get('diff')!r})"
                )
            wrote = summary["wrote"]
            if expect_wrote and not wrote:
                writing_controls_broken = True
                problems.append(
                    f"expected the confirmed write to happen; `wrote` was {wrote!r}"
                )
            if not expect_wrote and wrote:
                problems.append(
                    f"nothing may be written here; `wrote` was {wrote!r}. The wizard acted without "
                    "the confirmation it is required to obtain"
                )
            if not expect_wrote and (repo / ls.REPO_ALLOWLIST_REL).exists():
                problems.append(
                    "no config file may exist on disk for this session; "
                    f"{ls.REPO_ALLOWLIST_REL} was created anyway"
                )
            for key, expected in (repo_state or {}).items():
                got = (
                    ls.load_repo_allowlist(repo).get(key)
                    if isinstance(expected, list)
                    else ls.load_repo_config_bools(repo).get(key)
                )
                if got != expected:
                    problems.append(
                        f"repo config {key!r}: expected {expected!r}, got {got!r}"
                    )
            if hint_tokens is not None:
                got_tokens = ls.load_user_hints().get("tokens")
                if got_tokens != hint_tokens:
                    problems.append(
                        f"user hints tokens: expected {hint_tokens!r}, got {got_tokens!r}"
                    )
                if (repo / ls.USER_HINTS_FILENAME).exists():
                    problems.append(
                        "PRIVACY BREACH: the personal hints file was written INTO THE REPO TREE, "
                        "where it would be committed and would publish the token it exists to "
                        "detect"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if writing_controls_broken:
            note = (
                " A ROW THAT MUST WRITE DID NOT, so the wizard is writing nothing at all; while "
                "that is true the declined and no-change rows are vacuous, because a wizard that "
                "never writes satisfies both."
            )
        self.assertEqual(
            wrong,
            [],
            f"the wizard mishandled {len(wrong)} of {len(self.SESSIONS)} sessions.{note} The rows "
            "differ only in the canned answers, so the pattern names the defect: every writing row "
            "failing means the write path or the final confirm broke, the no-write rows failing "
            "means the confirmation is being ignored (which is the serious direction, since the "
            "wizard then edits config nobody approved), and the token row failing on DESTINATION "
            "means a personal hint is landing somewhere it would be committed. FIX: `changed` and "
            "`wrote` are deliberately different signals; do not collapse them to make a row pass.\n"
            + "\n".join(wrong),
        )


class ConfigReconciliationTests(unittest.TestCase):
    """PR-003: ONE canonical allowlist location, with a bounded legacy fallback.

    ONE table replaces the resolver test's four inline stages (`test_e04_...resolver_prefers_aw_config_falls_back_to_legacy`),
    which walked one temp directory through four states with four bare `assertEqual`s. As a
    sequence, a failure at stage two hid stages three and four and the message said only that two
    paths differed. As a table each state is named, each carries the rule it encodes, and all four
    are reported together - and each row now builds its own directory, so the rows are independent
    rather than order-dependent.

    WHY THE ORDER MATTERED AND NOW DOES NOT: the old test relied on files created by earlier stages
    still existing, so inserting a stage in the middle silently changed the meaning of every stage
    after it. The table states each precondition explicitly (which of the two files exist), which
    is also the only way to read the resolver's precedence rule as a rule.

    The two module-surface tests stay separate: one asserts re-exported IDENTITY, the other scans
    THIS repository for a competing config file.
    """

    #: (case, which config files exist ("none" | "legacy" | "new" | "both"), the expected resolved
    #: location ("new" | "legacy"), why this row exists)
    RESOLUTIONS = (
        (
            "neither file exists",
            "none",
            "new",
            "THE CREATE DEFAULT: a fresh repo must be steered to `.aw/config/`, never to the legacy "
            "path, or every new repository would be born un-migrated and the migration would never "
            "finish",
        ),
        (
            "only the legacy .agents/ file exists",
            "legacy",
            "legacy",
            "BOUNDED BACKWARD COMPATIBILITY: an un-migrated repo's existing allowlist must keep "
            "being honored, because silently ignoring it would turn every entry the operator "
            "justified into a fresh gate failure - or worse, re-enable a rule they had exempted",
        ),
        (
            "only the new .aw/config/ file exists",
            "new",
            "new",
            "THE MIGRATED STEADY STATE, and the control that the legacy row is a FALLBACK rather "
            "than a preference: without it, a resolver that always returned the legacy path would "
            "satisfy both rows above",
        ),
        (
            "BOTH files exist",
            "both",
            "new",
            "PRECEDENCE, which is the whole point of having one resolver: during a migration both "
            "files exist, and if different call sites disagreed about which wins, a rule would be "
            "active for the hook and inactive for CI. The new location must win",
        ),
    )

    NEW_REL = (".aw", "config", "local-leaks-allowlist.toml")
    LEGACY_REL = (".agents", "local-leaks-allowlist.toml")

    def test_the_resolver_picks_one_location_from_every_combination_present(self):
        wrong = []
        with tempfile.TemporaryDirectory() as d:
            for case, present, expect, why in self.RESOLUTIONS:
                repo = Path(d) / f"r-{present}"
                repo.mkdir(parents=True, exist_ok=True)
                new = repo.joinpath(*self.NEW_REL)
                legacy = repo.joinpath(*self.LEGACY_REL)
                for path, want in (
                    (new, present in ("new", "both")),
                    (legacy, present in ("legacy", "both")),
                ):
                    if want:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(
                            "allow_line_substrings = []\n", encoding="utf-8"
                        )
                expected = new if expect == "new" else legacy
                got = ls.resolve_allowlist_path(repo)
                problems = []
                if got != expected:
                    problems.append(f"expected {expected}, got {got}")
                # The loader must route through the resolver, or the resolution above is academic:
                # a loader reading a hardcoded path would make the legacy row's file unread.
                if present in ("legacy", "new", "both"):
                    loaded = ls.load_repo_allowlist(repo)
                    if "allow_line_substrings" not in loaded:
                        problems.append(
                            "load_repo_allowlist did not read the resolved file (key "
                            f"'allow_line_substrings' absent from {loaded!r}), so the resolver's "
                            "answer is not the one actually used"
                        )
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"resolve_allowlist_path mishandled {len(wrong)} of {len(self.RESOLUTIONS)} file "
            "combinations. One resolver exists so every read and write site agrees on one location, "
            "so the pattern names the defect: the `both` row alone failing means precedence "
            "inverted (the most dangerous case, because during a migration two call sites would "
            "read different rule sets), the `legacy` row alone means the fallback was dropped and "
            "existing allowlists stopped being honored, and the `none` row means new repos are "
            "being steered at the legacy path. FIX: also check the loader assertion in each row; a "
            "correct resolver whose answer nothing consults is no better than a wrong one.\n"
            + "\n".join(wrong),
        )

    def test_e04_local_leaks_reexports_resolver(self):
        """Kept separate: asserts MODULE IDENTITY of the re-exported surface, not a resolution.

        `local_leaks` is a compatibility shim, and the risk is it growing a SECOND copy of the
        resolver that drifts. `assertIs` on the function object is the only assertion that rules
        that out, and it has no data to vary.
        """
        from agent_workflows import local_leaks as legacy_mod

        self.assertEqual(legacy_mod.REPO_ALLOWLIST_REL, ls.REPO_ALLOWLIST_REL)
        self.assertEqual(
            legacy_mod.LEGACY_REPO_ALLOWLIST_REL, ls.LEGACY_REPO_ALLOWLIST_REL
        )
        self.assertIs(legacy_mod.resolve_allowlist_path, ls.resolve_allowlist_path)

    def test_one_canonical_tracked_config_no_competing_file(self):
        """Kept separate: the subject is THIS repository's own tree, not a fixture.

        PR-003 says there is ONE canonical tracked allowlist and NO competing allow file. The
        canonical location is now .aw/config/local-leaks-allowlist.toml with a bounded legacy
        fallback to .agents/local-leaks-allowlist.toml (until this repo is migrated), so resolve via
        the resolver rather than the raw new-location constant. A glob over the real tree cannot be
        a fixture row.
        """
        self.assertTrue(ls.resolve_allowlist_path(REPO_ROOT).is_file())
        stray = list(REPO_ROOT.glob(".agents/leak-sanitizer-allow*"))
        self.assertEqual(stray, [], f"competing config file present: {stray}")


if __name__ == "__main__":
    unittest.main()
