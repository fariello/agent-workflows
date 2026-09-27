from __future__ import annotations

import unittest


class LiftDriftScanGuardTests(unittest.TestCase):
    """Retired under IPD 96xtmi (source-guard cleanup).

    The AST drift scans pinning runner_shared.py source were deleted in favor of
    behavioral tests in tests/test_liftaudit_drift.py and type checking.
    """

    pass


if __name__ == "__main__":
    unittest.main()
