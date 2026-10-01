# IPD: Name the direction the pre-work suite baseline prohibition forbids

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared`'s `THE PRE-WORK SUITE BASELINE` banner states its prohibition with no DIRECTION: "THE BASELINE IS INFORMATION FOR AN HONEST AGENT, NOT A CHECK ON A DISHONEST ONE. NOTHING MAY REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT." All four of its numbered reasons forbid using the baseline to make an outcome WORSE, but the headline forbids changing an outcome AT ALL, and spec `25kzda` 5.1's "THE HONEST LIMIT" carries the same undirected wording ("nothing refuses on it"). MEASURED IN THIS LANE AT HEAD `bfa5a6f7`, and this is worse than the item knew: shipped code already changes a post-merge outcome on the strength of the baseline. `_relative_revalidation_verdict` on one red measurement returns `passed=True` when the baseline names the failing id and `passed=False` when no baseline exists, so the banner's headline, read literally, now forbids code that is live, reviewed, and correct. Its own body separately claims "THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT", which the same measurement falsifies: `revalidation_baseline_for` is a second consumer reading the same `attempt["suite_baseline"]` record.
- Scope: Correct the banner so it states the DIRECTION it forbids (a baseline may never make an outcome WORSE; it may make one more permissive) and so it stops claiming a single consumer that measurement contradicts, then carry the same direction into spec `25kzda` 5.1's "THE HONEST LIMIT" paragraph, which is the normative twin of the banner and is what a graduating plan is reviewed against. Give the direction rule a behavioral test, since it is currently unpinned in the one direction that matters. EXCLUDES any change to what the prohibition actually forbids (the rejected `not-mine` gate stays forbidden), EXCLUDES any change to `perform_gate_answer`'s baseline-free control flow, and EXCLUDES the dangling `tests/test_suite_baseline.py` citations in the same banner (carried by backlog `gia5i7`).
- Scope-Paths: agent_workflows/runner_shared.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_suite_baseline_direction.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: aced01
- Set: aced01
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: kcc71f
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-603 all FIXED, none deferred or open, no BLOCKER and no unfixed HIGH. ALL NINE OF THE PLAN'S FINDINGS REPRODUCE AND I DROVE THE CODE RATHER THAN READING IT, since the central claim is that a comment is FALSE against shipped behavior. The direction matrix reproduces cell for cell at HEAD c053dd2f: one red measurement passes at True only when the baseline names its failing id and refuses for a baseline naming another id, an empty completed baseline, or none; green passes under all four variants; unmeasured refuses under all four; and NO baseline value turns a pass into a refusal, so F-2 and F-3 both hold. Worth recording: my first attempt reproduced nothing because I passed failing_tests where the function reads failures and needs suite_passed, which is the adjacent trap E-01 already warns about, so that warning earned its place. F-5 is the subtle one and the plan is right to protect it: the gate_answer_record sentence is still TRUE because the comparison is against the merged tree's failures, not failing_tests. I additionally DROVE perform_gate_answer twice with a real outcome file and confirmed a not-mine answer releases identically with and without a baseline naming the failing id, so E-02 is executable as written; and I confirmed V-03's negative assertion (b) demands PRODUCIBLE evidence by patching the verdict so a baseline turns a pass into a refusal, watching all three green rows flip, then reverting clean. TWO HIGH DEFECTS, both about a record the plan is one edit from damaging. PR-601: E-05 edits the very HONEST LIMIT paragraph that the spec's own 2026-09-23 note lists under 'WHAT IS UNCHANGED, deliberately and verbatim', and the plan cites that note only as PRECEDENT, so the spec would carry two unconnected notes contradicting each other about the same paragraph; the earlier note may not be edited, so the new one must reconcile it by distinguishing the preserved RULING from the changed WORDING. PR-602: E-04 must add a live citation into a sentence that already ENDS in a dangling one owned by gia5i7, and both natural instincts are wrong, since striking it absorbs another item's declared work undeclared while re-pointing it at the new test is wrong on the merits because E-03 pins the DIRECTION and not the not-mine byte-identical-outcome property. PR-603: both open questions carried Owner: reviewer, so I resolved them in the drafted direction but on independently measured grounds, recorded as D-1 and D-2. I also read all three pending plans that both declare this spec and contain 'HONEST LIMIT' and confirmed every one uses the phrase for the unrelated host-capability preflight docstring, so the edit surfaces are disjoint and no dependency edge is owed. I AGREE with the chore classification and the refusal to invent a release gate, and record the agreement rather than passing over it. Bare suite 3361 passed, 2 skipped, 3 warnings in 137.59s; tree clean after every probe.

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

- [x] E-01 RE-DERIVE FACTS 2 AND 3 IN YOUR OWN LANE before editing any file, because the whole correction rests on them and a reworded banner justified by a measurement that no longer holds would be a worse defect than the one being fixed. Build the matrix directly: call `runner_shared._relative_revalidation_verdict` with ONE red measurement and vary ONLY the item's `attempts[-1]["suite_baseline"]` across (a) a `completed` baseline naming the same failing id, (b) a `completed` baseline naming a different id, (c) a `completed` baseline with an empty failing tuple, and (d) no baseline record at all. Repeat for a GREEN measurement and for an UNMEASURED one (`measured: False`). USE EXTRACTOR-SHAPED FAILING LINES (`FAILED tests/t.py::test_a - assert 1 == 2`), NOT bare node ids: `normalize_failure_id` maps an unparseable line to `UNPARSEABLE_FAILURE_ID`, so a bare id collapses both sides to `<unparseable>` and fabricates a match. This mistake was made and caught at authoring; the numbers in fact 2 are from the corrected run. Record the full matrix even if it differs from this plan's.
  - Depends on: none
  - Expected outcome: the pasted matrix for all three measurement kinds, plus an explicit sentence stating whether any baseline value turned a pass into a refusal. If one did, fact 3 is falsified, the corrected wording in E-03 is wrong as drafted, and you must stop and say so rather than proceed.
  - Execution state: performed

- [x] E-02 CONFIRM THE PROHIBITION'S ORIGINAL TARGET IS STILL UNREACHED, so the rewording narrows the rule's WORDING without narrowing the rule. Show that `perform_gate_answer` still reaches no decision on the baseline: demonstrate that a `not-mine` adjudication produces the same release outcome whether the failing id is in the baseline or not, by driving the function rather than by reading it. Also confirm by inspection that `baseline` still appears in that function only in the question-construction and record-writing calls. This is the property the four numbered reasons protect and the one thing the reworded banner must still forbid.
  - Depends on: E-01
  - Expected outcome: pasted evidence that the two adjudication outcomes are equal, plus a one-line statement that the rejected `not-mine` gate remains absent.
  - Execution state: performed

### Task group 2: pin the direction rule

- [x] E-03 ADD THE BEHAVIORAL PIN in a new `tests/test_suite_baseline_direction.py`, asserting the DIRECTION as a property rather than asserting any banner text. Two assertions, both driving `_relative_revalidation_verdict`: (a) the permissive direction is REACHABLE, so a red measurement whose failures the baseline names passes where the same measurement with no baseline refuses (this is what makes the corrected wording necessary, and it fails if someone later "restores" the absolute prohibition by deleting the relative verdict); and (b) the forbidden direction is ABSENT, so across the matrix from E-01 no baseline value turns a pass into a refusal (this is the ruling itself, in executable form). Assert on returned verdicts only. DO NOT read module source, and DO NOT assert on the presence or absence of any comment phrase: fact 5's deleted test was exactly such a pin and the maintainer has ruled it will not be restored (AGENTS.md; GUIDING_PRINCIPLES P16). Give the file a docstring naming this plan and stating that it pins the DIRECTION and not the prose.
  - Depends on: E-02
  - Expected outcome: a passing new test file, plus a pasted demonstration that assertion (b) is not vacuous (see V-03 for the required mutation).
  - Execution state: performed

### Task group 3: correct the record

- [x] E-04 REWORD THE BANNER'S HEADLINE AND ITS FALSE CONSUMER SENTENCE. Give the headline its direction: the baseline is information for an honest agent, and NOTHING MAY REFUSE OR DOWNGRADE AN OUTCOME on the strength of it, while a comparison that can ONLY make an outcome more permissive is permitted and one exists. State the test from the direction the reader needs: what is forbidden is using the baseline to DISBELIEVE the agent, which is what all four numbered reasons below it are about, so a reader who has a baseline-relative comparison in hand asks which SIGN its effect has. Replace "THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT" with the measured truth from fact 4: the prompt is the only consumer that can affect the ADJUDICATION, and `revalidation_baseline_for` is a second consumer whose effect is one-way. Cite the E-03 test as what enforces the direction, and point at the existing "THE RELATIVE REVALIDATION VERDICT" section, which already draws this exact distinction ("The sign of the effect is the whole difference") and is the evidence the correction is not an invention. CITE THE NEW TEST BY FILE AND TEST NAME, AND DO NOT REPLACE OR REPAIR THE ADJACENT DANGLING CITATION, which is the collision this item is one edit away from (F-11, added at review). The sentence E-04 rewrites currently ENDS with "`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` asserts a `not-mine` verdict produces a byte-identical outcome whether the failing id appears in the baseline or not" - a citation to a file that does not exist, and one of FOUR such citations in this module that `gia5i7` owns. So E-04 must keep the two acts separate and say which it did: ADD the live `tests/test_suite_baseline_direction.py` citation for the DIRECTION property, and LEAVE the dangling `NothingRefusesOnTheBaseline` citation exactly as it stands even though it sits in the same sentence. Striking it here would silently absorb `gia5i7`'s work into a plan that does not declare it and would leave that item's own measurement (four sites in this module) stale; "fixing" it by re-pointing it at the new E-03 file would be WRONG on the merits, because E-03 pins the direction rule and NOT the `not-mine` byte-identical-outcome property that citation describes, so the two are not substitutes. The honest outcome is a banner carrying one live citation beside one dangling one, with `gia5i7` named as the carrier for the latter. KEEP the four numbered reasons and KEEP the maintainer-ruling citations with their dates: they are the record of what was decided and are not being revisited. DO NOT touch the "Nothing in this package compares `suite_baseline['failures']` to `failing_tests`" sentence, which fact 4 measured as still true.
  - Depends on: E-03
  - Expected outcome: the `git diff` of the banner, showing the directed headline, the corrected consumer sentence, the four reasons and ruling citations intact, the E-03 citation present, the adjacent dangling `NothingRefusesOnTheBaseline` citation UNCHANGED and still carried by `gia5i7` (F-11), and no executable line changed.
  - Execution state: performed

- [x] E-05 AMEND SPEC `25kzda` SECTION 5.1's "THE HONEST LIMIT" PARAGRAPH to carry the same direction, since it is the NORMATIVE twin of the banner and is what a graduating plan is reviewed against; leaving it undirected would leave the authoritative copy of the defect in place while the comment is fixed. Its sentence "a pre-work baseline may be supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses on it" is true of the ADJUDICATION and is the sentence to make precise: nothing may refuse ON the baseline, and a comparison that only ever makes a gate more permissive is not such a refusal. Say explicitly that the 2026-09-08/2026-09-20 rulings are UNCHANGED and that only the direction is being named, so this is not read as a relitigation. Append the amendment to the spec's `## Workflow history` per repository convention, naming this plan and the measurement it rests on. DO NOT change the conjunctive conditions, the closed answer vocabulary, the two answers that may release, or the attribution argument.
  THE NEW HISTORY LINE MUST RECONCILE THE 2026-09-23 NOTE, WHICH THIS AMENDMENT FALSIFIES IF LEFT UNADDRESSED (F-10, added at review). That note, already in the spec's `## Workflow history`, lists among "WHAT IS UNCHANGED, deliberately and verbatim ... the HONEST LIMIT paragraph including the maintainer's 2026-09-08/2026-09-20 ruling that no gate may refuse on the strength of a pre-work baseline". E-05 edits exactly that paragraph, so after this plan the earlier note asserts a verbatim preservation that no longer holds, and a reader comparing the two would conclude one of them is wrong. DO NOT EDIT THE 2026-09-23 NOTE: it was true when written and the plan contract forbids rewriting a record. Instead, the NEW note must say plainly that it amends the HONEST LIMIT paragraph the 2026-09-23 note recorded as unchanged, and that what that note was protecting - the RULING - is still preserved verbatim while only the paragraph's undirected WORDING changed. That distinction is the whole content of this plan, so stating it in the history is where a future reader will look for it.
  - Depends on: E-04
  - Expected outcome: the `git diff` of section 5.1 plus the appended history line, showing the direction named, the rulings preserved verbatim, and no other normative text altered; the new history line explicitly reconciles the 2026-09-23 note's "verbatim" claim about this paragraph (F-10), and that earlier note is shown UNMODIFIED in the diff.
  - Execution state: performed

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
| F-10 | ADDED AT REVIEW. E-05 falsifies an existing spec history note unless the new note reconciles it | The spec's own `- 2026-09-23 note (aw specs)` line lists among "WHAT IS UNCHANGED, deliberately and verbatim ... the HONEST LIMIT paragraph including the maintainer's 2026-09-08/2026-09-20 ruling"; E-05 edits exactly that paragraph | E-05 must say in its NEW history line that it amends the paragraph the 2026-09-23 note recorded as verbatim-unchanged, preserving the RULING while changing only the undirected wording, and must NOT edit that earlier note. Without this the spec carries two history lines that contradict each other about the same paragraph, in the file a graduating plan is reviewed against |
| F-11 | ADDED AT REVIEW. E-04's new citation lands in the same sentence as a dangling one it must not touch | The sentence E-04 rewrites ends "`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` asserts a `not-mine` verdict produces a byte-identical outcome ..."; that file is absent and is one of FOUR such citations in this module, all owned by `gia5i7` (measured: `grep -c "tests/test_suite_baseline.py" agent_workflows/runner_shared.py` = 4) | E-04 must ADD the live citation and LEAVE the dangling one, saying which it did. Striking it would absorb `gia5i7`'s declared work undeclared and stale that item's own four-site measurement; re-pointing it at the E-03 file would be WRONG on the merits, since E-03 pins the DIRECTION and not the `not-mine` byte-identical-outcome property that citation describes |
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
- THE DANGLING `tests/test_suite_baseline.py` CITATIONS in the very banner E-04 edits (F-9). Not fixed here: the remedy is a nine-site citation sweep across two modules with a different subject, and doing it inside this plan would bury the correction this plan exists to make. CONFIRMED AT REVIEW that the carrier genuinely covers these and not only its headline symbol: `gia5i7`'s body names `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` and `::TheTwoMeasurementsAreComparable` explicitly and records both files still absent, so nothing is orphaned by deferring them. THE BOUNDARY IS NARROWER THAN "do not sweep", and F-11 states it: one of these citations sits INSIDE the sentence E-04 rewrites, so E-04 must add its own live citation beside it and leave it standing rather than striking or re-pointing it.
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
- PRECEDENT FOR THE AMENDMENT'S SHAPE: the same spec was amended on 2026-09-23 by plan `n9na1c` to extend section 5.1's exception to the second gate, and that note records the HONEST LIMIT paragraph as deliberately unchanged. This plan touches that paragraph, which is why it declares the spec and states the reason here. AND THAT PRECEDENT IS ALSO A CONFLICT THIS PLAN MUST SETTLE, not merely a model to copy (F-10, added at review): the 2026-09-23 note's exact words are "WHAT IS UNCHANGED, deliberately and verbatim: ... the HONEST LIMIT paragraph including the maintainer's 2026-09-08/2026-09-20 ruling", so once E-05 lands, that note asserts a verbatim preservation of a paragraph this plan reworded. The earlier note is NOT edited (it was true when written, and the plan contract forbids rewriting a record); E-05's new note reconciles it by naming the paragraph and distinguishing the RULING, which stays verbatim, from the undirected WORDING, which is what changes. A reader landing on either note must be able to reach the other's meaning without concluding one is false.
- THE SPEC IS UNDER CONCURRENT AMENDMENT BY MANY PLANS AND THAT IS NOT A BLOCKER HERE, recorded so a reviewer does not read it as an undeclared hazard: measured at review, sixteen pending plans declare this spec file in `- Scope-Paths:`, several `reviewed`. Of those, exactly three also contain the string "HONEST LIMIT" (`pi3bk8`, `wzhe4n`, `yu47nf`), and I read each: all three use it for the UNRELATED honest-limit paragraph in the host-capability preflight's module docstring, none names section 5.1 or the baseline prohibition, and none proposes editing that paragraph. So the edit surface here is disjoint from every concurrent plan's, and the runner's merge-and-revalidate gate handles mere textual adjacency in the same file. No `- Item-Dependencies:` edge is declared for the same reason the repository records elsewhere: the grammar offers no "prefer after" edge, and an `executed:` edge on a plan that merely shares a file would gate this work on unrelated review cycles.
- NO CHANGELOG ENTRY. This is a comment, spec-prose and test change with no user-visible behavior difference; the relative verdict behaves identically before and after.
- HISTORICAL RECORDS ARE LEFT ALONE. Executed plan `tgyfs2` and its review record their interpretation of the banner as it then read; rewriting them would falsify history, and the plan contract forbids changing what an executed record records.

## Open questions

### OQ-01: Should the corrected banner state the direction as a bare rule, or keep a pointer to the relative-verdict section as the worked example?

- Blocking: no
- Status: resolved
- Owner: reviewer (/plan-review 2026-09-30)
- Resolution or deferral rationale: KEEP THE POINTER, which is what E-04 already drafts, and the reviewer's basis is a measurement the plan does not make: the pointer's target is the ONE live permitted case in the tree, and I verified it is live rather than aspirational by driving `_relative_revalidation_verdict` across the full matrix (a red measurement passes at `True` only when the baseline names its failing id, and no baseline value turns any pass into a refusal). So the worked example a reader is sent to exists, is reachable, and is the exact shape the rule permits. THE ARGUMENT AGAINST WAS WEIGHED AND IS REAL BUT SMALLER: a section-title pointer does rot if the section is renamed, and this module has four already-rotted citations proving that risk is not hypothetical (F-9, F-11). It is outweighed here because the pointer names a SECTION HEADING in the SAME FILE rather than an external test id, so a rename is visible in the same diff that causes it, whereas the four rotted citations all point OUT of the file at a deleted test file. A reader who meets only the abstract rule has to re-derive the permitted case, which `tgyfs2` did at the cost of a full pass over three artifacts, and converting that one-off cost into the rule is this plan's stated purpose. E-04 is unchanged by this resolution.
- Carrier-Declined: No carrier is owed under either answer, because both are fully implemented inside E-04 and neither leaves anything unbuilt. V-04's required evidence is identical in both cases. Filing an item would imply an outstanding edit remains after this plan executes, and none does.

### OQ-02: Should E-03's pin live in a new file or beside an existing revalidation test?

- Blocking: no
- Status: resolved
- Owner: reviewer (/plan-review 2026-09-30)
- Resolution or deferral rationale: NEW FILE, as E-03 drafts. I re-ran the measurement the answer turns on rather than accepting it: `grep -rn "_relative_revalidation_verdict\|new_failures_since_baseline" tests/` returns NOTHING, so there is genuinely no host to join and the choice is between a new file and inventing a home in an unrelated one. The "a future reader may not find it" objection is answered by the same evidence that makes this plan necessary: the reader's entry point is the BANNER, not a test directory listing, and E-04 cites the new file from the banner, so the discovery path is the rule itself. One point the plan does not make and which settles it: the two absent files the banner cites (`tests/test_suite_baseline.py` and its classes) are precisely what happens when a guard's home is assumed rather than declared, so adding this pin to a file whose name does not say what it guards would repeat that. The filename `test_suite_baseline_direction.py` names the property, is declared in `- Scope-Paths:`, and matches the sibling convention (`cvs2b7` and `jw6cm3` both add property-named modules). E-03 is unchanged by this resolution.
- Carrier-Declined: No carrier is owed under either answer. Both branches are implemented inside E-03 and neither leaves anything unbuilt: the executor records which it chose, and V-03's mutation evidence proves the pin works regardless of location.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the PASTED direction matrix from the executor's own lane covering all three measurement kinds (green, red, unmeasured) against all four baseline variants, plus an explicit sentence stating whether ANY baseline value turned a pass into a refusal. Confirm by showing the fixture's failing lines that extractor-shaped lines were used, not bare node ids, since a bare id normalizes to `<unparseable>` on both sides and produces a false match (the authoring error this item records). Plus a pasted `git status --short` showing no file modified by the measurement. Numbers differing from F-2/F-3 are EXPECTED and satisfy this item; reusing this plan's numbers without running does NOT.
  - Observed evidence: Extracted matrix measured live in this lane via `runner_shared._relative_revalidation_verdict`:
    ```text
    measurement  | baseline             | verdict.passed  | comparison.judgement
    ---------------------------------------------------------------------------
    red          | (a) names same       | True            | no-regression
    red          | (b) names other      | False           | regressed
    red          | (c) empty completed  | False           | regressed
    red          | (d) no baseline      | False           | unknown
    green        | (a) names same       | True            | None
    green        | (b) names other      | True            | None
    green        | (c) empty completed  | True            | None
    green        | (d) no baseline      | True            | None
    unmeasured   | (a) names same       | False           | None
    unmeasured   | (b) names other      | False           | None
    unmeasured   | (c) empty completed  | False           | None
    unmeasured   | (d) no baseline      | False           | None
    ```
    Explicit statement: Across all 12 combinations, no baseline value turned a pass into a refusal.
    Extractor-shaped failing lines were verified in fixture:
    `failures = ["FAILED tests/t.py::test_a - assert 1 == 2"]` (not bare node ids).
    Pasted `git status --short` proving no file modified by the measurement:
    ```text
    ``` (clean, exit code 0)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted evidence that a `not-mine` adjudication produces the SAME release outcome with and without a baseline naming the failing id, obtained by DRIVING the function rather than by reading it, plus a one-line statement that the rejected `not-mine` gate remains absent. Reading the control flow alone does NOT satisfy this item, because the whole point of the rewording is that a reader can be wrong about what the code does on the baseline.
  - Observed evidence: Driven via `runner_shared.perform_gate_answer` with a recorded `not-mine` gate answer:
    ```text
    res_with.release: True
    res_without.release: True
    res_none.release: True
    res_with.release == res_without.release == res_none.release: True
    ```
    The rejected `not-mine` gate remains absent: `perform_gate_answer` contains no check or branching on `baseline`, using it strictly to populate the prompt and the audit record.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted PASS of the new test file, AND a separate mutation demonstration for EACH of the two assertions, each showing the assertion FAILING under a mutation and PASSING after restore. For (a) the permissive direction, a mutation that makes the relative verdict ignore the baseline must make it fail. For (b) the no-stricter property, a mutation that makes some baseline value turn a pass into a refusal must make it fail; a passing (b) with no paired failure does NOT satisfy this item, since (b) is a negative property that a stub satisfies. Plus confirmation, shown by reading the test file, that it asserts only on returned verdicts and reads no module source and no comment text.
  - Observed evidence: Verified live via pytest and mutation demonstrations:
    1. Targeted pass of new test file `tests/test_suite_baseline_direction.py`:
    ```text
    collected 2 items
    tests/test_suite_baseline_direction.py ..                                [100%]
    2 passed in 0.98s
    ```
    2. Mutation (a) demonstration: mutating `baseline = revalidation_baseline_for(item)` to `baseline = None` in `_relative_revalidation_verdict` made assertion (a) fail:
    ```text
    FAILED tests/test_suite_baseline_direction.py::test_permissive_direction_is_reachable
    AssertionError: Expected red suite with matching baseline to pass, got False: 1 failure; and the merged tree is refused because the pre-work suite baseline is 'not-started', so what was ALREADY failing before this work is UNKNOWN and no failure can be attributed to the merge (no reason recorded); an unknown baseline is NEVER read as an empty failing set
    assert False is True
    ```
    Restored and verified: 2 passed in 0.70s.
    3. Mutation (b) demonstration: adding a mutation where a passing suite is refused if baseline has failures made assertion (b) fail:
    ```text
    FAILED tests/test_suite_baseline_direction.py::test_forbidden_direction_is_absent
    AssertionError: Baseline (a) names same turned a passing green measurement into a refusal: mutated refusal on baseline
    assert False
    ```
    Restored and verified: 2 passed in 0.71s.
    4. Confirmed from reading `tests/test_suite_baseline_direction.py` that it asserts only on returned runtime verdicts from `runner_shared._relative_revalidation_verdict` and reads no module source and no comment text.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the `git diff` of the banner, shown to change comment text only with no executable line altered, and state how that was confirmed from the diff. The diff must show: the headline now naming the DIRECTION (refuse/downgrade forbidden, more-permissive allowed); the "ONLY CONSUMER IS THE ADJUDICATION PROMPT" sentence corrected per F-4; all four numbered reasons PRESENT; both maintainer-ruling dates PRESENT; the E-03 test cited; and the `gate_answer_record` sentence from F-5 UNTOUCHED. Confirm no NEW citation to a nonexistent test file or class was added (F-9), and SEPARATELY confirm the adjacent dangling `NothingRefusesOnTheBaseline` citation is byte-unchanged in the diff (F-11), stating that it was deliberately left for carrier `gia5i7` rather than overlooked. A diff that strikes or re-points that citation is a FAILED validation even if the banner otherwise reads perfectly: striking absorbs another item's declared work undeclared, and re-pointing it at the E-03 file asserts that the new test proves the `not-mine` byte-identical-outcome property, which it does not. Do NOT satisfy this item with a test that inspects source text; the diff is the evidence.
  - Observed evidence: Verified live via git diff of runner_shared.py:
    Pasted `git diff agent_workflows/runner_shared.py`:
    ```diff
    @@ -22930,7 +22930,11 @@ def format_verifier_evidence_section(state: dict[str, Any], run_dir: Path) -> li
     # WHAT THIS IS FOR, AND THE ONE SENTENCE THAT MUST NOT BE "IMPROVED" AWAY:
     #
     #     THE BASELINE IS INFORMATION FOR AN HONEST AGENT, NOT A CHECK ON A DISHONEST ONE. NOTHING MAY
    -#     REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT.
    +#     REFUSE OR DOWNGRADE AN OUTCOME ON THE STRENGTH OF IT.
    +#
    +# A comparison that can ONLY make an outcome more permissive is permitted (and one exists). What is
    +# forbidden is using the baseline to DISBELIEVE the agent, which is what all four numbered reasons below
    +# are about; so a reader who has a baseline-relative comparison in hand asks which SIGN its effect has.
     #
     # THE MAINTAINER RULED THAT EXPLICITLY, 2026-09-08 (recorded on `daexj1` OQ-02 and reaffirmed
     # 2026-09-20): "You cannot build a pre-test that detects deception ... We're mitigating sloppiness,
    @@ -22949,12 +22953,16 @@ def format_verifier_evidence_section(state: dict[str, Any], run_dir: Path) -> li
     #      believes the failure is unrelated answers `not-mine` in GOOD FAITH and is WRONG. Telling it
     #      what was already red lets it be RIGHT. That is the whole deliverable.
     #
    -# SO THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT, and its only effect is on what the
    -# agent READS. `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` asserts a `not-mine`
    -# verdict produces a byte-identical outcome whether the failing id appears in the baseline or not.
    -# If you are here to add a comparison that changes an outcome, the four reasons above say why not,
    -# and the plan's spec-sync section records that doing so would REQUIRE amending spec `25kzda`
    -# because it would change the AUTHORITY under which a red suite may be cleared.
    +# THE ADJUDICATION PROMPT IS THE ONLY CONSUMER THAT CAN AFFECT THE ADJUDICATION, and its only effect is
    +# on what the agent READS. `revalidation_baseline_for` is a second consumer whose effect is one-way:
    +# it only ever makes the post-merge gate MORE PERMISSIVE (see "THE RELATIVE REVALIDATION VERDICT" below,
    +# which already draws this exact distinction: "The sign of the effect is the whole difference").
    +# `tests/test_suite_baseline_direction.py::test_permissive_direction_is_reachable` and
    +# `tests/test_suite_baseline_direction.py::test_forbidden_direction_is_absent` enforce this direction
    +# property. Separately, `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` asserts a `not-mine`
    +# verdict produces a byte-identical outcome whether the failing id appears in the baseline or not (a
    +# dangling citation carried by `gia5i7`, deliberately left unmodified here). If you are here to add a
    +# comparison that makes an outcome stricter or disbelieves the agent, the four reasons above say why not.
     #
     # WHY THE MEASUREMENT IS COMPARABLE TO THE POST-WORK ONE, documented here because the next reader
     # needs to know whether a difference between the two id sets is real or an artifact of WHERE each
    ```
    Confirmation:
    - Every changed line begins with `# ` (comment text only; no executable line altered).
    - Headline names direction: refuse/downgrade forbidden, more-permissive allowed.
    - "ONLY CONSUMER IS THE ADJUDICATION PROMPT" corrected per F-4.
    - All four numbered reasons and both maintainer-ruling dates (2026-09-08 and 2026-09-20) present and intact.
    - E-03 test cited by file and test names (`tests/test_suite_baseline_direction.py::test_permissive_direction_is_reachable` and `::test_forbidden_direction_is_absent`).
    - No new citation to a nonexistent file/class was added (F-9).
    - Adjacent dangling citation `NothingRefusesOnTheBaseline` is byte-unchanged in the diff (F-11) and noted as carried by `gia5i7`.
    - `gate_answer_record` sentence from F-5 untouched.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the `git diff` of spec `25kzda` section 5.1 plus the appended `## Workflow history` line, pasted. The diff must show the direction named, the 2026-09-08/2026-09-20 ruling sentences preserved, and NO change to the conjunctive conditions, the closed answer vocabulary, the two releasing answers, or the attribution argument. Confirm the history line names this plan and the measurement the amendment rests on. QUOTE THE NEW HISTORY LINE'S RECONCILIATION CLAUSE (F-10) and show, from the same diff, that the existing `- 2026-09-23 note (aw specs)` line is UNMODIFIED: that note claims the HONEST LIMIT paragraph is unchanged "deliberately and verbatim", so a new note that does not name and reconcile the claim leaves the spec self-contradicting about the paragraph this plan just edited. A diff that edits the 2026-09-23 note instead of reconciling it is a FAILED validation, since it rewrites a record. Plus a statement that no other `.spec.md` file was modified, reconciled against `- Scope-Paths:`, since an undeclared spec edit is reported by both runners at run end.
  - Observed evidence: Verified live via git diff of spec 25kzda:
    Pasted `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```diff
    @@ -1149,9 +1149,12 @@ THE HONEST LIMIT, stated so the exception is not trusted further than it holds.
     "not mine" in good faith about a failure it actually caused, because it has no baseline of the suite
     before its own work and so cannot know what was already red. The maintainer ruled on 2026-09-08 and again
     on 2026-09-20 that no programmatic gate may refuse the verdict on that basis: a pre-work baseline may be
    -supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses on it. So this
    -exception mitigates SLOPPINESS and not deception, and ATTRIBUTION is what makes it safe: a wrong answer
    -is durably recorded, named, and reviewable afterwards, in the same way an attested `- Readiness:` field
    +supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses or downgrades
    +on it. That ruling is unchanged; what is made explicit here is the direction of the prohibition: nothing
    +may refuse on the baseline (using the baseline to disbelieve an agent remains forbidden), while a
    +comparison that only ever makes a gate more permissive is not such a refusal. So this exception
    +mitigates SLOPPINESS and not deception, and ATTRIBUTION is what makes it safe: a wrong answer is
    +durably recorded, named, and reviewable afterwards, in the same way an attested `- Readiness:` field
     and a `V-*` evidence block are made safe by being attributed rather than by machine verification.

     ### 5.2 Safety policy
    @@ -1603,6 +1606,8 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

     ## Workflow history

    +- 2026-10-01 note (aw specs): AMENDED (plan kcc71f, backlog aced01): Section 5.1's HONEST LIMIT paragraph amended to name the direction the pre-work suite baseline prohibition forbids: nothing may refuse or downgrade an outcome on the strength of the baseline (using the baseline to disbelieve an agent remains forbidden), while a comparison that can only ever make an outcome more permissive is permitted. Reconciles the 2026-09-23 note (plan n9na1c), which recorded the HONEST LIMIT paragraph as unchanged deliberately and verbatim: what that note protected - the maintainer's 2026-09-08/2026-09-20 ruling that no programmatic gate may refuse an outcome on the strength of a pre-work baseline - is preserved verbatim, while the paragraph's undirected wording ("nothing refuses on it") is clarified so it does not contradict shipped, reviewed, and correct permissive comparisons (such as _relative_revalidation_verdict, verified in runner_shared and pinned in tests/test_suite_baseline_direction.py). Conjunctive release conditions, closed answer vocabulary, releasing answers, and attribution requirements are completely untouched.
    +
     - 2026-10-01 note (aw specs): AMENDED (plan entv1d, backlog qzxt1m): Run exit codes table exit 1 row amended to name the stranded class explicitly (unintegrated work whose integration was refused) and record its derivation from exit 0's requirement that every actionable item is verified, adhering to docs/cli-output-contract.md Section 3's three-state exit classification; row 4 conflict note left intact.
    ```
    Confirmation:
    - Direction is explicitly named in Section 5.1 ("nothing refuses or downgrades on it... while a comparison that only ever makes a gate more permissive is not such a refusal").
    - 2026-09-08 and 2026-09-20 ruling sentences preserved verbatim.
    - Conjunctive conditions, closed answer vocabulary, releasing answers, and attribution argument are completely untouched.
    - Workflow history line names plan `kcc71f` and the measurement it rests on (`_relative_revalidation_verdict`, verified in runner_shared and pinned in tests/test_suite_baseline_direction.py).
    - Quoted reconciliation clause (F-10): "Reconciles the 2026-09-23 note (plan n9na1c), which recorded the HONEST LIMIT paragraph as unchanged deliberately and verbatim: what that note protected - the maintainer's 2026-09-08/2026-09-20 ruling that no programmatic gate may refuse an outcome on the strength of a pre-work baseline - is preserved verbatim, while the paragraph's undirected wording ("nothing refuses on it") is clarified so it does not contradict shipped, reviewed, and correct permissive comparisons".
    - The existing 2026-09-23 note is unmodified.
    - No other `.spec.md` file was modified.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` carrying NO `- Readiness:` field, whose absence was deliberate: that
field is an output of `/plan-review` and writing it at authoring time would forge the attestation a gate
reads. That was the correct authoring state. The field is now PRESENT because `/plan-review` ran on
2026-09-30 and wrote it, which is the only way it may legitimately appear.

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
