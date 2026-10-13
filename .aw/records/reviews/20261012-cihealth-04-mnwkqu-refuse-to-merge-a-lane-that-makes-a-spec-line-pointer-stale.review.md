# Review findings: plan mnwkqu

- Subject-Id: mnwkqu
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `bd4c7874e`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified:
- `spec_citations.stale_spec_anchors(repo_root, paths)` exists; `StaleSpecAnchor` fields are `file` (absolute), `line`, `id6`, `offset`, `enclosing_heading`, `validity`, with no cited-text field.
- `cli._run_check` `source_anchors` branch scans `agent_workflows`, `tools`, `tests`. `aw check specs --source-anchors` reports the one `check_engine.py` `pqsx96 :135` finding, which `fz3i3m` fixes.
- `runner_shared.integrate_lane_branch` calls `orchestrate_isolation.execute_merge_and_revalidate_gate` only under `if action_kind == INTEGRATION_ACTION_EXECUTE:`, returning `(False, tag_integration_cause(...), INTEGRATION_REFUSAL_CONFLICT)` on a non-pass.
- The only integration fix-it loop is the combined-red one in `runner_shared.execute_item_core` (`while ... read_integration_cause(integ_reason)[0] == INTEGRATION_CAUSE_GATE_COMBINED_RED ...`, `build_fix_it_notice("combined-red", ...)`, `resume_via_launcher`); hook-refused has its own. No generic path exists.
- Spec `25kzda` "5.5 Retry policy" lists group (a) "(12 members)" and a retry-class mapping table; `tests/test_retry_class_mapping.py` reads `TURN_RETRY_CLASSIFICATION`.
- Timing: `stale_spec_anchors` over the three roots took 2.16s real.
- `fz3i3m` is `approved` in `pending/`; backlog `5st6e5` carries `Blocks-Release: next`, which is inherited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Reachability | `runner_shared.execute_item_core` combined-red `while` keyed on `INTEGRATION_CAUSE_GATE_COMBINED_RED` | E-02 said to send the item to "the existing fix-it correction turn", but no such generic path exists: an integration refusal only gets a turn for combined-red or hook-refused. Without new code a held lane would end `fail-merge` with no turn, so V-02's demand for "the correction prompt text" was unreachable, and Goal ("until its agent fixes the pointer") was unmet. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-05/V-05: a send-back loop modeled on the combined-red loop, with its own counter, event and `build_fix_it_notice` prompt. E-02 now adds a typed cause `spec-anchor-new-stale` with its own terminal sentence. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness | `StaleSpecAnchor` fields; E-01 "key ... cited text or section" | The key named data the finding does not carry, and `file` is absolute, so lane and base findings (different roots) could never match and every finding would read as new. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 defines the key as relative path, id6, offset and the stripped citing line, read from each side's file. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `_handle_for` builds `WorktreeHandle(path=Path(worktree) if worktree else Path(""))` | "Run on the lane tree" fails on a preserved lane with no worktree, and a live tree can carry uncommitted files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 evaluates both sides at commits through temporary detached worktrees removed in `finally`; V-01 demands `git worktree list` proof of cleanup. |
| PR-004 | MEDIUM | IN-SCOPE | C. Operability / cost | Goal "about 5 seconds per merge"; measured 2.16s per side | Two full scans on every execute merge, with no short-circuit, and no rule on whether the check runs before or after the suite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 short-circuits when no spec or scanned `.py` changed. E-02 runs before the gate so a held lane spends no suite run. Goal and F-03 restated with the measurement. Test (h) added. |
| PR-005 | MEDIUM | IN-SCOPE | Spec sync | spec `25kzda` 5.5 "(12 members)"; `tests/test_retry_class_mapping.py` | "where it lists what lane integration checks" named no section, and adding a new group member would break the stated count and the classification table. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names Section "5.5 Retry policy" and classes the refusal under the existing member "missing expected artifact or failed deterministic check", adding one Notes sentence only. |
| PR-006 | LOW | UNDER-SCOPE | E. Tests | E-03 cases (a)-(f) | Exhaustion (the `fail-merge` end), the short-circuit, and the scan-root drift were untested. A pointer made stale only by main's later commits was unaddressed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added cases (g) and (h); E-01 shares the CLI's scan-root list. The merge-result case is deferred to `n7xlhm` with a reason. |
| PR-007 | LOW | UNDER-SCOPE | G. Execution contract | gate | The gate was missing the staged-set check, the no-`--no-verify` rule, the no-`git mv` rule, and the inherited release gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to the gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the fix-it turn come from? | A new send-back loop modeled on combined-red | Reuse the combined-red loop by tagging the refusal combined-red (mislabels the cause, prints "suite was RED"); have no turn (contradicts the maintainer-stated goal) | `execute_item_core` combined-red loop; plan Goal | yes |
| D-2 | Run the anchor check before or after the merge-and-revalidate gate? | Before | After (a held lane pays a full suite run first) | F-03 timings; `integrate_lane_branch` structure | yes |
| D-3 | Compare against the lane's base or the merge result? | Lane base | Merge result (would block a lane for a peer's change, contradicting OQ-01) | OQ-01 resolution | yes |
| D-4 | New retry-class member in spec 5.5? | No; an instance of "missing expected artifact or failed deterministic check" | New member (changes the stated "12 members" count and `TURN_RETRY_CLASSIFICATION`) | spec `25kzda` 5.5 text; `tests/test_retry_class_mapping.py` | yes |
