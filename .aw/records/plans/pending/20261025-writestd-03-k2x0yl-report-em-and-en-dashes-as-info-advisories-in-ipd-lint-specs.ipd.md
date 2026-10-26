# IPD: Report em and en dashes as info advisories in ipd lint, specs check, and backlog check

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-07 requires a mechanical check that reports an em dash or en dash in the prose of a plan, spec, or backlog item, as an `info` advisory that never changes an exit status. `aw ipd lint` retired its dash rule `IPD-D701` (comment above `ipd_lint` "Fence-aware structural reader"), and `tests/test_ipd_lint.py` `StructuralRuleTests` pins that a dash plan lints clean. `specs.validate_spec` and `backlog.validate_item` have no prose check.
- Scope: Add one shared prose-dash scanner; emit it as advisory `IPD-C802` from `ipd_lint.lint_text` and as `info` rules `spec.prose-dash` and `backlog.prose-dash` from the spec and backlog validators (registered in `check_engine.RULE_REGISTRY`); amend the IPD linting spec's Section 10 item 17. EXCLUDES fixing dashes in existing artifacts (Orders 07 to 09) and any blocking severity.
- Scope-Paths: agent_workflows/prose_dash.py, agent_workflows/ipd_lint.py, agent_workflows/specs.py, agent_workflows/backlog.py, agent_workflows/check_engine.py, tests/test_prose_dash_advisory.py, tests/test_ipd_lint.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: k2x0yl

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Report every em or en dash in authored prose of a spec, backlog item, or plan as a non-blocking advisory, so authors and the sweep can find them.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scanner and emitters

- [ ] E-01 Create `agent_workflows/prose_dash.py` with `find_prose_dashes(text) -> list[tuple[int, int, str]]` returning (line, column, character) for each U+2014 or U+2013 outside fenced code blocks, indented code blocks, block quotes, inline code spans, and the leading `- Key: value` front-matter block. Reuse `ipd_lint._structural_lines` for fence and quote detection if it fits; otherwise implement the same rules and say why in the module docstring.
  - Depends on: none
  - Expected outcome: the function exists and returns positions only for prose dashes.
  - Execution state: pending

- [ ] E-02 In `ipd_lint`, add constant `C_PROSE_DASH = "IPD-C802"` (next free code in the C8xx family; do not reuse `IPD-D701`) and append one advisory per dash to `advisories` in `lint_text`, never to `diags`. Gate it on the same authoring-date idea as `IPD-C801`, with a new cutover constant set to the date this plan executes, so plans authored earlier stay silent unless the existing `citation_anchors`-style on-demand flag is passed; add that flag only if `IPD-C801`'s flag cannot be reused.
  - Depends on: E-01
  - Expected outcome: a post-cutover plan with a prose dash gets one `IPD-C802` advisory and stays conforming.
  - Execution state: pending

- [ ] E-03 In `specs.validate_spec` and `backlog.validate_item`, emit `Drift` records with rule `spec.prose-dash` and `backlog.prose-dash`; register both in `check_engine.RULE_REGISTRY` with severity `info`, `DET_DETERMINISTIC`. Apply the same authoring-date cutover, read from the artifact's `- Date:` or its filename date. Confirm `aw specs check` and `aw backlog check` still exit 0 when only these rules fire.
  - Depends on: E-01
  - Expected outcome: `aw specs check` and `aw backlog check` list the advisory and exit 0.
  - Execution state: pending

### Task group 2: tests and spec

- [ ] E-04 Create `tests/test_prose_dash_advisory.py` (marker `core`), table-driven: dashes in prose (reported), in a fenced block, indented block, block quote, inline code, and front matter (not reported), for each of the three artifact types, asserting the reported codes and an unchanged disposition or exit status. Update the `StructuralRuleTests` row "an IPD containing an em dash and an en dash" in `tests/test_ipd_lint.py`: it must still forbid every blocking code, and its explanation must say dashes are now an `info` advisory (`IPD-C802`) rather than ignored.
  - Depends on: E-02, E-03
  - Expected outcome: both test files pass.
  - Execution state: pending

- [ ] E-05 Amend `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 10 item 17: dashes in authored prose are reported as advisory `IPD-C802` (spec `ecmw83` R-07); `IPD-D701` stays retired. Record the amendment with `aw specs note`. Add a CHANGELOG entry.
  - Depends on: E-02
  - Expected outcome: the spec item names `IPD-C802` and the history carries the note.
  - Execution state: pending

- [ ] E-06 Run the routine gate and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Advisories go in `LintResult.advisories` and never change `disposition` (precedent `ipd_lint.check_citation_anchors`, `IPD-C801`).
- `info` is advisory on every surface; `warning` fails `aw check` (`docs/cli-output-contract.md` Section 3). So the new rules are `info`.
- Codes are never recycled (comment beside `C_CITATION_ANCHOR`).

## Findings

- `tests/test_ipd_lint.py` row "an IPD containing an em dash and an en dash" asserts no codes. It lists no forbidden codes and checks only blocking diagnostics, so an advisory may still pass it; E-04 verifies this and edits only its explanation if so.

## Proposed changes (ordered, validatable)

1. Scanner (E-01).
2. Emit from the three validators (E-02, E-03).
3. Tests and spec amendment (E-04, E-05).
4. Gate and commit (E-06).

## Deferred / out of scope (with reason)

- Promoting the advisory to a blocking severity: refused for the same reason as `IPD-C801` (a heuristic over prose; quoted text can contain dashes).
  - Carrier-Declined: deliberate design position in spec `ecmw83` R-07.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_prose_dash_advisory.py`, `tests/test_ipd_lint.py`, the bare suite.

## Spec / documentation sync

Amends spec `ipd-structure-and-linting` Section 10 item 17, declared in Scope-Paths, because that item states the dash rule is not checked.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the E-04 test run covering the scanner rows.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the E-04 test run covering the IPD rows and `aw ipd lint --agent` on a temporary plan showing `"outcome":"clean"` with an `IPD-C802` diagnostic.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both commands run against a temporary repository holding one dash-bearing spec and one dash-bearing backlog item, with their exit codes.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_prose_dash_advisory.py tests/test_ipd_lint.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff` of the spec file and the `aw specs note` output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit k2x0yl -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
