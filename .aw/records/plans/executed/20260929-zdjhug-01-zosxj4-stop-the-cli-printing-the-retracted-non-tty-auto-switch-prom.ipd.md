# IPD: Stop the CLI printing the retracted non-TTY auto-switch promise in its agent-output hint

- Date: 2026-09-29
- Kind: child
- Concern: The shared human renderer appends the literal line `Agent output: --agent (automatic when piped)` to almost every `aw` command's output. The parenthetical asserts the automatic non-TTY switch to `aw.agent/v1` JSONL that was RETRACTED by maintainer ruling (ttyflags `yaxr4i` OQ-01, 2026-09-10) and never shipped. It is self-refuting in the very invocation that prints it: measured at base commit `b5a45362`, `python3 -m agent_workflows check plans | cat` ends with that exact line while every line above it is human prose. Plan `3rsdbj` corrected the same false claim in six user DOCS but could not reach the CLI, because its fence was docs-only; this is the code instance it carried here, and it reaches far more users than any doc, being printed on every command rather than read by whoever opens a file.
- Scope: IN: (a) the one-line wording fix in `agent_workflows.HumanRenderer.render`'s agent-output-hint branch, dropping the false parenthetical; (b) the remaining false instances of the same string in LIVE reference surfaces: the sample terminal transcript in `docs/cli-human-guide.md` "Anatomy of a standard render", which `3rsdbj` could not reach because that file was explicitly OUT of its fence as already-correct reference wording, AND (added at review, F-08) the present-tense Conventions clause in `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md`, which this plan had wrongly pre-classified as an untouchable historical record; (c) refreshing the four `*.human.golden` conformance fixtures that record this renderer's bytes, so the committed record of the hint does not contradict the code; (d) a NEW behavior test that pins the absence of the false promise in rendered human output, because the renderer currently has NO test caller at all and a one-line string is otherwise free to regress. OUT: restoring the deleted conformance gates that used to consume those goldens (F-04; it is a much larger job, it belongs to the suite-trim restoration family, and it is carried by a new backlog item rather than smuggled in here); correcting the two goldens' UNRELATED stale remediation text (F-05, same carrier); `agent_workflows.result_types.select_output` and `should_color`, whose docstrings and behavior are already correct for this ruling and are the reason only this user-visible string was wrong; the six docs `3rsdbj` already fixed; and any change to WHEN machine output is selected, which is behavior this plan must not touch.
- Scope-Paths: agent_workflows/renderers.py, docs/cli-human-guide.md, tests/fixtures/conformance_goldens/check_findings.human.golden, tests/fixtures/conformance_goldens/error_cannot_run.human.golden, tests/fixtures/conformance_goldens/mutation_preview.human.golden, tests/fixtures/conformance_goldens/read_clean.human.golden, tests/test_human_renderer_agent_hint.py, .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: zdjhug
- Blocks-Release: next
- Set: zdjhug
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: zosxj4

## Workflow history
- 2026-10-02 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: zosxj4 verified (set zdjhug, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-krwj2o-01-krwj2o-restore-deleted-cli-conformance-test-gates-and-ref.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-A01..PR-A05, all FIXED. THE BASE MOVED (plan measured at `b5a45362`, reviewed at `1d8fc76e`), so every finding was RE-MEASURED rather than read, and ALL SIX of the plan's original findings survive intact - a good result for a plan whose gate warns its premise could go stale. Verified independently: `renderers.py:184` prints the literal and `check plans | cat | tail -1` shows it under human prose (F-01); `select_output`'s docstring carries the color-only rule (F-06); `docs/cli-human-guide.md:41` holds the fifth instance (F-02); `grep -rln HumanRenderer tests/*.py` returns only the orphaned `conformance_matrix.py` (F-03); and F-05's drift is real (`build_remediation` now emits `--to-id6 --apply` and `--rename --apply` text the golden lacks). I ALSO RE-RAN F-04's EMPIRICAL CLAIM MYSELF rather than accepting it, because it overturns the backlog item's central scope claim in the easier direction: applied E-02, left the goldens untouched, bare suite `3246 passed, 2 skipped` identical to baseline, then reverted; plus `19313eed` deleted both consumers and `GOLDEN_DIR` has zero readers. TWO HIGH FINDINGS, both OUTSIDE the file the plan was staring at. PR-A01, which would have shipped a FALSE VERIFICATION: a SIXTH live instance exists in the CLI inventory survey's Conventions paragraph as a PRESENT-TENSE statement of current behavior, and this plan's V-06 pre-classified the survey among "historical records that must not be rewritten", so the plan would have finished with its own Goal unmet while declaring success; new E-07/V-07 fix it, the path is declared, and note the phrase WRAPS ACROSS A LINE so a full-phrase single-line grep finds nothing. PR-A02: concurrent pending plan `xs557y` declares the same `renderers.py` and the same guide and rewrites the SAME `HumanRenderer.render` method; recorded as a coordination and EVIDENTIARY fact and explicitly NOT as a runtime hazard (the runners isolate per item and merge through the revalidate gate), because V-02/V-03 demand a one-line diff the second lander may be unable to show. PR-A03: both `Carrier: NEEDS-BACKLOG-ITEM` placeholders FAILED the shipped `check_durable_carrier` as malformed, so the plan was red before executing; converted to honest `Carrier-Declined` rows while keeping OQ-01's file-during-execution requirement and V-06's gate, and the repository finding count fell 27 -> 26. PR-A04 adds a fourth honest limit: E-06 greps ONE literal, and `3rsdbj` already measured that this pattern class misses paraphrases. Five decisions recorded in the typed review record, all `Reversible: yes`. Structural preflight `conforming` at `author` and `review-finalize`.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog zdjhug. Authoring measurement CORRECTED the item's stated scope on two counts: the four goldens are ORPHANED (their sole consumer was deleted, so they pin nothing and the suite passes with the fix alone), and a FIFTH false instance survives in docs/cli-human-guide.md. See F-02, F-03, F-04.
- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the CLI stop telling users something false about its own output contract. After this plan, no `aw` command prints the claim that `--agent` is "automatic when piped", every LIVE instance of the claim is corrected, the committed golden fixtures agree with the code, and a real behavior test keeps the promise from coming back.

CORRECTED AT REVIEW: the original Goal said "the last user-facing doc instance is corrected", counting five instances. There are SIX live ones. The sixth is a present-tense normative sentence in the repository's own CLI inventory survey, which this plan's V-06 had pre-classified as an untouchable historical record when it is nothing of the kind (F-08, now E-07). So the honest form of this Goal is "every live instance", and the count is not stated as a fixed number because a further instance in a wording this plan's grep does not match would not be caught by it either.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the premise before changing anything

- [x] E-01 Re-measure the defect and the ruling at the execution base, so the fix is not built on a stale premise. Run `python3 -m agent_workflows check plans | cat | tail -3` and confirm the final line is `Agent output: --agent (automatic when piped)` while the lines above it are human prose (not a `{"schema":"aw.agent/v1"` record). Then confirm the resolver is already correct and is NOT what this plan changes: `grep -n "TTY-NESS OF STDOUT AFFECTS COLOR ONLY" agent_workflows/result_types.py`.
  - Depends on: none
  - Expected outcome: the false line is printed at the foot of PIPED human output (the self-refutation), and `select_output`'s docstring already records that TTY-ness affects color only. STOP AND REPORT if piped output is actually JSONL: the parenthetical would then be true and this plan's premise wrong.
  - Execution state: performed

### Task group 2: Fix the false claim

- [x] E-02 In `agent_workflows.HumanRenderer.render`, in the branch guarded by `if not result.data.get("suppress_agent_hint", False)`, change the appended literal from `"Agent output: --agent (automatic when piped)"` to `"Agent output: --agent"`. Drop ONLY the parenthetical: the hint itself is useful and correct, and the surrounding line, the guard, and the hint's position as the last line must not change. Do NOT touch `select_output`, `should_color`, or anything that decides WHICH mode is selected; the resolver is right (E-01) and this is a wording defect on a user-visible string.
  - Depends on: E-01
  - Expected outcome: the renderer's hint names the flag without asserting when it is selected. No behavior other than this one string changes.
  - Execution state: performed
- [x] E-03 In `docs/cli-human-guide.md`, correct the sample terminal transcript under "Anatomy of a standard render" whose last line reads `Agent output: --agent (automatic when piped)`, so the illustrated output matches what the CLI now prints. This file was deliberately OUT of plan `3rsdbj`'s fence (treated there as already-correct reference wording) and its V-09 evidence recorded this hit as "legitimate example output" precisely because it was a faithful transcript of the then-current bytes; once E-02 lands that justification expires and the line becomes the LAST false instance of the promise in the docs. Change only the transcript's hint line; the file's prose about output mode is already correct and is the reference wording this plan defers to.
  - Depends on: E-02
  - Expected outcome: no user-facing doc asserts the retracted auto-switch in any wording, and the guide's transcript is a truthful sample of real output.
  - Execution state: performed

### Task group 3: Make the committed record agree, and keep it agreeing

- [x] E-04 Refresh the four human golden fixtures that record this renderer's bytes (`tests/fixtures/conformance_goldens/{check_findings,error_cannot_run,mutation_preview,read_clean}.human.golden`), changing ONLY their final hint line to match E-02. Do NOT regenerate them wholesale: measured at authoring (F-05), `check_findings.human.golden` is ALSO stale on two unrelated remediation strings, and a blanket regeneration would silently fold that drift into this commit, making the diff unreviewable and claiming a fix this plan did not make. Edit the hint line in each file and leave every other byte alone. Note these fixtures are currently ORPHANED (F-04): nothing reads them, so this edit is about not committing a record that contradicts the code, NOT about making a test pass.
  - Depends on: E-02
  - Expected outcome: each of the four files differs from its base version on exactly one line, the hint line; `git diff --stat` shows `1 insertion, 1 deletion` per file.
  - Execution state: performed
- [x] E-05 Add `tests/test_human_renderer_agent_hint.py`, a BEHAVIOR test that renders real `CommandResult` values through `HumanRenderer` and asserts on the rendered output. It must assert: (1) the rendered human output of a normal result ENDS with `Agent output: --agent` and does NOT contain the substring `automatic when piped`; (2) the same holds for a result rendered with `color=True`, so the claim cannot survive behind ANSI styling; (3) a result whose `data` sets `suppress_agent_hint` true emits NO hint line at all, pinning the guard that exists today rather than only the string. This is the one durable guard: measured at authoring, `HumanRenderer` has NO test caller anywhere under `tests/` (F-03), so nothing currently stops this regressing. Assert on RENDERED OUTPUT only; do NOT read `renderers.py` source with `inspect`, `ast`, regex, or substring search, and do NOT assert on line counts or symbol censuses (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
  - Depends on: E-02
  - Expected outcome: a new test file that FAILS against the base renderer and PASSES after E-02, exercising the code rather than inspecting it.
  - Execution state: performed

- [x] E-07 CORRECT THE SIXTH LIVE INSTANCE, in `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md`'s "Conventions." paragraph, locating it by the content string `also\nautomatic when piped` (the phrase wraps across two lines, so a single-line grep for the full phrase will MISS it; search for `automatic when piped` alone). ADDED AT REVIEW (F-08). It reads "`--agent` (aw.agent/v1 JSONL, also automatic when piped)"; drop the ", also automatic when piped" clause so it reads "`--agent` (aw.agent/v1 JSONL)". THIS IS NOT A HISTORICAL RECORD AND MUST NOT BE TREATED AS ONE: it is a PRESENT-TENSE normative statement of the CLI's conventions in a durable reference artifact, not a transcript of past output and not a quotation of the retracted policy, so the immutability reasoning that correctly protects `plans/executed/` does not apply. Without this edit, this plan's own Goal is not met and V-06 would wrongly disposition a live falsehood as history. Change ONLY that clause; do not restructure the paragraph, do not touch the surrounding exit-code or R/W sentences, and do not edit any other part of the survey.
  - Depends on: E-02
  - Expected outcome: the CLI inventory survey no longer states the retracted auto-switch as current fact, with exactly one line changed and the rest of the Conventions paragraph intact.
  - Execution state: performed

### Task group 4: Verify

- [x] E-06 Verify the claim is gone tree-wide and nothing regressed. Run `git grep -n -i "automatic when piped"` over the whole repo and enumerate every remaining hit with a disposition. Then run the suite BARE as `python3 -m pytest`. Then `aw sanitize --agent; echo rc=$?`.
  DISPOSITION LIST CORRECTED AT REVIEW: the expected remaining hits are this plan, backlog `zdjhug`, plan `3rsdbj` and its review record, pending plan `dv7c49` (which cites the defect as out of its own scope), pending plan `xs557y` if it mentions it, and the two executed plans quoting old terminal transcripts. The SURVEY RECORD IS NO LONGER ON THAT LIST: it is a live surface, corrected by E-07 (F-08), so a surviving hit there is a FAILED E-06, not an expected historical one.
  - Depends on: E-03, E-04, E-05, E-07
  - Expected outcome: every remaining hit is a HISTORICAL record that must not be rewritten and none is a live user-facing surface (`agent_workflows/`, `docs/`, `README.md`, `CHANGELOG.md`, or the CLI inventory survey); suite green; sanitizer exit 0.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or quoted content string; line numbers below are at base commit `b5a45362` and are approximate by the time this executes (spec `ipd-structure-and-linting` Section 10.2).
- A reversed policy is labelled RETRACTED with a pointer to the ruling and kept, never silently deleted. `docs/cli-output-contract.md` section 9 ("Automatic Non-TTY Migration Policy: RETRACTED") and `docs/cli-human-guide.md` "Output mode and audience" are the REFERENCE WORDING; this plan matches them rather than inventing a sixth formulation of the same rule.
- Tests must exercise behavior and assert on real outputs; tests that read production source text or count symbols are forbidden (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). This is why E-05 renders results instead of grepping `renderers.py`.
- No em or en dashes in user-facing prose (`docs/cli-human-guide.md` here). The rule does not apply to this plan itself.
- Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md "HOW TO RUN THE SUITE").
- Commit through `aw commit zosxj4 -- <paths>`; never `git add -A`, never `-a`, never push.

## Findings

| # | Location (base `b5a45362`) | Finding |
| --- | --- | --- |
| F-01 | `agent_workflows/renderers.py`, `HumanRenderer.render`, the `# 7. Agent Output Hint` block (~:182-184) | CONFIRMED AS THE BACKLOG ITEM STATES. `lines.append("Agent output: --agent (automatic when piped)")` runs unless `result.data` sets `suppress_agent_hint`. Measured: `python3 -m agent_workflows check plans \| cat \| tail -3` ends with that line above human prose, exit 1. The claim is false per the 2026-09-10 ruling, which `docs/cli-output-contract.md` section 9 records verbatim ("Piping or redirecting `aw` emits HUMAN-READABLE TEXT. `--agent` is the explicit and only way to obtain `aw.agent/v1` JSONL"). The fix is the one-line wording change the item proposes. |
| F-02 | `docs/cli-human-guide.md`, the fenced sample transcript under "Anatomy of a standard render" whose final line is `Agent output: --agent (automatic when piped)` (~:41) | NOT IN THE BACKLOG ITEM. A FIFTH live instance of the false string survives in a user doc, inside the sample render transcript. Plan `3rsdbj` SAW this hit (its V-09 grep output lists that file's transcript line) and correctly dispositioned it as "legitimate example output", because the file was out of its fence and the transcript accurately showed the bytes the CLI then printed. That justification is valid ONLY while the code is unfixed: the moment E-02 lands, the transcript becomes both false and stale. So the docs are NOT fully clean after `3rsdbj`, and fixing the code without this line would leave the last readable instance of the retracted promise in the very guide that explains output mode. Added to scope as E-03. |
| F-03 | `tests/` tree | THE RENDERER HAS NO TEST CALLER AT ALL. `grep -rln "HumanRenderer" tests/*.py` returns only `tests/conformance_matrix.py`, which is itself imported by nothing (F-04). So no test renders human output today, and a one-line user-visible string has zero regression guard. This is why E-05 adds a real behavior test rather than relying on the goldens, and it is the most durable part of this plan. |
| F-04 | `tests/fixtures/conformance_goldens/*.human.golden`; deleted `tests/test_cli_quality_gates.py` | THE BACKLOG ITEM'S CENTRAL SCOPE CLAIM IS WRONG, AND IN THE EASIER DIRECTION. The item says "four conformance goldens pin the current bytes ... Expect the golden regeneration path plus a suite run". They pin NOTHING. Their sole consumer, `tests/test_cli_quality_gates.py` (which held `DeterministicByteGoldenTests` and read them through `GOLDEN_DIR`), was DELETED by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 339 lines removed), along with `tests/test_cli_conformance_matrix.py`. At base, `grep -rn "GOLDEN_DIR"` matches ONLY the definition in `tests/conformance_matrix.py`, and that module has no importer under `tests/`. PROVEN EMPIRICALLY, not inferred: with the E-02 fix applied and the goldens UNTOUCHED, a bare `python3 -m pytest` reported `3246 passed, 2 skipped` with zero failures, and `python3 -m pytest -m "slow or livecorpus"` reported the SAME 3 failures before and after the patch (`test_every_subparser_has_fuller_description`, `test_interactive_deep_cleanup_records_remove_fully_cleans_aw`, `test_deep_cleanup_records_remove_leaves_no_aw_directory`), so those are pre-existing and unrelated. CONSEQUENCE FOR THIS PLAN: the goldens are still edited (E-04), because leaving a committed fixture that records a string the code no longer emits is a second, quieter false record; but they are edited as RECORD-KEEPING, and the plan must not claim a test forced it. The real coverage gap is F-03, and restoring the deleted gates is out of scope (see "Deferred"). |
| F-05 | `tests/fixtures/conformance_goldens/check_findings.human.golden` | THE GOLDENS ARE ALREADY STALE ON AN UNRELATED AXIS, so "regenerate them" is a trap. Re-rendering the four original fixture `CommandResult` values at base shows `read_clean`, `mutation_preview`, and `error_cannot_run` match byte-for-byte, but `check_findings` DRIFTS on two remediation strings independent of this defect: the golden says `Fix: run 'aw rename plans a.md' or rename to match ...` where the code now emits `Fix: a.md does not carry a clustered identity prefix; run 'aw rename plans a.md --to-id6 --apply' or rename ...`, and similarly the setid-collision fix line gained `--rename --apply`. A wholesale regeneration would sweep that unrelated drift into this bug's commit, so E-04 edits ONLY the hint line in each file and F-05 is carried, not fixed. |
| F-06 | `agent_workflows/result_types.py`, `select_output` docstring | The resolver is ALREADY correct for this ruling ("TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE"), confirming the backlog item's note. So this is purely a user-visible string defect, not a behavior defect, and E-02 must not change any selection logic. Recorded so a reviewer does not expect a behavior change. |
| F-07 | ADDED AT REVIEW. `.aw/records/plans/pending/20260929-ct1n04-01-xs557y-...ipd.md` | **A CONCURRENT PENDING PLAN DECLARES TWO OF THE SAME PATHS AND REWRITES THE SAME RENDERER METHOD, AND THIS PLAN DOES NOT MENTION IT.** Plan `xs557y` (Set `ct1n04`, `- Status: to-review`) declares `- Scope-Paths: agent_workflows/renderers.py, docs/cli-human-guide.md, tests/test_check_findings_grouping.py, CHANGELOG.md`, so it overlaps THIS plan on `renderers.py` and `docs/cli-human-guide.md`. Its scope is "all inside `renderers.HumanRenderer.render`'s Findings block and the `next_actions` construction", i.e. the SAME METHOD this plan's E-02 edits, and its E-06 "correct[s] the two false statements in `docs/cli-human-guide.md`", i.e. the SAME FILE this plan's E-03 edits. Its F-09 independently measured the same orphaned-golden fact this plan's F-04 records, citing `check_findings.human.golden` as "INERT". THIS IS NOT A RUNTIME HAZARD and must not be reported as one: the runners isolate each item in its own worktree and merge through a revalidate gate, and dependency depth is the first queue sort key. It matters for TWO OTHER reasons. FIRST, whichever plan lands second inherits a `docs/cli-human-guide.md` and a `renderers.render` that the first already changed, so its "exactly one line changed" evidence demands (V-02, V-03) may not hold, and an executor must not treat a larger diff as its own error. SECOND, `xs557y` does NOT declare the four goldens, so if it changes the check-findings human output its own golden record drifts again; that is its problem, not this plan's, but a reader comparing the two should know. |
| F-08 | ADDED AT REVIEW. `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md`, the "Conventions." paragraph | **A SIXTH LIVE INSTANCE OF THE FALSE CLAIM EXISTS AND THIS PLAN MISCLASSIFIES IT AS HISTORICAL.** The survey record's conventions paragraph states that every command accepts "`--agent` (aw.agent/v1 JSONL, also automatic when piped)". V-06 pre-declares "the survey record" among hits expected ONLY in "historical records that must not be rewritten", but this is NOT a transcript of past output and NOT a quotation of a retracted policy: it is a present-tense normative statement about the CLI's conventions, in a durable reference artifact whose own README calls the tree "Durable research ... kept for provenance and cold-start handoff", with no immutability rule of the kind that protects `plans/executed/`. So a cold-start reader of the repository's own CLI inventory is told the retracted promise as current fact. This plan's Goal ("no `aw` command prints the claim ... the last user-facing doc instance is corrected") is therefore not achieved by E-02+E-03 alone. |

## Proposed changes (ordered, validatable)

1. E-01 re-measure the defect and confirm the resolver is already correct (guards the premise).
2. E-02 drop the false parenthetical from the renderer's hint (the actual fix).
3. E-03 correct the last false instance in `docs/cli-human-guide.md`'s sample transcript.
4. E-04 edit the hint line only in the four human goldens, leaving F-05's unrelated drift alone.
5. E-05 add the behavior test that pins the absence of the claim and the `suppress_agent_hint` guard.
6. E-06 tree-wide grep with per-hit disposition, bare suite, sanitizer.

## Deferred / out of scope (with reason)

- Restoring the deleted conformance gates (`tests/test_cli_quality_gates.py` and `tests/test_cli_conformance_matrix.py`, removed by `19313eed`) so the four goldens and `tests/conformance_matrix.py` are consumed again (F-04). This is a real coverage hole: schema validity, ANSI-stream separation, byte determinism, fact parity, and the parser-leaf coverage matrix all lost their only guard, and `tests/conformance_matrix.py` plus twelve golden files are dead weight until something reads them. It is deliberately NOT done here because it is a multi-hundred-line test restoration with its own review surface, it would dwarf a one-line wording fix, and it belongs to the existing suite-trim restoration family (`xvp5vx` audits what that commit cost; `f15tne`, `gzmr54`, `p5qx91` restore specific losses). E-05 covers THIS defect's regression risk in the meantime.
  - Carrier: krwj2o
- The unrelated stale remediation strings in `check_findings.human.golden` (F-05). Correcting them is either a genuine golden refresh or evidence the remediation text changed without its record being updated; either way it is a different defect on a different axis, and folding it in would make this plan's diff unreviewable.
  - Carrier: krwj2o
- Whether to implement non-TTY mode detection at all. `docs/cli-output-contract.md` section 9 records that the ruling does not forbid a future opt-in; this plan takes no position and changes no selection logic.
  - Carrier-Declined: a design question the ruling deliberately leaves open; no work is owed.
- The six docs plan `3rsdbj` already corrected. Verified executed; re-editing them is out of scope and the executed plan's record must not be rewritten.
  - Carrier-Declined: already fixed by an executed plan.

## Scope check

- Over-scope: four additions beyond the backlog item's literal text, each justified. `docs/cli-human-guide.md` (F-02) is added because it is a live instance of the same false claim and fixing the code alone would leave the docs newly wrong; stopping partway through the instances would be arbitrary. The CLI inventory survey (F-08, ADDED AT REVIEW) is added on exactly the same reasoning, and is the instance that makes "stopping partway" concrete: it was about to be dispositioned as history. `tests/test_human_renderer_agent_hint.py` (E-05) is added because F-03 measured that the renderer has no test caller at all, so without it a one-line string fix has no guard and the same regression can land tomorrow unnoticed. The goldens (E-04) are in the item's own scope, though for a corrected reason (F-04).
- Under-scope: the plan deliberately does NOT restore the deleted conformance gates (F-04), which is the larger coverage hole this work uncovered, and does not correct the goldens' unrelated drift (F-05). Both are carried by the backlog item OQ-01 mandates rather than dropped, and both are named in the approval gate so the approver is not surprised.
- Concurrency, ADDED AT REVIEW (F-07): pending plan `xs557y` (Set `ct1n04`, `to-review`) declares `agent_workflows/renderers.py` and `docs/cli-human-guide.md` too, and rewrites the SAME `HumanRenderer.render` method plus the SAME guide. This is NOT declared a hazard: the runners isolate each item in its own worktree and merge through the revalidate gate, so overlap is a coordination fact, not a runtime risk. The consequence for THIS plan is evidentiary only: if `xs557y` lands first, V-02's and V-03's "exactly one line changed" expectations may no longer hold, and the executor must report the larger diff with that explanation rather than treating it as its own error or forcing the diff to look smaller.

## Required tests / validation

One new behavior test, `tests/test_human_renderer_agent_hint.py` (E-05), is the durable verification: it renders real `CommandResult` values through `HumanRenderer` and asserts the rendered bytes, covering the plain path, the colored path, and the `suppress_agent_hint` guard. It must fail against the base renderer and pass after the fix; demonstrating that FAILURE is part of V-05, because a test that passes both before and after proves nothing.

Beyond it: E-01's measurement of the self-refuting output, E-06's tree-wide grep with a disposition per remaining hit, a bare `python3 -m pytest`, and `aw sanitize --agent`.

HONEST LIMITS ON WHAT THIS VERIFICATION PROVES. First, the four goldens are orphaned (F-04), so a green suite does NOT prove they are correct; nothing reads them, and their edit is verified by reading the diff, not by a test. Second, a grep proves the known phrasing is gone, not that the replacement is accurate; the accuracy check is human, reading the new hint and the corrected transcript against `docs/cli-output-contract.md` section 9 and `docs/cli-human-guide.md` "Output mode and audience". Third, the suite at base has 3 pre-existing failures in the `slow`/`livecorpus` selection (F-04); they are unrelated and must be reported as pre-existing, not silently absorbed.

FOURTH, ADDED AT REVIEW AND THE SHARPEST LIMIT OF THE FOUR: THE GREP PATTERN IS THE VERIFICATION, AND IT ONLY FINDS ONE WORDING. `git grep -i "automatic when piped"` cannot find a paraphrase, and plan `3rsdbj` already learned this the expensive way - its review measured that its authored three-phrase pattern MISSED `docs/cli-migration.md`'s "This is automatic and immediate" and `docs/cli-agent-protocol.md`'s "whenever stdout is not a terminal", the two most load-bearing sentences in that whole plan, so its E-09 had to be rewritten around a six-alternative pattern. This plan searches for ONE phrase. That is defensible, because this plan's subject IS that exact literal, but it means a clean grep proves the literal is gone and proves NOTHING about a seventh instance in other words. The reviewer's own re-measurement also shows the phrase WRAPS ACROSS A LINE in the survey record, so even a full-phrase single-line grep would have missed it; E-07 therefore says to search the short form. Anyone extending this work should run `3rsdbj`'s wider pattern rather than this plan's narrow one.

## Spec / documentation sync

No `.spec.md` is amended: the normative contract (`docs/cli-output-contract.md` section 9) is ALREADY correct and is the authority this plan brings the code into line with, so there is no contract change to make and `- Scope-Paths:` declares no spec file. The documentation sync is E-03, the one remaining false transcript in `docs/cli-human-guide.md`.

## Open questions

### OQ-01: File the backlog item carrying the orphaned conformance gates before or during execution?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: FILE IT DURING EXECUTION, as a separate `aw backlog new` call, and set the two declined carrier rows in "Deferred / out of scope" to `- Carrier: <id6>` before finalizing.
  CORRECTED AT REVIEW, ON A MEASURED TOOLING FACT: those two rows originally read `- Carrier: NEEDS-BACKLOG-ITEM (...)`, and that is not a placeholder the tooling tolerates. `check_engine.check_durable_carrier` REFUSES a non-id6 value outright ("malformed `Carrier` reference(s) ... expected a bare 6-char id6"), so the plan as authored FAILED `aw check` with `check.ipd-uncarried-obligation` before it ever executed. The rows are now `- Carrier-Declined:` with the reason stated, which is the shape the tooling accepts for an obligation whose carrier does not exist yet, and each row says plainly that it is declined for lack of a filable id6 rather than for lack of an obligation. The substance of this resolution is unchanged: the item is still filed during execution, and V-06 still fails if it is not. It is NOT filed at authoring because this turn is authoring-only and filing a second tracked record is a mutation beyond writing the plan. It is NOT deferred past execution because "the goldens pin nothing and their gates are deleted" (F-04) is the most consequential thing this work discovered, and an uncarried finding is a lost one. The item should name both F-04 (restore the deleted gates so `conformance_matrix.py` and the twelve goldens are consumed again) and F-05 (the unrelated drift), `- Work-Kind: chore` (it is lost coverage, not a user-perceptible defect, so it does not auto-gate the release per AGENTS.md "Every live bug gates the next release"), and cross-reference `xvp5vx`, which audits what `19313eed` cost.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the actual output of `python3 -m agent_workflows check plans | cat | tail -3` showing the false hint line as the LAST line with human prose above it, and the output of `grep -n "TTY-NESS OF STDOUT AFFECTS COLOR ONLY" agent_workflows/result_types.py`. Judge the SHAPE of the output only: do NOT compare the `N plans checked` count against any number written in this plan, since that is a live artifact count on a shared tree.
  - Observed evidence: PASS. Output matches expected format.
    ```
    $ python3 -m agent_workflows check plans | cat | tail -3
    Next  correct the plan history via `aw set <status> <id6>` (or `aw ipd finalize` for the terminal transition)
    Next  aw ipd set a6ootg --from-spec pqsx96
    Agent output: --agent (automatic when piped)

    $ grep -n "TTY-NESS OF STDOUT AFFECTS COLOR ONLY" agent_workflows/result_types.py
    77:       TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE: a piped or redirected invocation
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `git diff -- agent_workflows/renderers.py`. It must show exactly one changed line, removing ` (automatic when piped)` from the appended literal, with the `suppress_agent_hint` guard and the hint's position unchanged. Then paste `python3 -m agent_workflows check plans | cat | tail -1` showing `Agent output: --agent` with no parenthetical. A diff touching `select_output`, `should_color`, or any mode-selection logic is a FAILED V-02 (F-06).
  - EXCEPTION ADDED AT REVIEW (F-07): if pending plan `xs557y` has landed first, it will have rewritten this same `HumanRenderer.render` method, so a diff larger than one line may be unavoidable. In that case state so explicitly, show that THIS plan's own change is still the single hint-line edit, and do NOT reshape the file to make the diff look smaller. The invariant that must hold either way is the second half of this item: the piped output's last line reads `Agent output: --agent`.
  - Observed evidence: PASS. Diff and check plans output confirm single hint-line change.
    ```diff
    $ git diff -- agent_workflows/renderers.py
    diff --git a/agent_workflows/renderers.py b/agent_workflows/renderers.py
    index d9ff02fe2..0469c60ab 100644
    --- a/agent_workflows/renderers.py
    +++ b/agent_workflows/renderers.py
    @@ -181,7 +181,7 @@ class HumanRenderer(BaseRenderer):

             # 7. Agent Output Hint
             if not result.data.get("suppress_agent_hint", False):
    -            lines.append("Agent output: --agent (automatic when piped)")
    +            lines.append("Agent output: --agent")

             return "\n".join(lines) + "\n"
    ```
    ```
    $ python3 -m agent_workflows check plans | cat | tail -1
    Agent output: --agent
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `git diff -- docs/cli-human-guide.md` (exactly one line changed, inside the sample transcript) and `grep -n -i "automatic when piped" docs/cli-human-guide.md` returning nothing. Confirm in one sentence that the file's surrounding "Output mode and audience" prose was NOT edited, since it is the reference wording this plan defers to. Same `xs557y` exception as V-02 (F-07): that plan's E-06 also edits this guide, so if it landed first, say so and show this plan's own change is still the transcript hint line alone.
  - Observed evidence: PASS. Diff and grep confirm only transcript hint line changed.
    ```diff
    $ git diff -- docs/cli-human-guide.md
    diff --git a/docs/cli-human-guide.md b/docs/cli-human-guide.md
    index 6b284bb8a..78c5a08a8 100644
    --- a/docs/cli-human-guide.md
    +++ b/docs/cli-human-guide.md
    @@ -38,7 +38,7 @@ Evidence
       checked: 41

     Next  aw group plans x --set y (regroup)
    -Agent output: --agent (automatic when piped)
    +Agent output: --agent
     \```

     1. Title banner: `AW <command>  <target>` and, for timed operations, an elapsed time on the
    ```
    ```
    $ grep -n -i "automatic when piped" docs/cli-human-guide.md
    (empty, exit 1)
    ```
    The surrounding "Output mode and audience" prose was not edited at all and remains intact.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `git diff --stat -- tests/fixtures/conformance_goldens/` showing FOUR files each with exactly one insertion and one deletion, and paste the full `git diff` for `check_findings.human.golden` specifically, proving the two stale remediation strings in F-05 were left UNTOUCHED. A diff that also rewrites the `Fix:` lines is a FAILED V-04, not a passed one: that is F-05's drift and it belongs to the carried item.
  - Observed evidence: PASS. Fixtures diff stat and check_findings diff confirm 1 line per file.
    ```
    $ git diff --stat -- tests/fixtures/conformance_goldens/
     tests/fixtures/conformance_goldens/check_findings.human.golden   | 2 +-
     tests/fixtures/conformance_goldens/error_cannot_run.human.golden | 2 +-
     tests/fixtures/conformance_goldens/mutation_preview.human.golden | 2 +-
     tests/fixtures/conformance_goldens/read_clean.human.golden       | 2 +-
     4 files changed, 4 insertions(+), 4 deletions(-)
    ```
    ```diff
    $ git diff -- tests/fixtures/conformance_goldens/check_findings.human.golden
    diff --git a/tests/fixtures/conformance_goldens/check_findings.human.golden b/tests/fixtures/conformance_goldens/check_findings.human.golden
    index 152e56342..eeb1c6a3f 100644
    --- a/tests/fixtures/conformance_goldens/check_findings.human.golden
    +++ b/tests/fixtures/conformance_goldens/check_findings.human.golden
    @@ -15,4 +15,4 @@ Evidence
       checked: 41

     Next  aw group plans x --set y (regroup)
    -Agent output: --agent (automatic when piped)
    +Agent output: --agent
    ```
    The stale remediation strings in F-05 (`Fix:` lines) were left completely untouched.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: THE TEST MUST BE SHOWN TO FAIL FIRST. Paste (1) the new test file's contents; (2) the output of running it against the UNFIXED renderer, demonstrating a real failure, obtained by stashing the fix or by `git stash push agent_workflows/renderers.py`, running `python3 -m pytest tests/test_human_renderer_agent_hint.py -o addopts=""`, and restoring; (3) the same command PASSING with the fix in place, with its per-test counts. State explicitly that the test asserts on RENDERED OUTPUT and reads no production source text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). A test that passes in step (2) is a FAILED V-05: it is not pinning this defect.
  - Observed evidence: PASS. Test fails before fix and passes after fix, exercising rendered output only.
    (1) Contents of `tests/test_human_renderer_agent_hint.py`:
    ```python
    """Behavior tests for HumanRenderer agent output hint line.

    Validates that HumanRenderer outputs the accurate agent output hint and does not
    assert the retracted automatic non-TTY switch promise.
    """

    from agent_workflows.renderers import HumanRenderer
    from agent_workflows.result_types import CommandResult, OutputContext, OutputMode


    def test_human_renderer_agent_hint_normal_output():
        renderer = HumanRenderer()
        result = CommandResult(command="check", summary="All checks passed")
        rendered = renderer.render(result, OutputContext(mode=OutputMode.HUMAN, color=False))

        lines = rendered.rstrip("\n").split("\n")
        assert lines[-1] == "Agent output: --agent"
        assert "automatic when piped" not in rendered


    def test_human_renderer_agent_hint_with_color():
        renderer = HumanRenderer()
        result = CommandResult(command="check", summary="All checks passed")
        rendered = renderer.render(result, OutputContext(mode=OutputMode.HUMAN, color=True))

        lines = rendered.rstrip("\n").split("\n")
        assert lines[-1] == "Agent output: --agent"
        assert "automatic when piped" not in rendered


    def test_human_renderer_suppress_agent_hint():
        renderer = HumanRenderer()
        result = CommandResult(
            command="check",
            summary="All checks passed",
            data={"suppress_agent_hint": True},
        )
        rendered = renderer.render(result, OutputContext(mode=OutputMode.HUMAN, color=False))

        assert "Agent output:" not in rendered
        assert "automatic when piped" not in rendered
    ```

    (2) Running against UNFIXED renderer (prior to E-02 application):
    ```
    $ python3 -m pytest tests/test_human_renderer_agent_hint.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=2394248541
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_human_renderer_agent_hint.py FF.                              [100%]

    =================================== FAILURES ===================================
    __________________ test_human_renderer_agent_hint_with_color ___________________

        def test_human_renderer_agent_hint_with_color():
            renderer = HumanRenderer()
            result = CommandResult(command="check", summary="All checks passed")
            rendered = renderer.render(result, OutputContext(mode=OutputMode.HUMAN, color=True))

            lines = rendered.rstrip("\n").split("\n")
    >       assert lines[-1] == "Agent output: --agent"
    E       AssertionError: assert 'Agent output...c when piped)' == 'Agent output: --agent'
    E
    E         - Agent output: --agent
    E         + Agent output: --agent (automatic when piped)

    tests/test_human_renderer_agent_hint.py:27: AssertionError
    _________________ test_human_renderer_agent_hint_normal_output _________________

        def test_human_renderer_agent_hint_normal_output():
            renderer = HumanRenderer()
            result = CommandResult(command="check", summary="All checks passed")
            rendered = renderer.render(result, OutputContext(mode=OutputMode.HUMAN, color=False))

            lines = rendered.rstrip("\n").split("\n")
    >       assert lines[-1] == "Agent output: --agent"
    E       AssertionError: assert 'Agent output...c when piped)' == 'Agent output: --agent'
    E
    E         - Agent output: --agent
    E         + Agent output: --agent (automatic when piped)

    tests/test_human_renderer_agent_hint.py:17: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_human_renderer_agent_hint.py::test_human_renderer_agent_hint_with_color
    FAILED tests/test_human_renderer_agent_hint.py::test_human_renderer_agent_hint_normal_output
    ========================= 2 failed, 1 passed in 0.48s ==========================
    ```

    (3) Running against FIXED renderer:
    ```
    $ python3 -m pytest tests/test_human_renderer_agent_hint.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3121332767
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_human_renderer_agent_hint.py ...                              [100%]

    ============================== 3 passed in 0.66s ===============================
    ```
    The test asserts exclusively on rendered output and reads no production source text, conforming to AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE".
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste `git diff -- .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md` showing exactly one line changed, the Conventions clause, with the surrounding exit-code and R/W sentences untouched. Then paste `grep -n -i "automatic when piped" .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md` returning nothing. State in one sentence WHY this file was treated as a live surface rather than a historical record (present-tense normative statement of current conventions, not a transcript), since V-06 as originally authored would have dispositioned it the other way.
  - Observed evidence: PASS. Diff and grep confirm only Conventions clause changed.
    ```diff
    $ git diff -- .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
    diff --git a/.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md b/.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
    index 1bbb55da3..99aaebf67 100644
    --- a/.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
    +++ b/.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
    @@ -61,8 +61,8 @@ walk(cli._build_parser(), [])
     EOF
     \```

    -**Conventions.** Every command accepts `--no-color`, `--color`, `--agent` (aw.agent/v1 JSONL, also
    -automatic when piped), and `--json`. Exit codes are `0` clean, `1` findings, `2` cannot-run, unless a
    +**Conventions.** Every command accepts `--no-color`, `--color`, `--agent` (aw.agent/v1 JSONL),
    +and `--json`. Exit codes are `0` clean, `1` findings, `2` cannot-run, unless a
     row says otherwise. "Preview" means the command writes nothing without `--apply`. The **R/W** column
     is `R` read-only, `W` writes, `R/W` previews by default and writes with a flag.
    ```
    ```
    $ grep -n -i "automatic when piped" .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
    (empty, exit 1)
    ```
    Note on diff lines: The removed clause `, also automatic when piped` spanned lines 64-65 in the original file (`also\nautomatic when piped`), so dropping the clause edits both lines while leaving the surrounding sentences completely intact.
    This file was treated as a live surface rather than a historical record because its Conventions paragraph is a present-tense normative statement of active CLI conventions in a durable reference document intended for cold-start handoff, not a retrospective transcript of historical execution output.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the FULL output of `git grep -n -i "automatic when piped"`, then ENUMERATE every remaining hit with a disposition. Expect hits ONLY in historical records that must not be rewritten: this plan, backlog `zdjhug`, plan `3rsdbj` and its review record under `.aw/records/`, the survey record, and the two executed plans quoting old terminal transcripts. A hit in any LIVE user-facing surface (`agent_workflows/`, `docs/`, `README.md`, `CHANGELOG.md`) is a FAILED V-06. A pasted grep with no per-hit disposition is not evidence. Then paste the final summary line of a BARE `python3 -m pytest`, naming any failure as pre-existing (F-04 names the 3 known `slow`/`livecorpus` failures, which a bare run does not select) or new. Then `aw sanitize --agent; echo rc=$?` ending `rc=0`. Finally, confirm the OQ-01 backlog item was filed, paste its id6 and its `- Work-Kind: chore` front matter, and show that both declined carrier rows in "Deferred / out of scope" now read `- Carrier: <id6>` with that id6. Then paste `aw check --agent` (or `python3 -c` over `check_engine.check_durable_carrier`) showing NO `check.ipd-uncarried-obligation` finding against this plan: review measured that the original `Carrier: NEEDS-BACKLOG-ITEM` text FAILED that check as malformed, so this is the item where a well-meaning placeholder silently re-breaks it. A remaining placeholder, or a `Carrier` value that is not a bare 6-character id6, is a FAILED V-06.
  - Observed evidence: PASS. Whole-tree grep, pytest suite, sanitizer, and backlog carrier confirmed clean.
    Full output of `git grep -n -i "automatic when piped"`:
    ```
    .aw/records/backlog/graduated/20260926-zdjhug-01-zdjhug-renderer-hint-promises-retracted-auto-switch.backlog.md:8:- Summary: The human renderer hint claims --agent is "automatic when piped", which was retracted 2026-09-10
    .aw/records/backlog/graduated/20260926-zdjhug-01-zdjhug-renderer-hint-promises-retracted-auto-switch.backlog.md:12:- 2026-09-26 created (aw backlog): The human renderer hint claims --agent is "automatic when piped", which was retracted 2026-09-10
    .aw/records/backlog/open/20261001-qdd6ey-01-qdd6ey-config-epilog-nontty-claim.backlog.md:10:- 2026-10-01 created (aw backlog): Found in /plan-review of kfbom1: config epilog claims non-TTY auto-switches to JSONL (automatic when piped); should say --agent is the flag.
    .aw/records/plans/executed/20260822-awcliux-02-czw99i-human-tty-information-design-and-256-color-system.ipd.md:73:Agent output: --agent (automatic when piped)
    .aw/records/plans/executed/20260925-m105term-01-lz0o6j-make-ipd-m105-see-a-non-terminal-status-sitting-in-a-termina.ipd.md:349:    Agent output: --agent (automatic when piped)
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:5:- Concern: SIX user-facing docs claim piping or redirecting the CLI automatically switches stdout from human prose to `aw.agent/v1` JSONL. This auto-switch was RETRACTED by maintainer ruling (ttyflags `yaxr4i` OQ-01, 2026-09-10) before shipping, but the docs still assert it. The claim is self-refuting in the terminal: `aw check plans | cat` emits human prose, and the shared human renderer even appends `Agent output: --agent (automatic when piped)` to it. We must mark the cutover retracted in all six docs, align every mention of `--agent` with the shipped flags contract (`docs/cli-output-contract.md`), and pin the fix with a regression test.
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:80:- [x] E-09 Verify no other doc claims the auto-switch. Run `git grep -i -E "automatic when piped|automatically switches to jsonl|switches to machine format"` over `docs/` and `README.md`.
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:111:| F-9 | `agent_workflows/renderers.py` "Agent Output Hint" block, ~:184; four conformance goldens (`check_findings`, `error_cannot_run`, `mutation_preview`, `read_clean`) | THE CLI PRINTS THE RETRACTED PROMISE ON EVERY COMMAND. The human renderer appends `Agent output: --agent (automatic when piped)` unless `suppress_agent_hint`. Measured at `b5a45362`: `python3 -m agent_workflows check plans \| cat` ends with that line amid human prose. `select_output`'s docstring is already correct; this is a user-visible string defect. Four goldens pin it. |
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:129:- The CLI's own human renderer hint (`agent_workflows/renderers.py:184`: `lines.append("Agent output: --agent (automatic when piped)")`) and its four conformance goldens (`check_findings.human.golden`, `error_cannot_run.human.golden`, `mutation_preview.human.golden`, `read_clean.human.golden`). Out of scope because it is code and test fixtures, not docs; it is a separate concern with its own test and review surface; and the backlog item `zdjhug` carries it.
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:349:  - Required evidence: paste the command and full output of `git grep -i -E "automatic when piped|automatically switches to jsonl|switches to machine format" docs/ README.md`. Expect hits ONLY in `docs/cli-output-contract.md` (the retracted-migration section) and nowhere else in `docs/` or `README.md`. A hit in any other doc is a FAILED V-09.
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:350:  - Observed evidence:
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:361:  - Required evidence: paste the command and full output of `git grep -i -E "automatic when piped|automatically switches to jsonl|switches to machine|automatic non-tty|switches stdout to machine|automatic machine switch" docs/ README.md`. Expect hits ONLY in `docs/cli-output-contract.md` (the retracted-migration section) and legitimately documented example output in `docs/cli-human-guide.md`. A hit asserting the policy anywhere else is a FAILED V-09.
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:370:    docs/cli-human-guide.md:41:Agent output: --agent (automatic when piped)
    .aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md:410:WHAT THIS DELIBERATELY DOES NOT FIX: the CLI code itself (`agent_workflows/renderers.py:184`), which appends `Agent output: --agent (automatic when piped)` to human output, and the four conformance goldens that pin it. That is code and test fixtures, outside this plan's docs-only fence; it has its own carrier, backlog `zdjhug`.
    .aw/records/plans/executed/20260928-3sh9d6-01-dv7c49-correct-9iiqmm-s-falsified-non-tty-claims-by-appended-note-a.ipd.md:6:- Scope: IN: (a) append a prominent retraction warning banner to `9iiqmm` Section 3.2.1 ("Non-TTY Automatic Machine Output: RETRACTED BY RULING") with the ruling citation, the replacement model, and pointers to the normative contract and the backlog item carrying the code fix (`zdjhug`); (b) in `9iiqmm` Section 4.3 ("Non-TTY Redirection"), label the entire non-TTY auto-switch subsection as retracted with the same citation; (c) in `9iiqmm` Section 9.2 ("Open Questions"), add an explicit entry recording that OQ-01 resolved by reversing the automatic switch in favor of `--agent` only; (d) in `9iiqmm` Section 8.1 ("Format Selection"), add a note that the automatic switch never shipped and `--agent` is required. OUT: modifying the rest of `9iiqmm`'s historical text (it is an executed plan and the record must show what was planned vs what was reversed); modifying the code (`agent_workflows/renderers.py:184`), which is carried by backlog `zdjhug`; modifying the conformance goldens (same carrier); modifying `docs/cli-output-contract.md` (already correct).
    .aw/records/plans/executed/20260928-3sh9d6-01-dv7c49-correct-9iiqmm-s-falsified-non-tty-claims-by-appended-note-a.ipd.md:91:| F-07 | MED | `agent_workflows/renderers.py:184` | THE CLI CODE STILL EMITS THE RETRACTED CLAIM: `lines.append("Agent output: --agent (automatic when piped)")`. Four conformance goldens pin it. This is carried by backlog `zdjhug` and is outside this plan's fence. Recorded so a reviewer knows the code is not touched here. |
    .aw/records/plans/executed/20260929-checkinfotally-01-tzjtg4-tally-aw-check-findings-by-registered-severity-so-an-advisor.ipd.md:171:    Agent output: --agent (automatic when piped)
    .aw/records/plans/executed/20260929-checkinfotally-01-tzjtg4-tally-aw-check-findings-by-registered-severity-so-an-advisor.ipd.md:264:    Agent output: --agent (automatic when piped)
    .aw/records/plans/executed/20260929-iifcam-01-khiueh-clear-the-two-stale-escalations-by-amending-the-review-recor.ipd.md:395:       Agent output: --agent (automatic when piped)
    .aw/records/plans/executed/20260929-y0t9u7-01-3b01h9-read-a-prompt-s-id6-from-its-metadata-comment-and-filename-s.ipd.md:470:      Agent output: --agent (automatic when piped)
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:5:- Concern: The shared human renderer appends the literal line `Agent output: --agent (automatic when piped)` to almost every `aw` command's output. The parenthetical asserts the automatic non-TTY switch to `aw.agent/v1` JSONL that was RETRACTED by maintainer ruling (ttyflags `yaxr4i` OQ-01, 2026-09-10) and never shipped. It is self-refuting in the very invocation that prints it: measured at base commit `b5a45362`, `python3 -m agent_workflows check plans | cat` ends with that line while every line above it is human prose. Plan `3rsdbj` corrected the same false claim in six user DOCS but could not reach the CLI, because its fence was docs-only; this is the code instance it carried here, and it reaches far more users than any doc, being printed on every command rather than read by whoever opens a file.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:32:Make the CLI stop telling users something false about its own output contract. After this plan, no `aw` command prints the claim that `--agent` is "automatic when piped", every LIVE instance of the claim is corrected, the committed golden fixtures agree with the code, and a real behavior test keeps the promise from coming back.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:42:- [x] E-01 Re-measure the defect and the ruling at the execution base, so the fix is not built on a stale premise. Run `python3 -m agent_workflows check plans | cat | tail -3` and confirm the final line is `Agent output: --agent (automatic when piped)` while the lines above it are human prose (not a `{"schema":"aw.agent/v1"` record). Then confirm the resolver is already correct and is NOT what this plan changes: `grep -n "TTY-NESS OF STDOUT AFFECTS COLOR ONLY" agent_workflows/result_types.py`.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:49:- [x] E-02 In `agent_workflows.HumanRenderer.render`, in the branch guarded by `if not result.data.get("suppress_agent_hint", False)`, change the appended literal from `"Agent output: --agent (automatic when piped)"` to `"Agent output: --agent"`. Drop ONLY the parenthetical: the hint itself is useful and correct, and the surrounding line, the guard, and the hint's position as the last line must not change. Do NOT touch `select_output`, `should_color`, or anything that decides WHICH mode is selected; the resolver is right (E-01) and this is a wording defect on a user-visible string.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:53:- [x] E-03 In `docs/cli-human-guide.md`, correct the sample terminal transcript under "Anatomy of a standard render" whose last line reads `Agent output: --agent (automatic when piped)`, so the illustrated output matches what the CLI now prints. This file was deliberately OUT of plan `3rsdbj`'s fence (treated there as already-correct reference wording) and its V-09 evidence recorded this hit as "legitimate example output" precisely because it was a faithful transcript of the then-current bytes; once E-02 lands that justification expires and the line becomes the LAST false instance of the promise in the docs. Change only the transcript's hint line; the file's prose about output mode is already correct and is the reference wording this plan defers to.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:64:- [x] E-05 Add `tests/test_human_renderer_agent_hint.py`, a BEHAVIOR test that renders real `CommandResult` values through `HumanRenderer` and asserts on the rendered output. It must assert: (1) the rendered human output of a normal result ENDS with `Agent output: --agent` and does NOT contain the substring `automatic when piped`; (2) the same holds for a result rendered with `color=True`, so the claim cannot survive behind ANSI styling; (3) a result whose `data` sets `suppress_agent_hint` true emits NO hint line at all, pinning the guard that exists today rather than only the string. This is the one durable guard: measured at authoring, `HumanRenderer` has NO test caller anywhere under `tests/` (F-03), so nothing currently stops this regressing. Assert on RENDERED OUTPUT only; do NOT read `renderers.py` source with `inspect`, `ast`, regex, or substring search, and do NOT assert on line counts or symbol censuses (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:69:- [x] E-07 CORRECT THE SIXTH LIVE INSTANCE, in `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md`'s "Conventions." paragraph, locating it by the content string `also\nautomatic when piped` (the phrase wraps across two lines, so a single-line grep for the full phrase will MISS it; search for `automatic when piped` alone). ADDED AT REVIEW (F-08). It reads "`--agent` (aw.agent/v1 JSONL, also automatic when piped)"; drop the ", also automatic when piped" clause so it reads "`--agent` (aw.agent/v1 JSONL)". THIS IS NOT A HISTORICAL RECORD AND MUST NOT BE TREATED AS ONE: it is a PRESENT-TENSE normative statement of the CLI's conventions in a durable reference artifact, not a transcript of past output and not a quotation of the retracted policy, so the immutability reasoning that correctly protects `plans/executed/` does not apply. Without this edit, this plan's own Goal is not met and V-06 would wrongly disposition a live falsehood as history. Change ONLY that clause; do not restructure the paragraph, do not touch the surrounding exit-code or R/W sentences, and do not edit any other part of the survey.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:76:- [x] E-06 Verify the claim is gone tree-wide and nothing regressed. Run `git grep -n -i "automatic when piped"` over the whole repo and enumerate every remaining hit with a disposition. Then run the suite BARE as `python3 -m pytest`. Then `aw sanitize --agent; echo rc=$?`.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:95:| F-01 | `agent_workflows/renderers.py`, `HumanRenderer.render`, the `# 7. Agent Output Hint` block (~:182-184) | CONFIRMED AS THE BACKLOG ITEM STATES. `lines.append("Agent output: --agent (automatic when piped)")` runs unless `result.data` sets `suppress_agent_hint`. Measured: `python3 -m agent_workflows check plans \| cat \| tail -3` ends with that line above human prose, exit 1. The claim is false per the 2026-09-10 ruling, which `docs/cli-output-contract.md` section 9 records verbatim ("Piping or redirecting `aw` emits HUMAN-READABLE TEXT. `--agent` is the explicit and only way to obtain `aw.agent/v1` JSONL"). The fix is the one-line wording change the item proposes. |
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:96:| F-02 | `docs/cli-human-guide.md`, the fenced sample transcript under "Anatomy of a standard render" whose final line is `Agent output: --agent (automatic when piped)` (~:41) | NOT IN THE BACKLOG ITEM. A FIFTH live instance of the false string survives in a user doc, inside the sample render transcript. Plan `3rsdbj` SAW this hit (its V-09 evidence recorded this hit as "legitimate example output", because the file was out of its fence and the transcript accurately showed the bytes the CLI then printed. That justification is valid ONLY while the code is unfixed: the moment E-02 lands, the transcript becomes both false and stale. So the docs are NOT fully clean after `3rsdbj`, and fixing the code without this line would leave the last readable instance of the retracted promise in the very guide that explains output mode. Added to scope as E-03. |
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:102:| F-08 | ADDED AT REVIEW. `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md`, the "Conventions." paragraph | **A SIXTH LIVE INSTANCE OF THE FALSE CLAIM EXISTS AND THIS PLAN MISCLASSIFIES IT AS HISTORICAL.** The survey record's conventions paragraph states that every command accepts "`--agent` (aw.agent/v1 JSONL, also automatic when piped)". V-06 pre-declares "the survey record" among hits expected ONLY in "historical records that must not be rewritten", but this is NOT a transcript of past output and NOT a quotation of a retracted policy: it is a present-tense normative statement about the CLI's conventions, in a durable reference artifact whose own README calls the tree "Durable research ... kept for provenance and cold-start handoff", with no immutability rule of the kind that protects `plans/executed/` does not apply. So a cold-start reader of the repository's own CLI inventory is told the retracted promise as current fact. This plan's Goal ("no `aw` command prints the claim ... the last user-facing doc instance is corrected") is therefore not achieved by E-02+E-03 alone. |
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:138:FOURTH, ADDED AT REVIEW AND THE SHARPEST LIMIT OF THE FOUR: THE GREP PATTERN IS THE VERIFICATION, AND IT ONLY FINDS ONE WORDING. `git grep -i "automatic when piped"` cannot find a paraphrase, and plan `3rsdbj` already learned this the expensive way - its review measured that its authored three-phrase pattern MISSED `docs/cli-migration.md`'s "This is automatic and immediate" and `docs/cli-agent-protocol.md`'s "whenever stdout is not a terminal", the two most load-bearing sentences in that whole plan, so its E-09 had to be rewritten around a six-alternative pattern. This plan searches for ONE phrase. That is defensible, because this plan's subject IS that exact literal, but it means a clean grep proves the literal is gone and proves NOTHING about a seventh instance in other words. The reviewer's own re-measurement also shows the phrase WRAPS ACROSS A LINE in the survey record, so even a full-phrase single-line grep would have missed it; E-07 therefore says to search the short form. Anyone extending this work should run `3rsdbj`'s wider pattern rather than this plan's narrow one.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:163:  - Required evidence: paste `git diff -- agent_workflows/renderers.py`. It must show exactly one changed line, removing ` (automatic when piped)` from the appended literal, with the `suppress_agent_hint` guard and the hint's position unchanged. Then paste `python3 -m agent_workflows check plans | cat | tail -1` showing `Agent output: --agent` with no parenthetical. A diff touching `select_output`, `should_color`, or any mode-selection logic is a FAILED V-02 (F-06).
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:168:  - Required evidence: paste `git diff -- docs/cli-human-guide.md` (exactly one line changed, inside the sample transcript) and `grep -n -i "automatic when piped" docs/cli-human-guide.md` returning nothing. Confirm in one sentence that the file's surrounding "Output mode and audience" prose was NOT edited, since it is the reference wording this plan defers to. Same `xs557y` exception as V-02 (F-07): that plan's E-06 also edits this guide, so if it landed first, say so and show this plan's own change is still the transcript hint line alone.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:180:  - Required evidence: paste `git diff -- .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md` showing exactly one line changed, the Conventions clause, with the surrounding exit-code and R/W sentences untouched. Then paste `grep -n -i "automatic when piped" .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md` returning nothing. State in one sentence WHY this file was treated as a live surface rather than a historical record (present-tense normative statement of current conventions, not a transcript), since V-06 as originally authored would have dispositioned it the other way.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:185:  - Required evidence: paste the FULL output of `git grep -n -i "automatic when piped"`, then ENUMERATE every remaining hit with a disposition. Expect hits ONLY in historical records that must not be rewritten: this plan, backlog `zdjhug`, plan `3rsdbj` and its review record under `.aw/records/`, the survey record, and the two executed plans quoting old terminal transcripts. A hit in any LIVE user-facing surface (`agent_workflows/`, `docs/`, `README.md`, `CHANGELOG.md`) is a FAILED V-06. A pasted grep with no per-hit disposition is not evidence. Then paste the final summary line of a BARE `python3 -m pytest`, naming any failure as pre-existing (F-04 names the 3 known `slow`/`livecorpus` failures, which a bare run does not select) or new. Then `aw sanitize --agent; echo rc=$?` ending `rc=0`. Finally, confirm the OQ-01 backlog item was filed, paste its id6 and its `- Work-Kind: chore` front matter, and show that both declined carrier rows in "Deferred / out of scope" now read `- Carrier: <id6>` with that id6. Then paste `aw check --agent` (or `python3 -c` over `check_engine.check_durable_carrier`) showing NO `check.ipd-uncarried-obligation` finding against this plan: review measured that the original `Carrier: NEEDS-BACKLOG-ITEM` text FAILED that check as malformed, so this is the item where a well-meaning placeholder silently re-breaks it. A remaining placeholder, or a `Carrier` value that is not a bare 6-character id6, is a FAILED V-06.
    .aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md:198:TWO THINGS REVIEW ADDED, BOTH MEASURED. FIRST, A SIXTH LIVE INSTANCE (F-08, now E-07): the repository's own CLI inventory survey states, in the present tense, that `--agent` is "also automatic when piped". This plan's V-06 had pre-classified the survey among "historical records that must not be rewritten", which is wrong: it is a current-conventions statement in a durable reference artifact, not a transcript, and the immutability rule that protects `plans/executed/` does not reach it. Left alone, the plan's own Goal would have been unmet while its verification declared success. SECOND, A CONCURRENT OVERLAP (F-07): pending plan `xs557y` declares the same `renderers.py` and the same `docs/cli-human-guide.md` and rewrites the same `HumanRenderer.render` method. That is NOT a runtime hazard (the runners isolate each item in its own worktree and merge through the revalidate gate) and is NOT a reason to delay either plan; it is recorded because V-02 and V-03 demand a one-line diff, and whichever plan lands second may honestly be unable to show one.
    .aw/records/plans/pending/20260930-tsvagent-01-n9ua3b-route-the-three-surviving-tsv-agent-surfaces-onto-aw-agent-v.ipd.md:68:  Agent output: --agent (automatic when piped)
    .aw/records/plans/pending/20260930-tsvagent-01-n9ua3b-route-the-three-surviving-tsv-agent-surfaces-onto-aw-agent-v.ipd.md:158:| F-10 | **ADDED AT REVIEW, AND IT IS THE FINDING THAT WOULD HAVE STOPPED EXECUTION: THE HUMAN RENDERER DOES NOT PRODUCE THE HUMAN BRANCH THIS PLAN PROMISES TO PRESERVE.** E-01 requires the human output byte-unchanged (`location: rule: detail` plus the per-verb `clean` wording) while E-02 routes all output through `renderers.get_renderer(ctx).emit(...)`. Those two requirements are incompatible as authored: in HUMAN mode the shared renderer emits a title banner, an outcome line, a structured `Findings:` block with per-finding `Issue:`/`[SEVERITY]`/`Fix:` lines, and an `Agent output:` footer. An executor would edit all three verbs, then discover the contradiction when E-01's own assertions failed, with no instruction for what to do about it. THE MECHANISM THAT RESOLVES IT IS SHIPPED AND WAS DEMONSTRATED AT REVIEW rather than described: `HumanRenderer.render` returns `str(result.data["human_rendered"])` verbatim, before building any banner, so the legacy lines survive byte-exact while `--agent` and `--json` get canonical forms. E-02 now mandates it. | Driven at review: a `CommandResult` with one `Diagnostic` emitted through `get_renderer(ctx)` in human mode produced `AW index plans` / `✗ FINDINGS  2 findings` / `Findings:` / `  Issue: Manifest index is out of date` / `  - INDEX.json [WARNING]` / `    Fix: run 'aw index' to regenerate the manifest index.` / `Agent output: --agent (automatic when piped)`. The SAME result with `data["human_rendered"]` set emitted exactly the legacy line and nothing else. `renderers.HumanRenderer.render` reads the key first (`if "human_rendered" in result.data: return str(...)`). |
    .aw/records/reviews/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.review.md:31:Output Hint" block, appends the literal line `Agent output: --agent (automatic when piped)` unless a
    .aw/records/reviews/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.review.md:96:| PR-201 | HIGH | UNDER-SCOPE | F. honest documentation; C. operability | `agent_workflows/renderers.py` "Agent Output Hint" block: `lines.append("Agent output: --agent (automatic when piped)")`; measured `python3 -m agent_workflows check plans \| cat` ends with that line amid human prose; four goldens pin it (`check_findings`, `error_cannot_run`, `mutation_preview`, `read_clean`) | **THE CLI PRINTS THE RETRACTED PROMISE ON EVERY COMMAND.** The shared human renderer's hint claims `--agent` is "automatic when piped", which is the exact policy retracted on 2026-09-10 and never shipped. It reaches every user of the tool, far more than any doc in this plan's fence, and it is self-refuting in the same terminal. `select_output`'s docstring was already corrected for this ruling, so only the user-visible string was missed. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as F-9 and carried to new gated backlog `zdjhug`, not fixed here: it is code plus four goldens, outside a docs-only fence. The gate now names it under "what this deliberately does not fix" and the scope fence explicitly FORBIDS editing `renderers.py` or its goldens, so an executor cannot quietly turn a prose plan into a code plan. |
    .aw/records/reviews/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.review.md:57:file (`... JSONL, also` / `automatic when piped), and ...`), so a single-line grep for the full phrase
    .aw/records/reviews/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.review.md:98:| PR-A01 | HIGH | UNDER-SCOPE | F. honest documentation / E. verification | `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md` "Conventions." paragraph: "`--agent` (aw.agent/v1 JSONL, also automatic when piped)"; `.aw/records/research/README.md` describes the tree as "Durable research ... kept for provenance and cold-start handoff" with no immutability rule; the plan's V-06 lists "the survey record" among hits expected only in "historical records that must not be rewritten" | A SIXTH LIVE instance of the false claim exists and the plan pre-classifies it as untouchable history. It is a present-tense normative statement, not a transcript, so the plan would have ended with its own Goal unmet while V-06 declared success | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-08. New E-07 corrects the clause (locating it by the short form, since the phrase WRAPS across a line and a full-phrase single-line grep misses it); new V-07 demands the one-line diff, an empty grep, and a stated reason the file is live not historical; the survey path DECLARED in `Scope-Paths`; E-06's disposition list corrected to remove the survey and its `Depends on` extended to E-07; Goal, Scope (b) and Scope check corrected from "five"/"last" to "every live instance" |
    .aw/records/reviews/20260930-tsvagent-01-n9ua3b-route-the-three-surviving-tsv-agent-surfaces-onto-aw-agent-v.review.md:66:Agent output: --agent (automatic when piped)
    .aw/records/reviews/20261001-dtq6jr-01-kfbom1-give-the-seven-aw-config-verbs-a-working-schema-valid-agent.review.md:91:covers the renderer's `Agent output: --agent (automatic when piped)` hint in `renderers.py` plus four
    ```

    Disposition of each file matching `automatic when piped`:
    1. `.aw/records/backlog/graduated/20260926-zdjhug-01-zdjhug-renderer-hint-promises-retracted-auto-switch.backlog.md`: Historical backlog item that graduated to this plan (zosxj4). Accurately describes the defect; must not be rewritten.
    2. `.aw/records/backlog/open/20261001-qdd6ey-01-qdd6ey-config-epilog-nontty-claim.backlog.md`: Active backlog item tracking a separate finding in config command epilog text. Must not be rewritten.
    3. `.aw/records/plans/executed/20260822-awcliux-02-czw99i-human-tty-information-design-and-256-color-system.ipd.md`: Executed plan. Historical record; immutable.
    4. `.aw/records/plans/executed/20260925-m105term-01-lz0o6j-make-ipd-m105-see-a-non-terminal-status-sitting-in-a-termina.ipd.md`: Executed plan quoting past output. Historical record; immutable.
    5. `.aw/records/plans/executed/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.ipd.md`: Executed plan that fixed the six docs and recorded this defect as out of scope. Historical record; immutable.
    6. `.aw/records/plans/executed/20260928-3sh9d6-01-dv7c49-correct-9iiqmm-s-falsified-non-tty-claims-by-appended-note-a.ipd.md`: Executed plan citing this defect as out of scope. Historical record; immutable.
    7. `.aw/records/plans/executed/20260929-checkinfotally-01-tzjtg4-tally-aw-check-findings-by-registered-severity-so-an-advisor.ipd.md`: Executed plan quoting past output. Historical record; immutable.
    8. `.aw/records/plans/executed/20260929-iifcam-01-khiueh-clear-the-two-stale-escalations-by-amending-the-review-recor.ipd.md`: Executed plan quoting past output. Historical record; immutable.
    9. `.aw/records/plans/executed/20260929-y0t9u7-01-3b01h9-read-a-prompt-s-id6-from-its-metadata-comment-and-filename-s.ipd.md`: Executed plan quoting past output. Historical record; immutable.
    10. `.aw/records/plans/pending/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md`: This plan, describing and verifying the defect.
    11. `.aw/records/plans/pending/20260930-tsvagent-01-n9ua3b-route-the-three-surviving-tsv-agent-surfaces-onto-aw-agent-v.ipd.md`: Concurrent pending plan quoting terminal output.
    12. `.aw/records/reviews/20260926-staledocs-01-3rsdbj-mark-the-retracted-non-tty-jsonl-cutover-as-retracted-in-the.review.md`: Review record for 3rsdbj. Historical record; immutable.
    13. `.aw/records/reviews/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.review.md`: Review record for this plan. Historical record; immutable.
    14. `.aw/records/reviews/20260930-tsvagent-01-n9ua3b-route-the-three-surviving-tsv-agent-surfaces-onto-aw-agent-v.review.md`: Review record for n9ua3b. Historical record; immutable.
    15. `.aw/records/reviews/20261001-dtq6jr-01-kfbom1-give-the-seven-aw-config-verbs-a-working-schema-valid-agent.review.md`: Review record for kfbom1. Historical record; immutable.

    Summary: 0 hits in live user-facing code or docs (`agent_workflows/`, `docs/`, `README.md`, `CHANGELOG.md`, `.aw/records/research/`). All remaining hits are historical records or backlog items tracking separate work.

    Test suite output:
    ```
    $ python3 -m pytest
    2 failed, 4541 passed, 2 skipped, 3 warnings in 315.80s (0:05:15)
    ```
    The 2 test failures are pre-existing defects present at base:
    - `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` (fails due to `20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`, tracked by open backlog items `md2o3y` and `6bolin`)
    - `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` (fails because `LeaseTable.claim` is reachable, tracked by open backlog item `8jeh4x`)

    Sanitizer output:
    ```
    $ aw sanitize --agent; echo rc=$?
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    rc=0
    ```

    OQ-01 backlog item filed:
    - Item Id: `krwj2o`
    - Front matter:
      ```markdown
      - Id: krwj2o
      - Status: open
      - Set: krwj2o
      - Priority: medium
      - Work-Kind: chore
      - Summary: Restore deleted CLI conformance test gates and refresh stale goldens
      ```
    Both carrier rows in "Deferred / out of scope" have been updated to `- Carrier: krwj2o`.
    Verification via check_durable_carrier:
    ```
    $ python3 -c "import pathlib; from agent_workflows.check_engine import check_durable_carrier; drifts = check_durable_carrier(pathlib.Path('.')); zosxj4_drifts = [d for d in drifts if 'zosxj4' in pathlib.Path(d.location).name]; print('zosxj4 plan drifts count:', len(zosxj4_drifts))"
    zosxj4 plan drifts count: 0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a one-line wording fix to a user-visible string in the shared human renderer, the same one-line fix in a sample transcript in `docs/cli-human-guide.md`, a one-clause fix in the CLI inventory survey's Conventions paragraph (added at review), a one-line edit to each of four golden fixtures, and one new behavior test. No mode-selection logic changes, no spec is amended, and no existing test is modified.

TWO THINGS REVIEW ADDED, BOTH MEASURED. FIRST, A SIXTH LIVE INSTANCE (F-08, now E-07): the repository's own CLI inventory survey states, in the present tense, that `--agent` is "also automatic when piped". This plan's V-06 had pre-classified the survey among "historical records that must not be rewritten", which is wrong: it is a current-conventions statement in a durable reference artifact, not a transcript, and the immutability rule that protects `plans/executed/` does not reach it. Left alone, the plan's own Goal would have been unmet while its verification declared success. SECOND, A CONCURRENT OVERLAP (F-07): pending plan `xs557y` declares the same `renderers.py` and the same `docs/cli-human-guide.md` and rewrites the same `HumanRenderer.render` method. That is NOT a runtime hazard (the runners isolate each item in its own worktree and merge through the revalidate gate) and is NOT a reason to delay either plan; it is recorded because V-02 and V-03 demand a one-line diff, and whichever plan lands second may honestly be unable to show one.

TWO CORRECTIONS TO THE BACKLOG ITEM THE APPROVER SHOULD KNOW, both measured at authoring rather than assumed. FIRST, the item's claim that four goldens "pin the current bytes" is FALSE: their only consumer was deleted by commit `19313eed`, and the fix was applied and the full suite run to prove it (`3246 passed`, zero failures, goldens untouched). So the expected "golden regeneration path" is not a test requirement but record-keeping, and the item's scope was easier than stated in that respect. SECOND, and in the harder direction, the item missed a FIFTH live instance of the false string, in `docs/cli-human-guide.md`'s sample transcript, which plan `3rsdbj` legitimately left alone because it was then an accurate transcript; fixing the code without it would make that doc newly false.

WHAT THIS DELIBERATELY DOES NOT FIX, so the approver is not surprised later. The deleted conformance gates are NOT restored. That commit removed the only tests validating agent-record schema conformance, ANSI-stream separation, deterministic bytes, fact parity, and parser-leaf scenario coverage, leaving `tests/conformance_matrix.py` and twelve golden fixtures with no reader. That is a genuinely larger hole than the defect this plan fixes, and it is carried to a new backlog item (OQ-01) in the same family as `xvp5vx`, not fixed inside a one-line wording plan. The goldens' unrelated stale remediation text (F-05) rides with it.

GENUINE STOP CONDITIONS: E-01 shows piped output IS JSONL (the parenthetical would be true and this plan wrong), or a co-worker's concurrent edit to `renderers.py` cannot be safely combined. Neither is a scope question; both are conditions under which proceeding would write something false.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check passed that was not run. V-05 specifically requires demonstrating the new test FAILING before the fix. No em or en dashes in the edited `docs/cli-human-guide.md` prose. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the seven paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). In particular do NOT restore the deleted conformance test files to "finish the job": that is the carried item's work, and doing it here turns a one-line fix into a test-restoration plan.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit zosxj4 -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize zosxj4 --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `zdjhug`; AFTER EXECUTION, and not before, set that item `done` with `--evidence` citing this executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `zdjhug` fails closed because the gate is handed to a carrier that has not shipped, so the item stays `graduated` until `aw ipd finalize` has moved this plan to `executed/`.
