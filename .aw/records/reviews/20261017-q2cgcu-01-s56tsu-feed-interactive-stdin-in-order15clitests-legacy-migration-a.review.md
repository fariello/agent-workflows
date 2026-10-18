# Review findings: plan s56tsu

- Subject-Id: s56tsu
- Subject-Type: ipd
- Reviewed-At: 2026-10-18
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `9764d3c1c`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `q2cgcu`, Order 1), test-only, one declared path.

Verified in the lane (scratch test `tests/test_zz_probe_s56tsu_tmp.py`, removed afterwards; `git status` clean apart from the plan):
- Current quarantined test: `1 xpassed` in 5 of 5 runs at `-n 4` (`-m "slow or not slow"`); the class runs `3 passed, 2 xpassed`.
- Spy on `builtins.input` with `_ask_policy` mocked True:
  - current `isatty` mock: code 0, prompts `Keep current policy and proceed? [Y/n/review]`, `Proceed and install into <tmp>? [Y/n]`, `Would you like the installer to commit these changes? [Y/n]` (all EOF on ambient `/dev/null`).
  - `mock.patch("sys.stdin", io.StringIO("\n\n"))`: code 0, exactly the first two prompts; `.aw/system/workflows/index.md` True, `.aw/system/VERSION` True, `.agents/workflows` gone.
  - `io.StringIO("")`: identical outcome (defaults on EOF).
- `tests/test_cli.py:29` `pytestmark = pytest.mark.slow`; `io` and `mock` imported at module top (lines 14, 22).
- Mechanism of skipping the commit prompt: `engine.is_interactive_session` -> `term.is_interactive()`, which is False for a non-TTY StringIO stdin; the cli/wizard helpers instead accept `isinstance(sys.stdin, io.StringIO)`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence (root cause claim) | `tests/__init__.py` Interactive-prompt guard; probe XPASS 5/5 at `-n 4` | The plan asserts the test reads pytest's captured stdin and hangs; in this suite stdin is `/dev/null`, every prompt hits EOF, and the test passes. The fix is sound but the cause was overclaimed, and the plan missed a third prompt (`engine` commit prompt). | all Low | FIXED | Concern rewritten with measured behavior, "cause unknown", and the third prompt; F-03 records the probe; Scope check adds recurrence path. |
| PR-002 | MEDIUM | UNDER-SCOPE | Testing (outcome not asserted) | `tests/test_cli.py` `test_install_legacy_repo_interactive_accept_migrates_to_aw`: `code` unused | The test never asserts the exit code or that the legacy tree was migrated away, so a failing install leaving `.aw/system` files would still pass. | all Low | FIXED | E-01 adds `assertEqual(code, 0, out)` and `.agents/workflows` absence (both measured true under the new stdin); F-04; V-01 demands them in the diff. |
| PR-003 | LOW | IN-SCOPE | Validation | `tests/test_cli.py:29` module `slow` mark; V-02 demanded `1 passed` from `-v` without `-o addopts=""` | A single run cannot show a flake is gone; the bare gate never collects this module; `-v` with the default `-q` addopts and no `-rA`/`-rxX` does not reliably show PASSED vs XPASS. | all Low | FIXED | E-02/V-02: `-rA` target run, five `-n 4 -rxX` class repeats, bare gate labelled no-regression. |
| PR-004 | LOW | IN-SCOPE | Execution contract | gate paragraph | Gate lacked the staged-set check and the behavior-not-structure test rule; no lint evidence for the edited file. | all Low | FIXED | Gate amended; V-01 requires pasted `ruff check tests/test_cli.py`. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep `io.StringIO("\n\n")` (OQ-01) rather than empty stdin or patching `builtins.input`? | Keep `"\n\n"` | `io.StringIO("")` (same outcome via EOF defaults); `builtins.input` patch | probe: exactly two prompts consume the two newlines, so the answers are explicit; repo convention in `tests/test_installer.py` | yes |
| D-2 | Proceed although the flake does not reproduce? | Proceed; un-quarantine and record cause unknown | Keep quarantined until reproduced | backlog `q2cgcu` asks for un-quarantine; the change removes an ambient dependency; a recurrence turns red visibly | yes |
