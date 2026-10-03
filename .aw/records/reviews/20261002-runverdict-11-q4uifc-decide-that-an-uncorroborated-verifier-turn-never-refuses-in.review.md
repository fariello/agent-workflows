# Review: Decide that an uncorroborated verifier turn never refuses integration

- Subject-Id: q4uifc
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits.

Re-verified in this lane:

- Consumer census: `corroboration_verdict` / `corroboration_reason` / `corroboration_counts` / `corroborate_verifier_turn` are read only by `runner_shared.execute_item_core` (recorder), the `runner_shared` report renderer, `run_viewer` (`StepSummary` and its rendering), and `tests/test_verifier_corroboration.py`. No disposition, `verify_disp`, refusal or integration path reads them.
- F-06 re-driven: one `step_type: "subagent"` event plus one `git status` tool call against claim `python3 -m pytest tests/` returned `uncorroborated uncorroborated {'claimed': 1, 'observed': 1, 'matched': 0, 'delegations': 0, 'missing_command_text': 0}`.
- Authorities: GUIDING_PRINCIPLES P15 "WHAT NOT TO BUILD ... 'in case the agent lies'" present; `runner_shared` reason "3. A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE" present; spec `25kzda` Section 5.1 HONEST LIMIT "comparison that only ever makes a gate more permissive is not such a refusal" present.
- Corpus: `find .aw/records/runs -name "*-verification.json" | wc -l` = `0` (directory exists locally with only `analytics/`).
- `DECISIONS.md` tail is `### D158`; `sinhkj` is `graduated`; `iuhx9d` open; `e08ssu` pending; `bjx20r`, `btak7a`, `t18l64` executed.
- E-03 feasibility, measured in-process: a spy on `runner_shared.integration_is_earned` during the shipped equality test saw exactly ONE call, from the test body (`verify_disp='verified', suite_result=0`). `_drive_execute_turn` sets `self_finalize: False`, so `integration_gate_relevant` is false and the pipeline records no `integration_signal`. Mutating the pipeline call site to `verify_disp=(VERIFY_DISP_UNVERIFIED if item.get('corroboration_verdict') == 'uncorroborated' else verify_disp)`: shipped test PASS in all three arms; same drive with `self_finalize=True` and `driver_begin` stubbed to `(0, "ok")` recorded `integration_signal` `verifier` / `verifier-declined` / `verifier` (unmutated: `verifier` in all three). Without the `driver_begin` stub the item ends `fail-begin` ("pre-execution gate did NOT conform") and no verification runs.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Testing and verification (E); decision enforcement | plan E-03; `runner_shared.integration_is_earned(validate, verify_disp, suite_result)`; `tests/test_verifier_corroboration.py` `_drive_execute_turn` `"self_finalize": False` | E-03 as authored asserts `integration_is_earned` is identical across verdicts for a `verified` turn, but the predicate takes no corroboration input, so a test-side call is identical BY CONSTRUCTION and its mutation proof cannot go red for any refusal wired into the pipeline. The shipped test shares the blind spot (measured: integration-only mutation leaves it green). The plan's sole enforcement item would have pinned nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-03/Scope/Goal/F-07/Proposed changes/conventions rewritten: drive `execute_item_core` with self-finalize ON and `driver_begin` stubbed, assert pipeline-recorded `integration_signal` (non-`None`) identical across verdicts plus `status`/`verification_status`; mutation is the integration-only call-site refusal; V-03 also demands the shipped test stays green under it. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence accuracy | plan F-09 and Deferred `Carrier-Evidence: .aw/records/plans/pending/...t18l64...`; actual path `.aw/records/plans/executed/20261001-verremand-01-t18l64-...ipd.md` | `t18l64` is described as pending/to-review and its carrier path points at `pending/`, but it has been executed; a dangling carrier path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 and the Deferred entry now say executed; carrier path updated. |
| PR-003 | LOW | IN-SCOPE | Evidence accuracy | plan F-02 "does not exist in this worktree"; review lane `ls .aw/records/runs` shows `analytics/` | The runs directory can exist in a lane (created locally); the true property is zero verification outcomes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 reworded to "no verification outcomes" with the review measurement. E-01(b) already counts outcomes, so unchanged. |
| PR-004 | LOW | IN-SCOPE | Evidence currency | plan F-06 | Re-driven at review; result unchanged. Recorded for traceability only. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Noted in workflow history; no plan text change needed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should E-03 make the decision observable? | Drive real `execute_item_core` with self-finalize ON, `driver_begin` stubbed, assert recorded `integration_signal` | Keep test-side `integration_is_earned` call (cannot fail); extend shipped test in place (changes a shipped test's contract); spy on `integration_is_earned` args (closer to structure-pinning) | In-process mutation demonstration above; stub shape from `tests/test_suppress_narrowing.py` `mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok"))` | yes |
| D-2 | Is OQ-01's NO answer within reviewer/author authority without a maintainer prompt? | Accept as resolved | Escalate as blocking | GUIDING_PRINCIPLES P15 (`daexj1` OQ-02 ruling cited there); spec `25kzda` 5.1 HONEST LIMIT; decision changes no runtime behavior and is reversible by a new DECISIONS entry | yes |
