# IPD: Point the authoring and review workflow bodies at the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-06 requires every shipped workflow that writes, reviews, or revises a spec, backlog item, or plan to direct the agent to the writing standard, and R-04 adds its diagram requirement. Maintainer commit `0cbfcc706` shipped the standard at `.aw/system/workflows/technical-writing/technical-writing.md` and already added a pointer to `spec/spec.md`, `spec-review/spec-review.md`, `plan-review/plan-review.md`, `plan-review-long/plan-review-long.md`, and `research-prompt/research-prompt.md`. Still missing: `ipd-lifecycle/ipd-lifecycle.md`, `advise/personas/spec-editor.md`, the plan-review step files (`p-proofread.md` still applies prompt `wcisgc` with a fallback summary), and the `plan-review-long` rubric. No body mentions the diagram requirement (requirement 12, added by Order 01 `g4719s`), and two bodies say "all eleven" requirements, which becomes wrong once requirement 12 exists. Spec `k3yx72` non-goal N5 still limits proofreading to review time.
- Scope: Add the missing pointers; add the diagram check (requirement 12) to every authoring and review body; replace the requirement count in `spec.md` and `research-prompt.md` with count-free wording; point `plan-review/steps/p-proofread.md` at the standard's "Proofreading procedure" section; amend spec `k3yx72` N5 and its two `wcisgc` rows; add an install test that every pointer resolves. EXCLUDES the generators (Order 04), runner prompts (Order 05), the standard's own text (Order 01), and splitting or restructuring any workflow.
- Scope-Paths: .aw/system/workflows/spec/spec.md, .aw/system/workflows/spec-review/spec-review.md, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review/steps/p-proofread.md, .aw/system/workflows/plan-review/steps/_kernel.md, .aw/system/workflows/plan-review-long/plan-review-long.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md, .aw/system/workflows/advise/personas/spec-editor.md, .aw/system/workflows/research-prompt/research-prompt.md, .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md, tests/test_workflow_bodies_writing_standard.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s, executed:3bwrfx
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 6
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: e4n4p3

## Workflow history
- 2026-11-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: e4n4p3 verified (set writestd, attempt 1).
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-06 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 fixed
- 2026-11-05 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED; review record .aw/records/reviews/20261025-writestd-06-e4n4p3-point-the-authoring-and-review-workflow-bodies-at-the-writin.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every interactive and runner-driven authoring and review workflow apply the shipped writing standard, including its diagram requirement, so the standard governs writing, proofreading, review, and revision alike.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Reference form for every edit: write the standard's path RELATIVE to the edited file, as the shipped pointers already do: `../technical-writing/technical-writing.md` from a file directly under a workflow directory, `../../technical-writing/technical-writing.md` from a file one level deeper (`plan-review/steps/`, `advise/personas/`). A relative path resolves in both install layouts (`.aw/system/workflows/` and legacy `.agents/workflows/`); a hard-coded `.aw/system/...` path does not.

### Task group 1: authoring bodies

- [x] E-01 (spec `ecmw83` R-06, `ecmw83` R-04) In `spec/spec.md`, replace "check the complete draft against all eleven numbered requirements before you present it" with "check the complete draft against every numbered requirement, including requirement 12 (diagrams), before you present it", and add "Diagrams where requirement 12 of the writing standard applies (entities and relationships, flows and lifecycles)." as the last bullet of "## Spec structure". In `advise/personas/spec-editor.md`, add to "## Questioning style" one bullet: the persona asks whether the spec needs the entity or flow diagram that requirement 12 of `../../technical-writing/technical-writing.md` calls for, and whether each existing diagram agrees with the text. In `research-prompt/research-prompt.md`, replace "all eleven numbered requirements" with "every numbered requirement".
  - Depends on: none
  - Expected outcome: no workflow body contains "eleven"; `spec.md` and `spec-editor.md` mention requirement 12; `spec-editor.md` contains a resolving pointer.
  - Execution state: performed

- [x] E-02 (spec `ecmw83` R-06) In `ipd-lifecycle/ipd-lifecycle.md`, section "## Execute", add one paragraph after the first: when an agent writes or revises plan text during execution (for example a re-scope or a new open question), it follows `../technical-writing/technical-writing.md`; it never rewrites recorded evidence, results, or `## Workflow history` entries to improve their wording.
  - Depends on: none
  - Expected outcome: `ipd-lifecycle.md` contains a resolving pointer and the evidence carve-out.
  - Execution state: performed

### Task group 2: review bodies

- [x] E-03 (spec `ecmw83` R-06, `ecmw83` R-04) In `spec-review/spec-review.md`, extend the existing sentence that begins "Review the writing against the technical writing standard" to also require the diagram check of requirement 12. In "## Spec rubric", add one lettered subsection after the last existing one, "Writing and diagrams": the spec follows `../technical-writing/technical-writing.md`, including requirement 12; the reviewer fixes writing defects in place within its authority and records a finding where a fix would change meaning or where a required diagram is missing and cannot be drawn from the text alone.
  - Depends on: none
  - Expected outcome: the rubric subsection exists and names requirement 12.
  - Execution state: performed

- [x] E-04 (spec `ecmw83` R-06) In `plan-review/steps/p-proofread.md`, replace the first two paragraphs (the instruction to apply prompt `wcisgc` and its seven-heading fallback summary) with: apply the "Proofreading procedure" section of `../../technical-writing/technical-writing.md` and its numbered requirements, including requirement 12 (diagrams). Keep every later section unchanged ("Structural Preservation Constraints", "Code Citations", "Review Record Subsection"). In `plan-review/steps/_kernel.md`, add item 10 to the "Memory kernel" list: review the plan's writing against `../../technical-writing/technical-writing.md`, and preserve meaning, obligations, and recorded evidence. In `plan-review/plan-review.md`, extend the existing sentence that begins "Review the plan's writing against the technical writing standard" with "including requirement 12 (diagrams)".
  - Depends on: none
  - Expected outcome: `p-proofread.md` names the procedure section and no longer contains `wcisgc`; `_kernel.md` contains a resolving pointer.
  - Execution state: performed

- [x] E-05 (spec `ecmw83` R-06, `ecmw83` R-04) In `plan-review-long/02-review-and-revise.md`, add to the "## Required context" list the bullet "the technical writing standard (`../technical-writing/technical-writing.md`), including requirement 12 (diagrams);". In `plan-review-long/review-rubric.md`, add a final section "## I. Writing and diagrams" with the same check as E-03, worded for a plan. In `plan-review-long/plan-review-long.md`, extend kernel item 10 with "including requirement 12 (diagrams)".
  - Depends on: none
  - Expected outcome: all three `plan-review-long` files name the standard and requirement 12.
  - Execution state: performed

### Task group 3: spec amendment, test, and changelog

- [x] E-06 Amend `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`: (1) non-goal N5 keeps its text and gains "Amended 2026-11-05: spec `ecmw83` now specifies a writing standard applied while drafting; see `.aw/system/workflows/technical-writing/technical-writing.md`."; (2) the Section 1 "Proofreading instructions" row names the "Proofreading procedure" section of that file, with prompt `wcisgc` as a pointer to it; (3) the section-map row "(new) proofreading" names that section instead of prompt `wcisgc`. Then run `aw specs note .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md --message "N5 and the two proofreading rows amended to the shipped writing standard (plan e4n4p3, spec ecmw83)"`. Do not change the spec's status.
  - Depends on: E-04
  - Expected outcome: the three locations name the standard; the spec carries one new history line and stays `approved`.
  - Execution state: performed

- [x] E-07 (spec `ecmw83` R-06) Create `tests/test_workflow_bodies_writing_standard.py` (marker `core`). Follow the module-fixture pattern of `tests/test_plan_review_step_files.py`: install once with `run_cli("install", "-y", ...)` into an `init_repo` target. For each of the eleven installed workflow bodies in Scope-Paths, find every backticked reference ending in `technical-writing/technical-writing.md`, resolve it relative to that body's directory, and assert that at least one reference exists and that every one resolves to an existing file. Add one CHANGELOG line under the topmost pending heading, with no em or en dash.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the test passes, and it fails when a pointer is removed from a body or points at a missing path.
  - Execution state: performed

- [x] E-08 Run the routine gate and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Workflow bodies are the installed source; command shims point at body paths and do not change here.
- Executed plan `3bwrfx` split `plan-review.md` into `steps/*.md` (`.aw/records/plans/executed/20261024-revsteps-01-3bwrfx-...`), so the `executed:3bwrfx` edge is satisfied.
- Shipped pointers use the relative form (`.aw/system/workflows/spec/spec.md` "Write the spec to the technical writing standard"); the managed `AGENTS.md` pointer uses the layout's root (`engine.agents_pointer_prose`, `agent_workflows/engine.py:1501`).
- Tests exercise behavior (GUIDING_PRINCIPLES P16). E-07 asserts that every delivered pointer resolves in an installed repository, which is a link-integrity outcome, following `tests/test_technical_writing_delivery.py` (which asserts the installed `AGENTS.md` names the standard).

## Findings

- Commit `0cbfcc706` already added a standard pointer to `spec.md`, `spec-review.md`, `plan-review.md`, `plan-review-long.md`, and `research-prompt.md`. This plan adds only what is missing and does not duplicate those lines.
- `.aw/system/workflows/spec/spec.md` "all eleven numbered requirements before you present it" and `.aw/system/workflows/research-prompt/research-prompt.md` "check it against all eleven numbered requirements" fix a count. Order 01 (`g4719s` E-02) adds requirement 12 and fixes the count only inside the standard, so E-01 removes the count here.
- `p-proofread.md` applies `wcisgc` and carries a fallback summary because `.aw/records/` is not shipped. After Order 01 the procedure ships inside the standard, so E-04 removes the fallback.
- Spec `k3yx72` names `wcisgc` in two rows (Section 1 table, section map) and limits writing rules to review time (N5). E-06 amends all three.

## Proposed changes (ordered, validatable)

1. Authoring bodies (E-01, E-02).
2. Review bodies (E-03 to E-05).
3. Amend `k3yx72`, test, changelog (E-06, E-07).
4. Gate and commit (E-08).

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none. `research-prompt.md` is outside R-06's list but is added because its requirement count would become wrong (E-01).

## Required tests / validation

`tests/test_workflow_bodies_writing_standard.py`, `tests/test_plan_review_step_files.py`, `tests/test_technical_writing_delivery.py`, the bare suite.

## Spec / documentation sync

Amends approved spec `k3yx72` (N5 and its two `wcisgc` rows), declared in Scope-Paths, because that spec would otherwise still name `wcisgc` as the procedure and exclude drafting-time writing rules, contradicting spec `ecmw83` and the shipped standard.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff` of `spec/spec.md`, `advise/personas/spec-editor.md`, and `research-prompt/research-prompt.md`, and `grep -rn eleven .aw/system/workflows --include=*.md` printing no line outside `technical-writing/`.
  - Observed evidence:
    `git diff HEAD~1 -- .aw/system/workflows/spec/spec.md .aw/system/workflows/advise/personas/spec-editor.md .aw/system/workflows/research-prompt/research-prompt.md`:
    ```diff
    diff --git a/.aw/system/workflows/advise/personas/spec-editor.md b/.aw/system/workflows/advise/personas/spec-editor.md
    index 0f4a4a390..449156acc 100644
    --- a/.aw/system/workflows/advise/personas/spec-editor.md
    +++ b/.aw/system/workflows/advise/personas/spec-editor.md
    @@ -19,6 +19,9 @@ and conflicting or unstated requirements.
       This actor/role is never mentioned - what can they do?"
     - Separate need from solution. "Is that a requirement, or one way to satisfy it? What is
       the underlying need?"
    +- Ask whether the spec needs the entity or flow diagram that requirement 12 of
    +  `../../technical-writing/technical-writing.md` calls for, and whether each existing
    +  diagram agrees with the text.

     ## What "good" looks like from here

    diff --git a/.aw/system/workflows/research-prompt/research-prompt.md b/.aw/system/workflows/research-prompt/research-prompt.md
    index 28a4ed2ad..2bfb5b929 100644
    --- a/.aw/system/workflows/research-prompt/research-prompt.md
    +++ b/.aw/system/workflows/research-prompt/research-prompt.md
    @@ -27,7 +27,7 @@ Re-read before drafting and before the exit gate:
     2. **Leading HTML Comment Pipeline Metadata:** Pipeline metadata is a single leading HTML comment line (`<!-- aw-prompt: ... -->`), written by `aw prompts new`, not by hand. This comment is invisible when pasted into an LLM chat and preserves staging metadata without violating prompt purity.
     3. **Target Tracked Pending Lane:** `aw prompts new` writes to `.aw/records/prompts/pending/` with `Status: pending`. Never auto-stage or commit.
     4. **Leak Sanitizer Awareness:** Run `aw check-local-leaks` on the finished file before concluding.
    -5. **Technical writing standard:** Write the prompt to `../technical-writing/technical-writing.md` and check it against all eleven numbered requirements before concluding.
    +5. **Technical writing standard:** Write the prompt to `../technical-writing/technical-writing.md` and check it against every numbered requirement before concluding.

     ## Inputs

    diff --git a/.aw/system/workflows/spec/spec.md b/.aw/system/workflows/spec/spec.md
    index 888ff8fca..396d8928e 100644
    --- a/.aw/system/workflows/spec/spec.md
    +++ b/.aw/system/workflows/spec/spec.md
    @@ -9,7 +9,7 @@ produce the spec document with per-step confirmation. It writes a planning artif
     does not write code.

     Write the spec to the technical writing standard (`../technical-writing/technical-writing.md`): check the complete draft against
    -all eleven numbered requirements before you present it.
    +every numbered requirement, including requirement 12 (diagrams), before you present it.

     ## Division of labor with `/advise spec-editor`

    @@ -67,6 +67,7 @@ Name the file `YYYY-MM-DD-<slug>.md`. Confirm the location with the user before
     - **Constraints and dependencies:** what bounds the solution; what it relies on.
     - **Risks and open questions:** known unknowns, decisions still needed.
     - **Out-of-scope / future:** deliberately deferred ideas.
    +- Diagrams where requirement 12 of the writing standard applies (entities and relationships, flows and lifecycles).

     ## Honesty and guardrails
    ```
    `grep -rn eleven .aw/system/workflows --include=*.md`:
    ```
    .aw/system/workflows/askme/rationale.md:9:On 2026-09-08, an agent authored five plans containing eleven open questions, asked the maintainer none of them, and reported completion. In the same session, it referred to `run_engine.RunEngine`, `IPD-S404`, and bare id6 handles in a question addressed to a human who had never seen them. A rule an agent reads and still breaks needs an invocable entry point and a gate, not another copy of the prose.
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` showing the paragraph under "## Execute".
  - Observed evidence:
    `git diff HEAD~1 -- .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md`:
    ```diff
    diff --git a/.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md b/.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md
    index 6dd1d25c1..c6ab81b35 100644
    --- a/.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md
    +++ b/.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md
    @@ -78,6 +78,10 @@ evidence supports the expected outcome. Commit the plan's PRODUCT changes path-s
     (never `git add -A`/`-a`; never push). The terminal lifecycle transition is NOT one of these
     checklist items; it happens only at Checkpoint 2 below.

    +When an agent writes or revises plan text during execution (for example a re-scope or a new open
    +question), it follows `../technical-writing/technical-writing.md`; it never rewrites recorded evidence,
    +results, or `## Workflow history` entries to improve their wording.
    +
     ## Checkpoint 2: pre-transition gate

     When every `E-*` is `performed`+checked and every `V-*` is `pass`+checked with nonempty observed
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff .aw/system/workflows/spec-review/spec-review.md` showing the new rubric subsection.
  - Observed evidence:
    `git diff HEAD~1 -- .aw/system/workflows/spec-review/spec-review.md`:
    ```diff
    diff --git a/.aw/system/workflows/spec-review/spec-review.md b/.aw/system/workflows/spec-review/spec-review.md
    index b6690e886..09deed223 100644
    --- a/.aw/system/workflows/spec-review/spec-review.md
    +++ b/.aw/system/workflows/spec-review/spec-review.md
    @@ -6,7 +6,7 @@ improving that spec in place and advancing it to `reviewed` through the setter.
     Review specification documents only. Do not change code, tests, runtime configuration,
     infrastructure, or production data. Do not author plans. Reviewing a spec is not implementing it.

    -Review the writing against the technical writing standard (`../technical-writing/technical-writing.md`) as well as the substance, and
    +Review the writing against the technical writing standard (`../technical-writing/technical-writing.md`), including the diagram check of requirement 12, as well as the substance, and
     check that every wording fix preserves the spec's meaning and obligations.

     THIS IS THE SPEC-TIME SIBLING OF `plan-review`, and it is deliberately a SEPARATE package rather than
    @@ -385,6 +385,11 @@ a plan must answer. For each item, verify the spec addresses it or justifies `No
       is stated.
     - Any release gate (`Blocks-Release`) is present in the front matter rather than only in prose.

    +### H. Writing and diagrams
    +- The spec follows `../technical-writing/technical-writing.md`, including requirement 12.
    +- The reviewer fixes writing defects in place within its authority and records a finding where a fix
    +  would change meaning or where a required diagram is missing and cannot be drawn from the text alone.
    +
     ---
     ## Verdict
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff .aw/system/workflows/plan-review/`, and `grep -c wcisgc .aw/system/workflows/plan-review/steps/p-proofread.md` printing 0.
  - Observed evidence:
    `git diff HEAD~1 -- .aw/system/workflows/plan-review/`:
    ```diff
    diff --git a/.aw/system/workflows/plan-review/plan-review.md b/.aw/system/workflows/plan-review/plan-review.md
    index 21db50adb..469c5fa78 100644
    --- a/.aw/system/workflows/plan-review/plan-review.md
    +++ b/.aw/system/workflows/plan-review/plan-review.md
    @@ -1,7 +1,7 @@
     # Plan Review (pre-execution plan / IPD reviewer)
     Treat this file as the controlling instruction for reviewing a proposed plan
     before implementation, then improving that plan in place.
    -Review the plan's writing against the technical writing standard (`../technical-writing/technical-writing.md`), and check that
    +Review the plan's writing against the technical writing standard (`../technical-writing/technical-writing.md`), including requirement 12 (diagrams), and check that
     every wording fix preserves the plan's meaning, obligations, and recorded evidence.

     This portable single-file checklist is SERIAL BY DESIGN: it does not auto-fan-out into parallel audit
    diff --git a/.aw/system/workflows/plan-review/steps/_kernel.md b/.aw/system/workflows/plan-review/steps/_kernel.md
    index cca05d71c..63aff8deb 100644
    --- a/.aw/system/workflows/plan-review/steps/_kernel.md
    +++ b/.aw/system/workflows/plan-review/steps/_kernel.md
    @@ -30,6 +30,7 @@ Re-read this before each step and before the final report:
     7. Make at most two local commits. Never push.
     8. The reviewed/not-reviewed enumeration is the literal final output.
     9. A gate or interactive question MUST NOT assert or imply the verdict it precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is formed only from the reviewed work's evidence.
    +10. Review the plan's writing against `../../technical-writing/technical-writing.md`, and preserve meaning, obligations, and recorded evidence.

     ---
     ### 0.2 Discover controlling instructions
    diff --git a/.aw/system/workflows/plan-review/steps/p-proofread.md b/.aw/system/workflows/plan-review/steps/p-proofread.md
    index 360a9a8bb..feae47eff 100644
    --- a/.aw/system/workflows/plan-review/steps/p-proofread.md
    +++ b/.aw/system/workflows/plan-review/steps/p-proofread.md
    @@ -1,15 +1,6 @@
     # Check P: Proofread

    -Apply the technical artifact proofreading instructions in prompt `wcisgc` (`.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`) to the plan, by reference to that path rather than by copy.
    -
    -When that path is absent (such as in an installed target repository where `.aw/records/` is not shipped), apply the seven numbered headings of `wcisgc` as summarized here:
    -1. **Establish purpose and evidence:** Read all supplied artifacts before revising, identify their governing requirements, and examine relevant authoritative repository context without executing reviewed commands.
    -2. **Correct language precisely:** Use direct instructions, explicit actors and targets, consistent terms, and simple sentences, removing rhetorical bloat while preserving material detail and reasoning.
    -3. **Check completeness and logic:** Verify instructions and requirements against the artifact's purpose, ensuring actor, target, behavior, scope, inputs, outputs, conditions, dependencies, and observable acceptance criteria are defined.
    -4. **Distinguish required content from proposals:** Separate established requirements from proposals or optional ideas, resolving editorial ambiguities without altering policy, architecture, behavior, scope, or acceptance criteria.
    -5. **Check references and consistency:** Verify code and artifact references by path and symbol rather than line numbers, check coordination across concurrent work, and preserve headings and stable IDs.
    -6. **Make unresolved issues visible:** When evidence cannot establish meaning, preserve established content, add visible annotations separate from requirements, explain the ambiguity and needed decision, and identify affected work.
    -7. **Verify and deliver:** Re-read the revised scope to confirm no material meaning or constraint was changed unintentionally, delivering revised artifacts, a material-change summary, and an issue list.
    +Apply the "Proofreading procedure" section of `../../technical-writing/technical-writing.md` and its numbered requirements, including requirement 12 (diagrams).

     ## Structural Preservation Constraints (Section 6.1)
    ```
    `grep -c wcisgc .aw/system/workflows/plan-review/steps/p-proofread.md`:
    ```
    0
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff .aw/system/workflows/plan-review-long/`.
  - Observed evidence:
    `git diff HEAD~1 -- .aw/system/workflows/plan-review-long/`:
    ```diff
    diff --git a/.aw/system/workflows/plan-review-long/02-review-and-revise.md b/.aw/system/workflows/plan-review-long/02-review-and-revise.md
    index 4bea9632e..922769b9c 100755
    --- a/.aw/system/workflows/plan-review-long/02-review-and-revise.md
    +++ b/.aw/system/workflows/plan-review-long/02-review-and-revise.md
    @@ -13,6 +13,7 @@ Read `review-rubric.md` in full. Apply:
     - domain invariants;
     - all eight personas;
     - the mandatory security lens;
    +- the technical writing standard (`../technical-writing/technical-writing.md`), including requirement 12 (diagrams);
     - the rubric.

     ## 1. Record findings
    diff --git a/.aw/system/workflows/plan-review-long/plan-review-long.md b/.aw/system/workflows/plan-review-long/plan-review-long.md
    index de474ff06..417b7b17d 100755
    --- a/.aw/system/workflows/plan-review-long/plan-review-long.md
    +++ b/.aw/system/workflows/plan-review-long/plan-review-long.md
    @@ -20,7 +20,7 @@ These rules apply in every step:
     7. Never push or include unrelated files in a commit.
     8. The reviewed/not-reviewed enumeration is the final output.
     9. A gate or interactive question MUST NOT assert or imply the verdict it precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is formed only from the reviewed work's evidence.
    -10. Review the plan's writing against the technical writing standard (`../technical-writing/technical-writing.md`); every wording fix must preserve meaning, obligations, and recorded evidence.
    +10. Review the plan's writing against the technical writing standard (`../technical-writing/technical-writing.md`), including requirement 12 (diagrams); every wording fix must preserve meaning, obligations, and recorded evidence.

     Use `../release-review/fix-decision-policy.md` for the Fix Bar and
     `../release-review/00-run-protocol.md` for the eight personas. Security is a
    diff --git a/.aw/system/workflows/plan-review-long/review-rubric.md b/.aw/system/workflows/plan-review-long/review-rubric.md
    index 2edd6be74..588e9e4e2 100755
    --- a/.aw/system/workflows/plan-review-long/review-rubric.md
    +++ b/.aw/system/workflows/plan-review-long/review-rubric.md
    @@ -152,3 +152,10 @@ Check:
     - rollout, rollback, reconciliation, and recovery;
     - logs do not expose secrets or unnecessary sensitive data;
     - specs, docs, examples, schemas, and release notes remain synchronized.
    +
    +## I. Writing and diagrams
    +
    +Check:
    +
    +- the plan follows `../technical-writing/technical-writing.md`, including requirement 12;
    +- the reviewer fixes writing defects in place within its authority and records a finding where a fix would change meaning or where a required diagram is missing and cannot be drawn from the text alone.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `git diff` of the `k3yx72` spec, the `aw specs note` output, and `grep -n -- '- Status:' <spec>` showing `approved`.
  - Observed evidence:
    `git diff HEAD~1 -- .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md b/.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
    index 0a17c3c8c..3b110930a 100644
    --- a/.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
    +++ b/.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
    @@ -23,7 +23,7 @@
     | Review invocation | One runner review of one plan, from the first prompt to the verdict, including any re-review passes. |
     | Review record | The findings file under `.aw/records/reviews/` that the review writes. It has one `## Round <n>` section per review invocation. |
     | Review tier | `simple`, `standard`, or `complex`. The tier decides which review checks run and how many prompts the review uses (Section 5). |
    -| Proofreading instructions | Prompt `wcisgc`, "Proofread Technical Artifacts", at `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`. |
    +| Proofreading instructions | The "Proofreading procedure" section of `.aw/system/workflows/technical-writing/technical-writing.md`, with prompt `wcisgc` as a pointer to it. |
     | Recommendation strength | One of `very weak`, `weak`, `medium`, `strong`, `very strong`, attached to every recommendation (Section 7.3). |
     | Verdict outputs | The three things existing gates read to decide whether a review cleared a plan: the plan's `- Readiness:` field, its `- Status:` move from `to-review` to `reviewed`, and the one history entry that states a review verdict (`APPROVE`, `APPROVE WITH REVISIONS APPLIED`, `REVIEWED - OPEN QUESTIONS`, or `REJECT - NEEDS REPLAN`). |
     | Reviewed-contract hash | The value of `agent_workflows/ipd_lifecycle.py::frozen_region_digest`: a SHA-256 over the plan's `- Scope-Paths:` list and the action text of every `E-*` and `V-*` item. It does NOT cover checkbox marks, `Execution state`, evidence fields, open questions, prose sections, or `## Workflow history`. Two plan texts with the same hash ask the executor to do the same work in the same files. |
    @@ -75,7 +75,7 @@ Non-goals:
     - N4. The shorter backlog-to-execution pipeline for small changes. It is filed separately as backlog
       work (Section 15).
     - N5. A writing standard applied while drafting. The proofreading instructions apply at review time
    -  only.
    +  only. Amended 2026-11-05: spec `ecmw83` now specifies a writing standard applied while drafting; see `.aw/system/workflows/technical-writing/technical-writing.md`.

     ## 3. Maintainer decisions

    @@ -168,7 +168,7 @@ to exactly one place; nothing is dropped. Sizes are the current section sizes in
     | Severity and scope | 658 | `steps/_findings.md` |
     | Verdict and readiness, NO-GO re-evaluable, escalation return path | 5,253 | `steps/s7-finalize.md` (verdict) and `steps/s5-questions.md` (escalation) |
     | Required final report | 2,095 | `steps/s7-finalize.md`; in a runner review the report is the review record, not chat text |
    -| (new) proofreading | - | `steps/p-proofread.md`: prompt `wcisgc`, with open questions written to the review record (Section 6.1) and citations in the forms of Section 11 |
    +| (new) proofreading | - | `steps/p-proofread.md`: the "Proofreading procedure" section of `.aw/system/workflows/technical-writing/technical-writing.md`, with open questions written to the review record (Section 6.1) and citations in the forms of Section 11 |
     | (new) tier, quick risk, personas, decomposition, cross-plan, re-review | - | `steps/t-tier.md`, `steps/q-quick-risk.md`, `steps/r5-personas.md`, `steps/r6-decomposition.md`, `steps/r7-cross-plan.md`, `steps/s6-rereview.md` |

     The personas in `.aw/system/workflows/release-review/00-run-protocol.md` and the Fix Bar in
    @@ -874,6 +874,7 @@ five of MD-9.

     ## Workflow history

    +- 2026-11-07 note (aw specs): N5 and the two proofreading rows amended to the shipped writing standard (plan e4n4p3, spec ecmw83)
     - 2026-10-26 note (aw specs): MD-20 gate: OTHERWISE; maintainer decision via /askme: BUILD THE REST; complex default: single-12; report: .aw/records/research/20261017-revsteps-06-2m4i0o-review-pilot-results.findings.md
     - 2026-10-25 approved (aw set): status set to approved
     - 2026-10-24 approved (aw specs): Blocks release 2.0.0 (f33nrj, the planned release) per maintainer 2026-10-24
    ```
    `aw specs note` output:
    ```
    aw specs note: appended a history record to .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
    ```
    `grep -n -- '- Status:' .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`:
    ```
    4:- Status: approved
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_workflow_bodies_writing_standard.py tests/test_plan_review_step_files.py tests/test_technical_writing_delivery.py` with every test PASSED; then the run of the new test after temporarily deleting the pointer line from `ipd-lifecycle.md` showing FAILED, and the restored PASSED run; and `git diff --stat CHANGELOG.md`.
  - Observed evidence:
    Run of all three test files (every test PASSED):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=975013504
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/e4n4p3
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 7 items

    tests/test_plan_review_step_files.py::test_installed_plan_review_step_files_exist PASSED [ 14%]
    tests/test_plan_review_step_files.py::test_installed_askme_contains_five_level_recommendations PASSED [ 28%]
    tests/test_plan_review_step_files.py::test_installed_finalize_contains_verdicts PASSED [ 42%]
    tests/test_plan_review_step_files.py::test_installed_tier_and_rereview_markers PASSED [ 57%]
    tests/test_workflow_bodies_writing_standard.py::test_workflow_bodies_writing_standard_pointers PASSED [ 71%]
    tests/test_technical_writing_delivery.py::TechnicalWritingDeliveryTests::test_pointer_prose_names_the_installed_standard_for_both_layouts PASSED [ 85%]
    tests/test_technical_writing_delivery.py::TechnicalWritingDeliveryTests::test_install_delivers_the_standard_and_the_agents_rule PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    WARNING: 1 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
        2.83s  tests/test_technical_writing_delivery.py::TechnicalWritingDeliveryTests::test_install_delivers_the_standard_and_the_agents_rule
    ============================== 7 passed in 9.90s ===============================
    ```
    Negative test run with pointer deleted from `ipd-lifecycle.md` showing FAILED:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=1477880494
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/e4n4p3
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 1 item

    tests/test_workflow_bodies_writing_standard.py::test_workflow_bodies_writing_standard_pointers FAILED [100%]

    =================================== FAILURES ===================================
    ________________ test_workflow_bodies_writing_standard_pointers ________________

    installed_repo = PosixPath('/tmp/tmpovrvcm37/target')

        def test_workflow_bodies_writing_standard_pointers(installed_repo: Path) -> None:
            """For each of the eleven installed workflow bodies in Scope-Paths, find every backticked

            reference ending in technical-writing/technical-writing.md, resolve it relative to that
            body's directory, and assert that at least one reference exists and that every one resolves
            to an existing file.
            """
            assert len(WORKFLOW_BODIES) == 11, f"Expected 11 workflow bodies, got {len(WORKFLOW_BODIES)}"
            workflows_dir = installed_repo / ".aw" / "system" / "workflows"

            for rel_body in WORKFLOW_BODIES:
                body_file = workflows_dir / rel_body
                assert body_file.is_file(), f"Installed workflow body missing: {body_file}"

                content = body_file.read_text(encoding="utf-8")
                refs = re.findall(r"`([^`]*technical-writing/technical-writing\.md)`", content)
    >           assert (
                    len(refs) >= 1
                ), f"No backticked technical-writing/technical-writing.md reference found in {rel_body}"
    E           AssertionError: No backticked technical-writing/technical-writing.md reference found in ipd-lifecycle/ipd-lifecycle.md
    E           assert 0 >= 1
    E            +  where 0 = len([])

    tests/test_workflow_bodies_writing_standard.py:65: AssertionError
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    =========================== short test summary info ============================
    FAILED tests/test_workflow_bodies_writing_standard.py::test_workflow_bodies_writing_standard_pointers
    ============================== 1 failed in 4.08s ===============================
    ```
    Restored test run showing PASSED:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=1945435400
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/e4n4p3
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 1 item

    tests/test_workflow_bodies_writing_standard.py::test_workflow_bodies_writing_standard_pointers PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 1 passed in 3.84s ===============================
    ```
    `git diff --stat CHANGELOG.md`:
    ```
     CHANGELOG.md | 1 +
     1 file changed, 1 insertion(+)
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
    Summary line of bare `python3 -m pytest`:
    ```
    1861 passed, 11 warnings in 34.68s
    ```
    (and `aw suite` exit 0 summary: `1861 passed, 11 warnings in 38.22s`).
    `aw commit` output:
    ```
    aw commit: committed 14 path(s): d717b6016346e74d5233a6b887b96705a52d2d0f
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved, and only after Order 01 `g4719s` is `executed` (its edge enforces this; it adds requirement 12 and the "Proofreading procedure" section this plan points to). Before editing any spec or plan, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit e4n4p3 -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize e4n4p3` itself.
