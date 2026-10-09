# Review findings: plan 2pv5xd

- Subject-Id: 2pv5xd
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, open), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `8b76998c8`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review. After revision,
`author` and `review-finalize` both report exactly one diagnostic, `IPD-Q501`, which is the intended gate for the
new blocking OQ-02. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply. The run had no human
interaction channel, so OQ-02 is left open.

Verified anchors: `orchestrator_readiness._READY_CHILD_STATUSES` and the `child_status == "executed" and in_terminal`
branch in `review_readiness`; `REMEDY_CHILD_STATUS` text; `ipd_schema.TERMINAL == ('executed', 'superseded',
'not-executed')`; `runner_shared.set_retirement_terminal_statuses` ("Every child `Status:` that ENDS its
participation in a Set"); `runner_shared.RETIRED_PLAN_STATUSES`; `runner_shared.read_set_membership`;
`run_selection_policy.is_in_terminal_directory` and `TERMINAL_DIRECTORY_SEGMENTS` (includes `/reusable/`);
spec `25kzda` Section 2.5d condition 2; `62pkkg` and `itamry` both in `not-executed/`.

Demonstration (scratch repo built with the `tests/test_orchestrator_readiness.py` helpers, real `review_readiness`):

```text
retired child IN table ready= False [('child-status-not-ready', 'chd002', "child chd002 has status 'not-executed' (must be to-review, reviewed, approved, auto-approv"), ('coverage-record-absent', 'orc001', ...)]
retired child row REMOVED ready= False [('coverage-record-absent', 'orc001', ...)]
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric B/D; spec `25kzda` 2.5b/2.5e coverage gate | `runner_shared.PROBE_PROMPT_TEMPLATE` ("WORK ASSIGNED TO A NAMED CHILD IS COVERED ... a child listed in the `### Child IPDs table` section ... is COVERED"); probe payload keys `child_table_rows`, `e_items`, `prose_sections` carry no child status; plan OQ-01 | OQ-01 claimed work assigned only to a retired child "already reads as uncovered". False: the probe counts any listed child as covering, and retirement changes neither its input nor the fingerprint. So E-01 accepting a retired row in place leaves a pre-retirement `- Coverage: pass` current, and the orchestrator becomes approvable and runner-retirable with that child's work never performed. | C:Medium; U:Low; S:Medium-High; F:Medium-High; Overall:Medium-High | OPEN | Raised as OQ-02 (`- Blocking: yes`, `- Finding: PR-001`) with two bounded options (A: feed retired status into the coverage input; B: do not accept a retired row, fix the remedy instead). E-01, E-02, E-04, E-05 and V-01 rewritten to depend on the answer. Corrected the OQ-01 text and the Concern's "permanently" claim. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric C | `runner_shared` continue-handoff `remedy = _orch_readiness.REMEDIES.get(rf.code, rf.remedy)` | E-02 changed the remedy per finding under the same `CODE_CHILD_STATUS`; the runner looks remedies up by code, so its handoff text would keep the wrong "bring to to-review" advice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now adds a distinct `child-terminal-status` code with its own `REMEDIES` entry; `REMEDY_CHILD_STATUS` unchanged for non-terminal statuses (pinned by `test_condition_2_child_status_draft`); V-02 checks the handoff surface. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric G | E-02 "names `aw ipd set <status> <orchestrator> ...` review of the orchestrator's table" | The new remedy was not a usable instruction, did not meet spec `r07vma` R7, and "informational note" had no data path (`ReviewReadiness` has no such field). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Remedy text specified (edit the row, reassign work, re-run coverage; wrong-directory case re-runs the setter); note carried on a defaulted trailing `notes` field rendered by `render_human`/`render_agent`; composes with approved `juu1rj`. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric A/B; AGENTS.md shared checkout | E-03 "stage both files together so a self-commit includes both"; `status_set._offer_self_commit` commits `touched_paths` | Adding the orchestrator to the commit would sweep a co-worker's uncommitted edits to that file into this commit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 skips (and says so) when the orchestrator is dirty, terminal, absent, or itself in `matched_records`; V-03 pastes each skip. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric C/F; agent output contract | E-03 "print a one-line hint"; `run_set_command` agent branch emits one `CommandResult` | A bare `print` would corrupt `--agent` stdout. The cited "same history-append path" does not exist as a function (inline `new_lines.insert(i + 1, hist_entry)` in `apply_status_change`). `- Kind: child` misses legacy children with no `Kind:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Hint via `term` / `NextAction`; extract one private history helper; membership decided by `SetMember.is_orchestrator`. |
| PR-006 | LOW | IN-SCOPE | Rubric A | `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` includes `/reusable/`; E-01 "matching terminal directory (`is_in_terminal_directory`)" | `is_in_terminal_directory` accepts any terminal segment, so `superseded` under `reusable/` would pass although E-01 says "matching". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 defines matching as the `/<status>/` segment; V-01 adds the `superseded`-under-`not-executed/` case. |
| PR-007 | LOW | UNDER-SCOPE | Rubric E/G (evidence) | V-01..V-05 as authored | V-items were thin (no skip cases, no agent-mode check, no before/after suite comparison). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each V-item now names the concrete runs and observable outputs; V-05 requires the after-minus-before failing set be empty. |
| PR-008 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Plan "Approval and execution gate" (one line) | Gate lacked staged-set verification, scope fence as declaration, the lint completion rule and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full execution contract added; H1 trimmed to match Scope, which excludes the table edit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does a terminal child get a correct remedy on every surface? | New code `child-terminal-status` with its own `REMEDIES` entry. | Per-finding `remedy=` under `CODE_CHILD_STATUS`. REJECTED: the runner re-reads remedies by code. | `runner_shared` continue-handoff `REMEDIES.get(rf.code, rf.remedy)` | yes |
| D-2 | Should E-03 commit a dirty orchestrator? | No; skip and say why. | Commit it anyway. REJECTED: sweeps co-worker work. | AGENTS.md "Shared checkout"; `_offer_self_commit` | yes |
| D-3 | Where does the hint go in agent mode? | `NextAction` in the `CommandResult`. | `print`. REJECTED: breaks one-record stdout. | `run_set_command` agent branch | yes |
| D-4 | What does "matching terminal directory" mean? | The `/<status>/` segment. | Any `TERMINAL_DIRECTORY_SEGMENTS` member. REJECTED: admits `reusable/`. | `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` | yes |

No decision is `Reversible: no`. PR-001 is left OPEN at HIGH and is escalated in the plan as OQ-02 with `- Blocking: yes` and `- Finding: PR-001`.

## Round 2

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | high | IN-SCOPE | Rubric B/D; spec `25kzda` 2.5b/2.5e coverage gate | `runner_shared.PROBE_PROMPT_TEMPLATE` ("WORK ASSIGNED TO A NAMED CHILD IS COVERED ... a child listed in the `### Child IPDs table` section ... is COVERED"); probe payload keys `child_table_rows`, `e_items`, `prose_sections` carry no child status; plan OQ-01 | OQ-01 claimed work assigned only to a retired child "already reads as uncovered". False: the probe counts any listed child as covering, and retirement changes neither its input nor the fingerprint. So E-01 accepting a retired row in place leaves a pre-retirement `- Coverage: pass` current, and the orchestrator becomes approvable and runner-retirable with that child's work never performed. | C:Medium; U:Low; S:Medium-High; F:Medium-High; Overall:Medium-High | fixed | STALE ESCALATION CLOSED 2026-10-09 by agent (aw ipd recheck-readiness). The question this finding was escalated as (OQ-02) is `- Status: resolved`, so the finding it gated on has been answered and the record is caught up. NO FINDING WAS RE-DERIVED and no plan content was re-critiqued: the match was made on the question's declared `- Finding: PR-001` back-reference, not on a judgement about what the question was about. Previous decision: open. |
