# IPD: Record only the reason the user gave, check the premises it rests on, and keep the original question text

- Date: 2026-10-23
- Kind: child
- Concern: Live trials (plan `lkn1zt`, findings `auwidn`) found three recording defects that share one step, writing the user's answer into the record's `## Open questions`. D-5: a reason the user did not give, almost always the chosen option's own argument text, is written into `- Resolution or deferral rationale:` as the user's reason; Claude Code once labelled it "Rationale supplied" (T08) and the final report repeated "Reason: uniform across all artifact types" for a user who had typed only "Creation date" (T09). D-6: a premise stated in the record is copied into the prompt and the resolution without being checked (the fixture's false "only plans and specs carry a history"; backlog items carry one too, 1,104 of them, as OpenCode + opus measured every time). D-7: the original question text in `- Resolution or deferral rationale:` is deleted and replaced instead of appended to, so the record loses what was asked. These failed five trials (Claude Code T02, T08, T09; Antigravity T02; OpenCode + gem T02) and appear as notes in most passing rows on three of four hosts; OpenCode + opus never showed D-5 or D-7 and always recorded "No reason was given" when none was given. The workflow already says "Do not invent a reason the user did not give" (`askme.md` "Ask and wait") and "Update `- Resolution or deferral rationale:` with the decision, its source (the user or evidence), the date, and any reason actually supplied" ("Record project decisions"); agents read the chosen option's description as the user's reason.
- Scope: IN: in `askme.md` "Record project decisions", (1) say that choosing an option is not the same as giving its stated argument as a reason; record the option's label and, if no reason was typed, the literal phrase "No reason was given"; (2) require APPENDING the resolution after the original question text, never replacing it, and give the exact append shape (`<original text> RESOLVED <date> by <the user | evidence> via /askme: <decision>. <reason as given, or "No reason was given.">`, aligned with the runner's existing `RESOLVED <date> by <who> via <channel>: <answer>` shape in `runner_shared.record_oq_answer`); (3) in "Establish facts before asking", require checking any factual premise from the record that a prompt or option relies on, and correcting a false one in the prompt (and saying so) rather than repeating it; mirror the reasoning in `rationale.md`; add a behavioral installer-output test. OUT: other `lkn1zt` defects (plans `9vttho`, `wfy9ii`, `l5f2hg`, `pkz19w`); any runtime validator of record text.
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery.py, CHANGELOG.md
- Item-Dependencies: executed:lkn1zt, exists:backlog:mqsitd
- Status: reviewed
- Readiness: go-pending-approval
- Blocks-Release: next
- Work-Kind: bug
- Priority: high
- Set: askmeplain
- Order: 4
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: lf4j52

## Workflow history
- 2026-10-23 same-status (aw set): set Item-Dependencies to executed:lkn1zt, exists:backlog:mqsitd
- 2026-10-23 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-23 to-review (aw set): authored review-ready from lkn1zt findings auwidn (D-5, D-6, D-7)

- 2026-10-23 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every host record a user's answer as what the user actually said, appended to the original question, with any premise the prompt relied on checked first, so a record never claims a reason or a fact the user did not supply.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rules

- [ ] E-01 (D-5) In `.aw/system/workflows/askme/askme.md` `## Record project decisions`, replace the bullet beginning "Update `- Resolution or deferral rationale:`" so it states, in direct language: choosing an option is not giving a reason; an option's description is your argument, not the user's; record the chosen option and only reasons the user typed; when the user typed none, write the literal sentence "No reason was given."; never label your own argument as "supplied", "the user's reason" or similar. Keep the source and date requirements. Leave the other bullets of the section ("Set `- Status: resolved` only after...", "Preserve the original `- Blocking:` value.", "Record the answer before asking the next question.") unchanged; sibling plan `pkz19w` relies on the last one.
  - Depends on: none
  - Expected outcome: the bullet states all five points, namely (1) choosing an option is not giving a reason, (2) an option's description is the agent's argument, (3) record the chosen option and only typed reasons, (4) the literal "No reason was given." when none was typed, (5) never label the agent's argument as the user's; the existing "Do not invent a reason the user did not give" sentence in `## Ask and wait` and the section's other three bullets stay.
  - Execution state: pending
- [ ] E-02 (D-7) In the same section add a bullet: append the resolution after the existing rationale text, never delete or rewrite it, using the shape `<existing text> RESOLVED <YYYY-MM-DD> by <the user | evidence> via /askme: <decision>. <reason as given, or "No reason was given.">`; when the field is empty, write the `RESOLVED ...` text alone.
  - Depends on: E-01
  - Expected outcome: the append rule and shape are present.
  - Execution state: pending
- [ ] E-03 (D-6) In `## Establish facts before asking`, add a paragraph: before using a factual statement from the record (a count, a list of which record types have a field, a claim about current behavior) in a prompt, an option, or the resolution you write back, check it against the repository; if it is false, state the corrected fact in the prompt and say the record was wrong; never repeat an unchecked premise.
  - Depends on: none
  - Expected outcome: the premise-check paragraph is present in `## Establish facts before asking` and covers prompt, option and written resolution.
  - Execution state: pending
- [ ] E-04 Add a new test method to `AskmeCommandDeliveryTests` in `tests/test_askme_command_delivery.py` that runs `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)` into a fresh `tests.support.init_repo` temp repo (as `test_installer_delivers_and_preserves_askme_shims` does) and asserts the INSTALLED `<repo>/.aw/system/workflows/askme/askme.md` contains the operative phrases of E-01 to E-03: "No reason was given.", the append shape including `via /askme`, and the premise-check rule. Mark it `@pytest.mark.slow` like its installer sibling (one install takes about 5 s; `tests/slow_allowlist.txt` lists the sibling), so the bare core-tier run does not collect it.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the test passes against the edited body and fails against the pre-change body.
  - Execution state: pending
- [ ] E-05 Run the test file with the marker filter cleared, `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` (clearing `addopts` drops `-m 'not slow ...'`, so the slow installer tests run), then the bare core-tier gate `python3 -m pytest`, which does not collect this file and is the regression gate for the rest of the repository.
  - Depends on: E-04, E-06, E-07
  - Expected outcome: both runs report no failures.
  - Execution state: pending

### Task group 2: records

- [ ] E-06 Mirror the D-5, D-6 and D-7 reasoning in `.aw/system/workflows/askme/rationale.md`, one short paragraph each, citing `lkn1zt` findings `auwidn` (for D-5 the Claude Code T09 "Creation date. And that question was way too long-winded." row; for D-6 the false "only plans and specs carry a history" premise against the 1,104 backlog items OpenCode + opus measured; for D-7 the overwritten rationale fields).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: three new paragraphs in `rationale.md`; no existing paragraph changed.
  - Execution state: pending
- [ ] E-07 Add one CHANGELOG bullet under the topmost pending heading (`## 2.0.0 (pending)`, which holds the earlier `/askme` bullet beginning "- Changed: /askme is retained as a supported command alias"), with the section's `- Fixed: ` prefix, describing the user-visible change (recorded answers keep the original question, carry only the reason you gave, and no longer repeat an unchecked fact). Plain language, no em or en dashes (user-facing prose).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: one bullet under `## 2.0.0 (pending)`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The workflow body is `.aw/system/workflows/askme/askme.md`; host shims only reference it (`engine.shim_body`), so a body edit reaches every host.
- Delivery tests: `tests/test_askme_command_delivery.py` `AskmeCommandDeliveryTests`, installer round trip via `tests.support.init_repo`. Assertions are on installed output, not on repository source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Open-question record shape (`- Blocking:`, `- Status:`, `- Owner:`, `- Resolution or deferral rationale:`) is defined by the IPD spec (`ipd-structure-and-linting`); this plan changes how askme writes the rationale field's VALUE, not the field set, so no spec edit is needed.
- Every live bug gates the next release, hence `- Blocks-Release: next`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | D-5 failed five trials | `auwidn` Claude Code T02/T08/T09, Antigravity T02, OpenCode + gem T02 |
| F-2 | D-5 is the option's argument copied as the user's reason | `auwidn` Claude Code T09: user typed "Creation date. And that question was way too long-winded."; record: "Reason: the filename date is present on effectively every tracked artifact [...]" |
| F-3 | D-6 premise copied unchecked | `auwidn` Claude Code T02, Antigravity T02, OpenCode + gem T02 repeat "only plans and specs carry a history"; OpenCode + opus T02 measured "1,104 backlog items" |
| F-4 | D-7 original question text deleted | `auwidn` most recording rows on Claude Code, Antigravity, OpenCode + gem; Antigravity T10 is the single exception ("Original question: [...]") |
| F-5 | The correct behavior already exists on one host | `auwidn` OpenCode + opus T01: "No reason supplied beyond accepting the recommendation." |

## Proposed changes (ordered, validatable)

E-01 to E-07 (E-06 rationale and E-07 changelog split out of E-03 and E-04 at review), each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Re-running the recording rows live on each host after the change: maintainer-attended act, not plan work.
  - Carrier-Declined: re-verification reuses `lkn1zt`'s method at the maintainer's discretion.

## Scope check

- Over-scope: none.
- Under-scope: the runner's pre-flight answer writer `runner_shared.record_oq_answer` REPLACES the rationale line (`rationale_pattern.sub(rationale_line, new_block, count=1)`), the same overwrite D-7 forbids for agents. It is runner code, outside this workflow-text plan, and whether to change it is raised as OQ-01 (non-blocking). Sibling plans `9vttho`, `wfy9ii`, `l5f2hg`, `pkz19w` edit other parts of the same files; this plan touches only the "Update `- Resolution or deferral rationale:`" bullet, one new bullet in `## Record project decisions`, and one new paragraph in `## Establish facts before asking`.

## Required tests / validation

The installer-output test (E-04), run by path with `-o addopts=""` because it is `slow`, and the bare `python3 -m pytest` (E-05), outputs pasted. Honest limit: the test proves the rules are DELIVERED to an installed repo, not that an agent obeys them (research `y0vcm9`: "Automated checks can establish that instructions were generated and delivered."); behavioral confirmation is the attended re-run under Deferred.

Invariants and the test that maps to each:
- I-1 The decision and its source and date are still recorded, and `- Blocking:` is still preserved: V-01 diff showing those requirements and bullets kept.
- I-2 "Do not invent a reason the user did not give" in `## Ask and wait` and "Record the answer before asking the next question." stay: V-01 diff shows no change to them.
- I-3 The installed body carries all three rules: E-04 test, with V-04's pre-change failure proving sensitivity.

## Spec / documentation sync

N/A for specs (see Step 0: the field set is unchanged; spec `ipd-structure-and-linting` Section 7 only requires a nonempty rationale for `Status: resolved`, and spec `6kwd2e` R1.5 requires the rationale to name the human and date, which the append shape does). `rationale.md` updated in E-06; `CHANGELOG.md` in E-07.

## Open questions

### OQ-01: Should the runner's pre-flight answer writer also append instead of replacing the rationale?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: mqsitd
- Resolution or deferral rationale: Raised at review 2026-10-23. `runner_shared.record_oq_answer` (used by the `aw oc run` / `aw agy run` pre-flight question sweep) writes `RESOLVED <date> by <who> via <channel>: <answer>` by replacing the existing rationale line, so any text the author put there is lost, which is the D-7 defect this plan forbids for agents. Changing it is runner code outside this plan's scope and alters a behavior pinned by `tests/test_question_preflight.py` `test_a40_durable_artifact_write_back`, so it needs the maintainer's call: file a separate backlog item (recommended) or leave the runner as is. This plan does not depend on the answer, since it edits only workflow text.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/askme.md` hunk for the rationale bullet showing all five points (named in E-01's Expected outcome), and showing the section's other three bullets and the `## Ask and wait` "Do not invent a reason" sentence unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted diff hunk showing the append rule, its exact shape including `via /askme`, and the empty-field case.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted diff hunk for the premise-check paragraph in `askme.md`, covering prompt, option and written resolution.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` output with the new test passing; the test's `@pytest.mark.slow` line; and the same test failing against the pre-change body, produced WITHOUT `git stash` (shared-checkout rule): `cp .aw/system/workflows/askme/askme.md /tmp/opencode/askme.new && git show HEAD:.aw/system/workflows/askme/askme.md > .aw/system/workflows/askme/askme.md`, run the test, `cp /tmp/opencode/askme.new .aw/system/workflows/askme/askme.md`, then paste `git diff --stat -- .aw/system/workflows/askme/askme.md` proving the edit is restored.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted final summary lines of BOTH E-05 runs (`python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` and bare `python3 -m pytest`), each showing no failures.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/rationale.md` showing three added paragraphs (D-5, D-6, D-7), each citing `auwidn`, and no removed lines.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `git diff -- CHANGELOG.md` showing one `- Fixed: ` bullet under `## 2.0.0 (pending)`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D-5, D-6 and D-7 all occur in the single step of writing the answer to the record and are fixed in the same two sections of one file; separating them would produce three plans editing the same paragraphs (maintainer chose this grouping, 2026-10-23).

Execute only after explicit human approval (`Status: approved`); no blocking open question remains (OQ-01 is non-blocking and does not affect any E-item). Tests assert observable behavior (the installed file an installer run produced), never production source read with `inspect`, `ast` or regex (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Commit only files you changed, through `aw commit lf4j52 -- <paths>`, and verify `git diff --cached --name-only` lists only your paths; never `git add -A`, never `git stash`, never push or tag. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize lf4j52 --actor <agent/model> --message <summary> --apply` itself.
