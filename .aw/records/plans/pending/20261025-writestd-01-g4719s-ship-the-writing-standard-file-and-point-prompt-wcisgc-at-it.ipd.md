# IPD: Ship the writing standard file and point prompt wcisgc at it

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-01 to R-04 require one shipped writing standard for specs, backlog items, and plans. None exists. The maintainer's draft is a gitignored delivery copy (`tmp/20261025-technical-artifact-writing-requirements.md`), and the review-time proofreading prompt `wcisgc` lives under `.aw/records/`, which the installer does not ship (`engine.collect_source_members` walks only the workflows bundle).
- Scope: Create `.aw/system/workflows/standards/technical-artifact-writing.md` with the draft's requirements, the twelfth requirement on diagrams (R-04), the widened dash rule (MD-2), and a proofreading procedure section adopted from `wcisgc` (R-03). Turn `wcisgc` into a pointer to that section. Add a test that the file installs. EXCLUDES every reference to the standard from other surfaces (Orders 02, 04, 05, 06) and the dash advisory (Order 03).
- Scope-Paths: .aw/system/workflows/standards/technical-artifact-writing.md, .aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md, tests/test_writing_standard_install.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
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
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the writing standard exist in exactly one shipped file, so every later Order and every target repository can point to it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the standard

- [ ] E-01 Create `.aw/system/workflows/standards/technical-artifact-writing.md`. Copy, from the maintainer draft quoted in full in backlog item `qph7c5`'s source (`tmp/20261025-technical-artifact-writing-requirements.md`; if that file is absent, stop and ask the maintainer for it), the sections "Purpose and scope" and "Language and writing requirements" (requirements 1 to 11 and the concision paragraph) and the last paragraph of "How to use the standard" (automated checks do not establish clarity). Change requirement 11's last sentence to "Do not use em dashes or en dashes." (spec `ecmw83` MD-2). Do not copy the sections "Recommended repository location", "Required agent instruction", or the standalone-chat prompt; they are adoption instructions, which Orders 02 and 06 carry out.
  - Depends on: none
  - Expected outcome: the file exists with requirements 1 to 11 and the concision paragraph.
  - Execution state: pending

- [ ] E-02 Add requirement 12, "Draw diagrams where they help understanding", with the five clauses (a) to (e) of spec `ecmw83` R-04 in that order, and one short Mermaid example each of an `erDiagram` and a `flowchart` inside fenced blocks.
  - Depends on: E-01
  - Expected outcome: requirement 12 exists with clauses (a) to (e) and two fenced examples.
  - Execution state: pending

- [ ] E-03 Add a section "Proofreading procedure" carrying the substance of `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md` sections 1 to 7 (purpose and evidence, language, completeness and logic including its artifact table, meaning and authority including the must/should/may rule, references, unresolved issues, verify and deliver). Keep its scope rule but restate it in terms of this standard's scope. Remove the duplicates where `wcisgc` repeats a numbered requirement; point to the requirement number instead.
  - Depends on: E-02
  - Expected outcome: the section exists and covers all seven `wcisgc` headings.
  - Execution state: pending

- [ ] E-04 Replace the body of `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md` below its metadata comment with a short pointer: the prompt's title, one sentence saying the procedure now lives in the "Proofreading procedure" section of `.aw/system/workflows/standards/technical-artifact-writing.md`, and the instruction to read and apply that section. Keep the metadata comment and the file name, because pending plan `3bwrfx` E-03 names this path.
  - Depends on: E-03
  - Expected outcome: `wcisgc` is a pointer of fewer than 15 lines and still at the same path.
  - Execution state: pending

### Task group 2: install test and changelog

- [ ] E-05 Create `tests/test_writing_standard_install.py` (marker `core`). It runs `engine.install_into_repo` (or the `aw install` CLI) into a temporary git repository and asserts that `.aw/system/workflows/standards/technical-artifact-writing.md` exists there with the same bytes as the source file. Add a CHANGELOG entry under the unreleased heading.
  - Depends on: E-01
  - Expected outcome: the test passes and fails if the file is removed from the source tree.
  - Execution state: pending

- [ ] E-06 Run the routine gate and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shipped resources live under `.aw/system/workflows/`; `engine.collect_source_members` installs every file there except `SOURCE_EXCLUDED_NAMES`. A new subdirectory `standards/` is installed with no code change.
- The manifest table in `.aw/system/workflows/index.md` lists commands only; a reference file needs no row (precedent: `assess/references/prose-style.md`).
- Tests exercise behavior (GUIDING_PRINCIPLES P16): the install test runs the installer and compares bytes.

## Findings

- The draft names `docs/standards/`, which does not ship (`pyproject.toml` force-includes only `.aw/system`). Spec `ecmw83` R-01 therefore moves the path under `.aw/system/workflows/standards/`.
- `wcisgc` is cited by approved spec `k3yx72` and by pending plan `3bwrfx` E-03 by path. Keeping the file as a pointer keeps both valid.

## Proposed changes (ordered, validatable)

1. Write the standard (E-01 to E-03).
2. Reduce `wcisgc` to a pointer (E-04).
3. Prove installation (E-05) and commit (E-06).

## Deferred / out of scope (with reason)

- Pointing other surfaces at the standard: Orders 02, 04, 05, 06.
  - Carrier: 8fvkmp

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_writing_standard_install.py` and the routine gate (V-05, V-06).

## Spec / documentation sync

No spec text changes. Spec `ecmw83` already specifies this file.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n '^[0-9]*\. \*\*' .aw/system/workflows/standards/technical-artifact-writing.md` showing items 1 to 11, and `grep -c $'\u2014\|\u2013' .aw/system/workflows/standards/technical-artifact-writing.md` printing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the requirement 12 text from `.aw/system/workflows/standards/technical-artifact-writing.md`, and paste the two examples rendered unchanged by `python3 -c` reading the fenced blocks (or the raw lines).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -n '^##\|^###' .aw/system/workflows/standards/technical-artifact-writing.md` showing the procedure section and its seven subsections.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `wc -l` of the prompt file and its full text.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writing_standard_install.py` with every test PASSED, then the same run after temporarily renaming the source file showing FAILED, then the restored PASSED run, and `git diff --stat CHANGELOG.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit g4719s -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
