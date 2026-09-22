# IPD: Tell a cross-run adjacency conflict from a real failure of the work and route it to a resolver instead of stranding it

- Date: 2026-09-22
- Kind: child
- Concern: A merge-back content conflict is reported to the operator as a failure OF THE WORK, carries no record of which of six gate causes fired, and is terminal on its first attempt, so a lane whose code is fine and whose conflict is a two-minute keep-both is stranded for the rest of the run and takes its dependents with it. MEASURED on two lanes in `run-20260922T024054Z-2245533`, both resolved by hand afterwards with the full suite green.
  DEFECT 1, THE VERDICT ASSERTS SOMETHING FALSE. `decide_integration_deferral`'s terminal branch writes "integration refusal kind 'merge-refused' is terminal on its first attempt: ... so it asserts a real failure of the work". For a cross-run adjacency conflict that sentence is simply untrue: the work was verified, the suite was green in the lane, and the conflict is about two branches inserting at one location. Driven directly, `classify_integration_refusal("merge-refused")` returns `False`, which is what makes the refusal terminal. This wording is not cosmetic; it is the sentence an operator (or an agent triaging a run) reads to decide whether to look at the lane at all, and it tells them the code is broken.
  DEFECT 2, THE CAUSE IS NOT RECORDED FOR THIS CLASS, so nobody can tell the six causes apart after the fact. `orchestrate_isolation` defines SIX distinct gate outcomes (`INTEGRATION_FAILED_STALE_BASE`, `_CONFLICT`, `_COMBINED_RED`, `_MISSING_LANE`, `_SCOPE_VIOLATION`, `_LANE_FAILURE`) and `integrate_lane_branch` collapses all of them, plus its own post-`--ff-only` git conflict arm, onto the single kind `INTEGRATION_REFUSAL_CONFLICT`. MEASURED consequence in the recorded run: `ld8lb3`'s `integration_deferral` DOES contain the token `integration_failed_combined_red` (because it came from the gate's own status line), while `92u0v9`'s and `xipfy1`'s contain NO `integration_failed_*` token at all, because the real-git-conflict arm formats a human message and returns the bare kind. So for exactly the class this plan is about, the cause is absent from the durable record.
  DEFECT 3, IT CASCADES. A terminal `merge-refused` blocks dependents: three further items in that run reached `dependency-blocked` behind refused ones (`ut0vzr` and `k311gw` behind `65cuw0`, `lkexaw` behind `8u6770`), so one mislabelled refusal silently multiplies.
  THE TWO MEASURED CASES WERE CROSS-RUN RACES, PROVEN NOT INFERRED. `92u0v9` (compinert) conflicted in `agent_workflows/completion.py` with `4y95tp`, which belongs to a DIFFERENT run (`run-20260922T023434Z-2057475`); `git merge-base --is-ancestor f9a37808 f763be8c` exits nonzero, so the peer commit was NOT in the lane's base. `xipfy1` (retrywire) conflicted in `agent_workflows/runner_shared.py` with `8b9ufm` from a THIRD run (`run-20260922T023526Z-2065001`); `908db905` is likewise not an ancestor of base `d1d6b6eb`. In both, each side merely ADDS at the same insertion point (main's `installed_completion_state` vs the lane's `completion_framework_status` block; main's `role_block` vs the lane's `correction_notice`), and in `xipfy1`'s case the f-string below had ALREADY merged cleanly consuming both, so dropping either side would have left an undefined name.
  WHY THIS PLAN DOES NOT TRY TO MERGE THEM AUTOMATICALLY, and this is the load-bearing negative result that shapes the whole scope. The backlog item this plan graduates from originally proposed re-merging the lane onto current `main`, on the reasoning that two purely additive changes must combine. THAT WAS TESTED WITH `git merge-tree --write-tree` ON THE REAL COMMITS AND IS FALSE: `92u0v9`'s recovered lane tip `97255449` against `f9a37808` (a base that ALREADY CONTAINS the peer commit) still reports `CONFLICT (content): Merge conflict in agent_workflows/completion.py`; the OTHER direction (main into the lane, i.e. what a refresh or rebase performs) conflicts in the same file; and `xipfy1` conflicts likewise. Two insertions at ONE location conflict regardless of base or direction, because git has no basis to order them. "Purely additive" describes the SEMANTICS (which is why a human resolution is trivial and lossless) and says nothing about MERGEABILITY. So no unattended mechanism could have landed these lanes, and this plan deliberately delivers HONEST REPORTING AND ROUTING rather than automatic resolution.
- Scope: Make this refusal class legible and actionable: record WHICH gate cause fired, stop asserting a failure of the work for a conflict that is not one, and route it to a resolver with the facts needed to fix it in minutes (the conflicting paths, the peer commit and its run, and whether both sides only add). EXCLUDES automatic conflict resolution and any base refreshing or rebasing (measured insufficient for the only two documented cases, see the concern), excludes changing which refusals are DEFERRABLE (a retry cannot clear a same-location insertion, so promoting this kind to deferrable would only burn budget), excludes the baseline-subtraction defect (sibling plan `tgyfs2`), and excludes the concurrency guard (`vddpml`).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_integration_refusal_cause.py
- Item-Dependencies: none
- Status: to-review
- Set: stalemerge
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 87apfx
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- From-Backlog: qztbeq

## Workflow history

- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `qztbeq`, inheriting its `Blocks-Release: next` gate. THE SCOPE IS NARROWER THAN THE ITEM ORIGINALLY PROPOSED, because the item's own first remedy was measured and refuted: re-merging onto a fresher base does NOT clear either documented conflict, in either direction, so automatic resolution is off the table and the deliverable is reporting and routing. That refutation is recorded in the item's history and restated in this plan's concern so a future reader does not re-propose it. The design deliberately copies an existing precedent rather than inventing one: `revalidation_was_unmeasured` already reclassifies ONE collapsed cause (harness fault vs measured red) by reading a durable record the producer wrote, and E-01/E-03 extend exactly that pattern to the remaining causes.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

When an integration is refused, the run record must say WHICH of the six causes fired and must not claim the work failed when it did not, so an operator or a later agent turn can see a keep-both conflict for what it is and fix it in minutes instead of writing off a verified lane.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: record the cause

- [ ] E-01 Persist the SPECIFIC refusal cause on the item as a durable field, sourced from the gate's own `result.status` where the gate refused, and from an explicit constant for `integrate_lane_branch`'s own post-`--ff-only` git-conflict arm (which today returns the bare kind and records no cause). Follow the existing precedent: the producer writes a durable record and one reader interprets it, exactly as the `measured` flag and `revalidation_was_unmeasured` already do. Do NOT widen the gate's boolean return protocol.
  - Depends on: none
  - Expected outcome: replaying each of the three recorded refusals yields a cause field: `integration_failed_combined_red` for `ld8lb3`, and the new git-conflict cause for `92u0v9` and `xipfy1`, which today record none.
  - Execution state: pending
- [ ] E-02 Classify a recorded conflict as ADJACENCY-ONLY or SEMANTIC by a pure predicate over the conflict hunks: adjacency-only means every conflicting hunk has both sides ADDING with neither side modifying or deleting a line the other wrote. Return three-valued and report UNKNOWN rather than guessing, since a wrong `adjacency-only` claim would tell a resolver a semantic conflict is safe to keep-both.
  - Depends on: none
  - Expected outcome: `92u0v9`'s and `xipfy1`'s real conflicts classify as adjacency-only; a constructed conflict where one side edits a line the other wrote classifies as semantic; an unparseable hunk set returns UNKNOWN.
  - Execution state: pending

### Task group 2: stop asserting a falsehood

- [ ] E-03 Make the terminal verdict text CAUSE-SPECIFIC, so "asserts a real failure of the work" is written only for causes where it is true (a measured combined-red, a lane failure, a scope violation) and NOT for a conflict. For a conflict the verdict must state what actually happened (two branches changed the same region, main is untouched, the lane is preserved) and must not characterize the lane's code. Preserve every existing cause's terminality unchanged: this item changes WORDS, not verdicts.
  - Depends on: E-01
  - Expected outcome: the conflict verdict no longer contains "failure of the work"; the combined-red verdict is byte-identical to today's; no item's `status` or `deferrable` value changes for any cause.
  - Execution state: pending
- [ ] E-04 Emit the RESOLVER-FACING facts for a conflict refusal through the existing refusal writer (`record_refusal`), so the shipped diagnostics block renders it: the conflicting paths, the adjacency-only verdict from E-02, and, when resolvable, the PEER COMMIT and the run that produced it, so the reader learns this was a cross-run race rather than their own lane's defect. Reuse the existing remedy-phrasing convention (constructive, names the next action).
  - Depends on: E-01, E-02
  - Expected outcome: replaying `92u0v9` produces a refusal record naming `agent_workflows/completion.py`, adjacency-only, and the peer commit `f9a37808`; a semantic conflict produces the same record without the keep-both suggestion.
  - Execution state: pending

### Task group 3: prove it and keep it honest

- [ ] E-05 Ensure ONE shared implementation serves both hosts and pin it structurally, since a cause recorded by `aw oc run` and not by `aw agy run` would make the run record's meaning depend on which driver ran.
  - Depends on: E-01, E-03
  - Expected outcome: a test asserts both hosts resolve to the same cause-recording and verdict-composing symbols and fails if either forks them.
  - Execution state: pending
- [ ] E-06 Add the regression file with the REPLAY as its backbone plus two anti-regression controls: (a) a control that FAILS if the conflict verdict ever regains a "failure of the work" style claim, and (b) a control that FAILS if `classify_integration_refusal` is changed to make a plain conflict deferrable (which would burn retry budget on a refusal no retry can clear, and is explicitly out of scope).
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: RED before and GREEN after; both controls demonstrated failing when the property they guard is deliberately broken.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PRECEDENT THIS PLAN FOLLOWS EXISTS AND IS DOCUMENTED. `runner_shared` already reclassifies one collapsed cause after the fact: `if integ_kind == INTEGRATION_REFUSAL_CONFLICT and revalidation_was_unmeasured(item)` rewrites the kind to `merge-unchecked` and replaces the reason, and its in-code comment states the rule this plan generalizes: "The runner recorded which one this was, so read that rather than re-deriving it here or widening the gate's boolean protocol."
- The naming rule for these states is already fixed and must be honored by any new constant: the name states the NEXT ACTION, not the internal cause (`merge-retry` retries itself, `merge-needs-human` needs you, `merge-refused` is the gate declining the work, `merge-unchecked` is the gate unable to judge). This plan adds a CAUSE field rather than a new status precisely so that vocabulary is untouched.
- `LEGACY_INTEGRATION_STATUS_ALIASES` exists because run directories are DURABLE RECORDS and a rename must stay readable forever. Any new cause constant must therefore be additive, and an OLD record lacking the field must read as UNKNOWN rather than as any particular cause.
- `record_refusal` is the ONE refusal writer and the diagnostics block renders a `Refusal` for ANY status, so E-04 needs no renderer change.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The refusal is terminal on attempt 1 | `classify_integration_refusal("merge-refused")` returns `False`, driven directly |
| F-2 | The verdict asserts a failure of the work | `decide_integration_deferral`'s terminal branch text: "it asserts a real failure of the work" |
| F-3 | Six causes collapse to one kind | `orchestrate_isolation` defines six `INTEGRATION_FAILED_*` statuses; `integrate_lane_branch` returns `INTEGRATION_REFUSAL_CONFLICT` for all, plus its own git-conflict arm |
| F-4 | For THIS class the cause is recorded nowhere | `ld8lb3`'s deferral contains `integration_failed_combined_red`; `92u0v9`'s and `xipfy1`'s contain NO `integration_failed_*` token |
| F-5 | Both measured conflicts were cross-run races | neither peer commit is an ancestor of the lane base (`f9a37808` vs `f763be8c`; `908db905` vs `d1d6b6eb`) |
| F-6 | Both were adjacency-only and trivially resolvable | each side only ADDS at one insertion point; resolved by hand, suite green (`8474 passed`) |
| F-7 | Re-merging on a fresher base does NOT fix them | `merge-tree` of lane `97255449` against `f9a37808` still CONFLICTS; the reverse direction too; `xipfy1` likewise |
| F-8 | One mislabelled refusal cascades | three items reached `dependency-blocked` behind refused ones in the same run |

## Proposed changes (ordered, validatable)

1. Persist the specific refusal cause, including for the git-conflict arm that records none (E-01).
2. A three-valued adjacency-only vs semantic conflict predicate (E-02).
3. Cause-specific verdict text, removing the false failure-of-the-work claim for conflicts (E-03).
4. Resolver-facing refusal record: paths, adjacency verdict, peer commit and run (E-04).
5. One shared implementation across both hosts, structurally pinned (E-05).
6. Replay-backed regression file with two anti-regression controls (E-06).

## Deferred / out of scope (with reason)

- AUTOMATIC CONFLICT RESOLUTION and any base refresh or rebase: measured insufficient for both documented cases (F-7). A same-location double insertion requires an ordering judgement git cannot make, so an unattended resolver would have to guess, and guessing wrong writes bad code to main.
- MAKING A PLAIN CONFLICT DEFERRABLE: a retry recomputes the same conflict from the same two commits (there is no base-refresh machinery anywhere in `agent_workflows/`, verified), so promoting it would burn budget and change nothing. Pinned as an anti-regression control in E-06 rather than left implicit.
- The baseline-subtraction defect (sibling `tgyfs2`, backlog `fuk1mr`): the OTHER cause of the same run's strandings, and the bigger one (3 of 6 refusals). Independent.
- The concurrency guard (`vddpml`, backlog `yuffut`): would not have prevented these conflicts, since the peer commits landed 4.5 and 5 hours before the merges were attempted.
- Retroactively integrating the two stranded lanes: already merged by hand (`5c25bcd0`, `f38aeb4b`) with the suite green, so there is nothing to recover.

## Scope check

- Over-scope: none. One source path plus one new test file.
- Under-scope: this plan makes the refusal LEGIBLE and ROUTABLE; it does not make a run self-heal. A conflict still ends the item terminally and still cascades to dependents, which is honest (no retry can clear it) but means the operator cost is reduced rather than removed. If the maintainer wants the cascade itself softened, that is a separate question about whether a dependent should block on a lane whose code is verified but unmerged, and it is deliberately not decided here.

## Required tests / validation

- `python3 -m pytest tests/test_integration_refusal_cause.py` GREEN after, and RED before, the before-run produced by reverting only `agent_workflows/runner_shared.py` while keeping the new tests.
- `python3 -m pytest` bare, count line pasted, no new failing node ids against a baseline taken in the same worktree before the change.
- THE REPLAY, which is the backbone rather than a nicety: drive the real refusal path with the three recorded cases from `run-20260922T024054Z-2245533` (`ld8lb3` combined-red, `92u0v9` and `xipfy1` git conflicts) and paste the resulting cause field, verdict text, and refusal record for each. The lane branches for the two conflicts are gone, but both lane tips and both peer commits are still resolvable by hash (`97255449`, `d1cc184f`, `f9a37808`, `908db905`), so the conflict is reconstructible with `merge-tree`.
- An OLD record lacking the new field shown reading as UNKNOWN rather than as any specific cause.
- Both E-06 controls demonstrated failing when deliberately broken.

## Spec / documentation sync

No `.spec.md` amendment is expected. Spec `25kzda` and the `l2mzxn` work already require the gate to say what it measured and already separate measured-red from unmeasured; recording WHICH cause fired and not overstating it moves toward that contract rather than changing it. The in-code comment block above `INTEGRATION_REFUSAL_CONFLICT` should gain a sentence noting that the kind carries a separate CAUSE field, since that block is where a future reader looks for this taxonomy. If the executor finds a spec sentence that asserts a conflict implies a failure of the work, that sentence is wrong and must be reported (and then amended as a declared spec edit) rather than silently left to contradict the code.

## Open questions

### OQ-01: Should the resolver-facing record name the PEER COMMIT even when the peer is another run this one cannot read?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to name the COMMIT always and the RUN only when resolvable. The commit is a local git fact available to any driver (`git log` over the conflicting path), needs no cross-run state access, and is the single most useful datum for a resolver. Attributing it to a RUN requires reading another run's `state.json`, which may be absent or concurrently written, so that attribution is best-effort and its absence must never suppress the commit. Reported as UNKNOWN when unresolvable, never omitted silently.

### OQ-02: Should an adjacency-only conflict be surfaced differently from a semantic one in the run SUMMARY, not just the refusal record?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to NO for this plan. The refusal record already renders in the shipped diagnostics block, which is where a triaging reader looks, and adding a second surface means touching `render_stream` and its tests for presentation rather than correctness. Deliberately left out so this plan stays a two-path change; if the summary proves insufficient in practice that is a small follow-on, not a reason to widen this one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the cause field pasted for all three replayed cases, showing `integration_failed_combined_red` for `ld8lb3` and the new git-conflict cause for `92u0v9` and `xipfy1`; PLUS an old record lacking the field shown reading as UNKNOWN. Paste the actual field values.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the predicate's actual output for the two REAL reconstructed conflicts (both adjacency-only), for a constructed semantic conflict (one side editing a line the other wrote), and for an unparseable hunk set (UNKNOWN). Reconstruct via `merge-tree` from the recorded hashes, not from a synthetic fixture alone.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the conflict verdict text pasted BEFORE and AFTER, showing "failure of the work" gone; the combined-red verdict shown BYTE-IDENTICAL to today's; and a table of every cause's `status`/`deferrable` before and after proving no verdict changed.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the rendered refusal for replayed `92u0v9` pasted, naming `agent_workflows/completion.py`, the adjacency-only verdict, and peer commit `f9a37808`; plus a semantic case shown WITHOUT a keep-both suggestion; plus a case where the peer run is unresolvable shown still naming the commit.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the structural test output showing both hosts resolving to the same symbols, plus a demonstration that it FAILS when one host is pointed at a copy.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the new test file GREEN after and RED before; the bare suite count line; and each control demonstrated FAILING when broken on purpose (reinstate a failure-of-the-work phrasing; make a plain conflict deferrable).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`.

THE SPECIFIC DISCIPLINE THIS PLAN DEMANDS is that it must change WORDS AND RECORDS, NOT VERDICTS. Every cause keeps exactly the terminality it has today, and V-03 exists to prove that with a before/after table. An executor who finds themselves making a conflict deferrable, or resolving conflict content, has left this plan's scope and must stop and report: both were considered and are excluded on measured evidence (F-7), not by oversight. Note also that this plan's own backlog item had its first proposed remedy REFUTED by measurement, so an executor should treat the concern's negative results as load-bearing and re-measure rather than re-propose them.
