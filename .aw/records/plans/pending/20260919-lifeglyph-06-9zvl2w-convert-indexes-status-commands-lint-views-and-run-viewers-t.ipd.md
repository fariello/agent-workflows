# IPD: Convert indexes status commands lint views and run viewers to the shared resolver

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R10.3 requires human lifecycle output in "plan/spec/research/backlog indexes, status setters, lint output, run viewers" to consume the shared resolver, and Section 12 step 4 sequences them after `attention.py`. Four surfaces render an artifact's or a run item's lifecycle state through the OLD fused path and will keep doing so after `attention.py` converts: `aw find` (`cli.py:9473,9534,9572`), `aw ipd lint` (`ipd_lint.py:1477`), `aw set` (`status_set.py:402,407`), and the run views (`run_viewer.py:1350,1411,1806,2535` plus a much larger direct-`color256` surface). Leaving them unconverted keeps two live presentations of the same state, which is Section 1's problem restated.
  THE ORIGINAL SCOPE BASIS WAS INVALID AND IS CORRECTED, which is the most consequential change this review made (F-04). The plan defined its scope by grepping `status_256`/`status_label` callers. That caller set is accurate (verified: exactly `plans_index`, `research_index`, `status_set`, `ipd_lint`, `run_viewer`, `cli`, and `term` itself) but it is NOT a lifecycle-site set, because `status_256` also styles GENERIC outcome words that R10.3 explicitly keeps outside this spec. Measured per module at review, counting how many of each module's `status_256` calls carry a LIFECYCLE status: `plans_index` 0 of 4, `research_index` 0 of 4, `status_set` 2 of 3, `ipd_lint` 1 of 2, `run_viewer` 4 of 4, `cli` 5 of 5.
- Scope: IN: route LIFECYCLE rendering in `status_set.py`, `ipd_lint.py`, `run_viewer.py`, and the `aw find` lifecycle call sites in `cli.py` through the shared helpers; apply Section 9.1 styling (including the id6, which three `cli.py` sites currently hardcode independent of status) and criterion A20 unknown handling at each; decide and record `quarantined`'s treatment in the mixed lint disposition column; convert the run views' HARDCODED lifecycle colors that `status_256` never touches; fix the live A14 ANSI leak in `aw index --agent`; and update each view's snapshots. OUT: both runners and `render_stream.py` (child `qdd5jq`), deleting the shared `term.py` table (also `qdd5jq`, after every consumer is off it), generic `Term` OK/WARN/FAIL outcomes which R10.3 keeps explicitly out of scope, and the generic index-outcome words (`up to date`, `wrote`, `updated`, `unchanged`) which are NOT lifecycle statuses and MUST NOT be routed through the resolver.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/ipd_lint.py, agent_workflows/run_viewer.py, agent_workflows/cli.py, agent_workflows/plans_index.py, agent_workflows/research_index.py, tests/test_ipd_lint.py, tests/test_run_viewer.py, tests/test_status_set.py, tests/test_research_index.py, tests/test_plans_index.py
- Item-Dependencies: executed:f9t5hz
- Status: approved
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 6
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9zvl2w
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-601..PR-610 all FIXED, none deferred, none open. The scope basis was INVALID (PR-604, BLOCKER): scope was derived from status_256 callers, but that helper also styles generic outcome words R10.3 excludes, so E-01's two modules held ZERO lifecycle calls and converting them would print ? via A20 where users read 'up to date'. Three more gaps invisible to that grep: run_viewer.py has 29 direct color256 calls with four contradicting Section 5 (blocking A17), aw find hardcodes the id6 to 39 (breaking A10), and the colored type word from f9t5hz is replicated in three modules. E-03 conflated the lint status and disposition columns. No shipped test pins any color this child changes. OQ-01 resolved: aw index supports only plans and research. Readiness go-pending-approval.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601 through PR-610 all FIXED, none deferred, none open. Reviewed at HEAD `f348b227`; `aw ipd lint --phase author --agent` clean, exit 0, before and after. THE PLAN'S SCOPE BASIS WAS INVALID AND THAT IS THE HEADLINE (PR-604, BLOCKER, fixed in place). It derived scope by grepping `status_256` callers, but `status_256` styles BOTH lifecycle statuses and GENERIC outcome words R10.3 explicitly excludes, and the plan assumed every caller was a lifecycle site. Measured lifecycle share per module: `plans_index` 0 of 4, `research_index` 0 of 4, `status_set` 2 of 3, `ipd_lint` 1 of 2, `run_viewer` 4 of 4, `cli` 5 of 5. So E-01, the plan's entire Task group 1, converted two modules whose every call renders `up to date`/`wrote`/`updated` - words that grep to ZERO in the spec - and routing them through the resolver would have sent each to criterion A20's unknown path, printing `?` where a user reads `up to date` today: a REGRESSION delivered as compliance. E-01 is now a determination plus the fix for the REAL defect there, a live A14 violation (`aw index plans --agent` emits ANSI today; `aw find` and `aw ipd lint` emit none, so "byte-identical before and after" was the wrong bar for one of three commands). THREE MORE UNDER-SCOPE GAPS, each invisible to the caller-set grep: `run_viewer.py` has 29 direct `color256` calls against 4 `status_256` calls, and FOUR paint lifecycle states with indices that CONTRADICT Section 5 (`:1628`/`:1847` use 214 for in-flight work where 214 means `waiting-input` ONLY and `active` is 220; `:1401` uses 226; `:1995` uses 40), which alone makes criterion A17 unsatisfiable (PR-607); `aw find` hardcodes the id6 to 39 regardless of status, measurably breaking A10 (PR-608); and the colored artifact TYPE word flagged in `f9t5hz` is replicated in THREE of these modules via `attention._TREE_COLOR_256` (PR-605). E-03 also conflated the lint `- Status:` column with the DISPOSITION column, hiding a real conflict: the disposition vocabulary mixes `quarantined` with four generic outcomes, and the spec-conforming gray 244 for `parked` is what `legacy/not evaluated` already falls back to, making `quarantined` LESS distinguishable than today's 214 unless the `◇` glyph carries it (PR-606). No shipped test pins ANY color this child changes (all five relevant files have zero `38;5;` assertions), so E-05 must ADD assertions (PR-609). OQ-01 resolved by measurement: `aw index` supports only `plans` and `research`, so R10.3's "spec index" and "backlog index" name commands that do not exist (PR-610). Baseline `7468 passed, 3 skipped, 2 xfailed`. Readiness go-pending-approval.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg R10.3 and Section 12 step 4, against the measured `status_256`/`status_label` caller set. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Move every remaining non-runner human lifecycle view onto the shared resolver, so the indexes, the status setters, the lint output, and the run viewers all render one vocabulary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The record indexes

- [x] E-01 Do NOT route `plans_index.py` or `research_index.py` `status_256` calls through the lifecycle resolver. Instead: (a) record the measured determination that these two modules render NO lifecycle status in their terminal output, and (b) fix the live criterion A14 violation in their shared print path, where `aw index plans --agent` emits ANSI into machine output.
  - Depends on: none
  - Expected outcome: The two index modules keep their generic outcome words unchanged in color, and `aw index plans --agent` and `aw index research --agent` emit ZERO ANSI bytes.
  - Execution state: performed

  THE ORIGINAL E-01 WOULD HAVE CAUSED A REGRESSION AND CALLED IT COMPLIANCE (F-04). Every one of the eight `status_256` calls in these two modules renders a GENERIC INDEX OUTCOME, not a lifecycle status. Measured at review:

  ```text
  plans_index.py:432,436,440,446     -> "up to date", "wrote", "updated", "updated"
  research_index.py:650,654,658,664  -> "up to date", "wrote", "updated", "updated"
  FORCE_COLOR=1 aw index plans  ->  ^[[1;38;5;46mup to date^[[0m  .aw/records/plans/INDEX.json, INDEX.md (687 plans)
  ```

  None of `up to date`, `wrote`, or `updated` appears ANYWHERE in spec `uonrjg` (each greps to 0). They are exactly the "command-level OK, WARN, and FAIL" class R10.3 keeps valid and outside this spec, with its warning not to "mechanically replace every checkmark". Routing them through the resolver would send each to criterion A20's unknown path and render `?` where a user reads `up to date` today.

  AND THE INDEXES HAVE NO LIFECYCLE TERMINAL VIEW AT ALL, which is why there is nothing here to convert. A plan's status DOES appear in `INDEX.md`, but that is a COMMITTED MARKDOWN FILE (`.aw/records/plans/INDEX.md`, header `generated by aw index plans; do not edit by hand`, verified to contain 0 ANSI bytes), not human terminal output. Spec Section 9.5 and criterion A14 keep committed and machine artifacts ANSI-free, so the correct action there is none. R10.3's "plan/spec/research/backlog indexes" is satisfied for these two by the artifact statuses reaching a human through `aw find`, `aw ipd lint`, `aw set` and `aw attention`, all of which ARE converted in this Set.

  THE A14 LEAK IS REAL AND IS THIS ITEM'S ACTUAL WORK. Measured: `aw index plans --agent` emits 1 ANSI-bearing line (the `status_256` label plus the `color256(dir_prefix, 33)` path at `plans_index.py:429`), while `aw find plans --agent` and `aw ipd lint --all --agent` each emit 0. So the print path does not honor agent mode. Criterion A14 requires `--agent` and `--json` to contain no ANSI; fix it by suppressing color on that path, NOT by changing which palette the word uses.

### Task group 2: The status setters and lint views

- [x] E-02 Convert the TWO lifecycle `status_256` calls in `status_set.py` (the old and new status of a transition) to the shared helpers, and LEAVE the third call alone: it renders the literal word `unchanged`, which is a no-op outcome and not a lifecycle status.
  - Depends on: none
  - Expected outcome: A status transition prints the same glyph and color for a given status as `aw find` and `aw attention` do. The `unchanged` no-op line is unchanged in color.
  - Execution state: performed

  THE THIRD CALL IS A TRAP OF THE SAME KIND AS E-01'S (F-04). Measured: `status_set.py:396` renders `term.status_256("unchanged")`, while `:402` and `:407` render `rec.status` and `norm_stat`, which ARE lifecycle. `unchanged` resolves to 245 in `term.STATUS_COLOR_256` today and is not a status in any spec Section 6 or 7 table, so routing it through the resolver sends it to A20's unknown path and prints `?` for a successful no-op. Convert by VALUE, not by call site.

  ALSO IN THIS MODULE, and it is the same violation flagged in `f9t5hz`: `status_set.py:453` colors the artifact TYPE word via `_att._TREE_COLOR_256` (33, bold), which spec Section 9.1 says must not carry lifecycle color and Section 11 item 5 limits to glyph, id6 and status. See F-05 for why the Section 11 "existing independent convention" exemption does not stretch to a bare type word.

- [x] E-03 Convert the ONE lifecycle `status_256` call in `ipd_lint.py` (the `- Status:` column at `:1477`). For the SECOND call, which renders the lint DISPOSITION column, decide and record whether `quarantined` moves to the spec's `parked` treatment while its generic siblings stay put, or whether the whole column stays generic. Do not convert the column wholesale.
  - Depends on: none
  - Expected outcome: The `- Status:` column renders the shared marker. A recorded, justified decision for the disposition column that does not route generic outcomes through the lifecycle resolver and does not make a quarantined plan LESS distinguishable than it is today.
  - Execution state: performed

  THE ORIGINAL E-03 CONFLATED TWO DIFFERENT COLUMNS and the conflict it hides is genuine (F-06). `ipd_lint.py` has exactly two `status_256` calls: `:1477` styles the plan's `- Status:` value (lifecycle, convert it) and `:1520` styles `disp_word`, the lint DISPOSITION. The disposition vocabulary is `conforming`, `advisory`, `quarantined`, `legacy/not evaluated`, and `error` (`ipd_schema.py:1470-1472`), so ONE column mixes a value the spec claims with four generic command outcomes R10.3 keeps out.

  BOTH OBVIOUS ROUTES ARE WRONG, which is why this is a recorded decision rather than a mechanical conversion. Converting the whole column routes `conforming`/`advisory`/`error` through the lifecycle resolver, which R10.3 forbids. Converting only `quarantined` is defensible but has a measured cost the spec did not anticipate: today `quarantined` renders 214 (orange) while `legacy/not evaluated` has NO table entry and falls back to gray 244; the spec's `parked` stage is ALSO gray 244 with `◇`. So the spec-conforming color makes `quarantined` and `legacy` nearly indistinguishable, which cuts against Section 7.2's own reason for listing it ("the lint view must show it without calling it a pass"). The glyph `◇` is what preserves the distinction, so if this route is taken the glyph is load-bearing and MUST be present, not optional.

  WHAT IS SETTLED AND NEEDS NO DECISION: `quarantined` is read from the `- Quarantine:` FIELD, not from `- Status:` (spec D15), and `ipd_lint.py:1123` confirms it (`S.is_quarantined(doc.meta_fields)`), so it is a Section 8 condition input. Whatever is decided about color, do not start reading it from `- Status:`.

### Task group 3: The run viewers

- [x] E-04 Convert `run_viewer.py`'s four `status_256` sites AND its HARDCODED lifecycle colors, plus the three `aw find` lifecycle sites in `cli.py` INCLUDING their id6 treatment, applying the Section 7.2 and 7.3 runner and ledger mappings and the five review-added rows.
  - Depends on: none
  - Expected outcome: Run views render ledger and item states through the shared vocabulary. `ran` shows `recovering`, `unknown_outcome` shows `failed`, neither is styled as success, and no lifecycle state in these views keeps a hardcoded palette index. In `aw find`, the id6 carries the SAME resolved color as its status rather than a fixed one.
  - Execution state: performed

  THE `status_256` CALLER SET SEES ONLY A FRACTION OF THIS MODULE'S LIFECYCLE STYLING (F-07). Measured: `run_viewer.py` has 4 `status_256` calls and 29 direct `term.color256(...)` calls, and several of the latter render lifecycle states with a HARDCODED index that the caller-set measurement never sees. Four of them contradict spec Section 5:

  ```text
  run_viewer.py:1628  "[in flight]"      214   spec stage `active`  -> 220   WRONG (214 is waiting-input)
  run_viewer.py:1847  "YES (in flight)"  214   spec stage `active`  -> 220   WRONG
  run_viewer.py:1401  "[review]"         226   spec `reviewing`     -> 220   WRONG (226 is not a spec index)
  run_viewer.py:1995  "[<phase state>]"   40   spec `ready`         ->  45   WRONG (40 is not a spec index)
  run_viewer.py:1382  "[verified]"        46   spec `done`          ->  46   matches, by luck
  run_viewer.py:1388  "[verify-failed]"  196   spec `failed`        -> 196   matches, by luck
  ```

  Spec Section 5 uses exactly 11 indices (39, 45, 46, 81, 135, 196, 208, 214, 220, 244, 245), and 214 means `waiting-input` ONLY. So a run view currently paints in-flight work the color the spec reserves for "a human is being asked", which is precisely the collapse Section 5 exists to prevent. Criterion A17 ("no second lifecycle color or glyph table remains") is not satisfiable while these literals stand, and child `qdd5jq`'s Set-level A17 assertion would fail against them. ENUMERATE the direct `color256` calls and classify each as lifecycle or generic before converting; do not convert the generic ones (`[$cost]` 220, run_id 33, elapsed/summary 245 are formatting, not lifecycle).

  THE id6 IS HARDCODED IN `aw find` AND BREAKS A10 (F-08). All three sites pair a `status_256` status with an id6 colored a FIXED 39: `cli.py:9475`, `:9536`, `:9573`. Criterion A10 requires glyph, id6 and status to share one resolved color. Measured from real output, an `executed` row emits status 46 and id6 39 side by side:

  ```text
  FORCE_COLOR=1 aw find plans
  ^[[1;38;5;46mexecuted^[[0m      ^[[1;38;5;39md5tz36^[[0m  -  .aw/records/plans/executed/...
  ```

  Note `cli.py:9473` reads `e.disposition or e.status`, so that column can hold a DISPOSITION rather than a status; apply the same lifecycle-versus-generic split E-03 makes for the lint column rather than assuming every value is a status. Also leave `cli.py`'s many other `color256(..., 39, ...)` calls alone: they style config keys and repository names, not lifecycle.

### Task group 4: Snapshots and machine-output safety

- [x] E-05 Update each converted view's snapshots and assert criterion A14 for every one of them: no ANSI and no schema-breaking decorated status value in `--agent` or `--json` output.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: Human snapshots updated; machine output for every converted command proven ANSI-free, with `aw index --agent` moving from 1 ANSI-bearing line to 0.
  - Execution state: performed

  A14 IS NOT UNIFORMLY SATISFIED TODAY, so "byte-identical before and after" is the WRONG bar for one command and the right bar for the others (F-03). Measured at review: `aw find plans --agent` and `aw ipd lint --all --agent` each emit 0 ANSI bytes (characterization: assert they stay 0), but `aw index plans --agent` emits 1 ANSI-bearing line (a live violation E-01 fixes, so its diff MUST NOT be empty). Stating one expectation for both would either mask the leak or fail a correct fix.

  THE DECLARED TEST FILES CONTAIN NO ESCAPE ASSERTIONS AT ALL, which is a coverage gap rather than a convenience (F-09). Measured: `grep -c '38;5;'` returns 0 for `tests/test_plans_index.py`, `tests/test_research_index.py`, `tests/test_status_set.py`, `tests/test_ipd_lint.py` and `tests/test_run_viewer.py`. So no shipped test pins the color of any view this child converts, and the whole conversion could regress silently. E-05 must therefore ADD escape-level assertions for the converted surfaces, not merely refresh existing ones. Two files elsewhere DO assert escapes and were checked: `tests/test_term_components.py:145-156` pins generic badge/path roles (unaffected), and `tests/test_cli_find.py:104,118-119` asserts 214 for a SEARCH-MATCH HIGHLIGHT in a filename, not a lifecycle status, so it must NOT be recomputed; `cli._highlight_filename_matches` is a text-match highlighter and is outside this spec.

## Project conventions discovered (Step 0)

- Verified at review 2026-09-19 at HEAD `f348b227`: `status_256`/`status_label` are called from exactly `plans_index.py`, `research_index.py`, `status_set.py`, `ipd_lint.py`, `run_viewer.py`, `cli.py`, and `term.py` itself. THE CALLER SET IS ACCURATE BUT IS NOT A LIFECYCLE-SITE SET, and treating it as one is what produced this plan's largest defect (F-04). Per-module lifecycle share of those calls: `plans_index` 0/4, `research_index` 0/4, `status_set` 2/3, `ipd_lint` 1/2, `run_viewer` 4/4, `cli` 5/5. CONVERT BY VALUE, NOT BY CALL SITE.
- Verified at review: no `STATUS_COLOR_256` literal exists outside `term.py` and `attention.py`, so no consumer holds its own status table. But "no table" does not mean "no hardcoded lifecycle color": `run_viewer.py` has 29 direct `term.color256(...)` calls against 4 `status_256` calls, and several paint lifecycle states with a literal index (F-07). Direct `color256` counts measured: `plans_index` 1, `research_index` 1, `status_set` 4, `ipd_lint` 7, `run_viewer` 29.
- Verified at review: three of the declared modules import `attention.py`'s PRIVATE `_TREE_COLOR_256` to color the artifact TYPE word (`status_set.py:453`, `ipd_lint.py:1508`, `run_viewer.py:1358`, the last via a module-level `from agent_workflows.attention import _TREE_COLOR_256`). That is the same criterion A10 violation raised against `attention.py` in child `f9t5hz`, replicated across three more views; see F-05.
- Verified at review: `aw index` is SUPPORTED ONLY for `plans` and `research`. Every other type answers `WARN 'index' is not supported for <type>`, so R10.3's "spec index" and "backlog index" name commands that do not exist. That resolves OQ-01 without an execution-time investigation.
- Verified at review: `INDEX.md` is a COMMITTED markdown file (`generated by aw index plans; do not edit by hand`) containing 0 ANSI bytes, so an artifact status appearing there is not human terminal output and is correctly out of this spec's scope per Section 9.5 and A14.
- Verified at review: `quarantined` is read from the `- Quarantine:` FIELD, not from `- Status:` (spec D15), confirmed at `ipd_lint.py:1123` (`S.is_quarantined(doc.meta_fields)`), so it is a Section 8 condition input. The lint DISPOSITION vocabulary it shares a column with is `conforming`/`advisory`/`quarantined`/`legacy/not evaluated`/`error` (`ipd_schema.py:1470-1472`), four of which are generic outcomes R10.3 excludes; see F-06.
- Verified at review: A14 is NOT uniformly satisfied. `aw find plans --agent` and `aw ipd lint --all --agent` emit 0 ANSI bytes, but `aw index plans --agent` emits 1 ANSI-bearing line, a live violation this child must fix rather than characterize.
- Verified at review: NONE of the five test files covering the converted modules contains a single `38;5;` assertion, so no shipped test pins any color this child changes. E-05 must ADD assertions. `tests/test_cli_find.py:104,118-119` asserts 214 but for a SEARCH-MATCH HIGHLIGHT, not a lifecycle status, so it must not be recomputed.
- SUITE BASELINE at review HEAD `f348b227`: `7468 passed, 3 skipped, 2 xfailed in 100.23s`. Compare node ids, not just counts.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `- Readiness:` is deliberately absent at authoring (it is `/plan-review`'s output; IPD-M107 refuses an unattested value). This review writes it.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | FOUR surfaces render lifecycle state through the fused path and keep doing so after `attention.py` converts, which is Section 1's problem restated: `aw find`, `aw ipd lint`, `aw set`, and the run views. CORRECTED AT REVIEW from "six modules": two of the six named modules render no lifecycle status at all (F-04). | `cli.py:9473,9534,9572`; `ipd_lint.py:1477`; `status_set.py:402,407`; `run_viewer.py:1350,1411,1806,2535`. |
| F-02 | Medium | No consumer holds its own status TABLE (no `STATUS_COLOR_256` outside `term.py`/`attention.py`), so there are no duplicate tables to delete here. But that does NOT make the work mere call-site routing, because hardcoded per-call lifecycle colors exist and the caller-set grep cannot see them (F-07). | `grep -rn "STATUS_COLOR_256"` excluding term/attention returns nothing; direct `color256` counts `plans_index` 1, `research_index` 1, `status_set` 4, `ipd_lint` 7, `run_viewer` 29. |
| F-03 | Medium | CORRECTED AT REVIEW. A14 is not uniformly satisfied, so E-05's "byte-identical before and after" bar is wrong for one command: `aw index plans --agent` emits ANSI TODAY. Left as written, the item would have either masked the leak or failed a correct fix. | Measured: `aw index plans --agent` -> 1 ANSI-bearing line (`^[[1;38;5;46mup to date^[[0m ...`); `aw find plans --agent` -> 0; `aw ipd lint --all --agent` -> 0. Source: `plans_index.py:429,432`. |
| F-04 | BLOCKER | ADDED AT REVIEW. THE PLAN'S SCOPE BASIS IS INVALID. It defined scope by grepping `status_256` callers, but `status_256` also styles GENERIC outcome words R10.3 explicitly excludes. All EIGHT calls in E-01's two modules render `up to date`/`wrote`/`updated`, and `status_set.py:396` renders `unchanged`. Routing them through the lifecycle resolver sends each to criterion A20's unknown path, printing `?` where a user reads `up to date` today: a REGRESSION delivered as compliance, in the plan's entire Task group 1. | `plans_index.py:432,436,440,446`; `research_index.py:650,654,658,664`; `status_set.py:396`. Each of `up to date`, `wrote`, `updated` greps to 0 in spec `uonrjg`. `uonrjg` R10.3 ("Generic `Term` outcomes... remain valid and are outside this spec. Do not mechanically replace every checkmark"); criterion A20. |
| F-05 | High | ADDED AT REVIEW. The colored artifact TYPE word raised against `attention.py` in child `f9t5hz` is REPLICATED in three of this child's modules, and no plan in the Set owned it. Criterion A10 says type is not lifecycle-colored and Section 11 item 5 limits color to glyph, id6 and status; the "existing independent convention" exemption covers the tree SEGMENT OF A PATH, not a bare type word, so relying on it makes A10 untestable across four views. | `status_set.py:453`, `ipd_lint.py:1508`, `run_viewer.py:1358` (and its import at `run_viewer.py:23`), all using `attention._TREE_COLOR_256` = 33 bold; the legitimate path-segment use at `attention.py:1729`. |
| F-06 | High | ADDED AT REVIEW. E-03 conflated two different columns and hid a real conflict. `ipd_lint.py` has one lifecycle `status_256` call (`- Status:`, `:1477`) and one DISPOSITION call (`:1520`) whose vocabulary mixes `quarantined` with four generic outcomes. Converting the column wholesale routes generic outcomes through the resolver (R10.3 forbids); converting only `quarantined` gives it gray 244, which is what `legacy/not evaluated` already falls back to, making it LESS distinguishable than today's 214 and cutting against Section 7.2's stated reason for listing it. | `ipd_lint.py:1477` vs `:1520`; `ipd_schema.py:1470-1472`; measured `term.STATUS_COLOR_256`: `conforming` 46, `quarantined` 214, `error` 196, `legacy/not evaluated` absent -> 244; spec `parked` = 244 + `◇`; Section 7.2 ("the lint view must show it without calling it a pass"). |
| F-07 | High | ADDED AT REVIEW. The `status_256` measurement sees a fraction of `run_viewer.py`'s lifecycle styling: 4 such calls against 29 direct `color256` calls, several painting lifecycle states with literals that CONTRADICT Section 5. Criterion A17 is unsatisfiable while they stand, and `qdd5jq`'s Set-level A17 assertion would fail against them. | `run_viewer.py:1628` and `:1847` use 214 for in-flight work where the spec's `active` is 220 and 214 means `waiting-input` ONLY; `:1401` uses 226 for `[review]` where `reviewing` is 220; `:1995` uses 40 where `ready` is 45. Spec Section 5's 11 indices are 39/45/46/81/135/196/208/214/220/244/245. |
| F-08 | High | ADDED AT REVIEW. In `aw find`, the id6 is hardcoded to 39 regardless of status, directly violating criterion A10's requirement that glyph, id6 and status share one resolved color. Unaddressed, the first converted view would still show a mismatched id6. | `cli.py:9475`, `:9536`, `:9573` (`color256(..., 39, bold=True)`); measured output `^[[1;38;5;46mexecuted^[[0m ^[[1;38;5;39md5tz36^[[0m`. Also `cli.py:9473` reads `e.disposition or e.status`, so that column can hold a disposition. |
| F-09 | Medium | ADDED AT REVIEW. No shipped test pins any color this child changes: all five test files covering the converted modules contain ZERO `38;5;` assertions. So E-05 must ADD escape-level assertions rather than refresh existing ones, and the conversion could otherwise regress silently. Two undeclared files DO assert escapes; one is a false alarm that must not be recomputed. | `grep -c '38;5;'` -> 0 in `tests/test_plans_index.py`, `tests/test_research_index.py`, `tests/test_status_set.py`, `tests/test_ipd_lint.py`, `tests/test_run_viewer.py`. `tests/test_cli_find.py:104,118-119` asserts 214 for a filename SEARCH-MATCH highlight (`cli._highlight_filename_matches`), not lifecycle; `tests/test_term_components.py:145-156` pins generic badge/path roles. |
| F-10 | Low | ADDED AT REVIEW. OQ-01 (does a distinct backlog index exist?) was deferred to execution but is answerable now: `aw index` supports ONLY `plans` and `research`, so R10.3's "spec index" and "backlog index" name commands that do not exist. | Measured across all nine types: every type other than `plans` and `research` answers `WARN 'index' is not supported for <type>`. Specs and backlog reach a human through `status_set.py` (which handles `record_type == "specs"` and `"backlog"`) and `attention.py`. |

## Proposed changes (ordered, validatable)

1. Record that the two indexes have no lifecycle terminal view, and fix their live A14 ANSI leak (E-01).
2. Convert the two lifecycle status calls in the setter, leaving `unchanged` alone (E-02).
3. Convert the lint `- Status:` column and record a justified decision for the mixed disposition column (E-03).
4. Convert the run views' `status_256` sites AND their hardcoded lifecycle colors, plus `aw find`'s status and id6 (E-04).
5. Add escape-level assertions, update snapshots, and prove machine output ANSI-free (E-05).

## Deferred / out of scope (with reason)

- Both runners and `render_stream.py`: child `qdd5jq`, because they are the largest surface (`oc_runipd.py` 7872 lines, `runner_shared.py` 12822, `render_stream.py` 2553) and carry the re-export chain that must be dismantled last.
  - Carrier: qdd5jq
- Deleting `term.py`'s `STATUS_COLOR_256`: also `qdd5jq`, per Section 12 step 6, which removes duplicate tables only after ALL consumers use the shared source. Deleting it here would break the unconverted runners.
  - Carrier: qdd5jq
- Generic `Term` OK/WARN/FAIL, and the index/setter outcome words `up to date`, `wrote`, `updated` and `unchanged`: R10.3 keeps them valid and outside this spec, and F-04 measures that routing them through the resolver would print `?` via criterion A20's unknown path.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by R10.3, which keeps these generic outcomes valid and warns against mechanically replacing every checkmark. There is no obligation to carry, and creating one would assert work the spec forbids.
- A "spec index" and a "backlog index" as named by R10.3: verified at review that `aw index` supports ONLY `plans` and `research`; every other type answers `WARN 'index' is not supported`. So these two name commands that do not exist and there is nothing to convert. Spec and backlog lifecycle reach a human through `status_set.py` (converted here, and it handles `record_type == "specs"` and `"backlog"`) and `attention.py` (converted by `f9t5hz`).
  - Carrier-Declined: NOTHING TO CONVERT, established by measurement rather than deferred to execution. The two commands do not exist, and both trees' lifecycle already reaches a human through surfaces this Set converts. OQ-01 is resolved accordingly.
- An `INDEX.md` marker column: `INDEX.md` is a COMMITTED markdown file, not human terminal output, and Section 9.5 plus criterion A14 keep committed and machine artifacts ANSI-free. Verified to contain 0 ANSI bytes today.
  - Carrier-Declined: OUT OF SCOPE BY THE SPEC'S OWN BOUNDARY. `uonrjg` governs human TERMINAL presentation; adding lifecycle styling to a committed file would violate Section 9.5, so there is no obligation to carry.

## Scope check

- Over-scope: CLOSED AT REVIEW. E-01 previously converted two modules whose every `status_256` call renders a generic outcome word R10.3 excludes (F-04); it now records that finding and fixes the real A14 leak instead. E-02's third call (`unchanged`) and E-03's disposition column are the same error in miniature and are likewise excluded by value.
- Under-scope: FOUR GAPS CLOSED AT REVIEW, each of which would have executed cleanly while leaving a release-gating criterion unmet. (1) The colored artifact TYPE word in three of these modules is a live A10 violation no plan in the Set owned (F-05). (2) `run_viewer.py`'s hardcoded lifecycle colors, four of which contradict Section 5, are invisible to the caller-set grep and block criterion A17 (F-07). (3) `aw find`'s id6 is hardcoded to 39 independent of status, violating A10 (F-08). (4) No shipped test pins any color this child changes, so E-05 must ADD assertions rather than refresh them (F-09).
- The remaining scope maps to R10.3, Section 9.1, and criteria A10/A14/A17/A20.

## Required tests / validation

Run the suite BARE: `python3 -m pytest` (no added flags). Paste the actual summary line and compare to the review baseline `7468 passed, 3 skipped, 2 xfailed` at HEAD `f348b227`, explaining any difference by node id.

Validation must show:
- **A14, with the correct per-command bar** (F-03): `aw find --agent`/`--json` and `aw ipd lint --agent`/`--json` stay at ZERO ANSI (characterization, measured 0 today), while `aw index plans --agent` and `aw index research --agent` move from 1 ANSI-bearing line to 0 (a fix, so its diff must NOT be empty).
- **A10 on every converted row**: status and id6 sharing one escape code, and the artifact TYPE carrying none. Assert on raw escapes, never on stripped text.
- **A17 readiness**: an enumeration of `run_viewer.py`'s direct `color256` calls classified lifecycle versus generic, with every lifecycle one converted. This is what makes `qdd5jq`'s Set-level A17 assertion able to pass.
- **The generic words survive unchanged**: `up to date`, `wrote`, `updated`, `unchanged` still render their current color and are NOT `?`.
- **NEW escape-level assertions** for each converted surface, since none exists today (F-09). `tests/test_cli_find.py:104,118-119` must be left alone (search-match highlight, not lifecycle).

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`.

TWO THINGS A CARELESS READING WOULD TURN INTO SPEC EDITS, and neither needs one. R10.3's mention of a "spec index" and a "backlog index" names commands that do not exist; that is a harmless imprecision in the spec's prose, not a contract this child can satisfy, and it is recorded in Deferred rather than amended. And Section 7.2's `quarantined` row is satisfiable as written once E-03 records its decision. HOWEVER, if E-03 concludes the disposition column must keep `quarantined` at 214 rather than adopt `parked`'s gray, that CONTRADICTS the spec's Section 7.2 table and D15, and would require amending `uonrjg` plus adding the spec path to `- Scope-Paths:`; report it rather than deciding it silently.

## Open questions

### OQ-01: Does a distinct backlog index view exist that R10.3 names but the measurement did not find?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier-Declined: RESOLVED AT REVIEW BY MEASUREMENT, so nothing outlives the plan and no execution-time investigation is needed. There is no backlog index and no spec index to convert; both trees' lifecycle already reaches a human through surfaces this Set converts.
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-19. ANSWER: NO, and no spec index either. Measured across all nine artifact types, `aw index` is supported ONLY for `plans` and `research`; every other type (`specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`, `comms`, `releases`) answers `WARN 'index' is not supported for <type>`. So R10.3's "plan/spec/research/backlog indexes" names two commands that do not exist, which is an imprecision in the spec's prose rather than an obligation. Spec and backlog lifecycle DO reach a human, through `status_set.py` (in this child's scope, and it branches on `record_type == "specs"` and `"backlog"` at `:516`, `:582`, `:603`) and through `attention.py` (converted by `f9t5hz`), so criterion A17 is satisfiable without a view that does not exist. NOTE THE QUESTION WAS WORTH ASKING: it was the right instinct, and the answer also disposes of the "plan/research index" half, since those two modules turn out to render no lifecycle status at all (F-04).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the recorded determination that neither index renders a lifecycle status, with `grep -n "status_256(" agent_workflows/plans_index.py agent_workflows/research_index.py` showing all eight calls and the literal word each passes. THEN paste the A14 fix: `aw index plans --agent | grep -c $'\033'` and the same for `research`, each returning 0, contrasted against the review measurement of 1. FINALLY paste `FORCE_COLOR=1 aw index plans | cat -v` proving `up to date` still renders its CURRENT color and is NOT `?`. Do NOT paste a "shared marker" for these commands: there is no lifecycle status here to mark, and fabricating one would be false evidence.
  - Observed evidence: VERIFIED 2026-09-20 by execution in lane `aw/lane/9zvl2w` (base HEAD `5ff889aa`). Neither index renders a lifecycle status; the real defect there was a live A14/A11 color leak, now fixed.

    THE DETERMINATION, CONFIRMED BY MEASUREMENT AND NOT CONVERTED. All eight calls survive, each
    passing a generic outcome word:

    ```text
    $ grep -n "status_256(" agent_workflows/plans_index.py agent_workflows/research_index.py
    agent_workflows/plans_index.py:468:            status_lbl = term.status_256("up to date", width=12)
    agent_workflows/plans_index.py:472:            status_lbl = term.status_256("wrote", width=12)
    agent_workflows/plans_index.py:476:            status_lbl = term.status_256("updated", width=12)
    agent_workflows/plans_index.py:482:            status_lbl = term.status_256("updated", width=12)
    agent_workflows/research_index.py:662:            status_lbl = term.status_256("up to date", width=12)
    agent_workflows/research_index.py:666:            status_lbl = term.status_256("wrote", width=12)
    agent_workflows/research_index.py:670:            status_lbl = term.status_256("updated", width=12)
    agent_workflows/research_index.py:676:            status_lbl = term.status_256("updated", width=12)
    ```

    Each word greps to ZERO in spec `uonrjg`, confirming R10.3 excludes them:

    ```text
    up to date   -> 0 hits
    wrote        -> 0 hits
    updated      -> 0 hits
    ```

    THE A14 FIX, measured before at 1 ANSI-bearing line and now 0:

    ```text
    $ for c in plans research; do python3 -m agent_workflows index $c --agent | grep -c $'\033'; done
    0
    0
    ```

    THE GENERIC WORD IS UNCHANGED IN COLOR AND IS NOT `?` (index 46 exactly as before):

    ```text
    $ FORCE_COLOR=1 python3 -m agent_workflows index plans | cat -v
    ^[[1;38;5;46mup to date^[[0m   ^[[38;5;33m.aw/records/plans/^[[0mINDEX.json, INDEX.md (698 plans)
    $ FORCE_COLOR=1 python3 -m agent_workflows index research | cat -v
    ^[[1;38;5;46mup to date^[[0m   ^[[38;5;33m.aw/records/research/^[[0mINDEX.json, INDEX.md (116 docs)
    ```

    THE LEAK WAS WIDER THAN THE REVIEW MEASURED, AND ITS ROOT CAUSE WAS A SECOND DEFECT. The review
    measured `--agent` only; measured at execution, the same forced `Term(color=not no_color)` leaked
    ANSI in FIVE modes (`--agent`, `--json`, `NO_COLOR=1`, `TERM=dumb`, and a plain pipe), so this was
    a criterion A11 violation as well as A14. AND `--agent` NEVER REACHED THE BACKEND AT ALL:
    `cli._nv_backend_args` set `sub.agent` from `getattr(args, "as_agent", False)`, a name NO parser in
    the package defines, so a true `args.agent` was overwritten with `False` for every noun-verb
    backend. Both are fixed; all six modes now emit 0:

    ```text
    index plans        --agent  -> 0      index research     --agent  -> 0
    index plans        --json   -> 0      index research     --json   -> 0
    index plans        (pipe)   -> 0      NO_COLOR=1 / TERM=dumb      -> 0 / 0
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste a status transition's echoed output with escapes visible (`FORCE_COLOR=1 ... | cat -v`) and the same status as rendered by `aw find`, showing an IDENTICAL escape code. Then paste the no-op line proving `unchanged` still renders its current color and did NOT become `?` (F-04). Also paste the artifact TYPE word from the same row showing it carries NO escape (F-05), or the written justification if the Section 11 exemption was claimed instead.
  - Observed evidence: VERIFIED 2026-09-20 by execution in lane `aw/lane/9zvl2w` (base HEAD `5ff889aa`). The setter and `aw find` now emit identical bytes for one status; `unchanged` keeps its generic gray; the type word is plain.

    THE TRANSITION ECHO AND `aw find` NOW AGREE BYTE FOR BYTE. Note `approved` renders
    `^[[1;38;5;45m` in BOTH, which is spec Section 5's `ready` (45), where the old table gave 46:

    ```text
    $ FORCE_COLOR=1 python3 -m agent_workflows set to-review 9zvl2w --dry-run | cat -v
    - >  plan        20260919-lifeglyph-06-9zvl2w  ^[[1;38;5;196m[blocking]^[[0m  ^[[1;38;5;45mapproved^[[0m M-bM-^FM-^R ^[[38;5;39mM-bM-^WM-^T^[[0m  ^[[38;5;39mto-review^[[0m  (dry-run)

    $ FORCE_COLOR=1 python3 -m agent_workflows find plans 9zvl2w | cat -v
    ^[[1;38;5;45mM-bM-^WM-^U^[[0m  ^[[1;38;5;45mpending^[[0m       ^[[1;38;5;45m9zvl2w^[[0m  lifeglyph       .aw/records/plans/pending/...
    ```

    The `to-review` end of that transition carries `^[[38;5;39m` on BOTH its glyph (`◔`, shown as
    `M-bM-^WM-^T` under `cat -v`) and its word, which is Section 9.1's "same lifecycle color and
    weight" holding structurally. Asserted as raw bytes by
    `tests/test_status_set.py::SharedLifecycleRenderingTests::test_the_setter_and_aw_find_render_one_identical_escape_for_one_status`.

    `unchanged` KEEPS ITS CURRENT GRAY 245 AND IS NOT `?`:

    ```text
    $ FORCE_COLOR=1 python3 -m agent_workflows set approved 9zvl2w --dry-run | cat -v
    - >  plan        20260919-lifeglyph-06-9zvl2w  ^[[1;38;5;196m[blocking]^[[0m  ^[[1;38;5;245munchanged^[[0m  (dry-run)
    ```

    NOTE A CORRECTION TO THE PLAN'S OWN CLAIM: the plan states `unchanged` "greps to 0" in the spec.
    Measured, it appears SEVEN times, but never as a status value: all seven are prose or workflow
    history ("STATUS DELIBERATELY UNCHANGED", "unchanged, and unconditional"). There is no table row
    and no backtick-quoted `` `unchanged` `` anywhere in the spec, so the CONCLUSION stands unchanged
    and only the supporting count was wrong.

    THE TYPE WORD CARRIES NO ESCAPE (visible above: bare `plan`, where the review measured
    `^[[1;38;5;33mplan^[[0m`). The Section 11 exemption was NOT claimed; the removal matches what
    `f9t5hz` did to `attention.py` for the same reason. Verified programmatically:

    ```text
    any tree-colored 'plan'?  False
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: THREE pastes. (1) The `- Status:` column rendering the shared marker, with escapes visible. (2) The recorded DECISION for the disposition column, naming which route was taken and why, and showing that `conforming`, `advisory` and `error` were NOT routed through the lifecycle resolver. (3) `aw ipd lint` output for a quarantined plan showing it is not reported as conforming, AND showing it remains distinguishable from `legacy/not evaluated`; if `parked`'s gray 244 was adopted, the `◇` glyph MUST be present, because both words then share one color (F-06). Paste `grep -n is_quarantined agent_workflows/ipd_lint.py` proving the value is still read from the `- Quarantine:` field, not `- Status:`.
  - Observed evidence: VERIFIED 2026-09-20 by execution in lane `aw/lane/9zvl2w` (base HEAD `5ff889aa`). The `- Status:` column is converted; the mixed disposition column is split BY VALUE with the decision recorded below.

    (1) THE `- Status:` COLUMN RENDERS THE SHARED MARKER. `approved` is `ready`: `◕` + 45, both cells
    one escape:

    ```text
    $ FORCE_COLOR=1 python3 -m agent_workflows ipd lint .aw/records/plans/pending/20260919-lifeglyph-06-9zvl2w-*.ipd.md | cat -v
    - >  ^[[1;38;5;45mM-bM-^WM-^U^[[0m  ^[[1;38;5;45mapproved^[[0m     plan        20260919-lifeglyph-06-9zvl2w  ^[[1;38;5;196m[blocking]^[[0m  ^[[1;38;5;46mconforming^[[0m
    ```

    (2) THE RECORDED DECISION: **ROUTE `quarantined` THROUGH THE RESOLVER; LEAVE THE OTHER FOUR
    GENERIC.** The column holds five words and exactly ONE is a value spec Section 7.2 claims.
    Converting wholesale would route four generic command outcomes through the lifecycle resolver,
    which R10.3 forbids in terms and which criterion A20 would render `?`; leaving the column entirely
    generic would leave the one spec-claimed value unconverted and make A17 unsatisfiable for this
    view. So the split is BY VALUE, the same rule E-01 and E-02 apply. The decision, its cost, and why
    the glyph is load-bearing are recorded in-code at `ipd_lint.py` (the `disp_word` branch). This
    does NOT require a spec amendment: it adopts Section 7.2 as written, which is the case the plan's
    spec-sync section says needs none.

    `conforming` KEEPS ITS GENERIC 46 (visible in the paste above), and the other generic dispositions
    keep theirs, proven by the untouched `status_256` call and by
    `tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_the_generic_dispositions_are_not_routed_through_the_lifecycle_resolver`,
    which also asserts NO `?` appears.

    (3) A QUARANTINED PLAN IS NOT REPORTED AS CONFORMING AND STAYS DISTINGUISHABLE FROM `legacy`.
    Measured against a fixture plan carrying a `- Quarantine:` field:

    ```text
    quarantined: -    ^[[1;38;5;45m◕^[[0m  ^[[1;38;5;45mapproved^[[0m     plan        20260920-qtest-01-qq1111  ^[[38;5;244m◇^[[0m ^[[38;5;244mquarantined^[[0m
    legacy     : -    ^[[1;38;5;46m✓^[[0m  ^[[1;38;5;46mexecuted^[[0m     plan        20260101-instsafe-07-qrokie  ^[[1;38;5;244mlegacy/not evaluated^[[0m
    ```

    `parked`'s gray 244 WAS adopted, so the `◇` glyph is present and is what carries the distinction:
    the two words now share one color and differ only by that glyph, exactly as F-06 predicted. The
    difference is asserted directly by
    `tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_quarantined_remains_distinguishable_from_legacy_not_evaluated`,
    and the glyph's presence with color OFF by `...::test_color_off_keeps_glyph_and_word_with_no_ansi`.

    THE VALUE IS STILL READ FROM THE FIELD, NOT FROM `- Status:`:

    ```text
    $ grep -n is_quarantined agent_workflows/ipd_lint.py
    1125:    if S.is_quarantined(doc.meta_fields) and not _is_terminal_dir(directory):
    1550:        # FIELD (`ipd_schema.is_quarantined`, consulted at `_with_name_check`), never by a `- Status:`
    ```

    (`:1550` is the explanatory comment; `:1125` is the live read, unchanged by this plan.) It is
    passed to the resolver as `condition=`, reaching Section 8's condition rung per D15.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: THREE pastes. (1) Run-view output covering the Section 7.2/7.3 states available in a real or fixture ledger, explicitly showing `ran` rendering `recovering` and `unknown_outcome` rendering `failed`, neither styled as success. (2) THE HARDCODED-COLOR ENUMERATION (F-07): `grep -n "color256(" agent_workflows/run_viewer.py` with each of the 29 sites classified lifecycle or generic, and every lifecycle one shown converted. Name the four that contradicted Section 5 (`:1628` and `:1847` at 214, `:1401` at 226, `:1995` at 40) and show what each renders now. (3) THE id6 FIX (F-08): an `aw find` row via `cat -v` showing status and id6 sharing ONE escape code, contrasted with the review measurement `^[[1;38;5;46mexecuted^[[0m ^[[1;38;5;39md5tz36^[[0m`.
  - Observed evidence: VERIFIED 2026-09-20 by execution in lane `aw/lane/9zvl2w` (base HEAD `5ff889aa`). Section 7.2/7.3 states render their spec stage, all four Section-5-contradicting literals are gone, and the id6 shares the status color.

    (1) RUN-VIEW OUTPUT over a seven-item fixture ledger. `ran` renders 220 (`recovering`) and
    `unknown_outcome` renders 196 (`failed`); NEITHER carries the success green 46 that `executed` does:

    ```text
    │ ^[[1;38;5;46mexecuted^[[0m        │ demo-aaa111 │ execute │ ... │ ^[[1;38;5;46myes^[[0m      │ ^[[1;38;5;196mYES^[[0m   │
    │ ^[[1;38;5;220mran^[[0m             │ demo-bbb222 │ execute │ ... │ -        │ ^[[1;38;5;196mYES^[[0m   │
    │ ^[[1;38;5;196munknown_outcome^[[0m │ demo-ccc333 │ execute │ ... │ -        │ ^[[1;38;5;196mYES^[[0m   │
    ```

    And the non-table step line, showing the glyph each takes (`↩︎` for `recovering`, `✘` for `failed`):

    ```text
    -    ^[[1;38;5;46m✓^[[0m  ^[[1;38;5;46mexecuted^[[0m            plan      demo-zzz999  ^[[1;38;5;46m[verified]^[[0m
    -    ^[[1;38;5;220m↩︎^[[0m  ^[[1;38;5;220mran^[[0m                 plan      demo-zzz999
    -    ^[[1;38;5;196m✘^[[0m  ^[[1;38;5;196munknown_outcome^[[0m     plan      demo-zzz999
    -    ^[[1;38;5;220m◎^[[0m  ^[[1;38;5;220mrunning^[[0m             plan      demo-zzz999  ^[[1;38;5;220m[review]^[[0m
    -    ^[[1;38;5;220m↩︎^[[0m  ^[[1;38;5;220mpartial^[[0m             plan      demo-zzz999  ^[[1;38;5;208mdependency-blocked^[[0m
    -    ^[[1;38;5;208m⚠︎^[[0m  ^[[1;38;5;208mblocked^[[0m             plan      demo-zzz999
    -    ^[[1;38;5;196m✘^[[0m  ^[[1;38;5;196mfailed^[[0m              plan      demo-zzz999  ^[[1;38;5;196m[verify-failed]^[[0m
    -    ^[[1;38;5;220m●^[[0m  ^[[1;38;5;220mrunning^[[0m             plan      demo-zzz999
    -    ^[[38;5;244m◇^[[0m  ^[[38;5;244mquarantined^[[0m         plan      demo-zzz999
    ```

    Fifteen Section 7.2 rows are asserted as raw bytes by
    `tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_section_7_2_statuses_render_their_spec_stage`,
    and the no-success claim separately by `...::test_ran_and_unknown_outcome_are_never_styled_as_success`.

    (2) THE HARDCODED-COLOR ENUMERATION. The 29 `color256` calls are now 22, and every remaining one is
    GENERIC. THE FOUR THAT CONTRADICTED SECTION 5 ARE GONE (measured by pattern, each returning 0):

    ```text
    "[in flight]", 214        -> 0 occurrences   (was :1628; 214 is `waiting-input`, active is 220)
    "YES (in flight)", 214    -> 0 occurrences   (was :1847; same collapse in the audit table)
    "[review]", 226           -> 0 occurrences   (was :1401; 226 is not a Section 5 index at all)
    f"[{p_state}]", 40        -> 0 occurrences   (was :1995; 40 is not a Section 5 index either)
    ```

    WHAT EACH RENDERS NOW, all four inside Section 5's eleven indices:

    ```text
    [in flight] / YES (in flight): ^[[1;38;5;220m[in flight]^[[0m       (active, 220)
    [review]                     : ^[[1;38;5;220m[review]^[[0m          (reviewing, 220)
    [<pid state>]                : ^[[1;38;5;220m[live: S]^[[0m         (run-ledger running, 220)
    [verified] / [verify-failed] : ^[[1;38;5;46m[verified]^[[0m ^[[1;38;5;196m[verify-failed]^[[0m
    ```

    The last pair are the two that matched Section 5 BY LUCK (46 = `done`, 196 = `failed`); their bytes
    are unchanged and now DERIVE from the table rather than coinciding with it.

    THE 22 SURVIVORS, CLASSIFIED GENERIC (R10.3 keeps these, criterion A18 protects them):
    `:1468` projected-status badge (208, an attribution warning, not a stage); `:1487` `[$cost]` and
    `:2040`/`:2496` cost lines (220 formatting); `:1741`/`:1749`/`:1808`/`:1852` the artifact-audit
    DIFFERENCE CLASSES (`_AUDIT_CLASS_COLOR`, a separate vocabulary owned by `artifact_audit`);
    `:1928`/`:1934`/`:1964`/`:1970` the `yes`/`no`/`YES` verification and issue VERDICTS (severity, not
    lifecycle); `:2003`/`:2008`/`:2015` refusal / remedy / incomplete severity;
    `:2024`/`:2030`/`:2061` dimmed detail lines (245); `:2086`/`:2488` run id and header (33);
    `:2560`/`:2721` phase and action names (226). `term.status_256` no longer appears in the module at
    all. Both facts are asserted STRUCTURALLY, over the module's own source, by
    `tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_no_second_lifecycle_table_or_hardcoded_lifecycle_index_remains`,
    which names the four banned literals so a reintroduction fails by name.

    (3) THE id6 FIX. Status and id6 now share ONE escape (46), where the review measured 46 beside 39:

    ```text
    $ FORCE_COLOR=1 python3 -m agent_workflows find plans d5tz36 | cat -v
    ^[[1;38;5;46mM-bM-^\M-^S^[[0m  ^[[1;38;5;46mexecuted^[[0m      ^[[1;38;5;46md5tz36^[[0m  -               .aw/records/plans/executed/20260704-advise-workflow-00-^[[1;38;5;214md5tz36^[[0m-advise-workflow-and-personas.ipd.md
    ```

    Review measurement, for contrast: `^[[1;38;5;46mexecuted^[[0m ^[[1;38;5;39md5tz36^[[0m`. The glyph
    (`✓`, `M-bM-^\M-^S`) carries the same 46, so all three A10 elements agree. The trailing
    `^[[1;38;5;214md5tz36^[[0m` inside the FILENAME is the search-match highlighter, deliberately
    untouched.

    TWO THINGS THE PLAN DID NOT ANTICIPATE, both handled by VALUE rather than by call site. FIRST, the
    plan's note that `cli.py` reads `e.disposition or e.status` is correct and bites: `pending` is a
    DIRECTORY name, not a plan status (measured: `pending/` holds 88 `approved` plans and 3
    `to-review`), so passing it to the resolver renders `?`. It is translated to the stage the directory
    means (`ready`), pinned by
    `tests/test_cli_find.py::FindLifecycleColumnTests::test_a_plans_directory_word_is_not_rendered_as_an_unknown_status`.
    SECOND, `aw find` lists types with NO lifecycle (`comms`, `walkthroughs`, `roadmaps`, `other`,
    `reviews`), which resolve `none` (`·`) and NOT `unknown` (`?`), per R10.4 and Section 6.7; pinned by
    `...::test_a_type_with_no_lifecycle_renders_none_not_unknown`.

    AND ONE MORE A17 HOLE CLOSED IN `cli.py`, FOUND WHILE VERIFYING. `aw search --short` renders the
    same `attention.Item` the board does, and was the FOURTH consumer of that object left on the old
    table after `f9t5hz` converted the other three, so the two views disagreed out loud: measured,
    `aw search --short` painted `approved` bright green 46 while `aw attention` painted the identical
    item 45 with a `◕`. It now routes through `attention._resolve_item_lifecycle`, and both emit
    `^[[1;38;5;45m` for that status. In scope (`cli.py` is declared) and claimed by no other plan in the
    Set, verified against `qdd5jq`'s `- Scope-Paths:`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the BARE `python3 -m pytest` summary line and compare to the baseline `7468 passed, 3 skipped, 2 xfailed` at HEAD `f348b227`, explaining any difference by node id. Then paste A14 per command WITH THE CORRECT BAR (F-03): an EMPTY `--agent`/`--json` diff for `aw find` and `aw ipd lint` (already 0 ANSI), and a NON-EMPTY diff for `aw index` showing the ANSI leak removed. Paste each updated human snapshot diff. FINALLY paste the NEW escape-level assertions added for each converted surface, with their node ids, since no such assertion existed before this child (F-09), and state that `tests/test_cli_find.py:104,118-119` was checked and left unchanged because it pins a search-match highlight rather than a lifecycle status.
  - Observed evidence: VERIFIED 2026-09-20 by execution in lane `aw/lane/9zvl2w` (base HEAD `5ff889aa`). Bare suite green; A14 proven per command with the correct bar; 35 new escape-level assertions added.

    THE BARE SUITE, run as `python3 -m pytest` with no added flags:

    ```text
    $ python3 -m pytest
    7588 passed, 3 skipped, 2 xfailed, 3 warnings in 99.83s (0:01:39)
    ```

    COMPARED TO THE BASELINE `7468 passed, 3 skipped, 2 xfailed` at HEAD `f348b227`: skips and xfails
    are IDENTICAL; passes rise by 120. The difference is fully accounted for by this child's 35 NEW test
    methods (several parameterized with `subTest`, which pytest counts per case) in six classes:
    `tests/test_plans_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests` (2),
    `tests/test_research_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests` (2),
    `tests/test_status_set.py::SharedLifecycleRenderingTests` (5),
    `tests/test_ipd_lint.py::SharedLifecycleRenderingTests` (7),
    `tests/test_run_viewer.py::SharedLifecycleRenderingTests` (14),
    `tests/test_cli_find.py::FindLifecycleColumnTests` (5). The remaining delta is the baseline's own
    drift between `f348b227` and this lane's base `5ff889aa`, which added the `f9t5hz` conversion
    tests. NO pre-existing test was deleted, skipped, or recomputed (`git diff --numstat` shows
    `-0` deletions for all six test files).

    ONE ENVIRONMENTAL CAVEAT, STATED PLAINLY. Run inside this OpenCode turn WITHOUT clearing the
    ambient environment, the suite reports `1 failed, 7587 passed`, the failure being
    `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`.
    That is the PRE-EXISTING defect filed as backlog `r67fl1`: the test inherits
    `OPENCODE_CONFIG_CONTENT` from the enclosing agent turn. PROVEN UNRELATED by stashing every change
    in this plan and re-running at the untouched base, which fails identically:

    ```text
    (with all 12 files stashed)  1 failed, 42 passed in 4.97s
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    (with the ambient var cleared, changes restored)  43 passed in 4.89s
    ```

    The `7588 passed` line above is from `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest`, which is
    the suite's own intended environment and the only difference from a bare invocation.

    A14 PER COMMAND, WITH THE CORRECT BAR PER F-03:

    ```text
    aw find plans       --agent  -> 0 ANSI lines   (characterization: was 0, stays 0)
    aw find plans       --json   -> 0 ANSI lines   (characterization)
    aw ipd lint --all   --agent  -> 0 ANSI lines   (characterization)
    aw ipd lint --all   --json   -> 0 ANSI lines   (characterization)
    aw index plans      --agent  -> 0 ANSI lines   (FIX: was 1 ANSI-bearing line)
    aw index plans      --json   -> 0 ANSI lines   (FIX: was 1)
    aw index research   --agent  -> 0 ANSI lines   (FIX: was 1)
    aw index research   --json   -> 0 ANSI lines   (FIX: was 1)
    aw runs             --agent  -> 0 ANSI lines   (characterization)
    aw runs             --json   -> 0 ANSI lines   (characterization)
    ```

    So `aw find` and `aw ipd lint` are byte-identical in machine mode (the right bar for them), while
    `aw index` CHANGED, which is the right bar for it: its diff is NOT empty because it leaked ANSI.

    NO HUMAN SNAPSHOT NEEDED UPDATING, and that is a measured finding rather than an omission: zero
    shipped tests asserted any color on these surfaces (F-09), so there was no snapshot to refresh.
    `git diff --numstat` confirms all six test files are pure additions:

    ```text
    tests/test_cli_find.py           +150 -0
    tests/test_ipd_lint.py           +139 -0
    tests/test_plans_index.py        +114 -0
    tests/test_research_index.py     +92  -0
    tests/test_run_viewer.py         +319 -0
    tests/test_status_set.py         +108 -0
    ```

    THE NEW ESCAPE-LEVEL ASSERTIONS, by node id (35 methods; each converted surface covered):

    ```text
    tests/test_plans_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_the_generic_outcome_words_are_never_rendered_as_an_unknown_lifecycle_glyph
    tests/test_plans_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_machine_and_suppressed_modes_emit_no_ansi
    tests/test_research_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_the_generic_outcome_words_are_never_rendered_as_an_unknown_lifecycle_glyph
    tests/test_research_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_machine_and_suppressed_modes_emit_no_ansi
    tests/test_status_set.py::SharedLifecycleRenderingTests::test_a_transition_renders_glyph_and_status_in_one_shared_color
    tests/test_status_set.py::SharedLifecycleRenderingTests::test_the_setter_and_aw_find_render_one_identical_escape_for_one_status
    tests/test_status_set.py::SharedLifecycleRenderingTests::test_the_no_op_word_unchanged_keeps_its_generic_color_and_is_not_a_question_mark
    tests/test_status_set.py::SharedLifecycleRenderingTests::test_the_artifact_type_word_carries_no_escape
    tests/test_status_set.py::SharedLifecycleRenderingTests::test_color_off_keeps_the_glyph_and_the_word_with_no_ansi
    tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_the_status_column_renders_the_shared_marker_and_color
    tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_the_artifact_type_word_carries_no_escape
    tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_quarantined_adopts_the_spec_parked_treatment_and_keeps_its_glyph
    tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_the_generic_dispositions_are_not_routed_through_the_lifecycle_resolver
    tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_color_off_keeps_glyph_and_word_with_no_ansi
    tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_agent_mode_emits_no_ansi
    tests/test_ipd_lint.py::SharedLifecycleRenderingTests::test_quarantined_remains_distinguishable_from_legacy_not_evaluated
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_section_7_2_statuses_render_their_spec_stage
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_ran_and_unknown_outcome_are_never_styled_as_success
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_a_running_item_takes_its_action_aware_activity
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_an_action_the_activity_table_does_not_know_falls_back_to_active
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_review_badge_no_longer_uses_a_non_spec_palette_index
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_two_verification_badges_derive_from_the_table_not_from_luck
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_a_disposition_shares_the_shared_vocabulary
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_artifact_type_word_carries_no_escape
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_cost_badge_stays_generic
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_color_off_keeps_glyph_and_word_with_no_ansi
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_variation_selector_survives_rendering
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_glyph_pads_by_rendered_width_not_code_points
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_no_second_lifecycle_table_or_hardcoded_lifecycle_index_remains
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_audit_and_analytics_tables_share_the_same_vocabulary
    tests/test_run_viewer.py::SharedLifecycleRenderingTests::test_the_run_views_emit_no_ansi_in_machine_modes
    tests/test_cli_find.py::FindLifecycleColumnTests::test_status_glyph_and_id6_share_one_resolved_color
    tests/test_cli_find.py::FindLifecycleColumnTests::test_a_plans_directory_word_is_not_rendered_as_an_unknown_status
    tests/test_cli_find.py::FindLifecycleColumnTests::test_a_type_with_no_lifecycle_renders_none_not_unknown
    tests/test_cli_find.py::FindLifecycleColumnTests::test_color_off_keeps_glyph_and_word_with_no_ansi
    tests/test_cli_find.py::FindLifecycleColumnTests::test_machine_modes_emit_no_ansi
    ```

    TWO OF THESE WERE PROVEN NON-VACUOUS BY DELIBERATE REVERSION, not merely observed to pass. With the
    E-01 color decision temporarily reverted to the old `Term(color=not no_color)`, the index test fails
    with exactly the defect it names:

    ```text
    FAILED tests/test_plans_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_machine_and_suppressed_modes_emit_no_ansi
    AssertionError: '\x1b' unexpectedly found in '\x1b[1;38;5;46mwrote\x1b[0m ... ' : criterion A14/A11
    violation: `aw index plans` emitted ANSI in --agent mode.
    ```

    And `test_the_glyph_pads_by_rendered_width_not_code_points` caught a real error in its OWN first
    draft: it measured `str.index` (CODE POINTS) rather than rendered columns, and so failed against
    correct output. That is the exact `len()`-as-width confusion Section 9.4 and `term.visible_width`
    exist to remove; the test now measures `visible_width` and the mistake is recorded in its docstring.

    `tests/test_cli_find.py:104,118-119` WAS CHECKED AND LEFT UNCHANGED. It asserts
    `\033[1;38;5;214mki6tom\033[0m` for a filename SEARCH-MATCH highlight produced by
    `cli._highlight_filename_matches`, which is a text-match highlighter and not a lifecycle status, so
    its 214 must NOT be recomputed from the lifecycle table. `git diff tests/test_cli_find.py` shows
    ZERO removed lines, confirming nothing there was touched, and the new class's docstring records why
    it must stay that way. `tests/test_term_components.py:145-156` was also checked: it pins generic
    badge/path roles and is unaffected (this plan declares no edit to it).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved 9zvl2w --by-human`). Its `- Item-Dependencies: executed:f9t5hz` edge is re-checked at dispatch, sequencing it after the attention conversion per Section 12 steps 3 and 4. The edge is load-bearing rather than nominal for two measured reasons: `f9t5hz` establishes the conversion pattern these four surfaces copy, and three of this child's modules import `attention.py`'s private `_TREE_COLOR_256` (`status_set.py:453`, `ipd_lint.py:1508`, `run_viewer.py:23,1358`), so the A10 type-column decision made there governs the same decision here and the two must not diverge.

OPEN QUESTIONS: OQ-01 is RESOLVED at review by measurement (there is no backlog index and no spec index; `aw index` supports only `plans` and `research`). There is no blocking question on this child. NOTE THE SET CONTEXT, which is not this plan's to resolve: the transitive chain `f9t5hz` -> `bn026f` -> `udgilu`/`pow5sj` carries two unresolved `- Blocking: yes` questions upstream, so this child cannot dispatch until those are ruled on regardless of its own readiness. Do not attempt to clear that by editing this file.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:`. An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. In particular: do NOT route the generic outcome words (`up to date`, `wrote`, `updated`, `unchanged`) or the generic lint dispositions (`conforming`, `advisory`, `error`, `legacy/not evaluated`) through the lifecycle resolver, because R10.3 excludes them and F-04 measures that doing so prints `?` via A20's unknown path; do NOT delete `term.py`'s `STATUS_COLOR_256` (that is `qdd5jq`'s, after every consumer converts, and deleting it here breaks the unconverted runners); do NOT touch `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py` or `render_stream.py` (also `qdd5jq`); do NOT add lifecycle styling to `INDEX.md`, a committed file Section 9.5 keeps ANSI-free; and do NOT recompute `tests/test_cli_find.py:104,118-119`, which pins a filename search-match highlight rather than a lifecycle status. DO STOP AND REPORT for one genuinely unsafe condition: if the shared helpers `f9t5hz` consumed are absent or shaped differently than E-02/E-04 expect, report that rather than reintroducing a per-call hardcoded palette index, which is the defect F-07 exists to remove.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a rendered view, an ANSI count, or a `color256` enumeration you did not run. A `V-*` evidence block must contain real output, not a description of expected output. Two specific prohibitions follow from this review's measurements: do NOT paste a "shared lifecycle marker" for `aw index`, which renders no lifecycle status at all, and do NOT report A14 as "byte-identical before and after" for `aw index`, whose diff MUST change because it leaks ANSI today.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
