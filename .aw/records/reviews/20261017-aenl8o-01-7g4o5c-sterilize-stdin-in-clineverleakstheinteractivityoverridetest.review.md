# Review findings: plan 7g4o5c

- Subject-Id: 7g4o5c
- Subject-Type: ipd
- Reviewed-At: 2026-10-18
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `08fa69666`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `aenl8o`, Order 1), test-only, one declared path.

Verified in the lane (scratch test file `tests/test_zz_probe_7g4o5c_tmp.py`, removed afterwards; no production or test file left edited; `git status` clean):
- `python3 -c "import contextlib; print(hasattr(contextlib,'redirect_stdin'))"` on Python 3.14.6: `False`.
- Ambient stdin in a pytest test: `stdin type: TextIOWrapper fd0: /dev/null`; `input()` raised `EOFError` (serial and `-n 2`). Source: `tests/__init__.py` Interactive-prompt guard.
- Unpatched `cli.main(["--interactive"])` in a test: `configured: False`, `rc 130`, override after `None`.
- Current quarantined test: `1 xpassed` in 3 of 3 runs at `-n 4`; also `1 xpassed` with `-s` and a live pipe on stdin.
- With `mock.patch("sys.stdin", io.StringIO(""))`: `None ['--interactive'] rc 130 after None`; `None ['--no-interactive'] rc 0 after None`; `False ['--interactive'] rc 130 after False`; `True ['--no-interactive'] rc 0 after True`. Timings: `--interactive` 0.3s; bare `--no-interactive` 5.46s and 5.62s.
- Bare `python3 -m pytest --collect-only -q | grep -c test_term.py`: `0` (no `core` marker in the module).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (named mechanism does not exist) | plan E-01, V-01, conventions "`contextlib.redirect_stdin(io.StringIO(""))`"; probe `hasattr(contextlib, "redirect_stdin")` -> `False` | The required mechanism is not in the standard library, so E-01 as written raises `AttributeError` and V-01 demands an impossible diff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01/conventions now require `mock.patch("sys.stdin", io.StringIO(""))`, the repo's existing convention (`tests/test_installer.py` `test_prompt_case_r_yes_flag_never_prompts_and_removes`), demonstrated by probe (F8). |
| PR-002 | MEDIUM | IN-SCOPE | Evidence (root-cause claim unverified) | Concern "captured stdin either raises `OSError` ... or blocks"; `tests/__init__.py` reopens stdin on `/dev/null`; probe shows `EOFError` and XPASS 3/3 | The stated flake mechanism does not hold in this suite: pytest's `DontReadFromInput` is not what the test sees, and the test currently XPASSes. The fix is still right (own the stdin) but the plan overclaimed the cause. | all Low | FIXED | Concern rewritten to record measured behavior and "cause unknown"; F7 added; Scope check gives a recurrence path (new backlog item, not re-quarantine). |
| PR-003 | MEDIUM | UNDER-SCOPE | Testing (outcome not asserted) | plan E-01 Expected outcome "returns 130"; test body asserts only override state | Nothing asserted the bare `--interactive` exit code, so the stdin fix could regress (e.g. a raise swallowed or a different path) unnoticed. | all Low | FIXED | E-02 now asserts `cli.main(["--interactive"])` returns 130 and restores `None`, outer `False`, and outer `True`. |
| PR-004 | LOW | OVER-SCOPE | KISS / cost | plan E-02 item (1) "`--no-interactive` with no verb"; probe 5.46s and 5.62s per call | Bare `--no-interactive` never reads stdin, so it does not test this concern, and it would add about 11s to a non-slow-allowlisted test. | all Low | FIXED | Removed from E-02; recorded under Deferred with reason. |
| PR-005 | LOW | IN-SCOPE | Validation (gate does not cover the test; flake not stressed) | conftest.py `pytest_collection_modifyitems` (core filter); collect-only count `0` | Bare `python3 -m pytest` never runs `tests/test_term.py`, so it is not evidence for this test; and a single run cannot show a flake is gone. | all Low | FIXED | E-03/V-03 add five concurrent `-n 6` repeats with `-rxX`, a full-module run at `-n 6`, and label the bare gate as no-regression only. |
| PR-006 | LOW | UNDER-SCOPE | Executability (lint hook) | `tests/test_term.py` line 15 `import pytest`, only use is the xfail at line 678; `.pre-commit-config.yaml` ruff hook | Removing the decorator leaves `import pytest` unused, so the ruff pre-commit hook would reject the commit. | all Low | FIXED | E-01 removes the import if unused; V-01 requires pasted `ruff check tests/test_term.py`. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which mechanism sterilizes stdin? | `mock.patch("sys.stdin", io.StringIO(""))` | `contextlib.redirect_stdin` (does not exist); a custom context manager; relying on the ambient `/dev/null` guard | probe F8; `tests/test_installer.py` existing usage | yes |
| D-2 | Keep bare `--no-interactive` coverage? | Drop it | Keep it and slow-allowlist the test | measured 5.46s/5.62s per call; it never reads stdin | yes |
| D-3 | Proceed although the flake does not reproduce? | Proceed; un-quarantine and record cause unknown | Leave the test quarantined until reproduced | backlog `aenl8o` asks for un-quarantine; the fix removes an ambient dependency regardless; a recurrence turns red visibly | yes |
