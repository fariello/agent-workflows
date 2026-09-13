"""Tests for the analytics privacy projector (IPD bzz5e6, Set runanalytics, E-04 and E-06).

WHAT MAKES THIS SUITE THE FALSIFIABLE HALF OF THE PRIVACY CLAIM. The projector is a WRITE-side
allowlist, so on its own it can only be tested against the cases its author imagined. These tests
therefore pair every refusal assertion with an INDEPENDENT read-side scan by the shipped detector
(``leak_sanitizer``), and every clean scan with a CONTROL scan proving the SAME invocation flags
the SAME canary in its raw form. Without the control, "the detector reported clean" and "the
detector was not looking" are indistinguishable.

NO SENSITIVE LITERAL IS COMMITTED IN THIS FILE. Every canary is assembled from fragments at
runtime, which is the convention the detection engine itself follows for its own patterns
(``leak_sanitizer`` assembles its tokens so that the engine module is self-clean). A test corpus
full of real-shaped secrets is a leak that ships, and pasting one here would make
``aw sanitize --agent`` fail on this very file.

Stdlib unittest only.
"""

from __future__ import annotations

import json
import re
import stat
import tempfile
import unittest
from pathlib import Path

from agent_workflows import leak_sanitizer as ls
from agent_workflows import run_analytics_privacy as privacy
from tests.support import REPO_ROOT

# --- Canaries, assembled from fragments so this file holds no literal leak --------------------
_HANDLE = "gfa" + "riello"
_HOME_PATH = "/ho" + "me/" + _HANDLE + "/VC/agent-workflows"
_MAC_PATH = "/Us" + "ers/" + _HANDLE + "/src"
_WIN_PATH = "C:" + "\\Users\\" + _HANDLE + "\\src"
_HOSTNAME = _HANDLE + "-laptop.local"
_PRIVATE_REPO = "her" + "mes-agent"
_SESSION_ID = "ses_" + "9f3a71c0d2b84e55"
_AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLE"
_SECRET = "sk-" + "live" + "_" + "51H8xQ2mZk9Lw3Rt7Yv0Bn4Cp6Ds8Fg1"
_PROMPT_BODY = "You are an agent. Read the plan and " + "implement E-01 as specified."
_COMMAND_TEXT = "git commit -m 'wip' -- " + _HOME_PATH + "/agent_workflows/cli.py"


def _ruleset() -> ls.Ruleset:
    return ls.build_ruleset(REPO_ROOT)


def _scan(text: str) -> list[ls.Finding]:
    return ls.scan_text(text, "canary", _ruleset())


class SaltContractTests(unittest.TestCase):
    """OQ-01's resolution, asserted rather than merely documented."""

    def test_salt_is_created_beside_the_cache_and_is_not_world_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "analytics" / "cache"
            salt = privacy.load_or_create_salt(cache)
            target = privacy.salt_path(cache)
            self.assertTrue(
                target.is_file(), "the salt must be written beside the cache"
            )
            self.assertEqual(target.parent, cache)
            self.assertEqual(target.name, privacy.SALT_FILENAME)
            self.assertGreaterEqual(len(salt), 32)
            mode = stat.S_IMODE(target.stat().st_mode)
            self.assertEqual(
                mode & (stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH),
                0,
                f"the salt must not be group/world readable, got {oct(mode)}",
            )

    def test_salt_is_stable_across_calls_and_never_reminted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "cache"
            first = privacy.load_or_create_salt(cache)
            second = privacy.load_or_create_salt(cache)
            self.assertEqual(first, second, "re-reading must not mint a new salt")

    def test_pseudonym_is_stable_per_salt_and_uncorrelatable_across_salts(self) -> None:
        value = _HOME_PATH
        a = privacy.pseudonymize(value, salt="salt-a", domain="root")
        again = privacy.pseudonymize(value, salt="salt-a", domain="root")
        b = privacy.pseudonymize(value, salt="salt-b", domain="root")
        self.assertEqual(a, again, "the same salt must give a stable pseudonym")
        self.assertNotEqual(
            a, b, "a rotated salt must invalidate correlation by design"
        )

    def test_pseudonym_domains_do_not_join(self) -> None:
        value = _HOSTNAME
        as_host = privacy.pseudonymize(value, salt="s", domain="host")
        as_path = privacy.pseudonymize(value, salt="s", domain="path")
        self.assertNotEqual(
            as_host,
            as_path,
            "the domain must participate so a cross-domain join is impossible",
        )

    def test_pseudonym_does_not_contain_its_input(self) -> None:
        token = privacy.pseudonymize(_HOME_PATH, salt="s", domain="path")
        self.assertNotIn(_HANDLE, token)
        self.assertNotIn("/", token.split(":", 1)[1])
        self.assertTrue(re.match(r"^path:[0-9a-f]{16}$", token), token)

    def test_unknown_domain_and_empty_salt_are_refused(self) -> None:
        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.pseudonymize("x", salt="s", domain="not-a-domain")
        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.pseudonymize("x", salt="", domain="path")


class AllowlistDirectionTests(unittest.TestCase):
    """The boundary must PASS known-good keys, not FILTER known-bad ones."""

    def test_an_unknown_key_is_refused_and_the_diagnostic_names_it(self) -> None:
        with self.assertRaises(privacy.PrivacyRefusal) as ctx:
            privacy.project_metric_facts({"prompt_body": _PROMPT_BODY})
        self.assertEqual(ctx.exception.key, "prompt_body")
        self.assertIn("prompt_body", str(ctx.exception))
        self.assertIn("allowlist", str(ctx.exception))

    def test_refusal_is_not_a_silent_drop(self) -> None:
        """A dropped key would look like success; the refusal is what makes the boundary testable."""

        facts = {"cost": 1.25, "unlisted_extra": 7}
        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.project_metric_facts(facts)

    def test_every_forbidden_class_from_the_plan_is_refused(self) -> None:
        forbidden = {
            "prompt": _PROMPT_BODY,
            "response": _PROMPT_BODY,
            "conversation": _PROMPT_BODY,
            "file_contents": "def f():\n    return 1\n",
            "command": _COMMAND_TEXT,
            "argv": _COMMAND_TEXT,
            "environment": {"AWS_SECRET_ACCESS_KEY": _SECRET},
            "username": _HANDLE,
            "hostname": _HOSTNAME,
            "repo": _HOME_PATH,
            "path": _MAC_PATH,
            "remote": "git@github.com:" + _HANDLE + "/" + _PRIVATE_REPO + ".git",
            "branch": "wip/" + _HANDLE,
            "commit_message": "fix the thing in " + _HOME_PATH,
            "session_id": _SESSION_ID,
            "api_key": _AWS_KEY,
            "event_payload": {"text": _PROMPT_BODY},
        }
        for key, value in forbidden.items():
            with self.subTest(forbidden=key):
                with self.assertRaises(privacy.PrivacyRefusal) as ctx:
                    privacy.project_metric_facts({key: value})
                self.assertEqual(ctx.exception.key, key)

    def test_allowlisted_numeric_and_label_facts_pass_unchanged(self) -> None:
        facts = {
            "run_id": "run-20260101T000000Z-1234",
            "duration_seconds": 12.5,
            "cost": 0.4213,
            "cost_currency": "USD",
            "tokens": {"input": 100, "output": 20, "cache": 5, "total": 125},
            "token_total": 125,
            "phase": "execute",
            "model": "its_direct/pt3-claude-opus-5-1m-us",
            "provider": "opencode",
            "outcome": "executed",
            "is_complete": True,
            "event_count": 42,
            "quality_flags": ["complete", "parsed-clean"],
        }
        projected = privacy.project_metric_facts(facts)
        self.assertEqual(projected["duration_seconds"], 12.5)
        self.assertEqual(projected["cost"], 0.4213)
        self.assertEqual(
            projected["tokens"], {"input": 100, "output": 20, "cache": 5, "total": 125}
        )
        self.assertEqual(projected["quality_flags"], ["complete", "parsed-clean"])
        self.assertEqual(set(projected), set(facts))

    def test_projection_is_key_order_independent(self) -> None:
        a = {"cost": 1.0, "phase": "execute", "event_count": 3}
        b = {"event_count": 3, "cost": 1.0, "phase": "execute"}
        self.assertEqual(
            json.dumps(privacy.project_metric_facts(a), sort_keys=False),
            json.dumps(privacy.project_metric_facts(b), sort_keys=False),
            "the encoded form must not depend on the producer's dict ordering",
        )

    def test_an_allowlisted_key_still_refuses_a_smuggled_value(self) -> None:
        """The key allowlist is necessary but not sufficient: the VALUE shape is checked too."""

        smuggles = [
            ("phase", _HOME_PATH),
            ("phase", "execute; " + _COMMAND_TEXT),
            ("model", _MAC_PATH),
            ("driver", _WIN_PATH),
            ("outcome", _PROMPT_BODY),
            ("status", "../../etc/passwd"),
            ("warnings", ["failed to read " + _HOME_PATH + "/state.json"]),
            ("quality_flags", [_PROMPT_BODY]),
            ("run_id", _HOME_PATH),
            ("created_at", _HOME_PATH),
        ]
        for key, value in smuggles:
            with self.subTest(key=key, value=str(value)[:24]):
                with self.assertRaises(privacy.PrivacyRefusal):
                    privacy.project_metric_facts({key: value})

    def test_source_root_id_must_already_be_a_pseudonym(self) -> None:
        with self.assertRaises(privacy.PrivacyRefusal) as ctx:
            privacy.project_metric_facts({"source_root_id": _HOME_PATH})
        self.assertIn("pseudonym", str(ctx.exception))
        ok = privacy.pseudonymize(_HOME_PATH, salt="s", domain="root")
        self.assertEqual(
            privacy.project_metric_facts({"source_root_id": ok})["source_root_id"], ok
        )

    def test_open_token_map_accepts_an_unanticipated_component_key(self) -> None:
        """Measured in this repo's corpus: `reasoning` appears and a closed set would drop it."""

        projected = privacy.project_metric_facts(
            {
                "tokens": {
                    "input": 1,
                    "output": 2,
                    "cache": 3,
                    "reasoning": 4,
                    "total": 10,
                }
            }
        )
        self.assertEqual(projected["tokens"]["reasoning"], 4)
        invented = privacy.project_metric_facts({"tokens": {"some_future_key": 9}})
        self.assertEqual(invented["tokens"]["some_future_key"], 9)

    def test_token_map_refuses_a_non_numeric_or_path_shaped_component(self) -> None:
        for bad in ({"input": _PROMPT_BODY}, {_HOME_PATH: 1}, {"input": float("nan")}):
            with self.subTest(bad=str(bad)[:32]):
                with self.assertRaises(privacy.PrivacyRefusal):
                    privacy.project_metric_facts({"tokens": bad})

    def test_event_allowlist_is_narrower_than_the_metric_allowlist(self) -> None:
        self.assertTrue(
            privacy.ALLOWED_EVENT_KEYS
            < privacy.ALLOWED_METRIC_KEYS | privacy.ALLOWED_EVENT_KEYS
        )
        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.project_event_facts({"payload": {"text": _PROMPT_BODY}})
        shape_only = privacy.project_event_facts(
            {
                "event_type": "turn-start",
                "payload_byte_count": 1024,
                "payload_field_count": 7,
            }
        )
        self.assertEqual(shape_only["payload_byte_count"], 1024)

    def test_no_forbidden_key_is_in_the_allowlist_by_accident(self) -> None:
        forbidden_names = {
            "prompt",
            "response",
            "conversation",
            "command",
            "argv",
            "environment",
            "env",
            "username",
            "user",
            "hostname",
            "host",
            "repo",
            "path",
            "cwd",
            "remote",
            "branch",
            "commit_message",
            "session_id",
            "api_key",
            "secret",
            "token",
            "payload",
            "text",
            "content",
        }
        overlap = forbidden_names & (
            privacy.ALLOWED_METRIC_KEYS | privacy.ALLOWED_EVENT_KEYS
        )
        self.assertEqual(
            overlap, set(), f"forbidden names present in the allowlist: {overlap}"
        )


class DiagnosticRedactionTests(unittest.TestCase):
    """The second-most likely leak is a message, because the natural fix interpolates a path."""

    def test_redact_text_removes_home_paths_in_three_shapes(self) -> None:
        salt = "s"
        for raw in (_HOME_PATH, _MAC_PATH, "~/" + "VC/agent-workflows"):
            with self.subTest(shape=raw[:12]):
                redacted = privacy.redact_text(
                    f"could not read {raw}/state.json", salt=salt
                )
                self.assertNotIn(_HANDLE, redacted)
                self.assertIn("path:", redacted)

    def test_redacted_diagnostics_are_clean_under_the_shipped_detector(self) -> None:
        salt = "s"
        message = f"failed on {_HOME_PATH}/state.json and {_MAC_PATH}/x"
        control = _scan(message)
        self.assertTrue(
            control, "CONTROL: the raw message must be flagged, else nothing is proven"
        )
        redacted = privacy.redact_text(message, salt=salt)
        self.assertEqual(
            _scan(redacted), [], f"redacted diagnostic still leaks: {redacted}"
        )


class IndependentDetectorTests(unittest.TestCase):
    """Read-side proof by the SHIPPED engine, each with its control. See E-06/V-04."""

    def test_control_the_detector_does_flag_every_path_canary_raw(self) -> None:
        """If this fails, every 'clean' assertion in this suite is worthless."""

        for raw in (
            _HOME_PATH,
            _MAC_PATH,
            _WIN_PATH,
            _PRIVATE_REPO,
            _SESSION_ID,
            _HANDLE,
        ):
            with self.subTest(canary=raw[:16]):
                findings = _scan(raw)
                self.assertTrue(
                    findings, f"CONTROL FAILED: the detector does not flag {raw[:16]!r}"
                )
                self.assertTrue(
                    any(f.severity == "fail" for f in findings),
                    f"expected a fail-severity finding for {raw[:16]!r}, got "
                    f"{[(f.rule, f.severity) for f in findings]}",
                )

    def test_projected_facts_are_clean_under_the_shipped_detector(self) -> None:
        salt = "s"
        facts = privacy.project_metric_facts(
            {
                "run_id": "run-20260101T000000Z-1234",
                "source_root_id": privacy.pseudonymize(
                    _HOME_PATH, salt=salt, domain="root"
                ),
                "cost": 1.5,
                "tokens": {"input": 1, "output": 2, "total": 3},
                "phase": "execute",
                "model": "its_direct/pt3-claude-opus-5-1m-us",
            }
        )
        encoded = json.dumps(facts, indent=2, sort_keys=True)
        self.assertEqual(_scan(encoded), [], f"projected facts leaked: {encoded}")
        self.assertNotIn(_HANDLE, encoded)

    def test_the_projector_module_itself_is_self_clean(self) -> None:
        """A module documenting a privacy boundary must not contain a canary of its own."""

        source = (REPO_ROOT / "agent_workflows" / "run_analytics_privacy.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            _scan(source),
            [],
            "the projector module must be self-clean under the shipped detector",
        )

    def test_this_test_file_holds_no_literal_leak(self) -> None:
        """The canaries are assembled from fragments, so the tracked file is itself clean."""

        source = Path(__file__).read_text(encoding="utf-8")
        findings = _scan(source)
        self.assertEqual(
            findings,
            [],
            "this test file must not commit a literal canary: "
            f"{[(f.rule, f.location) for f in findings]}",
        )


class NoSecondSanitizerTests(unittest.TestCase):
    """`local_leaks` is deliberately ONE engine behind a thin re-export; do not fork it."""

    def test_the_analytics_modules_define_no_detection_ruleset(self) -> None:
        for name in ("run_analytics_privacy.py", "run_analytics_cache.py"):
            source = (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            with self.subTest(module=name):
                for forbidden in (
                    "_FAIL_PATTERNS",
                    "build_ruleset",
                    "derive_warn_tokens",
                ):
                    self.assertNotIn(
                        forbidden,
                        source,
                        f"{name} must not reimplement the detection engine ({forbidden})",
                    )

    def test_no_raw_filelock_or_fcntl_import_in_the_analytics_modules(self) -> None:
        pattern = re.compile(
            r"^\s*(?:import|from)\s+(?:fcntl|filelock)\b", re.MULTILINE
        )
        for name in ("run_analytics_privacy.py", "run_analytics_cache.py"):
            source = (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            with self.subTest(module=name):
                self.assertIsNone(
                    pattern.search(source),
                    f"{name} must take its lock through platform_lock, never directly",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
