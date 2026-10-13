# Review findings: plan z3cqvz

- Subject-Id: z3cqvz
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `edcfa515d` in an isolated review lane. The plan was committed and unchanged (`055d32396`), so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review.

Re-verified:
- `runner_shared.execute_item_core` collects the baseline only under `if integration_gate_relevant and not validate:` (agent_workflows/runner_shared.py:37118), while `start_suite_baseline` is called before the turn without any validate condition (runner_shared.py:35816) and `validate` is computed after the turn (runner_shared.py:36301). The orchestrator's Concern is accurate.
- `DEFAULT_STALL_TIMEOUT = 900.0` (runner_shared.py:32709); `INTEGRATION_LOCK_PROGRESS_SECONDS = 60.0` (runner_shared.py:6311), which is the 60s cadence the Set adopts.
- The watchdog wiring sites the child `xvm6no` names exist: `oc_runipd.run_opencode` `watchdog.progress_checker = observer.poll` (oc_runipd.py:3088), `agy_runipd.run_agy_turn` `progress_checker=observer.poll` (agy_runipd.py:2596).
- All four children exist in `pending/` with matching Id/Set/Order, `- Item-Dependencies:` matching the child table, `From-Backlog: 58x9mw` and `Blocks-Release: next`. Backlog `58x9mw` is `graduated` with `Graduated-To: z3cqvz`.
- The October run records cited as measurement source (`.aw/records/runs/`) are gitignored (`.aw/.gitignore:14`) and absent from this lane, so the 322/0 and 1,258/91.5h figures were not re-measured here; they are context for the Concern, not a V-item bar, and child `9ec94f` V-02/V-03 re-prove the mechanism behaviorally.
- Searched `.aw/records/backlog/` for items tracking the two deferred defects (general shell-tool idleness under the stall watchdog; driver concurrency / host load): none found.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Sequencing | plan E-04 "Depends on: E-03"; child table row 04 "Depends on executed:0o0wt2"; plan line 70 "03 and 04 are independent of each other" | E-04 depended on E-03 while the child table and prose say 04 needs only 02, so a hand executor would block 04 on 03 for no reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now depends on E-02, matching `1qut7y`'s `Item-Dependencies: executed:0o0wt2`. |
| PR-002 | MEDIUM | IN-SCOPE | G. Traceability | plan Cross-IPD validation "checked by xvm6no V-01 ... (xvm6no V-03)"; xvm6no V-01 is the baseline capture, V-03 is the nested guard; heartbeat/watchdog are V-04/V-05 | Cross-IPD checks cited the wrong child V-items, so the "one entry point" and "no silent wait" invariants pointed at evidence that does not prove them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-pointed to xvm6no V-02 (slot exercised through `aw suite`), V-04/V-05 (heartbeat, watchdog), 0o0wt2 V-03/V-06, 1qut7y V-03/V-04. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Verification checklist | plan V-02/V-03 quoted only child V-02/V-03; completion criterion 3 (seams and prompts, OWNER 0o0wt2) and the watchdog half of criterion 4 had no V-item quoting their evidence | The orchestrator's V-items could pass while two of its completion criteria (seam routing + prompts, watchdog counting) were never checked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01..V-03 now quote the specific child V-items for every completion criterion (0o0wt2 V-02/V-04/V-06/V-07; xvm6no V-02/V-04/V-05; 9ec94f V-02/V-03); E-02/E-03 expected outcomes extended to match. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the honesty rule, the commit command, never-push, the scope declaration, and the runner-vs-hand ownership of the terminal transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten on the shape of executed orchestrator `67lvds`: runner retires, by hand `aw ipd finalize`, no `git mv`, paste actual text, `aw commit z3cqvz`, never push. |
| PR-005 | LOW | UNDER-SCOPE | Project rule (backlog as work surface) | plan Deferred "to be filed separately" (two bullets); no matching backlog item found | Two deferred defects existed only in plan prose, which the attention view cannot see. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bullets now state they are NOT YET TRACKED and direct the maintainer to `aw backlog new`; filing is deliberately not added as orchestrator work (it would be uncovered parent work). |
| PR-006 | LOW | IN-SCOPE | Project rule (OQ owner) | plan OQ-01 "Owner: none"; xvm6no/0o0wt2 E-04 `max(2, cpu_count // slots)` | OQ-01 was resolved by the author with no recorded owner, and quoted `-n = cpu_count // slots` while 0o0wt2 E-04 specifies `max(2, ...)`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to `plan author`; formula corrected to `max(2, cpu_count // slots)` citing 0o0wt2 E-04. Decision row D-1. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept OQ-01's slot default `max(1, cpu_count // 6)`? | Yes, as authored by the plan author | One slot (serializes seven drivers behind a 216s-median suite); unbounded (today's failure) | backlog `58x9mw` measurements; xvm6no OQ resolution line 116; `AW_SUITE_SLOTS` makes it configurable | yes |
| D-2 | Add an orchestrator item to file the two deferred defects as backlog items? | No: annotate them as untracked and leave filing to the maintainer | Add an E-item on the parent (uncovered parent work, refused by the coverage gate's intent); add a fifth child (scope growth the maintainer did not ask for) | AGENTS.md orchestrator rule "work that exists ONLY on the parent ... ADD A CHILD"; Set scope in plan line 6 | yes |

### Structural loop

- IPD-S408 attempt 1: `aw ipd lint --phase review-finalize` reported `IPD-S408` after the revisions because the recorded `- Coverage-Fingerprint:` no longer matched the edited text. `aw ipd coverage z3cqvz` re-ran and reported "Orchestrator z3cqvz is ready for review", refreshing the fingerprint. No checklist rows changed (rows: 4 -> 4). Re-lint: conforming.
