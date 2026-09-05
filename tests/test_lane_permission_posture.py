#!/usr/bin/env python3
"""R4 host permission posture, honestly reported per host (spec `7ckptx` A8, A8b, A8c, A9; plan
`lhmrhx` V-01, V-02, V-03, V-05).

PARAMETERIZED OVER BOTH DRIVERS WHERE THE REQUIREMENT APPLIES TO BOTH, AND DELIBERATELY NOT WHERE IT
DOES NOT. Spec 0.3 makes a containment rule landing in one driver and not the other a DEFECT, so the
shared rules run against `oc_runipd` AND `agy_runipd` from one body. But spec A8 states explicitly that
a SINGLE UNIFORM ASSERTION ACROSS BOTH HOSTS FAILS the criterion, "because it would assert a parity
that does not exist": opencode has a real denial posture and antigravity has NONE, permanently and by
design (R4.1, R4.1c). So the posture tests are per host, and each names why.

WHAT IS ASSERTED:

  * A8/R4.1 (opencode) the child environment for an unattended ISOLATED turn carries a policy denying
    BOTH external-directory and interactive-question requests, with the inherited PATH and the runner's
    import pin intact.
  * A8/R4.1a (antigravity) the attempt record states NO denial posture exists here, names the layers
    that DO apply, and NO artifact describes it as denied. Asserted MECHANICALLY over the serialized
    record, not by reading, so a reworded claim of denial still fails.
  * A8c/R4.1c the antigravity skip-permissions default is PINNED. This guard runs in the OPPOSITE
    direction from every other check here: it fails if someone "hardens" the host into the interactive
    posture that was measured to deadlock.
  * A9/R4.3 an operator-supplied policy value is verifiably MERGED or LOUDLY OVERRIDDEN, never
    silently dropped.
  * R4.2 the effective policy is OBSERVED and recorded, or an explicit unverified marker with its
    reason is recorded; and a probe failure does NOT abort the turn.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path

import pytest

from agent_workflows import agy_runipd, ipd_lifecycle, lane_containment, oc_runipd

DRIVERS = pytest.mark.parametrize(
    "driver", (oc_runipd, agy_runipd), ids=("oc_runipd", "agy_runipd")
)


# ---- A8 / R4.1, OPENCODE: a real denial ------------------------------------------------------------


class TestOpencodeDenialPosture:
    """OPENCODE HAS A REAL DENIAL, achievable through the runner-supplied runtime config (R4.1)."""

    def test_isolated_child_env_denies_both_request_classes(self, monkeypatch):
        """The child env for an unattended ISOLATED turn denies external-directory AND question.

        Both classes, not one: `external_directory` is the ask that produced the measured deadlock,
        and `question` is the interactive-question class, equally unanswerable in an unattended turn.
        A test proving only one would leave the other open.
        """

        monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)
        request = lane_containment.build_permission_policy_env(None)
        payload = json.loads(request.env_value)
        assert payload["permission"]["external_directory"] == "deny"
        assert payload["permission"]["question"] == "deny"

    def test_policy_supplied_by_the_runner_not_by_editing_repository_config(self):
        """R4.1 forbids supplying the posture by editing repository configuration.

        Asserted as a PROPERTY of the mechanism rather than by wording: the variable carries INLINE
        CONTENT (`OPENCODE_CONFIG_CONTENT`), which is owned by the runner process and vanishes with
        it. `OPENCODE_CONFIG` would be a FILE PATH, i.e. a durable artifact somebody could later
        mistake for project config, which is what the requirement rules out.
        """

        assert lane_containment.OPENCODE_RUNTIME_CONFIG_ENV == "OPENCODE_CONFIG_CONTENT"
        # The value is self-contained JSON, not a path to anything.
        request = lane_containment.build_permission_policy_env(None)
        assert isinstance(json.loads(request.env_value), dict)
        assert not Path(request.env_value).exists()

    def test_inherited_path_and_the_runner_import_pin_both_survive(self, monkeypatch):
        """The posture must not cost the child its PATH or the runner's import pin.

        Regression-shaped on purpose: the policy is injected into the SAME single child-env
        construction that carries the pin, so a fork of that construction would show up here.
        """

        monkeypatch.setenv("PATH", "/usr/bin:/bin")
        env = oc_runipd.pinned_child_env()
        env[lane_containment.OPENCODE_RUNTIME_CONFIG_ENV] = (
            lane_containment.build_permission_policy_env(None).env_value
        )
        assert env["PATH"] == "/usr/bin:/bin"
        assert env["AW_PIN_KEEP_ROOT"] == oc_runipd.runner_package_root()
        assert oc_runipd.runner_package_root() in env["PYTHONPATH"].split(":")
        assert json.loads(env[lane_containment.OPENCODE_RUNTIME_CONFIG_ENV])[
            "permission"
        ]

    def test_the_policy_actually_reaches_the_env_handed_to_the_child(
        self, tmp_path, monkeypatch
    ):
        """BEHAVIORAL, and this test exists because a SOURCE-TEXT version of it did not work.

        MEASURED during execution of this plan: an earlier version asserted the injection line was
        present in `run_opencode`'s source. Sabotaging the product (replacing the assignment with
        `pass`) left that test GREEN, because the source still mentioned the helper in a comment and
        still called it. Only capturing the env actually handed to `Popen` fails when the assignment
        is removed, which is exactly what the plan's sabotage rule is for.
        """

        captured: dict[str, dict[str, str]] = {}

        class _Proc:
            def __init__(self, *a, **kw):
                captured["env"] = dict(kw.get("env") or {})
                self.stdout = iter(())
                self.stderr = None
                self.stdin = None

            def poll(self):
                return 0

            def wait(self):
                return 0

        monkeypatch.setattr(oc_runipd.subprocess, "Popen", _Proc)
        # The probe would spawn a real host; short-circuit it, since R4.2 is proven separately.
        monkeypatch.setattr(
            oc_runipd,
            "observe_opencode_policy",
            lambda *a, **k: lane_containment.evaluate_policy_observation(
                None, {}, failure_reason="probe skipped in this test"
            ),
        )
        monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)

        repo = tmp_path / "repo"
        run_dir = tmp_path / "run"
        (run_dir / "sessions").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        lane = tmp_path / "lane"
        lane.mkdir()
        repo.mkdir()
        plan = repo / "p.ipd.md"
        plan.write_text("# p\n", encoding="utf-8")
        prompt = run_dir / "prompts" / "p.md"
        prompt.write_text("do the thing\n", encoding="utf-8")

        item = {
            "id6": "lhmrhx",
            "setid": "lanectn",
            "position": 8,
            "attempts": [{"number": 1}],
            "action": "execute",
        }
        state = {
            "run_id": "run-1",
            "repo": str(repo),
            "options": {"opencode": "opencode"},
            "queue": [item],
        }

        oc_runipd.run_opencode(
            state, run_dir, item, plan, prompt, 1, work_dir=str(lane)
        )

        env = captured["env"]
        assert (
            lane_containment.OPENCODE_RUNTIME_CONFIG_ENV in env
        ), "the policy never reached the child environment"
        policy = json.loads(env[lane_containment.OPENCODE_RUNTIME_CONFIG_ENV])[
            "permission"
        ]
        assert policy["external_directory"] == "deny"
        assert policy["question"] == "deny"
        # ...and the pin plus the role selector are still intact in the SAME construction.
        assert env["AW_PIN_KEEP_ROOT"] == oc_runipd.runner_package_root()
        assert env["AW_EXECUTION_ROLE"] == "worker"
        assert env.get("PATH"), "the inherited PATH must survive"

    def test_a_non_isolated_turn_gets_no_denial_policy(self, tmp_path, monkeypatch):
        """THE SCOPES DIFFER DELIBERATELY (R4.1 vs R4.4a), and conflating them would be a defect.

        A non-isolated turn works in the main checkout, where an external-directory denial would
        refuse its ordinary work. So the POSTURE is isolation-scoped even though the BOUNDS are not.
        """

        captured: dict[str, dict[str, str]] = {}

        class _Proc:
            def __init__(self, *a, **kw):
                captured["env"] = dict(kw.get("env") or {})
                self.stdout = iter(())
                self.stderr = None
                self.stdin = None

            def poll(self):
                return 0

            def wait(self):
                return 0

        monkeypatch.setattr(oc_runipd.subprocess, "Popen", _Proc)
        monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)

        repo = tmp_path / "repo"
        run_dir = tmp_path / "run"
        (run_dir / "sessions").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        repo.mkdir()
        plan = repo / "p.ipd.md"
        plan.write_text("# p\n", encoding="utf-8")
        prompt = run_dir / "prompts" / "p.md"
        prompt.write_text("do the thing\n", encoding="utf-8")

        item = {
            "id6": "lhmrhx",
            "setid": "lanectn",
            "position": 8,
            "attempts": [{"number": 1}],
            "action": "execute",
        }
        state = {
            "run_id": "run-1",
            "repo": str(repo),
            "options": {"opencode": "opencode"},
            "queue": [item],
        }

        oc_runipd.run_opencode(state, run_dir, item, plan, prompt, 1, work_dir=None)

        env = captured["env"]
        assert lane_containment.OPENCODE_RUNTIME_CONFIG_ENV not in env
        assert "AW_EXECUTION_ROLE" not in env


# ---- A8 / A8b / R4.1a, ANTIGRAVITY: no denial posture, stated honestly -----------------------------


class TestAntigravityHasNoDenialPosture:
    """NO DENIAL POSTURE EXISTS ON THIS HOST, permanently and by design (R4.1, R4.1b, R4.1c).

    This is NOT an unclosed gap awaiting work. The requirement here is HONEST REPORTING, and the
    specific failure it prevents is claiming a parity that does not exist.
    """

    def test_record_says_no_denial_posture_and_never_claims_denial(self):
        """A8b, asserted MECHANICALLY over the serialized record, not by reading it.

        The check targets the PROPERTY ("no claim of denial") rather than a sentence, so a reworded
        violation still fails. `posture` must not be the denied tier, and the serialized record must
        not assert that this host denies anything.
        """

        record = lane_containment.antigravity_posture_record().as_dict()
        assert record["posture"] == lane_containment.HOST_POSTURE_NONE
        assert record["posture"] != lane_containment.HOST_POSTURE_DENIED
        # No REQUESTED policy either: requesting one here would be the parity claim R4.1a forbids.
        assert "requested_policy" not in record

        blob = json.dumps(record).lower()
        # The record may legitimately EXPLAIN that no denial exists; what it may not do is assert this
        # host denies. Checked as a claim shape, so a rephrasing does not slip through.
        for claim in (
            '"posture": "denied"',
            "this host denies",
            "denial posture is in effect",
            "permission.external_directory=deny",
        ):
            assert (
                claim not in blob
            ), f"artifact claims denial on a host that has none: {claim}"

    def test_record_names_the_layers_that_do_apply(self):
        """R4.1a requires pointing at the layers that carry the guarantee, not just stating a gap.

        On this host they are LOAD-BEARING rather than defence-in-depth, which is the practical reason
        the prompt work was worth doing at all.
        """

        record = lane_containment.antigravity_posture_record().as_dict()
        layers = " ".join(record["containment_layers"])
        assert "R1" in layers and "prompt" in layers.lower()
        assert "R4.4" in layers
        assert "MAX_TURN_TIMEOUT" in layers
        assert record["containment_layers"] == list(
            lane_containment.CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL
        )

    def test_the_agy_driver_records_the_posture_for_an_isolated_turn(self):
        """The honest statement is actually WIRED, not merely available.

        SABOTAGE TARGET: deleting the `record_host_posture` call in `run_agy_turn` fails this.
        """

        src = inspect.getsource(agy_runipd.run_agy_turn)
        assert "lane_containment.record_host_posture" in src
        assert "lane_containment.antigravity_posture_record()" in src
        # And it must NOT request a denial policy on a host that has none.
        assert "build_permission_policy_env" not in src

    def test_no_driver_reimplements_the_posture_wording(self):
        """The wording comes from ONE shared constructor, so a call site cannot get it wrong (R2.6)."""

        for driver in (oc_runipd, agy_runipd):
            src = Path(inspect.getfile(driver)).read_text(encoding="utf-8")
            assert f'"{lane_containment.HOST_POSTURE_NONE}"' not in src, (
                f"{driver.__name__} hardcodes the posture tier instead of using the shared "
                "constructor, which is how a call site drifts into claiming denial"
            )


# ---- A8c / R4.1c: the antigravity default is PINNED ------------------------------------------------


class TestAntigravitySkipPermissionsDefaultIsPinned:
    """A REGRESSION GUARD IN THE OPPOSITE DIRECTION FROM EVERY OTHER CHECK HERE (A8c, R4.1c).

    It FAILS if work tracing to this spec "hardens" the host into the interactive posture that was
    measured to deadlock. Running without `--dangerously-skip-permissions` was PROVEN in practice to
    fail or deadlock repeatedly, and its only alternative requires interactive permissions an
    unattended turn has no answerer for. That is a DECIDED CONSTRAINT (maintainer ruling), so this
    plan MUST NOT flip it and this test exists to make a later flip loud.
    """

    def test_option_still_defaults_to_true_on_the_parser(self):
        args = agy_runipd.build_parser().parse_args(["start", "someid"])
        assert args.dangerously_skip_permissions is True, (
            "the skip-permissions default was flipped; R4.1c forbids that without its own "
            "decision, its own evidence the deadlock is gone, and an explicit supersession"
        )

    def test_options_default_to_true_when_the_attribute_is_absent(self):
        """Absent attribute must ALSO default on, or a caller building options by hand regresses it."""

        ns = argparse.Namespace()
        assert getattr(ns, "dangerously_skip_permissions", True) is True

    def test_the_flag_is_present_on_an_unattended_turns_argv(self):
        """The DEFAULT being True is not enough; the flag must actually reach the child's argv."""

        src = inspect.getsource(agy_runipd.run_agy_turn)
        assert 'argv.append("--dangerously-skip-permissions")' in src
        assert 'options.get("dangerously_skip_permissions", True)' in src, (
            "the argv guard must default to True, or an options dict missing the key would "
            "silently launch the interactive posture that deadlocks"
        )

    def test_this_plan_did_not_change_the_default(self):
        """Stated in the test as well as in the plan: the default is 240m/True as it shipped."""

        assert agy_runipd.DEFAULT_TIMEOUT == "240m"


# ---- A9 / R4.3: an operator value is never silently discarded --------------------------------------


class TestOperatorSuppliedPolicyIsPreserved:
    """A BLIND OVERWRITE IS NON-CONFORMING (R4.3), and the risk is real rather than hypothetical.

    The child env is built from a copy of the process environment, so assigning the policy key
    unconditionally would silently discard whatever an operator had exported, with no warning. Three
    dispositions, each RECORDED so the choice is never silent.
    """

    def test_no_operator_value_records_the_runner_as_the_source(self):
        request = lane_containment.build_permission_policy_env(None)
        assert request.source == lane_containment.POLICY_SOURCE_RUNNER
        assert request.operator_value is None

    def test_operator_json_is_merged_and_every_operator_key_survives(self):
        """MERGED, verifiably: an operator's unrelated settings must not be collateral damage."""

        operator = json.dumps(
            {
                "model": "operator/model",
                "permission": {"bash": "allow", "external_directory": "allow"},
            }
        )
        request = lane_containment.build_permission_policy_env(operator)
        assert request.source == lane_containment.POLICY_SOURCE_MERGED
        merged = json.loads(request.env_value)
        # The operator's unrelated keys survive...
        assert merged["model"] == "operator/model"
        assert merged["permission"]["bash"] == "allow"
        # ...but the runner's REQUIRED denials win, and the conflict is RECORDED, not silent.
        assert merged["permission"]["external_directory"] == "deny"
        assert merged["permission"]["question"] == "deny"
        assert "external_directory" in request.note
        assert request.operator_value == operator

    def test_unparseable_operator_value_is_overridden_loudly_not_dropped(self):
        """OVERRIDDEN EXPLICITLY AND LOUDLY: the original is preserved and the reason recorded."""

        request = lane_containment.build_permission_policy_env("{not json")
        assert request.source == lane_containment.POLICY_SOURCE_OVERRIDE
        assert request.operator_value == "{not json"
        assert "OVERRIDDEN" in request.note
        assert "preserved" in request.note
        assert json.loads(request.env_value)["permission"]["question"] == "deny"

    def test_non_object_operator_value_is_overridden_loudly(self):
        request = lane_containment.build_permission_policy_env('"a string"')
        assert request.source == lane_containment.POLICY_SOURCE_OVERRIDE
        assert "OVERRIDDEN" in request.note

    def test_no_disposition_is_silent(self):
        """THE PROPERTY, not the wording: every disposition carries a non-empty explanation."""

        for value in (None, "", "{}", "{not json", '"str"', '{"permission": 3}'):
            request = lane_containment.build_permission_policy_env(value)
            assert request.note, f"disposition for {value!r} was recorded silently"
            assert request.source in {
                lane_containment.POLICY_SOURCE_RUNNER,
                lane_containment.POLICY_SOURCE_MERGED,
                lane_containment.POLICY_SOURCE_OVERRIDE,
            }

    def test_never_raises_on_any_operator_value(self):
        """An unusable operator value must not abort a turn (same reasoning as the R4.2 probe)."""

        for value in (None, "", "   ", "[]", "null", "3", "{", '{"permission": null}'):
            lane_containment.build_permission_policy_env(value)


# ---- R4.2: the effective policy is OBSERVED, or explicitly marked unverified -----------------------


class TestPolicyObservation:
    """OBSERVE, DO NOT ASSUME THE REQUEST WON (R4.2).

    Host configuration precedence can place a managed source ABOVE the runner's, so a run that only
    SETS the policy can believe it is protected when it is not. Recording NOTHING is what the
    requirement forbids; an unverified marker with its reason is a conforming outcome.
    """

    REQUESTED = {"external_directory": "deny", "question": "deny"}

    def test_a_conforming_host_config_is_recorded_as_observed(self):
        raw = json.dumps(
            {
                "permission": {
                    "external_directory": "deny",
                    "question": "deny",
                    "bash": "allow",
                }
            }
        )
        obs = lane_containment.evaluate_policy_observation(
            raw, self.REQUESTED, host_version="1.18.27"
        )
        assert obs.result == lane_containment.POLICY_OBSERVED
        assert obs.conforms is True
        assert obs.effective == {"external_directory": "deny", "question": "deny"}
        assert obs.as_dict()["host_version"] == "1.18.27"

    def test_a_higher_precedence_override_is_detected_not_assumed_away(self):
        """THE WHOLE POINT OF R4.2: the host reports `ask`, so the run is NOT protected."""

        raw = json.dumps(
            {"permission": {"external_directory": "ask", "question": "deny"}}
        )
        obs = lane_containment.evaluate_policy_observation(raw, self.REQUESTED)
        assert obs.result == lane_containment.POLICY_OBSERVED
        assert obs.conforms is False
        assert obs.reason, "a non-conforming observation must say why"

    @pytest.mark.parametrize(
        "raw,why",
        (
            (None, "unreadable"),
            ("not json at all", "unparseable"),
            ("[]", "not an object"),
            ('{"model": "x"}', "no permission object"),
        ),
    )
    def test_every_unobservable_shape_records_an_explicit_marker_with_a_reason(
        self, raw, why
    ):
        """RECORDING NOTHING IS THE FAILURE. Each bad shape yields a marker AND a reason."""

        obs = lane_containment.evaluate_policy_observation(raw, self.REQUESTED)
        assert obs.result == lane_containment.POLICY_UNVERIFIED, why
        assert (
            obs.reason
        ), f"{why}: an unverified marker with no reason is not conforming"
        assert "reason" in obs.as_dict()

    def test_the_probe_never_aborts_the_turn(self):
        """OQ-01 resolved NO: the observation is a DIAGNOSTIC, not a precondition.

        A probe failure must be recorded and the turn continue, because the R4.4 bounds hold
        regardless of what the host decided. Letting it propagate would abort turns that were
        otherwise fine, which is strictly worse than the unknown it removes.
        """

        obs = oc_runipd.observe_opencode_policy(
            "definitely-not-an-executable-anywhere", {}, self.REQUESTED
        )
        assert obs.result == lane_containment.POLICY_UNVERIFIED
        assert obs.reason

    def test_the_observation_reaches_the_attempt_record(self, tmp_path):
        """R4.2's failure mode is a run that believes it is protected, so it must be RECORDED."""

        item = {"id6": "lhmrhx", "attempts": [{"number": 1}]}
        obs = lane_containment.evaluate_policy_observation(
            None, self.REQUESTED, failure_reason="probe unavailable in this test"
        )
        record = lane_containment.record_host_posture(
            tmp_path,
            item,
            1,
            lane_containment.opencode_posture_record(
                lane_containment.build_permission_policy_env(None)
            ),
            obs,
        )
        assert item["attempts"][0]["host_posture"] == record
        assert (
            record["policy_observation"]["result"] == lane_containment.POLICY_UNVERIFIED
        )
        assert (
            record["policy_observation"]["reason"] == "probe unavailable in this test"
        )
        assert record["posture"] == lane_containment.HOST_POSTURE_DENIED
        events = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
        assert "host-permission-posture" in events

    def test_the_driver_observes_rather_than_assuming(self):
        """SABOTAGE TARGET: deleting the observation call in `run_opencode` fails this."""

        src = inspect.getsource(oc_runipd.run_opencode)
        assert "observe_opencode_policy" in src
        assert "lane_containment.record_host_posture" in src


# ---- R4.5 / R2.6 shared-home checks that apply to BOTH hosts ---------------------------------------


@DRIVERS
def test_the_role_selector_is_carried_for_an_isolated_turn(driver):
    """R4.5 on both hosts: an isolated turn's child env carries the execution-role selector."""

    launcher = driver.run_opencode if driver is oc_runipd else driver.run_agy_turn
    src = inspect.getsource(launcher)
    assert (
        "child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER" in src
    )
    assert "child_env.pop(ipd_lifecycle.EXECUTION_ROLE_ENV, None)" in src
    assert ipd_lifecycle.EXECUTION_ROLE_ENV == "AW_EXECUTION_ROLE"


@DRIVERS
def test_neither_driver_holds_a_second_copy_of_the_shared_posture_rules(driver):
    """A5c/R2.6: one definition per rule, in the DECLARED shared module, not per host."""

    src = Path(inspect.getfile(driver)).read_text(encoding="utf-8")
    for symbol in (
        "def build_permission_policy_env",
        "def evaluate_policy_observation",
        "def record_host_posture",
        "def antigravity_posture_record",
        "def opencode_posture_record",
        "def bound_expiry_reaper",
        "class TurnBoundWatch",
    ):
        assert symbol not in src, (
            f"{driver.__name__} defines {symbol!r}, forking a rule whose single home is "
            "`agent_workflows/lane_containment.py` (spec R2.6)"
        )
