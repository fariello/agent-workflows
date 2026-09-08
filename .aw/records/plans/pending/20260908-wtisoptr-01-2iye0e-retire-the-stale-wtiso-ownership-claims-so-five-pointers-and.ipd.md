# IPD: Retire the stale wtiso ownership claims so five pointers and one spec OQ stop naming a plan that will never run

- Date: 2026-09-08
- Kind: child
- Concern: Five in-code comments and one human-resolved spec question still name a RETIRED, UNLANDED plan as the live OWNER of unbuilt work, so the next reader deciding whether they may build that capability is sent to a plan that will never run. The `wtiso` Set was retired to `.aw/records/plans/superseded/` in `70b5338a` with Phases 4 (`58ha43`) and 5 (`2c122z`) retired UNLANDED. Nothing on `main` is broken by this; each site is a stale ownership CLAIM, not a behavior bug, which is why the item carries no release gate.
  ONE CLAIM IS NOW FACTUALLY FALSE RATHER THAN MERELY STALE, and the backlog item mislabels it. `runner_shutdown.py:218-219` says "the cross-platform ``platform_lock`` is owned elsewhere (`wtiso` Phase 5, `2c122z`), which this Set must not duplicate". But `agent_workflows/platform_lock.py` EXISTS on `main`: it shipped under plan `y6mfgo`, whose own record states the choice "SUPERSEDES the `platform_lock` portion of approved plan `2c122z`" (`:22`) and whose E-02 deliberately named the module `platform_lock` "to match what `2c122z` already refers to ... so that plan's prose still resolves" (`:40`). So that one site needs "already shipped under `y6mfgo`", not the "no successor" note the item prescribes for the others. Writing the item's generic note there would assert the capability is missing when it is present.
  THE SPEC IS THE DELICATE PART. Spec `c4gd2h` (`- Status: implementing`, `- Blocks-Release: next`) has OQ-03 at `:154-159`, `- Status: resolved`, `- Owner: human maintainer`, resolved 2026-08-29. Its resolution grounds the flag's location on Phase 4's accessors and states that "the out-of-repo path REQUIRES `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`) to be executed first". With both retired unlanded, that stated precondition is unsatisfiable as written. The resolved ANSWER remains correct (per-machine control state, inside the driver run dir, one accessor, never worktree-relative); only its cited SEQUENCING is stale. So this plan ADDS a note and MUST NOT reopen or rewrite a human-signed-off resolution.
- Scope: Rewrite the five surviving stale ownership pointers so each names the CAPABILITY and its actual status instead of a retired plan id, keeping every do-not-duplicate instruction intact; correct the one site whose claim is now false by citing the plan that shipped the capability; and append a note to spec `c4gd2h` OQ-03 recording that its cited precondition plans are retired and that the flag resolves through the in-repo accessor today, WITHOUT reopening the human-resolved answer. EXCLUDES the out-of-repo control-state relocation itself (Debt 1 of the item, which survives as its own backlog item); excludes any behavior change; excludes the `wtiso_gate.py` sites, which are already fixed; excludes `rchpms` citations, which are legitimate provenance for shipped code.
- Scope-Paths: agent_workflows/runner_stop.py, agent_workflows/runner_shutdown.py, agent_workflows/runner_shared.py, tests/fixtures/runner_shared_premove_fingerprints.json, .aw/records/specs/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: wtisoptr
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 2iye0e
- From-Backlog: ol8iyx

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `ol8iyx`, NARROWED. The item carries no `- Blocks-Release:` so none is inherited or invented. The item bundles TWO debts; this plan takes only Debt 2 (the stale pointers). Debt 1 (the out-of-repo relocation, which has no successor plan) is NOT graduated here because it is an open DECISION rather than a defined change, and it is recorded as a separate backlog item so it stays visible to `aw attention` instead of being buried in a plan that does not do it.
  I RAN THE ITEM'S OWN VERIFY-WITH GREP RATHER THAN TRUSTING ITS SITE LIST, and the list has changed. `grep -rn "58ha43\|2c122z\|7p9n2v" agent_workflows/` now returns 12 hits, of which SEVEN are in `wtiso_gate.py` and are ALREADY FIXED in exactly the style the item prescribes: executed plan `604wra` landed `1d9bbbd3` and rewrote `_unimplemented`'s contract so a message must name the owner AND ITS DISPOSITION, with `check_protected_refs:294` now reading "`2c122z` (Phase 5, RETIRED UNLANDED 2026-09-02) ... NEITHER is in flight and the recovery surface has no successor" and `check_receipt:423` recording that both owners were retired plus what did land. The item's own suggested fix (b) for `wtiso_gate.py` ("keep the skeleton, correct only the owner string") is therefore already delivered, and this plan excludes those sites so it does not re-edit them.
  ONE SITE IS MISLABELED BY THE ITEM AND I CORRECTED IT RATHER THAN COPYING THE PRESCRIPTION. The item lists `runner_shutdown.py`'s `platform_lock` comment among the "no successor" sites. It is not: `agent_workflows/platform_lock.py` exists, and executed plan `y6mfgo` states in its own history that it SUPERSEDES `2c122z`'s `platform_lock` portion and that it named the module to match `2c122z`'s references on purpose. Applying the item's generic note there would have written a false claim into the source, which is why E-02 is a separate item with a different message.
  TWO SITES THE ITEM'S GREP CANNOT FIND, discovered because I read the surrounding text rather than only the grep hits. `runner_stop.py:34-36` and `:41-44` are both in the module docstring; the second names Phase 4 by ID (`58ha43` does NOT appear there, it says "Set `wtiso` Phase 4" and cites `platform_state.checkout_state_root`), and `resolve_stop_request_path`'s docstring at `:362-363` says "when Set `wtiso` Phase 4 moves that accessor's answer" with no id6 at all. So the item's stated VERIFY-WITH grep would report success while two stale claims remained. E-03 fixes them and V-03 requires a PHRASE grep, not only an id6 grep.
  THE HAZARD THE ITEM DOES NOT MENTION, and it would have broken the suite. `describe_lane`'s docstring in `runner_shared.py` is frozen into an AST fingerprint fixture: `tests/fixtures/runner_shared_premove_fingerprints.json` holds `ast.dump(ast.parse(ast.unparse(node)))` for 34 symbols captured pre-move, and `tests/test_runner_shared.py` asserts each still fingerprints IDENTICALLY, which is deliberately falsifiable ("edit one moved line and this fails"). A docstring IS part of the unparsed body. I verified the breakage mechanically rather than predicting it: recomputing `describe_lane`'s fingerprint with the docstring edited returns a DIFFERENT dump. So E-04 must regenerate the fixture, and V-04 must show `tests/test_runner_shared.py` green (baseline `58 passed`) rather than assuming the edit is inert.

## Goal

Make every remaining pointer describe the CAPABILITY and its real status, so a reader deciding whether they may build the Windows process-tree kill, the recovery verbs, or the state relocation learns the truth (not implemented, no current owner, or already shipped elsewhere) instead of being sent to a plan that will never run, with every do-not-duplicate instruction preserved.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the pointers that genuinely have no successor

- [ ] E-01 REWRITE THE THREE `2c122z` NO-SUCCESSOR POINTERS to name the capability and its status instead of a retired owner. The sites, re-located by text: `runner_stop.py:34-36` (module docstring, "The Windows process-tree kill remains owned by Set `wtiso` Phase 5 (`2c122z`); do not build a second one here"), `runner_stop.py:1610-1611` (the same prohibition restated at the level-5 block), and `runner_shutdown.py:334-335` ("`wtiso` Phase 5 (`2c122z`) requires never auto-stashing, resetting, or overwriting a dirty user main").
  KEEP THE PROHIBITION, CHANGE ONLY THE OWNER. The item is explicit that the P8 do-not-duplicate instruction "is still the right guidance". Two of these three sites exist to STOP someone building a second implementation, and a rewrite that drops the prohibition while fixing the citation would remove a guardrail in the name of tidying prose. The shape the item prescribes: "not implemented; no current owner (was `wtiso` Phase 5 `2c122z`, retired unlanded 2026-09-02)".
  THE THIRD SITE IS DIFFERENT IN KIND AND MUST NOT GET THE SAME SENTENCE. `runner_shutdown.py:334-335` does not claim ownership of unbuilt work; it cites `2c122z` as the AUTHORITY for a still-correct requirement (never auto-stash a dirty user main). Read the surrounding paragraph: it independently grounds that requirement in house policy and GUIDING_PRINCIPLES 10. So the fix there is to attribute the requirement to the policy that survives, not to say "no owner" about a rule that is still in force.
  FOLLOW THE STYLE ALREADY LANDED IN `wtiso_gate.py`, which solved this exact problem under `604wra`: name the owner AND its disposition, and add a WHAT-DID-LAND note so a reader does not assume a total gap. Match that voice rather than inventing a second phrasing for the same idea.
  - Depends on: none
  - Expected outcome: the three sites name the capability and its status; every do-not-duplicate and never-auto-stash instruction is preserved verbatim in force; the still-correct requirement at `runner_shutdown.py:334-335` is attributed to surviving policy rather than declared ownerless.
  - Execution state: pending

- [ ] E-02 CORRECT THE ONE CLAIM THAT IS NOW FALSE: `runner_shutdown.py:218-219` says the cross-platform `platform_lock` "is owned elsewhere (`wtiso` Phase 5, `2c122z`), which this Set must not duplicate".
  THIS SITE GETS THE OPPOSITE NOTE FROM E-01, which is why it is its own item. The capability SHIPPED. `agent_workflows/platform_lock.py` exists on `main`; plan `y6mfgo` states it SUPERSEDES `2c122z`'s `platform_lock` portion, and its E-02 named the module `platform_lock` deliberately so that `2c122z`'s references still resolve. Writing "no current owner" here would assert something absent that is present.
  THE DO-NOT-DUPLICATE INSTRUCTION BECOMES STRONGER, NOT WEAKER, and that is the point: today it says "someone else will build this", which invites a reader to wait; it should say "this exists at `agent_workflows/platform_lock.py` (shipped under `y6mfgo`), so acquire through it and do not hand-roll a second lock". Cite the module by path so the next reader can go straight to it.
  VERIFY BEFORE WRITING, do not take this plan's word for it. Confirm `agent_workflows/platform_lock.py` exists and confirm `y6mfgo`'s supersession statement is really in its record. If either check fails, STOP and report rather than writing a citation you did not verify.
  - Depends on: none
  - Expected outcome: `runner_shutdown.py:218-219` states the capability exists, cites `agent_workflows/platform_lock.py` and plan `y6mfgo`, and keeps a do-not-duplicate instruction now grounded in a real module; both preconditions independently verified before the edit.
  - Execution state: pending

### Task group 2: the Phase 4 pointers, including the two no grep for an id6 will find

- [ ] E-03 REWRITE THE THREE PHASE 4 POINTERS, two of which are INVISIBLE to the item's own VERIFY-WITH grep because they name the phase in prose without its id6.
  THE THREE SITES, re-located by text rather than by the item's line numbers: `runner_stop.py:41-44` (module docstring, "Set `wtiso` Phase 4 relocates the driver run root OUT of the repository to `platform_state.checkout_state_root(<checkout-id>)/runs/<run-id>/`, and because this module resolves through the shared accessor it inherits that relocation automatically"), `runner_stop.py:362-363` (inside `resolve_stop_request_path`'s docstring, "when Set `wtiso` Phase 4 moves that accessor's answer out of the repository, the flag moves with it and nothing here changes (spec OQ-03)"), and `runner_shared.py:555-558` (`describe_lane`'s docstring, "`aw doctor --lanes` and `aw recover` are owned by plan `2c122z`").
  GREP FOR THE PHRASE, NOT ONLY THE ID6. Neither `runner_stop.py:41-44` nor `:362-363` contains the string `58ha43`, so the item's stated verification would pass while both stale claims remained. Search for "Phase 4", "Phase 5", "wtiso", and `platform_state` as well.
  PRESERVE THE ARCHITECTURAL POINT AT BOTH `runner_stop.py` SITES, because it is correct and load-bearing: this module resolves the flag through the drivers' own `state_root` accessor rather than constructing a path, so it inherits whatever that accessor answers and would inherit a future relocation for free. That is the reason the surrounding "DO NOT fix this back into `<repo>/.aw/state`" instruction exists. Rewrite the OWNER (a retired plan) into a capability status; do NOT delete the design rationale, and do NOT weaken the do-not-construct-a-second-root instruction.
  NAME THE SUCCESSOR TRACKER rather than leaving the relocation ownerless prose. The relocation survives as its own backlog item (filed alongside this plan), so these sites should point a reader at that item instead of at a retired plan. That is what makes this a re-pointing rather than a deletion of information.
  `describe_lane` IS THE FROZEN ONE. Its capability half is CORRECT (I confirmed `aw doctor --lanes` and `aw recover` do not exist: there is no `recover` verb in `cli.py`), so only the owner is stale. Editing this docstring breaks an AST fingerprint; E-04 handles that and this item must not be marked done until E-04 is performed.
  - Depends on: none
  - Expected outcome: all three sites name the capability and its status, cite the successor backlog item rather than a retired plan, and retain the accessor-indirection rationale and the do-not-construct-a-second-root instruction; located by phrase search, not by id6 alone.
  - Execution state: pending

- [ ] E-04 REGENERATE THE AST FINGERPRINT FIXTURE FOR `describe_lane`, because E-03's docstring edit provably breaks a freeze test.
  WHY THIS IS NOT OPTIONAL. `tests/fixtures/runner_shared_premove_fingerprints.json` holds `ast.dump(ast.parse(ast.unparse(node)))` for 34 symbols, and `tests/test_runner_shared.py` asserts each moved body still fingerprints IDENTICALLY, by design: its docstring says "edit one moved line and this fails". A docstring is part of the unparsed body. I verified mechanically that recomputing `describe_lane`'s fingerprint with the docstring changed yields a DIFFERENT dump, so this is a measured consequence, not a worry.
  REGENERATE ONLY THE ONE SYMBOL'S ENTRY. A wholesale re-capture would silently re-baseline all 34 and destroy the falsifiability the harness exists for, turning a real guard into a decorative one. If no targeted regeneration path exists, say so and regenerate narrowly by hand, showing a diff that touches exactly one fingerprint.
  RECORD WHY THE FIXTURE MOVED, in the fixture or in the test's prose. The fixture's whole value is that a change to it is suspicious; an unexplained edit teaches the next reader that re-baselining is routine. State that the change is a docstring-only ownership correction with no body change.
  PROVE THE BODY DID NOT CHANGE, not merely that the test passes. The claim is "docstring only", so show it: the function's non-docstring AST must be identical before and after.
  - Depends on: E-03
  - Expected outcome: exactly one fingerprint entry regenerated, with the reason recorded; `tests/test_runner_shared.py` green; independent proof that only the docstring changed and the executable body did not.
  - Execution state: pending

### Task group 3: the spec, which must be annotated and not reopened

- [ ] E-05 APPEND A NOTE TO SPEC `c4gd2h` OQ-03 recording that its cited precondition plans are retired unlanded and that the flag resolves through the in-repo accessor today, WITHOUT reopening the human-resolved answer.
  DO NOT CHANGE `- Status: resolved` AND DO NOT REWRITE THE RESOLUTION. OQ-03 was resolved by the HUMAN maintainer on 2026-08-29 (`- Owner: human maintainer`) and its ANSWER is still correct: per-machine control state, inside the driver run dir, one accessor, never a worktree-relative path. Only the cited SEQUENCING is stale ("the out-of-repo path REQUIRES `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`) to be executed first"). Reopening a signed-off question, or editing the maintainer's words, would be writing an attestation this plan has no authority to write. ADD; do not revise.
  WHAT THE NOTE MUST SAY, so it is useful rather than decorative: that `7p9n2v` and `58ha43` are retired to `superseded/` unlanded, so the stated precondition is unsatisfiable as written; that the flag TODAY resolves through the drivers' own `state_root` accessor and works, so nothing is broken; that the resolved answer stands and the relocation is tracked by the successor backlog item; and that `platform_state.state_home`/`checkout_state_root` do NOT exist on `main` (I confirmed: no `platform_state.py`, and neither symbol appears in any code), so a reader does not go looking for them.
  THIS IS A DECLARED SPEC EDIT AND THE SPEC FILE IS IN `- Scope-Paths:` FOR THAT REASON. Both runners announce declared spec edits BEFORE a run starts and the finalize scope gate reconciles actual against declared, so the declaration is what makes this amendment visible rather than a surprise. The spec also carries `- Blocks-Release: next`, so treat any edit to it as consequential and keep it strictly additive.
  DO NOT TOUCH THE SPEC'S OWN `- Status: implementing`, its requirement list, or any other OQ. The scope here is one note under one resolved question.
  - Depends on: E-03
  - Expected outcome: OQ-03 carries an additive note stating the retirement, the current in-repo resolution path, the surviving successor tracker, and the absence of the `platform_state` symbols; `- Status: resolved`, the maintainer's resolution text, the spec's own status, and every other OQ are unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE HOUSE STYLE FOR THIS EXACT FIX ALREADY EXISTS AND SHIPPED. `604wra` (`1d9bbbd3`) rewrote `wtiso_gate.py`'s labels to name the owner AND its disposition, added WHAT-DID-LAND paragraphs, and is pinned by `tests/test_containment_predicates.py`. Follow that voice; do not invent a second phrasing.
- THE `wtiso_gate.py` SITES THE ITEM LISTS ARE ALREADY DONE (`:294`, `:423`, `:440`, module docstring `:37-43`). Excluded from this plan.
- `rchpms` CITATIONS ARE LEGITIMATE AND MUST NOT BE TOUCHED. Phase 2 PARTLY LANDED (`frozen_region_digest`, `cdef9c90`), so `ipd_lifecycle.py:105` and the driver citations are historical provenance for SHIPPED code, not stale ownership. The item says this explicitly and it checks out. Note the item's own line numbers for two of those citations are stale (it says `oc_runipd.py:4223` and `agy_runipd.py:2345`; they are now `:5530` and `:2720`), which is itself a reminder to re-locate by symbol.
- A DOCSTRING IS PART OF AN AST FINGERPRINT. `tests/fixtures/runner_shared_premove_fingerprints.json` plus `tests/test_runner_shared.py` freeze 34 symbols including `describe_lane`. This is the plan's main trap and the item does not mention it.
- THE ITEM'S VERIFY-WITH GREP IS INSUFFICIENT. Two stale Phase 4 claims name the phase in prose with no id6, so an id6-only grep reports success while they survive. Grep by phrase.
- `aw doctor --lanes` AND `aw recover` GENUINELY DO NOT EXIST (no `recover` verb in `cli.py`), so `describe_lane`'s capability claim is correct and only its owner is stale.
- THE DOCS TABLE IS DELIBERATELY EXCLUDED. `docs/wtiso-state-taxonomy.md` has an owner column naming `58ha43`/`2c122z` in about a dozen rows and is FROZEN by `tests/test_wtiso_taxonomy_freeze.py`, whose `WTISO_CHILDREN` set (`:52-60`) enumerates those ids on purpose. It is a historical migration-ownership table, not a live pointer. See the deferred section.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `fac69fbd`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | N/A | `agent_workflows/wtiso_gate.py:294`, `:423`, `:440`, `:37-43` | SEVEN OF THE ITEM'S TWELVE SITES ARE ALREADY FIXED, by executed plan `604wra` (`1d9bbbd3`), in precisely the style the item's suggested fix (b) prescribes. Excluded from this plan. | grep, source read, that plan's record |
| F-2 | HIGH | `agent_workflows/runner_shutdown.py:218-219` | THE ITEM MISLABELS THIS SITE. It says `platform_lock` "is owned elsewhere (`2c122z`)", but `agent_workflows/platform_lock.py` EXISTS, shipped under `y6mfgo`, whose record states it SUPERSEDES `2c122z`'s `platform_lock` portion (`:22`) and named the module to match its references (`:40`). Applying the item's generic "no successor" note here would write a FALSE claim. | `ls` the module; that plan's record |
| F-3 | HIGH | `tests/fixtures/runner_shared_premove_fingerprints.json`, `tests/test_runner_shared.py` | EDITING `describe_lane`'S DOCSTRING BREAKS AN AST FREEZE. The fixture holds `ast.dump(ast.parse(ast.unparse(node)))` for 34 symbols and the test asserts identity by design. I recomputed the fingerprint with the docstring edited: it DIFFERS. The item does not mention this. | ran the recomputation; baseline `58 passed` |
| F-4 | MED | `agent_workflows/runner_stop.py:41-44`, `:362-363` | TWO STALE PHASE 4 CLAIMS ARE INVISIBLE TO THE ITEM'S OWN VERIFY-WITH GREP: both say "Set `wtiso` Phase 4" in prose with no `58ha43` anywhere, so an id6-only grep returns success while they survive. | grep returned 12 hits, neither of these among them; source read |
| F-5 | N/A | `agent_workflows/platform_state.py`, `state_home`, `checkout_state_root` | THE PHASE 4 CAPABILITY IS GENUINELY ABSENT: no `platform_state.py`, and neither symbol appears in any code (only in spec, item and plan prose). So the pointers describe real unbuilt work; the owner is what is wrong. | `ls`; repo-wide grep |
| F-6 | N/A | `agent_workflows/ipd_lifecycle.py:190` | THE DEFECT PHASE 4 WAS LINKED TO IS CLOSED, which is why this is not urgent: `checkout_control_root` collapses every worktree of a checkout onto one control root via `git rev-parse --git-common-dir`, pinned by `tests/test_statefork_dh0uno.py`. | source read; file exists |
| F-7 | MED | spec `c4gd2h:154-159` | OQ-03 IS HUMAN-RESOLVED (`- Owner: human maintainer`, 2026-08-29) AND ITS PRECONDITION IS NOW UNSATISFIABLE as written ("REQUIRES `wtiso` Phase 3+4 ... executed first"). The ANSWER is still correct; only the sequencing is stale. The spec carries `- Blocks-Release: next`. So the edit must be additive and must not reopen the resolution. | spec read |
| F-8 | LOW | `agent_workflows/runner_shutdown.py:334-335` | THIS SITE IS A DIFFERENT KIND from the other `2c122z` hits: it cites the retired plan as AUTHORITY for a still-correct requirement (never auto-stash a dirty user main), which the surrounding paragraph independently grounds in house policy and GUIDING_PRINCIPLES 10. It needs re-attribution, not a "no owner" note. | source read |
| F-9 | LOW | `tests/test_lane_allocation_idempotent.py:656`, `:339` | TWO TEST-PROSE SITES REPEAT THE STALE CLAIM (the `aw doctor --lanes`/`aw recover` ownership, and "Plan `2c122z` E-06 DEPENDS on this"). The item does not list them. Not in this plan's `- Scope-Paths:`; see the deferred section. | grep |
| F-10 | LOW | `docs/wtiso-state-taxonomy.md:69-97`, `tests/test_wtiso_taxonomy_freeze.py:52-60` | THE DOCS OWNER TABLE NAMES THESE IDS IN ABOUT A DOZEN ROWS AND IS FROZEN BY TEST, with `WTISO_CHILDREN` enumerating them deliberately. It is a historical migration-ownership record, not a live pointer. Deferred. | source read |

## Proposed changes (ordered, validatable)

1. E-01 rewrites the three `2c122z` no-successor pointers to name the capability and its status, keeping every prohibition in force and re-attributing the still-correct never-auto-stash requirement.
2. E-02 corrects the one false claim by citing `agent_workflows/platform_lock.py` and plan `y6mfgo`, strengthening rather than removing its do-not-duplicate instruction.
3. E-03 rewrites the three Phase 4 pointers (two invisible to an id6 grep), preserving the accessor-indirection rationale and pointing at the successor backlog item.
4. E-04 regenerates exactly one AST fingerprint entry, with the reason recorded and proof that only the docstring changed.
5. E-05 appends an additive note to spec `c4gd2h` OQ-03 without reopening the human-resolved answer.

## Deferred / out of scope (with reason)

- THE OUT-OF-REPO CONTROL-STATE RELOCATION ITSELF (Debt 1 of `ol8iyx`). This is an open DECISION, not a defined change: whether to relocate at all now the state-fork defect is closed, the migration path for existing receipts, locks and journals, whether the driver run root moves too, and the Windows/XDG-absent fallback. The item itself lists these as "what a successor would have to decide". Graduating it into this plan would mean either implementing an undecided design or writing a plan that does nothing. It survives as its own backlog item, filed with this plan, so `aw attention` keeps seeing it.
- ALL `wtiso_gate.py` SITES. Already fixed by executed `604wra` (F-1). Re-editing them would be re-doing landed work.
- EVERY `rchpms` CITATION. Phase 2 partly landed, so those are legitimate provenance for shipped code. The item says so and I confirmed it.
- `docs/wtiso-state-taxonomy.md`'s OWNER TABLE. F-10: a historical migration-ownership table, frozen by `tests/test_wtiso_taxonomy_freeze.py` whose `WTISO_CHILDREN` set enumerates these ids on purpose. Rewriting it means re-baselining a freeze for prose that is not a live ownership claim. Recorded as noticed and judged, not missed.
- THE TWO TEST-PROSE SITES IN `tests/test_lane_allocation_idempotent.py` (F-9). Not in this plan's scope-paths, and one of them ("Plan `2c122z` E-06 DEPENDS on this") is a statement about a retired plan's dependency, which is historically true. Flagged for the maintainer rather than silently swept in.
- ANY BEHAVIOR CHANGE. This plan edits comments, docstrings, one fixture entry, and one additive spec note. No executable line changes; E-04 requires proving that.

## Scope check

- Over-scope: none. All five declared paths are modified: `runner_stop.py` (E-01, E-03), `runner_shutdown.py` (E-01, E-02), `runner_shared.py` (E-03), the fingerprint fixture (E-04), and the spec (E-05).
- Under-scope: stated rather than left as `none`. After this plan, `docs/wtiso-state-taxonomy.md` still names the retired ids in its owner column (F-10) and `tests/test_lane_allocation_idempotent.py` still repeats the stale ownership claim twice (F-9), both deliberately. So the item's VERIFY-WITH grep, if run repo-wide rather than over `agent_workflows/` only, will still return hits; V-03 must therefore assert on the SCOPED grep the item actually specifies and enumerate the known remaining out-of-scope hits rather than claiming zero.

## Required tests / validation

`python3 -m pytest` bare in the executing worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS rather than totals. Then, explicitly, the suites this plan can actually break: `tests/test_runner_shared.py` (the AST freeze E-04 touches; pre-change baseline `58 passed`), `tests/test_containment_predicates.py` and `tests/test_wtiso_characterization.py` and `tests/test_wtiso_taxonomy_freeze.py` (they assert on wtiso prose and labels), and `tests/test_runner_stop_triggers.py`. Because every code edit here is comment-only, the strongest validation is a mechanical no-behavior-change proof: show that the AST of each edited module with docstrings stripped is unchanged. Do not rely on a green suite alone to prove that, since a comment change that accidentally deleted a line of code could still pass unrelated tests.

## Spec / documentation sync

THIS PLAN DELIBERATELY AMENDS A SPEC, which is why `.aw/records/specs/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md` is declared in `- Scope-Paths:`. The declaration is load-bearing: both runners announce declared spec edits before a run starts, and the finalize scope gate reconciles what was actually changed against what was declared, so an undeclared spec edit is exactly the invisible contract change that rule exists to prevent.
WHY THE AMENDMENT BELONGS HERE rather than being left to drift: OQ-03's resolution cites, as a PRECONDITION, two plans that no longer exist as live work. A spec that states an unsatisfiable precondition sends every future reader down a dead path, and the sites this plan rewrites all point back at that same OQ. Fixing the pointers while leaving the spec's sequencing stale would leave the authority contradicting the code that cites it.
THE AMENDMENT IS STRICTLY ADDITIVE AND THE LIMIT IS THE POINT. OQ-03 is `- Status: resolved` with `- Owner: human maintainer`. This plan may add a note recording the retirement and today's resolution path; it may NOT change the status, rewrite the resolution, or alter the spec's own `- Status: implementing`. The spec carries `- Blocks-Release: next`, so a careless edit here touches a release-gating contract. If the executor concludes the resolved ANSWER itself needs revisiting, that is a maintainer decision: stop and report, do not decide it inside this plan.

## Open questions

### OQ-01: Should the docs taxonomy owner table be rewritten too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as NO. `docs/wtiso-state-taxonomy.md:69-97` names `58ha43`/`2c122z` in an owner column across about a dozen rows, and the table is frozen by `tests/test_wtiso_taxonomy_freeze.py`, whose `WTISO_CHILDREN` set (`:52-60`) enumerates every wtiso child id deliberately. The table records WHICH PHASE WAS RESPONSIBLE for each state-migration, which is a historical fact that retirement does not falsify, unlike a code comment saying "this is owned, do not build it". Rewriting it would mean re-baselining a freeze test to change prose that is not a live ownership claim. Recorded so a later reader sees this was judged rather than overlooked; if the maintainer wants the table annotated as retired, that is a small separate change.

### OQ-02: Do the two stale claims in `tests/test_lane_allocation_idempotent.py` belong in this plan?

- Blocking: no
- Status: open
- Owner: the maintainer for the scope call
- Resolution or deferral rationale: NOT blocking, because they are test PROSE and mislead no reader about production ownership. `:656` repeats the `aw doctor --lanes`/`aw recover` ownership claim and `:339` says "Plan `2c122z` E-06 DEPENDS on this", which is historically TRUE of a retired plan and arguably should stay. They are outside this plan's `- Scope-Paths:` and I did not sweep them in, both because the file is not mine to edit for prose and because a shared checkout makes silent widening of scope hostile to whoever else is in that file. Flagged for the maintainer; folding them in later is trivial.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the before and after text of all three sites. For each, show the do-not-duplicate or never-auto-stash instruction still present and still imperative. For `runner_shutdown.py:334-335` specifically, show the requirement re-attributed to surviving policy rather than declared ownerless, and quote the surrounding paragraph proving that policy grounding already existed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `ls agent_workflows/platform_lock.py` proving the module exists, and paste the line from `y6mfgo`'s record stating it supersedes `2c122z`'s `platform_lock` portion. Then paste the before and after of `runner_shutdown.py:218-219`, showing the new text cites the real module path and plan and still forbids a second lock. Confirm explicitly that this site did NOT receive E-01's "no current owner" wording.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the before and after of all three sites, showing the accessor-indirection rationale and the do-not-construct-a-second-root instruction retained, and the successor backlog item cited. Paste BOTH greps: the item's `grep -rn "58ha43\|2c122z\|7p9n2v" agent_workflows/` AND a phrase grep for "Phase 4", "Phase 5" and "wtiso" over `agent_workflows/`, since F-4 shows the first alone is insufficient. Enumerate every remaining hit and classify each as fixed, legitimate `rchpms` provenance, or deliberately out of scope; a bare claim of zero hits is not acceptable given the Scope check.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_runner_shared.py` GREEN (pre-change baseline is `58 passed`). Paste a `git diff` of the fixture showing exactly ONE fingerprint entry changed, not 34. Paste the recorded reason for the fixture change. Paste independent proof that only the docstring changed: the AST of `describe_lane` with its docstring stripped must be identical before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `git diff` of the spec file, which must show ONLY an addition under OQ-03. Paste the unchanged lines proving `- Status: resolved`, `- Owner: human maintainer`, the maintainer's resolution text, the spec's own `- Status: implementing`, and every other OQ are untouched. Paste the note's text showing it states the retirement, today's in-repo resolution path, the successor tracker, and the absence of `platform_state.state_home`/`checkout_state_root` (paste the grep proving that absence). Paste `aw specs check` conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the five paths in `- Scope-Paths:`. Do NOT edit any `wtiso_gate.py` site (already fixed by `604wra`). Do NOT edit any `rchpms` citation (legitimate provenance for shipped code). Do NOT edit `docs/wtiso-state-taxonomy.md` (OQ-01, resolved) or `tests/test_lane_allocation_idempotent.py` (OQ-02). Do NOT change `- Status: resolved` on OQ-03, do NOT rewrite the maintainer's resolution, and do NOT touch the spec's own status or any other OQ. Do NOT implement the relocation itself. Do NOT change one executable line: every code edit here is comment-only and V-04 requires proving it. Do NOT re-baseline all 34 fingerprints. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL AND BY PHRASE, NEVER BY THE LINE NUMBERS IN THIS PLAN. `runner_stop.py`, `runner_shutdown.py` and `runner_shared.py` are under concurrent edit and these numbers will move (the backlog item's own numbers moved by up to 170 lines in three days). Find `resolve_stop_request_path`, `describe_lane`, `RunLockHandle` and `observe_tree` by name, and find the module-docstring sites by their quoted text.

SHARED CHECKOUT WARNING, sharper here than usual: all three runner modules are among the most heavily edited files in this repository and other agents may be in them right now. Before editing, confirm the target text is present as quoted; if it has already changed, STOP and report rather than reconciling someone else's in-flight edit.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 2iye0e --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, backlog `ol8iyx` (carried as `- From-Backlog:`) is closed only for its Debt 2; Debt 1 (the relocation) is NOT delivered here and lives on as its own backlog item, so set `ol8iyx` to `graduated` rather than `done` and confirm the successor item exists first. That item carries no release gate, so none is inherited.
