# Review: Remove the unshipped supports_deny_push flag and the three unenforced action verdicts

- Subject-Id: 01reg8
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4e91bb1b`. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review and again at `--phase review-finalize` after the revisions.

THE PLAN'S CENTRAL CLAIM IS TRUE AND I RE-VERIFIED EVERY LOAD-BEARING PART OF IT. `aw host capabilities
opencode` prints three `REFUSED` lines each naming `supports_commit_gateway, supports_deny_push` and the
summary `1 host(s) reported; 3 (host, action) pair(s) refused`. Nothing consumes those verdicts: the only
non-test caller of `check_action_capabilities` is `host_cmd._action_rows`, and `preflight_host_capabilities`
has no caller outside tests, which `run_selection_policy`'s own `SKIP_HOST_CAPABILITY_UNAVAILABLE` comment
already records ("NOT REACHABLE TODAY: neither driver calls that preflight"). The never-shipped claim also
holds: `git log -S"supports_deny_push"` gives one commit, `30108f78`, and `v1.3.0-rc.1` predates it by six
weeks. So the removal is correct and the maintainer's ruling is faithfully transcribed.

WHAT THE PLAN GOT WRONG IS EVERYTHING AROUND THE PART IT MEASURED, and two of the eight findings would
have stopped execution or silently gutted a safety property.

PR-601 IS THE ONE THAT WOULD HAVE BLOCKED. The plan's `- Scope-Paths:` and its spec-sync section both
name `.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`. That file
does not exist; the spec is `20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`. This
is not cosmetic, because the declared path is the mechanism by which a spec amendment becomes visible:
`runner_shared.declared_spec_paths` reads `- Scope-Paths:` and matches on the `.spec.md` facet, and
`spec_impacts_for_queue` feeds the pre-run announcement from it. The authored value WOULD have been
announced (it ends in `.spec.md`) while pointing at nothing, and then E-09 would have edited a spec the
run never declared, which is exactly the undeclared-spec-edit case both runners' end-of-run report exists
to catch. The finalize scope gate would have demanded a `--scope-reason` for the real path and a
`--scope-ack` for the phantom one.

PR-602 IS THE ONE THAT MATTERS MOST, and it is a property no lint can see. After E-04 the only surviving
action class is `read_only`, whose `required` tuple is EMPTY. So `check_action_capabilities` can no longer
return `satisfied=False` for any production action, and `preflight_host_capabilities` can no longer refuse.
Every REFUSES-side test in `CheckerTests` and `FailClosedPreflightTests` would then pass VACUOUSLY if
re-pointed at `ACTION_READ_ONLY`. The plan did propose a synthetic `_gated_for_test` action, which is the
right answer, but buried it as the last clause of an item that also re-pointed twelve methods and edited a
second file, with an `Expected outcome` that asserted only "the REFUSES/PROCEEDS pair still both run" -
and "runs" is precisely what a vacuous test does. This module is unusually explicit that one-sidedness is
the failure mode it fears: `_probe_fresh_verifier_session` requires both halves because "accepting only
the positive half would report True for a contract that never refuses", and
`test_it_PROCEEDS_when_the_same_action_is_satisfied` carries the docstring "a one-sided demonstration
proves nothing". Losing the refusal side while the file still contains tests NAMED `test_it_REFUSES_...`
is worse than losing the coverage outright, because the names assert coverage that is gone.

I DID NOT TAKE THE SYNTHETIC-ACTION IDEA ON FAITH; I DROVE IT. Inserting
`ActionRequirement(action="_gated_for_test", required=(CAP_COMMIT_GATEWAY, CAP_FRESH_VERIFIER_SESSION),
...)` into `ACTION_CAPABILITY_REQUIREMENTS` and restoring it in `finally` yields `satisfied=False` with
`missing=('supports_commit_gateway', 'supports_fresh_verifier_session')` on an all-False descriptor,
`satisfied=True` when both are set, `preflight_host_capabilities` refusing with
`finding_code='RUN-HOST-CAPABILITY'`, and the dict back to its four original keys after the block. So the
approach works, which is why this is a FIXED restructuring rather than a REPLAN. It is now E-06, ordered
BEFORE any deletion, with V-06 demanding both sides and the restore-on-exception proof, because the suite
runs under `pytest-randomly` and a leaked global would corrupt later tests non-deterministically.

PR-603 is a falsification the plan created and did not notice. Three prose sites (`host_cmd`'s module
docstring, `cli.py`'s `host probe` help, and the `SAFETY & DEFAULTS` epilog) do not merely say "two
capabilities are declared and never probed"; each ALSO says every action requiring them is therefore
REFUSED, and calls that fail-closed. After this plan NO action requires them, so the second clause becomes
false and the reassurance it offers becomes unearned. The plan's E-05 treated all of this as a count
correction and its `Expected outcome` was a grep for `push denial|four action classes|LEFT IN PLACE`,
which those sentences survive. E-05 now names the second correction explicitly and its expected outcome
adds the negative claim.

PR-604 is a smaller version of the same class and would have failed E-02 on the wrong error.
`tests/test_host_capability_extension.py` imports `argparse`, `io`, `json`, `unittest` and two
`contextlib` names, and NOT `dataclasses`. E-02's first assertion calls `dataclasses.fields`, so the new
test would have raised `NameError` at collection. It would still have "failed before", satisfying V-02's
letter, while proving nothing about the field's presence.

PR-605 is under-measurement of the test surface. The plan said "nine uses of `CAP_DENY_PUSH` and the three
action constants". An AST pass over the file finds the references spread across 16 test methods plus one
class-level table, in four classes. E-07 and E-08 now enumerate every one by symbol, which surfaced three
edits the plan's list missed: `test_a_fully_capable_host_passes_every_action` becomes a positive assertion
over a requirement-free action unless it also exercises the seam;
`test_requirement_map_structure_and_coverage` asserts `review.unrepresented` contents whose subject E-04
deletes; and `test_the_message_carries_the_recovery_command` asserts the literal string `required by
mjx7ne action review`, so its expectation changes with the action name. I also checked
`tests/test_hostdedup_third_host.py`, which the plan put in its verification command: it references
neither the flag nor any action constant, so it needs no edit, and the plan now says so rather than
leaving an executor to look.

PR-606 and PR-607 are adjacent scope temptations the plan left unguarded, each of which a reasonable
executor would have taken. Four of the seven `UNREPRESENTED_SPEC_CAPABILITIES` keys (`argv_capture`,
`timeout_cancel`, `hook_preserving_commit`, `isolated_worktree`) are referenced ONLY by the three entries
being deleted, so "tidy up the now-unused keys" looks like completion; it would in fact withdraw
spec-derived gaps, against that dict's own stated purpose ("a requirement that is never listed is a
requirement that can never fail"). Symmetrically, `run_evidence`'s `RUN-HOST-CAPABILITY` row sits three
lines from the comment E-05 edits and carries `binding=BOUND`; I verified its three named predicates all
survive this plan, so the binding stays honest and the row must not be touched. Both are now declined in
Deferred with the reason, and both appear in the gate's not-in-scope list.

PR-608 is the gate. As authored it was three sentences and was missing the approval statement, the scope
fence, the honesty rule, the stop conditions, and any acknowledgement of who owns the transition. That
last one matters here because this plan amends an APPROVED spec, which is the highest-leverage change a
run can make, and because two judgements in it are genuinely the maintainer's (OQ-01 and the new OQ-03).

I RAISED ONE NEW OPEN QUESTION RATHER THAN DECIDING IT. OQ-03: the code's action vocabulary drops to one
class while spec 5.2's table keeps four rows. The module's existing comment argues explicitly against
creating that disagreement ("Deliberately the spec's four, not a convenient two: ... would have silently
renamed the policy and made this layer's vocabulary disagree with the packet field the spec specifies"),
so this plan knowingly does the thing that comment was written to prevent. I did not resolve it, because
narrowing the spec table would withdraw host requirements the maintainer has not asked to withdraw and
would collide with backlog `oq05nc`, whose whole premise is that a real push-denial boundary may one day
be built and needs a place in 5.2 to land. It is non-blocking: either answer leaves the removal correct.
E-04 now requires the replacement comment to state the divergence, so it is recorded rather than silent.

TWO THINGS I CHECKED AND FOUND CORRECT, recorded so a later reader does not re-derive them. Backlog
`aagh7v` carries no `- Blocks-Release:` and is `Work-Kind: followup`, so no release gate is owed and the
every-live-bug rule does not apply. And the plan's claim that `tests/test_run_no_push_boundary.py` no
longer exists is true, so it is correctly out of scope.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | `ls .aw/records/specs/approved/20260826-0718-01-*.spec.md` -> No such file; the spec is `20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`; `runner_shared.declared_spec_paths` matches on the `.spec.md` facet and `spec_impacts_for_queue` feeds the pre-run announcement from it | THE DECLARED SPEC PATH NAMES A FILE THAT DOES NOT EXIST, in `- Scope-Paths:` and again in the spec-sync section. Because the value ends in `.spec.md` it would have been ANNOUNCED as a declared spec edit while resolving to nothing, and E-09 would then have edited the real spec UNDECLARED, which is the precise case both runners' end-of-run spec report exists to catch. The finalize scope gate would have demanded a `--scope-reason` for the real path and a `--scope-ack` for the phantom one, so the plan could not have finalized cleanly. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Corrected both occurrences to the real path. F-5 now records the correction explicitly so the wrong string is not restored, and the spec-sync section states why the declaration is the mechanism that makes the amendment visible. |
| PR-602 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `ACTION_CAPABILITY_REQUIREMENTS[ACTION_READ_ONLY].required == ()`; after E-04 it is the only entry; `_probe_fresh_verifier_session` docstring "accepting only the positive half would report True for a contract that never refuses"; `test_it_PROCEEDS_when_the_same_action_is_satisfied` docstring "a one-sided demonstration proves nothing"; driven at review: synthetic `_gated_for_test` REFUSES naming both capabilities, PROCEEDS when both True, dict restored after the block | THE REMOVAL MAKES EVERY REFUSAL TEST VACUOUS, and the plan's own success criterion could not detect it. With only a requirement-free action left, `check_action_capabilities` cannot return unsatisfied and `preflight_host_capabilities` cannot refuse, so re-pointing the REFUSES tests at `ACTION_READ_ONLY` leaves them passing while asserting nothing - with method names still claiming they test a refusal, which is worse than deleting them. The plan named the right remedy (a synthetic gated action) but as the last clause of a 12-method item, and asserted only that the pair "still both run", which is exactly what a vacuous test does. | C:Medium (a test-local global mutated under random ordering); U:Low; S:Low; F:Medium (silent loss of the only two-sided coverage of the preflight); Overall:Medium | FIXED | Promoted to its own item E-06, ordered BEFORE any deletion, with the vacuity argument stated as the reason. Added F-7 recording the driven proof. V-06 requires both sides driven plus restore-on-normal-exit AND restore-on-raise; V-07 requires the pair COLLECTED and PASSING and the REFUSES side to name the capabilities it observed missing. A project-conventions bullet records that the suite runs under random ordering, so a leaked global is non-deterministic. |
| PR-603 | MEDIUM | UNDER-SCOPE | F. Honest documentation | `host_cmd` module docstring "Those read not-supported on every host, so every action requiring them is refused. That is fail-closed and correct"; `cli.py` `host probe` "any action requiring them is refused; that is fail-closed, not a host defect"; `cli.py` epilog "actions requiring them are refused: fail-closed"; after E-04 no action requires either capability | THE PROSE EDITS WERE SCOPED AS A COUNT CORRECTION, MISSING A CLAIM THE REMOVAL FALSIFIES. Each of the three sites asserts not only that two capabilities are unprobed but that actions requiring them are consequently refused, offering that as the fail-closed reassurance. After this plan nothing requires them, so the sentence describes a protection that no longer operates - the same defect this plan exists to remove, relocated from the verdict table into the help text. E-05's grep (three alternatives: `push denial`, `four action classes`, `LEFT IN PLACE`) does not match these clauses, so the item would have reported success with them intact. | C:Low; U:Medium (the help text is a user's only account of what the verb proves); S:Low; F:Low; Overall:Low | FIXED | E-05 now names the second correction at each of the three sites and states the reason (nothing then requires them). Its `Expected outcome` adds the negative claim that no remaining sentence in those files asserts an action is refused for want of a runner-safety capability. F-2 records the correction. |
| PR-604 | MEDIUM | IN-SCOPE | E. Testing | `tests/test_host_capability_extension.py` imports `argparse`, `io`, `json`, `unittest`, `contextmanager`, `redirect_stdout` - no `dataclasses`; E-02's first assertion calls `dataclasses.fields(HostSandboxCapabilities)` | THE FIRST ASSERTION OF THE REGRESSION TEST WOULD HAVE RAISED `NameError`, NOT FAILED. V-02 requires the new class to FAIL against the unmodified module, and a collection-time `NameError` satisfies that wording while proving nothing about whether the field is present. The test that is supposed to prove the removal would have been unable to observe it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now requires `import dataclasses` be added and says why. Its `Expected outcome` requires the failure be on an ASSERTION rather than a collection or import error. Also strengthened the assertion set: `__all__` absence, the full requirement-map key set, and `UnknownActionError` for all THREE removed action names rather than one. |
| PR-605 | MEDIUM | UNDER-SCOPE | E. Testing / G. Plan executability (right-sizing) | AST pass over `tests/test_host_capability_extension.py`: the four targets appear in 16 test methods plus the class-level `PRESENCE_VS_OBSERVATION` table, across 4 classes (26 matching lines); plan text said "nine uses"; `test_the_message_carries_the_recovery_command` asserts the literal `required by mjx7ne action review`; `test_requirement_map_structure_and_coverage` asserts `review.unrepresented` membership; `test_a_fully_capable_host_passes_every_action` iterates `ACTION_CLASSES` | THE TEST SURFACE WAS UNDERCOUNTED BY ROUGHLY HALF AND THREE CONSEQUENT EDITS WERE MISSED, inside a single item that also edited a second test file and built the seam. The three: a positive-side test that degenerates to iterating one requirement-free action; an assertion whose subject (`review.unrepresented`) E-04 deletes; and a literal expected string containing the action name. An executor working from "nine uses" would have found the rest by test failure, one run at a time. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split the original E-06 into E-06 (seam), E-07 (action-class re-point, all 12 methods named by symbol with the three missed edits called out) and E-08 (capability-name re-point, including the `PRESENCE_VS_OBSERVATION` row and `CONTRACT_FIELDS`). F-4 records the AST measurement and marks the "nine uses" figure as an undercount. Added a note that `tests/test_hostdedup_third_host.py` needs no edit, verified at review. |
| PR-606 | LOW | OVER-SCOPE | C. Architecture / D. Anti-regression | `UNREPRESENTED_SPEC_CAPABILITIES` has 7 keys; `argv_capture`, `timeout_cancel`, `hook_preserving_commit`, `isolated_worktree` are referenced only by the three entries E-04 deletes; the dict's own comment: "a requirement that is never listed is a requirement that can never fail, which is the fail-OPEN direction" | FOUR SPEC-DERIVED GAP RECORDS BECOME UNREFERENCED AND WOULD LOOK LIKE DEAD CODE TO TIDY. The plan neither declared them in scope nor protected them. Deleting them would withdraw four spec-required capabilities from the record of what this contract cannot represent, which is the fail-OPEN direction the dict was written to prevent, and it is not covered by the maintainer's ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states the keys must all stay, with the count and the reason. Its `Expected outcome` asserts `len(UNREPRESENTED_SPEC_CAPABILITIES) == 7`. Added a Deferred entry with a `Carrier-Declined`, and named it in the gate's not-in-scope list. |
| PR-607 | LOW | OVER-SCOPE | A. Correctness / F. Honest documentation | `run_evidence.RUN_FINDING_CODES`' `RUN-HOST-CAPABILITY` row carries `binding=BOUND` with predicates `preflight_host_capabilities`, `format_host_capability_finding`, `check_action_capabilities`, all three of which survive; the `RUN-NO-PUSH` retirement comment E-05 edits sits immediately above it and ends "DO NOT REINTRODUCE THE CODE BOUND TO A PRESENCE CHECK ... (`host_sandbox_profile.py:88-95`)" | THE ADJACENT FINDING-CODE ROW WAS NEITHER DECLARED IN SCOPE NOR PROTECTED, and E-05 sends the executor into that exact region. Two risks: re-examining the `BOUND` binding (which is still honest, verified at review) and discarding the retirement comment's closing prohibition along with the sentence being corrected. That prohibition outlives the flag it discusses and is the reason the row was retired rather than rebound. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires the prohibition be PRESERVED and only its stale line reference converted to a symbol citation. Added a Deferred entry declining any change to the row or its binding, with the verification that its three predicates survive; `- Scope:` OUT and the gate's not-in-scope list both name it. |
| PR-608 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: four sentences (approve-first, commit path, an anti-inference reminder, and an instruction to "move the plan to `executed/` via the lifecycle transition"); `- Cohesion rationale: not required` | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS on a plan that amends an APPROVED SPEC. No statement of what a human is approving (and two judgements here are genuinely the maintainer's: OQ-01's now-gateless capability and the new OQ-03); no scope fence naming the intended surface within each declared path; no stop conditions; and a transition instruction that named neither the runner's ownership nor `aw ipd finalize`. With the item count now 11, `Cohesion rationale: not required` also no longer held. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming both overrulable judgements and the deliberate spec/code count divergence; a per-path scope fence stated as a DECLARATION with an explicit not-in-scope list mirroring Deferred, and the finalize-justifies-afterwards rule rather than a stop-on-scope directive; the hard-MUST honesty rule tied to the vacuity risk; three genuine stop conditions (an unrestorable seam, a `specs check` refusal, a symbol already changed under the executor); and the transition with conditional runner/executor ownership and an explicit no-hand-rolled-`git mv`. Filled in the cohesion rationale. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan proposes a synthetic test-local action to keep the preflight tests two-sided. Accept that approach, accept the loss of refusal coverage, or REPLAN? | Accept the synthetic action, but promote it to its own item ordered before any deletion, and prove it works at review rather than assuming. | (a) Re-point the refusal tests at `ACTION_READ_ONLY` - rejected: its `required` tuple is empty, so every REFUSES assertion becomes vacuous while the method names still claim coverage. (b) Delete the refusal tests outright - rejected: it discards the only two-sided coverage of `preflight_host_capabilities`, which survives this plan and is `RUN-HOST-CAPABILITY`'s binding. (c) REPLAN around keeping one gated production action - rejected: that contradicts the maintainer's ruling, which names all three entries for deletion. | Driven at review: inserting `_gated_for_test` requiring `(CAP_COMMIT_GATEWAY, CAP_FRESH_VERIFIER_SESSION)` yields REFUSES naming both, PROCEEDS when both True, `preflight_host_capabilities` refusing with `RUN-HOST-CAPABILITY`, and `ACTION_CAPABILITY_REQUIREMENTS` restored to its original keys after the block | yes |
| D-2 | Should the four now-unreferenced `UNREPRESENTED_SPEC_CAPABILITIES` keys be pruned as part of the cleanup? | No. Require them kept, and assert the count. | (a) Prune them - rejected: they record spec-required guarantees this contract cannot represent, and the dict's own comment states that an unlisted requirement can never fail, which is the fail-OPEN direction. (b) Leave the plan silent - rejected: four keys becoming unreferenced in the same diff reads as dead code, so silence invites the deletion. | `UNREPRESENTED_SPEC_CAPABILITIES`' own comment ("a requirement that is never listed is a requirement that can never fail"); the four keys are referenced only by the three entries E-04 deletes | yes |
| D-3 | Should the spec's 5.2 host-requirement bullet, its four-row action table, and the packet example's `deny_push` string be narrowed to match the code? | No. Amend only the sentences whose truth depends on the Python flag existing; raise the divergence as OQ-03 for the maintainer. | (a) Narrow the table to one row for parity - rejected: it withdraws host requirements the maintainer did not authorize withdrawing, and backlog `oq05nc` is the live carrier for building a real push-denial boundary that would need somewhere in 5.2 to land. (b) Leave the divergence unremarked - rejected: the module comment E-04 replaces argues explicitly AGAINST creating it, so silently doing so would look like an oversight and invite a later "restore parity" commit. | Spec 5.2's bullet and table describe what a HOST must prove; backlog `oq05nc` anticipates this plan landing first; `host_sandbox_profile`'s "Deliberately the spec's four, not a convenient two" comment | yes |
| D-4 | `supports_commit_gateway` survives and after this plan gates no action. Resolve OQ-01 myself, or leave it to the maintainer? | Leave it open to the maintainer; sharpen the consequence and add the second reason it now has to exist. | (a) Remove it too for consistency - rejected: the 2026-09-10 ruling names only `supports_deny_push`, and removing a second public field on my own authority exceeds a review's remit. (b) Close OQ-01 as resolved-keep - rejected: the maintainer is the owner and the position genuinely weakens (declared, unprobed, and now gating nothing), so it deserves a decision rather than a reviewer's default. | Backlog `aagh7v` records the ruling's scope as `supports_deny_push` only; backlog `b7tlsh` is the live carrier for the commit-gateway question; after E-04 it is also the capability E-06's synthetic action requires | yes |
