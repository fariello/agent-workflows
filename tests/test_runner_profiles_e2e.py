"""End-to-end proof of the WHOLE runner-profile feature, from an empty XDG dir to exact argv.

`runprofile` Order 05 (`p7xhhm`) E-04. Every other suite in this Set tests ONE layer with the
layers around it mocked, and that is correct for those suites. It is also exactly how a feature
passes its unit tests while being broken end to end: the schema round-trips, the wizard saves,
the runner resolves, the router routes, and yet no wizard-authored byte ever reaches a launched
process because two adjacent layers agreed on different field names.

SO THIS FILE MOCKS ONLY THE PROCESS BOUNDARY, and nothing above it. There is no fake schema, no
fake store, no fake wizard, no fake resolver, and no fake router: a test here writes into a real
temporary XDG directory by driving the REAL interview, then invokes the REAL CLI, and asserts on
the argv that would have been handed to `opencode` and on the `state.json` actually written to
disk. The chain under test is therefore:

    interview answers -> runner-profiles.json -> `aw run as`/`aw run ipd` -> runner resolution
    -> frozen durable state -> the argv of EVERY turn -> resume

WHAT EACH GROUP FALSIFIES, since a test that cannot fail proves nothing:

* `WizardToArgvE2E`: the wizard's saved bytes reach the LAUNCHED argv, through both the named
  (`as gem`) and the unqualified (`ipd`) form. A profile that only reached the resolver, or only
  the first turn, fails here.
* `DurableIdentityE2E`: the resolved identity is FROZEN. The alias is repointed and then deleted
  after the run starts, and the run's own state must not move.
* `NegativeE2E`: every refusal happens BEFORE durable state exists, so a bad invocation costs
  nothing and leaves nothing to clean up.
* `NamespaceE2E`: the existing run-ledger family and command-LIKE profile names coexist, which is
  the collision claim the fixed grammar exists to support.

Synthetic model identifiers only (`synthetic/...`). A real provider/model string in a tracked
file would disclose institutional topology, which is the reason the store is user-local at all.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

import pytest

from agent_workflows import (
    cli,
    oc_models,
    runner_profile_wizard as wiz,
    runner_profiles as rp,
)

# Spawns real `git` and the real driver in subprocesses for the durable-state cases.
pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parents[1]
_DRIVER_CMD = [sys.executable, "-m", "agent_workflows.oc_runipd"]

GEM_MODEL = "synthetic/gem-test"
SOL_MODEL = "synthetic/sol-test"


# ==================================================================================================
# Fixtures: a real empty XDG dir, the real interview, and a real repo holding one approved plan
# ==================================================================================================


def _cli(*argv: str) -> Tuple[int, str]:
    """Invoke the REAL CLI in-process, capturing stdout+stderr."""

    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(list(argv))
    except SystemExit as exc:
        rc = int(exc.code or 0)
    return rc, out.getvalue() + err.getvalue()


_CONFORMING_PLAN = """\
# IPD: Demo end-to-end profile plan

- Date: 2026-08-29
- Kind: child
- Concern: demo concern for the runner-profile end-to-end test.
- Scope: demo scope.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
- Set: demo
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history

- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 draft (test): created.

## Goal

Demo goal sentence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: demo

- [x] E-01 Create the demo file.
  - Depends on: none
  - Expected outcome: the demo file exists.
  - Execution state: performed

## Project conventions discovered (Step 0)

- demo convention.

## Findings

demo findings.

## Proposed changes (ordered, validatable)

1. src/demo.txt: create it.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Manual check that src/demo.txt exists.

## Spec / documentation sync

N/A: demo only.

## Open questions

### OQ-01: none?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass.

- [x] V-01 validates E-01
  - Required evidence: src/demo.txt present.
  - Observed evidence: src/demo.txt present.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit path-scoped; do not push.
"""


def _init_repo(repo: Path, id6: str) -> Path:
    """A real git repo holding one approved, lint-conforming plan (run state gitignored)."""

    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    plan = pending / f"20260829-demo-01-{id6}-demo.ipd.md"
    plan.write_text(_CONFORMING_PLAN.format(id6=id6), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return plan


class _EmptyXdgFixture(unittest.TestCase):
    """An EMPTY temporary XDG config home. Every test starts with NO profile store at all."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.xdg = self.root / "cfg"
        self._env = mock.patch.dict(
            os.environ, {"XDG_CONFIG_HOME": str(self.xdg), "NO_COLOR": "1"}
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        # The precondition every test in this file depends on: nothing configured yet.
        self.assertFalse(rp.store_path().exists(), "fixture did not start empty")

    @property
    def store(self) -> Path:
        return rp.store_path()

    def driver_env(self) -> Dict[str, str]:
        """Env for a SUBPROCESS driver run, pointed at this same synthetic XDG dir."""

        return {
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT),
            "XDG_CONFIG_HOME": str(self.xdg),
            "NO_COLOR": "1",
        }

    # -- the REAL interview, driven by a scripted transcript ----------------------------------

    def interview(self, answers: List[str], models=(GEM_MODEL, SOL_MODEL)) -> List[Any]:
        """Run the REAL `runner_profile_wizard.run_session` against the REAL store.

        Only `oc_models.discover_models` is stubbed, because a catalog read is a subprocess call
        to the operator's own `opencode` and this suite must not depend on one being installed.
        Everything else (validation, the preview, the save confirmation, the two default
        questions, the atomic write) is the shipped code path.
        """

        pending = list(answers)

        def ask(_prompt: str) -> str:
            if not pending:
                raise EOFError
            return pending.pop(0)

        catalog = oc_models.ModelCatalog(
            models=tuple(models), source=oc_models.CATALOG_SOURCE_CLI
        )
        io_ = wiz.WizardIO(
            ask=ask,
            emit=lambda _line: None,
            discover=lambda: catalog,
            load=rp.load,
            save=rp.save,
        )
        return wiz.run_session(io_)

    def setup_step(self, answers: List[str], models=(GEM_MODEL, SOL_MODEL)) -> None:
        """Drive the REAL `aw setup` profile step (E-01) against the REAL store."""

        import argparse

        from agent_workflows.term import Term

        pending = list(answers)

        def fake_input(_prompt: str = "") -> str:
            if not pending:
                raise EOFError
            return pending.pop(0)

        catalog = oc_models.ModelCatalog(
            models=tuple(models), source=oc_models.CATALOG_SOURCE_CLI
        )
        term = Term(stream=io.StringIO(), color=False)
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
            mock.patch.object(cli, "input", create=True, side_effect=fake_input),
            mock.patch.object(oc_models, "discover_models", return_value=catalog),
        ):
            cli._configure_runner_profiles(argparse.Namespace(yes=False), term)


class _ArgvSpyFixture(_EmptyXdgFixture):
    """Captures the argv the router hands the OpenCode driver (the process boundary)."""

    def forwarded(self, *argv: str) -> Tuple[int, List[List[str]]]:
        calls: List[List[str]] = []

        def fake_main(a: Optional[List[str]] = None) -> int:
            calls.append(list(a or []))
            return 0

        with mock.patch("agent_workflows.oc_runipd.main", side_effect=fake_main):
            rc, _out = _cli(*argv)
        return rc, calls


# ==================================================================================================
# 1. Wizard answers reach the LAUNCHED argv (both run forms)
# ==================================================================================================


class WizardToArgvE2E(_ArgvSpyFixture):
    """The load-bearing chain: an answer typed at the interview reaches a launched argv."""

    #: gate is NOT part of this transcript: `interview` enters the session directly.
    #: name -> model #1 -> variant `high` (option 4) -> no agent -> save -> default profile yes
    #: -> default runner yes -> no second profile.
    GEM = ["gem", "1", "4", "", "y", "y", "y", "n"]

    def test_setup_interview_creates_the_store_from_an_empty_xdg_directory(self):
        """Start with NOTHING configured, run the setup step, and get a real usable store."""

        self.setup_step(["y", *self.GEM])
        # The file exists, on disk, written by the shipped atomic writer.
        self.assertTrue(self.store.is_file(), "no store was written")
        doc = json.loads(self.store.read_text(encoding="utf-8"))
        # A freshly WRITTEN document declares the version this aw writes, which `runprofile`
        # Order 06 (`kgpptv`) bumped to 2 when `verify_with` was added (DECISION 06-kgpptv-D2).
        # Asserted against the constant rather than a literal, so the next bump does not require
        # editing an unrelated wizard test; the READ side (a v1 document still loading) is
        # asserted in `tests/test_runner_profiles.py`.
        self.assertEqual(doc["schema_version"], rp.SCHEMA_VERSION)
        self.assertEqual(rp.SCHEMA_VERSION, 2)
        self.assertEqual(doc["profiles"]["gem"]["model"], GEM_MODEL)
        self.assertEqual(doc["profiles"]["gem"]["variant"], "high")
        self.assertEqual(doc["profiles"]["gem"]["runner"], "oc")
        # Both defaults were accepted as SEPARATE answers.
        self.assertEqual(doc["defaults"]["profiles"]["oc"], "gem")
        self.assertEqual(doc["default_runner"], "oc")
        # And no forbidden key rode along.
        text = self.store.read_text(encoding="utf-8").lower()
        for forbidden in ("api_key", "token", "secret", "args", "env", "command"):
            self.assertNotIn(f'"{forbidden}"', text)

    def test_named_form_forwards_the_wizard_authored_clause(self):
        self.setup_step(["y", *self.GEM])
        rc, calls = self.forwarded("run", "as", "gem", "demo01")
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1, calls)
        # The clause is RE-STATED for the host, which is what keeps resolution unforked.
        self.assertEqual(calls[0], ["as", "gem", "demo01"])

    def test_unqualified_form_routes_through_the_wizard_authored_default_runner(self):
        """`aw run ipd` works ONLY because the interview's second default question was accepted."""

        self.setup_step(["y", *self.GEM])
        rc, calls = self.forwarded("run", "ipd", "demo01")
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [["demo01"]])

    def test_unqualified_form_refuses_when_the_default_runner_was_declined(self):
        """The CONTROLLED NEGATIVE for the test above: declining really does leave it unset."""

        # Same transcript, but DECLINE the default-runner question.
        self.setup_step(["y", "gem", "1", "4", "", "y", "y", "n", "n"])
        self.assertIsNone(rp.load().default_runner)
        rc, calls = self.forwarded("run", "ipd", "demo01")
        self.assertEqual(rc, 2)
        self.assertEqual(calls, [], "a host was launched with no default_runner")

    def test_per_field_override_keeps_the_rest_of_the_profile(self):
        """`--variant` must not discard the profile: the host receives BOTH the clause and flag."""

        self.setup_step(["y", *self.GEM])
        rc, calls = self.forwarded("run", "as", "gem", "demo01", "--variant", "max")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0], ["as", "gem", "demo01", "--variant", "max"])

    def test_named_and_host_explicit_forms_forward_equivalent_arguments(self):
        """`aw run as gem X` and `aw oc run as gem X` must not drift apart."""

        self.setup_step(["y", *self.GEM])
        _, neutral = self.forwarded("run", "as", "gem", "demo01")
        _, explicit = self.forwarded("oc", "run", "as", "gem", "demo01")
        self.assertEqual(neutral[0], explicit[0])

    def test_two_profiles_created_in_one_session_are_both_dispatchable(self):
        # Round 1 accepts BOTH defaults, so round 2 is asked only about the default PROFILE
        # (the default-runner question is skipped once it would change nothing).
        answers = [
            *["gem", "1", "4", "", "y", "y", "y"],
            "y",  # configure another?
            *["sol", "2", "3", "", "y", "n"],
            "n",  # configure another? no
        ]
        self.interview(answers)
        cfg = rp.load()
        self.assertEqual(sorted(cfg.profiles), ["gem", "sol"])
        self.assertEqual(cfg.profiles["sol"].model, SOL_MODEL)
        for name in ("gem", "sol"):
            rc, calls = self.forwarded("run", "as", name, "demo01")
            self.assertEqual(rc, 0, name)
            self.assertEqual(calls[0][:2], ["as", name])

    def test_edited_alias_changes_later_launches(self):
        """Sanity control for the freeze tests: with no run in flight, an edit DOES take effect."""

        self.setup_step(["y", *self.GEM])
        _, before = self.forwarded("run", "as", "gem", "demo01")
        rc, _out = _cli(
            "oc",
            "profile",
            "add",
            "gem",
            "--model",
            SOL_MODEL,
            "--replace",
            "--yes",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(rp.load().profiles["gem"].model, SOL_MODEL)
        _, after = self.forwarded("run", "as", "gem", "demo01")
        # The forwarded clause is identical (the HOST resolves fields), but the STORE moved.
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(
            json.loads(self.store.read_text(encoding="utf-8"))["profiles"]["gem"][
                "model"
            ],
            GEM_MODEL,
        )


# ==================================================================================================
# 2. The frozen durable identity, proven on the REAL driver against the REAL store
# ==================================================================================================


class DurableIdentityE2E(_EmptyXdgFixture):
    """A wizard-created profile reaches `state.json`, and a later edit cannot move it."""

    GEM = ["gem", "1", "4", "", "y", "y", "y", "n"]

    def _prepare_run(self, id6: str, *clause: str) -> Tuple[Path, str]:
        """Start a REAL `--prepare-only` run through the driver; return (run_dir, stdout)."""

        repo = self.root / f"repo-{id6}"
        _init_repo(repo, id6)
        res = subprocess.run(
            _DRIVER_CMD + [*clause, id6, "--repo", os.fspath(repo), "--prepare-only"],
            cwd=repo,
            env=self.driver_env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        runs = sorted((repo / ".aw" / "records" / "runs").glob("run-*"))
        self.assertEqual(len(runs), 1, res.stdout + res.stderr)
        return runs[0], res.stdout

    def test_wizard_created_profile_lands_in_state_json_with_provenance(self):
        self.setup_step(["y", *self.GEM])
        run_dir, stdout = self._prepare_run("prof10", "as", "gem")
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        opts = state["options"]
        # The RESOLVED values, in the keys every turn already reads.
        self.assertEqual(opts["model"], GEM_MODEL)
        self.assertEqual(opts["variant"], "high")
        lp = opts["launch_profile"]
        self.assertEqual(lp["requested"], "gem")
        self.assertEqual(lp["applied"], "gem")
        self.assertEqual(lp["runner"], "oc")
        self.assertEqual(lp["provenance"]["model"], "profile")
        self.assertTrue(lp["config_digest"])
        self.assertIn("runner-profiles.json", lp["config_source"])
        # The operator can SEE the identity before paying for a turn.
        self.assertIn(GEM_MODEL, stdout)
        # No credential-shaped key rode into durable state.
        blob = json.dumps(lp).lower()
        for forbidden in ("api_key", "token", "secret", "password"):
            self.assertNotIn(forbidden, blob)

    def test_default_profile_reaches_state_without_a_named_clause(self):
        """The unqualified path: the interview's default-profile answer is what supplies the model."""

        self.setup_step(["y", *self.GEM])
        run_dir, _ = self._prepare_run("prof11")
        lp = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
            "options"
        ]["launch_profile"]
        self.assertIsNone(lp["requested"])
        self.assertEqual(lp["applied"], "gem")
        self.assertEqual(lp["provenance"]["model"], "default-profile")

    def test_repointing_then_deleting_the_alias_does_not_move_a_started_run(self):
        """The whole durability claim, on the REAL resume path, with TWO mutations."""

        self.setup_step(["y", *self.GEM])
        run_dir, _ = self._prepare_run("prof12", "as", "gem")
        repo = run_dir.parents[3]
        frozen = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        frozen_digest = frozen["options"]["launch_profile"]["config_digest"]

        def status_state() -> Dict[str, Any]:
            res = subprocess.run(
                _DRIVER_CMD
                + ["status", run_dir.name, "--repo", os.fspath(repo), "--json"],
                cwd=repo,
                env=self.driver_env(),
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            return json.loads(res.stdout)

        # MUTATION 1: repoint `gem` at a different model, through the real CLI.
        rc, out = _cli(
            "oc", "profile", "add", "gem", "--model", SOL_MODEL, "--replace", "--yes"
        )
        self.assertEqual(rc, 0, out)
        state = status_state()
        self.assertEqual(
            state["options"]["model"], GEM_MODEL, "a repoint moved the run"
        )
        self.assertEqual(state["options"]["variant"], "high")
        self.assertEqual(
            state["options"]["launch_profile"]["config_digest"], frozen_digest
        )

        # MUTATION 2: delete the store outright. The run must still render its own identity.
        self.store.unlink()
        state = status_state()
        self.assertEqual(
            state["options"]["model"], GEM_MODEL, "a deletion moved the run"
        )
        self.assertEqual(
            state["options"]["launch_profile"]["config_digest"], frozen_digest
        )

    def test_controlled_negative_a_moved_store_is_observable_when_re_resolved(self):
        """Proves the freeze test above is not vacuous: re-resolution WOULD change the digest."""

        import argparse

        from agent_workflows import oc_runipd as driver

        self.setup_step(["y", *self.GEM])
        args = argparse.Namespace(profile="gem", model=None, variant=None, agent=None)
        before = driver.launch_profile_record(driver.resolve_launch_profile(args))
        rc, _ = _cli(
            "oc", "profile", "add", "gem", "--model", SOL_MODEL, "--replace", "--yes"
        )
        self.assertEqual(rc, 0)
        after = driver.launch_profile_record(driver.resolve_launch_profile(args))
        self.assertNotEqual(before["model"], after["model"])
        self.assertNotEqual(before["config_digest"], after["config_digest"])


# ==================================================================================================
# 3. Negative paths: every refusal happens BEFORE durable state exists
# ==================================================================================================


class NegativeE2E(_EmptyXdgFixture):
    """A bad invocation must cost nothing: no run id, no run directory, no partial state."""

    def _refusal_leaves_no_state(self, *clause: str) -> str:
        repo = self.root / f"repo-neg-{len(clause)}-{clause[-1][:6]}"
        _init_repo(repo, "prof20")
        runs_root = repo / ".aw" / "records" / "runs"
        before = (
            sorted(p.name for p in runs_root.glob("*")) if runs_root.exists() else []
        )
        res = subprocess.run(
            _DRIVER_CMD + [*clause, "prof20", "--repo", os.fspath(repo)],
            cwd=repo,
            env=self.driver_env(),
            capture_output=True,
            text=True,
        )
        combined = res.stdout + res.stderr
        self.assertEqual(res.returncode, 2, combined)
        after = (
            sorted(p.name for p in runs_root.glob("*")) if runs_root.exists() else []
        )
        self.assertEqual(before, after, "a refused run left durable state behind")
        self.assertNotIn("Run ID:", res.stdout)
        return combined

    def test_unknown_profile_refuses_before_any_durable_state(self):
        self.setup_step(["y", "gem", "1", "4", "", "y", "n", "n", "n"])
        out = self._refusal_leaves_no_state("as", "nope")
        self.assertIn("nope", out)

    def test_malformed_store_refuses_and_is_never_read_as_empty(self):
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text("{not json", encoding="utf-8")
        out = self._refusal_leaves_no_state("as", "gem")
        # Reported as a parse failure, NOT as "no such profile" (which would mean it degraded
        # to empty and would have silently launched the host default model).
        self.assertNotIn("no runner profile named", out)

    def test_unqualified_dispatch_with_no_configuration_refuses_with_the_fix(self):
        rc, out = _cli("run", "ipd", "demo01")
        self.assertEqual(rc, 2, out)
        self.assertIn("default_runner", out)
        self.assertFalse(self.store.exists(), "a refusal created a store")

    def test_unknown_profile_in_the_router_refuses_without_launching(self):
        self.setup_step(["y", "gem", "1", "4", "", "y", "n", "n", "n"])
        calls: List[List[str]] = []
        with mock.patch(
            "agent_workflows.oc_runipd.main",
            side_effect=lambda a=None: calls.append(list(a or [])) or 0,
        ):
            rc, out = _cli("run", "as", "nope", "demo01")
        self.assertEqual(rc, 2, out)
        self.assertEqual(calls, [], "the host was launched for an unknown profile")

    def test_wrong_runner_profile_is_not_launched_by_opencode(self):
        """A profile for another host must be refused, not run by the wrong driver."""

        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "profiles": {"gg": {"runner": "agy", "model": GEM_MODEL}},
                }
            ),
            encoding="utf-8",
        )
        calls: List[List[str]] = []
        with mock.patch(
            "agent_workflows.oc_runipd.main",
            side_effect=lambda a=None: calls.append(list(a or [])) or 0,
        ):
            rc, out = _cli("run", "as", "gg", "demo01")
        # MEASURED behavior, and the stricter of the two possible refusals: version 1's registry
        # (`runner_profiles.RUNNER_REGISTRY`) admits `oc` ONLY, so `agy` is refused at STORE LOAD
        # by the schema, before the router ever reaches its adapter table. Either way the
        # OpenCode driver is NOT called, which is the claim that matters: a profile for another
        # host is never quietly run by this one.
        self.assertEqual(rc, 2, out)
        self.assertEqual(calls, [], "the wrong host driver was launched")
        self.assertIn("unknown runner 'agy'", out)
        self.assertIn("registers: oc", out)

    def test_a_declined_interview_leaves_no_store_to_dispatch_from(self):
        self.setup_step(["n"])
        self.assertFalse(self.store.exists())
        rc, out = _cli("run", "ipd", "demo01")
        self.assertEqual(rc, 2, out)


# ==================================================================================================
# 4. Namespace safety: the run-ledger family and command-like profile names coexist
# ==================================================================================================


class NamespaceE2E(_ArgvSpyFixture):
    """A profile name is read ONLY after `as`, so it can never shadow a real command."""

    def _write_command_like_store(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "default_runner": "oc",
                    "defaults": {"profiles": {"oc": "gem"}},
                    "profiles": {
                        "gem": {"runner": "oc", "model": GEM_MODEL},
                        "status": {"runner": "oc", "model": SOL_MODEL},
                        "show": {"runner": "oc", "model": SOL_MODEL},
                        "evidence": {"runner": "oc", "model": SOL_MODEL},
                        "run": {"runner": "oc", "model": SOL_MODEL},
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_command_like_profile_names_dispatch_after_as(self):
        self._write_command_like_store()
        for name in ("status", "show", "evidence", "run"):
            rc, calls = self.forwarded("run", "as", name, "demo01")
            self.assertEqual(rc, 0, name)
            self.assertEqual(calls[0], ["as", name, "demo01"], name)

    def test_the_reading_noun_still_reaches_the_viewer_not_a_launcher(self):
        """`aw runs ...` must stay READ-ONLY even with a profile named `status`."""

        self._write_command_like_store()
        calls: List[List[str]] = []
        with mock.patch(
            "agent_workflows.oc_runipd.main",
            side_effect=lambda a=None: calls.append(list(a or [])) or 0,
        ):
            # A nonexistent run: the point is only that NO host launch happened.
            _cli("runs", "show", "run-does-not-exist")
        self.assertEqual(calls, [], "an inspection verb launched a host")

    def test_no_profile_name_became_a_command(self):
        """The inverse claim: a stored profile must not manufacture any command spelling."""

        self._write_command_like_store()
        from agent_workflows.command_surface import discover_parser_leaves

        leaves = set(discover_parser_leaves(cli._build_parser()))
        for spelling in ("gem", "run gem", "run-gem", "rungem", "gemrun", "runs gem"):
            self.assertNotIn(spelling, leaves, spelling)
        # The two FIXED routes are the only dispatch grammar.
        self.assertIn("run as", leaves)
        self.assertIn("run ipd", leaves)

    def test_ledger_write_verbs_are_untouched_by_a_profile_store(self):
        """`aw run start/record/cancel/finalize` must not be reinterpreted as dispatch."""

        self._write_command_like_store()
        from agent_workflows.command_surface import discover_parser_leaves

        leaves = set(discover_parser_leaves(cli._build_parser()))
        for leaf in ("run start", "run record", "run cancel", "run finalize"):
            self.assertIn(leaf, leaves, leaf)

    def test_a_selector_that_looks_like_a_profile_stays_a_selector(self):
        """Without `as`, a token equal to a profile name is a SELECTOR, never a profile."""

        self._write_command_like_store()
        rc, calls = self.forwarded("run", "ipd", "gem")
        self.assertEqual(rc, 0)
        # Forwarded verbatim with NO `as` clause synthesized.
        self.assertEqual(calls[0], ["gem"])


# ==================================================================================================
# 5. The published contract matches the SHIPPED surface (E-03 / V-03)
# ==================================================================================================


class PublishedContractParityTests(unittest.TestCase):
    """`docs/runner-profiles.md` is the user authority, so every command it prints must parse.

    THE FAILURE THIS PREVENTS is a stale doc, which outlives a merge conflict: a reader who is
    told to run a command that does not exist has no way to know the doc is wrong rather than
    their installation. `docs_check.check_aw_commands` already validates the `aw <sub>` tokens
    repository-wide; this goes further and PARSES the exact invocations, and asserts the
    precedence rule the doc states is the rule the resolver implements.
    """

    DOC = REPO_ROOT / "docs" / "runner-profiles.md"

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = cls.DOC.read_text(encoding="utf-8")

    def test_the_authority_exists_and_is_linked_from_readme_and_the_cli_guide(self):
        self.assertTrue(self.DOC.is_file())
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        guide = (REPO_ROOT / "docs" / "cli-human-guide.md").read_text(encoding="utf-8")
        self.assertIn("docs/runner-profiles.md", readme)
        self.assertIn("runner-profiles.md", guide)

    def test_every_canonical_run_form_the_doc_publishes_actually_parses(self):
        """The PR-003 guard: a published grammar must be the shipped grammar."""

        parser = cli._build_parser()
        for argv in (
            ["run", "as", "gem", "demo01"],
            ["run", "ipd", "demo01"],
            ["oc", "run", "as", "gem", "demo01"],
            ["oc", "profile", "add"],
            ["oc", "profile", "list"],
            ["oc", "profile", "show", "gem"],
            ["oc", "profile", "remove", "gem"],
            ["oc", "profile", "default", "gem"],
            ["oc", "profile", "default", "--clear"],
        ):
            with self.subTest(argv=argv):
                parser.parse_args(argv)  # raises SystemExit on an unknown form
        # And the two dispatch routes really are the doc's "fixed grammar".
        self.assertEqual(sorted(("as", "ipd")), sorted(("as", "ipd")))
        from agent_workflows import run_dispatch

        self.assertEqual(sorted(run_dispatch.ROUTES), ["as", "ipd"])

    def test_the_doc_states_the_precedence_the_resolver_implements(self):
        """Documented precedence is asserted against `runner_profiles.resolve`, not restated."""

        cfg = rp.from_document(
            {
                "schema_version": 1,
                "profiles": {
                    "gem": {
                        "runner": "oc",
                        "model": GEM_MODEL,
                        "variant": "high",
                        "agent": "build",
                    }
                },
                "defaults": {"profiles": {"oc": "gem"}},
            }
        )
        # 1. Explicit beats the named profile, PER FIELD (the doc's headline rule).
        r = rp.resolve(cfg, runner="oc", profile="gem", variant="max")
        self.assertEqual(r.variant, "max")
        self.assertEqual(r.model, GEM_MODEL, "an explicit field discarded the profile")
        self.assertEqual(r.agent, "build")
        self.assertEqual(r.provenance["variant"], "explicit")
        self.assertEqual(r.provenance["model"], "profile")
        # 2. The per-runner default applies when nothing is named.
        r = rp.resolve(cfg, runner="oc")
        self.assertEqual(r.applied_profile, "gem")
        self.assertEqual(r.provenance["model"], "default-profile")
        # 3. The host default applies when no level supplied a value.
        bare = rp.from_document({"schema_version": 1, "profiles": {}})
        r = rp.resolve(bare, runner="oc")
        self.assertIsNone(r.model)
        self.assertEqual(r.provenance["model"], "host-default")
        # 4. `validate` is a TRI-STATE whose shipped default is OFF, as documented.
        self.assertFalse(rp.SHIPPED_VALIDATE_DEFAULT)
        self.assertEqual(r.provenance["validate"], "shipped-default")

    def test_the_doc_names_the_real_store_location_and_reserved_names(self):
        self.assertIn("runner-profiles.json", self.text)
        self.assertEqual(rp.STORE_NAME, "runner-profiles.json")
        self.assertIn("XDG_CONFIG_HOME", self.text)
        # The two reserved names the doc calls out are the schema's own set.
        self.assertEqual(sorted(rp.RESERVED_PROFILE_NAMES), ["as", "default"])
        for name in ("as", "default"):
            self.assertIn(f"`{name}`", self.text)

    def test_every_field_the_doc_says_is_refused_really_is(self):
        """The privacy claim, asserted against the schema rather than trusted."""

        for forbidden in ("api_key", "token", "args", "env", "command", "prompt"):
            with self.subTest(key=forbidden):
                self.assertIn(forbidden, rp.FORBIDDEN_PROFILE_KEYS)
                with self.assertRaises(rp.ProfileSchemaError):
                    rp.parse_profile(
                        "x", {"runner": "oc", "model": GEM_MODEL, forbidden: "v"}
                    )
        # And the allowed set is exactly what the doc lists. `verify_with` joined both the schema
        # and the doc in `runprofile` Order 06 (`kgpptv`); it is a profile NAME, not a credential
        # or an argv fragment, so it does not weaken the claim this test defends.
        self.assertEqual(
            sorted(rp.ALLOWED_PROFILE_KEYS),
            ["agent", "model", "runner", "validate", "variant", "verify_with"],
        )

    def test_the_doc_contains_no_em_or_en_dash(self):
        """Repository convention for user-facing prose, enforced by `docs_check` too."""

        self.assertNotIn("\u2014", self.text)
        self.assertNotIn("\u2013", self.text)

    def test_the_doc_states_the_verify_with_limits_rather_than_implying_parity(self):
        """`runprofile` Order 06 (`kgpptv`) E-05(a).

        "The verifier can use a different profile" reads as host-agnostic and is NOT: the Antigravity
        runner has ZERO profile integration, so the doc must say so rather than let a reader infer
        parity. It must also not imply a different RUNNER can verify, which is deferred (OQ-01).
        """

        self.assertIn("verify_with", self.text)
        # It is OpenCode only, and the doc says which host does NOT participate.
        self.assertIn("OPENCODE ONLY", self.text.upper())
        self.assertIn("does not read runner profiles", self.text)
        # And it must not promise cross-runner verification.
        self.assertIn("routes the model, not the host", self.text)
        # The claim is true: the agy runner references no profile symbol at all.
        agy = (REPO_ROOT / "agent_workflows" / "agy_runipd.py").read_text(
            encoding="utf-8"
        )
        for symbol in ("runner_profiles", "launch_profile", "verify_with"):
            self.assertEqual(agy.count(symbol), 0, symbol)
        print(
            "doc states the OC-only limit; agy_runipd references 0 profile symbols, so the "
            "limit is a property of the system rather than of the doc's wording"
        )

    def test_the_doc_and_the_schema_agree_on_the_written_version(self):
        """The version bump is a USER-FACING contract, so the doc must state it (E-01 / D2)."""

        self.assertIn("`schema_version` 2", self.text)
        self.assertEqual(rp.SCHEMA_VERSION, 2)
        self.assertEqual(sorted(rp.SUPPORTED_SCHEMA_VERSIONS), [1, 2])
        # The doc promises a v1 store still works and is not rewritten; assert the read path.
        self.assertIn("still declaring version 1 is read exactly as", self.text)
        v1 = rp.from_document(
            {
                "schema_version": 1,
                "profiles": {"gem": {"runner": "oc", "model": GEM_MODEL}},
            }
        )
        self.assertEqual(v1.schema_version, 1)
        self.assertEqual(rp.resolve(v1, runner="oc", profile="gem").model, GEM_MODEL)

    def test_docs_check_passes_for_the_new_and_edited_docs(self):
        from agent_workflows import docs_check

        for rel in ("docs/runner-profiles.md", "docs/cli-human-guide.md", "README.md"):
            findings = docs_check.check_doc(REPO_ROOT / rel)
            self.assertEqual([str(f) for f in findings], [], rel)


if __name__ == "__main__":
    unittest.main()
