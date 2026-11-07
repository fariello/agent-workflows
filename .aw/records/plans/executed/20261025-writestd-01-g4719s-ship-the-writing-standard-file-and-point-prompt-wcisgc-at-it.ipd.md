# IPD: Ship the writing standard file and point prompt wcisgc at it

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-01 to R-04 require one shipped writing standard. Maintainer commit `0cbfcc706` (2026-11-02) shipped it at `.aw/system/workflows/technical-writing/technical-writing.md` with requirements 1 to 11, no dash rule (maintainer ruling), an install test, and the `AGENTS.md` pointer. The shipped file lacks the diagram requirement (R-04) and the proofreading procedure section (R-03), and prompt `wcisgc` still holds the procedure under `.aw/records/`, which the installer does not ship. Spec `ecmw83` still names the old path and the widened dash rule. The maintainer answered OQ-02 on 2026-11-05: keep the shipped file, amend the spec, and re-scope this plan.
- Scope: Amend spec `ecmw83` R-01, R-02, MD-2, AC-01, AC-02, and its entity-table row to match the shipped file. Add requirement 12 (diagrams) and a proofreading procedure section to the shipped file. Reduce `wcisgc` to a pointer. Add a CHANGELOG line. EXCLUDES a new install test (the shipped `tests/test_technical_writing_delivery.py` covers installation), every other surface that references the standard (Orders 02, 04, 05, 06), the dash advisory (Order 03), and the spec's dash-dependent rows R-05 and R-07 and non-goals N1 and N2, which Orders 02 and 03 must be re-reviewed against.
- Scope-Paths: .aw/system/workflows/technical-writing/technical-writing.md, .aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md, .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g4719s

## Workflow history
- 2026-11-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: g4719s verified (set writestd, attempt 1).
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-05 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; round 4: maintainer answered OQ-02 (keep shipped file, amend spec, re-scope) and OQ-01 (moot); plan re-scoped; PR-001, PR-009 FIXED; PR-010 FIXED
- 2026-11-05 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REJECT - NEEDS REPLAN; round 3: PR-009 REPLAN (commit 0cbfcc706 shipped the standard at technical-writing/technical-writing.md, no dash rule; OQ-02 blocking); PR-001 still OPEN (OQ-01 blocking)
- 2026-11-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; round 2: round 1 (parked commit 9b2d88cfd) re-verified and carried forward; PR-001 still OPEN (OQ-01 blocking); PR-008 FIXED
- 2026-11-02 reviewed (aw set): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001 open (OQ-01 blocking)
- 2026-11-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 OPEN (escalated OQ-01, blocking); PR-002..PR-007 FIXED; review record .aw/records/reviews/20261025-writestd-01-g4719s-ship-the-writing-standard-file-and-point-prompt-wcisgc-at-it.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Complete the writing standard that commit `0cbfcc706` shipped, so that `.aw/system/workflows/technical-writing/technical-writing.md` stays the one source for the writing requirements, the diagram requirement, and the proofreading procedure. Bring spec `ecmw83` into agreement with that file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: spec amendment

- [x] E-01 Amend `.aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md` (spec `ecmw83` R-01, `ecmw83` R-02; OQ-02 answer). Make these edits and no others: (1) R-01: the path becomes `.aw/system/workflows/technical-writing/technical-writing.md`. (2) R-02: the standard must contain its scope statement, the eleven numbered language requirements, the concision paragraph, and the statement that automated checks do not establish clarity, as shipped by commit `0cbfcc706`; delete "wording preserved except where R-04 and MD-2 change it" and the sentence requiring "Do not use em dashes or en dashes.". (3) MD-2: keep the original text and append "Superseded 2026-11-05: the shipped standard adds no dash rule of its own and defers to the `AGENTS.md` execution contract (maintainer ruling recorded in commit `0cbfcc706`; confirmed in plan `g4719s` OQ-02)." (4) AC-01: the path becomes the shipped path, and the criterion names `tests/test_technical_writing_delivery.py`. (5) AC-02: delete "and no em or en dash outside code". (6) The Section 4 entity row "Standard": the location becomes the shipped path. Then run `aw specs note <spec path> --message "R-01, R-02, MD-2, AC-01, AC-02 amended to the standard shipped by 0cbfcc706 (plan g4719s, OQ-02 answer)"`. Do not change the spec's `- Status:`.
  - Depends on: none
  - Expected outcome: the six spec locations name the shipped path and carry no widened dash requirement; the spec has one new history line and the same status.
  - Execution state: performed

### Task group 2: the standard

- [x] E-02 In `.aw/system/workflows/technical-writing/technical-writing.md`, add requirement 12, "Draw diagrams where they help understanding", after requirement 11 and before the concision paragraph. It states the five clauses (a) to (e) of spec `ecmw83` R-04 in that order and gives one short Mermaid `erDiagram` example and one short `flowchart` example, each in a fenced block. Change "all eleven requirements" (section "Checking your work", item 1) and "all eleven numbered requirements" (the attachment instruction) to "twelve".
  - Depends on: none
  - Expected outcome: requirement 12 exists with clauses (a) to (e) and two fenced examples, and the file contains no "eleven".
  - Execution state: performed

- [x] E-03 (spec `ecmw83` R-03) In the same file, add a section "## Proofreading procedure" before "## Using the standard outside this repository". It carries the substance of `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md` sections 1 to 7, one `###` subsection per heading: establish purpose and evidence; correct language precisely; check completeness and logic, with its artifact table; preserve meaning and decision authority, with its situation table and the must/should/may rule; check references and consistency; make unresolved issues visible; verify and deliver. Where a `wcisgc` bullet repeats a numbered requirement, cite the requirement number instead of repeating it. Do not import the `wcisgc` scope rule that excludes user-facing prose: this standard's own "Scope" section governs. Do not copy the `wcisgc` example paragraph in section 6 (it quotes project-specific phrases).
  - Depends on: E-02
  - Expected outcome: the section exists with seven `###` subsections, one per `wcisgc` heading.
  - Execution state: performed

- [x] E-04 (spec `ecmw83` R-03) Replace the body of the `wcisgc` prompt below its first-line `aw-prompt:` metadata comment with a pointer of fewer than 15 lines: the title, one sentence saying the procedure now lives in the "Proofreading procedure" section of `.aw/system/workflows/technical-writing/technical-writing.md`, and the instruction to read and apply that section together with the standard's numbered requirements. Keep the metadata comment and the file name, because spec `k3yx72` and the shipped `.aw/system/workflows/plan-review/steps/p-proofread.md` name this path.
  - Depends on: E-03
  - Expected outcome: `wcisgc` is a pointer of fewer than 15 lines at the same path, with line 1 unchanged.
  - Execution state: performed

### Task group 3: changelog and gate

- [x] E-05 Add one line under the topmost pending release heading of `CHANGELOG.md` (`## 2.0.0 (pending)` at review; re-read at execution), next to the existing "technical writing standard" entry: the standard now includes a diagram requirement and a proofreading procedure. Use no em or en dash (CHANGELOG is user-facing).
  - Depends on: E-02, E-03
  - Expected outcome: one added CHANGELOG line.
  - Execution state: performed

- [x] E-06 Run `python3 -m pytest -o addopts="" -v tests/test_technical_writing_delivery.py`, the bare routine gate `python3 -m pytest`, `aw specs check`, and `aw sanitize --agent`, then commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the delivery test and the routine gate pass, `aw specs check` reports no error for `ecmw83`, the sanitizer reports no diagnostic in a Scope-Paths file, and the commit holds only Scope-Paths files.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Shipped resources live under `.aw/system/workflows/`; `engine.collect_source_members` installs every file there except `SOURCE_EXCLUDED_NAMES`. The shipped standard is already installed and tested (`tests/test_technical_writing_delivery.py::test_install_delivers_the_standard_and_the_agents_rule`, which compares installed and source bytes, so it covers the edited file with no change).
- The `AGENTS.md` pointer (`engine.agents_pointer_prose`, `agent_workflows/engine.py:1501`) says "every numbered requirement", so adding requirement 12 needs no managed-block change.
- Tests exercise behavior (GUIDING_PRINCIPLES P16). A test asserting that the standard contains requirement 12 would pin document text, so the content is verified by the V-items instead.
- A plan may amend a spec and must list it in `- Scope-Paths:` (`AGENTS.md`, "A PLAN MAY AMEND A SPEC").

## Findings

- Commit `0cbfcc706` shipped `.aw/system/workflows/technical-writing/technical-writing.md` with requirements 1 to 11, the concision and automated-checks paragraphs, a scope covering all technical text, and "This standard adds no dash rule of its own". It has no diagram requirement and no proofreading procedure section.
- Spec `ecmw83` (`to-review`) still named `standards/technical-artifact-writing.md` (R-01, AC-01, Section 4) and required the widened dash sentence (R-02, MD-2, AC-02). The maintainer chose to amend the spec to the shipped file (OQ-02).
- Spec rows R-05 (dash clause), R-07 (dash advisory), and non-goals N1 and N2 (scope limited to three artifact types) also conflict with the shipped file. They belong to Orders 02 and 03 and to the scope decision, not to this plan (Deferred).
- `wcisgc` is cited by path by approved spec `k3yx72`, executed plan `3bwrfx` E-03, and `plan-review/steps/p-proofread.md`. Keeping the file as a pointer keeps all three valid. Order 06 (`e4n4p3` E-04) later repoints `p-proofread.md`.
- `wcisgc` excludes user-facing prose from its scope, but the shipped standard includes documentation, READMEs, and the changelog. E-03 therefore does not import that exclusion.

## Proposed changes (ordered, validatable)

1. Amend spec `ecmw83` to the shipped file (E-01).
2. Add requirement 12 and the proofreading procedure to the shipped file (E-02, E-03).
3. Reduce `wcisgc` to a pointer (E-04).
4. Add a CHANGELOG line, run the gate, and commit (E-05, E-06).

## Deferred / out of scope (with reason)

- Pointing other surfaces at the standard: Orders 02, 04, 05, 06.
  - Carrier: 8fvkmp
- Spec `ecmw83` R-05 dash clause, R-07, N1, N2, and the plans that implement them (Orders 02 and 03; every child also cites the old path `standards/technical-artifact-writing.md`): they must be re-reviewed against the amended MD-2 and the shipped path before they run. Changing them here would decide their scope without their review.
  - Carrier: 8fvkmp

## Scope check

- Over-scope: none.
- Under-scope: none. Installation is covered by the shipped delivery test.

## Required tests / validation

`tests/test_technical_writing_delivery.py` (spec `ecmw83` AC-01), the content checks of V-02 to V-04 (spec `ecmw83` AC-02), `aw specs check`, the routine gate, and the sanitizer (V-06).

## Spec / documentation sync

This plan amends spec `ecmw83` (E-01), listed in `- Scope-Paths:`. Why: the maintainer ruled on 2026-11-05 (OQ-02) that the standard shipped by `0cbfcc706` and its dash ruling stand, so the spec must describe the shipped path and drop the widened dash rule, or every later Order is reviewed against a contract the code contradicts. `docs/technical-artifact-writing.md` does not restate the requirements and needs no change.

## Open questions

### OQ-01: Where is the tracked copy of the maintainer's draft that E-01 copies from?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Carrier: qph7c5
- Resolution or deferral rationale: Maintainer answer, 2026-11-05 (terminal channel): "Moot under OQ-02 recommended answer". The shipped file already holds requirements 1 to 11, so no draft copy is needed and the plan no longer copies from `tmp/`.

### OQ-02: How should this plan and spec `ecmw83` change now that commit `0cbfcc706` shipped the standard at another path with no dash rule?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-009
- Carrier: qph7c5
- Resolution or deferral rationale: Maintainer answer, 2026-11-05 (terminal channel): "Keep shipped file; amend spec; re-scope g4719s (recommended)". Applied: the plan now amends spec `ecmw83` R-01, R-02, MD-2, AC-01, AC-02 (E-01), adds requirement 12 and the proofreading procedure to the shipped file (E-02, E-03), reduces `wcisgc` to a pointer (E-04), and drops the duplicate install test. Reconsidering Orders 02 and 03 is recorded under Deferred with carrier `8fvkmp`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md` showing only the six edits and one history line; paste `grep -c 'standards/technical-artifact-writing' <spec>` printing 0 and `grep -n -- '- Status:' <spec>` showing `to-review`.
  - Observed evidence:
    ```diff
    $ git diff HEAD~1 .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    diff --git a/.aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md b/.aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    index c0c669351..41ba86de4 100644
    --- a/.aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    +++ b/.aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    @@ -12,6 +12,8 @@
     - Constrained-by: `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md` (`k3yx72`, `approved`). Its proofreading step uses prompt `wcisgc`, and its non-goal N5 excludes "a writing standard applied while drafting". This spec supplies that standard and amends N5 (Section 7, Order 06).

     ## Workflow history
    +
    +- 2026-11-07 note (aw specs): R-01, R-02, MD-2, AC-01, AC-02 amended to the standard shipped by 0cbfcc706 (plan g4719s, OQ-02 answer)
     - 2026-10-26 to-review (aw specs): authored review-ready from backlog qph7c5

     - 2026-10-26 created (aw specs): Ship one writing standard (including diagram rules) and apply it whenever a spec, backlog item, or plan is written, proofread, reviewed, or revised; sweep live artifacts once.
    @@ -67,7 +69,7 @@ The maintainer supplied a draft standard on 2026-10-25. Backlog item `qph7c5` re
     | ID | Decision |
     | --- | --- |
     | MD-1 | The standard ships to every managed repository. |
    -| MD-2 | The standard's dash rule applies to specs, plans, and backlog items. It covers em dashes and en dashes. This replaces the exemption in P13 and in the `AGENTS.md` execution contract for these three artifact types. |
    +| MD-2 | The standard's dash rule applies to specs, plans, and backlog items. It covers em dashes and en dashes. This replaces the exemption in P13 and in the `AGENTS.md` execution contract for these three artifact types. Superseded 2026-11-05: the shipped standard adds no dash rule of its own and defers to the `AGENTS.md` execution contract (maintainer ruling recorded in commit `0cbfcc706`; confirmed in plan `g4719s` OQ-02). |
     | MD-3 | The standard applies to new work, and a one-time sweep proofreads every live artifact. |
     | MD-4 | The sweep includes approved artifacts. They keep their status. The sweep skips any plan that a live run is executing or has queued. |
     | MD-5 | The sweep includes parked backlog items and parked specs. |
    @@ -95,7 +97,7 @@ erDiagram

     | Entity | Meaning | Location |
     | --- | --- | --- |
    -| Standard | The single authoritative writing standard. | `.aw/system/workflows/standards/technical-artifact-writing.md` (R-01) |
    +| Standard | The single authoritative writing standard. | `.aw/system/workflows/technical-writing/technical-writing.md` (R-01) |
     | Proofreading procedure | The review-time procedure, adopted from `wcisgc`. | A section of the standard (R-03) |
     | AGENTS block paragraph | The managed `AGENTS.md` paragraph that points to the standard. | `engine.agents_pointer_prose` (R-05) |
     | Workflow body | A shipped workflow that writes or reviews an artifact, for example `spec`, `spec-review`, `plan-review`. | `.aw/system/workflows/<name>/` (R-06) |
    @@ -149,8 +151,8 @@ This table is the canonical declaration of this spec's requirements.

     | ID | Requirement | Section |
     | --- | --- | --- |
    -| R-01 | The standard must exist at `.aw/system/workflows/standards/technical-artifact-writing.md`. `aw install` must copy it into a target repository at the same relative path. The filename must not carry a date. | 1, 4 |
    -| R-02 | The standard must contain the scope statement, the eleven numbered language requirements of the maintainer's draft (wording preserved except where R-04 and MD-2 change it), the concision paragraph, and the statement that automated checks do not establish clarity. Requirement 11 must say "Do not use em dashes or en dashes." | 3, 4 |
    +| R-01 | The standard must exist at `.aw/system/workflows/technical-writing/technical-writing.md`. `aw install` must copy it into a target repository at the same relative path. The filename must not carry a date. | 1, 4 |
    +| R-02 | The standard must contain its scope statement, the eleven numbered language requirements, the concision paragraph, and the statement that automated checks do not establish clarity, as shipped by commit `0cbfcc706`. | 3, 4 |
     | R-03 | The standard must contain a proofreading procedure section that carries the substance of prompt `wcisgc` sections 1 to 7. After this, `wcisgc` must be a pointer to that section, so one source holds the procedure. | 1, 4 |
     | R-04 | The standard must contain a twelfth numbered requirement on diagrams. It must say: (a) add a Mermaid `erDiagram` or class diagram when an artifact introduces or changes three or more related entities, records, files, or components; (b) add a Mermaid `flowchart` or `stateDiagram-v2` when an artifact describes a process of three or more steps with a branch, a loop, or a status lifecycle; (c) do not add a diagram for a single entity or a linear process of fewer than three steps; (d) the text is normative, and a diagram that disagrees with the text is a defect that the author corrects; (e) a diagram must name entities and steps with the same terms as the text. | 2.1 G3, 4, 5 |
     | R-05 | The `AGENTS.md` managed block must contain a "Technical artifact writing" paragraph with the substance of the draft's "Required agent instruction", pointing to the path in R-01. The execution contract's dash clause must state that the dash rule also applies to specs, plans, and backlog items. `GUIDING_PRINCIPLES.md` P13, `CONTRIBUTING.md`, `prose-style.md`, `verify-execution/intent-audit.md`, and `GEMINI.md` must state the same scope. | 3 MD-2 |
    @@ -165,8 +167,8 @@ This table is the canonical declaration of this spec's requirements.

     | ID | Criterion | Requirements |
     | --- | --- | --- |
    -| AC-01 | A test installs the toolkit into a temporary repository and finds `.aw/system/workflows/standards/technical-artifact-writing.md` with the same bytes as the source. | R-01 |
    -| AC-02 | The standard contains numbered requirements 1 to 12, a proofreading procedure section, and no em or en dash outside code. `wcisgc` points to the standard. | R-02 to R-04 |
    +| AC-01 | A test installs the toolkit into a temporary repository and finds `.aw/system/workflows/technical-writing/technical-writing.md` with the same bytes as the source (`tests/test_technical_writing_delivery.py`). | R-01 |
    +| AC-02 | The standard contains numbered requirements 1 to 12 and a proofreading procedure section. `wcisgc` points to the standard. | R-02 to R-04 |
     | AC-03 | `python3 -m tools.regen_agents_block --check` reports no drift, and the regenerated `AGENTS.md` contains the "Technical artifact writing" paragraph and the widened dash clause. | R-05 |
     | AC-04 | A plan created by `aw ipd scaffold`, a spec created by `aw specs new`, and a backlog item created by `aw backlog new` each name the standard's path. Each still passes its own lint or check. | R-06 |
     | AC-05 | A test lints a plan, a spec, and a backlog item that each contain an em dash and an en dash in prose and in a fenced block. It observes one `info` advisory per prose dash, none for the fenced dashes, and an unchanged exit status. | R-07 |
    ```
    ```sh
    $ grep -c 'standards/technical-artifact-writing' .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    0
    $ grep -n -- '- Status:' .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    4:- Status: to-review
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-02) paste the requirement 12 text with clauses (a) to (e) in order and both fenced examples from `.aw/system/workflows/technical-writing/technical-writing.md`, and `grep -c eleven` on that file printing 0.
  - Observed evidence:
    ```markdown
    12. **Draw diagrams where they help understanding.**
        (a) Add a Mermaid `erDiagram` or class diagram when an artifact introduces or changes three or more related entities, records, files, or components.
        (b) Add a Mermaid `flowchart` or `stateDiagram-v2` when an artifact describes a process of three or more steps with a branch, a loop, or a status lifecycle.
        (c) Do not add a diagram for a single entity or a linear process of fewer than three steps.
        (d) The text is normative, and a diagram that disagrees with the text is a defect that the author corrects.
        (e) A diagram must name entities and steps with the same terms as the text.

        Example entity-relationship diagram:

        ```mermaid
        erDiagram
            SPEC ||--o{ PLAN : governs
            PLAN ||--o{ TASK : contains
        ```

        Example flowchart:

        ```mermaid
        flowchart TD
            A[Draft] --> B{Reviewed?}
            B -->|Yes| C[Approved]
            B -->|No| A
        ```
    ```
    ```sh
    $ grep -c eleven .aw/system/workflows/technical-writing/technical-writing.md
    0
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (spec `ecmw83` AC-02) paste `grep -n '^##\|^###' .aw/system/workflows/technical-writing/technical-writing.md` showing "## Proofreading procedure" and its seven subsections.
  - Observed evidence:
    ```
    $ grep -n '^##\|^###' .aw/system/workflows/technical-writing/technical-writing.md
    5:## Scope
    17:## How it combines with other rules
    25:## Requirements
    66:## Checking your work
    74:## Proofreading procedure
    78:### Establish purpose and evidence
    84:### Correct language precisely
    94:### Check completeness and logic
    122:### Preserve meaning and decision authority
    137:### Check references and consistency
    144:### Make unresolved issues visible
    156:### Verify and deliver
    170:## Using the standard outside this repository
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (spec `ecmw83` AC-02) paste `wc -l` of the `wcisgc` prompt file (fewer than 15) and its full text, showing line 1 unchanged and the shipped standard's path.
  - Observed evidence:
    ```
    $ wc -l .aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md
    6 .aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md

    $ cat .aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md
    <!-- aw-prompt: Kind: run-once | Id: wcisgc | Set: revsteps | Status: reusable | Created: 2026-10-17 | Author: opencode (pt3-claude-opus-5.5) . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
    # Proofread Technical Artifacts

    The technical artifact proofreading procedure now lives in the "Proofreading procedure" section of `.aw/system/workflows/technical-writing/technical-writing.md`.

    Read and apply that section together with the standard's numbered requirements.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff CHANGELOG.md` showing one added line under the pending heading.
  - Observed evidence:
    ```diff
    $ git diff HEAD~1 CHANGELOG.md
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 454f49d6d..61217c313 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -103,6 +103,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Fixed: bare /askme no longer searches the repository or asks other authors' open questions when no conversational question is pending. It now limits candidate records to those edited in the current conversation, and explains how to point /askme at a subject when both conversational and session sources are empty.
     - Fixed: recorded answers in open questions now preserve the original question text, record only the reasons you gave rather than adopting an option's argument, and no longer repeat unchecked factual premises from project records.
     - Added: a technical writing standard for all technical text (backlog items, specs, plans, research, prompts, reviews, walkthroughs, documentation, commit messages, code comments, and reports). `aw install` now installs it at `.aw/system/workflows/technical-writing/technical-writing.md`, the managed AGENTS.md block tells agents to read and follow it, and the spec, spec-review, plan-review, and research-prompt workflows apply it where the writing happens (see `docs/technical-artifact-writing.md`).
    +- Changed: the technical writing standard at `.aw/system/workflows/technical-writing/technical-writing.md` now includes a diagram requirement and a proofreading procedure.
     - Fixed: plain-text requests to use /askme (such as "use /askme" or "ask that again") are now recognized as commands rather than answers, including when submitted as custom answers in an interactive question tool. The workflow rewrites the most recent question asked even if askme was already applied in the session, and supersedes any earlier instruction for terse wording.
     - Added: every commit and merge created by `aw` now keeps the user as author and records `AW Agent (<model>) <local+aw@domain>` as committer (or `local+tag-aw@domain` when already tagged), stamps `AW-Runner` (`aw oc run`, `aw agy run`, or `aw commit`) alongside `AW-Run` and `AW-Item` when known, exports the agent committer identity and `AW_RUNNER` into runner agent turns, and preserves commit signing by supplying `user.signingkey` from the author identity when `commit.gpgsign` is enabled with no explicit key (see `docs/commit-identity.md`).
     - Fixed: aw rename and aw group now also rewrite citations that name a record by its filename without the type suffix, and skip with a warning when another record shares that name.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: (spec `ecmw83` AC-01) paste the `tests/test_technical_writing_delivery.py` run with every test PASSED, the summary line of bare `python3 -m pytest`, the `aw specs check` result for `ecmw83`, the `aw sanitize --agent` result record, and the `aw commit` output listing the committed paths.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_technical_writing_delivery.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=104385694
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/g4719s
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 2 items

    tests/test_technical_writing_delivery.py::TechnicalWritingDeliveryTests::test_install_delivers_the_standard_and_the_agents_rule PASSED [ 50%]
    tests/test_technical_writing_delivery.py::TechnicalWritingDeliveryTests::test_pointer_prose_names_the_installed_standard_for_both_layouts PASSED [100%]
    ============================== 2 passed in 3.02s ===============================

    Bare python3 -m pytest summary line:
    1860 passed, 11 warnings in 59.26s

    $ aw specs check
    aw specs check: all specs conform. 49 specs checked.

    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6254,"findings":0,"evidence":["leak-scan"],"next":null}

    $ aw commit g4719s -- .aw/system/workflows/technical-writing/technical-writing.md .aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md CHANGELOG.md
    aw commit: committed 4 path(s): e0f9c80dde521116b2d5982ff973f1d86612190d
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved (it is `to-review` at review time; this plan implements its requirements, and the orchestrator `8fvkmp` gate carries the same condition), and with every open question resolved (OQ-01 and OQ-02 were answered by the maintainer on 2026-11-05). While editing, follow the shipped standard itself. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit g4719s -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize g4719s` itself.
