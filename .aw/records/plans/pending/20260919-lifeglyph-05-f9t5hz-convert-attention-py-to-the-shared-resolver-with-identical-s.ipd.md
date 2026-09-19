# IPD: Convert attention.py to the shared resolver with identical status and id6 treatment

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 12 step 3 converts `attention.py` first among the consumers, and Section 1 names it as a specific duplication: it "duplicates native status colors and colors both status words and id6s". Verified at review 2026-09-19 at HEAD `7e002486`: `attention.py:1435` defines `_STATUS_COLOR_256` (23 keys), read at three lifecycle sites (1884, 2029, 2192), each falling back to `_CLASS_COLOR_256` and then to gray 244. THE DUPLICATION IS THE REAL DEFECT AND IT IS MEASURABLE: 13 of the 18 statuses this table shares with spec Section 5 carry a DIFFERENT color from the one the spec mandates, so the board is not merely duplicating the palette, it is contradicting it.
  ALL FOUR LINE NUMBERS IN THE ORIGINAL TEXT HAD DRIFTED BY +32 and are corrected above (authored `1403/1852/1997/2160`, now `1435/1884/2029/2192`). Commit `f3db5649` (`0ta5vg`, stranded-lane reporting) landed after this plan was authored and inserted 32 lines above the table. The numbers were RIGHT when written, which is precisely why an executor must re-grep rather than trust them; `grep -n "_STATUS_COLOR_256" agent_workflows/attention.py` is the durable locator and is what V-01 requires.
- Scope: IN: replace `attention.py`'s local `_STATUS_COLOR_256` lifecycle lookups with the shared `term.py` helpers, apply the Section 9.1 rule that glyph, id6 and status word receive the SAME treatment while artifact type, title and path receive none, handle the three statuses that currently fall through the lifecycle table, re-point the cross-module palette-parity test that reads the deleted symbol, and update the command's snapshots and the shipped hardcoded-escape assertions. OUT: deleting `_CLASS_COLOR_256` (it keys the attention CLASS vocabulary, which spec Section 3 excludes as a non-goal; see E-02), the other consumers (children `9zvl2w`, `qdd5jq`), any change to attention's class computation, and the `lanes` synthetic tree, which never becomes an `Item` and so never reaches a lifecycle site (see Deferred).
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py, tests/test_attention_priority_blocker.py, tests/test_term.py
- Item-Dependencies: executed:bn026f
- Status: approved
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 5
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: f9t5hz
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-501..PR-508 all FIXED, none deferred, none open. Four under-scope gaps closed: the colored artifact TYPE column is a live A10 violation no plan in the Set owned; deleting attention._STATUS_COLOR_256 breaks tests/test_term.py which was undeclared; the hardcoded escape assertions span two test files with one holding priority colors that must not change; and a glyph column would misalign under this file's bare-len padding. Corrected the headline claim: class_of raises before any render site, so the unreachable ?-row is replaced by the three statuses that genuinely miss the table. OQ-01 resolved. Readiness go-pending-approval.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501 through PR-508 all FIXED, none deferred, none open. Reviewed at HEAD `7e002486`; `aw ipd lint --phase author --agent` clean, exit 0, before and after. THE SEQUENCING AND THE TARGET ARE RIGHT and the duplication is real: 13 of the 18 statuses this board shares with spec Section 5 carry a DIFFERENT color, so `attention.py` is contradicting the palette, not merely copying it. FOUR UNDER-SCOPE GAPS were closed, each of which would have executed cleanly while leaving a release-gating criterion unmet. PR-503 (HIGH): a SECOND live A10 violation that NO plan in the Set owned - the artifact TYPE column is colored 33 bold (`attention.py:2227`, `:1898`), and measured output shows `^[[1;38;5;33mplan^[[0m` beside the status; Section 9.1 says type is not lifecycle-colored, so a reviewer testing A10 would have failed a "conforming" implementation. PR-504 (HIGH): E-01's deletion of `attention._STATUS_COLOR_256` breaks `tests/test_term.py:127-136`, which imports that private symbol and was NOT in `- Scope-Paths:`; it fails as an `AttributeError`, so it would not read as an expected palette change. PR-502 (HIGH) is a CORRECTION of the plan's own headline claim: there is no reachable "silent gray fallthrough for any absent status", because `attention_contract.class_of` is TOTAL and RAISES, so E-03 would have built and V-03 demanded evidence for an UNREACHABLE `?`-row while the three genuinely-wrong statuses (`auto-approved`, `graduated`, `archive`) went unfixed. PR-506 (MEDIUM): the hardcoded escape assertions span TWO test files, only one declared, and two of the undeclared file's assertions are PRIORITY colors that must NOT be recomputed. Also: all four line numbers in the original text had drifted +32 (commit `f3db5649` landed after authoring), so E-01 now mandates grep over quoted numbers; a new-glyph column would misalign under this file's universal bare-`len()` padding (PR-507); and OQ-01 is resolved from the code, with the trap recorded that all five class keys are bare strings identical to status words with identical colors today, so the obvious check deletes a protected vocabulary. Verified the `lanes` tree is NOT a sixth orphan: its five states never become an `Item`. Baseline `7468 passed, 3 skipped, 2 xfailed` (differs from `bn026f`'s `8369` one commit earlier; the lane was rebased). Readiness go-pending-approval.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 12 step 3, R10.3, and criteria A10/A17/A20. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw attention` the first view rendered entirely through the shared resolver, with the status word and the id6 carrying identical lifecycle treatment and no known status silently rendering as gray.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Convert the lookups

- [ ] E-01 Replace the three `_STATUS_COLOR_256` lifecycle lookup sites in `attention.py` with calls to the shared `term.py` lifecycle helpers, and remove the local `_STATUS_COLOR_256` table once no site reads it. LOCATE THE SITES BY GREP, not by the line numbers in prose, which have already drifted once.
  - Depends on: none
  - Expected outcome: No lifecycle color literal remains in `attention.py`. Every lifecycle color comes from the shared resolver. `_CLASS_COLOR_256` is evaluated separately (see E-02) rather than deleted reflexively.
  - Execution state: pending

  DELETING THAT SYMBOL BREAKS A SHIPPED TEST IN A DIFFERENT FILE, measured at review (F-04) and the reason `tests/test_term.py` is now declared in `- Scope-Paths:`. `tests/test_term.py:127-136::test_status_palette_consistency_with_attention` does `from agent_workflows import attention as att` and iterates `att._STATUS_COLOR_256.items()`, asserting every entry matches `term.STATUS_COLOR_256`. Verified by execution: the test passes today, and removing the attribute makes it raise `AttributeError: module 'agent_workflows.attention' has no attribute '_STATUS_COLOR_256'` - a hard error, not a comparison failure, so it cannot be mistaken for an expected palette change. THAT TEST'S PURPOSE IS ALSO SATISFIED BY THIS CHANGE, which is why the fix is to RETIRE it rather than rewrite it: it exists to catch the two tables drifting apart, and after this child there is only one table. Delete it (or re-point it at the shared resolver) IN THE SAME COMMIT, and say which was done and why in V-01's evidence. Do NOT leave it importing a symbol this item removes.

  THE THREE READ SITES ARE THE LIFECYCLE ONES ONLY. `grep -n "_CLASS_COLOR_256"` also matches a FOURTH site that this item must NOT touch: the section-header renderer, which colors a heading like `## ready (12)` by attention CLASS and reads no status table at all. Confirmed at review by reading it; it is the clearest evidence for E-02's determination.

- [ ] E-02 Record the determination that `_CLASS_COLOR_256` is the attention CLASS vocabulary and RETAIN it, and remove the `_CLASS_COLOR_256` rung from the three lifecycle fallback chains so the class palette stops standing in for a missing lifecycle color.
  - Depends on: E-01
  - Expected outcome: `_CLASS_COLOR_256` survives, still coloring the section headers by class. No lifecycle site consults it. The determination is recorded with the evidence below rather than re-derived.
  - Execution state: pending

  THE DETERMINATION IS ALREADY SETTLED AND IS NO LONGER AN OPEN QUESTION, resolved at review (see OQ-01) so an executor does not spend a turn rediscovering it. `_CLASS_COLOR_256`'s five keys are `A.ACTIVE`, `A.READY`, `A.BLOCKED`, `A.DONE`, `A.PARKED`, which are the cross-tree attention CLASSES, and spec Section 3 lists "attention classes" as an explicit NON-GOAL. Parent `2xz59a` reached the same conclusion independently. So it is NOT a lifecycle table, R10.3 does not reach it, and criterion A17 is satisfied without deleting it.

  BUT THE OBVIOUS CHECK IS A TRAP, AND THIS IS THE PART WORTH THE E-ITEM (F-05). Those five class constants are BARE STRINGS whose values are `'active'`, `'ready'`, `'blocked'`, `'done'`, `'parked'` - every one of which is ALSO a key in the native `_STATUS_COLOR_256` table, and today all five carry the IDENTICAL color in both tables. Verified at review:

  ```text
  A.ACTIVE='active'  status->39  class->39  SAME      A.READY='ready'    status->40  class->40  SAME
  A.BLOCKED='blocked' status->203 class->203 SAME     A.DONE='done'      status->244 class->244 SAME
  A.PARKED='parked'  status->244 class->244 SAME      class-only keys: NONE
  ```

  TWO CONSEQUENCES. FIRST, an agent testing "is this a lifecycle table?" by checking whether the keys look like statuses gets YES for all five and deletes a vocabulary the spec protects; the keys must be traced to the `A.*` constants, not pattern-matched. SECOND, because the colors are currently identical, REMOVING the class rung from the lifecycle chain is invisible in today's output, so V-02 must prove the rung is gone by reading the code rather than by diffing a board that cannot change. After the conversion the two palettes DIVERGE (the spec moves `active` to 220, `blocked` to 208, `done` to 46), so leaving the rung in place would silently reintroduce the class palette into lifecycle rendering the first time a status misses.

### Task group 2: The presentation rules

- [ ] E-03 Apply Section 9.1 in the attention board: glyph, id6, and status word take the same resolved color and bold flag; artifact type, title, and path take NONE. Map the three statuses that currently miss the lifecycle table to their spec Section 6 stage. Pad any new glyph column by RENDERED width via the `bn026f` primitive, never by `len()`.
  - Depends on: E-01
  - Expected outcome: Criterion A10 holds on the attention board, including the type column no longer carrying a color. `auto-approved`, `graduated` and `archive` each render their spec-assigned stage instead of borrowing a class color. A VS-bearing glyph column aligns with a non-VS one.
  - Execution state: pending

  THE "SILENT GRAY FALLTHROUGH" IS NOT WHAT THE ORIGINAL TEXT SAID, and the correction matters because it changes what must be built (F-02). An unmapped status CANNOT reach these render sites at all: `attention_contract.class_of` is TOTAL over each tree's enum and RAISES `UnknownNativeStatus` for anything else, and the scanner turns that into an `attention.unknown-status` violation (the releases path returns no `Item` at all). Verified by execution: `class_of("plans", "bogus-status")` raises. So there is no reachable "bogus status" row to render `?` for, and an A20 test written against one would be asserting unreachable code.

  WHAT IS REAL IS NARROWER AND WAS NOT STATED: exactly THREE statuses pass `class_of` yet MISS `_STATUS_COLOR_256`, so today they borrow a CLASS color rather than gray, which is a wrong-color defect rather than a gray-indistinguishability one. Measured at review by diffing every tree's `CLASS_MAPS` against the table:

  ```text
  plans    auto-approved -> class ready  -> renders class color 40   spec Section 6.1 says stage `ready`
  backlog  graduated     -> class active -> renders class color 39   spec Section 6.3 says stage `active`
  research archive       -> class parked -> renders gray 244         spec Section 6.4 says stage `parked`
  ```

  Only the third is actually gray. Fixing these three is what closes the defect here, and criterion A20's `?`-plus-diagnostic behavior belongs to the resolver (`udgilu`) and to views that CAN receive an unmapped value; this board's equivalent guarantee is already provided upstream by `class_of` raising, which V-03 records rather than re-implements.

  A SECOND A10 VIOLATION IS LIVE AND WAS UNCLAIMED BY THE WHOLE SET (F-03). The artifact TYPE column is colored today: `attention.py:2227` and `:1898` both wrap the type word in `term.color256(..., _TREE_COLOR_256, bold=True)` (33, bold blue). Measured from real output with `FORCE_COLOR=1`, an `approved` row emits `^[[1;38;5;33mplan^[[0m` beside `^[[1;38;5;46mapproved^[[0m`. Spec Section 9.1 says "The artifact type and title do not inherit lifecycle color" and Section 11 item 5 says only glyph, id6 and status are colored, "except for an existing independent convention". `_TREE_COLOR_256` IS such a convention for the TREE SEGMENT OF A PATH (`attention.py:1729`), but the bare type word in a row is not a path, so extending the exemption to it would make A10 untestable. Decide and record explicitly: either drop the color from the type COLUMN (the reading this plan adopts, since A10 says type is not lifecycle-colored and a reviewer will test exactly that) or justify it in writing as the Section 11 exemption. `grep -l _TREE_COLOR_256` across all eight `lifeglyph` children matched NOTHING before this review, so this is the only place it is owned.

  GLYPH PADDING MUST NOT USE `len()`. Every column in this file pads with bare `len()` on unstyled text (`attention.py:1886`, `2198`, `2230`, `2368` and a dozen more), which is correct for ANSI but wrong for a zero-width code point. Measured: a `⚠︎` (U+26A0 U+FE0E) cell padded to width 4 by `len()` occupies 4 code points but only 3 rendered columns, while `◕` occupies 4 and 4, so a VS-bearing glyph column sits one column short. This is exactly the defect `bn026f` F-05 exists to fix; consume its width primitive rather than adding a local one, which Section 9.4 forbids ("MUST NOT create per-renderer width guesses").

- [ ] E-04 Update the attention snapshots AND the shipped hardcoded-escape assertions for the new palette, preserving the existing column ORDER and every machine field, per Section 12's compatibility rule and criterion A14.
  - Depends on: E-03
  - Expected outcome: Human snapshots and every hardcoded escape assertion updated (expected, per Section 12). `--agent` and `--json` output byte-identical to before, proving no ANSI or schema change leaked into machine output.
  - Execution state: pending

  THE SCALE OF THE ASSERTION CHURN WAS UNSTATED AND IS THE LIKELIEST WAY THIS ITEM STALLS (F-06). 13 of the 18 statuses shared between `attention.py`'s table and spec Section 5 CHANGE COLOR, measured at review: `active` 39->220, `approved` 46->45, `blocked` 203->208, `done` 244->46, `implementing` 51->220, `open` 40->45, `planned` 40->45, `reference` 244->46, `reusable` 39->81, `reviewed` 226->135, `superseded` 240->244, `to-review` 214->39, `todo` 44->45. So this is not a cosmetic snapshot refresh; every test asserting a raw escape for one of those words must be recomputed.

  THE ASSERTIONS LIVE IN TWO FILES, and only one was declared before this review. `tests/test_attention.py` carries 15 such assertions (including `:242` `'\033[1;38;5;39mactive'`, and `:1818`/`:1820`/`:1822` asserting `running`/`queued`/`done`) and `tests/test_attention_priority_blocker.py` carries 2 (`:54`, `:67`). Both are now in `- Scope-Paths:`. Note `:54`/`:67` assert `196` for a PRIORITY value, not a lifecycle status, so they should NOT change; check before editing, because blindly recomputing them would fold priority into lifecycle styling, which spec Section 3 forbids.

  A14 IS A CHARACTERIZATION TEST HERE, not new work: verified at review that `aw attention --agent` and `aw attention --json` already emit ZERO ANSI bytes. Assert it so this change cannot leak escapes into machine output, and do not report it as a fix.

## Project conventions discovered (Step 0)

- Verified at review 2026-09-19 at HEAD `7e002486`: `attention.py:1435` defines `_STATUS_COLOR_256` (23 keys); it is read at 1884, 2029, and 2192, each with a `_CLASS_COLOR_256` then gray-244 fallback chain. A FOURTH `_CLASS_COLOR_256` read at 2718 is the section-header renderer and is NOT a lifecycle site.
- LINE NUMBERS IN THIS FILE HAVE ALREADY DRIFTED ONCE (+32, from commit `f3db5649` landing after authoring) and the original four were all stale by review time. Locate every site by `grep -n`, never by a number quoted in prose. `attention.py` is now 3352 lines.
- `attention.py` is a high-traffic file. Two pending plans (`9iiqmm`, `quqyc4`) declare it and one executed plan (`pr5b0t`) did; per AGENTS.md the runner isolates each execute item in its own worktree and re-validates on merge, so overlap is rebase friction rather than a hazard.
- `aw attention` is the command AGENTS.md directs agents to consume for cross-tree status, so a regression here is user-visible immediately.
- Verified at review: `attention_contract.class_of` is PURE and TOTAL over each tree's native enum and RAISES `UnknownNativeStatus` for anything unmapped, which the scanner converts into an `attention.unknown-status` violation (the releases path returns no `Item`). Only four of the five `class_of` call sites propagate; the releases one catches. THE CONSEQUENCE FOR THIS PLAN: an unrecognized status cannot reach a render site, so criterion A20's `?`-plus-diagnostic case is not reachable from this board and must not be tested as if it were.
- Verified at review: the trees that build `Item`s are exactly `plans`, `specs`, `backlog`, `research`, `releases`. `CLASS_MAPS` also defines a synthetic `lanes` tree (`EMPTY`/`LANDED`/`LIVE`/`STRANDED`/`UNKNOWN`), but lanes join at RENDER time as `Drift` rows and never become an `Item`, so they never reach a lifecycle site. This is why spec Section 12a's claim that `pr5b0t` "adds no status this spec must cover" holds; see Deferred.
- Verified at review: every column in this file pads with bare `len()` on UNSTYLED text (`1886`, `2198`, `2230`, `2368`, and more). That is correct for ANSI but wrong for a zero-width code point, so a VS-bearing glyph column would sit one rendered column short. Consume `bn026f`'s width primitive; Section 9.4 forbids a per-renderer width guess.
- Verified at review: machine output is already clean. `aw attention --agent` and `--json` each emit ZERO ANSI bytes, so criterion A14 is a characterization test here.
- SUITE BASELINE at review HEAD `7e002486`: `7468 passed, 3 skipped, 2 xfailed in 112.27s`. NOTE this differs from the `8369 passed` baseline recorded in sibling `bn026f` one commit earlier; the lane was rebased (46 test files changed, 2 net removed) between the two reviews, so use THIS number and compare node ids rather than counts.
- Focused pre-change baseline for the three declared test files: `python3 -m pytest tests/test_attention.py tests/test_attention_priority_blocker.py tests/test_term.py -o addopts="" -q` -> `110 passed in 1.77s`.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `- Readiness:` is deliberately absent at authoring (it is `/plan-review`'s output; IPD-M107 refuses an unattested value). This review writes it.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The duplication is real and is a CONTRADICTION, not merely a copy: 13 of the 18 statuses shared between `attention.py`'s table and spec Section 5 carry a different color from the one the spec mandates. That is the defect this child closes, and it is why the assertion churn in E-04 is large. | Measured at review: `active` 39->220, `approved` 46->45, `blocked` 203->208, `done` 244->46, `implementing` 51->220, `open` 40->45, `planned` 40->45, `reference` 244->46, `reusable` 39->81, `reviewed` 226->135, `superseded` 240->244, `to-review` 214->39, `todo` 44->45. `attention.py:1435`; spec `uonrjg` Section 5. |
| F-02 | High | CORRECTED AT REVIEW. The original F-01 claimed a live "silent gray fallthrough" for "any status absent from the local table", but an unmapped status cannot reach a render site: `class_of` is TOTAL and RAISES `UnknownNativeStatus`, which the scanner turns into a violation. The reachable defect is exactly THREE statuses that pass `class_of` yet miss the lifecycle table, and two of them render a CLASS color rather than gray. Harm if uncorrected: E-03 would have built and V-03 would have demanded evidence for an unreachable `?`-row, while the three real wrong-color statuses went unfixed. | Verified by execution: `class_of("plans","bogus-status")` raises `UnknownNativeStatus`; `attention_contract.py:408-425`; `attention.py:899-909` (releases catches and returns no Item). Diffing every tree's `CLASS_MAPS` against the table: `plans/auto-approved` -> class color 40, `backlog/graduated` -> 39, `research/archive` -> gray 244. |
| F-03 | High | ADDED AT REVIEW. A SECOND criterion A10 violation is live and was claimed by NO plan in the Set: the artifact TYPE column is colored `33` bold. Spec Section 9.1 says type does not inherit lifecycle color and Section 11 item 5 limits color to glyph, id6 and status. `_TREE_COLOR_256` is a legitimate independent convention for the tree SEGMENT OF A PATH, but a bare type word in a row is not a path, so extending the exemption there makes A10 untestable. | `attention.py:2227` and `:1898` (`term.color256(..., _TREE_COLOR_256, bold=True)`); `_TREE_COLOR_256 = 33` at `:1460`; the path-segment convention at `:1729`. Measured output with `FORCE_COLOR=1`: `^[[1;38;5;33mplan^[[0m` beside `^[[1;38;5;46mapproved^[[0m`. `grep -l _TREE_COLOR_256` across all eight `lifeglyph` children matched nothing. |
| F-04 | High | ADDED AT REVIEW. E-01's removal of `attention._STATUS_COLOR_256` breaks a shipped test in a file the plan did not declare: `tests/test_term.py` imports that private symbol and iterates it. It fails as an `AttributeError`, not a value mismatch, so it does not read as an expected palette change. | `tests/test_term.py:127-136::test_status_palette_consistency_with_attention`; verified by execution that it passes today and that deleting the attribute raises `AttributeError: module 'agent_workflows.attention' has no attribute '_STATUS_COLOR_256'`. |
| F-05 | Medium | ADDED AT REVIEW. E-02's determination has a trap that the obvious check fails: all five `_CLASS_COLOR_256` keys are BARE STRINGS equal to native status words, with IDENTICAL colors in both tables today. So a key-shape test says "lifecycle" for all five and deletes a protected vocabulary, and removing the class rung from the lifecycle chain is invisible in current output. | Verified at review: `A.ACTIVE='active'`, `A.READY='ready'`, `A.BLOCKED='blocked'`, `A.DONE='done'`, `A.PARKED='parked'`; all five present in `_STATUS_COLOR_256` with the same code; zero class-only keys. Spec Section 3 non-goal on attention classes; parent `2xz59a` reached the same conclusion. |
| F-06 | Medium | ADDED AT REVIEW. The hardcoded-escape assertions that must change live in TWO test files and only one was declared. `tests/test_attention.py` holds 15, `tests/test_attention_priority_blocker.py` holds 2. Two of the latter assert a PRIORITY color that must NOT change, so blind recomputation would fold priority into lifecycle styling, which Section 3 forbids. | `tests/test_attention.py:242,877-879,1712-1724,1818-1824`; `tests/test_attention_priority_blocker.py:54,67` (both `38;5;196` for `high` priority). Original `- Scope-Paths:` named only `tests/test_attention.py`. |
| F-07 | Medium | ADDED AT REVIEW. Any new glyph column would be padded by this file's universal bare-`len()` idiom, which miscounts a variation selector and leaves a VS-bearing cell one rendered column short. This is the same defect `bn026f` F-05 fixes, and Section 9.4 forbids solving it locally. | Measured: `⚠︎` padded to width 4 by `len()` -> 4 code points, 3 rendered columns, versus `◕` -> 4 and 4. Padding sites `attention.py:1886, 2198, 2230, 2368`; spec Section 9.4 ("MUST NOT create per-renderer width guesses"). |
| F-08 | Low | The original F-03 (machine output is load-bearing) is correct but overstated as risk: verified that `--agent` and `--json` already emit zero ANSI, so criterion A14 is a characterization test to be pinned, not a gap to close. | Measured: `aw attention --agent` and `aw attention --json` each -> 0 ANSI bytes. AGENTS.md attention paragraph; criterion A14. |

## Proposed changes (ordered, validatable)

1. Convert the three lookup sites, remove the local lifecycle table, and retire the cross-module parity test that reads it (E-01).
2. Record the settled `_CLASS_COLOR_256` determination and drop its rung from the lifecycle chains (E-02).
3. Apply Section 9.1 styling, fix the three fallthrough statuses and the colored type column, and pad by rendered width (E-03).
4. Update snapshots and both files' hardcoded escape assertions while proving machine output unchanged (E-04).

## Deferred / out of scope (with reason)

- Attention's class computation and the class vocabulary itself: spec Section 3 excludes "changing lifecycle states, transition rules, attention classes". This child restyles rows; it does not reclassify them. `_CLASS_COLOR_256` is RETAINED for the section headers (E-02).
  - Carrier-Declined: Spec Section 3 excludes changing lifecycle states, transition rules, and attention classes as a stated NON-GOAL. This child restyles rows without reclassifying them, so nothing is outstanding.
- The `lanes` synthetic tree and its five states (`EMPTY`, `LANDED`, `LIVE`, `STRANDED`, `UNKNOWN`): none appears anywhere in spec `uonrjg` and none is covered by Section 5. Verified at review that they never become an `Item` and so never reach a lifecycle render site; they surface as `Drift` rows in the violations block and the LOUD stranded-lane section. So this is NOT a sixth orphan of the kind that blocked `udgilu`, and spec Section 12a's claim that `pr5b0t` "adds no status this spec must cover" is confirmed rather than assumed.
  - Carrier-Declined: NOT A LIFECYCLE SURFACE. The lane states never reach an `Item` or a lifecycle render site, so the spec owes them no stage and no plan owes them a conversion. Recorded because the question ("is this a missing mapping?") is the right one to ask and the answer had not been written down.
- Criterion A20's `?`-plus-diagnostic rendering for an unrecognized status: unreachable from this board, because `class_of` raises before any render site is reached and the scanner emits a violation instead. The resolver owes A20 (`udgilu`); views that can actually receive an unmapped value owe its rendering.
  - Carrier: 9zvl2w
- The other consumers: children `9zvl2w` (indexes, status commands, lint views, run viewers) and `qdd5jq` (runners and `render_stream`), because each has an independent snapshot surface.
  - Carrier: 9zvl2w
- A local display-width helper: forbidden by Section 9.4, which requires the width primitive be SHARED. This child consumes `bn026f`'s.
  - Carrier-Declined: The shared primitive is `bn026f`'s deliverable and this child's dependency, so there is no outstanding work: building a second one here is what the spec forbids.
- Column reordering: Section 12 requires existing column order be preserved unless a separately reviewed interface change alters it. Section 9.1 permits following an existing stable contract, so attention's order stays.
  - Carrier-Declined: Section 12 REQUIRES existing column order be preserved absent a separately reviewed interface change, and Section 9.1 permits following an existing stable contract. Preserving the order is compliance, not deferral.

## Scope check

- Over-scope: none. Every E-item maps to Section 12 step 3, R10.3, or criterion A10/A14.
- Under-scope: FOUR GAPS CLOSED AT REVIEW, all of them cases where the plan would have executed cleanly while leaving a release-gating criterion unmet. (1) The colored artifact TYPE column is a live A10 violation no plan in the Set owned (F-03), now E-03's. (2) Deleting `attention._STATUS_COLOR_256` breaks `tests/test_term.py`, which was outside the declared scope (F-04), now declared and owned by E-01. (3) The hardcoded escape assertions span two test files and only one was declared (F-06), now both. (4) A new glyph column would misalign under this file's bare-`len()` padding (F-07), now E-03's with `bn026f`'s primitive.
- The original "Under-scope: none" rested on E-02 being a genuine determination step, which it was; the gaps were elsewhere.

## Required tests / validation

Run the suite BARE: `python3 -m pytest` (no added flags). Paste the actual summary line and compare to the review baseline `7468 passed, 3 skipped, 2 xfailed` at HEAD `7e002486`, explaining any difference by node id. NOTE the sibling `bn026f` review recorded `8369 passed` one commit earlier; the lane was rebased between them, so THIS baseline is the one to use.

Validation must show:
- **A10** on a real rendered row: glyph, id6 and status word carry the SAME escape code, and artifact type, title and path carry NONE. Assert on raw escapes (`cat -v` or `repr`), never on stripped text, or the test cannot fail. The type column is the case most likely to regress, because it is colored today.
- **A14** as a characterization test: `aw attention --agent` and `--json` emit zero ANSI before and after. Verified zero at review, so a nonzero count is a new leak.
- **The three fallthrough statuses** each rendering their spec Section 6 stage: `plans/auto-approved`, `backlog/graduated`, `research/archive`.
- **The class rung is gone** from all three lifecycle chains, proven by reading the code, because the two palettes are identical today and the removal is invisible in output (F-05).
- **Rendered-width padding** for a VS-bearing glyph cell, proven against a non-VS cell in the same column.
- **`tests/test_term.py`'s parity test** either deleted or re-pointed, with the choice justified (F-04).

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`.

NO SPEC AMENDMENT IS OWED, checked at review rather than assumed. Three things this review could have turned into spec edits do not need one: the `lanes` states need no Section 5 stage because they are not a lifecycle surface (Deferred); the colored type column is resolved by Section 9.1 and Section 11 item 5 as already written, not by amending them; and A20's unreachability here is a property of `attention_contract`, not a gap in the spec. If the executor instead concludes the type color IS a Section 11 "existing independent convention" and keeps it, that reading contradicts A10 as written and WOULD require a spec amendment plus adding the spec path to `- Scope-Paths:`; report it rather than deciding it silently.

## Open questions

### OQ-01: Is `_CLASS_COLOR_256` in scope for removal?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier-Declined: RESOLVED AT REVIEW, so nothing outlives the plan. The determination is written into E-02 with its evidence, and V-02 now verifies the RETENTION plus the removal of the class rung rather than asking the executor to decide.
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-19 from the code, because the question was answerable without a maintainer and leaving it open invited the executor to re-derive it and possibly get it wrong. ANSWER: `_CLASS_COLOR_256` is NOT in scope for removal. Its five keys are the `A.*` attention CLASS constants, and spec Section 3 lists "attention classes" as an explicit NON-GOAL, so R10.3 (which scopes removal to LIFECYCLE tables) does not reach it and criterion A17 is satisfied with it in place. Parent `2xz59a` reached the same conclusion independently against the same evidence. TWO REFINEMENTS THE ORIGINAL QUESTION DID NOT ANTICIPATE, both now in E-02. FIRST, the check is a trap: all five class keys are bare strings identical to native status words with identical colors today, so a key-shape test answers "lifecycle" for all five; the keys must be traced to the `A.*` constants. SECOND, retention is not the whole answer - the `_CLASS_COLOR_256` RUNG must still be removed from the three lifecycle fallback chains, because after the conversion the two palettes diverge and leaving it would silently reintroduce the class palette into lifecycle rendering.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `grep -n "_STATUS_COLOR_256" agent_workflows/attention.py` returning NO matches, and paste the three new call sites showing they route through the shared `term.py` helpers. THEN paste the disposition of the cross-file breakage (F-04): `grep -n "_STATUS_COLOR_256" tests/test_term.py` must also return no match, and state in one line whether `test_status_palette_consistency_with_attention` was DELETED (because one table cannot drift from itself) or RE-POINTED at the shared resolver, and why. Paste the focused run of the three declared test files proving none errors on import.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `grep -n "_CLASS_COLOR_256" agent_workflows/attention.py` showing the definition and the SECTION-HEADER read still present, and showing it appears in NONE of the three lifecycle sites. Because the two palettes are byte-identical today, a board diff cannot prove the rung is gone (F-05), so the evidence MUST be the code. Paste the one-line determination with the `A.*` constant trace (not a key-shape argument) and the spec Section 3 citation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: FOUR pastes, because A10 has two independent failure modes here and two of the four items are corrections this review added.
    1. A10 POSITIVE: a real rendered row via `FORCE_COLOR=1 aw attention | cat -v`, showing the SAME `38;5;N` code on glyph, id6 and status word.
    2. A10 NEGATIVE, the type column (F-03): the same row showing the artifact TYPE carrying NO escape, contrasted with the pre-change output where it emitted `^[[1;38;5;33mplan^[[0m`. If the executor instead kept the color under the Section 11 exemption, paste that justification and flag that it contradicts A10 and needs a spec amendment.
    3. THE THREE FALLTHROUGH STATUSES (F-02): `plans/auto-approved`, `backlog/graduated`, `research/archive` each rendering its spec Section 6 stage rather than a borrowed class color. Do NOT paste a `?`-row for a bogus status: `class_of` raises before any render site, so such a row is unreachable and fabricating one would be false evidence.
    4. RENDERED-WIDTH PADDING (F-07): a VS-bearing glyph cell and a non-VS cell in the same column measuring the SAME rendered width, with the measurement shown. Contrast with the bare-`len()` result measured at review (`⚠︎` -> 3 rendered columns where `◕` -> 4).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the BARE `python3 -m pytest` summary line and compare to the baseline `7468 passed, 3 skipped, 2 xfailed` at HEAD `7e002486`, explaining any difference by node id. Paste an EMPTY diff of `aw attention --agent` before and after, and the same for `--json` (A14, verified zero-ANSI at review). Paste the updated human snapshot diff. THEN account for BOTH assertion files (F-06): show every changed hardcoded escape in `tests/test_attention.py` recomputed against spec Section 5, and state explicitly that `tests/test_attention_priority_blocker.py:54,67` were checked and LEFT UNCHANGED because they assert a PRIORITY color, not a lifecycle status; changing them would fold priority into lifecycle styling, which spec Section 3 forbids.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved f9t5hz --by-human`). Its `- Item-Dependencies: executed:bn026f` edge is re-checked at dispatch, because this child consumes the rendering helpers that plan provides, AND specifically the rendered-width primitive E-03 needs (F-07): without it, padding a glyph column here would require a local width guess, which Section 9.4 forbids. Note the edge names only the nearest dependency: `bn026f` itself depends on `udgilu` and `pow5sj`, and the runner sorts by dependency depth, so the transitive chain is honored without restating it.

OPEN QUESTIONS: OQ-01 is RESOLVED at review (the `_CLASS_COLOR_256` determination is written into E-02 with its evidence). There is no blocking question on this child. NOTE THE SET CONTEXT, which is not this plan's to resolve: the transitive chain `bn026f` -> `udgilu`/`pow5sj` carries two unresolved `- Blocking: yes` questions (`integration-deferred`'s stage, and whether `FORCE_COLOR` still defeats `NO_COLOR`), so `aw check` reports `check.ipd-dependency-findings-blocked` against those upstream plans and this child cannot dispatch until they are ruled on regardless of its own readiness. That is the dependency machinery working, not a defect here, and it must not be "fixed" by editing this file.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`agent_workflows/attention.py`, `tests/test_attention.py`, `tests/test_attention_priority_blocker.py`, `tests/test_term.py`). An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. In particular: do NOT delete `_CLASS_COLOR_256` (E-02 retains it; deleting it removes the section-header class palette the spec protects as a non-goal); do NOT touch `attention_contract.py`, because changing `class_of` or `CLASS_MAPS` would be a lifecycle change Section 3 excludes and would alter which statuses exist rather than how they look; do NOT convert any other consumer; do NOT add a local width helper; and do NOT edit `agent_workflows/term.py` itself, whose lifecycle table is `qdd5jq`'s to delete after every consumer moves off it. DO STOP AND REPORT for one genuinely unsafe condition: if `bn026f` did not ship the rendered-width primitive E-03 depends on, report that rather than padding a glyph column with `len()`, which reintroduces the exact defect F-07 records.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a rendered board, a width measurement, or a machine-output diff you did not run. A `V-*` evidence block must contain real output, not a description of expected output. In particular do NOT fabricate a `?`-plus-diagnostic row for a bogus status: verified at review that `class_of` raises before any render site, so no such row exists and pasting one would be false evidence.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
