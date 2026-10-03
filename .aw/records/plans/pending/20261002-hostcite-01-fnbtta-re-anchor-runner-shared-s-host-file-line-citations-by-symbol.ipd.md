# IPD: Re-anchor runner_shared's host-file line citations by symbol, and correct the three that assert a status set that no longer holds

- Date: 2026-10-02
- Kind: child
- Concern: `agent_workflows/runner_shared.py` carries bare `<host>.py:<line>` citations in comments and docstrings, and EVERY ONE OF THEM IS NOW WRONG. Re-measured at HEAD `6e299712f` by resolving each offset against the host file rather than by reading the backlog's table (F-01): there are **15 offsets across 8 citing sites**, of which **5 are PAST END OF FILE** and the other 10 all land on something unrelated to what the prose says. `oc_runipd.py` is 5487 lines and `agy_runipd.py` is 4166, so the backlog item `ma8aig`'s own snapshot (5278 and 4162, taken 2026-09-30) is ALREADY STALE, which is the defect demonstrating itself inside the record that filed it.
  THE ITEM UNDERCOUNTS, AND THE UNDERCOUNT IS NOT A QUIBBLE. `ma8aig` lists seven resolutions and scopes itself to "the four citations gyam7x does NOT fix". Measured: the real population at this HEAD is 15 offsets / 8 sites, because the item counted a RANGE (`oc_runipd.py:6993-7031`) as one offset when both endpoints are independently past EOF, and because it did not enumerate the three-offset agy half of the `verdict_refusal_text` citation (`agy_runipd.py:3696/3698/3700`) nor the `announce_run_order` pair (`agy_runipd.py:84-88`). The item's `:29366` row, attributed to `gyam7x` and said to be FIXED there, is confirmed gone: no citation remains at or near that line. So the scope is larger than filed, and every site in it is dead rather than merely drifted.
  THREE SITES ASSERT A FACT THAT IS FALSE, WHICH IS A DIFFERENT AND WORSE DEFECT THAN A STALE OFFSET, AND THE ITEM DOES NOT MENTION IT (F-03, F-04). Chasing `apply_run_policy_flags_on_resume`'s citation (`oc_runipd.py:274`) to find what it MEANT surfaced that the sentence containing it is wrong about the code: it says `EXECUTION_SUCCESS_STATES` "includes `substantially-complete`". It does not. `runner_shared.EXECUTION_SUCCESS_STATES` is `{"executed"}`, narrowed by commit `6b94a4d9d` (2026-09-25, `statusvocab`), whose diff shows the literal `{"executed", "substantially-complete"}` being replaced. Two further comments repeat the same dead claim: the `EXECUTE_REPORTING_SUCCESS_STATES` note states "`EXECUTION_SUCCESS_STATES` = {`executed`, `substantially-complete`}" as a premise for why a third set exists, and `reconcile_interrupted`'s docstring makes a BEHAVIORAL claim on it ("`substantially-complete` is also in `EXECUTION_SUCCESS_STATES`, which `edge_satisfied` reads for a non-review item, so recovery can release a dependent that was waiting"). That claim is doubly dead: the member is gone AND `edge_satisfied` no longer reads the set at all for an `executed:` edge, having deleted the in-run shortcut on a maintainer ruling dated 2026-09-19 whose own comment records the measured incident. A reader trusting that docstring believes recovery releases dependents by a mechanism that was deliberately removed.
  WHY THIS IS A `chore` AND NOT A `bug`, ON THE REPOSITORY'S OWN PERCEPTIBILITY TEST, STATED BECAUSE THE FALSE-CLAIM FINDING INVITES ESCALATION. `AGENTS.md` gates `bug` on USER-PERCEPTIBLE impact. Nothing here is read by shipped code: these are comments and docstrings, no module reads them, no runner behavior turns on them, and no user waits on them. The harm is entirely to a FUTURE EDITOR of the runner layer, who is misdirected while changing code that executes plans unattended. That is real but it is not user-perceptible, so the item's `chore` classification is PRESERVED rather than escalated, and no `- Blocks-Release:` is invented (the item carries none). This is deliberately the same judgement the repository applied in reverse to `59t9x5`, where a measured 128ms of operator wait made a correct-output defect a `bug`.
  THE ITEM'S OPEN DESIGN QUESTION IS ALREADY ANSWERED BY THE REPOSITORY, TWICE, AND THIS PLAN DOES NOT RE-OPEN IT (F-05, F-06). `ma8aig` carries forward `gyam7x` OQ-01: "should a mechanical check refuse a `<file>:<line>` citation that points past end of file in tracked source?" It is answered in the affirmative and ALREADY BUILT. `aw check --source-anchors` exists, backed by `spec_citations.stale_spec_anchors`, and its `_resolve_offset` returns exactly the four verdicts the question contemplates: `past_eof`, `in_fence`, `blank_line`, `valid`. It even implements the EXPENSIVE HALF the item calls "not mechanically decidable", by flagging a `blank_line` landing. Its only gap is SUBJECT, not mechanism: it resolves offsets into `.spec.md` files only, so a `<host>.py:<line>` offset is invisible to it. Separately, spec `ipd-structure-and-linting` Section 10.2 already settles the POLICY for authored prose: a citation must anchor on (a) a symbol path or (b) a quoted content string, with a line number permitted only as a trailing convenience, and it states the reason this plan's measurements confirm. So the live question is not "should we check?" but "should the existing checker's subject widen to Python source?", which is a tool change with its own test surface and is NOT in this plan's fence; it is filed as carrier `7jl2bf` (F-05, Deferred). This plan does the thing that needs no decision: make the eight sites conform to the policy that already exists.
- Scope: IN, one file and the comments inside it. (1) RE-ANCHOR all 8 citing sites in `agent_workflows/runner_shared.py` so each names a SYMBOL or a QUOTED CONTENT STRING per spec Section 10.2, deleting the bare offsets rather than refreshing them (a refreshed offset is a new copy of the same expiring reference, and this plan exists because that reference type expired twice in 32 days). (2) CORRECT the three sentences asserting that `EXECUTION_SUCCESS_STATES` contains `substantially-complete`, and the one further asserting that `edge_satisfied` reads that set, naming `6b94a4d9d` and the 2026-09-19 shortcut deletion so the correction carries its own provenance. (3) Where a citation's referent is HISTORICAL (a pre-`pgq326` branch, a pre-`70a2059f` duplication), re-anchor it to the COMMIT plus the symbol the construct lived in, since a historical construct has no current line and a current offset would be a lie about where it is.
  OUT, each for a stated reason: WIDENING `aw check --source-anchors` to resolve Python-source offsets, which is the item's open design question, is a tool-and-test change to a shipped checker and is filed as carrier `7jl2bf` rather than smuggled into a comment fix (F-05). The IDENTICAL defect class in `agent_workflows/agy_runipd.py`, which carries 3 further past-EOF offsets into `oc_runipd.py` (F-06): measured and filed, not fixed, because this plan's fence is one file and sweeping a second host silently doubles the diff a reviewer must check. The 7 TRIVIAL-LANDING citations elsewhere in the tree (`check_engine.py`, `git_commit_helper.py`, `hooks/status_untooled_gate.py`, and three in `tests/`), which resolve to blank or punctuation lines (F-06). DELETED-TEST citations in these same comments, which are backlog `3tov52`'s declared subject and overlap this file. Any behavior change whatsoever: no constant is renamed, no set is widened, and `EXECUTION_SUCCESS_STATES` is left exactly `{"executed"}` because the CODE is right and the PROSE is wrong.
- Scope-Paths: agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: ma8aig
- Set: hostcite
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: fnbtta
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): status set to reviewed

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: `recover_interrupted_step` -> `reconcile_interrupted`), PR-002 (HIGH, fixed: recovered status is now `fail-gate`, E-04 widened to both docstrings), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed: 5 past EOF, not 6), PR-005 (MEDIUM, fixed: two F-07 referents), PR-006 (MEDIUM, fixed: AST-equality no-code-change proof), PR-007 (LOW, fixed: no stash), PR-008 (LOW, fixed). Record: `.aw/records/reviews/20261002-hostcite-01-fnbtta-re-anchor-runner-shared-s-host-file-line-citations-by-symbol.review.md`.
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `ma8aig` in an isolated lane. EVERY row of the item's table was re-resolved against the host files at HEAD `6e299712f` rather than transcribed, and the item needed correction on three counts. FIRST, IT UNDERCOUNTS (F-01): the real population is 15 offsets across 8 citing sites, of which 6 are PAST EOF, because the item counted the range `6993-7031` as one offset when both endpoints are independently dead and did not enumerate the three-offset agy half of `verdict_refusal_text` nor the `announce_run_order` pair. SECOND, THE ITEM'S OWN SNAPSHOT IS ALREADY STALE: it records `oc_runipd.py` at 5278 and `agy_runipd.py` at 4162 on 2026-09-30; they are now 5487 and 4166. The defect demonstrated itself inside the record that filed it, which is the strongest available argument for deleting offsets rather than refreshing them. THIRD, AND THIS IS THE FINDING THAT MOST CHANGES THE WORK, THE ITEM MISSES A WORSE DEFECT CLASS SITTING IN THE SAME SENTENCES (F-02, F-03): three comments assert `EXECUTION_SUCCESS_STATES` "includes `substantially-complete`", which commit `6b94a4d9d` (2026-09-25) made false by narrowing it to `{"executed"}`, and `recover_interrupted_step`'s docstring builds a BEHAVIORAL claim on that dead member, saying `edge_satisfied` reads the set so recovery can release a waiting dependent. `edge_satisfied` deleted that read on a maintainer ruling dated 2026-09-19. A stale offset wastes a reader's time; a false claim about a status set makes a runner-layer editor reason from a premise the code refutes, so the plan treats these as the primary work and the offsets as the occasion. FOURTH, THE ITEM'S OPEN DESIGN QUESTION IS ALREADY ANSWERED AND ALREADY BUILT (F-05): `aw check --source-anchors` exists, backed by `spec_citations._resolve_offset`, and returns `past_eof`/`in_fence`/`blank_line`/`valid` - including the "expensive half" the item calls mechanically undecidable. Its only gap is that it resolves into `.spec.md` only, so widening its SUBJECT to Python source is the live question; filed as a carrier rather than done here, because it is a tool change with its own test surface. Classification `chore` is PRESERVED on the repository's perceptibility test despite the false-claim finding: no shipped path reads a comment, so the harm is to a future editor and not to a user.
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make every host-file citation in `agent_workflows/runner_shared.py` point at something that survives the next commit, by replacing 15 bare offsets with symbol or quoted-string anchors, and correct the four sentences this measurement proved are asserting a status-set membership and a runner behavior that the code no longer has.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-resolve every `<host>.py:<line>` offset in `agent_workflows/runner_shared.py` against the host files at the EXECUTING HEAD, and record the transcript, so every later item edits on current fact rather than on this plan's authoring snapshot.
  - Depends on: none
  - Expected outcome: one pasted transcript, produced by PARSING (walk the file, regex each citation, open the named host, resolve the offset) and not by reading, printing for each offset either `PAST_EOF` or the stripped text of the line it lands on, plus the two host line counts. It must reproduce the F-01 census: 15 offsets across 8 citing sites, 5 of them past EOF (`oc_runipd.py` 6993, 7031, 6645, 6647, 6649), `oc_runipd.py` at 5487 lines and `agy_runipd.py` at 4166 at authoring (5494 and 4200 at review HEAD `2f22724d1`, which is the expected drift, not a stop condition).
    EXPECT THE NUMBERS TO HAVE MOVED, AND DO NOT TREAT THAT AS A STOP CONDITION. This is the one plan in which a changed measurement CONFIRMS rather than invalidates the premise: the hosts gained 209 and 4 lines in the 2 days between the item's filing and this authoring. So a differing line count or a different landing line is EXPECTED and the work proceeds. What WOULD be a stop condition is a citation having VANISHED (another agent fixed it, as `gyam7x` did for the `:29366` row) or a new one having appeared: in either case reconcile the per-site list in F-01 before editing, because a site this plan does not know about will not be fixed and a site already fixed must not be fixed twice.
  - Execution state: performed

- [x] E-02 Independently re-verify the three false `EXECUTION_SUCCESS_STATES` claims and the one false `edge_satisfied` claim by INSPECTING THE RUNTIME OBJECT and the function body, not by reading the comments, and record the transcript.
  - Depends on: none
  - Expected outcome: a pasted transcript showing (a) `runner_shared.EXECUTION_SUCCESS_STATES` imported and printed, demonstrating `{'executed'}` and that `'substantially-complete' not in` it; (b) the same for both host re-exports (`oc_runipd.EXECUTION_SUCCESS_STATES`, `agy_runipd.EXECUTION_SUCCESS_STATES`), since the comments claim a property of the set the hosts expose; (c) `git log -1 -S'EXECUTION_SUCCESS_STATES = {"executed"}'` attributing the narrowing to `6b94a4d9d` with its date, plus the diff line showing `{"executed", "substantially-complete"}` being replaced; and (d) a count of `EXECUTION_SUCCESS_STATES` occurrences inside `edge_satisfied`'s body, demonstrating that its ONE mention is inside the comment explaining the DELETED shortcut and that no live statement reads the set.
    IF ANY OF THESE NOW HOLDS, STOP AND RECONCILE. If `substantially-complete` has been re-admitted to the set, or if `edge_satisfied` has regained a read of it, then the comments are TRUE and E-04 must not "correct" them into falsehood. This item exists to make that failure impossible rather than unlikely, because its edit is the one place this plan could actively introduce a wrong claim.
  - Execution state: performed

### Task group 2: correct what is false

- [x] E-03 Correct the three sentences in `agent_workflows/runner_shared.py` asserting that `EXECUTION_SUCCESS_STATES` contains `substantially-complete`, and re-anchor the one bare offset inside them.
  - Depends on: E-02
  - Expected outcome: three sites say something true, each carrying its own provenance so the next reader need not re-derive it. (i) `apply_run_policy_flags_on_resume`'s `SET_RETIREMENT_DONE_STATUS` note currently reads "DELIBERATELY NOT `EXECUTION_SUCCESS_STATES`. That set (`oc_runipd.py:274`) includes `substantially-complete` for DEPENDENCY-EDGE purposes": drop the bare offset, name the constant's home by SYMBOL (`runner_shared.EXECUTION_SUCCESS_STATES`, which both hosts re-export), and state the membership as it now is. The sentence's POINT survives the correction and must be kept: this predicate is deliberately a different, narrower authority and does not consult the dependency bar. (ii) the `EXECUTE_REPORTING_SUCCESS_STATES` note's premise "`EXECUTION_SUCCESS_STATES` = {`executed`, `substantially-complete`} is the DEPENDENCY bar" must stop stating a membership that `6b94a4d9d` removed, and so must its follow-on clause "for which `substantially-complete` legitimately counts". Preserve the note's actual argument, that the DEPENDENCY question and the REPORTING question are different and must not be collapsed, but do NOT claim that argument is independent of the dead member: its MEASURED illustration (substituting the dependency bar at the exit-code site would silently admit `substantially-complete`) was true only under the two-member set. Restate it on the sets as they now are, verified in E-02: `EXECUTION_SUCCESS_STATES` is `{"executed"}` and `EXECUTE_REPORTING_SUCCESS_STATES` is `SUCCESS_STATES - {"reviewed"}` = `{"executed", "approved"}`, so the two still differ (by `approved`) and are still not interchangeable; mark the `substantially-complete` measurement as HISTORICAL (pre-`6b94a4d9d`) rather than deleting it. The deleted-test citation inside that note (`tests/test_rununify_run_queue.py::TheExitCodeReflectsTheRealOutcome::...`, removed by `19313eed`) is `3tov52`'s class: leave its wording alone. (iii) name `6b94a4d9d` (`statusvocab`, 2026-09-25) as the narrowing commit at least once, so a reader who finds an older plan or comment asserting the two-member set can date the change instead of guessing.
    DO NOT TOUCH `EXECUTION_SUCCESS_STATES` ITSELF, in either direction. The CODE is correct and the PROSE is wrong; widening the set to match the comments would be a behavior change to the dependency bar, which decides whether a dependent plan is dispatched, and `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests` pins the cross-host equality this plan has no mandate to disturb.
  - Execution state: performed

- [x] E-04 Correct `reconcile_interrupted`'s docstring, which asserts a RELEASE MECHANISM that two separate changes removed, plus the stale recovered-status token it and `outcome_precedence_disposition`'s docstring name.
  - Depends on: E-02
  - Expected outcome: the sentence "`substantially-complete` is also in `EXECUTION_SUCCESS_STATES`, which `edge_satisfied` reads for a non-review item, so recovery can release a dependent that was waiting" no longer claims either half, because BOTH are false: the member was removed by `6b94a4d9d`, and `edge_satisfied`'s `executed:` branch deleted its in-run status shortcut entirely on the maintainer ruling of 2026-09-19 (that branch's own comment records the ruling and the measured incident behind it, naming run `run-20260919T194413Z-2056285`). State instead what the code now does, i.e. that the `executed:` edge is answered from the plan's terminal directory ON DISK and not from in-run status, and point at `edge_satisfied`'s branch by symbol so a reader lands on that explanation.
    THE SURROUNDING PARAGRAPH'S RETRY CLAIM IS TRUE IN SUBSTANCE AND MUST SURVIVE, BUT ITS STATUS TOKEN IS STALE TOO. The docstring says a step recovered to `substantially-complete` leaves the still-`interrupted` set that `requeue_interrupted` flips back to `queued`, so it is NOT retried, attributed to maintainer decision `fduoj4` OQ-03 (2026-09-10). The mechanism still holds, but since `6b94a4d9d` the recovered status is the CANONICAL token: `outcome_precedence_disposition(None, {"disposition": "substantially-complete"})` and `(None, {"disposition": "executed"})` both return `"fail-gate"` (measured at review HEAD `2f22724d1`; `TERMINAL_STATUS_ALIASES["substantially-complete"] == "fail-gate"`). So name the recovered status as `fail-gate` (the canonical form of the legacy `substantially-complete`), and correct the same docstring's SELF-CLAIM DOWNGRADE bullet ("a recorded `executed` becomes `substantially-complete`") and `outcome_precedence_disposition`'s rung 2 ("DOWNGRADED to `substantially-complete`") the same way, since both describe the return value of a function whose code returns `"fail-gate"`. The sentence "Both effects are intended: work proven to have finished is not redone, and dependents waiting on it may proceed" must not keep asserting the second effect as current; record that the maintainer intended it at the time and that it no longer occurs (a `fail-gate` item's plan is still in `pending/`, so an `executed:` edge on it is unmet on disk). Keep the `fduoj4` OQ-03 attribution and the declined-alternative sentence intact: this docstring records a maintainer ruling and over-editing it would destroy the record the ruling lives in. Do NOT edit the `ydbhfd` measurement ("`outcomes/02-97df1z.json` recorded `substantially-complete`"): that is a true historical observation of what a file contained.
  - Execution state: performed

### Task group 3: delete the expiring references

- [x] E-05 Re-anchor the remaining bare offsets in `agent_workflows/runner_shared.py` so every citation names a symbol, a quoted content string, or a commit, and no bare `<host>.py:<line>` offset survives.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: zero bare host offsets remain in the file, each site re-anchored to the construct the prose actually means. The referents were located for every site during authoring (F-07), so this is a transcription of known targets and not a search: the `ORCH_DISPATCH_*` comment block's "pre-`pgq326` dispatch branch" (the module-level block directly after `enforce_spec_edit_ack_gate`, headed "THE THREE-WAY OUTCOME, WHICH REPLACES ONE `else`") cites a HISTORICAL branch, so anchor it to merge commit `394238996` (which replaced it) plus the symbol it lived in: `oc_runipd.run_queue`'s `if runnable.get("action") == "orchestrate":` block at `394238996^`, whose `else` arm after the `_set_children_all_executed(...)` / `finalize_orchestrator(...)` test set `runnable["status"] = "dependency-blocked"` (`_set_children_all_executed` is the predicate that block CALLED, not the function the `else` lived in), keeping the quoted `else:` block already shown there as the content anchor; `verdict_refusal_text`'s six-offset parenthetical about per-host duplication is likewise historical, so anchor it to commit `70a2059f` (2026-09-18, "deduplicate execute_item into runner_shared.execute_item_core") plus `execute_item_core`'s `v_outcome_file` block, which the same sentence already names; `HostLabels.shell_tool` and `build_verifier_prompt` both cite `agy_runipd.py:503` for where `run_command` is mapped, which is now `agy_runipd._AGY_TOOL_PREFIX_KIND`'s `"run_command"` key; the spec-edit-visibility comment block's (directly after `announce_run_order`) "re-export form documented at `agy_runipd.py:84-88`" means `agy_runipd`'s note "The `as <same-name>` form marks these as an intentional RE-EXPORT", the one preceding the `from agent_workflows.runner_shared import (... as ...)` seam that imports `spec_impacts_for_queue as spec_impacts_for_queue`, so cite it by that quoted content. Do NOT anchor it to the `# noqa: F401 - a DELIBERATE re-export` line: that line documents the unrelated `_read_id` alias and carries a deleted-test citation owned by `3tov52`; and `queue_plan_path`'s `(oc_runipd.py:2979, agy_runipd.py:2094)` is evidence for where each host freezes the plan location, which is the `"configured_file"` key written by `runner_shared.initialize_run_core`'s queue append, the one builder both hosts now call.
    A TRAILING OFFSET APPENDED TO A SYMBOL IS PERMITTED BY SPEC SECTION 10.2 AND IS STILL THE WRONG CHOICE HERE. The spec allows (c) a line number as a convenience on top of (a) or (b). Do not take it: this file's offsets into these two hosts have now expired twice in 32 days (5 of 15 past EOF, and the filing record's own line counts stale within 2 days), so re-adding one creates a reference that will be wrong again before anyone reads it, and the next agent cannot distinguish a freshly-wrong offset from a never-checked one. Anchor by symbol or quoted string ALONE.
    DO NOT WIDEN INTO THE NEIGHBOURING DEFECTS, all of which are measured in F-06 and filed. Leave `agy_runipd.py`'s own three past-EOF citations into `oc_runipd.py` alone, leave the trivial-landing citations in `check_engine.py`, `git_commit_helper.py`, `hooks/status_untooled_gate.py` and the three test files alone, and leave deleted-test citations to `3tov52`. The declared scope is one file.
  - Execution state: performed

### Task group 4: prove nothing else moved

- [x] E-06 Run the bare suite and both existing citation checkers against the edited tree, and capture a pre-change baseline in the SAME session to compare against.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: a pre-change and a post-change run of `python3 -m pytest`, BARE (no `-n0`, no second `-q`, no `-p no:randomly`), plus `aw check --source-citations` and `aw check --source-anchors` with their exit codes, all captured as actual output. The comparison is BY FAILURE NAME and not by count, because the tree is not reliably green here.
    THE BASELINE MUST BE TAKEN IN THE SAME SESSION, BEFORE the E-03/E-04/E-05 edits (do NOT produce it with `git stash` or any reset: this may be a shared checkout and `AGENTS.md` forbids stashing a co-worker's work), because a baseline from this plan's authoring would be a different HEAD. This plan changes only comments, so the expected result is an IDENTICAL failure set; ANY new failure name indicates an accidental code edit and must block rather than be explained away. Note that `aw check --source-anchors` is EXPECTED to still report findings afterwards (it reports `blank_line` spec-anchor offsets, a different citation class this plan does not touch), so its exit code is recorded as a comparison against the pre-change run rather than as a pass/fail gate.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan is by symbol, by quoted string, or by commit hash; this plan deliberately carries no bare offsets, since its subject is the harm bare offsets cause.
- Spec `ipd-structure-and-linting` Section 10.2 states the failure mode this plan measured, in advance and in the repository's own words: "A drifted line number almost never points at nothing; it points at OTHER, VALID, PLAUSIBLE-LOOKING code." It also records a counter-measurement worth carrying, that scanning the plan corpus for PROVABLY dead citations "found almost none". This file is the opposite case (5 of 15 offsets past EOF), because the two hosts shed thousands of lines to `runner_shared` during `rununify`/`cnwy8g`, so a sweep here is cheap in a way a corpus sweep is not.
- Section 10.2 also names THE ONE LEGITIMATE EXCEPTION, which this plan checked against every site before proposing an edit: a citation "whose SUBJECT IS THE LINE ITSELF" (a lint position, a traceback frame, a quoted diff hunk) is correctly a line number. No site in scope qualifies; all 8 use the offset as a POINTER to a construct, which is the prohibited form.
- THIS PLAN ITSELF TRIPS `IPD-C801` REPEATEDLY (13 advisories at review HEAD `2f22724d1`; the count is context, not a bar), AND EVERY ONE IS THAT EXCEPTION RATHER THAN A DEFECT TO FIX. `aw ipd lint` reports advisories on `oc_runipd.py:6993-7031`, `oc_runipd.py:274`, `agy_runipd.py:3696`, `agy_runipd.py:84-88`, `agy_runipd.py:2094` and `status_set.py:504` as they appear in the Concern, Scope and Findings. Those offsets are the SUBJECT OF THE REPORT, i.e. the broken citations being inventoried, so quoting them is reporting a fact and not pointing at a construct; rewriting them as symbols would destroy the evidence and make F-01 unverifiable. They are advisory-only and do not change the conformance disposition (the plan lints conforming). THIS IS ALSO A LIVE DATA POINT FOR CARRIER `7jl2bf`: a report ABOUT bad citations is the archetypal false positive any such checker must tolerate, and it is the reason Section 10.2 keeps `IPD-C801` advisory rather than gating.
- A mechanical past-EOF checker already exists and is reachable as `aw check --source-anchors`, backed by `spec_citations.stale_spec_anchors` and `spec_citations._resolve_offset`, which returns `past_eof`, `in_fence`, `blank_line`, or `valid`. It resolves offsets into `.spec.md` files only. This is why the item's open design question needs no new decision, only a subject widening (filed, not done here).
- GUIDING_PRINCIPLES P16 and `AGENTS.md` forbid tests that read production source with `inspect`/`ast`/regex or that pin comment text. THIS PLAN THEREFORE ADDS NO TEST, and that is a deliberate consequence rather than an omission: its deliverable is comment prose, and the only test that could pin comment prose is precisely the code-pinning test the repository prohibits. The durable guard is the EXISTING checker widened under its own carrier, which asserts a resolvable-citation property rather than a text match.
- `AGENTS.md` gates `bug` on USER-PERCEPTIBLE impact, which is why a false claim in a comment stays `chore`: no shipped path reads it.
- The suite is run BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **EVERY OFFSET IS WRONG, AND THE ITEM UNDERCOUNTS THE POPULATION.** Re-resolved at HEAD `6e299712f`: 15 offsets across 8 citing sites in `runner_shared.py`, **5 PAST EOF** (`oc_runipd.py` at 6993, 7031, 6645, 6647, 6649 against a 5487-line file) and 10 resolving to something unrelated to the prose: `oc_runipd.py:274` lands on `classify_drain_block as classify_drain_block,` (an import alias, in a sentence about a status set), `oc_runipd.py:2979` on `),`, `agy_runipd.py:503` on `peer_drivers as peer_drivers,` (cited TWICE, by `HostLabels.shell_tool` and `build_verifier_prompt`, both for where a SHELL TOOL is mapped), `agy_runipd.py:84` on `install_exit_signal_handler,`, `agy_runipd.py:2094` on `announce_run_order_fn=announce_run_order,`, and `agy_runipd.py:3696/3698/3700` on fragments of an unrelated `--no-self-finalize` argparse block. The item lists 7 resolutions and scopes to 4 fixes; the real figure is 15 offsets / 8 sites, because a range counted as one offset has two dead endpoints and the agy halves of two citations went unenumerated. The item's `:29366` row is confirmed already fixed by `gyam7x` as it predicted | the parse-and-resolve transcript printing each `runner_shared:<line> -> <host>:<offset>` with `PAST_EOF` or the landed line text, plus `wc -l` on both hosts |
| F-02 | **THE ITEM'S SNAPSHOT WENT STALE IN TWO DAYS, WHICH IS THE ARGUMENT FOR DELETING OFFSETS RATHER THAN REFRESHING THEM.** `ma8aig` records, as measured fact on 2026-09-30 at HEAD `f2326296`, that "`oc_runipd.py` is 5278 lines and `agy_runipd.py` is 4162". Verified at that commit: exactly 5278 and 4162. At this HEAD they are **5487 and 4166**, i.e. +209 and +4 in 2 days. So the record filed TO REPORT expiring references contains an expired measurement of its own. A plan that refreshed the 15 offsets would be shipping 15 references with the same two-day half-life, and a future reader could not tell a freshly-wrong offset from an unchecked one | `git show f2326296:agent_workflows/oc_runipd.py \| wc -l` -> 5278 and the agy equivalent -> 4162, against `wc -l` at HEAD -> 5487 and 4166 |
| F-03 | **THREE COMMENTS ASSERT A SET MEMBERSHIP THE CODE DOES NOT HAVE, WHICH THE ITEM DOES NOT MENTION AND WHICH IS A WORSE DEFECT THAN A DEAD OFFSET.** `runner_shared.EXECUTION_SUCCESS_STATES` is `{"executed"}`, printed from the imported module, and both hosts re-export that same object. Three comments say otherwise: `apply_run_policy_flags_on_resume`'s note ("That set (`oc_runipd.py:274`) includes `substantially-complete` for DEPENDENCY-EDGE purposes"), the `EXECUTE_REPORTING_SUCCESS_STATES` note ("`EXECUTION_SUCCESS_STATES` = {`executed`, `substantially-complete`} is the DEPENDENCY bar"), and `reconcile_interrupted`'s docstring. The narrowing is attributable: commit `6b94a4d9d` (2026-09-25, "statusvocab: rename the terminal status vocabulary so a label names its refusing authority") replaced the literal `{"executed", "substantially-complete"}` with `{"executed"}`. A dead offset costs a reader one search; a false claim about the DEPENDENCY BAR misleads an editor about which items a runner will dispatch | `python3 -c` printing the set and `'substantially-complete' in` it -> `False`; `git log -1 -S'EXECUTION_SUCCESS_STATES = {"executed"}'` -> `6b94a4d9d 2026-09-25`; that commit's diff line `-EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}` |
| F-04 | **ONE OF THE THREE IS A BEHAVIORAL CLAIM, AND BOTH ITS HALVES ARE DEAD.** `reconcile_interrupted`'s docstring states "`substantially-complete` is also in `EXECUTION_SUCCESS_STATES`, which `edge_satisfied` reads for a non-review item, so recovery can release a dependent that was waiting". The member is gone (F-03) AND the read is gone: `edge_satisfied` spans 178 lines and mentions `EXECUTION_SUCCESS_STATES` exactly ONCE, inside the comment explaining why the in-run shortcut was DELETED ("THE DISK IS THE ONLY AUTHORITY, AND THE IN-RUN SHORTCUT THAT USED TO SIT HERE IS GONE (maintainer ruling 2026-09-19: one check, not gates in depth). It read the dependency's IN-MEMORY run status and accepted any member of `EXECUTION_SUCCESS_STATES`, which admits `substantially-complete`"). That comment also records the measured incident, run `run-20260919T194413Z-2056285`, costing "2h 10m and $55.02 for nothing integrated". So the docstring promises a release mechanism whose removal is documented thirty-odd lines away, and an editor trusting it would reason about dependency release through a path that no longer exists | the occurrence count of `EXECUTION_SUCCESS_STATES` and `success_states` within `edge_satisfied`'s body bounds (1 and 0 respectively), with the single hit's line text; the quoted deletion comment and its ruling date |
| F-05 | **THE ITEM'S OPEN DESIGN QUESTION IS ALREADY ANSWERED AND THE MECHANISM IS ALREADY SHIPPED, INCLUDING THE HALF THE ITEM CALLS UNDECIDABLE.** `ma8aig` carries `gyam7x` OQ-01 ("should a mechanical check refuse a `<file>:<line>` citation that points past end of file in tracked source?") and argues the cheap half is decidable while "the expensive half is not mechanically decidable at all: the two citations that DO resolve land on ')' and '#', which ... no length check can see". Measured: `aw check --source-anchors` already exists as a documented flag, and `spec_citations._resolve_offset` already returns FOUR verdicts, `past_eof`, `in_fence`, `blank_line`, and `valid`. It therefore implements both halves, the `blank_line` arm being exactly the "expensive" case. Run at this HEAD it emits 10 findings, several of them `blank_line` landings in `runner_shared.py` itself. Its ONLY gap is subject: it resolves offsets into `.spec.md` files via `specs.discover_specs`, so a `<host>.py:<line>` offset is invisible. So no decision is owed; a subject widening is | `aw check --source-anchors` help text and its 10-finding output including `runner_shared.py:... spec 25kzda :1007 -> blank_line`; `_resolve_offset`'s four return verdicts; `check_source_citations`, which scans `.py` for dangling FILENAME citations and reports 0, confirming no existing checker resolves a `.py` OFFSET |
| F-06 | **THE SAME DEFECT CLASS LIVES OUTSIDE THIS FILE, MEASURED SO THE FENCE IS A CHOICE AND NOT AN OVERSIGHT.** A tree-wide resolve of every `<file>.py:<line>` citation under `agent_workflows/`, `tools/` and `tests/` finds 51 resolvable offsets in 19 files, of which 12 are defective: 5 past EOF and 7 landing on blank or punctuation-only lines. Three past-EOF cases are in `agy_runipd.py` citing `oc_runipd.py` at 8766, 8645 and 8834 (a 5487-line file) in comments about `register_signal_report` refreshes; the trivial landings are in `check_engine.py`, `git_commit_helper.py`, `hooks/status_untooled_gate.py` (each citing `status_set.py:504`, a blank line) and three test files. This plan fixes the 8 sites in its declared file only. The adjacent `3tov52` already owns DELETED-TEST citations in these same two modules, and `rdl9lh` (a `bug` with `Blocks-Release: next`) records the same class for a docstring citing a deleted guard test, noting it is "a KNOWN CLASS rather than an isolated instance" | the tree-wide resolve transcript listing all 12 defective citations with their verdicts |
| F-07 | **EVERY REPLACEMENT TARGET WAS LOCATED DURING AUTHORING, SO E-05 IS TRANSCRIPTION AND NOT A SEARCH.** This matters because a past-EOF offset says the construct moved but not where, which is the item's stated reason the sites need individual work. Found: the pre-`pgq326` dispatch `else` branch lives in commit `394238996`'s parent, in `oc_runipd.run_queue`'s `if runnable.get("action") == "orchestrate"` block, which calls `_set_children_all_executed` and whose `else` arm sets `runnable["status"] = "dependency-blocked"` exactly as the comment quotes; the per-host verdict triple was unified by commit `70a2059f` ("deduplicate execute_item into runner_shared.execute_item_core", 2026-09-18) into `execute_item_core`'s `v_outcome_file` block, which the citing sentence already names; `run_command` is mapped in `agy_runipd._AGY_TOOL_PREFIX_KIND` (`"run_command": "bash"`), not at `:503` which is a `peer_drivers` import alias; the agy re-export form is documented by that module's quoted note "The `as <same-name>` form marks these as an intentional RE-EXPORT" (corrected at review: NOT the `# noqa: F401 - a DELIBERATE re-export` line, which is the unrelated `_read_id` alias); and both hosts freeze the plan location through `runner_shared.initialize_run_core`'s queue append writing `"configured_file"`, so the two-host citation now has ONE shared referent | the located symbols, each confirmed present at HEAD; `git show 394238996^:agent_workflows/oc_runipd.py` showing the quoted `else` arm; `git log -1 70a2059f` |
| F-08 | **NO TEST CAN GUARD THIS WITHOUT VIOLATING P16, WHICH IS WHY THIS PLAN SHIPS NO TEST AND SAYS SO.** The deliverable is comment prose. A test asserting that a particular comment says a particular thing is precisely the code-pinning test `AGENTS.md` and GUIDING_PRINCIPLES P16 prohibit ("NEVER write or restore tests that read production source code using `inspect`, `ast`, regex, or substring search"; "NEVER assert that specific text, docstrings, or comment banners remain unchanged"). The repository has already paid for ignoring this: `rdl9lh`, `3tov52` and `tvv8gg` all exist because comments cited guard tests that commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted as code pins. Validation is therefore a MEASUREMENT of the file (zero bare offsets remain, the corrected claims match the runtime objects) plus the unchanged suite, and the durable guard is the existing checker widened under F-05's carrier | P16 and the `AGENTS.md` prohibition quoted; the three in-repo items caused by comments citing deleted pins; `19313eed`'s subject line |

## Proposed changes (ordered, validatable)

1. E-01 re-resolves all 15 offsets at the executing HEAD and reconciles the per-site list, stopping only if a site has vanished or appeared.
2. E-02 re-verifies the four false claims against the runtime objects and `edge_satisfied`'s body, stopping if any has become true.
3. E-03 corrects the three `EXECUTION_SUCCESS_STATES` membership claims, naming `6b94a4d9d` as the narrowing commit, and re-anchors the offset inside them.
4. E-04 corrects `reconcile_interrupted`'s dead release-mechanism claim while preserving the `fduoj4` OQ-03 retry reasoning the same paragraph records.
5. E-05 re-anchors the remaining sites to the symbols, quoted strings and commits located in F-07, leaving zero bare host offsets in the file.

## Deferred / out of scope (with reason)

- WIDENING `aw check --source-anchors` (or `check_source_citations`) TO RESOLVE `<file>.py:<line>` OFFSETS IN TRACKED SOURCE, which is the item's carried open design question. Not done here because the question is already answered in principle (F-05: the checker exists and implements both the past-EOF and the blank-line half) and what remains is a change to a shipped checker's SUBJECT, with its own behavioral test surface and its own false-positive policy to settle. Folding a tool change into a comment-correction plan would also make the diff unreviewable against a one-file declared scope. The measured sample this plan produced (12 defective citations tree-wide, 5 past EOF, 7 trivial landings) is exactly the evidence the item asked to have in hand before deciding, and it is recorded in F-01/F-06 for that carrier to consume.
  - Carrier: 7jl2bf
- THE THREE PAST-EOF CITATIONS IN `agent_workflows/agy_runipd.py` pointing into `oc_runipd.py` at 8766, 8645 and 8834 (F-06), plus the 7 trivial-landing citations in `check_engine.py`, `git_commit_helper.py`, `hooks/status_untooled_gate.py` and three test files. Measured and filed rather than swept: this plan declares one file, and widening to a second host would double a reviewer's verification burden for sites whose referents need their own location work.
  - Carrier: 7jl2bf
- DELETED-TEST CITATIONS in the comments of these same modules (for example a comment naming `tests/test_runner_refork_guard.py`, deleted in `19313eed`). Already owned, and overlapping this file. Deliberately not touched even where E-05 edits a nearby sentence, so the two plans cannot conflict over the same clause.
  - Carrier: 3tov52
- ANY CHANGE TO `EXECUTION_SUCCESS_STATES` ITSELF, in either direction.
  - Carrier-Declined: NOTHING IS OWED, because the code is RIGHT and the prose is WRONG. The set was narrowed deliberately by `6b94a4d9d` and the narrowing is cross-host pinned by `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests`. Filing a carrier would assert that a deliberate, tested, dated decision is a defect, for which this plan has no evidence; the only defect measured is three comments that did not follow it.
- THE `blank_line` SPEC-ANCHOR FINDINGS `aw check --source-anchors` ALREADY REPORTS IN THIS FILE (offsets into spec `25kzda`, 10 findings tree-wide).
  - Carrier-Declined: NOTHING IS OWED BY THIS PLAN and no carrier is filed, because these are not unreported: a shipped, documented checker reports them on demand, by design, as `info`. They are a different citation class (offsets into a `.spec.md`, not into a host `.py`), they are outside this plan's subject, and inventing a carrier for findings a checker already surfaces would duplicate an obligation the tool already discharges. Named only so a reviewer running the checker against this file is not surprised to see it still report findings after this plan executes.

## Scope check

- Over-scope: none. One path is declared, `agent_workflows/runner_shared.py`, and every E-item edits only comments and docstrings inside it. No constant, signature, or branch changes; no test is added (F-08 states why, and why that is a consequence of P16 rather than a gap); the three neighbouring defect populations found while measuring became F-06 plus carriers rather than scope creep.
- Under-scope: after this plan the identical defect class REMAINS LIVE outside the declared file, specifically 3 past-EOF citations in `agy_runipd.py` and 7 trivial-landing citations in four other modules and three test files (F-06), and nothing MECHANICAL will prevent the 8 corrected sites from being re-broken by a future bare offset, because the guard that would catch it is the checker widening deferred to `7jl2bf`. The plan reduces a measured 15-offset defect to 0 in one file and improves nothing elsewhere; a reader should not take a passing `aw check` afterwards as evidence that host-file citations are now checked, because they are not.

## Required tests / validation

No new test is authored, and F-08 records why that is forced by GUIDING_PRINCIPLES P16 rather than chosen for convenience: the deliverable is comment prose, and the only test that could pin comment prose is the code-pinning test the repository prohibits and has already had to delete across this very subject area (`19313eed`). Validation is therefore (a) a MEASUREMENT of the edited file proving zero bare host offsets survive and every re-anchored symbol resolves, (b) a MEASUREMENT proving each corrected claim now agrees with the runtime object it describes, and (c) the bare suite plus the two existing citation checkers, run to show nothing regressed. Run the suite BARE as `python3 -m pytest`.

## Spec / documentation sync

N/A. No spec is amended and `- Scope-Paths:` declares no `.spec.md`, deliberately: spec `ipd-structure-and-linting` Section 10.2 ALREADY states the citation-anchor contract this plan conforms to, and its scope (authored IPD prose, advisory `IPD-C801`, date-gated) is correct as written. This plan brings source comments into line with a policy that already exists rather than changing the policy. Extending that contract to Python source comments, and with it any spec text, belongs to the checker-widening carrier `7jl2bf`, where the enforcement decision and the spec sentence would land together.

## Open questions

### OQ-01: Should E-05 preserve a trailing line number alongside each new symbol anchor, which spec Section 10.2 form (c) permits?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. Section 10.2 permits a line number "only as a trailing convenience APPENDED to (a) or (b)", so a symbol-plus-offset citation would be conforming. It is still refused here on this file's measured history: 5 of 15 offsets into these two hosts are past EOF, and the filing record's own line counts for the same two files went stale within 2 days (F-01, F-02). An offset with that half-life is not a convenience, and a FRESHLY WRONG offset is worse than none, because a later reader cannot distinguish it from one nobody checked. E-05 therefore anchors by symbol or quoted string alone.

### OQ-02: Is correcting the three `EXECUTION_SUCCESS_STATES` claims (E-03, E-04) in scope for an item filed about stale line citations?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, and the alternative is worse. The false claims were not sought out; they are the CONTENT of the very sentences carrying the offsets in scope, and they surfaced only because locating each offset's real referent required reading what the sentence asserts (F-03, F-04). Re-anchoring a citation inside a sentence while leaving the sentence asserting a set membership the code refutes would ship a precise pointer to a false statement, which is a worse outcome than the dead offset and would make the plan's own edit misleading. The correction is also strictly narrower than the alternative reading of scope: no code changes, and `EXECUTION_SUCCESS_STATES` is explicitly left alone (see the declined carrier). If a reviewer judges otherwise, the honest split is to keep E-03/E-04 and drop E-05, not the reverse, since the false claims are the higher-harm half.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: the pasted resolve transcript from E-01, showing for EVERY citation in `runner_shared.py` its target host, offset, and resolution, together with both host line counts at the executing HEAD. It must enumerate at least the 8 citing sites F-01 names and must independently reproduce the past-EOF count. A transcript that merely says "measured, matches" is NOT acceptable: the per-offset lines must be present, because E-05's correctness is judged against this list. State explicitly whether the census differed from F-01's 15-offset / 8-site / 5-past-EOF figure and, if so, which site moved and how the per-site list was reconciled.
  - Observed evidence:
    Resolved at executing HEAD `acd237f78`:
    ```
    Host line counts at HEAD:
      agent_workflows/oc_runipd.py: 5516 lines
      agent_workflows/agy_runipd.py: 4203 lines

    Found 9 citation occurrences across 8 citing sites:
    Site 1 (runner_shared.py:17563): `oc_runipd.py:274`
      Context: #: DELIBERATELY NOT `EXECUTION_SUCCESS_STATES`. That set (`oc_runipd.py:274`) includes
        Offset 274 -> Line 274: from agent_workflows.runner_shared import (

    Site 2 (runner_shared.py:20182): `oc_runipd.py:6993-7031`
      Context: # The pre-`pgq326` dispatch branch (`oc_runipd.py:6993-7031`) wrote ONE status on ANY failure:
        Offset 6993 -> PAST_EOF (6993 > 5516)
        Offset 7031 -> PAST_EOF (7031 > 5516)

    Site 3 (runner_shared.py:22927): `oc_runipd.py:6645/6647/6649`
      Context: # still live on this tree (previously duplicated per host at `oc_runipd.py:6645/6647/6649` and
        Offset 6645 -> PAST_EOF (6645 > 5516)
        Offset 6647 -> PAST_EOF (6647 > 5516)
        Offset 6649 -> PAST_EOF (6649 > 5516)

    Site 4 (runner_shared.py:22928): `agy_runipd.py:3696/3698/3700`
      Context: # `agy_runipd.py:3696/3698/3700`, unified into `runner_shared.execute_item_core` by commit `70a2059f`):
        Offset 3696 -> Line 3696: help="Auto-approve all tool permission requests in agy (default: True)",
        Offset 3698 -> Line 3698: start.add_argument(
        Offset 3700 -> Line 3700: dest="dangerously_skip_permissions",

    Site 5 (runner_shared.py:26779): `agy_runipd.py:503`
      Context: #: Antigravity (mapped at `agy_runipd.py:503`), or None where the host names no tool. Consumed by
        Offset 503 -> Line 503: peer_drivers as peer_drivers,

    Site 6 (runner_shared.py:28214): `agy_runipd.py:503`
      Context: (mapped at `agy_runipd.py:503`) and names nothing an OpenCode agent can call, so this could
        Offset 503 -> Line 503: peer_drivers as peer_drivers,

    Site 7 (runner_shared.py:39246): `agy_runipd.py:84-88`
      Context: # re-export form documented at `agy_runipd.py:84-88`), for the reason that module records: a second
        Offset 84 -> Line 84: install_exit_signal_handler,
        Offset 88 -> Line 88: # oc-to-agy coupling that backlog `cnwy8g` tracks. Same object in both hosts, asserted by

    Site 8 (runner_shared.py:39291): `oc_runipd.py:2979, agy_runipd.py:2094`
      Context: `"configured_file"` (`oc_runipd.py:2979`, `agy_runipd.py:2094`) and nothing ever assigns `"path"`.
        Offset 2979 -> Line 2979: # `runner_shutdown.track_child`), and it has exactly TWO callers: the executor in
        Offset 2094 -> Line 2094: expand_selectors_fn=expand_selectors,

    Summary:
      Total citing sites: 8
      Total offsets resolved: 15
      Offsets PAST_EOF: 5
    ```
    Census comparison with F-01: exactly matches the 15-offset / 8-site / 5-past-EOF census. The 5 past-EOF offsets are `oc_runipd.py` 6993, 7031, 6645, 6647, and 6649 against 5516 lines. No site moved or vanished; no reconciliation required.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted transcript showing `runner_shared.EXECUTION_SUCCESS_STATES` and both host re-exports printed from the imported modules with `'substantially-complete'` absent from each; the `git log -1 -S` output attributing the narrowing to `6b94a4d9d` with its date; and the occurrence count of `EXECUTION_SUCCESS_STATES` inside `edge_satisfied`'s body with the text of its single hit, demonstrating that the only mention is the comment about the deleted shortcut and that no live statement reads the set. All four facts must appear; a transcript covering only the set membership does not validate the `edge_satisfied` half, which is the claim E-04 rewrites.
  - Observed evidence:
    (a) & (b) Runtime set inspection and object identity:
    ```
    >>> from agent_workflows import runner_shared, oc_runipd, agy_runipd
    >>> runner_shared.EXECUTION_SUCCESS_STATES
    {'executed'}
    >>> 'substantially-complete' in runner_shared.EXECUTION_SUCCESS_STATES
    False
    >>> oc_runipd.EXECUTION_SUCCESS_STATES
    {'executed'}
    >>> 'substantially-complete' in oc_runipd.EXECUTION_SUCCESS_STATES
    False
    >>> agy_runipd.EXECUTION_SUCCESS_STATES
    {'executed'}
    >>> 'substantially-complete' in agy_runipd.EXECUTION_SUCCESS_STATES
    False
    >>> oc_runipd.EXECUTION_SUCCESS_STATES is runner_shared.EXECUTION_SUCCESS_STATES
    True
    >>> agy_runipd.EXECUTION_SUCCESS_STATES is runner_shared.EXECUTION_SUCCESS_STATES
    True
    ```

    (c) Narrowing commit attribution via `git log -1 -p -S'EXECUTION_SUCCESS_STATES = {"executed"}' -- agent_workflows/runner_shared.py`:
    ```
    commit 6b94a4d9de6061b4dfe0fd8f5b50c55e92228b59
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Sep 25 01:56:56 2026 -0400

        statusvocab: rename the terminal status vocabulary so a label names its refusing authority

    @@ -22085,7 +22158,7 @@ SUCCESS_STATES = {"executed", "reviewed", "approved"}
    -EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}
    +EXECUTION_SUCCESS_STATES = {"executed"}
    ```

    (d) `EXECUTION_SUCCESS_STATES` occurrence count in `edge_satisfied`:
    ```python
    import inspect
    from agent_workflows import runner_shared
    src = inspect.getsource(runner_shared.edge_satisfied)
    lines = src.splitlines()
    matches = [l.strip() for l in lines if "EXECUTION_SUCCESS_STATES" in l]
    print(len(lines), len(matches), matches)
    # Output: 176 lines, 1 match:
    # ["# IN-MEMORY run status and accepted any member of `EXECUTION_SUCCESS_STATES`, which admits"]
    matches_success = [l.strip() for l in lines if "success_states" in l]
    print(len(matches_success))
    # Output: 0
    ```
    Confirmed: exactly 1 occurrence inside `edge_satisfied`, within the comment documenting the deleted shortcut; 0 live statements read the set.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the three corrected passages pasted VERBATIM from the edited file (before and after), each shown to state the membership as `{"executed"}` or to avoid asserting a membership at all, with `6b94a4d9d` named at least once across them. Plus a pasted search over `agent_workflows/runner_shared.py` for `substantially-complete` co-occurring with `EXECUTION_SUCCESS_STATES`, demonstrating that no surviving sentence pairs them as a membership claim; any remaining co-occurrence must be quoted and justified as a HISTORICAL statement (for example, text describing what the deleted shortcut used to admit, which is true as history and must not be rewritten). Plus a diff or `git diff --stat` confirming `EXECUTION_SUCCESS_STATES`'s own definition line is unchanged. For passage (ii), show the restated dependency-vs-reporting distinction matches the E-02 printout of both sets (`EXECUTE_REPORTING_SUCCESS_STATES` printed alongside), and that the `substantially-complete` exit-code measurement survives labelled as pre-`6b94a4d9d` history. Plus a one-off MEASUREMENT (not a committed test) proving no executable code changed: parse `git show HEAD:agent_workflows/runner_shared.py` (the pre-edit blob) and the edited file with `ast.parse`, blank every docstring constant, and paste the result of comparing `ast.dump` of the two (expected: equal). Comments are not in the AST, so equality proves every edit was a comment or docstring.
  - Observed evidence:
    (1) Passages before and after:
    Passage (i) `SET_RETIREMENT_DONE_STATUS` note:
    Before:
    ```python
    #: DELIBERATELY NOT `EXECUTION_SUCCESS_STATES`. That set (`oc_runipd.py:274`) includes
    #: `substantially-complete` for DEPENDENCY-EDGE purposes and is out of scope (spec Section 4). This
    #: predicate simply does not consult it; nothing about it is changed here.
    SET_RETIREMENT_DONE_STATUS = "executed"
    ```
    After:
    ```python
    #: DELIBERATELY NOT `EXECUTION_SUCCESS_STATES`. That set (`runner_shared.EXECUTION_SUCCESS_STATES`,
    #: which both hosts re-export) is `{"executed"}` (narrowed by commit `6b94a4d9d`, `statusvocab`,
    #: 2026-09-25, which removed legacy `substantially-complete`) and is the DEPENDENCY bar (spec Section 4).
    #: This predicate simply does not consult it; nothing about it is changed here.
    SET_RETIREMENT_DONE_STATUS = "executed"
    ```

    Passage (ii) `EXECUTE_REPORTING_SUCCESS_STATES` note:
    Before:
    ```python
    #: WHY THIS IS A THIRD SET AND NOT `EXECUTION_SUCCESS_STATES`, which is what the plan's E-02 proposed
    #: and what the dependency sites use. The two answer DIFFERENT QUESTIONS and are not interchangeable
    #: here. `EXECUTION_SUCCESS_STATES` = {`executed`, `substantially-complete`} is the DEPENDENCY bar:
    #: "may a dependent of this item now run?", for which `substantially-complete` legitimately counts.
    #: This is the REPORTING bar: "did the run succeed?", for which `substantially-complete` deliberately
    #: does NOT, and that is a pinned contract rather than an accident. MEASURED: substituting
    #: `EXECUTION_SUCCESS_STATES` at the exit-code site makes
    #: `tests/test_rununify_run_queue.py::TheExitCodeReflectsTheRealOutcome::
    #: test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` FAIL with `0 == 0`, because
    #: that test exists precisely to pin that a `substantially-complete` item still exits NONZERO. So the
    #: dependency bar would have SILENTLY WIDENED the reporting bar while narrowing it for `reviewed` -
    #: fixing one silent success by introducing another.
    ```
    After:
    ```python
    #: WHY THIS IS A THIRD SET AND NOT `EXECUTION_SUCCESS_STATES`, which is what the plan's E-02 proposed
    #: and what the dependency sites use. The two answer DIFFERENT QUESTIONS and are not interchangeable
    #: here. `EXECUTION_SUCCESS_STATES` is `{"executed"}` (narrowed from `{"executed", "substantially-complete"}`
    #: by commit `6b94a4d9d`, `statusvocab`, 2026-09-25) and is the DEPENDENCY bar: "may a dependent of this
    #: item now run?". This is the REPORTING bar: "did the run succeed?", where `EXECUTE_REPORTING_SUCCESS_STATES`
    #: is `SUCCESS_STATES - {"reviewed"}` = `{"executed", "approved"}`. The two sets still differ (by `approved`)
    #: and are still not interchangeable. HISTORICAL (pre-`6b94a4d9d`): under the legacy two-member set, substituting
    #: `EXECUTION_SUCCESS_STATES` at the exit-code site would have made
    #: `tests/test_rununify_run_queue.py::TheExitCodeReflectsTheRealOutcome::
    #: test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` FAIL with `0 == 0`, because
    #: that test existed precisely to pin that a `substantially-complete` item still exits NONZERO. So the
    #: dependency bar would have SILENTLY WIDENED the reporting bar while narrowing it for `reviewed` -
    #: fixing one silent success by introducing another.
    ```

    Passage (iii) `reconcile_interrupted` docstring:
    Before:
    ```python
    RECOVERY CHANGES WHAT A RESUME DOES, NOT ONLY WHAT THE RECORD SAYS, and that was a maintainer
    decision rather than an inference (`fduoj4` OQ-03, answered 2026-09-10). `run_queue` calls
    `requeue_interrupted` on the line after this function, and that flips every still-`interrupted`
    item back to `queued`; a step recovered to `substantially-complete` leaves that set, so it is NOT
    retried. `substantially-complete` is also in `EXECUTION_SUCCESS_STATES`, which `edge_satisfied`
    reads for a non-review item, so recovery can release a dependent that was waiting. Both effects
    are intended: work proven to have finished is not redone, and dependents waiting on it may
    proceed. The conservative alternative (record the provenance but leave the status `interrupted`
    for requeue purposes) was DECLINED, so the status field and the provenance field must not
    disagree.
    ```
    After:
    ```python
    RECOVERY CHANGES WHAT A RESUME DOES, NOT ONLY WHAT THE RECORD SAYS, and that was a maintainer
    decision rather than an inference (`fduoj4` OQ-03, answered 2026-09-10). `run_queue` calls
    `requeue_interrupted` on the line after this function, and that flips every still-`interrupted`
    item back to `queued`; a step recovered to `fail-gate` (canonical form of legacy
    `substantially-complete` since `6b94a4d9d`) leaves that set, so it is NOT retried. An `executed:`
    edge is answered from the plan's terminal directory ON DISK and not from in-run status (see
    `runner_shared.edge_satisfied`'s `executed:` branch, where the in-run shortcut was removed on
    maintainer ruling 2026-09-19). Both effects were intended by the maintainer at the time, but the
    second effect no longer occurs because a `fail-gate` item's plan remains in `pending/` so an
    `executed:` edge on it is unmet on disk. Work proven to have finished is not redone. The
    conservative alternative (record the provenance but leave the status `interrupted` for requeue
    purposes) was DECLINED, so the status field and the provenance field must not disagree.
    ```

    (2) Co-occurrence search across `agent_workflows/runner_shared.py` for `substantially-complete` and `EXECUTION_SUCCESS_STATES`:
    All 5 remaining blocks are historical / context statements:
    - Hit 1: `SET_RETIREMENT_DONE_STATUS`: notes `{"executed"}` narrowed by `6b94a4d9d` which removed legacy `substantially-complete`.
    - Hit 2: `SET_RETIREMENT_DONE_STATUS`: allowlist note listing known-bad values (`substantially-complete`, `blocked`, ...) and stating it does not consult `EXECUTION_SUCCESS_STATES`.
    - Hit 3: `EXECUTE_REPORTING_SUCCESS_STATES`: restates `EXECUTION_SUCCESS_STATES` is `{"executed"}` narrowed from `{"executed", "substantially-complete"}` by `6b94a4d9d`, and marks legacy measurement as `HISTORICAL (pre-6b94a4d9d)`.
    - Hit 4: `success_states_for_action` docstring: refers to `:data:EXECUTE_REPORTING_SUCCESS_STATES` for the test pinning `substantially-complete` exit code.
    - Hit 5: `edge_satisfied`: comment explaining deleted shortcut which admitted `substantially-complete` on maintainer ruling 2026-09-19.
    Zero surviving sentences make a live claim that `EXECUTION_SUCCESS_STATES` contains `substantially-complete`.

    (3) Printout of both sets:
    ```
    EXECUTION_SUCCESS_STATES = {'executed'}
    EXECUTE_REPORTING_SUCCESS_STATES = frozenset({'approved', 'executed'})
    ```
    The sets differ by `approved` and are not interchangeable. Definition line `EXECUTION_SUCCESS_STATES = {"executed"}` confirmed unchanged in `git diff`.

    (4) AST-equality verification:
    ```python
    import ast, subprocess
    pre_blob = subprocess.check_output(["git", "show", "HEAD:agent_workflows/runner_shared.py"]).decode()
    cur_blob = open("agent_workflows/runner_shared.py").read()
    def blank_docstrings(tree):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    node.body[0].value.value = ""
    t_pre, t_cur = ast.parse(pre_blob), ast.parse(cur_blob)
    blank_docstrings(t_pre); blank_docstrings(t_cur)
    print("AST dumps equal:", ast.dump(t_pre) == ast.dump(t_cur))
    # Output: AST dumps equal: True
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `reconcile_interrupted`'s docstring pasted before and after, showing the dependency-release clause no longer claims either the dead membership or an `edge_satisfied` read of the set, and showing the `requeue_interrupted` retry reasoning and its `fduoj4` OQ-03 attribution PRESERVED (that half is true and destroying it would lose a recorded maintainer ruling). The new text must point a reader at `edge_satisfied`'s `executed:` branch by symbol. Quote the sentence that replaced it, not a paraphrase. Also paste: a `python3 -c` call of `runner_shared.outcome_precedence_disposition(None, {"disposition": d})` for `d` in `executed` and `substantially-complete` showing the return value, and the before/after of the SELF-CLAIM DOWNGRADE bullet and `outcome_precedence_disposition`'s rung 2, each now naming the token that call returns (`fail-gate` unless E-02 found otherwise). Show the `ydbhfd` measurement sentence UNCHANGED.
  - Observed evidence:
    (1) `reconcile_interrupted` docstring pasted before and after in V-03 above.
    Replacement sentence pointing at `edge_satisfied`'s `executed:` branch by symbol:
    "An `executed:` edge is answered from the plan's terminal directory ON DISK and not from in-run status (see `runner_shared.edge_satisfied`'s `executed:` branch, where the in-run shortcut was removed on maintainer ruling 2026-09-19)."

    (2) `runner_shared.outcome_precedence_disposition` call:
    ```
    $ python3 -c 'from agent_workflows import runner_shared; print(runner_shared.outcome_precedence_disposition(None, {"disposition": "executed"})); print(runner_shared.outcome_precedence_disposition(None, {"disposition": "substantially-complete"}))'
    fail-gate
    fail-gate
    ```

    (3) SELF-CLAIM DOWNGRADE bullet before and after:
    Before:
    ```python
          * THE SELF-CLAIM DOWNGRADE, inside the shared precedence helper: a recorded `executed` becomes
            `substantially-complete`. The measured case needs NO relaxation of this, because its outcome
            file already says `substantially-complete`.
    ```
    After:
    ```python
          * THE SELF-CLAIM DOWNGRADE, inside the shared precedence helper: a recorded `executed` becomes
            `fail-gate` (canonical form since `6b94a4d9d`). The measured case needs NO relaxation of this,
            because its outcome file already says `substantially-complete` (which normalizes to `fail-gate`).
    ```

    (4) `outcome_precedence_disposition` rung 2 before and after:
    Before:
    ```python
          2. A RECORDED `executed` is DOWNGRADED to `substantially-complete`. This is the
             ANTI-FABRICATION RULE, not an inconvenience: an agent writing `disposition: executed` into
             its own outcome file is making a SELF-CLAIM, and this repository does not treat a self-claim
             as completion authority. Do not remove it to make a case report better.
    ```
    After:
    ```python
          2. A RECORDED `executed` is DOWNGRADED to `fail-gate`. This is the
             ANTI-FABRICATION RULE, not an inconvenience: an agent writing `disposition: executed` into
             its own outcome file is making a SELF-CLAIM, and this repository does not treat a self-claim
             as completion authority. Do not remove it to make a case report better.
    ```

    (5) `ydbhfd` measurement sentence unchanged at lines 31756-31758:
    ```python
             Measured (backlog `ydbhfd`): `aw oc run e32j35 97df1z` was killed by a
             reboot, `outcomes/02-97df1z.json` recorded `substantially-complete` with a real commit sha,
             and `state.json` recorded `interrupted` with `last_outcome: None`.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: a pasted re-run of E-01's resolver over the EDITED file reporting ZERO bare `<host>.py:<line>` citations, plus, for each of the 8 re-anchored sites, the new anchor quoted and PROVEN to resolve: a symbol anchor demonstrated by locating that symbol in the named module (pasted search hit), a quoted-string anchor demonstrated by a pasted search finding it, and a commit anchor demonstrated by a pasted `git log -1` for that hash. For the two HISTORICAL anchors also paste the historical construct itself: `git show 394238996^:agent_workflows/oc_runipd.py` lines showing the `runnable["status"] = "dependency-blocked"` `else` arm inside `run_queue`'s orchestrate block, and for the `agy_runipd` re-export note a pasted search hit for "The `as <same-name>` form marks these as an intentional RE-EXPORT" in `agent_workflows/agy_runipd.py`. A site whose new anchor is not demonstrated to resolve is NOT validated, since this plan's entire subject is citations that do not resolve, and shipping a dead symbol anchor would reproduce the defect in a new form.
  - Observed evidence:
    (1) Re-run of E-01 resolver over edited `agent_workflows/runner_shared.py`:
    ```
    $ python3 -c 'import re; lines=open("agent_workflows/runner_shared.py").readlines(); pat=re.compile(r"(oc_runipd\.py|agy_runipd\.py):(\d+(?:-\d+)?)"); hits=[(i+1,m.group(0),l.strip()) for i,l in enumerate(lines) for m in pat.finditer(l)]; print(f"Remaining bare host citations: {len(hits)}")'
    Remaining bare host citations: 0
    ```

    (2) Resolution proof for each of the 8 re-anchored sites:
    - Site 1 (`runner_shared.EXECUTION_SUCCESS_STATES`):
      `from agent_workflows import runner_shared; runner_shared.EXECUTION_SUCCESS_STATES == {'executed'}` (True)
    - Site 2 (`commit 394238996^`, `oc_runipd.run_queue`):
      `git log -1 394238996` -> `Merge lane aw/lane/pgq326: wire orchestrator retirement into both host dispatch paths`
      `git show 394238996^:agent_workflows/oc_runipd.py` (lines 7008-7032):
      ```python
              if runnable.get("action") == "orchestrate":
                  repo = Path(state["repo"])
                  all_done, unfinished = _set_children_all_executed(
                      state, runnable["setid"], runnable["id6"]
                  )
                  if all_done and finalize_orchestrator(
                      repo,
                      runnable["id6"],
                      f"Orchestrator rollup: all children of set {runnable['setid']} executed "
                      f"(aw oc run, no agent turn).",
                  ):
                      runnable["status"] = "executed"
                      append_jsonl(run_dir / "events.jsonl", ...)
                  else:
                      runnable["status"] = "dependency-blocked"
                      runnable["unsatisfied_dependencies"] = unfinished
      ```
    - Sites 3 & 4 (Commit `70a2059f` plus `runner_shared.execute_item_core`'s `v_outcome_file` block):
      `git log -1 70a2059f` -> `refactor(runner): deduplicate execute_item into runner_shared.execute_item_core`
      `v_outcome_file` in `agent_workflows/runner_shared.py:33747`:
      `v_outcome_file = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}-verification.json"`
    - Sites 5 & 6 (`agy_runipd._AGY_TOOL_PREFIX_KIND`'s `"run_command"` key):
      `from agent_workflows import agy_runipd; agy_runipd._AGY_TOOL_PREFIX_KIND["run_command"] == "bash"` (True)
    - Site 7 (quoted note "The `as <same-name>` form marks these as an intentional RE-EXPORT"):
      `grep -n "The \`as <same-name>\` form marks these as an intentional RE-EXPORT" agent_workflows/agy_runipd.py`:
      `agent_workflows/agy_runipd.py:157:# The \`as <same-name>\` form marks these as an intentional RE-EXPORT so an autoformatter cannot strip`
    - Site 8 (`runner_shared.initialize_run_core` writing `"configured_file"`):
      `agent_workflows/runner_shared.py:29153: "configured_file": plan["file"],`
      `agent_workflows/runner_shared.py:29191: "configured_file": item_info.get("file", ""),`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the ACTUAL pasted tail of a BARE `python3 -m pytest` run (no added flags: no `-n0`, no second `-q`, no `-p no:randomly`), including its summary line, for BOTH the pre-change baseline and the post-change run. Plus pasted output from `aw check --source-citations` and `aw check --source-anchors`, with their exit codes, for both. Compare the suite failure set BY NAME, not by count: the tree is not reliably green here and a count comparison would be meaningless. Any failure present after the change must be shown present before it, or explained. This plan changes only comments, so an introduced failure would indicate an accidental code edit and must block. A claim of "tests pass" with no pasted runner output does NOT validate this item.
  - Observed evidence:
    (1) Bare pytest suite runs:
    Pre-change baseline:
    ```
    ........................................................................ [ 99%]
    ...............                                                          [100%]
    =============================== warnings summary ===============================
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_the_lock_is_reacquirable_after_the_holder_exits
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED
      <venv>/lib/python3.14/multiprocessing/popen_fork.py:76: DeprecationWarning: This process (pid=524349) is multi-threaded, use of fork() may lead to deadlocks in the child.
        self.pid = os.fork()

    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    NOTE: 246 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    4982 passed, 2 skipped, 3 warnings in 681.13s (0:11:21)
    ```

    Post-change run:
    ```
    ........................................................................ [ 99%]
    .............                                                            [100%]
    =============================== warnings summary ===============================
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_the_lock_is_reacquirable_after_the_holder_exits
      <venv>/lib/python3.14/multiprocessing/popen_fork.py:76: DeprecationWarning: This process (pid=801807) is multi-threaded, use of fork() may lead to deadlocks in the child.
        self.pid = os.fork()

    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED
      <venv>/lib/python3.14/multiprocessing/popen_fork.py:76: DeprecationWarning: This process (pid=802357) is multi-threaded, use of fork() may lead to deadlocks in the child.
        self.pid = os.fork()

    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    NOTE: 246 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    4982 passed, 2 skipped, 3 warnings in 711.47s (0:11:51)
    ```
    Failure set comparison: exactly 0 failures in both runs. Zero regressions introduced.

    (2) `aw check --source-citations`:
    Pre-change:
    ```
    Skipped 4 test file(s) under scanned roots.
    (exit 0)
    ```
    Post-change:
    ```
    Skipped 4 test file(s) under scanned roots.
    (exit 0)
    ```

    (3) `aw check --source-anchors`:
    Pre-change:
    ```
    agent_workflows/check_engine.py:353: spec pqsx96 :135 -> ## 3. Invariant catalog
    (exit 0)
    ```
    Post-change:
    ```
    agent_workflows/check_engine.py:353: spec pqsx96 :135 -> ## 3. Invariant catalog
    (exit 0)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is NOT approved for execution by its own authorship. It requires explicit human approval, recorded through the tooled lifecycle, before any execution turn begins (`AGENTS.md`; `aw ipd begin`).

EXECUTION CONTRACT. Commit only `agent_workflows/runner_shared.py`, through `aw commit <plan> -- agent_workflows/runner_shared.py`; never `git add -A`, never a bare or `-a` commit, and never push. Verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed raw commit attempt: this is a shared checkout and `runner_shared.py` is among its most-edited files, so another party's unstaged change to it may be restored into the index by a rejected hook. If the file is being changed under you in a way these comment edits cannot be safely combined with, STOP and report rather than overwriting.

DO NOT CHANGE BEHAVIOR. Every edit is to a comment or a docstring. If an edit turns out to require touching a statement, a signature, or a constant, that is out of scope: stop and report. In particular `EXECUTION_SUCCESS_STATES` must still be `{"executed"}` when this plan finishes, and V-03 demands proof of it.

POST-GATE LIFECYCLE. Do not claim done, and do not move this plan to `.aw/records/plans/executed/`, until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries concrete pasted evidence with `Result: pass`. The terminal transition is performed through the tooled lifecycle (`aw ipd finalize`), never by hand-editing status or by moving the file.
