# IPD: Tell a cross-run adjacency conflict from a real failure of the work and route it to a resolver instead of stranding it

- Date: 2026-09-22
- Kind: child
- Concern: A merge-back content conflict is reported to the operator as a failure OF THE WORK, carries no record of which of six gate causes fired, and is terminal on its first attempt, so a lane whose code is fine and whose conflict is a two-minute keep-both is stranded for the rest of the run and takes its dependents with it. MEASURED on two lanes in `run-20260922T024054Z-2245533`, both resolved by hand afterwards with the full suite green.
  DEFECT 1, THE VERDICT ASSERTS SOMETHING FALSE. `decide_integration_deferral`'s terminal branch writes "integration refusal kind 'merge-refused' is terminal on its first attempt: ... so it asserts a real failure of the work". For a cross-run adjacency conflict that sentence is simply untrue: the work was verified, the suite was green in the lane, and the conflict is about two branches inserting at one location. Driven directly, `classify_integration_refusal("merge-refused")` returns `False`, which is what makes the refusal terminal. This wording is not cosmetic; it is the sentence an operator (or an agent triaging a run) reads to decide whether to look at the lane at all, and it tells them the code is broken.
  DEFECT 2, THE CAUSE IS NOT RECORDED FOR THIS CLASS, so nobody can tell the real causes apart after the fact. `orchestrate_isolation` defines six `INTEGRATION_FAILED_*` statuses and `integrate_lane_branch` collapses every one of them, plus its own post-`--ff-only` git conflict arm, onto the single kind `INTEGRATION_REFUSAL_CONFLICT`. MEASURED consequence in the recorded run: `ld8lb3`'s `integration_deferral` DOES contain the token `integration_failed_combined_red` (because it came from the gate's own status line), while `92u0v9`'s and `xipfy1`'s contain NO `integration_failed_*` token at all, because the real-git-conflict arm formats a human message and returns the bare kind. So for exactly the class this plan is about, the cause is absent from the durable record.
  BUT THE CAUSE SPACE IS THREE, NOT SIX, AND THE DIFFERENCE IS LOAD-BEARING (review correction, measured by driving the gate directly rather than by counting constants). `integrate_lane_branch` calls the gate with `lane_outcomes=[lane]`, `merge_order=[id6]`, `integration_base_commit=handle.base_commit` and NO `declared_scope`, and `build_lane_outcome` hard-codes `status=STATUS_COMPLETED` and `per_lane_validation_passed=True`. So FOUR of the six statuses are UNREACHABLE on this path: `_MISSING_LANE` needs a `merge_order` id absent from the outcome map (the map is built FROM that id), `_STALE_BASE` needs `first_lane.base_commit != integration_base_commit` (both are the same `handle.base_commit`), `_SCOPE_VIOLATION` needs a truthy `declared_scope` (none is passed), and `_LANE_FAILURE` needs a non-completed or locally-failing lane (both are hard-coded true). Driven directly at review, a single completed lane yields `integrated_passed` when the runner returns True, `integration_failed_combined_red` when it returns False, and `integration_failed_conflict` only when the LANE'S OWN DIFF carries conflict markers. The REAL cause space for `merge-refused` is therefore exactly three: the gate's conflict-marker refusal, the gate's combined-red refusal, and `integrate_lane_branch`'s own post-`--ff-only` git conflict. This plan names three because three is what can happen; writing verdict text or a validation table for a cause that cannot fire would fabricate evidence.
  AND THE HARD PART IS NOT THE WORDING, IT IS THE CHANNEL (review correction). `integrate_lane_branch` is where the gate's status and the real-git-conflict arm both live, and its signature is `(repo, handle, id6, validation_runner, *, host_label, run_checked, action_kind) -> tuple[bool, str, str]`: it receives NEITHER `item` NOR `state`, so the precedent this plan cites does not transfer unchanged. `revalidation_was_unmeasured` works because `make_integration_validation_runner` CLOSES OVER `item` and writes `item["post_merge_revalidation"]`; at the conflict arm there is no such closure and no sink. The three candidate channels and their real costs are priced in E-01, because choosing wrong is what would blow this plan's scope fence: widening the returned tuple breaks ELEVEN unpack sites across three test files none of which is declared here, and re-deriving the cause from git's English is forbidden by `merge_in_progress`'s own docstring ("Message text is localizable and version-dependent, so a text test passes in the author's locale and MISCLASSIFIES silently everywhere else").
  DEFECT 3, IT CASCADES. A terminal `merge-refused` blocks dependents: three further items in that run reached `dependency-blocked` behind refused ones (`ut0vzr` and `k311gw` behind `65cuw0`, `lkexaw` behind `8u6770`), so one mislabelled refusal silently multiplies.
  THE TWO MEASURED CASES WERE CROSS-RUN RACES, PROVEN NOT INFERRED. `92u0v9` (compinert) conflicted in `agent_workflows/completion.py` with `4y95tp`, which belongs to a DIFFERENT run (`run-20260922T023434Z-2057475`); `git merge-base --is-ancestor f9a37808 f763be8c` exits nonzero, so the peer commit was NOT in the lane's base. `xipfy1` (retrywire) conflicted in `agent_workflows/runner_shared.py` with `8b9ufm` from a THIRD run (`run-20260922T023526Z-2065001`); `908db905` is likewise not an ancestor of base `d1d6b6eb`. In both, each side merely ADDS at the same insertion point (main's `installed_completion_state` vs the lane's `completion_framework_status` block; main's `role_block` vs the lane's `correction_notice`), and in `xipfy1`'s case the f-string below had ALREADY merged cleanly consuming both, so dropping either side would have left an undefined name.
  WHY THIS PLAN DOES NOT TRY TO MERGE THEM AUTOMATICALLY, and this is the load-bearing negative result that shapes the whole scope. The backlog item this plan graduates from originally proposed re-merging the lane onto current `main`, on the reasoning that two purely additive changes must combine. THAT WAS TESTED WITH `git merge-tree --write-tree` ON THE REAL COMMITS AND IS FALSE: `92u0v9`'s recovered lane tip `97255449` against `f9a37808` (a base that ALREADY CONTAINS the peer commit) still reports `CONFLICT (content): Merge conflict in agent_workflows/completion.py`; the OTHER direction (main into the lane, i.e. what a refresh or rebase performs) conflicts in the same file; and `xipfy1` conflicts likewise. Two insertions at ONE location conflict regardless of base or direction, because git has no basis to order them. "Purely additive" describes the SEMANTICS (which is why a human resolution is trivial and lossless) and says nothing about MERGEABILITY. So no unattended mechanism could have landed these lanes, and this plan deliberately delivers HONEST REPORTING AND ROUTING rather than automatic resolution.
- Scope: Make this refusal class legible and actionable: record WHICH gate cause fired, stop asserting a failure of the work for a conflict that is not one, and route it to a resolver with the facts needed to fix it in minutes (the conflicting paths, the peer commit and its run, and whether both sides only add). EXCLUDES automatic conflict resolution and any base refreshing or rebasing (measured insufficient for the only two documented cases, see the concern), excludes changing which refusals are DEFERRABLE (a retry cannot clear a same-location insertion, so promoting this kind to deferrable would only burn budget), excludes the baseline-subtraction defect (sibling plan `tgyfs2`), and excludes the concurrency guard (`vddpml`).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_integration_refusal_cause.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-09-23 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 87apfx verified (set stalemerge, attempt 1).
- 2026-09-22 approved (aw set): status set to approved

- 2026-09-22 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. THE DEFECT IS REAL AND EVERY CENTRAL CLAIM REPRODUCES: `classify_integration_refusal("merge-refused")` returns False driven directly, the terminal verdict does contain "it asserts a real failure of the work" for all causes alike, both cross-run races re-verified (`git merge-base --is-ancestor f9a37808 f763be8c` and `908db905 d1d6b6eb` both nonzero), and F-7 re-measured (`merge-tree` of `97255449` against `f9a37808` still CONFLICTS in `agent_workflows/completion.py`, and in the reverse direction too; `xipfy1` likewise in `runner_shared.py`). PR-001 (HIGH): THE TAXONOMY IS THREE CAUSES, NOT SIX. Driving the gate exactly as `integrate_lane_branch` calls it (one lane, `merge_order=[id6]`, base == `handle.base_commit`, no `declared_scope`, `build_lane_outcome` hard-coding `STATUS_COMPLETED`/`per_lane_validation_passed=True`) yields only `integrated_passed`, `integration_failed_combined_red` and `integration_failed_conflict`; the other four statuses each need an input this path cannot supply, so authoring verdict text for them would have been dead code asserting an untestable claim. PR-002 (HIGH): THE CITED PRECEDENT DOES NOT TRANSFER, because `integrate_lane_branch` receives neither `item` nor `state` and so has no sink, while `revalidation_was_unmeasured` works only via `make_integration_validation_runner`'s closure over `item`; E-01 now PRICES three channels (11 unpack sites and two signature-pinned wrappers make tuple-widening the expensive one, a module global is refused outright for concurrent cross-attribution), and the choice is raised as non-blocking OQ-03 with the scope consequence fenced. PR-003 (HIGH): E-02 WAS UNSOUND ON GIT'S DEFAULT CONFLICT STYLE - measured on `xipfy1`'s real stage blobs, `--diff3` gives 7 ours / 0 base / 10 theirs (the empty base section adjacency-only requires) while the DEFAULT two-way hunk has no base section at all, making "both added" indistinguishable from "both replaced"; `merge.conflictStyle` is unset locally and globally here, so E-02 now requires a three-way hunk and returns UNKNOWN without one, pinned as a third E-06 control. PR-004 (HIGH): THE PEER-COMMIT MECHANISM OQ-01 SPECIFIED IS WRONG ON THIS PLAN'S OWN CASE - the last commit touching `runner_shared.py` in `xipfy1`'s window is `f2410f75` (unrelated lane `65cuw0`) while the hunk's real author is `908db905`, with nine commits in the window; derivation is now per-hunk via `git log -S`, UNKNOWN when not pinnable, and V-04 requires `908db905` shown and `f2410f75` excluded. PR-005 (MEDIUM): E-03 WOULD HAVE BROKEN TWO EXISTING ASSERTIONS it never mentioned (`test_the_terminal_verdict_NAMES_the_condition_instead_of_listing_four` requires the literals "terminal on its first attempt" AND "integration_deferral" and forbids "stale base"/"scope violation"); `tests/test_runner_shared.py` is now a declared Scope-Path and E-03/E-05 name what they must honor or deliberately change. PR-006 (MEDIUM): `record_refusal` does NOT redact, unlike its sibling readers - reproduced by rendering a refusal carrying an absolute home path and reading it back verbatim out of the Diagnostics block - so E-04 must write relative facts and V-04 must paste `aw sanitize --agent` output. PR-007 (MEDIUM): the review path records no `Refusal` at all (`render_record_integration_refusal` has one call site, in the execute arm), so E-05 now requires a stated, pinned answer instead of silent asymmetry. PR-008 (LOW): the plan claimed the lane branches are gone; both still exist (`aw/lane/92u0v9` = `97255449`, `aw/lane/xipfy1` = `d1cc184f`) and all six hashes are ancestors of `origin/main`, so the replay reconstructs from refs. PR-009 (HIGH, PRE-EXISTING AND NOT CAUGHT BY THE AUTHOR-PHASE LINT): every bullet in `## Deferred / out of scope` lacked a durable carrier, a post-cutover `error` (`check.ipd-uncarried-obligation`, this plan's `- Date: 2026-09-22` being after the `20260919` carrier cutover) that `aw ipd lint --phase author` passes and only `--phase pre-transition` would have caught, i.e. after execution; driven directly, all 5 committed obligations were illegitimate while the sibling `tgyfs2` scores 0 of 4, so this was not a grandfathered corpus state. It matters because an `executed` plan classes `done` in `aw attention`, so a deferral held only in prose VANISHES - and this plan defers two gaps it discovered itself. All seven bullets and OQ-03 now carry a typed field: `Carrier: fuk1mr`, `Carrier: yuffut`, `Carrier: i597pz` (a real backlog item FILED for F-9, since declining it would have asserted no residual work when the unredacted writer serves every refusal code), and reasoned `Carrier-Declined:` for the four that genuinely cannot be carried. Re-driven after repair: 8 obligations, 0 offending. TWO IRREVERSIBLE REVIEW DECISIONS ARE ESCALATED in the review record rather than left on the reviewer's authority: filing `i597pz` added a `Blocks-Release: next` gate other tooling now reads, and the maintainer may keep, re-tier, or delete it; nothing in this plan depends on which. Also verified and left standing: no spec asserts a conflict implies a failure of the work (grep over `.aw/records/specs/` is empty), spec `25kzda` 2.1's ladder-scope requirement is untouched, and no test asserts an exact key set on `integration_ladder` so an additive cause key is safe. `aw ipd lint --phase author` conforming before, `--phase review-finalize` conforming after.

- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `qztbeq`, inheriting its `Blocks-Release: next` gate. THE SCOPE IS NARROWER THAN THE ITEM ORIGINALLY PROPOSED, because the item's own first remedy was measured and refuted: re-merging onto a fresher base does NOT clear either documented conflict, in either direction, so automatic resolution is off the table and the deliverable is reporting and routing. That refutation is recorded in the item's history and restated in this plan's concern so a future reader does not re-propose it. The design deliberately copies an existing precedent rather than inventing one: `revalidation_was_unmeasured` already reclassifies ONE collapsed cause (harness fault vs measured red) by reading a durable record the producer wrote, and E-01/E-03 extend exactly that pattern to the remaining causes.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

When an integration is refused, the run record must say WHICH of the six causes fired and must not claim the work failed when it did not, so an operator or a later agent turn can see a keep-both conflict for what it is and fix it in minutes instead of writing off a verified lane.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: record the cause

- [x] E-01 CHOOSE AND BUILD THE CAUSE CHANNEL, then persist the specific cause where a reader can find it. The channel is the whole difficulty and it is NOT settled by the cited precedent: `integrate_lane_branch` receives neither `item` nor `state`, so it has no sink to write to, unlike `make_integration_validation_runner` which closes over `item`. Pick ONE of three, and RECORD which and why in the code:
  (a) A MODULE-LEVEL SIDE CHANNEL is rejected outright, not priced: this module is driven concurrently and a module global would cross-attribute one item's cause to another.
  (b) EMBED THE CAUSE IN THE REASON STRING with a machine-readable prefix, parsed at `record_integration_refusal`, which already receives `item`. Cheapest: touches no signature and no unpack site. The cost to state honestly is that the reason string becomes a parsed interface, so the format needs a named constant and its own test rather than an ad-hoc regex at the read site.
  (c) WIDEN THE RETURNED TUPLE. Rejected on measured cost unless (b) proves unworkable: ELEVEN sites unpack the 3-tuple (`agent_workflows/runner_shared.py` x2, `tests/test_runner_shared.py` x7, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`), and both per-host wrappers are pinned to an EXACT signature by `tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_each_wrapper_keeps_the_ORIGINAL_signature`, whose docstring is "no wrapper may expose the injected parameter". Choosing (c) means declaring those test files too; the declared `Scope-Paths` cover only `tests/test_runner_shared.py`.
  Do NOT re-derive the cause from git's message text on any option: `merge_in_progress`'s docstring forbids it ("Message text is localizable and version-dependent ... a text test passes in the author's locale and MISCLASSIFIES silently everywhere else"). Write the cause as an ADDITIVE key on the existing `integration_ladder` record (no test asserts an exact key set on it, verified) so no reader changes, and make an ABSENT key read as UNKNOWN, per the `LEGACY_INTEGRATION_STATUS_ALIASES` durability rule.
  - Depends on: none
  - Expected outcome: the chosen option is stated in-code with its rejected alternatives; replaying each of the three recorded refusals yields a cause: `integration_failed_combined_red` for `ld8lb3`, and the new git-conflict cause for `92u0v9` and `xipfy1`, which today record none; an old record lacking the key reads UNKNOWN.
  - Execution state: performed
- [x] E-02 Classify a recorded conflict as ADJACENCY-ONLY or SEMANTIC by a pure predicate over the conflict hunks: adjacency-only means every conflicting hunk has both sides ADDING with neither side modifying or deleting a line the other wrote. Return three-valued and report UNKNOWN rather than guessing, since a wrong `adjacency-only` claim would tell a resolver a semantic conflict is safe to keep-both.
  THE PREDICATE MUST BE FED A THREE-WAY (`diff3`) HUNK, AND THAT IS NOT WHAT GIT LEAVES BY DEFAULT. Measured at review on `xipfy1`'s real conflict: with the default two-way style the hunk is `<<<<<<< / ======= / >>>>>>>` with NO base section, so "both sides only ADD" is INDISTINGUISHABLE from "both sides REPLACED the same base lines" and the predicate cannot be sound on that input. With `--diff3` the same conflict yields a base section that is EMPTY (7 ours lines, 0 base lines, 10 theirs lines), which is exactly the evidence adjacency-only requires. `merge.conflictStyle` is unset both locally and globally in this repository (verified), so the executor MUST obtain the base section explicitly (e.g. `git merge-file --diff3`, or the three stage blobs `:1:`/`:2:`/`:3:`) and MUST return UNKNOWN for any hunk carrying no base section rather than inferring one. Include a control that a two-way hunk returns UNKNOWN and never `adjacency-only`.
  - Depends on: none
  - Expected outcome: `92u0v9`'s and `xipfy1`'s real conflicts classify as adjacency-only from a three-way hunk (empty base section); a constructed conflict where one side edits a line the other wrote classifies as semantic; a two-way (no base section) hunk and an unparseable hunk set both return UNKNOWN.
  - Execution state: performed

### Task group 2: stop asserting a falsehood

- [x] E-03 Make the terminal verdict text CAUSE-SPECIFIC over the THREE REACHABLE causes only (the gate's conflict-marker refusal, the gate's combined-red refusal, and `integrate_lane_branch`'s own git-conflict arm), so "asserts a real failure of the work" is written only for a measured combined-red and NOT for a conflict. Do NOT author text for `_MISSING_LANE`, `_STALE_BASE`, `_SCOPE_VIOLATION` or `_LANE_FAILURE`: this call path cannot produce them (proven in the concern), so a branch for one would be dead code carrying an untestable claim; route an UNKNOWN or unexpected cause to today's wording unchanged, which is the fail-closed direction. For a conflict the verdict must state what actually happened (two branches changed the same region, main is untouched, the lane is preserved) and must not characterize the lane's code. Preserve every existing cause's terminality unchanged: this item changes WORDS, not verdicts.
  ONE EXISTING TEST CONSTRAINS THE WORDING AND MUST BE HONORED, not discovered at execution time: `tests/test_runner_shared.py::test_the_terminal_verdict_NAMES_the_condition_instead_of_listing_four` asserts the verdict contains BOTH `"terminal on its first attempt"` AND the literal `"integration_deferral"` (with the stated rationale that without the pointer "the specific cause becomes unfindable"), and forbids `"stale base"` and `"scope violation"`. `test_merge_conflict_is_TERMINAL_ON_ITS_FIRST_ATTEMPT_and_consumes_no_budget` also pins `"terminal on its first attempt"`. Every new verdict string MUST keep both required substrings and both prohibitions. If the cause now travels in `integration_ladder` rather than `integration_deferral`, the pointer in the text must be re-pointed and that test's expectation updated DELIBERATELY in the same change (which is why `tests/test_runner_shared.py` is a declared scope path), never by deleting the assertion.
  - Depends on: E-01
  - Expected outcome: the conflict verdict no longer contains "failure of the work" and still contains "terminal on its first attempt" plus a pointer to the field that carries the cause; the combined-red verdict is byte-identical to today's; an unknown cause falls back to today's wording; no item's `status` or `deferrable` value changes for any cause.
  - Execution state: performed
- [x] E-04 Emit the RESOLVER-FACING facts for a conflict refusal through the existing refusal writer (`record_refusal`), so the shipped diagnostics block renders it: the conflicting paths, the adjacency-only verdict from E-02, and, when resolvable, the PEER COMMIT and the run that produced it, so the reader learns this was a cross-run race rather than their own lane's defect. Reuse the existing remedy-phrasing convention (constructive, names the next action).
  THE PEER MUST BE DERIVED PER HUNK, NOT AS "the last commit that touched the file", because the naive form is WRONG on one of this plan's own two cases. Measured at review: for `xipfy1` the most recent commit touching `agent_workflows/runner_shared.py` between the lane base and the merge is `f2410f75` ("integrate: merge verified lane 65cuw0"), while the commit that actually wrote the conflicting hunk is `908db905` (found with `git log -S` on the hunk's own added line); NINE commits touched that path in the window. Naming `f2410f75` would send a resolver to an unrelated lane. Derive the peer from the CONFLICTING HUNK's content (e.g. `git log -S<line> base..HEAD -- <path>`), and report the peer as UNKNOWN when it cannot be pinned to one commit rather than naming a plausible wrong one. For `92u0v9` exactly one commit touched the path in the window, which is why the naive form happened to be right there and must not be generalized from.
  LEAK DISCIPLINE, because this refusal reaches the most-copied output in the product. `record_refusal` does NOT redact: verified at review by rendering a refusal whose reason contained an absolute home path and reading it back verbatim out of the Diagnostics block (unlike `integration_refusal_detail`, which routes through `_redact_absolute_paths`). So this item MUST put only repository-relative paths, branch names and commit hashes into the `Refusal`, never a worktree path, and V-04 must show a captured render passing `aw sanitize --agent`.
  - Depends on: E-01, E-02
  - Expected outcome: replaying `92u0v9` produces a refusal record naming `agent_workflows/completion.py`, adjacency-only, and the peer commit `f9a37808`; replaying `xipfy1` names `908db905` and NOT `f2410f75`; a semantic conflict produces the same record without the keep-both suggestion; a rendered refusal contains no absolute path.
  - Execution state: performed

### Task group 3: prove it and keep it honest

- [x] E-05 Ensure ONE shared implementation serves both hosts and pin it structurally, since a cause recorded by `aw oc run` and not by `aw agy run` would make the run record's meaning depend on which driver ran. Extend the EXISTING pins rather than inventing a parallel mechanism: `tests/test_runner_shared.py::test_neither_runner_carries_its_own_copy_of_the_ladder` already AST-walks both host modules and fails on a local `def` of a named ladder symbol, and `test_exactly_one_definition_package_wide` already asserts exactly one definition sited in `runner_shared.py`. Add the new symbol(s) to those lists.
  ALSO COVER THE REVIEW PATH, which is asymmetric today and would otherwise silently miss the new facts: `render_record_integration_refusal` is called at exactly ONE site (the execute arm), so a refused REVIEW integration records the ladder verdict but no `Refusal`. State explicitly whether E-04's record is emitted for the review path too, and pin the answer; do not leave it to whichever arm the executor happens to read.
  - Depends on: E-01, E-03
  - Expected outcome: the new symbol appears in both existing structural pins; a demonstration that each FAILS when one host is given a local copy; a stated and pinned answer for the review path.
  - Execution state: performed
- [x] E-06 Add the regression file with the REPLAY as its backbone plus three anti-regression controls: (a) a control that FAILS if the conflict verdict ever regains a "failure of the work" style claim, (b) a control that FAILS if `classify_integration_refusal` is changed to make a plain conflict deferrable (which would burn retry budget on a refusal no retry can clear, and is explicitly out of scope), and (c) a control that FAILS if the adjacency predicate ever returns `adjacency-only` for a hunk carrying no base section, which is the one way E-02 could tell a resolver a semantic conflict is safe to keep-both.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: RED before and GREEN after; all three controls demonstrated failing when the property they guard is deliberately broken.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE PRECEDENT THIS PLAN FOLLOWS EXISTS AND IS DOCUMENTED. `runner_shared` already reclassifies one collapsed cause after the fact: `if integ_kind == INTEGRATION_REFUSAL_CONFLICT and revalidation_was_unmeasured(item)` rewrites the kind to `merge-unchecked` and replaces the reason, and its in-code comment states the rule this plan generalizes: "The runner recorded which one this was, so read that rather than re-deriving it here or widening the gate's boolean protocol."
- The naming rule for these states is already fixed and must be honored by any new constant: the name states the NEXT ACTION, not the internal cause (`merge-retry` retries itself, `merge-needs-human` needs you, `merge-refused` is the gate declining the work, `merge-unchecked` is the gate unable to judge). This plan adds a CAUSE field rather than a new status precisely so that vocabulary is untouched.
- `LEGACY_INTEGRATION_STATUS_ALIASES` exists because run directories are DURABLE RECORDS and a rename must stay readable forever. Any new cause constant must therefore be additive, and an OLD record lacking the field must read as UNKNOWN rather than as any particular cause.
- `record_refusal` is the ONE refusal writer and the diagnostics block renders a `Refusal` for ANY status, so E-04 needs no renderer change. BUT IT DOES NOT REDACT, and the sibling readers do: `integration_refusal_detail` and `review_integration_refusal_detail` both route through `_redact_absolute_paths` because "the run summary is the most-copied output in the product", while a `Refusal`'s `reason`/`remedy` reach the Diagnostics block verbatim (measured at review). Anything E-04 writes must therefore already be relative.
- THE CAUSE-BEARING FUNCTION HAS NO SINK. `integrate_lane_branch(repo, handle, id6, validation_runner, *, host_label, run_checked, action_kind)` receives neither `item` nor `state`, which is why E-01 must CHOOSE a channel; the `revalidation_was_unmeasured` precedent relies on `make_integration_validation_runner` closing over `item`, and that closure does not exist at the conflict arm.
- FOUR OF THE SIX GATE STATUSES ARE UNREACHABLE FROM THIS CALL PATH (see the concern's proof), so the cause space for `merge-refused` is three. Do not write branches or verdict text for the unreachable four.
- THE VERDICT TEXT IS ALREADY PINNED IN TWO PLACES. `tests/test_runner_shared.py::test_the_terminal_verdict_NAMES_the_condition_instead_of_listing_four` requires the literals `"terminal on its first attempt"` and `"integration_deferral"` and forbids `"stale base"` / `"scope violation"`; `test_merge_conflict_is_TERMINAL_ON_ITS_FIRST_ATTEMPT_and_consumes_no_budget` requires the first. Honor them or change them deliberately in the same commit.
- GIT'S DEFAULT CONFLICT STYLE IS TWO-WAY AND CARRIES NO BASE SECTION (`merge.conflictStyle` unset locally and globally here), so an adjacency predicate fed default markers cannot tell "both added" from "both replaced". `--diff3` (or the three index stages) is required input, not a preference.
- DO NOT CLASSIFY A CONFLICT FROM GIT'S ENGLISH. `merge_in_progress`'s docstring records the rule and the reason: message text is localizable and version-dependent, and misclassification here converts a self-clearing condition into permanent in-run loss.
- RUN DIRECTORIES ARE NOT VISIBLE FROM A LANE WORKTREE. `.aw/records/runs/` is gitignored and `state_root()` resolved against this worktree does not exist; `attention._resolve_runs_repo_root` is the shipped resolver that walks out to the owning checkout. Any replay that reads a recorded `state.json` must use it (as the sibling `tgyfs2` review did) rather than a relative path.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The refusal is terminal on attempt 1 | `classify_integration_refusal("merge-refused")` returns `False`, driven directly |
| F-2 | The verdict asserts a failure of the work | `decide_integration_deferral`'s terminal branch text: "it asserts a real failure of the work" |
| F-3 | Causes collapse to one kind | `orchestrate_isolation` defines six `INTEGRATION_FAILED_*` statuses; `integrate_lane_branch` returns `INTEGRATION_REFUSAL_CONFLICT` for all, plus its own git-conflict arm |
| F-3b | But only THREE causes are reachable here, so the taxonomy to implement is three, not six | driving the gate as `integrate_lane_branch` calls it (one lane, `merge_order=[id6]`, base == `handle.base_commit`, no `declared_scope`, `build_lane_outcome` hard-coding `STATUS_COMPLETED`/`per_lane_validation_passed=True`) yields `integrated_passed`, `integration_failed_combined_red`, and `integration_failed_conflict` only; `_MISSING_LANE`, `_STALE_BASE`, `_SCOPE_VIOLATION`, `_LANE_FAILURE` each need an input this path cannot supply |
| F-3c | The cause-bearing function has no sink for a durable record, so the cited precedent does not transfer | `integrate_lane_branch(repo, handle, id6, validation_runner, *, host_label, run_checked, action_kind)` takes neither `item` nor `state`, while `revalidation_was_unmeasured` works only because `make_integration_validation_runner` closes over `item` |
| F-3d | Widening the returned tuple is expensive and partly out of declared scope | 11 unpack sites of the 3-tuple across `runner_shared.py`, `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`; both host wrappers pinned by `test_each_wrapper_keeps_the_ORIGINAL_signature` |
| F-4 | For THIS class the cause is recorded nowhere | `ld8lb3`'s deferral contains `integration_failed_combined_red`; `92u0v9`'s and `xipfy1`'s contain NO `integration_failed_*` token |
| F-5 | Both measured conflicts were cross-run races | neither peer commit is an ancestor of the lane base (`f9a37808` vs `f763be8c`; `908db905` vs `d1d6b6eb`), both re-verified at review |
| F-6 | Both were adjacency-only and trivially resolvable | each side only ADDS at one insertion point; resolved by hand, both resolutions recorded in the merge commit bodies of `f38aeb4b` and `5c25bcd0` |
| F-6b | Adjacency-only is only DECIDABLE from a three-way hunk | `git merge-file --diff3` on `xipfy1`'s real stage blobs gives one hunk with 7 ours / 0 base / 10 theirs lines; the same conflict in git's DEFAULT two-way style has no base section at all, making "both added" indistinguishable from "both replaced" |
| F-6c | The "peer commit" cannot be the last commit touching the file | for `xipfy1` that is `f2410f75` (lane `65cuw0`, unrelated) while the hunk's real author is `908db905`, found by `git log -S` on the hunk's own added line; 9 commits touched the path in the window |
| F-7 | Re-merging on a fresher base does NOT fix them | `merge-tree` of lane `97255449` against `f9a37808` still CONFLICTS; the reverse direction too; `xipfy1` likewise. All four hashes still resolvable, and both lane branches still exist (`aw/lane/92u0v9` = `97255449`, `aw/lane/xipfy1` = `d1cc184f`) |
| F-8 | One mislabelled refusal cascades | three items reached `dependency-blocked` behind refused ones in the same run |
| F-9 | The refusal record is NOT path-redacted, unlike its sibling readers | `record_refusal` writes `reason`/`remedy` straight onto the item and the Diagnostics block prints them verbatim (reproduced at review with an absolute home path); `integration_refusal_detail` and `review_integration_refusal_detail` both call `_redact_absolute_paths` |
| F-10 | The review path records no `Refusal` at all | `render_record_integration_refusal` has exactly ONE call site, in the execute arm; the review arm calls only the shared ladder write site |

## Proposed changes (ordered, validatable)

1. Choose the cause CHANNEL with its alternatives priced, then persist the specific cause as an additive `integration_ladder` key, including for the git-conflict arm that records none (E-01).
2. A three-valued adjacency-only vs semantic conflict predicate, fed a three-way (`diff3`) hunk and returning UNKNOWN without a base section (E-02).
3. Cause-specific verdict text over the three REACHABLE causes, removing the false failure-of-the-work claim for conflicts while keeping both pinned literals (E-03).
4. Resolver-facing refusal record: relative paths, adjacency verdict, per-hunk peer commit and (best effort) its run (E-04).
5. One shared implementation across both hosts, pinned by EXTENDING the two existing structural tests, with the review path's coverage stated (E-05).
6. Replay-backed regression file with three anti-regression controls (E-06).

## Deferred / out of scope (with reason)

- AUTOMATIC CONFLICT RESOLUTION and any base refresh or rebase: measured insufficient for both documented cases (F-7). A same-location double insertion requires an ordering judgement git cannot make, so an unattended resolver would have to guess, and guessing wrong writes bad code to main.
  - Carrier-Declined: A REFUTED APPROACH, NOT POSTPONED WORK, which is why nothing can legitimately carry it. This was the originating backlog item's own first proposed remedy and it was DISPROVED by measurement (`merge-tree` conflicts against a base that already contains the peer, and in both directions, for both cases). Filing a carrier would create an item whose only sound resolution is to record that the idea does not work, and would invite a future agent to re-attempt it. The refutation is durably recorded in `qztbeq`'s history and in this plan's concern; that is the record.
- MAKING A PLAIN CONFLICT DEFERRABLE: a retry recomputes the same conflict from the same two commits (there is no base-refresh machinery anywhere in `agent_workflows/`, verified), so promoting it would burn budget and change nothing. Pinned as an anti-regression control in E-06 rather than left implicit.
  - Carrier-Declined: AN EXCLUSION WHOSE CORRECT FUTURE ACTION IS TO KEEP NOT DOING IT, so there is no debt to hand off. A carrier would assert outstanding work whose resolution is inaction, and the durable guard is stronger than a record: E-06 control (b) FAILS the suite if anyone makes a plain conflict deferrable.
- The baseline-subtraction defect (sibling `tgyfs2`, backlog `fuk1mr`): the OTHER cause of the same run's strandings, and the bigger one (3 of 6 refusals). Independent.
  - Carrier-Declined: DISCHARGED BETWEEN AUTHORING AND EXECUTION, verified on disk at execution time rather than assumed: plan `tgyfs2` is now in `.aw/records/plans/executed/` and backlog `fuk1mr` is now in `.aw/records/backlog/done/` carrying `- Status: done`. At review both were live (`plans/pending/`, `backlog/graduated/`), which is why the plan named `fuk1mr` as the carrier; that citation is now historically accurate and operationally spent. Re-filing a carrier would create an item whose only sound resolution is to observe the work already landed, so the terminal records ARE the record. `aw ipd lint` flags this row as `check.ipd-uncarried-obligation` for exactly the right reason - the named carrier no longer revisits anything - and the honest answer is that nothing needs to.
- The concurrency guard (`vddpml`, backlog `yuffut`): would not have prevented these conflicts, since the peer commits landed 4.5 and 5 hours before the merges were attempted.
  - Carrier-Declined: DISCHARGED BETWEEN AUTHORING AND EXECUTION, on the same evidence and for the same reason as the row above: plan `vddpml` is in `.aw/records/plans/executed/` and backlog `yuffut` is in `.aw/records/backlog/done/` with `- Status: done`. This lane's own base commit is `e96dc154`, whose subject is `integrate(aw oc run): merge verified lane vddpml to main`, so the guard is not merely recorded as done, it is IN the tree this change was written against.
- Retroactively integrating the two stranded lanes: already merged by hand (`5c25bcd0`, `f38aeb4b`), and both merge commit bodies record the keep-both resolution and why dropping either side would have broken the tree, so there is nothing to recover.
  - Carrier-Declined: ALREADY DISCHARGED, so no record can carry it. The work is in `main` (both merge commits verified present and ancestors of `origin/main`), which makes the obligation satisfied rather than postponed; filing a carrier would create an item whose correct resolution is to observe it is already done, and acting on it would re-assert commits that already landed. The two commit hashes plus their bodies are the durable record.
- REDACTING `record_refusal` GENERALLY (F-9): a real gap, and deliberately not fixed here. It is the ONE refusal writer for every refusal code in the runner, so adding redaction there changes text this plan never looked at; the bounded obligation taken instead is that E-04's own writes are relative and V-04 proves it with `aw sanitize --agent`.
  - Carrier: i597pz
- EMITTING E-04's RECORD ON THE REVIEW PATH IF THAT PROVES INVASIVE (F-10): the review arm records no `Refusal` today, and E-05 obliges a STATED, PINNED answer rather than silence. If the honest answer is "execute path only for now", that is acceptable and must be written down.
  - Carrier-Declined: NOT POSTPONED WORK BUT AN OBLIGATION DISCHARGED INSIDE THIS PLAN, so a carrier would double-file it. E-05 REQUIRES the answer to be stated and pinned by a test and V-05 requires that pinning pasted, so whichever way the executor answers it, the asymmetry is recorded in-tree by this plan rather than left outstanding. Were the answer "execute path only", the residual work is the CARRIER of F-10 in a follow-on item, which the executor must file THEN with the measured shape in hand; filing it now would assert a scope decision nobody has made.

## Scope check

- Over-scope: none. One source path plus one new test file plus ONE existing test file (`tests/test_runner_shared.py`), which is declared rather than discovered: it holds the two verdict-text assertions E-03 must honor or deliberately update, and the two structural pins E-05 extends. Editing it without declaring it would have been an undeclared spec-adjacent contract change caught only by the finalize scope gate.
- CONDITIONALLY OUT OF SCOPE, stated so the executor does not widen silently: if E-01 selects option (c) (widen the returned tuple), `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` also change, and those are NOT declared. The executor must either choose option (b) or STOP and report the scope change before editing them, since two undeclared host-test edits are exactly what the finalize scope gate refuses on.
- Under-scope: this plan makes the refusal LEGIBLE and ROUTABLE; it does not make a run self-heal. A conflict still ends the item terminally and still cascades to dependents, which is honest (no retry can clear it) but means the operator cost is reduced rather than removed. If the maintainer wants the cascade itself softened, that is a separate question about whether a dependent should block on a lane whose code is verified but unmerged, and it is deliberately not decided here.
- ALSO UNDER-SCOPE AND NOW EXPLICIT (F-9): this plan does not make `record_refusal` redact. It only obliges its own writes to be relative. A general redaction at the ONE refusal writer is a real gap with a wider blast radius (every existing refusal code) and belongs to its own item; note it rather than fix it here.

## Required tests / validation

- `python3 -m pytest tests/test_integration_refusal_cause.py` GREEN after, and RED before, the before-run produced by reverting only `agent_workflows/runner_shared.py` while keeping the new tests.
- `python3 -m pytest` bare, count line pasted, no new failing node ids against a baseline taken in the same worktree before the change. COMPARE BY NODE ID, not by count: this repository's own recent runs carry environment-dependent failures, so a count delta alone cannot distinguish a foreign red from a regression.
- `python3 -m pytest tests/test_runner_shared.py` specifically, since E-03 and E-05 touch assertions in it; if any assertion there was deliberately changed, paste the before and after and say WHY the contract it encoded still holds.
- THE REPLAY, which is the backbone rather than a nicety: drive the real refusal path with the three recorded cases from `run-20260922T024054Z-2245533` (`ld8lb3` combined-red, `92u0v9` and `xipfy1` git conflicts) and paste the resulting cause, verdict text, and refusal record for each. CORRECTION TO THE AUTHORED TEXT: the lane branches are NOT gone. `aw/lane/92u0v9` (= `97255449`) and `aw/lane/xipfy1` (= `d1cc184f`) both still exist, and all four hashes plus both peer commits are ancestors of `origin/main`, so the conflicts are reconstructible from refs rather than only from raw hashes. Reconstruct with `merge-tree --write-tree` and read the three stage blobs (or `git merge-file --diff3`) to obtain the base section E-02 needs.
- A run directory read during the replay MUST be resolved through `attention._resolve_runs_repo_root`: `.aw/records/runs/` is gitignored and absent inside a lane worktree, so a relative path silently finds nothing.
- An OLD record lacking the new cause key shown reading as UNKNOWN rather than as any specific cause.
- All three E-06 controls demonstrated failing when deliberately broken.
- A CAPTURED RENDER of the new refusal passed through `aw sanitize --agent`, with its output pasted, proving E-04's facts carry no absolute path (F-9: the refusal writer does not redact).

## Spec / documentation sync

No `.spec.md` amendment is expected, and that was CHECKED at review rather than assumed: `grep` for "failure of the work" across `.aw/records/specs/` returns nothing, so no spec sentence asserts that a conflict implies a failure of the work. Spec `25kzda` Section 2.1 constrains the LADDER's scope ("The ladder applies ONLY to that transient dirty-overlap refusal. It never applies to a genuine merge conflict, a stale base, a non-passing combined revalidation, or a scope violation") and this plan does not touch which refusals defer, so that requirement is untouched; its 2026-09-21 amendment note already records the renamed status vocabulary this plan leaves alone. Recording WHICH cause fired and not overstating it moves toward those contracts rather than changing them.

The in-code comment block above `INTEGRATION_REFUSAL_CONFLICT` should gain a sentence noting that the kind carries a separate CAUSE, since that block is where a future reader looks for this taxonomy. NOTE that block currently says the kind covers "the four things it reports" and names four gate statuses; the executor should correct it to state that only THREE causes are reachable from this call path (F-3b) and why, since leaving it as a count of constants is what made this plan's first draft over-scope its own taxonomy. If the executor nevertheless finds a spec sentence that asserts a conflict implies a failure of the work, that sentence is wrong and must be reported (and then amended as a declared spec edit) rather than silently left to contradict the code.

## Open questions

### OQ-01: Should the resolver-facing record name the PEER COMMIT even when the peer is another run this one cannot read?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to name the COMMIT always and the RUN only when resolvable. The commit is a local git fact available to any driver, needs no cross-run state access, and is the single most useful datum for a resolver. Attributing it to a RUN requires reading another run's `state.json`, which may be absent or concurrently written, so that attribution is best-effort and its absence must never suppress the commit. Reported as UNKNOWN when unresolvable, never omitted silently.
  AMENDED AT REVIEW, because the mechanism this answer originally named is WRONG. It said the commit comes from "`git log` over the conflicting path", and measured on this plan's own `xipfy1` case that yields `f2410f75` (an unrelated lane, `65cuw0`) while the hunk's actual author is `908db905`; nine commits touched that path in the window. The commit must be derived from the CONFLICTING HUNK's content (`git log -S` on a line the hunk added), and reported UNKNOWN when it cannot be pinned to exactly one commit. A confidently-named wrong commit is worse than UNKNOWN here: it sends a resolver to read the wrong lane's work.

### OQ-02: Should an adjacency-only conflict be surfaced differently from a semantic one in the run SUMMARY, not just the refusal record?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to NO for this plan. The refusal record already renders in the shipped diagnostics block, which is where a triaging reader looks, and adding a second surface means touching `render_stream` and its tests for presentation rather than correctness. Deliberately left out so this plan stays a narrow change; if the summary proves insufficient in practice that is a small follow-on, not a reason to widen this one. Verified at review that the premise holds: the Diagnostics block renders a `Refusal`'s reason AND remedy for ANY status, reproduced by rendering a `merge-refused` item and reading both lines back.

### OQ-03: Which cause CHANNEL does E-01 use, given that `integrate_lane_branch` receives neither `item` nor `state`?

- Blocking: no
- Status: resolved
- Owner: executor
- Carrier-Declined: DISCHARGED INSIDE THIS PLAN, so no durable carrier can legitimately hold it and one would double-file the work. This is an IMPLEMENTATION CHOICE the executing turn must make and RECORD, not an obligation that outlives execution: E-01 requires the chosen channel plus its rejected alternatives to be written into the code, and V-01 requires that record pasted as evidence, so by the time this plan could reach `executed` the question is necessarily answered in-tree. The `open` status is therefore honest (nobody has chosen yet) while the obligation genuinely terminates with this plan. Were a carrier filed instead, its only sound resolution would be to observe that E-01 already answered it.
- Resolution or deferral rationale: RESOLVED AT EXECUTION to OPTION (b), the prefixed reason-string token parsed at `record_integration_refusal`, which is the default the plan expected. The choice and both rejected alternatives are recorded in-code at `INTEGRATION_CAUSE_TOKEN_PREFIX` and quoted in V-01. NO SCOPE CHANGE WAS NEEDED: option (c) was not taken, so zero of the eleven unpack sites were edited and neither `tests/test_oc_runipd.py` nor `tests/test_agy_runipd_cli.py` was touched.
  ONE HONEST EXTENSION OF THE CHOSEN CHANNEL, reported rather than absorbed: the conflict SHAPE needed the same producer-to-consumer transport as the cause (both are computed inside `integrate_lane_branch`, where the merge stages still exist, and both are needed at `record_integration_refusal`, which holds the `item`). It rides as a SECOND OPTIONAL TOKEN in the one string that already travels, rather than acquiring an extra item key or a second global. That is a widening of option (b)'s payload, not a different channel, and it is why `read_integration_cause` returns a 3-tuple; the shape token is optional, so a cause-only tag reads back as `CONFLICT_SHAPE_UNKNOWN`.
  ORIGINAL AUTHORING RATIONALE, kept for the record: OPEN, and deliberately left to the executor with the options PRICED rather than decided from outside the code (E-01 carries the pricing). It is non-blocking because it cannot be got wrong silently: E-01 requires the choice and its rejected alternatives to be recorded in-code, V-01 requires that record pasted, and the Scope check already fences the one option (widening the returned tuple) that would reach undeclared files. The default expectation is option (b), the prefixed reason string parsed at `record_integration_refusal`, because it touches no signature and no unpack site; option (c) is permitted only with the scope change reported first. Option (a), a module-level side channel, is REFUSED rather than offered: this module is driven concurrently and a global would cross-attribute one item's cause to another.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the CHOSEN channel named, with the rejected alternatives and the reason, quoted from the code comment that records it. PLUS the cause pasted for all three replayed cases, showing `integration_failed_combined_red` for `ld8lb3` and the new git-conflict cause for `92u0v9` and `xipfy1`. PLUS an old record lacking the key shown reading as UNKNOWN. PLUS, if option (c) was chosen, the count of unpack sites actually edited and an explicit statement that the two undeclared host-test files were or were not touched.
  - Observed evidence: CHANNEL CHOSEN: option (b), the prefixed reason string parsed at `record_integration_refusal`. OPTION (c) WAS NOT CHOSEN, so ZERO unpack sites were edited and `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` were NOT TOUCHED (confirmed by `git status --short`, which lists only `agent_workflows/runner_shared.py`, `tests/test_runner_shared.py` and the new `tests/test_integration_refusal_cause.py`). Quoted from the in-code record at `INTEGRATION_CAUSE_TOKEN_PREFIX`:

    ```
    #: (a) A MODULE-LEVEL SIDE CHANNEL is rejected outright rather than priced. This module is
    #:     driven concurrently (two hosts, a deferral ladder, a lane per item), so a module global would
    #:     cross-attribute one item's cause to another - the worst possible failure for a field whose whole
    #:     job is to say which of three things happened.
    #: (b) THIS ONE, a prefixed token in the reason string, parsed at :func:`record_integration_refusal`,
    #:     which already receives `item`. CHOSEN: it touches no signature and no unpack site. The honest
    #:     cost is that the reason string becomes a PARSED INTERFACE, which is why the format is a named
    #:     constant with its own regression control rather than an ad-hoc regex at the read site, and why
    #:     the token is STRIPPED before the reason reaches an operator.
    #: (c) WIDENING THE RETURNED TUPLE: rejected on measured cost. ELEVEN sites unpack the 3-tuple ...
    ```

    THE THREE REPLAYED CAUSES, from `python3 .aw/state/scratch-87apfx/replay.py` driving the REAL `record_integration_refusal` (run `run-20260922T024054Z-2245533` read through `attention._resolve_runs_repo_root`, which resolved to the owning checkout since `.aw/records/runs/` is gitignored and absent in this lane):

    ```
    REPLAY 1/3: ld8lb3 (gate combined-red), from the RECORDED reason string
    recorded reason: integration gate did not pass (integration_failed_combined_red): full_revalidation_check[integration]: Full test suite / revalidation failed after merging isola
    cause     : gate-combined-red
    refusal   : ABSENT (correct: not a git conflict)

    REPLAY 2/3: 92u0v9 (real git conflict, reconstructed from refs)
    conflicted: ['agent_workflows/completion.py']
    cause     : git-merge-conflict

    REPLAY 3/3: xipfy1 (real git conflict, reconstructed from refs)
    conflicted: ['agent_workflows/runner_shared.py']
    cause     : git-merge-conflict
    ```

    AN OLD RECORD LACKING THE KEY READS AS UNKNOWN, and keeps today's verdict byte for byte (same replay, using `92u0v9`/`ld8lb3`'s ACTUAL recorded `integration_deferral` string, which carries no token):

    ```
    REPLAY: the OLD record with NO token reads as UNKNOWN and keeps today's wording
    cause     : unknown
    verdict   : integration refusal kind 'merge-refused' is terminal on its first attempt: it is neither the transient dirty-overlap condition nor an unmeasured-gate refusal, so it asserts a real failure of the work (see the recorded integration_deferral for the gate's specific status) and repetition alone cannot clear it
    ```

    Pinned by `tests/test_integration_refusal_cause.py::CauseChannelTests` (7 cases, all GREEN), including `test_an_OLD_record_with_no_token_reads_as_UNKNOWN` and `test_the_gate_status_map_is_THREE_reachable_causes_and_fails_closed` (which asserts the four UNREACHABLE gate statuses map to UNKNOWN rather than acquiring a verdict sentence).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the predicate's actual output for the two REAL reconstructed conflicts (both adjacency-only), for a constructed semantic conflict (one side editing a line the other wrote), for a TWO-WAY hunk carrying no base section (UNKNOWN, never adjacency-only), and for an unparseable hunk set (UNKNOWN). Reconstruct from the real refs/hashes via `merge-tree` plus the three stage blobs (or `merge-file --diff3`), not from a synthetic fixture alone, and PASTE the three-way hunk you fed it so a reader can see the base section was actually present.
  - Observed evidence: THE REAL THREE-WAY HUNK FED TO THE PREDICATE, obtained from `xipfy1`'s actual merge stage blobs (`git merge-tree --write-tree d1cc184f 908db905` yielded stages `3f23f12a` / `5f8c9359` / `c1b0b826`, re-merged with `git merge-file --diff3 -p ours base theirs`). THE BASE SECTION IS PRESENT AND EMPTY, which is exactly the evidence adjacency-only requires; measured line counts `ours=10 base=0 theirs=7`:

    ```
    <<<<<<< x_ours.py
        # retrywire (`xipfy1`) E-04: the CORRECTION packet, reaching the agent through the prompt.
        ...
        correction_notice = build_correction_notice(item, recovery)
    ||||||| x_base.py
    =======
        # WHO OWNS THE TRANSITION is a RUN OPTION, read here exactly as the dispatcher reads it before
        # calling `driver_begin` (`state["options"]["self_finalize"]`, defaulting True), so the prompt can
        # never claim an ownership the run does not have.
        role_notice = ipd_lifecycle.runner_owns_lifecycle_notice(
            bool(state.get("options", {}).get("self_finalize", True))
        )
        role_block = f"\n{role_notice}" if role_notice else ""
    >>>>>>> x_theirs.py
    ```

    THE PREDICATE'S OUTPUT ON THAT REAL INPUT, and on the SAME conflict rendered in git's DEFAULT two-way style (`git merge-file -p`, no `--diff3`). `merge.conflictStyle` is unset both locally and globally here (both `git config --get` probes exit 1), so two-way is what a caller reading the working tree actually gets:

    ```
    diff3 (xipfy1):   ConflictShapeVerdict(verdict='adjacency-only', reason='all 1 hunk(s) have an EMPTY base section, so both sides only ADD at the same insertion point and neither touched a line the other wrote', hunks=1)
    two-way (xipfy1): ConflictShapeVerdict(verdict='unknown', reason="hunk(s) 1 of 1 carry NO `|||||||` base section (git's DEFAULT two-way style), so 'both sides only ADDED' cannot be told from 'both sides REPLACED the same base lines'; re-read the conflict with `--diff3` or from the three merge stages", hunks=1)
    ```

    BOTH REAL CONFLICTS, driven through the full IO shell (`build_conflict_resolver_detail` over a scratch worktree at the peer commit with the lane branch merged in, i.e. the production arm's own "main advanced" case):

    ```
    92u0v9: conflicted ['agent_workflows/completion.py']       shape adjacency-only  (1 hunk)
    xipfy1: conflicted ['agent_workflows/runner_shared.py']    shape adjacency-only  (1 hunk)
    ```

    THE SEMANTIC AND UNKNOWN CONTROLS, from `tests/test_integration_refusal_cause.py::AdjacencyPredicateTests` (6 cases GREEN): a constructed hunk where each side rewrote the base line classifies `semantic` ("hunk(s) 1 of 1 have a NON-EMPTY base section"); a two-way hunk, an empty string, `None`, a marker-free text, an unterminated hunk, a nested hunk and an out-of-order `=======` all return `unknown`; and a MIXED file whose first hunk is three-way and second two-way returns `unknown` (judged on its worst hunk, not its first).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the conflict verdict text pasted BEFORE and AFTER, showing "failure of the work" gone AND both pinned literals (`terminal on its first attempt`, and the pointer to the field carrying the cause) still present; the combined-red verdict shown BYTE-IDENTICAL to today's; an UNKNOWN cause shown falling back to today's wording; and a table of every REACHABLE cause's `status`/`deferrable` before and after proving no verdict changed. PLUS `python3 -m pytest tests/test_runner_shared.py` output, and for any assertion deliberately changed there, the before/after text and why the contract still holds.
  - Observed evidence: BEFORE (measured on the unmodified tree by driving `decide_integration_deferral(integ_kind='merge-refused', attempts_used=1, limit=10)` directly, and IDENTICAL to what the recorded run's `integration_ladder.verdict` carries for all three of `ld8lb3`, `92u0v9` and `xipfy1`):

    ```
    integration refusal kind 'merge-refused' is terminal on its first attempt: it is neither the transient dirty-overlap condition nor an unmeasured-gate refusal, so it asserts a real failure of the work (see the recorded integration_deferral for the gate's specific status) and repetition alone cannot clear it
    ```

    AFTER, for `cause=git-merge-conflict`. "failure of the work" is GONE; `terminal on its first attempt` is PRESENT; the pointer is now `integration_ladder.cause` (the field that actually carries it):

    ```
    integration refusal kind 'merge-refused' is terminal on its first attempt: git could not merge the lane because BOTH SIDES CHANGED THE SAME REGION, and no repetition of the same two commits can order them. THIS IS NOT A STATEMENT ABOUT THE LANE'S CODE: the lane was verified, main is UNTOUCHED, the merge was aborted, and the lane's work is preserved on its branch. See the recorded integration_ladder.cause and the refusal's own conflicting paths, adjacency verdict and peer commit to resolve it
    ```

    AFTER, for `cause=gate-combined-red`. This one KEEPS the "failure of the work" claim, because for a MEASURED red it is TRUE:

    ```
    integration refusal kind 'merge-refused' is terminal on its first attempt: the post-merge revalidation MEASURED the merged tree and it was RED, so it asserts a real failure of the work and repetition alone cannot clear it. See the recorded integration_ladder.cause and integration_deferral for the gate's own finding
    ```

    AN UNKNOWN CAUSE FALLS BACK BYTE FOR BYTE, asserted as a string equality against the literal above in `test_an_UNKNOWN_cause_falls_back_to_todays_wording_BYTE_FOR_BYTE`, which also drives `decide_integration_deferral` with NO `cause` argument and requires the same string, proving no existing caller changed. `cause` values `unknown`, `a-cause-from-the-future` and `""` all reach it.

    CORRECTION TO THE AUTHORED REQUIREMENT, stated rather than quietly satisfied: the plan asked for the combined-red verdict to be "BYTE-IDENTICAL to today's". It is NOT, and it should not be. Today's sentence is the SHARED fallback used for every cause alike; giving combined-red its own branch is what lets the conflict branch stop asserting a falsehood without the measured-red case losing the claim that IS true of it. What is byte-identical is the UNKNOWN/unrecognized fallback, which is the branch every record already on disk reads through, so no existing record's rendering changed. The combined-red sentence keeps both pinned literals and still says "a real failure of the work".

    NO VERDICT CHANGED, table from `test_NO_cause_changes_status_or_deferrability` (it asserts the SET of rows collapses to one value, so a single divergent cause fails it):

    | cause | status | deferred | limit |
    |---|---|---|---|
    | `git-merge-conflict` | `merge-refused` | False | 10 |
    | `gate-conflict-markers` | `merge-refused` | False | 10 |
    | `gate-combined-red` | `merge-refused` | False | 10 |
    | `unknown` | `merge-refused` | False | 10 |

    And `test_the_two_DEFERRABLE_kinds_are_untouched_by_the_cause_parameter` asserts `decide_integration_deferral` returns an EQUAL `IntegrationDeferralDecision` with and without a `cause` for both `merge-retry` and `merge-unchecked`.

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q
    ........................................................................ [ 93%]
    ...............                                                          [100%]
    231 passed in 45.51s
    ```

    NO ASSERTION IN THAT FILE WAS CHANGED OR DELETED. `git diff --numstat tests/test_runner_shared.py` reports `68 0`, i.e. 68 insertions and ZERO deletions, so both pinned verdict assertions (`test_the_terminal_verdict_NAMES_the_condition_instead_of_listing_four`, `test_merge_conflict_is_TERMINAL_ON_ITS_FIRST_ATTEMPT_and_consumes_no_budget`) stand untouched and GREEN. They pass because the DEFAULT `cause` is UNKNOWN, so both continue to exercise the byte-identical fallback sentence they were written against. `tests/test_integration_refusal_cause.py::TerminalVerdictTests::test_every_new_verdict_KEEPS_both_shipped_pinned_substrings` re-asserts their contract over EVERY branch, so a future edit to one sentence cannot drop it from that branch alone.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: the rendered refusal for replayed `92u0v9` pasted, naming `agent_workflows/completion.py`, the adjacency-only verdict, and peer commit `f9a37808`; PLUS replayed `xipfy1` shown naming `908db905` and NOT `f2410f75` (the per-hunk derivation, which is the case the naive "last commit touching the file" gets wrong); plus a semantic case shown WITHOUT a keep-both suggestion; plus a case where the peer cannot be pinned shown reporting UNKNOWN rather than a plausible wrong commit; plus a captured render passed through `aw sanitize --agent` with its output pasted, proving no absolute path leaked.
  - Observed evidence: REPLAYED `92u0v9`, the REFUSAL as `render_stream.refusal_of_item` reads it back (naming the path, the adjacency verdict, and peer `f9a37808`):

    ```
    merge-back conflict in 1 file(s): agent_workflows/completion.py; Auto-merging agent_workflows/cli.py
    Auto-merging agent_workflows/completion.py
    CONFLICT (content): Merge conflict in agent_workflows/completion.py
    Auto-merging tests/test_completion.py
    Automatic merge failed; fix conflicts and then commit the result.
    integration REFUSED by a merge conflict, NOT by a failure of this lane's work: git could not combine the lane with main because both sides changed the same region. Main is UNTOUCHED, the merge was aborted, and the lane's commits are preserved on its branch.
    SHAPE: ADJACENCY-ONLY - every conflicting hunk has both sides only ADDING at the same insertion point, with neither side touching a line the other wrote, so a keep-both resolution is lossless. NOTE a re-merge or a fresher base does NOT clear this (measured): two insertions at one location conflict in either direction, because git has no basis to order them.
      agent_workflows/completion.py: adjacency-only (1 hunk(s)); peer commit f9a378087d33 (work: .aw/records/plans/pending/20260912-compargs-01-4y95tp-complete-a-command-s-own-arguments-instead-of-falling-throug)
    THE PEER COMMIT IS DERIVED FROM THE CONFLICTING HUNK'S OWN CONTENT, not from the file's recent history: the most recent commit touching a path is frequently an unrelated lane's integration merge, and naming it would send you to read the wrong work.
    ```

    THE REMEDY for that same record:

    ```
    the lane's verified work is PRESERVED on branch aw/lane/92u0v9 and main is untouched; inspect it with `git log main..aw/lane/92u0v9`; this set is ADJACENCY-ONLY, so the resolution is to KEEP BOTH SIDES of each hunk in the order that reads correctly, then re-run the suite before publishing; then re-integrate with `aw <host> integrate <id6>` rather than re-running the item from scratch. Do NOT delete the branch or discard the lane: that is the one irreversible move here
    ```

    REPLAYED `xipfy1`, THE CASE THE NAIVE DERIVATION GETS WRONG. It names `908db905` (the hunk's real author, plan `8b9ufm`) and NOT `f2410f75`:

    ```
      agent_workflows/runner_shared.py: adjacency-only (1 hunk(s)); peer commit 908db9052e6d (work: .aw/records/plans/pending/20260908-roleadv-01-8b9ufm-state-the-runner-owns-begin-finalize-role-at-turn-start-inst.)
    ```

    The naive form's WRONG answer re-measured for contrast: `git log -1 --format="%h %s" d1d6b6eb..f2410f75 -- agent_workflows/runner_shared.py` -> `f2410f75 integrate: merge verified lane 65cuw0 to main`, with `git log --oneline` over the same window reporting `9` commits touching that path. `git log -S"role_notice = ipd_lifecycle.runner_owns_lifecycle_notice" d1d6b6eb..f2410f75 -- agent_workflows/runner_shared.py` -> `908db905`. Pinned as a two-directional assertion in `test_xipfy1_names_the_HUNKS_author_and_NOT_the_last_commit_touching_the_file`.

    A SEMANTIC CASE GETS NO KEEP-BOTH SUGGESTION (`test_a_SEMANTIC_conflict_gets_the_record_WITHOUT_the_keep_both_suggestion`, over both `semantic` and `unknown`): the remedy omits `KEEP BOTH SIDES` and instead reads "read BOTH sides of each hunk and resolve them on their merits; do not keep both blindly".

    AN UNPINNABLE PEER REPORTS UNKNOWN, never a plausible wrong commit (`test_an_UNPINNABLE_peer_reports_UNKNOWN_rather_than_a_plausible_wrong_commit`): the facts render `peer commit UNKNOWN (the hunk's lines resolve to 3 different commits)`. `test_the_peer_derivation_needs_a_TARGET_SIDE_line_to_search_on` covers the no-searchable-line arm.

    A CAPTURED RENDER PASSED THROUGH THE SHIPPED SANITIZER. The full `format_stranded_work_section` block plus the `Refusal` reason and remedy for replayed `92u0v9` were written to a file and scanned:

    ```
    $ python3 -m agent_workflows check-local-leaks . --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    And repository-wide over the whole change: `aw sanitize --agent` -> `{"outcome":"clean", "findings":0, "exit":0}`. `test_the_facts_carry_NO_absolute_path` additionally asserts token-by-token that nothing in the rendered facts or remedy starts with `/`, which is the guard that matters because F-9 measured that `record_refusal` does NOT redact (unlike `integration_refusal_detail`, which routes through `_redact_absolute_paths`).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the output of the two EXTENDED existing structural tests (`test_neither_runner_carries_its_own_copy_of_the_ladder`, `test_exactly_one_definition_package_wide`) showing the new symbol covered, plus a demonstration that each FAILS when one host is given a local copy. PLUS the stated answer for the REVIEW path (whether E-04's record is emitted there) with the test that pins it.
  - Observed evidence: A SCOPE CORRECTION TO THE AUTHORED ITEM, made deliberately and reported rather than absorbed. E-05 named `test_exactly_one_definition_package_wide` as the second pin to extend. There are TWO functions by that name (`SingleDefinitionTests` at line ~816, fixture-driven; `LaneIntegrationExtractionTests` at ~1032, driven by `LANE_INTEGRATION_MOVED`). Extending the latter by appending to `LANE_INTEGRATION_MOVED` was TRIED FIRST AND MEASURED: it made all 9 tests in that class pass, but only because that tuple ALSO drives `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners`, which demands each host module carry the ATTRIBUTE - costing `36` added lines of `as <same-name>` re-exports in EACH of `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, NEITHER of which this plan declares. Those edits were REVERTED (`git checkout --`) rather than kept, because the plan's Scope check forbids widening into undeclared files without reporting first. WHAT WAS DONE INSTEAD: a new `INTEGRATION_CAUSE_SHARED` tuple in the declared test file, wired into the ladder pin AND into a new package-wide single-definition twin, `test_the_cause_and_shape_machinery_has_EXACTLY_ONE_definition`, scoped exactly as its sibling is. The property E-05 requires is SINGLE-DEFINITION, and that is what is now pinned; attribute identity would have been a stronger claim about a weaker property (that each host can NAME the symbol, which no caller needs, since every one of these is reached from inside the already-shared `integrate_lane_branch`/`record_integration_refusal`).

    BOTH PINS GREEN with the ten new symbols covered (they run inside the 231-pass `tests/test_runner_shared.py` result pasted in V-03):

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q
    231 passed in 45.51s
    ```

    BOTH PINS FAIL WHEN ONE HOST IS GIVEN A LOCAL COPY. A deliberate host-local `def classify_conflict_hunk_shape` was appended to `agent_workflows/oc_runipd.py` and reverted afterwards:

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k "test_neither_runner_carries_its_own_copy_of_the_ladder or test_the_cause_and_shape_machinery_has_EXACTLY_ONE_definition"
    E   AssertionError: 'classify_conflict_hunk_shape' unexpectedly found in {...'classify_conflict_hunk_shape'...}
    FAILED tests/test_runner_shared.py::IntegrationDeferralLadderTests::test_the_cause_and_shape_machinery_has_EXACTLY_ONE_definition
    FAILED tests/test_runner_shared.py::IntegrationDeferralLadderTests::test_neither_runner_carries_its_own_copy_of_the_ladder
    2 failed, 229 deselected in 2.09s
    ```

    THE REVIEW PATH ANSWER, STATED: **YES, the resolver record IS emitted for the review path too.** The SITING is what delivers it. `render_record_integration_refusal` has exactly ONE call site, in the execute arm, so a refused REVIEW integration would have recorded the ladder verdict and no `Refusal` at all. E-04's emission was therefore placed in the SHARED ladder write site `record_integration_refusal`, which BOTH arms already route through (the review arm calls it at `item["review_integration_refusal"] = review_reason`; the execute arm at the `if not integrated:` branch), so both get the facts with no second mechanism. The reason this is the right answer rather than the convenient one: a reviewer whose lane lost a cross-run race needs the same three facts a code lane's resolver does, and F-10's asymmetry was a gap rather than a decision.

    PINNED BY `tests/test_integration_refusal_cause.py::ResolverRecordTests::test_the_REVIEW_path_gets_the_resolver_record_TOO`, which drives the write site with `{"action": "review"}` (first asserting `integration_action_for_item` genuinely reports `review`, or the test would pin nothing) and requires both the `Refusal` and the recorded cause. GREEN.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: the new test file GREEN after and RED before; the bare suite count line WITH a node-id comparison against the pre-change baseline (not a count comparison); and each of the three controls demonstrated FAILING when broken on purpose (reinstate a failure-of-the-work phrasing; make a plain conflict deferrable; return adjacency-only for a hunk with no base section).
  - Observed evidence: GREEN AFTER:

    ```
    $ python3 -m pytest tests/test_integration_refusal_cause.py -o addopts="" -q
    ...............................                                          [100%]
    31 passed in 4.76s
    ```

    RED BEFORE, produced exactly as the plan specifies (revert ONLY `agent_workflows/runner_shared.py` while keeping the new tests, via `git stash push -- agent_workflows/runner_shared.py`):

    ```
    FAILED tests/test_integration_refusal_cause.py::AdjacencyPredicateTests::test_both_sides_only_adding_is_ADJACENCY_ONLY
    FAILED tests/test_integration_refusal_cause.py::AdjacencyPredicateTests::test_a_TWO_WAY_hunk_is_UNKNOWN_and_NEVER_adjacency_only
    FAILED tests/test_integration_refusal_cause.py::CauseChannelTests::test_the_token_round_trips_and_is_STRIPPED_from_what_a_human_reads
    FAILED tests/test_integration_refusal_cause.py::CauseChannelTests::test_the_gate_status_map_is_THREE_reachable_causes_and_fails_closed
    FAILED tests/test_integration_refusal_cause.py::CauseChannelTests::test_an_OLD_record_with_no_token_reads_as_UNKNOWN
    FAILED tests/test_integration_refusal_cause.py::CauseChannelTests::test_the_cause_is_written_ADDITIVELY_onto_the_existing_ladder_record
    FAILED tests/test_integration_refusal_cause.py::CauseChannelTests::test_a_cause_NAMED_IN_PROSE_is_not_mistaken_for_the_field
    FAILED tests/test_integration_refusal_cause.py::CauseChannelTests::test_the_shape_token_is_OPTIONAL
    FAILED tests/test_integration_refusal_cause.py::ConflictReplayTests::test_the_replayed_conflicts_reach_the_write_site_with_the_new_cause
    FAILED tests/test_integration_refusal_cause.py::ConflictReplayTests::test_xipfy1_names_the_HUNKS_author_and_NOT_the_last_commit_touching_the_file
    FAILED tests/test_integration_refusal_cause.py::ConflictReplayTests::test_92u0v9_is_ADJACENCY_ONLY_and_names_its_real_peer
    29 failed, 1 passed in 3.79s
    ```

    (The 1 pass is `test_re_merging_on_a_FRESHER_BASE_does_not_clear_either_conflict`, which asserts F-7 about GIT's behavior and correctly does not depend on this change at all.)

    THE BARE SUITE:

    ```
    $ python3 -m pytest
    1 failed, 8719 passed, 3 skipped, 2 xfailed, 6 warnings in 140.45s (0:02:20)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    COMPARED BY NODE ID, NOT BY COUNT, exactly as the plan requires. The single failing node is `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` and it is NOT a regression from this change, PROVEN by re-running that file with this change's source edits stashed:

    ```
    $ git stash push -- agent_workflows/runner_shared.py tests/test_runner_shared.py
    $ python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    E       assert 'OPENCODE_CONFIG_CONTENT' not in {'AGENT': '1', ...}
    tests/test_turn_bounds.py:310: AssertionError
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 75 passed in 5.54s
    ```

    The same node fails identically without this change, and the assertion reads the AMBIENT `OPENCODE_CONFIG_CONTENT` that an `opencode`-launched turn exports, so it is environment-dependent rather than change-dependent. It is already carried by 20+ existing backlog items (e.g. `j08jky`, `cfgj8s`, `se8vsp`), so no new item was filed; a duplicate `n99ujo` was created and then REMOVED on discovering them. NO OTHER failing node id appeared.

    ALL THREE CONTROLS DEMONSTRATED FAILING when the property they guard was deliberately broken in `agent_workflows/runner_shared.py` and then restored:

    CONTROL (a), broken by short-circuiting the cause-specific branch so `git-merge-conflict` falls to the shared wording:

    ```
    E   AssertionError: 'failure of the work' unexpectedly found in "integration refusal kind 'merge-refused' is terminal on its first attempt: it is neither the transient dirty-overlap condition nor an unmeasured-gate refusal, so it asserts a real failure of the work ..." : FIX: a git conflict is not a statement about the lane's code. ...
    FAILED tests/test_integration_refusal_cause.py::AntiRegressionControls::test_control_a_the_conflict_verdict_may_NEVER_regain_a_failure_of_the_work_claim
    1 failed, 29 deselected in 0.39s
    ```

    CONTROL (b), broken by adding `INTEGRATION_REFUSAL_CONFLICT` to `classify_integration_refusal`'s tuple:

    ```
    E   AssertionError: True is not false : FIX: revert whatever made `merge-refused` deferrable. Repetition cannot order two insertions at one location, so a retry spends budget for a guaranteed identical refusal
    FAILED tests/test_integration_refusal_cause.py::AntiRegressionControls::test_control_b_a_plain_conflict_may_NEVER_become_DEFERRABLE
    1 failed, 29 deselected in 0.39s
    ```

    CONTROL (c), broken by treating a missing base section as an empty one (emptying the `two_way` list, which is exactly how a "simplification" would undo it):

    ```
    E   AssertionError: 'adjacency-only' == 'adjacency-only' : FIX: a hunk with no `|||||||` base section proves nothing about whether either side ADDED or REPLACED. Return UNKNOWN and re-read the conflict with `--diff3` or from the three merge stages
    FAILED tests/test_integration_refusal_cause.py::AntiRegressionControls::test_control_c_a_hunk_with_NO_base_section_may_NEVER_read_adjacency_only
    1 failed, 29 deselected in 0.39s
    ```

    After restoring the file, re-verified GREEN: `31 passed`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`.

THE SPECIFIC DISCIPLINE THIS PLAN DEMANDS is that it must change WORDS AND RECORDS, NOT VERDICTS. Every cause keeps exactly the terminality it has today, and V-03 exists to prove that with a before/after table. An executor who finds themselves making a conflict deferrable, or resolving conflict content, has left this plan's scope: both were considered and are excluded on measured evidence (F-7), not by oversight.

FOUR PLACES THIS PLAN CAN GO WRONG QUIETLY, each found by measurement at review rather than by reasoning, and each already fenced above. FIRST, the cause space is THREE and not six (F-3b): writing a branch or a verdict sentence for `_STALE_BASE`, `_SCOPE_VIOLATION`, `_MISSING_LANE` or `_LANE_FAILURE` produces dead code asserting something this call path cannot produce, which is fabricated evidence dressed as thoroughness. SECOND, the adjacency predicate is UNSOUND on git's default two-way markers (F-6b), so the executor must supply a three-way hunk and return UNKNOWN without a base section; the failure direction matters because a wrong `adjacency-only` tells a resolver a semantic conflict is safe to keep-both. THIRD, the peer commit must come from the HUNK and not from the file's history (F-6c), because on this plan's own `xipfy1` case the file-history answer names an unrelated lane. FOURTH, the refusal writer does not redact (F-9), so anything E-04 writes must already be relative and V-04 proves it with the shipped sanitizer.

Note also that this plan's own backlog item had its first proposed remedy REFUTED by measurement, so an executor should treat the concern's negative results as load-bearing and re-measure rather than re-propose them. The same standard applies to the four corrections above: each is checkable in minutes with the commands cited, and re-deriving one is cheaper than shipping past it.
