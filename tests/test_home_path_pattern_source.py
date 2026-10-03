"""Behavioral tests pinning derivation and agreement for home-path detection patterns.

Validates that:
- `agent_schema` and `leak_sanitizer` derive their home-path detection rules directly
  from `home_path_patterns` (P8 single source of truth).
- Both consumers are sensitive to upstream changes in `home_path_patterns` (derivation sensitivity).
- The fused detector agrees identically with the union of the three individual rules across the F-02 corpus.
- Each rule's required-substring prefilter is coherent with its regex pattern body (F-06).
- Rule names and ordering in `_FAIL_PATTERNS` are preserved.
- Planted paths are detected end-to-end through `build_ruleset` and `scan_text`.

Leak tokens and paths are assembled from fragments at runtime so this test file contains
no literal leak tokens (self-clean, requiring no sanitizer exemption).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import agent_workflows.agent_schema as agent_schema
import agent_workflows.home_path_patterns as home_path_patterns
import agent_workflows.leak_sanitizer as leak_sanitizer


def _frag(*parts: str) -> str:
    """Helper to assemble test path prefixes without containing literal leak strings."""
    return "".join(parts)


_H_ROOT = _frag("/ho", "me/")
_U_ROOT = _frag("/Use", "rs/")
_W_BS_ROOT = _frag("C:\\Use", "rs\\")
_W_FS_ROOT = _frag("C:/Use", "rs/")
_W_D_ROOT = _frag("D:\\Use", "rs\\")

F02_CORPUS: list[str] = [
    # 1. POSIX real
    _H_ROOT + "bob/project",
    # 2. macOS real
    _U_ROOT + "bob/project",
    # 3. Windows backslash real
    _W_BS_ROOT + "bob\\project",
    # 4. Windows forward slash real
    _W_FS_ROOT + "bob/project",
    # 5. Windows D: drive real
    _W_D_ROOT + "bob",
    # 6. Exemption /home/u/
    _H_ROOT + "u/src",
    # 7. Exemption /home/alice/
    _H_ROOT + "alice/data",
    # 8. Exemption /home/user/
    _H_ROOT + "user/docs",
    # 9. Exemption /home/USER/
    _H_ROOT + "USER/test",
    # 10. Exemption /home/<
    _H_ROOT + "<username>/file",
    # 11. Exemption /Users/<
    _U_ROOT + "<username>/file",
    # 12. Exemption /Users/user/
    _U_ROOT + "user/file",
    # 13. Exemption C:\\Users\\<user>\\
    _W_BS_ROOT + "<user>\\file",
    # 14. Exemption C:/Users/<user>/
    _W_FS_ROOT + "<user>/file",
    # 15. Embedded POSIX 1 (/opt + /home/<name>)
    "/opt" + _H_ROOT + "bob",
    # 16. Embedded POSIX 2 (tokens + /home/<name>)
    "tokens" + _H_ROOT + "bob",
    # 17. Embedded Windows (prefix + C:\\Users\\<name> + suffix)
    "prefix " + _W_BS_ROOT + "bob suffix",
    # 18. Non-path 1
    "/var/log/syslog",
    # 19. Non-path 2
    "https://example.com/api",
]


def test_derivation_identity() -> None:
    """Assert agent_schema and leak_sanitizer patterns equal the home_path_patterns datum."""
    assert (
        agent_schema._HOME_PATH_RE.pattern
        == home_path_patterns.fused_home_path_pattern()
    )
    assert agent_schema._HOME_PATH_RE.flags == 32

    for name, (body, prefilters) in home_path_patterns.HOME_PATH_RULES.items():
        assert leak_sanitizer._FAIL_PATTERNS[name].pattern == body
        assert leak_sanitizer._FAIL_PATTERNS[name].flags == 32
        assert leak_sanitizer._REQUIRED_RULE_SUBSTRINGS[name] == prefilters


def test_cross_module_agreement_corpus() -> None:
    """Assert zero disagreements between the fused detector and the three rule union over F-02 corpus."""
    home_rules = [
        leak_sanitizer._FAIL_PATTERNS["home-path"],
        leak_sanitizer._FAIL_PATTERNS["users-path"],
        leak_sanitizer._FAIL_PATTERNS["windows-home"],
    ]

    disagreements = []
    for case in F02_CORPUS:
        fused_hit = bool(agent_schema._HOME_PATH_RE.search(case))
        rules_hit = any(bool(r.search(case)) for r in home_rules)
        if fused_hit != rules_hit:
            disagreements.append((case, fused_hit, rules_hit))

    assert len(F02_CORPUS) == 19
    assert not disagreements, f"Disagreements across corpus: {disagreements}"


@pytest.mark.parametrize(
    "target_class",
    ["home-path", "users-path", "windows-home"],
)
def test_derivation_sensitivity_in_subprocess(target_class: str) -> None:
    """Assert that mutating HOME_PATH_RULES in a fresh interpreter propagates to both consumers.

    If either agent_schema or leak_sanitizer were to re-fork to an independent literal,
    this subprocess test fails because the mutated sentinel body and prefilter would not be seen.
    """
    script = f"""
import sys
import agent_workflows.home_path_patterns as h

sentinel_body = r"SENTINEL_BODY_{target_class}"
sentinel_prefilter = ("SENTINEL_PREFILTER_{target_class}",)

h.HOME_PATH_RULES["{target_class}"] = (sentinel_body, sentinel_prefilter)

import agent_workflows.agent_schema as s
import agent_workflows.leak_sanitizer as l

assert sentinel_body in s._HOME_PATH_RE.pattern, (
    f"agent_schema._HOME_PATH_RE did not pick up mutated pattern for {target_class}: "
    f"{{s._HOME_PATH_RE.pattern!r}}"
)
assert l._FAIL_PATTERNS["{target_class}"].pattern == sentinel_body, (
    f"leak_sanitizer._FAIL_PATTERNS[{target_class!r}] did not pick up mutated pattern: "
    f"{{l._FAIL_PATTERNS['{target_class}'].pattern!r}}"
)
assert l._REQUIRED_RULE_SUBSTRINGS["{target_class}"] == sentinel_prefilter, (
    f"leak_sanitizer._REQUIRED_RULE_SUBSTRINGS[{target_class!r}] did not pick up mutated prefilter: "
    f"{{l._REQUIRED_RULE_SUBSTRINGS['{target_class}']!r}}"
)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Derivation sensitivity check failed for {target_class}:\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )


def test_prefilter_coherence() -> None:
    """Assert each required substring prefilter is a literal substring of its rule pattern body (F-06)."""
    for name, (body, prefilters) in home_path_patterns.HOME_PATH_RULES.items():
        assert prefilters, f"Rule {name} has empty prefilters"
        for prefilter in prefilters:
            assert (
                prefilter in body
            ), f"Prefilter {prefilter!r} is not a substring of pattern body for rule {name!r}: {body!r}"


def test_rule_name_and_order_preservation() -> None:
    """Assert the first three fail rules remain the home rules in order, and historical names persist."""
    first_three = list(leak_sanitizer._FAIL_PATTERNS.keys())[:3]
    assert first_three == ["home-path", "users-path", "windows-home"]

    historical_names = [
        "home-path",
        "users-path",
        "windows-home",
        "vc-home",
        "private-repo",
        "other-account",
        "session-id",
        "handle",
    ]
    for name in historical_names:
        assert name in leak_sanitizer._FAIL_PATTERNS, f"Missing historical rule: {name}"


def test_e2e_detection_of_planted_paths() -> None:
    """Assert build_ruleset and scan_text detect planted paths across all three home classes."""
    ruleset = leak_sanitizer.build_ruleset(Path("."))

    # POSIX planted path
    planted_posix = _H_ROOT + "planted_usr_99/src/code.py"
    findings_posix = leak_sanitizer.scan_text(planted_posix, "dummy.txt", ruleset)
    assert any(
        f.rule == "home-path" and f.severity == "fail" for f in findings_posix
    ), f"Expected home-path finding for POSIX planted path, got: {findings_posix}"

    # macOS planted path
    planted_mac = _U_ROOT + "planted_usr_99/src/code.py"
    findings_mac = leak_sanitizer.scan_text(planted_mac, "dummy.txt", ruleset)
    assert any(
        f.rule == "users-path" and f.severity == "fail" for f in findings_mac
    ), f"Expected users-path finding for macOS planted path, got: {findings_mac}"

    # Windows backslash planted path
    planted_win_bs = _W_BS_ROOT + "planted_usr_99\\src\\code.py"
    findings_win_bs = leak_sanitizer.scan_text(planted_win_bs, "dummy.txt", ruleset)
    assert any(
        f.rule == "windows-home" and f.severity == "fail" for f in findings_win_bs
    ), f"Expected windows-home finding for Windows backslash path, got: {findings_win_bs}"

    # Windows forward slash planted path
    planted_win_fs = _W_FS_ROOT + "planted_usr_99/src/code.py"
    findings_win_fs = leak_sanitizer.scan_text(planted_win_fs, "dummy.txt", ruleset)
    assert any(
        f.rule == "windows-home" and f.severity == "fail" for f in findings_win_fs
    ), f"Expected windows-home finding for Windows forward slash path, got: {findings_win_fs}"
