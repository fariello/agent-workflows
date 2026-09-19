"""Tests for sensitivity-tiered analytics export (runanalytics Order 09, ixis0c: E-02..E-05).

THE CENTRAL TESTS HERE ARE STRUCTURAL, NOT DETECTOR-DRIVEN, and that is the plan's root finding
turned into assertions. A canary is asserted absent because the field allowlist never NAMED its
field, which holds for a payload no pattern would have matched. The detector is then run over the
same data and its coverage RE-MEASURED at test time, so the "two of thirteen" figure in the shipped
report cannot silently go stale.

NO CANARY IS COMMITTED AS A LITERAL. The plan's gate forbids it, so every payload is assembled from
fragments at runtime, the same way the detection engine builds its own patterns.
"""

from __future__ import annotations

import getpass
import json
import os
import socket
import tarfile
import zipfile
from pathlib import Path

import pytest

from agent_workflows import run_analytics_export as export
from agent_workflows import run_analytics_privacy as privacy


# --- canary construction -------------------------------------------------------------------------


def _canary_payloads() -> dict[str, str]:
    """One representative payload per canary class, assembled from fragments."""

    home = os.path.expanduser("~")
    return {
        "prompt-text": "The user asked me to " + "drop the production database",
        "response-text": "I will now " + "exfiltrate the customer table",
        "shell-command": "psql -h " + "internal.db.example.corp -U admin -c 'select *'",
        "filesystem-path": home + "/VC/agent-workflows/secret_notes.py",
        "hostname": "observed on host " + socket.gethostname(),
        "username": "operator is " + getpass.getuser(),
        "git-remote": "git@" + "github.com:acme/private-" + "inventory.git",
        "branch-name": "feature/" + "acme-unreleased-pricing",
        "commit-message": "fix the " + "acquisition valuation spreadsheet",
        "environment-secret": "AWS_SECRET"
        + "_ACCESS_KEY="
        + "wJalrXUtnFEMI"
        + "K7MDENG",
        "high-entropy-token": "sk-" + "proj-" + ("b" * 44),
        "spreadsheet-formula": "=cmd|" + "'/C calc'!A0",
        "archive-traversal": "../../.." + "/etc/passwd",
    }


#: A run id of the shape Order 02's projector actually accepts (`_RUN_ID_RE`). Using a made-up id
#: here would make these tests pass or fail for a reason that has nothing to do with the export.
RUN_ID = "run-20260914T033154Z-457353"
RUN_ID_2 = "run-20260914T040000Z-111111"


def _code_lines(path: str) -> str:
    """Source with comments and docstring prose stripped, for a "does the CODE do X" assertion.

    Necessary rather than fastidious: this module's docstrings QUOTE the very API names the tests
    assert are unused (``filter="data"``, ``extractall``), because explaining why they are avoided
    requires naming them. Grepping raw source would match the explanation and report the opposite
    of the truth.
    """

    import io
    import tokenize

    text = Path(path).read_text(encoding="utf-8")
    out: list[str] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except tokenize.TokenError:  # pragma: no cover - defensive
        return text
    prev_type = None
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            continue
        # A STRING alone on a logical line is a docstring; keep other strings (real values).
        if tok.type == tokenize.STRING and prev_type in (
            None,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.NEWLINE,
            tokenize.NL,
        ):
            continue
        if tok.type not in (
            tokenize.NEWLINE,
            tokenize.NL,
            tokenize.INDENT,
            tokenize.DEDENT,
        ):
            out.append(tok.string)
        if tok.type not in (tokenize.NL,):
            prev_type = tok.type
    return " ".join(out)


class _Envelope:
    """A minimal stand-in exposing the CacheEnvelope attributes the export reads."""

    def __init__(
        self, run_id=RUN_ID, metric_facts=None, event_facts=None, source_root_id="root0"
    ):
        self.run_id = run_id
        self.metric_facts = dict(metric_facts or {})
        self.event_facts = [dict(e) for e in (event_facts or [])]
        self.source_root_id = source_root_id


# --- E-02: the metrics tier ----------------------------------------------------------------------


class MetricsTierTests:
    pass


def test_metrics_reemits_projected_facts_and_records_projector_version():
    env = _Envelope(metric_facts={"run_id": RUN_ID, "token_total": 12})
    payload = export.build_metrics_payload([env], tool_version="test")
    assert payload["tier"] == "metrics"
    assert payload["run_count"] == 1
    assert payload["runs"][0]["run_id"] == RUN_ID
    # The bundle records WHICH projector generation produced it.
    assert isinstance(payload["projector_version"], int)
    assert payload["projector_allowlist_size"] == len(privacy.ALLOWED_METRIC_KEYS)


def test_metrics_refuses_an_unknown_key_rather_than_dropping_it():
    # A key the write-side allowlist does not name must not ride into a bundle.
    env = _Envelope(metric_facts={"run_id": RUN_ID, "prompt_text": "secret"})
    payload = export.build_metrics_payload([env])
    assert payload["runs"] == []
    assert len(payload["refused_records"]) == 1
    assert "prompt_text" in payload["refused_records"][0]


def test_metrics_uses_order_02_allowlist_and_builds_no_second_projector():
    # The allowlist the export re-validates against IS Order 02's, not a copy.
    code = _code_lines("agent_workflows/run_analytics_export.py")
    assert "project_metric_facts" in code
    # No competing filter or detector definitions in the export module.
    assert "ALLOWED_METRIC_KEYS =" not in code
    assert "def project_facts" not in code
    # No second DETECTOR: the module may READ the shared detector's rule names for its blind-spot
    # report (that is the corroboration path), but it must define no pattern of its own.
    assert "_FAIL_PATTERNS =" not in code
    # Exactly ONE compiled pattern in the module, and it is the archive member-name check rather
    # than any content detection. (`_code_lines` joins tokens with spaces, hence "re . compile".)
    assert code.count("re . compile") == 1
    # The one allowlist this module DOES define narrows events for export; it is not a projector.
    assert "ALLOWED_EXPORT_EVENT_FIELDS" in code


def test_no_tier_claims_anonymity_or_safety():
    for tier in export.TIERS:
        assert export.tier_claims_safety(tier) is False
        notes = export.residual_risk_notes(tier)
        assert any("not anonymous" in n for n in notes)
    assert export.DEFAULT_TIER == "metrics"


def test_unknown_tier_is_refused():
    with pytest.raises(export.ExportRefusal):
        export.residual_risk_notes("totally-open")


# --- E-03: the redacted tier, structurally ------------------------------------------------------


def test_every_canary_class_is_excluded_structurally_not_by_detection():
    """The heart of the plan: absence by construction, for all thirteen classes."""

    canaries = _canary_payloads()
    # Seed an event carrying EVERY canary in fields the export allowlist does not name.
    hostile_event = {"event_type": "turn", "duration_seconds": 1.5}
    for index, (name, payload) in enumerate(sorted(canaries.items())):
        hostile_event[f"leak_field_{index}_{name.replace('-', '_')}"] = payload
    env = _Envelope("run-c", event_facts=[hostile_event])

    bundle = export.build_redacted_events([env])
    serialized = json.dumps(bundle)

    for name, payload in canaries.items():
        assert payload not in serialized, f"{name} survived into the redacted bundle"

    # And the reason is the allowlist, not a scan.
    assert bundle["redaction_method"] == "structural-field-allowlist"
    kept = bundle["runs"][0]["events"][0]
    assert set(kept) <= export.ALLOWED_EXPORT_EVENT_FIELDS
    assert kept["event_type"] == "turn"
    # The narrowing is visible rather than silent.
    assert bundle["dropped_field_occurrences"] == len(canaries)
    assert len(bundle["dropped_field_names"]) == len(canaries)


def test_export_event_allowlist_is_a_subset_of_the_cache_allowlist():
    # A field may be fine to cache locally and wrong to put in a shareable bundle.
    assert export.ALLOWED_EXPORT_EVENT_FIELDS <= privacy.ALLOWED_EVENT_KEYS


def test_detector_coverage_is_remeasured_and_matches_the_shipped_report():
    """RE-MEASURE the detector, so the shipped figure cannot go stale silently."""

    from agent_workflows import leak_sanitizer

    ruleset = leak_sanitizer.build_ruleset(Path("."))
    caught = set()
    for name, payload in _canary_payloads().items():
        if leak_sanitizer.scan_text(payload, "canary", ruleset):
            caught.add(name)

    # Every class the report claims is a blind spot must genuinely be uncaught.
    for name in export.DETECTOR_BLIND_SPOTS:
        assert name not in caught, (
            f"{name} is listed as a detector blind spot but the detector caught it; "
            "update DETECTOR_COVERED_CLASSES/DETECTOR_BLIND_SPOTS"
        )
    # And the detector must not be silently catching MORE than the report credits it with,
    # which would mean the shipped coverage figure understates it.
    assert caught == set(export.DETECTOR_COVERED_CLASSES), (
        f"measured coverage {sorted(caught)} != declared "
        f"{sorted(export.DETECTOR_COVERED_CLASSES)}"
    )
    # The measured figure is a small MINORITY of the classes: that is the finding.
    assert len(caught) < len(export.CANARY_CLASSES) / 2


def test_sanitizer_report_enumerates_blind_spots_by_name():
    """A report claiming a clean scan WITHOUT the enumeration is a failed validation."""

    report = export.sanitizer_blind_spot_report(["nothing interesting here"])
    assert report["finding_count"] == 0
    # Clean is not the claim. The blind spots must be named, individually.
    named = report["classes_this_detector_does_not_look_for"]
    for blind in export.DETECTOR_BLIND_SPOTS:
        assert blind in named
    assert "CORROBORATION ONLY" in report["detector_role"]
    assert "gitleaks" in report["no_secret_shape_detection"]
    assert set(report["maintainer_specific_rules"]) == {
        "handle",
        "private-repo",
        "other-account",
    }
    assert "match nothing" in report["maintainer_specific_caveat"]


def test_maintainer_specific_rules_do_not_transfer_to_another_machine():
    """F-2 re-measured: the gate is weakest exactly where the data is not the maintainer's."""

    from agent_workflows import leak_sanitizer

    ruleset = leak_sanitizer.build_ruleset(Path("."))
    other_handle = "contact " + "jsmith" + " about this"
    other_repo = "git@" + "github.com:othercorp/secret-" + "thing.git"
    assert leak_sanitizer.scan_text(other_handle, "c", ruleset) == []
    assert leak_sanitizer.scan_text(other_repo, "c", ruleset) == []
    # while a GENERIC rule does still match
    generic_home = "/home/" + "jsmith" + "/project/file.py"
    assert leak_sanitizer.scan_text(generic_home, "c", ruleset) != []


def test_redacted_bundle_states_residual_risk_and_no_anonymity():
    bundle = export.build_redacted_events([_Envelope("run-d")])
    assert bundle["claims_anonymity"] is False
    assert any("MINIMIZED, not anonymous" in n for n in bundle["residual_risk"])


# --- E-04: the raw tier --------------------------------------------------------------------------


def _seed_run(tmp_path: Path) -> Path:
    run = tmp_path / "runs" / "run-x"
    (run / "prompts").mkdir(parents=True)
    (run / "sessions").mkdir(parents=True)
    (run / "prompts" / "01.md").write_text("prompt one", encoding="utf-8")
    (run / "prompts" / "02.md").write_text("prompt two", encoding="utf-8")
    (run / "sessions" / "a.jsonl").write_text('{"x":1}\n', encoding="utf-8")
    (run / "outcome.json").write_text("{}", encoding="utf-8")
    return run


def test_raw_selection_defaults_to_nothing(tmp_path):
    """The default for a tier that may carry secrets is EMPTY, not everything."""

    run = _seed_run(tmp_path)
    assert export.select_raw_files([run]) == []
    assert export.select_raw_files([run], include=[]) == []


def test_raw_preview_summarizes_by_category_with_counts_and_bytes(tmp_path):
    run = _seed_run(tmp_path)
    files = export.select_raw_files([run], include=["prompts", "sessions"])
    assert len(files) == 3
    preview = export.preview_raw_selection(files, base=run)
    assert preview.file_count == 3
    assert preview.total_bytes > 0
    assert preview.categories["prompts"]["count"] == 2
    assert preview.categories["sessions"]["count"] == 1
    assert preview.categories["prompts"]["bytes"] > 0
    # And the preview WARNS, since this listing is the only review a human gets.
    assert any("RAW TIER" in w for w in preview.warnings)
    assert preview.to_dict()["claims_anonymity"] is False


def test_raw_bundle_manifest_is_deterministic_and_checksummed(tmp_path):
    run = _seed_run(tmp_path)
    files = export.select_raw_files([run], include=["prompts"])
    first = export.write_bundle(
        tmp_path / "b1", tier="raw", raw_files=files, raw_base=run
    )
    second = export.write_bundle(
        tmp_path / "b2", tier="raw", raw_files=files, raw_base=run
    )
    paths1 = [e.path for e in first.entries]
    paths2 = [e.path for e in second.entries]
    assert paths1 == paths2 == sorted(paths1)
    sums1 = {e.path: e.sha256 for e in first.entries}
    sums2 = {e.path: e.sha256 for e in second.entries}
    # Every file except the timestamped README is byte-identical across runs.
    for path in sums1:
        if path == "README.txt":
            continue
        assert sums1[path] == sums2[path]
    assert all(len(e.sha256) == 64 for e in first.entries)


def test_raw_bundle_carries_no_safety_label_and_names_its_danger(tmp_path):
    run = _seed_run(tmp_path)
    files = export.select_raw_files([run], include=["prompts"])
    bundle = export.write_bundle(
        tmp_path / "b", tier="raw", raw_files=files, raw_base=run
    )
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    assert manifest["claims_anonymity"] is False
    blob = bundle.manifest_path.read_text(encoding="utf-8") + (
        bundle.root / "README.txt"
    ).read_text(encoding="utf-8")
    lowered = blob.lower()
    # Assert the CLAIM is absent, not the word: the bundle must be free to say "NOT anonymous",
    # which is the whole point. A bare substring ban would forbid the honest disclaimer and permit
    # nothing useful in its place.
    for forbidden in (
        "is anonymous",
        "fully anonymous",
        "has been anonymized",
        "safe to share",
        "safe to submit",
        "no sensitive data",
        "contains no secrets",
    ):
        assert forbidden not in lowered, f"raw bundle claimed {forbidden!r}"
    # And the honest disclaimers ARE present.
    assert "not anonymous" in lowered
    assert "may include prompts" in blob
    assert (
        "Nothing here is redacted" in blob
        or "nothing in this tier has been redacted" in lowered
    )


# --- E-05: archives on a 3.9 floor ---------------------------------------------------------------


def test_tarfile_data_filter_is_feature_detected_not_assumed():
    """The 3.9 floor may lack PEP 706 filters; the code must not assume them."""

    assert isinstance(export.tarfile_data_filter_available(), bool)
    # Prose is stripped: this module's docstrings NAME the APIs it avoids in order to explain why.
    code = _code_lines("agent_workflows/run_analytics_export.py")
    assert 'filter="data"' not in code
    assert "extractall" not in code
    # The detection is a real runtime check, not an assumption.
    assert "hasattr" in code and "data_filter" in code


@pytest.mark.parametrize(
    "name,kwargs,expect",
    [
        ("/etc/passwd", {}, "absolute"),
        ("../../../etc/passwd", {}, "traversal"),
        ("a/../../b", {}, "traversal"),
        ("C:/windows/system32", {}, "absolute"),
        ("ok.txt", {"is_symlink": True}, "symlink"),
        ("ok.txt", {"is_hardlink": True}, "hardlink"),
        ("ok.txt", {"is_device": True}, "device"),
        ("dup.txt", {"seen": ["dup.txt"]}, "duplicate"),
        ("", {}, "empty"),
    ],
)
def test_hostile_archive_members_are_refused(name, kwargs, expect):
    reason = export.archive_member_refusal(name, **kwargs)
    assert reason is not None, f"{name!r} should have been refused"
    assert expect in reason


def test_benign_member_is_allowed():
    assert export.archive_member_refusal("dir/file.txt") is None


def test_hostile_tar_is_refused_before_any_write(tmp_path):
    archive = tmp_path / "hostile.tar"
    payload = tmp_path / "payload.txt"
    payload.write_text("x", encoding="utf-8")
    with tarfile.open(archive, "w") as tf:
        tf.add(payload, arcname="good.txt")
        tf.add(payload, arcname="../../escaped.txt")
    dest = tmp_path / "out"
    with pytest.raises(export.ExportRefusal) as caught:
        export.safe_extract(archive, dest)
    assert "traversal" in str(caught.value)
    # NOTHING was partially extracted.
    assert not dest.exists() or list(dest.rglob("*")) == []


def test_hostile_zip_is_refused_before_any_write(tmp_path):
    archive = tmp_path / "hostile.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("good.txt", "x")
        zf.writestr("../escaped.txt", "y")
    dest = tmp_path / "out"
    with pytest.raises(export.ExportRefusal):
        export.safe_extract(archive, dest)
    assert not dest.exists() or list(dest.rglob("*")) == []


def test_tar_symlink_member_is_refused(tmp_path):
    archive = tmp_path / "link.tar"
    with tarfile.open(archive, "w") as tf:
        info = tarfile.TarInfo("evil-link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tf.addfile(info)
    with pytest.raises(export.ExportRefusal) as caught:
        export.safe_extract(archive, tmp_path / "out")
    assert "symlink" in str(caught.value)


def test_benign_archive_extracts_identically_regardless_of_filter_support(tmp_path):
    """Behavior does not branch on `tarfile.data_filter`, so 3.9 and 3.14 agree."""

    archive = tmp_path / "ok.tar"
    payload = tmp_path / "p.txt"
    payload.write_text("hello", encoding="utf-8")
    with tarfile.open(archive, "w") as tf:
        tf.add(payload, arcname="nested/p.txt")

    dest = tmp_path / "out"
    names = export.safe_extract(archive, dest)
    assert names == ["nested/p.txt"]
    assert (dest / "nested" / "p.txt").read_text(encoding="utf-8") == "hello"

    # Exercise the fallback explicitly: with the attribute REMOVED, the result is identical.
    saved = getattr(tarfile, "data_filter", None)
    try:
        if saved is not None:
            del tarfile.data_filter
        assert export.tarfile_data_filter_available() is False
        dest2 = tmp_path / "out2"
        assert export.safe_extract(archive, dest2) == ["nested/p.txt"]
        assert (dest2 / "nested" / "p.txt").read_text(encoding="utf-8") == "hello"
    finally:
        if saved is not None:
            tarfile.data_filter = saved


def test_no_archive_precedent_existed_in_the_package():
    """Documents F-4's measurement: archive handling here is greenfield."""

    pkg = Path("agent_workflows")
    users = []
    for path in sorted(pkg.glob("*.py")):
        if "extractall" in _code_lines(str(path)):
            users.append(path.name)
    # Nothing in the package calls extractall, including this module: `safe_extract` validates
    # every member and then writes them by hand, which is what makes 3.9 and 3.14 behave alike.
    assert users == [], f"unexpected extractall users: {users}"


# --- E-01: the surface contract ------------------------------------------------------------------
#
# WHY THESE LIVE HERE AND NOT ONLY IN THE SLOW CONFORMANCE MATRIX. `tests/test_cli_conformance_matrix.py`
# is `pytestmark = pytest.mark.slow` and `addopts` supplies `-m "not slow"`, so the gate proving a
# leaf is declared and covered is DESELECTED by a bare `python3 -m pytest`. The plan's own stop
# condition names that trap ("if a bare suite is green and you are about to report the leaves
# conformant, STOP"). These tests assert the same properties in the FAST suite, so a regression is
# caught by the run everyone actually does, and the slow gate remains the authority.


def _decl(command: str):
    from agent_workflows.command_surface import get_declaration

    decl = get_declaration(command)
    assert decl is not None, f"{command} carries no CommandDeclaration"
    return decl


def test_both_new_leaves_are_declared_and_are_real_parser_leaves():
    from agent_workflows.cli import _build_parser
    from agent_workflows.command_surface import discover_parser_leaves

    leaves = discover_parser_leaves(_build_parser())
    for command in ("runs export", "runs submit"):
        assert command in leaves, f"{command} is not a parser leaf"
        _decl(command)


def test_no_new_undeclared_leaf_was_introduced():
    """The measured BASELINE is the five pre-existing `oc profile *` entries, and only those.

    `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves` asserts this set is
    EMPTY and currently FAILS on those five, which is a pre-existing condition this plan explicitly
    does not fix. Asserting the exact set here makes a NEW undeclared leaf attributable in the fast
    suite rather than hiding behind an already-red slow gate.
    """

    from agent_workflows.cli import _build_parser
    from agent_workflows.command_surface import find_undeclared_leaves

    assert sorted(find_undeclared_leaves(_build_parser())) == [
        "oc profile add",
        "oc profile default",
        "oc profile list",
        "oc profile remove",
        "oc profile show",
    ]


def test_each_new_leaf_declares_a_gate_matching_the_mechanism_it_implements():
    """The gate field is a machine-readable claim about authorization, so it must be TRUE.

    Both values are drawn from the shipped four-value vocabulary rather than invented:
    `dry_run_default` (22 other declarations) for the preview-first verb, and `auth_floor` (7 other
    declarations, all of them `--by-human`-gated transitions) for the attested one. `confirmation`
    is deliberately NOT used: it would assert a TTY prompt that implemented spec
    `20260815-0151-01` retired, which this plan's stop conditions forbid reintroducing.
    """

    from agent_workflows.command_surface import get_all_declarations

    vocabulary = {d.mutation_gate for d in get_all_declarations()}
    assert vocabulary <= {
        "none",
        "dry_run_default",
        "confirmation",
        "auth_floor",
        "policy",
    }

    export_decl = _decl("runs export")
    assert export_decl.command_class == "mutation"
    assert export_decl.mutation_gate == "dry_run_default"
    assert export_decl.exit_contract == (0, 1, 2)

    submit_decl = _decl("runs submit")
    assert submit_decl.command_class == "mutation"
    assert submit_decl.mutation_gate == "auth_floor"
    assert submit_decl.exit_contract == (0, 1, 2)


def test_each_new_leaf_is_a_mutation_so_it_owes_the_success_preview_scenario():
    """`command_class` DRIVES required coverage, so a wrong class demands the wrong scenarios."""

    from tests.conformance_matrix import required_scenarios

    for command in ("runs export", "runs submit"):
        scenarios = set(required_scenarios(_decl(command)))
        assert "success_preview" in scenarios, command
        for base in ("tty", "non_tty", "agent", "no_color", "help", "usage_error"):
            assert base in scenarios, f"{command} missing {base}"


def test_the_matrix_gives_both_new_leaves_a_full_scenario_row_set():
    """The same assertion the slow gate makes, over the two leaves this plan adds."""

    from agent_workflows.cli import _build_parser
    from tests.conformance_matrix import build_matrix, required_scenarios

    report = build_matrix(_build_parser())
    for command in ("runs export", "runs submit"):
        covered = report.scenarios_for(command)
        missing = set(required_scenarios(_decl(command))) - covered
        assert missing == set(), f"{command} missing scenarios: {sorted(missing)}"


def test_the_exit_contract_is_carryable_by_the_agent_record():
    """Every declared code must be one `validate_agent_record` accepts for a result record."""

    for command in ("runs export", "runs submit"):
        for code in _decl(command).exit_contract:
            assert code in (0, 1, 2), f"{command} declares un-carryable exit {code}"
