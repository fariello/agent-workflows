"""Tests for sensitivity-tiered analytics export (runanalytics Order 09, ixis0c: E-02..E-05).

THE CENTRAL TESTS HERE ARE STRUCTURAL, NOT DETECTOR-DRIVEN, and that is the plan's root finding
turned into assertions. A canary is asserted absent because the field allowlist never NAMED its
field, which holds for a payload no pattern would have matched. The detector is then run over the
same data and its coverage RE-MEASURED at test time, so the "two of thirteen" figure in the shipped
report cannot silently go stale.

NO CANARY IS COMMITTED AS A LITERAL. The plan's gate forbids it, so every payload is assembled from
fragments at runtime, the same way the detection engine builds its own patterns.

Restored for backlog liybkg from findings b1mx2w and source revision 19313eed^; source-reading and
CLI-surface tests were deliberately not restored.
"""

from __future__ import annotations

import json
import os
import socket
import tarfile
import zipfile
from pathlib import Path

import pytest

from agent_workflows import leak_sanitizer
from agent_workflows import run_analytics_export as export
from agent_workflows import run_analytics_privacy as privacy

pytestmark = pytest.mark.core


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
        "username": "operator is " + leak_sanitizer._H,
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
    for path, sha1 in sums1.items():
        if path == "README.txt":
            continue
        assert sha1 == sums2[path]
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


# --- residual branch coverage (E-02) -------------------------------------------------------------


def test_residual_tier_is_sensitive():
    assert export.tier_is_sensitive("raw") is True
    assert export.tier_is_sensitive("metrics") is False
    assert export.tier_is_sensitive("events-redacted") is False
    with pytest.raises(export.ExportRefusal):
        export.tier_is_sensitive("bogus")


def test_residual_build_redacted_events_non_mapping_and_cap():
    env = _Envelope()
    env.event_facts = [
        "not a mapping",
        {"activity": 1, "prompt_text": "x"},
        {"activity": 2},
        {"activity": 3},
    ]
    res = export.build_redacted_events([env], max_events_per_run=2)
    assert res["runs"][0]["event_count"] == 2
    assert res["runs"][0]["events"] == [{"activity": 1}, {"activity": 2}]
    assert res["dropped_field_names"] == ["prompt_text"]
    assert res["dropped_field_occurrences"] == 1


def test_residual_sanitizer_blind_spot_report_with_finding():
    sample = "see /home/" + "someone" + "/x.py"
    report = export.sanitizer_blind_spot_report([sample])
    assert report["finding_count"] >= 1
    assert any(
        f.get("location") == "sample[0]:1"
        and f.get("rule") == "home-path"
        and f.get("severity") == "fail"
        for f in report["findings"]
    )


def test_residual_write_bundle_metrics_payload_and_sanitizer(tmp_path):
    dest = tmp_path / "m"
    bundle = export.write_bundle(
        dest,
        tier="metrics",
        payload={"a": 1},
        sanitizer_report={"k": "v"},
    )
    assert (dest / "payload.json").is_file()
    assert (dest / "sanitizer-report.json").is_file()
    paths = {e.path for e in bundle.entries}
    assert "payload.json" in paths
    assert "sanitizer-report.json" in paths
    assert "README.txt" in paths
    bundle_dict = bundle.to_dict()
    assert set(bundle_dict.keys()) == {
        "entries",
        "file_count",
        "manifest_path",
        "root",
        "tier",
    }
    assert bundle_dict["file_count"] == len(bundle.entries)


def test_residual_select_and_preview_raw_files(tmp_path):
    run = tmp_path / "run"
    (run / "sub").mkdir(parents=True)
    sub_file = run / "sub" / "file.txt"
    sub_file.write_text("content", encoding="utf-8")
    missing = tmp_path / "missing"
    files = export.select_raw_files([missing, run], include=["sub"])
    assert files == [sub_file]
    preview = export.preview_raw_selection([tmp_path / "nope.txt"])
    assert preview.total_bytes == 0
    assert preview.categories == {"other": {"count": 1, "bytes": 0}}


def test_residual_build_manifest(tmp_path):
    d = tmp_path / "d"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text("{}", encoding="utf-8")
    (d / "k.txt").write_text("hi", encoding="utf-8")
    entries = export.build_manifest(d)
    assert len(entries) == 1
    assert entries[0].to_dict() == {
        "path": "k.txt",
        "size_bytes": 2,
        "sha256": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
    }


def test_residual_safe_extract(tmp_path):
    zpath = tmp_path / "test.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("dir/", "")
        zf.writestr("dir/f.txt", "hey")
    dest_zip = tmp_path / "out_zip"
    assert export.safe_extract(zpath, dest_zip) == ["dir/f.txt"]
    assert (dest_zip / "dir" / "f.txt").read_text(encoding="utf-8") == "hey"

    tpath = tmp_path / "test.tar"
    with tarfile.open(tpath, "w") as tf:
        d_info = tarfile.TarInfo("dd")
        d_info.type = tarfile.DIRTYPE
        tf.addfile(d_info)
        f_payload = tmp_path / "g.txt"
        f_payload.write_text("hey", encoding="utf-8")
        tf.add(f_payload, arcname="dd/g.txt")
    dest_tar = tmp_path / "out_tar"
    assert export.safe_extract(tpath, dest_tar) == ["dd/g.txt"]
    assert (dest_tar / "dd" / "g.txt").read_text(encoding="utf-8") == "hey"
