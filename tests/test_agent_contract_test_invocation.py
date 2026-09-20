"""Tests for testinvoke Order 01 (uyd3lw): the agent contract's test-invocation rule.

The defect this guards: nothing in the always-loaded agent contract said HOW to run this repo's
suite, so an agent overrode the configured `-n auto` with `-n0` (measured 4.7x slower on this
checkout: 35.44s vs 167.19s) and then spent minutes fighting a `-q` it had added itself, which
compounded with the configured `-q` into `-qq` and suppressed the very `N passed` summary line the
contract requires it to paste.

WHAT THIS FILE ASSERTS NOW, and what it deliberately stopped asserting.

The SUBJECT is the REAL pytest configuration: the rule tells every agent to rely on repo defaults,
so if those defaults change, the always-loaded contract becomes a lie that no amount of rereading
the prose detects. `PytestConfigurationTests` reads the configuration through pytest's OWN ini
loader (not a bespoke regex) and checks each promise the rule makes about it.

The prose pins are GONE. Four tests asserted particular English sentences of `AGENTS.md`
("HOW TO RUN THE SUITE", "make test", "addopts", "4x to 6x", "core count"). Those are
change-detectors over a document git already versions: a reworded rule is a normal, desirable edit
and every reword was a red test, while no defect was ever caught. What remains from them is ONE
table of the literal FLAGS and COMMANDS an agent is instructed to type verbatim, asserted against
the GENERATED source (`engine.agents_pointer_prose`) rather than against the rendered file, which
is strictly stronger: the generated text is what every adopter receives on install, and
`test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated` already
proves this repo's `AGENTS.md` block equals it byte for byte.

Also deleted, with where the property now lives:

* `test_rule_lives_inside_the_managed_block` (rule between the `aw:block` markers of AGENTS.md).
  Implied by two stronger existing facts: the rule is in the GENERATED pointer prose (table below),
  and `test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated`
  asserts AGENTS.md's marked block equals the generated block exactly. A byte-window scan of the
  rendered file cannot fail unless one of those two already has.
* `test_agents_md_contract_has_no_em_or_en_dash` plus its companion
  `test_ascii_hyphen_is_present_and_tolerated`. Two codepoints inside a fixed 4200-character
  WINDOW is the fragile kind of pin (insert a paragraph upstream and the window silently checks
  different text), and the companion existed only to prove the window was not vacuous. Replaced by
  `test_the_generated_contract_is_pure_ascii`, which refuses ANY non-ASCII character anywhere in
  the generated block and so tolerates the ASCII hyphen by construction. `docs_check.
  check_no_unicode_dashes` (via `tests/test_docs.py`) covers `docs/`, NOT `AGENTS.md`, so this
  property genuinely had no other owner.
"""

from __future__ import annotations

import shlex
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _pointer_prose() -> str:
    """The GENERATED contract text every adopter installs (not this repo's rendered copy)."""

    from agent_workflows import engine

    return engine.agents_pointer_prose(target_layout="aw")


def _pytest_ini() -> dict:
    """`[tool.pytest.ini_options]` as PYTEST ITSELF parses it.

    Read through `_pytest.config.findpaths.load_config_dict_from_file` rather than a hand-rolled
    regex so the values asserted below are the values the runner will actually use: a quoting or
    continuation change that fooled a regex would silently make every assertion here meaningless.
    """

    from _pytest.config.findpaths import load_config_dict_from_file

    cfg = load_config_dict_from_file(REPO_ROOT / "pyproject.toml")
    assert (
        cfg is not None
    ), "pyproject.toml carries no [tool.pytest.ini_options] section"
    return cfg


class InstalledInvocationRuleTests(unittest.TestCase):
    """The literal flags and commands the rule tells an agent to type (or never type).

    ONE table, not five tests. Every element below is load-bearing for the same reason the house
    exemplar (`tests/test_shared_checkout_contract.py`) keeps its `git` commands: something other
    than a human consumes the token verbatim. An agent types `python3 -m pytest` exactly; the three
    forbidden flags are the exact strings it must not append; `-o addopts=""` is the exact escape
    hatch it is told to use instead. Rewording the sentences AROUND them is free and expected, and
    is what the deleted prose pins wrongly forbade.

    Asserted against the GENERATED prose, so a rule that survives in this repo's AGENTS.md but was
    dropped from the generator (and therefore from every adopter's next install) still fails here.
    """

    #: (needle, why it is load-bearing)
    REQUIRED = (
        (
            "python3 -m pytest",
            "the invocation an agent is instructed to type verbatim; without it the rule names no "
            "command at all",
        ),
        (
            "-n0",
            "the exact flag that caused the measured 4.7x slowdown; a rule that does not spell it "
            "does not forbid it",
        ),
        (
            "-qq",
            "names the COMPOUND an added -q produces, which is why the summary line vanished; "
            "without it an agent reads 'do not add -q' as style advice",
        ),
        (
            "-p no:randomly",
            "the exact flag that disables the order randomization, so this spelling is what an "
            "agent greps its own command line for",
        ),
        (
            '-o addopts=""',
            "the ONE supported escape hatch; an agent that needs per-test counts and is not given "
            "this literal string invents flag-by-flag workarounds instead",
        ),
    )

    def test_the_generated_contract_carries_every_literal_an_agent_types(self):
        prose = _pointer_prose()
        missing = [
            f"  MISSING {needle!r}\n    needed because: {why}"
            for needle, why in self.REQUIRED
            if needle not in prose
        ]
        self.assertEqual(
            missing,
            [],
            f"the generated agent contract (engine.agents_pointer_prose) lost {len(missing)} of "
            f"{len(self.REQUIRED)} load-bearing literals of the test-invocation rule. Each is a "
            "flag or command consumed VERBATIM (typed by an agent, or matched against what it "
            "typed), so losing one silently disables that half of the rule for every adopter on "
            "their next install. Wording around these literals is NOT pinned and may change "
            "freely.\n"
            + "\n".join(missing)
            + "\n  FIX: restore the literal in `engine.agents_pointer_prose`, then reinstall (`aw "
            "setup-repo`) so this repo's AGENTS.md matches the generated block again.",
        )

    def test_the_generated_contract_is_pure_ascii(self):
        """Repo rule: no em/en dashes in authored user-facing prose. Asserted as a CHARACTER CLASS.

        Strictly stronger than the two `assertNotIn` pins it replaces (U+2014, U+2013 inside a
        4200-character window): it covers the WHOLE generated block, every non-ASCII codepoint, and
        cannot be silently re-aimed at different text by an unrelated paragraph inserted above.
        It also tolerates the ASCII hyphen by construction, which is why the separate
        "hyphens are still allowed" companion test is gone.
        """

        from agent_workflows import engine

        block = engine.agents_managed_block(target_layout="aw")
        bad = sorted({c for c in block if ord(c) > 127})
        self.assertEqual(
            bad,
            [],
            "the generated AGENTS.md managed block contains non-ASCII characters "
            f"{[hex(ord(c)) for c in bad]}: {bad}. This text is installed into every adopter's "
            "pointer file and is required to be ASCII (an em/en dash also violates the repo's "
            "user-facing prose rule). FIX: replace them in `engine.py` with ASCII equivalents.",
        )


class PytestConfigurationTests(unittest.TestCase):
    """E-04: the rule's factual claims about the repo defaults must still be TRUE.

    This is the load-bearing half of the file. The guidance tells agents a BARE run is already
    parallel, already quiet, and already the fast subset, then forbids the three flags that would
    override those defaults. Each claim is a property of `pyproject.toml`, not of any prose, so it
    is asserted against the configuration pytest itself parses.
    """

    @classmethod
    def setUpClass(cls):
        cls.cfg = _pytest_ini()
        cls.addopts = cls.cfg.get("addopts", "")
        # Token-level, because substring matching cannot tell `-n auto` from `--numprocesses=auto`
        # written into a marker expression, and `-q` from `-qq`.
        cls.tokens = shlex.split(cls.addopts) if isinstance(cls.addopts, str) else []

    def test_addopts_still_supplies_parallelism(self):
        """If the repo default stops being parallel, AGENTS.md's advice becomes a lie. Fail loudly.

        STRENGTHENED from a substring check on the raw string to a TOKEN check: `-n` must be
        present and its VALUE must be `auto`, so `-n 0` (which is exactly the serial configuration
        the rule exists to prevent, and which contains the substring `-n `) can no longer pass.
        """

        tokens = self.tokens
        supplied = None
        for i, tok in enumerate(tokens):
            if tok == "-n" and i + 1 < len(tokens):
                supplied = tokens[i + 1]
            elif tok.startswith("-n") and tok != "-n":
                supplied = tok[2:]
            elif tok.startswith("--numprocesses"):
                supplied = tok.partition("=")[2] or (
                    tokens[i + 1] if i + 1 < len(tokens) else ""
                )
        self.assertEqual(
            supplied,
            "auto",
            "AGENTS.md tells every agent a BARE `python3 -m pytest` is ALREADY parallel and that "
            "adding `-n0` is the mistake. The configured worker count is now "
            f"{supplied!r} (addopts: {self.addopts!r}), so that guidance is wrong: either the "
            "suite now runs serially by default, or the flag moved. FIX: restore `-n auto` in "
            "`[tool.pytest.ini_options] addopts`, or update the rule in "
            "`engine.agents_pointer_prose` in the SAME change.",
        )

    #: (claim the AGENTS.md rule makes, predicate over the parsed config, why it is load-bearing)
    CLAIMS = (
        (
            "a bare run is already quiet",
            lambda tokens, cfg: "-q" in tokens,
            "the rule says an agent must NOT add its own `-q`; that instruction is only correct "
            "while exactly one is configured",
        ),
        (
            "adding one more -q compounds into -qq",
            lambda tokens, cfg: tokens.count("-q") == 1 and "-qq" not in tokens,
            "the measured harm (the `N passed` summary suppressed) needs the configured count to "
            "be exactly ONE: at zero, adding `-q` is harmless; at two, the summary is ALREADY "
            "gone and the contract's paste-the-output requirement is unsatisfiable by anyone",
        ),
        (
            "a bare run is already scoped to the fast subset",
            lambda tokens, cfg: (
                any(t == "-m" for t in tokens)  # the marker filter is present
                and "not slow" in " ".join(tokens)
            ),
            "the rule claims the default run is the fast subset; if the `-m` filter goes away, a "
            "bare run becomes the FULL suite and the agent's time estimate is wrong by minutes",
        ),
        (
            "the `slow` marker the filter names is declared",
            lambda tokens, cfg: any(
                str(m).split(":")[0].strip() == "slow"
                for m in (cfg.get("markers") or ())
            ),
            "an undeclared marker in `-m` is a silent no-op under some pytest configurations, so "
            "the fast-subset claim would be false while the flag still looked present",
        ),
        (
            "order randomization exists to be disabled",
            lambda tokens, cfg: (
                "pytest-randomly"
                in (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
            ),
            "the rule forbids `-p no:randomly` BECAUSE randomization surfaces order-dependence "
            "bugs; drop the plugin from the test dependencies and the prohibition guards nothing",
        ),
    )

    def test_every_claim_the_rule_makes_about_the_defaults_still_holds(self):
        broken = []
        for claim, predicate, why in self.CLAIMS:
            try:
                ok = bool(predicate(self.tokens, self.cfg))
            except Exception as exc:  # a predicate that cannot even run is a failure
                ok, why = False, f"{why} (predicate raised {exc!r})"
            if not ok:
                broken.append(
                    f"  BROKEN CLAIM: {claim}\n    load-bearing because: {why}"
                )
        self.assertEqual(
            broken,
            [],
            f"{len(broken)} of {len(self.CLAIMS)} factual claims the always-loaded test-invocation "
            "rule makes about this repo's pytest defaults are no longer true "
            f"(addopts: {self.addopts!r}). The rule tells every agent to depend on these defaults, "
            "so a broken claim means the contract is instructing agents to rely on something that "
            "does not exist.\n"
            + "\n".join(broken)
            + "\n  FIX: restore the configuration in `[tool.pytest.ini_options]`, or change the "
            "rule in `engine.agents_pointer_prose` in the SAME change so prose and config cannot "
            "drift.",
        )

    def test_the_rule_quotes_flags_that_are_actually_configured(self):
        """Kept separate: this is the DRIFT direction, prose -> config, not config -> prose.

        The tests above ask "is the configuration still what the rule promises". This asks the
        opposite and equally real question: does the rule quote a flag that no longer exists? A
        stale quotation is how an agent ends up passing a flag pytest rejects. Only flags the rule
        QUOTES AS CONFIGURED are listed; the forbidden flags are deliberately absent from addopts.
        """

        prose = _pointer_prose()
        stale = []
        for flag in ("-n auto", "--dist=worksteal"):
            in_prose = flag in prose
            in_config = flag in self.addopts
            if in_prose and not in_config:
                stale.append(
                    f"  {flag!r}: quoted by the contract as configured, but absent from addopts "
                    f"({self.addopts!r})"
                )
            if in_config and not in_prose:
                stale.append(
                    f"  {flag!r}: configured, but the contract no longer quotes it, so an agent "
                    "cannot tell a bare run already supplies it"
                )
        self.assertEqual(
            stale,
            [],
            "the test-invocation rule and `[tool.pytest.ini_options] addopts` disagree about which "
            "flags a bare run already supplies:\n"
            + "\n".join(stale)
            + "\n  FIX: change both in the same commit; that coupling is the entire point of this "
            "test.",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
