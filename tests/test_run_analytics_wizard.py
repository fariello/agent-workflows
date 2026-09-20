"""Tests for analytics setup choices, retention and deletion (Order 09, ixis0c: E-09).

THE CONFIG-LOCATION TEST IS WRITTEN TO FAIL AGAINST THE NAIVE CHOICE, which is the only way it
carries information. :func:`test_the_xdg_user_config_would_have_dropped_the_setting` demonstrates
``config.normalize()`` discarding an ``analytics_endpoint`` key, and the adjacent test shows the
same setting surviving a round trip through ``local.json``. A bare "settings round-trip" test would
pass against a location that silently loses them on the NEXT save.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_workflows import run_analytics_wizard as wizard


def _repo(tmp_path: Path) -> Path:
    (tmp_path / ".aw" / "config").mkdir(parents=True)
    return tmp_path


# --- the config location -------------------------------------------------------------------------


def test_the_xdg_user_config_would_have_dropped_the_setting():
    """MEASURED: the plan's authored location silently discards an unregistered key."""

    from agent_workflows import config

    # ASSERTS THE CLAIM, NOT A SNAPSHOT OF THE WHOLE ALLOWLIST (narrowed 2026-09-20, plan
    # `pow5sj`). This read `== {"aw_home", "config_version", "defaults", "repos"}`, which made every
    # legitimate new config key a failure of an ANALYTICS test: the exact set is incidental to what
    # this test demonstrates, which is that a key NOT on the allowlist is silently dropped by
    # `normalize()`. Pinning the whole set asserted "these four keys are the only keys this toolkit
    # will ever have", a claim this test never needed and which no analytics behavior depends on.
    # `color_depth` (spec `uonrjg` R9.3a.4) was the first legitimate addition to trip it.
    # The substantive claim is preserved and is now stated directly.
    assert "analytics_endpoint" not in config._ALLOWED_TOP_KEYS
    payload = config.default_config()
    payload["analytics_endpoint"] = {"url": "https://analytics.example.org/submit"}
    normalized = config.normalize(payload)
    # This is the bug the plan would have shipped: no error, no warning, setting gone.
    assert "analytics_endpoint" not in normalized


def test_settings_survive_a_round_trip_through_the_local_binding(tmp_path):
    repo = _repo(tmp_path)
    settings = wizard.AnalyticsSettings(
        analytics_enabled=True,
        endpoint_url="https://analytics.example.org/submit",
        auth_env_var="AW_ANALYTICS_TOKEN",
        retention_days=30,
    )
    path = wizard.write_settings(repo, settings)
    assert path == repo / ".aw" / "config" / "local.json"

    read_back = wizard.read_settings(repo)
    assert read_back.analytics_enabled is True
    assert read_back.endpoint_url == "https://analytics.example.org/submit"
    assert read_back.auth_env_var == "AW_ANALYTICS_TOKEN"
    assert read_back.retention_days == 30
    # And it survives a SECOND save, which is where the XDG config loses it.
    wizard.write_settings(repo, read_back)
    assert wizard.read_settings(repo).endpoint_url == settings.endpoint_url


def test_writing_settings_preserves_other_keys_in_the_local_binding(tmp_path):
    """`local.json` is shared: clobbering it would destroy a co-resident setting."""

    repo = _repo(tmp_path)
    local = repo / ".aw" / "config" / "local.json"
    local.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "project_id": "abc123",
                "run_analytics_telemetry": {"enabled": True},
            }
        ),
        encoding="utf-8",
    )
    wizard.write_settings(repo, wizard.AnalyticsSettings(analytics_enabled=True))
    payload = json.loads(local.read_text(encoding="utf-8"))
    assert payload["project_id"] == "abc123"
    assert payload["run_analytics_telemetry"] == {"enabled": True}
    assert payload[wizard.ANALYTICS_KEY]["analytics_enabled"] is True


def test_the_local_binding_schema_round_trips_the_unknown_key(tmp_path):
    """The mechanism that makes this location work, asserted rather than assumed."""

    from agent_workflows.project_schema import parse_local_binding

    repo = _repo(tmp_path)
    wizard.write_settings(
        repo, wizard.AnalyticsSettings(endpoint_url="https://a.example/s")
    )
    payload = json.loads(
        (repo / ".aw" / "config" / "local.json").read_text(encoding="utf-8")
    )
    parsed = parse_local_binding(payload)
    assert wizard.ANALYTICS_KEY in parsed.unknown_fields


def test_a_credential_value_is_refused_where_a_variable_name_belongs(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(wizard.WizardRefusal) as caught:
        wizard.write_settings(
            repo,
            wizard.AnalyticsSettings(auth_env_var="Bearer sk-" + "proj-" + "a" * 40),
        )
    assert "environment variable NAME" in str(caught.value)


def test_no_secret_is_ever_written_to_the_config(tmp_path):
    repo = _repo(tmp_path)
    wizard.write_settings(
        repo, wizard.AnalyticsSettings(auth_env_var="AW_ANALYTICS_TOKEN")
    )
    blob = (repo / ".aw" / "config" / "local.json").read_text(encoding="utf-8")
    # The NAME is stored; there is no field in which a value could live.
    assert "AW_ANALYTICS_TOKEN" in blob
    assert "auth_token" not in blob
    assert "secret" not in blob.lower()


# --- conservative defaults -----------------------------------------------------------------------


def test_every_default_is_off(tmp_path):
    settings = wizard.read_settings(_repo(tmp_path))
    assert settings.analytics_enabled is False
    assert settings.sampling_enabled is False
    assert settings.submission_enabled is False
    assert settings.cross_box_correlation_enabled is False
    assert settings.endpoint_url == ""
    assert settings.retention_days == 0
    assert settings.sources == ()


def test_cross_box_correlation_defaults_off_as_order_02_deferred(tmp_path):
    """Order 02's OQ-01 scoped correlation to one box and handed the wider opt-in here."""

    repo = _repo(tmp_path)
    settings = wizard.apply_choices(
        repo,
        {
            "analytics_enabled": True,
            "sampling_enabled": False,
            "submission_enabled": False,
        },
    )
    assert settings.cross_box_correlation_enabled is False
    # It takes an EXPLICIT opt-in to turn on.
    opted_in = wizard.apply_choices(
        repo,
        {
            "analytics_enabled": True,
            "sampling_enabled": False,
            "submission_enabled": False,
            "cross_box_correlation_enabled": True,
        },
    )
    assert opted_in.cross_box_correlation_enabled is True


def test_sampling_is_a_separate_question_from_analytics(tmp_path):
    repo = _repo(tmp_path)
    settings = wizard.apply_choices(
        repo,
        {
            "analytics_enabled": True,
            "sampling_enabled": False,
            "submission_enabled": False,
        },
    )
    assert settings.analytics_enabled is True
    assert settings.sampling_enabled is False


def test_endpoint_is_unavailable_unless_submission_is_explicitly_enabled(tmp_path):
    repo = _repo(tmp_path)
    settings = wizard.apply_choices(
        repo,
        {
            "analytics_enabled": True,
            "sampling_enabled": False,
            "submission_enabled": False,
            "endpoint_url": "https://analytics.example.org/submit",
        },
    )
    # A configured url does NOT make submission live.
    assert settings.endpoint()["url"] == ""
    # And the consumer therefore reports `unavailable` and transmits nothing, which is the
    # end-to-end property that matters rather than the empty string on its own.
    from agent_workflows import run_analytics_export as export
    from agent_workflows import run_analytics_submit as submit

    bundle = export.write_bundle(
        tmp_path / "bundle", tier="metrics", payload=export.build_metrics_payload([])
    )
    result = submit.submit_bundle(
        bundle.root, endpoint=settings.endpoint(), tier="metrics"
    )
    assert result["status"] == submit.STATUS_UNAVAILABLE
    assert result["transmitted"] is False


def test_enabling_submission_without_a_url_is_refused(tmp_path):
    with pytest.raises(wizard.WizardRefusal) as caught:
        wizard.apply_choices(
            _repo(tmp_path),
            {
                "analytics_enabled": True,
                "sampling_enabled": False,
                "submission_enabled": True,
            },
        )
    assert "requires an endpoint_url" in str(caught.value)


# --- unattended fails closed ---------------------------------------------------------------------


def test_unattended_with_incomplete_choices_fails_closed(tmp_path):
    with pytest.raises(wizard.WizardRefusal) as caught:
        wizard.apply_choices(
            _repo(tmp_path), {"analytics_enabled": True}, unattended=True
        )
    message = str(caught.value)
    assert "refuses to infer" in message
    assert "sampling_enabled" in message
    assert "submission_enabled" in message


def test_unattended_with_yes_alone_still_fails_closed(tmp_path):
    """`--yes` preauthorizes expected mutations; it does not answer a privacy question."""

    with pytest.raises(wizard.WizardRefusal) as caught:
        wizard.apply_choices(
            _repo(tmp_path), {"analytics_enabled": True}, unattended=True, yes=True
        )
    assert "--yes does not answer these" in str(caught.value)


def test_unattended_is_local_and_no_submit(tmp_path):
    repo = _repo(tmp_path)
    settings = wizard.apply_choices(
        repo,
        {
            "analytics_enabled": True,
            "sampling_enabled": False,
            "submission_enabled": False,
        },
        unattended=True,
    )
    assert settings.submission_enabled is False
    # And an unattended run may not turn transmission on at all.
    with pytest.raises(wizard.WizardRefusal) as caught:
        wizard.apply_choices(
            repo,
            {
                "analytics_enabled": True,
                "sampling_enabled": False,
                "submission_enabled": True,
                "endpoint_url": "https://analytics.example.org/submit",
            },
            unattended=True,
        )
    assert "refuses to enable submission" in str(caught.value)


def test_negative_retention_is_refused(tmp_path):
    with pytest.raises(wizard.WizardRefusal):
        wizard.apply_choices(
            _repo(tmp_path),
            {
                "analytics_enabled": True,
                "sampling_enabled": False,
                "submission_enabled": False,
                "retention_days": -1,
            },
        )


def test_no_optional_install_mechanism_is_built():
    """F-8: the modules ship in-package; the wizard gates ENABLEMENT, not code presence."""

    from tests.test_run_analytics_export import _code_lines

    code = _code_lines("agent_workflows/run_analytics_wizard.py")
    for forbidden in (
        "pip",
        "subprocess",
        "install",
        "extras_require",
        "importlib.util.find_spec",
    ):
        assert forbidden not in code, f"wizard reaches for {forbidden!r}"
    # What it DOES gate is a boolean.
    assert "analytics_enabled" in code


# --- precise deletion ----------------------------------------------------------------------------


def test_deletion_plans_only_tool_owned_analytics_children(tmp_path):
    from agent_workflows import runner_shared

    repo = _repo(tmp_path)
    analytics = runner_shared.analytics_root(repo)
    analytics.mkdir(parents=True, exist_ok=True)
    owned = analytics / "cache" / "entry.json"
    owned.parent.mkdir(parents=True, exist_ok=True)
    owned.write_text("{}", encoding="utf-8")

    plan = wizard.plan_deletion(repo)
    assert str(owned) in plan["removable"]
    assert plan["refused"] == []
    assert plan["source_runs_touched"] is False


def test_deletion_refuses_a_target_outside_the_analytics_namespace(tmp_path):
    from agent_workflows import runner_shared

    repo = _repo(tmp_path)
    runner_shared.analytics_root(repo).mkdir(parents=True, exist_ok=True)
    source_run = repo / ".aw" / "records" / "runs" / "run-x"
    source_run.mkdir(parents=True, exist_ok=True)
    precious = source_run / "prompt.md"
    precious.write_text("original prompt", encoding="utf-8")

    with pytest.raises(wizard.WizardRefusal) as caught:
        wizard.delete_analytics_artifacts(repo, targets=[precious], dry_run=False)
    assert "outside the reserved analytics namespace" in str(caught.value)
    # THE SOURCE RUN IS UNTOUCHED.
    assert precious.read_text(encoding="utf-8") == "original prompt"


def test_deletion_refuses_the_whole_batch_rather_than_half_deleting(tmp_path):
    from agent_workflows import runner_shared

    repo = _repo(tmp_path)
    analytics = runner_shared.analytics_root(repo)
    analytics.mkdir(parents=True, exist_ok=True)
    owned = analytics / "a.json"
    owned.write_text("{}", encoding="utf-8")
    outside = repo / ".aw" / "records" / "runs" / "run-y" / "p.md"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("keep me", encoding="utf-8")

    with pytest.raises(wizard.WizardRefusal):
        wizard.delete_analytics_artifacts(repo, targets=[owned, outside], dry_run=False)
    # Neither was removed: a refusal aborts the batch.
    assert owned.exists()
    assert outside.exists()


def test_deletion_is_dry_run_by_default(tmp_path):
    from agent_workflows import runner_shared

    repo = _repo(tmp_path)
    analytics = runner_shared.analytics_root(repo)
    analytics.mkdir(parents=True, exist_ok=True)
    owned = analytics / "a.json"
    owned.write_text("{}", encoding="utf-8")

    result = wizard.delete_analytics_artifacts(repo, targets=[owned])
    assert result["dry_run"] is True
    assert result["deleted"] == []
    assert owned.exists()

    result = wizard.delete_analytics_artifacts(repo, targets=[owned], dry_run=False)
    assert result["dry_run"] is False
    assert str(owned) in result["deleted"]
    assert not owned.exists()


def test_deletion_never_composes_the_runs_literal_itself():
    """Order 01 owns the resolver; a second copy is a second thing to get wrong."""

    from tests.test_run_analytics_export import _code_lines

    code = _code_lines("agent_workflows/run_analytics_wizard.py")
    assert ".aw/records/runs" not in code
    assert "path_is_within_analytics" in code
    assert "analytics_root" in code
