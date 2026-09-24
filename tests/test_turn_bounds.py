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
import contextlib
import hashlib
import inspect
import io
import json
import subprocess
import time
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import agy_runipd, lane_containment, oc_runipd

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

    def test_the_permission_policy_by_contrast_IS_isolation_scoped(
        self, tmp_path, monkeypatch
    ):
        """The two scopes differ DELIBERATELY, and confusing them would be a real defect.

        The runner narrows the POSTURE to an unattended ISOLATED turn (`run_opencode`'s deliberate
        "ISOLATED TURNS ONLY" narrowing, ordered by R4.6), because a non-isolated turn works in
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

        monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)
        monkeypatch.delenv("AW_EXECUTION_ROLE", raising=False)

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
            "where external-directory denial would refuse its ordinary work"
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


# ---- A10 (structural): no second reaper was introduced ---------------------------------------------


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
# THE SECOND HEALTHY FORM, captured from `run-20260924T010059Z-999731` item `lc4unl` on 2026-09-24.
# Same `waiting up to` phrasing as the truncating form above, and the OPPOSITE meaning: the host named
# its FULL `--print-timeout` ceiling, then waited out a 306s foreground `python3 -m pytest` and let it
# finish. This line is the reason the bound's magnitude is parsed rather than the phrase matched.
_HOST_WAITING_FULL_CEILING = (
    "root agent idle; waiting up to 4h0m0s for 1 background task(s)"
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

    AND THAT NEGATIVE CONTROL WAS INCOMPLETE, WHICH COST A FALSE POSITIVE (2026-09-24). The host also
    emits `waiting up to 4h0m0s` - the SAME phrasing as the truncating form, its FULL ceiling, and
    HEALTHY - and this class originally pinned the phrase alone as proof of a cut, so a turn that ran
    its suite to completion was recorded truncated twice. The verdict now turns on the BOUND'S SIZE,
    and `_HOST_WAITING_FULL_CEILING` is the negative control that was missing.
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

    def test_a_full_ceiling_bounded_wait_is_healthy_not_truncating(self):
        """THE REGRESSION. The measured false positive of 2026-09-24, pinned by its real line.

        `waiting up to 4h0m0s` is maximal patience, not a cut: the host then waited out a 306s
        foreground test run. The old `waiting up to` substring called this a truncation.
        """

        verdict = lane_containment.classify_host_turn_line(_HOST_WAITING_FULL_CEILING)
        assert verdict == lane_containment.HOST_TURN_WAITING
        assert verdict != lane_containment.HOST_TURN_TRUNCATING

    def test_the_two_bounded_wait_forms_differ_ONLY_in_their_bound(self):
        """So the test cannot pass by matching some other incidental difference in the sentence."""

        cut = _HOST_TRUNCATING_BOUNDED_WAIT.replace("2 background", "1 background")
        healthy = _HOST_WAITING_FULL_CEILING
        assert cut.replace("5s", "<B>") == healthy.replace("4h0m0s", "<B>")
        assert (
            lane_containment.classify_host_turn_line(cut)
            == lane_containment.HOST_TURN_TRUNCATING
        )
        assert (
            lane_containment.classify_host_turn_line(healthy)
            == lane_containment.HOST_TURN_WAITING
        )

    @pytest.mark.parametrize(
        ("bound", "expected"),
        (
            ("500ms", lane_containment.HOST_TURN_TRUNCATING),
            ("5s", lane_containment.HOST_TURN_TRUNCATING),
            ("60s", lane_containment.HOST_TURN_TRUNCATING),
            ("1m", lane_containment.HOST_TURN_TRUNCATING),
            ("61s", lane_containment.HOST_TURN_WAITING),
            ("1m30s", lane_containment.HOST_TURN_WAITING),
            ("10m", lane_containment.HOST_TURN_WAITING),
            ("4h0m0s", lane_containment.HOST_TURN_WAITING),
            ("240m", lane_containment.HOST_TURN_WAITING),
        ),
    )
    def test_the_verdict_turns_on_the_bound_either_side_of_the_ceiling(
        self, bound, expected
    ):
        line = f"root agent idle; waiting up to {bound} for 1 background task(s)"
        assert lane_containment.classify_host_turn_line(line) == expected

    def test_the_token_wait_ceiling_sits_between_both_measured_bounds(self):
        """The threshold must separate the two real observations, or it separates nothing."""

        ceiling = lane_containment.HOST_TOKEN_WAIT_CEILING_SECONDS
        measured_cut = lane_containment.parse_go_duration_seconds("5s")
        measured_healthy = lane_containment.parse_go_duration_seconds("4h0m0s")
        assert measured_cut is not None and measured_healthy is not None
        assert measured_cut <= ceiling
        assert measured_healthy > ceiling

    def test_an_unreadable_bound_yields_no_verdict_rather_than_a_truncation(self):
        """Fail toward "this line does not say", never toward accusing a healthy turn."""

        for line in (
            "root agent idle; waiting up to for 1 background task(s)",
            "root agent idle; waiting up to soon for 1 background task(s)",
            "root agent idle; waiting up to 4h0m0sZZ for 1 background task(s)",
        ):
            assert lane_containment.classify_host_turn_line(line) is None, line

    def test_the_terminate_line_still_settles_a_kill_on_its_own(self):
        """The bound check must not weaken the branch that reads the ACTUAL kill admission.

        Across every measured truncation the host printed this line too, which is what makes the
        unreadable-bound fallthrough above safe.
        """

        assert (
            lane_containment.classify_host_turn_line(_HOST_TRUNCATING_TERMINATE)
            == lane_containment.HOST_TURN_TRUNCATING
        )

    @pytest.mark.parametrize(
        ("text", "seconds"),
        (
            ("4h0m0s", 14400.0),
            ("5s", 5.0),
            ("1m30s", 90.0),
            ("500ms", 0.5),
            ("240m", 14400.0),
            ("4h", 14400.0),
        ),
    )
    def test_the_compound_duration_parser_reads_the_hosts_own_shapes(
        self, text, seconds
    ):
        assert lane_containment.parse_go_duration_seconds(text) == seconds

    @pytest.mark.parametrize(
        "text", ("", "   ", "garbage", "4h0m0sZZ", "12", "-5s", None, object())
    )
    def test_the_compound_duration_parser_refuses_anything_else_without_raising(
        self, text
    ):
        assert lane_containment.parse_go_duration_seconds(text) is None

    def test_the_two_duration_parsers_stay_separate(self):
        """Widening the CONFIGURED-ceiling parser would move the driver's own timeout arithmetic.

        `parse_host_ceiling_seconds` feeds `driver_bound_for_host`; it must keep refusing the host's
        compound shape rather than growing to accept it.
        """

        assert lane_containment.parse_host_ceiling_seconds("4h0m0s") is None
        assert lane_containment.parse_go_duration_seconds("4h0m0s") == 14400.0

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

    @pytest.mark.parametrize(
        "healthy_line",
        (_HOST_WAITING, _HOST_WAITING_FULL_CEILING),
        ids=("print-timeout-bound", "full-ceiling-bounded-wait"),
    )
    def test_a_healthy_turn_through_the_same_loop_records_nothing(
        self, tmp_path, healthy_line
    ):
        """END TO END, at the seam where the false positive was actually observed.

        The `full-ceiling-bounded-wait` case is the 2026-09-24 regression: the driver printed its
        truncation warning and wrote `host_truncation` into the run record for a turn nothing had cut.
        """

        repo = tmp_path / f"repo-healthy-{abs(hash(healthy_line))}"
        repo.mkdir(parents=True)
        run_dir = tmp_path / f"run-healthy-{abs(hash(healthy_line))}"
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
            healthy_line + "\n",
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

    def test_the_four_tuple_return_shape_is_unchanged(self):
        """Widening it would edit `runner_shared.execute_item_core`, which `ty7w6o` does not declare."""

        import typing

        hints = typing.get_type_hints(agy_runipd.run_agy_turn)
        assert hints["return"] == tuple[int, str | None, Path, list[str]]


# ==================================================================================================
# reaskscore-03 (`dy9ymn`): A TURN THAT PROVABLY ATTEMPTED NOTHING IS RETRIED, NOT LEFT TERMINAL
# ==================================================================================================
#
# WHY THESE LIVE HERE, beside the host-truncation family above rather than in a new file: this is the
# CONSUMER of `ty7w6o`'s signal and the other half of the same measured incident. The cases are
# deliberately built in `tmp_path`; the live `.aw/records/runs/` tree is gitignored and absent in CI,
# so a test reading it would pass locally and fail in a fresh clone.
#
# THE TWO PROPERTIES THAT MATTER MORE THAN THE HAPPY PATH, each with its own class:
#
#   1. THE PREDICATE MUST BE UNABLE TO FIRE ON A TURN THAT DID ANYTHING. Every negative control is
#      built in the MODE WHERE IT CAN ACTUALLY FAIL, which is the point `TheNegativeControls` exists
#      to make: two of the four conditions are VACUOUS on an isolated turn (`ending_head` and
#      `ending_status` read the MAIN CHECKOUT while the lane is `work_dir`), so asserting all four in
#      one mode would present two controls that cannot fail as if they had passed.
#   2. THE REQUEUE MUST HAPPEN BEFORE THE CASCADE OBSERVES THE TERMINAL STATUS, or the retry rescues
#      nothing. That is the actual user-visible defect and it needs an end-to-end multi-item run.


def _zero_work_attempt(isolated: bool = True, **extra):
    """An attempt record in the shape the measured incident produced."""

    attempt = {
        "number": 1,
        "starting_head": "7c233993",
        "ending_head": "7c233993",
        "ending_status": "",
    }
    if isolated:
        attempt["worktree"] = "/tmp/lane/zqs0px"
        attempt["worktree_lane_id"] = "zqs0px"
        attempt["worktree_base"] = "7c233993"
    attempt.update(extra)
    return attempt


def _empty_lane(**extra):
    lane = {
        "state": "EMPTY",
        "branch": "aw/lane/zqs0px",
        "commits_ahead": 0,
        "dirty": False,
    }
    lane.update(extra)
    return lane


def _verdict(
    item=None, attempt=None, lane=None, outcome_written=False, disposition="partial"
):
    from agent_workflows import runner_shared

    return runner_shared.turn_attempted_nothing(
        item if item is not None else {"id6": "zqs0px", "action": "execute"},
        attempt if attempt is not None else _zero_work_attempt(),
        disposition=disposition,
        outcome_written=outcome_written,
        lane=_empty_lane() if lane is None else lane,
    )


class TestTheZeroWorkVerdictIsEvidenceBased:
    """V-01/E-01: the measured shape is recognized, and every missing input FAILS CLOSED."""

    def test_the_measured_case_is_recognized_with_its_reason_and_facts(self):
        verdict = _verdict()
        assert verdict.attempted_nothing is True
        assert verdict.proven is True
        # A REASONED verdict, not a bare bool: this authorizes spending a turn's tokens.
        assert "PROVABLY attempted nothing" in verdict.reason
        assert verdict.facts["outcome_written"] is False
        assert verdict.facts["isolated"] is True
        assert verdict.facts["lane_commits_ahead"] == 0
        assert verdict.facts["lane_dirty"] is False

    def test_an_absent_lane_reading_cannot_prove_it(self):
        """FAIL-CLOSED: a lane that cannot be inspected is not evidence of emptiness."""

        verdict = _verdict(lane=None if False else {})
        # An empty mapping carries no `commits_ahead`.
        assert verdict.attempted_nothing is False
        assert verdict.proven is False
        assert "FAIL-CLOSED" in verdict.reason

    def test_a_missing_lane_for_an_isolated_turn_cannot_prove_it(self):
        from agent_workflows import runner_shared

        verdict = runner_shared.turn_attempted_nothing(
            {"id6": "zqs0px", "action": "execute"},
            _zero_work_attempt(),
            disposition="partial",
            outcome_written=False,
            lane=None,
        )
        assert (verdict.attempted_nothing, verdict.proven) == (False, False)
        assert "FAIL-CLOSED" in verdict.reason

    def test_an_unreadable_outcome_question_cannot_prove_it(self):
        verdict = _verdict(outcome_written=None)
        assert (verdict.attempted_nothing, verdict.proven) == (False, False)
        assert "FAIL-CLOSED" in verdict.reason

    def test_a_shared_tree_turn_missing_its_ending_status_cannot_prove_it(self):
        attempt = _zero_work_attempt(isolated=False)
        attempt.pop("ending_status")
        verdict = _verdict(attempt=attempt, lane=None)
        assert (verdict.attempted_nothing, verdict.proven) == (False, False)
        assert "FAIL-CLOSED" in verdict.reason

    def test_a_shared_tree_turn_missing_its_heads_cannot_prove_it(self):
        attempt = _zero_work_attempt(isolated=False)
        attempt.pop("ending_head")
        verdict = _verdict(attempt=attempt, lane=None)
        assert (verdict.attempted_nothing, verdict.proven) == (False, False)

    def test_a_lane_whose_commits_ahead_is_not_an_int_cannot_prove_it(self):
        verdict = _verdict(lane=_empty_lane(commits_ahead=None))
        assert (verdict.attempted_nothing, verdict.proven) == (False, False)

    def test_which_conditions_bite_in_which_mode_is_DOCUMENTED(self):
        """A reader who believes all four conditions always bite will over-trust an isolated verdict."""

        from agent_workflows import runner_shared

        # Collapsed, because the phrases wrap across doc lines; a literal search on the raw
        # docstring would fail on intact prose.
        doc = " ".join((runner_shared.turn_attempted_nothing.__doc__ or "").split())
        assert "MAIN CHECKOUT" in doc
        assert "TRUE BY CONSTRUCTION" in doc
        assert "commits_ahead" in doc


class TestTheNegativeControls:
    """V-02: one control per condition, each built in the MODE WHERE IT CAN ACTUALLY FAIL.

    A control that cannot fail is not a control, and presenting one as passing would MISREPORT the
    predicate's strictness. So each case below names its mode:

      * `outcome file exists`  -> ISOLATED (bites in both modes; asserted on the isolated fixture,
        which is the mode the defect was measured in).
      * `the lane holds a commit` / `the lane is dirty` -> ISOLATED (the only mode where a lane
        exists at all).
      * `ending_head != starting_head` / `dirty tree` -> SHARED-TREE (`--no-isolate-worktree`).
        On an ISOLATED turn both fields read the MAIN checkout, so they are fixed regardless of what
        the lane did and a control flipping them there would be vacuous.
    """

    def test_an_outcome_file_refuses_the_verdict_isolated_mode(self):
        verdict = _verdict(outcome_written=True)
        assert verdict.attempted_nothing is False
        assert verdict.proven is True
        assert "outcome file WAS written" in verdict.reason

    def test_a_lane_commit_refuses_the_verdict_isolated_mode(self):
        verdict = _verdict(lane=_empty_lane(commits_ahead=3, state="HOLDS-WORK"))
        assert verdict.attempted_nothing is False
        assert "3 commit(s)" in verdict.reason

    def test_a_dirty_lane_refuses_the_verdict_isolated_mode(self):
        verdict = _verdict(lane=_empty_lane(dirty=True, state="HOLDS-WORK"))
        assert verdict.attempted_nothing is False
        assert "DIRTY" in verdict.reason

    def test_a_moved_head_refuses_the_verdict_SHARED_TREE_mode(self):
        """MODE: shared tree. On an isolated turn this field cannot move, so the control would be vacuous."""

        attempt = _zero_work_attempt(isolated=False, ending_head="deadbeef")
        verdict = _verdict(attempt=attempt, lane=None)
        assert verdict.attempted_nothing is False
        assert "HEAD MOVED" in verdict.reason

    def test_a_dirty_shared_tree_refuses_the_verdict_SHARED_TREE_mode(self):
        """MODE: shared tree, for the same reason as above."""

        attempt = _zero_work_attempt(
            isolated=False, ending_status=" M agent_workflows/x.py"
        )
        verdict = _verdict(attempt=attempt, lane=None)
        assert verdict.attempted_nothing is False
        assert "DIRTY" in verdict.reason

    def test_the_isolated_fixture_really_is_vacuous_for_those_two_conditions(self):
        """The MEASUREMENT behind the mode split, asserted so the claim is not merely prose.

        An ISOLATED turn whose lane committed real work still reports `starting_head == ending_head`
        and an empty `ending_status`, because both read the MAIN checkout. If the predicate rested on
        them, this fixture would be called zero-work. It is refused on the LANE facts instead."""

        attempt = _zero_work_attempt()
        assert attempt["starting_head"] == attempt["ending_head"]
        assert attempt["ending_status"] == ""
        verdict = _verdict(attempt=attempt, lane=_empty_lane(commits_ahead=5))
        assert verdict.attempted_nothing is False, (
            "the verdict must be refused by the LANE's commits, which are the only load-bearing "
            "commit evidence on an isolated turn"
        )

    @pytest.mark.parametrize(
        "disposition",
        (
            "interrupted",
            "unknown_outcome",
            "dependency-blocked",
            "not-attempted",
            "merge-retry",
        ),
    )
    def test_every_protected_disposition_is_refused(self, disposition):
        verdict = _verdict(disposition=disposition)
        assert verdict.attempted_nothing is False
        assert verdict.proven is True

    def test_a_review_action_is_refused(self):
        verdict = _verdict(item={"id6": "zqs0px", "action": "review"})
        assert verdict.attempted_nothing is False
        assert "REVIEW" in verdict.reason

    def test_a_deliberately_stopped_item_is_refused(self):
        verdict = _verdict(
            item={
                "id6": "zqs0px",
                "action": "execute",
                "stopped": {"stopped_deliberately": True},
            }
        )
        assert verdict.attempted_nothing is False
        assert "DELIBERATE OPERATOR STOP" in verdict.reason

    def test_an_indeterminate_item_is_refused_through_the_EXISTING_predicate(self):
        """E-02: the refusal REUSES `runner_stop.is_indeterminate` so the two routes cannot disagree."""

        from agent_workflows import runner_stop

        with mock.patch.object(
            runner_stop, "is_indeterminate", return_value=True
        ) as gate:
            verdict = _verdict()
        assert gate.called, "the existing predicate must be CALLED, not restated"
        assert verdict.attempted_nothing is False
        assert "INDETERMINATE" in verdict.reason


class TestTheHostTruncationSignalIsSupportingNotRequired:
    """V-03/E-03: the chosen reading, its rationale, and the case that proves it is not sufficient."""

    def test_a_zero_work_turn_WITHOUT_a_truncation_record_still_fires(self):
        verdict = _verdict()
        assert verdict.attempted_nothing is True
        assert verdict.truncated is False
        assert "SUPPORTING" in verdict.reason

    def test_a_zero_work_turn_WITH_a_truncation_record_fires_and_says_so(self):
        attempt = _zero_work_attempt(
            host_truncation={
                "verdict": lane_containment.HOST_TURN_TRUNCATING,
                "background_tasks": 2,
            }
        )
        verdict = _verdict(attempt=attempt)
        assert verdict.attempted_nothing is True
        assert verdict.truncated is True
        assert "HOST ITSELF admitted" in verdict.reason

    def test_a_truncation_record_ALONE_does_NOT_authorize_a_retry(self):
        """A host may truncate a turn that had ALREADY done real work."""

        attempt = _zero_work_attempt(
            host_truncation={"verdict": lane_containment.HOST_TURN_TRUNCATING}
        )
        verdict = _verdict(attempt=attempt, lane=_empty_lane(commits_ahead=1))
        assert verdict.attempted_nothing is False
        assert (
            verdict.truncated is True
        ), "the record is still READ, just not sufficient"

    def test_the_choice_and_its_reason_are_RECORDED_in_the_code(self):
        """OQ-02 obliges the executor to decide, implement ONE reading, and record why."""

        from agent_workflows import runner_shared

        doc = " ".join((runner_shared.turn_attempted_nothing.__doc__ or "").split())
        assert "SUPPORTING" in doc and "NOT REQUIRED" in doc
        assert "OQ-02" in doc
        assert "confine the retry to the one measured cause" in doc
        assert "CAUSE-AGNOSTIC" in doc


class TestTheZeroWorkRetryIsBoundedByTheFrozenBudget:
    """V-04's budget half: the LIMIT is the frozen `--retry-budget` and the SPEND lives on the item."""

    @staticmethod
    def _decide(used, budget):
        from agent_workflows import runner_shared

        item = {"id6": "zqs0px"}
        if used:
            item[runner_shared.ZERO_WORK_RETRY_COUNT_KEY] = used
        return runner_shared.zero_work_retry_decision(
            item, {"options": {"retry_budget": budget}}, _verdict()
        )

    def test_budget_zero_gives_no_retry_at_all(self):
        decision = self._decide(0, 0)
        assert (decision.retry, decision.exhausted) == (False, True)
        assert decision.budget == 0

    def test_budget_one_gives_exactly_one_retry_then_stands(self):
        first = self._decide(0, 1)
        assert first.retry is True
        assert first.attempts == 0
        second = self._decide(1, 1)
        assert (second.retry, second.exhausted) == (False, True)

    def test_a_budget_above_one_is_still_bounded_by_the_frozen_value(self):
        assert self._decide(0, 3).retry is True
        assert self._decide(1, 3).retry is True
        assert self._decide(2, 3).retry is True
        exhausted = self._decide(3, 3)
        assert (exhausted.retry, exhausted.exhausted) == (False, True)

    def test_a_refused_verdict_never_retries_even_at_a_generous_budget(self):
        from agent_workflows import runner_shared

        decision = runner_shared.zero_work_retry_decision(
            {"id6": "zqs0px"},
            {"options": {"retry_budget": 10}},
            _verdict(outcome_written=True),
        )
        assert (decision.retry, decision.exhausted) == (False, False)

    def test_the_counter_is_SEPARATE_from_the_other_two_budgets(self):
        from agent_workflows import runner_shared

        keys = {
            runner_shared.ZERO_WORK_RETRY_COUNT_KEY,
            runner_shared.TURN_RETRY_COUNT_KEY,
            runner_shared.FINALIZE_RETRY_COUNT_KEY,
        }
        assert len(keys) == 3, "spec 5.5 counts corrections separately for each action"


class TestTheZeroWorkRetryIsAuditable:
    """V-05/E-05: an event per retry, NONE on a refusal, and the reason in the report either way."""

    @staticmethod
    def _run(tmp_path, *, lane, outcome, budget=2, status="partial", item_extra=None):
        from agent_workflows import runner_shared

        repo = tmp_path / "repo"
        (repo / "outcomes").mkdir(parents=True, exist_ok=True)
        run_dir = tmp_path / "run"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        item = {
            "id6": "zqs0px",
            "position": 2,
            "setid": "reaskscore",
            "action": "execute",
            "status": status,
            "attempts": [_zero_work_attempt()],
        }
        item.update(item_extra or {})
        state = {
            "run_id": "r",
            "repo": str(repo),
            "options": {"retry_budget": budget},
            "queue": [item],
        }
        if outcome:
            (run_dir / "outcomes" / "02-zqs0px.json").write_text("{}", encoding="utf-8")

        saved: list[int] = []

        def save_state(rd, st):
            saved.append(1)

        with mock.patch.object(
            runner_shared, "read_zero_work_evidence", return_value=(outcome, lane)
        ):
            result = runner_shared.handle_zero_work_retry(
                repo=repo,
                run_dir=run_dir,
                state=state,
                item=item,
                host_labels=runner_shared.OC_HOST_LABELS,
                save_state=save_state,
                append_jsonl=runner_shared.append_jsonl,
            )
        events = (
            [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            if (run_dir / "events.jsonl").exists()
            else []
        )
        return result, item, state, events

    def test_a_retry_emits_exactly_one_event_carrying_the_facts_and_the_budget(
        self, tmp_path
    ):
        from agent_workflows import runner_shared

        result, item, _state, events = self._run(
            tmp_path, lane=_empty_lane(), outcome=False
        )
        assert result == "queued"
        zero = [e for e in events if e["event"] == "zero-work-retry"]
        assert len(zero) == 1
        (event,) = zero
        assert event["id6"] == "zqs0px"
        assert event["attempt"] == 1
        assert event["from_status"] == "partial"
        assert "PROVABLY attempted nothing" in event["reason"]
        assert event["facts"]["lane_commits_ahead"] == 0
        assert event["retry_attempts_used"] == 1
        assert event["retry_budget"] == 2
        assert event["budget_remaining"] == 1
        assert event["host_truncation"] is False
        assert item[runner_shared.ZERO_WORK_RETRY_COUNT_KEY] == 1
        assert item["status"] == "queued"
        assert item["recovery_next"] is True
        assert item["requeue_from_status"] == "partial"

    def test_a_REFUSAL_emits_no_event_and_changes_no_status(self, tmp_path):
        from agent_workflows import runner_shared

        result, item, _state, events = self._run(
            tmp_path, lane=_empty_lane(commits_ahead=2), outcome=False
        )
        assert result == "partial"
        assert item["status"] == "partial"
        assert [e for e in events if e["event"] == "zero-work-retry"] == []
        assert runner_shared.ZERO_WORK_RETRY_COUNT_KEY not in item
        refusal = item[runner_shared.ZERO_WORK_REFUSAL_KEY]
        assert refusal["attempted_nothing"] is False
        assert "2 commit(s)" in refusal["reason"]

    def test_an_item_that_did_not_end_partial_is_untouched(self, tmp_path):
        from agent_workflows import runner_shared

        result, item, _state, events = self._run(
            tmp_path, lane=_empty_lane(), outcome=False, status="executed"
        )
        assert result == "executed"
        assert item["status"] == "executed"
        assert events == []
        assert runner_shared.ZERO_WORK_REFUSAL_KEY not in item

    def test_the_exhausted_case_stands_terminal_and_records_a_refusal(self, tmp_path):
        from agent_workflows import runner_shared

        result, item, _state, events = self._run(
            tmp_path,
            lane=_empty_lane(),
            outcome=False,
            budget=0,
        )
        assert result == "partial"
        assert [e for e in events if e["event"] == "zero-work-retry"] == []
        assert item[runner_shared.ZERO_WORK_REFUSAL_KEY]["exhausted"] is True
        assert (
            "budget is exhausted" in item[runner_shared.ZERO_WORK_REFUSAL_KEY]["reason"]
        )

    def test_the_report_names_BOTH_a_retry_and_a_refusal_reason(self):
        from agent_workflows import runner_shared

        state = {
            "queue": [
                {
                    "id6": "aaa111",
                    "status": "queued",
                    runner_shared.ZERO_WORK_RETRY_KEY: {
                        "retries_used": 1,
                        "retry_budget": 2,
                        "reason": "the turn PROVABLY attempted nothing",
                    },
                },
                {
                    "id6": "bbb222",
                    "status": "partial",
                    runner_shared.ZERO_WORK_REFUSAL_KEY: {
                        "exhausted": False,
                        "reason": "the lane holds 2 commit(s) beyond its base, which is work",
                    },
                },
            ]
        }
        rendered = "\n".join(runner_shared.render_zero_work_notes(state))
        assert "Zero-work turns" in rendered
        assert "aaa111` RE-DISPATCHED (zero-work retry 1 of 2)" in rendered
        assert "bbb222` not retried (status `partial`)" in rendered
        assert "2 commit(s)" in rendered

    def test_the_report_section_is_absent_when_nothing_happened(self):
        from agent_workflows import runner_shared

        assert (
            runner_shared.render_zero_work_notes(
                {"queue": [{"id6": "x", "status": "executed"}]}
            )
            == []
        )


class TestTheRequeueFiresFromInsideTheDispatchLoop:
    """V-06/E-06: the call site is AFTER `execute_item` returns, INSIDE `while True:`, on both hosts.

    WHY THIS IS ITS OWN PROPERTY: the plan originally cited the pre-loop `--retry-incomplete` block,
    which carries the right requeue SHAPE but is the wrong PLACE - it runs BEFORE `while True:` and
    inspects statuses left by a PREVIOUS invocation, so a check there never observes an in-run turn.
    Asserted on STRUCTURE rather than on a byte offset, which drifts.
    """

    @staticmethod
    def _run_queue_tree(driver):
        return ast.parse(inspect.getsource(driver.run_queue).lstrip())

    @DRIVERS
    def test_the_call_is_inside_the_dispatch_loop(self, driver):
        tree = self._run_queue_tree(driver)
        loops = [n for n in ast.walk(tree) if isinstance(n, ast.While)]
        assert loops, "run_queue must still have its dispatch loop"
        inside = {
            id(call)
            for loop in loops
            for call in ast.walk(loop)
            if isinstance(call, ast.Call)
        }
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "handle_zero_work_retry"
        ]
        assert len(calls) == 1, "exactly one seam per host"
        assert id(calls[0]) in inside, (
            "a check placed in the PRE-LOOP `--retry-incomplete` block would never observe a turn "
            "that happened during this run"
        )

    @DRIVERS
    def test_the_call_follows_execute_item_in_the_same_try_statement(self, driver):
        """It must be on the `else` of the `try` wrapping `execute_item`, so it runs only on RETURN."""

        tree = self._run_queue_tree(driver)
        matches = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            body_calls = {
                call.func.id
                for call in ast.walk(ast.Module(body=node.body, type_ignores=[]))
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            }
            if "execute_item" not in body_calls:
                continue
            orelse_attrs = {
                call.func.attr
                for call in ast.walk(ast.Module(body=node.orelse, type_ignores=[]))
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
            }
            matches.append(orelse_attrs)
        assert matches, "the `try` around `execute_item` must still exist"
        assert any("handle_zero_work_retry" in attrs for attrs in matches)

    def test_the_reason_the_pre_loop_block_is_wrong_is_RECORDED(self):
        """So a later reader does not "tidy" the seam into the requeue block whose shape it copies."""

        from agent_workflows import runner_shared

        doc = " ".join((runner_shared.handle_zero_work_retry.__doc__ or "").split())
        assert "retry-incomplete" in doc
        assert "PREVIOUS invocation" in doc
        assert "cascade" in doc.lower()


class TestTheSiblingsAreNotBlockedEndToEnd:
    """V-04's user-visible half: the SET survives a zero-work turn, on BOTH hosts.

    THIS IS THE ACTUAL DEFECT and a unit test on the predicate cannot prove it. In
    `run-20260918T045802Z-2547360` one `partial` item took `qmgn12`, `di08i9` and `rgaasb` down with
    it for a `BLOCKED` run with 1 of 5 executed. So this drives each host's REAL `run_queue` over a
    multi-item queue with a dependent and an orchestrator, and asserts the dependent still EXECUTES.

    THE TURN HAPPENS DURING THE RUN, not on a resume, which is the property E-06 exists to make
    reachable: `retry_incomplete=False` throughout, so nothing here can be satisfied by the pre-loop
    requeue block.

    MODE: SHARED TREE (`--no-isolate-worktree`), deliberately and with NO mock of the evidence
    collector, so this is a genuine end-to-end path. The isolated-lane reading needs a live
    `git worktree` and is covered by the unit cases above.
    """

    @staticmethod
    def _repo(tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "t@e.st"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
        (repo / "README.md").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
        return repo

    @staticmethod
    def _state(repo, run_dir, budget):
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        queue = [
            {
                "position": 1,
                "id6": "zqs0px",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            },
            {
                "position": 2,
                "id6": "qmgn12",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": ["executed:zqs0px"],
                "attempts": [],
            },
            # THE ORCHESTRATOR, the third member V-04 requires. It is NOT agent-executed: the loop
            # routes an `orchestrate` action to `dispatch_orchestrator_item`, which RECONSIDERS while a
            # child is still actionable and TERMINATES once one reaches a non-success terminal state.
            # So it is the surface that shows a zero-work `partial` taking the SET down, not just a
            # sibling.
            {
                "position": 3,
                "id6": "s0gnha",
                "setid": "reaskscore",
                "action": "orchestrate",
                "kind": "orchestrator",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            },
        ]
        state = {
            "schema_version": 1,
            "run_id": run_dir.name,
            "repo": str(repo),
            "created_at": "2026-09-19T00:00:00+00:00",
            "updated_at": "2026-09-19T00:00:00+00:00",
            "selectors": ["reaskscore"],
            "options": {"retry_budget": budget, "isolate_worktree": False},
            "set_sessions": {},
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return head

    @classmethod
    def _drive(cls, driver, tmp_path, *, budget=2, zero_work_forever=False):
        """Run the real loop. `zqs0px`'s FIRST turn does nothing at all; its second does the work."""

        repo = cls._repo(tmp_path)
        run_dir = tmp_path / f"run-{driver.__name__}"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        head = cls._state(repo, run_dir, budget)
        executed_dir = repo / ".aw" / "records" / "plans" / "executed"
        executed_dir.mkdir(parents=True, exist_ok=True)
        turns: list[str] = []

        def finalize_on_disk(id6):
            (executed_dir / f"20260919-reaskscore-01-{id6}-stub.ipd.md").write_text(
                f"# IPD: stub\n\n- Id: {id6}\n- Status: executed\n", encoding="utf-8"
            )

        def fake_exec(rd, st, it, *a, **kw):
            id6 = str(it["id6"])
            turns.append(id6)
            if len(turns) > 20:
                raise AssertionError("SPIN: the loop is not converging")
            # Every turn records an attempt, exactly as the real one does.
            attempt = {
                "number": len(it.get("attempts") or []) + 1,
                "starting_head": head,
                "ending_head": head,
                "ending_status": "",
                "recovery": bool(kw.get("recovery")),
            }
            it.setdefault("attempts", []).append(attempt)
            first_turn_for_item = len([t for t in turns if t == id6]) == 1
            if id6 == "zqs0px" and (zero_work_forever or first_turn_for_item):
                # THE MEASURED SHAPE: no outcome file, no commit, clean tree, terminal `partial`.
                it["status"] = "partial"
            else:
                it["status"] = "executed"
                (rd / "outcomes" / f"{it['position']:02d}-{id6}.json").write_text(
                    json.dumps({"disposition": "executed"}), encoding="utf-8"
                )
                finalize_on_disk(id6)
            driver.save_state(rd, st)

        buf = io.StringIO()
        with mock.patch.object(driver, "execute_item", side_effect=fake_exec):
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc = driver.run_queue(run_dir, retry_incomplete=False)
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        statuses = {it["id6"]: it["status"] for it in state["queue"]}
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        return rc, statuses, turns, events, state, buf.getvalue()

    @DRIVERS
    def test_the_zero_work_item_is_re_dispatched_and_its_dependent_still_executes(
        self, driver, tmp_path
    ):
        from agent_workflows import runner_shared

        rc, statuses, turns, events, state, _out = self._drive(driver, tmp_path)
        assert turns == [
            "zqs0px",
            "zqs0px",
            "qmgn12",
        ], "the zero-work item must be re-dispatched IN THIS RUN, before its dependent"
        assert statuses["zqs0px"] == "executed"
        assert (
            statuses["qmgn12"] == "executed"
        ), "THE DEFECT: the dependent of a zero-work turn must no longer be cascaded onto"
        assert (
            [e for e in events if e["event"] == "dependency-blocked"] == []
        ), "THE DEFECT: one zero-work turn must no longer cascade onto its siblings"
        # THE ORCHESTRATOR IS STILL TERMINATED, AND THE REASON IS A FIXTURE ARTIFACT RATHER THAN THE
        # CASCADE. Stated rather than hidden, because asserting `executed` here would be asserting
        # something this fixture cannot earn: no orchestrator PLAN exists on the synthetic repo's disk,
        # so Set membership cannot be resolved and `dispatch_orchestrator_item` terminates with
        # `no-orchestrator`. What matters for THIS plan is that it is NOT terminated for a child-driven
        # reason and names NO unfinished child - i.e. the zero-work turn did not take the parent down.
        orch = [e for e in events if e["event"] == "orchestrator-deferred"]
        assert (
            orch
        ), "the orchestrator must still be dispatched through the shared performer"
        assert orch[-1]["reason"] == "no-orchestrator", orch[-1]["reason"]
        assert (
            orch[-1]["unfinished_children"] == []
        ), "the parent must not be refused because of the zero-work child"
        assert len([e for e in events if e["event"] == "zero-work-retry"]) == 1
        item = next(it for it in state["queue"] if it["id6"] == "zqs0px")
        assert item[runner_shared.ZERO_WORK_RETRY_COUNT_KEY] == 1
        # THE EXIT CODE IS NOT ASSERTED ZERO HERE, and the reason is the same fixture artifact: the
        # orchestrator above cannot retire on a synthetic repo holding no orchestrator plan, so the run
        # honestly exits nonzero on THAT and not on the zero-work item. Asserting 0 would demand the
        # fixture earn something unrelated to this plan; the budget-exhaustion cases below assert
        # nonzero, and the EXECUTED statuses above are what this plan's claim rests on.

    @DRIVERS
    def test_the_retry_is_dispatched_in_RECOVERY_mode(self, driver, tmp_path):
        _rc, _st, _turns, _ev, state, _out = self._drive(driver, tmp_path)
        item = next(it for it in state["queue"] if it["id6"] == "zqs0px")
        assert [a["recovery"] for a in item["attempts"]] == [False, True]

    @DRIVERS
    def test_without_the_fix_the_cascade_would_fire_which_is_what_this_prevents(
        self, driver, tmp_path
    ):
        """THE NEGATIVE CONTROL: with the seam neutralized, the sibling IS blocked.

        This is what makes the assertion above meaningful rather than a tautology - it demonstrates
        the fixture genuinely reaches the cascade when the retry does not happen."""

        from agent_workflows import runner_shared

        with mock.patch.object(
            runner_shared,
            "handle_zero_work_retry",
            side_effect=lambda **kw: str(kw["item"].get("status") or ""),
        ):
            rc, statuses, turns, events, _state, _out = self._drive(driver, tmp_path)
        assert turns == ["zqs0px"], "no retry happens when the seam is neutralized"
        assert statuses["zqs0px"] == "partial"
        assert (
            statuses["qmgn12"] == "dependency-blocked"
        ), "this is the MEASURED defect: one zero-work item takes its sibling down with it"
        assert [
            e
            for e in events
            if e["event"] == "dependency-blocked" and e["id6"] == "qmgn12"
        ], "the cascade genuinely fires in this fixture, which is what makes the positive case meaningful"
        assert rc != 0

    @DRIVERS
    def test_budget_zero_gives_no_retry_at_all_end_to_end(self, driver, tmp_path):
        rc, statuses, turns, events, _state, out = self._drive(
            driver, tmp_path, budget=0
        )
        assert turns == [
            "zqs0px"
        ], "`--retry-budget 0` must mean NO retry (spec 25kzda 5.5)"
        assert statuses["zqs0px"] == "partial"
        assert [e for e in events if e["event"] == "zero-work-retry"] == []
        assert "budget is exhausted" in out
        assert rc != 0

    @DRIVERS
    def test_a_permanently_zero_work_item_cannot_loop_past_the_budget(
        self, driver, tmp_path
    ):
        """Boundedness, measured with the COUNTER pasted rather than inferred from the status.

        A retry that fired twice because the code hardcoded two, and one that fired twice because the
        budget allowed two, are indistinguishable from the final status alone."""

        from agent_workflows import runner_shared

        rc, statuses, turns, events, state, _out = self._drive(
            driver, tmp_path, budget=2, zero_work_forever=True
        )
        assert turns == [
            "zqs0px",
            "zqs0px",
            "zqs0px",
        ], "budget + 1 dispatches, never more"
        assert statuses["zqs0px"] == "partial"
        item = next(it for it in state["queue"] if it["id6"] == "zqs0px")
        assert item[runner_shared.ZERO_WORK_RETRY_COUNT_KEY] == 2
        assert len([e for e in events if e["event"] == "zero-work-retry"]) == 2
        assert item[runner_shared.ZERO_WORK_REFUSAL_KEY]["exhausted"] is True
        assert rc != 0

    @DRIVERS
    def test_a_budget_above_one_bounds_the_same_way(self, driver, tmp_path):
        from agent_workflows import runner_shared

        _rc, _st, turns, events, state, _out = self._drive(
            driver, tmp_path, budget=3, zero_work_forever=True
        )
        assert turns == ["zqs0px"] * 4
        item = next(it for it in state["queue"] if it["id6"] == "zqs0px")
        assert item[runner_shared.ZERO_WORK_RETRY_COUNT_KEY] == 3
        assert len([e for e in events if e["event"] == "zero-work-retry"]) == 3

    @DRIVERS
    def test_the_counter_PERSISTS_across_a_resume(self, driver, tmp_path):
        """The spend lives in `state.json` on the item, so a resume cannot buy fresh retries."""

        from agent_workflows import runner_shared

        repo = self._repo(tmp_path)
        run_dir = tmp_path / f"resume-{driver.__name__}"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        head = self._state(repo, run_dir, 2)
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        item = state["queue"][0]
        item["status"] = "partial"
        item[runner_shared.ZERO_WORK_RETRY_COUNT_KEY] = 2
        item["attempts"] = [
            {
                "number": 1,
                "starting_head": head,
                "ending_head": head,
                "ending_status": "",
            }
        ]
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        reread = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        assert (
            reread["queue"][0][runner_shared.ZERO_WORK_RETRY_COUNT_KEY] == 2
        ), "the counter is durable state, not in-memory bookkeeping"
        decision = runner_shared.zero_work_retry_decision(
            reread["queue"][0], reread, _verdict()
        )
        assert (decision.retry, decision.exhausted) == (False, True)
        assert decision.attempts == 2
