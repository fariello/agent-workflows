# IPD: Remove the never-built --follow-generated run flag because nothing generates an IPD mid-run

- Date: 2026-09-24
- Kind: child
- Concern: `--follow-generated` (spec `25kzda` 2.1) is registered, appears in `--help`, and REFUSES (`runner_shared.RUN_POLICY_FLAGS` row `flag="--follow-generated"`, `implemented=False`). Backlog `ceauac` asks whether the behavior is wanted and how a generated IPD would be detected. MEASURED: nothing in the runner can generate an IPD during a run, nothing reads back what a turn created, and the queue cannot admit one. The flag follows a thing that does not exist, and its refusal names an owner (`backlog x8diyb`) that is already `done`, so an operator who hits it is pointed at a closed item.
- Scope: REMOVE `--follow-generated` from the shared flag table (both hosts register from it), update the docstrings that name it, add a regression test proving both host parsers reject it, amend spec `25kzda` so every mention states the report-only behavior plainly and records why same-run following is not offered, correct the stale `x8diyb` owner sentence in spec `z7nbn1` 3.4, and add a CHANGELOG line. EXCLUDES building any production action (`--action plan` stays refused; spec `z7nbn1` owns it), any generated-artifact reporting (no producer exists), and any change to `refuse_unimplemented_run_flags` as a mechanism (it stays, with no current row).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_shared.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- Set: followgen
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: hzdq8y
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved
- From-Backlog: ceauac

## Workflow history
- 2026-09-25 approved (aw set): status set to approved

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED. Independently reproduced the case for removal: `ACTION_IMPLEMENTED` is `frozenset({'review'})` so `--action plan` is refused, `files_changed`/`recommended_next_action` are never parsed back (zero hits), and `--follow-generated` is the ONLY `implemented=False` row of 15. PR-001 (the declared `25kzda` path `20260826-0718-01-...` DOES NOT EXIST, so `_scope_match` is False and the finalize gate fails in both directions while E-01(c) and V-04 would have passed VACUOUSLY over a missing file), PR-002 (two uncarried obligations; `- Carrier: z7nbn1` is REFUSED because `_CARRIER_TARGET_TYPES` excludes specs by maintainer decision), PR-003 (two stale inherited facts: the contract test `tests/test_run_flag_surface.py` was deleted in `19313eed`, and `--with-dependencies` is already implemented so the docstring E-02 rewrites is doubly wrong), PR-004 (leaving `z7nbn1` OQ-01 naming a removed flag with nothing reconciling it), PR-005 (thin gate; E-03 used an absolute `/tmp` path and probed only the harmless polarity) all FIXED. Added Findings 7 to 9 and corrected `- Scope-Paths:` to the real id6 path. Findings in `.aw/records/reviews/20260924-followgen-01-hzdq8y-remove-the-never-built-follow-generated-run-flag-because-not.review.md`. Readiness go-pending-approval.
- 2026-09-25 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED (a dead spec path defeated the scope gate and two of the plan's own verifications)

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ceauac; re-measured that no run outcome across 481 recorded turns ever created a plan outside its frozen manifest, that `files_changed`/`recommended_next_action` are never parsed back, and that `--action plan` is refused, so the plan removes the flag rather than designing detection.

## Goal

Stop advertising a run flag whose subject cannot occur. Remove `--follow-generated` from the CLI and from spec `25kzda`, keep the spec's report-only rule for generated IPDs (so a future production action inherits the safe default), and record why same-run following is not offered.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Regression test first

- [x] E-01 Add a test class `FollowGeneratedRemovedTests` to `tests/test_runner_shared.py` asserting (a) `"--follow-generated" not in runner_shared.RUN_POLICY_FLAGS_BY_FLAG` and `"follow_generated" not in runner_shared.RUN_POLICY_FLAGS_BY_DEST`; (b) `oc_runipd.build_parser().parse_args(["start", "abc123", "--follow-generated"])` and the same on `agy_runipd.build_parser()` raise `SystemExit` with code 2 (argparse unknown argument); (c) the spec `25kzda` file contains no `--follow-generated` token. Run it against the unmodified tree and confirm it FAILS.
  - RESOLVE THE SPEC PATH FOR (c) BY ID6, NOT BY A LITERAL STRING. The spec was renamed to the id6 grammar and now lives at `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`; the old `20260826-0718-01-...` name does NOT exist (measured: `Path(...).exists()` is False). A hardcoded stale path makes assertion (c) read a missing file, which either errors or (worse, if the test guards with `if exists`) passes VACUOUSLY while the spec still names the flag. Glob the approved dir for `*-25kzda-*.spec.md` and fail loudly if it does not resolve to exactly one file.
  - ALL THREE PARTS ARE ALREADY CONFIRMED FALSIFIABLE (measured at review, re-derive at execution): (a) both `RUN_POLICY_FLAGS_BY_FLAG` and `RUN_POLICY_FLAGS_BY_DEST` carry the flag today; (b) both host parsers ACCEPT `--follow-generated` today, returning `follow_generated=True`, and BOTH return `SystemExit(2)` for a genuinely unknown flag, so the post-removal assertion is testing the right mechanism; (c) the spec carries 9 occurrences.
  - Depends on: none
  - Expected outcome: the new test exists and fails on the current tree because the flag is still registered and the spec still names it.
  - Execution state: performed

### Task group 2: Remove the flag

- [x] E-02 In `agent_workflows/runner_shared.py`, delete the `RunPolicyFlag(flag="--follow-generated", ...)` row from `RUN_POLICY_FLAGS`. Update the `refuse_unimplemented_run_flags` docstring (it says "This is the honest end state for `--follow-generated` and `--with-dependencies`") to say the mechanism is retained for any future registered-but-unbuilt flag and that no row currently uses it. Do not delete the function or its call in `initialize_run_core`.
  - THE DOCSTRING IS ALREADY WRONG ABOUT `--with-dependencies`, AND THE REWRITE MUST NOT PRESERVE THAT. Measured: `--with-dependencies` is `implemented=True` (plan `dhycim` flipped it), and `--follow-generated` is the ONLY `implemented=False` row of the 15 today. So the sentence "whose behavior nobody has built" is false for one of the two flags it names; do not merely swap one name out. The corrected docstring must ALSO state the post-removal fact plainly: the loop runs over ZERO rows (verified by simulation: removing the row leaves `[]` unimplemented), so the function is a deliberate no-op kept for the NEXT unbuilt flag rather than dead code someone should delete.
  - THE `- Expected outcome:` BELOW IS ONLY SATISFIABLE IF THE REWRITE DROPS THE FLAG NAME ENTIRELY. Write the replacement so it names no specific flag; otherwise E-02's own zero-hit check and V-02 both fail on the docstring you just wrote.
  - Depends on: E-01
  - Expected outcome: `rg -n "follow.generated" agent_workflows` returns no hit (measured today: 3 hits, all in `runner_shared.py`, two in the row and one in this docstring; `rg` honors gitignore so the `__pycache__` `.pyc` is correctly skipped); both host parsers reject the flag; the E-01 parts (a) and (b) pass.
  - Execution state: performed

- [x] E-03 Confirm old run state stays resumable: `apply_run_policy_flags_on_resume` and `freeze_run_policy_flags` iterate `RUN_POLICY_FLAGS` only, so a stale `options["follow_generated"]` key in a pre-removal `state.json` is inert. Prove it with a one-off probe that loads a state dict carrying the stale key, calls `runner_shared.apply_run_policy_flags_on_resume(state, argparse.Namespace())`, and shows it returns `False` without raising. No code change unless the probe fails; if it fails, STOP and report.
  - PROBE BOTH POLARITIES, NOT JUST `False`. `follow_generated: False` is the trivially safe case; the one that would matter is a stale `True`, because that is the value an operator who passed the flag would have had refused BEFORE the run and is the only value that could plausibly be acted on. Measured at review on the CURRENT tree: both `{"follow_generated": False}` and `{"follow_generated": True}` return `False` with no raise, so the claim holds in the dangerous direction too. Re-derive AFTER the removal, which is the state that actually matters.
  - RUN THE PROBE INSIDE THE WORKSPACE, not under a hardcoded absolute `/tmp/...` path. The original text named a machine-local absolute directory, which is exactly the kind of string the leak-sanitizer exists to keep out of shared output and which will not exist on another machine. A throwaway `python3 -` heredoc needs no directory at all.
  - Depends on: E-02
  - Expected outcome: the probe reports `False` (no change applied) for BOTH a stale `True` and a stale `False`, with no traceback.
  - Execution state: performed

### Task group 3: Spec and docs

- [x] E-04 Amend spec `25kzda` at its REAL path, `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (the `20260826-0718-01-...` name this plan originally declared does NOT exist; the spec was renamed to the id6 grammar, measured). Remove `[--follow-generated]` from the 2.1 synopsis; drop it from the `--full-auto` "does not imply" list; replace the 2.1 bullet "`--follow-generated` adds newly generated IPDs ..." with a bullet stating generated IPDs are ALWAYS reported as generated next actions and never join the frozen run, with the reason (the frozen queue is what resume reads, and no producer exists; see this plan `hzdq8y`); reword the "generated child is recorded but excluded because `--follow-generated` was not selected" endpoint, the two dispatch-table cells "Do not run the generated IPD(s) unless `--follow-generated` is present", DAG rule 10, the "Generated child" consent-table row, and the worked `spec09` example, so each says report-only without naming the flag.
  - THERE ARE EXACTLY 9 OCCURRENCES (measured at review; re-derive before editing, since a sibling plan may land first). The enumeration above accounts for all 9: the 2.1 synopsis, the `--full-auto` list, the 2.1 bullet, the recorded-but-excluded endpoint, TWO dispatch-table cells (the `approved` row and the `open` row), DAG rule 10, the consent-table "Generated child" row, and the `spec09` example. Do not stop at the ones you recognize; `rg -c` before and after.
  - THE CONSENT-TABLE ROW NEEDS A DECISION, NOT A REWORD, and it is the only site that does. It reads `| Generated child | User may choose a new run, or original command may include --follow-generated | Requires original --follow-generated |`, i.e. BOTH cells are about the flag as the consent mechanism. With the flag gone the honest row is that a generated child ALWAYS requires a new run, with no same-run consent path at all. Write it that way rather than deleting the row, which would remove a case the consent table is supposed to enumerate.
  - RECORD THE AMENDMENT WITH THE TOOLING, not by hand-editing the history section: `python3 -m agent_workflows specs note <spec path> --message "AMENDED 2026-09-24 (plan hzdq8y, backlog ceauac): ..."` (or the current `aw specs note` form). The history is NEWEST-FIRST and the verb places the record correctly; the sibling plan `01reg8` amending the same spec uses exactly this form.
  - Depends on: E-02
  - Expected outcome: `rg -c "follow-generated" <real spec path>` returns 0 (from 9); `rg -n "generated next action" <same>` still returns the report-only rule; E-01 part (c) passes.
  - Execution state: performed

- [x] E-05 In spec `z7nbn1` section 3.4, replace "the repository has an unimplemented flag reserving the question (`--follow-generated`, measured `implemented=False`, owner backlog `x8diyb`)" with a sentence stating the flag was removed by plan `hzdq8y` because no producer existed, and that a plan building production actions may reintroduce an opt-in if the maintainer wants one. Do NOT edit the OQ-01 Resolution text (a recorded maintainer ruling). Add one CHANGELOG bullet under the pending 2.0.0 entry: "Removed the `--follow-generated` run flag. It was never implemented and always refused. Plans created during a run are reported as next actions, as before."
  - THE OQ-01 RULING WILL BE LEFT NAMING A FLAG THAT NO LONGER EXISTS, AND THAT IS A DELIBERATE, RECORDED CONSEQUENCE, not an oversight. Measured: the ruling says "When `--follow-generated` is implemented (owner backlog `x8diyb`), that flag becomes the opt-in mechanism for the same-run behavior". Leaving it verbatim is correct, because it is a dated maintainer ruling and a reviewer must not rewrite one. But the 3.4 replacement MUST therefore carry a forward pointer saying the ruling's named mechanism was removed and why, so a reader who reaches OQ-01 is not sent to a flag that is gone. Without that sentence the two paragraphs contradict each other with nothing reconciling them. See OQ-02, which is what asks the maintainer to confirm this reading.
  - THE RULING'S SUBSTANCE IS UNAFFECTED, WHICH IS WHY THIS IS SAFE: the ruling's operative decision is "NO FOLLOW FOR NOW ... the default stays report-only", and removing the flag makes report-only the ONLY behavior. Nothing the ruling required stops being true; only its forward-looking mechanism name goes stale.
  - CHANGELOG: the pending entry's heading is `## 2.0.0 (pending) - AW project layout, storage backends, install wizard, and operational state` (measured). Add the bullet there, in user-facing prose with NO em or en dashes.
  - Depends on: E-04
  - Expected outcome: `rg -n "x8diyb" <z7nbn1 spec>` shows only the untouched OQ-01 ruling (measured today: 2 hits, one in 3.4 which E-05 rewrites and one in the ruling which it must not); `rg -n "follow-generated" CHANGELOG.md` shows the new bullet.
  - Execution state: performed

### Task group 4: Full suite

- [x] E-06 Run the bare suite `python3 -m pytest` with no extra flags.
  - Depends on: E-05
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Both hosts register spec 2.1 flags from one table, `runner_shared.RUN_POLICY_FLAGS`, via `register_run_policy_flags`, so one row deletion removes the flag from `aw oc run` and `aw agy run` together.
- `RunPolicyFlag.implemented=False` means registered-and-refusing; `refuse_unimplemented_run_flags` raises `RunFlagRefusal` naming `row.owner`.
- Specs are living contracts; a plan that changes described behavior amends the spec and declares it in `- Scope-Paths:` (AGENTS.md "A PLAN MAY AMEND A SPEC").
- Commit through `aw commit hzdq8y -- <paths>`; CHANGELOG prose has no em/en dashes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-measured at HEAD `cfc7f5c1`:

1. NO PRODUCER. `run_selection_policy.ACTION_PLAN` is the only action that would author an IPD (spec rows "`approved`: author conformant IPDs", "`open`: graduate"). It is registered and refused: `runner_shared` docstring near `ACTION_IMPLEMENTED`: "that action is registered and REFUSED (`ACTION_IMPLEMENTED` excludes it)". `refuse_unrunnable_selected_types` refuses any non-`ipd` selection, so a spec or backlog item cannot even be queued.
2. NO DETECTION INPUT. `files_changed` and `recommended_next_action` appear only in the outcome schema text inside the turn prompt (`runner_shared` prompt builder, `"files_changed": [],`). `rg '\.get\("files_changed|\.get\("recommended_next_action'` over `agent_workflows/` returns nothing: they are written by agents and never read. `collect_earned_paths` reads the git diff, but only to decide closes.
3. NO QUEUE GROWTH. The queue is built once in `initialize_run_core` (`queue.append(` inside `for position, id6 in enumerate(queue_ids, start=1)`); spec `25kzda` DAG rule 11 "The queue never incorporates unrelated files discovered after freezing", and spec `z7nbn1` OQ-01 records why: "the frozen `state['queue']` is what `resume` reads".
4. NO OCCURRENCE IN PRACTICE. Probe `/tmp/opencode/g2/probe-followgen/p.py` over the main checkout's `.aw/records/runs/*/outcomes/*.json`: 481 outcomes, 446 listing a `plans/pending/*.ipd.md` path, 181 naming a plan other than the item's own, and exactly 1 naming a plan absent from its run's frozen manifest (`uvwqvz` in run `run-20260924T050407Z-3108751`, item `68uhp0`). That plan was ADDED by commit `df792b59` on 2026-09-23, before the run; the turn's summary says it migrated existing orchestrator checklists. So zero turns generated a new IPD.
5. STALE OWNER. The row's `owner="backlog x8diyb (rundepflags-01)"` names an item filed under `.aw/records/backlog/done/`; the refusal message points operators at closed work.
6. RESUME IS SAFE. 161 of 261 recorded `state.json` files carry `follow_generated` in `options`; `apply_run_policy_flags_on_resume` and `freeze_run_policy_flags` iterate the table, not the stored keys, so a leftover key is ignored (confirmed in E-03). RE-CONFIRMED at review on the current tree for BOTH polarities: a stale `follow_generated: True` and a stale `False` each return `False` with no raise, so the safety does not depend on the value.
7. THE CONTRACT TEST THAT ONCE PINNED THIS SURFACE IS GONE, which LOWERS this plan's risk and must not be mistaken for the opposite. Plan `dhycim` (executed) recorded that `tests/test_run_flag_surface.py` asserted the unimplemented set was EXACTLY `["--follow-generated", "--with-dependencies"]` and required `NOT YET IMPLEMENTED` and `x8diyb` in an unimplemented row's help, and it narrowed that assertion to exactly one row. That file NO LONGER EXISTS: it was deleted in commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests", and nothing in `tests/` now references `RUN_POLICY_FLAGS`'s implemented-ness, `NOT YET IMPLEMENTED`, or the flag name at all (measured: zero hits). CONSEQUENCE, stated in both directions: the removal will NOT break a shipped contract test, so no test edit is owed beyond E-01; and NOTHING would have caught the removal either, which is precisely why E-01 exists and why it must be written FIRST and shown failing.
8. `--with-dependencies` IS IMPLEMENTED, so the `refuse_unimplemented_run_flags` docstring is ALREADY stale independently of this plan. Measured: of 15 rows, exactly ONE is `implemented=False` (`--follow-generated`); `--with-dependencies` is `True`. The docstring names both as unbuilt. E-02's rewrite must correct that rather than carry it forward.
9. STALE SCOPE PATH. This plan declared spec `25kzda` at `.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, which does not exist; the spec was renamed to the id6 grammar (`20260826-25kzda-01-25kzda-...`). Measured: `ipd_lifecycle._scope_match(real_path, declared_path)` is `False`, so editing the real spec would have produced an out-of-scope path needing a `--scope-reason` while the declared path sat unmodified needing a `--scope-ack`. Corrected in `- Scope-Paths:` and in E-04. NOTE this is not unique to this plan: two other pending plans (`01reg8`, `1g4i1t`) declare the same dead path, so an executor of any of them hits the same gate. That is a finding against THEM and is not fixed here.

## Proposed changes (ordered, validatable)

1. Failing regression test (E-01).
2. Delete the table row and fix the docstring (E-02); prove old state resumes (E-03).
3. Amend spec `25kzda` to report-only wording with the reason (E-04); fix `z7nbn1` 3.4 and CHANGELOG (E-05).
4. Bare suite (E-06).

## Deferred / out of scope (with reason)

- Building a production action that authors IPDs mid-run (`--action plan`) and reporting what it created.
  - Carrier-Evidence: .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
  - Note on the carrier FORM, recorded because the obvious spelling is refused: `- Carrier: z7nbn1` does NOT resolve. `check_engine._CARRIER_TARGET_TYPES` is `("backlog", "plans")` and its comment records that accepting a SPEC "was offered to the maintainer and REJECTED", so a spec id6 in a `- Carrier:` field is reported as resolving to nothing (measured: `check.ipd-uncarried-obligation` at `error`). The spec is cited as `Carrier-Evidence` instead, which is the resolvable-artifact form. If this obligation needs a revisited HOME rather than a citation, file a backlog item and point `- Carrier:` at that.
- Re-introducing a same-run opt-in once a producer exists. Nothing to design until then; the maintainer can ask for it in the plan that builds production actions.
  - Carrier-Declined: no producer exists to follow; spec `z7nbn1` OQ-01 already fixes the default as report-only, and E-05 leaves a pointer in its 3.4.

## Scope check

- Over-scope: none. The `z7nbn1` edit is one sentence that names this flag and its dead owner.
- Under-scope: backlog `ceauac` itself is not transitioned here. Measured: it is ALREADY `- Status: graduated` with `- Graduated-To: followgen`, so nothing is owed on that front during execution; closing it `done` is a follow-up after this plan reaches `executed/` (see the gate).
- Under-scope, RESOLVED IN PLACE at review: the declared `25kzda` path did not exist (Finding 9) and would have failed the finalize scope gate in both directions; `- Scope-Paths:` and E-04 now name the real file.
- NOT A SCOPE CONCERN BUT WORTH KNOWING: a sibling pending plan `01reg8` also amends `25kzda`, and `1g4i1t` declares it too. Both declare the same DEAD path. Under a runner each item gets its own isolated worktree and the merge gate REFUSES rather than clobbers, so overlap is not a hazard to design around; if a merge is refused, re-run the refused item rather than hand-resolving the spec.

## Required tests / validation

- New `FollowGeneratedRemovedTests` fails before E-02/E-04 and passes after.
- Resume probe shows a stale key is inert.
- `rg` checks for zero `follow.generated` hits in `agent_workflows/` and spec `25kzda`.
- Bare `python3 -m pytest` passes.

## Spec / documentation sync

- Spec `25kzda` (approved) is AMENDED in E-04. WHY: it describes a flag whose subject cannot arise; leaving it makes every plan reviewed against 2.1 inherit a phantom obligation, and it is what made backlog `ceauac` exist. The report-only rule for generated IPDs is KEPT, so no contract weakens.
- Spec `z7nbn1` (to-review) section 3.4 is corrected in E-05; its OQ-01 ruling text is untouched.
- CHANGELOG gains one bullet (E-05).

## Open questions

### OQ-01: Remove the flag, or design detection of generated IPDs?

- Blocking: yes
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REMOVE. Findings 1 to 4: the only producer (`--action plan`) is refused, the outcome fields that could carry a detection are never parsed, the queue is frozen by design, and 0 of 481 recorded turns generated an IPD. Detection would be "invent the missing half", the shape superseded plan `kaygwo` E-07 already drew NEEDS REPLAN for.

### OQ-02: Does removal sit with the maintainer's z7nbn1 OQ-01 ruling?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: That ruling (2026-09-16, `- Blocking: yes`, `Owner: maintainer`, `Status: resolved`) says `--follow-generated` "becomes the opt-in mechanism for the same-run behavior" once implemented, with report-only as the default. DEFAULT: proceed with removal. WHY THIS IS NOT OVERRIDING THE RULING, which is the actual question: the ruling's OPERATIVE decision is "NO FOLLOW FOR NOW ... the default stays report-only", and removal makes report-only the ONLY behavior, so nothing the maintainer decided stops being true. What goes stale is the ruling's forward-looking MECHANISM NAME, and removal is a strict narrowing of the surface rather than a change of behavior: the flag has never done anything but refuse. WHY IT IS `Blocking: no` DESPITE TOUCHING A MAINTAINER RULING: no behavior changes under either answer, the ruling's text is left verbatim either way, and E-05's forward pointer keeps the spec internally coherent without editing it. THE ALTERNATIVE IS CHEAP AND IS SPELLED OUT so the maintainer can pick it without a round trip: keep the reserved flag, drop E-04/E-05's removal wording, and instead re-point the row's `owner` from the closed `backlog x8diyb` to `spec z7nbn1`, which fixes Finding 5 (the refusal pointing an operator at closed work) and leaves the reservation intact. Under that answer E-01/E-02 are dropped and the plan becomes a one-line owner correction plus a CHANGELOG line.
- Carrier-Declined: Both answers are fully specified inside this plan (removal as authored, or the one-line owner re-point named above), and neither leaves work for a later carrier; the maintainer is choosing between two complete options rather than deferring an obligation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_runner_shared.py -k FollowGeneratedRemoved` run on the tree BEFORE E-02, showing it FAILING (expected: at least one `failed`, with an assertion naming `--follow-generated`).
  - Observed evidence: Ran pytest before removal; confirmed 3 failures including AssertionError on '--follow-generated':
```
$ python3 -m pytest -o addopts="" tests/test_runner_shared.py -k FollowGeneratedRemoved
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=3207038148
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 92 items / 89 deselected / 3 selected

tests/test_runner_shared.py FFF                                          [100%]

=================================== FAILURES ===================================
_ FollowGeneratedRemovedTests.test_follow_generated_flag_removed_from_shared_tables _

self = <tests.test_runner_shared.FollowGeneratedRemovedTests testMethod=test_follow_generated_flag_removed_from_shared_tables>

    def test_follow_generated_flag_removed_from_shared_tables(self):
>       self.assertNotIn("--follow-generated", runner_shared.RUN_POLICY_FLAGS_BY_FLAG)
E       AssertionError: '--follow-generated' unexpectedly found in {'--allow-mixed': RunPolicyFlag(flag='--allow-mixed', dest='allow_mixed', kind='bool', implemented=True, owner='runner_shared.initialize_run_core', help='Admit a mixed-type selection without an interactive confirmation on a TTY; required unattended when selection mixes types'), ...}

tests/test_runner_shared.py:4345: AssertionError
_ FollowGeneratedRemovedTests.test_host_parsers_reject_follow_generated_flag _

self = <tests.test_runner_shared.FollowGeneratedRemovedTests testMethod=test_host_parsers_reject_follow_generated_flag>

    def test_host_parsers_reject_follow_generated_flag(self):
        for name, mod in (("oc", oc_runipd), ("agy", agy_runipd)):
            with self.subTest(host=name):
                parser = mod.build_parser()
                with contextlib.redirect_stderr(io.StringIO()):
>                   with self.assertRaises(SystemExit) as cm:
E                   AssertionError: SystemExit not raised

tests/test_runner_shared.py:4353: AssertionError
_ FollowGeneratedRemovedTests.test_spec_25kzda_contains_no_follow_generated_token _

self = <tests.test_runner_shared.FollowGeneratedRemovedTests testMethod=test_spec_25kzda_contains_no_follow_generated_token>

    def test_spec_25kzda_contains_no_follow_generated_token(self):
...
>       self.assertNotIn("--follow-generated", content)
E       AssertionError: '--follow-generated' unexpectedly found in '# Spec: aw <host> run ...'
=========================== short test summary info ============================
FAILED tests/test_runner_shared.py::FollowGeneratedRemovedTests::test_spec_25kzda_contains_no_follow_generated_token
FAILED tests/test_runner_shared.py::FollowGeneratedRemovedTests::test_follow_generated_flag_removed_from_shared_tables
FAILED tests/test_runner_shared.py::FollowGeneratedRemovedTests::test_host_parsers_reject_follow_generated_flag
======================= 3 failed, 89 deselected in 0.50s =======================
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `rg -n "follow.generated" agent_workflows` (expected: no output, exit 1; measured BEFORE the change: 3 hits) and the same pytest command as V-01 after E-02, showing parts (a) and (b) pass. ALSO paste the rewritten `refuse_unimplemented_run_flags` docstring, which must name NO specific flag and must not repeat the false claim that `--with-dependencies` is unbuilt (Finding 8).
  - Observed evidence: Verified zero matches for follow.generated in agent_workflows and passing host parser tests:
```
$ rg -n "follow.generated" agent_workflows
[exit 1, no matches]

$ python3 -m pytest -o addopts="" tests/test_runner_shared.py -k FollowGeneratedRemoved
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=2397753177
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 92 items / 89 deselected / 3 selected

tests/test_runner_shared.py ..F                                          [100%]

=================================== FAILURES ===================================
_ FollowGeneratedRemovedTests.test_spec_25kzda_contains_no_follow_generated_token _
...
=========================== short test summary info ============================
FAILED tests/test_runner_shared.py::FollowGeneratedRemovedTests::test_spec_25kzda_contains_no_follow_generated_token
================== 1 failed, 2 passed, 89 deselected in 0.74s ==================

Rewritten refuse_unimplemented_run_flags docstring:
def refuse_unimplemented_run_flags(args: Any) -> None:
    """REFUSE any flag whose behavior does not ship (`implemented=False`), before anything happens.

    Called from `initialize_run` before the run directory exists, so a refusal leaves nothing durable
    behind - the same "No work started" property the mixed-type refusal has, for the same reason.

    This mechanism is retained for any future registered-but-unbuilt flag so that an unbuilt flag
    fails loudly at initialization rather than parsing and silently doing nothing. No row in
    `RUN_POLICY_FLAGS` currently uses `implemented=False`, so the loop runs over zero rows.
    """
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the probe and its output for BOTH a stale `follow_generated: True` and a stale `False`, each showing the call returned `False` with no traceback. A single-polarity paste does not satisfy this item: `True` is the value that would matter.
  - Observed evidence: Ran resume probe for both stale True and False follow_generated keys; both returned False without error:
```
$ python3 - <<'EOF'
import argparse
from agent_workflows import runner_shared

for val in (True, False):
    state = {"options": {"follow_generated": val}}
    args = argparse.Namespace()
    res = runner_shared.apply_run_policy_flags_on_resume(state, args)
    print(f"probe follow_generated={val}: res={res}, args={args}")
EOF
probe follow_generated=True: res=False, args=Namespace()
probe follow_generated=False: res=False, args=Namespace()
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `rg -c "follow-generated" .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (expected: 0; measured BEFORE: 9) and `rg -n "generated next action" <same path>` (expected: the new report-only bullet), plus the V-01 pytest command now fully passing. ALSO paste the rewritten consent-table "Generated child" row, showing it states a new run is the only path rather than having been deleted.
  - Observed evidence: Verified 0 occurrences of follow-generated in spec 25kzda, verified report-only rules, and passing tests:
```
$ rg -c "follow-generated" .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
[exit 1, 0 matches]

$ rg -n "generated next action" .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
425:- Newly generated IPDs are ALWAYS reported as generated next actions and never join the frozen run (the frozen queue is what resume reads, and no producer exists; see plan `hzdq8y`).
599:- a generated child is recorded as a generated next action and excluded from the run.
1225:10. Newly generated IPDs are recorded in the result as generated next actions and never join the frozen run. A generated IPD must still resolve `Item-Dependencies` before review-readiness.
1399:| Generated child | Always requires a new run; reported as a generated next action | Always requires a new run; reported as a generated next action |
1526:- `spec09` is human-approved, so the runner authors exactly one `to-review` IPD with `From-Spec: spec09` and a resolved `Item-Dependencies` value. It checks trace coverage and release-gate carry-forward, commits only the spec/IPD/index paths, and tool-sets the spec to `implementing`. The new IPD is reported as a generated next action and is not executed in the same run.

$ python3 -m pytest -o addopts="" tests/test_runner_shared.py -k FollowGeneratedRemoved
======================= 3 passed, 89 deselected in 0.25s =======================

Rewritten consent-table "Generated child" row:
| Generated child | Always requires a new run; reported as a generated next action | Always requires a new run; reported as a generated next action |
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `rg -n "x8diyb|hzdq8y" .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md` (expected: `hzdq8y` in the rewritten 3.4, `x8diyb` ONLY in the untouched OQ-01 ruling; measured BEFORE: two `x8diyb` hits, one in each place) and `rg -n "follow-generated" CHANGELOG.md` (expected: one bullet). ALSO paste the 3.4 replacement sentence showing it carries the forward pointer that reconciles the now-stale mechanism name in OQ-01, and paste `git diff` of the OQ-01 block showing it is UNCHANGED.
  - Observed evidence: Verified z7nbn1 references and CHANGELOG bullet; confirmed OQ-01 block unchanged:
```
$ rg -n "x8diyb|hzdq8y" .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
139:`--follow-generated` flag mentioned in `OQ-01` below was removed by plan `hzdq8y` because no producer
230:  `--follow-generated` is implemented (owner backlog `x8diyb`), that flag becomes the opt-in mechanism

$ rg -n "follow-generated" CHANGELOG.md
61:- Removed the `--follow-generated` run flag. It was never implemented and always refused. Plans created during a run are reported as next actions, as before.

Rewritten 3.4 sentence:
The previously reserved `--follow-generated` flag mentioned in `OQ-01` below was removed by plan `hzdq8y` because no producer existed; a future plan building production actions may reintroduce an opt-in mechanism if the maintainer wants one. See `OQ-01`.

$ git diff -U5 .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
[Diff touches only Section 3.4; Section 6 / OQ-01 block is UNCHANGED]
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (expected: `N passed`, 0 failed).
  - Observed evidence: Full test suite ran and passed cleanly:
```
$ python3 -m pytest
1995 passed, 1 skipped, 3 warnings in 29.30s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `Status: approved`.

OPEN QUESTIONS: OQ-01 is `resolved` (REMOVE, on Findings 1 to 4) and is the plan's own deliverable. OQ-02 is `Blocking: no`, `Owner: maintainer`, and asks whether removal sits with the `z7nbn1` OQ-01 ruling; its default is to proceed, and the ALTERNATIVE is fully specified (keep the flag, re-point the row's `owner` to `spec z7nbn1`, drop E-01/E-02 and E-04/E-05's removal wording). An executor must NOT re-decide OQ-02 mid-run: if the maintainer wants the alternative, that is a different and much smaller plan.

THIS PLAN REMOVES A PUBLIC CLI SURFACE, WHICH IS THE ONE THING TO BE DELIBERATE ABOUT. `--follow-generated` appears in `--help` on both hosts today, so after E-02 an operator's existing command line FAILS with argparse exit 2 instead of the current `RunFlagRefusal`. That is the intended improvement (a flag that cannot work should not parse), and it is a BREAKING surface change even though the behavior it names never existed, which is why the CHANGELOG bullet is required rather than optional. Measured: it is the ONLY `implemented=False` row, so after removal `refuse_unimplemented_run_flags` iterates zero rows; keep the function, as E-02 says.

TEST-FIRST IS LOAD-BEARING HERE BECAUSE NOTHING ELSE GUARDS THIS SURFACE. The contract test that once pinned the unimplemented-flag set (`tests/test_run_flag_surface.py`) was DELETED in commit `19313eed`, and no test in the tree now asserts anything about it (Finding 7). So E-01 is the only thing standing between this change and a silent regression. Write it first, show it FAILING (V-01 demands the failing paste), and do not reorder.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS: `- Scope-Paths:` is `agent_workflows/runner_shared.py`, `tests/test_runner_shared.py`, spec `25kzda` at its REAL id6 path, spec `z7nbn1`, and `CHANGELOG.md`. It is a DECLARATION, not a stop order: an out-of-scope edit that is genuinely required must be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a `--scope-ack`. Do not halt over a scope question. DO halt for a genuinely unsafe condition: an unresolvable concurrent-edit conflict in `runner_shared.py` or in `25kzda` (both high-traffic, and a sibling plan amends the same spec).

SPEC EDITS DECLARED, AND ONE IS AN APPROVED SPEC: `25kzda` is `- Status: approved` and carries `- Blocks-Release: next`; `z7nbn1` is `to-review`. Both runners announce declared spec edits before the run and reconcile them at the end. Two limits on the `z7nbn1` edit: do NOT touch the OQ-01 Resolution block (a dated maintainer ruling), and DO include the forward pointer E-05 requires so the ruling's now-stale mechanism name is reconciled rather than left contradicting 3.4. Record the `25kzda` amendment with `aw specs note`, not by hand-editing its history.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*` above, including V-01's BEFORE-failing run and V-03's BOTH polarities. Never mark a `V-*` from the matching `E-*` checkmark or from memory, and never claim a test pass that was not run.

COMMIT DISCIPLINE: commit only the declared `- Scope-Paths:`, path-scoped, through `aw commit hzdq8y -- <paths>`; never `git add -A`, never `-a`, and never push. This is a shared checkout, so run `git diff --cached --name-only` before each commit and unstage anything that is not yours with `git restore --staged <path>`. CHANGELOG prose is user-facing: no em or en dashes.

LIFECYCLE TRANSITION: after every `V-*` passes and `aw ipd lint --phase pre-transition` conforms, the terminal transition is the RUNNER's in a managed lane and otherwise the executor's via `aw ipd finalize`. Do not hand-roll a `git mv` to `executed/`.

BACKLOG `ceauac` IS NOT CLOSED BY THIS PLAN. It is already `graduated` with `- Graduated-To: followgen`, and `aw ipd finalize` performs no backlog write, so closing it is a follow-up once this plan is in `executed/`. The HANDOFF route is in place (`- From-Backlog: ceauac`), and measured at review the item carries no `- Blocks-Release:`, so `aw backlog set done ceauac --message "resolved by hzdq8y: flag removed, no producer exists"` will not fail closed.
