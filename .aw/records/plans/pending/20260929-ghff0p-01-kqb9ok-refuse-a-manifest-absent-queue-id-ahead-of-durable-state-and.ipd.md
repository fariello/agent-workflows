# IPD: Refuse a manifest-absent queue id ahead of durable state, and retire the stale unguarded-subscript rationale

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `ghff0p` reports an UNGUARDED `manifest["plans"][id6]` in `runner_shared.initialize_run_core`'s queue-build loop that can raise a bare `KeyError` after the run directory exists. Re-measured at HEAD `287622dc`, that exact access NO LONGER EXISTS and the failure mode it described is already refused ahead of durable state, so this plan does NOT re-fix it. What is LIVE is a smaller, measured set of residue the fix left behind: a manifest-absent id is refused with a message NO TEST PINS, THREE in-tree comments still assert the bare subscript as current fact and are read by future authors as a live hazard, and ONE adjacent hole survives, where a manifest `file` that EXISTS but sits OUTSIDE the plans trees passes every pre-queue gate and then raises `DriverError` at dispatch with the run directory already written - which is the very no-durable-state property the item was filed to protect.
- Scope: `agent_workflows/runner_shared.py` (the refusal at the queue-build seam plus three stale rationale comments), `agent_workflows/run_selection_policy.py` (one stale gate census), and `tests/test_typed_queue_entries.py` (behavioral coverage for the refusal and for the surviving dispatch hole). NOT in scope: widening the manifest to non-plan types, changing `resolve_plan_path`'s resolution order, or any part of spec `z7nbn1`'s unbuilt per-type dispatch.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_selection_policy.py, tests/test_typed_queue_entries.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: ghff0p
- Blocks-Release: next
- Set: ghff0p
- Order: 1
- Highest E allocated: 05
- Author: opencode model=pt3-claude-opus-5-1m-us
- Id: kqb9ok

## Workflow history

- 2026-09-29 draft (opencode model=pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode model=pt3-claude-opus-5-1m-us): authored from backlog `ghff0p`; re-measured the item's premise at HEAD `287622dc`, found the primary defect already closed, and narrowed the plan to the measured live residue.

## Goal

Leave the repository in a state where a manifest-absent queue id is refused ahead of durable state WITH A TEST THAT PROVES IT, where the surviving sibling hole (a manifest `file` outside the plans trees) is refused at the same seam instead of at dispatch, and where no comment in the tree still tells a future author that the queue builder reads `manifest["plans"][id6]` with a bare subscript. The user-visible defect being closed is the one the backlog item names: a traceback or refusal arriving AFTER a run directory has been written, leaving an operator a run to reconcile by hand for work that never started.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the refusal that already ships

- [ ] E-01 Add a behavioral test to `tests/test_typed_queue_entries.py` that drives `initialize_run` on BOTH hosts with an expanded selection containing an id6 absent from every manifest map, and asserts the run REFUSES with `DriverError` naming that id6 AND that the runs root contains no run directory afterwards.
  - Depends on: none
  - Expected outcome: A new test fails if `lookup_manifest_artifact`'s `DriverError` is weakened to a bare `KeyError`, or if the queue build is ever re-sited after the run directory mkdir. Today it passes unchanged, because the behavior already ships (see F-01); its value is that nothing pins it now (F-03).
  - Execution state: pending

### Task group 2: close the surviving sibling hole

- [ ] E-02 In `runner_shared.initialize_run_core`, refuse at the queue-build seam (ahead of the `run_dir = state_root(repo) / run_id` mkdir) any IPD queue entry whose configured `file` cannot be resolved by `resolve_plan_path`, using the resolution the runner will itself perform at dispatch. Compose the refusal as a `DriverError` naming the id6, the configured path, and the reason the resolver gave; state in the message that no work started and nothing durable was created.
  - Depends on: E-01
  - Expected outcome: The Case-2 selection measured in F-02 (a conformant IPD at `docs/...ipd.md`, existing on disk but outside the plans trees) refuses with no run directory created, instead of building a queue, writing durable state, and then raising `DriverError` from `queue_plan_path_for` at dispatch.
  - Execution state: pending

- [ ] E-03 Add a behavioral test to `tests/test_typed_queue_entries.py` for E-02 on BOTH hosts: a manifest entry whose `file` exists but sits outside the plans trees refuses at initialize time, names the path, and leaves the runs root empty.
  - Depends on: E-02
  - Expected outcome: The test fails against HEAD `287622dc` (where the same fixture yields a created run directory and a dispatch-time raise) and passes after E-02.
  - Execution state: pending

### Task group 3: retire the stale rationale

- [ ] E-04 Correct the THREE comments in `agent_workflows/runner_shared.py` that assert the bare subscript as current fact, at `match_spec_selector`'s docstring ("reads `manifest["plans"][id6]` with a BARE SUBSCRIPT"), inside `closure_target_admission`'s non-plan refusal ("per-item first statement is an unguarded `manifest["plans"][id6]`, and it runs AFTER the run directory is created"), and in `enforce_mixed_type_gate`'s docstring ("resolves `manifest["plans"][id6]` inside `except (DriverError, KeyError): continue`"). Replace each with what the code now does, KEEPING the argument each comment was making where that argument still holds, and cite the current symbol rather than an offset.
  - Depends on: E-02
  - Expected outcome: No comment in `runner_shared.py` claims an unguarded subscript. `closure_target_admission`'s refusal keeps its two surviving reasons (a plans-only manifest has no entry to build, and a second queue-entry shape is a real behavioral change) and drops the third, which is now false. `enforce_mixed_type_gate`'s docstring still warns that a future non-plan admitter must fix the resolution loop, since `resolve_selected_artifact_paths` still DROPS an unresolvable id into `TypedSelection.unresolved` and nothing reads that field (F-04).
  - Execution state: pending

- [ ] E-05 Correct the gate census in `run_selection_policy.py`'s `SKIP_REASON_SOURCES` preamble, which states as measured fact that the run directory "is not created until offset 134" and names five pre-run-directory gates. Re-measure at execution HEAD and rewrite the claim in terms of SYMBOLS and ordering rather than statement offsets, which have already expired.
  - Depends on: E-04
  - Expected outcome: The comment's CONCLUSION is unchanged (an excluded draft never enters the queue and has no disposition, so `render_drafts_exclusion` remains the right reporter), but every number in it is either re-measured or replaced by a symbol reference that cannot expire.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A refusal in this seam MUST precede the run directory. `runner_shared.initialize_run_core` states the property repeatedly at its own gates: `expand_dependency_closure` is sited "AHEAD OF THE RUN DIRECTORY, so a `ClosureRefusal` leaves nothing durable behind, which is the same property `refuse_unimplemented_run_flags` has and for the same reason", and `enforce_freeze_time_refusal`'s docstring says it "Refuses the WHOLE RUN before any session, lane worktree, lease, or run directory is created". E-02 adopts that siting rather than inventing one.
- The refusal TEXT convention in this seam ends with a no-durable-state clause. `refuse_unrunnable_selected_types` closes with "No work started, and nothing durable was created", and `enforce_freeze_time_refusal`'s `RUN-NOT-FOUND` finding is rendered with the same tail. E-02 follows it.
- Spec authority for the whole-run refusal is `z7nbn1` (`- Status: implementing`) 1.3: "A runner MUST check, before anything runs, that every selected artifact is CONFORMANT and is the kind of thing the runner expects. A malformed or misfiled artifact is refused at selection time, not discovered by a handler that assumed otherwise. The refusal is of the WHOLE RUN, before any host session, lease or worktree (OQ-04)." A MISFILED artifact is exactly Case 2, so E-02 implements an existing approved-shape requirement rather than adding policy.
- Spec `z7nbn1` 5.7 names the adjacent resolver requirement ("The typed resolver refuses a type mismatch with a diagnostic") and 4.2 records the measurement that `resolve_plan_path`'s `configured` branch "returns any path which merely EXISTS", refusing a spec "ONLY when no `configured` path is supplied". E-02 does NOT change `resolve_plan_path` (that is 5.7's own work); it refuses at the seam using the resolver's verdict, which is the narrower act.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan's own F-05 is a worked example of an offset that expired.

## Findings

All measurements below were taken in this lane at HEAD `287622dc` ("integrate(aw oc run): merge verified lane eozq91 to main") by driving `initialize_run` on both hosts against temporary fixture repositories built from `tests/test_typed_queue_entries.py`'s own `_make_test_repo` / `_write_plan` helpers, and by reading the named symbols.

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S PRIMARY DEFECT IS ALREADY CLOSED, and this is the finding that reshapes the whole plan. The unguarded `plan = manifest["plans"][id6]` the item names is GONE: `initialize_run_core`'s queue loop now begins `atype, item_info = lookup_manifest_artifact(manifest, repo, id6)`, and that function ends `raise DriverError(f"No manifest entry found for artifact '{id6}'")` rather than propagating `KeyError`. The loop was ALSO re-sited ahead of the run directory. Injecting a manifest-absent id6 (`gho001`) into the expanded selection on both hosts yields `DriverError: No manifest entry found for artifact 'gho001'` with the runs root EMPTY (`run dirs=[]`) on each. So neither half of the reported failure mode (bare `KeyError`; durable state already written) reproduces. | The access was replaced by commit `20dcd6a6` ("artdispatch(8l8dgb): carry spec and backlog artifacts as typed queue entries"), whose diff shows `- plan = manifest["plans"][id6]` becoming `+ atype, item_info = lookup_manifest_artifact(manifest, repo, id6)`. The re-siting is visible by comparing the two symbols' order across commits: at `bb714fd8` (the item's own re-measurement HEAD) `run_dir = state_root(repo) / run_id` preceded `for position, id6 in enumerate(queue_ids, start=1)`; at `287622dc` the loop precedes it, with `enforce_freeze_time_refusal` and `enforce_orchestrator_shape_gate` between them. |
| F-02 | ONE ADJACENT HOLE SURVIVES AND IS THE SAME CLASS OF DEFECT. A manifest entry whose `file` EXISTS but sits outside the plans trees passes every pre-queue gate, is frozen into the queue, gets a run directory written, and only then refuses AT DISPATCH. Fixture: a conformant IPD text written to `docs/20260927-s2-01-pln002-outside.ipd.md` with a matching manifest entry. Measured on both hosts: `initialize_run` returns OK, `run dirs created: ['run-x-000001']`, queue entry `id6=pln002 action=execute status=queued`; then `runner_shared.queue_plan_path_for` on that very entry raises `DriverError: Refusing 'docs/20260927-s2-01-pln002-outside.ipd.md' for IPD pln002: it is outside the plans trees, not an IPD plan`. That is a refusal arriving after durable state, which is precisely the property the item was filed to protect. | `enforce_freeze_time_refusal`'s structure check tests `abs_path.is_file()` and the file DOES exist, so `RUN-NOT-FOUND` does not fire; `resolve_plan_path`'s plans-tree guard (`Refusing {configured!r} for IPD {id6}: it is {what}, not an IPD plan`) is only reached later, through `queue_plan_path_for`, which `runner_shared.execute_item_core` calls. `resolve_selected_artifact_paths` DID notice: it returned `plan_paths=0 all_paths=0 unresolved=('pln002',)` for the same selection. Nothing consumed that. |
| F-03 | THE SHIPPED REFUSAL IS UNTESTED. `No manifest entry found for artifact` greps to ZERO hits under `tests/`, and `lookup_manifest_artifact` greps to ZERO hits under `tests/`. So the behavior F-01 relies on is unpinned: a future refactor could restore a bare `KeyError`, or re-site the queue build after the run-directory mkdir, and the suite would stay green. | `grep -rn "No manifest entry\|manifest entry found" tests/` and `grep -rn "lookup_manifest_artifact" tests/` each return nothing. |
| F-04 | `TypedSelection.unresolved` HAS NO READER ANYWHERE, so the one signal that already detects Case 2 is discarded. An AST walk for `Attribute(attr="unresolved")` across every module in `agent_workflows/` returns ZERO hits; the only reference in the repository is the assertion `self.assertEqual(selection.unresolved, ())` in `tests/test_typed_queue_entries.py`. The field's own docstring says it is "kept rather than dropped so a caller can say WHICH id it could not place instead of silently shortening the selection" - a caller that does not exist. This is what makes E-02 cheap: the detection already runs, and only the refusal is missing. | AST scan over `agent_workflows/*.py` for `.unresolved` attribute reads: no results. `grep -rn "\.unresolved" agent_workflows/ tests/`: one hit, in the test named above. Corpus check: for all 924 discoverable plans, and for all 1637 plans+specs+backlog ids, `resolve_selected_artifact_paths` returns `unresolved: 0`, so no CURRENT repository artifact trips this. |
| F-05 | THREE COMMENTS IN `runner_shared.py` STILL ASSERT THE BARE SUBSCRIPT AS CURRENT FACT, which is how this stale premise propagates to the next author. (1) `match_spec_selector`'s docstring: "`initialize_run_core`'s queue loop reads `manifest["plans"][id6]` with a BARE SUBSCRIPT - so returning a spec id6 into the expanded selection would raise `KeyError` there rather than run it." Measured false: it raises `DriverError` and refuses. (2) `closure_target_admission`'s non-plan refusal: "`initialize_run_core`'s per-item first statement is an unguarded `manifest["plans"][id6]`, and it runs AFTER the run directory is created, so a non-plan id6 that got that far would raise a bare `KeyError` with durable state already written". Both clauses are now false. (3) `enforce_mixed_type_gate`'s docstring: "that list is built by a loop that resolves `manifest["plans"][id6]` inside `except (DriverError, KeyError): continue`". The loop is now `resolve_selected_artifact_paths`, whose plans branch does still catch `(DriverError, KeyError)` and continue, so this one's ARGUMENT survives while its quoted code does not. | The three sites are `match_spec_selector`, `closure_target_admission`, and `enforce_mixed_type_gate` in `agent_workflows/runner_shared.py`; each quoted string is verbatim and locatable by content search. The backlog item itself cites the second as its "WHY IT MATTERS" authority, so the stale comment is the item's own evidential base. |
| F-06 | ONE COMMENT IN `run_selection_policy.py` CARRIES AN EXPIRED OFFSET MEASUREMENT. Its `SKIP_REASON_SOURCES` preamble says the draft gate "runs at offset 70 of `initialize_run_core` while the run directory is not created until offset 134", measured at HEAD `7562ca6c`. Both offsets have moved (the queue build alone was re-sited past the run-directory statement since then), and the same comment's census of "the five gates it runs before the run directory exists" omits gates added afterwards, including `enforce_freeze_time_refusal` and `enforce_orchestrator_shape_gate`. The comment's CONCLUSION still holds; its numbers do not. | The quoted claims are in `run_selection_policy.SKIP_REASON_SOURCES`' preamble comment. `enforce_freeze_time_refusal` was added by commit `544ba188`; `enforce_orchestrator_shape_gate`'s wiring by `688d73ef`. Neither appears in that census. |
| F-07 | THE ITEM'S PROPOSED FIX NAMED THE RIGHT SHAPE, and E-02 adopts it for the case that survives. The item wrote: "Make the access match its sibling loop: catch the missing entry and either skip with a recorded reason or refuse BEFORE the run directory is created. The second is preferable, since a silently shortened queue is the falsehood the surrounding refusals exist to prevent." For the manifest-absent case that is already what happens (F-01). For Case 2 it is not, and the same reasoning applies verbatim: `resolve_selected_artifact_paths` silently shortens the selection to zero plan paths and the run proceeds. | The item's FIX paragraph, quoted. F-02's measurement supplies the case it still applies to. |
| F-08 | FOUR NEIGHBOURING MALFORMED-MANIFEST CASES ALREADY REFUSE CORRECTLY, so E-02 must not duplicate them. A manifest `file` pointing at a nonexistent path refuses with `[RUN-STRUCTURE-PREFLIGHT] ... violates RUN-NOT-FOUND`, no run directory. A Set `order` naming an id6 absent from `plans` refuses in `validate_manifest` with `Set s1 contains unknown plans: ['gho001']`. A `plans` entry with an empty `file` refuses with `Plan gho001 requires file and set`. An id6 with no plan anywhere refuses with `No IPD plan found with id6 'pln001' under .aw/records/plans/.` Each leaves the runs root empty. | Measured on the oc host across four fixture variants; each printed `run dirs: []` with the quoted message. The `RUN-NOT-FOUND` text is composed in `enforce_freeze_time_refusal`; the two manifest-shape messages in `validate_manifest`. |

## Proposed changes (ordered, validatable)

1. (E-01) `tests/test_typed_queue_entries.py`: add a test that patches each host module's `expand_selectors` to append a manifest-absent id6 to the resolved selection, calls `initialize_run` with `--prepare-only --unattended`, and asserts (a) `DriverError` naming the id6 and (b) an empty runs root. Patching the host's own `expand_selectors` is the seam the existing suite already uses for host-level wiring, and it is the only way to reach the queue builder with an id no selector would produce.
2. (E-02) `agent_workflows/runner_shared.py`: at the queue-build seam, for each entry whose `artifact_type` is `ipd`, resolve the configured file through `resolve_plan_path` and collect the resolver's `DriverError` rather than discarding it. Raise ONE `DriverError` naming every unresolvable entry, sited with the other pre-queue refusals and ahead of `run_id = getattr(args, "run_id", None) or new_run_id()`. The queue loop ALREADY calls `resolve_plan_path` inside a bare `except Exception:` for status backfill, so this adds no new filesystem work in the common case; it stops swallowing the verdict.
3. (E-03) `tests/test_typed_queue_entries.py`: add the Case-2 test from F-02 on both hosts, asserting the refusal message names the configured path and that the runs root is empty.
4. (E-04) `agent_workflows/runner_shared.py`: rewrite the three comments in F-05. `match_spec_selector` keeps its conclusion (a spec id6 must be REFUSED by the caller, not enqueued) and states the true mechanism. `closure_target_admission` keeps its two surviving reasons and drops the KeyError clause. `enforce_mixed_type_gate` keeps its forward warning and re-points it at `resolve_selected_artifact_paths` and `TypedSelection.unresolved`, noting E-02 now refuses rather than drops.
5. (E-05) `agent_workflows/run_selection_policy.py`: rewrite the two expired claims in F-06 in terms of symbols and ordering, and extend the gate census to the gates that exist at execution HEAD.

## Deferred / out of scope (with reason)

- Making `resolve_plan_path` itself refuse a type mismatch on a supplied `configured` path (spec `z7nbn1` 5.7, measured in that spec's 4.2). Out of scope because it changes a resolver every `configured_file` reader shares (5.8 counts 44 such sites), which is a far wider blast radius than this item's gate; E-02 refuses at the seam using the resolver's existing verdict instead.
- Giving `TypedSelection.unresolved` a general-purpose reader for non-plan types. Out of scope because the manifest is plans-only and admitting non-plan types is owned by spec `z7nbn1`'s unbuilt per-type dispatch; E-02 reads the plans branch's verdict only.
- Reopening whether the manifest should carry non-plan artifacts at all (`closure_target_admission`'s recorded narrowing versus spec `25kzda` :166). Out of scope and explicitly left to a plan that can review the discovery change on its own merits, exactly as that refusal's comment already says.
- Any change to `TODO.md` or to the backlog item's requirements.

## Scope check

- Over-scope: none. Each of the three Scope-Paths carries at least one E-item: `runner_shared.py` (E-02, E-04), `run_selection_policy.py` (E-05), `tests/test_typed_queue_entries.py` (E-01, E-03).
- Under-scope: The plan does NOT fix the item as literally written, because the access it names no longer exists (F-01). That is stated as a finding rather than silently narrowed, and the item's own FIX reasoning is carried over to the case that survives (F-07). If a reviewer judges that closing `ghff0p` requires only the retraction and not E-02, E-02 and E-03 can be dropped without affecting the rest; the reverse is not true, since E-04's rewrite depends on E-02's outcome being true.

## Required tests / validation

- The full suite, run BARE as `python3 -m pytest`, with the actual `N passed` summary line pasted into V-05. No added flags.
- The two new tests run on BOTH hosts (`oc_runipd`, `agy_runipd`) through the existing `_HOSTS` tuple, since the seam is shared and a one-host test would not prove the other.
- E-03's test must be shown to FAIL against the pre-change code and PASS after, with both outputs pasted; a test that passes before and after would not prove E-02 changed anything.
- Every new assertion is on observable behavior: a raised `DriverError`'s message, and the presence or absence of a directory under the runs root. No test reads production source with `inspect`, `ast`, or substring search, and none asserts on comment text (which is why E-04 and E-05 are validated by inspection under V-04 and V-05, not by a pinning test; a test asserting that a comment banner remains unchanged is exactly the code-pinning shape GUIDING_PRINCIPLES P16 forbids).

## Spec / documentation sync

No spec amendment. E-02 implements an existing requirement of spec `z7nbn1` (`- Status: implementing`) 1.3, which already demands that a "malformed or misfiled artifact is refused at selection time, not discovered by a handler that assumed otherwise", with the refusal being "of the WHOLE RUN, before any host session, lease or worktree". Case 2 is a misfiled artifact discovered by a handler, so the spec's contract is unchanged and only the implementation moves toward it. No `.spec.md` file is in `- Scope-Paths:`, deliberately and consistently with that. E-04 and E-05 change only comments, which no spec governs.

## Open questions

### OQ-01: Does closing `ghff0p` require E-02, or only the retraction of its premise?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: The plan proceeds on the reading that it requires E-02. The item's stated FIX and its stated WHY ("a traceback plus orphaned durable state ... leaves the operator a run directory to reconcile by hand for work that never started") both describe a property rather than a single subscript, and F-02 measures that property still violated on a neighbouring input. Recording the question rather than deciding it silently because the alternative reading is defensible: an item whose named access no longer exists could legitimately be closed by evidence alone, with F-02 refiled as its own bug. Non-blocking because either answer leaves E-01, E-04 and E-05 correct and wanted, and the maintainer can drop E-02/E-03 at review without reshaping the plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the actual output of running the new manifest-absent test alone on both hosts (the pytest node ids and the `passed` line). Then paste the output of the same test run against a deliberately reverted `lookup_manifest_artifact` that re-raises `KeyError` instead of `DriverError`, showing it FAILS; restore the code and paste a final passing run. A test that cannot fail proves nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste, for BOTH hosts, the Case-2 fixture driven through `initialize_run` after the change, showing the raised `DriverError` message text (including the configured path and the no-durable-state clause) and a listing of the runs root proving it is EMPTY. Paste the same two facts measured BEFORE the change for comparison, which must show a created run directory.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste the new Case-2 test FAILING at the pre-E-02 commit (with the assertion text showing a run directory was created) and PASSING after E-02, on both hosts, with the pytest output for each.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the output of a content search across `agent_workflows/` for each retired claim (`BARE SUBSCRIPT`, `per-item first statement is an unguarded`, and the quoted `except (DriverError, KeyError): continue` clause inside `enforce_mixed_type_gate`'s docstring), showing ZERO hits for the retired wording. Then paste the new text of each of the three rewritten comments and, for each, name the symbol whose current behavior it now describes, so a reviewer can check the new claim rather than trust it. Confirm explicitly that `closure_target_admission`'s refusal still states its two surviving reasons and that `enforce_mixed_type_gate`'s forward warning survives, re-pointed at `resolve_selected_artifact_paths` and `TypedSelection.unresolved`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Paste a content search across `agent_workflows/run_selection_policy.py` showing the expired offset claims (`offset 70`, `offset 134`) are GONE, plus the rewritten comment text and the re-measured gate census, with each named gate resolvable as a symbol in `runner_shared.initialize_run_core`. Then, because this is the last E-item performed, paste the ACTUAL final summary line of a bare `python3 -m pytest` run (the `N passed` line) taken after every other E-item, with no added flags and no narrowing to the touched files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is `to-review` and requires explicit human approval before execution; it must not be executed from this status. The executing agent commits through `aw commit <plan> -- <paths>` naming only the three Scope-Paths, never `git add -A` and never `--no-verify`, and does not push. If E-02's refusal turns out to reject any CURRENT repository artifact (F-04 measures zero such artifacts across all 1637 ids, so it should not), the executor must STOP and report rather than relaxing the refusal, because a gate that refuses live work is a worse defect than the one being fixed.

Before the terminal transition: `aw ipd lint --phase pre-transition` must report conforming, every `V-*` above must carry pasted evidence, and the plan is moved to `.aw/records/plans/executed/` only then. If OQ-01 is answered such that E-02 and E-03 are dropped, the executor must record that answer in the workflow history and mark those two items and their `V-*` twins deferred with the maintainer's instruction cited, rather than deleting them.

- Size assessment: standard
- Cohesion rationale: not required
