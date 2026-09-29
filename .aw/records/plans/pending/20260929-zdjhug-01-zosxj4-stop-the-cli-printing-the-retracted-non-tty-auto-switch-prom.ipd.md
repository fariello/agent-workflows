# IPD: Stop the CLI printing the retracted non-TTY auto-switch promise in its agent-output hint

- Date: 2026-09-29
- Kind: child
- Concern: The shared human renderer appends the literal line `Agent output: --agent (automatic when piped)` to almost every `aw` command's output. The parenthetical asserts the automatic non-TTY switch to `aw.agent/v1` JSONL that was RETRACTED by maintainer ruling (ttyflags `yaxr4i` OQ-01, 2026-09-10) and never shipped. It is self-refuting in the very invocation that prints it: measured at base commit `b5a45362`, `python3 -m agent_workflows check plans | cat` ends with that exact line while every line above it is human prose. Plan `3rsdbj` corrected the same false claim in six user DOCS but could not reach the CLI, because its fence was docs-only; this is the code instance it carried here, and it reaches far more users than any doc, being printed on every command rather than read by whoever opens a file.
- Scope: IN: (a) the one-line wording fix in `agent_workflows.HumanRenderer.render`'s agent-output-hint branch, dropping the false parenthetical; (b) the ONE remaining false instance of the same string in user docs, the sample terminal transcript in `docs/cli-human-guide.md` "Anatomy of a standard render", which `3rsdbj` could not reach because that file was explicitly OUT of its fence as already-correct reference wording, and which is now the last place a reader can see the retracted promise; (c) refreshing the four `*.human.golden` conformance fixtures that record this renderer's bytes, so the committed record of the hint does not contradict the code; (d) a NEW behavior test that pins the absence of the false promise in rendered human output, because the renderer currently has NO test caller at all and a one-line string is otherwise free to regress. OUT: restoring the deleted conformance gates that used to consume those goldens (F-04; it is a much larger job, it belongs to the suite-trim restoration family, and it is carried by a new backlog item rather than smuggled in here); correcting the two goldens' UNRELATED stale remediation text (F-05, same carrier); `agent_workflows.result_types.select_output` and `should_color`, whose docstrings and behavior are already correct for this ruling and are the reason only this user-visible string was wrong; the six docs `3rsdbj` already fixed; and any change to WHEN machine output is selected, which is behavior this plan must not touch.
- Scope-Paths: agent_workflows/renderers.py, docs/cli-human-guide.md, tests/fixtures/conformance_goldens/check_findings.human.golden, tests/fixtures/conformance_goldens/error_cannot_run.human.golden, tests/fixtures/conformance_goldens/mutation_preview.human.golden, tests/fixtures/conformance_goldens/read_clean.human.golden, tests/test_human_renderer_agent_hint.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: zdjhug
- Blocks-Release: next
- Set: zdjhug
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: zosxj4

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog zdjhug. Authoring measurement CORRECTED the item's stated scope on two counts: the four goldens are ORPHANED (their sole consumer was deleted, so they pin nothing and the suite passes with the fix alone), and a FIFTH false instance survives in docs/cli-human-guide.md. See F-02, F-03, F-04.
- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the CLI stop telling users something false about its own output contract. After this plan, no `aw` command prints the claim that `--agent` is "automatic when piped", the last user-facing doc instance is corrected, the committed golden fixtures agree with the code, and a real behavior test keeps the promise from coming back.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the premise before changing anything

- [ ] E-01 Re-measure the defect and the ruling at the execution base, so the fix is not built on a stale premise. Run `python3 -m agent_workflows check plans | cat | tail -3` and confirm the final line is `Agent output: --agent (automatic when piped)` while the lines above it are human prose (not a `{"schema":"aw.agent/v1"` record). Then confirm the resolver is already correct and is NOT what this plan changes: `grep -n "TTY-NESS OF STDOUT AFFECTS COLOR ONLY" agent_workflows/result_types.py`.
  - Depends on: none
  - Expected outcome: the false line is printed at the foot of PIPED human output (the self-refutation), and `select_output`'s docstring already records that TTY-ness affects color only. STOP AND REPORT if piped output is actually JSONL: the parenthetical would then be true and this plan's premise wrong.
  - Execution state: pending

### Task group 2: Fix the false claim

- [ ] E-02 In `agent_workflows.HumanRenderer.render`, in the branch guarded by `if not result.data.get("suppress_agent_hint", False)`, change the appended literal from `"Agent output: --agent (automatic when piped)"` to `"Agent output: --agent"`. Drop ONLY the parenthetical: the hint itself is useful and correct, and the surrounding line, the guard, and the hint's position as the last line must not change. Do NOT touch `select_output`, `should_color`, or anything that decides WHICH mode is selected; the resolver is right (E-01) and this is a wording defect on a user-visible string.
  - Depends on: E-01
  - Expected outcome: the renderer's hint names the flag without asserting when it is selected. No behavior other than this one string changes.
  - Execution state: pending
- [ ] E-03 In `docs/cli-human-guide.md`, correct the sample terminal transcript under "Anatomy of a standard render" whose last line reads `Agent output: --agent (automatic when piped)`, so the illustrated output matches what the CLI now prints. This file was deliberately OUT of plan `3rsdbj`'s fence (treated there as already-correct reference wording) and its V-09 evidence recorded this hit as "legitimate example output" precisely because it was a faithful transcript of the then-current bytes; once E-02 lands that justification expires and the line becomes the LAST false instance of the promise in the docs. Change only the transcript's hint line; the file's prose about output mode is already correct and is the reference wording this plan defers to.
  - Depends on: E-02
  - Expected outcome: no user-facing doc asserts the retracted auto-switch in any wording, and the guide's transcript is a truthful sample of real output.
  - Execution state: pending

### Task group 3: Make the committed record agree, and keep it agreeing

- [ ] E-04 Refresh the four human golden fixtures that record this renderer's bytes (`tests/fixtures/conformance_goldens/{check_findings,error_cannot_run,mutation_preview,read_clean}.human.golden`), changing ONLY their final hint line to match E-02. Do NOT regenerate them wholesale: measured at authoring (F-05), `check_findings.human.golden` is ALSO stale on two unrelated remediation strings, and a blanket regeneration would silently fold that drift into this commit, making the diff unreviewable and claiming a fix this plan did not make. Edit the hint line in each file and leave every other byte alone. Note these fixtures are currently ORPHANED (F-04): nothing reads them, so this edit is about not committing a record that contradicts the code, NOT about making a test pass.
  - Depends on: E-02
  - Expected outcome: each of the four files differs from its base version on exactly one line, the hint line; `git diff --stat` shows `1 insertion, 1 deletion` per file.
  - Execution state: pending
- [ ] E-05 Add `tests/test_human_renderer_agent_hint.py`, a BEHAVIOR test that renders real `CommandResult` values through `HumanRenderer` and asserts on the rendered output. It must assert: (1) the rendered human output of a normal result ENDS with `Agent output: --agent` and does NOT contain the substring `automatic when piped`; (2) the same holds for a result rendered with `color=True`, so the claim cannot survive behind ANSI styling; (3) a result whose `data` sets `suppress_agent_hint` true emits NO hint line at all, pinning the guard that exists today rather than only the string. This is the one durable guard: measured at authoring, `HumanRenderer` has NO test caller anywhere under `tests/` (F-03), so nothing currently stops this regressing. Assert on RENDERED OUTPUT only; do NOT read `renderers.py` source with `inspect`, `ast`, regex, or substring search, and do NOT assert on line counts or symbol censuses (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
  - Depends on: E-02
  - Expected outcome: a new test file that FAILS against the base renderer and PASSES after E-02, exercising the code rather than inspecting it.
  - Execution state: pending

### Task group 4: Verify

- [ ] E-06 Verify the claim is gone tree-wide and nothing regressed. Run `git grep -n -i "automatic when piped"` over the whole repo and enumerate every remaining hit with a disposition. Then run the suite BARE as `python3 -m pytest`. Then `aw sanitize --agent; echo rc=$?`.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: every remaining hit is a HISTORICAL record that must not be rewritten (this plan, its backlog item, `3rsdbj` and its review record, and the two executed plans quoting old transcripts) and none is a live user-facing surface; suite green; sanitizer exit 0.
  - Execution state: pending

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

## Proposed changes (ordered, validatable)

1. E-01 re-measure the defect and confirm the resolver is already correct (guards the premise).
2. E-02 drop the false parenthetical from the renderer's hint (the actual fix).
3. E-03 correct the last false instance in `docs/cli-human-guide.md`'s sample transcript.
4. E-04 edit the hint line only in the four human goldens, leaving F-05's unrelated drift alone.
5. E-05 add the behavior test that pins the absence of the claim and the `suppress_agent_hint` guard.
6. E-06 tree-wide grep with per-hit disposition, bare suite, sanitizer.

## Deferred / out of scope (with reason)

- Restoring the deleted conformance gates (`tests/test_cli_quality_gates.py` and `tests/test_cli_conformance_matrix.py`, removed by `19313eed`) so the four goldens and `tests/conformance_matrix.py` are consumed again (F-04). This is a real coverage hole: schema validity, ANSI-stream separation, byte determinism, fact parity, and the parser-leaf coverage matrix all lost their only guard, and `tests/conformance_matrix.py` plus twelve golden files are dead weight until something reads them. It is deliberately NOT done here because it is a multi-hundred-line test restoration with its own review surface, it would dwarf a one-line wording fix, and it belongs to the existing suite-trim restoration family (`xvp5vx` audits what that commit cost; `f15tne`, `gzmr54`, `p5qx91` restore specific losses). E-05 covers THIS defect's regression risk in the meantime.
  - Carrier: NEEDS-BACKLOG-ITEM (file at authoring; see Open questions OQ-01)
- The unrelated stale remediation strings in `check_findings.human.golden` (F-05). Correcting them is either a genuine golden refresh or evidence the remediation text changed without its record being updated; either way it is a different defect on a different axis, and folding it in would make this plan's diff unreviewable.
  - Carrier: NEEDS-BACKLOG-ITEM (same item as F-04; the goldens' correctness is only meaningful once something reads them)
- Whether to implement non-TTY mode detection at all. `docs/cli-output-contract.md` section 9 records that the ruling does not forbid a future opt-in; this plan takes no position and changes no selection logic.
  - Carrier-Declined: a design question the ruling deliberately leaves open; no work is owed.
- The six docs plan `3rsdbj` already corrected. Verified executed; re-editing them is out of scope and the executed plan's record must not be rewritten.
  - Carrier-Declined: already fixed by an executed plan.

## Scope check

- Over-scope: three additions beyond the backlog item's literal text, each justified. `docs/cli-human-guide.md` (F-02) is added because it is the LAST live instance of the same false claim and fixing the code alone would leave the docs newly wrong; stopping at four of five instances would be arbitrary. `tests/test_human_renderer_agent_hint.py` (E-05) is added because F-03 measured that the renderer has no test caller at all, so without it a one-line string fix has no guard and the same regression can land tomorrow unnoticed. The goldens (E-04) are in the item's own scope, though for a corrected reason (F-04).
- Under-scope: the plan deliberately does NOT restore the deleted conformance gates (F-04), which is the larger coverage hole this work uncovered, and does not correct the goldens' unrelated drift (F-05). Both are carried to a backlog item rather than dropped, and both are named in the approval gate so the approver is not surprised.

## Required tests / validation

One new behavior test, `tests/test_human_renderer_agent_hint.py` (E-05), is the durable verification: it renders real `CommandResult` values through `HumanRenderer` and asserts the rendered bytes, covering the plain path, the colored path, and the `suppress_agent_hint` guard. It must fail against the base renderer and pass after the fix; demonstrating that FAILURE is part of V-05, because a test that passes both before and after proves nothing.

Beyond it: E-01's measurement of the self-refuting output, E-06's tree-wide grep with a disposition per remaining hit, a bare `python3 -m pytest`, and `aw sanitize --agent`.

HONEST LIMITS ON WHAT THIS VERIFICATION PROVES. First, the four goldens are orphaned (F-04), so a green suite does NOT prove they are correct; nothing reads them, and their edit is verified by reading the diff, not by a test. Second, a grep proves the known phrasing is gone, not that the replacement is accurate; the accuracy check is human, reading the new hint and the corrected transcript against `docs/cli-output-contract.md` section 9 and `docs/cli-human-guide.md` "Output mode and audience". Third, the suite at base has 3 pre-existing failures in the `slow`/`livecorpus` selection (F-04); they are unrelated and must be reported as pre-existing, not silently absorbed.

## Spec / documentation sync

No `.spec.md` is amended: the normative contract (`docs/cli-output-contract.md` section 9) is ALREADY correct and is the authority this plan brings the code into line with, so there is no contract change to make and `- Scope-Paths:` declares no spec file. The documentation sync is E-03, the one remaining false transcript in `docs/cli-human-guide.md`.

## Open questions

### OQ-01: File the backlog item carrying the orphaned conformance gates before or during execution?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: FILE IT DURING EXECUTION, as a separate `aw backlog new` call, and replace the two `Carrier: NEEDS-BACKLOG-ITEM` placeholders in "Deferred / out of scope" with its id6 before finalizing. It is NOT filed at authoring because this turn is authoring-only and filing a second tracked record is a mutation beyond writing the plan. It is NOT deferred past execution because "the goldens pin nothing and their gates are deleted" (F-04) is the most consequential thing this work discovered, and an uncarried finding is a lost one. The item should name both F-04 (restore the deleted gates so `conformance_matrix.py` and the twelve goldens are consumed again) and F-05 (the unrelated drift), `- Work-Kind: chore` (it is lost coverage, not a user-perceptible defect, so it does not auto-gate the release per AGENTS.md "Every live bug gates the next release"), and cross-reference `xvp5vx`, which audits what `19313eed` cost.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual output of `python3 -m agent_workflows check plans | cat | tail -3` showing the false hint line as the LAST line with human prose above it, and the output of `grep -n "TTY-NESS OF STDOUT AFFECTS COLOR ONLY" agent_workflows/result_types.py`. Judge the SHAPE of the output only: do NOT compare the `N plans checked` count against any number written in this plan, since that is a live artifact count on a shared tree.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- agent_workflows/renderers.py`. It must show exactly one changed line, removing ` (automatic when piped)` from the appended literal, with the `suppress_agent_hint` guard and the hint's position unchanged. Then paste `python3 -m agent_workflows check plans | cat | tail -1` showing `Agent output: --agent` with no parenthetical. A diff touching `select_output`, `should_color`, or any mode-selection logic is a FAILED V-02 (F-06).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff -- docs/cli-human-guide.md` (exactly one line changed, inside the sample transcript) and `grep -n -i "automatic when piped" docs/cli-human-guide.md` returning nothing. Confirm in one sentence that the file's surrounding "Output mode and audience" prose was NOT edited, since it is the reference wording this plan defers to.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `git diff --stat -- tests/fixtures/conformance_goldens/` showing FOUR files each with exactly one insertion and one deletion, and paste the full `git diff` for `check_findings.human.golden` specifically, proving the two stale remediation strings in F-05 were left UNTOUCHED. A diff that also rewrites the `Fix:` lines is a FAILED V-04, not a passed one: that is F-05's drift and it belongs to the carried item.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: THE TEST MUST BE SHOWN TO FAIL FIRST. Paste (1) the new test file's contents; (2) the output of running it against the UNFIXED renderer, demonstrating a real failure, obtained by stashing the fix or by `git stash push agent_workflows/renderers.py`, running `python3 -m pytest tests/test_human_renderer_agent_hint.py -o addopts=""`, and restoring; (3) the same command PASSING with the fix in place, with its per-test counts. State explicitly that the test asserts on RENDERED OUTPUT and reads no production source text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). A test that passes in step (2) is a FAILED V-05: it is not pinning this defect.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the FULL output of `git grep -n -i "automatic when piped"`, then ENUMERATE every remaining hit with a disposition. Expect hits ONLY in historical records that must not be rewritten: this plan, backlog `zdjhug`, plan `3rsdbj` and its review record under `.aw/records/`, the survey record, and the two executed plans quoting old terminal transcripts. A hit in any LIVE user-facing surface (`agent_workflows/`, `docs/`, `README.md`, `CHANGELOG.md`) is a FAILED V-06. A pasted grep with no per-hit disposition is not evidence. Then paste the final summary line of a BARE `python3 -m pytest`, naming any failure as pre-existing (F-04 names the 3 known `slow`/`livecorpus` failures, which a bare run does not select) or new. Then `aw sanitize --agent; echo rc=$?` ending `rc=0`. Finally, confirm the OQ-01 backlog item was filed and that both `NEEDS-BACKLOG-ITEM` placeholders in "Deferred / out of scope" now carry its id6.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a one-line wording fix to a user-visible string in the shared human renderer, the same one-line fix in a sample transcript in `docs/cli-human-guide.md`, a one-line edit to each of four golden fixtures, and one new behavior test. No mode-selection logic changes, no spec is amended, and no existing test is modified.

TWO CORRECTIONS TO THE BACKLOG ITEM THE APPROVER SHOULD KNOW, both measured at authoring rather than assumed. FIRST, the item's claim that four goldens "pin the current bytes" is FALSE: their only consumer was deleted by commit `19313eed`, and the fix was applied and the full suite run to prove it (`3246 passed`, zero failures, goldens untouched). So the expected "golden regeneration path" is not a test requirement but record-keeping, and the item's scope was easier than stated in that respect. SECOND, and in the harder direction, the item missed a FIFTH live instance of the false string, in `docs/cli-human-guide.md`'s sample transcript, which plan `3rsdbj` legitimately left alone because it was then an accurate transcript; fixing the code without it would make that doc newly false.

WHAT THIS DELIBERATELY DOES NOT FIX, so the approver is not surprised later. The deleted conformance gates are NOT restored. That commit removed the only tests validating agent-record schema conformance, ANSI-stream separation, deterministic bytes, fact parity, and parser-leaf scenario coverage, leaving `tests/conformance_matrix.py` and twelve golden fixtures with no reader. That is a genuinely larger hole than the defect this plan fixes, and it is carried to a new backlog item (OQ-01) in the same family as `xvp5vx`, not fixed inside a one-line wording plan. The goldens' unrelated stale remediation text (F-05) rides with it.

GENUINE STOP CONDITIONS: E-01 shows piped output IS JSONL (the parenthetical would be true and this plan wrong), or a co-worker's concurrent edit to `renderers.py` cannot be safely combined. Neither is a scope question; both are conditions under which proceeding would write something false.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check passed that was not run. V-05 specifically requires demonstrating the new test FAILING before the fix. No em or en dashes in the edited `docs/cli-human-guide.md` prose. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the seven paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). In particular do NOT restore the deleted conformance test files to "finish the job": that is the carried item's work, and doing it here turns a one-line fix into a test-restoration plan.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit zosxj4 -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize zosxj4 --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `zdjhug`; AFTER EXECUTION, and not before, set that item `done` with `--evidence` citing this executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `zdjhug` fails closed because the gate is handed to a carrier that has not shipped, so the item stays `graduated` until `aw ipd finalize` has moved this plan to `executed/`.
