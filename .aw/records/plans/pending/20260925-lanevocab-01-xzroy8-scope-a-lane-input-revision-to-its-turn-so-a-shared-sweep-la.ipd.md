# IPD: Scope a lane input revision to its turn so a shared sweep lane attaches the right plan

- Date: 2026-09-25
- Kind: child
- Concern: Spec `7ckptx` R5.1a (iii) treats a lane's manifest revisions as ONE owner's input history ("any legitimate change to the input set is a NEW MANIFEST REVISION"), and the code inherits that assumption: `lane_containment.localize_attachment` defaults to `revision=None`, which `read_lane_input_manifest` resolves to `latest_lane_input_revision` (the highest `rev-<N>` directory on disk). The review sweep lane breaks the assumption: `runner_shared.execute_item_core` materializes each review at `revision=int(item["position"])`, but the queue dispatches by `queue_sort_key` (dependency depth first), not by position, so a review dispatched after a higher-positioned one gets the OTHER plan attached. `oc_runipd.run_opencode` calls `localize_attachment` for the plan with no `revision`. The backlog item called this wording-only; it is not: it is shipped misbehavior, REPRODUCED DETERMINISTICALLY at review by driving the real `run_opencode` (a turn recording `lane_input_revision: 3` received `rev-5/plan-planB.ipd.md`), and corroborated in recorded runs. The item was reclassified `bug` with `- Blocks-Release: next` before this plan was authored.
- Scope: IN: (a) `oc_runipd.run_opencode` passes the current attempt's `lane_input_revision` to both `localize_attachment` calls; (b) docstrings state that `revision=None` means "latest" and is only correct for a single-owner lane, across all FIVE `revision`-taking readers in `lane_containment` that share that default; (c) spec `7ckptx` R5.1a (iii) and acceptance A12b state that a revision is scoped to the (lane, turn) pair, that a shared lane holds one revision per turn, and that a consumer MUST address a turn's own revision rather than the latest, plus a note in A12b naming which of its parts currently has no shipped test; (d) a regression test with no-regression cases that can actually fail. OUT: renaming or re-keying `rev-<N>` directories; narrowing the four verifier signatures from a defaulting `None` (no product caller); restoring the deleted R5 acceptance test file; the agy host (it has no `--file` surface and names the lane plan path in the prompt, which `resolve_plan_path(lane_root, ...)` already resolves per turn); the execute lane (single owner, always rev-1).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/lane_containment.py, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, tests/test_lane_input_revision_scope.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: i4y84y
- Blocks-Release: next
- Set: lanevocab
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: xzroy8
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, no deferrals, no open questions (OQ-01 resolved from the tree). Reproduced F-1 deterministically by driving the real `run_opencode`. Split E-01 (scratch reproduction now authoritative; the run-corpus probe demoted to corroboration because a bare glob returns 0 from a lane and the tree is gitignored), added the no-regression cases that can actually fail (the single-owner lane the plan proposed cannot discriminate), widened the docstring work to all five `revision`-taking readers, added an A12b note that R5 has NO shipped test since `19313eed` deleted its 21-test file, corrected the nonexistent `lane_containment.lane_input_paths` citation, and rewrote the gate with a scope fence, honesty rule, and two stop conditions. Renumbered E/V to E-01..E-10 / V-01..V-10.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog i4y84y; re-measured the sweep lane's revision use across all 22 recorded runs with sweep reviews and found 4 review attempts whose `--file` attachment named a different plan's `rev-<N>` copy.

## Goal

Every isolated turn attaches the plan copy from ITS OWN manifest revision, and the containment spec says a revision belongs to a (lane, turn) pair, so the sweep lane's one-revision-per-review layout is both correct and described.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect

- [ ] E-01 Reproduce the misattachment DETERMINISTICALLY, in a scratch lane, and do NOT gate execution on the run corpus. Build a temp lane; call `lane_containment.materialize_lane_inputs` for plan B at `revision=5`, then for plan A at `revision=3` (the out-of-position dispatch order); then call `lane_containment.localize_attachment(lane_root=<lane>, fallback=<plan A>, input_class="plan")` with NO `revision` and print the returned path.
  - Depends on: none
  - Expected outcome: the returned path is under `rev-5/` and its bytes are plan B's, while plan A's own manifest revision is 3. REPRODUCED AT REVIEW, pasted verbatim in V-01's required evidence: `own manifest rev: 3 entry: .aw/state/lane-inputs/rev-3/plan-planA.ipd.md`, `latest on disk: 5`, and the argv attachment resolving to `rev-5/plan-planB.ipd.md` with bytes `# PLAN B`. If the scratch reproduction does NOT show the wrong revision, stop and report: the defect has moved.
  - Execution state: pending

- [ ] E-02 Probe the recorded runs as CORROBORATION ONLY, and resolve the runs root rather than globbing the cwd. Use `runner_shared.runs_repo_root(Path("."))` then `runner_shared.state_root(<that>)` to locate the corpus; a bare `.aw/records/runs/*/state.json` glob returns ZERO from a lane worktree (measured at review: 0 from the lane, 265 through the resolver), and the tree is gitignored (`.aw/.gitignore:14`), so it may be absent entirely. For each attempt with `review_sweep_lane: true`, compare `lane_input_revision` against the `rev-<N>` segment following each `--file` in `argv`, and print each mismatch as `run id6 rev=<own> attached=<rev-dir>/<plan-prefix>`.
  - Depends on: E-01
  - Expected outcome: EITHER the mismatch lines (the authoring measurement found 4: run `run-20260917T231229Z-2701568` `nmlx47` rev 5, `xdvglg` rev 6, `ut0vzr` rev 10, each attached `rev-12/...-zx9dkq-...`; run `run-20260919T133719Z-1618106` `udgilu` rev 2 attached `rev-3/...-13xo5k-...`) OR an explicit `corpus unavailable: <resolved path>` line. An absent or empty corpus is NOT a failure and does NOT contradict E-01: the corpus is untracked local scratch, so it is evidence when present and silent when not. Zero mismatches across a NON-empty corpus is also not a contradiction, since a corpus whose reviews all dispatched in position order has no mismatch to find; E-01's scratch reproduction is the authority.
  - Execution state: pending

- [ ] E-03 Add `tests/test_lane_input_revision_scope.py`. Build a temp lane, call `lane_containment.materialize_lane_inputs` for plan B at `revision=5` then plan A at `revision=3` (the out-of-position dispatch order). Drive the REAL `oc_runipd.run_opencode` with `work_dir=<lane>`, `item={"position": 3, "id6": "revaaa", "setid": "s1", "action": "review", "attempts": [{"lane_input_revision": 3}]}`, capturing argv through a patched `driver.subprocess.Popen` exactly as `LaunchProfileFrozenTurnArgvTests._argv_for` in `tests/test_oc_runipd.py` does (note that helper wraps the call in `try/except Exception: pass`, because stream handling aborts on the fake process AFTER argv is captured; the assertions must read the captured argv, never the return value). Read the attachments with `lane_containment.attachment_values(argv)` rather than by index arithmetic. Assert the path after the plan `--file` is under `rev-3/` and its bytes are plan A's.
  - Depends on: E-01
  - Expected outcome: the review case FAILS at HEAD (attachment under `rev-5/`, plan B).
  - Execution state: pending

- [ ] E-04 Add the NO-REGRESSION cases to the same file, chosen so each one can actually FAIL if E-05 is written wrongly. A single-owner lane holding ONLY rev-1 cannot discriminate (measured at review: `revision=None` and `revision=1` both return `rev-1`), so do NOT rely on it as the guard. Instead assert: (a) an attempt list that is EMPTY and an attempt dict carrying NO `lane_input_revision` key both still attach the LATEST revision when two revisions exist, which is what pins `None` to today's behavior and would fail if E-05 defaulted the missing key to 1 (measured at review: both return `rev-2/plan-B.md`); (b) a NON-isolated turn (`work_dir=None`) attaches the `fallback` unchanged; (c) the runbook attachment on an EXECUTE turn is localized to the same turn revision as the plan, since E-05 changes BOTH `localize_attachment` calls and only the plan call is otherwise covered.
  - Depends on: E-03
  - Expected outcome: all three pass at HEAD and again after E-05; (a) is the one that would catch a wrong default.
  - Execution state: pending

### Task group 2: fix the consumer and the contract

- [ ] E-05 In `oc_runipd.run_opencode`, read `turn_revision = ((item.get("attempts") or [{}])[-1]).get("lane_input_revision")` next to `lane_root_for_attachments`, and pass `revision=turn_revision` to both `lane_containment.localize_attachment(` calls (runbook and plan). Extend the comment block above `lane_root_for_attachments` with one paragraph naming this plan and the measured mismatch. `None` MUST keep today's latest-revision behavior and MUST NOT be defaulted to `1`: three live call sites reach this function with no materialized revision at all (`oc_runipd.audit`'s direct `run_opencode` call, which appends its attempt only AFTER the launch at `oc_runipd.py` `item["attempts"].append(`; a `--no-isolate-worktree` turn, where `lane_root_for_attachments` is `None` and the revision is never read; and `runner_shared`'s defect re-ask, which re-enters through `raw_launcher` on an attempt that DOES carry the key and so is correctly unaffected). Note also that a revision the manifest does not hold falls through to `fallback`, which for a review is the MAIN checkout's plan path and therefore an R5.3 attachment-outside-lane violation (measured at review: `revision=99` returns the out-of-lane fallback and `attachments_outside_lane` flags it); that is the existing documented fallback behavior and this plan does not change it, but E-06 must say so.
  - Depends on: E-04
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_lane_input_revision_scope.py` passes, including the E-04 `None` cases.
  - Execution state: pending

- [ ] E-06 In `lane_containment.localize_attachment`'s docstring, add a paragraph: `revision=None` reads the LATEST revision, which is the turn's own only in a single-owner lane; a shared lane (the review sweep) holds one revision per turn, so its caller MUST pass the turn's recorded `lane_input_revision`. State in the same paragraph that a revision the lane does NOT hold falls through to `fallback`, which for a review is the main-checkout plan and therefore an out-of-lane attachment, so a caller passing a revision must pass one it materialized. Add the same one-line caveat to `read_lane_input_manifest`'s docstring, and to the FOUR other `revision: int | None = None` readers in this module that inherit the same latest-means-latest default (`verify_link_independence`, `verify_lane_input_seal`, `verify_lane_input_manifest`, at `lane_containment.py` lines 2665, 2750 and 2814), since each would silently verify another turn's revision on a shared lane. No code change in this module.
  - Depends on: E-05
  - Expected outcome: `git diff -- agent_workflows/lane_containment.py` shows docstring-only changes.
  - Execution state: pending

- [ ] E-07 Amend spec `7ckptx` (`- Status: approved`, so this is an amendment to a live contract and the reason must travel with it; see Spec / documentation sync). In R5.1a append to part (iii): "A revision is scoped to the (lane, turn) pair. A lane shared by several turns (the review sweep lane) therefore holds one revision per turn, numbered by the turn's queue position, and consecutive revision numbers need not belong to the same turn. Any consumer that reads a manifest on a turn's behalf MUST address that turn's own recorded revision, never the latest on disk." Append the standing dated-amendment note the spec's own R5.4 already models (`AMENDED 2026-09-13/16 by dirtygates Order 01 ...`), naming this plan and its date, so a reader can tell amended text from original. In A12b append "and, for a shared lane, that each turn's attachment resolves to its own revision when turns are dispatched out of position order."
  - Depends on: E-06
  - Expected outcome: the R5.1a paragraph contains `(lane, turn) pair`, A12b names the out-of-position shared-lane case, and an `AMENDED ... xzroy8` line is present. Assert by reading the amended paragraphs, not by a count.
  - Execution state: pending

- [ ] E-08 Record in the spec's A12b that its shared-lane clause is ASPIRATIONAL as to a shipped test, because it must not read as a claim that one exists. NO test in `tests/` imports `lane_containment` for any R5 acceptance criterion: the file that held A12/A12b/A13 (`tests/test_lane_input_manifest.py`, 444 lines, 21 tests including `test_part_iii_a_change_is_a_new_revision_not_an_edit` and `test_both_attachments_are_localized`) was DELETED in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), along with 13 other lane test files. So `tests/test_lane_input_revision_scope.py` added by E-03 becomes the ONLY shipped test of any part of R5, and the spec must say which criteria are currently unenforced rather than implying A12b is covered. State it as one sentence in A12b naming `19313eed`; do NOT restore the deleted file (out of scope, see Deferred).
  - Depends on: E-07
  - Expected outcome: A12b names `19313eed` and says which of its three parts has no shipped test; `grep -rl "lane_containment" tests/` still lists only the files it listed before this plan plus `tests/test_lane_input_revision_scope.py`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-09 Run the directly affected modules: `python3 -m pytest tests/test_lane_input_revision_scope.py tests/test_oc_runipd.py tests/test_defect_report.py`. These three are the ones that drive `run_opencode` and so construct the argv this plan changes (`tests/test_oc_runipd.py` at `driver.run_opencode(` in four places, `tests/test_defect_report.py` at its `run_opencode(... resume_session="ses-1")` argv capture); `tests/test_defect_report.py` matters specifically because the defect re-ask re-enters `run_opencode` through `raw_launcher` and so inherits the new `revision=` argument.
  - Depends on: E-08
  - Expected outcome: 0 failed.
  - Execution state: pending

- [ ] E-10 Run the bare suite `python3 -m pytest`.
  - Depends on: E-09
  - Expected outcome: summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `lane_containment.materialize_lane_inputs` takes `revision: int = 1` and writes `<lane>/.aw/state/lane-inputs/rev-<N>/`; `latest_lane_input_revision` derives "latest" from directory names only.
- The sweep path in `runner_shared.execute_item_core` (`if work_dir and is_review:`) calls `materialize_lane_inputs(..., revision=int(item["position"]))` and records `attempt["lane_input_revision"]`; the attempt dict is appended to `item["attempts"]` before materialization mutates it, so `item["attempts"][-1]` is the live attempt when `run_opencode` runs.
- Dispatch order is `queue_sort_key` (dependency depth, then position), so position order is NOT dispatch order whenever a lower-positioned review declares an in-queue dependency. Driven at review: with `aaaaaa` at position 3 declaring a dependency on `bbbbbb` at position 5, `dependency_depth` returns 1 and 0 respectively and the sort dispatches `(bbbbbb, 5)` before `(aaaaaa, 3)`.
- The dependency token grammar is `executed:<id6>` or a BARE `<id6>`; `parse_dependency_token("ipd:bbbbbb")` returns `None`. A test or probe writing `"ipd:<id6>"` into `dependencies` produces depth 0 for BOTH items and silently fails to reproduce the out-of-position dispatch (hit at review before switching to the bare form).
- CORRECTION TO THE AUTHORED CLAIM, recorded because an executor trusting it would cite a symbol that does not exist: there is NO `lane_containment.lane_input_paths`. The `range(1, latest + 1)` iteration the authored bullet described is in `lane_containment.driver_written_lane_paths`, which skips a missing revision by `continue`. The substantive conclusion stands (teardown accounting tolerates sparse, out-of-order revisions and needs no change), but only that function name is correct.
- `lane_containment.attachment_values(argv)` returns every `--file` value in order, and `attachments_outside_lane(argv, lane_root)` flags the ones that do not resolve inside the lane. Tests must read attachments through these rather than by argv index arithmetic.
- `runner_shared.runs_repo_root(repo)` is the ONE resolver for the runs tree, and it exists precisely because a lane worktree resolves `state_root` to its own nonexistent `.aw/records/runs`. The tree is gitignored at `.aw/.gitignore:14`, so any probe over recorded runs is corroboration, never a gate.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.run_opencode` plan `--file` | A sweep review attaches the latest revision's plan, which is another review's plan when dispatch is out of position order. The reviewing agent receives the wrong plan as its attachment. | REPRODUCED DETERMINISTICALLY at review by driving the real `run_opencode`: with rev-5 holding plan B and rev-3 plan A, and an attempt recording `lane_input_revision: 3`, the single `--file` value was `.../rev-5/plan-planB.ipd.md` with bytes `# PLAN B`. Corroborating recorded argv: `udgilu rev 2 attached: ['rev-3/plan-20260919-stopcrash-01-13xo5k-record']`; three more in run `run-20260917T231229Z-2701568`, all attaching `rev-12/...zx9dkq...` |
| F-2 | MED | spec `7ckptx` R5.1a (iii) | The spec describes revisions as one owner's input history and says nothing about which revision a consumer reads; the shipped sweep lane violates the unstated assumption. | R5.1a text; `revision=int(item["position"])` in `execute_item_core` |
| F-3 | INFO | backlog `i4y84y` | Its claim "nothing behaves incorrectly" was true of the manifest bookkeeping and false of the attachment consumer. THE RECLASSIFICATION ALREADY HAPPENED: the item on disk carries `- Work-Kind: bug` and `- Blocks-Release: next`, so OQ-01 as authored asked a question the tree had already answered and is recorded resolved. | Item front matter; its history line "2026-09-25 graduated (aw set): ... reclassified bug"; commit `7d42c93d` |
| F-4 | INFO | agy host | Not affected: no `--file` surface at all (`grep -n "\-\-file" agent_workflows/agy_runipd.py` returns nothing; its argv is `[agy_bin, "-p", prompt_text, ...]`), and the prompt names `resolve_plan_path(lane_root, ...)`, the lane's tracked copy, resolved per turn. | `agy_runipd.run_agy_turn` argv construction; `build_review_prompt`'s lane-relative path |
| F-5 | MED | `lane_containment` `revision: int | None = None` readers | The latest-means-latest default is NOT confined to `localize_attachment`. FIVE functions in the module take it: `read_lane_input_manifest`, `verify_link_independence`, `verify_lane_input_seal`, `verify_lane_input_manifest`, and `localize_attachment`. On a shared lane each verifier would silently verify ANOTHER turn's revision. They have no product caller today (`grep` across `agent_workflows` finds none outside the module), so this is latent rather than live, which is why E-06 documents all five instead of changing signatures. | `grep -n "revision: int | None = None" agent_workflows/lane_containment.py` -> lines 2604, 2665, 2750, 2814, 3072 |
| F-6 | MED | `tests/` | R5 HAS NO SHIPPED TEST. `tests/test_lane_input_manifest.py` (444 lines, 21 tests, covering A12, A12b parts i/ii/iii, and A13 including `test_both_attachments_are_localized`) was deleted in commit `19313eed` along with 13 other lane test files. No test in `tests/` imports `lane_containment` for any R5 criterion, so `tests/test_lane_input_revision_scope.py` becomes the only one, and the A12b text this plan amends describes behavior nothing enforces. | `git show 19313eed --stat` lists `tests/test_lane_input_manifest.py \| 444 ----`; `grep -rn "lane_input\|materialize_lane_inputs" tests/` returns nothing |
| F-7 | LOW | `oc_runipd.run_opencode` fallback | A `revision` the lane does NOT hold falls through to `fallback`, which for a review is `resolve_plan_path(repo, ...)` against MAIN, i.e. an out-of-lane attachment that spec R5.3 forbids. Driven: `revision=99` returned the main-checkout path and `attachments_outside_lane` flagged it. This is the module's existing documented fallback and this plan does not change it, but passing a revision makes reaching it newly possible, so E-06 must say a caller must pass only a revision it materialized. | `localize_attachment` docstring "FALLBACK IS DELIBERATE"; driven `revision=99` result |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the mismatch deterministically in a scratch lane; E-02 corroborates from recorded runs when a corpus is reachable.
2. E-03 adds the failing regression test; E-04 adds the no-regression cases that can actually fail.
3. E-05 passes the turn's revision at the one consumer, keeping `None` as latest.
4. E-06 documents the `None` default's single-owner limit across all five readers that carry it, plus the out-of-lane fallback.
5. E-07 amends R5.1a and A12b with a dated amendment note; E-08 records in A12b which criteria have no shipped test.
6. E-09 and E-10 run the affected modules and the bare suite.

## Deferred / out of scope (with reason)

- Replacing the position-keyed revision integer with an explicit per-turn key (the backlog's second suggested shape). The (lane, turn) scoping plus a consumer that addresses its own revision removes the ambiguity without a layout change that every teardown and accounting path would have to follow.
  - Carrier-Declined: the wording plus consumer fix closes the defect; a re-key is churn with no measured need.
- Restoring `tests/test_lane_input_manifest.py` (F-6), the 21-test R5 acceptance file deleted in `19313eed`. Its absence is a real coverage hole and it is deliberately NOT this plan's job: the deletion was an intentional suite-wide trim of 219,063 lines across 318 files, so reversing one file of it is a decision about that trim rather than about this defect, and bundling it would make a focused one-consumer fix into a test-policy argument.
  - Carrier-Declined for THIS plan only. E-08 records the hole IN the spec so it is visible rather than silently implied, and a separate backlog item is the right carrier. Not filed here because this plan's own review must not create the work it then cites.
- Narrowing the four other `revision: int | None = None` readers (F-5) from a defaulting `None` to a required argument. They have no product caller, so a signature change today would be churn with no observable effect, and E-06 documents the hazard where a future caller will read it.
  - Carrier-Declined: latent, not live; documentation is the proportionate response until a caller exists.

## Scope check

- Over-scope: none.
- Under-scope: none remaining. The authored claim that `oc_runipd.run_opencode` is "the only product caller of `localize_attachment`" is CORRECT and was re-verified (`grep -rn "localize_attachment" agent_workflows/` returns only the definition and the two call sites in `run_opencode`). But it was the wrong question for the docstring work: the latest-means-latest default lives in FIVE functions (F-5), and the caller census answers only which ones are called today. E-06 now covers all five.

## Required tests / validation

New `tests/test_lane_input_revision_scope.py` (the review case failing before E-05, the E-04 cases passing both before and after), then the affected modules, then the bare suite. Note that no pre-existing test covers this surface (F-6), so the bare-suite run is a no-regression check and the new file is the only positive evidence.

## Spec / documentation sync

AMENDS spec `7ckptx` (listed in Scope-Paths, so both runners announce the declared spec edit before the run and reconcile it at finalize): R5.1a (iii) and A12b. The spec is `- Status: approved`, so this changes a live contract every other lane-containment plan is reviewed against. Why it belongs here rather than in a follow-up: the spec currently does not say which revision a turn owns, which is exactly the gap F-1 fell through, so fixing the consumer without the contract would leave the next consumer free to repeat it. The amendment is ADDITIVE (it constrains a consumer and names a shared lane's layout) and withdraws nothing, so no existing conforming behavior becomes non-conforming. E-08 additionally records in A12b that its shared-lane clause has no shipped test (F-6), because an acceptance criterion that reads as covered when nothing enforces it is the more dangerous of the two errors. No user-facing docs describe lane revisions.

## Open questions

### OQ-01: Should backlog `i4y84y` be reclassified from `chore` to `bug`?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM THE TREE, not by asking: the reclassification had already happened before this plan was authored. The item on disk carries `- Work-Kind: bug` and `- Blocks-Release: next`, and its own history line reads "2026-09-25 graduated (aw set): graduated into lanevocab plan xzroy8; reclassified bug: a sweep review was handed another plan's file in 4 recorded reviews" (commit `7d42c93d`, whose message lists `i4y84y` among "Reclassified bug + Blocks-Release next on measurement"). This plan already carries the matching `- Work-Kind: bug` and `- Blocks-Release: next`, so the gate is inherited and nothing is outstanding. The authored text describing the item as filed `chore` was stale at authoring time. No action.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of the E-01 scratch probe showing all three facts together: the turn's own manifest revision (3), the latest on disk (5), and the returned attachment path under `rev-5/` with plan B's bytes. The reproduction must be from the SCRATCH lane, not from run records, so it holds in any tree.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of the corpus probe: EITHER mismatch lines (ideally including `udgilu rev=2 attached=rev-3/...13xo5k...`) OR the literal `corpus unavailable: <resolved path>` line, plus the resolved root printed so a reader can see `runs_repo_root` was used and not a bare cwd glob. An unavailable or mismatch-free corpus is a PASS; it is corroboration and V-01 is the authority.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_lane_input_revision_scope.py` run BEFORE E-05, pasted, showing the review case FAILING, and quote the failure's own assertion text showing the attached path under `rev-5/`. A bare "1 failed" line is NOT sufficient: it cannot distinguish the defect from a broken test.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the same BEFORE run, pasted, showing the three no-regression cases PASSING at HEAD; and their names, so V-05 can show the same three still pass after. Case (a) must be identifiable in the output, since it is the only one that would catch E-05 defaulting a missing `lane_input_revision` to 1.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the same command after E-05, pasted, showing ALL cases passed (the review case now passing AND the three E-04 cases still passing, named); plus `git diff -- agent_workflows/oc_runipd.py` showing `revision=turn_revision` on BOTH `localize_attachment(` calls, not one. Confirm in the diff that no `or 1`, `int(...)`, or other coercion was added to `turn_revision`, since any of those would convert a missing key into revision 1 and reintroduce a wrong attachment on a lane whose turn is not position 1.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff --stat -- agent_workflows/lane_containment.py` plus the diff hunks showing ONLY docstring lines changed (no signature, no body), naming "single-owner" and `lane_input_revision`, and covering all five readers named in E-06. Also paste `python3 -c "import agent_workflows.lane_containment"` succeeding, since an unbalanced docstring quote is the one way a docstring-only edit breaks the module.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted amended R5.1a part (iii) paragraph and the amended A12b bullet, read in full rather than grepped, so a reader can confirm the new sentences sit in the right requirement and that nothing existing was removed. Also paste the `AMENDED ... xzroy8` note and `git diff --stat` for the spec showing insertions only.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted A12b text showing the sentence naming the deletion commit `19313eed` and which of its parts has no shipped test; plus pasted `git show 19313eed --stat | grep test_lane_input_manifest` confirming the file and line count the sentence rests on, so the claim is anchored rather than asserted.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted summary line of `python3 -m pytest tests/test_lane_input_revision_scope.py tests/test_oc_runipd.py tests/test_defect_report.py` with 0 failed, AND the pre-change baseline for the same three files, recorded BEFORE E-05, so a pre-existing failure is not read as caused by this change and a silently skipped file is not read as a pass. State both counts as `<before> -> <after>`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: pasted final summary line of the bare `python3 -m pytest`, showing 0 failed. Run it BARE: `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection, so do NOT add `-n0` (several times slower here), a second `-q` (compounds to `-qq` and suppresses the very summary line this item requires), or `-p no:randomly`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING. A two-line behavior change at ONE consumer (`oc_runipd.run_opencode` passes the turn's own `lane_input_revision` to both `localize_attachment` calls), docstring-only edits in `lane_containment`, one new test file, and an AMENDMENT to approved spec `7ckptx`. The spec edit is the largest part of what is being approved: `7ckptx` is the contract every lane-containment plan is reviewed against, and R5.1a (iii) gains a constraint on consumers that did not exist before. The amendment is additive and withdraws nothing, so no currently-conforming behavior becomes non-conforming.

THE DEFECT IS LIVE AND WAS REPRODUCED AT REVIEW, not inferred: driving the real `run_opencode` against a lane holding rev-3 (plan A) and rev-5 (plan B), a turn recording `lane_input_revision: 3` received `rev-5/plan-planB.ipd.md`. A reviewing agent handed another plan's file is the worst available failure of a review sweep, because the review it produces is confidently about the wrong artifact. The reachability condition is narrow (a lower-positioned review declaring an in-queue dependency on a higher-positioned one, which inverts dispatch order), which is why `- Priority: low` is defensible even though the consequence is severe.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `agent_workflows/oc_runipd.py`, only the `turn_revision` read and the two `revision=` arguments plus the comment block above `lane_root_for_attachments`. In `agent_workflows/lane_containment.py`, DOCSTRINGS ONLY across the five `revision`-taking readers; no signature, body, or default changes. In the spec, only R5.1a (iii), A12b, and an amendment note. `tests/test_lane_input_revision_scope.py` is new. `agent_workflows/runner_shared.py` and `agent_workflows/agy_runipd.py` are expected to need NO edit (the materializer already records the revision; agy has no `--file` surface). No run record, backlog item, or other spec is edited. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Three claims here are specifically easy to fake and must not be. V-03's BEFORE failure must quote the assertion text showing `rev-5/`, because a bare "1 failed" cannot distinguish the defect from a broken test. V-04/V-05's no-regression cases must be named in the output in BOTH states, because the single-owner lane the plan originally proposed as the guard cannot discriminate (measured at review: `revision=None` and `revision=1` both return `rev-1`), so only the two-revision `None` cases prove `None` still means latest. V-02's corpus probe must print the RESOLVED runs root, because a bare `.aw/records/runs/*` glob returns zero from a lane and would read as "no mismatches found".

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the E-01 scratch reproduction does NOT show the wrong revision, stop and report, since the defect has moved and the fix would then be unvalidated. If E-05 cannot be written without coercing a missing `lane_input_revision` to a number, stop and report, because defaulting to 1 would attach position 1's plan to every non-materialized turn and is strictly worse than today's behavior.

Commit ONLY paths in `- Scope-Paths:` through `aw commit xzroy8 -- <paths>`, never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Backlog item `i4y84y` is already `graduated` and carries `- Blocks-Release: next`, which this plan inherits, so the gate is preserved by that handoff; set the item `done` with `--evidence` citing the executed plan.
