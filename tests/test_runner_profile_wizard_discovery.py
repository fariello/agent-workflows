"""Behavioral tests for runner_profile_wizard discovery-failure reporting and manual-entry flows.

Guarantees:
1. Failed model discovery is reported with its named reason and falls through to exact manual entry.
2. Manual entry is reachable, schema-validated, and bounded.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from agent_workflows import oc_models, runner_profile_wizard, runner_profiles
from tests import support


class _Script:
    """A scripted TTY: ask pops answers, emit records output lines and ordered events."""

    def __init__(self, answers: Sequence[str], interrupt_at: Optional[int] = None):
        self.answers = list(answers)
        self.prompts: List[str] = []
        self.lines: List[str] = []
        self.events: List[Tuple[str, str]] = []
        self.interrupt_at = interrupt_at
        self._asked = 0

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        self.events.append(("ask", prompt))
        self._asked += 1
        if self.interrupt_at is not None and self._asked == self.interrupt_at:
            raise KeyboardInterrupt
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def emit(self, line: str) -> None:
        self.lines.append(line)
        self.events.append(("emit", line))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class _Store:
    """An injected store that counts writes."""

    def __init__(
        self,
        cfg: Optional[runner_profiles.ProfileConfig] = None,
        error: Optional[Exception] = None,
    ):
        self.cfg = cfg if cfg is not None else runner_profiles.empty_config()
        self.error = error
        self.writes: List[runner_profiles.ProfileConfig] = []

    def load(self) -> runner_profiles.ProfileConfig:
        return self.cfg

    def save(self, cfg: runner_profiles.ProfileConfig) -> Path:
        if self.error is not None:
            raise self.error
        self.writes.append(cfg)
        self.cfg = cfg
        return Path("/injected/runner-profiles.json")


def _io(
    script: _Script,
    catalog: Optional[oc_models.ModelCatalog] = None,
    store: Optional[_Store] = None,
    with_writer: bool = True,
) -> runner_profile_wizard.WizardIO:
    store = store if store is not None else _Store()
    cat = (
        catalog
        if catalog is not None
        else oc_models.ModelCatalog(
            models=("example-vendor/model-1",),
            source=oc_models.CATALOG_SOURCE_CLI,
        )
    )
    return runner_profile_wizard.WizardIO(
        ask=script.ask,
        emit=script.emit,
        discover=lambda: cat,
        load=store.load,
        save=store.save if with_writer else None,
    )


class RunnerProfileWizardDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_every_failure_reason_is_named_on_screen(self) -> None:
        reasons = (
            oc_models.CATALOG_MISSING_BINARY,
            oc_models.CATALOG_TIMED_OUT,
            oc_models.CATALOG_NONZERO_EXIT,
            oc_models.CATALOG_UNPARSEABLE,
            oc_models.CATALOG_NO_MODELS,
        )
        for i, reason in enumerate(reasons):
            with self.subTest(reason=reason):
                detail = f"detail-{i}"
                catalog = oc_models.ModelCatalog(
                    source=oc_models.CATALOG_SOURCE_NONE,
                    reason=reason,
                    detail=detail,
                )
                script = _Script([])
                io = _io(script, catalog)
                runner_profile_wizard._report_catalog(io, catalog)
                self.assertIn(reason, script.text)
                self.assertIn(detail, script.text)
                self.assertIn("exact provider/model", script.text)
                self.assertNotIn("Found ", script.text)

    def test_config_fallback_still_names_the_cli_failure(self) -> None:
        catalog = oc_models.ModelCatalog(
            models=("example-vendor/model-1", "example-vendor/model-2"),
            source=oc_models.CATALOG_SOURCE_CONFIG,
            reason=oc_models.CATALOG_TIMED_OUT,
            detail="timed out after 20s",
        )
        script = _Script([])
        io = _io(script, catalog)
        runner_profile_wizard._report_catalog(io, catalog)
        self.assertIn(oc_models.CATALOG_TIMED_OUT, script.text)
        self.assertIn("2", script.text)

    def test_dead_catalog_falls_through_to_manual_entry_and_saves(self) -> None:
        catalog = oc_models.ModelCatalog(
            source=oc_models.CATALOG_SOURCE_NONE,
            reason=oc_models.CATALOG_MISSING_BINARY,
            detail="not found in PATH",
        )
        script = _Script(["gem", "example/private-model", "", "", "", "", ""])
        store = _Store()
        io = _io(script, catalog, store)

        result = runner_profile_wizard.run_wizard(io)

        self.assertEqual(len(script.answers), 0)
        self.assertTrue(result.saved)
        self.assertIsNotNone(result.profile)
        assert result.profile is not None
        self.assertEqual(result.profile.model, "example/private-model")
        self.assertEqual(len(store.writes), 1)
        self.assertIn(catalog.reason, script.text)

        manual_idx = next(
            i
            for i, (kind, val) in enumerate(script.events)
            if kind == "ask" and "Exact provider/model" in val
        )
        for kind, val in script.events[:manual_idx]:
            if kind == "emit":
                self.assertNotIn("  [1] ", val)

        self.assertTrue(
            any(
                kind == "emit" and "  [1] " in val
                for kind, val in script.events[manual_idx:]
            )
        )


class ManualEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_m_reaches_manual_entry_from_a_live_catalog(self) -> None:
        catalog = oc_models.ModelCatalog(
            models=("example-vendor/model-1",),
            source=oc_models.CATALOG_SOURCE_CLI,
        )
        script = _Script(["m", "example/unlisted"])
        io = _io(script, catalog)
        selected = runner_profile_wizard.select_model(io, catalog)
        self.assertEqual(selected, "example/unlisted")

    def test_invalid_ids_are_refused_then_a_valid_one_accepted(self) -> None:
        catalog = oc_models.ModelCatalog(
            source=oc_models.CATALOG_SOURCE_NONE,
            reason=oc_models.CATALOG_MISSING_BINARY,
        )
        script = _Script(["", "not a model", "example/ok"])
        io = _io(script, catalog)
        selected = runner_profile_wizard.select_model(io, catalog)
        self.assertEqual(selected, "example/ok")
        self.assertIn("A model identifier is required", script.text)
        self.assertIn("invalid model 'not a model'", script.text)

    def test_manual_entry_is_bounded(self) -> None:
        catalog = oc_models.ModelCatalog(
            source=oc_models.CATALOG_SOURCE_NONE,
            reason=oc_models.CATALOG_NO_MODELS,
        )
        script = _Script(["bad"] * (runner_profile_wizard.MAX_ATTEMPTS + 2))
        io = _io(script, catalog)
        with self.assertRaises(runner_profile_wizard.WizardCancelled):
            runner_profile_wizard.select_model(io, catalog)
        self.assertEqual(len(script.prompts), runner_profile_wizard.MAX_ATTEMPTS)

    def test_exhausted_manual_entry_writes_nothing(self) -> None:
        catalog = oc_models.ModelCatalog(
            source=oc_models.CATALOG_SOURCE_NONE,
            reason=oc_models.CATALOG_NO_MODELS,
        )
        script = _Script(["gem"] + ["bad"] * runner_profile_wizard.MAX_ATTEMPTS)
        store = _Store()
        io = _io(script, catalog, store)
        result = runner_profile_wizard.run_wizard(io)
        self.assertFalse(result.saved)
        self.assertTrue(result.cancelled)
        self.assertEqual(result.reason, "cancelled")
        self.assertEqual(len(store.writes), 0)


if __name__ == "__main__":
    unittest.main()
