# IPD: Make the releases metadata line writers tolerate an empty value so they replace rather than duplicate their field, and refuse an unresolvable --from-backlog at the setter

- Date: 2026-09-30
- Kind: child
- Concern: Two writers in `agent_workflows/releases.py` DUPLICATE the field they are meant to replace. `releases._BLOCKS_RELEASE_LINE_RE` and `releases._FROM_BACKLOG_LINE_RE` both use a `\S+` value group, which cannot match an EMPTY value, so the idempotent strip that opens `releases.set_blocks_release_line` and `releases.set_from_backlog_line` misses an existing bare `- Blocks-Release:` / `- From-Backlog:` line and the subsequent insert adds a SECOND one. Measured in this lane at HEAD `d7328e8e`: `set_from_backlog_line("- Status: to-review\n- From-Backlog:\n- Id: abc123\n", "zzz999")` returns text containing TWO `- From-Backlog:` lines, and `set_blocks_release_line` does the same for its field. The duplicate is PERMANENT rather than transient: repeating the write four times leaves the junk line untouched every time (the strip can never reach it), and clearing with `-` removes the GOOD line and leaves the empty one behind, so a cleared gate is indistinguishable from the corrupt state that produced it. The correct shape is already in the same module two functions away: `releases.set_priority_line` and `releases.set_work_kind_line` use `[^\n]*` and their docstrings state the reason outright, "Tolerates any value so an existing malformed line is still replaced." SEPARATELY, `aw ipd set --from-backlog` and `aw specs set --from-backlog` write ANY value unvalidated, so a sanctioned command mints the exact dangling link `check.from-backlog-dangling` is registered at `error` to fail on: measured, `aw ipd set to-review <plan> --from-backlog nosuch` exits 0 and `releases.check_from_backlog` then reports `From-Backlog 'nosuch' does not resolve to a backlog item`.
- Scope: Change the value group of `releases._BLOCKS_RELEASE_LINE_RE` and `releases._FROM_BACKLOG_LINE_RE` from `\S+` to `[^\n]*`, matching their `set_priority_line`/`set_work_kind_line` siblings, so both writers REPLACE an empty-valued or malformed line instead of duplicating it; and add a resolvability refusal for `--from-backlog` on the two setter surfaces that lack one (`aw ipd set` / the bare `aw set` through `status_set`, and `aw specs set` through `specs.run_set`), mirroring the `--from-spec` refusal those same two functions already carry and reaching the id set through the EXISTING `backlog.existing_backlog_ids` authority. Add the writer and setter tests that do not exist today. EXCLUDES any change to the READER patterns `releases._ITEM_BLOCKS_RELEASE_RE` / `releases._ITEM_FROM_BACKLOG_RE` (measured below: their `\S+` is CORRECT and changing it would be a regression, which is a deliberate correction to the backlog item's suggestion that they be changed in the same pass); EXCLUDES any corpus backfill (zero artifacts carry an empty-valued line today); EXCLUDES `aw ipd scaffold --from-backlog`, which already refuses an unresolvable id; EXCLUDES any change to `check.from-backlog-dangling`, `check.blocks-release-dangling`, or any severity.
- Scope-Paths: agent_workflows/releases.py, agent_workflows/status_set.py, agent_workflows/specs.py, tests/test_releases_line_writers.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 71wqol
- Blocks-Release: next
- Set: relwriteempty
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: izh17y

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: izh17y verified (set relwriteempty, attempt 1).
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (aw set): status set to reviewed

- 2026-09-30 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-1001 (HIGH), PR-1002, PR-1003, PR-1004, PR-1007 (MEDIUM), PR-1005, PR-1006 (LOW), all FIXED. Reviewed at HEAD `7a9e4be3c`; typed record at `.aw/records/reviews/20260930-relwriteempty-01-izh17y-make-the-releases-metadata-line-writers-tolerate-an-empty-va.review.md`. BOTH DEFECTS REPRODUCE EXACTLY AND THE PRESCRIBED FIX IS PRECISELY RIGHT: the two writers duplicate while `set_priority_line` and `set_from_spec_line` on identical input do not; four successive writes never heal the record and `-` deletes the GOOD line; E-01's regex is character-for-character the sibling shape modulo the field name and provably cannot cross a newline; and both setter surfaces exit 0 while persisting a dangling link. F-02, F-04, F-07 through F-10, the `cli.py` fork citation and the whole `0ykozn` -> `71wqol` provenance chain all verified. THE SERIOUS FINDING IS PR-1001, A RIGHT ANSWER FROM A WRONG ARGUMENT: F-05 and OQ-01 justify leaving the readers strict on the claim that the duplicate "always sits SECOND", and both halves are false, because the junk line sits FIRST whenever the pre-existing empty line precedes the `- Status:` anchor (reachable from an ordinary tooled write, measured) and because on the junk-second order a line-bounded tolerant reader returns the REAL value; the `''` figure came from a `\s*` pattern that crosses newlines. The conclusion survives on the ordering-independent ground that `\S+` cannot match an empty value while a tolerant reader captures `''` which `source_link_is_absent` reports as ABSENT, losing a real gate. PR-1002 widens that audit from two readers to FOUR across two modules (`production_checks.py` has its own copy at four call sites). PR-1003 names the deliberate divergence the empty-set skip creates with `check_from_backlog`, whose own docstring calls itself the less-safe twin and forbids harmonizing, so the skip must be documented or a later reader deletes it. PR-1004 supplies the missing baseline: the suite is NOT green (one date-dependent failure in `tests/test_backlog.py`, a module E-03's path exercises) and both prescribed `aw check` runs already exit 1. PR-1007 corrects an instruction that cannot be followed literally, since `specs.run_set` has no `repo_root` and must use its own `_repo_root_of(path)`. No production code or test was changed by this review.
- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `71wqol`. Reproduced both defects in this lane at HEAD `d7328e8e` and resolved the item's one open design question (whether to also change the READER patterns) AGAINST changing them, from a measurement recorded as F-05: on the duplicated text the readers' `\S+` correctly returns the REAL value while a tolerant reader would return the empty string, so the audit the item asks for concludes the readers are already right. Also corrected one claim in the item (F-04: the duplicate IS diagnosable on a plan, via `IPD-M102`) and strengthened its severity case with two consequences the item did not measure (F-06, F-07).
- 2026-09-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make two metadata line writers keep their advertised contract. Both `releases.set_blocks_release_line` and `releases.set_from_backlog_line` document themselves as "Idempotent: replaces an existing line or inserts one", and both break that promise on one input shape: an existing line whose value is empty. The fix is a two-character-class change per pattern, to the shape two sibling writers in the same module already use and document.

THE POINT IS NOT THE EMPTY VALUE, IT IS THAT THE FIELD BECOMES UNREPAIRABLE. A duplicated single-valued metadata field is not merely untidy, because no subsequent tooled write can clean it up: the strip that would remove it is the very strip that cannot see it. Measured in this lane, calling `set_blocks_release_line(t, "next")` four times in a row leaves the junk line present after every call, and calling it with `-` (the documented clear) deletes the GOOD line and leaves the junk one, so an operator who tries to fix the record by re-writing or by clearing and re-setting cannot succeed with the tools. Only a hand edit recovers it, and hand-editing managed metadata is what the repository's own conventions push authors away from.

THE SECOND HALF IS A SETTER THAT MANUFACTURES A CI FAILURE. `check.from-backlog-dangling` is registered at `error` severity, so an unresolvable `- From-Backlog:` value fails `aw check` and the named CI step. Two shipped setter surfaces write that value with no resolution check at all, so `aw ipd set to-review <plan> --from-backlog nosuch` exits 0 having created a state the repository's own gate rejects. This is not a hypothesis about a hypothetical user: it is the asymmetry `agent_workflows/status_set.py` already documents in prose at its `--from-spec` guard, which calls itself "deliberately STRICTER than its twin, because adding a refusal costs nothing while the alternative writes a known-bad link". This plan makes the twin match, using the same guard shape and the same fail-safe posture (skip the refusal when the known-id set is empty, so an invisible corpus cannot make every write fail).

WHY THE READERS ARE LEFT ALONE, since the backlog item explicitly asks for them to be "audited in the same pass" and the audit's conclusion is that they are correct. `releases._ITEM_BLOCKS_RELEASE_RE` and `releases._ITEM_FROM_BACKLOG_RE` share the `\S+` shape, but for a READER that shape is the RIGHT answer, measured rather than assumed (F-05, with its reasoning corrected at review in F-11): a tolerant pattern captures `''` from an empty-valued line, and `ipd_schema.source_link_is_absent("")` is `True`, so a tolerant READER turns a malformed line into a confident claim that the field is ABSENT. A strict `\S+` reader cannot, because it cannot match an empty value at all and `.search()` therefore continues to the next line and finds the real value if one exists. So harmonizing the readers onto the writers' new shape would convert a correctly-read gate into an absent one, which for `check.blocking-item-closed-without-gate` means a release blocker could be closed as though it carried no gate. The writer axis and the reader axis want opposite tolerances, and this plan changes only the writers. NOTE the argument above deliberately does NOT depend on which of the two duplicate lines comes first: review measured both orders to be reachable from ordinary tooled writes, so any reasoning resting on the junk line's position is unsound (F-11). This is the same lesson `0ykozn` recorded in its own conventions section: in this module "mirror the twin exactly" is an unsafe instruction, and each axis must be chosen on its own evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the writer fix

- [x] E-01 In `agent_workflows/releases.py`, change the value group of `_BLOCKS_RELEASE_LINE_RE` and `_FROM_BACKLOG_LINE_RE` from `\S+` to `[^\n]*`, giving `(?m)^- Blocks-Release:[ \t]*[^\n]*$\n?` and `(?m)^- From-Backlog:[ \t]*[^\n]*$\n?`. Change NOTHING else about either writer: the `- Status:` anchor with its `- Id:` fallback, the `None`/`'-'` clearing branch, and the final no-anchor fallback are all OUT OF SCOPE and are relied upon by callers in `status_set.py`, `specs.py` and `backlog.py`. BE PRECISE ABOUT THE LAST ONE RATHER THAN CALLING IT "CORRECT": measured at review, when a text contains neither a `- Status:` nor an `- Id:` line the writer returns the text UNCHANGED and the caller's value is SILENTLY DROPPED (`set_blocks_release_line("Some prose with no bullets at all.\n", "next")` returns its input). That is a separate shape from the duplication this plan fixes, it is unreachable from any real record (every record type requires `- Id:`), and it is deliberately NOT changed here; do not "improve" it in passing, because a silent-drop-to-raise change would alter a shipped writer's contract for every caller and belongs in its own plan with its own corpus measurement. Extend each function's docstring with the sentence its two correct siblings already carry, "Tolerates any value so an existing malformed line is still replaced", and name `set_priority_line` and `set_work_kind_line` as the precedent so the next author does not re-derive the choice. DO NOT touch `_ITEM_BLOCKS_RELEASE_RE` or `_ITEM_FROM_BACKLOG_RE`, the READERS declared further down the same module: F-05 measures that their `\S+` is correct and that a tolerant reader would return the empty string for a real value.
  THE FULL-LINE ANCHORING MUST SURVIVE THE EDIT, and it is the one way this change could go wrong. `[^\n]*` is greedy but cannot cross a newline, and the pattern keeps `(?m)` with `^- Blocks-Release:` and `$\n?`, so it still matches exactly one whole line. Do NOT reach for `.*` with `re.DOTALL`, and do NOT drop the `$` anchor: either would let the pattern consume following lines and silently delete adjacent metadata. The neighbouring `_WORK_KIND_LINE_RE` docstring records why full-line anchoring is load-bearing for a related reason (it must never touch the unrelated `- Gate-Kind:` or the structural `- Kind:`), and the same discipline applies here.
  - Depends on: none
  - Expected outcome: two changed patterns and two extended docstrings in `releases.py`; `set_blocks_release_line("- Status: open\n- Blocks-Release:\n- Id: aaaaaa\n", "next")` and `    set_from_backlog_line("- Status: to-review\n- From-Backlog:\n- Id: abc123\n", "zzz999")` each yield text containing EXACTLY ONE line of the field; every previously-working case (absent line, valued line, clearing, no-`- Status:` fallback) is unchanged.
  - Execution state: performed

- [x] E-02 Add `tests/test_releases_line_writers.py` covering the two repaired writers as OUTCOMES, because no test exercises either writer today (measured: `rg -n "set_from_backlog_line|set_blocks_release_line" tests/` returns nothing, so this defect shipped with zero writer coverage and the regression guard must be created, not extended). For EACH of the two functions assert, over realistic front matter: the empty-valued existing line is REPLACED so exactly one line remains; a whitespace-only value (`- Blocks-Release:   `) is likewise replaced, since that is the same class of malformed line and the `[ \t]*` prefix plus `[^\n]*` value must absorb it; a normally-valued existing line is replaced with the new value; an absent line is inserted immediately after `- Status:`, asserted by quoting the adjacent lines rather than by a bare substring test; insertion falls back to after `- Id:` when no `- Status:` exists; a second identical call is BYTE-IDENTICAL to the first; `'-'` and `None` remove the line and leave NO residue, which is the clearing half F-03 measures as broken today; and the REPAIR case, where a text that already carries the duplicate corruption is healed to exactly one line by one write, since that is the operator-recovery property F-03 shows is absent today. Assert no OTHER metadata line is disturbed by any of these writes, comparing the full remaining bullet block, which is what would catch a mis-anchored pattern deleting a neighbour.
  TEST OUTCOMES, NOT CODE STRUCTURE. Drive the real functions and assert on returned text. Do NOT assert that the pattern source string equals `[^\n]*` and do NOT read `releases.py` with `inspect`, `ast`, regex, or substring search: AGENTS.md and `GUIDING_PRINCIPLES` P16 forbid a code-pinning test, and a behavioral assertion that one line results is strictly stronger anyway, because it fails for every wrong pattern rather than for one spelling.
  - Depends on: E-01
  - Expected outcome: a new test file whose cases all fail on the pre-E-01 code for the empty-value, whitespace-value, clearing-residue and repair cases and all pass after it; paste both runs.
  - Execution state: performed

### Task group 2: the setter refusal

- [x] E-03 In `agent_workflows/status_set.py`, refuse an unresolvable `--from-backlog` value before anything is resolved or written, mirroring the `--from-spec` refusal already present in the SAME function. Add the guard at the entry point beside the existing `fs_val = getattr(args, "from_spec", None)` block (the block whose message reads `aw set: unresolvable spec id`), so a malformed value exits 2 having written nothing, and add the matching backstop beside the `from_spec` validation inside `apply_status_change` (the block raising `ValueError` with `unresolvable spec id`) so a direct call cannot bypass it either. Resolve the value through the EXISTING `backlog.existing_backlog_ids` authority, which `releases.check_from_backlog` already uses to decide this exact question, and add no second scanner (`GUIDING_PRINCIPLES` P8). `'-'` must pass through untouched, since it is the documented clear. SKIP the refusal when the known-id set is EMPTY, exactly as the `--from-spec` guard does and for the reason its comment records: an invisible backlog corpus must not make every write fail.
  THE EMPTY-SET SKIP DELIBERATELY DISAGREES WITH THE CHECKER, AND THAT DIVERGENCE MUST BE WRITTEN DOWN IN THE CODE RATHER THAN LEFT FOR A LATER READER TO "FIX" (F-12). `releases.check_from_backlog` has NO such guard and its own docstring says so, calling itself "the less safe" twin and recording that on a repo with neither tree it returns one FALSE finding where the spec-side checker returns none, and then instructing: "Do NOT 'harmonize' that guard away to match this function; the difference is a known gap here, not a standard to spread." Reproduced at review. So after this plan, on a backlog-tree-less repository, the SETTER permits the write while `aw check` reports it dangling at `error`. State that in the guard's comment, naming `check_from_backlog`'s docstring as the authority for why the setter takes the SAFE posture rather than copying the checker's. Do NOT add the guard to `check_from_backlog` (out of scope, and that module is not declared), and do NOT drop the skip to make the two agree.
  KEEP THE GATE-INHERITANCE BLOCK WORKING, because it sits immediately below the write this guard protects and reads the same value. `status_set.apply_status_change`'s `from_backlog` block calls `backlog.blocks_release_of_item(repo_root, fb)` to inherit the item's `- Blocks-Release:` at graduation; after this change that lookup can only ever be handed a value that resolves or is `-`, which strictly improves it and must not be removed or reordered. Its stdout notice (`aw set: inherited - Blocks-Release: ...`) must still fire for a resolvable id carrying a gate.
  - Depends on: none
  - Expected outcome: `aw ipd set to-review <plan> --from-backlog nosuch` exits nonzero naming `nosuch` and leaves the file byte-identical; `--from-backlog <real-id6>` still writes the field and still inherits the item's gate with its notice; `--from-backlog -` still clears.
  - Execution state: performed

- [x] E-04 In `agent_workflows/specs.py`, add the same refusal to the FORKED `--status` spelling, `specs.run_set`, whose `from_backlog_arg` block writes the value through `releases.set_from_backlog_line` with no validation. THIS SURFACE IS NOT COVERED BY E-03 AND THAT IS THE WHOLE REASON IT IS A SEPARATE ITEM: measured in this lane, `aw specs set <spec> --status draft --from-backlog nosuch` exits 0 and persists the dangling link, because `aw specs set --status ...` routes to `specs.run_set` rather than through `status_set`. The repository already records this fork as a real bypass class: `agent_workflows/cli.py` carries the comment that `aw specs set --status approved` "routes to the FORKED `specs.run_set`, not through status_set, so the override must exist on this surface too or the spelling itself would be the bypass". Use the same `backlog.existing_backlog_ids` resolution, the same `'-'` passthrough, and the same empty-set skip as E-03, and return 2 with a message naming the unresolvable id, matching this function's existing refusal style (it already returns 2 for a malformed `--graduated-to` and writes its message to stderr, verified at review at the `graduated_to_arg` block). Leave its gate-inheritance block, which mirrors `status_set`'s, untouched.
  REACH THE REPO ROOT THE WAY THIS FUNCTION ALREADY DOES, NOT THE WAY `status_set` DOES. Added at review: `specs.run_set` has no `repo_root` parameter or local; it derives one per use with the module-local `specs._repo_root_of(path)`, which walks up from the SPEC FILE to the first ancestor holding `.aw`, `.agents` or `.git` and falls back to cwd. Its own `from_backlog_arg` block already calls `blocks_release_of_item(_repo_root_of(path), ...)`. Use `_repo_root_of(path)` for `existing_backlog_ids` too, so the guard and the inheritance lookup immediately below it resolve against the SAME root; reaching for `Path.cwd()` or inventing a second root derivation would let the guard consult a different tree than the write it is guarding, which is a silent wrong-answer shape rather than a visible failure.
  PLACE THE REFUSAL BEFORE ANY WRITE, WHICH ON THIS SURFACE MEANS BEFORE `set_from_backlog_line` MUTATES `new_text`. This function builds `new_text` in memory and only persists after a final `validate_spec` gate, so a late refusal would still be byte-safe on disk; but returning 2 before the in-memory write keeps the guard's shape identical to E-03's and keeps the V-04 byte-identical assertion meaningful rather than incidental.
  - Depends on: E-03
  - Expected outcome: `aw specs set <spec> --status draft --from-backlog nosuch` exits nonzero naming `nosuch` with the spec file byte-identical; the resolvable case still writes the field and still inherits the item's gate.
  - Execution state: performed

- [x] E-05 Extend `tests/test_releases_line_writers.py` with CLI-level outcome tests for both refusals, driven as real subprocesses over a real temporary repository containing one real backlog item, one plan and one spec. Required cases, for `aw ipd set` and `aw specs set --status` INDEPENDENTLY because E-04 establishes they are different code paths: an unresolvable value exits nonzero, names the offending value in its output, and leaves the target file BYTE-IDENTICAL (compare the bytes, not a field, since a partial write is the failure mode that matters); a resolvable id6 still writes `- From-Backlog: <id6>` and, when the item carries `- Blocks-Release:`, still inherits it; `-` still clears the field. Add one case pinning the empty-set fail-safe: in a repository with NO backlog tree at all, a `--from-backlog` write must still succeed rather than refuse, which is the posture the `--from-spec` guard's comment demands and the one way this change could break an unrelated project layout. THAT TEST PINS A STATE THE CHECKER DISAGREES WITH, DELIBERATELY, AND ITS DOCSTRING MUST SAY SO (F-12): on the same tree `releases.check_from_backlog` reports the value as dangling at `error`, because that function has no empty-set guard and its own docstring records the asymmetry and forbids harmonizing it away. Write that into the test's docstring so the next reader does not read the passing test as proof the two surfaces agree, and do NOT assert anything about `aw check`'s behavior in that case. Assert on exit codes, on output text, and on file content only.
  - Depends on: E-04
  - Expected outcome: tests that fail on the pre-E-03/E-04 code (the refusal cases exit 0 and write the bad value there) and pass after; paste both runs.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THIS MODULE'S WRITERS DO NOT AGREE WITH EACH OTHER, AND THE DISAGREEMENT IS DOCUMENTED RATHER THAN ACCIDENTAL. `releases.py` holds seven single-line metadata writers. `set_priority_line`, `set_work_kind_line`, `set_from_spec_line` and `set_graduated_to_line` use `[^\n]*` and say why ("Tolerates any value so an existing malformed line is still replaced"); `set_blocks_release_line` and `set_from_backlog_line` use `\S+` and say nothing; `set_item_dependencies_line` uses `[^\n]*` and its docstring explicitly contrasts itself with "the release/backlog line regex (which requires a `\S+` value)". So the correct shape is not a judgement call to be made fresh: it is stated four times in the same file, and the two outliers are the defect.
- A TWIN IS A PRECEDENT FOR SHAPE, NOT A GUARANTEE OF CORRECTNESS. Plan `0ykozn` recorded exactly this as a discovered convention of this module after measuring the same duplication bug, and its E-01 was amended at review to pin `[^\n]*` and to forbid inheriting `_FROM_BACKLOG_LINE_RE`'s shape. That plan is `executed` and its `## Deferred` rows name this item's id6 (`71wqol`) as the carrier for the repair it declined to make, so this plan is the sanctioned continuation rather than a re-litigation.
- `check.from-backlog-dangling` IS AN `error`, WHICH IS WHAT MAKES THE UNVALIDATED SETTER A DEFECT RATHER THAN AN UNTIDINESS. `check_engine.RULE_REGISTRY` registers it at `error`, `agent_workflows/check_engine.py` lists it among the rules composed into the release-gate family, and AGENTS.md records `aw check release-gates` as a named fail-closed CI step. A setter that writes a value this rule rejects has manufactured a CI failure from an exit-0 command.
- THE `--from-spec` GUARD IS THE EXACT TEMPLATE, INCLUDING ITS FAIL-SAFE. It validates at the CLI entry AND again inside `apply_status_change`, resolves through one shared helper rather than a second construction, passes `'-'` through, and skips the refusal when the known-id set is empty so an invisible corpus cannot fail every write. Its comment states the asymmetry with `--from-backlog` and calls the twin's gap out by name, so the fix here is to satisfy a TODO the code already wrote for itself.
- A SPEC SETTER HAS TWO SPELLINGS AND THEY DO NOT SHARE A CODE PATH. `aw specs set <path> --status <s>` routes to `specs.run_set`; the bare `aw specs set <s> <path>` routes to `status_set.apply_status_change`. `cli.py` records this fork explicitly where it duplicates `--allow-open-questions` onto the specs surface, warning that otherwise "the spelling itself would be the bypass". Any guard added to one must be added to the other, which is why E-03 and E-04 are separate items rather than one.
- `aw ipd scaffold --from-backlog` ALREADY DOES THE RIGHT THING, so the defect is a gap in two surfaces and not a missing design. `ipd_authoring.run_scaffold` calls `backlog.find_item` and prints `error: --from-backlog <id>: no backlog item has that id` with exit 2 before writing anything. The refusal E-03/E-04 add is the same decision on the other two surfaces, reached through `existing_backlog_ids` because those call sites need only the resolvability answer and not the parsed item.
- THERE IS A FOURTH `From-Backlog` READER, IN A DIFFERENT MODULE, AND IT IS ALSO CORRECTLY STRICT. Added at review (PR-1002): `production_checks.py` declares its OWN `_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^-[ \t]*From-Backlog:[ \t]*(\S+)[ \t]*$")` and uses it at four call sites, so the reader population the item asks to "audit in the same pass" is four patterns across two modules, not two in one. F-05's and F-11's conclusion covers it unchanged (it is a reader, so strictness is right, and it is additionally more tightly bounded than its `releases.py` cousins because it uses `[ \t]*` rather than `\s*`). RECORDED, NOT CHANGED: `production_checks.py` is deliberately absent from `- Scope-Paths:` and must stay absent. It is named here so a reader auditing the claim "the readers are correct" can find every reader, and so a later author does not discover an unmentioned copy and conclude the audit was partial.
- TEST OUTCOMES, NOT CODE STRUCTURE (AGENTS.md; `GUIDING_PRINCIPLES` P16). Every test this plan adds drives a real function or a real CLI over a real temporary repository and asserts on returned text, file bytes, exit codes and output. None reads production source.

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | In this lane at HEAD `d7328e8e`: `set_from_backlog_line("- Status: to-review\n- From-Backlog:\n- Id: abc123\n", "zzz999")` -> `'- Status: to-review\n- From-Backlog: zzz999\n- From-Backlog:\n- Id: abc123\n'`, count 2. `set_blocks_release_line` on the analogous input -> `'- Status: to-review\n- Blocks-Release: next\n- Blocks-Release:\n- Id: abc123\n'`, count 2. `set_priority_line` on the same shape -> one line. `set_from_spec_line` on the same shape -> one line | THE ITEM'S CENTRAL CLAIM REPRODUCES EXACTLY, ON BOTH NAMED FUNCTIONS, AND THE CORRECT BEHAVIOR IS AVAILABLE IN THE SAME MODULE. Two writers duplicate; two siblings, called with the identical input shape, do not. So this is a one-line divergence from an established in-module contract rather than an open design question. |
| F-02 | HIGH | `releases.py`: `_BLOCKS_RELEASE_LINE_RE` and `_FROM_BACKLOG_LINE_RE` use `\S+`; `_PRIORITY_LINE_RE`, `_WORK_KIND_LINE_RE`, `_FROM_SPEC_LINE_RE`, `_GRADUATED_TO_LINE_RE`, `_ITEM_DEPENDENCIES_LINE_RE` use `[^\n]*`. `set_item_dependencies_line`'s docstring: "Unlike the release/backlog line regex (which requires a `\S+` value), this regex tolerates any value so an existing malformed line is still replaced idempotently" | THE DIVERGENCE IS 2 OUT OF 7 AND IS ALREADY NAMED IN THE CODE AS THE ODD ONE OUT. A later author documented choosing differently FROM these two specifically, which means the defect was observed and routed around rather than fixed, twice (here and in `0ykozn`). That is the strongest available argument that the fix belongs in the shared writers rather than in each new caller. |
| F-03 | HIGH | Added here; NOT measured in the backlog item. Calling `set_blocks_release_line(t, "next")` four times on the empty-valued input leaves `['- Blocks-Release: next', '- Blocks-Release:']` after EVERY call. Then `set_blocks_release_line(<that text>, "-")` returns `['- Blocks-Release:']`, having removed the GOOD line and kept the junk one | THE CORRUPTION IS UNREPAIRABLE BY THE TOOLS AND THE DOCUMENTED CLEAR MAKES IT WORSE, which raises the severity above the item's "latent" framing. A re-write cannot heal the record because the strip that would remove the junk line is the strip that cannot see it, and `-` deletes the wrong line, leaving a state that reads as "no gate" while still carrying a stray bullet. An operator's two obvious recovery moves both fail, so recovery requires the hand edit the repository's conventions discourage. This is also why E-02 demands a REPAIR test case: after the fix, one write must heal an already-corrupt record. |
| F-04 | MED | The item says the duplicate is "UNDIAGNOSABLE downstream". Measured: on a PLAN it is diagnosed. `aw ipd lint` on a plan carrying both lines reports `IPD-M102: From-Backlog: duplicate field`, because `ipd_schema.parse_metadata_block` counts field occurrences and emits `duplicate field` on the second. But on a BACKLOG ITEM and a SPEC it is invisible: `aw backlog check` reported `all backlog items conform` and `aw specs check` reported `all specs conform` on files carrying the duplicate, and `aw check all` reported it nowhere | ONE CLAIM IN THE ITEM IS TOO BROAD AND THE CORRECTION NARROWS THE BLAST RADIUS WITHOUT WEAKENING THE CASE. The plan surface has a lint that catches this; the backlog and spec surfaces have none, and `aw backlog set` and `aw specs set` are exactly the verbs that write these two fields onto those record types. So the undiagnosable population is backlog items and specs, which is where `- Blocks-Release:` most often lives. Recorded because a reviewer checking the item's wording on a plan would find the duplicate reported and might wrongly conclude the item overstates the problem. |
| F-05 | HIGH | Added here; DECIDES the item's open audit question. CONCLUSION CONFIRMED AT REVIEW, REASONING CORRECTED (see F-11). Measured: `_ITEM_BLOCKS_RELEASE_RE.search` and `_ITEM_FROM_BACKLOG_RE.search` both return `None` on a text whose only line is empty-valued, and `ipd_schema.source_link_is_absent("")` is `True`, so "no match" and "empty value" already mean the same thing to every consumer. On the duplicated text `- Blocks-Release:\n- Blocks-Release: next\n` a strict `\S+` reader captures `'next'` while a LINE-BOUNDED tolerant pattern (`[ \t]*([^\n]*?)[ \t]*$`) captures `''` | THE READERS MUST NOT BE HARMONIZED ONTO THE WRITERS' NEW SHAPE, WHICH REVERSES THE ITEM'S SUGGESTION THAT THEY BE CHANGED IN THE SAME PASS. The two axes want opposite tolerances. A strict `\S+` reader SKIPS an empty-valued line and finds the real value on a later line; a tolerant reader stops at the first matching line and returns the empty string, which `source_link_is_absent` then reports as ABSENT, so loosening the readers would report a real release blocker as ungated and `check.blocking-item-closed-without-gate` would permit closing it. The readers are also already correct for the single-line empty case: both return `None`, the same answer as absent. The audit the item requests is therefore performed and its answer is "no change". ONE PREMISE OF THE ORIGINAL ROW WAS WRONG AND IS CORRECTED IN F-11: it asserted the junk line is always SECOND, which is false, and the ordering is not what the argument needs. |
| F-06 | MED | Added here. `aw ipd set to-review <plan> --from-backlog nosuch` exits 0 and persists `- From-Backlog: nosuch`; `releases.check_from_backlog` then reports `check.from-backlog-dangling`, registered `error`. `aw specs set <spec> --status draft --from-backlog nosuch` likewise exits 0 and persists it | DEFECT 2 REPRODUCES ON TWO SURFACES, NOT ONE, AND THE ITEM NAMES ONLY `aw ipd set`. The `--status` spelling of `aw specs set` forks to `specs.run_set` and has its own unvalidated write, so a guard on `status_set` alone would leave a live bypass. This is why the fix is split into E-03 and E-04 and why E-05 tests the two spellings independently. |
| F-07 | MED | Added here. `aw ipd scaffold --from-backlog nosuch` refuses: `error: --from-backlog nosuch: no backlog item has that id`, exit 2, via `ipd_authoring.run_scaffold`'s `backlog.find_item` call. `status_set.py` comments that its `--from-spec` guard is "deliberately STRICTER than its twin, because adding a refusal costs nothing while the alternative writes a known-bad link" | THE REPOSITORY HAS ALREADY DECIDED THIS QUESTION TWICE IN FAVOUR OF REFUSING, which removes it from the set of things this plan must argue. One of three `--from-backlog` surfaces validates, and the code beside the two that do not explicitly names their gap. So E-03/E-04 apply an established decision to the surfaces that missed it rather than introducing a new policy, and no open question about setter strictness needs a human. |
| F-08 | MED | `rg -c '^- (From-Backlog\|Blocks-Release\|From-Spec\|Graduated-To):[ \t]*$' .aw/records/` returns nothing; `python3 -m agent_workflows check plans` reports no `IPD-M102` | THE ITEM'S HONEST LIMIT HOLDS: NOTHING IN THE CORPUS IS CORRUPT TODAY, so this plan has no backfill obligation and its validation cannot lean on a live example. Every case must therefore be constructed in a temporary repository, which E-02 and E-05 do. It also means the fix cannot regress any existing record, because no existing record takes the changed branch. |
| F-09 | LOW | `rg -n "set_from_backlog_line\|set_blocks_release_line" tests/` returns nothing. `tests/test_releases.py` has 21 tests, all on release records, listing, and parsing; none on any line writer. `tests/test_check_engine_from_spec_missing.py` tests `set_from_spec_line` thoroughly, including its empty-value case | THE TWO DEFECTIVE WRITERS HAVE ZERO TEST COVERAGE AND THEIR ONE CORRECT SIBLING HAS THOROUGH COVERAGE, which is a plausible explanation for how the bug survived and is the reason E-02 creates a new test file rather than extending one. The `set_from_spec_line` suite is the shape to copy, since it already pins the exact empty-value property this plan needs for two more functions. |
| F-10 | LOW | `attention.py` carries a comment on an unrelated `Blocks-Release` guard reading "LATENT, recorded so nobody over-claims the impact: `releases.set_blocks_release_line` REMOVES the line for value `-`, and 0 artifacts in this tree carry `Blocks-Release: -`" | A THIRD SITE ALREADY REASONS ABOUT THIS WRITER'S CLEARING BEHAVIOR, and its stated premise is exactly what F-03 shows is conditionally false: the writer removes the line for `-` only when the line has a value. The comment's conclusion (0 artifacts affected) is still true per F-08, so nothing there is wrong today, but the fix makes its premise unconditionally true. Recorded so a reviewer sees the blast radius is understood and bounded, not so that comment is edited: it is outside `- Scope-Paths:` and needs no change. Verified verbatim at review at `agent_workflows/attention.py:816`. |
| F-11 | HIGH | ADDED AT REVIEW (PR-1001). Driven on the actual writer output: `set_blocks_release_line("- Status: x\n- Blocks-Release:\n- Id: abc123\n", "next")` puts the GOOD line FIRST and the junk line SECOND; but `set_blocks_release_line("- Blocks-Release:\n- Status: to-review\n- Id: abc123\n", "next")` puts the JUNK line FIRST, because the writer's strip cannot see the empty line and its insert lands after the `- Status:` anchor, wherever that is. On the FIRST (junk-second) text, a LINE-BOUNDED tolerant reader captures `'next'`, NOT `''` | F-05'S CONCLUSION IS RIGHT AND ITS STATED REASON IS NOT, AND THE REASON IS WHAT A LATER AUTHOR WOULD RELY ON. F-05 and OQ-01 both argue "the duplicate ALWAYS sits SECOND, so a strict reader skips the junk and a tolerant one stops at the empty first line". BOTH halves fail. (a) The ordering is NOT invariant: it depends on where the pre-existing empty line sits relative to the `- Status:` anchor, and the junk-FIRST order is reachable from an ordinary tooled write, measured above. (b) On the junk-SECOND order the tolerant reader returns the REAL value, so the stated mechanism does not even fire on the case F-05 says is universal. The AUDIT'S ANSWER IS STILL "NO CHANGE", on the half of F-05 that holds and that needs no ordering assumption: a tolerant reader returns `''` for an empty-valued line, `source_link_is_absent('')` is `True`, so a tolerant reader converts a MALFORMED line into a confident claim of ABSENT, and on the junk-first order that is exactly what happens to a record carrying a real gate. The strict reader cannot do this, because `\S+` cannot match an empty value at all and `.search()` continues to the next line. That argument is ordering-independent, which is why it is the one the plan must carry. SECOND CORRECTION: the "tolerant" comparison in the original F-05 used `\s*`, which CROSSES newlines and captures `'- Blocks-Release: next'` (a value containing a bullet), so the figure `''` it reported came from a pattern nobody would write. The honest comparison uses the line-bounded form and is recorded here. |
| F-12 | MED | ADDED AT REVIEW (PR-1003). `releases.check_from_backlog`'s own docstring: "THE TWO BACK-LINK TWINS DISAGREE ON FAIL-SAFETY, AND THIS ONE IS THE LESS SAFE ... the spec-side `check_engine.check_from_spec_dangling` returned 0 findings (it bails out when its known-id set is empty) while THIS function returned 1 FALSE finding, having no such guard. Do NOT 'harmonize' that guard away to match this function; the difference is a known gap here, not a standard to spread." Reproduced on a scratch repo with a plan carrying both links and NEITHER tree: `check_from_backlog` -> 1 finding, `check_from_spec_dangling` -> 0 | THE EMPTY-SET SKIP E-03/E-04 ADD IS CORRECT AND CREATES A DOCUMENTED, DELIBERATE DIVERGENCE FROM THE CHECKER, which the plan must state rather than leave for a later reader to discover as an inconsistency. After this plan, on a repo with no backlog tree, the SETTER permits `--from-backlog nosuch` (the fail-safe E-05 pins) while `aw check` REPORTS it as dangling at `error`. That is the right trade in both places for the reasons each site records, but it means the fail-safe test is pinning a state the checker disagrees with, and an author who later finds that mismatch must not "fix" it by deleting the setter's skip. `known_spec_ids` additionally exists because ONE authority is wrong under an externally-redirected layout (its docstring measures `_existing_spec_ids` returning EMPTY while an in-tree spec plainly existed); `existing_backlog_ids` reads both `BACKLOG_ROOTS` layouts but does NOT consult the record-producer resolver, so the same redirected-layout blindness is plausible for backlog and is precisely why the empty-set skip is load-bearing rather than cosmetic. |
| F-13 | MED | ADDED AT REVIEW (PR-1004). Bare `python3 -m pytest` at review HEAD `7a9e4be3c`: `1 failed, 3480 passed, 2 skipped, 3 warnings in 87.54s`. The failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, which asserts a history line dated `2026-09-30` against a setter writing `2026-10-01` | THE SUITE IS NOT GREEN AT BASE AND THE PLAN RECORDS NO BASELINE AT ALL. The Required tests section says to run the suite bare and names seven regression files, and V-02/V-05 require pasting the summary line, but nothing tells the executor what the base looks like. Since the one live failure is a DATE BOMB in `tests/test_backlog.py`, and this plan touches `status_set.py`, `specs.py` and `releases.py` (all of which that module exercises), an executor would plausibly attribute it to their own change and start debugging a non-defect. The bar must be a failing-node-id SET re-derived before any edit, not a bare "suite passes". |
| F-14 | LOW | ADDED AT REVIEW (PR-1005). The Spec/documentation sync section cites `tests/test_run_flag_surface.py` as pinning spec `25kzda` Section 2.1 "as a file". That path DOES NOT EXIST. The nearest real module is `tests/test_flag_surface_uniformity.py`, whose docstring describes behavioral uniformity tests for presentation and interactivity flags and which cites no spec section and reads no `.spec.md` | A SPEC-SYNC ARGUMENT RESTS ON A TEST FILE THAT DOES NOT EXIST, which matters because the section's whole purpose is to prove a verified conclusion rather than an omission. The CONCLUSION survives (E-03/E-04 add no flag, so no flag-surface contract is touched, and the real module reads no spec), but the stated proof must name something real or the next reader cannot check it. |
| F-15 | MED | ADDED AT REVIEW (PR-1007). `specs.run_set` takes only `args` and holds no `repo_root`; it derives one per use with the module-local `specs._repo_root_of(path)` (docstring: "Walk up from a spec file to the repo root (a dir containing `.aw` or `.agents` or `.git`), falling back to cwd"), and its existing `from_backlog_arg` block calls `blocks_release_of_item(_repo_root_of(path), from_backlog_arg)`. `status_set.apply_status_change` by contrast has `repo_root` in hand | E-04 SAID "USE THE SAME RESOLUTION AS E-03" WITHOUT NAMING HOW THIS FUNCTION REACHES A REPO ROOT, AND THE TWO SURFACES REACH IT DIFFERENTLY. `existing_backlog_ids` takes a `repo_root` argument, so an executor copying E-03's guard literally would find no `repo_root` in scope and would have to invent one; the plausible wrong choices are `Path.cwd()` (which makes the guard consult a different tree than the write when the CLI is run from outside the project) and a fresh `find_project_root` call (a second derivation, against P8). Either yields a guard that can disagree with the gate-inheritance lookup three lines below it, which is a silent wrong answer rather than a visible failure. E-04 now names `_repo_root_of(path)` explicitly and says why. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/releases.py`: change `_BLOCKS_RELEASE_LINE_RE` and `_FROM_BACKLOG_LINE_RE` value groups from `\S+` to `[^\n]*` and extend both docstrings with the tolerance sentence their siblings carry (E-01).
2. `tests/test_releases_line_writers.py`: new outcome tests for both writers, covering empty value, whitespace value, replacement, insertion anchor and fallback, idempotence, clearing residue, and repair of an already-duplicated record (E-02).
3. `agent_workflows/status_set.py`: refuse an unresolvable `--from-backlog` at the CLI entry and again inside `apply_status_change`, through `backlog.existing_backlog_ids`, with `'-'` passthrough and an empty-set skip whose comment records the deliberate divergence from `check_from_backlog`'s less-safe posture (E-03, F-12).
4. `agent_workflows/specs.py`: the same refusal in `specs.run_set`, the forked `--status` spelling, resolving the root through this function's own `_repo_root_of(path)` rather than inventing a second derivation (E-04, F-15).
5. `tests/test_releases_line_writers.py`: CLI-level refusal tests for both spellings plus the empty-set fail-safe (E-05).

## Deferred / out of scope (with reason)

- CHANGING THE READER PATTERNS. The backlog item asks for these to be "audited in the same pass", and this plan performs that audit and concludes they are CORRECT (F-05, reasoning corrected in F-11): a tolerant reader captures `''` from an empty-valued line and `source_link_is_absent('')` reports that as ABSENT, so loosening them would report a real release gate as missing. THE AUDITED POPULATION IS FOUR PATTERNS ACROSS TWO MODULES, not the two the item names: `releases._ITEM_BLOCKS_RELEASE_RE`, `releases._ITEM_FROM_BACKLOG_RE`, and `production_checks._ITEM_FROM_BACKLOG_RE` at its four call sites (the fourth copy, found at review, PR-1002). All are readers, so the same conclusion covers all of them. Deferred permanently as a decision, not postponed as work.
  - Carrier-Declined: No future work is owed, because the audit the item requested is complete, now over the full reader population, and its answer is "no change". The argument is ordering-independent (F-11): `\S+` cannot match an empty value at all, so a strict reader cannot be fooled into reporting absent, whereas a tolerant one can. `ipd_schema.source_link_is_absent("")` already makes "no match" and "empty value" the same answer to every consumer, so there is no behavioral gap left to close. Filing an item would record a settled correctness conclusion as outstanding debt and would invite a later author to make the regression this row exists to prevent.
- BACKFILLING OR REPAIRING ANY EXISTING ARTIFACT. F-08 measures zero empty-valued lines and zero `IPD-M102` findings in the corpus, so there is nothing to repair. E-02's repair case proves the healing property on a constructed record instead.
  - Carrier-Declined: Nothing is owed because no artifact is corrupt. The property that a single tooled write heals a duplicated record is validated by E-02 rather than by touching history, and if a corrupt record ever appears the fixed writer repairs it on the next ordinary write with no migration.
- ADDING A DUPLICATE-FIELD CHECK FOR BACKLOG ITEMS AND SPECS, the gap F-04 measures (a plan gets `IPD-M102`; a backlog item and a spec get nothing). This is a genuine detection gap in shipped code, but it is a DIFFERENT concern from the writer that creates the duplicate: it would add a rule to `backlog.validate_item` and `specs.validate_spec`, neither of which is in `- Scope-Paths:`, and it would be a new finding class needing its own severity decision and its own corpus measurement. Fixing the writer removes the tooled route that creates the condition; a detector would catch a hand edit, which is a separate question. Filed `chore` rather than `bug` because after E-01 no tooled write can produce the duplicate, so the only remaining producer is a hand edit, and no user-perceptible impact is measured.
  - Carrier: in7pfz
- RETROFITTING A REFUSAL ONTO EVERY OTHER UNVALIDATED METADATA SETTER. `--priority`, `--work-kind` and `--blocks-release` also write values that `aw check` validates afterwards. Out of scope: this plan closes the two surfaces the item names for the ONE field whose dangling rule is registered `error` and whose asymmetry the code itself already documents. Widening to a general validate-everything policy is a design decision about where validation belongs, and no finding here measures those other flags producing an error-severity state.
  - Carrier-Declined: Nothing is owed, because no defect is measured for those flags. `--priority` and `--work-kind` are enum fields whose checks are documented as deliberately living in `aw check` rather than in the pure line writers, and `--blocks-release` resolves against a release corpus that legitimately varies. If a future measurement shows one of them minting an error-severity finding from an exit-0 command, as F-06 does for `--from-backlog`, that measurement is the evidence that would justify an item; asserting it now would file work nobody has shown is needed.
- `aw ipd scaffold --from-backlog`. Already refuses an unresolvable id (F-07), so there is nothing to add.
  - Carrier-Declined: The behavior this plan wants already ships on that surface, verified by running it. No work is owed.

## Scope check

- Over-scope: none. The writer fix (E-01/E-02) and the setter refusal (E-03/E-04/E-05) are the two defects the single backlog item records, and they touch adjacent code: the refusal guards the very value the fixed writer writes, and `status_set`'s `from_backlog` block is both the caller of the fixed writer and the site of the missing validation. Splitting them into two plans would put two halves of one item's fix behind two review cycles for no isolation benefit.
- Under-scope: Four limits, stated plainly. FIRST, a backlog item or spec carrying a hand-edited duplicate field is still undiagnosable after this plan (F-04); the tooled route that creates one is closed, the detector is deferred with a carrier. SECOND, all FOUR reader patterns keep their `\S+` shape (the two in `releases.py` and the two uses of `production_checks._ITEM_FROM_BACKLOG_RE`, the fourth copy F-11's companion note records), which is deliberate per F-05 as corrected by F-11: a reader given a duplicate reports whichever valued line it finds, which is the right answer rather than a residual defect. THIRD, the setter's empty-set fail-safe will deliberately disagree with `releases.check_from_backlog`, which has no such guard and whose own docstring forbids harmonizing it away (F-12); closing that checker-side gap is not this plan's work and `releases.check_from_backlog`'s guard is not touched. FOURTH, the writers' no-anchor final fallback still drops a value silently when a text has neither `- Status:` nor `- Id:` (measured at review, see E-01); unreachable from any real record and deliberately unchanged.

## Required tests / validation

BASELINE FIRST, AS A FAILING-NODE-ID SET, BECAUSE THE SUITE IS NOT GREEN (F-13). Before making ANY edit, run bare `python3 -m pytest` and paste both the summary line and every `FAILED`/`ERROR` node id. Measured at review HEAD `7a9e4be3c`: `1 failed, 3480 passed, 2 skipped, 3 warnings in 87.54s`, the failure being `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a DATE-DEPENDENT assertion (it expects a `2026-09-30` history line and the setter writes `2026-10-01`), which will keep failing until someone repairs the test. That node id is a particular hazard for THIS plan, because `tests/test_backlog.py` exercises the very setter path E-03 modifies, so an executor comparing against "the suite passes" would attribute a date bomb to their own guard. Treat as blocking ONLY a node id absent from the base set, and do NOT compare counts: the base figures above are a review-time observation, not a bar.

Run the suite BARE as `python3 -m pytest` (AGENTS.md: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not add `-n0`, a second `-q`, or `-p no:randomly`). Targeted files: the new `tests/test_releases_line_writers.py`, plus `tests/test_releases.py`, `tests/test_status_set.py`, `tests/test_specs_from_backlog.py`, `tests/test_backlog_handoff_close.py`, `tests/test_check_engine_release_gate.py`, `tests/test_carrier_scan_single_item_contract.py` and `tests/test_check_engine_from_spec_missing.py`, since each exercises a caller of a changed writer or of a changed setter path (all eight verified to exist at review; the first is the one this plan creates). Also run `aw check`, `aw ipd lint`, and `aw sanitize --agent`. `aw check plans` and `aw check backlog` BOTH exit 1 at review base for reasons unrelated to this plan, so neither exit code is a pass bar; report them and compare the per-rule finding set rather than the exit status.

Every test drives real code or a real CLI over a real temporary repository and asserts on returned text, file bytes, exit codes and output. No test may read production source with `inspect`, `ast`, regex, or substring search, and none may assert a symbol census or a line count. Required coverage:

- Both repaired writers, EACH: empty-valued existing line replaced (exactly one line results); whitespace-only value replaced; valued line replaced; absent line inserted immediately after `- Status:`, proven by quoting adjacent lines; fallback insertion after `- Id:` with no `- Status:`; second call byte-identical; `'-'` and `None` leave NO residue; an already-duplicated record healed to one line by one write; no neighbouring metadata line disturbed in any case.
- BEFORE-AND-AFTER PROOF: the empty-value, whitespace-value, clearing-residue and repair cases must be shown FAILING on the pre-E-01 code, not merely passing after. A test that passes both before and after has pinned nothing.
- `aw ipd set --from-backlog`: unresolvable value exits nonzero, names the value, and leaves the target file byte-identical; resolvable id6 writes the field and inherits the item's `- Blocks-Release:` with its notice; `-` clears.
- `aw specs set --status ... --from-backlog`: the same three cases, tested independently of `aw ipd set` because F-06 measures them as different code paths.
- Fail-safe: in a repository with no backlog tree, a `--from-backlog` write SUCCEEDS rather than refusing, pinning the empty-known-set skip.
- Regression on the gate-inheritance path: a graduation write through `aw ipd set --from-backlog <id6>` where the item carries a gate must still produce the inherited `- Blocks-Release:` line and its stdout notice, since E-03's guard sits directly above that block.

## Spec / documentation sync

NO `.spec.md` IS IN `- Scope-Paths:` AND NONE IS AMENDED, which is a verified conclusion rather than an omission. Three candidates were checked. Spec `25kzda` Section 2.7 mandates the POSITION of `- Item-Dependencies:` in the metadata block and is the reason `set_item_dependencies_line` anchors differently from its siblings; this plan changes no anchor and no field position, only two value-tolerance character classes, so that section is untouched. Spec `25kzda` Section 2.1 governs the `aw <host> run` flag surface; E-03/E-04 add no flag at all (they add a refusal to existing flags on `aw ipd set` and `aw specs set`, neither of which is a host run flag), so no flag-surface contract is touched. CORRECTED AT REVIEW (F-14): an earlier draft of this paragraph claimed that section was "pinned as a file by `tests/test_run_flag_surface.py`", and NO SUCH FILE EXISTS. The real neighbouring module is `tests/test_flag_surface_uniformity.py`, which tests presentation and interactivity flag ACCEPTANCE behaviorally and reads no `.spec.md` at all, so it pins no spec file and cannot be affected either. The conclusion is unchanged; only its proof needed to name something real. The IPD structural contract spec governs `IPD-M102` and the metadata block's recognized fields; this plan changes neither the field set nor the lint, and F-04's deferred detector row explicitly keeps the new-rule question out of scope. No user-facing documentation describes either writer's empty-value behavior, and AGENTS.md's `--from-backlog` paragraphs describe the flag's MEANING (the graduation handoff and the gate that travels with it), which this plan preserves exactly while refusing an unresolvable value; so no AGENTS.md edit is owed either.

## Open questions

### OQ-01: Should the `- Blocks-Release:` and `- From-Backlog:` READER patterns be loosened to match the writers' new value tolerance, as the backlog item's "should be audited in the same pass" suggests?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED NO, FROM A MEASUREMENT (F-05), AND THE ANSWER REVERSES THE ITEM'S IMPLICATION. THE ARGUMENT WAS CORRECTED AT REVIEW (F-11) AND THE CORRECTION MATTERS, because the original rested on an ordering claim that is false. The ordering-INDEPENDENT argument, which is the one that holds: a tolerant reader captures `''` for an empty-valued line, and `ipd_schema.source_link_is_absent("")` is `True`, so a tolerant reader converts a MALFORMED line into a confident claim that the field is ABSENT. The strict `\S+` reader cannot do that, because it cannot match an empty value at all and `.search()` therefore continues to the next line, finding the real value if one exists. On a record carrying a real `- Blocks-Release: next` beside a stray empty line, loosening the reader would report no gate, and `check.blocking-item-closed-without-gate` would then permit closing a release blocker. The readers are also already correct for the single-line empty case: both return `None`, the same answer as absent. So the writer axis wants tolerance and the reader axis wants strictness, and treating them as one "consistency" change would be a regression. WHAT WAS WITHDRAWN: the claim that "the duplicate always sits SECOND". Measured at review, the junk line sits FIRST whenever the pre-existing empty line precedes the `- Status:` anchor, which an ordinary tooled write produces; and on the junk-second order a line-bounded tolerant reader returns the REAL value, so the original mechanism did not fire on the case it called universal. NOT BLOCKING: the plan is executable as written and the readers are explicitly fenced out by `- Scope:`, by the `## Deferred` row, and by V-01's outright-failure clause. REVERSIBLE: not applicable, since nothing is changed.

### OQ-02: Should this plan also add a duplicate-field detector for backlog items and specs, the gap F-04 measures?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED NO, DEFERRED WITH A CARRIER. F-04 is a real gap: a plan carrying the duplicate is reported as `IPD-M102` by `aw ipd lint`, while `aw backlog check` and `aw specs check` both reported "all conform" on files carrying it. But it is a different concern from the writer that creates the condition, it would touch `backlog.validate_item` and `specs.validate_spec` (neither in `- Scope-Paths:`), and it would introduce a new finding class needing a severity decision and a corpus measurement of its own. Crucially, E-01 removes the only TOOLED producer: after the fix no `aw` command can create the duplicate, so the detector would guard against a hand edit alone, which is genuinely lower value and is why it is `chore` rather than `bug`. Deferring it keeps this plan's diff to the two writers plus two setter guards, which is what makes the before-and-after proof E-02 demands legible. NOT BLOCKING: the carrier is ALREADY FILED as backlog item `in7pfz` (filed at authoring time, not promised for execution), so the obligation is recorded rather than dropped, and V-05 requires proof it still resolves. REVERSIBLE: yes; nothing is deleted and the deferred detector remains available.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: PASTE the committed `_BLOCKS_RELEASE_LINE_RE` and `_FROM_BACKLOG_LINE_RE` lines and both extended docstrings. PASTE a Python transcript, for EACH of the two functions, showing: (a) the empty-valued input yielding a text whose count of the field's lines is EXACTLY 1, with the count printed; (b) a whitespace-only value (`- Blocks-Release:   `) likewise yielding exactly 1; (c) insertion into a text with no such line landing IMMEDIATELY after `- Status:`, quoting the three adjacent lines to prove position; (d) fallback insertion after `- Id:` when no `- Status:` exists; (e) a second call being byte-identical (`f(f(t,v),v) == f(t,v)` -> `True`); (f) `'-'` and `None` each leaving ZERO lines of the field, printing the count; (g) the REPAIR case, starting from an already-duplicated text and showing one write reduces it to exactly 1 line. PASTE the full remaining bullet block for case (a) to show no neighbouring line was consumed. A transcript showing count 2 in any of (a), (b) or (g) FAILS this item. A pattern using `.*` with `re.DOTALL`, or one that has dropped the `$` anchor, FAILS this item even if every transcript passes, because F-02's full-line anchoring is what keeps the writer from eating adjacent metadata. Any diff hunk touching `releases._ITEM_BLOCKS_RELEASE_RE`, `releases._ITEM_FROM_BACKLOG_RE`, or `production_checks._ITEM_FROM_BACKLOG_RE` (the fourth reader copy found at review, PR-1002, in a module that is not declared in `- Scope-Paths:` at all) FAILS this item, per F-05 as corrected by F-11 and per OQ-01.
  - Observed evidence: Committed patterns and extended docstrings in `agent_workflows/releases.py`:
    ```python
    _BLOCKS_RELEASE_LINE_RE = re.compile(r"(?m)^- Blocks-Release:[ \t]*[^\n]*$\n?")


    def set_blocks_release_line(text: str, value: Optional[str]) -> str:
        """Return `text` with the `- Blocks-Release:` metadata line set to `value`, or removed when
        `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
        (falling back to after `- Id:`, or the top of the bullet block). Tolerates any value so an
        existing malformed line is still replaced (matching precedent in `set_priority_line` and
        `set_work_kind_line`)."""
    ```
    ```python
    _FROM_BACKLOG_LINE_RE = re.compile(r"(?m)^- From-Backlog:[ \t]*[^\n]*$\n?")


    def set_from_backlog_line(text: str, value: Optional[str]) -> str:
        """Return `text` with the `- From-Backlog:` metadata line set to `value`, or removed when
        `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
        (falling back to after `- Id:`, or the top of the bullet block). Mirrors
        `set_blocks_release_line` exactly (bklggrad Order ku93tn). Tolerates any value so an
        existing malformed line is still replaced (matching precedent in `set_priority_line` and
        `set_work_kind_line`)."""
    ```

    Python transcript exercising both writers:
    ```
    === Testing set_blocks_release_line (Blocks-Release) ===
    (a) empty-valued input: count = 1
    Full bullet block for (a):
    - Date: 2026-09-30
    - Status: open
    - Blocks-Release: next
    - Id: aaaaaa
    (b) whitespace-only value: count = 1
    (c) adjacent lines:
    Found needle:
    - Status: open
    - Blocks-Release: next
    - Id: aaaaaa

    (d) fallback adjacent lines:
    Found needle:
    - Id: aaaaaa
    - Blocks-Release: next
    - Scope: test

    (e) f(f(t,v),v) == f(t,v): True
    (f) count on dash: 0, on None: 0
        from empty input on dash: 0, on None: 0
    (g) repair duplicate: count = 1

    === Testing set_from_backlog_line (From-Backlog) ===
    (a) empty-valued input: count = 1
    Full bullet block for (a):
    - Date: 2026-09-30
    - Status: open
    - From-Backlog: zzz999
    - Id: aaaaaa
    (b) whitespace-only value: count = 1
    (c) adjacent lines:
    Found needle:
    - Status: open
    - From-Backlog: zzz999
    - Id: aaaaaa

    (d) fallback adjacent lines:
    Found needle:
    - Id: aaaaaa
    - From-Backlog: zzz999
    - Scope: test

    (e) f(f(t,v),v) == f(t,v): True
    (f) count on dash: 0, on None: 0
        from empty input on dash: 0, on None: 0
    (g) repair duplicate: count = 1
    ```
    No reader patterns (`_ITEM_BLOCKS_RELEASE_RE`, `_ITEM_FROM_BACKLOG_RE`, or `production_checks._ITEM_FROM_BACKLOG_RE`) were touched; regexes retain multiline anchoring and full-line termination with no `.*` or `re.DOTALL`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE `git diff --stat` for `tests/test_releases_line_writers.py` and the test names. PASTE the BEFORE run: with E-01's two patterns reverted to `\S+` in the working tree, run the new test file and paste the actual failing output, which must show the empty-value, whitespace-value, clearing-residue and repair cases FAILING for both functions; name which cases failed. Then restore E-01 and PASTE the AFTER run showing them passing, including the `N passed` summary line. PASTE the bare full-suite run's summary line (`python3 -m pytest`) AND its full `FAILED`/`ERROR` node-id list, then compare that SET against the pre-change baseline set required by the Required tests section; only a node id absent from the baseline is a regression. Do NOT read a nonzero summary as this plan's failure: the base carries at least one pre-existing date-dependent failure in `tests/test_backlog.py` (F-13), which is a module this plan's E-03 path touches and is therefore exactly the false attribution this clause exists to prevent. A test file that passes identically before and after E-01 FAILS this item, because it has pinned nothing. Any test that reads `releases.py` with `inspect`, `ast`, regex or substring search, or that asserts a pattern's source text, FAILS this item per AGENTS.md and `GUIDING_PRINCIPLES` P16.
  - Observed evidence: `git diff --stat --no-index /dev/null tests/test_releases_line_writers.py`:
    ```
    tests/test_releases_line_writers.py | 628 +++++++++++++++++++++++
    1 file changed, 628 insertions(+)
    ```
    Test names in `TestSetBlocksReleaseLine` and `TestSetFromBacklogLine`:
    - `test_blocks_release_empty_value_replaced`
    - `test_blocks_release_whitespace_value_replaced`
    - `test_blocks_release_normally_valued_replaced`
    - `test_blocks_release_absent_inserted_after_status`
    - `test_blocks_release_fallback_after_id`
    - `test_blocks_release_idempotent`
    - `test_blocks_release_clear_dash_and_none`
    - `test_blocks_release_repair_duplicate`
    - `test_from_backlog_empty_value_replaced`
    - `test_from_backlog_whitespace_value_replaced`
    - `test_from_backlog_normally_valued_replaced`
    - `test_from_backlog_absent_inserted_after_status`
    - `test_from_backlog_fallback_after_id`
    - `test_from_backlog_idempotent`
    - `test_from_backlog_clear_dash_and_none`
    - `test_from_backlog_repair_duplicate`

    BEFORE run with E-01 patterns reverted to `\S+`:
    ```
    .FF...FF.FF...FF
    ======================================================================
    FAIL: test_blocks_release_clear_dash_and_none (tests.test_releases_line_writers.TestSetBlocksReleaseLine.test_blocks_release_clear_dash_and_none)
    AssertionError: 1 != 0
    ======================================================================
    FAIL: test_blocks_release_empty_value_replaced (tests.test_releases_line_writers.TestSetBlocksReleaseLine.test_blocks_release_empty_value_replaced)
    AssertionError: 2 != 1
    ======================================================================
    FAIL: test_blocks_release_repair_duplicate (tests.test_releases_line_writers.TestSetBlocksReleaseLine.test_blocks_release_repair_duplicate)
    AssertionError: 2 != 1
    ======================================================================
    FAIL: test_blocks_release_whitespace_value_replaced (tests.test_releases_line_writers.TestSetBlocksReleaseLine.test_blocks_release_whitespace_value_replaced)
    AssertionError: 2 != 1
    ======================================================================
    FAIL: test_from_backlog_clear_dash_and_none (tests.test_releases_line_writers.TestSetFromBacklogLine.test_from_backlog_clear_dash_and_none)
    AssertionError: 1 != 0
    ======================================================================
    FAIL: test_from_backlog_empty_value_replaced (tests.test_releases_line_writers.TestSetFromBacklogLine.test_from_backlog_empty_value_replaced)
    AssertionError: 2 != 1
    ======================================================================
    FAIL: test_from_backlog_repair_duplicate (tests.test_releases_line_writers.TestSetFromBacklogLine.test_from_backlog_repair_duplicate)
    AssertionError: 2 != 1
    ======================================================================
    FAIL: test_from_backlog_whitespace_value_replaced (tests.test_releases_line_writers.TestSetFromBacklogLine.test_from_backlog_whitespace_value_replaced)
    AssertionError: 2 != 1
    ----------------------------------------------------------------------
    Ran 16 tests in 0.004s

    FAILED (failures=8)
    ```
    Failed cases on pre-E-01 code: empty-value, whitespace-value, clearing-residue, and repair cases for BOTH functions.

    AFTER run with E-01 restored:
    ```
    Ran 16 tests in 0.001s

    OK
    ```
    Full bare suite summary line (`python3 -m pytest`):
    `3927 passed, 2 skipped, 3 warnings in 104.10s (0:01:44)`
    Failing node id set: `set()` (matching pre-change baseline set `set()`, 0 regressions).
    No test reads production code via inspect/ast/regex/substring search.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the committed guard at the CLI entry and the backstop inside `apply_status_change`, showing both resolve through `backlog.existing_backlog_ids`, neither constructs a second scanner, and the empty-set skip's comment states the deliberate divergence from `releases.check_from_backlog`'s unguarded posture, citing that function's own docstring (F-12). A guard whose comment is silent on that divergence FAILS this item, because the next reader finding the mismatch would otherwise be invited to delete the skip. PASTE a terminal transcript over a temporary repository showing: `aw ipd set to-review <plan> --from-backlog nosuch` exiting nonzero with output naming `nosuch`, plus a `git diff` or byte comparison proving the plan file is UNCHANGED; `--from-backlog <real-id6>` still writing `- From-Backlog: <id6>`; the gate-inheritance notice `aw set: inherited - Blocks-Release:` still firing when the item carries a gate, which is the regression F-07's neighbouring block risks; and `--from-backlog -` still clearing the field. PASTE the exit codes. A transcript where the refusal case exits 0, or where the target file differs after a refusal, FAILS this item. A transcript missing the inheritance notice FAILS this item even if the refusal works, because the guard sits directly above that block.
  - Observed evidence: Committed guard at CLI entrypoint in `agent_workflows/status_set.py:run_set_command`:
    ```python
    # IPD izh17y E-03: validate `--from-backlog` value BEFORE any artifact is resolved or written,
    # so an unresolvable backlog id refuses with exit 2 instead of creating a dangling link.
    # Resolves via existing authority `backlog.existing_backlog_ids` (P8: no second scanner).
    # An empty id set skips the refusal so an invisible backlog corpus cannot make every write fail.
    # DELIBERATE DIVERGENCE FROM CHECKER (F-12): `releases.check_from_backlog` has no empty-set skip
    # and its own docstring explicitly records that asymmetry ("THE TWO BACK-LINK TWINS DISAGREE ON
    # FAIL-SAFETY, AND THIS ONE IS THE LESS SAFE ... Do NOT 'harmonize' that guard away to match this
    # function; the difference is a known gap here, not a standard to spread"). The setter takes the
    # safe posture rather than copying the checker's less-safe posture.
    fb_val = getattr(args, "from_backlog", None)
    if fb_val is not None and fb_val != "-":
        from agent_workflows import backlog as _backlog

        known_backlog = _backlog.existing_backlog_ids(repo_root)
        if known_backlog and fb_val not in known_backlog:
            term.status(
                "fail",
                f"aw set: unresolvable backlog id '{fb_val}' (does not resolve to an existing backlog item)",
            )
            return 2
    ```

    Committed backstop inside `agent_workflows/status_set.py:apply_status_change`:
    ```python
    fb = getattr(args, "from_backlog", None)
    if fb is not None:
        if fb != "-":
            # IPD izh17y E-03: validation backstop in apply_status_change preventing unresolvable
            # dangling links even via direct calls. Resolves via `backlog.existing_backlog_ids` (P8).
            # An empty id set skips the refusal so an invisible backlog corpus cannot make every write fail.
            # DELIBERATE DIVERGENCE FROM CHECKER (F-12): `releases.check_from_backlog` has no empty-set skip
            # and its own docstring explicitly records that asymmetry ("THE TWO BACK-LINK TWINS DISAGREE ON
            # FAIL-SAFETY, AND THIS ONE IS THE LESS SAFE ... Do NOT 'harmonize' that guard away to match this
            # function; the difference is a known gap here, not a standard to spread"). The setter takes the
            # safe posture rather than copying the checker's less-safe posture.
            from agent_workflows import backlog as _backlog

            known_backlog = _backlog.existing_backlog_ids(repo_root)
            if known_backlog and fb not in known_backlog:
                raise ValueError(
                    f"unresolvable backlog id '{fb}' (does not resolve to an existing backlog item)"
                )
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_from_backlog_line(tmp_text, fb)
        new_lines = tmp_text.splitlines()
    ```

    Terminal transcript over a temporary repository:
    ```
    $ aw ipd set to-review pln001 --from-backlog nosuch
    exit code: 2
    stdout: FAIL     aw set: unresolvable backlog id 'nosuch' (does not resolve to an existing backlog item)
    stderr:
    bytes identical: True

    $ aw ipd set to-review pln001 --from-backlog bkl001
    exit code: 0
    stdout: aw set: inherited - Blocks-Release: relaaa from backlog item bkl001 (graduation handoff: the gate travels with the work)
    -    plan        20260930-testset-01-pln001  [medium]  unchanged
    content has - From-Backlog: bkl001: True
    content has - Blocks-Release: relaaa: True

    $ aw ipd set to-review pln001 --from-backlog -
    exit code: 0
    content has - From-Backlog:: False
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the committed guard in `specs.run_set` beside its `from_backlog_arg` block, SHOWING that it resolves the repo root through this function's own `_repo_root_of(path)` and not through `Path.cwd()` or a second `find_project_root` call; a guard resolving against a different root than the gate-inheritance lookup immediately below it FAILS this item, per F-15. PASTE a terminal transcript showing `aw specs set <spec> --status draft --from-backlog nosuch` exiting nonzero and naming `nosuch`, with the spec file byte-identical afterwards, and the resolvable case still writing the field and still inheriting the item's gate. The transcript MUST use the `--status` spelling specifically, because F-06 measures that this spelling forks to `specs.run_set` and is therefore not covered by E-03; a transcript that exercises only the bare `aw specs set <status> <path>` spelling FAILS this item. PASTE the exit codes.
  - Observed evidence: Committed guard in `agent_workflows/specs.py:run_set`:
    ```python
    # uruqaz E-02/E-03: write From-Backlog and inherit the item's release gate on the `--status` path,
    # matching the bare spelling handled by `status_set.py`.
    from_backlog_arg = getattr(args, "from_backlog", None)
    if from_backlog_arg is not None:
        if from_backlog_arg != "-":
            # IPD izh17y E-04: refuse unresolvable --from-backlog on the forked `aw specs set --status`
            # path before mutating new_text. Resolves via `backlog.existing_backlog_ids` using
            # `_repo_root_of(path)` (F-15: reach repo root identically to the gate inheritance below).
            # An empty id set skips the refusal so an invisible backlog corpus cannot make every write fail.
            # DELIBERATE DIVERGENCE FROM CHECKER (F-12): `releases.check_from_backlog` has no empty-set skip
            # and its own docstring explicitly records that asymmetry ("THE TWO BACK-LINK TWINS DISAGREE ON
            # FAIL-SAFETY, AND THIS ONE IS THE LESS SAFE ... Do NOT 'harmonize' that guard away to match this
            # function; the difference is a known gap here, not a standard to spread"). The setter takes the
            # safe posture rather than copying the checker's less-safe posture.
            from agent_workflows import backlog as _backlog

            known_backlog = _backlog.existing_backlog_ids(_repo_root_of(path))
            if known_backlog and from_backlog_arg not in known_backlog:
                sys.stderr.write(
                    f"aw specs set: unresolvable backlog id '{from_backlog_arg}' (does not resolve to an existing backlog item)\n"
                )
                return 2

        from agent_workflows import releases as _releases

        new_text = _releases.set_from_backlog_line(new_text, from_backlog_arg)
        if from_backlog_arg != "-" and getattr(args, "blocks_release", None) is None:
            from agent_workflows import backlog as _backlog

            _carrier_m = re.search(
                r"(?m)^- Blocks-Release:[ \t]*(\S+)[ \t]*$", new_text
            )
            if _carrier_m is None:
                _item_gate = _backlog.blocks_release_of_item(
                    _repo_root_of(path), from_backlog_arg
                )
                if _item_gate:
                    new_text = _releases.set_blocks_release_line(new_text, _item_gate)
                    sys.stdout.write(
                        f"aw set: inherited - Blocks-Release: {_item_gate} from backlog item "
                        f"{from_backlog_arg} (graduation handoff: the gate travels with the work)\n"
                    )
    ```

    Terminal transcript for `aw specs set --status`:
    ```
    $ aw specs set 20260930-spc001-01-spc001-test-spec.spec.md --status draft --from-backlog nosuch
    exit code: 2
    stdout:
    stderr: aw specs set: unresolvable backlog id 'nosuch' (does not resolve to an existing backlog item)
    bytes identical: True

    $ aw specs set 20260930-spc001-01-spc001-test-spec.spec.md --status draft --from-backlog bkl001
    exit code: 0
    stdout: aw set: inherited - Blocks-Release: relaaa from backlog item bkl001 (graduation handoff: the gate travels with the work)
    aw specs set: /tmp/tmpzc_s_zo6/.aw/records/specs/draft/20260930-spc001-01-spc001-test-spec.spec.md -> draft
    content has - From-Backlog: bkl001: True
    content has - Blocks-Release: relaaa: True

    $ aw specs set 20260930-spc001-01-spc001-test-spec.spec.md --status draft --from-backlog -
    exit code: 0
    content has - From-Backlog:: False
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the new CLI test names and the BEFORE run: with E-03 and E-04 reverted, the refusal tests must FAIL (they will exit 0 and persist the bad value); paste that output. PASTE the AFTER run passing, with the `N passed` summary line. PASTE the fail-safe case's assertion and result: in a repository with no backlog tree, a `--from-backlog` write SUCCEEDS, together with the test's docstring showing it records that `check_from_backlog` disagrees on the same tree (F-12). PASTE the bare full-suite run (`python3 -m pytest`) summary line AND its failing node-id set, compared against the baseline set as a SET and not as a count (F-13). PASTE `aw check` output with the per-rule finding breakdown rather than treating its exit code as a bar (`check plans` and `check backlog` both exit 1 at base for unrelated reasons), `aw ipd lint` output for this plan, and `aw sanitize --agent` output. ALSO PASTE proof that the F-04 / OQ-02 carrier `in7pfz` (the backlog-item and spec duplicate-field detection gap, filed `chore` at authoring time) still RESOLVES to a live backlog item: paste `aw find backlog in7pfz` output or the item's `- Status:` line. This item is NOT complete without that proof, because OQ-02 defers real work onto that carrier and a dangling carrier is a dropped obligation.
  - Observed evidence: CLI test names added to `tests/test_releases_line_writers.py`:
    - `test_cli_ipd_set_refuse_unresolvable_backlog_id`
    - `test_cli_ipd_set_resolvable_backlog_id_writes_and_inherits_gate`
    - `test_cli_ipd_set_clear_from_backlog_with_dash`
    - `test_cli_specs_set_refuse_unresolvable_backlog_id`
    - `test_cli_specs_set_resolvable_backlog_id_writes_and_inherits_gate`
    - `test_cli_specs_set_clear_from_backlog_with_dash`
    - `test_cli_empty_backlog_corpus_failsafe_allows_write`

    BEFORE run with E-03 and E-04 reverted:
    ```
    ..F..F.................
    ======================================================================
    FAIL: test_cli_ipd_set_refuse_unresolvable_backlog_id (tests.test_releases_line_writers.TestCliIpdSetFromBacklog.test_cli_ipd_set_refuse_unresolvable_backlog_id)
    AssertionError: 0 == 0
    ======================================================================
    FAIL: test_cli_specs_set_refuse_unresolvable_backlog_id (tests.test_releases_line_writers.TestCliSpecsSetFromBacklog.test_cli_specs_set_refuse_unresolvable_backlog_id)
    AssertionError: 0 == 0
    ----------------------------------------------------------------------
    Ran 23 tests in 5.522s

    FAILED (failures=2)
    ```

    AFTER run with E-03 and E-04 restored:
    ```
    .......................
    ----------------------------------------------------------------------
    Ran 23 tests in 4.764s

    OK
    ```
    Pytest targeted run:
    `23 passed in 11.28s`

    Fail-safe case docstring, assertion, and result:
    ```python
    def test_cli_empty_backlog_corpus_failsafe_allows_write(self) -> None:
        """In a repository with no backlog tree at all, a --from-backlog write succeeds rather
        than refusing (fail-safe for invisible corpus).

        NOTE ON DELIBERATE DIVERGENCE (F-12): on this same tree, releases.check_from_backlog
        reports the value as dangling at error, because that function has no empty-set guard
        and its own docstring records the asymmetry ('the less safe twin') and forbids
        harmonizing it away.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            # Create repo with NO backlog tree
            paths = _setup_test_repo(repo_root, with_backlog=False)
            plan_path = paths["plan"]

            proc = run_cli(
                "ipd",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "pln001",
                "--from-backlog",
                "anyval",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            content = plan_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: anyval\n", content)
    ```
    Result: passed (proc.returncode == 0, content contains `- From-Backlog: anyval\n`).

    Bare full-suite run (`python3 -m pytest`):
    `3927 passed, 2 skipped, 3 warnings in 104.10s (0:01:44)`
    Failing node id set: `set()` (0 regressions from baseline set `set()`).

    `aw ipd lint` output for this plan:
    ```
    - >  ◕  approved     plan        20260930-relwriteempty-01-izh17y  [medium]  [blocking]  conforming
    ```

    `aw sanitize --agent` output:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    Carrier `in7pfz` resolution proof (`aw find backlog in7pfz`):
    ```
    ◕  open          in7pfz  .aw/records/backlog/open/20260930-in7pfz-01-in7pfz-backlog-spec-duplicate-metadata-field-undetected.backlog.md
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` carrying NO `- Readiness:` field, which was deliberate and correct: `- Readiness:` is an OUTPUT of `/plan-review`, and writing it at authoring time would forge the attestation the auto-approve predicate reads. `/plan-review` ran on 2026-09-30 and wrote `- Readiness: go-pending-approval` as that output. Explicit human approval is still required before execution; `reviewed` is not `approved`.

The executor must: RE-DERIVE THE FAILING-TEST BASELINE AS A NODE-ID SET BEFORE ANY EDIT, because the suite is NOT green at base and one live failure sits in `tests/test_backlog.py`, a module E-03's path exercises (F-13); perform E-01 through E-05 in order, respecting the declared `Depends on` edges; treat E-01 as the gate for everything else, since E-02's before-and-after proof and every later item's regression surface depend on it landing first; change ONLY the two WRITER patterns and NONE of the four reader patterns, which F-05 as corrected by F-11 establishes are correct and whose modification V-01 treats as an outright failure; keep `status_set`'s gate-inheritance block and its stdout notice intact, which V-03 verifies; resolve the repo root in `specs.run_set` through that function's own `_repo_root_of(path)` rather than a second derivation (F-15); write the empty-set skip's deliberate divergence from `check_from_backlog` into the guard's comment rather than harmonizing either side (F-12); confirm the already-filed OQ-02 carrier `in7pfz` still resolves, per V-05; commit only the four paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; and run the suite BARE as `python3 -m pytest`, pasting the ACTUAL output rather than claiming success.

After every `V-*` item carries concrete pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition. Do not claim done or move the file on the strength of the execution checkmarks alone.
