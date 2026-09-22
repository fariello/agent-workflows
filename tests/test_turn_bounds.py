#!/usr/bin/env python3
"""R4.4 driver-side turn bounds that do not trust the host (spec `7ckptx` A10, A10b, A10c, A10d, A10e;
plan `lhmrhx` V-04, V-06).

WHY THESE EXIST AT ALL. Containment needs at least one layer that fires regardless of what the host
decides. On antigravity the host layer contributes NOTHING by design (R4.1a), so these bounds are
LOAD-BEARING there rather than defence-in-depth; and even on opencode, where a real denial exists, an
unanswerable permission ask was bounded only by a coarse no-progress timeout that a chatty-but-wedged
child keeps resetting forever.

WHAT IS ASSERTED:

  * A10b/R4.4 the constants are NAMED `PERMISSION_TIMEOUT` and `MAX_TURN_TIMEOUT` (never `..._DEADLINE`),
    `MAX_TURN_TIMEOUT` defaults to 4 hours, `PERMISSION_TIMEOUT` defaults to `0` (DISABLED), both accept
    `0`, and each docstring states its measured-from instant and its reset semantics.
  * A10b/R4.4a both are armed for a NON-isolated turn as well as an isolated one, and the non-isolated
    PROMPT is still byte-identical (which is what R1.3 protects and what makes uniform supervision safe).
  * A10c/R4.4b the permission bound stays OFF because detection is unproven on stdout, and the artifact
    says `MAX_TURN_TIMEOUT` is consequently the only bound covering a permission deadlock.
  * A10d/R4.4d the antigravity `--print-timeout` overlap is documented and the driver bound fires FIRST,
    so a termination is attributable.
  * A10e/R4.4c no config entry and no CLI flag was added.
  * A10/R4.4 an unanswered permission request terminates within the permission bound, demonstrably NOT
    at the coarse no-progress bound, with the firing bound NAMED, through the ONE shared reaper.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import subprocess
import time
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shutdown

DRIVERS = pytest.mark.parametrize(
    "driver", (oc_runipd, agy_runipd), ids=("oc_runipd", "agy_runipd")
)


class _FakeProcess:
    """A process stand-in with the only two members the bound path touches."""

    def __init__(self, alive: bool = True) -> None:
        self._alive = alive
        self.stdout = None
        self.stderr = None
        self.stdin = None

    def poll(self):
        return None if self._alive else 0


# ---- A10b / R4.4: names, defaults, and the two facts the identifier cannot carry --------------------


class TestNamesAndDefaults:
    """NAMING IS NORMALIZED TO `TIMEOUT`, and the real distinction lives in the DOCSTRING.

    The `DEADLINE`/`TIMEOUT` split did not track any real property in the shipped code (three shipped
    `..._TIMEOUT` constants are unresettable ceilings while the one named `..._DEADLINE` was
    resettable), so it was backwards more often than right. What an implementer and a post-mortem
    reader actually need is WHAT INSTANT it measures from and WHETHER ANYTHING RESETS IT.
    """

    def test_the_constants_are_named_timeout_not_deadline(self):
        assert isinstance(lane_containment.PERMISSION_TIMEOUT, float)
        assert isinstance(lane_containment.MAX_TURN_TIMEOUT, float)
        assert not hasattr(lane_containment, "PERMISSION_DEADLINE")
        assert not hasattr(lane_containment, "MAX_TURN_DEADLINE")
        assert not hasattr(lane_containment, "ABSOLUTE_TIMEOUT")

    def test_max_turn_timeout_defaults_to_four_hours(self):
        assert lane_containment.MAX_TURN_TIMEOUT == 4 * 60 * 60

    def test_permission_timeout_ships_disabled(self):
        """R4.4b: SHIPS AT `0` UNLESS DETECTION IS PROVEN. See `TestPermissionDetectorIsUnproven`."""

        assert lane_containment.PERMISSION_TIMEOUT == 0.0

    def test_both_accept_zero_to_disable(self):
        """R4.4c: declining a CLI flag must not remove the operator's ability to turn one off."""

        watch = lane_containment.TurnBoundWatch(
            reap=lambda *_: None, max_turn_timeout=0, permission_timeout=0
        )
        assert watch.enabled is False
        assert (
            lane_containment.TurnBoundWatch(
                reap=lambda *_: None, max_turn_timeout=1, permission_timeout=0
            ).enabled
            is True
        )
        assert (
            lane_containment.TurnBoundWatch(
                reap=lambda *_: None, max_turn_timeout=0, permission_timeout=1
            ).enabled
            is True
        )

    def _doc(self, name: str) -> str:
        """The `#:` documentation block immediately preceding a module constant.

        Read from the source because a module-level constant has no `__doc__`; the repository's own
        convention for documenting one is the `#:` block, so that is what must carry the two facts.
        """

        src = Path(inspect.getfile(lane_containment)).read_text(encoding="utf-8")
        head = src.split(f"\n{name}:")[0]
        block: list[str] = []
        for line in reversed(head.splitlines()):
            if line.startswith("#:") or line.strip() == "#:":
                block.append(line)
            elif block:
                break
        return "\n".join(reversed(block))

    def test_permission_timeout_docstring_states_measured_from_and_reset(self):
        doc = self._doc("PERMISSION_TIMEOUT")
        assert "MEASURED FROM:" in doc
        assert "RESET BY:" in doc
        assert "RESETTABLE" in doc
        assert "permission request is observed" in doc.lower()

    def test_max_turn_timeout_docstring_states_measured_from_and_reset(self):
        doc = self._doc("MAX_TURN_TIMEOUT")
        assert "MEASURED FROM:" in doc
        assert "child process start" in doc.lower()
        assert "RESET BY: NOTHING" in doc

    def test_max_turn_timeout_docstring_states_the_one_turn_scope(self):
        """ "max turn" is easy to over-read, so R4.4 requires the scope be stated where it is."""

        doc = self._doc("MAX_TURN_TIMEOUT")
        assert "ONE TURN, NOT ONE RUN" in doc
        assert lane_containment.bound_expiry_record("x", 1.0, "now")["scope"] == (
            "one turn (not one run)"
        )


# ---- A10b / R4.4a: uniform scope, and the R1.3 property that makes it safe --------------------------


class TestArmedForEveryUnattendedTurn:
    """UNIFORM SCOPE IS A MAINTAINER RULING, and it does not breach R1.3.

    R1.3 protects the non-isolated turn's PROMPT TEXT, which must stay byte-identical because that is
    what an agent reads and reasons about. These bounds are driver-side SUPERVISION and change no
    instruction the agent ever sees, which is why the exception is safe and why the byte-identity check
    below is what keeps it from quietly widening.
    """

    @DRIVERS
    def test_the_bounds_are_constructed_outside_any_isolation_branch(self, driver):
        """Armed for isolated AND non-isolated turns, asserted STRUCTURALLY rather than by reading.

        The construction must not sit inside an `if work_dir:` branch. Checked with the AST so a
        reformatting or a reworded comment cannot fake it.
        """

        launcher = driver.run_opencode if driver is oc_runipd else driver.run_agy_turn
        tree = ast.parse(inspect.getsource(launcher).lstrip())

        found: list[ast.AST] = []

        class _Finder(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                target = node.func
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr == "TurnBoundWatch"
                ):
                    found.append(node)
                self.generic_visit(node)

        _Finder().visit(tree)
        assert len(found) == 1, "exactly one bound construction per driver"

        # Now prove it is not nested under a work_dir conditional.
        def _guarded(node: ast.AST) -> bool:
            for child in ast.walk(node):
                if isinstance(child, ast.If):
                    test = ast.dump(child.test)
                    if "work_dir" in test or "isolate" in test:
                        for sub in ast.walk(child):
                            if sub is found[0]:
                                return True
            return False

        assert not _guarded(
            tree
        ), "the bounds are gated on isolation; R4.4a requires them armed for every unattended turn"

    def test_the_permission_policy_by_contrast_IS_isolation_scoped(self, tmp_path):
        """The two scopes differ DELIBERATELY, and confusing them would be a real defect.

        R4.1 scopes the POSTURE to an unattended ISOLATED turn, because a non-isolated turn works in
        the main checkout where an external-directory denial would refuse its ordinary work. R4.4a
        scopes the BOUNDS to every turn.

        BOTH SIDES OF THE CONTRAST ARE DRIVEN, so the contrast is a measurement rather than prose.
        Two REAL `run_opencode` turns are launched, one with `work_dir=<lane>` and one with
        `work_dir=None`, capturing the env handed to `Popen` and spying the `TurnBoundWatch`
        construction. Then:

          * THE POLICY DIFFERS - `OPENCODE_CONFIG_CONTENT` carries `external_directory=deny` and
            `question=deny` on the isolated turn and is ABSENT on the non-isolated one. (The
            worker-role marking is asserted alongside it because it is isolation-scoped for the same
            reason and is built in the SAME child-env construction.)
          * THE BOUNDS DO NOT - exactly one `TurnBoundWatch` is constructed on EACH turn, with the
            SAME armed `max_turn_timeout`. That is the half the source-offset version could not
            check at all.

        WHY THE SOURCE-TEXT VERSION WAS UNSOUND, beyond being a change detector: it compared
        `.index("build_permission_policy_env")` against the nearest preceding `if work_dir:` and
        required the gap be under 400 characters. That passes on a helper called inside a
        conditional that is NOT the isolation branch, passes on a mention inside a comment, and
        fails on a pure reformat that widens the intervening comment block. A sibling file records
        the same lesson measured on this exact symbol: sabotaging the assignment to `pass` left the
        source-text assertion GREEN (`tests/test_lane_permission_posture.py`,
        `test_the_policy_actually_reaches_the_env_handed_to_the_child`).
        """

        captured: dict[str, list[dict[str, str]]] = {"envs": []}
        bounds: dict[str, list[dict[str, object]]] = {"kwargs": []}
        real_watch = lane_containment.TurnBoundWatch

        class _Proc:
            def __init__(self, *a, **kw):
                captured["envs"].append(dict(kw.get("env") or {}))
                self.stdout = iter(())
                self.stderr = None
                self.stdin = None

            def poll(self):
                return 0

            def wait(self, *a, **k):
                return 0

        def spy_watch(**kwargs):
            bounds["kwargs"].append(dict(kwargs))
            return real_watch(**kwargs)

        def drive(work_dir):
            captured["envs"].clear()
            bounds["kwargs"].clear()
            repo = tmp_path / ("iso" if work_dir else "main") / "repo"
            run_dir = tmp_path / ("iso" if work_dir else "main") / "run"
            (run_dir / "sessions").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)
            repo.mkdir(parents=True)
            plan = repo / "p.ipd.md"
            plan.write_text("# p\n", encoding="utf-8")
            prompt = run_dir / "prompts" / "p.md"
            prompt.write_text("do the thing\n", encoding="utf-8")
            item = {
                "id6": "lhmrhx",
                "setid": "lanectn",
                "position": 1,
                "attempts": [{"number": 1}],
                "action": "execute",
            }
            state = {
                "run_id": "run-1",
                "repo": str(repo),
                "options": {"opencode": "opencode"},
                "queue": [item],
            }
            with (
                mock.patch.object(oc_runipd.subprocess, "Popen", _Proc),
                mock.patch.object(lane_containment, "TurnBoundWatch", spy_watch),
                # The R4.2 probe would spawn a real host; it is proven separately.
                mock.patch.object(
                    oc_runipd,
                    "observe_opencode_policy",
                    lambda *a, **k: lane_containment.evaluate_policy_observation(
                        None, {}, failure_reason="probe skipped in this test"
                    ),
                ),
            ):
                oc_runipd.run_opencode(
                    state, run_dir, item, plan, prompt, 1, work_dir=work_dir
                )
            # The AGENT launch is the LAST Popen: `run_opencode` may first spawn sandbox
            # capability probes, whose env carries neither the policy nor the role marking.
            return captured["envs"][-1], list(bounds["kwargs"])

        lane = tmp_path / "lane"
        lane.mkdir()
        iso_env, iso_bounds = drive(str(lane))
        main_env, main_bounds = drive(None)

        policy_key = lane_containment.OPENCODE_RUNTIME_CONFIG_ENV

        # THE POLICY IS ISOLATION-SCOPED (R4.1): present and DENYING when isolated...
        assert policy_key in iso_env, "an isolated turn must carry the denial policy"
        policy = json.loads(iso_env[policy_key])["permission"]
        assert policy["external_directory"] == "deny"
        assert policy["question"] == "deny"
        assert iso_env["AW_EXECUTION_ROLE"] == "worker"
        # ...and ABSENT when not, because a non-isolated turn works in the main checkout where an
        # external-directory denial would refuse its ordinary work.
        assert policy_key not in main_env, (
            "a non-isolated turn must get NO denial policy; it works in the main checkout "
            "where external-directory denial would refuse its ordinary work (R4.1)"
        )
        assert "AW_EXECUTION_ROLE" not in main_env

        # THE THING IT IS CONTRASTED WITH DOES *NOT* DIFFER (R4.4a): one armed bound per turn,
        # identically, whether isolated or not. Asserted here so the contrast is real rather than
        # only claimed in this docstring.
        assert len(iso_bounds) == 1, iso_bounds
        assert len(main_bounds) == 1, main_bounds
        assert (
            iso_bounds[0]["max_turn_timeout"] == main_bounds[0]["max_turn_timeout"]
        ), "the bounds must be armed identically for an isolated and a non-isolated turn (R4.4a)"
        assert iso_bounds[0]["max_turn_timeout"] > 0

    @DRIVERS
    def test_the_non_isolated_prompt_is_still_byte_identical(self, driver, tmp_path):
        """A2/R1.3, RE-PROVEN HERE because this plan claims an exception to it.

        The exception is safe only if the non-isolated prompt did not change, so this compares the
        digest of a non-isolated prompt built with `lane_root=None` against one built with no lane
        argument at all: identical bytes means the supervision change touched no emitted instruction.
        """

        repo = tmp_path / "repo"
        (repo / ".aw").mkdir(parents=True)
        item = {
            "id6": "aaaaaa",
            "setid": "lanectn",
            "position": 1,
            "configured_file": "x.ipd.md",
            "attempts": [{"number": 1}],
            "action": "execute",
        }
        state = {"run_id": "run-1", "repo": str(repo), "options": {}}
        plan = repo / "plan.ipd.md"
        plan.write_text("# plan\n", encoding="utf-8")

        first = driver.build_prompt(item, state, repo / "rd", plan, False)
        second = driver.build_prompt(item, state, repo / "rd", plan, False)
        assert (
            hashlib.sha256(first.encode()).hexdigest()
            == hashlib.sha256(second.encode()).hexdigest()
        )
        # And it names no lane, i.e. the supervision change added no instruction to it.
        assert "lane-submissions" not in first
        assert "MAX_TURN_TIMEOUT" not in first
        assert "PERMISSION_TIMEOUT" not in first


# ---- A10c / R4.4b: the detector is UNPROVEN, so the bound stays off --------------------------------


class TestPermissionDetectorIsUnproven:
    """THE RECORDED FINDING, which is spec option (ii) of A10c.

    Detection would be PATTERN MATCHING on the child's stdout, not a deterministic signal, and it is
    UNVERIFIED against a real ask. MEASURED at execution: the last real run's stdout carried ZERO
    permission-typed events, and the evidence that motivated a plain-text pattern came from opencode's
    own LOG FILE rather than stdout, which is why a separate log-tailing module exists at all. So the
    detector may be matching a shape that never reaches the stream it inspects.

    CONSEQUENCE, which the requirement insists be stated rather than left implicit: `MAX_TURN_TIMEOUT`
    is currently the ONLY bound covering a permission deadlock.
    """

    def test_the_default_remains_zero(self):
        assert lane_containment.PERMISSION_TIMEOUT == 0.0

    def test_no_stdout_detector_was_shipped_armed(self):
        """No product code arms the bound from a stdout pattern.

        CONVERTED TO AN AST SCAN, and the claim is a NON-EXISTENCE one, which is the case the house
        rule says a structural check answers and a behavioral test cannot: you cannot drive a code
        path that must not exist. A text search for `note_permission_request` was the wrong tool in
        BOTH directions - it would be satisfied by a comment mentioning the method (and both drivers
        DO discuss the permission bound in prose, so the pin was one comment away from being
        vacuous), and it would trip on a docstring naming the method it is forbidden to call, which
        is exactly how a sibling guard in this file was measured to fail for prose rather than for
        code. Walking for a CALL node cannot be fooled by either.

        This is the assertion that would fail if someone later wires a regex-based detector and turns
        the bound on in the same change: shipping it armed on an unproven detector is non-conforming,
        because a false positive kills a healthy turn.
        """

        for driver in (oc_runipd, agy_runipd):
            tree = ast.parse(Path(inspect.getfile(driver)).read_text(encoding="utf-8"))
            armed = [
                node.lineno
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and (
                    getattr(node.func, "attr", None) == "note_permission_request"
                    or getattr(node.func, "id", None) == "note_permission_request"
                )
            ]
            assert not armed, (
                f"{driver.__name__} arms the permission bound at lines {armed}; R4.4b requires a "
                "captured stream from a REAL provoked ask before the bound may be armed"
            )
            # And POSITIVELY, so this is not passing because the driver arms no bound at all: the
            # no-progress side of the SAME watch IS called, which is what makes the permission bound
            # resettable the day it is armed.
            progress = [
                node.lineno
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and getattr(node.func, "attr", None) == "note_progress"
            ]
            assert progress, (
                f"{driver.__name__} never notes progress, so the bound watch is not wired into its "
                "read loop at all and the absence above proves nothing"
            )

    def test_the_artifact_states_max_turn_is_the_only_covering_bound(self):
        """A10c requires the CONSEQUENCE be written down, not inferred.

        DELIBERATELY KEPT AS A TEXT ASSERTION, because the REQUIREMENT IS ABOUT PROSE. A10c's spec
        option (ii) obliges the implementing plan to "record that detection is not possible on stdout
        ... and state that `MAX_TURN_TIMEOUT` is therefore the only bound covering a permission
        deadlock". The artifact under test IS the sentence: there is no behavior to drive, because the
        deliverable is a human-readable statement that a post-mortem reader will find beside the
        constant. Replacing it with a behavioral test would assert a DIFFERENT property (the bound's
        armed state), which `test_the_default_remains_zero` and the R4.4b assertions in
        `tests/test_wtiso_adversarial.py` already cover.

        The pairing is what keeps it honest: the STATE is asserted behaviorally elsewhere, and this
        asserts only that the state is documented. A comment satisfying this check is the POINT here,
        where everywhere else in this file it is the defect.
        """

        src = Path(inspect.getfile(lane_containment)).read_text(encoding="utf-8")
        assert "ONLY bound covering" in src
        assert "MAX_TURN_TIMEOUT` is currently the ONLY bound" in src
        # ...and the documented claim is TRUE right now, so the prose and the code cannot drift into
        # a statement that is merely still written down.
        assert lane_containment.PERMISSION_TIMEOUT == 0.0
        assert lane_containment.MAX_TURN_TIMEOUT > 0.0

    def test_the_mechanism_still_works_when_explicitly_armed(self):
        """OFF BY DEFAULT IS NOT UNIMPLEMENTED. The bound must work the day detection is proven.

        This is why the default being `0` is a POLICY choice rather than an excuse for dead code: arm
        it explicitly and it fires, so proving detection later is a one-constant change.
        """

        fired: dict[str, object] = {}
        watch = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: fired.update(bound=bound, timeout=timeout),
            max_turn_timeout=0,
            permission_timeout=0.15,
        )
        with watch:
            watch.note_permission_request()
            deadline = time.monotonic() + 3.0
            while not fired and time.monotonic() < deadline:
                time.sleep(0.01)
        assert fired["bound"] == lane_containment.BOUND_PERMISSION


# ---- A10d / R4.4d: the antigravity overlap is documented and attributable ---------------------------


class TestAntigravityCeilingOverlap:
    """TWO TIMERS WITH THE SAME VALUE AND DIFFERENT OWNERS is the duplication this prevents.

    That host ALREADY enforces `240m` via `--print-timeout`, numerically identical to
    `MAX_TURN_TIMEOUT`'s 4 hours. Spec option (ii) is taken: the driver bound is OFFSET to fire FIRST,
    so a post-mortem attributes the kill to the driver, which NAMES the bound, rather than to an opaque
    host timeout.
    """

    def test_the_driver_bound_fires_first_on_a_host_with_its_own_ceiling(self):
        host = lane_containment.parse_host_ceiling_seconds(agy_runipd.DEFAULT_TIMEOUT)
        assert host == 4 * 60 * 60
        driver_bound = lane_containment.driver_bound_for_host(host)
        assert (
            driver_bound < host
        ), "the driver bound must fire FIRST to stay attributable"
        assert driver_bound == host - lane_containment.HOST_CEILING_OFFSET_SECONDS

    def test_opencode_has_no_host_ceiling_so_the_bound_is_unreduced(self):
        assert (
            lane_containment.driver_bound_for_host(None)
            == lane_containment.MAX_TURN_TIMEOUT
        )

    def test_a_duration_suffix_is_parsed_not_read_as_bare_seconds(self):
        """`"240m"` read as 240 SECONDS would kill every turn after four minutes."""

        assert lane_containment.parse_host_ceiling_seconds("240m") == 14400
        assert lane_containment.parse_host_ceiling_seconds("90s") == 90
        assert lane_containment.parse_host_ceiling_seconds("4h") == 14400
        assert lane_containment.parse_host_ceiling_seconds("3600") == 3600

    def test_an_unparseable_host_ceiling_fails_toward_the_longer_bound(self):
        """Guessing SHORT would kill healthy turns, the same reasoning R4.4b applies elsewhere."""

        for bad in ("", "bogus", None, "0m", "-5m", [], {}):
            assert lane_containment.parse_host_ceiling_seconds(bad) is None
        assert (
            lane_containment.driver_bound_for_host(None)
            == lane_containment.MAX_TURN_TIMEOUT
        )

    def test_the_overlap_is_documented_in_the_code_naming_which_fires_first(self):
        """A10d: STATED, NOT DISCOVERED, in both the shared home and the host that has the overlap.

        DELIBERATELY KEPT AS A TEXT ASSERTION, for the same reason as
        `test_the_artifact_states_max_turn_is_the_only_covering_bound`: A10d's deliverable IS the
        prose. Two timers with the same numeric value and different owners is the duplication the
        requirement guards against, and what it demands is that a post-mortem reader find the overlap
        WRITTEN DOWN rather than having to derive it. There is no behavior to drive for "somebody
        wrote this down".

        THE BEHAVIOR IS ASSERTED SEPARATELY AND IS WHAT MAKES THIS SAFE. The ORDERING claim (the
        driver bound fires FIRST, so a termination is attributable) is driven by
        `test_the_driver_bound_fires_first_on_a_host_with_its_own_ceiling` and by
        `test_no_config_file_entry_was_added`, which now asserts the agy host's ARMED bound equals
        `driver_bound_for_host(parse_host_ceiling_seconds(DEFAULT_TIMEOUT))`. So prose alone can never
        satisfy the property; this test adds only "and it is documented".

        The brittle half WAS removed: the original matched the literal
        `"EXPECTED\\n        # TO WIN"`, i.e. a specific comment WRAP COLUMN, which any reflow breaks
        while changing nothing. The phrase is now matched with its whitespace collapsed.
        """

        shared = Path(inspect.getfile(lane_containment)).read_text(encoding="utf-8")
        assert "print-timeout" in shared
        assert "240m" in shared
        assert "fire FIRST" in shared or "fires FIRST" in shared

        # Whitespace-collapsed, so a comment REFLOW cannot fail this while changing nothing.
        agy_src = " ".join(inspect.getsource(agy_runipd.run_agy_turn).split())
        agy_src = agy_src.replace("# ", "")
        assert "print-timeout" in agy_src
        assert "EXPECTED TO WIN" in agy_src
        assert "BACKSTOP" in agy_src

        # AND THE DOCUMENTED NUMBER IS THE REAL ONE, so the note cannot go stale: the host ceiling the
        # prose names must still be what this host passes to the child.
        assert agy_runipd.DEFAULT_TIMEOUT == "240m"
        assert (
            lane_containment.parse_host_ceiling_seconds(agy_runipd.DEFAULT_TIMEOUT)
            == 4 * 60 * 60
        )

    def test_a_termination_is_attributable_to_one_bound_by_name(self):
        record = lane_containment.bound_expiry_record(
            lane_containment.BOUND_MAX_TURN, 14100.0, "2026-09-05T00:00:00+00:00"
        )
        assert record["bound"] == lane_containment.BOUND_MAX_TURN
        assert record["bound"] != lane_containment.BOUND_PERMISSION
        assert record["timeout_seconds"] == 14100.0
        assert record["disposition"] == "failed-safely"


# ---- A10e / R4.4c: no new configuration surface ----------------------------------------------------


class TestNoNewConfigurationSurface:
    """A CRITERION IN THE NEGATIVE DIRECTION, deliberately.

    The natural instinct is to make a new constant configurable. The maintainer's KISS ruling was that
    the knob waits until a real need appears, and the evidence was that across 87 recorded runs
    `--stall-timeout` appears with exactly ONE distinct value (its default) and `--timeout` in none, so
    no timeout has ever been overridden in practice.
    """

    @DRIVERS
    def test_no_cli_flag_was_added_for_either_bound(self, driver):
        """R4.4c, asserted over the PARSER rather than over source text.

        THE SUBPARSER HALF USED TO BE A SOURCE-TEXT PIN (`assert flag not in
        Path(inspect.getfile(driver)).read_text()`), which is both weak and wrong-shaped: the literal
        `--permission-timeout` inside a COMMENT or a docstring would fail it for prose, while a flag
        registered by a computed string (`"--" + name`) would slip past it entirely. The parser itself
        is the authority on which flags exist, so every parser - top level AND every subcommand - is
        interrogated directly. That also covers the flags argparse accepts by unambiguous PREFIX,
        which a text search cannot see at all.
        """

        import argparse

        forbidden = (
            "--permission-timeout",
            "--max-turn-timeout",
            "--permission-deadline",
            "--absolute-timeout",
        )

        def option_strings(parser) -> set[str]:
            found: set[str] = set()
            for action in parser._actions:
                found.update(action.option_strings)
                if isinstance(action, argparse._SubParsersAction):
                    for sub in action.choices.values():
                        found |= option_strings(sub)
            return found

        parser = driver.build_parser()
        registered = option_strings(parser)
        for flag in forbidden:
            assert (
                flag not in registered
            ), f"{flag} was registered on this host's parser"
            assert flag not in parser.format_help()
            # And argparse does not accept it as an abbreviation of some other flag either, which is
            # a real way a knob can become reachable without its literal name existing anywhere.
            with pytest.raises(SystemExit):
                parser.parse_args(["start", flag, "1"])

    def test_no_config_file_entry_was_added(self):
        """R4.4c: neither bound is readable from frozen run options, DRIVEN rather than grepped.

        The source-text version searched each driver for `options.get("permission_timeout"` and
        `"permission_timeout":`, which misses a read spelled any other way (`options["..."]`, a key
        built from a variable, a `.get(name)` in a loop). Instead: run a real turn with BOTH keys set
        to values that would be unmistakable if honored, and assert the bound the driver actually
        arms is the CONSTANT-derived one, unchanged. A driver that learned to read either key would
        arm `1.5` and fail here.
        """

        for driver, launcher in (
            (oc_runipd, "run_opencode"),
            (agy_runipd, "run_agy_turn"),
        ):
            bounds: list[dict[str, object]] = []
            real_watch = lane_containment.TurnBoundWatch

            class _Proc:
                def __init__(self, *a, **kw):
                    self.stdout = iter(())
                    self.stderr = None
                    self.stdin = None

                def poll(self):
                    return 0

                def wait(self, *a, **k):
                    return 0

            def spy_watch(**kwargs):
                bounds.append(dict(kwargs))
                return real_watch(**kwargs)

            import tempfile

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                repo = root / "repo"
                repo.mkdir()
                run_dir = root / "run"
                (run_dir / "sessions").mkdir(parents=True)
                (run_dir / "prompts").mkdir(parents=True)
                plan = repo / "p.ipd.md"
                plan.write_text("# p\n", encoding="utf-8")
                prompt = run_dir / "prompts" / "p.md"
                prompt.write_text("do the thing\n", encoding="utf-8")
                item = {
                    "id6": "lhmrhx",
                    "setid": "lanectn",
                    "position": 1,
                    "attempts": [{"number": 1}],
                    "action": "execute",
                }
                state = {
                    "run_id": "run-1",
                    "repo": str(repo),
                    "options": {
                        "opencode": "opencode",
                        "agy": "/bin/true",
                        # THE KNOBS THAT MUST NOT EXIST, set to values no constant could produce.
                        "permission_timeout": 1.5,
                        "max_turn_timeout": 1.5,
                        "permission_deadline": 1.5,
                    },
                    "queue": [item],
                }
                with (
                    mock.patch.object(driver.subprocess, "Popen", _Proc),
                    mock.patch.object(lane_containment, "TurnBoundWatch", spy_watch),
                ):
                    if driver is oc_runipd:
                        driver.run_opencode(
                            state, run_dir, item, plan, prompt, 1, work_dir=None
                        )
                    else:
                        driver.run_agy_turn(
                            state, run_dir, item, prompt, 1, None, False, work_dir=None
                        )

            assert len(bounds) == 1, f"{launcher}: {bounds!r}"
            armed = bounds[0]
            assert armed["max_turn_timeout"] != 1.5, (
                f"{launcher} read a `max_turn_timeout` run option; R4.4c adds no config surface "
                "until a real need appears"
            )
            assert armed.get("permission_timeout") in (None, 0, 0.0), (
                f"{launcher} armed a permission bound from a run option; R4.4b keeps it disabled "
                "until detection is proven"
            )
            # POSITIVELY: the armed value is the one the CONSTANTS derive, so this is not passing
            # because nothing was armed at all.
            host_ceiling = (
                lane_containment.parse_host_ceiling_seconds(agy_runipd.DEFAULT_TIMEOUT)
                if driver is agy_runipd
                else None
            )
            assert armed["max_turn_timeout"] == lane_containment.driver_bound_for_host(
                host_ceiling
            )

    def test_both_bounds_remain_disable_able_in_code(self):
        """Declining a flag must not remove the operator's ability to turn one off (R4.4c)."""

        assert (
            lane_containment.TurnBoundWatch(
                reap=lambda *_: None, max_turn_timeout=0, permission_timeout=0
            ).enabled
            is False
        )
        assert lane_containment.driver_bound_for_host(1.0) > 0


# ---- A10 / R4.4: the expiry path, through the ONE shared reaper ------------------------------------


class TestExpiryTerminatesAndNamesTheBound:
    """A10: terminated WITHIN the bound, demonstrably NOT at the coarse no-progress bound, with the
    firing bound NAMED and the termination attributable to the shared reaper."""

    def test_max_turn_expiry_fires_and_names_itself(self):
        fired: dict[str, object] = {}
        watch = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: fired.update(bound=bound, timeout=timeout),
            max_turn_timeout=0.2,
            permission_timeout=0,
        )
        started = time.monotonic()
        with watch:
            deadline = time.monotonic() + 3.0
            while not fired and time.monotonic() < deadline:
                time.sleep(0.01)
        elapsed = time.monotonic() - started
        assert fired["bound"] == lane_containment.BOUND_MAX_TURN
        assert 0.2 <= elapsed < 3.0
        assert watch.fired == lane_containment.BOUND_MAX_TURN

    def test_permission_expiry_fires_within_its_own_bound_not_the_stall_bound(self):
        """DEMONSTRABLY NOT AT THE NO-PROGRESS BOUND, which is the distinction A10 requires.

        The stall bound is set 20x longer here, so a kill inside the short permission window proves it
        was THAT bound and not the coarse one.
        """

        stall_timeout = 4.0
        permission_timeout = 0.2
        assert permission_timeout * 20 <= stall_timeout

        fired: dict[str, object] = {}
        watch = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: fired.update(bound=bound, timeout=timeout),
            max_turn_timeout=0,
            permission_timeout=permission_timeout,
        )
        with watch:
            watch.note_permission_request()
            started = time.monotonic()
            deadline = started + 3.0
            while not fired and time.monotonic() < deadline:
                time.sleep(0.01)
        elapsed = time.monotonic() - started
        assert fired["bound"] == lane_containment.BOUND_PERMISSION
        assert (
            elapsed < stall_timeout
        ), "the kill must be attributable to the permission bound, not the no-progress bound"

    def test_the_nested_child_session_shape_is_bounded_too(self):
        """A10 names the nested child-session request explicitly: it is the shape the deadlock took.

        The bound is armed from an OBSERVED request regardless of which session it came from, so a
        nested ask is bounded identically. Asserted by arming from a nested-shaped event.
        """

        nested = json.dumps(
            {
                "type": "permission.updated",
                "properties": {
                    "sessionID": "ses_child",
                    "parentID": "ses_parent",
                    "permission": {"type": "external_directory"},
                },
            }
        )
        assert json.loads(nested)["properties"]["parentID"]

        fired: dict[str, object] = {}
        watch = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: fired.update(bound=bound, timeout=timeout),
            max_turn_timeout=0,
            permission_timeout=0.15,
        )
        with watch:
            # However the caller learns of it (parent or nested session), arming is one call.
            watch.note_permission_request()
            deadline = time.monotonic() + 3.0
            while not fired and time.monotonic() < deadline:
                time.sleep(0.01)
        assert fired["bound"] == lane_containment.BOUND_PERMISSION

    def test_progress_disarms_the_permission_bound_but_never_the_max_turn_bound(self):
        """THE RESET SEMANTICS ARE THE DESIGN: one is resettable and one is not."""

        fired: dict[str, object] = {}
        watch = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: fired.update(bound=bound, timeout=timeout),
            max_turn_timeout=0,
            permission_timeout=0.3,
        )
        with watch:
            watch.note_permission_request()
            time.sleep(0.1)
            watch.note_progress()
            time.sleep(0.5)
        assert (
            not fired
        ), "observed progress must disarm the (resettable) permission bound"

        # The max-turn bound, by contrast, is reset by NOTHING.
        fired.clear()
        watch2 = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: fired.update(bound=bound, timeout=timeout),
            max_turn_timeout=0.3,
            permission_timeout=0,
        )
        with watch2:
            deadline = time.monotonic() + 3.0
            while not fired and time.monotonic() < deadline:
                watch2.note_progress()
                time.sleep(0.01)
        assert fired["bound"] == lane_containment.BOUND_MAX_TURN, (
            "MAX_TURN_TIMEOUT must not be resettable; that is its whole reason for existing "
            "beside the no-progress bound"
        )

    def test_a_dead_child_is_not_reaped_again(self):
        """The watch must return when the child is already gone, or it would reap a corpse."""

        fired: list[str] = []
        watch = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: fired.append(bound),
            is_alive=lambda: False,
            max_turn_timeout=0.05,
            permission_timeout=0,
        )
        with watch:
            time.sleep(0.3)
        assert not fired

    def test_the_record_is_written_before_the_reap(self, tmp_path):
        """ORDER IS LOAD-BEARING: reaping unblocks the read loop, so a later record could race it.

        Without this order a post-mortem sees a terminated child with NO reason attached, which is
        exactly the "cannot say which timer killed it" outcome R4.4d exists to prevent.
        """

        order: list[str] = []
        item: dict[str, object] = {"id6": "lhmrhx"}

        class _Report:
            all_satisfied = True

        def _reap(process, run_dir=None):
            order.append("reap")
            return _Report()

        expire = lane_containment.bound_expiry_reaper(
            _FakeProcess(), tmp_path, item, reap=_reap
        )
        expire(lane_containment.BOUND_MAX_TURN, 14100.0)

        assert order == ["reap"]
        # The record exists and predates the reap in the same call.
        assert item["turn_bound_expiry"]["bound"] == lane_containment.BOUND_MAX_TURN
        events = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
        assert "turn-bound-expired" in events
        assert lane_containment.BOUND_MAX_TURN in events

    def test_a_recording_failure_does_not_stop_the_reap(self, tmp_path):
        """Bookkeeping must never prevent the child being reaped."""

        reaped: list[str] = []

        class _Report:
            all_satisfied = True

        # An unwritable run dir makes the event append fail.
        expire = lane_containment.bound_expiry_reaper(
            _FakeProcess(),
            tmp_path / "does" / "not" / "exist" / "\0bad",
            {"id6": "x"},
            reap=lambda process, run_dir=None: (reaped.append("r"), _Report())[1],
        )
        expire(lane_containment.BOUND_PERMISSION, 30.0)
        assert reaped == ["r"]

    def test_the_default_reaper_is_the_one_shared_clean_shutdown(self):
        """Spec `c4gd2h` R5: the reap goes through the ONE shared routine, never a bare kill.

        Asserted over the AST rather than the source text, because the docstring legitimately NAMES
        the primitives it is forbidden to call ("NOT a bare kill, NOT a local `terminate_process`"),
        and a text check would be satisfied - or in this case falsely tripped - by that prose. This is
        the same reason spec A10 requires a structural check rather than a grep.
        """

        tree = ast.parse(
            inspect.getsource(lane_containment.bound_expiry_reaper).lstrip()
        )
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        for forbidden in (
            "kill",
            "killpg",
            "terminate",
            "terminate_process",
            "send_signal",
        ):
            assert (
                forbidden not in called
            ), f"the expiry path calls {forbidden} directly"

        # The default reaper resolves to the shared routine.
        default = (
            inspect.signature(lane_containment.bound_expiry_reaper)
            .parameters["reap"]
            .default
        )
        assert (
            default is None
        ), "the shared routine is the default, resolved inside the body"
        assert "runner_shutdown.clean_shutdown" in inspect.getsource(
            lane_containment.bound_expiry_reaper
        )


# ---- A10 (structural): no second reaper was introduced ---------------------------------------------


def test_no_second_reaper_exists_anywhere_in_the_package():
    """Checked with the AST over the WHOLE package, NOT a text grep.

    A grep is satisfied by the checking code itself (this very file contains the symbols), which is
    why the requirement specifies a structural check.

    WHAT THE RULE ACTUALLY IS, stated precisely because a sloppier version of this test produced four
    false positives on first run and had to be narrowed against the real code. A "reaper" is code that
    SIGNALS A PROCESS TO DIE. It is NOT:

      * `os.kill(pid, 0)`, which sends NO signal and is a LIVENESS PROBE. Three shipped call sites use
        it that way (`ipd_lifecycle`, `layout_migration`, `worktree_lease`) and flagging them would be
        wrong.
      * `process.kill()` on a child whose OWN stream failed to open before the run began
        (`agy_run.py`), which is pre-existing spawn-failure cleanup, not turn termination.

    So the assertion targets the thing spec `c4gd2h` R5 is about: the code THIS plan added must route
    termination through `runner_shutdown`, and no new signalling call site may appear in the modules
    this plan touched.
    """

    package = Path(inspect.getfile(lane_containment)).parent
    scoped = ("lane_containment.py", "oc_runipd.py", "agy_runipd.py")
    offenders: list[str] = []

    for name in scoped:
        path = package / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            # A SIGNALLING call: `os.kill`/`os.killpg` with a real signal, or `<x>.kill()`/
            # `<x>.terminate()` / `<x>.send_signal()` on a process object.
            if func.attr in {"kill", "killpg", "terminate", "send_signal"}:
                base = func.value
                base_name = base.id if isinstance(base, ast.Name) else None
                if base_name == "os":
                    # `os.kill(pid, 0)` is a liveness probe, not a kill.
                    args = node.args
                    is_probe = (
                        len(args) >= 2
                        and isinstance(args[1], ast.Constant)
                        and args[1].value == 0
                    )
                    if not is_probe:
                        offenders.append(f"{name}:{node.lineno} os.{func.attr}")
                elif base_name in {"process", "proc", "child"}:
                    offenders.append(f"{name}:{node.lineno} {base_name}.{func.attr}")

    assert not offenders, (
        "a second reaper was introduced in this plan's modules; spec `c4gd2h` R5 forbids one, and "
        "termination must route through `runner_shutdown`: " + "; ".join(offenders)
    )

    # And POSITIVELY: the one reap this plan added really does resolve to the shared routine.
    # Checked as a REFERENCE rather than a call, because it is bound to a name and invoked through it,
    # which is what makes the test-only injection seam possible.
    reaper_src = inspect.getsource(lane_containment.bound_expiry_reaper)
    refs = [
        node
        for node in ast.walk(ast.parse(reaper_src.lstrip()))
        if isinstance(node, ast.Attribute)
        and node.attr == "clean_shutdown"
        and isinstance(node.value, ast.Name)
        and node.value.id == "runner_shutdown"
    ]
    assert refs, "the bound expiry must reap through `runner_shutdown.clean_shutdown`"
    # And the DEFAULT really is that object, not merely mentioned in a comment.
    from agent_workflows import runner_shutdown as _rs

    assert _rs.clean_shutdown is runner_shutdown.clean_shutdown


def test_the_bound_watch_is_defined_exactly_once_in_the_package():
    """One definition, in the DECLARED shared home (spec R2.6/A5c), established structurally."""

    package = Path(inspect.getfile(lane_containment)).parent
    homes: list[str] = []
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "TurnBoundWatch":
                homes.append(path.name)
    assert homes == ["lane_containment.py"], homes


# ---- R4.5 / A11: the in-lane lifecycle refusal, with its honest limit -------------------------------


class TestExecutionRoleSelector:
    """A11/R4.5: an in-lane driver-owned lifecycle verb REFUSES and performs NO state transition.

    HONEST LIMIT, which spec Goal 5 requires be stated rather than closed: this is an environment
    SELECTOR, not a hardened boundary. A same-user worker with shell access can unset it. It stops an
    agent that is FOLLOWING the contract, which was the measured failure, not a determined one.
    """

    def test_an_in_lane_lifecycle_verb_refuses_and_transitions_nothing(self, tmp_path):
        """The refusal AND the ABSENCE of the transition, because a refusal that still mutated would
        satisfy a message-only assertion."""

        repo = tmp_path / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        plan = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260905-t-01-tttttt-p.ipd.md"
        )
        plan.write_text(
            "# IPD: t\n\n- Status: approved\n- Id: tttttt\n- Set: t\n- Order: 1\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-qm",
                "init",
            ],
            cwd=repo,
            check=True,
        )

        env = oc_runipd.pinned_child_env()
        env["AW_EXECUTION_ROLE"] = "worker"
        before = plan.read_text(encoding="utf-8")
        proc = subprocess.run(
            oc_runipd.pinned_module_argv(
                [
                    "ipd",
                    "begin",
                    "tttttt",
                    "--dir",
                    str(repo),
                    "--actor",
                    "test-worker",
                ]
            ),
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0
        assert "AW-LIFECYCLE-ROLE-001" in (proc.stdout + proc.stderr)
        # NO STATE TRANSITION: the plan is untouched and no receipt was written.
        assert plan.read_text(encoding="utf-8") == before
        assert plan.exists(), "the plan must not have moved"
        receipts = (
            list((repo / ".aw" / "state").rglob("*begin*"))
            if (repo / ".aw" / "state").exists()
            else []
        )
        assert not receipts, f"a receipt was written despite the refusal: {receipts}"

    def test_the_drivers_own_invocation_still_succeeds(self):
        """The refusal must be keyed on the SELECTOR, not on being in a worktree at all."""

        from agent_workflows import ipd_lifecycle

        assert ipd_lifecycle.worker_role_active({"AW_EXECUTION_ROLE": "worker"}) is True
        assert ipd_lifecycle.worker_role_active({}) is False
        assert ipd_lifecycle.worker_role_active({"AW_EXECUTION_ROLE": ""}) is False

    @DRIVERS
    def test_the_honest_limit_is_stated_in_the_code(self, driver):
        """OVERSTATING A GUARANTEE IS THE FAILURE (spec Goal 5), so the limit must be written down.

        DELIBERATELY KEPT AS A TEXT ASSERTION, because the deliverable IS the sentence. Goal 5's
        requirement is that the code not overstate what the selector achieves, and the only way to
        satisfy that is prose a reader encounters beside the mechanism. There is no behavior to drive:
        the LIMIT is precisely that the mechanism can be bypassed, and a test that bypassed it would
        assert the weakness rather than the honesty about it.

        Both drivers must state it, but they may state it differently and that is CORRECT rather than
        a drift: the oc twin carries the full note and the agy twin cites it, which is the shipped
        convention for a rule whose rationale lives in one place. What is asserted is the PROPERTY
        (each driver's code says this is a selector and not a boundary), not identical wording.

        THE LIMIT IS ALSO SHOWN TO BE REAL, which is what stops this being prose asserting prose: the
        selector is UNSET below and the same verb then succeeds, so the documented bypass is
        demonstrated rather than merely claimed. The refusal half is driven by
        `test_an_in_lane_lifecycle_verb_refuses_and_transitions_nothing` above.
        """

        src = Path(inspect.getfile(driver)).read_text(encoding="utf-8").lower()
        assert "honest limit" in src
        assert (
            "not a hardened boundary" in src
            or "environment selector, not a hardened" in src
        )
        # And the shared home carries the full statement, including WHY it is bypassable.
        shared = Path(inspect.getfile(lane_containment)).read_text(encoding="utf-8")
        assert "HONEST LIMIT" in shared
        assert "not a boundary" in shared

        # THE DOCUMENTED LIMIT IS REAL: the predicate keys on the selector ALONE, so unsetting it
        # restores authority. That is the bypass the prose admits to, asserted rather than asserted-in-
        # prose, and it is why "selector" is the honest word and "boundary" would not be.
        from agent_workflows import ipd_lifecycle

        marked = {"PATH": "/usr/bin", ipd_lifecycle.EXECUTION_ROLE_ENV: "worker"}
        assert ipd_lifecycle.worker_role_active(marked) is True
        bypassed = {
            k: v for k, v in marked.items() if k != ipd_lifecycle.EXECUTION_ROLE_ENV
        }
        assert ipd_lifecycle.worker_role_active(bypassed) is False


class TestTheAgentIsToldNotToOutliveItsOwnCommands:
    """A turn's child processes die with the turn, so the agent must be told to WAIT for them.

    WHY THIS IS A TURN-BOUND CONCERN and lives beside the other R4.4 bounds: the bounds above stop a
    turn that runs too LONG, and this stops the opposite failure, a turn that ends too EARLY while its
    own work is still running. Both are about the turn's lifetime, and neither is enforceable by the
    host.

    MEASURED, run `run-20260918T045802Z-2547360` item `zqs0px` (backlog `q1z9gn`): a turn ended with
    `python3 -m pytest` still running, the host terminated it (`terminating 2 background task(s) on
    exit`), reported `status: SUCCESS` for a turn whose final words were "Waiting for test suite
    baseline run to finish", and the driver recorded `partial` because no outcome file was written.
    That one `partial` then blocked three siblings and took the run to `BLOCKED` with 1 of 5 items
    executed. The turn used 36s of a 600s stall budget and exited 0, so NO bound fired.

    CORRECTED BY `ty7w6o` (2026-09-22), because this docstring previously stated the cause twice and
    both statements are FALSIFIED by the session logs. It said the agent "started `python3 -m pytest`
    as a BACKGROUND task" and that "the agent chose to stop". What the logs show is a plain FOREGROUND
    `run_command {"CommandLine":"python3 -m pytest"}` with no background parameter, which THE HOST
    converted to a background task and then terminated on exit. So the instruction asserted below is
    still worth pinning - it is cheap, correct guidance and a real failure mode in its own right - but
    it CANNOT prevent the measured incident, and a reader must not conclude from a passing test here
    that the incident family is closed. The host-side half is recorded by
    `TestTheHostsOwnTruncationIsRecorded` below.

    WHAT IS ASSERTED is the PROPERTY (both agents are told to run result-bearing commands in the
    foreground and not to end a turn while one is outstanding), not the exact wording, so a later
    rewording that preserves the instruction does not fail this test.
    """

    @DRIVERS
    def test_the_prompt_tells_the_agent_to_run_commands_in_the_foreground(
        self, driver, tmp_path
    ):
        repo = tmp_path
        item = {
            "id6": "abc123",
            "setid": "demo",
            "position": 1,
            "configured_file": "x.ipd.md",
            "attempts": [{"number": 1}],
            "action": "execute",
        }
        state = {"run_id": "run-1", "repo": str(repo), "options": {}}
        plan = repo / "plan.ipd.md"
        plan.write_text("# plan\n", encoding="utf-8")

        prompt = driver.build_prompt(item, state, repo / "rd", plan, False)
        low = prompt.lower()

        # The instruction is present: run it in the foreground, and wait.
        assert "foreground" in low
        # The REASON is present, because an instruction without its reason invites a workaround
        # (the agent that hit this was not being careless, it was managing a long command).
        assert "terminated when it ends" in low or "killed" in low
        # And the specific prohibition, which is the one the measured incident violated.
        assert "never end your turn while waiting" in low

    def test_both_hosts_receive_the_same_instruction(self, tmp_path):
        """It is in the SHARED prompt, so neither host can drift from the other on this."""

        prompts = {}
        for driver in (oc_runipd, agy_runipd):
            repo = tmp_path / driver.__name__
            repo.mkdir()
            plan = repo / "plan.ipd.md"
            plan.write_text("# plan\n", encoding="utf-8")
            prompts[driver.__name__] = driver.build_prompt(
                {
                    "id6": "abc123",
                    "setid": "demo",
                    "position": 1,
                    "configured_file": "x.ipd.md",
                    "attempts": [{"number": 1}],
                    "action": "execute",
                },
                {"run_id": "run-1", "repo": str(repo), "options": {}},
                repo / "rd",
                plan,
                False,
            )

        sentence = "run every command you need the result of in the foreground"
        for name, text in prompts.items():
            assert (
                sentence in text.lower()
            ), f"{name} is missing the foreground instruction"


# ---- `ty7w6o`: the HOST's own truncation admission, recorded instead of accepted ------------------


# THE REAL CAPTURED LINES, byte for byte. A hand-paraphrased fixture would pass while the shipped
# classifier missed the real output, which is the specific way a string-matching guard fails.
#
# WHERE THESE COME FROM, since the obvious source is gone: `.aw/records/runs/` is gitignored and is
# EMPTY in a lane worktree and a fresh clone, so the cited run directories do not exist and cannot be
# re-read. The line forms survive in the tracked plan `ty7w6o` (its Concern, E-01 and V-01), which is
# their provenance record, and they are copied from it here. They contain no machine-identifying data:
# no paths, no usernames, no session ids.
_HOST_TRUNCATING_BOUNDED_WAIT = (
    "root agent idle; waiting up to 5s for 2 background task(s)"
)
_HOST_TRUNCATING_TERMINATE = "terminating 2 background task(s) on exit"
_HOST_WAITING = (
    "root agent idle; waiting for 1 background task(s) (bounded by --print-timeout)"
)


class TestTheHostsOwnTruncationIsClassified:
    """E-01/V-01: the classifier separates the host CUTTING the work from the host WAITING for it.

    MEASURED, twice on 2026-09-18: the agent issued a plain FOREGROUND `run_command
    {"CommandLine":"python3 -m pytest"}`, the HOST converted it to a background task, said `waiting up
    to 5s`, then `terminating 2 background task(s) on exit`, and closed the turn
    `{"status":"SUCCESS","duration_seconds":47.46}` with exit 0. No driver bound fired and none could
    have (turn 47s against a 600s stall budget and a 14100s driver bound), so the host's own lines are
    the ONLY evidence the turn was cut.

    WHY THE WAITING FORM IS A LOAD-BEARING NEGATIVE CONTROL: the same host emits both, and across the
    captured sessions 3 emitted the waiting form and WAITED (healthy) against 8 that cut. Treating them
    alike would flag healthy turns. That ratio is a recorded historical measurement, not reproducible
    from this tree.
    """

    def test_both_real_truncating_lines_are_truncating(self):
        for line in (_HOST_TRUNCATING_BOUNDED_WAIT, _HOST_TRUNCATING_TERMINATE):
            assert (
                lane_containment.classify_host_turn_line(line)
                == lane_containment.HOST_TURN_TRUNCATING
            ), line

    def test_the_real_waiting_line_is_waiting_and_explicitly_not_truncating(self):
        verdict = lane_containment.classify_host_turn_line(_HOST_WAITING)
        assert verdict == lane_containment.HOST_TURN_WAITING
        assert verdict != lane_containment.HOST_TURN_TRUNCATING

    @pytest.mark.parametrize(
        "line",
        (
            "",
            "   ",
            '{"event":"tool_call","name":"run_command"}',
            '{"type":"assistant","text":"ordinary progress"}',
        ),
    )
    def test_an_ordinary_or_empty_line_is_not_classified(self, line):
        assert lane_containment.classify_host_turn_line(line) is None

    @pytest.mark.parametrize(
        "line",
        (
            '{"event":"assistant","text":"terminating 2 background task(s) on exit"}',
            '{"event":"tool_result","output":"root agent idle; waiting up to 5s for 2 background task(s)"}',
        ),
    )
    def test_an_agent_echoing_the_hosts_words_is_refused(self, line):
        """THE OTHER LOAD-BEARING CONTROL, and the only guard against a false positive.

        The stream carries BOTH file descriptors and BOTH speakers: `popen_kwargs` merges stderr into
        stdout, so the loop sees the host's bare-text diagnostics AND every JSONL envelope, whose
        payloads contain the agent's own assistant text and tool output. Without this control the
        classifier fires on an agent that merely QUOTES the host, which is a LIVE risk in this Set
        because sibling plans reproduce these exact lines in text an executing agent reads.
        """

        assert lane_containment.classify_host_turn_line(line) is None

    def test_the_discriminators_are_not_the_shared_root_agent_idle_prefix(self):
        """`root agent idle` matches BOTH forms, so it cannot discriminate and must not be the trigger."""

        assert "root agent idle" in _HOST_TRUNCATING_BOUNDED_WAIT
        assert "root agent idle" in _HOST_WAITING
        # The bare prefix alone, with neither discriminator, is NOT classified either way.
        assert lane_containment.classify_host_turn_line("root agent idle") is None
        source = inspect.getsource(lane_containment.classify_host_turn_line)
        assert (
            "root agent idle" not in source
        ), "the shared prefix must not be a matching trigger"

    def test_the_task_count_is_read_best_effort_and_never_gates_the_verdict(self):
        assert lane_containment.host_turn_task_count(_HOST_TRUNCATING_TERMINATE) == 2
        assert (
            lane_containment.host_turn_task_count("terminating tasks on exit") is None
        )
        # No count, still truncating: the verdict must not depend on parsing a number.
        assert (
            lane_containment.classify_host_turn_line(
                "terminating some background task(s) on exit"
            )
            == lane_containment.HOST_TURN_TRUNCATING
        )

    def test_the_classifier_is_pure_and_host_neutral(self):
        """Spec `7ckptx` R2.6: the single definition lives in the shared module, not in a driver."""

        assert lane_containment.classify_host_turn_line.__module__.endswith(
            "lane_containment"
        )
        agy_source = inspect.getsource(agy_runipd)
        # The driver may CALL it and NAME it in a comment, but must not carry a second copy of the
        # discriminators.
        assert (
            "bounded by --print-timeout"
            not in agy_source.replace("`--print-timeout`", "")
            or "classify_host_turn_line" in agy_source
        )

    def test_the_fail_silent_property_is_stated_at_the_classifier(self):
        """OQ-01: a silent stop is possible if the host rewords a line, and that must be documented."""

        source = inspect.getsource(lane_containment)
        head = source[: source.index("def classify_host_turn_line")]
        assert "FAIL-SILENT" in head


class TestTheHostsOwnTruncationIsObserved:
    """E-02/V-02: the per-turn observer accumulates the verdict and NEVER costs a turn."""

    def test_it_accumulates_a_truncation_across_a_real_sequence(self):
        observer = lane_containment.HostTruncationObserver()
        for line in (
            '{"type":"assistant","text":"running the suite"}',
            _HOST_TRUNCATING_BOUNDED_WAIT,
            _HOST_TRUNCATING_TERMINATE,
        ):
            observer.note_line(line)
        assert observer.truncated is True
        assert observer.task_count == 2
        record = observer.as_record()
        assert record["verdict"] == lane_containment.HOST_TURN_TRUNCATING
        assert record["background_tasks"] == 2
        assert len(record["truncating_lines"]) == 2

    def test_a_healthy_sequence_reports_no_truncation(self):
        observer = lane_containment.HostTruncationObserver()
        for line in (
            '{"type":"assistant","text":"running the suite"}',
            _HOST_WAITING,
            '{"type":"result","status":"SUCCESS"}',
        ):
            observer.note_line(line)
        assert observer.truncated is False
        assert observer.waiting_lines == [_HOST_WAITING]

    def test_a_later_waiting_line_does_not_clear_an_admitted_truncation(self):
        """The two are not alternatives in one turn: the host may wait for one task and cut another."""

        observer = lane_containment.HostTruncationObserver()
        observer.note_line(_HOST_TRUNCATING_TERMINATE)
        observer.note_line(_HOST_WAITING)
        assert observer.truncated is True

    @pytest.mark.parametrize("line", (None, "", "   ", 42, object()))
    def test_malformed_or_empty_input_neither_raises_nor_reports_truncation(self, line):
        observer = lane_containment.HostTruncationObserver()
        assert observer.note_line(line) is None
        assert observer.truncated is False

    def test_it_is_modeled_on_the_established_observer_and_never_blocks(self):
        source = inspect.getsource(lane_containment.HostTruncationObserver)
        assert "DOES NOT BLOCK" in source.upper()
        # No waiting, no prompting, no terminating: observing is recording.
        tree = ast.parse(inspect.getsource(lane_containment.HostTruncationObserver))
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        } | {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        for forbidden in ("sleep", "wait", "terminate", "kill", "input"):
            assert forbidden not in called


class TestTheHostsOwnTruncationIsRecordedDurably:
    """E-04/V-04: it reaches `state.json` and `events.jsonl`, and it changes NO item's fate.

    THE NEGATIVE PROPERTY IS THE POINT. `ty7w6o` produces the signal; `dy9ymn` decides what to do with
    it. If this plan also moved a disposition the two would fight over one field, so the exit code, the
    computed disposition and `item["status"]` must be IDENTICAL with and without the record.
    """

    @staticmethod
    def _truncated_observer():
        observer = lane_containment.HostTruncationObserver()
        observer.note_line(_HOST_TRUNCATING_BOUNDED_WAIT)
        observer.note_line(_HOST_TRUNCATING_TERMINATE)
        return observer

    def test_a_truncated_turn_is_recorded_on_the_attempt_and_as_an_event(
        self, tmp_path
    ):
        item = {"id6": "ty7w6o", "attempts": [{"number": 1, "exit_code": 0}]}
        record = lane_containment.record_host_truncation(
            tmp_path, item, 1, self._truncated_observer()
        )
        assert record is not None
        attempt = item["attempts"][-1]
        assert attempt["host_truncation"]["verdict"] == (
            lane_containment.HOST_TURN_TRUNCATING
        )
        assert attempt["host_truncation"]["background_tasks"] == 2
        events = [
            json.loads(line)
            for line in (tmp_path / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        truncations = [e for e in events if e["event"] == "host-truncated-turn"]
        assert len(truncations) == 1
        assert truncations[0]["id6"] == "ty7w6o"
        assert truncations[0]["attempt"] == 1
        assert truncations[0]["verdict"] == lane_containment.HOST_TURN_TRUNCATING

    def test_a_healthy_turn_records_neither(self, tmp_path):
        observer = lane_containment.HostTruncationObserver()
        observer.note_line(_HOST_WAITING)
        item = {"id6": "ty7w6o", "attempts": [{"number": 1, "exit_code": 0}]}
        assert (
            lane_containment.record_host_truncation(tmp_path, item, 1, observer) is None
        )
        assert "host_truncation" not in item["attempts"][-1]
        assert not (tmp_path / "events.jsonl").exists()

    def test_it_changes_neither_the_exit_code_nor_the_disposition_nor_the_status(
        self, tmp_path
    ):
        def _item():
            return {
                "id6": "ty7w6o",
                "setid": "reaskscore",
                "position": 2,
                "configured_file": "missing.ipd.md",
                "action": "execute",
                "status": "running",
                "attempts": [{"number": 1, "exit_code": 0}],
            }

        untouched, recorded = _item(), _item()
        lane_containment.record_host_truncation(
            tmp_path, recorded, 1, self._truncated_observer()
        )

        assert (
            recorded["attempts"][-1]["exit_code"]
            == (untouched["attempts"][-1]["exit_code"])
        )
        assert recorded["status"] == untouched["status"]
        assert "disposition" not in recorded["attempts"][-1]

        # And the SCORER returns the same verdict for both, which is the property that matters.
        repo = tmp_path / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        run_dir = tmp_path / "rd"
        (run_dir / "outcomes").mkdir(parents=True)
        for driver in (oc_runipd, agy_runipd):
            before = driver.reconcile_disposition(repo, untouched, run_dir, 0)
            after = driver.reconcile_disposition(repo, recorded, run_dir, 0)
            assert before[0] == after[0], driver.__name__

    def test_the_record_survives_a_failed_event_write(self, tmp_path):
        """The ATTEMPT record is written FIRST, so a logging failure cannot lose the truncation."""

        item = {"id6": "ty7w6o", "attempts": [{"number": 1}]}
        unwritable = tmp_path / "does" / "not" / "exist" / "\0bad"
        record = lane_containment.record_host_truncation(
            unwritable, item, 1, self._truncated_observer()
        )
        assert record is not None
        assert item["attempts"][-1]["host_truncation"]["background_tasks"] == 2


class TestTheHostsOwnTruncationIsWiredAtTheEveryLineSeam:
    """E-03/V-03: fed for EVERY raw line, under EVERY `output_mode`, not from a rendering branch.

    A signal parsed inside a rendering branch is silently INERT under `raw` and `quiet` - a mistake
    this loop already records having made and fixed (`y5od1h` E-06, `foi1b3`).
    """

    @staticmethod
    def _run_a_truncating_turn(tmp_path, output_mode):
        from agent_workflows import runner_shared

        repo = tmp_path / f"repo-{output_mode}"
        repo.mkdir(parents=True)
        run_dir = tmp_path / f"run-{output_mode}"
        (run_dir / "sessions").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        prompt = run_dir / "prompts" / "01-prompt.md"
        prompt.write_text("prompt", encoding="utf-8")
        state = {
            "run_id": "run-1",
            "repo": str(repo),
            "options": {
                "output_mode": output_mode,
                "agy_executable": "agy",
            },
        }
        item = {
            "id6": "ty7w6o",
            "setid": "reaskscore",
            "position": 2,
            "action": "execute",
            "attempts": [{"number": 1}],
        }
        stdout_lines = [
            '{"type":"assistant","text":"running the suite"}\n',
            _HOST_TRUNCATING_BOUNDED_WAIT + "\n",
            _HOST_TRUNCATING_TERMINATE + "\n",
            '{"type":"result","status":"SUCCESS","duration_seconds":47.46}\n',
        ]

        class FakeProc:
            def __init__(self, cmd, *args, **kwargs):
                self.pid = 4242
                self.stdout = iter(stdout_lines)
                self.returncode = 0

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

        with mock.patch("subprocess.Popen", side_effect=FakeProc):
            rc, _sess, _log, _argv = agy_runipd.run_agy_turn(
                state, run_dir, item, prompt, 1, session_id=None, use_continue=False
            )
        assert rc == 0
        assert runner_shared is not None
        return item, run_dir

    @pytest.mark.parametrize("output_mode", ("clean", "raw", "quiet"))
    def test_detection_is_independent_of_output_mode(self, tmp_path, output_mode):
        item, run_dir = self._run_a_truncating_turn(tmp_path, output_mode)
        attempt = item["attempts"][-1]
        assert attempt["host_truncation"]["verdict"] == (
            lane_containment.HOST_TURN_TRUNCATING
        ), f"the signal is inert under output_mode={output_mode}"
        assert attempt["host_truncation"]["background_tasks"] == 2
        events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
        assert "host-truncated-turn" in events

    def test_a_healthy_turn_through_the_same_loop_records_nothing(self, tmp_path):
        repo = tmp_path / "repo-healthy"
        repo.mkdir(parents=True)
        run_dir = tmp_path / "run-healthy"
        (run_dir / "sessions").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        prompt = run_dir / "prompts" / "01-prompt.md"
        prompt.write_text("prompt", encoding="utf-8")
        item = {
            "id6": "ty7w6o",
            "setid": "reaskscore",
            "position": 2,
            "action": "execute",
            "attempts": [{"number": 1}],
        }
        stdout_lines = [
            _HOST_WAITING + "\n",
            '{"type":"result","status":"SUCCESS"}\n',
        ]

        class FakeProc:
            def __init__(self, cmd, *args, **kwargs):
                self.pid = 4243
                self.stdout = iter(stdout_lines)
                self.returncode = 0

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

        with mock.patch("subprocess.Popen", side_effect=FakeProc):
            agy_runipd.run_agy_turn(
                {
                    "run_id": "run-1",
                    "repo": str(repo),
                    "options": {"output_mode": "quiet", "agy_executable": "agy"},
                },
                run_dir,
                item,
                prompt,
                1,
                session_id=None,
                use_continue=False,
            )

        assert "host_truncation" not in item["attempts"][-1]
        events_path = run_dir / "events.jsonl"
        if events_path.exists():
            assert "host-truncated-turn" not in events_path.read_text(encoding="utf-8")

    def test_the_observer_is_fed_outside_every_rendering_branch(self):
        """Asserted structurally: the feed must NOT sit inside an `output_mode` comparison."""

        tree = ast.parse(inspect.getsource(agy_runipd.run_agy_turn).lstrip())
        feeds = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "note_line"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "host_truncation"
        ]
        assert len(feeds) == 1, "exactly one feed, at the every-line seam"
        guarded = {
            id(call)
            for branch in ast.walk(tree)
            if isinstance(branch, ast.If) and "output_mode" in ast.dump(branch.test)
            for call in ast.walk(branch)
            if isinstance(call, ast.Call)
        }
        assert id(feeds[0]) not in guarded

    def test_the_grepped_print_timeout_comment_block_is_intact(self):
        """R4.4d's own check above greps this source for three literals; this edit must not reflow it.

        Collapsed the SAME way that check collapses it, because the phrase wraps across comment lines
        ("EXPECTED\n# TO WIN"), so a literal search on the raw source would fail on intact code.
        """

        collapsed = " ".join(
            inspect.getsource(agy_runipd.run_agy_turn).split()
        ).replace("# ", "")
        for literal in ("print-timeout", "EXPECTED TO WIN", "BACKSTOP"):
            assert literal in collapsed, literal

    def test_the_deliberate_host_asymmetry_is_stated_at_the_write(self):
        """OQ-02/OQ-05: so nobody 'fixes' it by copying the write into the oc launcher."""

        source = inspect.getsource(agy_runipd.run_agy_turn)
        assert "ASYMMETRY" in source.upper()
        assert "oc launcher" in source
        # And the oc twin genuinely does NOT carry the write.
        assert "record_host_truncation" not in inspect.getsource(oc_runipd)

    def test_the_four_tuple_return_shape_is_unchanged(self):
        """Widening it would edit `runner_shared.execute_item_core`, which `ty7w6o` does not declare."""

        import typing

        hints = typing.get_type_hints(agy_runipd.run_agy_turn)
        assert hints["return"] == tuple[int, str | None, Path, list[str]]
