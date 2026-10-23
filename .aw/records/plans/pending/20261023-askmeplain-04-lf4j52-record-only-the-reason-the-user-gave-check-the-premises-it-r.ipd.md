# IPD: Record only the reason the user gave, check the premises it rests on, and keep the original question text

- Date: 2026-10-23
- Kind: child
- Concern: Live trials (plan `lkn1zt`, findings `auwidn`) found three recording defects that share one step, writing the user's answer into the record's `## Open questions`. D-5: a reason the user did not give, almost always the chosen option's own argument text, is written into `- Resolution or deferral rationale:` as the user's reason; Claude Code once labelled it "Rationale supplied" (T08) and the final report repeated "Reason: uniform across all artifact types" for a user who had typed only "Creation date" (T09). D-6: a premise stated in the record is copied into the prompt and the resolution without being checked (the fixture's false "only plans and specs carry a history"; backlog items carry one too, 1,104 of them, as OpenCode + opus measured every time). D-7: the original question text in `- Resolution or deferral rationale:` is deleted and replaced instead of appended to, so the record loses what was asked. These failed five trials (Claude Code T02, T08, T09; Antigravity T02; OpenCode + gem T02) and appear as notes in most passing rows on three of four hosts; OpenCode + opus never showed D-5 or D-7 and always recorded "No reason was given" when none was given. The workflow already says "Do not invent a reason the user did not give" (`askme.md` "Ask and wait") and "Update `- Resolution or deferral rationale:` with the decision, its source (the user or evidence), the date, and any reason actually supplied" ("Record project decisions"); agents read the chosen option's description as the user's reason.
- Scope: IN: in `askme.md` "Record project decisions", (1) say that choosing an option is not the same as giving its stated argument as a reason; record the option's label and, if no reason was typed, the literal phrase "No reason was given"; (2) require APPENDING the resolution after the original question text, never replacing it, and give the exact append shape (`<original text> RESOLVED <date> by <the user | evidence>: <decision>. <reason as given, or "No reason was given.">`); (3) in "Establish facts before asking", require checking any factual premise from the record that a prompt or option relies on, and correcting a false one in the prompt (and saying so) rather than repeating it; mirror the reasoning in `rationale.md`; add a behavioral installer-output test. OUT: other `lkn1zt` defects (plans `9vttho`, `wfy9ii`, `l5f2hg`, `pkz19w`); any runtime validator of record text.
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery.py, CHANGELOG.md
- Item-Dependencies: executed:lkn1zt
- Status: to-review
- Blocks-Release: next
- Work-Kind: bug
- Priority: high
- Set: askmeplain
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: lf4j52

## Workflow history
- 2026-10-23 to-review (aw set): authored review-ready from lkn1zt findings auwidn (D-5, D-6, D-7)

- 2026-10-23 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every host record a user's answer as what the user actually said, appended to the original question, with any premise the prompt relied on checked first, so a record never claims a reason or a fact the user did not supply.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rules

- [ ] E-01 (D-5) In `.aw/system/workflows/askme/askme.md` `## Record project decisions`, replace the bullet beginning "Update `- Resolution or deferral rationale:`" so it states, in direct language: choosing an option is not giving a reason; an option's description is your argument, not the user's; record the chosen option and only reasons the user typed; when the user typed none, write the literal sentence "No reason was given."; never label your own argument as "supplied", "the user's reason" or similar. Keep the source and date requirements.
  - Depends on: none
  - Expected outcome: the bullet states all five points; the existing "Do not invent a reason the user did not give" sentence in `## Ask and wait` stays.
  - Execution state: pending
- [ ] E-02 (D-7) In the same section add a bullet: append the resolution after the existing rationale text, never delete or rewrite it, using the shape `<existing text> RESOLVED <YYYY-MM-DD> by <the user | evidence>: <decision>. <reason as given, or "No reason was given.">`.
  - Depends on: E-01
  - Expected outcome: the append rule and shape are present.
  - Execution state: pending
- [ ] E-03 (D-6) In `## Establish facts before asking`, add a paragraph: before using a factual statement from the record (a count, a list of which record types have a field, a claim about current behavior) in a prompt or an option, check it against the repository; if it is false, state the corrected fact in the prompt and say the record was wrong; never repeat an unchecked premise. Mirror D-5, D-6 and D-7 reasoning in `.aw/system/workflows/askme/rationale.md` in one short paragraph each, citing `lkn1zt` findings `auwidn`.
  - Depends on: none
  - Expected outcome: the paragraph and three rationale paragraphs are present.
  - Execution state: pending
- [ ] E-04 Add a behavioral test to `tests/test_askme_command_delivery.py` that installs into a temporary repo (`tests.support.init_repo`, as `test_installer_delivers_and_preserves_askme_shims` does) and asserts the INSTALLED `askme.md` contains the operative phrases of E-01 to E-03: "No reason was given.", the append shape, and the premise-check rule. Add one CHANGELOG bullet under the topmost pending heading (plain language, no em or en dashes).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the test passes against the edited body and fails against the pre-change body; CHANGELOG bullet present.
  - Execution state: pending
- [ ] E-05 Run the bare suite `python3 -m pytest` and the new test by path.
  - Depends on: E-04
  - Expected outcome: both pass.
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

E-01 to E-05, each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Re-running the recording rows live on each host after the change: maintainer-attended act, not plan work.
  - Carrier-Declined: re-verification reuses `lkn1zt`'s method at the maintainer's discretion.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

The installer-output test (E-04) and the bare `python3 -m pytest` (E-05), outputs pasted.

## Spec / documentation sync

N/A for specs (see Step 0: the field set is unchanged). `rationale.md` updated in E-03; `CHANGELOG.md` in E-04.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/askme.md` hunk for the rationale bullet showing all five points.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted diff hunk showing the append rule and its exact shape.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted diff hunks for the premise-check paragraph in `askme.md` and the three paragraphs in `rationale.md`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` output with the new test passing, the same test failing against the pre-change body, and the `git diff -- CHANGELOG.md` bullet.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted final summary line of the bare `python3 -m pytest` run showing no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D-5, D-6 and D-7 all occur in the single step of writing the answer to the record and are fixed in the same two sections of one file; separating them would produce three plans editing the same paragraphs (maintainer chose this grouping, 2026-10-23).

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit lf4j52 -- <paths>`; never push or tag. Finalize with `aw ipd finalize lf4j52 --actor <agent/model> --message <summary> --apply` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
