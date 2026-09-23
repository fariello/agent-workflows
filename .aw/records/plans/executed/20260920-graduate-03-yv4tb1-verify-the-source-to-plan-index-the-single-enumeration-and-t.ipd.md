# IPD: Verify the source-to-plan index, the single enumeration, and the backlog ledger after both children land

- Date: 2026-09-20
- Kind: child
- Concern: Orchestrator `y9s4vm` carries three E-items that NO CHILD COVERS, and the sharpest of them (E-03, the backlog `6h7y2y` ledger) is one the runner CANNOT discharge even in principle. `process_backlog_close` fires only when an AGENT-EXECUTED IPD finalizes, and an orchestrator is not agent-executed: `dispatch_orchestrator_item` and `ipd_lifecycle.retire_orchestrator` contain no backlog-close call at all (verified at HEAD: `'backlog' in source` is False for both). Worse, `evaluate_backlog_close` requires EVERY IPD carrier terminal and the parent ITSELF carries `- From-Backlog: 6h7y2y`, so the close is refused by construction while the parent sits unretired. Because `retire_orchestrator` also skips the pre-transition E/V checkpoint, a runner would mark the parent `executed` with all three items unperformed.
- Scope: Perform the whole-Set verification the parent cannot. IN: confirm both children reached `executed` in the required order, prove exactly ONE spec enumeration survives and that the review sweep and the plan action agree, verify the cross-Set single-traversal constraint against `setidhard`'s `bwgyum`, and verify backlog `6h7y2y` reached its correct CONDITIONAL terminal state with the actor named. OUT: performing either child's implementation, closing the backlog item on the parent's behalf without checking which branch applies, and inventing a `Blocks-Release` gate the item does not carry.
- Scope-Paths: .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md, .aw/records/backlog/done/
- Item-Dependencies: executed:jxxec8, executed:iuxtjy
- Status: executed
- Work-Kind: feature
- Priority: medium
- Readiness: go-pending-approval
- Set: graduate
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yv4tb1
- From-Backlog: 6h7y2y

## Workflow history
- 2026-09-23 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: yv4tb1 verified (set graduate, attempt 1). [Scope reconciliation - in-scope-unmodified .aw/records/backlog/done/: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-23 approved (opencode its_direct/pt3-claude-opus-5-1m-us): EXECUTION EVIDENCE RECORDED; the terminal transition is the runner's to perform (`aw ipd finalize`), so this entry deliberately does NOT claim `executed`. Executed in lane `aw/lane/yv4tb1` at HEAD `0823163b` under driver run `run-20260923T023317Z-3622118` (position 13). All four E-items performed, all four V-items pass with pasted evidence; `aw ipd lint --phase pre-transition` conforming. THE SET IS COMPLETE AND THE LEDGER IS CORRECT, BUT ONE OF THE PARENT'S COMPLETION CRITERIA IS NOT MET AND I REPORT IT AS UNMET RATHER THAN DECLARING IT SATISFIED. E-01: both children `executed`, and Order 01's finalize (`fe664b70`, 2026-09-21T23:53:32) is a strict git ANCESTOR of Order 02's (`87469293`, 2026-09-23T06:09:54), so the guard-before-verb sequencing held in fact; all eleven child `V-*` items are `pass` with substantial evidence (2975-6813 chars each), spot-checked as real observations (mutation testing, CLI transcripts) rather than assertions. E-02: SINGLE-SURFACE verdict, not a fabricated comparison. `discover_specs` is defined ONCE and all THREE callers reach the same object (`id=0x740c2c2c5220`, one code object, all bare `Name` AST nodes); the caller count rose from the 1 measured at review to 3 because `iuxtjy` added `match_spec_selector` and `resolve_selected_artifact_paths` as CONSUMERS of the shared authority, which is the opposite of the damage CID-2 guards. No second surface exists to compare: `ACTION_IMPLEMENTED` is still `frozenset({'review'})`, so `--action plan` fails closed, exactly as child 02's V-02 records deliberately. Re-measured 17 specs of 36 on disk (NOT the parent's stale 9-of-28); named AST guard `test_enumeration_reuses_the_shared_authority` passes (`1 passed in 5.11s`). E-03 IS THE SUBSTANTIVE FINDING AND THIS PLAN'S OWN PREDICTION WAS STALE: F-07 and E-03 both said `bwgyum` had not landed and that "half-satisfied" would be the honest verdict. `bwgyum` IS `executed` (`55a99b5c`, 2026-09-23T01:30:52), so BOTH Sets are in and the real verdict is that **CID-7 IS NOT SATISFIED**. `bwgyum` landed SECOND, so the "second consumes the first" obligation fell on it, and introspection proves it did not: `check_graduated_to` contains neither `build_graduation_reverse_index` nor `graduation_cluster`, and builds its own `known_setids` with a SECOND `_iter_plan_ipds` pass plus its own `rglob`. Not a race: child 01's index was already present at `bwgyum`'s own finalize commit (`git show 55a99b5c:...` contains its `def`), and `bwgyum`'s E-04 re-check read the wrong signal, asking whether an `aw graduate` VERB existed (and recording `jxxec8` as still pending, which was stale by ~25h) rather than whether the reverse INDEX existed. LATENT, NOT LIVE: zero records declare `- Graduated-To:` so the forward check returns 0 findings and the two share no live input; on a purpose-built fixture the two directions AGREE (`forward=['fixset']`/`reverse=['fixset']`) and the dangler is correctly flagged. Filed as backlog `knvpiv` (`chore`, not `bug`, since no operator can observe a wrong answer today) WITH the measurement that rules out the naive fix: the reverse index sees 124 setids against the forward check's 328 over 712 plan files, so substituting it would make 204 legitimate setids read as dangling on an error-severity rule. E-04: NO TRANSITION OWED. `6h7y2y` remains `graduated`, which is CORRECT because child 02's V-03 deferred the backlog half ("DEFER the backlog half; deliver the spec RESOLUTION half only") and the item's own graduated history line pre-authorized precisely this branch ("If iuxtjy OQ-01 defers the backlog half, this item stays graduated rather than going done"); follow-on `oc3mhb` exists and is `open`, so OQ-01's contingency never arose. I ran the mandated POSITIONAL `aw backlog set done 6h7y2y --dry-run` to document the safe path and re-test `19lmbe`: it previewed `graduated -> done (dry-run)` and wrote NOTHING (`git status` byte-identical either side), confirming `19lmbe` is specific to the `--status` spelling; I did NOT then perform it, and specifically did not perform it to satisfy the scope fence. No plan in this Set carries `- Blocks-Release:` (verified 0 for all four), so no gate was invented. VALIDATION: `aw backlog check` reports "all backlog items conform" (the 16 `id-duplicate` violations this plan recorded at review have since been resolved by another party, so the delta is zero against a clean tree); `aw check all` reports 0 findings for `from-backlog-dangling`, `from-spec-dangling` and `from-backlog-gate-mismatch`, and 0 mentioning `knvpiv`. Bare `python3 -m pytest`: `3 failed, 9069 passed, 3 skipped, 2 xfailed in 416.24s`. The failing NODE-ID delta is EMPTY, PROVEN rather than asserted: my only change is one untracked `.backlog.md` (`git diff --stat` empty), and with it moved aside so `git status --short | wc -l` is `0`, the same three node ids still fail (`3 failed in 4.68s`). Two are already filed by other parties (`2tiyl8`; and `turn_bounds` many times over) so I filed no duplicates. Nothing pushed; no tracked file modified by this plan.
- 2026-09-23 approved (aw set): Backfilled Priority and Work-Kind by inheritance from source backlog item 6h7y2y (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
- 2026-09-22 approved (aw set): status set to approved
- 2026-09-21 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review at HEAD cd2e6adb in an isolated lane; APPROVE WITH REVISIONS APPLIED, readiness go-pending-approval; PR-101..PR-109 all FIXED in place, none deferred, none OPEN, none REPLAN. aw ipd lint CONFORMING at author and review-finalize. THE PLAN'S CENTRAL INSIGHT IS CORRECT AND STRONGER THAN IT CLAIMED: evaluate_backlog_close('6h7y2y') returns close=False naming FOUR unexecuted IPD carriers, and the fourth is THIS PLAN, so the predicate cannot fire while the plan that verifies the item is itself pending; and neither dispatch_orchestrator_item nor retire_orchestrator mentions backlog at all (introspection), so no runner path closes the item on retirement. THE ONE SERIOUS FINDING IS THAT THE PRESCRIBED CLOSE COMMAND WAS MALFORMED AND ITS OBVIOUS SAFE VARIANT MUTATES THE TREE. 'aw backlog set done <item> --status done' mixes the two spellings, so 'done' is parsed as the SELECTOR and the id is ignored (exits 2, 'selector done is ambiguous'). An executor would then try --dry-run, and THAT IGNORES THE FLAG AND PERFORMS THE TRANSITION: it closed 6h7y2y from graduated to done during this review, moved the file, and printed only a success line. I reverted it and reproduced it deliberately to confirm determinism; nothing was committed. Root cause: cli.py:12636 routes the --status form to backlog.run_set, whose only write guard is getattr(args,'apply',True) at backlog.py:838, and aw backlog set defines NO --apply flag, so the guard is unreachable, while the POSITIONAL form routes to status_set and honors dry_run correctly. FILED AS BACKLOG 19lmbe (bug, Blocks-Release: next) with the reproduction and root cause; E-04 now mandates the positional spelling, requires a dry-run preview plus a git status check first, and tells the executor how to recognize and revert an accidental mutation. SECOND SERIOUS FINDING: E-02's 'prove the review sweep and the plan action resolve the same spec set' IS NOT PERFORMABLE, because discover_specs has exactly ONE caller (runner_shared.py:5564) and the plan action resolves no specs at all (enforce_requested_action raises at :14486 since ACTION_IMPLEMENTED is frozenset(('review',))). Child 02's own E-02 says stopping short is a legitimate outcome, so E-02 now branches on what child 02 shipped and FORBIDS a fabricated comparison, requiring an explicit SINGLE-SURFACE verdict citing the sibling's recorded decision instead. ALSO FIXED: the expected NO-TRANSITION branch would REFUSE at finalize because both declared Scope-Paths would be declared-but-unmodified (ipd_lifecycle.py:3461-3464), whose bad escape is closing the item to tidy the report, so the scope check now names the two --scope-ack flags and forbids that; the graduated/ path is a SNAPSHOT that a done transition deletes, so the item must be resolved by id6 at execution time; three stale citations corrected (process_backlog_close is at oc_runipd.py:2715 and agy_runipd.py:1644, not :2680/:1608; discover_specs is at :5464, not :5460); the AST guard is NAMED exactly (test_spec_review_attestation.py::test_enumeration_reuses_the_shared_authority, verified passing) since the repo has several; 'aw backlog check clean' was an unreachable bar because the tree already carries 16 pre-existing id-duplicate violations, so it is now judged on the delta; the measured lane baseline is recorded (1 failed, 7942 passed, the failure being test_turn_bounds.py from ambient OPENCODE_CONFIG_CONTENT); and the gate gained the paste-actual-output rule, a declaration-style scope fence, and conditional runner-versus-executor finalize ownership. SEPARATELY AND DISCLOSED: my earlier review of sibling 2s0iym advanced it to reviewed, which turned tests/test_orchestrator_retirement.py's commitguard row red because it pins that child's literal status. I RE-POINTED the row as the test's own guidance mandates (re-measure, never loosen) and recorded why; the refusal reason and child count are unchanged and the full suite is back to its one environmental failure. Nine decisions recorded as D-1..D-9 in the review record, none irreversible. E-count 4 to 4; no E-item added or removed; no sibling plan and no product code touched.

- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored to own orchestrator `y9s4vm`'s E-01, E-02 and E-03, which the ORCHESTRATOR COVERAGE GATE refused a run over on 2026-09-21. AGENTS.md prescribes adding a child for uncovered parent work rather than deleting the item, so `y9s4vm`'s checklist is left EXACTLY as authored and this child is what makes those items performable under a pre-transition E/V checkpoint. THE PARENT ALREADY PROVED THE HARDEST PART OF THE CASE, and I re-verified it live rather than trusting the prose. `evaluate_backlog_close(repo, '6h7y2y', [])` returns `close=False` with `reason='IPD carrier(s) not executed: ...graduate-00-y9s4vm..., ...graduate-01-jxxec8..., ...graduate-02-iuxtjy...'`, naming the PARENT as a blocking carrier, exactly as the parent's E-03 documented. Also re-verified by introspection that neither `runner_shared.dispatch_orchestrator_item` nor `ipd_lifecycle.retire_orchestrator` mentions `backlog` at all, while `process_backlog_close` is called from the agent-executed finalize path in both hosts (`oc_runipd.py:2680`, `agy_runipd.py:1608`). So the close is a deliberate human-or-agent act after the Set, and this plan is the agent-executed member that can legitimately perform it. MEASURED AT HEAD `41f6a45b` AND THREE OF THE PARENT'S FIGURES MOVED, which is itself why a re-measuring child is needed rather than a parent asserting stale numbers. `6h7y2y` is `- Status: graduated` (in `.aw/records/backlog/graduated/`), so E-03's CONDITIONAL branch is the live one and an executor holding it to `done` unconditionally would be wrong. `runner_shared.discover_specs` still exists exactly ONCE (`grep -c "def discover_specs"` -> 1, at `runner_shared.py:5460`) and finds 17 specs of 36 on disk, not the 9 of 28 the parent recorded; the gap is documented in its own docstring and is not a defect, but the parent's figure must not be quoted. `ACTION_CHOICES` is still `("review", "plan", "execute")` with `ACTION_IMPLEMENTED` still `frozenset(("review",))` (`runner_shared.py:12707-12708`), so the fail-closed refusal is intact and must not be re-implemented. The `From-Spec: 25kzda` cluster is NINE plans, matching the parent's largest-legitimate-cluster figure, so CID-1 has a real subject. SIX plans carry BOTH a `From-Spec:` and a `From-Backlog:` bullet, not the five the parent's F-9 recorded, so a first-match-only index would now drop six edges. THE CROSS-SET CONSTRAINT IS STILL UNBUILT AND THEREFORE STILL LIVE: `Graduated-To` occurs ZERO times in `agent_workflows/` and `check.graduated-to-dangling` does not exist (`grep -c` -> 0), so `bwgyum` has not landed and CID-7 must be reported as half-satisfied rather than declared clean.
- 2026-09-20 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Discharge the `graduate` Set's whole-Set verification from an agent-executed plan, so the Set's completion criteria and its backlog ledger are checked by something a pre-transition E/V checkpoint gates, instead of being parked on a parent that a runner retires without reading and that cannot close its own backlog item by construction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the children landed in the required order

- [x] E-01 CONFIRM BOTH CHILDREN REACHED `executed` AND THAT ORDER 01 PRECEDED ORDER 02, reading the STATUS ON DISK and the FINALIZE COMMITS rather than trusting any table. The parent's E-01 is explicit that the order is the backlog item's own instruction, on the stated reason that the verb without the guard is "a machine for generating redundant plans faster than a human can".
  PROVE THE ORDER BY COMMIT, NOT BY ORDER DIGIT. Compare the two finalize commits' timestamps or ancestry. An Order digit is an intention; a commit is what happened. This is the same standard the sibling `specdirs` Set applies in its CID-1.
  - Depends on: none
  - Expected outcome: `jxxec8` and `iuxtjy` both read `- Status: executed` and sit in `.aw/records/plans/executed/`, with pasted evidence that Order 01's finalize commit precedes Order 02's.
  - Execution state: performed

### Task group 2: the two structural properties no child can assert alone

- [x] E-02 PROVE EXACTLY ONE SPEC ENUMERATION SURVIVES, AND THAT THE REVIEW SWEEP AND THE PLAN ACTION RESOLVE THE SAME SPEC SET. This is the parent's named damage case: a parallel enumeration would make the two surfaces disagree about which specs exist.
  THE "TWO SURFACES" COMPARISON IS CONDITIONAL ON CHILD 02 HAVING BUILT THE SECOND SURFACE, AND TODAY IT DOES NOT EXIST. MEASURED AT REVIEW: `discover_specs` has exactly ONE caller in `agent_workflows/`, the `spec` branch of `sweep_review_candidates_for_type` (`runner_shared.py:5564`); the plan action has no spec resolution at all, because `enforce_requested_action` raises on `--action plan` before resolving anything (`runner_shared.py:14486`, `ACTION_IMPLEMENTED = frozenset(("review",))` at `:14028`). So there is currently NO second resolution to compare against, and a literal attempt to compare two surfaces would have nothing to put on the other side.
  SO BRANCH ON WHAT CHILD 02 ACTUALLY SHIPPED, and read its `V-*` evidence to decide. Child 02's own E-02 is explicit that consuming `discover_specs` is "roughly a quarter" of the job, that four seams must be crossed, and that RECORDING THAT IT DOES NOT RESOLVE AND STOPPING is a legitimate outcome (its OQ-03 permits splitting to a follow-on Set). IF child 02 wired the plan action, compare the two resolutions as originally written. IF child 02 legitimately stopped short, the honest verdict is SINGLE-SURFACE: prove the ONE enumeration is still unique and still the only spec authority, state that the second surface was not built and cite child 02's recorded decision, and do NOT manufacture a comparison. Declaring "both surfaces agree" when only one exists would be a false pass of exactly the kind this Set exists to prevent.
  ASSERT BY IDENTITY, NOT BY GREP ALONE. The parent's CID-2 requires object identity plus a comparison of the two resolutions. Grep proves a name appears once; identity proves both callers reach the SAME function. Where only one caller exists, the identity claim is still meaningful and still required: prove that the single caller reaches `runner_shared.discover_specs` itself rather than a private copy.
  NAME THE GUARD TEST EXACTLY, because "the AST guard" is ambiguous in a repo with several AST tests. It is `tests/test_spec_review_attestation.py::...::test_enumeration_reuses_the_shared_authority`, which walks `runner_shared`'s AST rejecting any non-docstring `"records/specs"` string constant AND requires `_iter_spec_records` to still be called. VERIFIED PASSING AT REVIEW (`1 passed, 32 deselected in 0.45s`).
  MEASURED AT HEAD `41f6a45b` AND RE-MEASURED AT REVIEW: `grep -c "def discover_specs" agent_workflows/runner_shared.py` is 1, and `discover_specs(repo)` returns 17 records against 36 `*.spec.md` files on disk. THE DEFINITION IS AT `runner_shared.py:5464`, NOT `:5460` as this plan first recorded, which is itself the reason to verify by symbol and not by line number. DO NOT QUOTE THE PARENT'S "9 of 28": that figure is stale and the tree moves. The 17-of-36 gap is DOCUMENTED BEHAVIOR, not a bug: `discover_specs` deliberately skips a spec with no `- Id:` because such a spec "cannot be named by a selector, cannot carry a review record ... and cannot be attested". Re-measure and report your own numbers, and treat a DROP in the ratio as the signal, not the ratio itself.
  ALSO CONFIRM THE AST GUARD STILL HOLDS: it is what makes "no second enumeration" durable rather than momentary, so run the named test above and paste its summary line.
  - Depends on: E-01
  - Expected outcome: exactly one spec-discovery function in `runner_shared` proven by identity and not only by grep; EITHER the review sweep and the plan action shown to resolve the same spec set (if child 02 built the second surface) OR an explicit SINGLE-SURFACE verdict citing child 02's recorded decision not to, never a fabricated comparison; the named AST path-literal guard test passing with its summary line pasted; re-measured counts reported rather than inherited.
  - Execution state: performed

- [x] E-03 VERIFY THE CROSS-SET SINGLE-TRAVERSAL CONSTRAINT AGAINST `setidhard`'s `bwgyum`, which is the parent's coordination constraint and the one thing neither Set's children can see. Both Sets read ONE relationship from opposite ends: `bwgyum` adds the FORWARD `- Graduated-To: <setid>[, ...]` link on the source plus `check.graduated-to-dangling`, while this Set's child 01 builds the REVERSE index from source id6 to the plans citing it. Whichever landed SECOND must CONSUME what the first built rather than re-walking the tree.
  MEASURED AT HEAD `41f6a45b`: `bwgyum` HAS NOT LANDED. `Graduated-To` occurs ZERO times in `agent_workflows/` and `check.graduated-to-dangling` does not exist (`grep -c "graduated-to-dangling" agent_workflows/check_engine.py` -> 0). `bwgyum` is `approved` and still in `pending/`. So the EXPECTED outcome is that only ONE of the two Sets has landed.
  THE HONEST REPORT IS THEN "HALF-SATISFIED", NOT "CLEAN". The parent's CID-7 says so explicitly: "If only one of the two Sets has landed, state that plainly rather than declaring the CID satisfied." Do NOT declare the constraint met because no duplication exists yet; the duplication risk transfers to `bwgyum`, so the deliverable is a RECORDED note that `bwgyum` must consume child 01's index, placed where `bwgyum`'s executor will see it.
  - Depends on: E-01
  - Expected outcome: a statement of which of the two Sets has landed, measured rather than assumed; if only this one, an explicit half-satisfied verdict plus a recorded hand-off note that `bwgyum` must consume child 01's reverse index rather than re-walking the tree; if both, the single shared symbol named and the two directions shown to return consistent answers for the same source.
  - Execution state: performed

### Task group 3: the backlog ledger

- [x] E-04 VERIFY BACKLOG `6h7y2y` REACHED ITS CORRECT TERMINAL STATE, PERFORM THE TRANSITION IF IT IS OWED, AND NAME THE ACTOR. This is the parent's E-03 and it is the item the runner cannot discharge: the close is refused while the parent is unretired because the parent is itself a carrier.
  THE TERMINAL STATE IS CONDITIONAL AND THE CONDITION DECIDES CORRECTNESS. `done` ONLY IF child 02 built the backlog half; `graduated` PLUS a filed follow-on if child 02's OQ-01 legitimately deferred it (there is no `discover_backlog` to consume, unlike `discover_specs`, which is why the deferral is permitted). Read child 02's shipped outcome to decide WHICH branch applies; do not assume `done`. An executor holding the item to `done` after a legitimate deferral would close an item whose half is unbuilt.
  MEASURED AT HEAD AND RE-CONFIRMED AT REVIEW: the item is `- Status: graduated` in `.aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md`. So if child 02 deferred, the state is ALREADY correct and this item is satisfied by verifying it and confirming a follow-on exists; if child 02 built the backlog half, a transition to `done` is owed.
  READ `6h7y2y`'s CURRENT DIRECTORY AT EXECUTION TIME RATHER THAN TRUSTING THE PATH ABOVE. The `graduated/` path is where it sits TODAY, but a `done` transition RELOCATES the file, so the path in this plan's `Scope-Paths` is a snapshot, not an invariant. Resolve it by id6 (`aw find backlog 6h7y2y`, or `find .aw/records/backlog -name '*6h7y2y*'`) before asserting anything about it. If you find it already in `done/` with a bare `status -> done` history line and no substantive message, do NOT treat that as this Set's work having completed: suspect an accidental `19lmbe` mutation by another party, and report it rather than accepting it as evidence.
  USE THE TOOLED SETTER, AND USE THE POSITIONAL SPELLING: `aw backlog set done 6h7y2y`. Do NOT hand-edit the status line (an opt-in pre-commit gate exists precisely to catch that, and the portable authority is the `aw check` rule). CONFIRM NO GATE IS INVENTED: the item carries NO `- Blocks-Release:`, and no plan in this Set may add one, so the close-legitimacy predicate has no gate to preserve. Verify that rather than assuming it.
  THE COMMAND THIS ITEM ORIGINALLY PRESCRIBED WAS MALFORMED AND DANGEROUS, AND IT WAS CORRECTED AT REVIEW. It read `aw backlog set done <item> --status done`, which MIXES the two mutually exclusive spellings. With `--status` present, `args` is the SELECTOR, so `done` is parsed as the selector and the real item id is ignored: measured, it exits 2 with "selector 'done' is ambiguous (status)" and lists every item in `done/`. An executor would then likely "fix" it by dropping the id, which is the dangerous branch below.
  DO NOT ADD `--dry-run` TO THE `--status` FORM TO "CHECK FIRST": IT IS IGNORED AND THE TREE IS MUTATED. This is a LIVE BUG measured during this review and now filed as backlog `19lmbe` (`bug`, `Blocks-Release: next`). `aw backlog set <path> --status done --dry-run` PERFORMED the transition: it closed `6h7y2y` from `graduated` to `done`, moved the file into `done/`, and printed only a success line with no preview. Root cause: with `--status` present `cli.py:12636` routes to `backlog.run_set`, whose only write guard is `if not getattr(args, "apply", True)` (`backlog.py:838`), and `aw backlog set` defines NO `--apply` flag, so the guard is unreachable. The POSITIONAL form routes to `status_set.run_set_command` instead, which honors `dry_run` (`status_set.py:1667`) and correctly previews (`graduated -> done (dry-run)`). So the positional spelling is mandated here for SAFETY, not style.
  PREVIEW WITH `aw backlog set done 6h7y2y --dry-run` FIRST, confirm it reports `graduated -> done (dry-run)` and that `git status --short` is unchanged, and only then re-run without `--dry-run`. If you ever see a bare `aw backlog set: <name> -> done` line where you expected a preview, you have hit `19lmbe`: the write already happened, so revert it (`rm` the new copy under `done/`, `git restore` the original path) and report it rather than committing.
  NAME WHO PERFORMED THE TRANSITION AND SAY IT WAS NOT AUTOMATION. The three precedent items closed this way (`kjzlgw`, `1ap48y`, `kxkc04`) each record the orchestrator caveat with a hand-written justification; the three the runner auto-closed (`q5pdiy`, `0zj66l`, `2k42zu`) have ZERO orchestrator carriers. Follow the first pattern.
  - Depends on: E-02, E-03
  - Expected outcome: `6h7y2y` reads `done` if child 02 built the backlog half, or `graduated` with a filed follow-on if it deferred; the branch chosen is justified by citing child 02's shipped outcome; the transition (if any) was performed through the tooled setter by a named actor rather than by runner automation; no plan in this Set carries `- Blocks-Release:`; `aw backlog check` clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR'S UNCOVERED ITEM GETS A CHILD, NOT A DELETION. AGENTS.md: "do NOT delete it: ADD A CHILD for it." `y9s4vm`'s checklist is untouched by this plan; its items are discharged by citing this child's evidence.
- A BACKLOG ITEM IS NOT CLOSED BY THE SET THAT DRAINS IT WHEN AN ORCHESTRATOR CARRIES THE LINK. `process_backlog_close` fires only at an agent-executed IPD's finalize (`oc_runipd.py:2715`, `agy_runipd.py:1644`; the `:2680`/`:1608` this plan first cited are STALE, so verify by symbol rather than by line); orchestrator retirement never calls it (verified by introspection: `'backlog' in inspect.getsource(...)` is False for both `dispatch_orchestrator_item` and `retire_orchestrator`), and `evaluate_backlog_close` refuses while ANY carrier including the orchestrator is unexecuted.
- `evaluate_backlog_close` NAMES FOUR CARRIERS, NOT THREE, AND THE FOURTH IS THIS PLAN. Re-measured live at review: `close=False, reason='IPD carrier(s) not executed: ...y9s4vm..., ...jxxec8..., ...iuxtjy..., ...yv4tb1...'`. This plan carries `- From-Backlog: 6h7y2y` too, so it is a carrier of the item it verifies and the predicate CANNOT return `close=True` while this plan is itself pending. That is the mechanical reason E-04 must perform a DELIBERATE tooled transition rather than wait for automation, and it is not a defect.
- ALL THREE SIBLINGS ARE `approved` AND STILL IN `pending/` AT REVIEW, so the Set has not run. `y9s4vm`, `jxxec8` and `iuxtjy` each read `- Status: approved`. This plan's `Item-Dependencies: executed:jxxec8, executed:iuxtjy` are therefore BOTH UNSATISFIED today, and a runner will correctly mark this item `dependency-blocked`.
- `discover_specs` EXISTS EXACTLY ONCE AND IS CAREFULLY BUILT. At `runner_shared.py:5464`, taking no injected parser because there is one spec record shape. It reads identity and status through shared authorities and adds NO path literal, guarded by `tests/test_spec_review_attestation.py::...::test_enumeration_reuses_the_shared_authority`. It finds 17 of 36 specs at HEAD and the gap is documented in its own docstring.
- `discover_specs` HAS EXACTLY ONE CALLER TODAY, which bounds what E-02 can assert. The sole caller is the `spec` branch of `sweep_review_candidates_for_type` (`runner_shared.py:5564`); the plan action never reaches a spec because `enforce_requested_action` refuses first. "Two surfaces agree" is therefore a CONDITIONAL claim that depends on child 02 wiring the second one.
- `aw backlog set` HAS TWO HANDLERS AND ONLY ONE HONORS `--dry-run`. The positional form (`aw backlog set <status> <selector>`) routes to `status_set.run_set_command` and previews correctly; the `--status` form routes to `backlog.run_set`, whose write guard reads a nonexistent `apply` flag, so `--dry-run` is silently ignored and the tree is mutated (backlog `19lmbe`). Use the positional spelling.
- `--action plan` ALREADY FAILS CLOSED. `ACTION_CHOICES = ("review", "plan", "execute")` and `ACTION_IMPLEMENTED = frozenset(("review",))` at `runner_shared.py:12707-12708`. Do not re-fix it.
- MULTIPLE PLANS PER SOURCE ARE LEGITIMATE. The `From-Spec: 25kzda` cluster is NINE plans at HEAD and is correct work. No child may implement a `count > 1` uniqueness rule.
- SIX PLANS CARRY BOTH A `From-Spec:` AND A `From-Backlog:` BULLET at HEAD (the parent's F-9 recorded five). A first-match-only index would drop one edge per such plan.
- THE FORWARD LINK IS UNBUILT. `Graduated-To` occurs zero times in `agent_workflows/` and `check.graduated-to-dangling` does not exist, so `bwgyum` has not landed.

## Findings

| Id | Severity | Location (measured at HEAD `41f6a45b`) | Finding | Evidence |
|---|---|---|---|---|
| F-01 | error | `y9s4vm` E-01..E-03 | All three parent items are covered by no child, and orchestrator retirement skips the E/V checkpoint, so a runner reports them complete unperformed. This plan closes that. | ORCHESTRATOR COVERAGE GATE refused `aw oc run` naming `y9s4vm` on 2026-09-21. |
| F-02 | error | `oc_runipd.evaluate_backlog_close` | The parent is itself a blocking carrier for its own backlog item, so the close is refused by construction while it is unretired. Confirmed live, not inferred. | `close=False, reason='IPD carrier(s) not executed: ...y9s4vm..., ...jxxec8..., ...iuxtjy...'`. |
| F-03 | info | `dispatch_orchestrator_item`, `retire_orchestrator` | Neither mentions `backlog` at all, so no runner path can close the item on an orchestrator's retirement. | `'backlog' in inspect.getsource(fn)` is False for both. |
| F-04 | warn | `y9s4vm` Step 0 ("finds 9 of 28 specs") | STALE. `discover_specs` finds 17 of 36 at HEAD. The ratio is documented behavior, not a defect, but the parent's figure must not be quoted as current. | `len(discover_specs(repo))` -> 17; `ls .aw/records/specs/*.spec.md | wc -l` -> 36. |
| F-05 | warn | `y9s4vm` F-9 ("five plans carry both") | STALE in the direction that matters: SIX plans carry both a `From-Spec:` and a `From-Backlog:` bullet, so a first-match index drops six edges, not five. | Counted over `.aw/records/plans/*/*.ipd.md`. |
| F-06 | info | `6h7y2y` | The item is `graduated`, so E-04's CONDITIONAL branch is live. An executor defaulting to `done` would be wrong. | `.aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-...backlog.md` reads `- Status: graduated`. |
| F-07 | info | `agent_workflows/` | `bwgyum` has not landed, so CID-7 is half-satisfiable at best and must be reported as such rather than declared clean. | `Graduated-To` zero occurrences; `check.graduated-to-dangling` zero occurrences. |
| F-08 | error | plan E-04, the prescribed command | **THE PRESCRIBED CLOSE COMMAND WAS MALFORMED, AND ITS OBVIOUS "SAFE" VARIANT MUTATES THE TREE.** `aw backlog set done <item> --status done` mixes both spellings: with `--status` present, `args` is the selector, so `done` is the selector and the id is ignored (exits 2, "selector 'done' is ambiguous (status)"). Worse, adding `--dry-run` to the `--status` form IGNORES IT and performs the transition. It CLOSED `6h7y2y` during this review; reverted and reproduced. Filed as `19lmbe` (`bug`, `Blocks-Release: next`). | `cli.py:12636` routes `--status` to `backlog.run_set`, whose guard is `getattr(args, "apply", True)` (`backlog.py:838`) for a flag that does not exist. |
| F-09 | error | plan E-02 | **THE "TWO SURFACES AGREE" ASSERTION IS NOT PERFORMABLE TODAY.** `discover_specs` has exactly ONE caller (`runner_shared.py:5564`); the plan action resolves no specs because `enforce_requested_action` raises first (`:14486`). E-02 now branches on what child 02 shipped and forbids a fabricated comparison. | `grep -rn discover_specs agent_workflows/*.py` -> definition plus one docstring plus one call. |
| F-10 | error | plan Step 0 + `evaluate_backlog_close` | **THE PREDICATE NAMES FOUR CARRIERS, NOT THREE, AND THE FOURTH IS THIS PLAN.** Re-measured: the reason string also names `...yv4tb1...`. So the predicate cannot return `close=True` while this plan is pending, which is precisely why E-04 must transition deliberately. Recording three understated the point the plan was making. | Live `evaluate_backlog_close(Path('.'), '6h7y2y', [])`. |
| F-11 | warn | plan Step 0, `process_backlog_close` lines | STALE line numbers: the calls are at `oc_runipd.py:2715` and `agy_runipd.py:1644`, not `:2680`/`:1608`. `discover_specs` is at `runner_shared.py:5464`, not `:5460`. Verify by symbol, never by line. | `grep -n process_backlog_close`; `grep -n "def discover_specs"`. |
| F-12 | warn | plan `Scope-Paths` + finalize | **THE EXPECTED NO-TRANSITION BRANCH REFUSES AT FINALIZE.** Both declared paths would be declared-but-unmodified, and finalize demands a `--scope-ack` each. The bad escape is performing the close to tidy the report. Scope check now names the acks and forbids that. | `ipd_lifecycle.py:2108-2112`, `:3461-3464`; `runner_shared.py:14215-14219`. |
| F-13 | warn | plan E-04 | The `graduated/` path in `Scope-Paths` is a SNAPSHOT, not an invariant: a `done` transition relocates the file. Resolve the item by id6 at execution time. Also: an item found in `done/` with a bare `status -> done` line may be an accidental `19lmbe` mutation, not this Set's work. | Measured during the accidental transition and its revert. |
| F-14 | info | sibling plans | All three siblings are `approved` and still in `pending/`, so BOTH of this plan's `Item-Dependencies` edges are unsatisfied today and a runner will mark it `dependency-blocked`. Correct behavior, recorded so it is not read as a defect. | Each sibling reads `- Status: approved`. |
| F-15 | info | `tests/test_spec_review_attestation.py` | The "AST guard" is `test_enumeration_reuses_the_shared_authority`, which rejects a non-docstring `"records/specs"` constant AND requires `_iter_spec_records`. Named exactly because the repo has several AST tests. VERIFIED PASSING (`1 passed, 32 deselected`). | Run at review. |
| F-16 | info | `.aw/records/plans/*/*.ipd.md` | The six-plans-carry-both count re-measures as SIX, confirming this plan's F-05 correction of the parent's five. | Counted over both `From-Spec:` and `From-Backlog:` bullets. |

## Proposed changes (ordered, validatable)

1. Confirm both children `executed` with Order 01's finalize commit preceding Order 02's (E-01).
2. Prove one spec enumeration by identity, with the two surfaces agreeing and the AST guard passing (E-02).
3. Report the cross-Set traversal constraint honestly as half-satisfied, and record the hand-off note for `bwgyum` (E-03).
4. Verify (and if owed, perform through the tooled setter) `6h7y2y`'s conditional terminal transition, naming the actor (E-04).

This plan ships almost no code. Its deliverables are a verification record and, conditionally, one backlog status transition plus a hand-off note. That is the correct shape for the work the parent could not perform.

## Deferred / out of scope (with reason)

- IMPLEMENTING EITHER CHILD'S WORK. Child 01 owns the reverse index and child 02 owns the selector; this plan verifies, it does not build.
  - Carrier-Declined: A DIVISION OF LABOUR, not deferred work: both children are already authored and approved, and each owns its half. Nothing is left unowned for a carrier to hold.
- ADDING A `count > 1` UNIQUENESS RULE. Forbidden by the parent's hard constraints: 17 of 72 sources legitimately have more than one plan and the largest correct cluster is nine. A uniqueness rule would flag correct work and teach people to ignore the warning.
  - Carrier-Declined: A REJECTED DESIGN, recorded so it is not re-proposed. The parent's hard constraints forbid it on measured grounds (the largest legitimate cluster is nine plans), so there is no future state in which it should be built.
- RE-FIXING THE `--action plan` REFUSAL. It already fails closed (`ACTION_IMPLEMENTED = frozenset(("review",))`) and must keep doing so for anything child 02 did not implement.
  - Carrier-Declined: Correct as-is, not deferred. `ACTION_IMPLEMENTED = frozenset(("review",))` already fails closed, so there is no work to hand off.
- WEAKENING `check.from-backlog-dangling` OR `check.from-spec-dangling`. Both are `error` severity and validate the FORWARD direction. This Set adds a reverse VIEW and does not touch them.
  - Carrier-Declined: A PROHIBITION, not an obligation. Both rules are `error` severity and must stay untouched; a carrier would imply someone should later change them.
- ANSWERING THE "ALREADY IMPLEMENTED" CASE MECHANICALLY. There is no per-requirement tracking: a spec carries ONE whole-artifact status, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog `f1sw71` tracks that gap and is `graduated` to decision plan `si24ia`.
  - Carrier-Declined: Already carried: backlog `f1sw71` owns this gap and is `graduated` to decision plan `si24ia`. A second carrier would duplicate a live record.
- BUILDING THE FORWARD `Graduated-To` LINK. That is `bwgyum`'s deliverable in the `setidhard` Set. This plan records the coordination note and stops.
  - Carrier-Declined: Already carried by plan `bwgyum` (Set `setidhard`), which is `approved` and owns the forward link plus its dangling check. E-03 records the coordination note rather than duplicating the work.
- ADDING A `Blocks-Release` GATE. The item carries none, and inventing one would fabricate a release gate.
  - Carrier-Declined: A PROHIBITION protecting an absent gate. The item carries none, so inventing one would fabricate a release blocker; there is nothing to carry.
- THE `Readiness:` FIELD. Written by `/plan-review` on 2026-09-21, which is the only legitimate author of it. It was correctly ABSENT while this plan was unreviewed.
  - Carrier-Declined: Now an ATTESTED REVIEW OUTPUT rather than an omission. Nothing is left for a carrier.
- FIXING BACKLOG `19lmbe` (`aw backlog set --status` ignores `--dry-run`). Discovered during this plan's review because E-04's prescribed command tripped it. E-04 now routes around it by mandating the positional spelling.
  - Carrier-Declined: Already carried by backlog item `19lmbe`, filed `open` with `Work-Kind: bug` and `Blocks-Release: next`, holding the measured reproduction and the root cause (`backlog.py:838` reads a nonexistent `apply` flag). A second carrier would duplicate a live record. This plan must not fix it: a verification plan editing the setter it uses would put the fix and its only user in one unreviewed change.
- FIXING `tests/test_turn_bounds.py`'s AMBIENT-ENVIRONMENT FAILURE. It fails because `OPENCODE_CONFIG_CONTENT` is set in the executing agent's session, which is an environment fact rather than a repository defect this plan's fence can reach.
  - Carrier-Declined: NOT A DEFECT IN THIS PLAN'S SUBJECT and not caused by it. Recording it as the measured baseline is the correct treatment; asserting a carrier would invent an obligation nobody owes.

## Scope check

- Over-scope: none. This plan reads state, asserts properties, and performs at most one tooled backlog transition.
- Scope-Paths justification: the declared paths are the backlog item itself and the `done/` directory it may be relocated INTO, because E-04 may perform a `graduated` -> `done` transition and the tooled setter relocates the file with `git mv` (a single staged rename). Both endpoints must be declared or the finalize scope gate would refuse the rename. NO product-code path is declared, deliberately: this plan verifies code it does not change, and reading is not declaring. The hand-off note E-03 records goes in this plan's own file, which `_is_implicitly_allowed` already covers.
- TWO FINALIZE CONSEQUENCES OF THIS FENCE, BOTH MEASURED AT REVIEW AND BOTH LIKELY. FIRST, THE `graduated/` PATH IS A SNAPSHOT: if E-04 performs the `done` transition, the declared `.aw/records/backlog/graduated/...6h7y2y...` path is DELETED by the rename, and if E-04 does NOT transition (the expected branch, since the item is already correct if child 02 deferred), then NEITHER declared path is modified. SECOND, in that no-transition branch BOTH declared entries are declared-but-unmodified, and `aw ipd finalize` FAILS CLOSED on exactly that, demanding one `--scope-ack` each ("declared-but-unmodified path needs a --scope-ack", `ipd_lifecycle.py:3461-3464`, computed at `:2108-2112`). So finalize the no-transition branch with `--scope-ack .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md=no-transition-owed --scope-ack .aw/records/backlog/done/=no-transition-owed`. DO NOT PERFORM THE TRANSITION MERELY TO SATISFY THE FENCE: that would close a backlog item to tidy a scope report, which is the precise inversion this plan exists to prevent. A runner auto-acknowledges these (`runner_shared.py:14215-14219`), so this matters most on the hand-finalize path.
- Under-scope: this plan builds no index, adds no selector, adds no check, touches no dangling rule, and does not build the forward link. Each is a sibling's job or is excluded above.

## Required tests / validation

- `aw backlog check`, judged on the DELTA. MEASURED AT REVIEW: the tree already reports `16 violation(s)`, ALL of them `backlog.id-duplicate` on other parties' items and none naming `6h7y2y`. So "clean" is the wrong bar and would either be unreachable or invite fixing another party's records; the bar is that no NEW violation appears and none names this Set's item.
- IF ANY BACKLOG STATUS CHANGE IS MADE, verify with `git status --short` that exactly ONE item moved and that it is `6h7y2y`. This is cheap insurance against backlog `19lmbe`, where a `--dry-run` that was ignored performed a real transition and reported only a success line.
- `aw check all` shows no new `check.from-backlog-dangling` or `check.from-backlog-gate-mismatch` finding attributable to this plan. NOTE the repo has PRE-EXISTING findings of other rules; judge on the DELTA for these two rule ids specifically, and name them rather than quoting a total.
- The AST path-literal guard test for `runner_shared` passes (E-02).
- Bare suite `python3 -m pytest`, judged on the failing NODE ID delta against a baseline measured in the executing worktree. AFTER minus BEFORE must be EMPTY. Do NOT copy this Set's cited baseline: the parent's own Step 0 records that its `1 failed, 5648 passed` figure and its named failure were BOTH stale, and the one real failure it later measured was environmental. Measure your own and name node ids, never totals.
  MEASURED IN THIS LANE AT REVIEW: `1 failed, 7942 passed, 3 skipped, 2 xfailed in 143.08s`, the single failure being `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`. It is ENVIRONMENTAL and PRE-EXISTING: the assertion is `'OPENCODE_CONFIG_CONTENT' not in main_env` (`tests/test_turn_bounds.py:310`) and that variable is set in the executing agent session, so the non-isolated env inherits it. Nothing in this plan's fence can affect it.
  EXPECT `tests/test_orchestrator_retirement.py` TO BE SENSITIVE TO THIS SET'S OWN LIFECYCLE, which is the one suite interaction this plan should anticipate rather than be surprised by. Its `RealRepositorySets::test_every_live_set_reaches_its_measured_verdict_for_its_measured_reason` pins the REAL status of live Sets' children, so a child of a pinned Set advancing (or a new child being authored) turns that row red BY DESIGN. It was re-pointed during this review for exactly that reason. `graduate` is NOT a pinned row today, so this plan is unlikely to trip it; but if it does, the fix the test itself mandates is to RE-MEASURE AND RE-POINT the row, never to loosen the assertion, and never to revert a legitimate status change to make it green.
- Do NOT delete another party's untracked files to make the suite green; this is a shared checkout.

## Spec / documentation sync

- NO SPEC AMENDMENT IS INTENDED and no `.spec.md` path is declared in `Scope-Paths`. Spec `25kzda`'s graduation text (a run "may produce more than one IPD") and spec `6m4kow`'s spec-review authority are both CONSUMED by this plan, not amended. If E-02 or E-03 finds that a shipped behavior contradicts either spec, STOP and record it: a spec edit is a contract change that must be declared in `Scope-Paths` before the run starts, so it needs its own plan.
- The hand-off note in E-03 is a PLAN-LEVEL record, not documentation: it belongs in this plan's evidence and, if the maintainer prefers, in a backlog item for `bwgyum`'s executor. It must not be written into `bwgyum` itself, which is another plan's file.

## Open questions

### OQ-01: If child 02 deferred the backlog half, who files the follow-on and is this plan allowed to file it?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution at execution (2026-09-23): MOOT. THE CONTINGENCY NEVER AROSE. The question only bites if child 02 deferred the backlog half AND filed no follow-on. Child 02 DID defer (its V-03: "DEFER the backlog half; deliver the spec RESOLUTION half only"), but it ALSO filed the follow-on itself: `aw find backlog oc3mhb` resolves `.aw/records/backlog/open/20260923-oc3mhb-01-oc3mhb-spec-selector-resolves-but-cannot-be-queued.backlog.md`, `- Status: open`. So neither option (a) nor option (b) was exercised, no out-of-scope write into `.aw/records/backlog/open/` was needed on OQ-01's account, and no `--scope-reason` was required for it. The maintainer's authority preference is therefore still unrecorded and remains available for a future case. NOTE for the record: I did write ONE new item into `.aw/records/backlog/open/` (`knvpiv`), but on E-03's account (the CID-7 hand-off carrier), not OQ-01's.
- Carrier-Declined: A CONTINGENT AUTHORITY QUESTION, not an outstanding obligation. It only arises if child 02 deferred the backlog half AND filed no follow-on, and in that case E-04's evidence RECORDS the missing follow-on as a finding, so nothing disappears unrecorded. The question is which of two legitimate routes an executor should take, which is a convention for the maintainer rather than work anyone owes.
- Resolution or deferral rationale: NON-BLOCKING because E-04's verification succeeds either way: the item is ALREADY `graduated`, so if child 02 deferred, the correct state is the current one and this plan's job is to CONFIRM a follow-on exists rather than to invent a status change. The open part is narrow: if child 02 deferred and NO follow-on was filed, the honest options are (a) this plan files one with `aw backlog new`, which is a small records-only act well within an agent's normal authority but slightly widens this plan's scope beyond verification, or (b) this plan reports the missing follow-on as a finding and leaves the filing to the maintainer, keeping the plan purely verificatory. RECOMMENDATION: (a), because a verification that discovers a missing record and declines to create it leaves the gap open with nobody owning it, and `aw backlog new` is exactly the tooled path for that. If the maintainer prefers (b), E-04's expected outcome should be narrowed to reporting only. Either way, this plan must NOT set the item `done` to make the branch tidy.
  NARROWED AT REVIEW 2026-09-21 ON THE MECHANICS, leaving only the authority preference to the maintainer. If option (a) is taken, the filing must NOT be a bare `aw backlog new`: an item created with `--apply` lands with only a one-line history record, so the whole reason it exists must be written into its body afterwards (measured while filing `19lmbe` during this review). Also, `aw backlog new` WRITES INTO `.aw/records/backlog/open/`, which this plan does NOT declare in `Scope-Paths`, so option (a) necessarily produces an out-of-scope path. That is PERMITTED and is reconciled at finalize with `--scope-reason .aw/records/backlog/open/=filed the follow-on OQ-01 option (a) authorizes`, not a reason to stop. If the new item's `- Work-Kind:` is `bug` it MUST also carry `- Blocks-Release:` per the repository rule; a follow-on for unbuilt design work is a `feature` or `chore` and carries no gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste both children's `- Status:` lines and their file paths showing they sit in `.aw/records/plans/executed/`. Paste the ORDERING proof as commit evidence (timestamps or `git merge-base --is-ancestor`), not as a restatement of the Order digits. Also paste a summary of each child's `V-*` results showing they carry real observed evidence rather than assertions, since a child marked `executed` with empty evidence blocks would make this Set's completion claim hollow.
  - Observed evidence: BOTH CHILDREN ARE `executed` AND THE ORDER IS PROVEN BY ANCESTRY, NOT BY THE ORDER DIGIT. Measured in lane `aw/lane/yv4tb1` at HEAD `0823163b`.

    STATUS ON DISK, both in `.aw/records/plans/executed/`:

    (Captured with `grep -H` so each status line carries its path prefix: a bare `- Status: executed`
    line pasted into a plan file is indistinguishable from a real status declaration, and the
    `ipd-executed-transition-gate` pre-commit hook correctly refuses a commit containing one. That
    refusal fired on this very evidence block and is working as designed.)

    ```
    $ for f in .aw/records/plans/executed/20260908-graduate-01-jxxec8-*.ipd.md \
               .aw/records/plans/executed/20260908-graduate-02-iuxtjy-*.ipd.md; do
        grep -H -m1 '^- Status:' "$f"; done
    .aw/records/plans/executed/20260908-graduate-01-jxxec8-report-every-existing-plan-for-a-source-before-a-tenth-is-au.ipd.md:- Status: executed
    .aw/records/plans/executed/20260908-graduate-02-iuxtjy-make-a-spec-or-backlog-selector-reachable-for-the-plan-actio.ipd.md:- Status: executed
    ```

    THE ORDERING PROOF IS COMMIT ANCESTRY PLUS TIMESTAMPS, as the item demands:

    ```
    $ git log --format='%H %cI %s' -1 -- <jxxec8 plan path>
    fe664b70518b73b5c75501e7bb8ca5736849490f 2026-09-21T23:53:32-04:00 lifecycle(jxxec8): finalize jxxec8 -> executed
    $ git log --format='%H %cI %s' -1 -- <iuxtjy plan path>
    874692935603f1d6aeb55f962def732f2561b407 2026-09-23T06:09:54-04:00 lifecycle(iuxtjy): finalize iuxtjy -> executed

    $ git merge-base --is-ancestor fe664b70 874692935 && echo "ANCESTOR: jxxec8 finalize precedes iuxtjy finalize"
    ANCESTOR: jxxec8 finalize precedes iuxtjy finalize
    ```

    Order 01's finalize is a strict ANCESTOR of Order 02's and precedes it by ~30 hours, so the backlog item's sequencing instruction (the guard before the verb) was honored in fact and not merely in intent.

    EACH CHILD'S `V-*` BLOCKS CARRY REAL EVIDENCE, NOT ASSERTIONS. Every one is `pass` with a substantial pasted body (character counts of the `Observed evidence` block, measured by parsing the two files):

    ```
    === jxxec8   (5 validation items, all pass)
      V-01: result=pass evidence_chars=6410
      V-02: result=pass evidence_chars=6079
      V-03: result=pass evidence_chars=4071
      V-04: result=pass evidence_chars=6671
      V-05: result=pass evidence_chars=5340
    === iuxtjy   (6 validation items, all pass)
      V-01: result=pass evidence_chars=6813
      V-02: result=pass evidence_chars=6748
      V-03: result=pass evidence_chars=2975
      V-04: result=pass evidence_chars=4577
      V-05: result=pass evidence_chars=3357
      V-06: result=pass evidence_chars=5537
    ```

    ELEVEN validation items, ZERO empty evidence blocks, ZERO non-`pass` results. Spot-read confirms they are genuine observations rather than restatements: `jxxec8` V-05 pastes three applied source MUTATIONS against a named commit (`caa4c9...`) and their failures, and `iuxtjy` V-02 pastes end-to-end CLI transcripts from both hosts plus a deliberate precedence mutation producing `7 failed, 19 passed` then `26 passed` after revert. So this Set's completion claim rests on demonstrated work, not on checkmarks.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the identity proof that the caller(s) reach `runner_shared.discover_specs` ITSELF (object identity, not grep). THEN paste EITHER the two resolutions compared for the same repository showing an identical spec set (if child 02 wired the plan action) OR the explicit SINGLE-SURFACE verdict with the CITATION from child 02's shipped evidence recording that it did not, plus a re-measured caller count showing how many callers exist. A comparison presented as if two surfaces existed when only one does FAILS this item (F-09). Paste `grep -c "def discover_specs" agent_workflows/runner_shared.py` and your OWN re-measured `len(discover_specs(repo))` against the on-disk `*.spec.md` count, and compare to the 1 and 17-of-36 recorded in this plan's Findings, explaining any change. Paste the summary line of `tests/test_spec_review_attestation.py -k test_enumeration_reuses_the_shared_authority`, naming that test rather than "the AST guard".
  - Observed evidence: SINGLE-SURFACE IS THE LIVE VERDICT, AND THE CALLER COUNT MOVED FROM 1 TO 3, WHICH I EXPLAIN RATHER THAN PAPER OVER. Measured at HEAD `0823163b`.

    EXACTLY ONE ENUMERATION SURVIVES:

    ```
    $ grep -c "def discover_specs" agent_workflows/runner_shared.py
    1
    ```

    IDENTITY, NOT GREP. A bare `Name` call resolves through the calling function's `__globals__` at call time, so proving that entry IS the canonical object proves every caller reaches it. All three callers plus the module table agree on ONE object at ONE address, backed by ONE code object:

    ```
    canonical: <function discover_specs at 0x740c2c2c5220>

    sweep_review_candidates_for_type       globals['discover_specs'] is rs.discover_specs -> True  id=0x740c2c2c5220
    resolve_selected_artifact_paths        globals['discover_specs'] is rs.discover_specs -> True  id=0x740c2c2c5220
    match_spec_selector                    globals['discover_specs'] is rs.discover_specs -> True  id=0x740c2c2c5220

    module-global table identity: True
    code object: .../agent_workflows/runner_shared.py firstlineno=10189
    ```

    An AST walk confirms all three call sites are bare `Name(id='discover_specs')` nodes (no attribute access on a private copy, no shadowing):

    ```
    line 10289: enclosing=sweep_review_candidates_for_type  func_node=Name(id='discover_specs', ctx=Load())
    line 10512: enclosing=resolve_selected_artifact_paths   func_node=Name(id='discover_specs', ctx=Load())
    line 10850: enclosing=match_spec_selector               func_node=Name(id='discover_specs', ctx=Load())
    ```

    THE CALLER COUNT CHANGED FROM THE 1 THIS PLAN RECORDED AT REVIEW, AND THE CHANGE IS CHILD 02'S SHIPPED WORK, NOT A SECOND ENUMERATION. Review measured one caller (`sweep_review_candidates_for_type`). There are now THREE, the two new ones added by `iuxtjy`: `match_spec_selector` (selector precedence, so a spec token resolves to the SPEC and never falls back to a plan) and `resolve_selected_artifact_paths` (per-type resolution). Both CONSUME the shared authority; neither re-walks. Child 02's own V-02 states this and pins it with a test: "`match_spec_selector`'s body contains `specs = discover_specs(Path(repo))`, asserted by `NoSecondEnumerationTests::test_the_spec_branch_calls_discover_specs`; `src.count("def discover_specs") == 1`". More callers of one authority is the OPPOSITE of the damage CID-2 guards against.

    THE VERDICT IS **SINGLE-SURFACE**, AND I DID NOT MANUFACTURE A COMPARISON. Child 02 deliberately did not wire the plan action, so no second resolution exists to compare against. Its V-02, verbatim: "Seam 1 (EXPANSION) is FIXED ... Seams 2-4 (the preflight triple, a derived action of `plan`, and a queue entry) are NOT delivered, and the derived action is NOT `plan`: `action_for` still returns only `{execute, review, orchestrate}` over all 76 Kind x status pairs." And: "`ACTION_IMPLEMENTED` BEFORE: `frozenset({'review'})`. AFTER: `frozenset({'review'})` - UNCHANGED, deliberately (D2)". The remainder is filed as backlog `oc3mhb`. Confirmed live at HEAD:

    ```
    ACTION_CHOICES   : ('review', 'plan', 'execute')
    ACTION_IMPLEMENTED: frozenset({'review'})
    ```

    So `--action plan` still FAILS CLOSED (`enforce_requested_action` raises before resolving anything) and there is no second spec resolution in existence. Declaring "both surfaces agree" here would be exactly the false pass this Set exists to prevent.

    RE-MEASURED COUNTS, MY OWN, NOT INHERITED:

    ```
    len(discover_specs(repo)) = 17
    on-disk *.spec.md         = 36
    ```

    Identical to the 17-of-36 this plan's Findings recorded at review (and NOT the parent's stale 9-of-28). The ratio is documented behavior: specs with no `- Id:` are deliberately skipped because they cannot be named by a selector or carry an attestation. No DROP occurred, which is the signal the item asks me to watch.

    THE NAMED AST GUARD PASSES:

    ```
    $ python3 -m pytest tests/test_spec_review_attestation.py -k test_enumeration_reuses_the_shared_authority
    1 passed in 5.11s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the measurement of whether `bwgyum` has landed (`grep -c "graduated-to-dangling" agent_workflows/check_engine.py` and an occurrence count for `Graduated-To` in `agent_workflows/`), plus `bwgyum`'s current `- Status:` and directory. If only this Set has landed, paste the explicit HALF-SATISFIED verdict and the recorded hand-off note; a verdict of "satisfied, no duplication found" on a tree where the forward link does not exist yet does NOT satisfy this item, because the constraint is about what the SECOND Set must do. If both have landed, name the single shared symbol and paste the two directions returning consistent answers for one source.
  - Observed evidence: **THE PLAN'S PREDICTED BRANCH IS WRONG: `bwgyum` HAS LANDED, SO BOTH SETS ARE IN, AND THE "SECOND CONSUMES THE FIRST" CLAUSE IS NOT SATISFIED.** This plan's E-03 and its F-07 both recorded, at review, that `bwgyum` had not landed and that the honest verdict would be "half-satisfied". That is STALE. Re-measured at HEAD `0823163b`, which is why the item told me to measure rather than assume.

    `bwgyum` IS EXECUTED:

    ```
    $ f=.aw/records/plans/executed/20260908-setidhard-02-bwgyum-add-the-graduated-to-forward-link-and-its-dangling-check-mir.ipd.md
    $ grep -H -m1 '^- Status:' $f
    .aw/records/plans/executed/20260908-setidhard-02-bwgyum-add-the-graduated-to-forward-link-and-its-dangling-check-mir.ipd.md:- Status: executed
    $ dirname $f
    .aw/records/plans/executed
    $ git log --format='%H %cI %s' -1 -- $f
    55a99b5ccb2b2dfa7eedc2e220188ed12c5e969b 2026-09-23T01:30:52-04:00 lifecycle(bwgyum): finalize bwgyum -> executed
    ```

    THE MEASUREMENTS THIS PLAN PREDICTED WOULD BE ZERO ARE NOT ZERO:

    ```
    $ grep -c "graduated-to-dangling" agent_workflows/check_engine.py
    1
    $ grep -ro "Graduated-To" agent_workflows/*.py | wc -l
    23        # backlog.py:2 check_engine.py:2 ipd_schema.py:2 releases.py:15 specs.py:1 status_set.py:1
    ```

    WHICH LANDED SECOND, AND THEREFORE WHO OWED THE OBLIGATION. Finalize order by commit timestamp: `jxxec8` 2026-09-21T23:53:32 -> `bwgyum` 2026-09-23T01:30:52 -> `iuxtjy` 2026-09-23T06:09:54. The parent's constraint binds "whichever executes second" to consume the first; for THIS edge the reverse index shipped in `jxxec8` (first) and the forward link in `bwgyum` (second), so the obligation fell on `bwgyum`.

    **IT DID NOT CONSUME IT. TWO INDEPENDENT TRAVERSALS OF ONE RELATIONSHIP EXIST.** Proven by introspection of both shipped symbols:

    ```
      build_graduation_reverse_index     in check_graduated_to source -> False
      graduation_cluster                 in check_graduated_to source -> False
      _iter_plan_ipds                    in check_graduated_to source -> True
      _parse_setid                       in check_graduated_to source -> True
      rglob                              in check_graduated_to source -> True

      Graduated-To                       in build_graduation_reverse_index -> False
      parse_graduated_to                 in build_graduation_reverse_index -> False
    ```

    * REVERSE (`jxxec8`): `check_engine.build_graduation_reverse_index` walks `_iter_plan_ipds` + `_iter_spec_records` into `(kind, id6) -> [GraduationArtifact]`.
    * FORWARD (`bwgyum`): `releases.check_graduated_to` builds its OWN `known_setids` with a SECOND `_iter_plan_ipds` pass, then `rglob("*.md")`s `backlog`/`specs`/`plans` itself.

    So there is NOT "exactly one mechanism" per direction sharing a traversal; there are two passes that could in principle disagree about what a source became. **CID-7 IS THEREFORE NOT SATISFIED, AND I REPORT THAT RATHER THAN DECLARING IT MET.**

    IT IS A MISSED OBLIGATION, NOT A RACE, AND I CHECKED THE EXCUSE. Child 01's index was ALREADY IN THE TREE at `bwgyum`'s own finalize commit:

    ```
    $ git show 55a99b5c:agent_workflows/check_engine.py | grep -c "def build_graduation_reverse_index"
    1
    ```

    `bwgyum`'s E-04 did re-check the `graduate` Set as instructed, but checked the WRONG SIGNAL. Its V-04 evidence reads: "`aw graduate` still does not exist (the `graduate` Set's plans `y9s4vm`/`jxxec8`/`iuxtjy` remain in `pending/`)". That was stale for `jxxec8` (executed ~25h earlier) and was in any case a question about a VERB rather than about the reverse INDEX it was obliged to consume.

    THE TWO DIRECTIONS DO NOT DISAGREE TODAY, BECAUSE THEY SHARE NO LIVE INPUT. Measured on the live corpus: ZERO records declare `- Graduated-To:` (the sole `grep` hit is `backlog/README.md`, i.e. documentation), so the forward check is inert:

    ```
    LIVE sources declaring Graduated-To (excluding README/INDEX/STATUS): 0
    check_graduated_to findings: 0
    ```

    Because live data cannot exercise the comparison, I built a throwaway git fixture holding ONE source carrying BOTH directions plus one dangler, and the two directions AGREE on the shared source while the forward check correctly flags the dangler:

    ```
      REVERSE src111: setids=('fixset',) artifacts=[('pln222', 'fixset')]
      REVERSE src333: setids=() artifacts=[]
      FORWARD src111: Graduated-To=['fixset']
      FORWARD src333: Graduated-To=['nosuchset']

      check_graduated_to findings: 1
        rule=check.graduated-to-dangling loc=.../20260101-fixset-02-src333-a-dangler.backlog.md

      AGREEMENT for src111: forward=['fixset'] reverse=['fixset'] -> agree=True
    ```

    So the defect is LATENT (no operator can observe a wrong answer today), which is why I filed it `chore` rather than `bug` under the user-perceptible-impact test.

    THE OBVIOUS FIX IS WRONG, AND I MEASURED WHY, so the follow-on cannot be closed naively. The reverse index CANNOT become the forward check's resolution target:

    ```
    reverse index: sources = 136  artifacts = 251
    setids reachable via reverse index = 124
    forward check known_setids = 328 (from 712 plan files)
    setids the reverse index CANNOT see = 204
    ```

    The index only sees artifacts that CARRY a `From-*` bullet, so substituting it would make 204 legitimate setids read as dangling on an `error`-severity rule. The sharable unit is the underlying plan-setid ENUMERATION, not the index's keyed output.

    RECORDED HAND-OFF, PLACED WHERE IT WILL BE SEEN. Since `bwgyum` has already executed, a note addressed to "`bwgyum`'s executor" has no reader, and the spec-sync section forbids me editing another plan's file. So the durable carrier is a filed backlog item: **`knvpiv`** (`.aw/records/backlog/open/20260923-gradtravers-01-knvpiv-unify-graduation-edge-traversals.backlog.md`, `- Work-Kind: chore`, `- Status: open`), holding the introspection evidence, the finalize ordering, the 124-vs-328 constraint that rules out the naive fix, and the suggested shape. Recorded as DECISION 13-yv4tb1-D1.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `6h7y2y`'s final `- Status:` and file path, RESOLVED BY id6 at execution time rather than copied from this plan's `Scope-Paths` snapshot (F-13), and paste the CITATION from child 02's shipped outcome that justifies which branch (`done` versus `graduated` plus follow-on) is correct. If a transition was performed, paste the tooled command used (the POSITIONAL spelling, `aw backlog set done 6h7y2y`) and its output, PLUS the `--dry-run` preview you ran first showing `graduated -> done (dry-run)` and a `git status --short` confirming the preview wrote nothing. A hand-edited status line is not acceptable evidence, and neither is the `--status` spelling, which ignores `--dry-run` and mutates the tree (F-08, backlog `19lmbe`). If NO transition was owed, say so explicitly and paste the two `--scope-ack` flags used at finalize (F-12), confirming you did NOT transition the item merely to satisfy the scope fence. NAME THE ACTOR explicitly and state that the transition was not performed by runner automation, following the `kjzlgw`/`1ap48y`/`kxkc04` precedent. Paste a confirmation that no plan in this Set carries `- Blocks-Release:` and the `aw backlog check` result; NOTE the repo carries 16 PRE-EXISTING `backlog.id-duplicate` violations unrelated to this plan, so judge on the delta and name any violation mentioning `6h7y2y`. Finally, paste the `aw check all` delta for `check.from-backlog-dangling` and `check.from-backlog-gate-mismatch` specifically, naming the rule ids rather than quoting a repo-wide total.
  - Observed evidence: **NO TRANSITION WAS OWED. `6h7y2y` CORRECTLY REMAINS `graduated`, BECAUSE CHILD 02 DEFERRED THE BACKLOG HALF.** I did not set it `done`, and specifically did not set it `done` to tidy the scope report.

    RESOLVED BY id6 AT EXECUTION TIME, not copied from this plan's `Scope-Paths` snapshot (F-13):

    ```
    $ aw find backlog 6h7y2y
    ●  graduated     6h7y2y  .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md
    $ grep -m1 '^- Status:' <that path>
    - Status: graduated
    ```

    It is still in `graduated/`, NOT in `done/`, so the accidental-`19lmbe`-mutation case F-13 warns about did not occur.

    THE BRANCH IS JUSTIFIED BY CHILD 02'S SHIPPED OUTCOME, CITED. `iuxtjy`'s V-03 records the deferral verbatim: "OQ-01 ANSWERED: DEFER the backlog half; deliver the spec RESOLUTION half only. Recorded as DECISION 12-iuxtjy-D1." Its stated reason is the four seams rather than a missing enumeration: "the enumeration was never the cost, the FOUR SEAMS are, and BOTH halves must cross them identically." And it confirms the ledger consequence explicitly: "Backlog `6h7y2y` therefore stays `graduated` rather than `done`, exactly as the plan and its orchestrator require."

    THE ITEM ITSELF PRE-AUTHORIZED THIS EXACT BRANCH, which settles it beyond my judgement. Its own `2026-09-08 graduated` history line ends: "If iuxtjy OQ-01 defers the backlog half, this item stays graduated rather than going done."

    THE FOLLOW-ON EXISTS, so the deferred half has a live carrier and nothing is dropped:

    ```
    $ aw find backlog oc3mhb
    ◕  open          oc3mhb  .aw/records/backlog/open/20260923-oc3mhb-01-oc3mhb-spec-selector-resolves-but-cannot-be-queued.backlog.md
    ```

    So OQ-01's contingency (child 02 deferred AND filed no follow-on) did NOT arise, and I had no occasion to exercise either of its options.

    I RAN THE PREVIEW ANYWAY, TO DOCUMENT THE SAFE PATH AND RE-TEST `19lmbe`. Using the MANDATED POSITIONAL spelling, with a `git status` check either side:

    ```
    $ git status --short > before
    $ aw backlog set done 6h7y2y --dry-run
    -    backlog     20260906-graduate-01-6h7y2y  [medium]  graduated → ✓  done  (dry-run)
    exit: 0
    $ git status --short > after; diff before after
    (no change: the preview wrote nothing)
    ```

    The positional form previews CORRECTLY and mutates NOTHING, confirming that backlog `19lmbe` is specific to the `--status` spelling. I did NOT then re-run it without `--dry-run`, because the deferral branch is the live one. `git status --short .aw/records/backlog/` afterwards shows only my newly filed item, and `6h7y2y` untouched:

    ```
    ?? .aw/records/backlog/open/20260923-gradtravers-01-knvpiv-unify-graduation-edge-traversals.backlog.md
    ```

    NO `--scope-ack` FLAGS WERE PASSED BY ME, and the reason is a lifecycle fact rather than an omission: this run is DRIVER-DRIVEN, and the turn prompt states the runner owns `aw ipd begin`/`aw ipd finalize` (a worker invoking them is refused with `AW-LIFECYCLE-ROLE-001`). F-12's no-transition branch is live, so both declared paths ARE declared-but-unmodified and each needs an ack; the runner auto-acknowledges exactly this (`runner_shared.py:14215-14219`), which is the path in force. For a HAND finalize the required flags would be `--scope-ack .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md=no-transition-owed --scope-ack .aw/records/backlog/done/=no-transition-owed`.

    ACTOR, NAMED, AND NOT AUTOMATION: **no status transition was performed by anyone**, so there is no transition to attribute. The only mutation I made to the backlog tree is the NEW item `knvpiv`, filed by me (opencode `its_direct/pt3-claude-opus-5-1m-us`, plan `yv4tb1`, run `run-20260923T023317Z-3622118`) through the tooled `aw backlog new --apply`, not by runner automation. Per the `kjzlgw`/`1ap48y`/`kxkc04` precedent I record the orchestrator caveat: `evaluate_backlog_close` cannot fire for this item anyway, because the parent `y9s4vm` and this plan both carry `- From-Backlog: 6h7y2y` and orchestrator retirement never calls `process_backlog_close`. That is expected, not a defect.

    NO PLAN IN THIS SET CARRIES `- Blocks-Release:`, so the close-legitimacy predicate has no gate to preserve and none was invented:

    ```
    y9s4vm         0
    jxxec8         0
    iuxtjy         0
    yv4tb1         0        (count of '^- Blocks-Release:' lines per plan)
    ```

    `aw backlog check` IS CLEAN, AND THE PLAN'S BASELINE IS STALE IN THE GOOD DIRECTION. This plan recorded 16 pre-existing `backlog.id-duplicate` violations at review and told me to judge on the delta; another party has since resolved them:

    ```
    $ aw backlog check
    aw backlog check: all backlog items conform.
    $ aw backlog check | grep -c "6h7y2y\|knvpiv"
    0
    ```

    No violation names `6h7y2y` or my new item, so the delta is zero against a now-clean tree.

    `aw check all` DELTA FOR THE NAMED RULE IDS, counted by rule id rather than by a repo-wide total as the item requires:

    ```
    $ aw check all | grep -c "from-backlog-dangling"        -> 0
    $ aw check all | grep -c "from-spec-dangling"           -> 0
    $ aw check all | grep -c "from-backlog-gate-mismatch"   -> 0
    $ aw check all | grep -c "knvpiv"                       -> 0
    ```

    Zero findings for all three named rules, and nothing anywhere in the sweep attributable to my new item. (The sweep does report unrelated pre-existing naming/schema advisories on other parties' artifacts, which are untouched by this plan and not mine to fix in a shared checkout.)

    BARE SUITE, WITH THE FAILING NODE-ID DELTA EMPTY. Run in the foreground in this lane:

    ```
    $ python3 -m pytest
    FAILED tests/test_agy_runipd_cli.py::AgyCostAttributionTests::test_agy_does_not_import_the_record_builder_FROM_oc_runipd
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    FAILED tests/test_oc_runipd.py::AgyCardIsNotResolvableTests::test_the_shared_symbol_lives_in_runner_shared_NOT_in_oc_runipd
    3 failed, 9069 passed, 3 skipped, 2 xfailed, 6 warnings in 416.24s (0:06:56)
    ```

    I PROVED THE THREE ARE PRE-EXISTING RATHER THAN ASSERTING IT. My only change is ONE UNTRACKED `.backlog.md` file (`git diff --stat` is empty: no tracked file is modified). Moving it aside to make the tree pristine (`git status --short | wc -l` -> `0`) and re-running the three node ids:

    ```
    $ python3 -m pytest <the three node ids>
    3 failed in 4.68s
    ```

    All three fail on a tree with ZERO changes, so AFTER minus BEFORE is EMPTY. The file was then restored. Two are already filed by other parties (`2tiyl8` for the stale `56` import pin; the `turn_bounds` ambient-env failure is filed many times over, e.g. `j08jky`, `cfgj8s`, `tem4g9`), and the third (`AgyCardIsNotResolvableTests`) is covered by that same `2tiyl8` item, so I did not file duplicates. `tests/test_orchestrator_retirement.py` did NOT go red, as this plan anticipated it might.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: go-pending-approval`, WRITTEN BY `/plan-review` ON 2026-09-21 as that workflow's attested output. It was correctly ABSENT while the plan was unreviewed, because hand-writing it would have forged a review that never happened. `go-pending-approval` means the plan passed review and awaits sign-off; it is NOT an approval. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`.

THIS PLAN RUNS LAST IN ITS SET, BY CONSTRUCTION. It declares `Item-Dependencies: executed:jxxec8, executed:iuxtjy` because a whole-Set verification cannot precede the Set. Under a runner, `dependency_depth` sorts it last and both edges are re-checked AT DISPATCH, so if either child has not landed this item is marked `dependency-blocked` and the run continues rather than failing. That is correct behavior and not a defect to report.

WHY THIS CHILD IS THE RIGHT PLACE FOR THE BACKLOG CLOSE, stated because it is the subtle part. The close is refused while the parent is unretired, since `evaluate_backlog_close` requires every carrier terminal and the parent is itself a carrier. This plan carries `- From-Backlog: 6h7y2y` too, so it is a carrier as well and does NOT magically unblock the predicate on its own; what it provides is an AGENT-EXECUTED finalize, which is the only event that calls `process_backlog_close` at all. Expect the ordinary outcome to be that this plan VERIFIES the item's state and performs the transition deliberately through the tooled setter, exactly as the three `done/` precedents with orchestrator carriers were closed, rather than relying on automation firing. Do not read a refused automatic close as a defect.

WHAT THIS PLAN DOES TO ITS PARENT: NOTHING is deleted from `y9s4vm`. Its E-01, E-02 and E-03 stay exactly as authored, because that checklist is what makes `execute graduate` complete when a human drives the Set with no runner involved. This plan's row is ADDED to the parent's child table so the Set is covered, which lets the coverage gate pass and lets the runner retire the parent honestly. The parent's items are then discharged by CITING this child's pasted evidence.

Execution contract: commit ONLY files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED CHECKOUT with other agents and humans working concurrently: verify the staged set with `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on rejection and can leave paths you never staged in the index. Prefer the tooled path (`aw commit <plan> -- <paths>`), which snapshots the index before staging and commits only the intersection of your explicit paths with what it staged. Use the tooled POSITIONAL `aw backlog set <status> <selector>` spelling for any status change, never a hand edit and never the `--status` form (which ignores `--dry-run` and mutates the tree, backlog `19lmbe`).

WHEN YOU REPORT A CHECK OR A SUITE PASSED, PASTE THE ACTUAL COMMAND OUTPUT. Every `V-*` above demands pasted evidence, and this plan's ONLY deliverable is a verification record, so an unrun claim here is not a shortcut but the whole product falsified. This applies with particular force to the two branch-dependent items (E-02's single-versus-two-surface verdict and E-04's `done`-versus-`graduated` branch): state which branch you observed and cite the sibling evidence that put you on it.

SCOPE FENCE, AS A DECLARATION: the two declared paths let the runner reconcile afterwards what moved. An out-of-scope edit is MADE AND THEN JUSTIFIED at finalize with `--scope-reason` (OQ-01 option (a) is the expected instance), and the no-transition branch needs `--scope-ack` per untouched path; neither is a reason to halt. The conditions that DO warrant stopping and reporting are the genuinely unsafe ones: a shipped behavior contradicting a spec (the spec-sync section states this), an accidental `19lmbe` mutation you did not intend, or a sibling's status you would have to change to proceed.

LIFECYCLE TRANSITION: when every `E-*` is performed and every `V-*` carries pasted evidence, this plan moves to `.aw/records/plans/executed/` through `aw ipd finalize` (with the `--scope-ack`/`--scope-reason` flags the scope check names), NEVER by a hand-rolled `git mv`. IF A RUNNER IS DRIVING THIS PLAN it owns `aw ipd begin` and `aw ipd finalize` and auto-reconciles the scope delta, so do not invoke either yourself; an agent or human executing directly owns both calls.
