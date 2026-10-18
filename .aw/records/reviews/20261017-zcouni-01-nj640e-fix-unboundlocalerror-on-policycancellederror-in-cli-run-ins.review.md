# Review findings: plan nj640e

- Subject-Id: nj640e
- Subject-Type: ipd
- Reviewed-At: 2026-10-18
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `08fa69666`. Plan committed and byte-identical to the
sealed lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`, 0
findings; after revisions `--phase review-finalize --agent`: `clean`, 0 findings. Not an orchestrator.

Verified at review with scratch scripts under the gitignored `.aw/state/scratch-nj640e/` (not committed):
- Bug reproduced: declined legacy repo, `builtins.input` raising `KeyboardInterrupt` at the final
  confirmation -> `UnboundLocalError: cannot access local variable 'PolicyCancelledError' where it is
  not associated with a value`.
- Same masking for a non-cancel error: pytest's `DontReadFromInput` as stdin -> `UnboundLocalError`
  with `__context__` `OSError: pytest: reading from stdin while output is captured!`.
- Fix prototyped by exec'ing a copy of `_run_install` with the E-01 edit: KeyboardInterrupt case
  `EXIT 1`, cancelled line present, `.agents/workflows/index.md` not written; OSError case propagates
  `OSError`; non-legacy cancellation still `EXIT 1` with the cancelled line; `io.StringIO("\n")` case
  `EXIT 0`, legacy VERSION kept, no `.aw/system`.
- The quarantined test currently XPASSes: `3 passed, 2 xpassed` in each of 3 runs at `-n 4`; a spy
  showed stdin is the `tests/__init__.py` `/dev/null` guard stream, `_confirm_install` returns True.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (honest diagnosis) | `tests/__init__.py` "Interactive-prompt guard" `sys.stdin = open(os.devnull, "r")`; review runs `3 passed, 2 xpassed` | The plan asserted the test crashes on captured stdin; measured, it XPASSes because ambient stdin is the `/dev/null` guard. The flake trigger is not reproduced, so the plan overstated its cause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-02 now state the measured behavior and "cause unknown", and say to file a new item rather than re-quarantine if it recurs. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (test detects the bug) | `agent_workflows/cli.py` `_confirm_install` `except KeyboardInterrupt:` ... `raise PolicyCancelledError(`; `tests/test_cli.py` `InstallAtomicWizardTests.test_install_ctrl_c_preset_prompt_writes_zero_files_and_skips_cleanly` | E-03 left the injection open ("e.g."); mocking `_confirm_install` would bypass the real translation, and no assertion that nothing was written or that it fails pre-fix was required. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now drives the real `_confirm_install` via `builtins.input` raising `KeyboardInterrupt` (existing precedent), asserts code 1, cancelled line, no FAIL, no `index.md`; V-03 demands a pre-change run failing with `UnboundLocalError`. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric D (masked errors) | scratch reproduction: `UnboundLocalError` with `__context__` `OSError` | The unbound handler also masks every unrelated exception from the final-gate `try` on the legacy path; the plan did not name this effect or what changes after the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-04 and the post-fix propagation behavior to E-01's Expected outcome. |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric G (validation completeness) | `tests/test_cli.py` `pytestmark = pytest.mark.slow`; plan had no V-item for the class/core runs | There was no E/V item for the regression runs listed under Required tests, so the class run and core gate were never evidenced; the slow-marker reason was misattributed to `slow_allowlist.txt`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-04/V-04 (Order15 + InstallAtomicWizard classes, three `-n 4` runs, bare gate); corrected the convention note. |
| PR-005 | LOW | IN-SCOPE | Rubric C (one binding), E (outcome assertions) | `agent_workflows/cli.py` `_run_install` inner `from agent_workflows.install_wizard import (` list | E-01 kept a second redundant binding inside `if not kept_legacy:`; E-02 asserted no exit code and no absence of `.aw/system`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 removes the inner import entry; E-02 adds `assertEqual(code, 0, out)` and `.aw/system` absence, and is fenced off the `s56tsu` sibling. |
| PR-006 | LOW | IN-SCOPE | Carrier, traceability | `.aw/records/plans/pending/20261017-q2cgcu-01-s56tsu-*.ipd.md` `- Id: s56tsu` | The deferred sibling test used `Carrier-Declined` although a live carrier plan exists; findings had no evidence column; no invariant map; sibling call sites not checked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed to `- Carrier: s56tsu`; added an evidence column, invariants I-1..I-3, and a verified sibling-site sweep in Scope check. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the regression test inject the cancellation? | `builtins.input` raising `KeyboardInterrupt`, through the real `_confirm_install` | mock `_confirm_install` to raise `PolicyCancelledError` (skips the real translation) | `tests/test_cli.py` `InstallAtomicWizardTests.test_install_ctrl_c_preset_prompt_writes_zero_files_and_skips_cleanly`; scratch reproduction | yes |
| D-2 | Keep the inner `PolicyCancelledError` import too? | Remove it; one binding at function entry | keep both (harmless but redundant) | scratch prototype with the removal passed every case | yes |
| D-3 | Carrier for the sibling quarantined test? | `- Carrier: s56tsu` | keep `Carrier-Declined` | `s56tsu` exists in `pending/`, `Status: reviewed`, and owns that test | yes |
