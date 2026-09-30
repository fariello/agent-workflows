# IPD: Print each unmet dependency's reason once by stripping the reason's self-referential token prefix at the renderers

- Date: 2026-09-30
- Kind: child
- Concern: Every dependency-block surface prints the dependency token TWICE on one line, because `runner_shared.edge_satisfied` composes each refusal as `f"{tok}: ..."` and all four downstream surfaces then re-compose that already-prefixed string as `<token> (<reason>)` or `- <token>: <reason>`.
- Scope: IN: (a) ONE shared, pure de-duplication helper in `run_selection_policy` that removes a reason's leading self-reference to its own token (or to that token's bare target id6) and is a no-op otherwise; (b) its application at the FOUR render sites that compose token-plus-reason (`render_stream.render_run_summary_table`'s diagnostics block, `runner_shared.write_report`'s `## Dependency blocks (why)` section, `runner_shared.render_transient_dependency_waits`, and `run_selection_policy.derive_item_disposition`'s `unmet:` clause); (c) behavioral tests over every reason SHAPE the three live producers emit. OUT: changing any reason string a producer WRITES (so the durable `events.jsonl` `reasons` map stays byte-identical and `derive_item_disposition`'s substring-matched code selector keeps its input), changing any disposition CODE or gloss (spec `25kzda` 5.4 owns those names), and the two adjacent defects `8mohre` (in-queue edge mislabelled `external`, owned by pending `zhqt51`) and the missing recovery hint (owned by pending `8eei5p`).
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/render_stream.py, agent_workflows/runner_shared.py, tests/test_dependency_block_reporting.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: csjq81
- Set: csjq81
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: p22nrx

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `csjq81`. Every finding measured at HEAD `62b18f47` by CALLING the real functions, and the prescribed fix prototyped in the tree and run against the suite before being written down (the prototype was reverted; `git status` is clean).

## Goal

Make each dependency-block line name its unmet edge ONCE. Today an operator reads

```text
• eee555: fail-depend (executed:5j7jv1 (executed:5j7jv1: external target 5j7jv1 is 'reviewed' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)))
```

where the token `executed:5j7jv1` appears twice and the line carries four nested parentheses. The
information is correct and singular, which is why backlog `csjq81` is `chore` and not `bug`; it is the
SCANNABILITY that fails.

The fix is deliberately at the RENDERERS and not at the producer, and that choice is the whole design.
Stripping the prefix inside `edge_satisfied` would change (a) the `reasons` map already frozen in many
run directories' `events.jsonl`, and (b) the input to `run_selection_policy.derive_item_disposition`,
which picks between two spec-named disposition codes by SUBSTRING-MATCHING that prose. Both are
avoided entirely by fixing the composition instead of the string.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared predicate, in the pure policy module

- [ ] E-01 Add ONE pure public helper to `agent_workflows/run_selection_policy.py` that takes a dependency token and a reason string and returns the reason with a LEADING SELF-REFERENCE removed, else the reason unchanged. THE PREDICATE MUST ACCEPT TWO PREFIX SPELLINGS, not one, and this is measured rather than assumed (F-03): `edge_satisfied`'s own refusals begin with the FULL canonical token (`executed:5j7jv1: external target ...`), while the findings gate reached from the same function begins with the BARE TARGET id6 (`review_findings.GatingBlock.describe` composes `f"{self.plan_id6}: ..."`, measured as `5j7jv1: review finding F-01 is high/open and unresolved`). A helper testing only the full token leaves the findings-gate line still duplicated, in the SUFFIX position where a reader is most likely to read the id6 as a second, different target. So strip a leading `<token>:` OR a leading `<token's last colon-separated field>:`, in that order, and strip at most ONE of them. STRIP NOTHING ELSE: match only at position 0 and only when followed by `:`, so a reason that legitimately MENTIONS another token mid-sentence is untouched (measured: `executed:bbb222: waits on executed:aaa111 which is pending` must keep the inner `executed:aaa111`). Return the input unchanged for a reason that is already token-free, which is the shape the other two producers write (`cascade_dependency_blocked`'s `target aaa111 is reviewed` and `dispatch_orchestrator_item`'s `child chi001 is queued`), so their output is byte-identical after this plan. Accept a non-string defensively (coerce with `str()`) rather than raising, because this runs inside a closing report path where an exception costs the operator the whole summary. WHY THIS MODULE: it is the one place all four call sites can already reach with NO new module-level import and NO cycle, verified by import rather than by reading (F-06) - `render_stream` binds `run_selection_policy` at module level today (line 46, `from agent_workflows import run_selection_policy`), `runner_shared` reaches it FUNCTION-LOCALLY in at least eight existing places (its own documented route for a first-party dependency, e.g. inside `edge_satisfied`'s `executed:` branch), and `run_selection_policy` imports only `selectors` and `status_set`, so nothing it can reach imports back. Do NOT add a module-level first-party import to `runner_shared` for this.
  - Depends on: none
  - Expected outcome: a public function in `run_selection_policy` that, called directly, returns the reason MINUS its leading token or bare-id6 self-reference for the five prefixed shapes tabled in F-02/F-03, returns the reason UNCHANGED for the two token-free producer shapes, leaves a mid-sentence token intact, and is idempotent (applying it twice equals applying it once). `run_selection_policy`'s module-level import list is unchanged at exactly `selectors` and `status_set`.
  - Execution state: pending

### Task group 2: the four composition sites

- [ ] E-02 Apply the helper in `render_stream.render_run_summary_table`'s dependency diagnostics arm (the `elif st in ("fail-depend", "dependency-blocked"):` branch), which composes `f"{d} ({reasons[d]})"`. Reach it through the module-level `run_selection_policy` binding that file already holds; add no import. PRESERVE THE BRANCH'S EXISTING REPAIR EXACTLY: the `f"{d} ({reasons[d]})" if d in reasons else str(d)` conditional is plan `5o1jye`'s E-03 fix for frozen run records whose TOKEN already embeds its reason and which carry no map, and it must keep rendering a bare `d` when no reason was recorded. Only the parenthesized reason changes. Do NOT touch the `refusal`, `driver_error`, or `integration_deferral` arms of the same `for` loop; a recorded `Refusal`'s reason is composed by a different producer and is not token-prefixed.
  - Depends on: E-01
  - Expected outcome: the diagnostics line for a drain-produced item reads `• eee555: fail-depend (executed:5j7jv1 (external target 5j7jv1 is 'reviewed' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)))` with the token present once; the line for a cascade-produced item is BYTE-IDENTICAL to HEAD (`• cas001: fail-depend (executed:aaa111 (target aaa111 is reviewed))`); a frozen-record item with no map still renders its bare token with no second parenthetical.
  - Execution state: pending

- [ ] E-03 Apply the helper at the TWO sites in `agent_workflows/runner_shared.py` that compose the same fact into the written report, using a FUNCTION-LOCAL import in each, matching this module's documented convention. FIRST, `write_report`'s `## Dependency blocks (why)` section, which emits `f"  - \`{dep}\`: {detail}"` - note the shape here is `- <token>: <reason>` rather than `<token> (<reason>)`, so the duplication reads as a doubled colon-separated prefix; the backlog item explicitly asks whether this form wants the same treatment and the answer is YES, because the token is already the line's own label. SECOND, `render_transient_dependency_waits`, which emits the identical `f"  - \`{dep}\`: {why.get(dep) or 'dependency not satisfied'}"` shape for an item the drain arm left `queued`. THAT SECOND SITE IS NOT IN THE BACKLOG ITEM'S LIST OF FOUR AND IS A FIFTH SURFACE THIS PLAN FOUND (F-04); it is in scope because it renders reasons from the SAME `dependency_status_detailed` map, so leaving it out would fix the terminal report and leave the transient one duplicated, which is a worse state than uniform verbosity. Preserve both sites' existing `or 'dependency not satisfied'` fallbacks. Do NOT touch that function's `Why this is not terminal:` line in this item; it renders `verdict.detail`, a different producer, and E-04 owns it.
  - Depends on: E-01
  - Expected outcome: both report sections render `- \`executed:5j7jv1\`: external target 5j7jv1 is 'reviewed' ...` with the token appearing once (as the backtick-quoted label only); a cascade- or orchestrator-produced item's section lines are byte-identical to HEAD; the no-reason fallback still prints `dependency not satisfied`.
  - Execution state: pending

- [ ] E-04 Apply the helper to the `unmet:` clause of `run_selection_policy.derive_item_disposition`, which composes `"{0} ({1})".format(d, why[d])` into the per-artifact disposition line, AND CONFIRM IN THE SAME PASS THAT THE CODE SELECTION IMMEDIATELY BELOW IT IS UNAFFECTED. That confirmation is the point of making this its own item rather than folding it into E-01: the very next statement chooses between two spec-named codes with `if "not in this run" in named`, reading the STRING THIS ITEM EDITS. The selection survives because the stripped prefix is the token, while the matched phrase lives in the refusal's tail - measured, both before and after: `'not in this run' in named` is `True` either way (F-05). SO: make the edit, then prove the invariant rather than asserting it, and do NOT "improve" the selector here; that defect is `8mohre`, owned by pending plan `zhqt51`, whose `- Scope-Paths:` includes this file. Keep the two code constants, their glosses, and `SKIP_REASON_SOURCES` untouched. ALSO apply the helper to `render_transient_dependency_waits`' `Why this is not terminal:` line from E-03, whose text is `classify_drain_block`'s `verdict.detail`: that detail is composed from `f"{tok}: prerequisite ... "` strings AND, for an external target, is `reasons.get(tok)` passed straight through, so it carries the same prefix (measured verbatim in F-04). The de-duplication there is per-cause and the line renders a `; `-joined detail for possibly several causes, so strip against the ITEM'S unmet tokens: apply the helper once per token in the record's `unsatisfied_dependencies`, in order, and accept that a multi-cause detail only loses the prefix of the cause whose token matches at position 0. Do NOT re-split or re-compose `verdict.detail`; it is one producer's sentence and reformatting it is a different change.
  - Depends on: E-01, E-03
  - Expected outcome: the disposition line reads `dependency_not_met_external (... ; unmet: executed:5j7jv1 (external target 5j7jv1 is 'reviewed' ...))` with the token once; `derive_item_disposition` returns the SAME code for all five shapes tabled in `tests/test_run_selection_policy.py::_DISPOSITION_LINES` as it does at HEAD; the transient-wait `Why this is not terminal:` line loses its leading token and keeps its full explanation.
  - Execution state: pending

### Task group 3: tests, and the one existing test this fix legitimately turns red

- [ ] E-05 REPAIR `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once`, WHICH THIS FIX TURNS RED, and do it by strengthening the assertion rather than deleting it. MEASURED, NOT PREDICTED (F-07): the prototype was applied to `render_stream.py` in the tree and `python3 -m pytest tests/test_dependency_block_reporting.py tests/test_run_selection_policy.py` reported exactly `1 failed, 60 passed`, failing on `assert un_reasons["executed:drnprereq"] in drain_diags[0]` with `AssertionError: assert 'executed:drnprereq: unparseable dependency token' in '  • drn001: fail-depend (executed:drnprereq (unparseable dependency token))'`. The assertion is CORRECT TODAY and becomes wrong under this plan precisely because it asserts the reason survives composition VERBATIM, which is what this plan stops. Replace that containment check with one that pins the plan's actual contract: the rendered line contains the token EXACTLY ONCE, and contains the reason's de-duplicated form (obtained by CALLING the E-01 helper on the producer's own reason, never by hardcoding prose). Keep every other assertion in the test: `assert not sat`, the single-diagnostic-line count, and the `(blocked)` absence. DO NOT hardcode `edge_satisfied`'s wording anywhere in this file; two pending plans are authorized to change it (`zhqt51`'s E-04 removes the words `external target` and `not in this run` outright), and a literal would collide with them.
  - Depends on: E-02
  - Expected outcome: the repaired test passes under this plan's change and FAILS if the de-duplication is reverted (because the token then appears twice); it hardcodes no reason prose; the file's other five tests are byte-unchanged by this item.
  - Execution state: pending

- [ ] E-06 ADD BEHAVIORAL COVERAGE FOR EVERY REASON SHAPE THE THREE LIVE PRODUCERS EMIT, in `tests/test_dependency_block_reporting.py`, driving the REAL functions and asserting on REAL rendered output (never by reading source, per the repository's outcomes-not-structure rule). Cover, as a table: (i) the drain/external shape from `dependency_status_detailed` against a SYNTHESIZED repository root under `tmp_path` (use the existing in-tree idiom - write one four-line plan file `20260919-s-01-<id6>-dep.ipd.md` containing `- Id: <id6>` and a non-`executed` `- Status:`, exactly as `tests/test_finalize_sendback.py` already does - so the test does NOT resolve against the live checkout and cannot rot when a real plan executes, which is the failure `03aicr` filed and `jefifu` is repairing); (ii) the FINDINGS-GATE shape, whose prefix is the BARE id6 and not the token, constructed by calling `review_findings.GatingBlock(...).describe()` so the string comes from its real producer; (iii) `cascade_dependency_blocked`'s token-free shape, asserted BYTE-IDENTICAL to HEAD's rendered line, which is what proves this plan changes nothing for it; (iv) a frozen-record item (reason embedded in the token, no map), asserted to gain no second parenthetical, which is `5o1jye` E-03's property and must not regress; (v) the `write_report` and `render_transient_dependency_waits` sections for the same drain item, since E-03 edits two sites the summary table does not cover; and (vi) the mid-sentence-token no-over-strip case from E-01. For each case assert the token's OCCURRENCE COUNT in the rendered line, not merely a substring's presence: a count is what distinguishes "printed once" from "printed twice" and is the only form that can actually fail if the helper stops being applied. Reach every expected reason by CALLING its producer.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a new test (or tabled test) covering all six cases, passing, in which each case asserts a token occurrence count of exactly 1 in the rendered line for the prefixed shapes and byte-identity with HEAD for the two token-free producer shapes; no case hardcodes `edge_satisfied`'s or `GatingBlock`'s wording; no case resolves a dependency against the live checkout.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE REASON MAP IS A DURABLE RECORD, WHICH IS WHY THIS PLAN EDITS NO PRODUCER. Both hosts write the map into `events.jsonl` under the `dependency-blocked` event's `reasons` key (`oc_runipd` and `agy_runipd` each append `"reasons": why` in their drain arm), and `runner_shared.record_transient_dependency_wait` persists the same shape under the item's `transient_dependency_wait` key. Anything written there is already on disk in existing run directories, so a producer-side edit would make old and new records disagree about one fact's format.
- `runner_shared` REACHES FIRST-PARTY MODULES FUNCTION-LOCALLY BY CONVENTION, and the convention is documented in the code rather than inferred: `edge_satisfied`'s `executed:` branch carries a comment stating the local form is "this module's documented route for a first-party dependency", and the module does this for `run_selection_policy` in at least eight functions. Its module-level first-party imports are exactly `runner_profiles` and `render_stream`. NOTE the comment ALSO cites a guard test at `tests/test_orchestrator_probe_cache.py` policing this; THAT FILE DOES NOT EXIST at HEAD `62b18f47` (verified by `ls`), so nothing will catch a module-level import for you. Follow the convention anyway: it is what keeps the import graph acyclic.
- THE OUTCOMES-NOT-STRUCTURE RULE GOVERNS E-05 AND E-06. AGENTS.md forbids tests that read production source with `inspect`/`ast`/regex or that assert on symbol censuses. Every assertion this plan adds therefore runs the real producer and asserts on the real rendered string.
- THE SUITE IS RUN BARE. `python3 -m pytest`, with no added flags; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Authoring baseline at HEAD `62b18f47`, clean tree: `3387 passed, 2 skipped, 3 warnings in 71.68s`.
- A RETAINED AST FIXTURE MENTIONS `edge_satisfied` AND IS NOT A CONSTRAINT. `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json` contains a full AST dump of `edge_satisfied` including its reason f-strings. Verified by scanning every `.py` under `tests/` and `agent_workflows/` for the fixture's name: it is read by ZERO test (the only in-tree references are to the SIBLING fixture `runner_shared_premove_fingerprints.json`, which `tests/test_runner_shared.py` itself describes as "a retained historical capture that no test reads"). This plan changes no producer string anyway, so the point is moot in both directions; it is recorded so a reviewer who greps for `edge_satisfied` does not mistake the fixture for a pin.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE DEFECT REPRODUCES AT HEAD, AND THE BACKLOG ITEM'S OWN EXAMPLE NO LONGER DOES.** The item measured `executed:5o1jye` at HEAD `04352120`; plan `5o1jye` has since EXECUTED, so that edge is now SATISFIED and `dependency_status_detailed` returns `satisfied: True` with an empty reason map. Re-measured against a currently-live pending plan (`5j7jv1`, `- Status: reviewed`), the defect is identical: reason `executed:5j7jv1: external target 5j7jv1 is 'reviewed' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)`, rendered as `• eee555: fail-depend (executed:5j7jv1 (executed:5j7jv1: external target ...))`. A reviewer must re-measure with a LIVE target, not with the item's frozen id6. | Called `dependency_status_detailed` with `dependencies=["executed:5o1jye"]` (returned `satisfied=True, missing=[]`) and then with `executed:5j7jv1`; fed the result to the real `render_run_summary_table`. |
| F-02 | **EVERY REFUSAL `edge_satisfied` COMPOSES IS TOKEN-PREFIXED, ACROSS ALL FOUR OF ITS REFUSAL BRANCHES, so this is a property of the function and not of one branch.** Measured, printing `reason.startswith(token + ":")` per branch: the external/status branch `True`; the unresolvable-target branch (`executed:zzzz99: Cannot locate IPD zzzz99; configured path was `) `True`; the dangling-owner branch (`state:spec:approved:zzzz99: no spec artifact has id6 zzzz99`) `True`; and `dependency_status_detailed`'s own unparseable-token guard (`nonsense-token: unparseable dependency token`) `True`. | One script calling `dependency_status_detailed` four times with the four token shapes and printing the boolean per reason. |
| F-03 | **ONE PRODUCER REACHED FROM THE SAME FUNCTION PREFIXES WITH THE BARE id6, NOT THE TOKEN, so a helper testing only the full token would leave that line duplicated.** `dependency_status_detailed`'s findings gate calls `_findings_block_reason`, which joins `review_findings.GatingBlock.describe()`, and that method composes `f"{self.plan_id6}: ..."`. Measured: `describe()` returns `5j7jv1: review finding F-01 is high/open and unresolved`, for which `startswith("executed:5j7jv1:")` is `False` while `startswith("5j7jv1:")` is `True`; composed today as `(executed:5j7jv1 (5j7jv1: review finding F-01 is high/open and unresolved))`. This is why E-01 accepts two prefix spellings. | Constructed a real `GatingBlock` and called `.describe()`; printed both booleans and the composed line. |
| F-04 | **THERE ARE FIVE AFFECTED SURFACES, NOT THE FOUR THE ITEM NAMES.** The item lists the summary table, `write_report`, the events map, and `derive_item_disposition`. `runner_shared.render_transient_dependency_waits` is a FIFTH: it renders the same `dependency_status_detailed` reasons with the identical `- \`{dep}\`: {reason}` shape, measured as `- \`executed:5j7jv1\`: executed:5j7jv1: external target ...`. Its `Why this is not terminal:` line duplicates too, because `classify_drain_block` passes an external target's reason straight through (`reasons.get(tok) or ...`), measured as `Why this is not terminal: executed:aaa111: prerequisite aaa111 reached the non-success terminal state 'interrupted', so it can never satisfy this edge`. | Built a drain item, called `classify_drain_block` then `record_transient_dependency_wait`, then the real `render_transient_dependency_waits`; output pasted above. |
| F-05 | **THE FIX CANNOT MOVE `derive_item_disposition`'s CODE SELECTION, which is the risk the backlog item flags as making the fix "not as local as it looks".** The selector is `if "not in this run" in named`. The phrase sits in the refusal's TAIL while the stripped prefix is at position 0, so it survives. Measured on the real string: `'not in this run' in named` is `True` before the strip and `True` after. The two spec-named codes (`dependency_not_met`, `dependency_not_met_external`) are therefore unchanged for every shape. | Prototyped the helper, composed `named` both ways from the real reason, printed the boolean for each. |
| F-06 | **`run_selection_policy` IS THE ONLY HOME ALL FOUR CALL SITES REACH WITH NO NEW IMPORT AND NO CYCLE.** Verified by importing rather than by reading: `render_stream.run_selection_policy is run_selection_policy` -> `True` (module-level binding, line 46); `runner_shared` reaches it function-locally in at least eight functions; and `run_selection_policy`'s module-level first-party imports are exactly `selectors` and `status_set`, so it imports neither consumer and cannot form a cycle. Putting the helper in `runner_shared` instead would force `run_selection_policy` to import a runner, which is the "two-import purity" property its own comments record other plans as depending on. | `python3 -c` importing all three modules and printing the identity check plus the import lists; `rg` of `^from agent_workflows` in `run_selection_policy.py` returning exactly two lines. |
| F-07 | **THE FIX TURNS EXACTLY ONE EXISTING TEST RED, MEASURED BY APPLYING IT RATHER THAN BY PREDICTION.** The prototype was written into `render_stream.py`'s diagnostics arm and the suite run: `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` FAILED with `assert 'executed:drnprereq: unparseable dependency token' in '  • drn001: fail-depend (executed:drnprereq (unparseable dependency token))'`; `1 failed, 60 passed`. No other test in either dependency-reporting module moved. The prototype was then reverted and `git status` confirmed clean. | `python3 -m pytest tests/test_dependency_block_reporting.py tests/test_run_selection_policy.py` with the prototype applied; failure output pasted; file restored from a backup copy and `git status --short` empty. |
| F-08 | **THE SAME TEST IS BEING REWRITTEN BY PENDING PLAN `jefifu`, AND ITS POST-EDIT FORM IS *ALSO* RED UNDER THIS FIX, so this plan must not assume `jefifu` absorbs the repair.** `jefifu` (`- Status: reviewed`, `- Scope-Paths: tests/test_dependency_block_reporting.py`) repoints that test at a synthesized `tmp_path` root and explicitly PRESERVES the containment assertion, its Step 0 reasoning being that reading the reason out of the map "pins 'rendered once, containing the mapped reason' without pinning prose. That matters because `csjq81` proposes changing exactly that prose". Measured: that reasoning does not hold for THIS fix, because the composed line no longer CONTAINS the map's value verbatim. Reproducing `jefifu`'s prescribed post-E-02 state exactly (a four-line `20260919-s-01-depx01-dep.ipd.md` with `- Status: approved` under `tmp_path`), the reason is `executed:depx01: external target depx01 is 'approved' ...` and `un_reasons[tok] in line` is `True` under today's renderer and `False` under this plan's. So the two plans genuinely interact and E-05 owns the assertion either way; whichever lands second must re-run the other's test. | Built `jefifu`'s synthesized root and item verbatim, called the real `dependency_status_detailed`, and printed the containment boolean for both renderer forms. |
| F-09 | **NO PENDING PLAN CONTESTS THE PRODUCTION EXPRESSIONS THIS PLAN EDITS, though three declare overlapping FILES.** `zhqt51` (`reviewed`, `8mohre`) declares all three production files here; it edits `derive_item_disposition`'s CODE SELECTION and `edge_satisfied`'s refusal WORDING - this plan edits neither (it edits the same function's `unmet:` COMPOSITION, one statement earlier, and no producer string). `8eei5p` (`reviewed`, `mjrac4`) declares `runner_shared.py` plus this test file; it adds a RECOVERY HINT key to the cascade and orchestrator producers and edits `test_cascade_producer_output_shape`, touching neither the reason composition nor the test E-05 repairs. `cup9r7` (`reviewed`) declares `run_selection_policy.py`; it adds `isinstance` guards for a non-mapping queue entry and explicitly excludes the dependency branch. Per AGENTS.md the runner isolates each item in its own worktree and merges through a revalidation gate, so a shared file is not a hazard; the honest statement is that no two of these edit one expression. | `rg -l` over `.aw/records/plans/pending/` for each `- Scope-Paths:` entry, then read of each hit's `- Scope-Paths:` and E-items. |
| F-10 | **THE SPEC GOVERNS THE REASON *CODES* AND THE REQUIRED *FACTS*, NOT THE RENDERED PROSE, so no spec amendment is owed.** Spec `25kzda` 5.4 requires a skipped item to record `reason_code: dependency_not_met`, "the immediate blocking edge and dependency ID", the root cause, the chain, and `session_started: false`. It fixes the code vocabulary (and 5.4's table names `dependency_not_met_external`) but states no format for the human reason string. This plan changes neither a code nor a recorded fact: the blocking edge and dependency ID remain on the line, printed once instead of twice. | Read of the spec's 5.4 propagation list and its dependency-disposition table; `rg` for `reason_detail`/`reason text`/`reason string` in that spec returning nothing. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/run_selection_policy.py`: add one pure public helper stripping a reason's leading self-reference to its own token or that token's bare id6 (E-01).
2. `agent_workflows/render_stream.py`: apply it in `render_run_summary_table`'s dependency diagnostics arm, preserving `5o1jye`'s bare-token fallback (E-02).
3. `agent_workflows/runner_shared.py`: apply it in `write_report`'s `## Dependency blocks (why)` section and in `render_transient_dependency_waits`' per-dependency lines (E-03), and in that function's `Why this is not terminal:` line (E-04).
4. `agent_workflows/run_selection_policy.py`: apply it in `derive_item_disposition`'s `unmet:` clause and prove the adjacent code selection is unmoved (E-04).
5. `tests/test_dependency_block_reporting.py`: repair the one test this fix legitimately turns red, by strengthening rather than deleting its assertion (E-05), and add occurrence-count coverage for all six producer shapes (E-06).

## Deferred / out of scope (with reason)

- CHANGING ANY REASON STRING A PRODUCER WRITES is out of scope, and this is the plan's central design choice rather than an omission. `edge_satisfied`'s strings are (a) persisted verbatim in `events.jsonl`'s `dependency-blocked` `reasons` map in run directories already on disk, and (b) the input to `derive_item_disposition`'s substring-matched selection between two spec-named codes. Fixing the composition instead leaves both untouched, which F-05 measures.
- THE IN-QUEUE-MISLABELLED-`external` DEFECT (backlog `8mohre`) is out of scope and is actively owned by pending plan `zhqt51`, which will also REMOVE the words `external target` and `not in this run` from the refusal. This plan is compatible with that either way: the helper keys on the token prefix, not on any word in the tail, so it neither depends on nor blocks that rewording. This is also why E-05 and E-06 forbid hardcoding that prose.
- THE MISSING RECOVERY HINT on cascade- and orchestrator-produced blocks is out of scope and owned by pending plan `8eei5p`.
- A NON-MAPPING QUEUE ENTRY crashing these renderers is out of scope and owned by pending plan `cup9r7`.
- REFORMATTING `classify_drain_block`'s `verdict.detail` (for instance splitting a multi-cause `; `-joined sentence so each cause is de-duplicated independently) is deliberately NOT done. E-04 strips only a prefix matching one of the item's own tokens at position 0. Restructuring one producer's sentence is a different change with its own reporting-contract question.
- THE FOUR-NESTED-PARENTHESES SHAPE of the summary-table line is not otherwise restyled. This plan removes the duplicated token; whether the surviving `<token> (<reason>)` nesting should become a two-line form (as the `refusal` arm's separate `→ remedy:` line already does) is a presentation decision for whoever owns that table's layout.

## Scope check

- Over-scope: none. Each declared path carries specific E-items: `run_selection_policy.py` for E-01 (the helper) and E-04 (its `unmet:` clause); `render_stream.py` for E-02; `runner_shared.py` for E-03 and E-04's transient-wait line; `tests/test_dependency_block_reporting.py` for E-05 and E-06.
- Under-scope: `tests/test_run_selection_policy.py` is deliberately NOT declared. E-04 edits `derive_item_disposition`, whose five shipped row shapes are tabled there, and F-05 measures that all five keep their codes and that the composed `named` string keeps the substring the selector matches. If execution finds a row that does move, the correct response is to STOP and report a contradicted finding, not to edit an undeclared file: a red row there would mean the fix changes a disposition code, which this plan asserts it cannot.

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with its summary line pasted. Authoring baseline at HEAD `62b18f47`, clean tree: `3387 passed, 2 skipped, 3 warnings in 71.68s`.
- The two directly-affected modules run together, since F-07's measurement was taken over exactly that pair: `python3 -m pytest tests/test_dependency_block_reporting.py tests/test_run_selection_policy.py` (baseline `61 passed`).
- A REVERT CHECK for the new coverage: with the helper's application removed from one site, E-06's occurrence-count assertion for that site must FAIL. A test that cannot go red does not protect the property.
- `aw ipd lint` conforming, and `aw sanitize --agent` clean, before the terminal transition.

## Spec / documentation sync

N/A with reason. No `.spec.md` path is in `- Scope-Paths:` and none is owed: F-10 measures that spec `25kzda` 5.4 fixes the reason CODE vocabulary and the FACTS a skipped item must record, while stating no format for the human reason string. This plan changes no code, no recorded fact, and no durable record format - only how one line composes a token and a reason it already had.

## Open questions

### OQ-01: Should `write_report`'s `- <token>: <reason>` form be de-duplicated too, or only the parenthesized `<token> (<reason>)` form?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS YES, de-duplicate both, which is the question the backlog item leaves open ("Decide whether `write_report`'s `- <token>: <reason>` form wants the same treatment"). The reason it is the same defect: the token is already the line's own backtick-quoted LABEL, so a token-prefixed reason renders `- \`executed:5j7jv1\`: executed:5j7jv1: external target ...`, which is the same fact stated twice with the second statement reading as the start of a new field. Doing only the parenthesized form would also make the two report surfaces disagree about one item within one file, which is the class of divergence `5o1jye` and `8eei5p` both exist to remove. E-03 therefore covers it.

### OQ-02: Is stripping the BARE id6 prefix (not just the full token) safe, given a six-character id6 is a short string to match at position 0?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS SAFE, with the safety coming from three restrictions rather than from the id6's length. First, the match is ANCHORED at position 0 and must be followed by `:`, so a mid-sentence mention is untouched (measured in E-01's no-over-strip case). Second, the candidate prefix is not "any id6" but specifically THIS token's own last colon-separated field, so it can only ever remove a self-reference. Third, at most ONE prefix is stripped, so a reason beginning with two prefixes keeps the second. The residual risk is a producer whose reason legitimately BEGINS by naming the same target with a colon and where that naming is load-bearing; F-03's findings-gate string is exactly that shape and is the case this rule exists to fix, so the risk is the intended behavior. E-06 case (vi) pins the no-over-strip property.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste a single script's output that CALLS the new helper (never reads its source) over a table of cases and prints, per case, the input reason and the returned string: (a) all four `edge_satisfied`/`dependency_status_detailed` prefixed shapes from F-02, obtained by CALLING `dependency_status_detailed` rather than by hardcoding, each shown losing exactly its leading `<token>:`; (b) the findings-gate shape from F-03, obtained by calling a real `GatingBlock(...).describe()`, shown losing its leading `<id6>:`; (c) `cascade_dependency_blocked`'s and `dispatch_orchestrator_item`'s token-free shapes, each shown returned UNCHANGED (print the `==` boolean, not just the string); (d) the mid-sentence case `executed:bbb222: waits on executed:aaa111 which is pending`, shown keeping the inner `executed:aaa111`; (e) idempotency, as the printed boolean `helper(t, helper(t, r)) == helper(t, r)` for every case above. Then paste `rg -n '^from agent_workflows' agent_workflows/run_selection_policy.py`, which must still return exactly the two `selectors` and `status_set` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the ACTUAL diagnostics line from `render_stream.render_run_summary_table` for three items built from real producers, and for each print the occurrence count of the token in the line: (a) a drain item whose reasons come from `dependency_status_detailed` against a synthesized `tmp_path` root - count must be 1, and paste the HEAD line beside it (count 2) so the change is visible rather than asserted; (b) an item produced by calling `cascade_dependency_blocked` - the line must be BYTE-IDENTICAL to HEAD, shown as an `==` boolean against the HEAD string `• cas001: fail-depend (executed:aaa111 (target aaa111 is reviewed))`; (c) a frozen-record item carrying `unsatisfied_dependencies: ["executed:aaa111 (target reviewed)"]` and NO map, shown rendering with no second parenthetical and no `(blocked)`, which is `5o1jye` E-03's property.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the real `## Dependency blocks (why)` section from `runner_shared.write_report` and the real `## Dependency waits (NOT blocked; left queued)` section from `render_transient_dependency_waits`, in both cases for a drain item whose reasons came from `dependency_status_detailed`, with the token occurrence count printed per dependency line (must be 1: the backtick-quoted label only). Paste the HEAD form of the same two sections beside them (count 2). Then show the fallback intact: an item with an unmet token and NO recorded reason must still render `dependency not satisfied` in each section. Then show a cascade-produced item's section lines BYTE-IDENTICAL to HEAD, as an `==` boolean.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Two parts, the second being the one that can actually go red. FIRST, paste the real line from `run_selection_policy.render_queue_dispositions` for a drain-shaped entry, with the token occurrence count (must be 1), beside the HEAD line (count 2); and paste the real `Why this is not terminal:` line, shown losing its leading token while keeping its full explanation. SECOND, prove the adjacent selector is unmoved: for EVERY one of the five entry shapes tabled in `tests/test_run_selection_policy.py::_DISPOSITION_LINES`, print the code `derive_item_disposition` returns at HEAD and after the change, as a per-shape equality boolean; all five must be `True`, and the external shape must still resolve to `dependency_not_met_external`. Additionally print `'not in this run' in named` for the external shape both before and after (F-05 measured both `True`). Then paste `python3 -m pytest tests/test_run_selection_policy.py` (baseline: part of `61 passed` with the sibling module).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `python3 -m pytest tests/test_dependency_block_reporting.py` passing, and paste `git diff` for that file showing the repaired assertion. Then show the repaired test HAS TEETH, by pasting a red run obtained with the de-duplication removed from `render_stream`'s arm only (the test must FAIL because the token then appears twice); restore the code and paste the green run again. Confirm by `rg` that the file contains no literal of `edge_satisfied`'s wording (`external target`, `needs one of`, `not in this run`), since two pending plans may change it. State explicitly whether `jefifu` had already landed in your tree, and if it had, paste its repointed test passing too (F-08 measures that its preserved assertion is red under this fix, so this is the interaction check, not a formality).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste `python3 -m pytest tests/test_dependency_block_reporting.py -v` (or the tabled test's own node id) showing all six cases from E-06 present and passing, and name which pasted case is which. For each of the six, the pasted output or the test body must show the token OCCURRENCE COUNT asserted rather than substring presence. Then paste a REVERT CHECK: with the helper's application removed from ONE site, the case covering that site FAILS; paste the failure and then the restored green. Finally paste the bare `python3 -m pytest` summary line for the whole suite (authoring baseline `3387 passed, 2 skipped`) and `aw sanitize --agent` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph. A `chore`-class legibility fix with an unusually
careful blast radius, because the backlog item correctly warns that "the fix is not as local as it
looks". Five render surfaces (one more than the item counted, F-04) each print a dependency token
twice, because the producer embeds the token in its reason and every consumer re-prefixes it. The fix
adds ONE pure helper and applies it at those five compositions, changing NO producer string, so the
durable `events.jsonl` reason map stays byte-identical and the substring-matched disposition-code
selector keeps its exact input (F-05, measured both ways). Two facts are worth a human's attention
before approval. FIRST, the fix legitimately turns ONE existing test red, measured by applying the
prototype and running the suite (F-07), and E-05 repairs it by STRENGTHENING the assertion to the
property this plan actually establishes rather than deleting it. SECOND, that same test is being
rewritten right now by pending plan `jefifu`, whose author reasoned its preserved assertion would
survive this change; measured, it does NOT (F-08), so whichever of the two lands second must re-run
the other's test. Nothing here changes a disposition code, a spec-named vocabulary, or a recorded
fact, so no spec amendment is owed (F-10).

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan,
through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set
with `git diff --cached --name-only` before committing, since this is a shared checkout and another
party's work must never be swept in; run the BARE `python3 -m pytest` and paste its ACTUAL summary
line rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it
demands, including V-05's and V-06's revert checks, which are the only evidence that the new
assertions can go red at all. An out-of-scope edit is to be MADE and then JUSTIFIED to
`aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop. After validation passes,
move this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition.
