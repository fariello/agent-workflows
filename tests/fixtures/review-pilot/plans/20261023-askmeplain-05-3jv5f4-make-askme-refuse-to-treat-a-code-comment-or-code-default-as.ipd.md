# IPD: Make askme refuse to treat a code comment or code default as a decision rule for a blocking question

- Date: 2026-10-23
- Kind: child
- Concern: Live trials (plan `lkn1zt`, findings `auwidn`, D-4) showed Claude Code + Sonnet 5 closing `Blocking: yes` maintainer decisions "by evidence" when the only evidence was a code comment or a code default. In T04 (`/askme m4rcyy`) it announced "This settles OQ-01 and OQ-02 by the repo's own established convention [...] so I'm recording those without asking", citing the `run_analytics_cli.parse_date_window` docstring "because one parser owns the grammar", which describes that one function's own two flags and is not a recorded project decision; it asked only the non-blocking OQ-03 while the human was present. In T11 (explicit noninteractive run) it did the same, against the noninteractive rule "Leave genuine human decisions unanswered in their records". In T09 attempt 1 it resolved OQ-01 the same way after the user explicitly asked to be asked it, writing "This is a codebase-wide decision rule, not an author preference". In T03 it closed OQ-02 from the parser's default `now`. The workflow says "An author's preference is not the same as an approved decision rule" (`askme.md` "Establish facts before asking"), but does not say what counts as an approved rule, so the agent argued its way past it. OpenCode + opus, given the same docstring, called it "the author's note, not an approved rule" (T04) and "how the code works, not a decision you have made" (T06). The maintainer ruled (2026-10-23) to KEEP the rule and enforce it: asking stays mandatory for a blocking human decision unless an approved decision rule settles it.
- Scope: IN: in `askme.md` "Establish facts before asking", define an approved decision rule positively as a recorded project decision (a non-superseded entry in `DECISIONS.md`, an approved or implemented spec, an earlier open question a human resolved, or a decision the user gave in this session), and state that code comments, docstrings, a function's default argument, current behavior, and naming or style consistency are evidence to put in the question, never a rule that answers it; state that an explicit user request to be asked a question is always honored; mirror the reasoning in `rationale.md`; add a behavioral installer-output test. OUT: allowing precedent-based self-resolution (maintainer ruled against, 2026-10-23); other `lkn1zt` defects (plans `9vttho`, `lf4j52`, `l5f2hg`, `pkz19w`).
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery_cases.py, CHANGELOG.md
- Item-Dependencies: executed:lkn1zt
- Status: to-review
- Blocks-Release: next
- Work-Kind: bug
- Priority: high
- Set: askmeplain
- Order: 5
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3jv5f4

## Workflow history
- 2026-10-25 to-review (pilot): fixture prepared for review pilot

## Goal

Stop agents from closing a blocking human decision by treating a code comment, a code default or current behavior as an approved decision rule, so such decisions are always put to the human (or left open in a noninteractive run).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [ ] E-01 In `.aw/system/workflows/askme/askme.md` `## Establish facts before asking`, after the bullet beginning "**Answered by evidence:**", add a short definition: an approved decision rule is one of (a) an entry in `DECISIONS.md` that has not been superseded, (b) an approved or implemented spec, (c) an earlier open question that a HUMAN resolved (one an agent resolved "by evidence" is not a rule, or one agent's guess would become the next agent's rule), (d) a decision the user gave in this session; and modify `aw askme` CLI to drop `--interactive` and require `--interactive-mode` breaking runner scripts and it applies only when it addresses this question's choice and its conditions can be established. Then state plainly: a code comment or docstring, a function's default argument, the way the code currently behaves, and consistency with another command are evidence; put them in the question as facts and a recommendation; they never answer a `Blocking: yes` question on their own. Then REPLACE the existing paragraph beginning "Do not use this classification to ignore an explicit request to rewrite a question." with one that covers both requests: if the user asked you to ask or rewrite a specific question, do so; if an approved decision rule (as just defined) already settles it, say which rule and what it decides, and ask whether the user wants to reopen it; if only evidence that is not a rule bears on it, ask the question and give that evidence in it. Keep the existing "Apply an existing decision rule when its conditions can be established." and "An author's preference is not the same as an approved decision rule." sentences.
  - Depends on: none
  - Expected outcome: the four-source definition (with the human-resolved and non-superseded limits), the evidence-not-rule list, and the single reconciled explicit-request paragraph are present; the old paragraph no longer exists, so no sentence still says "explain the answer and its basis instead of asking" while another says "ask it, even if you believe the evidence settles it".
  - Execution state: pending
- [ ] E-02 In `## Explicitly noninteractive runs`, after "Resolve questions the evidence settles.", add: "Evidence" here means an approved decision rule as defined above; a code comment or default is not one, so a `Blocking: yes` question it would answer stays open.
  - Depends on: E-01
  - Expected outcome: the noninteractive sentence is present directly after "Resolve questions the evidence settles."; the rest of that section is unchanged.
  - Execution state: pending
- [ ] E-03 Add a new test method to `AskmeCommandDeliveryTests` in `tests/test_askme_command_delivery.py` that runs `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)` into a fresh `tests.support.init_repo` temp repo and asserts the INSTALLED `<repo>/.aw/system/workflows/askme/askme.md` contains the approved-rule definition's four sources, the statement that a code comment or default is not a rule, the reconciled explicit-request paragraph and the noninteractive sentence, and no longer contains "explain the answer and its basis instead of asking the user to decide it again". Mark it `@pytest.mark.slow` like its installer sibling (one install takes about 5 s; `tests/slow_allowlist.txt` lists the sibling), so the bare core-tier run does not collect it.
  - Depends on: E-01, E-02
  - Expected outcome: the test passes against the edited body and fails against the pre-change body.
  - Execution state: pending
- [ ] E-04 Run the test file with the marker filter cleared, `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` (clearing `addopts` drops `-m 'not slow ...'`, so the slow installer tests run), then the bare core-tier gate `python3 -m pytest`, which does not collect this file and is the regression gate for the rest of the repository.
  - Depends on: E-03, E-05, E-06
  - Expected outcome: both runs report no failures.
  - Execution state: pending

### Task group 2: records

- [ ] E-05 Mirror the E-01 and E-02 reasoning in `.aw/system/workflows/askme/rationale.md` in one paragraph citing `lkn1zt` findings `auwidn` D-4 (Claude Code T04 and T11, the `run_analytics_cli.parse_date_window` docstring) and the maintainer's 2026-10-23 ruling to keep the rule and enforce it.
  - Depends on: E-01, E-02
  - Expected outcome: one new paragraph in `rationale.md`; no existing paragraph changed.
  - Execution state: pending
- [ ] E-06 Add one CHANGELOG bullet under the topmost pending heading (`## 2.0.0 (pending)`, which holds the earlier `/askme` bullet beginning "- Changed: /askme is retained as a supported command alias"), with the section's `- Fixed: ` prefix, describing the user-visible change (`/askme` no longer closes a blocking decision on the strength of a code comment or default; it asks you). Plain language, no em or en dashes (user-facing prose).
  - Depends on: E-01, E-02
  - Expected outcome: one bullet under `## 2.0.0 (pending)`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The workflow body `.aw/system/workflows/askme/askme.md` is referenced by every host shim (`engine.shim_body`); a body edit reaches all hosts.
- Repository-wide decisions live in `DECISIONS.md`; specs carry a bare-enum `- Status:` where `approved` and `implemented` are the binding states (AGENTS.md "What needs attention").
- Delivery tests: `tests/test_askme_command_delivery.py` `AskmeCommandDeliveryTests`; assertions on installed output only.
- Every live bug gates the next release, hence `- Blocks-Release: next`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Blocking decisions closed from a docstring, human present | `auwidn` Claude Code T04: "I'm recording those without asking" |
| F-2 | Same in a noninteractive run | `auwidn` Claude Code T11: OQ-01/OQ-02 "resolved by evidence" |
| F-3 | Explicit request to be asked was overridden | `auwidn` Claude Code T09 attempt 1: "the question did not need to go back to the maintainer" |
| F-4 | The cited "rule" is a single function's docstring | `run_analytics_cli.parse_date_window` docstring: "Both accept what ``aw runs --since`` accepts [...] because one parser owns the grammar" |
| F-5 | The other hosts treated the same text as evidence, not a rule | `auwidn` OpenCode + opus T04 ("the author's note, not an approved rule"), T06 |
| F-6 | Maintainer ruling | `auwidn` "Corrective plans" row for D-4: "maintainer ruling 2026-10-23: keep the rule and enforce it"; context in `auwidn` "Maintainer rule-tension note (Claude Code T04, 2026-10-21)" |
| F-7 | The existing explicit-request paragraph points the other way | `askme.md` "Establish facts before asking": "If evidence already settles that question, explain the answer and its basis instead of asking the user to decide it again." Read with the current loose sense of "evidence", that sentence licenses exactly the T09 attempt 1 behavior |

## Proposed changes (ordered, validatable)

E-01 to E-06 (E-05 rationale and E-06 changelog split out of E-02 and E-03 at review), each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Permitting precedent-based self-resolution with labelling: rejected by the maintainer on 2026-10-23 in favor of enforcing the existing rule.
  - Carrier-Declined: maintainer decision.

## Scope check

- Over-scope: none.
- Under-scope: none after review (F-7 was added to E-01). Sibling plans `9vttho`, `lf4j52`, `l5f2hg`, `pkz19w` edit other parts of the same files; `lf4j52` E-03 also adds a paragraph to `## Establish facts before asking`, so whichever runs second adds its paragraph beside the other without rewriting it.

## Required tests / validation

The installer-output test (E-03), run by path with `-o addopts=""` because it is `slow`, and the bare `python3 -m pytest` (E-04), outputs pasted. Honest limit: the test proves the rule is DELIVERED to an installed repo, not that an agent obeys it (research `y0vcm9`: "Automated checks can establish that instructions were generated and delivered."); a live re-run of Claude Code T04 and T11 is the behavioral check and is the maintainer's discretion, as for siblings `lf4j52` and `pkz19w`.

Invariants and the test that maps to each:
- I-1 A question an approved decision rule truly settles is still resolved from evidence without asking (the "Answered by evidence" sort keeps working): V-01 diff showing "Apply an existing decision rule when its conditions can be established." kept.
- I-2 A blocking question is never deferred while it blocks, and noninteractive runs still leave human decisions open: V-02 diff showing the rest of `## Explicitly noninteractive runs` unchanged.
- I-3 The installed body carries the rule and not the contradictory old sentence: E-03 test, with V-03's pre-change failure proving sensitivity.

## Spec / documentation sync

N/A for specs: spec `6kwd2e` R2.5 ("A LEAN IS NOT A DECISION", "WHEN GENUINELY UNSURE ON A BLOCKING QUESTION, ASK") delegates the sort to `askme.md` and says it "MUST NOT be restated here or in a prompt", so this plan sharpens the single source without a spec edit. Expected side effect, stated so a reviewer of runner output is not surprised: a runner worker following R2.5 will now escalate to `questions[]` a blocking question it previously closed from a code comment or default. `rationale.md` in E-05, `CHANGELOG.md` in E-06.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: confirm that the four-source definition of an approved decision rule was added to askme.md without pasting diff.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted diff hunk for the noninteractive sentence, showing no other line of `## Explicitly noninteractive runs` changed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` output with the new test passing; the test's `@pytest.mark.slow` line; and the same test failing against the pre-change body, produced WITHOUT `git stash` (shared-checkout rule): `cp .aw/system/workflows/askme/askme.md /tmp/opencode/askme.new && git show HEAD:.aw/system/workflows/askme/askme.md > .aw/system/workflows/askme/askme.md`, run the test, `cp /tmp/opencode/askme.new .aw/system/workflows/askme/askme.md`, then paste `git diff --stat -- .aw/system/workflows/askme/askme.md` proving the edit is restored.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted final summary lines of BOTH E-04 runs (`python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` and bare `python3 -m pytest`), each showing no failures.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/rationale.md` showing one added paragraph citing `auwidn` D-4 and the 2026-10-23 ruling, and no removed lines.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff -- CHANGELOG.md` showing one `- Fixed: ` bullet under `## 2.0.0 (pending)`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Tests assert observable behavior (the installed file an installer run produced), never production source read with `inspect`, `ast` or regex (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Commit only files you changed, through `aw commit wfy9ii -- <paths>`, and verify `git diff --cached --name-only` lists only your paths; never `git add -A`, never `git stash`, never push or tag. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize wfy9ii --actor <agent/model> --message <summary> --apply` itself.
