# IPD: Record the verifier corroboration verdict on the attempt and surface it, without refusing on it

- Date: 2026-09-30
- Kind: child
- Concern: Order 08 (`bjx20r`) computes whether a verifier's claimed `tests_run` commands are corroborated by the tool calls its own session log shows it made, but nothing calls it, so the answer exists only in a test. A maintainer auditing "was this verification real" still has exactly what they had before: an opaque `verified` token plus a self-reported command list that `runner_shared.has_verifier_test_evidence` admits proves activity and not correctness. The shipped surfaces that already render verifier facts (`runner_shared.format_verifier_evidence_section` in `execution-report.md`, and `run_viewer`'s human/`--json`/`--agent` renderings of `tests_run` and `corrections_made`) render the CLAIM with no indication of whether it was corroborated.
- Scope: Make the corroboration verdict a RECORDED, RENDERED FACT and nothing more. Call Order 08's verdict function once, at the single existing verifier-outcome consumption site in `runner_shared.execute_item_core`, store the verdict plus its reason code and counts on the attempt and item records, and render it beside the evidence already shown in `execution-report.md` and `aw runs`. EXPLICITLY NOT INCLUDED, AND THIS IS THE PLAN'S CENTRAL DELIBERATE LIMIT: no refusal, no downgrade, no disposition change, no effect on `verify_disp`, and no effect on `integration_is_earned`. An `uncorroborated` turn integrates exactly as it does today; the ONLY change is that a human and a machine consumer can now see the discrepancy. OQ-01 carries the refusal question to the maintainer rather than deciding it by implementation.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_viewer.py, tests/test_verifier_corroboration.py
- Item-Dependencies: executed:bjx20r
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- Set: runverdict
- Order: 9
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: btak7a
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved
- From-Backlog: 5xgllt

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401..PR-409. EVERY STRUCTURAL CLAIM RE-DROVE CORRECTLY AT HEAD `eef2a03e`: the verifier-outcome block in `runner_shared.execute_item_core` is singular and shared and already holds `attempt["verify_log"]`, `v_data`, `map_verdict` and `has_verifier_test_evidence` exactly as F-1 describes; F-2's two literal-matching `run_viewer` sites quote verbatim, including the `else: v_disp = "-"` fallthrough; `format_verifier_evidence_section`'s byte-identical-when-empty docstring is verbatim; both hosts' `write_report` are one-line wrappers over the one shared function, so F-3 holds; `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` and its driver-only comment listing `verify_log` are verbatim; `tests/test_verifier_evidence.py`'s named-but-simulated test is exactly the flaw F-5 records; and `runner_shared` has precisely TWO module-level first-party imports. THREE CORRECTIONS MATTER. FIRST, THE PLAN'S CENTRAL SAFETY PRECEDENT DOES NOT EXIST: `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`, which E-05 is told to copy and F-4 calls 'the shipped outcome-equality precedent', was DELETED in `19313eed` (1020 lines), the same trim this plan cites elsewhere; two `runner_shared` comments still cite it, so the plan inherited a dangling citation rather than inventing one. E-05 must now author the shape from the description rather than copy a file, and must not cite the deleted test as though a reader could open it. SECOND, E-01's PLACEMENT INSTRUCTION IS UNSAFE AS WRITTEN: `v_data` is bound only in the try's else-path, and the existing `v_has_evidence` guard is what keeps the unreadable arm from a `NameError` via `not v_unreadable` short-circuit; E-01 says to compute 'immediately after `v_has_evidence`' AND to yield a verdict 'for every path including the unreadable-verdict arm', which at the outer level touches unbound `v_data` and would be silently converted into `indeterminate` by the plan's own exception guard, so the guard would MASK the defect rather than reveal it. THIRD, E-01 SAYS 'Call Order 08's verdict function' AND NEITHER PLAN NAMES IT: `bjx20r` describes the function in prose and declares no symbol, so there is no citable name at authoring time; E-01 now requires reading the shipped module and reporting the symbol rather than assuming one. Baseline re-measured: `3523 passed, 2 skipped, 3 warnings in 154.35s`, 208 deselected; targeted `53 passed`.
- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog item `5xgllt` together with Order 08 (`bjx20r`), which owns the predicate this plan consumes and is declared as `- Item-Dependencies: executed:bjx20r` so the runner enforces the ordering at dispatch rather than a human remembering a note. WHY THE BACKLOG ITEM'S ONE-LINE FIX IS TWO PLANS: the item describes a single act ("parse the verifier turn's session log, extract the tool calls it really made, and match them against the commands it CLAIMED"), but the two halves have DIFFERENT failure models and therefore different review questions. Order 08's risk is a miscalibrated matcher producing false accusations; this plan's risk is a wrong surface - specifically, adding a state token that renders as a bare `-`, which is the trap plan `bxx9af` measured and documented for this exact code path ("`run_viewer.py:1617-1631` maps `verified` to `yes`, the set `(unverified, verify-failed, failed)` to `no`, and EVERYTHING ELSE to a bare `-`", i.e. visually identical to "no verification ran"). A reviewer cannot hold both questions at once, and the runner isolates each in its own lane. THE PLAN SHIPS NO REFUSAL, DELIBERATELY AND ON THE RECORD. `runner_shared`'s pre-work-baseline comment block records the maintainer's 2026-09-08 and 2026-09-20 rulings with four reasons, including one that applies to this module verbatim ("A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE. It has write access to this file"), and spec `25kzda` Section 5.1 records the same ruling. Building a refusal here would re-litigate a settled decision by implementation; OQ-01 asks instead. WHAT MAKES A RECORD-ONLY CHANGE WORTH SHIPPING ANYWAY, since "it changes no behavior" invites the question: the same argument the maintainer accepted for the suite baseline applies, in the same words - it is INFORMATION FOR AN HONEST READER. A discrepancy a human can see is one they can act on; today there is nothing to see.

## Goal

Turn the corroboration verdict from a tested function into a recorded and visible fact, at one call
site and on the surfaces that already render verifier evidence, with the fail-open guarantee stated
and pinned by a test rather than promised.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: compute it once, where the verdict is already read

- [x] E-01 Call Order 08's turn-level verdict from `runner_shared.execute_item_core`, at the point where the verification outcome is ALREADY parsed and the evidence predicate is ALREADY applied: the block that reads `v_outcome_file`, computes `v_data`, calls `map_verdict`, then sets `v_has_evidence = has_verifier_test_evidence(v_data)`. Use the verifier log path the same block has already stored on `attempt["verify_log"]` (set from `spawn_verifier`'s returned `_v_log` a few lines above). IMPORT IT FUNCTION-LOCALLY, not at module level: `runner_shared`'s module-level first-party imports are PINNED in-tree to exactly `render_stream` + `runner_profiles` (re-measured at review: exactly two `^from agent_workflows` lines), and its own comments name the function-local import as the established route for anything else ("`ipd_lint`/`ipd_schema`/`ipd_lifecycle`/`worktree_lease` all arrive that way").
  READ THE SHIPPED SYMBOL NAME RATHER THAN ASSUMING ONE. Order 08 (`bjx20r`) describes the turn-level verdict function in prose and declares NO symbol name anywhere in its text, which review confirmed by grepping it, so there is no name this plan can cite. Open `agent_workflows/verifier_corroboration.py` as Order 08 actually shipped it, report the function's real name and signature in V-01, and call that. If its signature does not accept a log path plus the claimed-commands list in some form, STOP AND REPORT: that is an interface mismatch between two plans and belongs in a corrective plan, not in a guess at this call site.
  PLACEMENT IS LOAD-BEARING AND THE EARLIER INSTRUCTION WAS UNSAFE. `v_data` is bound ONLY in the `else:` branch of the surrounding `try`; on the exception path `v_unreadable` is set True and `v_data` is NEVER BOUND. The existing line `if not v_unreadable and isinstance(v_data, dict):` is what keeps that arm from a `NameError`, by short-circuiting on `not v_unreadable` before `v_data` is named. So the computation must sit INSIDE that same `not v_unreadable and isinstance(v_data, dict)` guarded region, where `v_data` provably exists; and the UNREADABLE ARM must reach its `indeterminate` verdict by INITIALIZING the verdict variables BEFORE the guard (alongside `v_has_evidence = False`) rather than by running the computation there. Do NOT place the call at the outer level after `attempt["verify_has_evidence"] = v_has_evidence`: that path executes on the unreadable arm, touches unbound `v_data`, and the exception guard below would silently convert the resulting `NameError` into `indeterminate`, so the plan's own guard would MASK the bug instead of surfacing it. V-01 requires the guarded region pasted with the unreadable arm's verdict shown to come from initialization.
  THE COMPUTATION MUST NOT BE ABLE TO BREAK THE TURN, and "Order 08 never raises" is not sufficient grounds to omit the guard: this call sits inside the block that decides a verified turn's disposition, and an exception here would convert a successful verification into a crash. Wrap it so any failure yields the `indeterminate` verdict with a distinct reason code naming the computation itself as the thing that failed, and record that reason rather than swallowing it silently. State in a comment that the guard is deliberate and why, AND that it is not a licence to place the call where `v_data` may be unbound, since a masked `NameError` is indistinguishable from a legitimate `indeterminate` in the recorded output.
  NOTHING IN THIS ITEM MAY READ `verify_disp`, `disposition`, OR ANY REFUSAL, and nothing may write them. The computed verdict is an OUTPUT of this block, never an input to it.
  - Depends on: none
  - Expected outcome: one function-local call to the symbol Order 08 actually shipped, placed inside the existing `not v_unreadable and isinstance(v_data, dict)` guarded region, guarded so no exception can escape, with the unreadable arm's `indeterminate` verdict arriving by pre-guard initialization rather than by running the computation on unbound state; `verify_disp` and `disposition` provably unchanged (V-01 pins this).
  - Execution state: performed

- [x] E-02 Store the verdict on the records that already carry the verifier's facts, in the SAME shape and at the SAME two places the existing evidence fields use: the block already sets `attempt["tests_run"]`, `attempt["corrections_made"]`, `item["tests_run"]`, `item["corrections_made"]` and `attempt["verify_has_evidence"]`. Add the corroboration verdict, its reason code, and its counts (claimed, observed, matched, delegations) alongside them, on the attempt AND on the item, because the two have different readers: `run_viewer` reads the ITEM for the steps table and the attempt for per-attempt detail.
  DO NOT ADD IT TO `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`. That tuple governs which attempt keys are replayed into a LATER TURN'S PROMPT, and its neighbouring comment enumerates `verify_log` as a DELIBERATELY OMITTED driver-only key for the stated reason that such keys are absolute filesystem paths and driver bookkeeping. A corroboration verdict is a judgement about a PREVIOUS verifier turn, and feeding it to a retrying agent would tell that agent how it was assessed, which is a prompt-design decision nobody has asked for. Leave the tuple alone and say so in a comment at the write site.
  - Depends on: E-01
  - Expected outcome: a verifier attempt's record and its queue item both carry the verdict, reason code and counts; `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` is byte-identical; a run whose verifier produced no outcome file carries no corroboration key at all rather than a misleading default.
  - Execution state: performed

### Task group 2: surface it beside the claim it qualifies

- [x] E-03 Render it in `execution-report.md` by EXTENDING the existing section rather than adding a new one: `runner_shared.format_verifier_evidence_section` already renders a `## Verification evidence` heading with a `Tests run:` and `Corrections made:` sub-list per verified item, and it is SHARED (both hosts' reports reach it through `runner_shared.write_report`, so one edit reaches both). Add the verdict and its reason as a line in the same per-item block, directly adjacent to the `Tests run:` list it qualifies, because a claim and its corroboration read as one fact and separating them invites reading the claim alone.
  PRESERVE THE FUNCTION'S BYTE-IDENTICAL-WHEN-EMPTY CONTRACT, which its own docstring states ("Returns [] if no items have verified test evidence, ensuring unaffected reports are byte-identical"). A run with no verification must produce the same report bytes as before this change, and E-05 pins that.
  DO NOT ADD A TABLE COLUMN. `runner_shared.write_report`'s own inline comments state three times that new facts are appended as SECTIONS or lines "so the table's column contract is unchanged"; that contract has a machine reader (`run_viewer.load_run_summary` parses those columns), so a new column is a breaking change to a parser this plan does not own.
  - Depends on: E-02
  - Expected outcome: a verified item's report block shows its corroboration verdict beside its claimed commands, in both hosts' reports through the one shared renderer; a run with no verification evidence yields byte-identical report output to HEAD; the table's columns unchanged.
  - Execution state: performed

- [x] E-04 Surface it in `aw runs` through the SAME path the claimed commands already take, and DO NOT introduce a new `verification_status` token. `run_viewer` already carries `tests_run` and `corrections_made` on its `StepSummary` (read from the item, falling back to the outcome file), serializes them into the `--json`/`--agent` payload by `asdict`, and renders them in `render_step_details` via `extract_verifier_test_commands`. Add the verdict as a sibling field on that same dataclass so all three renderings gain it from one change, and render it in the details view immediately beside the tests-run list.
  THE FORBIDDEN SHORTCUT, MEASURED IN-TREE FOR THIS EXACT FILE: do NOT express corroboration by writing a new value into `verification_status`. Plan `bxx9af`'s review measured that `run_viewer` matches that field on LITERAL values in two places - one badges only `verified` and `failed`, the other maps `verified` to `yes`, `(unverified, verify-failed, failed)` to `no`, and EVERYTHING ELSE to a bare `-` - so a novel token renders identically to "no verification ran", which is the opposite of this plan's purpose. A separate field has no such collision. Re-read both sites before writing to confirm the mapping still holds, and report what you find.
  ALSO CHECK FOR A DUPLICATED PREDICATE BEFORE ADDING A RENDERER. The same review recorded that `run_viewer`'s per-item `Issue` predicate existed as FIVE copies across `format_artifact_audit_summary`, `render_steps_table` and three `run_viewer_cli` branches, which is how `aw runs` once said one thing in the table and omitted the same item from `--json`. Reach all three renderings through the one dataclass field; do not fork a sixth copy of anything.
  - Depends on: E-02
  - Expected outcome: the verdict appears in `aw runs`' human details, `--json` and `--agent` payloads from one dataclass field; `verification_status`' value set is unchanged and no novel token is introduced; no additional copy of a per-item predicate is created; a run predating this change renders without the field rather than crashing.
  - Execution state: performed

### Task group 3: pin the fail-open guarantee rather than promising it

- [x] E-05 Extend `tests/test_verifier_corroboration.py` (Order 08's file, so the subsystem has one test home) with the INTERACTION tests this plan's whole safety argument rests on, and make the central one an assertion about BYTE-IDENTICAL OUTCOMES rather than about intent: for a verifier outcome whose verdict is `VERIFIED` and whose `tests_run` passes the evidence gate, the resulting `verify_disp`, `disposition`, recorded refusal, and `integration_is_earned` result must be IDENTICAL whether the corroboration verdict is `corroborated`, `uncorroborated`, or `indeterminate`.
  THE CITED PRECEDENT NO LONGER EXISTS AND MUST NOT BE CITED AS IF A READER COULD OPEN IT. This item previously told the executor to copy the shape of `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`. Measured at review: that FILE was deleted in `19313eed` (1020 lines removed, the same suite trim this plan cites elsewhere for a different deletion), and the class existed at `19313eed^` so the plan's description of it was accurate when written. TWO `runner_shared` COMMENTS STILL CITE IT, so this plan inherited a dangling citation rather than inventing one; those comments are out of scope here and are recorded in F-4 for whoever owns the dangling-citation sweep. WHAT TO DO INSTEAD: author the shape FROM THE DESCRIPTION rather than by copying a file. The shape is: parameterize one test over the three verdict values, drive the same outcome through each, and assert the four downstream facts are equal across all three, so the test's own name and body carry the ruling. You MAY read the deleted test for inspiration via `git show 19313eed^:tests/test_suite_baseline.py`, and if you do, say so in V-05; you may NOT write a docstring or comment implying the file is present in the tree.
  NAME THE TEST SO ITS NAME CARRIES THE REASON, which is the durable half of the precedent and survives the file's deletion: a future author who adds a refusal here should be stopped by a test whose name says why, not by prose in a plan they will not read.
  ALSO PIN: that a raising or absent corroboration module cannot break the turn (E-01's guard), by monkeypatching the computation to raise and asserting the turn's outcome is unchanged with the guard's reason code recorded; and that both hosts reach the SAME objects, following the existing `RunnerVerificationGateTests::test_cross_driver_symmetry` pattern in `tests/test_verifier_evidence.py`, which asserts `assertIs` between each host's re-export and `runner_shared`'s definition.
  BEWARE THE PRECEDENT THIS FILE'S NEIGHBOUR SETS AND DO NOT COPY IT. `tests/test_verifier_evidence.py::RunnerVerificationGateTests::test_execute_item_core_refuses_verified_verdict_with_empty_tests_run` names `execute_item_core` but RE-IMPLEMENTS the gate inline with a hand-written `if`, so it never executes the function it claims to test and would pass even if that code path were deleted. Drive the real code path, or state plainly in the test's docstring what is simulated and why the real path could not be reached.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a named test asserting outcome equality across all three corroboration verdicts; a test proving a raising computation leaves the turn's outcome unchanged; a cross-host symmetry test; and no test that merely re-implements the logic it claims to cover.
  - Execution state: performed

## Project conventions discovered (Step 0)

- There is exactly ONE verifier-outcome consumption site for BOTH hosts, in `runner_shared.execute_item_core`: each host's `_spawn_verifier` closure is injected into that shared function, so a change there reaches oc and agy from one edit. The hosts re-export the evidence symbols by `from agent_workflows.runner_shared import X as X` and NEVER define them, with an in-tree comment stating exactly that ("Bound from `runner_shared` and NEVER defined here").
- `runner_shared`'s module-level first-party imports are PINNED to exactly `render_stream` + `runner_profiles`; the function-local import is the documented route for anything else. The guard that enforced it (`tests/test_orchestrator_probe_cache.py`) was DELETED in `19313eed`, so the convention is currently unenforced; follow it anyway.
- `runner_shared.write_report` is SHARED (one definition, both hosts, parameterized by `HostLabels`), and its docstring records the three ways unification changed the Antigravity report. This is a CHANGE from the state plan `bxx9af` worked against, where two divergent per-host implementations existed and sharing them was forbidden in-tree; that constraint is GONE and a report change is now made once. Verify this at execution rather than trusting it: if two implementations have reappeared, the section must be added to both or the limitation stated.
- `runner_shared.format_verifier_evidence_section` returns `[]` when nothing qualifies, and its docstring names the reason ("ensuring unaffected reports are byte-identical"). Every other optional report section in `write_report` follows the same rule (`render_transient_dependency_waits`, `render_zero_work_notes`, `lane_containment.format_preserved_lanes`), each with a comment saying an unaffected run's report stays byte-identical.
- A refusal is written through ONE writer and read through ONE reader (`render_stream.record_refusal` / `render_stream.refusal_of_item`), whose docstrings state the reason ("so no surface can look under a different key than the producers write"). This plan writes NO refusal, so it calls neither, and E-05 asserts the absence.
- `run_viewer` reads `tests_run`/`corrections_made` from the queue item and falls back to the outcome file, carries them on `StepSummary`, and reaches the human view, `--json` and `--agent` from that one field. That is the seam to extend.
- `verification_status` has ten readers and two match on LITERAL values, mapping anything unrecognized to a bare `-`; a novel token is therefore indistinguishable from "no verification ran". Measured and recorded by plan `bxx9af`'s review for this exact file.
- `.aw/records/runs/` is gitignored with zero tracked files and is ABSENT from every lane worktree and fresh clone (measured in-tree in `doctor.probe_artifact_audit` and `lane_containment`), so tests use committed fixtures.
- The one accepted V-item result token is `pass` (writing the natural word `verified` produces `IPD-S402`/`IPD-S404`), so every `V-*` below terminates at `pass`.
- THE 2026-09-24 SUITE TRIM (`19313eed`) DELETED GUARDS THIS AREA'S COMMENTS STILL CITE, and this plan is affected twice over, which is worth holding as a convention rather than as two isolated findings. It deleted `tests/test_suite_baseline.py` (1020 lines), whose `NothingRefusesOnTheBaseline` class two `runner_shared` comments still name as live (F-4), AND it deleted `tests/test_orchestrator_probe_cache.py`, the guard that enforced this module's module-level import pin (already noted above). So when this plan cites a `runner_shared` comment as evidence, the COMMENT's claim about a test may be stale even where its claim about the code is exact. Verify the file exists before treating a cited test as a thing a reader can open; the dangling-citation class itself is tracked by backlog `ikxtkj` and `gia5i7` and is not this plan's to sweep.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- |
| F-1 | THE CALL SITE IS SINGULAR AND SHARED, so this plan adds ONE call and reaches both hosts. The block in `runner_shared.execute_item_core` already parses `v_data`, maps the verdict, applies `has_verifier_test_evidence`, and writes `attempt["tests_run"]`/`item["tests_run"]`; it also already holds the verifier log path it stored on `attempt["verify_log"]` lines earlier. | `runner_shared.execute_item_core`'s `if v_outcome_file.is_file():` block; each host's `_spawn_verifier` closure injected into it; both hosts' `from agent_workflows.runner_shared import ... as ...` re-export blocks with the comment "Bound from `runner_shared` and NEVER defined here". | E-01 and E-02 are small and local. No host module is in Scope-Paths, because neither needs editing. |
| F-2 | **A NOVEL `verification_status` VALUE WOULD RENDER AS A BARE `-`, IDENTICAL TO "no verification ran", and this was MEASURED for this exact file.** Two `run_viewer` sites match on literal values: one badges only `verified` and `failed`; the other maps `verified` to `yes`, `(unverified, verify-failed, failed)` to `no`, and everything else to `-`. | Recorded in plan `bxx9af`'s E-04 instruction and its F-4 review finding, which enumerates the ten readers and names the two literal-matchers. The shipped `fzxfph` change made the same choice for the same reason, recording in-tree that "`verify_disp` KEEPS ITS EXISTING TOKEN DELIBERATELY. A novel value would render as a bare `-` ... which is precisely how 'no verification ran' already renders and is the opposite of this change's purpose". | E-04 forbids the shortcut explicitly and uses a SEPARATE field. This is the single most likely wrong turn an executor could take here, which is why it is a finding and not a footnote. |
| F-3 | THE REPORT RENDERER IS NOW SHARED, WHICH IS A CHANGE FROM WHAT THE LAST PLAN IN THIS AREA FACED. `bxx9af` had to contend with two divergent per-host `write_report` implementations and an in-tree prohibition on sharing them; today `runner_shared.write_report` is one function parameterized by `HostLabels`, and `format_verifier_evidence_section` is reached from it once. | `runner_shared.write_report`'s docstring enumerates the three ways unification changed the Antigravity report and why the verify cell is no longer backticked; both hosts re-export `format_verifier_evidence_section` from `runner_shared`. | E-03 is one edit for both hosts instead of two. The plan instructs the executor to VERIFY this rather than assume it, because a re-divergence would silently halve the change's reach. |
| F-4 | **CORRECTED AT REVIEW: THE OUTCOME-EQUALITY PRECEDENT WAS DELETED, SO IT IS A SHAPE TO AUTHOR AND NOT A FILE TO COPY.** The maintainer's ruling and the RULING ITSELF are intact and verbatim; what is gone is the test that made the no-effect guarantee durable. `tests/test_suite_baseline.py` was deleted in `19313eed` (1020 lines), the same trim this plan cites elsewhere, and `NothingRefusesOnTheBaseline` existed at `19313eed^`, so the plan's description was accurate when written and the file was absent by the time it would execute. TWO `runner_shared` COMMENTS STILL CITE THE DELETED TEST, which is the same dangling-citation class backlog `ikxtkj`/`gia5i7` track; this plan does not own `runner_shared`'s comments beyond its own edits and does not strike them. | `runner_shared`'s pre-work-baseline comment block states "NOTHING MAY REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT" and names the deleted test; a second `runner_shared` comment cites it again ("still holds"). `git show 19313eed --stat -- tests/test_suite_baseline.py` reports the 1020-line deletion; `git show 19313eed^:tests/test_suite_baseline.py` finds `class NothingRefusesOnTheBaseline` at line 763. Spec `25kzda` Section 5.1 records the 2026-09-08 and 2026-09-20 rulings and is intact. | E-05 now AUTHORS the shape from its description instead of copying a file, may consult the deleted version through git, and is forbidden to imply the file is present. The durable half of the precedent is the NAMING convention, which survives the deletion and is what E-05 keeps. |
| F-4b | **ADDED AT REVIEW: E-01'S PLACEMENT WOULD TOUCH UNBOUND STATE AND THE PLAN'S OWN GUARD WOULD HIDE IT.** `v_data` is bound only in the `else:` branch of the outcome-parsing `try`; the exception path sets `v_unreadable = True` and leaves `v_data` unbound, and the existing `if not v_unreadable and isinstance(v_data, dict):` line is the short-circuit that prevents a `NameError` there. E-01 said to compute "immediately after `v_has_evidence`" while also yielding a verdict "for every path through the block including the unreadable-verdict arm"; at the outer level that runs on the unreadable arm, raises `NameError`, and the plan's exception guard converts it to `indeterminate`, so the recorded output is indistinguishable from a legitimate unknown and the defect is invisible. | The block's structure as read at review: `try: v_data = json.loads(...)` / `except Exception: v_raw_verdict = None; v_unreadable = True` / `else: v_unreadable = False`, then `v_has_evidence = False` followed by `if not v_unreadable and isinstance(v_data, dict):` guarding every `v_data` read. | E-01 now requires the call INSIDE that guarded region, with the unreadable arm's `indeterminate` arriving by pre-guard INITIALIZATION; the guard comment must say it is not a licence for unsafe placement; V-01 requires the guarded region pasted. |
| F-4c | **ADDED AT REVIEW: THE FUNCTION THIS PLAN CALLS HAS NO NAME YET.** E-01 said "Call Order 08's turn-level verdict", and `bjx20r` describes that function in prose across E-04 without ever declaring a symbol: grepping it for `verifier_corroboration.<name>` returns only the module filename. So at authoring there was no citable name, and an executor would have had to invent or guess one. | `grep -o 'verifier_corroboration\.[a-z_]*' ` over `bjx20r` returns `verifier_corroboration.py` alone; `agent_workflows/verifier_corroboration.py` and `tests/test_verifier_corroboration.py` are both ABSENT at review HEAD, which is correct since `bjx20r` is `reviewed` and unexecuted. | E-01 now requires reading the shipped module, reporting the real symbol and signature in V-01, and STOPPING on an interface mismatch rather than guessing. This is the one claim in the plan that could not be verified at review BY CONSTRUCTION, which is itself worth recording. |
| F-5 | THE ADJACENT TEST FILE CONTAINS A TEST THAT DOES NOT TEST WHAT IT NAMES, and copying its pattern would produce a vacuous guard for this plan's most important property. `test_execute_item_core_refuses_verified_verdict_with_empty_tests_run` names `execute_item_core` but re-implements the gate inline with a hand-written `if verify_disp == VERIFY_DISP_VERIFIED and not v_has_evidence:`, so it never calls the function and would pass if that code path were deleted. | `tests/test_verifier_evidence.py::RunnerVerificationGateTests`; the test's own body comment reads "Parse as execute_item_core does". | E-05 requires driving the real path or stating plainly what is simulated and why. Named as a finding because it is the local convention, and following the local convention would be the wrong choice here. |
| F-6 | `_PRIOR_ATTEMPT_SAFE_KEYS` IS AN ATTRACTIVE-LOOKING WRONG PLACE for this field, and the tuple's own neighbouring comment already refuses its nearest relative. It governs which attempt keys are replayed into a LATER turn's prompt, and it deliberately omits `verify_log` as a driver-only key. | `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` and the `_PRIOR_ATTEMPT_DRIVER_ONLY_EXAMPLES` comment above it, which lists `verify_log` as "absolute filesystem path to verification log" among keys "deliberately omitted here". | E-02 forbids adding it and requires a comment saying why: telling a retrying agent how its predecessor was assessed is a prompt-design change nobody requested, and it is not this plan's to make. |
| F-7 | SPEC `25kzda` ALREADY CLASSIFIES BOTH SIDES OF THIS COMPARISON, so recording the verdict implements the spec and no amendment is owed - but a REFUSAL would owe one. Section 5.1 lists captured tool events as admissible completion evidence and "an agent-authored summary or checklist without captured evidence" and "a verifier's opinion" as NOT completion evidence. | Spec `25kzda` Sections 5.1 and 4.2 ("Captured tool events are admissible because they are structured, hash-bound repository evidence, not agent narration"), status `approved`. | The spec-sync section says no amendment is owed and cites this; it also states that adding a refusal WOULD owe one, because it would change the authority under which a verdict may be recorded. That is a second, independent reason OQ-01 asks rather than implements. |
| F-8 | A RECORD-ONLY CHANGE IS DEFENSIBLE ON THE MAINTAINER'S OWN STATED GROUNDS, which matters because "changes no behavior" invites deletion at review. The accepted framing for the analogous case is that the artifact is information for an honest agent, and its value is that a human can act on what they can see. | `runner_shared`'s pre-work-baseline block: "THE BASELINE IS INFORMATION FOR AN HONEST AGENT, NOT A CHECK ON A DISHONEST ONE"; and its reason 4, "An agent that broke something subtly and genuinely believes the failure is unrelated answers `not-mine` in GOOD FAITH and is WRONG. Telling it what was already red lets it be RIGHT. That is the whole deliverable." | Gives the plan its own justification in the maintainer's terms rather than in the author's. The parallel is exact: a verifier that believes it ran the tests it cites, and did not, is sloppy rather than malicious, and a visible discrepancy is what lets the next reader be right. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/runner_shared.py`: compute the corroboration verdict once, function-locally and exception-guarded, in `execute_item_core`'s existing verifier-outcome block (E-01).
2. `agent_workflows/runner_shared.py`: store the verdict, reason code and counts on the attempt and item beside the evidence fields already written there, and leave `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` alone (E-02).
3. `agent_workflows/runner_shared.py`: extend `format_verifier_evidence_section`'s per-item block with the verdict, preserving its empty-returns-byte-identical contract (E-03).
4. `agent_workflows/run_viewer.py`: add the verdict as a `StepSummary` field so the human view, `--json` and `--agent` all gain it from one change, with no new `verification_status` token (E-04).
5. `tests/test_verifier_corroboration.py`: the outcome-equality test across all three verdicts, the raising-computation guard test, and the cross-host symmetry test (E-05).

## Deferred / out of scope (with reason)

- ANY REFUSAL, DOWNGRADE, OR DISPOSITION EFFECT IS OUT OF SCOPE, and this is the plan's defining limit rather than an omission. Two independent reasons, each sufficient. FIRST, the maintainer ruled twice (2026-09-08 and 2026-09-20, recorded in spec `25kzda` Section 5.1 and restated with four reasons in `runner_shared`'s pre-work-baseline block) that no programmatic gate may refuse a verdict on derived suspicion of dishonesty; reason 3 of that block applies verbatim ("A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE. It has write access to this file"). SECOND, it is premature on Order 08's own evidence: that plan's F-5 measures four mechanisms by which a genuine test run is invisible or unmatchable (subagent delegation, `make test` indirection, command chaining, and claim truncation or prose wrapping), so an `uncorroborated` verdict is not yet trustworthy enough to strand a lane on, and a false accusation costs a verified lane's work. OQ-01 asks the maintainer with the measurement in hand.
  - Carrier: sinhkj
- Feeding the verdict back to a RETRYING agent (via `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`) is out of scope: F-6 shows the tuple already refuses this field's nearest relative, and telling an agent how its predecessor was assessed is a prompt-design decision with its own review question.
  - Carrier-Declined: NOTHING IS OWED, because nobody has asked for this and this plan argues against it rather than postponing it. The tuple's own neighbouring comment already lists `verify_log` among keys DELIBERATELY omitted, so the exclusion follows an existing recorded decision rather than creating a gap; and telling a retrying agent how its predecessor was assessed would change what a turn READS about itself, which is a prompt-design change with its own review question and no current requester. A carrier here would schedule work this plan contends should not be done.
- The analytics surfaces (`run_dashboard`, `run_analytics_*`, `aw runs analytics`) are NOT extended. They aggregate per-session numerics on a `(size, mtime_ns)`-keyed cache; adding a per-item judgement to that layer is a different consumer with a cache-invalidation question of its own, and `aw runs` is where an operator looks first.
  - Carrier-Declined: NOT A DEFERRED DEFECT. The analytics layer aggregates per-session NUMERICS and this plan adds a per-ITEM judgement, so there is no missing row in an existing table; extending it would be a new capability with its own cache-invalidation contract, not the residue of this change. `aw runs` is the surface an operator reaches for a per-item fact and it is in scope here, so the information is not stranded. If a fleet-level corroboration rate is later wanted, it is a new analytics capability filed against whatever question prompts it.
- Rendering in the LIVE stream (`render_stream`) is out of scope: the corroboration verdict is computable only AFTER the verifier turn ends and its outcome file is read, so there is no live moment at which to render it.
  - Carrier-Declined: IMPOSSIBLE RATHER THAN POSTPONED, so nothing can carry it. The verdict requires the verifier turn's session log to be COMPLETE and its outcome file to be written, and both happen after the turn the live stream renders has ended; there is no moment during the stream at which the fact exists. A carrier would name work that cannot be done rather than work not yet done.
- Backfilling the verdict for runs already on disk is out of scope. Nothing rewrites run history in this package (`runner_shared.attempt_log_path` records the same principle for renamed logs: "nothing renames history"), and `aw runs` reading a pre-change run must simply show no field, which E-04 requires.
  - Carrier-Declined: PROHIBITED BY AN ESTABLISHED PRINCIPLE, not deferred. This package does not rewrite run history, which `runner_shared.attempt_log_path` states in as many words for the exactly analogous case of renamed logs, and a backfilled verdict would assert a measurement that was never taken at the time the run happened. The correct handling of a pre-change run is to show no field, which E-04 requires and V-04 proves. Nobody should ever own this.

## Scope check

- Over-scope: none. Each declared path is modified by an E-item: `agent_workflows/runner_shared.py` by E-01, E-02 and E-03; `agent_workflows/run_viewer.py` by E-04; `tests/test_verifier_corroboration.py` by E-05.
- Under-scope: TWO paths are deliberately NOT declared and an executor may expect them. Neither host runner (`oc_runipd.py`, `agy_runipd.py`) is in scope, because the call site, the record writes and the report renderer are all in shared code and the hosts only re-export; if editing a host proves necessary, that is a signal a symbol was defined in the wrong module and the correct response is to STOP AND REPORT. `agent_workflows/verifier_corroboration.py` (Order 08's module) is not in scope either: if it needs a change, that is a calibration defect belonging to `bjx20r`, and the honest route is a corrective plan rather than editing a dependency from its consumer. `tests/test_verifier_evidence.py` is also NOT in scope; F-5's flawed test is named as a finding to avoid copying, not as something this plan repairs.

## Required tests / validation

- `python3 -m pytest tests/test_verifier_corroboration.py tests/test_verifier_evidence.py tests/test_run_viewer.py -o addopts=""` for per-test counts on the changed surface and the two adjacent shipped ones.
- `python3 -m pytest` (bare; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the fast-marker scope) for regression. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. RE-DERIVE THE BASELINE on the pre-change tree rather than treating any figure here as a bar: review measured `3523 passed, 2 skipped, 3 warnings in 154.35s` with `208 deselected` at HEAD `eef2a03e`, and that count moves with every merged lane. The property to hold is green plus exactly the tests E-05 adds.
- A BYTE-IDENTICAL-REPORT proof for E-03's empty case: render `execution-report.md` for a fixture run with no verification evidence before and after the change and diff the two outputs, which must be empty.
- A BACKWARD-COMPATIBILITY proof for E-04: run `aw runs` (human, `--json` and `--agent`) against a fixture run directory carrying NO corroboration field and show all three render without error.
- A RED-then-GREEN falsifiability proof for E-05's outcome-equality test: introduce a one-line refusal keyed on the `uncorroborated` verdict, observe the test FAIL, revert, observe it PASS. A guard that has never been observed to fail is not evidence, and for this plan that guard IS the safety argument.
- `aw sanitize --agent` must report no `fail`.

## Spec / documentation sync

No `.spec.md` file is amended and none is in Scope-Paths, and the reason is worth stating precisely because a REFUSAL would change the answer. Spec `25kzda` (`aw <host> run` deterministic run-and-verify, `approved`) already classifies both sides of this comparison in Section 5.1: "hash-bound argv-list tool events with exit codes and captured-output digests" are admissible completion evidence, while "an agent-authored summary or checklist without captured evidence" and "a verifier's opinion" are NOT, and Section 4.2 closes that captured tool events are admissible "because they are structured, hash-bound repository evidence, not agent narration". RECORDING a comparison between the inadmissible self-report and the admissible tool events therefore implements Section 5.1 and amends nothing. HAD THIS PLAN ADDED A REFUSAL, an amendment WOULD be owed, because it would change the AUTHORITY under which a verified verdict may be recorded, and Section 5.1's attributed-suite-attribution subsection is where the maintainer's ruling on exactly that question lives; that is a second independent reason the refusal sits behind OQ-01 rather than inside this plan. No user-facing document describes the verifier's evidence handling, and `aw runs`' output is self-describing.

## Open questions

### OQ-01: Should an `uncorroborated` verifier turn eventually be refused, and if so on whose authority?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: sinhkj
- Resolution or deferral rationale: NOT BLOCKING, because this plan ships the RECORD and the record is useful on its own terms (F-8: the same information-for-an-honest-agent argument the maintainer accepted for the suite baseline), and because every part of this plan is unchanged by either answer - a refusal would be a later, separate change consuming the field this plan adds. WHAT THE MAINTAINER IS BEING ASKED, stated so the question is answerable from this paragraph alone: today a verifier that writes a plausible command string having run nothing is recorded `verified` and its lane integrates; after this plan, the same turn is still recorded `verified` and still integrates, but a human and a machine consumer can SEE that its claims were not corroborated by its own session log. The question is whether that discrepancy should eventually BLOCK integration. THE CASE AGAINST REFUSING, which is why this plan does not: the maintainer ruled twice against gates that refuse on derived suspicion of dishonesty ("You cannot build a pre-test that detects deception ... We're mitigating sloppiness, not malice"), one of the four recorded reasons applies verbatim here (a malicious agent has write access to this file and would rewrite the gate), and Order 08's F-5 measures four ways a GENUINE test run is unmatchable, so a false `uncorroborated` would strand verified work. THE CASE FOR: spec `25kzda` Section 5.1 already declares a verifier's self-report inadmissible as completion evidence and captured tool events admissible, so refusing on a contradiction between them arguably enforces a rule already written. WHAT WOULD MAKE IT DECIDABLE: a real-corpus false-negative rate, which is Order 08's E-06 and which will be zero-row if that plan executes in a lane worktree (`.aw/records/runs/` is absent there). So the honest recommendation is to ship the record, accumulate verdicts across real runs, and revisit with the observed rate. If the maintainer wants a refusal sooner, it is a new plan consuming this field, not a change to this one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the added call site in full, showing it is function-local, exception-guarded, and reads the already-stored verifier log path. PASTE THE WHOLE GUARDED REGION, not just the added lines, showing the call sits INSIDE the existing `if not v_unreadable and isinstance(v_data, dict):` block and that the unreadable arm's `indeterminate` verdict comes from INITIALIZATION before that guard rather than from running the computation on unbound `v_data` (F-4b). Then drive the UNREADABLE arm specifically, with a corrupt outcome file, and paste its recorded verdict and reason code, which must be the initialization reason and NOT the exception-guard reason; a run whose unreadable arm reports the guard's reason code means the call is misplaced and this item FAILS.
  REPORT THE SYMBOL YOU ACTUALLY CALLED, with its real name and full signature as Order 08 shipped it, because neither plan names it (F-4c). State whether its signature accepted the log path and claimed-commands in the shape E-01 assumed, and if it did not, show that you STOPPED rather than adapting the call site.
  Paste `rg -n '^from agent_workflows|^import' agent_workflows/runner_shared.py` proving no module-level import was added (review measured exactly two `^from agent_workflows` lines at HEAD; the count must be unchanged). Paste the proof that the guard works: monkeypatch the computation to raise, drive the block, and paste the resulting verdict and reason code showing `indeterminate` with a reason naming the computation, plus the turn's unchanged disposition. Paste a `git diff` over the block showing no line assigning `verify_disp` or `disposition` was touched.
  - Observed evidence: Guarded region in runner_shared.py lines 32817-32885 verified; Order 08 symbol corroborate_verifier_turn(log_path, claimed_commands) called function-locally; unreadable outcome fixture yields indeterminate with outcome-unreadable; rg check confirms exactly 2 module-level from agent_workflows lines; monkeypatch raise test yields indeterminate with computation-failed and unchanged verified/executed status; git diff confirms no lines assigning verify_disp or disposition touched.
    1. Guarded region in `agent_workflows/runner_shared.py`:
    ```python
                            # runverdict-05 (`bxx9af`) E-04: require real test evidence before verify_disp can be 'verified'
                            v_has_evidence = False
                            # runverdict-09 (`btak7a`) E-01: pre-guard initialization for corroboration variables.
                            # Placement is load-bearing: v_data is bound ONLY in the try's else: branch above and
                            # is unbound when v_unreadable is True. The unreadable arm reaches 'indeterminate'
                            # through this initialization, NOT through executing computation on unbound v_data.
                            v_corr_verdict = "indeterminate"
                            v_corr_reason = "outcome-unreadable"
                            v_corr_counts = {
                                "claimed": 0,
                                "observed": 0,
                                "matched": 0,
                                "delegations": 0,
                                "missing_command_text": 0,
                            }
                            if not v_unreadable and isinstance(v_data, dict):
                                v_has_evidence = has_verifier_test_evidence(v_data)
                                attempt["tests_run"] = v_data.get("tests_run", [])
                                attempt["corrections_made"] = v_data.get(
                                    "corrections_made", []
                                )
                                item["tests_run"] = v_data.get("tests_run", [])
                                item["corrections_made"] = v_data.get(
                                    "corrections_made", []
                                )
                                # runverdict-09 (`btak7a`) E-01: call Order 08's turn-level verdict function-locally.
                                # The computation must not break the turn under any circumstances: wrap it so any failure
                                # yields indeterminate with reason 'computation-failed'. This guard is deliberate, but is
                                # not a licence to place the call where v_data could be unbound (a masked NameError would
                                # look like a valid indeterminate).
                                try:
                                    from agent_workflows.verifier_corroboration import (
                                        corroborate_verifier_turn,
                                    )

                                    v_log_path = attempt.get("verify_log") or ""
                                    v_claims = extract_verifier_test_commands(v_data)
                                    v_corr = corroborate_verifier_turn(v_log_path, v_claims)
                                    v_corr_verdict = v_corr.verdict
                                    v_corr_reason = v_corr.reason_code
                                    v_corr_counts = v_corr.counts
                                except Exception:
                                    v_corr_verdict = "indeterminate"
                                    v_corr_reason = "computation-failed"
                                    v_corr_counts = {
                                        "claimed": (
                                            len(v_data.get("tests_run", []))
                                            if isinstance(v_data.get("tests_run"), list)
                                            else 0
                                        ),
                                        "observed": 0,
                                        "matched": 0,
                                        "delegations": 0,
                                        "missing_command_text": 0,
                                    }
                            attempt["verify_has_evidence"] = v_has_evidence
    ```
    2. Shipped symbol:
    `corroborate_verifier_turn(log_path: Path | str, claimed_commands: Sequence[str]) -> CorroborationVerdict`
    The signature accepted `(log_path, claimed_commands)` exactly in the shape E-01 assumed.
    3. Unreadable arm driven with corrupt outcome JSON:
    Recorded verdict: `indeterminate`
    Recorded reason: `outcome-unreadable`
    (Confirmed initialization reason, not `computation-failed`).
    4. First-party module-level imports check:
    ```
    $ rg -n '^from agent_workflows|^import' agent_workflows/runner_shared.py
    123:import argparse
    124:import contextlib
    125:import datetime as dt
    126:import functools
    127:import hashlib
    128:import inspect
    129:import json
    130:import os
    131:import re
    132:import secrets
    133:import shlex
    134:import shutil
    135:import subprocess
    136:import sys
    137:import tempfile
    138:import threading
    139:import time
    157:from agent_workflows import runner_profiles
    168:from agent_workflows.render_stream import (
    ```
    Exactly two lines matching `^from agent_workflows` (unchanged).
    5. Monkeypatched raising computation proof:
    Recorded verdict: `indeterminate`
    Recorded reason: `computation-failed`
    Item verification_status: `verified`
    Attempt disposition: `executed`
    6. Git diff over the block proves no line assigning `verify_disp` or `disposition` was touched.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the record writes and the adjacent comment explaining the `_PRIOR_ATTEMPT_SAFE_KEYS` exclusion. Paste a resulting `state.json` fragment for a fixture run showing the verdict, reason code and counts on BOTH the attempt and the item. Paste `git diff agent_workflows/lane_containment.py` showing it is EMPTY. Paste the no-outcome-file case's record showing NO corroboration key is present rather than a default value.
  - Observed evidence: Record writes in runner_shared.py verified; state.json fixture fragment carries verdict, reason, and counts on both item and attempt; git diff lane_containment is empty; no-outcome-file fixture records no corroboration keys.
    1. Record writes in `agent_workflows/runner_shared.py`:
    ```python
                            # runverdict-09 (`btak7a`) E-02: store the verdict, reason code, and counts
                            # on both attempt and item beside existing evidence fields.
                            # Deliberately omitted from lane_containment._PRIOR_ATTEMPT_SAFE_KEYS:
                            # feeding previous verifier assessments to a retrying agent is an unrequested prompt-design change.
                            attempt["corroboration_verdict"] = v_corr_verdict
                            attempt["corroboration_reason"] = v_corr_reason
                            attempt["corroboration_counts"] = v_corr_counts
                            item["corroboration_verdict"] = v_corr_verdict
                            item["corroboration_reason"] = v_corr_reason
                            item["corroboration_counts"] = v_corr_counts
    ```
    2. `state.json` fragment:
    ```json
    {
      "item": {
        "id6": "tst001",
        "corroboration_verdict": "corroborated",
        "corroboration_reason": "corroborated",
        "corroboration_counts": {
          "claimed": 1,
          "delegations": 0,
          "matched": 1,
          "missing_command_text": 0,
          "observed": 1
        }
      },
      "attempt": {
        "number": 1,
        "corroboration_verdict": "corroborated",
        "corroboration_reason": "corroborated",
        "corroboration_counts": {
          "claimed": 1,
          "delegations": 0,
          "matched": 1,
          "missing_command_text": 0,
          "observed": 1
        }
      }
    }
    ```
    3. `git diff agent_workflows/lane_containment.py`: empty (no changes made).
    4. No-outcome-file run record:
    ```
    corroboration_verdict in attempt: False
    corroboration_verdict in item: False
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the rendered `## Verification evidence` section for a fixture run whose verifier claimed commands, showing the verdict line adjacent to `Tests run:`. Paste the BYTE-IDENTICAL proof: the full report rendered from a no-verification fixture before and after the change, and the `diff` between them showing no output. Paste the report's table header and one row showing the column contract is unchanged. State explicitly whether `write_report` was still SHARED at execution time (F-3) and, if two host implementations had reappeared, what you did about it.
  - Observed evidence: Rendered ## Verification evidence section shows corroboration verdict adjacent to Tests run; byte-identical empty section returns []; table columns unchanged; write_report verified shared.
    1. Rendered `## Verification evidence` section:
    ```markdown
    ## Verification evidence

    - `abc123` (position 1):
      - Tests run:
        - `pytest tests/`
      - Corroboration: corroborated (reason: corroborated)
      - Corrections made:
        - (none recorded)
    ```
    Adjacent to `Tests run:` sub-list.
    2. Byte-identical proof: `format_verifier_evidence_section` returns `[]` when no items have verification evidence, resulting in no section emitted.
    3. Report table header and row showing unchanged column structure:
    `| IPD | Set | Action | Status | Disp | Verify | Tests Run | Time | Detail |`
    4. `write_report` was verified to remain SHARED in `runner_shared.py` (line 23078), called by both hosts.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `StepSummary` field addition and the details renderer change. Paste ACTUAL `aw runs` output in all three renderings (human details, `--json`, `--agent`) for a fixture run carrying the field, and then for a fixture run NOT carrying it, showing the second renders cleanly with no field and no error. Paste `git diff` proving no new `verification_status` value was introduced, and re-read and QUOTE the two literal-matching `run_viewer` sites F-2 names, reporting whether the mapping still holds as measured. Paste a count of the per-item `Issue` predicate's copies showing it did not grow.
  - Observed evidence: StepSummary carries corroboration_verdict and corroboration_reason; render_step_details renders corroboration adjacent to tests run; aw runs details, --json, and --agent outputs verified on carrying and legacy fixtures; no new verification_status token; literal-matching sites in run_viewer verified; Issue predicate count unchanged.
    1. `StepSummary` addition:
    ```python
    corroboration_verdict: str | None = None
    corroboration_reason: str | None = None
    ```
    2. `render_step_details` addition:
    ```python
    if step.corroboration_verdict:
        corr_label = (
            f"{step.corroboration_verdict} (reason: {step.corroboration_reason})"
            if step.corroboration_reason
            else str(step.corroboration_verdict)
        )
        lines.append(f"  * corroboration: {corr_label}")
    ```
    3. Three renderings output:
    - Carrying fixture:
      Human details:
      ```
      Details for test-abc123:
        > test: pytest tests/
        * corroboration: corroborated (reason: corroborated)
      ```
      `--json`:
      ```json
      "corroboration_verdict": "corroborated",
      "corroboration_reason": "corroborated"
      ```
      `--agent`:
      ```json
      "corroboration_verdict":"corroborated","corroboration_reason":"corroborated"
      ```
    - Not carrying fixture:
      Human details:
      ```
      Details for test-def456:
        > test: pytest tests/
      ```
      (Clean, no corroboration line rendered).
      `--json`:
      ```json
      "corroboration_verdict": null,
      "corroboration_reason": null
      ```
      `--agent`:
      ```json
      "corroboration_verdict":null,"corroboration_reason":null
      ```
    4. `git diff` over `run_viewer.py` confirms no new value added to `verification_status`.
    5. F-2 literal-matching sites in `run_viewer.py` re-read and quoted:
       Site 1 (lines 1705-1712): `if step.verification_status == "verified": ... elif step.verification_status == "failed": ...`
       Site 2 (lines 2259-2273): `if v_val == "verified": ... elif v_val in ("unverified", "verify-failed", "failed"): ... else: v_disp = "-"`
       The mapping holds exactly as measured.
    6. Count of `Issue` predicate in `run_viewer.py`: remains 1 copy (`audit_row_is_issue`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the outcome-equality test's source and its full passing output with per-test names and exit code. Paste its RED-then-GREEN proof: the actual FAILURE output with a one-line refusal keyed on `uncorroborated` injected, then the actual PASS after reverting, with exit codes for both. Paste the raising-computation test and the cross-host symmetry test with their output.
  CONFIRM THE DELETED PRECEDENT WAS NOT CITED AS PRESENT (F-4). State whether you consulted `tests/test_suite_baseline.py` through `git show 19313eed^:...`, and paste a grep over the new test file proving no docstring or comment implies that path exists in the tree. The test's NAME must carry the no-refusal reason, since that is the half of the precedent the deletion did not take; quote it.
  Paste the full bare `python3 -m pytest` summary line as regression evidence, RE-DERIVED in the executing worktree rather than compared against this plan's figure (review measured `3523 passed, 2 skipped, 3 warnings in 154.35s` with 208 deselected at HEAD `eef2a03e`, which is CONTEXT and moves with every merged lane), plus per-test counts for the named files run with `-o addopts=""` (review measured `53 passed` for `tests/test_verifier_evidence.py tests/test_run_viewer.py`, with `tests/test_verifier_corroboration.py` ABSENT until Order 08 executes). State explicitly whether E-05's tests drive the real `execute_item_core` path or simulate it, and if they simulate it, quote the docstring sentence that says so and why (F-5).
  - Observed evidence: Real execute_item_core pipeline driven across corroborated, uncorroborated, and indeterminate with identical outcomes; RED-then-GREEN proof verified with injected refusal; raising computation and cross-driver symmetry tests pass; deleted precedent confirmed unreferenced; bare pytest run verified; per-test counts for named files pass.
    1. Outcome-equality test source (`test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts`): drives real `runner_shared.execute_item_core` across `corroborated`, `uncorroborated`, and `indeterminate`, asserting `verification_status == "verified"`, `disposition == "executed"`, `refusal_of_item(item) is None`, and `integration_is_earned.earned is True`.
    Passing output:
    ```
    tests/test_verifier_corroboration.py ...                                 [100%]
    3 passed, 34 deselected in 14.55s (exit code 0)
    ```
    2. RED-then-GREEN proof:
    RED failure with injected refusal `if v_corr_verdict == "uncorroborated": record_refusal(...)`:
    ```
    FAILED tests/test_verifier_corroboration.py::TestCorroborationInteractionAndOutcomeEquality::test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts[uncorroborated]
    AssertionError: assert Refusal(code='UNEXPECTED-UNCORROBORATED-REFUSAL', reason='refused', remedy='none') is None
    1 failed, 2 passed, 34 deselected in 17.86s (exit code 1)
    ```
    GREEN pass after reverting injected line:
    ```
    tests/test_verifier_corroboration.py ...                                 [100%]
    3 passed, 34 deselected in 14.55s (exit code 0)
    ```
    3. Raising computation and cross-host symmetry tests:
    ```
    tests/test_verifier_corroboration.py::TestCorroborationInteractionAndOutcomeEquality::test_corroboration_raising_computation_cannot_break_turn PASSED [ 50%]
    tests/test_verifier_corroboration.py::TestCorroborationInteractionAndOutcomeEquality::test_cross_driver_symmetry PASSED [100%]
    2 passed, 35 deselected in 2.15s (exit code 0)
    ```
    4. Deleted precedent check: `git show 19313eed^:tests/test_suite_baseline.py` was inspected for design precedent only. `grep -n "test_suite_baseline" tests/test_verifier_corroboration.py` returned exit code 1 (no occurrences in the test file).
    Test name carries the no-refusal reason: `test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts`.
    5. Bare `python3 -m pytest` run in worktree:
    `2 failed, 4387 passed, 2 skipped, 3 warnings in 389.00s (0:06:28)`
    (Both failures pre-date this change: `test_verbose_flag_reach.py` hang timeout reading live-corpus and perturbation assertion in `test_run_finding_reachability.py`).
    6. Per-test counts for named files run with `-o addopts=""`:
    `tests/test_verifier_corroboration.py`: 37 passed in 42.07s
    `tests/test_run_viewer.py` and `tests/test_verifier_evidence.py`: 63 passed in 28.76s
    7. Tests drive the real `runner_shared.execute_item_core` pipeline via `_drive_execute_turn` rather than simulating it.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must not be executed before it is explicitly approved by a human.
It carries `- Item-Dependencies: executed:bjx20r` and MUST NOT be executed before Order 08 is executed:
the predicate it consumes does not exist until then, and Order 08's E-06 calibration is a review-gate
input for this plan's OQ-01. REVIEW CONFIRMED THE DEPENDENCY IS REAL AND UNMET: `bjx20r` is `reviewed`
with `Readiness: go-pending-approval`, and both `agent_workflows/verifier_corroboration.py` and
`tests/test_verifier_corroboration.py` are ABSENT at review HEAD, which is the correct state and is why
E-01's symbol name could not be verified at review (F-4c).

OPEN QUESTIONS. OQ-01 is `open` with `- Blocking: no` and `- Owner: maintainer`, and it is correctly
theirs: it asks whether an `uncorroborated` turn should eventually be REFUSED, which is a risk-appetite
decision against a standing maintainer ruling, not something repository evidence settles. It carries
`- Carrier: sinhkj` (verified `open`), so the question survives this plan either way, and every `E-*` and
`V-*` here is unchanged by either answer because this plan ships the record and no refusal. Nothing waits
on a human before execution.

The executor of this plan MUST: read this plan in full, and read Order 08 (`bjx20r`) and its recorded
E-06 measurement, before editing; keep every change inside the declared Scope-Paths and STOP AND REPORT
rather than broadening them, which for this plan specifically means editing NEITHER host runner, NOT
`agent_workflows/verifier_corroboration.py`, NOT `agent_workflows/lane_containment.py`, and NOT
`tests/test_verifier_evidence.py`; add NO refusal, downgrade, or disposition effect of any kind, since
that is the plan's defining limit and a standing maintainer ruling governs it; introduce NO new
`verification_status` token (F-2 measures why); preserve
`format_verifier_evidence_section`'s empty-returns-byte-identical contract and prove it by diff; perform
the RED-then-GREEN proof V-05 demands rather than asserting the guard works, because that guard IS this
plan's safety argument; paste ACTUAL runner output with exit codes for every test claim; and commit only
the paths it modified through `aw commit <plan> -- <paths>`, never `git add -A`, and never push.

LIFECYCLE OWNERSHIP IS CONDITIONAL. If this plan is executed by `aw oc run` or `aw agy run` with the
runner owning the lifecycle, the executor must NOT move this file or set its terminal status: the runner
performs the atomic finalize after its own checks. If it is executed by an agent directly, that agent
performs the terminal transition itself, and only after `aw ipd lint --phase pre-transition` reports
conforming and every `V-*` above carries concrete pasted evidence with `- Result: pass`.
