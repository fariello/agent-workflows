"""`private_file.create_private_file` makes a secret readable by the current user ONLY, on every OS.

POSIX: mode 0600. Windows: a PROTECTED DACL (no inheritance from the folder) holding exactly one
ALLOW ACE, for the current user's SID, read back from the OS with `GetFileSecurityW`.
"""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path

from agent_workflows import private_file


class PrivateFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_content_is_written_and_creation_is_exclusive(self) -> None:
        path = self.dir / "secret"
        private_file.create_private_file(path, b"s3cret")
        self.assertEqual(path.read_bytes(), b"s3cret")
        with self.assertRaises(FileExistsError):
            private_file.create_private_file(path, b"other")
        self.assertEqual(
            path.read_bytes(), b"s3cret", "an existing secret must never be clobbered"
        )

    @unittest.skipUnless(os.name == "posix", "POSIX mode bits")
    def test_posix_mode_is_0600(self) -> None:
        path = self.dir / "secret"
        private_file.create_private_file(path, b"x")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    @unittest.skipUnless(os.name == "nt", "Windows DACL")
    def test_windows_dacl_is_protected_and_owner_only(self) -> None:  # pragma: no cover
        path = self.dir / "secret"
        private_file.create_private_file(path, b"x")
        sddl = private_file.read_file_sddl(path)
        print(f"DACL read back from the OS: {sddl!r}")
        self.assertIsNone(
            private_file.sddl_is_owner_only(sddl, private_file._current_user_sid())
        )
        # And the file is still usable by its owner.
        self.assertEqual(path.read_bytes(), b"x")


if __name__ == "__main__":
    unittest.main()


class SddlCheckTests(unittest.TestCase):
    """The structural DACL check itself, on every OS (pure string logic)."""

    SID = "S-1-5-21-1-2-3-1001"

    def test_accepts_owner_only_including_canonicalized_flags(self) -> None:
        for sddl in (f"D:P(A;;FA;;;{self.SID})", f"D:PAI(A;;FA;;;{self.SID})"):
            with self.subTest(sddl=sddl):
                self.assertIsNone(private_file.sddl_is_owner_only(sddl, self.SID))

    def test_rejects_every_permissive_shape(self) -> None:
        bad = {
            "inherits": f"D:(A;;FA;;;{self.SID})",
            "second ace": f"D:P(A;;FA;;;{self.SID})(A;;FR;;;BU)",
            "inherited ace": f"D:P(A;ID;FA;;;{self.SID})",
            "other user": "D:P(A;;FA;;;S-1-5-21-9-9-9-9)",
            "deny only": f"D:P(D;;FA;;;{self.SID})",
            "not a dacl": "garbage",
            "none": None,
        }
        for name, sddl in bad.items():
            with self.subTest(name=name):
                self.assertIsNotNone(private_file.sddl_is_owner_only(sddl, self.SID))


class AnalyticsSaltIsPrivateTests(unittest.TestCase):
    """The analytics pseudonym salt is the second secret; it goes through the same helper."""

    def test_salt_is_owner_only_and_stable(self) -> None:
        from agent_workflows import run_analytics_privacy as RAP

        with tempfile.TemporaryDirectory() as d:
            salt = RAP.load_or_create_salt(Path(d))
            path = RAP.salt_path(Path(d))
            self.assertTrue(salt)
            self.assertEqual(
                RAP.load_or_create_salt(Path(d)), salt, "the salt must be stable"
            )
            self.assertEqual(
                [p.name for p in Path(d).iterdir()], [path.name], "no tmp left behind"
            )
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            else:  # pragma: no cover - Windows
                self.assertIsNone(
                    private_file.sddl_is_owner_only(
                        private_file.read_file_sddl(path),
                        private_file._current_user_sid(),
                    )
                )
