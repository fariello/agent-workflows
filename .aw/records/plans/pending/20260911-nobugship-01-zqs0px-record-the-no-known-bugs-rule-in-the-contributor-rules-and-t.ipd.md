# IPD: Record the no-known-bugs rule in the contributor rules and the decisions log

- Date: 2026-09-11
- Kind: child
- Concern: The rule that every bug blocks the next release is recorded nowhere. `grep` across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md` and the backlog README returns nothing, so it survives only in conversation and is measurably forgotten: 28 of 60 live bug items carry no gate.
  AND THE UNRECORDED RULE HAS NOW BEEN CLARIFIED TWICE IN ONE DAY WHILE STILL UNWRITTEN, which is the sharpest evidence that conversation is not a durable medium for it. On 2026-09-12 the maintainer ruled that inefficiency IMPACTING THE USER EXPERIENCE is a defect while inefficiency users cannot notice is not, so `bug` reaches a correct-but-slow code path when a human waits on it. That ruling arrived because an agent had filed such a defect as `chore` (backlog `59t9x5`, `aw find` opening every record twice, ~128ms of a ~530ms command) on the reasonable-looking basis that nothing returned a wrong answer; the agent then over-corrected and wrote the rule as covering ALL knowingly redundant work, which the maintainer narrowed again to the perceptibility test. Both the misfiling and the over-correction happened inside one session, from the same cause: nothing in the repository states the test, so each agent supplies its own.
- Scope: State the rule where it is discoverable and where the enforcing code can cite it: the existing release-gates section of the contributor rules, and a numbered entry in the decisions log. State BOTH maintainer rulings the policy now carries (every live bug gates the next release, 2026-09-11; and inefficiency counts as a defect when it is USER-PERCEPTIBLE and not when it is invisible, 2026-09-12), plus its two honest limits. Does NOT change any code, does NOT gate any other work kind, and does NOT backfill any item.
- Scope-Paths: AGENTS.md, DECISIONS.md, .aw/records/backlog/README.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: nobugship
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zqs0px
- Blocks-Release: next

## Workflow history

- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (BLOCKER) through PR-009 all FIXED, no deferrals, no open questions, readiness `go-pending-approval`. Record: `.aw/records/reviews/20260911-nobugship-01-zqs0px-record-the-no-known-bugs-rule-in-the-contributor-rules-and-t.review.md`. `aw ipd lint --phase author` CONFORMING (clean, 0 findings) BEFORE semantic review. Suite measured bare at HEAD `839c1ff8`: `5971 passed, 3 skipped, 2 xfailed in 68.73s`. DISCLOSURE: the same agent/model family authored this Set, so treat this as a near-self-review; its value rests on what was EXECUTED rather than on the reading.
  THE PLAN'S DEFINING HAZARD WAS FALSE, AND IT WAS THE ONE INSTRUCTION MOST LIKELY TO BE OBEYED. Four independent proofs, each run rather than reasoned. (1) `AGENTS.md`'s `## Release gates (Blocks-Release)` sits at line 125, and the managed block CLOSES at line 108 (`<!-- /aw:block -->`), so the section is OUTSIDE every managed region. (2) The commit that created it says so in its own message (`9cf9178`, 2026-08-18): "Placed in the hand-maintained region (outside the managed aw:block) so a regen preserves it". (3) `grep` for the section heading or its opening sentence in `agent_workflows/engine.py` returns ZERO: no generator carries this prose. (4) DRIVEN, not inferred: calling `engine.merge_aw_block` over the live `AGENTS.md` returns action `refreshed` with the release-gates section INTACT and a three-line diff that removes only blank lines. So editing `AGENTS.md` directly is CORRECT here, and the plan's repeated instruction to edit `engine.py` instead would have put a repo-local policy into every adopter's installed contract while `tests/test_shared_checkout_contract.py:132` failed on the drift. Corrected in the metadata, E-01, E-02, F-4, the conventions list, and the closing note; `engine.py` removed from `Scope-Paths`.
  THE OTHER GAP WORTH NAMING is that the plan wrote a Findings table with no `- Blocking:` question and no route for the one judgement it needs. Its own text says "a numeric cutoff" is the maintainer's to set and then leaves nothing to carry that; OQ-02 now records the resolution from the maintainer's own 2026-09-12 framing (perceptibility is the test, the filer records the number) so the executor does not invent a threshold. Added E-05 to prove the rendered file matches its generator by RUNNING the shipped parity assertion rather than by inspection, since the plan's original E-04 asked for a regeneration diff that this correction makes vacuous.
- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from the maintainer's question of 2026-09-11, "How do we ensure that approach persists?" This child is the answer's first third: an unwritten rule cannot persist. MEASURED at HEAD `2ff2b1b1`: the rule appears in none of the four candidate documents, while `AGENTS.md:125-146` ALREADY owns a "Release gates (Blocks-Release)" section that describes the mechanism without stating this policy, so the addition extends an existing section rather than inventing a home for it. `DECISIONS.md`'s highest entry is D153. NOTE THE GENERATION HAZARD: the `AGENTS.md` release-gates text is emitted from `engine.py`, so a hand-edit to `AGENTS.md` alone would be reverted by the next install; the generator is declared in `Scope-Paths` for that reason. **RETRACTED AT REVIEW 2026-09-12: THAT GENERATION CLAIM IS FALSE.** The release-gates section is hand-maintained, deliberately placed OUTSIDE the managed block, and survives a regeneration untouched (four proofs in the review record above). It is left visible here rather than deleted so a later reader can see which claim was corrected and why, but do NOT act on it: edit `AGENTS.md` directly.

## Goal

Make the rule discoverable by a reader and citable by the checker, so the other two children have something to point at rather than each restating policy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish where the rule belongs

- [ ] E-01 RE-CONFIRM THE OWNING DOCUMENT AND THE MANAGED-BLOCK BOUNDARY, then write in `AGENTS.md` directly. The answer is settled and must be re-proved rather than trusted: the `## Release gates (Blocks-Release)` section is HAND-MAINTAINED and sits OUTSIDE the managed block. Re-prove it with these three commands and paste them, because acting on the wrong answer is the single most damaging mistake available in this plan:
  (a) `grep -n "aw:block\|^## Release gates" AGENTS.md` must show the section BELOW the `<!-- /aw:block -->` line (measured at review: block closes at 108, section opens at 125).
  (b) `grep -c "Release gates\|first-class record under" agent_workflows/engine.py` must return `0`, proving no generator carries this prose.
  (c) drive the installer's own merge and confirm the section SURVIVES: `python3 -c "from agent_workflows import engine; cur=open('AGENTS.md',encoding='utf-8').read(); new,act=engine.merge_aw_block(cur, engine.agents_managed_sections(target_layout='aw')); print(act, '## Release gates (Blocks-Release)' in new)"` printed `refreshed True` at review.
  IF ANY OF THE THREE DISAGREES, STOP AND REPORT rather than guessing: that would mean the file was restructured since review and the edit target genuinely moved. This is the unsafe-condition case the scope fence permits stopping for.
  WHY THIS MATTERS MORE THAN IT LOOKS: the `engine.py` block is INSTALLED INTO EVERY ADOPTER REPO. Putting this repository's own release policy there would ship a repo-local rule to every downstream user, and `tests/test_shared_checkout_contract.py:132` would then fail until `AGENTS.md` was regenerated to match. The correct edit is repo-local prose in `AGENTS.md`.
  ALSO VERIFY NO SPEC ALREADY OWNS RELEASE-GATE POLICY. Review found spec `20260818-1525-03-release-record-and-blocker-gate` (`Status: implemented`), which owns the MECHANISM (the record shape, the field grammar, the setter, the dangling check) and whose R6 explicitly delegates the DOCUMENTATION of the model to `AGENTS.md`. It says nothing about WHICH items must carry the field, so it does not own this policy and the contributor rules are the right home. Re-run the search, cite what you find, and if a spec HAS since taken the policy, point at it instead of duplicating.
  - Depends on: none
  - Expected outcome: all three boundary commands pasted and agreeing that the section is hand-maintained, plus the spec-ownership search with its verdict; the edit target confirmed as `AGENTS.md` itself.
  - Execution state: pending

- [ ] E-02 WRITE THE RULE INTO THE EXISTING `## Release gates (Blocks-Release)` SECTION OF `AGENTS.md`, and keep it to the smallest wording that carries the policy and its two limits. It must say: a backlog item, spec or plan whose `- Work-Kind:` is `bug` MUST carry `- Blocks-Release:` while it is live (`open`, `blocked` or `graduated`), because known bugs do not ship; and the gate travels to whatever plan or spec the item graduates into, which is an obligation the existing graduation paragraph already states for a gate that exists and must now apply to one that is implied.
  DO NOT EDIT `agent_workflows/engine.py`, AND DO NOT REGENERATE `AGENTS.md`. E-01 proves the target section is hand-maintained and outside the managed block, so a direct edit is correct and survives every install. The generator is deliberately absent from `- Scope-Paths:`; adding the rule there would install this repository's own policy into every adopter's contract, which is exactly the wrong blast radius for a repo-local decision.
  PLACE IT WHERE IT WILL BE READ, not merely where it fits: append it as a short paragraph inside the existing section, near the `Blocks-Release` versus `Blocked-By` contrast, and do NOT disturb that contrast (the orchestrator's spec-sync section names preserving it as a constraint). Cross-reference `- Work-Kind:` as the backlog README already defines it rather than restating the enum.
  THE GRADUATION HALF IS A POINTER, NOT A SECOND COPY. The managed block already says a graduating plan "inherits the item's `- Blocks-Release:` if it has one" (`engine.py:1187`, rendered at `AGENTS.md:38`). Say that this policy makes the gate exist so that clause has something to inherit, and reference the clause rather than restating it (P8: one canonical place per rule).
  THE RULE COVERS INEFFICIENCY A USER CAN NOTICE, AND THE TEST IS USER-PERCEPTIBLE IMPACT, NOT REDUNDANCY. Maintainer ruling 2026-09-12: inefficiency that impacts the user experience is a defect; inefficiency that does not noticeably affect users is not. So `bug` is not limited to a wrong answer, and it is equally not extended to every wasteful code path. The discriminator is whether a user can perceive the cost, which means the filer owes a MEASUREMENT against the surface a user actually touches, not a count of redundant operations.
  WRITE THE DISCRIMINATOR THIS WAY, because the tempting wording is wrong. Provable redundancy is EVIDENCE of inefficiency but is not itself the test: doubling a 2ms internal call is redundant and unnoticeable, so it is a `chore`. Conversely a slow path with no redundancy at all can be a bug if a user waits on it. Measure the END-TO-END command a user runs, warm and cold, rather than an internal function in isolation; an isolated call can read many times its real cost when nothing else has warmed the page cache.
  THE WORKED EXAMPLE, and it qualifies on the measurement rather than on the redundancy. Backlog `59t9x5`: `aw find` opens every record TWICE (1240 opens end to end against the 620 the resolver needs). What makes it a `bug` is that the redundant read costs ~128ms of a ~530ms command an operator waits on, so removing it would leave ~402ms; that is a difference a human notices. It was filed `chore` on the reasoning that output was correct, and the maintainer reclassified it to `bug`. Had the same double read cost 3ms, `chore` would have been right.
  STATE THE JUDGEMENT HONESTLY RATHER THAN INVENTING A THRESHOLD. Do not write a numeric cutoff into the rule unless the maintainer sets one; "noticeable" is a judgement the filer makes and records with the number that supports it, so a reviewer can disagree with the number rather than with a vibe. An unmeasured hunch that something feels slow is not a bug and should not be filed as one.
  STATE THE TWO LIMITS HONESTLY, because a rule whose limits are hidden gets trusted further than it should. FIRST, the gate keys on an AUTHOR'S CLASSIFICATION, so a genuine defect filed as `chore` or `followup` escapes it; that is the parent's OQ-02 and the wording must name it rather than imply completeness. NOTE the inefficiency ruling makes this limit BITE HARDER rather than softer, and in BOTH directions: a user-visible performance defect is easy to file as `chore` (which `59t9x5` measurably was), while an invisible one is easy to over-file as `bug` now that inefficiency is nameable at all. Use `59t9x5` as the worked example of the first and say plainly that the second is also a misfiling. SECOND, the rule governs LIVE items only: a bug already `done` is not retroactively gated, because rewriting its gate now would assert a history that did not happen.
  DO NOT WRITE THE RULE AS AN ABSOLUTE. The maintainer's standing instruction is recorded verbatim in plan `u06zo2` OQ-04 (2026-09-10, via `/askme`): "I would like you to stop speaking in absolutes. We enforce these things until such a time as we receive evidence that the rules need relaxing or changing." Its operative constraint there was to state the requirement WITHOUT the words "never", "no override possible", "permanent", or "in perpetuity", and without a clause forbidding a future maintainer from revisiting it. Apply the same test here. NOTE the scope is the RULE TEXT you author, not the surrounding file: `AGENTS.md` already contains 16 legitimate uses of "never" in other rules, so a repository-wide grep for the word is the WRONG check and would fail on prose you did not write. Grep the paragraph you added.
  - Depends on: E-01
  - Expected outcome: the rule stated inside the existing `AGENTS.md` release-gates section with both limits and the perceptibility test, no `engine.py` edit, and the `Blocks-Release` versus `Blocked-By` contrast left intact.
  - Execution state: pending

### Task group 2: record it as a decision and prove the file agrees with its generator

- [ ] E-03 ADD A NUMBERED `DECISIONS.md` ENTRY, since this shapes the repository beyond one artifact and constrains every future bug filing. Record WHAT was decided, WHO decided it (the maintainer, 2026-09-11), the reasoning in their own framing ("We don't ship known bugs"), and the MEASUREMENT that motivated writing it down: 28 of 60 live bug items were ungated, two of them filed by an agent hours after being told the rule in the same session.
  CHECK THE HIGHEST D-NUMBER AT WRITE TIME, do not reuse this plan's. Measured D153 at authoring and STILL D153 at review (HEAD `839c1ff8`), but other agents append concurrently, so re-derive it immediately before writing and paste the command.
  MATCH THE SECTION SHAPE THE FILE ALREADY USES rather than inventing one: the existing entries carry a `### D<n>. <title>` heading followed by bolded `- **Context:**`, `- **Decision:**`, `- **Rejected:**` (where something was), `- **Status:**` and `- **Applied:**` bullets. Read D153 as the immediate model. Also RECORD WHAT WAS REJECTED, because this decision has a real alternative: leaving `bug` to mean only a wrong ANSWER, which the maintainer explicitly declined on 2026-09-12 when they reclassified `59t9x5`.
  RECORD THE SECOND RULING, NOT ONLY THE FIRST. The entry covers two maintainer acts: 2026-09-11 ("We don't ship known bugs"), and 2026-09-12 (inefficiency is a defect when a user can notice it, not when they cannot). Both are load-bearing, and the second is what decides whether a performance item is a release blocker at all.
  - Depends on: E-02
  - Expected outcome: a `DECISIONS.md` entry at the next free number, in the file's existing bullet shape, carrying both rulings, the rejected reading, the author and date of each, and the motivating measurement; with the freshly derived highest-D command pasted.
  - Execution state: pending

- [ ] E-04 PROVE THE MANAGED BLOCK STILL MATCHES ITS GENERATOR, which is what catches an edit that strayed into managed territory. The assertion already ships: `tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated` (`:132`) compares this repo's `<!-- aw:block -->` region against `engine.agents_managed_block`. RUN IT rather than writing a new one, and run its sibling `test_contract_is_not_duplicated_inside_and_outside_the_block` (`:139`) too, which is the P8 guard against restating managed prose below the block.
  BOTH MUST PASS UNCHANGED, and that is the POINT rather than a weak result: your edit is outside the managed block, so parity is expected to hold both before and after. This is the inverse of the original instruction, which asked for a nonempty regeneration diff; that expectation followed from the false generation premise E-01 corrects, and a nonempty managed-block diff here would now mean the edit landed in the WRONG place.
  - Depends on: E-03
  - Expected outcome: both named assertions run and passing after the edit, with the actual pytest output pasted, proving the managed block was not disturbed.
  - Execution state: pending

- [ ] E-05 PROVE THE RULE SURVIVES AN INSTALL, which is the durability claim this plan actually makes and which no other item tests. Drive the installer's own merge over the edited `AGENTS.md` and show your new paragraph is still present afterwards, using the same one-liner as E-01(c) but asserting on the RULE TEXT rather than on the section heading. A rule that a regeneration would erase is not recorded, which is the exact failure this Set exists to end.
  - Depends on: E-04
  - Expected outcome: the merge driven post-edit, printing the action and `True` for the new rule paragraph's presence.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `AGENTS.md` is PART generated and PART hand-maintained, and the boundary is the `<!-- /aw:block -->` marker at line 108. The managed sections above it come from `engine.py` and are installed into every adopter repo; everything below is repo-local and survives regeneration. VERIFIED at review by driving `engine.merge_aw_block` over the live file: action `refreshed`, the release-gates section intact, three lines of diff all blank-line removals.
- THE `## Release gates (Blocks-Release)` SECTION IS HAND-MAINTAINED, deliberately. Its originating commit (`9cf9178`, 2026-08-18) states the placement was chosen "so a regen preserves it", and no generator carries the prose. Edit `AGENTS.md` directly.
- A decision that shapes the repository beyond one artifact belongs in `DECISIONS.md`, which the `askme` workflow states explicitly. Entries use `### D<n>. <title>` plus bolded Context / Decision / Rejected / Status / Applied bullets; D153 is the current model and the current highest number.
- Per the maintainer's instruction of 2026-09-10 (recorded verbatim in plan `u06zo2` OQ-04), a rule should be written as what is currently enforced rather than as an absolute, because a declared inflexibility later has to be policed. The named words to avoid are "never", "no override possible", "permanent" and "in perpetuity", in the rule text you author.
- Spec `20260818-1525-03-release-record-and-blocker-gate` (`implemented`) owns the release-gate MECHANISM and its R6 delegates DOCUMENTING the model to `AGENTS.md`. It does not say which items must carry the field, so it does not own this policy.
- P8 (single source of truth) governs the graduation half: the managed block already states the inheritance obligation at `engine.py:1187`, so reference it rather than restating it below the block. `tests/test_shared_checkout_contract.py:139` mechanically guards that boundary for the graduation contract's own body.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | The rule is unrecorded. `grep` for it across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md` and `.aw/records/backlog/README.md` returns nothing at HEAD `2ff2b1b1`. |
| F-2 | HIGH | Loaded context is not a sufficient mechanism, and this session is the proof: an agent filed two ungated bug items (`kyb0v5`, `mqmlug`) hours after the maintainer stated the rule to it directly. Writing it down is necessary but, on this evidence, not sufficient either, which is why children 02 and 03 exist. |
| F-3 | MEDIUM | A home already exists: `AGENTS.md:125-183` owns "Release gates (Blocks-Release)" and describes the field and the `Blocks-Release` versus `Blocked-By` distinction without stating this policy. The addition extends that section. |
| F-4 | HIGH | **CORRECTED AT REVIEW 2026-09-12.** The authored finding claimed the text is GENERATED from `engine.py` and would be reverted on install. IT IS NOT. The section sits BELOW `<!-- /aw:block -->` (block closes 108, section opens 125), its originating commit `9cf9178` says it was placed in the hand-maintained region "so a regen preserves it", `grep` finds the prose nowhere in `engine.py`, and driving `engine.merge_aw_block` over the live file returns `refreshed` with the section intact. Editing `AGENTS.md` directly is correct; editing `engine.py` would ship a repo-local policy to every adopter and break `tests/test_shared_checkout_contract.py:132`. |
| F-5 | LOW | `DECISIONS.md`'s highest entry is D153 at authoring and still D153 at review (HEAD `839c1ff8`), and other agents append concurrently, so the number must be re-derived at write time. |
| F-6 | MEDIUM | Spec `20260818-1525-03` (`implemented`) owns the release-gate MECHANISM and its R6 delegates documenting the model to `AGENTS.md`; it is silent on which items must carry the field. So no spec owns this policy and the contributor rules are the right home, which resolves OQ-01 from evidence rather than by choice. |
| F-7 | MEDIUM | The rule's discriminator is USER-PERCEPTIBLE cost, and the corpus already carries the worked example in the shape the rule needs: `59t9x5` records "best 530.2ms, median 571.5ms over 7 runs", `~128ms` attributable, and states plainly that "had the same double read cost 3ms, `chore` would have been correct". The plan may cite that item rather than paraphrasing it. |
| F-8 | LOW | The original E-04 was self-defeating: it demanded a NONEMPTY regeneration diff as proof the edit landed, which follows only from F-4's false premise. Under the corrected premise a nonempty managed-block diff means the edit landed in the wrong place. Inverted, and E-05 added to test the durability claim the plan actually makes. |

## Proposed changes (ordered, validatable)

1. Re-prove the managed-versus-local boundary and the spec-ownership verdict (E-01).
2. State the rule and its two limits in the hand-maintained `AGENTS.md` section (E-02).
3. Record it as a numbered decision carrying both rulings and the rejected reading (E-03).
4. Prove the managed block was not disturbed, using the shipped parity assertions (E-04).
5. Prove the rule survives an install by driving the merge (E-05).

## Deferred / out of scope (with reason)

- ANY CODE CHANGE, INCLUDING THE GENERATOR. Children 02 and 03 own the default and the enforcement; this child only makes the rule discoverable and citable. `agent_workflows/engine.py` was REMOVED from `- Scope-Paths:` at review because the target prose is not generated (F-4), and installing a repo-local policy into every adopter's contract is a blast radius nothing here justifies.
- BACKFILLING THE 28 VIOLATIONS. Child 03 owns that, deliberately after the default is in place so the backfill cannot immediately re-diverge.
- EXTENDING THE RULE TO `security`. The parent's OQ-01; not assumed here.

## Scope check

- Over-scope: none, and one path was REMOVED at review. Three paths remain: the contributor rules that own the section, the decisions log, and the backlog README a filer is most likely to read. `agent_workflows/engine.py` was dropped because the target prose is not generated (F-4).
- Under-scope: this child does not prevent a single future ungated bug on its own. That is honest rather than a gap: F-2 measures that documentation alone failed, which is why the Set has three children.
- Note on the backlog README: it is declared because a filer reads it when choosing `- Work-Kind:`, and a one-line pointer to the `AGENTS.md` rule belongs there. Keep it a POINTER (P8), not a second copy of the policy. If on inspection no pointer is warranted, leave the file untouched and acknowledge the unmodified declared path at finalize with `--scope-ack` rather than inventing an edit to justify the declaration.

## Required tests / validation

No new test file: this child changes documentation. It must run the SHIPPED parity assertions named in E-04 (`tests/test_shared_checkout_contract.py::NoDriftTests`), the install-survival check in E-05, and the bare suite, with the baseline established BEFORE the first edit.

Suite measured bare at review, HEAD `839c1ff8`: `5971 passed, 3 skipped, 2 xfailed in 68.73s`. That figure is REFERENCE ONLY; re-measure before the first edit and judge on the failure-SET delta, not on the count. Run it BARE: the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0` or a second `-q` makes the run slower and suppresses the summary line the contract requires you to paste.

## Spec / documentation sync

This child IS the documentation change, and it amends no spec. SETTLED AT REVIEW so the executor need not re-litigate it: spec `20260818-1525-03-release-record-and-blocker-gate` (`Status: implemented`) owns the release-gate MECHANISM (record shape, field grammar, setter, dangling validation) and its R6 explicitly delegates DOCUMENTING the model to `AGENTS.md`. It is silent on which items must carry the field, so this policy has no spec owner and the contributor rules are the correct home. E-01 re-runs the search and reports; if a spec has since taken the policy, point at it rather than duplicating.

No `.spec.md` file is in `- Scope-Paths:`, which is deliberate: nothing here changes a spec-governed contract.

## Open questions

### OQ-01: Should the rule live in a spec rather than in the contributor rules?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM EVIDENCE, not asked. THE CONTRIBUTOR RULES. Spec `20260818-1525-03-release-record-and-blocker-gate` (`Status: implemented`) is the only spec carrying release-gate normative text, and it owns the MECHANISM rather than this policy: its R1 through R5 define the record shape, the field grammar, the setter and the dangling-reference validation, while its R6 says to "document the concept ... in AGENTS.md so agents capture blockers consistently and in ONE place". So the spec itself delegates this text to the contributor rules, and duplicating it into a spec would violate P8 rather than honor it. E-01 re-runs the search and reports, so a spec that has since taken the policy would still be caught.

### OQ-02: Is there a numeric threshold at which slowness becomes a bug?

- Blocking: no
- Status: resolved
- Owner: maintainer (already answered in substance)
- Resolution or deferral rationale: NO THRESHOLD, AND THE PLAN MUST NOT INVENT ONE. RAISED IN REVIEW because the plan instructs the executor to "state the judgement honestly rather than inventing a threshold" and then provides no question to carry that instruction, which is how an executor ends up choosing a number on its own authority. Resolved from the maintainer's own framing rather than asked, because they already set the test on 2026-09-12: inefficiency that impacts the USER EXPERIENCE is a defect, inefficiency users cannot notice is not. That is a perceptibility test, not a millisecond cutoff. What the filer owes is a MEASUREMENT of the end-to-end command a user runs, recorded on the item so a reviewer can dispute the number rather than the vibe. Backlog `59t9x5` is the model and already reads this way: "best 530.2ms, median 571.5ms over 7 runs", `~128ms` attributable, and the explicit counterfactual "had the same double read cost 3ms, `chore` would have been correct". Non-blocking because the rule's CONTENT is fixed either way and only a hypothetical future cutoff would change; if the maintainer later sets a number, it amends this text rather than blocking it. V-02 enforces the absence of a numeric cutoff.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste ALL THREE boundary commands from E-01 with their output: the `grep -n "aw:block\|^## Release gates" AGENTS.md` showing the section BELOW the closing marker; the `grep -c` over `engine.py` returning `0`; and the driven `merge_aw_block` printing its action plus `True`. State the verdict in one line: the section is hand-maintained and the edit target is `AGENTS.md`. If any command disagrees with review's finding, paste it and report the STOP rather than proceeding. Then paste the search over `.aw/records/specs/` for release-gate normative text with its verdict against OQ-01's recorded resolution.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `AGENTS.md` diff, showing the rule, BOTH stated limits (author-classification leak, live-items-only), AND the inefficiency ruling of 2026-09-12 with its USER-PERCEPTIBILITY test and `59t9x5` as the worked example. Quote the sentence establishing that redundancy is EVIDENCE rather than the test itself, and the sentence saying an unmeasured hunch is not a bug. Confirm the wording does NOT contain a numeric threshold, per OQ-02; if a reader could apply the rule without measuring anything, the wording has failed. Paste a grep over THE ADDED PARAGRAPH ONLY proving it contains none of `never`, `no exception`, `permanent`, `in perpetuity` (a whole-file grep is the wrong check: `AGENTS.md` legitimately uses `never` 16 times in prose you did not write). Paste `git diff --stat -- AGENTS.md`. Finally paste `git status --porcelain -- agent_workflows/engine.py` proving it is UNMODIFIED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new `DECISIONS.md` entry verbatim, and paste the command showing the highest D-number IMMEDIATELY BEFORE the write, proving no collision with a concurrently-appended entry. Confirm by inspection that the entry carries BOTH rulings (2026-09-11 and 2026-09-12), the rejected reading, and the file's existing bullet shape.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_shared_checkout_contract.py -o addopts=""` with per-test names, showing `test_repo_agents_block_equals_generated` and `test_contract_is_not_duplicated_inside_and_outside_the_block` PASSING after the edit. Both passing unchanged is the CORRECT result and must be reported as such, not apologized for. Then paste the bare `python3 -m pytest` summary against the pre-edit baseline and name any failure as pre-existing or new by comparing failure SETS, not counts.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the post-edit `merge_aw_block` run asserting on the NEW RULE TEXT, showing the action and `True`. State plainly what this proves: the rule is durable against an install, which is the claim the whole Set rests on.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: go-pending-approval`. It has no open questions and no unfixed finding; a human must set it `approved` before it is executed.

It carries `- Blocks-Release: next` in line with the rule it records.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL runner output; do not claim a pass you did not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. The declared paths are a DECLARATION so the run can be reconciled afterwards: an out-of-scope edit is made and then JUSTIFIED at finalize with `--scope-reason`, and a declared-but-unmodified path is acknowledged with `--scope-ack`, rather than either being a reason to stop.

THE HAZARD THAT DEFINED THIS PLAN AS AUTHORED WAS FALSE, AND CORRECTING IT INVERTS THE INSTRUCTION. The authored text said `AGENTS.md` is GENERATED and told the executor to edit `engine.py` and regenerate. `## Release gates (Blocks-Release)` is HAND-MAINTAINED and sits below the `<!-- /aw:block -->` marker; its originating commit `9cf9178` chose that placement "so a regen preserves it", `engine.py` carries none of the prose, and driving `engine.merge_aw_block` over the live file leaves the section intact. EDIT `AGENTS.md` DIRECTLY. Following the original instruction would have installed this repository's own release policy into every adopter repo and broken the parity assertion at `tests/test_shared_checkout_contract.py:132`, so this is the correction most worth carrying into execution.

THE REAL HAZARD IS THE OPPOSITE ONE: an edit that strays ABOVE the closing marker lands in managed text. E-04 exists to catch exactly that, and E-05 proves the durability claim the Set rests on.
