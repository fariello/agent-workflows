# Review findings: plan ckxypc

- Subject-Id: ckxypc
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `7abf0ad6c`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; after revision
`author` and `review-finalize` both `clean`. Not an orchestrator, so S407/S408 do not apply.

Verified: `runner_shared.handle_review_orchestrator_readiness` (`if exit_code != 0: return disposition`; returns
`disposition` for non-IPD, missing plan, parse failure and `Kind != "orchestrator"`; its own `return "fail-gate"`
on exhausted correction budget); `reconcile_disposition` returns `fail-gate` for a review on nonzero exit; two
`if review_orch_disp == "fail-gate":` call sites in `execute_item_core`; `record_lane_preserved` with the quoted
reason and `("review-orchestrator-failed",)`; `render_stream.render_event` error branch; `agy_runipd.render_agy_event`
`result` record; `render_run_summary_table` `Diagnostics / Blocked Items:` block; `lane_containment.format_preserved_lanes`;
`attempt["log"] = str(attempt_log_path(...))`. Plan `ytas91` is `to-review` and also edits `execute_item_core`.

Measured at review:

```text
$ python3 - (render_event on the F-01 error event, Palette(False), use_unicode=False)
! diag:  ContentFilterError: The response was blocked by the provider's content filter
```

The session file cited by F-01 is under the gitignored `.aw/records/runs/` and is not present in this lane; the
fixture is to be written from F-01's quoted lines (not a missing input for review: the quoted content suffices).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric C (duplicate path) | `render_stream.render_event` `if etype == "error":` branch decodes `error.name` / `error.data.message`; E-02 "Add a pure parser" | E-02 would add a second decoder for the exact event `render_event` already decodes, so the summary and the live stream could disagree on the same event. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 factors the extraction into one helper used by `render_event` (output byte-identical, measured line pinned) plus a log-scan helper. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric A/D | Two `if review_orch_disp == "fail-gate":` sites in `execute_item_core` (lane branch and `tree=repo` branch) | E-01 named one site; the non-isolated branch has the same conflation. Inferring "evaluated" in the caller by re-reading `Kind` would duplicate the handler's plan-file resolution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Handler returns `(disposition, evaluated, refused)`; both sites updated; case (d) (orchestrator, exit 1) added to tests. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric G (dependency) | E-01 "the host error from E-02 when present", `Depends on: none` | E-01 consumes E-02's field but declared no dependency, and gave no reason codes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 depends on E-02; three named codes added in `lane_containment` (now in Scope-Paths). |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (feasibility) | `agy_runipd.render_agy_event` (`event == "result"`, `result.status`, `result.error`); E-03 "include it in the `--agent` run record" | The agy failure shape was unstated ("equivalent, or none"), and the run has no `--agent` record to extend. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the agy `result` mapping; E-03 uses `state.json` as the machine surface and the existing Diagnostics block and shared `write_report`. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric B (untrusted text) | Provider-authored message reaches summary and report | Unbounded, possibly multi-line provider text written to operator surfaces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bounded to one line (name 80, message 300) with `_one_line`, as `render_event` already does; tested. |
| PR-006 | LOW | IN-SCOPE | Evidence feasibility | `.aw/.gitignore` `records/runs/`; E-02 "real session file ... copied into a fixture" | The cited run directory is not available in a lane. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fixture written from F-01's quoted lines; path declared in Scope-Paths. |
| PR-007 | LOW | UNDER-SCOPE | Rubric G (execution contract, evidence) | Gate (one line); V-01..V-04; OQ-01 `Owner: this plan` | Gate lacked invariants, staged-set check, scope fence as declaration, finalize ownership, and `ytas91` coordination; V-items lacked unchanged-output and disposition checks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract; V-items demand byte-identical no-error output and unchanged dispositions; OQ-01 owner set to plan author. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does the caller know readiness actually refused? | Handler returns an explicit `(disposition, evaluated, refused)`. | Caller re-reads `Kind`. REJECTED: duplicates plan-file resolution. Compare dispositions. REJECTED: equal in the failed case. | `handle_review_orchestrator_readiness` early returns | yes |
| D-2 | Where does the error decoding live? | One helper in `render_stream`, shared with `render_event`. | New parser module. REJECTED: second decoder. | `render_event` error branch | yes |
| D-3 | What is the machine-readable surface? | Attempt/item field in `state.json`. | New `--agent` run record. REJECTED: none exists; out of scope. | `oc_runipd` CLI has no run-level agent record | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
