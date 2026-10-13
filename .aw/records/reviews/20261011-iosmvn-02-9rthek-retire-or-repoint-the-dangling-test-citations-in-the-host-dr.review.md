# Review findings: plan 9rthek

- Subject-Id: 9rthek
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `3e328494b`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified:
- The Set measurement command (verbatim from `yuhl6o`) over the six source files prints the same 19 hits as Findings S-01..S-19, `UNRETIRED 19`.
- The AST-equivalence command against `HEAD` prints `AST-DIFFER []` on the unchanged files, so the E-04 tool works.
- Enclosing symbols match: `finalize_orchestrator`, `terminate_process`, `run_queue`, `main` (oc); `run_agy_turn`, `build_parser` (agy); the remaining sites are module-level comments.
- S-14: `git show 19313eed^:tests/test_lane_permission_posture.py` has `TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser` (behavioral, calls `agy_runipd.build_parser()`); `rg -n dangerously_skip_permissions tests/` is empty.
- S-17: the deleted `test_ledger_status_vocabulary_covers_both_drivers` asserted `TERMINAL_STATES - KNOWN_ITEM_STATUSES == set()`; live `tests/test_retry_class_mapping.py::test_vocabulary_coverage_is_one_directional` reads both sets but asserts a different property (coverage by the retry table), so it is not a REPOINT candidate. That is the executor's E-02 call; noted, not a finding.
- S-18: `tests/test_artifact_audit.py` is live but its `assertIs(run_viewer.StepArtifactAudit, artifact_audit.ArtifactAudit)` test was removed by `19313eed7`, and the live file never imports `run_viewer`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Honest documentation | `agent_workflows/run_viewer.py:541` "asserted by object identity in `tests/test_artifact_audit.py`"; `git show 19313eed7 -- tests/test_artifact_audit.py` removes `test_run_viewer_audit_type_is_the_shared_module_object` | The S-18 sentence carries a second false enforcement claim about a LIVE file, which the measurement cannot detect. Editing only the `test_runner_refork_guard.py` half would leave a false claim in the same sentence and pass `UNRETIRED 0`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Findings note on S-18; E-03 and V-03 now require that claim corrected and quoted. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-02 "19 (plus deltas) dispositioned rows" | The bar was the authoring count of a drifting population. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 bar is now one row per E-01 hit, re-derived; 19 kept as context. Findings records the review-HEAD re-measurement. |
| PR-003 | MEDIUM | IN-SCOPE | E. Evidence sufficiency | E-03 expected outcome; V-03 | `UNRETIRED 0` proves only that `19313eed` is within 3 lines, not that the rewritten text is true; V-03 did not demand the edited passages. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires each passage to be true at HEAD and forbids non-prose changes; V-03 demands each edited passage quoted, including both halves of twin pairs. |
| PR-004 | LOW | IN-SCOPE | Evidence | `agy_runipd.run_agy_turn` comment; deleted `test_lane_permission_posture.py` | S-14 left the disposition fully open although review can settle the evidence: the guard was behavioral and no live test asserts the default. Also the "Do NOT harden" instruction must survive the edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Findings note records the evidence; E-02 expects RETIRE-UNGUARDED unless a live guard is found; E-03 keeps the R4.1c instruction. |
| PR-005 | LOW | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status line, scope-fence declaration, the MUST-paste honesty rule, staged-set verification, the concurrent-edit stop, runner/executor ownership of begin/finalize, and the no-`git mv` rule; E-04 had no rule for a pre-existing suite failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the sibling `65d5zf` shape; E-04/V-04 require a pre-existence re-run for any failure. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the S-18 `test_artifact_audit.py` claim be fixed here though the measurement does not flag it? | Yes, same sentence, same file, in Scope-Paths | Leave it for `ellenm` (it audits only measured hits, so it would be lost) | `git show 19313eed7 -- tests/test_artifact_audit.py`; plan Goal "make every residual citation truthful" | yes |
| D-2 | Pre-decide S-14's disposition? | No; record evidence and expected disposition, leave the call to E-02 | Hard-code RETIRE-UNGUARDED (would skip the execution-time re-check) | `rg -n dangerously_skip_permissions tests/` empty at `3e328494b` | yes |
