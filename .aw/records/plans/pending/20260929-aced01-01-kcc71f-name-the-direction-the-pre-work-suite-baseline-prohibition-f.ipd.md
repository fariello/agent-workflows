# IPD: Name the direction the pre-work suite baseline prohibition forbids

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared`'s `THE PRE-WORK SUITE BASELINE` banner states its prohibition with no DIRECTION: "THE BASELINE IS INFORMATION FOR AN HONEST AGENT, NOT A CHECK ON A DISHONEST ONE. NOTHING MAY REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT." All four of its numbered reasons forbid using the baseline to make an outcome WORSE, but the headline forbids changing an outcome AT ALL, and spec `25kzda` 5.1's "THE HONEST LIMIT" carries the same undirected wording ("nothing refuses on it"). MEASURED IN THIS LANE AT HEAD `bfa5a6f7`, and this is worse than the item knew: shipped code already changes a post-merge outcome on the strength of the baseline. `_relative_revalidation_verdict` on one red measurement returns `passed=True` when the baseline names the failing id and `passed=False` when no baseline exists, so the banner's headline, read literally, now forbids code that is live, reviewed, and correct. Its own body separately claims "THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT", which the same measurement falsifies: `revalidation_baseline_for` is a second consumer reading the same `attempt["suite_baseline"]` record.
- Scope: Correct the banner so it states the DIRECTION it forbids (a baseline may never make an outcome WORSE; it may make one more permissive) and so it stops claiming a single consumer that measurement contradicts, then carry the same direction into spec `25kzda` 5.1's "THE HONEST LIMIT" paragraph, which is the normative twin of the banner and is what a graduating plan is reviewed against. Give the direction rule a behavioral test, since it is currently unpinned in the one direction that matters. EXCLUDES any change to what the prohibition actually forbids (the rejected `not-mine` gate stays forbidden), EXCLUDES any change to `perform_gate_answer`'s baseline-free control flow, and EXCLUDES the dangling `tests/test_suite_baseline.py` citations in the same banner (carried by backlog `gia5i7`).
- Scope-Paths: agent_workflows/runner_shared.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_suite_baseline_direction.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: aced01
- Set: aced01
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: kcc71f

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `aced01`, graduating it. Every claim was re-measured in this lane at HEAD `bfa5a6f7` rather than inherited, and THREE measurements change the work's shape. FIRST, the item frames this as a readability defect ("what is missing is one sentence naming the direction"); measured, the banner is now FALSE rather than merely terse, because `_relative_revalidation_verdict` demonstrably changes a post-merge outcome on the strength of the baseline, so a literal reading of the headline forbids shipped code. SECOND, the banner's "THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT" is falsified by the same measurement and the item does not mention it; correcting the direction while leaving that sentence would leave a second false claim in the paragraph a reader consults for the rule. THIRD, the item's closing NOTE is stale and its instruction must NOT be followed: it says the wording is pinned by `tests/test_suite_baseline.py::test_THE_RULING_IS_RECORDED_AT_THE_CODE_with_its_reasoning` asserting five exact phrases and that "an edit must keep those and ADD to them". That file does not exist (deleted in `19313eed`), and the item's own 2026-09-28 maintainer ruling supersedes the note. The plan therefore refuses the preserve-exact-phrases constraint and does not restore the text pin, adding a BEHAVIORAL test of the direction rule instead.

## Goal

Make the baseline prohibition state the direction it forbids, so that the rule is true as written and a
future author can tell a forbidden gate from a permitted one without re-deriving the scope.

The ruling itself is correct and is not being weakened: using the baseline to DISBELIEVE an agent stays
forbidden, for the four reasons the banner already gives. What changes is that the banner currently
over-states that ruling into a prohibition on changing an outcome in EITHER direction, and shipped code
changes one in the permissive direction. So the banner is not just hard to read; it is false, and it is
false in the expensive direction, because the next author to need a permissive baseline-relative
comparison reads an absolute prohibition, and either abandons legitimate work or concludes the banner may
be ignored. `tgyfs2` already paid this cost once: it needed exactly such a verdict, spent a full pass over
the banner, the spec paragraph and a test file to decide it was permitted, and recorded the interpretation
as a decision flagged for maintainer review. This plan converts that one-off interpretation into the rule.

FIVE FACTS ESTABLISHED AT AUTHORING, so the executor inherits measurement rather than the item's diagnosis.

1. THE UNDIRECTED HEADLINE IS PRESENT VERBATIM. `runner_shared`'s banner reads "THE BASELINE IS
   INFORMATION FOR AN HONEST AGENT, NOT A CHECK ON A DISHONEST ONE. NOTHING MAY REFUSE, DOWNGRADE, OR
   OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT." The four numbered reasons that follow are all
   reasons a baseline cannot be used to disbelieve an agent.

2. SHIPPED CODE ALREADY CHANGES AN OUTCOME ON THE STRENGTH OF THE BASELINE, so the headline read
   literally is false. One red measurement, three baselines, only the baseline varying:

   ```text
   red suite    baseline=names it         no-baseline=False with=True
   red suite    baseline=names other      no-baseline=False with=False
   red suite    baseline=empty+completed  no-baseline=False with=False
   ```

   The first row is a post-merge outcome that is `True` BECAUSE of the baseline and `False` without it.
   That is `_relative_revalidation_verdict`, added by `tgyfs2`, and it is correct: it only ever passes a
   tree that would otherwise be refused.

3. THE DIRECTION IS ASYMMETRIC IN THE CODE, WHICH IS WHAT MAKES THE CORRECTED RULE TRUE RATHER THAN
   MERELY TIDIER. Across the same matrix, no baseline value turns a `True` into a `False`: a green suite
   passes under every baseline including one naming failures, and an unmeasured suite refuses under every
   baseline. So "a baseline may only ever make an outcome MORE permissive" is an observed property of the
   current tree and not an aspiration.

4. THE BANNER CARRIES A SECOND, SEPARATELY FALSE SENTENCE THE ITEM DOES NOT MENTION: "SO THE BASELINE'S
   ONLY CONSUMER IS THE ADJUDICATION PROMPT, and its only effect is on what the agent READS."
   `revalidation_baseline_for` reads `attempt["suite_baseline"]`, the same record the prompt renders, and
   feeds `new_failures_since_baseline`. Fact 2 is that consumer's effect. A neighbouring docstring makes
   the matching claim, "Nothing in this package compares `suite_baseline['failures']` to `failing_tests`",
   which is still TRUE as written (the comparison is against the merged tree's failures, not against
   `failing_tests`) and must not be "corrected" into falsehood.

5. THE ITEM'S CLOSING INSTRUCTION IS STALE AND MUST BE REFUSED. It says the wording is pinned by
   `tests/test_suite_baseline.py::test_THE_RULING_IS_RECORDED_AT_THE_CODE_with_its_reasoning` and that an
   edit "must keep those and ADD to them". Measured: `tests/test_suite_baseline.py` does not exist, no
   class of any cited name exists anywhere under `tests/`, and `git log -S` shows the deletion in
   `19313eed`. The item's own later history carries the maintainer ruling that such text pins "will not be
   restored" and that "Edits do not need to preserve exact phrases for code pins". So the executor is
   FREE to rewrite the phrases, and must not restore a text-pinning test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the direction before rewording anything

- [ ] E-01 RE-DERIVE FACTS 2 AND 3 IN YOUR OWN LANE before editing any file, because the whole correction rests on them and a reworded banner justified by a measurement that no longer holds would be a worse defect than the one being fixed. Build the matrix directly: call `runner_shared._relative_revalidation_verdict` with ONE red measurement and vary ONLY the item's `attempts[-1]["suite_baseline"]` across (a) a `completed` baseline naming the same failing id, (b) a `completed` baseline naming a different id, (c) a `completed` baseline with an empty failing tuple, and (d) no baseline record at all. Repeat for a GREEN measurement and for an UNMEASURED one (`measured: False`). USE EXTRACTOR-SHAPED FAILING LINES (`FAILED tests/t.py::test_a - assert 1 == 2`), NOT bare node ids: `normalize_failure_id` maps an unparseable line to `UNPARSEABLE_FAILURE_ID`, so a bare id collapses both sides to `<unparseable>` and fabricates a match. This mistake was made and caught at authoring; the numbers in fact 2 are from the corrected run. Record the full matrix even if it differs from this plan's.
  - Depends on: none
  - Expected outcome: the pasted matrix for all three measurement kinds, plus an explicit sentence stating whether any baseline value turned a pass into a refusal. If one did, fact 3 is falsified, the corrected wording in E-03 is wrong as drafted, and you must stop and say so rather than proceed.
  - Execution state: pending

- [ ] E-02 CONFIRM THE PROHIBITION'S ORIGINAL TARGET IS STILL UNREACHED, so the rewording narrows the rule's WORDING without narrowing the rule. Show that `perform_gate_answer` still reaches no decision on the baseline: demonstrate that a `not-mine` adjudication produces the same release outcome whether the failing id is in the baseline or not, by driving the function rather than by reading it. Also confirm by inspection that `baseline` still appears in that function only in the question-construction and record-writing calls. This is the property the four numbered reasons protect and the one thing the reworded banner must still forbid.
  - Depends on: E-01
  - Expected outcome: pasted evidence that the two adjudication outcomes are equal, plus a one-line statement that the rejected `not-mine` gate remains absent.
  - Execution state: pending

### Task group 2: pin the direction rule

- [ ] E-03 ADD THE BEHAVIORAL PIN in a new `tests/test_suite_baseline_direction.py`, asserting the DIRECTION as a property rather than asserting any banner text. Two assertions, both driving `_relative_revalidation_verdict`: (a) the permissive direction is REACHABLE, so a red measurement whose failures the baseline names passes where the same measurement with no baseline refuses (this is what makes the corrected wording necessary, and it fails if someone later "restores" the absolute prohibition by deleting the relative verdict); and (b) the forbidden direction is ABSENT, so across the matrix from E-01 no baseline value turns a pass into a refusal (this is the ruling itself, in executable form). Assert on returned verdicts only. DO NOT read module source, and DO NOT assert on the presence or absence of any comment phrase: fact 5's deleted test was exactly such a pin and the maintainer has ruled it will not be restored (AGENTS.md; GUIDING_PRINCIPLES P16). Give the file a docstring naming this plan and stating that it pins the DIRECTION and not the prose.
  - Depends on: E-02
  - Expected outcome: a passing new test file, plus a pasted demonstration that assertion (b) is not vacuous (see V-03 for the required mutation).
  - Execution state: pending

### Task group 3: correct the record

- [ ] E-04 REWORD THE BANNER'S HEADLINE AND ITS FALSE CONSUMER SENTENCE. Give the headline its direction: the baseline is information for an honest agent, and NOTHING MAY REFUSE OR DOWNGRADE AN OUTCOME on the strength of it, while a comparison that can ONLY make an outcome more permissive is permitted and one exists. State the test from the direction the reader needs: what is forbidden is using the baseline to DISBELIEVE the agent, which is what all four numbered reasons below it are about, so a reader who has a baseline-relative comparison in hand asks which SIGN its effect has. Replace "THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT" with the measured truth from fact 4: the prompt is the only consumer that can affect the ADJUDICATION, and `revalidation_baseline_for` is a second consumer whose effect is one-way. Cite the E-03 test as what enforces the direction, and point at the existing "THE RELATIVE REVALIDATION VERDICT" section, which already draws this exact distinction ("The sign of the effect is the whole difference") and is the evidence the correction is not an invention. KEEP the four numbered reasons and KEEP the maintainer-ruling citations with their dates: they are the record of what was decided and are not being revisited. DO NOT touch the "Nothing in this package compares `suite_baseline['failures']` to `failing_tests`" sentence, which fact 4 measured as still true.
  - Depends on: E-03
  - Expected outcome: the `git diff` of the banner, showing the directed headline, the corrected consumer sentence, the four reasons and ruling citations intact, the E-03 citation present, and no executable line changed.
  - Execution state: pending

- [ ] E-05 AMEND SPEC `25kzda` SECTION 5.1's "THE HONEST LIMIT" PARAGRAPH to carry the same direction, since it is the NORMATIVE twin of the banner and is what a graduating plan is reviewed against; leaving it undirected would leave the authoritative copy of the defect in place while the comment is fixed. Its sentence "a pre-work baseline may be supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses on it" is true of the ADJUDICATION and is the sentence to make precise: nothing may refuse ON the baseline, and a comparison that only ever makes a gate more permissive is not such a refusal. Say explicitly that the 2026-09-08/2026-09-20 rulings are UNCHANGED and that only the direction is being named, so this is not read as a relitigation. Append the amendment to the spec's `## Workflow history` per repository convention, naming this plan and the measurement it rests on. DO NOT change the conjunctive conditions, the closed answer vocabulary, the two answers that may release, or the attribution argument.
  - Depends on: E-04
  - Expected outcome: the `git diff` of section 5.1 plus the appended history line, showing the direction named, the rulings preserved verbatim, and no other normative text altered.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here is by symbol or quoted string; the two commit citations (`19313eed`, `bfa5a6f7`) are durable shas.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (AGENTS.md). This plan declares the `25kzda` spec file in `- Scope-Paths:` so both runners announce the spec edit before the run starts and the finalize scope gate can reconcile it. The amendment is in E-05 and its reason is in Spec / documentation sync.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). Load-bearing here, because the obvious test for "the banner now says the right thing" is a text assertion, which is the banned structural pin AND is the exact test the maintainer ruled will not be restored (fact 5). E-04 and E-05 are validated by their diffs; E-03 pins the property the prose describes.
- THE BANNER'S OWN NEIGHBOURHOOD ALREADY CONTAINS THE CORRECT DISTINCTION, so E-04 restates rather than invents. `runner_shared`'s "THE RELATIVE REVALIDATION VERDICT (revalbase 01, `tgyfs2`)" section says the prohibition is about the adjudication answer, that the rejected proposal made an outcome WORSE, that what happens there is "the opposite direction", and that "the sign of the effect is the whole difference". The defect is that this lives beside the new code instead of in the rule.
- RUN THE SUITE BARE (AGENTS.md). `pyproject.toml` `addopts` already supplies quiet, parallel and the fast subset; a second `-q` would suppress the `N passed` line this plan requires pasted. Use `-o addopts=""` when a per-test count from a narrowed run is needed.
- THE MUTATION-DEMONSTRATION CONVENTION IS ESTABLISHED IN THIS REPOSITORY and V-03 requires it. Sibling pending plans `cvs2b7` and `jw6cm3` both require a mutate/fail/restore/pass triple for every test they add, on the reasoning that a test that passes is not evidence it tests anything. It matters more than usual for E-03's assertion (b), which is a NEGATIVE property and would pass against a stub.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The undirected headline is present verbatim | "NOTHING MAY REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT" in `runner_shared`'s `THE PRE-WORK SUITE BASELINE` banner | E-04 rewords it |
| F-2 | Shipped code already changes an outcome on the strength of the baseline, so the headline is FALSE, not merely terse | One red measurement through `_relative_revalidation_verdict`: `passed=True` with a baseline naming the failing id, `passed=False` with no baseline | Raises the defect from readability to incorrectness and is the core justification for E-04/E-05 |
| F-3 | The asymmetry holds: no baseline value makes an outcome stricter | Same matrix over green, red and unmeasured measurements: green passes under every baseline, unmeasured refuses under every baseline, no pass becomes a refusal | The corrected wording is an observed property, and E-03(b) pins it |
| F-4 | The banner carries a SECOND false sentence the item does not mention | "THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT"; measured, `revalidation_baseline_for` reads the same `attempt["suite_baseline"]` record and feeds `new_failures_since_baseline` | E-04 corrects it too; fixing the direction alone would leave a false claim in the same paragraph |
| F-5 | A neighbouring claim that LOOKS equally false is still TRUE and must be left alone | `gate_answer_record`'s "Nothing in this package compares `suite_baseline['failures']` to `failing_tests`": the relative verdict compares the baseline to the MERGED tree's failures, not to `failing_tests` | E-04 is explicitly forbidden from "correcting" it |
| F-6 | The item's closing NOTE is stale and its instruction must be refused | `tests/test_suite_baseline.py` absent; no cited class exists under `tests/`; `git log -S` shows deletion in `19313eed`; the item's own 2026-09-28 ruling says such pins will not be restored | E-03 pins BEHAVIOR; the preserve-five-exact-phrases constraint is refused, freeing E-04 to reword |
| F-7 | The spec twin carries the same undirected wording | `25kzda` 5.1 "THE HONEST LIMIT": "a pre-work baseline may be supplied to the agent as INFORMATION ... but nothing refuses on it" | E-05 exists; the normative copy is the one a graduating plan is reviewed against |
| F-8 | The correct distinction already exists in the tree, beside the new code | `runner_shared`'s "THE RELATIVE REVALIDATION VERDICT" section: "That is a gate that makes an outcome WORSE ... What happens HERE is the opposite direction ... The sign of the effect is the whole difference" | E-04 relocates an existing, reviewed distinction into the rule rather than inventing one |
| F-9 | The banner cites two test classes in an absent file | "`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`" and "`::TheTwoMeasurementsAreComparable`" in the banner; neither file nor class exists | OUT OF SCOPE, carried by `gia5i7`. E-04 edits text CONTAINING these citations: it must not add a new one |

## Proposed changes (ordered, validatable)

1. Re-derive the direction matrix in the executor's own lane, with extractor-shaped failing lines (E-01).
2. Confirm the originally-rejected `not-mine` gate is still absent from `perform_gate_answer` (E-02).
3. Add a behavioral test pinning both halves of the direction rule (E-03).
4. Reword the banner's headline and its false consumer sentence, keeping the four reasons (E-04).
5. Amend spec `25kzda` 5.1 to name the same direction, with a history line (E-05).

## Deferred / out of scope (with reason)

- CHANGING WHAT THE PROHIBITION FORBIDS. The rejected proposal, refusing a `not-mine` claim for a failing id absent from the baseline, stays forbidden, and the four numbered reasons stay. This plan changes only the wording's scope.
  - Carrier-Declined: A scope fence, not deferred work. No finding measures a fault in the ruling; F-1 and F-7 measure a fault in how it is STATED. Filing an item would assert the repository intends to revisit a maintainer ruling it does not.
- THE DANGLING `tests/test_suite_baseline.py` CITATIONS in the very banner E-04 edits (F-9). Not fixed here: the remedy is a nine-site citation sweep across two modules with a different subject, and doing it inside this plan would bury the correction this plan exists to make.
  - Carrier: gia5i7
- RESTORING A TEXT-PINNING TEST for the reworded banner, which the backlog item's own NOTE effectively asks for by requiring five exact phrases be preserved. REFUSED ON A MAINTAINER RULING, not deferred: the item's 2026-09-28 history says such pins will not be restored and edits need not preserve exact phrases, and AGENTS.md plus GUIDING_PRINCIPLES P16 forbid tests that read production source text.
  - Carrier-Declined: Nothing is owed because there is no latent work, only a constraint this plan measured as withdrawn. Filing it would assert the repository intends to restore a pin its maintainer has ruled against twice.
- THE `run_viewer`-STYLE QUESTION OF WHETHER THE TWO BASELINE CONSUMERS SHOULD SHARE A READER. `suite_baseline_context` renders the record for the prompt and `revalidation_baseline_for` parses it for the verdict; they duplicate no logic worth unifying and each is documented where it sits.
  - Carrier-Declined: Nothing is owed because this is not a defect. The two answer different questions from one record, which is the shape F-4's correction describes; an item would imply a refactor this plan has no measurement to justify.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` holds the banner, the relative-verdict section that already carries the correct distinction, `_relative_revalidation_verdict`, `revalidation_baseline_for` and `perform_gate_answer`, so every code-side fact and edit is in one file. The spec file is declared because E-05 amends the normative twin, which AGENTS.md requires be declared so the runners can announce it. The new test file is the only test surface added.
- Under-scope: `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` are deliberately NOT declared: both reach this logic through `runner_shared`, and neither carries the text being corrected. No existing test file is declared, because E-03 adds a new one and no existing test asserts on this property (measured: `grep` for `_relative_revalidation_verdict` and `new_failures_since_baseline` across `tests/` returns nothing). If the executor concludes an edit outside these paths is required, that is a scope change to stop and re-declare rather than absorb.

## Required tests / validation

- Bare `python3 -m pytest` with the `N passed` summary line pasted, against a pre-execution baseline captured the same way BEFORE any edit lands. A pre-existing failure must be shown pre-existing by that baseline rather than argued harmless.
- A targeted run of the new `tests/test_suite_baseline_direction.py` with `-o addopts=""` for the per-test count.
- A MUTATION DEMONSTRATION for E-03, required in full because assertion (b) is a negative property that a stub satisfies: paste each assertion FAILING under a mutation that genuinely breaks it, then PASSING after restore.
- A `git status --short` after E-01 and after each mutation demonstration, proving every exploratory mutation was reverted before any real edit landed and before commit.
- `aw ipd lint --phase pre-transition` conforming, `aw check` no worse than a pre-change baseline with both counts pasted, and `aw sanitize --agent` clean.
- NO TEST MAY ASSERT ON THE PRESENCE OR ABSENCE OF BANNER OR SPEC TEXT. E-04 and E-05 are validated by their diffs (V-04, V-05). Such a test would violate P16 and would itself become the next stale-text defect (F-6).

## Spec / documentation sync

- SPEC `25kzda` IS AMENDED BY E-05, declared in `- Scope-Paths:` as AGENTS.md requires. WHY, since a spec edit changes the contract every other plan is reviewed against: section 5.1's "THE HONEST LIMIT" is the normative statement of the same rule the banner states informally, and it carries the same undirected wording (F-7). Correcting only the comment would leave the authoritative copy of the defect in place, and a future `/plan-review` reads the spec, not the comment. The amendment NARROWS THE WORDING'S SCOPE AND NOT THE RULE: the 2026-09-08 and 2026-09-20 rulings are preserved verbatim, the conjunctive release conditions and the closed answer vocabulary are untouched, and the only change is that "nothing refuses on it" becomes explicit that a comparison which can only make a gate more permissive is not a refusal. That reading is already the one shipped code relies on (F-2), so the amendment describes the tree rather than changing it.
- PRECEDENT FOR THE AMENDMENT'S SHAPE: the same spec was amended on 2026-09-23 by plan `n9na1c` to extend section 5.1's exception to the second gate, and that note records the HONEST LIMIT paragraph as deliberately unchanged. This plan touches that paragraph, which is why it declares the spec and states the reason here.
- NO CHANGELOG ENTRY. This is a comment, spec-prose and test change with no user-visible behavior difference; the relative verdict behaves identically before and after.
- HISTORICAL RECORDS ARE LEFT ALONE. Executed plan `tgyfs2` and its review record their interpretation of the banner as it then read; rewriting them would falsify history, and the plan contract forbids changing what an executed record records.

## Open questions

### OQ-01: Should the corrected banner state the direction as a bare rule, or keep a pointer to the relative-verdict section as the worked example?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-04 KEEPS the pointer. The argument for keeping: F-8 shows the distinction already exists beside the new code, and a reader who meets the abstract rule ("the sign of the effect decides") benefits from being shown the one live case that is permitted, which is exactly the question `tgyfs2` had to answer from scratch. The argument against: a pointer dates as soon as the section is renamed, and the rule should stand alone. NOT BLOCKING because every other E-04 requirement (the directed headline, the corrected consumer sentence, the preserved reasons and rulings) is identical under either answer, and the difference is one clause.
- Carrier-Declined: No carrier is owed under either answer, because both are fully implemented inside E-04 and neither leaves anything unbuilt. V-04's required evidence is identical in both cases. Filing an item would imply an outstanding edit remains after this plan executes, and none does.

### OQ-02: Should E-03's pin live in a new file or beside an existing revalidation test?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-03 creates `tests/test_suite_baseline_direction.py`, because measurement found NO existing test exercising `_relative_revalidation_verdict` or `new_failures_since_baseline` at all, so there is no natural host class to join and the two files the banner cites as the historical guards do not exist (F-6, F-9). Against that: a new top-level test file for two assertions is a small file, and a future reader may not find it. NOT BLOCKING because the assertions, the mutation demonstration and the docstring V-03 requires are identical wherever the test lives; only the path changes, and the path is declared in `- Scope-Paths:` either way.
- Carrier-Declined: No carrier is owed under either answer. Both branches are implemented inside E-03 and neither leaves anything unbuilt: the executor records which it chose, and V-03's mutation evidence proves the pin works regardless of location.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the PASTED direction matrix from the executor's own lane covering all three measurement kinds (green, red, unmeasured) against all four baseline variants, plus an explicit sentence stating whether ANY baseline value turned a pass into a refusal. Confirm by showing the fixture's failing lines that extractor-shaped lines were used, not bare node ids, since a bare id normalizes to `<unparseable>` on both sides and produces a false match (the authoring error this item records). Plus a pasted `git status --short` showing no file modified by the measurement. Numbers differing from F-2/F-3 are EXPECTED and satisfy this item; reusing this plan's numbers without running does NOT.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted evidence that a `not-mine` adjudication produces the SAME release outcome with and without a baseline naming the failing id, obtained by DRIVING the function rather than by reading it, plus a one-line statement that the rejected `not-mine` gate remains absent. Reading the control flow alone does NOT satisfy this item, because the whole point of the rewording is that a reader can be wrong about what the code does on the baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted PASS of the new test file, AND a separate mutation demonstration for EACH of the two assertions, each showing the assertion FAILING under a mutation and PASSING after restore. For (a) the permissive direction, a mutation that makes the relative verdict ignore the baseline must make it fail. For (b) the no-stricter property, a mutation that makes some baseline value turn a pass into a refusal must make it fail; a passing (b) with no paired failure does NOT satisfy this item, since (b) is a negative property that a stub satisfies. Plus confirmation, shown by reading the test file, that it asserts only on returned verdicts and reads no module source and no comment text.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `git diff` of the banner, shown to change comment text only with no executable line altered, and state how that was confirmed from the diff. The diff must show: the headline now naming the DIRECTION (refuse/downgrade forbidden, more-permissive allowed); the "ONLY CONSUMER IS THE ADJUDICATION PROMPT" sentence corrected per F-4; all four numbered reasons PRESENT; both maintainer-ruling dates PRESENT; the E-03 test cited; and the `gate_answer_record` sentence from F-5 UNTOUCHED. Confirm no NEW citation to a nonexistent test file or class was added (F-9). Do NOT satisfy this item with a test that inspects source text; the diff is the evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `git diff` of spec `25kzda` section 5.1 plus the appended `## Workflow history` line, pasted. The diff must show the direction named, the 2026-09-08/2026-09-20 ruling sentences preserved, and NO change to the conjunctive conditions, the closed answer vocabulary, the two releasing answers, or the attribution argument. Confirm the history line names this plan and the measurement the amendment rests on. Plus a statement that no other `.spec.md` file was modified, reconciled against `- Scope-Paths:`, since an undeclared spec edit is reported by both runners at run end.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

The executor must: perform E-01 through E-05 in order, respecting the declared `Depends on` edges; treat
E-01 as a HARD GATE, because if fact 3 fails to reproduce then the corrected wording drafted in E-04 is
itself false and the plan must stop rather than install a new incorrect rule; commit only the three paths
in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL runner output for every
claim of a passing test, INCLUDING both mutation demonstrations V-03 requires; and verify each `V-*` in a
separate pass from the `E-*` that produced it. Do NOT mark this plan executed or move it to
`.aw/records/plans/executed/` until every `V-*` carries concrete pasted evidence and
`aw ipd lint --phase pre-transition` conforms.

THE ONE WAY TO GET THIS PLAN WRONG is to read "the prohibition is too absolute" as "the prohibition is
wrong". It is not. The rejected gate, refusing a `not-mine` claim because the failing id is absent from
the baseline, remains forbidden for all four of the reasons the banner gives, and E-02 exists to prove it
is still absent before E-04 touches a word. This plan makes the rule SAY what it has always MEANT. If you
find yourself weakening what the baseline may not do, or adding any comparison that makes an outcome
worse, stop.

A SECOND, SUBTLER WAY TO GET IT WRONG: the banner and its neighbours contain one sentence that is false
(F-4) and one that merely LOOKS false (F-5). Correct the first and leave the second, and say in V-04 how
you told them apart.

Backlog item `aced01` is this plan's origin (`- From-Backlog: aced01`). That item carries NO
`- Blocks-Release:` gate and none is invented here. The `chore` classification is CONFIRMED by
measurement rather than inherited: no user-perceptible behavior is wrong, the relative verdict already
behaves correctly, and no operator waits on anything, so the cost falls on the next author to read the
rule (AGENTS.md's perceptibility test). What the item under-measured was not severity but the defect's
KIND: it recorded a terse-but-true banner needing one added sentence, where measurement shows a banner
that is FALSE as written against shipped code (F-2), carries a second false sentence (F-4), and instructs
its executor to preserve phrases under a constraint that no longer exists (F-6).
