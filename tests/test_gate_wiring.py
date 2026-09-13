"""Every shipped gate verb must be CLASSIFIED as wired-by-default or deliberately exempt
(commitguard Order 01 `kbqpkn` E-06).

WHY THIS FILE EXISTS. Six local gate verbs ship in this package; only two are registered in this
repository's `.pre-commit-config.yaml`, and backlog item `wjl471` filed that asymmetry as "four
unwired gates". It is not an oversight: all four are deliberately OPT-IN by a resolved maintainer
decision (executed plan `diundn` OQ-01, "RESOLVED - OPT-IN ... NEVER installed by default",
reaffirmed for this plan on 2026-09-10 as "keep all four opt-in, wire none of them"). The real
defect the item found is that FOUR GATES ACCUMULATED WITH NOBODY NOTICING: nothing in the tree
recorded whether each one was supposed to be on. This file records that decision mechanically, so a
SEVENTH gate cannot be added and silently left unclassified: a new gate verb belongs to neither
list below and therefore FAILS here until somebody decides which list it belongs in.

THE CAVEAT, adopted verbatim from `tests/test_executed_transition_gate.py::PreCommitConfigStage\
RegistrationTests`, because it applies word for word to everything asserted here:

    This is a CONFIGURATION assertion only. It is NOT evidence that the stage fires.

Proof that a stage actually fires lives in the real-commit / real-merge tests of the individual gate
modules (`tests/test_executed_transition_gate.py`, `tests/test_status_untooled_gate.py`,
`tests/test_phase4_hooks.py`, ...), never here.

DISCOVERY, NOT A HARDCODED LIST OF SIX. The verb set is derived from `agent_workflows/cli.py` by
finding each `args.command == "<verb>"` dispatch block that imports a module from
`agent_workflows.hooks`, and is cross-checked for BIJECTION against the modules physically present
in `agent_workflows/hooks/`. A hardcoded list of six would be blind to exactly the seventh gate this
file exists to catch.

HONEST LIMIT OF THE EXEMPTIONS. "Not registered in this repository's config" is NOT "unavailable":
every exempt gate has a working idempotent no-clobber installer in `engine.py`
(`create_precommit_scope_gate_hook`, `create_prepush_authorization_gate_hook`,
`create_backlog_close_gate_hook`, `create_dependency_gate_hook`), so an operator who wants one has a
supported route. The exemption is about this repository's DEFAULT posture for everyone who clones
it, and the portable authority for all of these invariants remains `aw check` in required CI.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "agent_workflows" / "cli.py"
HOOKS_DIR = REPO_ROOT / "agent_workflows" / "hooks"
CONFIG_PATH = REPO_ROOT / ".pre-commit-config.yaml"

#: Gate verbs this repository registers in its OWN `.pre-commit-config.yaml`, mapped to the exact
#: git stages each must run in. The stage matters: a gate registered for the wrong stage is as
#: ineffective as an unregistered one (a pre-push guard on `pre-commit` refuses work that is not
#: being pushed, and a `pre-merge-commit` gate absent from that stage misses every automated merge).
WIRED_BY_DEFAULT: dict[str, tuple[str, ...]] = {
    # integpath `29wvmj` OQ-03 option (b): git runs `pre-merge-commit`, NOT `pre-commit`, for an
    # AUTOMATED merge, so the terminal-transition gate must opt into both stages explicitly.
    "ipd-executed-gate": ("pre-commit", "pre-merge-commit"),
    # proclint `79li67`: the intermediate-status sibling of the terminal gate; commit-scoped only.
    "ipd-status-untooled-gate": ("pre-commit",),
}

#: Gate verbs deliberately NOT registered here, each with the decision that made it opt-in. A verb
#: in this list must appear ZERO times in `.pre-commit-config.yaml`; registering one without moving
#: it to `WIRED_BY_DEFAULT` (and recording the reversal) fails this file.
EXEMPT_OPT_IN: dict[str, str] = {
    # `diundn` OQ-01: "RESOLVED - OPT-IN ... NEVER installed by default", on the stated rationale
    # that "local hooks are opt-in feedback, not an imposed authority boundary"; installer
    # `engine.create_precommit_scope_gate_hook` documents "opt-in-only (never default-installed)".
    # Additionally measured unwirable today: it refuses a CLEAN tree with `check.scope-drift`
    # findings against OTHER agents' in-flight plans whose frozen begin bases trail main (the
    # defect plan `wmnmei` owns). Reaffirmed by the maintainer 2026-09-10 via `kbqpkn` OQ-01.
    "precommit-scope-gate": "diundn OQ-01 RESOLVED - OPT-IN; reaffirmed kbqpkn OQ-01 2026-09-10",
    # `diundn` OQ-01 covers this gate too; `engine.create_prepush_authorization_gate_hook` says
    # "opt-in-only". It refuses EVERY push lacking `AW_PUSH_AUTHORIZED=1` BY DESIGN, so wiring it
    # is a workflow-posture choice, not a safety fix. Declined by the maintainer 2026-09-10.
    "prepush-authorization-gate": "diundn OQ-01 RESOLVED - OPT-IN; declined kbqpkn OQ-01 2026-09-10",
    # AGENTS.md ("An OPT-IN local pre-commit hook (`backlog-blocking-close-gate`) ... It is NOT
    # installed by default"); wired on request via `engine.create_backlog_close_gate_hook(
    # repo, install=True)`. The portable authority is `check.blocking-item-closed-without-gate`
    # in CI. Runs clean here (exit 0) but was left opt-in by the maintainer 2026-09-10.
    "backlog-blocking-close-gate": "AGENTS.md 'NOT installed by default'; kbqpkn OQ-01 2026-09-10",
    # `agent_workflows/hooks/ipd_dependency_statement_gate.py:1` opens "OPT-IN local pre-commit
    # gate"; wired on request via `engine.create_dependency_gate_hook(repo, install=True)`. The
    # portable authority is the shared `check.ipd-dependency-*` rules in CI. Runs clean here
    # (exit 0) but was left opt-in by the maintainer 2026-09-10.
    "ipd-dependency-statement-gate": "module docstring 'OPT-IN'; kbqpkn OQ-01 2026-09-10",
}


def discover_gate_verbs(cli_source: str) -> dict[str, str]:
    """Return ``{cli verb: hooks module name}`` for every gate verb the CLI dispatches.

    Derived from the source rather than declared, so a NEW gate verb is discovered automatically.
    A gate verb is a top-level ``args.command == "<verb>"`` branch whose body imports a module from
    ``agent_workflows.hooks``; that import is what makes it a gate rather than an ordinary verb, and
    it is independent of naming (a gate verb that does not end in ``-gate`` is still found).
    """

    found: dict[str, str] = {}
    for node in ast.walk(ast.parse(cli_source)):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and isinstance(test.left, ast.Attribute)
            and test.left.attr == "command"
            and isinstance(test.comparators[0], ast.Constant)
            and isinstance(test.comparators[0].value, str)
        ):
            continue
        modules: set[str] = set()
        for sub in ast.walk(node):
            if (
                isinstance(sub, ast.ImportFrom)
                and sub.module == "agent_workflows.hooks"
            ):
                modules |= {alias.name for alias in sub.names}
        if len(modules) == 1:
            found[test.comparators[0].value] = modules.pop()
    return found


def classify(
    discovered: set[str], wired: dict[str, tuple[str, ...]], exempt: dict[str, str]
) -> list[str]:
    """Return the classification violations for ``discovered`` against the two declared lists.

    Factored out as a pure function so its failure mode is provable WITHOUT perturbing the real
    repository: the unclassified-verb test below feeds it a synthetic seventh gate. Violations:
    a discovered verb in neither list, a declared verb that no longer exists, and a verb declared
    in both lists at once.
    """

    violations: list[str] = []
    for verb in sorted(discovered - set(wired) - set(exempt)):
        violations.append(
            f"gate verb {verb!r} is classified in NEITHER WIRED_BY_DEFAULT nor EXEMPT_OPT_IN: "
            "decide whether this repository registers it by default (and record the decision) or "
            "leaves it opt-in (and record the citation), then add it to the right list"
        )
    for verb in sorted((set(wired) | set(exempt)) - discovered):
        violations.append(
            f"declared gate verb {verb!r} is no longer dispatched by the CLI: remove the stale "
            "declaration or restore the verb"
        )
    for verb in sorted(set(wired) & set(exempt)):
        violations.append(
            f"gate verb {verb!r} is declared BOTH wired and exempt; it must be exactly one"
        )
    return violations


def _hook_modules() -> set[str]:
    return {
        path.stem
        for path in HOOKS_DIR.glob("*.py")
        if path.stem != "__init__" and "def main(" in path.read_text(encoding="utf-8")
    }


def _config():
    import yaml

    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _hooks_by_entry_verb(data) -> dict[str, dict]:
    """Map ``verb -> hook mapping`` for every local hook whose entry runs a packaged verb.

    Keyed on the ENTRY (`python3 -m agent_workflows <verb>`) rather than the hook `id`, because the
    id is free text (`ipd-executed-transition-gate` runs the verb `ipd-executed-gate`) while the
    entry is what actually executes.
    """

    prefix = "python3 -m agent_workflows "
    out: dict[str, dict] = {}
    for repo in data.get("repos") or []:
        for hook in repo.get("hooks") or []:
            entry = str(hook.get("entry") or "")
            if entry.startswith(prefix):
                out[entry[len(prefix) :].strip()] = hook
    return out


class GateVerbDiscoveryTests(unittest.TestCase):
    """The verb set is DISCOVERED, and discovery is proven to agree with the shipped modules."""

    def test_discovery_finds_a_gate_verb_for_every_hook_module(self):
        discovered = discover_gate_verbs(CLI_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(discovered.values()),
            sorted(_hook_modules()),
            "every module in agent_workflows/hooks/ with a main() must be reachable through exactly "
            "one CLI verb, and every gate verb must dispatch to a real hook module",
        )

    def test_discovery_is_not_vacuous(self):
        # A gate verb is recognized by its hooks import, not by its name, so a differently named
        # verb is still discovered; and an ordinary verb that imports nothing from hooks is not.
        source = (
            "def run(args):\n"
            "    if args.command == 'brand-new-guard':\n"
            "        from agent_workflows.hooks import brand_new_guard as _g\n"
            "        return _g.main([])\n"
            "    if args.command == 'check':\n"
            "        return run_check(args)\n"
        )
        self.assertEqual(
            discover_gate_verbs(source), {"brand-new-guard": "brand_new_guard"}
        )


class GateClassificationTests(unittest.TestCase):
    """Every discovered gate verb must be classified, so a new gate cannot accumulate unnoticed."""

    def test_every_discovered_gate_verb_is_classified(self):
        discovered = set(discover_gate_verbs(CLI_PATH.read_text(encoding="utf-8")))
        self.assertEqual(
            classify(discovered, WIRED_BY_DEFAULT, EXEMPT_OPT_IN),
            [],
        )

    def test_an_unclassified_new_gate_verb_fails(self):
        # THE PROPERTY THAT MAKES THIS FILE DURABLE, proven without touching the real tree: add a
        # seventh gate and it belongs to neither declared list, so classification refuses it.
        discovered = set(WIRED_BY_DEFAULT) | set(EXEMPT_OPT_IN) | {"brand-new-guard"}
        violations = classify(discovered, WIRED_BY_DEFAULT, EXEMPT_OPT_IN)
        self.assertEqual(len(violations), 1, violations)
        self.assertIn("brand-new-guard", violations[0])
        self.assertIn("NEITHER", violations[0])

    def test_a_removed_gate_verb_fails(self):
        discovered = set(WIRED_BY_DEFAULT) | set(EXEMPT_OPT_IN)
        discovered.discard("ipd-status-untooled-gate")
        violations = classify(discovered, WIRED_BY_DEFAULT, EXEMPT_OPT_IN)
        self.assertEqual(len(violations), 1, violations)
        self.assertIn("ipd-status-untooled-gate", violations[0])

    def test_every_exemption_carries_a_reason_and_citation(self):
        # An exemption with no citation is indistinguishable from an oversight, which is the state
        # this file exists to make impossible.
        for verb, citation in EXEMPT_OPT_IN.items():
            self.assertTrue(citation.strip(), f"{verb} has an empty exemption citation")


class WiredGateRegistrationTests(unittest.TestCase):
    """`.pre-commit-config.yaml` must register exactly the WIRED gates, in the established shape.

    This is a CONFIGURATION assertion only. It is NOT evidence that the stage fires.
    """

    def setUp(self) -> None:
        self.data = _config()
        self.by_verb = _hooks_by_entry_verb(self.data)

    def test_each_wired_gate_is_registered_for_its_declared_stages(self):
        default_stages = tuple(self.data.get("default_stages") or ())
        for verb, stages in WIRED_BY_DEFAULT.items():
            self.assertIn(
                verb, self.by_verb, f"wired gate verb {verb!r} is not registered"
            )
            hook = self.by_verb[verb]
            effective = tuple(hook.get("stages") or default_stages)
            self.assertEqual(effective, stages, f"{verb} runs in the wrong stages")

    def test_each_wired_gate_uses_the_established_local_hook_shape(self):
        local_ids = {
            hook.get("id")
            for repo in self.data["repos"]
            if repo.get("repo") == "local"
            for hook in repo.get("hooks") or []
        }
        for verb in WIRED_BY_DEFAULT:
            hook = self.by_verb[verb]
            self.assertIn(
                hook.get("id"), local_ids, f"{verb} must be a repo:local hook"
            )
            self.assertEqual(hook.get("language"), "system", verb)
            self.assertIs(hook.get("pass_filenames"), False, verb)
            self.assertIs(hook.get("always_run"), True, verb)

    def test_each_exempt_gate_is_absent_from_the_config(self):
        # Registering an exempt gate reverses a recorded decision (`diundn` OQ-01, reaffirmed by
        # `kbqpkn` OQ-01), so it must move to WIRED_BY_DEFAULT with that reversal recorded rather
        # than appearing here silently.
        raw = CONFIG_PATH.read_text(encoding="utf-8")
        for verb in EXEMPT_OPT_IN:
            self.assertNotIn(verb, self.by_verb, f"exempt gate {verb!r} is registered")
            self.assertNotIn(
                verb,
                raw,
                f"exempt gate {verb!r} appears in {CONFIG_PATH.name}; if this is intended, move it "
                "to WIRED_BY_DEFAULT and record the reversal of diundn OQ-01",
            )

    def test_no_unclassified_packaged_verb_is_registered(self):
        # The reverse direction: a hook entry running a gate verb that no list declares would be a
        # wiring nobody decided on.
        discovered = set(discover_gate_verbs(CLI_PATH.read_text(encoding="utf-8")))
        for verb in self.by_verb:
            if verb in discovered:
                self.assertIn(
                    verb, WIRED_BY_DEFAULT, f"{verb} is registered but not declared"
                )


if __name__ == "__main__":
    unittest.main()
