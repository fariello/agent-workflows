# IPD: Ship the writing standard file and point prompt wcisgc at it

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-01 to R-04 require one shipped writing standard for specs, backlog items, and plans. None existed at authoring. Maintainer commit `0cbfcc706` (2026-11-02) has since shipped one at a different path, `.aw/system/workflows/technical-writing/technical-writing.md`, with a different scope and dash rule, so this plan awaits a replan (OQ-02). The maintainer's draft exists only as a gitignored delivery copy (`tmp/20261025-technical-artifact-writing-requirements.md`, 78 lines and 11 numbered requirements per research `7fe5zd`); no tracked artifact quotes it (OQ-01), and the review-time proofreading prompt `wcisgc` lives under `.aw/records/`, which the installer does not ship (`engine.collect_source_members` walks only the workflows bundle).
- Scope: Create `.aw/system/workflows/standards/technical-artifact-writing.md` with the draft's requirements, the twelfth requirement on diagrams (R-04), the widened dash rule (MD-2), and a proofreading procedure section adopted from `wcisgc` (R-03). Turn `wcisgc` into a pointer to that section. Add a test that the file installs. EXCLUDES every reference to the standard from other surfaces (Orders 02, 04, 05, 06) and the dash advisory (Order 03).
- Scope-Paths: .aw/system/workflows/standards/technical-artifact-writing.md, .aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md, tests/test_writing_standard_install.py, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
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
- 2026-11-05 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REJECT - NEEDS REPLAN; round 3: PR-009 REPLAN (commit 0cbfcc706 shipped the standard at technical-writing/technical-writing.md, no dash rule; OQ-02 blocking); PR-001 still OPEN (OQ-01 blocking)
- 2026-11-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; round 2: round 1 (parked commit 9b2d88cfd) re-verified and carried forward; PR-001 still OPEN (OQ-01 blocking); PR-008 FIXED
- 2026-11-02 reviewed (aw set): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001 open (OQ-01 blocking)
- 2026-11-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 OPEN (escalated OQ-01, blocking); PR-002..PR-007 FIXED; review record .aw/records/reviews/20261025-writestd-01-g4719s-ship-the-writing-standard-file-and-point-prompt-wcisgc-at-it.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the writing standard exist in exactly one shipped file, so every later Order and every target repository can point to it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

REPLAN PENDING (review round 3, finding PR-009): E-01 to E-05 were written before commit `0cbfcc706` shipped the standard at `.aw/system/workflows/technical-writing/technical-writing.md`. Do not execute them as written. They would create a second standard file and reverse a maintainer dash ruling. Rewrite them after the maintainer answers OQ-02.

### Task group 1: the standard

- [ ] E-01 Create `.aw/system/workflows/standards/technical-artifact-writing.md` (spec `ecmw83` R-01, `ecmw83` R-02). Copy, from the tracked copy of the maintainer draft that OQ-01 names (until OQ-01 is answered the only copy is the gitignored `tmp/20261025-technical-artifact-writing-requirements.md`, which an isolated runner worktree does not contain; if no copy is readable, stop this item, report `AW_MISSING_INPUT:<path>`, and do not reconstruct the wording from memory or from the spec), the sections "Purpose and scope" and "Language and writing requirements" (requirements 1 to 11 and the concision paragraph) and the last paragraph of "How to use the standard" (automated checks do not establish clarity). Change requirement 11's last sentence to "Do not use em dashes or en dashes." (maintainer decision MD-2 of spec `ecmw83`). Replace any em or en dash elsewhere in the copied text with other punctuation without changing meaning. Do not copy the sections "Recommended repository location", "Required agent instruction", or the standalone-chat prompt; they are adoption instructions, which Orders 02 and 06 carry out.
  - Depends on: none
  - Expected outcome: the file exists with requirements 1 to 11 in the draft's wording (except requirement 11's last sentence), the concision paragraph, and the automated-checks paragraph.
  - Execution state: pending

- [ ] E-02 Add requirement 12, "Draw diagrams where they help understanding", with the five clauses (a) to (e) of spec `ecmw83` R-04 in that order, and one short Mermaid example each of an `erDiagram` and a `flowchart` inside fenced blocks.
  - Depends on: E-01
  - Expected outcome: requirement 12 exists with clauses (a) to (e) and two fenced examples.
  - Execution state: pending

- [ ] E-03 Add a section "Proofreading procedure" (spec `ecmw83` R-03) carrying the substance of `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md` sections 1 to 7 (purpose and evidence, language, completeness and logic including its artifact table, meaning and authority including the must/should/may rule, references, unresolved issues, verify and deliver). Keep its scope rule but restate it in terms of this standard's scope. Remove the duplicates where `wcisgc` repeats a numbered requirement; point to the requirement number instead. Use one `###` subsection per `wcisgc` heading 1 to 7. Reword the one em dash in `wcisgc` section 6 ("from sources[em dash]not guesses" in the examples paragraph) without changing meaning.
  - Depends on: E-02
  - Expected outcome: the section exists with seven subsections, one per `wcisgc` heading, and the file still contains no em or en dash.
  - Execution state: pending

- [ ] E-04 (spec `ecmw83` R-03) Replace the body of `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md` below its metadata comment with a short pointer: the prompt's title, one sentence saying the procedure now lives in the "Proofreading procedure" section of `.aw/system/workflows/standards/technical-artifact-writing.md`, and the instruction to read and apply that section. Keep the metadata comment as the first line (`check_engine` reads the `aw-prompt:` comment there) and the file name, because spec `k3yx72` and the shipped step file `.aw/system/workflows/plan-review/steps/p-proofread.md` (written by executed plan `3bwrfx` E-03) name this path.
  - Depends on: E-03
  - Expected outcome: `wcisgc` is a pointer of fewer than 15 lines and still at the same path.
  - Execution state: pending

### Task group 2: install test and changelog

- [ ] E-05 Create `tests/test_writing_standard_install.py` (marker `core`; spec `ecmw83` R-01). It runs `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)` once into a repository made by `tests.support.init_repo` in a temporary directory (the pattern of `tests/test_agy_skill_install.py`) and asserts that `.aw/system/workflows/standards/technical-artifact-writing.md` exists there with the same bytes as the source file. Add a CHANGELOG entry under the topmost pending release heading (`## 2.0.0 (pending)` at authoring; re-read at execution), with no em or en dash.
  - Depends on: E-01
  - Expected outcome: the test passes and fails if the file is removed from the source tree.
  - Execution state: pending

- [ ] E-06 Run the routine gate, run `aw sanitize --agent` (the new file carries text from an untracked draft into the shipped package), and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the bare suite passes, the sanitizer reports no diagnostic located in a Scope-Paths file, and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shipped resources live under `.aw/system/workflows/`; `engine.collect_source_members` installs every file there except `SOURCE_EXCLUDED_NAMES`. A new subdirectory `standards/` is installed with no code change.
- The manifest table in `.aw/system/workflows/index.md` lists commands only; a reference file needs no row (precedent: `assess/references/prose-style.md`; a top-level non-command directory already exists: `templates/`). Measured at review: installing a copy of the source bundle with an added `standards/technical-artifact-writing.md` writes that file into the target byte-identical.
- `.aw/system/managed-sections.json` (this repository's own ownership manifest) is not edited by hand; executed plan `3bwrfx` added shipped step files without touching it.
- Tests exercise behavior (GUIDING_PRINCIPLES P16): the install test runs the installer and compares bytes.

## Findings

- The draft names `docs/standards/`, which does not ship (`pyproject.toml` force-includes only `.aw/system`). Spec `ecmw83` R-01 therefore moves the path under `.aw/system/workflows/standards/`.
- `wcisgc` is cited by path by approved spec `k3yx72`, by executed plan `3bwrfx` E-03, and by the shipped `.aw/system/workflows/plan-review/steps/p-proofread.md`. Keeping the file as a pointer keeps all three valid; Order 06 (`e4n4p3` E-04) later repoints `p-proofread.md` at the standard.
- `wcisgc` section 6 contains one em dash; the standard must contain none (spec `ecmw83` AC-02), so E-03 rewords it.
- The draft is the only source of the wording that spec `ecmw83` R-02 requires to be preserved, and it is untracked (OQ-01).
- Review round 3: maintainer commit `0cbfcc706` shipped `.aw/system/workflows/technical-writing/technical-writing.md` with requirements 1 to 11 and the concision and automated-checks paragraphs. It widened the scope to all technical text. Its "How it combines with other rules" item 4 says "This standard adds no dash rule of its own", and the commit message records "Its no-em-dash rule was dropped in favor of the existing execution-contract split (maintainer ruling)". The commit also added an install test (`tests/test_technical_writing_delivery.py::test_install_delivers_the_standard_and_the_agents_rule`) and the `AGENTS.md` pointer. The shipped file has no requirement 12 on diagrams and no proofreading procedure section. Spec `ecmw83` was not amended: R-01 still names `standards/technical-artifact-writing.md`, and R-02 and MD-2 still require the widened dash sentence. This plan therefore contradicts the shipped state and its own Goal ("exactly one shipped file") (PR-009, OQ-02).

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

`tests/test_writing_standard_install.py` (spec `ecmw83` AC-01, V-05), the content checks of V-01 to V-04 (spec `ecmw83` AC-02), the routine gate, and the sanitizer (V-06).

## Spec / documentation sync

No spec text changes. Spec `ecmw83` already specifies this file.

## Open questions

### OQ-01: Where is the tracked copy of the maintainer's draft that E-01 copies from?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Carrier: qph7c5
- Resolution or deferral rationale: OPEN. Facts: spec `ecmw83` R-02 requires requirements 1 to 11 "wording preserved", so E-01 must copy the draft verbatim. The only copy is `tmp/20261025-technical-artifact-writing-requirements.md`, which `.gitignore` excludes (`tmp/`). No tracked artifact quotes it: backlog `qph7c5` and spec `ecmw83` paraphrase it, and research `7fe5zd` only describes it (78 lines, 11 requirements). A runner executes this plan in an isolated worktree that has no `tmp/` and whose lane inputs carry only the plan and the runbook (`lane_containment._INPUT_CLASSES`), so an unattended run cannot read the draft. Bringing maintainer text into tracked history is the maintainer's act. Recommended answer: before approval, the maintainer commits the draft verbatim as a tracked record (for example a reference research record via `aw research new`, or an appendix to spec `ecmw83`) and edits E-01 to cite that path. Alternative: run this plan attended in the main checkout where `tmp/` exists. Recommendation strength: strong. Review round 3 note: if OQ-02 is answered by keeping the shipped file, the shipped file already holds requirements 1 to 11, and this question becomes moot.

### OQ-02: How should this plan and spec `ecmw83` change now that commit `0cbfcc706` shipped the standard at another path with no dash rule?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-009
- Carrier: qph7c5
- Resolution or deferral rationale: OPEN. Facts: commit `0cbfcc706` shipped `.aw/system/workflows/technical-writing/technical-writing.md`. It has requirements 1 to 11, the concision paragraph, and the automated-checks paragraph. It covers all technical text, not only specs, backlog items, and plans. It states "This standard adds no dash rule of its own", and the commit message calls dropping the dash rule a maintainer ruling. It has no diagram requirement (spec `ecmw83` R-04) and no proofreading procedure section (R-03). Spec `ecmw83` (`to-review`) still requires the path `standards/technical-artifact-writing.md` (R-01) and the sentence "Do not use em dashes or en dashes." (R-02, MD-2). All ten `writestd` plans cite the old path. As written, E-01 would create a second standard and reverse the dash ruling. Who decides: the maintainer, because this changes a spec contract and a recorded maintainer ruling. Recommended answer: keep the shipped path and its dash ruling. Amend spec `ecmw83` R-01, R-02, MD-2, and AC-01 to match the shipped file. Re-scope this plan to add only requirement 12 (diagrams) and the proofreading procedure section to the shipped file, reduce `wcisgc` to a pointer, and drop E-05 (the shipped test already covers installation). Reconsider Order 03 (`k2x0yl`, dash advisory) and the dash parts of Order 02 (`gzhw9c`). Recommendation strength: strong. Alternative: retire Set `writestd` and file a smaller follow-up for diagrams and the proofreading procedure.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: (spec `ecmw83` AC-02) paste the line that opens each of requirements 1 to 11 in `.aw/system/workflows/standards/technical-artifact-writing.md` (state the grep pattern used, matching the draft's numbering form), paste requirement 11's last sentence reading "Do not use em dashes or en dashes.", paste `diff` of requirements 1 to 10 against the tracked draft copy named by OQ-01 showing no wording change, and `grep -c $'\u2014\|\u2013' .aw/system/workflows/standards/technical-artifact-writing.md` printing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-02) paste the requirement 12 text, showing clauses (a) to (e) in order, from `.aw/system/workflows/standards/technical-artifact-writing.md`, and paste the two examples rendered unchanged by `python3 -c` reading the fenced blocks (or the raw lines).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (spec `ecmw83` AC-02) paste `grep -n '^##\|^###' .aw/system/workflows/standards/technical-artifact-writing.md` showing the procedure section and its seven subsections, and the `grep -c` dash count of V-01 re-run after E-03 printing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (spec `ecmw83` AC-02) paste `wc -l` of the prompt file (fewer than 15) and its full text, showing the `aw-prompt:` metadata comment unchanged on line 1 and the standard's path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: (spec `ecmw83` AC-01) paste `python3 -m pytest -o addopts="" -v tests/test_writing_standard_install.py` with every test PASSED, then the same run after temporarily renaming the source file showing FAILED, then the restored PASSED run, and `git diff --stat CHANGELOG.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the summary line of bare `python3 -m pytest`, the `aw sanitize --agent` result record with no diagnostic located in a Scope-Paths file, and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved (it is `to-review` at review time; this plan implements its requirements, and the orchestrator `8fvkmp` gate carries the same condition), and only once blocking OQ-01 and OQ-02 are resolved and the E-items are rewritten to match the answer to OQ-02. This plan creates the standard, so while writing it follow the draft it copies. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit g4719s -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize g4719s` itself.
