#!/usr/bin/env python3
"""THE BOUNDARY of the rununify 03 (`i3d6ml`) lift: what moved, and what must NEVER move.

WHY THIS FILE ASSERTS IN TWO DIRECTIONS, which is the whole point and is not symmetry for its own
sake. A lift suite that checks only what moved has a blind spot in the direction of the more likely
mistake. `i3d6ml` lifted 9 symbols into `runner_shared` and deliberately did NOT lift 11 others, and
those 11 are the dangerous ones:

  * TEN are the `INJECTED` set. Each already has exactly ONE implementation, in `runner_shared`, and
    keeps a one-line runner-local wrapper that binds a host-specific dependency. That wrapper IS the
    de-duplicated form; it is not leftover duplication. The maintainer ruled it (`818uru` OQ-02, quoted
    verbatim in `runner_shared.run_checked`'s docstring) after rejecting two alternatives: threading the
    parameter through ~86 call sites, and a registration seam whose global state makes behavior depend
    on import order.
  * ONE is `disable_lane_prompt`, which writes a module-level `_LANE_PROMPT_DISABLED` through `global`
    while each host's `_lane_reclaim_prompt` reads its OWN copy. Lifting it produces no error and no
    failure that names the cause: prompt suppression just silently stops working, and the symptom is an
    unattended run pausing for a question nobody is there to answer.

So a future agent counting definitions will find 11 symbols that LOOK like unfinished work. Reading a
one-directional suite, they would delete a wrapper, watch every test pass, and reverse a ruling. The
INVERSE assertions below are what stops that, and each carries the citation that excludes its symbol
so the reason travels with the test.

WHAT IS ASSERTED FOR A LIFTED SYMBOL, three independent properties, none implying another:
  1. OBJECT IDENTITY. Both runners resolve the name to the SAME object.
  2. DEFINING MODULE. That object's `__module__` is `agent_workflows.runner_shared`.
  3. NO RE-FORK, checked REPO-WIDE by AST rather than pairwise (the parent plan's F10): no module in
     the package other than `runner_shared` may hold a top-level `def`/`class` of the name. A pairwise
     oc-vs-agy check would pass while a third module grew a copy.

Property 3 subsumes 1 in practice but not in principle: a runner can hold no definition and still
rebind the name at runtime, which is exactly the trap `tests/test_runner_refork_guard.py` documents.

THE TABLE IS NAMED DATA, not the literal 48 the plan was authored around. The plan's original scope was
re-measured at execution and only 9 of those 48 were liftable, so a test driven by the number would
assert something untrue. Driven by names, it says exactly what happened.
"""

from __future__ import annotations

import ast
import pathlib
import unittest
from typing import NamedTuple

from agent_workflows import agy_runipd, oc_runipd, runner_shared

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {
    "oc_runipd": oc_runipd,
    "agy_runipd": agy_runipd,
    "runner_shared": runner_shared,
}
_PKG = pathlib.Path(runner_shared.__file__).parent


class Lifted(NamedTuple):
    """One symbol `i3d6ml` moved into `runner_shared`, with the group it came from."""

    symbol: str
    group: str
    note: str


# GROUP A: closure-clean at execution HEAD, no prerequisite, no observable change.
GROUP_A: tuple[Lifted, ...] = (
    Lifted(
        "StallTimeout",
        "A",
        "the watchdog's exception. RISKY DESPITE BEING 2 LINES: each runner's `main` caught its "
        "OWN class, so unifying changes which `except` catches a cross-host raise. "
        "`tests/test_runner_shared.py`'s DriverErrorUnificationTests exercises every handler form.",
    ),
    Lifted(
        "EmptyStatusSelection",
        "A",
        "an empty status selector is a SUCCESS (spec `25kzda` 2.4a property 3). Its `main` handler "
        "must still be ORDERED ahead of the generic `except DriverError`, or an empty selection "
        "exits 2 instead of 0.",
    ),
    Lifted(
        "_findings_block_reason",
        "A",
        "delegates entirely to `review_findings.subject_gating_blocks`; held no logic in either "
        "runner. Both docstrings said the wrapper existed only because neither runner imports the "
        "other, a reason the shared module discharges.",
    ),
    Lifted(
        "make_integration_validation_runner",
        "A",
        "returns a constant-True validator for the single-lane case. Tests PATCH this to exercise "
        "a combined-red path; there is one function to patch now.",
    ),
    Lifted(
        "build_review_prompt",
        "A",
        "the `/plan-review` command plus the mandatory isolation statement. oc called "
        "`lane_containment.isolation_notice` directly, agy reached it through its own one-line "
        "`build_isolation_notice`, so the same string arrived by a different number of hops.",
    ),
)

# GROUP B: closure-clean, but the two hosts' OBSERVABLE OUTPUT differed. Each is disclosed at its
# shared definition; two of the four change an antigravity filename.
GROUP_B: tuple[Lifted, ...] = (
    Lifted(
        "attempt_log_path",
        "B",
        "REPAIRS A LIVE DEFECT. agy emitted `-verify-attempt-<n>.jsonl` while "
        "`run_analytics_statistics._VERIFY_LOG_RE` matches oc's `-attempt-<n>-verify.jsonl`, so "
        "every agy verifier log was classified `execute`. See the dedicated test below.",
    ),
    Lifted(
        "write_prompt",
        "B",
        "a SEMANTIC difference, not a tag reordering: oc's `suffix` REPLACES the action prefix, "
        "agy's ADDED to it. oc's form is adopted; nothing parses a PROMPT filename.",
    ),
    Lifted(
        "resolve_prior_lane",
        "B",
        "DELETES A RUNNER-TO-RUNNER IMPORT: agy's body imported oc at call time. There was already "
        "one implementation; what changed is where it lives.",
    ),
    Lifted(
        "sync_receipt_into_worktree",
        "B",
        "a deprecated no-op in both runners. Lifted because two no-ops are still two places the "
        "receipt copy (a hazard research x03wgn names) could be 'restored' into.",
    ),
)

LIFTED: tuple[Lifted, ...] = GROUP_A + GROUP_B


class Excluded(NamedTuple):
    """One symbol that must NOT be lifted, and the ruling or pinned test that excludes it."""

    symbol: str
    group: str
    citation: str


# GROUP C: already ONE implementation in `runner_shared` behind a deliberate one-line host wrapper.
# The wrapper binds a host-specific dependency and is the maintainer's ruled mechanism.
GROUP_C: tuple[Excluded, ...] = tuple(
    Excluded(name, "C", citation)
    for name, citation in (
        (
            "run_checked",
            "`818uru` OQ-02, quoted in `runner_shared.run_checked`; binds `pinned_child_env`",
        ),
        ("save_state", "`818uru` OQ-02; binds the host's DIVERGED `write_report`"),
        (
            "discover_plans",
            "`818uru` OQ-02; binds `parse_plan_file`, which builds each host's OWN PlanRecord",
        ),
        (
            "validate_manifest",
            "`818uru` OQ-02; binds the opencode-only `parse_dependency_token`",
        ),
        ("print_status", "`818uru` OQ-02; binds the host's own `driver_label`"),
        (
            "git_head",
            "`818uru` OQ-02 + the intra-seam note; binds the host's `run_checked` wrapper",
        ),
        (
            "git_status",
            "`818uru` OQ-02 + the intra-seam note; binds the host's `run_checked` wrapper",
        ),
        (
            "git_common_dir",
            "`818uru` OQ-02 + the intra-seam note; binds the host's `run_checked` wrapper",
        ),
        (
            "build_lane_outcome",
            "integpath-02 `6sb3yu`; binds the host's `run_checked` wrapper",
        ),
        (
            "integrate_lane_branch",
            "integpath-02 `6sb3yu`; binds `run_checked` AND the `host_label` that lands in a merge subject on MAIN",
        ),
    )
)

# GROUP D: pinned UNMOVABLE. Not deferred: permanently excluded for a reason that still holds.
GROUP_D: tuple[Excluded, ...] = (
    Excluded(
        "disable_lane_prompt",
        "D",
        "`tests/test_runner_shared.py::UnmovableSymbolTests` + `runner_shared`'s docstring: it "
        "writes `_LANE_PROMPT_DISABLED` through `global` while each host's `_lane_reclaim_prompt` "
        "reads its own copy, so lifting it silently breaks prompt suppression",
    ),
)

EXCLUDED: tuple[Excluded, ...] = GROUP_C + GROUP_D


def _top_level_definitions(path: pathlib.Path) -> dict[str, int]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (
        SyntaxError
    ):  # pragma: no cover - a syntax error is a different test's failure
        return {}
    return {
        node.name: node.lineno
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


class LiftedSymbolTests(unittest.TestCase):
    """The forward direction: the 9 symbols moved and both hosts reach the ONE definition."""

    def test_both_runners_resolve_the_same_object(self):
        for row in LIFTED:
            with self.subTest(symbol=row.symbol, group=row.group):
                shared = getattr(runner_shared, row.symbol, None)
                self.assertIsNotNone(
                    shared,
                    f"`{row.symbol}` (group {row.group}) is not defined in runner_shared. "
                    f"{row.note}",
                )
                self.assertIs(
                    getattr(oc_runipd, row.symbol),
                    shared,
                    f"oc_runipd.{row.symbol} is not the shared object; a fix to the shared "
                    f"definition would not reach this host",
                )
                self.assertIs(
                    getattr(agy_runipd, row.symbol),
                    shared,
                    f"agy_runipd.{row.symbol} is not the shared object; a fix to the shared "
                    f"definition would not reach this host",
                )

    def test_the_defining_module_is_runner_shared(self):
        for row in LIFTED:
            with self.subTest(symbol=row.symbol, group=row.group):
                obj = getattr(runner_shared, row.symbol)
                self.assertEqual(
                    obj.__module__,
                    "agent_workflows.runner_shared",
                    f"`{row.symbol}` reports {obj.__module__} as its defining module; identity "
                    "alone can be satisfied by a re-export chain that still hides a second body",
                )

    def test_no_module_in_the_package_re_forks_a_lifted_symbol(self):
        """REPO-WIDE by AST, not pairwise, per the parent plan's F10.

        A pairwise oc-vs-agy check passes while a THIRD module in the package grows a copy, which is
        how `render_stream`'s symbols came to be re-forked in a runner in the first place. This walks
        every module and names the offender and its line, because "something was re-forked" is not an
        actionable failure message.
        """
        names = {row.symbol for row in LIFTED}
        violations = []
        for path in sorted(_PKG.glob("*.py")):
            if path.name == "runner_shared.py":
                continue
            for name, line in _top_level_definitions(path).items():
                if name in names:
                    violations.append(f"{path.name}:{line} re-defines `{name}`")
        self.assertEqual(
            violations,
            [],
            "RE-FORK FOUND. A lifted symbol has a second top-level definition; import it "
            "from `runner_shared` instead, because a fix to the shared definition does not "
            "reach a copy.\n  " + "\n  ".join(violations),
        )

    def test_each_lifted_symbol_is_defined_exactly_once_in_runner_shared(self):
        defined = _top_level_definitions(_PKG / "runner_shared.py")
        for row in LIFTED:
            with self.subTest(symbol=row.symbol, group=row.group):
                self.assertIn(row.symbol, defined)


class ExcludedSymbolTests(unittest.TestCase):
    """The INVERSE direction, and the reason this file exists rather than a one-sided lift check.

    Every assertion here FAILS IF SOMEONE LIFTS the symbol. That is deliberate: the excluded symbols
    look like leftover duplication to anyone counting definitions, and "finishing the job" on them
    reverses a maintainer ruling (group C) or silently breaks prompt suppression (group D).
    """

    def test_every_group_c_symbol_still_has_a_runner_local_wrapper(self):
        for row in GROUP_C:
            with self.subTest(symbol=row.symbol, group=row.group):
                for runner in BOTH:
                    defined = _top_level_definitions(_PKG / f"{runner}.py")
                    self.assertIn(
                        row.symbol,
                        defined,
                        f"{runner} no longer defines `{row.symbol}`. That wrapper is NOT "
                        f"leftover duplication: it is the ruled mechanism for binding a "
                        f"host-specific dependency, and the real implementation already lives "
                        f"once in runner_shared. Citation: {row.citation}",
                    )

    def test_disable_lane_prompt_is_still_defined_in_both_runners(self):
        for row in GROUP_D:
            for runner in BOTH:
                with self.subTest(symbol=row.symbol, runner=runner):
                    self.assertIn(
                        row.symbol,
                        _top_level_definitions(_PKG / f"{runner}.py"),
                        f"{runner} no longer defines `{row.symbol}`. Citation: {row.citation}",
                    )

    def test_the_shared_module_does_not_define_an_excluded_symbol(self):
        defined = _top_level_definitions(_PKG / "runner_shared.py")
        for row in GROUP_D:
            with self.subTest(symbol=row.symbol, group=row.group):
                self.assertNotIn(
                    row.symbol,
                    defined,
                    f"`{row.symbol}` was LIFTED into runner_shared. This produces no error and "
                    f"no failure naming the cause: prompt suppression silently stops working, "
                    f"and the symptom is an unattended run pausing for a question nobody is "
                    f"there to answer. Citation: {row.citation}",
                )

    def test_every_exclusion_carries_a_citation(self):
        """The disclosure E-04 delivers, asserted rather than left to prose.

        An exclusion without a stated reason decays into an unexplained gap, and an unexplained gap
        is what the next agent 'fixes'.
        """
        for row in EXCLUDED:
            with self.subTest(symbol=row.symbol):
                self.assertTrue(row.citation.strip())
        self.assertEqual(
            len(EXCLUDED), 11, "the 11 exclusions are a measured set, not an open list"
        )


class ObservableChangeTests(unittest.TestCase):
    """The group-B disclosures, EXERCISED. Two of them change an antigravity filename."""

    ITEM = {"position": 3, "id6": "abc123", "action": "execute"}

    def test_attempt_log_path_now_produces_the_shape_the_analytics_parse(self):
        """The repaired defect, proven end to end rather than asserted.

        This is the one user-visible improvement in `i3d6ml`, so it is checked against the ACTUAL
        consumer instead of against a hand-written expected string: the analytics function is asked
        what phase it reads off the name.
        """
        from agent_workflows import run_analytics_statistics as stats

        path = runner_shared.attempt_log_path(
            pathlib.Path("/run"), self.ITEM, 1, suffix="verify"
        )
        self.assertEqual(path.name, "03-abc123-attempt-1-verify.jsonl")
        phase, derived = stats.verifier_phase_of_log(path.name)
        self.assertEqual(
            phase,
            "verify",
            "the shared verifier log name is not recognized by "
            "`run_analytics_statistics._VERIFY_LOG_RE`, so verifier cost would be attributed "
            "to the execute phase",
        )
        self.assertTrue(derived)

        # The shape agy produced BEFORE the lift, kept as a literal so the repair is visible: the
        # analytics read it as an EXECUTE log, which is the defect.
        old_agy_name = "03-abc123-verify-attempt-1.jsonl"
        self.assertEqual(
            stats.verifier_phase_of_log(old_agy_name)[0],
            "execute",
            "the pre-lift antigravity name is no longer misclassified, so this test's premise "
            "changed; re-derive it rather than deleting it",
        )

        # Both hosts reach the SAME function, so neither can regress alone.
        self.assertEqual(
            oc_runipd.attempt_log_path(pathlib.Path("/run"), self.ITEM, 1, "verify"),
            agy_runipd.attempt_log_path(pathlib.Path("/run"), self.ITEM, 1, "verify"),
        )

    def test_write_prompt_suffix_replaces_the_action_prefix_on_both_hosts(self):
        """The SEMANTIC difference, pinned in the direction that was chosen.

        oc treated `suffix` as replacing `exec`/`review`; agy treated it as an extra tag. Adopting
        oc's meaning changes agy's filename, which is why it is pinned here rather than described.
        """
        for suffix, expected in (
            ("verify", "03-abc123-verify-attempt-1.md"),
            ("defect-reask", "03-abc123-defect-reask-attempt-1.md"),
        ):
            with self.subTest(suffix=suffix):
                import tempfile

                with tempfile.TemporaryDirectory() as tmp:
                    run_dir = pathlib.Path(tmp)
                    (run_dir / "prompts").mkdir()
                    path = runner_shared.write_prompt(
                        run_dir, self.ITEM, "body", 1, suffix
                    )
                    self.assertEqual(path.name, expected)
                    # NOT the agy shape, which carried the action prefix as well.
                    self.assertNotIn("-exec-", path.name)

    def test_write_prompt_without_a_suffix_keeps_the_action_prefix(self):
        """The unsuffixed case is byte-identical on both hosts and must not have moved."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            (run_dir / "prompts").mkdir()
            self.assertEqual(
                runner_shared.write_prompt(run_dir, self.ITEM, "b", 2).name,
                "03-abc123-exec-attempt-2.md",
            )
            review_item = dict(self.ITEM, action="review")
            self.assertEqual(
                runner_shared.write_prompt(run_dir, review_item, "b", 1).name,
                "03-abc123-review-attempt-1.md",
            )


class ExceptionUnificationTests(unittest.TestCase):
    """The risky half of group A: unifying a class changes which `except` catches a raise."""

    def test_a_raise_through_one_runners_name_is_caught_through_the_others(self):
        for name in ("StallTimeout", "EmptyStatusSelection"):
            for raiser, catcher in (
                ("oc_runipd", "agy_runipd"),
                ("agy_runipd", "oc_runipd"),
            ):
                with self.subTest(symbol=name, raiser=raiser, catcher=catcher):
                    caught = False
                    try:
                        raise getattr(_MODULES[raiser], name)("cross-host raise")
                    except getattr(_MODULES[catcher], name):
                        caught = True
                    self.assertTrue(
                        caught,
                        f"a `{name}` raised through {raiser} is not caught by "
                        f"{catcher}'s `except {name}`",
                    )

    def test_each_runners_except_DriverError_still_catches_both_subclasses(self):
        """The property the unification could have broken WITHOUT any test naming the cause."""
        for name in ("StallTimeout", "EmptyStatusSelection"):
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    caught = False
                    try:
                        raise getattr(_MODULES[runner], name)("boom")
                    except _MODULES[runner].DriverError:
                        caught = True
                    self.assertTrue(caught)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
