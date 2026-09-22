"""Tests for wkindname Order 01 (9trlc3): backlog's work-nature field renamed to `- Work-Kind:`.

The field was formerly spelled `- Kind:`, which collided with four unrelated uses of that token (an
IPD's structural kind, a research document type, a comms message kind, and backlog's own
`- Gate-Kind:`). This module covers the dual-read window (E-01), the write side plus the retained
`--kind` alias (E-02), the corpus migration (E-03), and the `backlog new` flag declaration (E-05).

Three tests here are load-bearing NEGATIVES, each written to fail against a specific plausible
mis-implementation:

* `test_legacy_spelling_still_parses` fails if someone accepts ONLY the new spelling, which would
  make a partially migrated tree, a long-lived branch, or a stash stop parsing.
* `test_absent_work_kind_is_still_rejected` fails if someone "unified" the field by making it
  OPTIONAL on backlog. The Set unified the field's NAME, not its requiredness: backlog requires it
  and plans/specs do not, and that asymmetry is the intended outcome.
* `test_gate_kind_is_a_distinct_field_and_is_never_rewritten` fails against a rename anchored on the
  bare token `Kind`, which would silently produce `- Gate-Work-Kind:` and break the gate contract.

Every case builds a THROWAWAY tree. The live `.aw/records/backlog/` is shared state that other
sessions mutate concurrently, so asserting against it would be flaky and could mask a real defect.
"""

from __future__ import annotations

import io
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import backlog, command_surface

REPO_ROOT = Path(__file__).resolve().parents[1]

# The canonical spelling, as written today.
NEW_ITEM = """- Id: {id6}
- Status: open
- Set: tst
- Priority: high
- Work-Kind: {kind}
- Summary: A test item.

## Workflow history
- 2026-08-30 created (test): A test item.

Body.
"""

# The legacy spelling, which the dual-read window must keep accepting.
OLD_ITEM = """- Id: {id6}
- Status: open
- Set: tst
- Priority: high
- Kind: {kind}
- Summary: A test item.

## Workflow history
- 2026-08-30 created (test): A test item.

Body.
"""

# No work-nature field at all: still an error, because backlog REQUIRES the field.
NO_KIND_ITEM = """- Id: {id6}
- Status: open
- Set: tst
- Priority: high
- Summary: A test item.

## Workflow history
- 2026-08-30 created (test): A test item.

Body.
"""

# A blocked item carrying the DISTINCT `- Gate-Kind:` field alongside the work-nature one.
GATE_ITEM = """- Id: {id6}
- Status: blocked
- Set: tst
- Priority: high
- Work-Kind: {kind}
- Summary: A test item.
- Gate-Kind: artifact
- Gate-Ref: abc123

## Workflow history
- 2026-08-30 created (test): A test item.

Body.
"""


def _write_item(root: Path, id6: str, template: str, kind: str = "feature") -> Path:
    """Write one item into a throwaway tree, in the status dir its own `- Status:` names."""

    text = template.format(id6=id6, kind=kind)
    status = "open"
    for line in text.split("\n"):
        if line.startswith("- Status:"):
            status = line.split(":", 1)[1].strip()
            break
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260830-tst-01-{id6}-a-test-item.backlog.md"
    p.write_text(text, encoding="utf-8")
    return p


def _rules(path: Path) -> list:
    """The drift rule ids `validate_item` reports for one item file."""

    return [
        d.rule for d in backlog.validate_item(path, path.read_text(encoding="utf-8"))
    ]


class DualReadTests(unittest.TestCase):
    """E-01: both spellings parse; the canonical one wins; the tree never stops parsing."""

    def test_canonical_spelling_parses(self):
        item = backlog.parse_item(NEW_ITEM.format(id6="aaa111", kind="bug"))
        self.assertEqual(item.kind, "bug")

    def test_legacy_spelling_still_parses(self):
        """LOAD-BEARING NEGATIVE: fails if only the new spelling is accepted.

        Without this, the instant the first item is converted the tree carries a spelling the parser
        rejects, and every concurrent reader sees a broken tree until the last item lands.
        """

        item = backlog.parse_item(OLD_ITEM.format(id6="aaa222", kind="bug"))
        self.assertEqual(item.kind, "bug")

    def test_canonical_spelling_wins_when_an_item_carries_both(self):
        """A half-merged item can carry both. The canonical value must win, whatever the line order."""

        both = """- Id: aaa333
- Status: open
- Set: tst
- Priority: high
- Kind: chore
- Work-Kind: security
- Summary: A test item.

## Workflow history
- 2026-08-30 created (test): A test item.
"""
        self.assertEqual(backlog.parse_item(both).kind, "security")
        # and with the lines the other way round, proving precedence is not line-order luck
        reordered = both.replace(
            "- Kind: chore\n- Work-Kind: security\n",
            "- Work-Kind: security\n- Kind: chore\n",
        )
        self.assertEqual(backlog.parse_item(reordered).kind, "security")

    def test_a_tree_containing_both_spellings_validates(self):
        """The exact midpoint state the migration passes through must be clean."""

        with TemporaryDirectory() as td:
            root = Path(td)
            legacy = _write_item(root, "bbb111", OLD_ITEM)
            canonical = _write_item(root, "bbb222", NEW_ITEM)
            self.assertEqual(_rules(legacy), [])
            self.assertEqual(_rules(canonical), [])
            # and no work-nature finding anywhere across the mixed tree
            found = []
            for f in backlog._iter_items(root):
                found.extend(_rules(f))
            self.assertNotIn("backlog.kind-invalid", found)
            self.assertEqual(found, [])

    def test_the_field_regexes_are_anchored_on_the_full_line(self):
        """A bare-token match would capture `- Gate-Kind:`; a full-line one cannot."""

        self.assertIsNone(backlog._WORK_KIND_RE.match("- Gate-Kind: artifact"))
        self.assertIsNone(backlog._KIND_RE.match("- Gate-Kind: artifact"))
        self.assertIsNotNone(backlog._WORK_KIND_RE.match("- Work-Kind: bug"))
        self.assertIsNotNone(backlog._KIND_RE.match("- Kind: bug"))
        # a `- Work-Kind:` line must not be read as the legacy field either
        self.assertIsNone(backlog._KIND_RE.match("- Work-Kind: bug"))


class WriteSideTests(unittest.TestCase):
    """E-02: only the canonical spelling is ever written, by every write path."""

    def test_render_item_writes_the_canonical_spelling(self):
        item = backlog.BacklogItem()
        item.id, item.status, item.set = "ccc111", "open", "tst"
        item.priority, item.kind, item.summary = "high", "feature", "A test item."
        rendered = backlog._render_item(item, "")
        self.assertIn("- Work-Kind: feature", rendered)
        self.assertNotRegex(rendered, r"(?m)^- Kind:")

    def test_a_newly_created_item_carries_the_canonical_spelling_on_disk(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "backlog").mkdir(parents=True)
            args = _NewArgs(dir=str(root), summary="A test item.", work_kind="security")
            self.assertEqual(backlog.run_new(args), 0)
            written = backlog._iter_items(root)
            self.assertEqual(len(written), 1)
            text = written[0].read_text(encoding="utf-8")
            self.assertIn("- Work-Kind: security", text)
            self.assertNotRegex(text, r"(?m)^- Kind:")

    def test_a_status_transition_rewrites_the_field_in_the_canonical_spelling(self):
        """`backlog set` re-renders the item, so a legacy item is migrated as a side effect."""

        with TemporaryDirectory() as td:
            root = Path(td)
            _write_item(root, "ccc222", OLD_ITEM)
            args = _SetArgs(dir=str(root), path="ccc222", status="done")
            self.assertEqual(backlog.run_set(args), 0)
            items = backlog._iter_items(root)
            self.assertEqual(len(items), 1)
            text = items[0].read_text(encoding="utf-8")
            self.assertIn("- Work-Kind: feature", text)
            self.assertNotRegex(text, r"(?m)^- Kind:")

    def test_the_module_docstring_documents_the_canonical_spelling(self):
        doc = backlog.__doc__ or ""
        self.assertIn("- Work-Kind:", doc)
        self.assertNotRegex(doc, r"(?m)^    - Kind:")


class RequirednessAndVocabularyTests(unittest.TestCase):
    """E-02: the rename preserves BOTH the requirement and the vocabulary check."""

    def test_a_valid_value_is_accepted(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            for kind in sorted(backlog.KINDS):
                p = _write_item(root, f"ddd{kind[:3]}", NEW_ITEM, kind=kind)
                self.assertEqual(_rules(p), [], f"{kind} should be accepted")

    def test_absent_work_kind_is_still_rejected(self):
        """LOAD-BEARING NEGATIVE: fails against an implementation that made the field OPTIONAL.

        Backlog rejects an item with no work-nature value today, and this plan is a pure rename, so
        that must survive. The Set unified the field's NAME, not its requiredness: it stays optional
        on plans and specs and REQUIRED here, deliberately.
        """

        with TemporaryDirectory() as td:
            p = _write_item(Path(td), "ddd111", NO_KIND_ITEM)
            self.assertIn("backlog.kind-invalid", _rules(p))

    def test_an_out_of_vocabulary_value_is_still_rejected(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _write_item(root, "ddd222", NEW_ITEM, kind="bogus")
            self.assertIn("backlog.kind-invalid", _rules(p))
            # and through the legacy spelling too, so dual-read did not become a bypass
            q = _write_item(root, "ddd333", OLD_ITEM, kind="bogus")
            self.assertIn("backlog.kind-invalid", _rules(q))

    def test_run_new_rejects_an_out_of_vocabulary_value(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "backlog").mkdir(parents=True)
            args = _NewArgs(dir=str(root), summary="A test item.", work_kind="bogus")
            self.assertEqual(backlog.run_new(args), 2)
            self.assertEqual(backlog._iter_items(root), [])

    def test_exactly_one_vocabulary_definition_is_consumed(self):
        """The Set's one-vocabulary rule: `backlog.KINDS` is the single source, unforked."""

        self.assertEqual(
            backlog.KINDS,
            frozenset(("bug", "feature", "chore", "security", "followup")),
        )
        pat = re.compile(r"KINDS\s*=\s*frozenset\(\(\s*\"bug\"")
        forks = [
            p.name
            for p in sorted((REPO_ROOT / "agent_workflows").glob("*.py"))
            if pat.search(p.read_text(encoding="utf-8"))
        ]
        self.assertEqual(forks, ["backlog.py"])


class GateKindGuardTests(unittest.TestCase):
    """E-03: `- Gate-Kind:` is a DIFFERENT field and the rename must not touch it."""

    def test_gate_kind_is_a_distinct_field_and_is_never_rewritten(self):
        """LOAD-BEARING NEGATIVE: fails against a substring-anchored rename.

        A rename anchored on the bare token `Kind` turns `- Gate-Kind:` into `- Gate-Work-Kind:`,
        which parses as no gate at all, so a blocked item silently loses its typed gate.
        """

        with TemporaryDirectory() as td:
            p = _write_item(Path(td), "eee111", GATE_ITEM)
            text = p.read_text(encoding="utf-8")
            self.assertIn("- Gate-Kind: artifact", text)
            self.assertNotIn("Gate-Work-Kind", text)
            item = backlog.parse_item(text)
            self.assertEqual(item.gate_kind, "artifact")
            self.assertEqual(item.gate_ref, "abc123")
            self.assertEqual(item.kind, "feature")
            self.assertEqual(_rules(p), [])

    def test_a_substring_rename_would_have_corrupted_the_gate(self):
        """Demonstrates the hazard directly: the naive rewrite breaks the gate, the real one does not."""

        text = GATE_ITEM.format(id6="eee222", kind="feature")
        naive = text.replace("Kind:", "Work-Kind:")
        self.assertIn("- Gate-Work-Kind:", naive)
        self.assertIsNone(backlog.parse_item(naive).gate_kind)
        # the full-line pattern the migration actually used leaves the gate alone
        anchored = re.sub(r"(?m)^- Kind:", "- Work-Kind:", text)
        self.assertNotIn("Gate-Work-Kind", anchored)
        self.assertEqual(backlog.parse_item(anchored).gate_kind, "artifact")

    def test_a_status_transition_preserves_the_gate_field_spelling(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_item(root, "eee333", GATE_ITEM)
            args = _SetArgs(
                dir=str(root),
                path="eee333",
                status="blocked",
                gate_kind="artifact",
                gate_ref="abc123",
            )
            self.assertEqual(backlog.run_set(args), 0)
            text = backlog._iter_items(root)[0].read_text(encoding="utf-8")
            self.assertIn("- Gate-Kind: artifact", text)
            self.assertNotIn("Gate-Work-Kind", text)


class MigratedCorpusTests(unittest.TestCase):
    """E-03/E-06: the live tree is migrated, and the README is documentation rather than data."""

    def test_every_parsed_item_carries_the_canonical_spelling(self):
        """Asserted on the live tree because it is the migration's actual deliverable.

        Enumeration comes from the PARSER, not a tree grep: `_iter_items` skips `README.md` (which is
        documentation carrying the field list) and does read one legacy-named item without the
        `.backlog.md` suffix, so a `grep -rl` over the tree reports one more file than there are items.
        """

        items = backlog._iter_items(REPO_ROOT)
        self.assertGreater(len(items), 0)
        stale = []
        for f in items:
            lines = f.read_text(encoding="utf-8").split("\n")
            if any(line.startswith("- Kind:") for line in lines):
                stale.append(f.name)
        self.assertEqual(stale, [])

    def test_no_item_lost_its_work_nature_value_in_the_migration(self):
        for f in backlog._iter_items(REPO_ROOT):
            item = backlog.parse_item(f.read_text(encoding="utf-8"))
            self.assertIn(
                item.kind, backlog.KINDS, f"{f.name} lost its work-nature value"
            )

    def test_the_gate_kind_field_survived_the_migration(self):
        carriers = [
            f
            for f in backlog._iter_items(REPO_ROOT)
            if any(
                line.startswith("- Gate-Kind:")
                for line in f.read_text(encoding="utf-8").split("\n")
            )
        ]
        for f in carriers:
            item = backlog.parse_item(f.read_text(encoding="utf-8"))
            self.assertIsNotNone(item.gate_kind, f"{f.name} lost its Gate-Kind")
            self.assertIsNotNone(item.gate_ref, f"{f.name} lost its Gate-Ref")
        self.assertNotIn(
            "Gate-Work-Kind",
            "".join(
                f.read_text(encoding="utf-8") for f in backlog._iter_items(REPO_ROOT)
            ),
        )

    def test_the_readme_documents_the_canonical_spelling_and_is_not_an_item(self):
        """KEPT, and STRENGTHENED from a literal-prefix pin into a vocabulary comparison.

        NOT a prose pin, for the same two reasons the surviving `- Status:` test in
        `test_backlog_graduated.py::test_readme_status_list_matches_statuses` is not one. FIRST,
        `- Work-Kind:` is a FRONT-MATTER FIELD SPELLING a parser reads: `backlog.parse_item` keys on
        it, so the README's line is the template a human copies when hand-writing an item, and the
        old spelling appearing here would be copied into a real artifact. SECOND, the value list is
        a CLOSED VOCABULARY that `backlog.run_new`/`run_set` validate against, and this README is
        one of its duplicate copies.

        WHAT CHANGED: the assertion was `assertRegex(text, r'^- Work-Kind: bug \\| feature')`, which
        pinned the first two members IN ORDER and said nothing about the rest, so adding or removing
        a kind left it green while reordering the documented list turned it red. It now parses the
        line and compares the SET to `backlog.KINDS`, so a reword or reorder is free and a
        vocabulary change fails. The `assertNotRegex` for the legacy spelling is kept because the
        rename's whole point is that only ONE spelling is written going forward.
        """

        readme = REPO_ROOT / ".aw" / "records" / "backlog" / "README.md"
        if not readme.exists():  # pragma: no cover - the tree always ships it
            self.skipTest("no backlog README in this checkout")
        text = readme.read_text(encoding="utf-8")

        m = re.search(r"(?m)^- Work-Kind: (.+)$", text)
        self.assertIsNotNone(
            m,
            "the backlog README must document a `- Work-Kind:` line: it is the template a human "
            "copies when hand-writing an item, and the field name is what `backlog.parse_item` "
            "keys on.",
        )
        assert m is not None
        documented = {v.strip() for v in m.group(1).split("|")}
        self.assertEqual(
            documented,
            set(backlog.KINDS),
            f"the README's documented work-kind vocabulary {sorted(documented)} no longer equals "
            f"`backlog.KINDS` {sorted(backlog.KINDS)}. The setters VALIDATE against the code's set, "
            "so a value documented here but absent there is refused when a human copies it, and a "
            "value in the code but missing here is invisible to whoever writes an item by hand. "
            "FIX: update the README line (its wording and order are NOT pinned, only the set).",
        )
        self.assertNotRegex(
            text,
            r"(?m)^- Kind: bug \| feature",
            "the README documents the LEGACY `- Kind:` spelling again. It is still READ for "
            "back-compat, but only `- Work-Kind:` is written, and documenting the old name gets it "
            "hand-copied into new items.",
        )
        # the parser must never have counted it as data
        self.assertNotIn(readme, backlog._iter_items(REPO_ROOT))


class BacklogSetClassificationTests(unittest.TestCase):
    """bklgkind b5sfwm E-06: `aw backlog set` can CORRECT a mislabeled classification.

    The defect these tests pin: neither `Work-Kind` nor `Priority` was settable on an EXISTING item,
    although `aw ipd set` and `aw specs set` both set both fields on their record types, so an agent
    reclassifying a mislabeled item had to hand-edit frontmatter the tool otherwise owns. The measured
    harm was an audit miss (the 2026-09-03 all-bugs-block-release audit selects on `Work-Kind: bug`).

    TWO THINGS MAKE THESE CASES LOAD-BEARING RATHER THAN ROUTINE.

    FIRST, the verb has TWO DISPATCH PATHS that do not share a write path, and only one of them worked.
    The fork tests whether `--status` was PASSED: absent goes to `status_set.run_set_command`, whose
    Work-Kind/Priority writers are record-type-agnostic and already hoisted out of every status branch;
    present goes to `backlog.run_set`, which had no writer at all. So every case here is asserted on
    BOTH spellings, and a single demonstration would have validated only half the surface.

    SECOND, the case the defect was actually hit on is the NO-OP: a pure reclassification changes no
    status, and the verb is named for transitions. A test that only reclassified while also moving the
    item would pass against an implementation that wrote the field solely inside a status branch.

    NOTE THE DELIBERATE ASYMMETRY WITH THE PLAN-SIDE TWIN (OQ-02, ruled 2026-09-10): there is NO `-`
    clearing sentinel here. Both fields are REQUIRED on a backlog item, so clearing one manufactures an
    item `validate_item` and `aw check backlog` reject; `test_a_clear_sentinel_is_refused_on_both_fields`
    pins the refusal, and `_assert_item_valid` pins the property that distinguishes this verb from the
    plan-side one.
    """

    ITEM = """- Id: {id6}
- Status: open
- Set: bkl
- Priority: medium
- Work-Kind: followup
- Summary: A test item.

## Workflow history
- 2026-09-08 created (aw backlog): A test item.

Body.
"""

    def _item(self, root: Path, id6: str, status: str = "open") -> Path:
        d = root / ".aw" / "records" / "backlog" / status
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"20260908-bkl-01-{id6}-a-test-item.backlog.md"
        p.write_text(self.ITEM.format(id6=id6), encoding="utf-8")
        return p

    def _fields(self, path: Path) -> dict:
        item = backlog.parse_item(path.read_text(encoding="utf-8"))
        return {"kind": item.kind, "priority": item.priority, "status": item.status}

    def _assert_item_valid(self, path: Path) -> None:
        """The property that distinguishes this verb from `aw ipd set`: a successful set must leave the
        item VALID. Both fields are required here, so a write that removed one would pass a
        "did the line change?" assertion while producing an item the repository's checker rejects."""

        rules = _rules(path)
        self.assertNotIn("backlog.kind-invalid", rules)
        self.assertNotIn("backlog.priority-invalid", rules)
        self.assertEqual(rules, [], f"{path.name} is not conformant after the set")

    def _run_cli(self, argv: list) -> int:
        """Drive the SHIPPED parser + dispatch, so the fork itself is exercised."""

        from agent_workflows import cli

        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = cli.main(argv)
        self._last_output = buf.getvalue()
        return rc

    # -- the no-op reclassification: the exact case the defect was hit on ----------------

    def test_a_noop_reclassification_persists_on_the_positional_spelling(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = self._item(root, "noop01")
            self.assertEqual(self._fields(p)["kind"], "followup")
            rc = self._run_cli(
                [
                    "backlog",
                    "set",
                    "open",  # SAME status the item already carries: a pure reclassification
                    "noop01",
                    "--work-kind",
                    "bug",
                    "--dir",
                    str(root),
                    "--message",
                    "reclassify followup -> bug",
                    "--yes",
                    "--no-commit",
                ]
            )
            self.assertEqual(rc, 0, self._last_output)
            items = backlog._iter_items(root)
            self.assertEqual(len(items), 1)
            after = items[0]
            self.assertEqual(self._fields(after)["kind"], "bug")
            self.assertEqual(self._fields(after)["status"], "open")
            # the file did NOT move: a reclassification is not a transition
            self.assertEqual(after.parent.name, "open")
            self.assertEqual(after.resolve(), p.resolve())
            # a history record was appended, so the change is auditable
            self.assertIn("## Workflow history", after.read_text(encoding="utf-8"))
            self.assertIn(
                "reclassify followup -> bug", after.read_text(encoding="utf-8")
            )
            self._assert_item_valid(after)

    def test_a_noop_reclassification_persists_on_the_status_spelling(self):
        """The spelling that had NO writer at all before this change.

        Note this spelling can never express a classification-ONLY call: `run_set` refuses unless a
        status is supplied, so a reclassification here always restates the current status.
        """

        with TemporaryDirectory() as td:
            root = Path(td)
            p = self._item(root, "noop02")
            rc = self._run_cli(
                [
                    "backlog",
                    "set",
                    str(p),
                    "--status",
                    "open",  # restating the current status
                    "--work-kind",
                    "bug",
                    "--dir",
                    str(root),
                    "--message",
                    "reclassify followup -> bug",
                    "--yes",
                    "--no-commit",
                ]
            )
            self.assertEqual(rc, 0, self._last_output)
            after = backlog._iter_items(root)[0]
            self.assertEqual(self._fields(after)["kind"], "bug")
            self.assertEqual(after.parent.name, "open")
            self.assertIn(
                "reclassify followup -> bug", after.read_text(encoding="utf-8")
            )
            self._assert_item_valid(after)

    def test_priority_is_settable_on_both_spellings(self):
        """The field the backlog item wrongly believed already worked: it was only on `backlog new`."""

        with TemporaryDirectory() as td:
            root = Path(td)
            p = self._item(root, "prio01")
            self.assertEqual(
                self._run_cli(
                    [
                        "backlog",
                        "set",
                        "open",
                        "prio01",
                        "--priority",
                        "high",
                        "--dir",
                        str(root),
                        "--yes",
                        "--no-commit",
                    ]
                ),
                0,
                self._last_output,
            )
            after = backlog._iter_items(root)[0]
            self.assertEqual(self._fields(after)["priority"], "high")
            self._assert_item_valid(after)

        with TemporaryDirectory() as td:
            root = Path(td)
            p = self._item(root, "prio02")
            self.assertEqual(
                self._run_cli(
                    [
                        "backlog",
                        "set",
                        str(p),
                        "--status",
                        "open",
                        "--priority",
                        "high",
                        "--dir",
                        str(root),
                        "--yes",
                        "--no-commit",
                    ]
                ),
                0,
                self._last_output,
            )
            after = backlog._iter_items(root)[0]
            self.assertEqual(self._fields(after)["priority"], "high")
            self._assert_item_valid(after)

    def test_both_fields_together_land_identically_on_both_spellings(self):
        """One write mechanism, so the two spellings' metadata blocks agree line for line.

        Compared as text (with the id and the history normalized away) because the two spellings reach
        the SAME `releases.set_work_kind_line` / `set_priority_line` primitives; a forked
        implementation that mutated the parsed item on one side would drift in field ORDER here even
        though both files carried the right values.
        """

        blocks = []
        for id6, argv_tail in (
            ("both01", ["open", "both01"]),
            ("both02", ["__PATH__", "--status", "open"]),
        ):
            with TemporaryDirectory() as td:
                root = Path(td)
                p = self._item(root, id6)
                argv = ["backlog", "set"] + [
                    str(p) if a == "__PATH__" else a for a in argv_tail
                ]
                argv += [
                    "--work-kind",
                    "security",
                    "--priority",
                    "low",
                    "--dir",
                    str(root),
                    "--yes",
                    "--no-commit",
                ]
                self.assertEqual(self._run_cli(argv), 0, self._last_output)
                after = backlog._iter_items(root)[0]
                self.assertEqual(self._fields(after)["kind"], "security")
                self.assertEqual(self._fields(after)["priority"], "low")
                self._assert_item_valid(after)
                meta = [
                    line
                    for line in after.read_text(encoding="utf-8").split("\n")
                    if line.startswith("- ") and not line.startswith("- 2026")
                ]
                blocks.append([re.sub(r"^- Id: \w+$", "- Id: <id6>", m) for m in meta])
        self.assertEqual(
            blocks[0], blocks[1], "the two spellings disagree on the block"
        )

    # -- refusals ------------------------------------------------------------------------

    def test_an_out_of_vocabulary_value_is_refused_and_nothing_is_written(self):
        for id6, argv_tail in (
            ("bad001", ["open", "bad001"]),
            ("bad002", ["__PATH__", "--status", "open"]),
        ):
            with TemporaryDirectory() as td:
                root = Path(td)
                p = self._item(root, id6)
                before = p.read_text(encoding="utf-8")
                argv = ["backlog", "set"] + [
                    str(p) if a == "__PATH__" else a for a in argv_tail
                ]
                argv += ["--work-kind", "bogus", "--dir", str(root), "--no-commit"]
                with self.assertRaises(SystemExit) as cm:
                    self._run_cli(argv)
                self.assertNotEqual(cm.exception.code, 0)
                self.assertEqual(p.read_text(encoding="utf-8"), before)

    def test_a_clear_sentinel_is_refused_on_both_fields(self):
        """OQ-02: `-` is NOT accepted here, unlike on `aw ipd set`.

        LOAD-BEARING NEGATIVE. Both fields are REQUIRED on a backlog item, so a `-` clear removes the
        line and leaves an item `validate_item` reports as `backlog.kind-invalid` /
        `backlog.priority-invalid` and `aw check backlog` exits nonzero on. Copying the plan-side
        twin's `-` semantics onto this verb would therefore have shipped a documented way to
        manufacture an invalid item; this asserts argparse refuses it before any file is touched.
        """

        for flag in ("--work-kind", "--priority"):
            with TemporaryDirectory() as td:
                root = Path(td)
                p = self._item(root, "clr001")
                before = p.read_text(encoding="utf-8")
                with self.assertRaises(SystemExit) as cm:
                    self._run_cli(
                        [
                            "backlog",
                            "set",
                            "open",
                            "clr001",
                            flag,
                            "-",
                            "--dir",
                            str(root),
                            "--no-commit",
                        ]
                    )
                self.assertNotEqual(cm.exception.code, 0, flag)
                self.assertEqual(p.read_text(encoding="utf-8"), before, flag)

    def test_run_set_refuses_an_out_of_vocabulary_value_passed_directly(self):
        """The shared line writers do NOT validate ("enforced by `aw check` ... not here"), and this
        function is called directly by tests and other code, so the refusal must live in `run_set`
        itself rather than relying on argparse `choices`."""

        with TemporaryDirectory() as td:
            root = Path(td)
            p = self._item(root, "dir001")
            before = p.read_text(encoding="utf-8")
            rc = backlog.run_set(
                _SetArgs(dir=str(root), path="dir001", status="open", work_kind="bogus")
            )
            self.assertEqual(rc, 2)
            self.assertEqual(p.read_text(encoding="utf-8"), before)
            rc = backlog.run_set(
                _SetArgs(dir=str(root), path="dir001", status="open", priority="urgent")
            )
            self.assertEqual(rc, 2)
            self.assertEqual(p.read_text(encoding="utf-8"), before)
            # and the '-' sentinel is refused on this route too, not merely by argparse
            rc = backlog.run_set(
                _SetArgs(dir=str(root), path="dir001", status="open", work_kind="-")
            )
            self.assertEqual(rc, 2)
            self.assertEqual(p.read_text(encoding="utf-8"), before)

    # -- the classification write does not disturb neighbouring fields -------------------

    def test_a_reclassification_preserves_the_typed_gate_and_its_spelling(self):
        """`- Gate-Kind:` is a DIFFERENT field; the writers are full-line anchored on `- Work-Kind:`."""

        with TemporaryDirectory() as td:
            root = Path(td)
            _write_item(root, "gat001", GATE_ITEM)
            rc = self._run_cli(
                [
                    "backlog",
                    "set",
                    "blocked",
                    "gat001",
                    "--work-kind",
                    "bug",
                    "--gate-kind",
                    "artifact",
                    "--gate-ref",
                    "abc123",
                    "--dir",
                    str(root),
                    "--yes",
                    "--no-commit",
                ]
            )
            self.assertEqual(rc, 0, self._last_output)
            after = backlog._iter_items(root)[0]
            text = after.read_text(encoding="utf-8")
            self.assertIn("- Work-Kind: bug", text)
            self.assertIn("- Gate-Kind: artifact", text)
            self.assertNotIn("Gate-Work-Kind", text)
            item = backlog.parse_item(text)
            self.assertEqual(item.gate_kind, "artifact")
            self.assertEqual(item.gate_ref, "abc123")

    def test_a_reclassification_preserves_a_blocks_release_gate(self):
        """The classification write is applied through the same post-render mechanism as
        `--blocks-release`, so the two must not clobber each other."""

        with TemporaryDirectory() as td:
            root = Path(td)
            p = self._item(root, "brl001")
            p.write_text(
                p.read_text(encoding="utf-8").replace(
                    "- Summary: A test item.",
                    "- Summary: A test item.\n- Blocks-Release: next",
                ),
                encoding="utf-8",
            )
            rc = self._run_cli(
                [
                    "backlog",
                    "set",
                    "open",
                    "brl001",
                    "--work-kind",
                    "bug",
                    "--dir",
                    str(root),
                    "--yes",
                    "--no-commit",
                ]
            )
            self.assertEqual(rc, 0, self._last_output)
            text = backlog._iter_items(root)[0].read_text(encoding="utf-8")
            self.assertIn("- Work-Kind: bug", text)
            self.assertIn("- Blocks-Release: next", text)


class FlagSurfaceTests(unittest.TestCase):
    """E-02/E-05: `--work-kind` is preferred, `--kind` is kept, and the declaration agrees."""

    def _accepted_flags(self, leaf: str = "new"):
        """Every option string the real `backlog <leaf>` subparser accepts.

        Walks the parser the CLI actually builds, so the assertion is about the shipped surface and
        not about a re-declaration in the test.
        """

        import argparse

        from agent_workflows.cli import _build_parser

        def _subparser(parent, name):
            for action in parent._actions:
                if (
                    isinstance(action, argparse._SubParsersAction)
                    and name in action.choices
                ):
                    return action.choices[name]
            return None

        backlog_parser = _subparser(_build_parser(), "backlog")
        if backlog_parser is None:
            self.fail("no `backlog` subparser")
        leaf_parser = _subparser(backlog_parser, leaf)
        if leaf_parser is None:
            self.fail(f"no `backlog {leaf}` subparser")
        return {opt for a in leaf_parser._actions for opt in a.option_strings}

    def test_both_spellings_are_accepted_by_the_parser(self):
        accepted = self._accepted_flags()
        self.assertIn("--work-kind", accepted)
        self.assertIn("--kind", accepted)

    def test_the_declaration_matches_the_parser(self):
        declared = None
        for d in command_surface.COMMAND_INVENTORY:
            if d.command == "backlog new":
                declared = set(d.legacy_flags)
        self.assertIsNotNone(declared)
        assert declared is not None
        self.assertIn("--work-kind", declared)
        self.assertIn("--kind", declared)
        # every declared flag is really accepted (the declaration is not aspirational)
        self.assertEqual(declared - self._accepted_flags(), set())

    def test_the_set_verb_declares_its_classification_flags(self):
        """bklgkind b5sfwm E-05: the two flags are DECLARED, not merely accepted.

        STATED HONESTLY, because this test could easily be read as proving more than it does: like its
        `backlog new` sibling it checks `declared - accepted == set()`, i.e. that every declared flag is
        really accepted. It is ONE-DIRECTIONAL, so an accepted-but-undeclared flag still passes, and
        this entry indeed still omits `--evidence`, `--yes` and `--commit`/`--no-commit`, which were
        left alone deliberately as outside this plan's fence. So this asserts the two fields are
        declared and the declaration is not aspirational; it does NOT assert the entry is complete.
        """

        declared = None
        for d in command_surface.COMMAND_INVENTORY:
            if d.command == "backlog set":
                declared = set(d.legacy_flags)
        self.assertIsNotNone(declared)
        assert declared is not None
        self.assertIn("--work-kind", declared)
        self.assertIn("--priority", declared)
        accepted = self._accepted_flags("set")
        self.assertIn("--work-kind", accepted)
        self.assertIn("--priority", accepted)
        self.assertEqual(declared - accepted, set())

    def test_the_preferred_spelling_wins_when_both_are_passed(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "backlog").mkdir(parents=True)
            args = _NewArgs(
                dir=str(root),
                summary="A test item.",
                work_kind="security",
                kind="bug",
            )
            self.assertEqual(backlog.run_new(args), 0)
            text = backlog._iter_items(root)[0].read_text(encoding="utf-8")
            self.assertIn("- Work-Kind: security", text)

    def test_the_retained_alias_still_works(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "backlog").mkdir(parents=True)
            args = _NewArgs(dir=str(root), summary="A test item.", kind="bug")
            self.assertEqual(backlog.run_new(args), 0)
            text = backlog._iter_items(root)[0].read_text(encoding="utf-8")
            self.assertIn("- Work-Kind: bug", text)

    def test_neither_flag_falls_back_to_chore(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "backlog").mkdir(parents=True)
            args = _NewArgs(dir=str(root), summary="A test item.")
            self.assertEqual(backlog.run_new(args), 0)
            text = backlog._iter_items(root)[0].read_text(encoding="utf-8")
            self.assertIn("- Work-Kind: chore", text)


class _NewArgs:
    """Minimal `aw backlog new` args namespace (apply-by-default, human output)."""

    def __init__(self, **kw):
        self.dir = kw.get("dir")
        self.summary = kw.get("summary")
        self.set = kw.get("set")
        self.status = kw.get("status")
        self.priority = kw.get("priority")
        self.work_kind = kw.get("work_kind")
        self.kind = kw.get("kind")
        self.slug = kw.get("slug", "a-test-item")
        self.gate_kind = kw.get("gate_kind")
        self.gate_ref = kw.get("gate_ref")
        self.blocks_release = kw.get("blocks_release")
        self.message = kw.get("message")
        self.body = kw.get("body")
        self.apply = kw.get("apply", True)
        self.json = False
        self.agent = False
        self.no_color = True


class _SetArgs:
    """Minimal `aw backlog set` args namespace.

    bklgkind b5sfwm E-06 added `work_kind` and `priority`. THIS MATTERS MORE THAN IT LOOKS: `run_set`
    reads them with `getattr(..., None)`, following the surrounding style, so a namespace MISSING the
    attributes silently no-ops instead of raising. A test suite driving an un-extended namespace would
    therefore stay green against an implementation that never wrote the fields at all.
    """

    def __init__(self, **kw):
        self.dir = kw.get("dir")
        self.path = kw.get("path")
        self.status = kw.get("status")
        self.message = kw.get("message", "")
        self.gate_kind = kw.get("gate_kind")
        self.gate_ref = kw.get("gate_ref")
        self.blocks_release = kw.get("blocks_release")
        self.evidence = kw.get("evidence")
        self.work_kind = kw.get("work_kind")
        self.priority = kw.get("priority")
        self.force = kw.get("force", False)
        self.apply = kw.get("apply", True)
        self.json = False
        self.agent = False
        self.no_color = True


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
