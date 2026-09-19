"""Tests for analytics submission transport and consent (Order 09, ixis0c: E-06..E-08).

THE TRANSPORT TESTS ARE WRITTEN TO FAIL AGAINST A NAIVE IMPLEMENTATION, which is the only way they
mean anything. :func:`test_a_bare_urlopen_would_have_leaked_a_local_file` demonstrates the
vulnerability directly, by showing the stdlib default opener returning the contents of a local file
and the payload of a ``data:`` url; the adjacent tests then show the restricted opener refusing both.
Without that pair, a passing "file:// is refused" test would be indistinguishable from a test whose
url simply happened not to resolve.

NO TEST REACHES THE NETWORK. The restricted-opener tests are refused at policy time, before any
socket, and the success path uses a stub opener. The no-network guarantee is asserted with the
EXISTING harness (``lifecycle_fixtures.run_no_network``) rather than a hand-rolled mock.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from agent_workflows import run_analytics_export as export
from agent_workflows import run_analytics_submit as submit


ENDPOINT = "https://analytics.example.org/submit"


# --- E-06: the transport is not the stdlib default ----------------------------------------------


def test_a_bare_urlopen_would_have_leaked_a_local_file():
    """THE VULNERABILITY, demonstrated, so the refusal tests below are not vacuous."""

    handlers = {type(h).__name__ for h in urllib.request.build_opener().handlers}
    # The default chain is the problem: each of these is an exfiltration or SSRF vector.
    assert "FileHandler" in handlers
    assert "DataHandler" in handlers
    assert "FTPHandler" in handlers
    assert "HTTPRedirectHandler" in handlers

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write("LOCAL-FILE-CONTENT-THAT-MUST-NOT-TRAVEL")
        path = fh.name
    try:
        # A bare urlopen RESOLVES a local file. This is what a naive submit would have shipped.
        leaked = urllib.request.urlopen("file://" + path).read().decode()
        assert "LOCAL-FILE-CONTENT-THAT-MUST-NOT-TRAVEL" in leaked
        assert urllib.request.urlopen("data:text/plain,hello").read() == b"hello"
    finally:
        os.unlink(path)


def test_restricted_opener_carries_no_file_data_or_ftp_handler():
    opener = submit.build_restricted_opener()
    names = {type(h).__name__ for h in opener.handlers}
    assert "HTTPSHandler" in names
    assert names.isdisjoint({"FileHandler", "DataHandler", "FTPHandler", "HTTPHandler"})
    # The redirect handler present is the REFUSING one, not the stdlib's permissive default.
    assert "RefusingRedirectHandler" in names
    # It is refused by protocol registration too, not merely by the entry-point policy check.
    assert set(opener.handle_open) == {"https"}


@pytest.mark.parametrize(
    "url,fragment",
    [
        ("file:///etc/passwd", "file"),
        ("data:text/plain,hello", "data"),
        ("ftp://example.org/x", "ftp"),
        ("http://example.org/x", "https"),
        ("gopher://example.org/x", "gopher"),
        ("", "empty"),
    ],
)
def test_policy_refuses_every_non_https_target_with_an_actionable_message(
    url, fragment
):
    reason = submit.url_policy_refusal(url)
    assert reason is not None
    assert fragment in reason


def test_open_url_refuses_a_file_target_with_an_actionable_message():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write("secret")
        path = fh.name
    try:
        with pytest.raises(submit.SubmitRefusal) as caught:
            submit.open_url("file://" + path)
        assert caught.value.code == "url-refused"
        # Actionable, not a bare AttributeError.
        assert "never permitted" in caught.value.summary
        assert "https" in caught.value.remedy
    finally:
        os.unlink(path)


def test_open_url_refuses_a_data_target():
    with pytest.raises(submit.SubmitRefusal) as caught:
        submit.open_url("data:text/plain,hello")
    assert caught.value.code == "url-refused"


def test_scheme_unhandled_refusal_wraps_the_bare_attributeerror():
    """MEASURED: a restricted opener asked for an unclaimed scheme raises a bare AttributeError.

    The refusal is correct but the message is useless, so it must be wrapped. This test drives the
    wrapper directly by handing `open_url` an opener whose policy check has been satisfied but whose
    handler chain cannot serve the scheme.
    """

    class _NoHandlerOpener:
        def open(self, request, timeout=None):
            raise AttributeError("'NoneType' object has no attribute 'read'")

    with pytest.raises(submit.SubmitRefusal) as caught:
        submit.open_url(ENDPOINT, opener=_NoHandlerOpener())
    assert caught.value.code == "scheme-unhandled"
    assert "no permitted handler" in caught.value.summary


@pytest.mark.parametrize(
    "target", ["file:///etc/passwd", "data:text/plain,x", "ftp://h/x"]
)
def test_a_redirect_to_a_forbidden_target_is_refused(target):
    """A 302 must not be able to smuggle in the scheme the entry check just rejected."""

    handler = submit.RefusingRedirectHandler()
    with pytest.raises(submit.SubmitRefusal) as caught:
        handler.redirect_request(
            urllib.request.Request(ENDPOINT), io.BytesIO(b""), 302, "Found", {}, target
        )
    assert caught.value.code == "redirect-refused"
    assert "may not go" in caught.value.remedy


def test_a_redirect_to_a_permitted_https_target_is_allowed():
    handler = submit.RefusingRedirectHandler()
    result = handler.redirect_request(
        urllib.request.Request(ENDPOINT),
        io.BytesIO(b""),
        302,
        "Found",
        {},
        "https://analytics.example.org/v2/submit",
    )
    assert result is not None


def test_no_retry_queue_or_daemon_exists_anywhere_in_the_module():
    """An automatic retry would transmit on an occasion the user never consented to."""

    text = Path("agent_workflows/run_analytics_submit.py").read_text(encoding="utf-8")
    lowered = text.lower()
    for forbidden in (
        "while true",
        "retry_count",
        "max_retries",
        "time.sleep",
        "threading",
        "daemon=",
        "schedule",
    ):
        assert forbidden not in lowered, f"submit module contains {forbidden!r}"
    # And the receipt records the absence as a fact a reader can check.
    receipt = submit.build_receipt(
        tier="metrics", destination=ENDPOINT, status="refused", total_bytes=0
    )
    assert receipt["retried"] is False
    assert receipt["queued"] is False


# --- E-07: validation, receipts, and the unavailable path ---------------------------------------


def _bundle(tmp_path: Path, tier: str = "metrics") -> Path:
    payload = export.build_metrics_payload([])
    bundle = export.write_bundle(tmp_path / f"b-{tier}", tier=tier, payload=payload)
    return bundle.root


def test_submission_is_unavailable_when_no_endpoint_is_configured(tmp_path):
    """THE EXPECTED RESULT TODAY: no endpoint governance exists in this repository."""

    result = submit.submit_bundle(_bundle(tmp_path), endpoint=None, tier="metrics")
    assert result["status"] == submit.STATUS_UNAVAILABLE
    assert result["code"] == "endpoint-unavailable"
    assert result["transmitted"] is False
    assert result["exit_code"] == submit.EXIT_REFUSED
    # Actionable rather than a bare failure.
    assert "export locally" in result["remedy"].lower()
    assert "retention" in result["remedy"].lower()
    assert "Nothing was transmitted" in result["receipt"]["detail"]


def test_validation_accepts_a_wellformed_bundle(tmp_path):
    facts = submit.validate_bundle(_bundle(tmp_path), tier="metrics")
    assert facts["tier"] == "metrics"
    assert facts["total_bytes"] > 0


@pytest.mark.parametrize(
    "mutate,code",
    [
        ("remove-manifest", "manifest-missing"),
        ("corrupt-manifest", "manifest-unreadable"),
        ("bad-version", "schema-unknown"),
        ("tamper-file", "checksum-mismatch"),
        ("delete-file", "file-missing"),
        ("hostile-path", "manifest-hostile-path"),
    ],
)
def test_each_validation_failure_class_has_a_code_and_a_remedy(tmp_path, mutate, code):
    root = _bundle(tmp_path)
    manifest_path = root / "manifest.json"
    if mutate == "remove-manifest":
        manifest_path.unlink()
    elif mutate == "corrupt-manifest":
        manifest_path.write_text("{not json", encoding="utf-8")
    elif mutate == "bad-version":
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["schema_version"] = 999
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
    elif mutate == "tamper-file":
        (root / "payload.json").write_text('{"tampered": true}', encoding="utf-8")
    elif mutate == "delete-file":
        (root / "payload.json").unlink()
    elif mutate == "hostile-path":
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["files"] = [
            {"path": "../../escape.json", "sha256": "0" * 64, "size_bytes": 1}
        ]
        manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(submit.SubmitRefusal) as caught:
        submit.validate_bundle(root, tier="metrics")
    assert caught.value.code == code
    # Every refusal is reportable: a summary always, and a remedy wherever one exists.
    assert caught.value.summary


def test_raw_tier_cannot_be_submitted(tmp_path):
    """The dangerous combination is unreachable, not merely discouraged."""

    assert "raw" not in submit.SUBMITTABLE_TIERS
    root = _bundle(tmp_path, tier="raw")
    with pytest.raises(submit.SubmitRefusal) as caught:
        submit.validate_bundle(root)
    assert caught.value.code == "tier-not-submittable"
    assert "stays local" in caught.value.remedy


def test_oversized_bundle_is_refused(tmp_path, monkeypatch):
    root = _bundle(tmp_path)
    monkeypatch.setattr(submit, "MAX_BUNDLE_BYTES", 1)
    with pytest.raises(submit.SubmitRefusal) as caught:
        submit.validate_bundle(root, tier="metrics")
    assert caught.value.code == "too-large"


def test_tier_mismatch_is_refused(tmp_path):
    with pytest.raises(submit.SubmitRefusal) as caught:
        submit.validate_bundle(_bundle(tmp_path), tier="events-redacted")
    assert caught.value.code == "tier-mismatch"


def test_missing_auth_is_refused_and_names_the_env_var(tmp_path, monkeypatch):
    monkeypatch.delenv("AW_TEST_ANALYTICS_TOKEN", raising=False)
    result = submit.submit_bundle(
        _bundle(tmp_path),
        endpoint={"url": ENDPOINT, "auth_env_var": "AW_TEST_ANALYTICS_TOKEN"},
        tier="metrics",
        attestation=submit.Attestation(
            tier="metrics", destination=ENDPOINT, by_human=True, actor="tester"
        ),
    )
    assert result["code"] == "auth-missing"
    assert "AW_TEST_ANALYTICS_TOKEN" in result["summary"]
    assert result["transmitted"] is False


def test_receipt_never_records_the_secret(tmp_path, monkeypatch):
    secret = "tok-" + ("z" * 32)
    monkeypatch.setenv("AW_TEST_ANALYTICS_TOKEN", secret)
    sent_headers = {}

    class _StubOpener:
        def open(self, request, timeout=None):
            sent_headers.update(request.headers)

            class _R:
                def read(self_inner):
                    return b'{"ok":true}'

                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *a):
                    return False

            return _R()

    result = submit.submit_bundle(
        _bundle(tmp_path),
        endpoint={"url": ENDPOINT, "auth_env_var": "AW_TEST_ANALYTICS_TOKEN"},
        tier="metrics",
        attestation=submit.Attestation(
            tier="metrics", destination=ENDPOINT, by_human=True, actor="tester"
        ),
        opener=_StubOpener(),
    )
    assert result["status"] == submit.STATUS_SUBMITTED
    # The token DID travel in a header...
    assert any(secret in str(v) for v in sent_headers.values())
    # ...and appears NOWHERE in the receipt, nor in any rendered output.
    blob = json.dumps(result)
    assert secret not in blob
    assert result["receipt"]["auth_source_env_var"] == "AW_TEST_ANALYTICS_TOKEN"
    assert result["receipt"]["auth_value_recorded"] is False
    # The destination is reduced to scheme+host, since a url can carry a token in its query.
    assert result["receipt"]["destination"] == "https://analytics.example.org"


def test_server_rejection_does_not_retry(tmp_path):
    calls = []

    class _RejectingOpener:
        def open(self, request, timeout=None):
            calls.append(request.full_url)
            raise urllib.error.HTTPError(ENDPOINT, 503, "busy", {}, None)

    result = submit.submit_bundle(
        _bundle(tmp_path),
        endpoint={"url": ENDPOINT},
        tier="metrics",
        attestation=submit.Attestation(
            tier="metrics", destination=ENDPOINT, by_human=True, actor="tester"
        ),
        opener=_RejectingOpener(),
    )
    assert result["code"] == "server-rejected"
    assert result["transmitted"] is False
    assert len(calls) == 1, "the submission was retried"
    assert result["receipt"]["retried"] is False


def test_timeout_and_cancellation_do_not_retry(tmp_path):
    calls = []

    class _TimingOutOpener:
        def open(self, request, timeout=None):
            calls.append(1)
            raise TimeoutError("timed out")

    result = submit.submit_bundle(
        _bundle(tmp_path),
        endpoint={"url": ENDPOINT},
        tier="metrics",
        attestation=submit.Attestation(
            tier="metrics", destination=ENDPOINT, by_human=True, actor="tester"
        ),
        opener=_TimingOutOpener(),
    )
    assert result["code"] == "transport-failed"
    assert len(calls) == 1
    assert result["receipt"]["queued"] is False


# --- E-08: consent is a non-TTY attestation -----------------------------------------------------


def test_absent_attestation_refuses():
    reason = submit.attestation_refusal(None, tier="metrics", destination=ENDPOINT)
    assert reason is not None
    assert "explicit attestation" in reason


def test_yes_alone_never_authorizes(tmp_path):
    """`--yes` is a preauthorization for expected mutations, not consent to disclose."""

    reason = submit.attestation_refusal(
        None, tier="metrics", destination=ENDPOINT, yes=True
    )
    assert reason is not None
    assert "--yes alone does NOT authorize it" in reason

    result = submit.submit_bundle(
        _bundle(tmp_path), endpoint={"url": ENDPOINT}, tier="metrics", yes=True
    )
    assert result["code"] == "not-attested"
    assert result["transmitted"] is False


def test_present_attestation_records_attribution_without_a_tty():
    att = submit.Attestation(
        tier="metrics",
        destination=ENDPOINT,
        by_human=True,
        actor="maintainer via chat",
        recorded_at="2026-09-14T04:00:00Z",
    )
    assert submit.attestation_refusal(att, tier="metrics", destination=ENDPOINT) is None
    recorded = att.to_dict()
    assert recorded["by_human"] is True
    assert recorded["actor"] == "maintainer via chat"
    assert recorded["tty_required"] is False
    assert recorded["mechanism"] == "explicit-attestation-flag"


def test_attestation_is_not_transferable_across_tier_or_destination():
    att = submit.Attestation(tier="metrics", destination=ENDPOINT, by_human=True)
    wrong_tier = submit.attestation_refusal(
        att, tier="events-redacted", destination=ENDPOINT
    )
    assert wrong_tier is not None and "not transferable" in wrong_tier
    wrong_dest = submit.attestation_refusal(
        att, tier="metrics", destination="https://elsewhere.example/submit"
    )
    assert wrong_dest is not None and "not transferable" in wrong_dest


def test_no_code_path_requires_a_tty_or_asserts_humanity():
    """Spec 20260815-0151-01 retired the TTY gate as dishonest and agent-hostile."""

    # Prose stripped: these modules' docstrings NAME `isatty` and quote 'I am human' precisely in
    # order to explain why neither is used. Grepping raw source would match the explanation.
    from tests.test_run_analytics_export import _code_lines

    for name in (
        "agent_workflows/run_analytics_submit.py",
        "agent_workflows/run_analytics_export.py",
        "agent_workflows/run_analytics_wizard.py",
    ):
        code = _code_lines(name)
        assert "isatty" not in code, f"{name} gates on a TTY"
        assert "I am human" not in code, f"{name} asks the operator to assert humanity"
        assert "stdin" not in code, f"{name} reads stdin for consent"
    # The attestation itself records that no TTY was needed.
    assert (
        submit.Attestation(tier="metrics", destination=ENDPOINT).to_dict()[
            "tty_required"
        ]
        is False
    )


@contextlib.contextmanager
def no_network():
    """Any `connect` raises, using the EXACT technique `lifecycle_fixtures.run_no_network` uses.

    The plan cited that fixture as the pattern to reuse rather than hand-rolling a mock. MEASURED
    CORRECTION: ``run_no_network`` is a FIXTURE with the signature ``(env: IsolatedEnv) ->
    FixtureOutcome``, not a context manager, so it cannot be entered from a unit test. What is
    reusable is its mechanism: subclass ``socket.socket`` so ``connect``/``connect_ex`` raise. That
    is what is reproduced here, deliberately including ``connect_ex``, which a naive version omits
    and which is the call ``socket.create_connection`` actually makes on some paths.
    """

    import socket

    real_socket = socket.socket

    class _NoNetSocket(real_socket):  # type: ignore[misc,valid-type]
        def connect(self, *args, **kwargs):
            raise AssertionError("network access attempted")

        def connect_ex(self, *args, **kwargs):
            raise AssertionError("network access attempted")

    socket.socket = _NoNetSocket  # type: ignore[misc,assignment]
    try:
        yield
    finally:
        socket.socket = real_socket  # type: ignore[misc]


def test_the_no_network_harness_would_actually_catch_a_connection():
    """Guards the guard: a harness that caught nothing would make the tests below vacuous."""

    import socket

    with no_network():
        with pytest.raises(AssertionError):
            socket.socket().connect(("127.0.0.1", 9))


def test_no_network_call_happens_on_the_unavailable_path(tmp_path):
    with no_network():
        result = submit.submit_bundle(_bundle(tmp_path), endpoint=None, tier="metrics")
    assert result["status"] == submit.STATUS_UNAVAILABLE
    assert result["transmitted"] is False


def test_no_network_call_happens_while_building_a_bundle(tmp_path):
    with no_network():
        payload = export.build_metrics_payload([])
        events = export.build_redacted_events([])
        report = export.sanitizer_blind_spot_report(["nothing"])
        bundle = export.write_bundle(
            tmp_path / "nn", tier="metrics", payload=payload, sanitizer_report=report
        )
    assert bundle.manifest_path.is_file()
    assert events["tier"] == "events-redacted"


# --- E-01: the two leaves, exercised through the REAL cli entry point ----------------------------
#
# THESE GO THROUGH `cli.main`, NOT THROUGH THE MODULE FUNCTIONS, deliberately. Everything above
# proves the export/submit LOGIC; this section proves the leaf a user actually types reaches it, with
# the right exit code and without a prompt. A module-level test cannot catch a dispatch that never
# wired the leaf, which is exactly what E-01 adds.


def _cli(argv):
    """Invoke the real entry point. Returns ``(stdout, stderr, rc)``."""

    import io
    from contextlib import redirect_stderr, redirect_stdout

    from agent_workflows import cli

    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(list(argv))
    except SystemExit as exc:  # argparse usage errors exit rather than return
        rc = int(exc.code or 0)
    return out.getvalue(), err.getvalue(), rc


def _repo_with_runs(tmp_path: Path, count: int = 2) -> Path:
    """A synthetic repo with `count` terminal runs, each carrying a same-named prompt file.

    The same NAME in every run is the point: it is what makes the flattening defect detectable.
    """

    repo = tmp_path / "repo"
    runs = repo / ".aw" / "records" / "runs"
    runs.mkdir(parents=True)
    for index in range(count):
        rid = f"run-2026091800000{index}Z-11111{index}"
        run_dir = runs / rid
        run_dir.mkdir()
        (run_dir / "state.json").write_text(
            json.dumps({"run_id": rid, "status": "completed"}), encoding="utf-8"
        )
        (run_dir / "prompt.md").write_text(f"prompt of {rid}", encoding="utf-8")
    return repo


def _exports_dir(repo: Path) -> Path:
    return repo / ".aw" / "records" / "runs" / "analytics" / "exports"


def test_export_previews_by_default_and_writes_nothing(tmp_path):
    """The `dry_run_default` gate is a claim about behavior; this is the behavior."""

    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(["runs", "export", "--dir", str(repo), "--agent"])
    assert rc == 0, out + err
    record = json.loads(out.splitlines()[-1])
    assert record["outcome"] == "preview"
    assert record["applied"] is False
    # NOTHING on disk: not an empty bundle, not a directory.
    assert not _exports_dir(repo).exists()


def test_export_writes_only_under_apply(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(["runs", "export", "--dir", str(repo), "--apply", "--json"])
    assert rc == 0, out + err
    payload = json.loads(out)
    assert payload["data"]["wrote_anything"] is True
    manifest = Path(payload["data"]["manifest_path"])
    assert manifest.is_file()
    assert json.loads(manifest.read_text(encoding="utf-8"))["tier"] == "metrics"


def test_export_defaults_to_the_metrics_tier(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, _err, rc = _cli(["runs", "export", "--dir", str(repo), "--apply", "--json"])
    assert rc == 0
    assert json.loads(out)["data"]["tier"] == "metrics"


def test_export_refuses_an_unknown_tier_rather_than_narrowing_it(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(["runs", "export", "--dir", str(repo), "--tier", "kinda-safe"])
    assert rc == 2, out + err
    assert "unknown export tier" in (out + err)
    assert not _exports_dir(repo).exists()


def test_raw_export_refuses_without_the_attestation_and_writes_nothing(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(
        [
            "runs",
            "export",
            "--dir",
            str(repo),
            "--tier",
            "raw",
            "--include",
            "prompt",
            "--apply",
            "--json",
        ]
    )
    assert rc == 1, out + err
    data = json.loads(out)["data"]
    assert data["code"] == "not-attested"
    assert data["wrote_anything"] is False
    # The refusal names the LOCAL destination rather than rendering it as a redacted url: the shared
    # refusal text runs its destination through `_redact_url`, which printed a filesystem path as the
    # literal "<url>" (measured while wiring the leaf), so the message is authored at the leaf.
    assert "<url>" not in json.loads(out)["summary"]
    assert str(repo) in json.loads(out)["summary"]
    assert not _exports_dir(repo).exists()


def test_yes_alone_does_not_authorize_a_raw_export_through_the_cli(tmp_path):
    """`--yes` is not even accepted here, so it cannot be mistaken for consent."""

    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(
        [
            "runs",
            "export",
            "--dir",
            str(repo),
            "--tier",
            "raw",
            "--include",
            "prompt",
            "--yes",
            "--apply",
        ]
    )
    # A native argparse usage error (exit 2), NOT a silently-authorized export.
    assert rc == 2, out + err
    assert not _exports_dir(repo).exists()


def test_raw_export_refuses_when_attested_but_nothing_was_selected(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(
        [
            "runs",
            "export",
            "--dir",
            str(repo),
            "--tier",
            "raw",
            "--by-human",
            "--actor",
            "maintainer via chat",
            "--apply",
            "--json",
        ]
    )
    assert rc == 1, out + err
    assert json.loads(out)["data"]["code"] == "no-selection"
    assert not _exports_dir(repo).exists()


def test_attested_raw_export_records_its_provenance(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(
        [
            "runs",
            "export",
            "--dir",
            str(repo),
            "--tier",
            "raw",
            "--include",
            "prompt",
            "--by-human",
            "--actor",
            "maintainer via chat",
            "--apply",
            "--json",
        ]
    )
    assert rc == 0, out + err
    attestation = json.loads(out)["data"]["attestation"]
    assert attestation["by_human"] is True
    assert attestation["actor"] == "maintainer via chat"
    # Per spec 20260815-0151-01: no TTY was needed, and the record says so.
    assert attestation["tty_required"] is False
    assert attestation["mechanism"] == "explicit-attestation-flag"


def test_a_raw_export_of_two_runs_keeps_both_same_named_files(tmp_path):
    """MEASURED DEFECT, FIXED: a missing base collapsed every run's `prompt.md` into one file.

    `write_bundle` falls back to `src.name` when `raw_base` is None, and every run directory carries
    a `prompt.md`, so a two-run raw export produced a single `raw/prompt.md` and silently dropped the
    other run's content. An export that loses half its selection while reporting success is worse
    than one that refuses, so the leaf passes the runs' common parent as the base.
    """

    repo = _repo_with_runs(tmp_path, count=2)
    out, err, rc = _cli(
        [
            "runs",
            "export",
            "--dir",
            str(repo),
            "--tier",
            "raw",
            "--include",
            "prompt",
            "--by-human",
            "--actor",
            "t",
            "--apply",
            "--json",
        ]
    )
    assert rc == 0, out + err
    manifest = json.loads(
        Path(json.loads(out)["data"]["manifest_path"]).read_text(encoding="utf-8")
    )
    copied = sorted(
        f["path"] for f in manifest["files"] if f["path"].startswith("raw/")
    )
    assert len(copied) == 2, f"a run's file was lost: {copied}"
    assert copied[0] != copied[1]
    assert all("prompt.md" in path for path in copied)


def test_the_raw_preview_summarizes_by_category_with_counts_and_bytes(tmp_path):
    repo = _repo_with_runs(tmp_path, count=2)
    out, _err, rc = _cli(
        [
            "runs",
            "export",
            "--dir",
            str(repo),
            "--tier",
            "raw",
            "--include",
            "prompt",
            "--by-human",
            "--actor",
            "t",
            "--json",
        ]
    )
    assert rc == 0
    preview = json.loads(out)["data"]["preview"]
    assert preview["categories"]["prompts"]["count"] == 2
    assert preview["categories"]["prompts"]["bytes"] > 0
    assert any("RAW TIER" in w for w in preview["warnings"])


def test_no_export_record_claims_anonymity_or_safety(tmp_path):
    repo = _repo_with_runs(tmp_path)
    for extra in (
        ["--tier", "metrics"],
        ["--tier", "events-redacted"],
        ["--tier", "raw", "--include", "prompt", "--by-human", "--actor", "t"],
    ):
        out, err, rc = _cli(["runs", "export", "--dir", str(repo), "--json", *extra])
        assert rc == 0, out + err
        blob = out.lower()
        for claim in (
            "is anonymous",
            "has been anonymized",
            "safe to share",
            "safe to submit",
            "no sensitive data",
            "contains no secrets",
        ):
            assert claim not in blob, f"{extra} claimed {claim!r}"
        assert json.loads(out)["data"]["claims_anonymity"] is False


def test_the_events_redacted_tier_ships_the_blind_spot_enumeration_through_the_cli(
    tmp_path,
):
    """A report claiming a clean scan without naming its blind spots is a false guarantee."""

    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(
        ["runs", "export", "--dir", str(repo), "--tier", "events-redacted", "--json"]
    )
    assert rc == 0, out + err
    report = json.loads(out)["data"]["sanitizer_report"]
    assert "CORROBORATION ONLY" in report["detector_role"]
    for blind in export.DETECTOR_BLIND_SPOTS:
        assert blind in report["classes_this_detector_does_not_look_for"]
    assert "gitleaks" in report["no_secret_shape_detection"]


def test_submit_returns_the_expected_unavailable_through_the_cli(tmp_path):
    """THE EXPECTED OUTCOME TODAY: this repository approves no endpoint."""

    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(["runs", "export", "--dir", str(repo), "--apply", "--json"])
    assert rc == 0, out + err
    bundle = Path(json.loads(out)["data"]["manifest_path"]).parent

    out, err, rc = _cli(["runs", "submit", "--dir", str(repo), str(bundle), "--json"])
    assert rc == 1, out + err
    data = json.loads(out)["data"]
    assert data["status"] == "unavailable"
    assert data["code"] == "endpoint-unavailable"
    assert data["transmitted"] is False
    assert "export locally" in data["remedy"].lower()


def test_submit_reaches_no_network_on_the_unavailable_path(tmp_path):
    """Proven with the socket-subclass harness, not by reading the code."""

    repo = _repo_with_runs(tmp_path)
    out, _err, rc = _cli(["runs", "export", "--dir", str(repo), "--apply", "--json"])
    assert rc == 0
    bundle = Path(json.loads(out)["data"]["manifest_path"]).parent
    with no_network():
        out, err, rc = _cli(
            ["runs", "submit", "--dir", str(repo), str(bundle), "--json"]
        )
    assert rc == 1, out + err
    assert json.loads(out)["data"]["transmitted"] is False


def test_submit_refuses_a_missing_bundle_rather_than_inventing_one(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(["runs", "submit", "--dir", str(repo), str(tmp_path / "nope")])
    assert rc == 2, out + err
    assert "no bundle directory" in (out + err)


def test_submit_refuses_with_no_bundle_named(tmp_path):
    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(["runs", "submit", "--dir", str(repo)])
    assert rc == 2, out + err
    assert "manifest.json" in (out + err)


def test_a_raw_bundle_cannot_be_submitted_through_the_cli(tmp_path):
    """The dangerous combination is UNREACHABLE, not merely discouraged."""

    repo = _repo_with_runs(tmp_path)
    out, err, rc = _cli(
        [
            "runs",
            "export",
            "--dir",
            str(repo),
            "--tier",
            "raw",
            "--include",
            "prompt",
            "--by-human",
            "--actor",
            "t",
            "--apply",
            "--json",
        ]
    )
    assert rc == 0, out + err
    bundle = Path(json.loads(out)["data"]["manifest_path"]).parent
    # With no endpoint configured the `unavailable` refusal comes first, which is itself the
    # strongest possible answer; the tier gate is asserted directly so the claim does not depend on
    # the absence of configuration.
    out, err, rc = _cli(["runs", "submit", "--dir", str(repo), str(bundle), "--json"])
    assert rc == 1, out + err
    assert json.loads(out)["data"]["transmitted"] is False
    assert "raw" not in submit.SUBMITTABLE_TIERS


def test_neither_new_leaf_prompts_or_reads_a_tty(tmp_path):
    """Every path above ran with stdin unavailable; this pins the absence in the CODE too."""

    from tests.test_run_analytics_export import _code_lines

    code = _code_lines("agent_workflows/run_analytics_cli.py")
    assert "isatty" not in code
    assert "input (" not in code
    assert "I am human" not in code
