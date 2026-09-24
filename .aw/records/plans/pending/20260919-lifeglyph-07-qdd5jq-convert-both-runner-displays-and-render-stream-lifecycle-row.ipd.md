# IPD: Convert both runner displays and render_stream lifecycle rows then delete every duplicate table

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 12 step 5 converts the runner displays and `render_stream.py` last, and step 6 deletes the duplicate tables only after every consumer is off them. This child is where the spec's Section 1 complaint is most concretely true: `render_stream.py:51 _STATUS_COLOR` maps `approved`, `reviewed`, `executed`, and `substantially-complete` ALL to green (verified 2026-09-19), which collapses exactly the readiness-versus-completion distinction Section 5 exists to prevent ("Green is reserved for successful completion. Ready work is cyan, not green"). That table is re-exported into both drivers (`oc_runipd.py:104` and its `__all__` at 447, `agy_runipd.py:104`, `runner_shared.py:168`, consumed at `runner_shared.py:12789`), so one wrong palette currently reaches every runner view.
- Scope: IN: convert lifecycle item and statusline rendering in `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py`, and `render_stream.py` to the shared resolver, including the `Palette.status()` method and the hardcoded glyph/success-color pair in the run-finish line; dismantle the `_STATUS_COLOR` re-export chain; SPLIT `term.py`'s `STATUS_COLOR_256` so the lifecycle keys leave and the generic role keys are retained under a non-lifecycle name; fix `render_stream._one_line`'s variation-selector-severing clip, inherited from child `bn026f`; repair the shipped palette test this necessarily breaks; and assert criterion A17 by CONTENT rather than by symbol name. OUT: `render_stream.py`'s EVENT glyphs and severity colors including `STATUS_GLYPHS`/`_status_glyph_char`, which R10.3 explicitly permits it to retain because they are not lifecycle semantics; DELETING `term.py`'s generic role keys, which R10.3 keeps valid; and any change to run outcome vocabulary, exit codes, report sections, or `INTEGRATION_ACTION_KINDS`, which the spec's Section 0.5 override explicitly does not touch.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/render_stream.py, agent_workflows/term.py, tests/test_render_stream.py, tests/test_runner_shared.py, tests/test_term_components.py, tests/test_term.py
- Item-Dependencies: executed:9zvl2w
- Status: approved
- Work-Kind: feature
- Priority: medium
- Blocks-Release: next
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qdd5jq
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: uonrjg

## Workflow history
- 2026-09-24 approved (aw set): backfill: Priority/Work-Kind per planprio-03 lc4unl maintainer decision on OQ-05 (lifeglyph: medium/feature)
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-701..PR-710 all FIXED, none deferred, none open. E-04 said DELETE term.py's STATUS_COLOR_256, a BLOCKER: only one of its four readers is lifecycle, so deleting it removes the command-outcome banner, every badge and all path styling while reporting A17 satisfied; parent 2xz59a had already ruled it must SPLIT and named this child. Three under-scope gaps: Palette.status() is a second, public reader of _STATUS_COLOR re-exported into both drivers; render_stream._one_line's VS-severing clip was assigned here by bn026f and was uncarried; and the run-finish line hardcodes the success glyph and green, so the F-01 collapse survives the conversion. E-03 was not implementable as worded because INTEGRATION_ACTION_KINDS holds only two of A3's five activities. A17 now asserted by content, not by symbol name. OQ-01 resolved by splitting ambiguous-width from the deterministic variation-selector defect. Readiness go-pending-approval.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701 through PR-710 all FIXED, none deferred, none open. Reviewed at HEAD `67ac3495`; `aw ipd lint --phase author --agent` clean, exit 0, before and after. THE DIAGNOSIS IS RIGHT AND F-01 IS THE BEST FINDING IN THE SET: the live runner palette really does map `approved`, `reviewed`, `executed` and `substantially-complete` all to green, collapsing exactly the readiness-versus-completion distinction Section 5 exists to protect. But E-04 said DELETE `term.py`'s `STATUS_COLOR_256`, and that is a BLOCKER (PR-704): only ONE of its four reads is lifecycle, while `format_outcome` (`:394`), `badge` (`:469`) and `format_path` (`:477`) are generic roles R10.3 keeps and this plan's OWN Deferred section already excluded, so the plan contradicted itself and would have deleted `aw`'s command-outcome banner, every bracketed badge, and all path styling while reporting A17 satisfied. Parent `2xz59a` had already ruled on this and named THIS child ("E-04 must SPLIT this table... A17 is satisfied when no second LIFECYCLE table remains, not when the string is absent"); E-04 now splits it, with the 32/24 key classification measured at review so the split is reproducible. THREE UNDER-SCOPE GAPS: `Palette.status()` at `render_stream.py:88` is a SECOND reader of `_STATUS_COLOR`, public and re-exported into both drivers, so removing the table without it breaks a public surface (PR-705); `render_stream._one_line`'s variation-selector-severing clip was explicitly assigned to this plan by `bn026f` (`Carrier: qdd5jq`) and this plan mentioned it ZERO times (PR-706); and the run-finish line hardcodes `glyph = "✓" if reached_success` and `"green" if reached_success` (`runner_shared.py:14047-14050`), so the F-01 collapse SURVIVES the table conversion at the one line printed at the end of every run. E-03 was not implementable as worded (PR-707): `INTEGRATION_ACTION_KINDS` is exactly `('execute','review')`, so `action` carries only TWO of criterion A3's five activities, and the other three live on `verification_status`, `integration_signal` and the retry state; the item now derives each from its own field and requires an honest partial to be REPORTED rather than claimed. V-04's `grep STATUS_COLOR_256` guard both false-passes and false-fails, so A17 is now asserted by CONTENT (PR-708), and E-04 breaks a shipped test in an undeclared file three ways, now declared (PR-709). One line number had drifted +1260 (`runner_shared.py:12789` -> `:14049`). OQ-01 resolved by splitting it: three of five activity glyphs are ambiguous-width (not two) and that half is declined on Section 9.4's own terms, while `↩︎`'s variation selector misaligns DETERMINISTICALLY and is now in scope. Baseline `7468 passed, 3 skipped, 2 xfailed`. Readiness go-pending-approval.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 12 steps 5-6, R10.3, and criteria A17/A18. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Move the runner and stream lifecycle rows onto the shared resolver and then remove every duplicate lifecycle table, so criterion A17 holds and the readiness-versus-completion collapse in the current runner palette is gone.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The stream renderer

- [x] E-01 Convert `render_stream.py` lifecycle rendering to the shared resolver, and SEPARATE it from the event glyphs and severity colors that module legitimately keeps. Remove `_STATUS_COLOR` (`render_stream.py:51`) once BOTH of its readers are converted. Also fix `_one_line`'s variation-selector-severing clip, which child `bn026f` assigned to this plan.
  - Depends on: none
  - Expected outcome: Lifecycle rows render through the shared resolver; event glyphs and severity colors are untouched and still pass their own tests (criterion A18). `approved` no longer shares a color with `executed`. Clipping a VS-bearing string no longer drops U+FE0E.
  - Execution state: performed

  THERE ARE TWO READERS IN THIS MODULE, NOT ONE, and the second is a PUBLIC method re-exported into both drivers (F-05). Measured: `render_stream.py:88` is `Palette.status()`, which does `_STATUS_COLOR.get(status)`, and it is called at `render_stream.py:2269` (`pal.status(st_val)`) in the item summary table. `Palette` itself is re-exported (`oc_runipd.py:106`, `__all__` at `:449`) and instantiated in the drivers (`oc_runipd.py:1324`, `:2018`, `:2057`), so removing the table without converting this method breaks a public surface. Convert `Palette.status()` or remove it deliberately; do not discover it when the import fails.

  THE `_one_line` OBLIGATION IS INHERITED AND WAS UNCARRIED (F-06). Child `bn026f`'s review deferred `render_stream._one_line`'s clip with `Carrier: qdd5jq`, this plan, because `bn026f` may not touch this file. Measured there and re-measured here: `_one_line` (`render_stream.py:222-227`) clips with `collapsed[: limit - 1]`, which severs a base character from its following variation selector when the boundary falls between them, so `⚠︎` and `↩︎` lose U+FE0E. This plan mentioned it zero times before review. Use `bn026f`'s VS-safe truncation primitive rather than writing a second one, which Section 9.4 forbids.

  ALSO NOTE `STATUS_GLYPHS` IS A TRAP, NOT A TARGET. `render_stream.py:170-181` defines `STATUS_GLYPHS`/`STATUS_GLYPHS_ASCII` keyed `completed`/`error`/`running`/`other`, which are TOOL-EVENT outcomes, not artifact lifecycle states, and `_status_glyph_char` maps them to green/red/yellow/gray. R10.3 explicitly permits this module to keep event glyphs, and criterion A18 requires proving they were not remapped. The keys `running` and `error` LOOK like lifecycle words, so a grep-driven edit would fold a tool-event table into lifecycle styling, which is precisely what A18 exists to catch. Leave both tables and `_status_glyph_char` alone.

### Task group 2: The runner displays

- [x] E-02 Dismantle the `_STATUS_COLOR` re-export chain: remove the import at `oc_runipd.py:104` and its `__all__` entry at `:447`, the aliased import at `agy_runipd.py:104`, and the import at `runner_shared.py:168`, converting the consumption site at `runner_shared.py:14049` to the shared resolver.
  - Depends on: E-01
  - Expected outcome: No module re-exports a lifecycle palette. The disposition styling in the run-finish line resolves through the shared module, including the Section 7.2 rows for `ran`, `unknown_outcome`, `needs_input`, and `awaiting-human`.
  - Execution state: performed

  THE CONSUMPTION SITE HAD DRIFTED BY +1260 LINES and is corrected above (`runner_shared.py:12789` -> `:14049`); the plan's other four numbers still hold. LOCATE EVERY SITE BY GREP, not by a number quoted here: `grep -rn "_STATUS_COLOR\b" agent_workflows/` is the durable locator and returns exactly eight matches today (the definition, a docstring mention at `render_stream.py:8`, two readers inside `render_stream.py`, three imports/aliases, one `__all__` entry, and the `runner_shared.py` consumption site). V-02 requires that grep as evidence.

  THE SITE ALSO HARDCODES A GLYPH AND A SUCCESS COLOR, which the item's wording did not cover. At `runner_shared.py:14047-14050` the finish line computes `glyph = "✓" if reached_success else "●"` and `glyph_color = "green" if reached_success else _STATUS_COLOR.get(disposition, "yellow")`. So even after the table lookup is converted, a literal `✓`/`●` pair and a literal `green` remain, and a `reached_success` item would bypass the resolver entirely. Route BOTH the glyph and the color through the shared resolver, or criterion A17 still fails here and the readiness-versus-completion collapse F-01 describes survives in the one line a user sees at the end of every run.

- [x] E-03 Convert the remaining lifecycle item and statusline rendering in both drivers to the shared resolver, applying the Section 7.1 action-aware activity rule. Derive each activity from the field that actually carries it, NOT from `action` alone, and fall back to generic `active` only where no signal exists.
  - Depends on: E-02
  - Expected outcome: A live runner view names the specific activity when a signal for it exists, and generic `active` otherwise. A plan being executed still displays its STORED status unchanged (criterion A7), because the runner must not mutate an artifact to produce a display.
  - Execution state: performed

  `action` CARRIES ONLY TWO OF THE FIVE ACTIVITIES, measured at review, so the item as originally worded was not implementable from the field it implied (F-07). `runner_shared.INTEGRATION_ACTION_KINDS` is exactly `('execute', 'review')`. The other three activities exist in the runner but on DIFFERENT fields:

  ```text
  reviewing    action == "review"                     INTEGRATION_ACTION_KINDS
  executing    action == "execute"                    INTEGRATION_ACTION_KINDS
  verifying    item["verification_status"]            runner_shared.py:11394
  integrating  item["integration_signal"]             runner_shared.py:1466
  recovering   retry / correction_required state      the retry ladder (DEFAULT_INTEGRATION_RETRY_LIMIT etc.)
  ```

  So the mapping is a per-signal decision, and an agent reading only `action` would either emit `active` for three of the five (silently failing criterion A3) or invent action values that do not exist. WHAT THIS ITEM MUST NOT DO: add a new action kind to `INTEGRATION_ACTION_KINDS` to make the display neater. That is a runner VOCABULARY change, which spec Section 0.5 bounds out ("covers DISPLAY only") and this plan's own Deferred section excludes.

  CRITERION A3 MAY NOT BE FULLY SATISFIABLE HERE, and that must be REPORTED rather than papered over. A3 asks that all five activities "render as `◎`, `▶`, `◆`, `⇄`, `↩︎` respectively, with their exact activity words". If a signal for one of the three non-`action` activities cannot be reached at the render site without a data-flow change beyond presentation, render generic `active` there and SAY SO in V-03's evidence, naming the activity and the missing signal. Section 7.1 itself permits generic `running`/`active` "only when the subtype is genuinely unavailable", so an honest partial is conforming; a claim that all five render when three were never wired is not.

### Task group 3: Delete the duplicates and prove it

- [x] E-04 SPLIT `term.py`'s `STATUS_COLOR_256`: move the LIFECYCLE keys out (they are now served by `lifecycle_style.py`) and RETAIN the generic command-outcome and formatting roles under a non-lifecycle name. Do NOT delete the symbol outright.
  - Depends on: E-03
  - Expected outcome: One LIFECYCLE table exists in the package, in `lifecycle_style.py`. A separate, clearly-named generic role table still serves `format_outcome`, `badge` and `format_path`, and those three keep working unchanged.
  - Execution state: performed

  DELETING IT OUTRIGHT BREAKS THREE WORKING, IN-SPEC FEATURES, and the parent orchestrator already ruled on this (F-04). Measured: `term.py` reads `STATUS_COLOR_256` at four sites and only ONE is lifecycle.

  ```text
  term.py:287  status_256      LIFECYCLE  -> served by lifecycle_style after 9zvl2w/f9t5hz
  term.py:394  format_outcome  GENERIC    -> command-level OK/WARN/FAIL banner
  term.py:469  badge           GENERIC    -> arbitrary caller-supplied role_or_code
  term.py:477  format_path     GENERIC    -> the "paths" role (33)
  ```

  Verified by execution that all three generic paths resolve through this table today: `format_outcome("ok","done")` -> `\x1b[1;38;5;46m✓ OK\x1b[0m  done`, `badge("RULE","error")` -> `[\x1b[1;38;5;196mRULE\x1b[0m]`, `format_path(".aw/x")` -> `\x1b[38;5;33m.aw/x\x1b[0m`. R10.3 keeps exactly these ("Generic `Term` outcomes such as command-level OK, WARN, and FAIL remain valid and are outside this spec"), and this plan's own Deferred section already excludes them, so E-04 as written contradicted its own plan. Parent `2xz59a` states the requirement directly and names this child: "child `qdd5jq`'s E-04 must SPLIT this table, retaining the generic roles under a non-lifecycle name and moving only the lifecycle keys, rather than deleting the symbol outright. A17 is satisfied when no second LIFECYCLE table remains, not when the string `STATUS_COLOR_256` is absent."

  THE SPLIT IS MEASURED, so the executor does not have to judge each key. Classifying all 56 keys by whether the key is named in a spec Section 6 or 7 mapping row gives 32 lifecycle and 24 generic:

  ```text
  LIFECYCLE (32): active approved archived blocked complete deferred dependency-blocked done draft
                  executed failed failed-safely implemented implementing intake interrupted
                  not-executed open parked partial pending planned queued reference reusable
                  reviewed running shipped substantially-complete superseded to-review todo
  GENERIC   (24): action advisory conforming conforms current error fail failure info legacy ok
                  path paths preview quarantined ready secondary success unchanged
                  "up to date" updated warn warning wrote
  ```

  TWO KEYS NEED A JUDGEMENT CALL rather than mechanical placement, recorded so the split is reproducible. `ready` is a spec STAGE NAME, not any tree's native status (verified: no tree's `CLASS_MAPS` contains a status matching `ready`), so as a `term.py` KEY it is a generic role word and belongs with the generic set. `quarantined` is a Section 8 CONDITION input carried by a `- Quarantine:` field rather than a `- Status:` value (spec D15), and child `9zvl2w` owns the decision about how the lint view renders it; keep the key generic here and let that child's decision govern the rendering. NOTE the parent's own count ("22 generic") was derived by substring-matching the spec text and is not reproducible; use the 32/24 split above, which is derived from the mapping-table rows.

- [x] E-05 Add the criterion A17 and A18 guard tests, and REPAIR the shipped palette test that E-04 necessarily breaks. The A17 guard must assert by CONTENT (no second table maps a lifecycle status to a color or glyph), not by the string `STATUS_COLOR_256`, because a name-based assertion both false-passes and false-fails after the split.
  - Depends on: E-04
  - Expected outcome: A test that FAILS if a future change reintroduces a local lifecycle palette, and that PASSES with the retained generic role table present. Severity and event visuals proven independent rather than assumed so. The whole suite green.
  - Execution state: performed

  A NAME-BASED A17 GUARD IS THE WRONG INSTRUMENT, for two measured reasons (F-08). FALSE PASS: the generic roles must survive E-04's split under some name, so `grep STATUS_COLOR_256` returning nothing proves only that a STRING is gone, while a renamed table could still map `approved` to a color. FALSE FAIL: `attention.py` also defines `_STATUS_COLOR_256` (removed by `f9t5hz`), so the grep's result depends on a sibling child rather than on this one. Assert the PROPERTY: for every native status in `lifecycle_style`'s mappings, no module other than `lifecycle_style` contains a dict mapping that status to a color index or a glyph.

  E-04 BREAKS A SHIPPED TEST IN AN UNDECLARED FILE, THREE WAYS, and it is now declared (F-09). `tests/test_term_components.py::PaletteSingleSourceTests` currently passes (verified: 16 passed) and asserts all of: `palette["approved"] == 46` (the spec moves `approved` to 45), `palette["active"] == 39` (the spec moves `active` to 220), and at `:68-73` that the ONLY `COLOR`-named dict in `term.py` is exactly `["STATUS_COLOR_256"]`. That last assertion fails under EITHER route: deleting the symbol leaves `[]`, and splitting it adds a second `COLOR` dict. Its docstring ("Exactly one palette exists") encodes a premise this Set deliberately replaces, so REWRITE it to assert the new invariant (one LIFECYCLE source plus one generic role table) rather than deleting it, and say which in V-05.

  ALSO RE-POINT OR RETIRE `tests/test_term.py`'s parity test IF `f9t5hz` did not. That test reads `attention._STATUS_COLOR_256` and `term.STATUS_COLOR_256`; `f9t5hz` owns it and this child removes the second symbol, so verify at execution that it no longer references either and fix it here if it still does. Check, do not assume, because a stale reference fails at import with an `AttributeError` rather than as a palette mismatch.

## Project conventions discovered (Step 0)

- Verified at review 2026-09-19 at HEAD `67ac3495`: `render_stream.py:51 _STATUS_COLOR` maps `executed`, `reviewed`, `approved`, and `substantially-complete` all to `green`, which is the readiness/completion collapse the spec's Section 5 forbids.
- Verified at review: the chain is `render_stream._STATUS_COLOR` (def `:51`) -> `oc_runipd.py:104` (+ `__all__` at `:447`), `agy_runipd.py:104` (aliased), `runner_shared.py:168` -> consumed at `runner_shared.py:14049`. THE CONSUMPTION LINE HAD DRIFTED +1260 (plan said `12789`); the other four numbers hold. There are also TWO readers INSIDE `render_stream.py` that the plan did not name: `Palette.status()` at `:88`, called at `:2269`. `grep -rn "_STATUS_COLOR\b" agent_workflows/` returns 8 matches and is the durable locator.
- Verified at review: `term.py`'s `STATUS_COLOR_256` is read at FOUR sites and only ONE is lifecycle (`status_256`, `:287`); `format_outcome` (`:394`), `badge` (`:469`) and `format_path` (`:477`) are generic roles R10.3 keeps. So E-04 SPLITS rather than deletes; parent `2xz59a` states this requirement and names this child.
- Verified at review by classifying all 56 keys against the spec's Section 6/7 mapping rows: 32 lifecycle keys, 24 generic. `ready` is a spec STAGE name and not any tree's native status, so as a `term.py` key it is generic; `quarantined` is a Section 8 condition input whose rendering `9zvl2w` owns.
- Verified at review: `runner_shared.INTEGRATION_ACTION_KINDS` is exactly `('execute', 'review')`, so `action` carries only TWO of criterion A3's five activities. `verifying` comes from `item["verification_status"]` (`runner_shared.py:11394`), `integrating` from `item["integration_signal"]` (`:1466`), and `recovering` from the retry/correction state. E-03 must derive each from its own field.
- Verified at review: `render_stream.py:170-181` `STATUS_GLYPHS`/`STATUS_GLYPHS_ASCII` are keyed `completed`/`error`/`running`/`other` and are TOOL-EVENT outcomes, not lifecycle. R10.3 permits them and criterion A18 requires proving they were not remapped. Two of their keys look like lifecycle words, so they are a grep trap; leave them and `_status_glyph_char` alone.
- Verified at review: `render_stream._one_line` (`:222-227`) clips with `collapsed[: limit - 1]`, severing a base character from its variation selector. Child `bn026f` deferred this with `Carrier: qdd5jq`, meaning THIS plan, which mentioned it zero times before review.
- Verified at review: three of criterion A3's five activity glyphs are East Asian Width AMBIGUOUS (`◎` U+25CE, `▶` U+25B6, `◆` U+25C6), not two as OQ-01 implied, and `↩︎` is TWO code points. The statusline pads with bare `len()` (`render_stream.py:936-942`), so the VS case misaligns deterministically while the ambiguous cases are terminal-dependent. These are different problems with different fixes; see OQ-01.
- File sizes make this the largest child: `runner_shared.py` 12822 lines, `oc_runipd.py` 7872, `agy_runipd.py` 4327, `render_stream.py` 2553. The E-items are split by module and by concern so each is executable in one focused pass.
- Four plans touch `render_stream.py` or the runners (`r2i1b1` and `st5klo` already executed; `ys1dor` and `zzcrlo` still pending as of 2026-09-19). Spec Section 12a classifies this as MERGE FRICTION ONLY, not an ordering hazard, because each execute item gets an isolated worktree and returns through the merge-and-revalidate gate.
- `render_stream.py` already carries a measured `use_unicode` ASCII-substitution pattern, which spec Section 9.4 names as the route to reuse for ASCII mode.
- SUITE BASELINE at review HEAD `67ac3495`: `7468 passed, 3 skipped, 2 xfailed in 109.52s`. Focused baseline for the four declared test files (`test_render_stream`, `test_runner_shared`, `test_term_components`, `test_term`): `266 passed in 26.07s`. Compare node ids, not just counts.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `- Readiness:` is deliberately absent at authoring (it is `/plan-review`'s output; IPD-M107 refuses an unattested value). This review writes it.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The live runner palette collapses `approved` (ready) and `executed` (complete) into one green, which is the precise distinction spec Section 5 was written to protect, and it currently reaches every runner view through the re-export chain. The collapse ALSO survives the table conversion at one site, because the run-finish line hardcodes `"green" if reached_success`. | `render_stream.py:51-55`; re-exported at `oc_runipd.py:104`, `agy_runipd.py:104`, `runner_shared.py:168`; the literal at `runner_shared.py:14047-14050`. |
| F-02 | High | `term.py`'s `STATUS_COLOR_256` cannot be touched before this child, because the unconverted runners still reach lifecycle styling through `term.py`. Section 12 step 6 sequences it last for this reason. CORRECTED AT REVIEW: the action is a SPLIT, not a deletion (F-04). | Section 12 step 6; the `status_256`/`status_label` caller set measured in child `9zvl2w`. |
| F-03 | Medium | `render_stream.py` legitimately owns non-lifecycle visuals (event glyphs, severity colors, `STATUS_GLYPHS`) that R10.3 permits it to keep, so a blunt "remove the palette" edit here would delete working, in-spec behavior. Two `STATUS_GLYPHS` keys (`running`, `error`) look like lifecycle words, which makes it a grep trap. | R10.3: "`render_stream.py` MAY retain event glyphs and severity colors that are not lifecycle semantics"; criterion A18; `render_stream.py:170-181`, `_status_glyph_char` at `:184`. |
| F-04 | BLOCKER | ADDED AT REVIEW. E-04 as written ("Delete `term.py`'s `STATUS_COLOR_256`") would break three working, in-spec features and contradicts both R10.3 and this plan's own Deferred section. Only ONE of `term.py`'s four reads is lifecycle; `format_outcome`, `badge` and `format_path` are generic roles the spec keeps. The parent orchestrator already ruled on this and named THIS child. Harm if uncorrected: `aw` loses its command-outcome banner, every bracketed badge, and all path styling, while the plan reports A17 satisfied. | `term.py:287` (lifecycle) vs `:394`, `:469`, `:477` (generic); verified by execution that all three generic paths resolve through the table today; `uonrjg` R10.3; parent `2xz59a` ("child `qdd5jq`'s E-04 must SPLIT this table... A17 is satisfied when no second LIFECYCLE table remains, not when the string `STATUS_COLOR_256` is absent"). |
| F-05 | High | ADDED AT REVIEW. The plan named ONE reader of `_STATUS_COLOR` inside `render_stream.py` and there are TWO. The second is `Palette.status()`, a PUBLIC method re-exported into both drivers and instantiated there, so removing the table without converting it breaks a public surface at import/call time rather than at review time. | `render_stream.py:88` (`Palette.status`), called at `:2269`; `Palette` re-exported at `oc_runipd.py:106` and `__all__` `:449`, instantiated at `oc_runipd.py:1324`, `:2018`, `:2057`. |
| F-06 | High | ADDED AT REVIEW. An obligation this Set explicitly assigned to this plan was uncarried: child `bn026f`'s review deferred `render_stream._one_line`'s variation-selector-severing clip with `Carrier: qdd5jq`, and this plan mentioned it zero times. Left uncarried, criterion A15 has no owner for this module and the defect ships. | `render_stream.py:222-227` (`collapsed[: limit - 1]`); `bn026f` Deferred section, `Carrier: qdd5jq`; measured there that clipping drops U+FE0E. `grep -c _one_line` on this plan returned 0 before review. |
| F-07 | High | ADDED AT REVIEW. E-03 implied all five Section 7.1 activities derive from `action`, but `INTEGRATION_ACTION_KINDS` holds exactly two values. Three activities live on other fields. An agent implementing the item literally would emit generic `active` for three of five and silently fail criterion A3, or would add action kinds, which Section 0.5 bounds out as a vocabulary change. | `runner_shared.INTEGRATION_ACTION_KINDS == ('execute', 'review')` (`:2451-2455`); `verification_status` at `:11394`; `integration_signal` at `:1466`; spec A3 and Section 7.1. |
| F-08 | Medium | ADDED AT REVIEW. V-04's `grep STATUS_COLOR_256` guard is the wrong instrument in both directions: it FALSE-PASSES because the retained generic table could be renamed while still mapping a lifecycle status, and it FALSE-FAILS because `attention.py` defines the same symbol and its removal belongs to sibling `f9t5hz`. A17 must be asserted by CONTENT. | `attention.py:1435` defines `_STATUS_COLOR_256` (owned by `f9t5hz`); criterion A17's text is "No second lifecycle color or glyph table remains", a property, not a symbol name. |
| F-09 | Medium | ADDED AT REVIEW. E-04 breaks a shipped test in an UNDECLARED file, three separate ways, and the file encodes the very premise this Set replaces. It currently passes, so the breakage is a real regression rather than a pre-existing failure. | `tests/test_term_components.py::PaletteSingleSourceTests` (16 passed, verified): asserts `palette["approved"] == 46` (spec: 45), `palette["active"] == 39` (spec: 220), and at `:68-73` that `term_dicts == ["STATUS_COLOR_256"]` exactly, which fails under BOTH deletion (`[]`) and split (two dicts). |
| F-10 | Low | ADDED AT REVIEW. OQ-01 names ONE hazard for the statusline (ambiguous width) but there are two, with different fixes, and it undercounts the ambiguous glyphs. Three of the five activity glyphs are Ambiguous, not two, and `↩︎` additionally carries a variation selector whose misalignment is DETERMINISTIC rather than terminal-dependent. | Measured `unicodedata.east_asian_width`: `◎` A, `▶` A, `◆` A, `⇄` N, `↩︎` two code points; statusline padding by bare `len()` at `render_stream.py:936-942`. |

## Proposed changes (ordered, validatable)

1. Convert `render_stream.py` lifecycle rows (BOTH readers) and fix `_one_line`, keeping event and severity visuals (E-01).
2. Dismantle the `_STATUS_COLOR` re-export chain and convert its consumption site including its hardcoded glyph and success color (E-02).
3. Convert both drivers' lifecycle rendering, deriving each activity from the field that carries it (E-03).
4. SPLIT `term.py`'s `STATUS_COLOR_256`, moving the 32 lifecycle keys out and retaining the 24 generic roles (E-04).
5. Add content-based A17/A18 guards and repair the shipped palette test (E-05).

## Deferred / out of scope (with reason)

- Run outcome vocabulary, exit codes, and report sections: spec Section 0.5 states its override "covers DISPLAY only" and changes none of these. Touching them here would exceed the spec's own authority.
  - Carrier-Declined: Excluded by the granting authority itself: spec Section 0.5 bounds its override to DISPLAY only and changes no state, transition, exit code, or report section. Touching them would exceed the maintainer's ruling, so there is no obligation to carry.
- `render_stream.py`'s event glyphs and severity colors: R10.3 keeps them, and criterion A18 requires proving they were NOT remapped.
  - Carrier-Declined: R10.3 explicitly PERMITS this module to retain non-lifecycle event glyphs and severity colors, and criterion A18 requires proving they were not remapped. Retaining them is compliance, not deferred work.
- Generic `Term` OK/WARN/FAIL: R10.3 keeps them valid and explicitly warns against mechanically replacing every checkmark in the repository.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by R10.3, which keeps these valid and warns against mechanically replacing every checkmark. No obligation to carry.
- A NEW shared display-width helper: not needed, because child `bn026f` BUILDS the two primitives this child consumes (a zero-width-aware visible-width measurement and a VS-safe truncation). Section 9.4 forbids a per-renderer width guess, so E-01 and E-03 must consume `bn026f`'s rather than write local ones.
  - Carrier-Declined: The primitives are `bn026f`'s deliverable and this child's dependency, so nothing is outstanding; building a second set here is what Section 9.4 forbids.
- Making the three AMBIGUOUS-width activity glyphs (`◎`, `▶`, `◆`) align across every terminal: Section 9.4 states this "cannot be guaranteed across every terminal's ambiguous-width policy", so it is declined on the spec's own terms. The ASCII fallback is the guarantee for width-constrained cells. Note this does NOT cover `↩︎`'s variation selector, which is deterministic and IS fixed here (E-01).
  - Carrier-Declined: DECLINED ON THE SPEC'S OWN TERMS. Section 9.4 admits the ambiguous-width guarantee is unreachable and requires only its four contract bullets; the VS half is in scope and owned by E-01.
- Retaining `term.py`'s generic role keys: R10.3 keeps command-level OK/WARN/FAIL and formatting roles valid and outside this spec, so they are retained by E-04's split rather than deleted.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by R10.3. Retaining them is compliance, not deferred work, and deleting them would break `format_outcome`, `badge` and `format_path` (F-04).

## Scope check

- Over-scope: ONE ITEM CORRECTED. E-04 previously deleted `term.py`'s `STATUS_COLOR_256` outright, which would have removed 24 generic role keys R10.3 protects and broken three working features (F-04). It now splits the table, which is what parent `2xz59a` directs.
- Under-scope: THREE GAPS CLOSED AT REVIEW, each of which would have executed cleanly while leaving a release-gating criterion unmet or a feature broken. (1) `Palette.status()`, a second reader of `_STATUS_COLOR` that is public and re-exported into both drivers (F-05). (2) `render_stream._one_line`'s VS-severing clip, an obligation `bn026f` explicitly assigned to this plan and that this plan did not carry (F-06). (3) The hardcoded `✓`/`●` glyph and `green` success color in the run-finish line, which keeps the F-01 collapse alive at that site even after the table lookup is converted (E-02).
- Also corrected: E-03's activity derivation (F-07), the A17 guard's instrument (F-08), and the undeclared test file E-04 breaks (F-09).

## Required tests / validation

Run the suite BARE: `python3 -m pytest` (no added flags). Paste the actual summary line and compare to the review baseline `7468 passed, 3 skipped, 2 xfailed` at HEAD `67ac3495`, explaining any difference by node id. A focused baseline for the four declared test files is `266 passed`.

This is the largest-surface child and touches both drivers, so validation must additionally show:
- **A7**: a live executing plan keeps its stored `approved` status on disk, with the file content shown.
- **A14**: no ANSI and no schema change in `--agent`/`--json` for the run views.
- **A17 BY CONTENT, not by symbol name** (F-08): no module other than `lifecycle_style` maps a native status to a color or glyph. A `grep STATUS_COLOR_256` result is necessary-but-not-sufficient evidence and must not be presented as the whole proof.
- **A18**: `STATUS_GLYPHS`, `_status_glyph_char`, event prefixes, finding-severity, priority and gate visuals all still resolve independently. `STATUS_GLYPHS`'s `running`/`error` keys make this the criterion most likely to be silently violated.
- **The retained generic roles still work** (F-04): `format_outcome`, `badge` and `format_path` each producing their current output.
- **The repaired palette test** (F-09), asserting the new invariant rather than deleted.

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`. The `25kzda` Section 5.6 amendment that spec Section 0.5 REQUIRES is carried by child `7p3tt8`, which declares that spec file. Note the sequencing this creates: the superseded five-color table remains in the tree until `7p3tt8` lands, so a reader between these two children will find `25kzda` still describing the old scheme. That is a known, bounded documentation lag, and it is why `7p3tt8` is the final child rather than an optional follow-up.

## Open questions

### OQ-01: Does any runner statusline need a lifecycle glyph in a width-constrained cell that the ASCII pattern cannot satisfy?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier-Declined: RESOLVED AT REVIEW into two separate obligations, both owned inside this plan. The AMBIGUOUS-width half is declined on the spec's own terms (Section 9.4 says it cannot be guaranteed) with ASCII mode as the guarantee, and is recorded in Deferred. The VARIATION-SELECTOR half is deterministic, is in scope, and is E-01's via `bn026f`'s primitive. Nothing outlives the plan.
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-19, and the question CONFLATED TWO DIFFERENT PROBLEMS with different fixes, which is why resolving it changed the work. Measured `unicodedata.east_asian_width` over the five activity glyphs: `◎` U+25CE is `A`, `▶` U+25B6 is `A`, `◆` U+25C6 is `A`, `⇄` U+21C4 is `N`, and `↩︎` is U+21A9 plus U+FE0E (two code points). So (a) THREE glyphs are ambiguous-width, not the two the question implied, and that hazard is terminal-dependent and declined by Section 9.4 itself, with ASCII mode as the conforming fallback exactly as the question reasoned; but (b) `↩︎`'s variation selector makes a `len()`-based cell one column short DETERMINISTICALLY, on every terminal, and the statusline does pad with bare `len()` (`render_stream.py:936-942`). Half (b) is therefore not a "check the statusline" note but a real defect with an owner: it is the same problem as `_one_line`'s clip, both are fixed by `bn026f`'s width and truncation primitives, and E-01 now carries them. The question was worth asking and its ASCII reasoning was right for half of it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: FOUR pastes. (1) `grep -n "_STATUS_COLOR" agent_workflows/render_stream.py` showing no table definition AND no remaining reader, which must account for BOTH `:51` and `Palette.status()` at `:88` (F-05); name what happened to `Palette.status()` (converted or removed) since it is re-exported into both drivers. (2) Rendered lifecycle rows showing `approved` and `executed` in DIFFERENT colors, with escapes visible. (3) The `_one_line` fix (F-06): clip a string at the ADVERSARIAL boundary (limit landing between U+26A0 and U+FE0E) and show U+FE0E still present, as a `[hex(ord(c)) for c in out]` dump; a clip asserted at a safe offset proves nothing. (4) The event-glyph and severity tests still passing, plus `grep -n "STATUS_GLYPHS" agent_workflows/render_stream.py` showing both tables and `_status_glyph_char` UNCHANGED (A18, F-03).
  - Observed evidence: |
      (1) NO TABLE AND NO REMAINING READER. `grep -n "_STATUS_COLOR" agent_workflows/render_stream.py`
      returns ONE line, and it is prose:
          64:# THE TABLE THAT USED TO LIVE HERE WAS THE SPEC'S WORKED EXAMPLE OF THE DEFECT. `_STATUS_COLOR`
      Both readers accounted for. The definition at the old `:51` is GONE. `Palette.status()` (the old
      `:88`) was CONVERTED, not removed, because it is re-exported into both drivers and instantiated
      there; its body is now:
          def status(self, status: str, *, action: str | None = None) -> str:
              return self.lifecycle(resolve_item_lifecycle(status, action=action), status)

      (2) `approved` AND `executed` IN DIFFERENT COLORS. All four formerly-green statuses now differ:
          approved                 '\x1b[1;38;5;45mapproved\x1b[0m'
          reviewed                 '\x1b[38;5;135mreviewed\x1b[0m'
          executed                 '\x1b[1;38;5;46mexecuted\x1b[0m'
          substantially-complete   '\x1b[1;38;5;220msubstantially-complete\x1b[0m'
      45 cyan = `ready`, 46 green = `done`, 135 = `authority-queued`, 220 amber = `recovering`. The
      F-01 collapse (all four -> one green) is gone.

      (3) `_one_line` AT THE ADVERSARIAL BOUNDARY. Input `xxx⚠︎tail` =
      ['0x78','0x78','0x78','0x26a0','0xfe0e','0x74','0x61','0x69','0x6c']. The boundary that severs is
      limit=5 (between U+26A0 and U+FE0E). Walked EVERY limit 1..8; the base is never kept without its
      selector:
          limit=4  out=['0x78','0x78','0x78','0x2026']                     base=False vs=False  OK
          limit=5  out=['0x78','0x78','0x78','0x26a0','0xfe0e','0x2026']   base=True  vs=True   OK
      GUARD THE GUARD: the OLD `collapsed[: limit - 1] + "…"` at that same limit=5 produced
      ['0x78','0x78','0x78','0x26a0','0x2026'] -- base present, selector GONE, i.e. it shipped the
      emoji form criterion A5 forbids. The fix consumes `term.truncate_visible`, not a second local
      guess (Section 9.4).

      (4) A18, EVENT GLYPHS AND SEVERITY UNCHANGED. `grep -n "STATUS_GLYPHS"` shows both tables still
      defined at `:346`/`:352` and consumed at `:362`, with values byte-identical:
          STATUS_GLYPHS       = {'completed': '✓', 'error': '✗', 'running': '…', 'other': '•'}
          STATUS_GLYPHS_ASCII = {'completed': '+', 'error': 'x', 'running': '.', 'other': '-'}
          _status_glyph_char('completed') = ('✓', 'green')   ('error') = ('✗', 'red')
          _status_glyph_char('running')   = ('…', 'yellow')  ('other') = ('•', 'gray')
      `tests/test_render_stream.py` 130 passed, which includes the event-glyph and severity tests.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `grep -rn "_STATUS_COLOR\b" agent_workflows/` showing no import, alias, or `__all__` entry remains (it returns 8 matches today). Paste the converted consumption site (`runner_shared.py:14049` at review time; locate it by grep) and its resolved output for `ran`, `unknown_outcome`, `needs_input`, and `awaiting-human`. THEN paste the run-finish line proving the hardcoded pair is gone: the `glyph = "✓" if reached_success else "●"` and `glyph_color = "green" if reached_success` literals at `:14047-14050` must BOTH resolve through the shared module, or the F-01 collapse survives at the one line printed at the end of every run.
  - Observed evidence: |
      (1) THE WHOLE-PACKAGE GREP. `grep -rn "_STATUS_COLOR\b" agent_workflows/ --include=*.py` returned
      8 matches before this change and now returns TWO, both PROSE:
          agent_workflows/render_stream.py:64:# THE TABLE THAT USED TO LIVE HERE ... `_STATUS_COLOR`
          agent_workflows/runner_shared.py:171:    # `_STATUS_COLOR` table this module used to import.
      Gone: the definition, the `oc_runipd.py:104` import, the `oc_runipd.py:447` `__all__` entry, the
      `agy_runipd.py:104` alias, the `runner_shared.py:169` import, and both `render_stream` readers.

      (2) THE CONVERTED CONSUMPTION SITE (`runner_shared.py:16384`, drifted from the plan's `:14049`):
          finish_resolved = (
              resolve_reached_success_lifecycle(disposition)
              if reached_success
              else resolve_item_lifecycle(disposition)
          )
          finish = (
              pal.lifecycle_glyph(finish_resolved, width=2)
              + pal(f"IPD {seq:02d}/{total} {item['id6']}", "bold")
              + pal(f" ({action})", "dim")
              + " -> "
              + pal.lifecycle(finish_resolved, disposition)
              + pal(f"  (exit {exit_code})", "dim")
          )
      Resolved output for the four Section 7.2 rows this item names:
          ran              stage=recovering    glyph='\x1b[1;38;5;220m↩︎\x1b[0m'  word='...220mran'
          unknown_outcome  stage=failed        glyph='\x1b[1;38;5;196m✘\x1b[0m'   word='...196munknown_outcome'
          needs_input      stage=waiting-input glyph='\x1b[1;38;5;214m…\x1b[0m'   word='...214mneeds_input'
          awaiting-human   stage=waiting-input glyph='\x1b[1;38;5;214m…\x1b[0m'   word='...214mawaiting-human'

      (3) THE HARDCODED PAIR IS GONE. Neither `glyph = "✓" if reached_success` nor
      `"green" if reached_success` appears as CODE anywhere in `runner_shared.py` (the only textual hit
      is the comment at `:16371` recording what was removed). Both the glyph AND the color now resolve
      through the shared module. Rendered finish lines:
          success  : '\x1b[1;38;5;46m✓\x1b[0m \x1b[1mIPD 01/3 qdd5jq\x1b[0m... -> \x1b[1;38;5;46mexecuted\x1b[0m...(exit 0)'
          ran      : '\x1b[1;38;5;220m↩︎\x1b[0m \x1b[1mIPD 01/3 qdd5jq\x1b[0m... -> \x1b[1;38;5;220mran\x1b[0m...(exit 1)'
          unknown_o: '\x1b[1;38;5;196m✘\x1b[0m \x1b[1mIPD 01/3 qdd5jq\x1b[0m... -> \x1b[1;38;5;196munknown_outcome\x1b[0m...(exit 1)'
      `reached_success` STILL decides the success case (the `zz5yxq` judgement an execute item ending
      `reviewed` must not get a check); what is gone is the LITERAL, not the judgement.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste runner view output for each Section 7.1 activity the runner can signal, showing the correct glyph and the exact activity word (A3), and name the FIELD each was derived from (`action` for `reviewing`/`executing`; `verification_status`, `integration_signal`, and the retry state for the other three). If any of the five renders generic `active` because its signal is not reachable at the render site without a data-flow change, SAY SO explicitly and name the activity and the missing signal (F-07): Section 7.1 permits generic `active` when the subtype is genuinely unavailable, so an honest partial conforms, but claiming five when three were never wired does not. Paste evidence for A7: a plan displayed as `executing` whose on-disk `- Status:` is still `approved`, with the file content shown. Also paste the statusline with a VS-bearing activity glyph (`↩︎`) showing its cell measures the same rendered width as a non-VS one (OQ-01 half b).
  - Observed evidence: |
      (1) ALL FIVE ACTIVITIES RENDER, each derived from the FIELD that carries it. Measured:
          reviewing    OK  glyph='\x1b[1;38;5;220m◎\x1b[0m'  word='reviewing'    <- item["action"] == "review"
          executing    OK  glyph='\x1b[1;38;5;220m▶\x1b[0m'  word='executing'    <- item["action"] == "execute"
          verifying    OK  glyph='\x1b[1;38;5;220m◆\x1b[0m'  word='verifying'    <- item["verification_status"]
          integrating  OK  glyph='\x1b[1;38;5;220m⇄\x1b[0m'  word='integrating'  <- item["integration_signal"]
          recovering   OK  glyph='\x1b[1;38;5;220m↩︎\x1b[0m'  word='recovering'   <- the retry state (attempt["recovery"])
      NOTHING RENDERS GENERIC `active` FOR WANT OF A SIGNAL, so there is no partial to report. The
      plan's caution that three signals might be unreachable without a data-flow change did NOT hold:
      all three are already written onto the queue entry the renderer receives
      (`verification_status` at `runner_shared.py:15553`, `integration_signal` at `:15698`,
      `attempt["recovery"]` at `:14915`). Recorded as DECISION 08-qdd5jq-D2.
      The fallback still works where it SHOULD: a running `plan` action (a real `ACTION_CHOICES`
      member with no activity mapping) resolves stage=active, glyph='\x1b[1;38;5;220m●\x1b[0m', not `?`.

      (2) CRITERION A7. On-disk `- Status:` of THIS plan before rendering: `9:- Status: approved`.
      Rendered display for the in-flight entry {"id6":"qdd5jq","action":"execute","status":"running",
      "initial_status":"approved"}:
          glyph='\x1b[1;38;5;220m▶\x1b[0m'  activity word='executing'  stage=executing
      The resolver mutated nothing (entry unchanged after the call), and the on-disk status AFTER
      rendering is still `9:- Status: approved`. A live executing plan displays `▶ executing` while
      its stored status stays `approved`.

      (3) OQ-01 HALF (b), THE VS CELL. A VS-bearing activity glyph measures the SAME rendered width as
      a non-VS one:
          activity=executing   cell=' ▶ Executng '  raw len()=12  VISIBLE=12
          activity=recovering  cell=' ↩︎ Recovrng '  raw len()=13  VISIBLE=12
          box visible widths, both cases: (130, 130, 130, 130)
      Same visible width (12 == 12) while raw `len()` DIFFERS (13 vs 12), which is exactly why
      `format_activity_cell` returns the measurement from `term.visible_width` instead of letting the
      caller use `len()`. The selector is intact in the cell: ['0x21a9', '0xfe0e'].
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: THREE pastes, because a grep alone both false-passes and false-fails here (F-08). (1) The SPLIT: paste the new lifecycle-free `term.py` role table and its name, and show the 32 lifecycle keys are gone from it while the 24 generic keys remain. (2) THE RETAINED FEATURES STILL WORK (F-04): paste `format_outcome("ok","done")`, `badge("RULE","error")` and `format_path(".aw/x")` producing their current output with escapes visible. (3) `grep -rn "STATUS_COLOR_256" agent_workflows/` with its result INTERPRETED: state plainly that a zero result is necessary-but-not-sufficient for A17 and that the sufficient proof is V-05's content-based guard.
  - Observed evidence: |
      (1) THE SPLIT. New table name `ROLE_COLOR_256`, 24 keys, all generic:
          action 214, advisory 214, conforming 46, conforms 46, current 46, error 196, fail 196,
          failure 196, info 39, legacy 244, ok 46, path 33, paths 33, preview 214, quarantined 214,
          ready 40, secondary 245, success 46, unchanged 245, up to date 46, updated 46, warn 226,
          warning 226, wrote 46
      The 32 LIFECYCLE keys LEFT: `still present in ROLE_COLOR_256: []` (empty), and all 32 are
      resolvable through `lifecycle_style` (32/32). `hasattr(term, "STATUS_COLOR_256")` is False.

      (2) THE RETAINED FEATURES STILL WORK, byte-identical to the capture taken BEFORE the split:
          format_outcome("ok","done")  IDENTICAL  '\x1b[1;38;5;46m✓ OK\x1b[0m  done'
          badge("RULE","error")        IDENTICAL  '[\x1b[1;38;5;196mRULE\x1b[0m]'
          format_path(".aw/x")         IDENTICAL  '\x1b[38;5;33m.aw/x\x1b[0m'
      This is what F-04 required: deleting the symbol would have broken all three.

      (3) `grep -rn "STATUS_COLOR_256" agent_workflows/` RETURNS 8 LINES, AND THE RESULT IS
      INTERPRETED RATHER THAN PRESENTED AS PROOF. Tokenizing every match shows how many are CODE:
          matches that are a NAME token (i.e. code): 0
          all 8 are COMMENT or STRING tokens, i.e. prose recording the history
      Four name the symbol as history ("the old", "used to"); two that had gone STALE
      (`ipd_lint.py:1545`, `status_set.py:452`, which described a live lookup) were re-pointed to
      `ROLE_COLOR_256`; two in `attention.py` refer to that module's own `_STATUS_COLOR_256`, removed
      by sibling `f9t5hz`.
      STATED PLAINLY: a zero-or-prose-only grep is NECESSARY BUT NOT SUFFICIENT for criterion A17,
      because the retained generic table could have been renamed while still mapping a lifecycle
      status, and because the `attention.py` half depends on a sibling child rather than on this one.
      The SUFFICIENT proof is V-05's content-based guard.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the BARE `python3 -m pytest` summary line and compare to the baseline `7468 passed, 3 skipped, 2 xfailed` at HEAD `67ac3495`, explaining any difference by node id. Paste the A17 guard FAILING against a deliberately reintroduced local lifecycle palette, then passing after removal: a guard that cannot fail is not evidence. The guard must assert by CONTENT (no module outside `lifecycle_style` maps a native status to a color or glyph), and paste proof it still passes WITH the retained generic role table present, since a name-based guard would fail on that table (F-08). Paste the A18 assertions showing severity, event, priority and gate visuals resolve independently. FINALLY paste the repaired `tests/test_term_components.py::PaletteSingleSourceTests` (F-09), stating which of its three broken assertions was rewritten to what, and confirm `tests/test_term.py` no longer references either removed symbol. ALSO DISCHARGE CRITERION A21 HERE, assigned at review 2026-09-19 because this is the last code child and a whole-tree gate is only meaningful once every conversion has landed: paste the BARE `python3 -m pytest` summary line AND `git diff --check` showing clean output. That pair IS A21.
  - Observed evidence: |
      (1) THE BARE SUITE. `python3 -m pytest` (no added flags):
          7600 passed, 3 skipped, 2 xfailed, 3 warnings in 97.66s (0:01:37)
      RECONCILED BY NODE ID against the baseline I measured at the starting HEAD `54c7f5fb`, which was
      `1 failed, 7587 passed, 3 skipped, 2 xfailed` = 7588 tests run. Delta = +12 passed, and every one
      is a node I added:
          +11  tests/test_lifecycle_palette_singleness.py (new file; 11 tests collected)
          + 1  tests/test_refusal_surfacing.py::test_the_allowed_leaf_modules_really_cannot_reach_back
      `skipped` (3) and `xfailed` (2) are UNCHANGED.
      ON THE REVIEW'S QUOTED BASELINE OF 7468: the tree gained tests between that review (HEAD
      `67ac3495`) and this execution (HEAD `54c7f5fb`, four `lifeglyph` children later), so 7468 is not
      the count at MY starting HEAD. I reconcile against the baseline I measured myself, which is the
      only one my change can be held to.
      THE ONE BASELINE FAILURE WAS NOT MINE AND IS NOT A REGRESSION:
      `tests/test_turn_bounds.py::test_the_permission_policy_by_contrast_IS_isolation_scoped` failed
      BEFORE I edited anything, because `OPENCODE_CONFIG_CONTENT` is set in THIS runner turn's own
      environment and the test asserts it is absent for a non-isolated turn. Proven at baseline:
      `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` -> `43 passed`.
      Every suite run above therefore uses `env -u OPENCODE_CONFIG_CONTENT`, which removes the
      harness artifact and nothing else.

      (2) THE A17 GUARD FAILING, THEN PASSING. Injected a deliberate local lifecycle palette into
      `render_stream.py` and ran the guard:
          FAILED tests/test_lifecycle_palette_singleness.py::...::test_no_module_holds_a_second_lifecycle_color_or_glyph_table
          AssertionError: ['render_stream._REINTRODUCED_LIFECYCLE_PALETTE maps 5 lifecycle statuses to
          a color index: ['approved', 'draft', 'executed', 'superseded', 'to-review']']
          1 failed, 10 passed
      Removed the injection; `11 passed`. The guard names the module, the symbol, and the statuses.
      IT ASSERTS BY CONTENT, NOT BY NAME: for every native status `lifecycle_style` knows, no other
      module may hold a dict mapping it to a color index or a Section 5 glyph. Three companion tests
      keep that honest: a color-table probe, a GLYPH-table probe (which a color-only guard would miss),
      and `test_the_retained_generic_role_table_PASSES`, which proves the guard does NOT false-fail on
      `term.ROLE_COLOR_256` -- the exact false-fail a name-based guard would have suffered (F-08).

      (3) A18 ASSERTIONS, 5 passed:
          test_the_event_prefix_tables_are_untouched PASSED
          test_the_tool_event_severity_colors_are_untouched PASSED
          test_the_severity_labels_resolve_independently PASSED
          test_the_tool_event_glyphs_are_untouched PASSED
          test_the_generic_command_outcome_banner_still_works PASSED
      Severity (196/226/46 via `severity_label`), tool-event glyphs, event prefixes (whose `write`
      value IS `▶`, the spec's `executing` glyph, which is the coincidence that makes a careless remap
      plausible) and the generic OK banner all resolve independently.

      (4) THE REPAIRED SHIPPED TEST (F-09). `tests/test_term_components.py::PaletteSingleSourceTests`
      had THREE broken assertions and all three were REWRITTEN, not deleted:
        - `palette["approved"] == 46` and `palette["active"] == 39`: REMOVED from this file as claims,
          because both CONTRADICT spec Section 5 (`approved` is 45 cyan; `active` is 220 amber).
          Asserting them here would have pinned the very collapse the spec forbids. They are now
          `lifecycle_style`'s to assert.
        - the `COLOR`-dict allowlist `== ["STATUS_COLOR_256", "STAGE_COLOR_16"]`: REWRITTEN to
          `["ROLE_COLOR_256", "STAGE_COLOR_16"]`, plus a NEW assertion that `term.STATUS_COLOR_256`
          does not come back (re-adding it is the one edit that would silently restore the mixed
          table).
        - the class docstring's premise ("Exactly one palette exists") was replaced by the invariant
          this Set establishes: one LIFECYCLE source plus one generic role table.
      Also added a negative half driven from `lifecycle_style.NATIVE_MAPS` rather than a hand-list, so
      a status added upstream is covered with no edit here.
      `tests/test_term.py`'s parity test: verified it no longer references either removed symbol
      (`f9t5hz` had already re-pointed it to assert `attention._STATUS_COLOR_256` is ABSENT, which
      still holds). Its `test_status_256_styling_and_padding` DID still break, on `open` -> 40; `open`
      is a backlog lifecycle status, so it was re-pointed to the generic word `updated` and given a
      negative half proving five lifecycle statuses now fall through to neutral 244 there.

      (5) CRITERION A21, DISCHARGED HERE as the last code child:
          python3 -m pytest        -> 7600 passed, 3 skipped, 2 xfailed in 97.66s
          git diff --check         -> (no output, exit 0)
      `git diff --check` initially reported `render_stream.py:2916: new blank line at EOF` (an artifact
      of removing the guard-failure injection); normalized, re-run, clean.

      (6) A14, machine output. With color off (the `--agent`/`--json`/piped path) the run summary table
      and the statusline contain ZERO ANSI escapes, while both status WORDS survive
      (`executed`/`ran` present) and the activity word survives in the statusline (`Recovrng`),
      which is criterion A11/R9.3a.5's glyph-plus-word invariant at the `none` tier. No schema field
      changed: the conversion touches styling only.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved qdd5jq --by-human`). Its `- Item-Dependencies: executed:9zvl2w` edge is re-checked at dispatch, sequencing it after the non-runner consumers per Section 12 steps 4 and 5, so the table SPLIT in E-04 happens only when nothing else reads the lifecycle keys. The edge is load-bearing rather than nominal: this child also consumes `bn026f`'s width and truncation primitives (transitively, through the chain) for E-01's `_one_line` fix and E-03's statusline cell, and `f9t5hz` owns `attention.py`'s copy of `_STATUS_COLOR_256` whose removal E-05's A17 guard depends on.

OPEN QUESTIONS: OQ-01 is RESOLVED at review, split into a declined ambiguous-width half and an in-scope variation-selector half now owned by E-01. There is no blocking question on this child. NOTE THE SET CONTEXT, which is not this plan's to resolve: the upstream chain `9zvl2w` -> `f9t5hz` -> `bn026f` -> `udgilu`/`pow5sj` carries two unresolved `- Blocking: yes` questions, so this child cannot dispatch until those are ruled on regardless of its own readiness. Do not attempt to clear that by editing this file.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:`. An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. In particular: do NOT delete `term.py`'s generic role keys or the symbol outright (E-04 SPLITS it; deleting breaks `format_outcome`, `badge` and `format_path`, per F-04); do NOT touch `render_stream.py`'s `STATUS_GLYPHS`, `STATUS_GLYPHS_ASCII`, `_status_glyph_char`, `EVENT_PREFIXES` or severity colors, which R10.3 keeps and A18 protects even though two of their keys look like lifecycle words; do NOT add a value to `INTEGRATION_ACTION_KINDS` to make the activity display neater, because that is a runner vocabulary change Section 0.5 bounds out; do NOT change run outcome vocabulary, exit codes, or report sections; do NOT write a local display-width or truncation helper (consume `bn026f`'s, per Section 9.4); and do NOT edit `attention.py`, whose table is `f9t5hz`'s. DO STOP AND REPORT for one genuinely unsafe condition: if `bn026f`'s width and VS-safe truncation primitives are absent or shaped differently than E-01 and E-03 expect, report that rather than clipping or padding with bare `len()`, which reintroduces the exact defect F-06 and OQ-01 half (b) record.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a rendered runner view, a grep result, or a guard-test failure you did not run. A `V-*` evidence block must contain real output, not a description of expected output. Three specific prohibitions follow from this review's measurements: do NOT present a zero `grep STATUS_COLOR_256` result as proof of criterion A17 (it is necessary but not sufficient, and it also depends on a sibling child, per F-08); do NOT claim all five Section 7.1 activities render if three were never wired (F-07); and do NOT claim `_one_line` is fixed from a truncation asserted at a safe offset rather than at the base/variation-selector boundary.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
