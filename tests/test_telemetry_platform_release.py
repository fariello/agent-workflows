"""`platform_release_major` must conform to its schema shape on every OS, or EVERY event is dropped.

Measured on the Windows Server CI runner: `platform.release()` returned `2025Server`, the probe
emitted that verbatim, the schema (`^\\d{1,6}$`) refused the whole event, and no telemetry stream
was written for any turn.
"""

from __future__ import annotations

import unittest
from unittest import mock

from agent_workflows import run_analytics_telemetry as T


class PlatformReleaseMajorTests(unittest.TestCase):
    def test_release_strings_reduce_to_leading_digits_or_are_omitted(self) -> None:
        cases = {
            "2025Server": "2025",
            "10": "10",
            "6.8.0-45-generic": "6",
            "22.04": "22",
            "": None,
            "Vista": None,
        }
        for release, expected in cases.items():
            with self.subTest(release=release):
                with mock.patch("platform.release", return_value=release):
                    resources = T.SystemResourceProbeAdapter().resources()
                self.assertEqual(resources.get("platform_release_major"), expected)

    def test_a_windows_server_release_still_yields_a_valid_event(self) -> None:
        with mock.patch("platform.release", return_value="2025Server"):
            resources = T.SystemResourceProbeAdapter().resources()
        payload = {
            "schema_version": T.TELEMETRY_SCHEMA_VERSION,
            "event_kind": "start",
            "execution_id": "x1",
            "monotonic_offset_seconds": 0.0,
            "wall_timestamp": "2026-09-25T00:00:00Z",
            "sequence": 1,
            "resources": resources,
        }
        T.validate_event(payload)  # raises SchemaRefusal on a non-conforming field


if __name__ == "__main__":
    unittest.main()
