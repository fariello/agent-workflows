# Review findings: plan kht4vk

- Subject-Id: kht4vk
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `bad917edc` in an isolated review lane. The plan was committed and unchanged (lane input sha256 `c55f0ac1...` matches the tracked file), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review. After revisions the first `--phase review-finalize` reported `IPD-S408` (coverage fingerprint stale after the edits); see the coverage attempt log below. The second run was clean.

Re-verified:
- Children `0owirm` (reviewed, go-pending-approval, `Blocks-Release: next`) and `s95x79` (to-review) exist in `plans/pending/` and match the child table.
- All ten items are in `backlog/open/` (`h0tiaw` also has a `graduated/` sibling file `2wowfy`, a different id6).
- `vy20et` spec carrier `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` reads `- Status: approved`, `- From-Backlog: vy20et`.
- `run_selection_policy._BACKLOG_ACTIONS["open"] = ACTION_PLAN`; `runner_shared.evaluate_backlog_close` "this run executed none of its carriers, so the close was not earned"; `production_checks.backlog_graduate_count` "[BACKLOG-GRADUATE-COUNT] ... produced 0 linked IPDs" / "linking a different item or none"; commit `02bfc7618` "reopen(backlog): reopen 13 backlog items and record note on h0tiaw".
- Cause 2 commits: `1feee61ca` (lane base, merge-base of `aw/lane/2rm0gz`) contains `jykyqb`, `ml7b9e`; `97959e3fa` contains neither. `8538be828` (merge-base of `aw/lane/iosmvn`) contains `k6clui`; `c56c5cf0b` does not. `aw/lane/2rm0gz` diff vs base is one plan (`hdep9j`); `aw/lane/iosmvn` adds five `iosmvn` plans. None of those plans is on HEAD.
- `aw lanes list`: both lanes "keep: no run record". `runner_shared.allocate_isolation_worktree` docstring: attempt-scoped lane "when the existing lane holds work"; `runner_shared.integrate_stranded_lanes` selects from the current run's `state`.
- `check_engine.evaluate_durable_carrier` on the plan: `check.ipd-uncarried-obligation` (error), "2 obligation(s) name no durable carrier: deferred row 1, deferred row 2".
- Release `f33nrj` (2.0.0) is the single `planned` release; child `0owirm` carries `Blocks-Release: next`, the orchestrator did not.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / cross-plan consistency | `.aw/records/plans/pending/20261012-gradfix-01-0owirm-close-a-backlog-item-whose-carriers-are-all-executed-instead.ipd.md` F-01, E-07, Deferred "Closing `vy20et`"; spec `89xjll` `- Status: approved` | Goal, E-01 Expected outcome, Completion criteria and V-01 required all eight Cause-1 items (including `vy20et`) under `backlog/done/`. The reviewed child explicitly does NOT close `vy20et` because its spec carrier is not `implemented`, so E-01/V-01 were unsatisfiable and would have blocked retirement or forced a false close. They also used a live-artifact count as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal, E-01, Completion criteria and V-01 now require the property (every item `0owirm` reports `COMPLETE` closed, every `NOT_COMPLETE` item left `open` with its reason), re-derived from `0owirm`'s recorded evidence; the eight-item list is context only. |
| PR-002 | MEDIUM | UNDER-SCOPE | G. Honesty / follow-up | `0owirm` Deferred "Closing `vy20et`"; `run_selection_policy._BACKLOG_ACTIONS["open"]`; `production_checks.backlog_graduate_count` | Under-scope claimed every failure is fixed, but `vy20et` stays `open`, is dispatched again, and can fail `BACKLOG-GRADUATE-COUNT` again if the agent again finds nothing to plan. The residual recurrence was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Deferred row stating the consequence, carried by `- Carrier: vy20et` (open backlog item); Scope check updated. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness / evidence | `runner_shared.allocate_isolation_worktree` docstring; `runner_shared.integrate_stranded_lanes`; `aw lanes list` "keep: no run record" | Goal said the concurrency victims' "lanes hold correct plans that graduate on the next run". The next run does not reuse those lanes: allocation attempt-scopes a new lane when the old one holds work, and stranded-lane integration only covers the current run's state. The items are re-graduated from scratch; the old lanes are orphaned evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal corrected; Deferred row added for the two preserved lanes with `Carrier-Declined` (re-graduation loses nothing; integrating or pruning them is the maintainer's choice). |
| PR-004 | HIGH | IN-SCOPE | Repository rule `check.ipd-uncarried-obligation` | `check_engine.evaluate_durable_carrier` -> "2 obligation(s) name no durable carrier: deferred row 1, deferred row 2" (severity error) | Both Deferred rows lacked `Carrier`/`Carrier-Evidence`/`Carrier-Declined`, an error-severity finding in `aw check all`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `Carrier-Declined` with the reason to both rows. Re-run of `evaluate_durable_carrier` returns `[]`. |
| PR-005 | MEDIUM | IN-SCOPE | Release gate | AGENTS.md "Every live bug gates the next release"; `0owirm` front matter `- Blocks-Release: next`; release `f33nrj` `- Status: planned` | A live `Work-Kind: bug` plan without `- Blocks-Release:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next` (resolves to `f33nrj`). |
| PR-006 | MEDIUM | IN-SCOPE | G. Execution contract | plan-review Step 4 execution-contract bullet; plan `## Approval and execution gate` | The gate lacked the human-approval line, OQ status, scope-as-declaration wording, the MUST-paste rule, path-scoped `aw commit` and never-push, and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with every element; runner retirement is named as the owner under `aw oc run`/`aw agy run`, `aw ipd finalize kht4vk` by hand. |
| PR-007 | LOW | IN-SCOPE | E. Verification strength | plan V-02 | V-02 demanded only the child's status line, not evidence that its concurrent-merge test passed, which E-02's Expected outcome requires. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now also demands `s95x79`'s V-03 pasted passing test output. |

### Coverage attempts (IPD-S408)

- Attempt 1: `aw ipd lint --phase review-finalize --agent` reported `IPD-S408` after the edits changed the coverage-relevant text (recorded fingerprint `28b24ac4...` stale). Ran `aw ipd coverage kht4vk`: "Orchestrator kht4vk is ready for review." and it re-recorded `- Coverage: pass`, fingerprint `3a4f6e35...`. No checklist rows changed (rows: 2 -> 2). Re-run of `review-finalize` clean.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the orchestrator require `vy20et` to be closed for the Set to be done? | No: the bar is "every item `0owirm` reports `COMPLETE` is closed"; `vy20et` is carried as an open follow-up. | Require all eight closed (contradicts the reviewed child and would force a false close); add a child to drive `89xjll` to `implemented` (an agent may not set `implemented` without cited evidence, and the spec's implementation is not this Set's concern). | `0owirm` E-02/E-07 and Deferred; AGENTS.md "may NOT set `implemented` (needs cited evidence)"; spec `25kzda` 3.4 per `0owirm` review PR-007. | yes |
| D-2 | Should this Set integrate the preserved lanes `aw/lane/2rm0gz` / `aw/lane/iosmvn`? | No; recorded as maintainer's choice with `Carrier-Declined`. | Add a child to integrate them (duplicates the next run's re-graduation and acts on unreviewed lane content). | `aw lanes list` "keep: no run record"; `runner_shared.integrate_stranded_lanes` scope. | yes |
