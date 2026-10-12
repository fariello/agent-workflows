# IPD: Bound the six sibling releases line writers' strip to the metadata region

- Date: 2026-10-12
- Kind: child
- Concern: Six metadata line writers in `agent_workflows/releases.py` (`set_priority_line`, `set_work_kind_line`, `set_from_backlog_line`, `set_from_spec_line`, `set_item_dependencies_line`, `set_graduated_to_line`) strip their field with a `(?m)` pattern applied to the WHOLE text before inserting the new line, so setting the field on a record that QUOTES that field's bullet in its body silently deletes the body line. Executed plan `b92m14` E-07 fixed the identical defect in `set_blocks_release_line` by bounding the strip to `selectors.metadata_region` and deferred these six to carrier backlog `7afjyu`. Re-measured at authoring (HEAD `d795acb85`): records with a line matching each strip pattern after their metadata region are Priority 11, Work-Kind 11, Item-Dependencies 5, Graduated-To 5, From-Backlog 0, From-Spec 0. Driven in-process: `set_item_dependencies_line(text, "none")` on the approved spec `25kzda` removes the body line `- Item-Dependencies: executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9` (1754 -> 1753 lines), and `set_work_kind_line(text, "bug")` on `.aw/records/backlog/README.md` removes the documentation line `- Work-Kind: bug | feature | chore | security | followup`.
- Scope: IN: add one private module helper in `releases` that runs a line writer's whole strip-and-insert on the metadata region only and reattaches the untouched remainder; route `set_blocks_release_line` and the six sibling writers through it, so BOTH the strip and the insertion anchor search are bounded (F-06); author outcome tests driving each writer on fixtures; one CHANGELOG entry. OUT (reasons under Deferred): the anchor ORDER and fallbacks (unchanged; only their search extent is bounded), the field grammars and regexes themselves (unchanged, including `Graduated-To`'s multi-valued value), `research_cmd._set_priority_line` (already fence-bounded), and every caller in `status_set`.
- Scope-Paths: agent_workflows/releases.py, tests/test_releases_sibling_line_writers_bounding.py, CHANGELOG.md
- Item-Dependencies: executed:b92m14
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 7afjyu
- Blocks-Release: next
- Set: brgate
- Order: 2
- Highest E allocated: 09
- Author: opencode
- Id: nrdrv6

## Workflow history
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog `7afjyu`; exposure re-measured at HEAD `d795acb85`.

## Goal

Make every metadata line writer in `agent_workflows/releases.py` strip only inside the record's metadata region, so that setting Priority, Work-Kind, From-Backlog, From-Spec, Item-Dependencies or Graduated-To can never delete a body line, following the pattern `b92m14` E-07 shipped for `set_blocks_release_line`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: shared bounded strip

- [ ] E-01 In `agent_workflows/releases.py`, add a private helper `_in_metadata_region(text: str, edit: Callable[[str], str]) -> str` placed immediately above `set_blocks_release_line`. Body: `region = _sel.metadata_region(text)`, `return edit(region) + text[len(region):]`. Each writer keeps its existing strip/anchor/insert code in a private inner function (or local closure) that operates on the text it is given, and the public writer returns `_in_metadata_region(text, <that function with value bound>)`. So BOTH the strip and the anchor search see only the region: bounding only the strip leaves the anchor search able to insert the new line INTO THE BODY of a real record (F-06). Docstring states that bounding is what stops a QUOTED field bullet in a record's body being deleted or used as an insertion anchor, that a YAML-fenced record's region is its leading fence (so body bullets of research docs are equally safe), that a region with no anchor yields the documented 'leave unchanged' fallback, and cites `b92m14` E-07 and `7afjyu`. Then convert `set_blocks_release_line` to the same shape, removing its inline region/remainder lines. `set_blocks_release_line`'s existing tests must pass unchanged; its anchor search is also bounded by this change, which is the intended correction of the same F-06 hazard.
  - Depends on: none
  - Expected outcome: one helper exists; `set_blocks_release_line` uses it for both strip and insertion; the existing `tests/test_blocks_release_reader_bounding.py` and `tests/test_releases_line_writers.py` still pass unchanged.
  - Execution state: pending

### Task group 2: convert the six sibling writers

- [ ] E-02 In `set_priority_line`, route the whole body (strip `_PRIORITY_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes. Leave the regex, anchor order, insertion and `-`/`None` clearing semantics unchanged; only their extent is bounded. Append one docstring sentence: "Bounded to metadata_region so body lines are neither deleted nor used as an insertion anchor (7afjyu)."
  - Depends on: E-01
  - Expected outcome: `set_priority_line` no longer removes a body `- Priority:` line; all other behavior unchanged.
  - Execution state: pending
- [ ] E-03 In `set_work_kind_line`, route the whole body (strip `_WORK_KIND_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence as E-02. The pattern stays full-line anchored on `- Work-Kind:` so it still never touches `- Gate-Kind:` or `- Kind:`.
  - Depends on: E-01
  - Expected outcome: `set_work_kind_line` no longer removes a body `- Work-Kind:` line.
  - Execution state: pending
- [ ] E-04 In `set_from_backlog_line`, route the whole body (strip `_FROM_BACKLOG_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Exposure today is 0 records; this is converted so no sibling writer keeps the unbounded shape for a new call site to copy.
  - Depends on: E-01
  - Expected outcome: `set_from_backlog_line` no longer removes a body `- From-Backlog:` line.
  - Execution state: pending
- [ ] E-05 In `set_from_spec_line`, route the whole body (strip `_FROM_SPEC_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Exposure today is 0 records; converted for the same reason as E-04.
  - Depends on: E-01
  - Expected outcome: `set_from_spec_line` no longer removes a body `- From-Spec:` line.
  - Execution state: pending
- [ ] E-06 In `set_item_dependencies_line`, route the whole body (strip `_ITEM_DEPENDENCIES_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Keep its distinct anchor order (after `- Scope-Paths:`, else before `- Status:`, else after `- Id:`) untouched, per spec `25kzda` 2.7. This writer is the one F-06 measured: on spec `25kzda`, whose region has no `- Scope-Paths:` but whose body does, a strip-only bound inserts a SECOND `- Item-Dependencies: none` line in the body; bounded whole, it inserts before the in-region `- Status:`.
  - Depends on: E-01
  - Expected outcome: `set_item_dependencies_line` no longer removes or inserts next to a body line; on spec `25kzda` the body is byte-identical and the new line lands inside the metadata region.
  - Execution state: pending
- [ ] E-07 In `set_graduated_to_line`, route the whole body (strip `_GRADUATED_TO_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Do NOT change `_GRADUATED_TO_LINE_RE` or `_ITEM_GRADUATED_TO_RE`: the strip pattern is already whole-value (`[^\n]*`), so a multi-valued `a, b` line is stripped whole, and the comment above `_ITEM_GRADUATED_TO_RE` forbids adopting a sibling's single-token pattern.
  - Depends on: E-01
  - Expected outcome: `set_graduated_to_line` no longer removes a body `- Graduated-To:` line, and still replaces a multi-valued front-matter line with exactly one line.
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-08 Author `tests/test_releases_sibling_line_writers_bounding.py` driving OUTCOMES only (no `inspect`, `ast`, regex over production source, or symbol censuses; AGENTS.md and GUIDING_PRINCIPLES P16). For EACH of the six writers, parameterized over `(writer, field, value)`, on a fixture text with front-matter bullets (`- Id:`, `- Status:`, `- Scope-Paths:`, `- Set:`), a front-matter line for the field, and a `## Description` body that quotes the field's bullet: (a) setting a value replaces the front-matter line and leaves the body after `## Description` byte-identical; (b) applying the writer twice yields identical text (idempotence); (c) `-` and `None` remove the FRONT-MATTER line only and the body quote survives; (d) on a fixture with NO front-matter line for the field, exactly one line is added and the body is byte-identical; (e) a CONTROL asserting the front-matter line IS replaced (exactly one occurrence of the new value in the region), so no assertion can pass by a writer that strips nothing; (e2) ANCHOR-IN-BODY: a fixture whose region carries `- Id:` but NOT the writer's preferred anchor (`- Status:`, or `- Scope-Paths:` for `set_item_dependencies_line`) while the body quotes that anchor bullet: the new line lands inside `selectors.metadata_region` of the output (or, with no in-region anchor at all, the text is returned unchanged) and the body is byte-identical. Add (f) for `set_graduated_to_line`: a front-matter `- Graduated-To: aaa, bbb` replaced by `ccc` leaves exactly one front-matter `Graduated-To` line, while a body `- Graduated-To: aaa, bbb` survives. Add (g) a YAML-fenced fixture (leading `---` fence then body bullets) asserting a body bullet survives each writer. Add (h) one CLI-level test driving `aw backlog set open <id6> --work-kind feature --no-commit --dir <root>` (POSITIONAL status form: the flag-less `aw backlog set <id6> --work-kind ...` exits 2 with 'at least one target selector ... is required'; and `feature`, not `bug`, so the bug-gating release warning path is not exercised; measured at review) via `tests.support.run_cli` on a fixture backlog item with front-matter `- Work-Kind: chore` whose `## Description` body quotes `- Work-Kind: chore`, asserting exit 0, the front matter carries `- Work-Kind: feature`, and the body quote line is still present in the written file (at review, on the base code, that body line was deleted).
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the new test file passes; each case fails against the pre-change writers (demonstrated in V-08).
  - Execution state: pending
- [ ] E-09 Add a CHANGELOG.md entry under the `## 2.0.0 (pending)` section, in plain prose with no em or en dashes, stating that setting a record's Priority, Work-Kind, From-Backlog, From-Spec, Item-Dependencies or Graduated-To no longer deletes a matching line quoted in the record's body.
  - Depends on: E-01
  - Expected outcome: one new CHANGELOG line under 2.0.0 (pending).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.metadata_region` is the repository's single declared boundary for a record's own metadata (bullet front matter: everything before the first `##`; YAML: the leading fence only; header exhaustion means the region continues). Shipped for identity by executed plan `76w6mq` and for `Blocks-Release` by executed plan `b92m14`.
- `releases` already imports `selectors` as `_sel` (added by `b92m14` E-05), and `selectors` imports none of `releases`/`status_set`/`backlog`, so no cycle is introduced.
- The six writers each share the shape "strip with a whole-text `(?m)` pattern, return on `-`/`None`, else insert after an anchor". Their callers are `status_set.apply_status_change` (the `fb`/`fs`/`idep`/`prio`/`work_kind`/`graduated_to` arms) and the `backlog_close_verdicts` loop in `status_set` (Priority, Work-Kind), plus `ipd_schema` referencing `releases.set_item_dependencies_line`.
- `research_cmd._set_priority_line` is a DIFFERENT, private function operating only inside the first `--- ... ---` block; it is already bounded.
- Tests must exercise behavior (P16). The suite runs BARE: `python3 -m pytest`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The defect reproduces on real tracked records for the two most-exposed shapes. | In-process at HEAD `d795acb85`: `releases.set_item_dependencies_line(text, "none")` on `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` produced a diff removing `- Item-Dependencies: executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9` (1754 -> 1753 lines). `releases.set_work_kind_line(text, "bug")` on `.aw/records/backlog/README.md` added `+- Work-Kind: bug` and removed `-- Work-Kind: bug \| feature \| chore \| security \| followup`. On the `rendrop` review record, `set_priority_line`, `set_work_kind_line` and `set_graduated_to_line` each altered the body (body-after-region no longer a substring of the output). |
| F-02 | Exposure has grown since the backlog item's 2026-10-02 measurement, confirming the item's "re-measure before acting". | Over `.aw/records/**/*.md`, records with a strip-pattern match after `metadata_region`: Priority 11 (was 7), Work-Kind 11 (7), Item-Dependencies 5 (4), Graduated-To 5 (3), From-Backlog 0 (0), From-Spec 0 (0). Body-only examples include `.aw/records/reviews/20260926-rendrop-01-2yqt0a-...review.md` and `.aw/records/plans/executed/20261004-gradcover-08-24qw39-...ipd.md`. |
| F-03 | The fix shape is proven: `set_blocks_release_line` already uses it and is covered. | `releases.set_blocks_release_line` computes `region = _sel.metadata_region(text)` and strips only `region`; `tests/test_blocks_release_reader_bounding.py::test_set_blocks_release_line_preserves_body` and `test_set_blocks_release_line_remove_front_matter_only` pin the outcome. |
| F-04 | `Graduated-To`'s multi-valued grammar needs no special handling for the STRIP, only for parsing. | `_GRADUATED_TO_LINE_RE` is `(?m)^- Graduated-To:[ \t]*[^\n]*$\n?`, already whole-line; the single-token hazard described above `_ITEM_GRADUATED_TO_RE` concerns the READER (`parse_graduated_to`), which this plan does not touch. |
| F-06 | Bounding only the STRIP is not enough: the anchor search still runs over the whole text, so a writer can INSERT its line into the body. Over tracked records whose region carries `- Id:`, the first `- Scope-Paths:` match lies in the body for 1 record (spec `25kzda`) and the first `- Status:` match lies in the body for 1 record (walkthrough `v0nmuv`). | Review probe at `cee68756c`: strip-only bounded `set_item_dependencies_line(t, "none")` on `25kzda` went 1754 -> 1755 lines, adding a second `- Item-Dependencies: none` at body line 530; `set_priority_line(t, "low")` on `v0nmuv` inserted at line 233 of a 18-line region. With the WHOLE writer applied to the region and the remainder reattached, `tests/test_blocks_release_reader_bounding.py`, `tests/test_releases_line_writers.py` and `tests/test_status_set.py` all passed (142 passed). |
| F-05 | 13 records have no `- Status:`/`- Id:` anchor in their metadata region but do have one in their body (all are READMEs, reviews, or research docs). For them an unbounded anchor search could insert into the body; after E-01 these records are returned unchanged (no in-region anchor). | In-process scan printing `anchor-outside-region 13`, e.g. `.aw/records/backlog/README.md`, `.aw/records/reviews/README.md`. |

## Proposed changes (ordered, validatable)

1. E-01 generalizes the bounding `b92m14` E-07 wrote inline into one private helper that applies a writer's whole edit to the region, and routes `set_blocks_release_line` through it.
2. E-02 through E-07 route each of the six sibling writers through the helper, one writer per item so each change is individually reviewable.
3. E-08 pins every writer's outcome on fixtures, with a control proving the front-matter line is still replaced and one CLI-level test.
4. E-09 records the user-visible fix in CHANGELOG.

## Deferred / out of scope (with reason)

- `research_cmd._set_priority_line` IS NOT CHANGED. It already edits only inside the first `--- ... ---` block.
  - Carrier-Declined: Already bounded; nothing is owed.
- CALLERS IN `status_set` ARE NOT CHANGED. They pass the full record text to the writers; bounding inside the writer fixes every caller at once.
  - Carrier-Declined: The fix lives in the callee; changing callers would duplicate it.
- NO SOURCE-INSPECTING GUARD against a future unbounded writer is added, because P16 forbids it. After this plan no writer in `releases` keeps the unbounded shape to be copied.
  - Carrier-Declined: No permitted mechanism exists.

## Scope check

- Over-scope: none. `agent_workflows/releases.py` is edited by E-01..E-07, `tests/test_releases_sibling_line_writers_bounding.py` by E-08, `CHANGELOG.md` by E-09.
- Under-scope: none. All six writers named by `7afjyu` are converted, with strip AND anchor search bounded (F-06); `status_set.py`, `ipd_schema.py` and `research_cmd.py` are deliberately untouched (Deferred).

## Required tests / validation

The new `tests/test_releases_sibling_line_writers_bounding.py` must pass, and must be shown to FAIL against the pre-change writers (so it is not vacuous). The existing `tests/test_releases_line_writers.py` and `tests/test_blocks_release_reader_bounding.py` must pass unchanged. The real-record reproductions from F-01 must show an empty body diff after the change. The BARE suite (`python3 -m pytest`) must show no new failures against a same-session baseline. Paste actual runner output for every claim.

## Spec / documentation sync

No `.spec.md` is amended. Spec `25kzda` 2.7 specifies WHERE `- Item-Dependencies:` lives in front matter, which this plan preserves; no spec describes the writers' strip or anchor extent. `CHANGELOG.md` gains one entry (E-09).

## Open questions

### OQ-01: Should the six conversions be split into six plans so each can be reverted independently?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: No. `b92m14`'s Deferred row worried about revert granularity when converting seven writers alongside a reader refactor. Here each conversion is a one-line change through a shared helper that is already proven by `set_blocks_release_line`, each sits in its own E-item, and the backlog item `7afjyu` is a single carrier. One plan with one commit keeps the change atomic and a single `git revert` restores the old behavior for all six.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `agent_workflows/releases.py` showing the new `_in_metadata_region` helper and `set_blocks_release_line` routed through it, plus the pasted runner output of `python3 -m pytest -o addopts="" tests/test_blocks_release_reader_bounding.py tests/test_releases_line_writers.py tests/test_status_set.py` showing all pass.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste an in-process Python session showing `releases.set_priority_line(text, "low")` on `.aw/records/reviews/20260926-rendrop-01-2yqt0a-preserve-unrecognized-metadata-bullets-when-backlog-records.review.md` (read only, not rewritten) yields a body (text after `selectors.metadata_region`) byte-identical to the input's, where before the change it did not (F-01).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a unified diff of `releases.set_work_kind_line(text, "bug")` against `.aw/records/backlog/README.md` (read only) showing the body line `- Work-Kind: bug | feature | chore | security | followup` is NOT removed, beside F-01's pre-change diff that removed it.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the pytest output of the E-08 test cases for `set_from_backlog_line` (body-preserve, idempotence, `-`/`None` removal, control) passing.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the pytest output of the E-08 test cases for `set_from_spec_line` passing.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste a unified diff of `releases.set_item_dependencies_line(text, "none")` against the approved spec `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (read only) showing zero body lines removed or added, the new `- Item-Dependencies: none` line inside the metadata region, and the line count 1754 -> 1755 from that one front-matter insertion only, beside F-01's pre-change result (1754 -> 1753) and F-06's strip-only result (a second line in the body).
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste an in-process session showing `releases.set_graduated_to_line` on a text with front-matter `- Graduated-To: aaa, bbb` and the same line in the body, set to `ccc`, yields exactly one front-matter `Graduated-To` line (`ccc`) and the body line intact; and the same on the `rendrop` review record showing a byte-identical body.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_releases_sibling_line_writers_bounding.py` output passing after the change, AND output of the same file run against the pre-change `releases.py` (taken from a `git worktree` of the base commit, never `git stash`) showing the body-preservation and (e2) anchor-in-body cases FAIL, so the tests are not vacuous. Then paste the BARE `python3 -m pytest` summary line, with any failures compared to a same-session baseline on the base commit.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste the CHANGELOG.md diff showing the new entry under `## 2.0.0 (pending)` and the output of a search over the added line showing no em or en dash characters.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT AN APPROVER MOST NEEDS TO KNOW. This is the deferred remainder of executed plan `b92m14`: the bounding E-07 applied to `set_blocks_release_line`, now applied to the six sibling writers (and to the anchor search, F-06) through one shared helper. The defect is live and growing (F-02: Priority and Work-Kind exposure rose from 7 to 11 records since filing) and it reproduces on an approved spec and on the backlog README (F-01). Risk is low: only the extent the strip and the anchor search see changes; regexes, anchor order, insertion and clearing semantics are untouched (a review probe of this exact shape passed the existing writer and `status_set` tests, F-06), and the existing writer tests must pass unchanged.

EXECUTION CONTRACT. Commit only the three declared paths plus this plan, through `aw commit nrdrv6 -- <paths>`; never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`, and never push. This is a SHARED CHECKOUT: verify the staged set with `git diff --cached --name-only` before committing and unstage anything not yours with `git restore --staged <path>`. Paste ACTUAL runner output for every test claim. Run the suite BARE (`python3 -m pytest`) with no added flags. Scope fence: `- Scope-Paths:` is a declaration; an edit outside it is made and justified with `--scope-reason` at finalize, not a reason to stop. Open questions: OQ-01 resolved; none open. Begin with `aw ipd begin nrdrv6`. You MUST paste the actual runner output; never claim a result you did not run. Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the executor MUST NOT run it; only in a manual run, after every V-item passes with evidence and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize nrdrv6 ... --apply` (never a hand `git mv` to `executed/`); the backlog item `7afjyu` then closes via the From-Backlog handoff.
