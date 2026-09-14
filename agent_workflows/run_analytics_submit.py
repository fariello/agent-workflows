"""Explicit, attested submission of an analytics bundle (runanalytics Order 09, ixis0c: E-06..E-08).

THIS MODULE'S EXPECTED ANSWER TODAY IS "UNAVAILABLE", AND THAT IS A COMPLETE IMPLEMENTATION RATHER
THAN A STUB. The plan's endpoint contract requires an operator, a URL, a TLS posture, an
authentication source, a size limit, an accepted schema, a server retention policy, an access
policy, a deletion-request method and a contact. NONE of those exists in this repository. So the
honest deliverable is a tested refusal with an actionable message, and the thing NOT to build is a
generic uploader pointed at whatever URL a caller supplies. The transport below is nevertheless real
and fully tested, because the refusal has to be the POLICY layer's decision, not an accident of
having no working client.

THE STDLIB DEFAULT OPENER IS AN EXFILTRATION SURFACE, AND A SCHEME CHECK ON THE CONFIGURED URL DOES
NOT FIX IT. Measured 2026-09-14: ``urllib.request.build_opener()`` installs ``HTTPRedirectHandler``,
``FileHandler``, ``DataHandler`` and ``FTPHandler``; ``urlopen("file:///<path>")`` RETURNED THE
FILE'S CONTENTS and ``urlopen("data:text/plain,hello")`` returned its payload. Therefore validating
the scheme of the URL a user configured is insufficient: a ``302`` to ``file:///etc/passwd`` is
followed by the same opener that just passed the check, which turns a submit command into a
local-file reader whose output goes to a remote server. The fix is
:func:`build_restricted_opener`, an ``OpenerDirector`` carrying ONLY ``HTTPSHandler``,
``HTTPDefaultErrorHandler`` and ``HTTPErrorProcessor``, plus :class:`RefusingRedirectHandler` so a
redirect target is re-checked against the same policy as the original.

Measured detail worth keeping: a restricted opener asked for ``file://`` fails with a bare
``AttributeError`` ("'NoneType' object has no attribute 'read'"), because no handler claims the
scheme and ``OpenerDirector.open`` ends up calling ``.read()`` on ``None``. That is a correct
refusal with a useless message, so :func:`open_url` wraps it in :class:`SubmitRefusal`.

AUTHENTICATION IS READ FROM THE ENVIRONMENT BY NAME AND NEVER STORED, LOGGED OR ECHOED, following
``oc_models.http_fetch_json``, whose Authorization header "is never echoed anywhere". The receipt
records the environment variable NAME, never its value.

THERE IS NO RETRY, NO QUEUE, NO DAEMON AND NO BEACON, and their absence is asserted by a test that
greps this module. A failed submission is reported to the caller, who decides. Automatic retry of an
upload the user consented to ONCE would transmit data on an occasion the user never approved.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

__all__ = [
    "SubmitRefusal",
    "STATUS_UNAVAILABLE",
    "STATUS_REFUSED",
    "STATUS_SUBMITTED",
    "EXIT_OK",
    "EXIT_REFUSED",
    "EXIT_USAGE",
    "MAX_BUNDLE_BYTES",
    "SUBMITTABLE_TIERS",
    "RefusingRedirectHandler",
    "build_restricted_opener",
    "url_policy_refusal",
    "open_url",
    "Attestation",
    "attestation_refusal",
    "validate_bundle",
    "build_receipt",
    "submit_bundle",
]


class SubmitRefusal(ValueError):
    """A submission was REFUSED, carrying a machine-readable code and a human remedy."""

    def __init__(self, code: str, summary: str, remedy: str = "") -> None:
        self.code = code
        self.summary = summary
        self.remedy = remedy
        super().__init__(summary if not remedy else f"{summary} ({remedy})")


STATUS_UNAVAILABLE = "unavailable"
STATUS_REFUSED = "refused"
STATUS_SUBMITTED = "submitted"

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2

#: A conservative ceiling. A bundle larger than this is refused rather than streamed, because a
#: submission whose size the user did not review is a submission whose contents they did not review.
MAX_BUNDLE_BYTES: int = 32 * 1024 * 1024

#: `raw` IS DELIBERATELY ABSENT. Raw bundles carry original prompts, code, commands and possibly
#: secrets. With no approved endpoint, retention policy or deletion method, transmitting one is
#: unreviewable, so the dangerous combination is made unreachable rather than merely discouraged.
SUBMITTABLE_TIERS: frozenset[str] = frozenset({"metrics", "events-redacted"})

_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


# --- E-06: the transport ------------------------------------------------------------------------


def url_policy_refusal(url: str, *, allow_loopback_http: bool = False) -> str | None:
    """The URL policy, as one predicate reused for the ORIGINAL url and every redirect target."""

    if not url or not str(url).strip():
        return "empty url"
    parts = urlsplit(str(url))
    scheme = (parts.scheme or "").lower()
    if scheme in ("file", "data", "ftp", "ftps", "gopher", "jar", "netdoc"):
        return f"scheme {scheme!r} is never permitted for submission"
    if scheme == "http":
        host = (parts.hostname or "").lower()
        if allow_loopback_http and host in _LOOPBACK_HOSTS:
            return None
        return "plain http is refused; submission requires https"
    if scheme != "https":
        return f"unsupported scheme {scheme!r}; submission requires https"
    if not parts.hostname:
        return "url has no host"
    return None


class RefusingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-check EVERY redirect target against the same policy as the original url.

    Without this the restricted opener would still be wrong in the interesting case. The handler
    chain refuses ``file://`` as an ENTRY point, but a server answering ``302 Location:
    file:///etc/passwd`` hands the new url back through the redirect machinery, and a permissive
    redirect handler would follow it. So the policy check belongs HERE as well as at the entry.
    """

    def __init__(self, *, allow_loopback_http: bool = False) -> None:
        self.allow_loopback_http = allow_loopback_http

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        reason = url_policy_refusal(
            newurl, allow_loopback_http=self.allow_loopback_http
        )
        if reason:
            raise SubmitRefusal(
                "redirect-refused",
                f"refusing redirect to a target that fails policy: {reason}",
                "the server redirected the submission somewhere it may not go; "
                "check the endpoint configuration with its operator",
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_restricted_opener(
    *, allow_loopback_http: bool = False
) -> urllib.request.OpenerDirector:
    """An opener carrying ONLY https, its error handling, and a refusing redirect handler.

    Built by hand rather than with ``build_opener``, because ``build_opener`` starts from the
    DEFAULT handler list and adds to it; the whole point here is what is ABSENT. Measured, the
    default list includes ``FileHandler``, ``DataHandler``, ``FTPHandler`` and a permissive
    ``HTTPRedirectHandler``, and each is an exfiltration or SSRF vector for a command whose job is
    to send local data somewhere.
    """

    opener = urllib.request.OpenerDirector()
    opener.add_handler(urllib.request.HTTPSHandler())
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
    opener.add_handler(urllib.request.HTTPErrorProcessor())
    opener.add_handler(RefusingRedirectHandler(allow_loopback_http=allow_loopback_http))
    if allow_loopback_http:
        # Only for a local test double, and only because `url_policy_refusal` gates the host.
        opener.add_handler(urllib.request.HTTPHandler())
    return opener


def open_url(
    url: str,
    *,
    data: bytes | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: float = 15.0,
    opener: urllib.request.OpenerDirector | None = None,
    allow_loopback_http: bool = False,
) -> bytes:
    """Open `url` through the restricted opener, refusing anything policy forbids.

    Never retries. A failure is returned to the caller as a refusal, because a retry would transmit
    the bundle again on an occasion the user did not consent to.
    """

    reason = url_policy_refusal(url, allow_loopback_http=allow_loopback_http)
    if reason:
        raise SubmitRefusal(
            "url-refused",
            f"refusing to open {_redact_url(url)}: {reason}",
            "configure an https endpoint; file:, data: and ftp: are never permitted",
        )
    director = opener or build_restricted_opener(
        allow_loopback_http=allow_loopback_http
    )
    request = urllib.request.Request(url, data=data, headers=dict(headers or {}))
    try:
        with director.open(request, timeout=timeout) as response:
            return response.read()
    except SubmitRefusal:
        raise
    except urllib.error.HTTPError as exc:
        raise SubmitRefusal(
            "server-rejected",
            f"endpoint rejected the submission with status {exc.code}",
            "nothing was retried; inspect the endpoint's response and resubmit deliberately",
        ) from exc
    except AttributeError as exc:
        # The MEASURED refusal shape when no handler claims the scheme: OpenerDirector.open ends up
        # calling .read() on None. A correct refusal with a useless message, so it is wrapped here.
        raise SubmitRefusal(
            "scheme-unhandled",
            f"refusing {_redact_url(url)}: no permitted handler claims that scheme",
            "submission requires https; the restricted opener carries no file/data/ftp handler",
        ) from exc
    except Exception as exc:
        raise SubmitRefusal(
            "transport-failed",
            f"submission transport failed: {type(exc).__name__}",
            "nothing was retried and nothing was queued; resubmit deliberately when ready",
        ) from exc


def _redact_url(url: str) -> str:
    """Show scheme and host only. A url can carry a token in its query string."""

    try:
        parts = urlsplit(str(url))
    except Exception:
        return "<unparseable url>"
    if not parts.scheme:
        return "<url>"
    return f"{parts.scheme}://{parts.hostname or '<host>'}"


# --- E-08: consent as a non-TTY attestation -----------------------------------------------------


@dataclass(frozen=True)
class Attestation:
    """An explicit, non-TTY consent record naming the tier and the destination.

    THIS IS NOT A TTY CONFIRMATION, AND THE DIFFERENCE IS A DECIDED QUESTION IN THIS REPOSITORY.
    Spec ``20260815-0151-01-honest-human-approval-attestation`` is ``Status: implemented`` and
    replaced a ``sys.stdin.isatty()`` requirement plus a typed confirmation with ``--by-human``, an
    explicit attestation, on the reasoning that "an executing agent has no TTY, so it can NEVER
    record an approval, even one the human explicitly gave in chat", and that no surface should
    require asserting "I am human". Its G2 is the shape copied here: the action SUCCEEDS iff the
    explicit flag is passed and is REFUSED with a clear message otherwise, with attributed
    provenance recorded.

    ``--yes`` DOES NOT SATISFY THIS, deliberately. ``--yes`` is a broad preauthorization for the
    mutations a command is expected to make; treating it as consent would make a raw export or a
    transmission collateral damage of an unrelated batch invocation. The attestation names the tier
    AND the destination, so it cannot be reused for a different disclosure.
    """

    tier: str
    destination: str
    by_human: bool = False
    actor: str = ""
    recorded_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "destination": self.destination,
            "by_human": bool(self.by_human),
            "actor": self.actor,
            "recorded_at": self.recorded_at,
            "mechanism": "explicit-attestation-flag",
            "tty_required": False,
        }


def attestation_refusal(
    attestation: Attestation | None,
    *,
    tier: str,
    destination: str,
    yes: bool = False,
) -> str | None:
    """Return a refusal reason, or None if this disclosure is attested.

    `yes` is accepted ONLY so this function can prove it is not sufficient: it is never read as
    consent. A test asserts that passing `yes=True` with no attestation still refuses.
    """

    if attestation is None or not attestation.by_human:
        return (
            "this disclosure requires an explicit attestation naming the tier and the "
            f"destination (tier={tier!r}, destination={_redact_url(destination)}); "
            "--yes alone does NOT authorize it"
        )
    if attestation.tier != tier:
        return (
            f"the attestation names tier {attestation.tier!r} but the requested tier is "
            f"{tier!r}; consent is specific to a tier and is not transferable"
        )
    if attestation.destination != destination:
        return (
            "the attestation names a different destination; consent is specific to a "
            "destination and is not transferable"
        )
    return None


# --- E-07: validation, the receipt, and the unavailable path ------------------------------------


def validate_bundle(root: Path | str, *, tier: str | None = None) -> dict[str, Any]:
    """Validate manifest, schema, checksums, tier and size BEFORE any transmission."""

    from agent_workflows import run_analytics_export as export

    base = Path(root)
    manifest_path = base / "manifest.json"
    if not manifest_path.is_file():
        raise SubmitRefusal(
            "manifest-missing",
            f"no manifest.json under {base.name}",
            "re-create the bundle with `runs export`",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SubmitRefusal(
            "manifest-unreadable",
            f"manifest.json is not valid JSON: {type(exc).__name__}",
            "re-create the bundle with `runs export`",
        ) from exc
    if not isinstance(manifest, Mapping):
        raise SubmitRefusal(
            "manifest-unreadable",
            "manifest.json is not a JSON object",
            "re-create the bundle with `runs export`",
        )

    version = manifest.get("schema_version")
    if version != export.EXPORT_SCHEMA_VERSION:
        raise SubmitRefusal(
            "schema-unknown",
            f"bundle schema_version {version!r} is not the supported "
            f"{export.EXPORT_SCHEMA_VERSION}",
            "a bundle from a different tool generation is refused rather than guessed at",
        )

    bundle_tier = manifest.get("tier")
    if tier is not None and bundle_tier != tier:
        raise SubmitRefusal(
            "tier-mismatch",
            f"bundle tier {bundle_tier!r} is not the requested {tier!r}",
            "submit the bundle you inspected",
        )
    if bundle_tier not in SUBMITTABLE_TIERS:
        raise SubmitRefusal(
            "tier-not-submittable",
            f"tier {bundle_tier!r} may not be submitted",
            "only "
            + ", ".join(sorted(SUBMITTABLE_TIERS))
            + " are transmissible; a raw "
            "bundle carries original content and stays local",
        )

    total = 0
    for entry in manifest.get("files") or []:
        if not isinstance(entry, Mapping):
            raise SubmitRefusal(
                "manifest-unreadable",
                "a manifest file entry is not an object",
                "re-create the bundle",
            )
        rel = str(entry.get("path") or "")
        reason = export.archive_member_refusal(rel)
        if reason:
            raise SubmitRefusal(
                "manifest-hostile-path", f"manifest entry refused: {reason}", ""
            )
        target = base / rel
        if not target.is_file():
            raise SubmitRefusal(
                "file-missing",
                f"manifest names {rel!r} but it is absent",
                "re-create the bundle",
            )
        actual = _sha256(target)
        if actual != entry.get("sha256"):
            raise SubmitRefusal(
                "checksum-mismatch",
                f"{rel!r} does not match its manifest checksum",
                "the bundle was modified after creation; re-create it",
            )
        total += target.stat().st_size

    if total > MAX_BUNDLE_BYTES:
        raise SubmitRefusal(
            "too-large",
            f"bundle is {total} bytes, over the {MAX_BUNDLE_BYTES} limit",
            "export a narrower selection",
        )

    return {"tier": bundle_tier, "total_bytes": total, "manifest": dict(manifest)}


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_receipt(
    *,
    tier: str,
    destination: str,
    status: str,
    total_bytes: int,
    attestation: Attestation | None = None,
    auth_env_var: str = "",
    detail: str = "",
) -> dict[str, Any]:
    """A local record of what was sent, where and when. CARRIES NO SECRET.

    The destination is stored scheme-and-host only, and the credential is recorded as an
    environment variable NAME. A receipt is a file that outlives the command and gets pasted into
    bug reports, so a token in one is a token in a chat log.
    """

    from datetime import datetime, timezone

    return {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tier": tier,
        "destination": _redact_url(destination),
        "status": status,
        "total_bytes": total_bytes,
        "auth_source_env_var": auth_env_var,
        "auth_value_recorded": False,
        "attestation": attestation.to_dict() if attestation is not None else None,
        "detail": detail,
        "retried": False,
        "queued": False,
    }


def submit_bundle(
    root: Path | str,
    *,
    endpoint: Mapping[str, Any] | None = None,
    tier: str | None = None,
    attestation: Attestation | None = None,
    yes: bool = False,
    opener: urllib.request.OpenerDirector | None = None,
    allow_loopback_http: bool = False,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Submit a validated bundle, or return an actionable `unavailable`.

    WITH NO CONFIGURED ENDPOINT THIS RETURNS ``unavailable`` AND TRANSMITS NOTHING, which is the
    expected result in this repository today: no operator, URL, retention policy, deletion method
    or contact is approved anywhere in it. That is the deliberate deliverable, not a fallback.
    """

    url = str((endpoint or {}).get("url") or "").strip()
    if not url:
        receipt = build_receipt(
            tier=str(tier or ""),
            destination="",
            status=STATUS_UNAVAILABLE,
            total_bytes=0,
            attestation=None,
            detail=(
                "No submission endpoint is configured, and this repository approves none: there "
                "is no operator, URL, TLS posture, retention policy, access policy, deletion "
                "method or contact for analytics submission. Nothing was transmitted."
            ),
        )
        return {
            "status": STATUS_UNAVAILABLE,
            "exit_code": EXIT_REFUSED,
            "code": "endpoint-unavailable",
            "summary": "submission is unavailable: no approved endpoint is configured",
            "remedy": (
                "Export locally with `runs export` and share the bundle yourself. Submission "
                "becomes available only once an endpoint with a published retention and "
                "deletion policy is approved and configured."
            ),
            "receipt": receipt,
            "transmitted": False,
        }

    try:
        facts = validate_bundle(root, tier=tier)
    except SubmitRefusal as exc:
        return _refusal_result(exc, tier=str(tier or ""), destination=url)

    effective_tier = str(facts["tier"])
    reason = attestation_refusal(
        attestation, tier=effective_tier, destination=url, yes=yes
    )
    if reason:
        return _refusal_result(
            SubmitRefusal(
                "not-attested",
                reason,
                "pass the explicit attestation naming this tier and destination",
            ),
            tier=effective_tier,
            destination=url,
        )

    auth_env_var = str((endpoint or {}).get("auth_env_var") or "")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_env_var:
        import os

        token = os.environ.get(auth_env_var, "")
        if not token:
            return _refusal_result(
                SubmitRefusal(
                    "auth-missing",
                    f"endpoint requires credentials from ${auth_env_var}, which is unset",
                    f"export {auth_env_var} in your shell; it is never written to a config file",
                ),
                tier=effective_tier,
                destination=url,
            )
        # Sent in a header, never echoed, never logged, never written to the receipt.
        headers["Authorization"] = f"Bearer {token}"

    payload = json.dumps(
        {"tier": effective_tier, "manifest": facts["manifest"]}, sort_keys=True
    ).encode("utf-8")
    try:
        open_url(
            url,
            data=payload,
            headers=headers,
            timeout=timeout,
            opener=opener,
            allow_loopback_http=allow_loopback_http,
        )
    except SubmitRefusal as exc:
        return _refusal_result(exc, tier=effective_tier, destination=url)

    return {
        "status": STATUS_SUBMITTED,
        "exit_code": EXIT_OK,
        "code": "",
        "summary": f"submitted {effective_tier} bundle",
        "remedy": "",
        "receipt": build_receipt(
            tier=effective_tier,
            destination=url,
            status=STATUS_SUBMITTED,
            total_bytes=int(facts["total_bytes"]),
            attestation=attestation,
            auth_env_var=auth_env_var,
        ),
        "transmitted": True,
    }


def _refusal_result(
    exc: SubmitRefusal, *, tier: str, destination: str
) -> dict[str, Any]:
    return {
        "status": STATUS_REFUSED,
        "exit_code": EXIT_REFUSED,
        "code": exc.code,
        "summary": exc.summary,
        "remedy": exc.remedy,
        "receipt": build_receipt(
            tier=tier,
            destination=destination,
            status=STATUS_REFUSED,
            total_bytes=0,
            detail=exc.summary,
        ),
        "transmitted": False,
    }
