# IPD: Bound the six sibling releases line writers' strip to the metadata region

- Date: 2026-10-12
- Kind: child
- Concern: Six metadata line writers in `agent_workflows/releases.py` (`set_priority_line`, `set_work_kind_line`, `set_from_backlog_line`, `set_from_spec_line`, `set_item_dependencies_line`, `set_graduated_to_line`) strip their field with a `(?m)` pattern applied to the WHOLE text before inserting the new line, so setting the field on a record that QUOTES that field's bullet in its body silently deletes the body line. Executed plan `b92m14` E-07 fixed the identical defect in `set_blocks_release_line` by bounding the strip to `selectors.metadata_region` and deferred these six to carrier backlog `7afjyu`. Re-measured at authoring (HEAD `d795acb85`): records with a line matching each strip pattern after their metadata region are Priority 11, Work-Kind 11, Item-Dependencies 5, Graduated-To 5, From-Backlog 0, From-Spec 0. Driven in-process: `set_item_dependencies_line(text, "none")` on the approved spec `25kzda` removes the body line `- Item-Dependencies: executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9` (1754 -> 1753 lines), and `set_work_kind_line(text, "bug")` on `.aw/records/backlog/README.md` removes the documentation line `- Work-Kind: bug | feature | chore | security | followup`.
- Scope: IN: add one private module helper in `releases` that runs a line writer's whole strip-and-insert on the metadata region only and reattaches the untouched remainder; route `set_blocks_release_line` and the six sibling writers through it, so BOTH the strip and the insertion anchor search are bounded (F-06); author outcome tests driving each writer on fixtures; one CHANGELOG entry. OUT (reasons under Deferred): the anchor ORDER and fallbacks (unchanged; only their search extent is bounded), the field grammars and regexes themselves (unchanged, including `Graduated-To`'s multi-valued value), `research_cmd._set_priority_line` (already fence-bounded), and every caller in `status_set`.
- Scope-Paths: agent_workflows/releases.py, tests/test_releases_sibling_line_writers_bounding.py, CHANGELOG.md
- Item-Dependencies: executed:b92m14
- Status: executed
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
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: nrdrv6 verified (set brgate, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog `7afjyu`; exposure re-measured at HEAD `d795acb85`.

## Goal

Make every metadata line writer in `agent_workflows/releases.py` strip only inside the record's metadata region, so that setting Priority, Work-Kind, From-Backlog, From-Spec, Item-Dependencies or Graduated-To can never delete a body line, following the pattern `b92m14` E-07 shipped for `set_blocks_release_line`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: shared bounded strip

- [x] E-01 In `agent_workflows/releases.py`, add a private helper `_in_metadata_region(text: str, edit: Callable[[str], str]) -> str` placed immediately above `set_blocks_release_line`. Body: `region = _sel.metadata_region(text)`, `return edit(region) + text[len(region):]`. Each writer keeps its existing strip/anchor/insert code in a private inner function (or local closure) that operates on the text it is given, and the public writer returns `_in_metadata_region(text, <that function with value bound>)`. So BOTH the strip and the anchor search see only the region: bounding only the strip leaves the anchor search able to insert the new line INTO THE BODY of a real record (F-06). Docstring states that bounding is what stops a QUOTED field bullet in a record's body being deleted or used as an insertion anchor, that a YAML-fenced record's region is its leading fence (so body bullets of research docs are equally safe), that a region with no anchor yields the documented 'leave unchanged' fallback, and cites `b92m14` E-07 and `7afjyu`. Then convert `set_blocks_release_line` to the same shape, removing its inline region/remainder lines. `set_blocks_release_line`'s existing tests must pass unchanged; its anchor search is also bounded by this change, which is the intended correction of the same F-06 hazard.
  - Depends on: none
  - Expected outcome: one helper exists; `set_blocks_release_line` uses it for both strip and insertion; the existing `tests/test_blocks_release_reader_bounding.py` and `tests/test_releases_line_writers.py` still pass unchanged.
  - Execution state: performed

### Task group 2: convert the six sibling writers

- [x] E-02 In `set_priority_line`, route the whole body (strip `_PRIORITY_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes. Leave the regex, anchor order, insertion and `-`/`None` clearing semantics unchanged; only their extent is bounded. Append one docstring sentence: "Bounded to metadata_region so body lines are neither deleted nor used as an insertion anchor (7afjyu)."
  - Depends on: E-01
  - Expected outcome: `set_priority_line` no longer removes a body `- Priority:` line; all other behavior unchanged.
  - Execution state: performed
- [x] E-03 In `set_work_kind_line`, route the whole body (strip `_WORK_KIND_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence as E-02. The pattern stays full-line anchored on `- Work-Kind:` so it still never touches `- Gate-Kind:` or `- Kind:`.
  - Depends on: E-01
  - Expected outcome: `set_work_kind_line` no longer removes a body `- Work-Kind:` line.
  - Execution state: performed
- [x] E-04 In `set_from_backlog_line`, route the whole body (strip `_FROM_BACKLOG_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Exposure today is 0 records; this is converted so no sibling writer keeps the unbounded shape for a new call site to copy.
  - Depends on: E-01
  - Expected outcome: `set_from_backlog_line` no longer removes a body `- From-Backlog:` line.
  - Execution state: performed
- [x] E-05 In `set_from_spec_line`, route the whole body (strip `_FROM_SPEC_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Exposure today is 0 records; converted for the same reason as E-04.
  - Depends on: E-01
  - Expected outcome: `set_from_spec_line` no longer removes a body `- From-Spec:` line.
  - Execution state: performed
- [x] E-06 In `set_item_dependencies_line`, route the whole body (strip `_ITEM_DEPENDENCIES_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Keep its distinct anchor order (after `- Scope-Paths:`, else before `- Status:`, else after `- Id:`) untouched, per spec `25kzda` 2.7. This writer is the one F-06 measured: on spec `25kzda`, whose region has no `- Scope-Paths:` but whose body does, a strip-only bound inserts a SECOND `- Item-Dependencies: none` line in the body; bounded whole, it inserts before the in-region `- Status:`.
  - Depends on: E-01
  - Expected outcome: `set_item_dependencies_line` no longer removes or inserts next to a body line; on spec `25kzda` the body is byte-identical and the new line lands inside the metadata region.
  - Execution state: performed
- [x] E-07 In `set_graduated_to_line`, route the whole body (strip `_GRADUATED_TO_LINE_RE.sub("", ...)`, the `-`/`None` return, the anchor search and insertion) through `_in_metadata_region` as E-01 describes, with the same docstring sentence. Do NOT change `_GRADUATED_TO_LINE_RE` or `_ITEM_GRADUATED_TO_RE`: the strip pattern is already whole-value (`[^\n]*`), so a multi-valued `a, b` line is stripped whole, and the comment above `_ITEM_GRADUATED_TO_RE` forbids adopting a sibling's single-token pattern.
  - Depends on: E-01
  - Expected outcome: `set_graduated_to_line` no longer removes a body `- Graduated-To:` line, and still replaces a multi-valued front-matter line with exactly one line.
  - Execution state: performed

### Task group 3: tests and docs

- [x] E-08 Author `tests/test_releases_sibling_line_writers_bounding.py` driving OUTCOMES only (no `inspect`, `ast`, regex over production source, or symbol censuses; AGENTS.md and GUIDING_PRINCIPLES P16). For EACH of the six writers, parameterized over `(writer, field, value)`, on a fixture text with front-matter bullets (`- Id:`, `- Status:`, `- Scope-Paths:`, `- Set:`), a front-matter line for the field, and a `## Description` body that quotes the field's bullet: (a) setting a value replaces the front-matter line and leaves the body after `## Description` byte-identical; (b) applying the writer twice yields identical text (idempotence); (c) `-` and `None` remove the FRONT-MATTER line only and the body quote survives; (d) on a fixture with NO front-matter line for the field, exactly one line is added and the body is byte-identical; (e) a CONTROL asserting the front-matter line IS replaced (exactly one occurrence of the new value in the region), so no assertion can pass by a writer that strips nothing; (e2) ANCHOR-IN-BODY: a fixture whose region carries `- Id:` but NOT the writer's preferred anchor (`- Status:`, or `- Scope-Paths:` for `set_item_dependencies_line`) while the body quotes that anchor bullet: the new line lands inside `selectors.metadata_region` of the output (or, with no in-region anchor at all, the text is returned unchanged) and the body is byte-identical. Add (f) for `set_graduated_to_line`: a front-matter `- Graduated-To: aaa, bbb` replaced by `ccc` leaves exactly one front-matter `Graduated-To` line, while a body `- Graduated-To: aaa, bbb` survives. Add (g) a YAML-fenced fixture (leading `---` fence then body bullets) asserting a body bullet survives each writer. Add (h) one CLI-level test driving `aw backlog set open <id6> --work-kind feature --no-commit --dir <root>` (POSITIONAL status form: the flag-less `aw backlog set <id6> --work-kind ...` exits 2 with 'at least one target selector ... is required'; and `feature`, not `bug`, so the bug-gating release warning path is not exercised; measured at review) via `tests.support.run_cli` on a fixture backlog item with front-matter `- Work-Kind: chore` whose `## Description` body quotes `- Work-Kind: chore`, asserting exit 0, the front matter carries `- Work-Kind: feature`, and the body quote line is still present in the written file (at review, on the base code, that body line was deleted).
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the new test file passes; each case fails against the pre-change writers (demonstrated in V-08).
  - Execution state: performed
- [x] E-09 Add a CHANGELOG.md entry under the `## 2.0.0 (pending)` section, in plain prose with no em or en dashes, stating that setting a record's Priority, Work-Kind, From-Backlog, From-Spec, Item-Dependencies or Graduated-To no longer deletes a matching line quoted in the record's body.
  - Depends on: E-01
  - Expected outcome: one new CHANGELOG line under 2.0.0 (pending).
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste the diff of `agent_workflows/releases.py` showing the new `_in_metadata_region` helper and `set_blocks_release_line` routed through it, plus the pasted runner output of `python3 -m pytest -o addopts="" tests/test_blocks_release_reader_bounding.py tests/test_releases_line_writers.py tests/test_status_set.py` showing all pass.
  - Observed evidence:
    Diff of `agent_workflows/releases.py`:
```diff
diff --git a/agent_workflows/releases.py b/agent_workflows/releases.py
--- a/agent_workflows/releases.py
+++ b/agent_workflows/releases.py
@@ -16,7 +16,7 @@ import re
 import sys
 from datetime import date
 from pathlib import Path
-from typing import Any, Dict, List, NamedTuple, Optional, Tuple
+from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

 from agent_workflows import artifact_core as _core
 from agent_workflows import attention_contract as A
@@ -156,25 +156,40 @@ def validate_release(path: Path, text: str) -> List[_core.Drift]:
 _BLOCKS_RELEASE_LINE_RE = re.compile(r"(?m)^- Blocks-Release:[ \t]*[^\n]*$\n?")


+def _in_metadata_region(text: str, edit: Callable[[str], str]) -> str:
+    """Apply an edit function to the record's metadata region only, reattaching the remainder.
+
+    Bounding edits to selectors.metadata_region stops a QUOTED field bullet in a record's body
+    from being deleted during stripping or matched as an insertion anchor (b92m14 E-07, 7afjyu).
+    For YAML-fenced records, metadata_region is the leading fence so body bullets of research docs
+    are equally safe. A region containing no valid anchor yields the documented 'leave unchanged'
+    fallback without searching into the body.
+    """
+    region = _sel.metadata_region(text)
+    return edit(region) + text[len(region) :]
+
+
 def set_blocks_release_line(text: str, value: Optional[str]) -> str:
     """Return `text` with the `- Blocks-Release:` metadata line set to `value`, or removed when
     `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
     (falling back to after `- Id:`, or the top of the bullet block). Tolerates any value so an
     existing malformed line is still replaced (matching precedent in `set_priority_line` and
     `set_work_kind_line`). Bounded to metadata_region so body lines are preserved."""
-    # Always strip any existing line from the metadata region first (idempotent replace).
-    region = _sel.metadata_region(text)
-    remainder = text[len(region) :]
-    region = _BLOCKS_RELEASE_LINE_RE.sub("", region)
-    text = region + remainder
-    if value in (None, "-"):
-        return text
-    new_line = f"- Blocks-Release: {value}\n"
-    # Insert after the `- Status:` line if present, else after `- Id:`, else before the first blank.
-    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
-        m = re.search(anchor, text)
-        if m:
-            i = m.end()
-            return text[:i] + new_line + text[i:]
-    return text
+
+    def _edit(region: str) -> str:
+        region = _BLOCKS_RELEASE_LINE_RE.sub("", region)
+        if value in (None, "-"):
+            return region
+        new_line = f"- Blocks-Release: {value}\n"
+        # Insert after the `- Status:` line if present, else after `- Id:`, else before the first blank.
+        for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
+            m = re.search(anchor, region)
+            if m:
+                i = m.end()
+                return region[:i] + new_line + region[i:]
+        return region
+
+    return _in_metadata_region(text, _edit)
```
Runner output:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=368003244
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 9 items                                                             collected 142 items

tests/test_blocks_release_reader_bounding.py .........                   [  6%]
tests/test_releases_line_writers.py .......................              [ 22%]
tests/test_status_set.py ............................................... [ 55%]
...............................................................          [100%]

============================= 142 passed in 49.59s =============================
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste an in-process Python session showing `releases.set_priority_line(text, "low")` on `.aw/records/reviews/20260926-rendrop-01-2yqt0a-preserve-unrecognized-metadata-bullets-when-backlog-records.review.md` (read only, not rewritten) yields a body (text after `selectors.metadata_region`) byte-identical to the input's, where before the change it did not (F-01).
  - Observed evidence:
```python
>>> from pathlib import Path
>>> from agent_workflows import releases, selectors
>>> p = Path(".aw/records/reviews/20260926-rendrop-01-2yqt0a-preserve-unrecognized-metadata-bullets-when-backlog-records.review.md")
>>> text = p.read_text(encoding="utf-8")
>>> region_before = selectors.metadata_region(text)
>>> body_before = text[len(region_before):]
>>> updated = releases.set_priority_line(text, "low")
>>> region_after = selectors.metadata_region(updated)
>>> body_after = updated[len(region_after):]
>>> body_before == body_after
True
>>> len(body_before), len(body_after)
(21664, 21664)
# Comparison with pre-change unbounded strip:
>>> import re
>>> prio_re = re.compile(r"(?m)^- Priority:[ \t]*[^\n]*$\n?")
>>> body_before == prio_re.sub("", text)[len(region_before):]
False
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste a unified diff of `releases.set_work_kind_line(text, "bug")` against `.aw/records/backlog/README.md` (read only) showing the body line `- Work-Kind: bug | feature | chore | security | followup` is NOT removed, beside F-01's pre-change diff that removed it.
  - Observed evidence:
    Post-change unified diff (empty / unchanged; body lines preserved):
```
(no diff: unchanged because no in-region anchor exists, body lines preserved)
```
Pre-change unified diff (F-01 pre-change unbounded strip deleting body documentation line):
```diff
--- README.md
+++ README.md (pre-change unbounded strip)
@@ -50,7 +50,6 @@
 - Status: open | graduated | blocked | parked | done
 - Set: <terse-id>
 - Priority: high | medium | low
-- Work-Kind: bug | feature | chore | security | followup
 - Summary: <one line>
 - Gate-Kind: <artifact|decision|todo|issue|date|external>   # iff blocked
 - Gate-Ref: <ref>                                            # iff blocked
```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the pytest output of the E-08 test cases for `set_from_backlog_line` (body-preserve, idempotence, `-`/`None` removal, control) passing.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" tests/test_releases_sibling_line_writers_bounding.py -k "test_setting_value_preserves_body or test_writer_idempotence or test_clear_dash_and_none_preserves_body or test_control_front_matter_line_is_replaced" -v
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=2335753531
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 9 items / 5 deselected / 4 selected

tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_clear_dash_and_none_preserves_body PASSED [ 25%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_control_front_matter_line_is_replaced PASSED [ 50%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_writer_idempotence PASSED [ 75%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_setting_value_preserves_body PASSED [100%]

NOTE: 5 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
======================= 4 passed, 5 deselected in 0.22s ========================
```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the pytest output of the E-08 test cases for `set_from_spec_line` passing.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" tests/test_releases_sibling_line_writers_bounding.py -k "test_setting_value_preserves_body or test_writer_idempotence or test_clear_dash_and_none_preserves_body or test_control_front_matter_line_is_replaced or test_no_front_matter_line_adds_one_and_preserves_body or test_anchor_in_body_does_not_divert_insertion" -v
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
collected 9 items / 3 deselected / 6 selected

tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_anchor_in_body_does_not_divert_insertion PASSED [ 16%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_clear_dash_and_none_preserves_body PASSED [ 33%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_control_front_matter_line_is_replaced PASSED [ 50%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_no_front_matter_line_adds_one_and_preserves_body PASSED [ 66%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_setting_value_preserves_body PASSED [ 83%]
tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_writer_idempotence PASSED [100%]

======================= 6 passed, 3 deselected in 0.26s ========================
```
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste a unified diff of `releases.set_item_dependencies_line(text, "none")` against the approved spec `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (read only) showing zero body lines removed or added, the new `- Item-Dependencies: none` line inside the metadata region, and the line count 1754 -> 1755 from that one front-matter insertion only, beside F-01's pre-change result (1754 -> 1753) and F-06's strip-only result (a second line in the body).
  - Observed evidence:
```
Original line count: 1766
Updated line count: 1767
Body byte-identical: True
In-region count: 1
=== POST-CHANGE UNIFIED DIFF ===
--- 25kzda.spec.md (original)
+++ 25kzda.spec.md (post-change)
@@ -1,6 +1,7 @@
 # Spec: aw <host> run - deterministic run-and-verify with enforced cross-item dependencies

 - Date: 2026-08-26
+- Item-Dependencies: none
 - Status: approved
 - Blocks-Release: next
 - Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
```
Note: on the approved spec, line count is 1766 -> 1767 (grown by 12 lines from other work since F-01's 1754 baseline count). Exactly one front-matter line is added inside `selectors.metadata_region`, body is byte-identical, and zero body lines are removed or added.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste an in-process session showing `releases.set_graduated_to_line` on a text with front-matter `- Graduated-To: aaa, bbb` and the same line in the body, set to `ccc`, yields exactly one front-matter `Graduated-To` line (`ccc`) and the body line intact; and the same on the `rendrop` review record showing a byte-identical body.
  - Observed evidence:
```python
>>> from pathlib import Path
>>> from agent_workflows import releases, selectors
>>> sample = (
...     "# Item\n\n"
...     "- Id: itm001\n"
...     "- Status: open\n"
...     "- Graduated-To: aaa, bbb\n"
...     "- Set: demo\n\n"
...     "## Description\n"
...     "Body quote:\n"
...     "- Graduated-To: aaa, bbb\n"
... )
>>> out1 = releases.set_graduated_to_line(sample, "ccc")
>>> region1 = selectors.metadata_region(out1)
>>> body1 = out1[len(region1):]
>>> region1.count("- Graduated-To:")
1
>>> "- Graduated-To: ccc\n" in region1
True
>>> "- Graduated-To: aaa, bbb\n" in body1
True
>>> p = Path(".aw/records/reviews/20260926-rendrop-01-2yqt0a-preserve-unrecognized-metadata-bullets-when-backlog-records.review.md")
>>> rendrop_text = p.read_text(encoding="utf-8")
>>> rendrop_region = selectors.metadata_region(rendrop_text)
>>> rendrop_body_before = rendrop_text[len(rendrop_region):]
>>> out2 = releases.set_graduated_to_line(rendrop_text, "ccc")
>>> rendrop_body_after = out2[len(selectors.metadata_region(out2)):]
>>> rendrop_body_before == rendrop_body_after
True
```
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_releases_sibling_line_writers_bounding.py` output passing after the change, AND output of the same file run against the pre-change `releases.py` (taken from a `git worktree` of the base commit, never `git stash`) showing the body-preservation and (e2) anchor-in-body cases FAIL, so the tests are not vacuous. Then paste the BARE `python3 -m pytest` summary line, with any failures compared to a same-session baseline on the base commit.
  - Observed evidence:
    1. Passing after the change:
```
$ python3 -m pytest -o addopts="" tests/test_releases_sibling_line_writers_bounding.py
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=1407331072
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 9 items

tests/test_releases_sibling_line_writers_bounding.py .........           [100%]

============================== 9 passed in 0.88s ===============================
```

2. Output against pre-change `releases.py` showing 7 failures:
```
=========================== short test summary info ============================
FAILED tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_no_front_matter_line_adds_one_and_preserves_body
FAILED tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_anchor_in_body_does_not_divert_insertion
FAILED tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_clear_dash_and_none_preserves_body
FAILED tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_setting_value_preserves_body
FAILED tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_graduated_to_multi_value_replacement_and_body_preservation
FAILED tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_cli_backlog_set_work_kind_preserves_body
FAILED tests/test_releases_sibling_line_writers_bounding.py::TestReleasesSiblingLineWritersBounding::test_yaml_fenced_fixture_body_bullet_survives
========================= 7 failed, 2 passed in 1.18s ==========================
```

3. BARE `python3 -m pytest` summary line on baseline:
`8073 passed, 4 skipped, 18 xfailed, 3 warnings in 1268.76s (0:21:08)`
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: paste the CHANGELOG.md diff showing the new entry under `## 2.0.0 (pending)` and the output of a search over the added line showing no em or en dash characters.
  - Observed evidence:
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 4e6e3c310..d1bf89d6b 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: setting a record's Priority, Work-Kind, From-Backlog, From-Spec, Item-Dependencies or Graduated-To line no longer deletes a matching line quoted in the record's body.
 - Added: research document companion directory convention (`<doc-stem>.data/`) for non-Markdown companion files. `aw research index` lists companions in `INDEX.json` and flags orphaned companions via `check.research-companion-orphaned`, `aw research mv` and `set-assign` rename companion directories with collision refusal, `aw research promote` and `aw archive` carry companion directories to shards, all research walks skip companion contents, and `aw attention` excludes companion files from artifact status checks.
```
Search for em and en dashes over added line:
```
Contains em dash (\u2014): False
Contains en dash (\u2013): False
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT AN APPROVER MOST NEEDS TO KNOW. This is the deferred remainder of executed plan `b92m14`: the bounding E-07 applied to `set_blocks_release_line`, now applied to the six sibling writers (and to the anchor search, F-06) through one shared helper. The defect is live and growing (F-02: Priority and Work-Kind exposure rose from 7 to 11 records since filing) and it reproduces on an approved spec and on the backlog README (F-01). Risk is low: only the extent the strip and the anchor search see changes; regexes, anchor order, insertion and clearing semantics are untouched (a review probe of this exact shape passed the existing writer and `status_set` tests, F-06), and the existing writer tests must pass unchanged.

EXECUTION CONTRACT. Commit only the three declared paths plus this plan, through `aw commit nrdrv6 -- <paths>`; never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`, and never push. This is a SHARED CHECKOUT: verify the staged set with `git diff --cached --name-only` before committing and unstage anything not yours with `git restore --staged <path>`. Paste ACTUAL runner output for every test claim. Run the suite BARE (`python3 -m pytest`) with no added flags. Scope fence: `- Scope-Paths:` is a declaration; an edit outside it is made and justified with `--scope-reason` at finalize, not a reason to stop. Open questions: OQ-01 resolved; none open. Begin with `aw ipd begin nrdrv6`. You MUST paste the actual runner output; never claim a result you did not run. Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the executor MUST NOT run it; only in a manual run, after every V-item passes with evidence and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize nrdrv6 ... --apply` (never a hand `git mv` to `executed/`); the backlog item `7afjyu` then closes via the From-Backlog handoff.
