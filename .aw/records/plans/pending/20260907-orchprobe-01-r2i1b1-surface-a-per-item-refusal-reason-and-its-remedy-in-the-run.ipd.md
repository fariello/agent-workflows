# IPD: Surface a per-item refusal reason and its remedy in the run summary and aw runs

- Date: 2026-09-07
- Kind: child
- Concern: A run can refuse an item for a reason no surface reports. Measured 2026-09-07 and RE-VERIFIED 2026-09-08 at round 2 (all coordinates below re-measured; they drifted in one day, so locate by symbol): the end-of-run summary's diagnostics block (`render_stream.render_run_summary_table`, block at `:2152-2178`, was `:2124-2150`) keys on a HARDCODED status allowlist (`dependency-blocked`, `failed-safely`, `integration-blocked`, `merge-conflict`, `interrupted`), so any other refusal produces a table row and NO diagnostic line. `aw runs`' `Issue` column (`run_viewer.render_steps_table`, `:1498`) is computed only from `missing_entirely`/`location_mismatch`/`status_mismatch`, all of which describe a plan being in the wrong DIRECTORY, so a semantic refusal leaves the column reading `no`. And neither surface has any field for a REMEDY: both report what happened, never what to do about it. This is a defect today, independent of the probe that motivated finding it, which is why it is Order 01 and depends on nothing.
  IT IS WORSE THAN AN ALLOWLIST, AND THE DIFFERENCE CHANGES THIS PLAN. ALL COORDINATES RE-MEASURED AT ROUND 2 (they drifted within a day; locate by symbol). Re-measured by rendering the real function with the fields the runners actually write: only THREE of the five allowlisted statuses emit a line at all. `integration-blocked` and `merge-conflict` emit NOTHING, because the branch that would render them (`:2166-2171`) requires `driver_error` while the code that sets those statuses writes `integration_deferral` instead (`oc_runipd.py:6554`, `agy_runipd.py:3815`; `driver_error` is written at exactly one site per host, `oc_runipd.py:7246` / `agy_runipd.py:4467`, for `failed-safely`). So two of the five are ALREADY invisible today, and the existing test passes only because it supplies `driver_error` on a `failed-safely` item (`tests/test_run_summary_table.py:198`). "Preserve the four existing special cases verbatim" would therefore have preserved a live defect as a requirement. ROUND-2 CONTROL, which isolates the cause to the field NAME rather than the status: supplying `driver_error` on an `integration-blocked` item DOES render a line. See F-4.
- Scope: The two READ surfaces and the state they read. IN: a per-item `refusal` record (reason code, human reason, remedy) written into run state by whatever refuses; the summary's diagnostics block rendering it for ANY status rather than an allowlist, and repairing the two statuses that render nothing today; `aw runs` reporting it in the `Issue` column, in the artifact-discrepancy summary, and in the `--json`/`--agent` payloads, through ONE shared predicate rather than the five copies that exist. OUT: adding any new refusal (child 03 does that); changing what any existing gate decides; the verdict cache (child 02).
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/run_viewer.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_summary_table.py, tests/test_refusal_surfacing.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: orchprobe
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: r2i1b1
- Approval: 2026-09-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-08 approved (aw set): status set to approved
- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-005 closed, PR-010..PR-013 FIXED, no open questions remain. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. ROUND 1's TECHNICAL WORK VERIFIED IN FULL, WHICH IS THE MAIN RESULT: every load-bearing claim was re-executed rather than re-read, and all of it holds. F-4 was RE-REPRODUCED by calling the real `render_run_summary_table(state, pal=Palette(False))` per status with the fields the runners actually write: `dependency-blocked` True, `failed-safely` True, `integration-blocked` FALSE, `merge-conflict` FALSE, `interrupted` True, plus a NEW control (the same item supplied `driver_error` instead DOES render) that isolates the cause to the field NAME rather than the status, which is the sharpest form of the finding and is now in the plan. F-2's five predicate copies were re-grepped and are all still at `run_viewer.py:1349`/`:1498`/`:2564`/`:2608`/`:2639`. E-01's circular-import argument was re-verified by AST walk and is exactly right: `render_stream` imports ZERO first-party modules while `runner_shared.py:136` imports it, so `render_stream` is the only legal home; that reasoning is now its own finding F-7 so it cannot be lost. The oc-to-agy import count is still exactly 47, so E-08's assertion stands unchanged. THE FINDING THAT MATTERED WAS THE GATE ASSERTING A BLOCKER THAT DOES NOT EXIST (PR-010): it said "EXECUTION IS BLOCKED ON OQ-02 ... OQ-02 carries `Blocking: yes`", while OQ-02 has carried `- Blocking: no` / `- Status: resolved` since the maintainer's 2026-09-07 ruling; measured, `has_unresolved_blocking_question` returns False and `approval_refusals` named ONLY the stale `- Readiness: no-go`. The OPERATIONAL concern inside that paragraph is real and was kept, restated as what it actually is: a merge-ordering hazard, because OQ-02's chosen fix edits both host runners at the same functions `integpath`'s approved `51vw4y` and `rl67b0` are editing. CITATION DRIFT, corrected in five places: the diagnostics block is `:2152-2178` (was `:2124-2150`), its F-4 branch `:2166-2171` (was `:2138-2143`), and the four runner sites are `oc_runipd.py:6554`/`:7246` and `agy_runipd.py:3815`/`:4467` (was `:6498-6512`/`:7204`/`:3798-3811`/`:4464`); E-02 now says to locate by the `# Failure / Dependency block diagnostics` comment rather than by line, since these moved within one day. E-02 also now states the repair DIRECTION that OQ-02 chose (fix the runners, not the renderer), which was recorded only in the question. Baseline re-measured: `1 failed, 5648 passed, 3 skipped, 2 xfailed` versus round 1's `5632 passed`, an identical failure set with a total that moved by 16, which is this plan's own node-ids-not-totals rule demonstrated in a day.
- 2026-09-08 to-review (aw set): status set to to-review
- 2026-09-07 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; PR-001..PR-009, eight FIXED and one OPEN. THE BLOCKER IS A FALSE PREMISE THAT WOULD HAVE BEEN FROZEN AS A REQUIREMENT. E-02 said to keep "the four existing special cases working verbatim (their wording is asserted by existing tests)" and V-02 demanded byte-identical output for each. Measured by rendering the real function with the fields the runners actually write: only THREE of the five allowlisted statuses emit any line, because the `integration-blocked`/`merge-conflict` branch gates on `driver_error` while both hosts write `integration_deferral` for those two (`oc_runipd.py:6498-6512`, `agy_runipd.py:3798-3811`). So "byte-identical to before" for those two means "still nothing", and V-02 would have PASSED on a defect. Now E-02 repairs them and V-02 requires the before/after contrast pasted. SECOND, the `Issue` predicate is FIVE copies, not one (`run_viewer.py:1349`, `:1498`, `:2564`, `:2608`, `:2639`, spanning `format_artifact_audit_summary`, `render_steps_table` and three `run_viewer_cli` branches), and the plan named only one, so `aw runs` would have said YES in the table and omitted the same item from `--json`, `--agent` and `--issues`: new E-03 extracts one predicate, E-04 wires the machine surfaces. THIRD, a CIRCULAR IMPORT was latent: E-01 put the record in `runner_shared` while E-02 has `render_stream` read it, but `runner_shared` already imports `render_stream` at module level (`:136`), so the reverse edge cannot exist; E-01 now sites the dataclass in `render_stream` with the reason. OPEN: OQ-02 (`Blocking: yes`, PR-005) asks whether repairing those two statuses is in this child's fence, since it edits both host runners to do it. ALSO FIXED: the stale baseline note (`test_run_viewer` is 46 passed, not ~14 known failures) (PR-006), the "~46" import count (measured 47) (PR-007), `--detail`-only siting of the remedy (PR-004), a `Scope-Paths` naming a test file the plan never edits while omitting the one it must (PR-008), and an OQ-01 that licensed touching asserted strings without saying which (PR-009).

- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make any refusal a run produces visible in both the end-of-run summary and `aw runs`, carrying not just what happened but what the reader should do next. After this child, a new refusal kind is surfaced by construction rather than by remembering to extend an allowlist.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: a refusal record that carries its own remedy

- [x] E-01 Define ONE shared refusal record: a reason CODE (stable, machine-readable), a human REASON (what happened), and a REMEDY (what to do next). Store it on the queue item so it is durable in run state rather than only printed. The remedy field is the point: `AGENTS.md` records that a gate saying only "X is forbidden" gets complied with by DELETION, so every refusal this system produces must name the constructive action.
  SITE IT IN `render_stream.py`, NOT `runner_shared.py`, and the reason is mechanical rather than aesthetic: `runner_shared` ALREADY imports `render_stream` at module level (`runner_shared.py:136`, `from agent_workflows.render_stream import Palette, render_run_summary_table`), so the reverse edge E-02 needs (the renderer reading the record) cannot exist without a circular import. `render_stream` imports no first-party module at all today (only stdlib), which is what makes it the safe home for a type both a renderer and the runners read. If a later reader believes `runner_shared` is the better home, that requires moving `render_run_summary_table`'s import first, which is a different change.
  - Depends on: none
  - Expected outcome: a single definition in `render_stream`, imported by `oc_runipd`, `agy_runipd` and `runner_shared`, with the remedy as a required field rather than an optional one; `render_stream` still imports no first-party module.
  - Execution state: performed

- [x] E-02 Make the summary's diagnostics block render a refusal record for ANY status, replacing the hardcoded allowlist inside `render_stream.render_run_summary_table` (the block begins at the comment `# Failure / Dependency block diagnostics`, `:2152` at round 2, was `:2124`; LOCATE BY THAT COMMENT OR BY SYMBOL, never by line number, since these coordinates drifted between review rounds). Add a general branch so an item carrying a refusal record is reported whatever its status.
  DO NOT PRESERVE THE CURRENT BEHAVIOR OF ALL FIVE STATUSES: two of them are BROKEN and preserving them is preserving the defect. Re-reproduced at round 2 by calling the real function with the fields the runners actually write, only `dependency-blocked`, `failed-safely` and `interrupted` emit a line. `integration-blocked` and `merge-conflict` emit NOTHING, because their branch requires `driver_error` while the code setting those statuses writes `integration_deferral` (`oc_runipd.py:6554`, `agy_runipd.py:3815`; both re-measured at round 2, was `:6498-6512`/`:3798-3811`). Repair those two so they render their `integration_deferral` reason. PRESERVE VERBATIM only the three that work, whose exact strings are asserted at `tests/test_run_summary_table.py:211-214`.
  THE REPAIR DIRECTION IS FIXED BY OQ-02's RESOLUTION AND IS NOT THE OBVIOUS ONE: fix the RUNNERS to write the reason under the name the renderer reads, rather than teaching the renderer a second field name. That is the source-side fix, and it means this E-item edits both host runners, which is why the gate carries a merge-ordering instruction relative to `integpath`'s `51vw4y` and `rl67b0`.
  - Depends on: E-01
  - Expected outcome: an item with a refusal record always yields a diagnostic line whatever its status; the three WORKING special cases render byte-identically to before; `integration-blocked` and `merge-conflict` now render their reason where they previously rendered nothing.
  - Execution state: performed

- [x] E-03 Extract the `aw runs` ISSUE PREDICATE into ONE function and route every caller through it. It is currently FIVE copies of the same three-term expression (`run_viewer.py:1349` in `format_artifact_audit_summary`, `:1498` in `render_steps_table`, and `:2564`/`:2608`/`:2639` in three `run_viewer_cli` branches serving `--json`, `--agent --issues` and human `--issues`). Extract before extending, because extending one copy is what makes the surfaces disagree. Do not change what the three existing terms mean.
  - Depends on: E-01
  - Expected outcome: one predicate function; all five sites call it; behavior identical before the extension lands (prove it with the suite, not by inspection).
  - Execution state: performed

- [x] E-04 Extend that ONE predicate to count a refusal record as an issue, so the `Issue` column reads YES and the SAME item appears in `--json`, `--agent`, `--issues` and the artifact-discrepancy summary. This is the item that makes the surfacing real for tooling: a human-only fix would leave `aw runs --agent` reporting a clean run.
  - Depends on: E-03
  - Expected outcome: a refused item is reported as an issue by every one of the five call sites; a clean run is unchanged at all five.
  - Execution state: performed

- [x] E-05 Make the reason and remedy VISIBLE WITHOUT A FLAG. `render_step_details` (`run_viewer.py:1537`) is called only under `if detail:` (`:1699`, `:1737`), so putting the remedy only there means the default `aw runs` shows YES and never says why or what to do, which defeats the purpose. Decide and record where the remedy appears by default (the step row, a per-run note block, or the discrepancy table) and put the full reason plus remedy in the detail view as well. Also add both to the machine payloads, so `--json`/`--agent` carry the code, reason and remedy as fields rather than embedded prose.
  - Depends on: E-04
  - Expected outcome: bare `aw runs` on a refused run shows the remedy with no flag; `--detail` shows the full reason; `--json` and `--agent` each carry code, reason and remedy as discrete fields.
  - Execution state: performed

- [x] E-06 Add a REGRESSION GUARD against the allowlist shape returning. A test must fail if the summary's diagnostics block regains a closed set of statuses, because that is the exact defect F-1 records and it would silently re-hide every future refusal. Assert on behavior (an unknown status with a refusal record still yields a line), not on source text.
  - Depends on: E-02
  - Expected outcome: a test that fails if a new refusal kind would be invisible.
  - Execution state: performed

- [x] E-07 Add a SECOND guard, for the defect class F-4 actually found: a branch whose rendering condition reads a field the producing code never writes. Assert for EVERY status the diagnostics block special-cases that the fields it reads are the fields a host runner actually sets, so a future status added with a new field name fails here instead of rendering silence. This is the guard whose absence let `integration-blocked` and `merge-conflict` be invisible while a test suite stayed green.
  - Depends on: E-02
  - Expected outcome: a test that fails if a special-cased status reads a field no runner writes.
  - Execution state: performed

- [x] E-08 Confirm both hosts share every symbol added, by OBJECT IDENTITY rather than grep, per the anti-re-fork discipline `2r306y`/`818uru` established. `agy_runipd` imports 47 names from `oc_runipd` (measured by AST walk 2026-09-07; backlog `cnwy8g` recorded 40 and it has grown), so a new symbol must not deepen that: import from `render_stream`, never from the other host's driver.
  - Depends on: E-01, E-02, E-04, E-05
  - Expected outcome: pasted proof that each new symbol is one object shared by both hosts and defined in `render_stream`, and that the oc-to-agy import count did not increase.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The wording rule is load-bearing, not stylistic. A refusal that names only the prohibition invites the destructive fix; the remedy field exists to make the constructive one obvious.
- `render_stream.py` is the ONE definition of runner wording, imported by both hosts, precisely so an improvement cannot re-fork (its own docstring cites the `Heartbeat` divergence as the failure it prevents). It also imports NO first-party module (stdlib only), which is the property E-01 depends on and must preserve.
- THE IMPORT DIRECTION IS FIXED AND ONE-WAY: `runner_shared` imports `render_stream` (`:136`), never the reverse. Any shared type a renderer must read therefore lives in `render_stream`.
- THE BASELINE, RE-MEASURED AT ROUND 2 AND STILL THE SAME SHAPE. Measured bare (`python3 -m pytest`) at HEAD `d2e76917`: `1 failed, 5648 passed, 3 skipped, 2 xfailed in 81.04s`. Round 1 recorded `1 failed, 5632 passed, 3 skipped, 2 xfailed` at `a6954bca`, so the pass TOTAL moved by 16 within a day while the failure SET did not change at all, which is this note's own rule demonstrated: compare failing NODE IDS, never totals. `tests/test_run_viewer.py` alone is still `46 passed`, so the old claim of "~14 known `agrlvw` failures" remains wrong and an executor trusting it would dismiss real failures in a module this plan edits. The ONE failure is still `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, which asserts `{"kgpptv": "reviewed"}` while `kgpptv` reads `- Status: approved`: a test coupled to this repository's mutable plan statuses, unrelated to this child. Re-measure in the executing worktree.
- Suite bare: `python3 -m pytest`. Work in an isolated worktree; this repo has concurrent agents.
- `aw check plans` REPORTS `check.lifecycle-transition-invalid` FOR THIS PLAN, AND IT IS A CHECKER GAP, NOT A DEFECT. Do not "fix" it by editing the history. The recorded stream is `draft -> to-review -> reviewed -> to-review -> reviewed`, and the `reviewed -> to-review` step is a REAL maintainer act performed via `aw set` that sent a reviewed plan back for another critique round. `ipd_lifecycle.validate_transition` treats any rank decrease as backwards and `check_lifecycle_transitions` exempts only off-sequence targets, so a legitimate re-review demotion has no representation. The flag pre-dates this review round. Rewriting that line to silence the checker would erase evidence of a maintainer decision and forge a cleaner history than the one that happened; the predicate belongs to the check engine, not to this Set. The same note appears on this Set's orchestrator (`yeh7gc`), which carries the same pattern, and a backlog item is warranted for the predicate itself.

## Findings

| Id | Severity | Location (2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `render_stream.render_run_summary_table`, block at `:2152-2178` (RE-MEASURED at round 2; was `:2124-2150`) | The diagnostics block keys on a hardcoded status allowlist, so any new refusal kind yields no line. RE-VERIFIED at round 2: the allowlist is still exactly the same five statuses and still has no default branch. Locate by the comment `# Failure / Dependency block diagnostics` (`:2152`), not by line number. | source re-read at round 2 |
| F-2 | HIGH | `run_viewer.py:1349`, `:1498`, `:2564`, `:2608`, `:2639` (ALL FIVE RE-VERIFIED UNMOVED at round 2) | The issue predicate is FIVE copies of one three-term expression, not one, spanning `format_artifact_audit_summary`, `render_steps_table` and three `run_viewer_cli` branches (`--json`, `--agent --issues`, human `--issues`). Extending one makes the surfaces DISAGREE: the table would say YES while `--json` omitted the same item. The plan originally named only `:1497`. | AST walk mapping each line to its enclosing function; re-grepped at round 2, all five still present at the same lines |
| F-3 | HIGH | both | No remedy field exists anywhere, so advice has nowhere to live. | source read |
| F-4 | BLOCKER | `render_stream.py:2166-2171` (branch); `oc_runipd.py:6554` (writes `integration_deferral`), `:7246` (writes `driver_error`); `agy_runipd.py:3815`, `:4467`. ALL RE-MEASURED AT ROUND 2; the round-1 coordinates `:2138-2143`/`:6498-6512`/`:7204`/`:3798-3811`/`:4464` have DRIFTED. | TWO OF THE FIVE ALLOWLISTED STATUSES RENDER NOTHING TODAY. The `integration-blocked`/`merge-conflict` branch requires `driver_error`, but the code that sets those statuses writes `integration_deferral`; `driver_error` is written at exactly ONE site per host, for `failed-safely`. So the plan's instruction to keep the existing cases "verbatim" would have frozen a live defect as a requirement, and V-02's byte-identical check would have PASSED on silence. The existing test passes only because it supplies `driver_error` on a `failed-safely` item. | RE-REPRODUCED AT ROUND 2 by calling the real `render_run_summary_table(state, pal=Palette(False))` with each status and the field the runners actually write: `dependency-blocked` True, `failed-safely` True, `integration-blocked` FALSE, `merge-conflict` FALSE, `interrupted` True. Control: `integration-blocked` supplied `driver_error` instead renders True, which isolates the cause to the field NAME rather than the status. |
| F-5 | MED | `run_viewer.py:1537`, `:1699`, `:1737` | `render_step_details` runs only under `if detail:`, so a remedy placed only there is invisible to bare `aw runs`. The reader who most needs the remedy is the one who just saw `Issue: YES` without a flag. | source read |
| F-6 | MED | measured | `agy_runipd` imports 47 names from `oc_runipd`, not the "~46" the plan cited; backlog `cnwy8g` recorded 40, so the coupling is still growing and a new symbol must not add to it. RE-MEASURED AT ROUND 2: still exactly 47, so the count is stable over this window and E-08's "did not increase from 47" remains the right assertion. | AST walk over `ImportFrom` nodes targeting `oc_runipd`, re-run at round 2 |
| F-7 | MED | `render_stream.py` import graph; `runner_shared.py:136` | RE-VERIFIED AT ROUND 2 because E-01's entire siting argument rests on it, and it holds exactly: an AST walk over `render_stream.py`'s `Import`/`ImportFrom` nodes finds ZERO first-party modules (stdlib only), while `runner_shared.py:136` does `from agent_workflows.render_stream import Palette, render_run_summary_table`. So the import edge is one-way today and `render_stream` is the only home for a type both a renderer and the runners read. | AST walk at round 2: `render_stream` first-party imports NONE; `runner_shared:136` confirmed |

## Proposed changes (ordered, validatable)

1. E-01 defines the record in `render_stream` (the only home the import graph allows).
2. E-02 makes the summary read it for any status AND repairs the two statuses that render nothing.
3. E-03 extracts the one issue predicate; E-04 extends it so every `aw runs` surface agrees.
4. E-05 puts reason and remedy where a reader without flags will see them, and in the machine payloads.
5. E-06 guards the allowlist shape from returning; E-07 guards the field-mismatch class F-4 found.
6. E-08 proves one definition across hosts without deepening the oc-to-agy coupling.

## Deferred / out of scope (with reason)

- Adding any new refusal: child 03. This child makes refusals VISIBLE; producing one is separate.
- The verdict cache: child 02.
- Moving `render_run_summary_table`'s import out of `runner_shared` so the record could live there instead: a different change with its own risk, recorded in E-01 rather than smuggled in.
- Retrofitting a REMEDY onto the three refusals that already render (see OQ-01): a separate judgement, because their strings are asserted.

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY for the two purposes E-02 and E-01 name (repairing the `integration_deferral` rendering path and importing the record). Do NOT change what any gate decides, and do not touch the integration logic itself; children 03/04 of the `integpath` Set are actively editing those same functions.
- Under-scope: none. The `--json`/`--agent` surfaces and the four extra predicate copies were under-scope before review and are now E-03/E-04/E-05.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured there and pasted, comparing failing NODE IDS not totals. `tests/test_run_summary_table.py:179-214` is the existing pin on the diagnostics wording and MUST be extended rather than rewritten: keep its three working assertions untouched and add the two repaired statuses.

## Spec / documentation sync

N/A for the surfacing itself: this child changes no documented contract, it fixes two surfaces that already promised to report problems. Child 03 owns the spec sync for the gate it adds.

ONE THING TO CHECK RATHER THAN ASSUME: if `aw runs`' `--json`/`--agent` payload shape is documented anywhere as a contract (a spec section, `run_cli` help text, or the `aw.agent/v1` envelope description), E-05 ADDS fields to it, and an additive change to a machine-readable envelope still belongs in the record. Confirm whether such a document exists and either amend it (declaring the file in `Scope-Paths`) or state that none does.

CHECKED AT EXECUTION 2026-09-14: NO SUCH DOCUMENT EXISTS, so there is nothing to amend and no spec file is added to `Scope-Paths`. Searched every tracked spec for the payload's own key (`grep -rn "artifact_discrepancies" --include=*.md .`): the only hit outside this Set's own plan/review records is this plan's review record quoting the plan. The command-surface spec (`20260818-1525-01`) describes verbs and flags, not the run payload's field set, and no spec section, `run_cli` help string, or `aw.agent/v1` envelope description enumerates the keys of an `artifact_discrepancies` record. The change is additive in any case: existing keys keep their names and meanings, and the two new keys (`issue_reasons`, `refusal`) are new names, so a consumer reading only the old fields is unaffected. Verified for the `--agent` surface specifically: `aw sanitize --agent` still emits a conforming `aw.agent/v1` envelope (`"outcome":"clean","exit":0`), so the shared envelope contract is untouched by this change.

## Open questions

### OQ-01: Should an existing refusal be retrofitted to carry a remedy?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-07 by the maintainer, and BROADENED beyond the original narrow question. The requirement is now explicit: every refusal must state BOTH what went wrong AND the likely correct fix, and it must appear in FOUR places: (1) the end-of-run summary, the one thing a human is guaranteed to read; (2) the START of the output; (3) the END of the output, because agents habitually pipe through `head` or `tail` and would otherwise miss it; and (4) both the `aw runs` report and the durable run logs. The start/end duplication is deliberate redundancy, accepted as the price of neither reader missing it. THE REASON IS THE WHOLE POINT: a message saying only 'abd123 contains items that are not allowed' very likely gets 'fixed' by DELETING items someone thought important enough to write, when a correct non-destructive fix exists. The three pinned strings at `tests/test_run_summary_table.py:211-214` must stay byte-identical; add the remedy as an ADDITIONAL line or field. If a given message cannot carry it without editing an asserted string, record that and leave the string alone.

### OQ-02: Is repairing the two broken statuses inside this child's fence?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-005
- Resolution or deferral rationale: RESOLVED 2026-09-07 by the maintainer: option (b), FIX BOTH RUNNERS to write the reason under the name the renderer reads. This is the more correct fix at the source rather than teaching the display a second name. ACCEPTED COST, stated because the review raised it: this touches `oc_runipd.py:6554` and `agy_runipd.py:3815` (re-measured at round 2; the round-1 coordinates have drifted), which the `integpath` children `51vw4y` and `rl67b0` are actively editing, so a merge conflict is possible; sequence this after those land, or coordinate. NOTE this bug is live and already cost the maintainer twice: `ueg5cf` and `pgq326` both reported an unhelpful reason because the renderer reads `driver_error` while the runners write `integration_deferral`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the record definition and a `python3 -c` showing both hosts resolve it to the SAME object, plus proof the remedy field is required (constructing one without it fails). ALSO paste proof the import graph is intact: `render_stream` still imports no first-party module (an AST walk over its `Import`/`ImportFrom` nodes), and importing `render_stream` alone in a fresh interpreter succeeds.
  - Observed evidence: the record definition, both `TypeError` (omitted remedy) and `ValueError` (blank remedy) arms, object-identity output for all five symbols across both hosts, and an AST walk showing `render_stream` still imports NO first-party module. Detail below.
    The record, `agent_workflows/render_stream.py` (`REFUSAL_KEY` + frozen dataclass, docstrings elided here):

    ```python
    REFUSAL_KEY = "refusal"

    @dataclass(frozen=True)
    class Refusal:
        code: str
        reason: str
        remedy: str

        def __post_init__(self) -> None:
            for field_name in ("code", "reason", "remedy"):
                value = getattr(self, field_name)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(...)
    ```

    REMEDY IS REQUIRED, both arms measured:

    ```
    $ PYTHONPATH=. python3 -c "from agent_workflows.render_stream import Refusal; Refusal(code='c', reason='r')"
    missing remedy -> TypeError: Refusal.__init__() missing 1 required positional argument: 'remedy'
    empty remedy   -> ValueError: Refusal.remedy must be a non-empty string (got '   '); a refusal
                      that cannot say what happened or what to do next is incomplete by construction
    ```

    ONE OBJECT IN BOTH HOSTS (object identity, not a behavioral comparison, which passes against a copy):

    ```
    symbol                                   owner id  oc is owner  agy is owner
    REFUSAL_KEY                       139031431542080         True          True
    Refusal                           104386569068848         True          True
    record_refusal                    139031431809504         True          True
    record_integration_refusal        139031431809856         True          True
    refusal_of_item                   139031431809152         True          True

    run_viewer.refusal_of_item is render_stream.refusal_of_item: True
    run_viewer.REFUSAL_KEY   is render_stream.REFUSAL_KEY  : True
    ```

    IMPORT GRAPH INTACT (F-7's property, which is E-01's entire siting argument). AST walk over
    `render_stream.py`'s `Import`/`ImportFrom` nodes:

    ```
    render_stream first-party imports: NONE (stdlib only)
    ```

    A fresh interpreter importing it alone succeeds (this is how the before/after harness in V-02
    loads the HEAD copy standalone, which would be impossible if the module had first-party imports).
    Asserted permanently by `test_render_stream_still_imports_no_first_party_module`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste rendered summary output for (a) an item with a refusal record and an UNKNOWN status, showing a diagnostic line; (b) the THREE working special cases (`dependency-blocked`, `failed-safely`, `interrupted`), showing their wording byte-identical to before; and (c) THE BEFORE/AFTER CONTRAST for `integration-blocked` and `merge-conflict`, rendered with the field the runners actually write (`integration_deferral`, NOT `driver_error`), showing NO diagnostic line before and the reason present after. Part (c) is the load-bearing half: "byte-identical to before" for those two would mean "still nothing", which is what the pre-review V-02 would have accepted.
  - Observed evidence: before/after rendered by loading the HEAD blob standalone beside the working tree in one process: the three working statuses byte-identical, `integration-blocked`/`merge-conflict` `[]` BEFORE and the reason present AFTER, an unknown status rendering reason plus remedy, and a THIRD dead status (`interrupted`) found and fixed. Detail below.
    METHOD, because it decides whether this evidence is worth anything: BEFORE is not a remembered
    measurement, it is the HEAD blob of `render_stream.py` loaded standalone with `importlib` and
    called side by side with the working-tree module in ONE process. That is possible only because the
    module has no first-party imports (V-01), and it makes the contrast a real execution rather than a
    claim. Harness output, run at HEAD `fea2c9f8` before the commit:

    ```
    working-tree package: <worktree>/agent_workflows/__init__.py
    HEAD blob rev:        fea2c9f84162a89d5f45d24cac3f6e8fbe78d53f

    === (b) THE THREE WORKING SPECIAL CASES: must be BYTE-IDENTICAL ===

    status=dependency-blocked
      BEFORE: ['  • aaa111: dependency-blocked (unmet dependencies)']
      AFTER : ['  • aaa111: dependency-blocked (unmet dependencies)']
      byte-identical: True

    status=failed-safely
      BEFORE: ['  • aaa111: failed-safely (merge conflict in tests/test_main.py)']
      AFTER : ['  • aaa111: failed-safely (merge conflict in tests/test_main.py)']
      byte-identical: True

    status=interrupted
      BEFORE: ['  • aaa111: interrupted (stall_timeout)']
      AFTER : ['  • aaa111: interrupted (stall_timeout)']
      byte-identical: True

    === (c) THE TWO REPAIRED STATUSES, with the field the RUNNERS write ===

    status=integration-blocked field=integration_deferral
      BEFORE: []   <- NO diagnostic line
      AFTER : ['  • aaa111: integration-blocked (dirty overlap on src/demo.txt; lane aw/lane/x preserved)']

    status=merge-conflict field=integration_deferral
      BEFORE: []   <- NO diagnostic line
      AFTER : ['  • aaa111: merge-conflict (dirty overlap on src/demo.txt; lane aw/lane/x preserved)']

    === (a) AN UNKNOWN STATUS CARRYING A REFUSAL RECORD ===
      BEFORE: []   <- allowlist had no branch for it
      AFTER : ['  • aaa111: orchestrator-refused (plan declares a step no child covers)',
               '    → remedy: add a child plan for that step; do NOT delete the orchestration checklist']
    ```

    So part (c) lands exactly as the plan predicted: `[]` before, the reason present after. Part (b)
    is byte-identical for all three, and `tests/test_run_summary_table.py` (which pins those exact
    strings) is `10 passed` unchanged.

    THE SOURCE HALF, per OQ-02's resolution: both hosts now record a `Refusal` at the integration
    failure site through the ONE shared writer `record_integration_refusal`
    (`oc_runipd.py` and `agy_runipd.py`, in the `if not integrated:` branch). `integration_deferral`
    is still written, so the existing consumers that assert on it are untouched.

    A THIRD DEAD STATUS FOUND AND FIXED, which the plan did not know about; see D-2 and V-07. F-4
    undercounted: `interrupted` was ALSO dead for real run state, because all eight producing sites
    write `interrupt_reason` on the ATTEMPT while the renderer read it off the ITEM. Measured:

    ```
    (1) runner-written shape (reason on the ATTEMPT):
        diagnostics: NONE  <-- the arm is DEAD for real state
    (2) test-only shape (reason hoisted onto the ITEM):
        diagnostics: ['  • aaa111: interrupted (stall_timeout)']
    ```

    Now read through `_interrupt_reason_of` (item-level first, so the pinned hoisted shape stays
    byte-identical), and regression-tested by
    `test_the_interrupted_arm_reads_where_the_runners_write`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the extracted predicate, and paste proof that all FIVE former call sites now call it (`run_viewer.py` at the former `:1349`, `:1498`, `:2564`, `:2608`, `:2639`; locate by enclosing function since the lines will move). Paste the suite green for `tests/test_run_viewer.py` showing the extraction alone changed no behavior, and confirm no sixth copy remains (a repo-wide search for the three-term expression returning only the predicate itself).
  - Observed evidence: the extracted `step_issue_reasons`/`step_has_issue`, a table mapping all five former call sites to their new call, a repo-wide search finding no sixth copy, and `86 passed` proving the extraction changed no behavior. Detail below.
    THE EXTRACTED PREDICATE, `agent_workflows/run_viewer.py`. It returns REASONS rather than a bool,
    because the two classes are independent (an artifact discrepancy is about a plan being in the wrong
    DIRECTORY; a refusal is semantic and typically has its artifact exactly where it belongs), and the
    surfaces need to say WHICH:

    ```python
    def step_issue_reasons(audit, step=None) -> list[str]:
        reasons: list[str] = []
        refusal = step_refusal(step) if step is not None else None
        if refusal is not None:
            reasons.append(f"refused: {refusal.reason}")
        if audit.missing_entirely:
            reasons.append("artifact missing")
        elif audit.location_mismatch:
            reasons.append("artifact in unexpected directory")
        if audit.status_mismatch:
            reasons.append("on-disk status disagrees with the run record")
        return reasons

    def step_has_issue(audit, step=None) -> bool:
        return bool(step_issue_reasons(audit, step))
    ```

    ALL FIVE FORMER CALL SITES NOW ROUTE THROUGH IT, located by enclosing function since the lines
    moved (the plan's `:1349`/`:1498`/`:2564`/`:2608`/`:2639` had drifted to
    `:1400`/`:1549`/`:2770`/`:2814`/`:2845` before I touched anything):

    | Former site | Enclosing function | Now calls |
    | --- | --- | --- |
    | `:1349` | `format_artifact_audit_summary` | `step_has_issue(a)` |
    | `:1498` | `render_steps_table` | `step_has_issue(audit, step)` |
    | `:2564` | `run_viewer_cli` `--json` | `_issue_records()` -> `step_issue_reasons` |
    | `:2608` | `run_viewer_cli` `--agent --issues` | `_issue_records()` -> `step_issue_reasons` |
    | `:2639` | `run_viewer_cli` human `--issues` | `step_has_issue(a, st)` |

    NO SIXTH COPY REMAINS. Repo-wide search for the three-term expression returns only prose inside the
    predicate's own docstring:

    ```
    $ grep -rn "missing_entirely or .*location_mismatch or .*status_mismatch" agent_workflows/ | grep -v artifact_audit.py
    agent_workflows/run_viewer.py:475:    three-term expression ``missing_entirely or location_mismatch or status_mismatch`` was copied at
    ```

    (`artifact_audit.py` is excluded deliberately: that is the OWNER's own `has_discrepancy` property,
    not a viewer copy.)

    THE EXTRACTION ALONE CHANGED NO BEHAVIOR, proven by the suite rather than by inspection:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_run_viewer.py tests/test_run_summary_table.py -o addopts="-q"
    ........................................................................ [ 83%]
    ..............                                                           [100%]
    86 passed in 4.54s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: for a run containing a refused item, paste ALL FIVE surfaces agreeing that it is an issue: the `Issue` column in the steps table, the artifact-discrepancy summary, `--json`, `--agent --issues`, and human `--issues`. Then paste the same five for a CLEAN run showing none reports an issue. A fix proven on one surface is exactly the disagreement F-2 predicts.
  - Observed evidence: all five surfaces on a refused run whose artifact is deliberately PERFECT (so the YES comes from the refusal alone), then the same five on a clean run reporting nothing. Detail below.
    METHOD: a real temp repo with a real `state.json` and a real plan file, driven through the actual
    `run_viewer_cli` entry point for each surface (not by calling helpers directly). THE ARTIFACT IS
    DELIBERATELY PERFECT - in `executed/` with `- Status: executed` matching the recorded status - so
    NONE of the three original audit terms can fire. Every YES below therefore comes from the refusal
    alone, which is the whole point of the test.

    A REFUSED RUN, all five surfaces:

    ```
    --- SURFACE 1: steps table `Issue` column (BARE, no flags) ---
    │ Status   │ Item                         │ Action  │ ... │ Verified │ Issue │
    │ executed │ 20260907-orchprobe-01-aaa111 │ execute │ ... │ yes      │ YES   │

    --- SURFACE 2: the discrepancy/refusals summary (BARE, no flags) ---
    Refusals (what the run declined, and what to do):
      ! 20260907-orchprobe-01-aaa111 [orchestrator-uncovered-work]: the orchestrator declares a step no child covers
        → remedy: add a child plan for that step; do NOT delete the orchestration checklist

    --- SURFACE 3: --json ---
    [
      {
        "id6": "aaa111",
        "missing_entirely": false,
        "location_mismatch": false,
        "status_mismatch": false,
        "issue_reasons": [
          "refused: the orchestrator declares a step no child covers"
        ],
        "refusal": {
          "code": "orchestrator-uncovered-work",
          "reason": "the orchestrator declares a step no child covers",
          "remedy": "add a child plan for that step; do NOT delete the orchestration checklist"
        }
      }
    ]

    --- SURFACE 4: --agent --issues ---
    {"id6":"aaa111",...,"missing_entirely":false,"location_mismatch":false,"status_mismatch":false,
     "issue_reasons":["refused: the orchestrator declares a step no child covers"],
     "refusal":{"code":"orchestrator-uncovered-work","reason":"the orchestrator declares a step no child covers",
     "remedy":"add a child plan for that step; do NOT delete the orchestration checklist"}}

    --- SURFACE 5: human --issues ---
    Refusals (what the run declined, and what to do):
      ! 20260907-orchprobe-01-aaa111 [orchestrator-uncovered-work]: the orchestrator declares a step no child covers
        → remedy: add a child plan for that step; do NOT delete the orchestration checklist
    ```

    Note the three artifact booleans are all `false` in surfaces 3 and 4 while `issue_reasons` names the
    refusal: that is precisely the case that used to leave the column reading `no`.

    THE SAME FIVE ON A CLEAN RUN (identical repo, refusal removed): none reports an issue.

    ```
    --- SURFACE 1: Issue column ---
    │ executed │ 20260907-orchprobe-01-aaa111 │ execute │ ... │ yes      │ no    │
    --- SURFACE 2: (no refusals block)
    --- SURFACE 3: --json                 -> []
    --- SURFACE 4: --agent --issues       -> (no records emitted)
    --- SURFACE 5: human --issues         -> no artifact or status discrepancies found
    ```

    Surface 5's clean-run wording is deliberately unchanged; see D-1 for why (it is reached only when
    there is nothing at all to report, and it is pinned by a test outside this plan's `Scope-Paths`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste BARE `aw runs` (no flags) on a refused run showing the remedy visible without `--detail`; paste `--detail` showing the full reason; paste `--json` and `--agent` showing code, reason and remedy as DISCRETE fields rather than embedded prose. Record which default location was chosen and why.
  - Observed evidence: bare `aw runs` showing the remedy with no flag, `--detail` showing the full untruncated reason, and `--json`/`--agent` carrying code/reason/remedy as discrete fields; the chosen default location and why. Detail below.
    DEFAULT LOCATION CHOSEN: a dedicated `Refusals` block rendered by `format_refusal_summary`,
    appended to the artifact-discrepancy summary region, so it appears on BARE `aw runs` with no flag.
    WHY THIS ONE of the three the plan offered: the step ROW is width-constrained box art (adding a
    remedy column would either truncate the remedy, which defeats it, or blow the table width), and the
    discrepancy TABLE is a five-column artifact-location grid whose columns mean nothing for a semantic
    refusal. A block has no width limit, so a full remedy sentence survives intact. It is also placed
    where a reader who just saw `Issue: YES` is already looking.

    BARE `aw runs`, NO FLAGS (the F-5 requirement: `render_step_details` runs only under `if detail:`,
    so a remedy placed only there would be invisible to exactly the reader who needs it):

    ```
    Refusals (what the run declined, and what to do):
      ! 20260907-orchprobe-01-aaa111 [orchestrator-uncovered-work]: the orchestrator declares a step no child covers
        → remedy: add a child plan for that step; do NOT delete the orchestration checklist
    ```

    `--detail`, the FULL untruncated reason and remedy (this view elides nothing):

    ```
      ! refused [orchestrator-uncovered-work]: the orchestrator declares a step no child covers
        → remedy: add a child plan for that step; do NOT delete the orchestration checklist
    ```

    Untruncated even at length, asserted by `test_the_detail_view_carries_the_full_reason_and_remedy`,
    which uses a 300-character reason and a 300-character remedy and requires both present in full.

    `--json`: code, reason and remedy as DISCRETE FIELDS, not embedded prose, so a tool reads the
    remedy without parsing a sentence:

    ```json
    {
      "refusal": {
        "code": "orchestrator-uncovered-work",
        "reason": "the orchestrator declares a step no child covers",
        "remedy": "add a child plan for that step; do NOT delete the orchestration checklist"
      }
    }
    ```

    `--agent` carries the same three keys per record (see V-04 surface 4), and the step objects in
    `--json`/`--agent` carry `refusal` as a nested object with those same discrete keys. On a clean run
    the field is `{"refusal": null}`.

    THE REMEDY IS ON ITS OWN LINE, deliberately: agents habitually pipe through `head`/`tail`, and a
    long reason must not be able to push the remedy off screen. Pinned by
    `test_the_remedy_is_on_its_own_line`, which uses a 400-character reason.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the guard test passing, AND a mutation check: reintroduce the allowlist, show the guard FAILS, revert, show it passes. A guard that cannot fail is not evidence.
  - Observed evidence: the guard passing (`28 passed`), the allowlist reintroduced making SIX assertions fail, and the revert passing again. Detail below.
    The guard is `tests/test_refusal_surfacing.py::TestNoStatusAllowlist`, asserting on BEHAVIOR (render
    a state, read the output) rather than on source text, because a guard that greps for `if status in
    (...)` passes the moment someone spells the allowlist differently.

    PASSING:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_refusal_surfacing.py -o addopts="-q"
    ............................                                             [100%]
    28 passed in 0.47s
    ```

    MUTATION CHECK. Allowlist reintroduced around the refusal branch
    (`if refusal is not None and st in ("failed-safely", "merge-conflict")`), which is the exact defect
    shape F-1 records:

    ```
    MUTATION APPLIED: allowlist reintroduced around the refusal branch
    FAILED tests/test_refusal_surfacing.py::TestNoStatusAllowlist::test_an_unknown_status_with_a_refusal_still_reports
    FAILED tests/test_refusal_surfacing.py::TestNoStatusAllowlist::test_every_status_shape_is_surfaced[verdict-cache-stale]
    FAILED tests/test_refusal_surfacing.py::TestNoStatusAllowlist::test_every_status_shape_is_surfaced[]
    FAILED tests/test_refusal_surfacing.py::TestNoStatusAllowlist::test_every_status_shape_is_surfaced[some-status-invented-in-2027]
    FAILED tests/test_refusal_surfacing.py::TestNoStatusAllowlist::test_every_status_shape_is_surfaced[orchestrator-refused]
    FAILED tests/test_refusal_surfacing.py::TestNoStatusAllowlist::test_the_remedy_is_on_its_own_line
    6 failed, 22 passed in 0.46s
    ```

    REVERTED, passing again:

    ```
    ............................                                             [100%]
    28 passed in 0.47s
    ```

    Six failures rather than one, which is the useful property: the guard does not depend on a single
    invented status name, so it detects a narrowed allowlist however the narrowing is spelled.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the guard passing, AND a mutation check that reproduces F-4 specifically: point one special-cased status's condition at a field no runner writes, show the guard FAILS, revert, show it passes. This is the guard whose absence let two statuses render silence under a green suite, so a version that cannot detect that exact mutation is not evidence.
  - Observed evidence: the guard FINDING A REAL THIRD DEFECT on first run before any mutation, then the F-4 mutation (a status reading a field no runner writes) failing three assertions, then the revert passing. Detail below.
    The guard is `tests/test_refusal_surfacing.py::TestNoFieldNameMismatch`. It compares TWO AST-derived
    sets that nobody had ever compared, which is the root cause of F-4: the fields the diagnostics block
    READS (scoped to that block, so an unrelated `it.get(...)` elsewhere cannot pad the set and dilute
    the guard) against the fields either host runner WRITES to an item.

    THIS GUARD FOUND A REAL, UNKNOWN THIRD DEFECT ON FIRST RUN, which is the strongest possible evidence
    that it works. It failed immediately, before any mutation:

    ```
    AssertionError: the diagnostics block reads ['interrupt_reason'], which NO runner writes.
    This is F-4's defect class: such a branch renders SILENCE while the suite stays green.
    ```

    Verified as a true positive, not a guard artifact: all eight producing sites write
    `attempt["interrupt_reason"]` and set only `item["status"] = "interrupted"`
    (`oc_runipd.py:6456`, `:6486`, `:6528`; `agy_runipd.py:3603`, `:3628`, `:3669`;
    `runner_shared.py:1104`, `:1197`). Rendering both shapes confirmed the arm was dead for real state;
    see V-02's third-status evidence and D-2. Fixed via `_interrupt_reason_of`.

    PASSING after that fix:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_refusal_surfacing.py -o addopts="-q"
    ............................                                             [100%]
    28 passed in 0.47s
    ```

    MUTATION CHECK REPRODUCING F-4 EXACTLY. A special-cased status's condition pointed at a field no
    runner writes (`integration_deferral` -> `integration_blocked_because`):

    ```
    MUTATION APPLIED: a special-cased status now reads a field NO runner writes
    FAILED tests/test_refusal_surfacing.py::TestNoFieldNameMismatch::test_every_field_the_diagnostics_block_reads_is_one_a_runner_writes
    FAILED tests/test_refusal_surfacing.py::TestNoFieldNameMismatch::test_the_two_repaired_statuses_render_the_field_the_runners_write[merge-conflict]
    FAILED tests/test_refusal_surfacing.py::TestNoFieldNameMismatch::test_the_two_repaired_statuses_render_the_field_the_runners_write[integration-blocked]
    3 failed, 25 passed in 0.45s
    ```

    Both halves fire: the AST comparison catches the orphaned field name, and the behavioral test
    catches the resulting silence. REVERTED, passing again:

    ```
    ............................                                             [100%]
    28 passed in 0.47s
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: pasted object-identity output for every symbol added, showing each resolves to the same object from `oc_runipd`, `agy_runipd` and `render_stream`; plus the AST-measured count of names `agy_runipd` imports from `oc_runipd` before and after, showing it did not increase from 47.
  - Observed evidence: object-identity output for all five new symbols and the AST-measured oc-to-agy import count unchanged at 48 before and after, with a correction to the plan's stated 47. Detail below.
    OBJECT IDENTITY for every symbol added (identity, not a behavioral comparison, which passes against
    a copy - the `Heartbeat` divergence this discipline exists to prevent):

    ```
    symbol                                   owner id  oc is owner  agy is owner
    REFUSAL_KEY                       139031431542080         True          True
    Refusal                           104386569068848         True          True
    record_refusal                    139031431809504         True          True
    record_integration_refusal        139031431809856         True          True
    refusal_of_item                   139031431809152         True          True

    run_viewer.refusal_of_item is render_stream.refusal_of_item: True
    run_viewer.REFUSAL_KEY   is render_stream.REFUSAL_KEY  : True
    ```

    Every symbol is defined in `render_stream` and imported from there by both hosts and by the viewer;
    none is imported from the other host's driver.

    THE OC-TO-AGY COUPLING DID NOT DEEPEN. AST walk over `agy_runipd`'s `ImportFrom` nodes targeting
    `oc_runipd`, comparing the HEAD blob against the working tree:

    ```
    names agy_runipd imports from oc_runipd  BEFORE: 48
    names agy_runipd imports from oc_runipd  AFTER : 48
    increased: False   added: none   removed: none
    ```

    A CORRECTION TO THE PLAN'S NUMBER, stated rather than quietly absorbed: the plan asserts "did not
    increase from 47", but the count measured 48 at this HEAD both before and after my change, so the
    baseline had drifted by one in the days between review and execution (the plan itself records this
    number growing: backlog `cnwy8g` had 40, review measured 47, now 48). The SUBSTANCE of E-08 holds
    exactly - the count did not increase, and none of the five new symbols crosses that seam. The
    permanent guard `test_no_new_symbol_deepens_the_oc_to_agy_coupling` therefore asserts the DIRECTIONAL
    property (none of these names is imported from `oc_runipd`) rather than pinning a magic number, which
    would otherwise turn every unrelated sharing decision elsewhere into a failure in this file.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

CORRECTED AT ROUND 2, BECAUSE THIS PARAGRAPH CONTRADICTED THE PLAN'S OWN RECORD. It read "EXECUTION IS BLOCKED ON OQ-02 ... OQ-02 carries `Blocking: yes`, so the pre-execution checkpoint refuses while it is open". OQ-02 is neither open nor blocking: the maintainer resolved it on 2026-09-07 (option (b), fix both runners to write the reason under the name the renderer reads), and its own record carries `- Blocking: no` and `- Status: resolved`. Measured at review: `plan_readiness.has_unresolved_blocking_question` returns False, so the pre-execution checkpoint does NOT refuse on it, and `approval_refusals` named ONLY the stale `- Readiness: no-go`. A reader trusting this sentence would have waited for a maintainer answer that already existed.

WHAT ACTUALLY CONSTRAINS THIS PLAN, since the operational concern the paragraph raised is REAL even though the blocker was not:

1. A MERGE-ORDERING HAZARD, not a refusal. OQ-02's resolution edits `oc_runipd.py:6554` and `agy_runipd.py:3815`, and the `integpath` children `51vw4y` (`approved`) and `rl67b0` (`approved`) are approved work over the same integration functions. SEQUENCE THIS CHILD AFTER THOSE LAND, or coordinate. This is the accepted cost the maintainer recorded, and it is a scheduling instruction rather than a gate: the runner gives each item an isolated worktree and merges through the revalidate gate, so an overlap is a conflict to resolve, not a correctness failure.
2. Ordinary human approval (`- Status: approved`), which this plan does not have.

At round 2 the readiness is `go-pending-approval`: all findings are fixed, no blocking question remains, and `approval_refusals` returns empty.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved r2i1b1 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
