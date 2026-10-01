# IPD: Key the derive_plan_status baseline by plan id6 so a terminal-plan rename or archive shard cannot erode the floor

- Date: 2026-09-29
- Kind: child
- Concern: `tests/test_history_order.py::DerivationIsUnchangedTests` compares a frozen baseline keyed by repo-relative PATH against the live terminal-plan tree, so any operation that moves a terminal plan (`aw rename plans`, `aw group plans --rename`, `aw archive plans`) silently shrinks the compared set toward a hard `assertGreaterEqual(..., 700)` floor and reddens the suite with a message that names the wrong cause.
- Scope: Re-key the baseline fixture and its only reader from path to plan `id6`, the repo's stable cross-tree handle, and replace the single frozen intersection floor with two self-diagnosing assertions (a coverage fraction of the baseline, plus a retained absolute floor on the FIXTURE's own size so the fraction cannot go vacuous). Pure re-key of already-frozen values; the `derive_plan_status` algorithm and every other test are untouched.
- Scope-Paths: tests/fixtures/derive_plan_status_baseline.json, tests/test_history_order.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: p0a5kr
- Blocks-Release: next
- Set: p0a5kr
- Order: 1
- Highest E allocated: 04
- Author: agent aw oc run
- Id: rlcq7g

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: rlcq7g verified (set p0a5kr, attempt 1).
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-29 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 all FIXED. Premise re-measured at HEAD `f5c6114b` (291 commits after the plan's `afb948ce`): 777 baseline keys, 882 live terminal plans, 732 intersection, and the re-key prototyped lossless (732 -> 732, value multiset equal, 0 mismatches). PR-001 (HIGH): OQ-01's fraction-only floor is vacuous against a shrinking fixture and contradicts its own stated rationale (a 10-entry fixture with all 10 found scores 100 percent and passes), so E-03 now carries a retained `len(baseline) >= 700` non-vacuity floor beside the coverage fraction. PR-003 (HIGH): 33 of the 732 carried values are JSON `null` and E-01 never said so, so a natural falsy-filter transform would have dropped 33 entries while satisfying every stated check but the count. PR-004: id6 keying opens a duplicate/absent-id silent-coverage-loss mode that path keying could not have; E-02 now asserts against it. PR-005: E-04's shared helper could not have served both callers as specified. PR-006: F-3 understated itself; one argument-free `aw archive plans --apply` takes the intersection from 732 to 118 today (614 sweep candidates at the 14-day default). PR-008: gate gained a scope fence and the runner/executor lifecycle conditional. Two V-items demanded evidence that measurably proves nothing (V-03's "a few extra ids" passes at 3, 10 and even 38; V-02's sanctioned history note does not change any derived status) and were corrected. Findings and decisions D-1..D-5 in `.aw/records/reviews/20260929-p0a5kr-01-rlcq7g-key-the-derive-plan-status-baseline-by-plan-id6-so-a-termina.review.md`.
- 2026-09-29 draft (agent aw oc run): created.
- 2026-09-29 to-review (agent aw oc run): graduated backlog `p0a5kr`; premise re-measured at `afb948ce` and the fix direction chosen on measured evidence (see Findings).

## Goal

Make the `derive_plan_status` anti-regression guard invariant to where a terminal plan FILE lives, so that renaming or archiving a plan cannot erode it, and so that when it does fail it fails for the one reason it exists to catch: the derivation changed. Re-key the fixture from path to `id6` and make the coverage assertions self-diagnosing.

WHAT THIS DOES NOT CLAIM, stated so the Goal is not read as broader than the change. It does not grow coverage: the compared set stays at exactly the 732 plans compared today, and the roughly 150 live terminal plans absent from the baseline stay absent (deliberately, see Deferred). It does not make the guard immune to every cause of a shrinking comparison: a plan DELETED, moved OUT of a terminal directory, or given a different `- Id:` still reduces coverage and will still trip the coverage floor, which is correct, because each of those is a real event a human should see. And it does not make the guard more SENSITIVE than before; F-12 records that the coverage floor first fires at 37 missing ids where the old absolute fired at 33. What it removes is the whole class of failures caused by a file MOVE, which is the class that had no business affecting this guard at all and which one argument-free `aw archive plans --apply` would otherwise trigger at scale today (F-3, F-16).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-key the fixture

- [x] E-01 Rewrite `tests/fixtures/derive_plan_status_baseline.json` as a mapping of plan `id6` -> frozen derived status, by PURE RE-KEY of the existing file rather than by fresh capture. For each of the current 777 path keys that (a) resolves to a live file under `executed/`, `superseded/`, or `not-executed/` and (b) is in the intersection the test compares today, read that file's text, take its declared id6 via `selectors.read_front_matter_id`, and carry the EXISTING frozen value across unchanged. Emit sorted-by-id6 JSON with a trailing newline. Do NOT call `derive_plan_status` to produce the values: re-deriving would silently re-baseline a real regression as the new truth, destroying the only evidence the guard holds. Drop the 45 `pending/` keys (all 45 are already uncomparable dead weight, see F-4) and do NOT resurrect them by id6 (see F-5, which is the trap in this task).
  PRESERVE JSON `null` AS A FIRST-CLASS VALUE (F-13). 33 of the 732 carried entries have the value `null`, not a status string, recorded by plan `63h054` E-01's "`null` for None" convention because `derive_plan_status` returns `None` for a plan whose history declares no status event. A transform that filters falsy values, coerces `null` to `""`, or skips an entry whose value is `None` silently drops 33 entries and, worse, converts 33 real comparisons into no comparison at all. Carry `null` through unchanged and keep comparing it: `assertEqual`-style comparison of `None == None` is exactly the check those 33 entries need.
  USE `selectors.read_front_matter_id` (or its whole-file twin `selectors.declared_id6`) AND NOTHING ELSE. Do NOT reach for `selectors.filename_slot_id6`, which is the WRONG resolver and fails on 95 of the 732 keys you must carry (measured; F-6).
  - Depends on: none
  - Expected outcome: The fixture is a JSON object of exactly 732 entries; every key matches `^[0-9a-z]{6}$`; the multiset of VALUES is identical to the multiset of the 732 values carried over, INCLUDING all 33 `null` values (so no status was invented, changed, re-derived, or dropped); no key is a path; no `pending/`-era entry survives.
  - Execution state: performed

### Task group 2: re-key the reader and fix the diagnosis

- [x] E-02 In `tests/test_history_order.py::DerivationIsUnchangedTests.test_whole_tree_derivation_is_unchanged`, build the live side as an `id6 -> (repo-relative path, derived status)` map over the same three terminal buckets it globs today, reading each plan's text ONCE and taking both `selectors.read_front_matter_id(text)` and `il.derive_plan_status(text)` from that one string. Intersect on id6 instead of on path. Keep the existing terminal-bucket restriction (it is load-bearing, see F-4) and keep the `mismatches` comparison and its first-20 truncation. Report each mismatch as `<id6> (<current path>): expected <frozen>, got <derived>` so a failure still names a file a human can open even though the key no longer is one.
  DO NOT LET A KEY COLLISION OR A MISSING `- Id:` PASS SILENTLY (F-14). Keying by id6 introduces a failure mode path-keying could not have: two live terminal plans declaring the SAME `- Id:`, where a dict build silently keeps whichever the glob visited last and drops the other from comparison, or a terminal plan declaring NO `- Id:`, where `read_front_matter_id` returns `None` and every such plan collapses onto a single `None` key. Neither is true today (measured: 882 terminal plans, 882 declared ids, 0 collisions, 0 missing) and this guard exists so a future violation fails LOUDLY instead of quietly shrinking coverage. While building the map, collect any id6 seen twice and any file whose declared id is `None`, and assert BOTH collections are empty with a message naming the offending paths. `check.id6-collision` polices this repo-wide, but this test must not depend on that check having been run.
  - Depends on: E-01
  - Expected outcome: The test intersects on id6, performs exactly one read per terminal plan, and its mismatch lines carry id6, the plan's CURRENT path, the expected status, and the derived status. A duplicate declared id6 or a terminal plan with no `- Id:` fails the test by name rather than silently reducing the compared set.
  - Execution state: performed

- [x] E-03 Replace the frozen `assertGreaterEqual(len(intersection), 700)` with TWO assertions, because one alone is measurably insufficient (F-11, F-12). FIRST, a COVERAGE assertion on the found FRACTION: require that at least 95 percent of the fixture's entries resolve to a plan in the live terminal tree, computed as `found >= 0.95 * len(baseline)`. SECOND, a NON-VACUITY assertion on the fixture's own SIZE: require `len(baseline) >= 700`, retaining the frozen absolute for THAT purpose alone. The two assertions guard different failures and neither substitutes for the other: the fraction catches baseline ids that have gone missing from the live tree, while the size floor catches a fixture that was truncated, emptied, or regenerated too small, which a pure fraction CANNOT catch because a 10-entry fixture with all 10 found scores 100 percent and passes (measured, F-11). Write BOTH failure messages to name their own real cause and remedy: the coverage message says that baseline ids are missing from the live terminal tree (a plan was deleted, or moved OUT of a terminal directory, or had its `- Id:` changed), NOT that `derive_plan_status` regressed, and that a legitimate mass change requires re-keying the fixture; the size message says the fixture itself shrank and must be re-keyed from the committed file rather than re-captured. State in a comment that the SIZE floor is deliberately absolute and is NOT the rotting kind the plan removes: it bounds the fixture, a frozen authored artifact whose entry count changes only when someone edits it, whereas the old 700 bounded the live-tree INTERSECTION and so rotted with every file move. A rename or an archive shard must not be able to trip either assertion, because neither changes a plan's `- Id:` and neither changes the fixture.
  - Depends on: E-02
  - Expected outcome: Two assertions replace the one: a coverage floor relative to `len(baseline)` and a non-vacuity floor `len(baseline) >= 700`. Each carries its own message naming its own cause. Neither is reachable by any number of renames or archive shards. A truncated fixture fails the second even when every surviving entry is found.
  - Execution state: performed

- [x] E-04 Add a behavioral regression test in `tests/test_history_order.py` that proves the decoupling by CONSTRUCTION rather than by assertion about the live tree: build a temporary repo containing a handful of terminal plans plus an id6-keyed baseline, run the same intersect-and-compare logic, then physically rename every plan file (and additionally move one into a `YYYYMM/` shard subdirectory, the shape `aw archive plans` produces) WITHOUT touching any `- Id:`, and assert the comparison still finds every entry and still reports zero mismatches. Then, as the discriminating negative, mutate one plan's history so its derived status genuinely changes and assert the test's comparison DOES report that one plan as a mismatch. Use the existing module-level `_fixture_plan_text(id6, history_text, status=...)` helper to author the temporary plans rather than writing a second plan-text builder; it already emits a conforming plan with a settable `- Id:` and `## Workflow history`, which is exactly what this test needs.
  THE SHARED HELPER TAKES A ROOT AND RETURNS DATA; IT DOES NOT ASSERT (F-15). Extract exactly one module-level function that takes a repository root plus a baseline mapping and RETURNS the comparison result (the live id6 map, the found-id set, and the mismatch list), leaving every `assert*` call in the two test methods. This is what lets the new test drive the helper against a TEMPORARY root while the whole-tree guard drives it against `_repo_root()`, so the two genuinely share the logic under test; a helper that asserts internally, or that hard-codes `_repo_root()`, cannot be pointed at a temp repo and the "cannot drift apart" claim would be false.
  A DERIVED-STATUS CHANGE MUST BE PRODUCED BY A HISTORY EDIT, NOT BY EDITING THE BASELINE (F-15). The discriminating negative must perturb the PLAN so `derive_plan_status` genuinely returns something else; changing the fixture value instead would prove only that two unequal strings compare unequal. Two perturbations are measured to work on a real executed plan: appending a later-dated `draft` history record flips the derived status to `draft`, and deleting the `executed` history record flips it to `approved`. Note for contrast that appending the dated cross-reference note `AGENTS.md` sanctions on an executed plan does NOT change the derived status (measured over all 262 non-`executed`-valued and `null`-valued compared entries: zero flips), which is why that sanctioned append is safe and is not what this negative should use.
  - Depends on: E-03
  - Expected outcome: A new test that fails if the path-coupling is ever reintroduced and that still catches a real derivation change; both the whole-tree guard and the new test call one shared root-parameterized helper that performs no assertions; the negative is produced by editing plan history, not the baseline.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The canonical id6 readers live in `agent_workflows/selectors.py`: `selectors.read_front_matter_id(text)` is the documented public text reader ("Return the `- Id:` id6 from a record's METADATA REGION, or ``None``", bounded to `metadata_region` so a QUOTED `- Id:` in a body is not read as a declaration), and `selectors.declared_id6(path)` is its whole-file twin. Both host runners re-export the former. Because `il.derive_plan_status` takes TEXT ONLY, a loop that already reads the text can take the id6 from the same string with no extra read; E-02 relies on this.
- Do NOT add a tenth duplicate `- Id:` regex. `selectors.declares_id6` documents the existing byte-identical twins (`plans_refs`, `plans_index`, `check_engine`, `artifact_rename`, `record_history`, `plans_archive`, `specs`, `releases`, `ipd_authoring`, `work_cmd`, `hooks/executed_transition_gate`, `research_index`); this plan consumes the canonical reader instead of adding to that list.
- GUIDING_PRINCIPLES P16 ("Test outcomes and behavior, never code structure or text") governs this fixture class. Its "one narrow exception" is that "Content verification is permissible only where the text or file itself is the artifact under test", which is exactly this guard's warrant: the derived status of frozen plan text IS the artifact. This plan keeps the guard and narrows its key; it does not weaken it into a structural assertion.
- The baseline has NO generator script by deliberate choice. E-01 of plan `63h054` (`.aw/records/plans/executed/20260924-historder-01-63h054-...ipd.md`) instructs "Write a small script (untracked scratch is fine)" and warns "Do NOT hand-write or edit this file: it is a machine capture, and a hand-touched entry destroys the only evidence that the derivation is unchanged." E-01 here honors that by transforming keys mechanically and carrying values across verbatim, never by hand-authoring a status.
- THE FIXTURE'S VALUE DOMAIN INCLUDES JSON `null`, not only status strings. The same `63h054` E-01 specifies a "mapping of repo-relative path -> derived status (`null` for None)", because `ipd_lifecycle.derive_plan_status` returns `Optional[str]` and yields `None` for a plan whose history declares no status event. 33 of the 732 compared entries are `null` today. Any transform, comparison, or sort written over these values must be `None`-safe; a bare `sorted(values)` raises `TypeError` (F-13).
- `tests/support.py` defines `FIXTURES` as "Static, checked-in test fixtures (decoupled from the mutable live plans board)", but `test_history_order.py` builds its own path from a local `_repo_root()` helper and does not use it. This plan does not churn that; noted so a reviewer does not read the omission as an oversight.

## Findings

| Id | Severity | Finding | Consequence |
|---|---|---|---|
| F-1 | HIGH | The baseline keys repo-relative PATHS (777 keys, all at slash-depth 4) and `DerivationIsUnchangedTests` intersects them against a live glob of `executed/`, `superseded/`, `not-executed/`, then asserts `assertGreaterEqual(len(intersection), 700)`. Measured at `afb948ce`: live terminal population 882, baseline 777, intersection 732, margin 32. | Confirms the backlog premise exactly. Every terminal-plan move costs one key, so ~33 renames redden a test that has nothing to do with renaming. |
| F-2 | HIGH | `plans_refs._find_plan_by_id` resolves an id6 by `rglob("*.md")` over the WHOLE plans tree with NO disposition filter, and `plans_refs.apply_renames` moves the file in place via `artifact_core.git_mv`. Verified live: resolving `5xzld0` returns a path under `.aw/records/plans/executed/`. | A terminal plan is fully renameable today. The eroding operation is reachable, not hypothetical. |
| F-3 | HIGH | `aw archive plans` is a SECOND, far worse eroder that the backlog item does not mention: `plans_archive` shards terminal plans into `YYYYMM/` subdirectories inside each terminal dir (a DIR-ONLY move that keeps the filename and the `Id`), changing path depth. No live terminal plan is sharded yet (all 882 at depth 4; zero baseline keys deeper). Simulated at `afb948ce`: sharding every terminal plan drops the path-keyed intersection from 732 to **0**. CORRECTED AND STRENGTHENED AT REVIEW (F-16): this is not hypothetical and needs no full-tree sharding. `aw archive plans` has a bare-sweep mode with a 14-day default (`plans_archive.DEFAULT_SWEEP_AGE_DAYS = 14`), and `plans_archive.sweep_candidates` returns **614** plans today, all 614 inside the compared intersection. One argument-free `aw archive plans --apply` leaves the intersection at **118** against a floor of 700. | The first real `aw archive plans` run does not erode the floor, it annihilates it, and a single default-argument invocation is already enough. This raises the fix's urgency well above the backlog's "about 33 renames" framing and is the strongest argument for option (a). |
| F-4 | MEDIUM | 45 of the 777 baseline keys are `pending/` paths and are ALREADY uncomparable: the test globs only the three terminal buckets and re-filters with `_TERMINAL_DIRS`. The in-file comments record why (a pending plan's derived status legitimately changes on approval, which reddened this guard on main; backlog `shw0eh`, `kcahc0`, `u4k33q`, `iyca6n`). | Dropping them in E-01 loses no coverage and removes a standing trap. The terminal-only restriction must be PRESERVED, not relaxed, when re-keying. |
| F-5 | HIGH | A naive id6 re-key RESURRECTS those 45 dead `pending/` keys and breaks the suite. Measured: 38 of the 45 pending-era ids are now live in a TERMINAL directory, and for **all 38** the derived status has legitimately changed from the frozen pending-era value (e.g. `63h054` frozen `approved`, now `executed`). Keying by id6 removes the very path signal that was silently suppressing them. | This is the one real hazard in the change and the reason E-01 says to re-key only the CURRENT intersection. An executor who instead re-keys all 777 keys ships 38 false mismatches. |
| F-6 | MEDIUM | `filename_slot_id6` is the WRONG resolver for this task: it returns `None` for **95 of the 732 keys E-01 must carry** (102 of the full 777). CORRECTED MECHANISM (F-17): only **4** of those 102 genuinely fail to parse as clustered names; the other **98** parse fine (e.g. `20260101-instsafe-07-qrokie-...` and `20260704-guided-onboarding-00-ksvzgc-...` both yield a slot token) and are then rejected by the resolver's DELIBERATE all-letters guard `_HAS_DIGIT_RE`, which mirrors `check_engine._is_real_id6` so an ordinary slug word such as `assess` cannot be mistaken for an id6. By contrast `selectors.declared_id6` succeeds on **all 882** live terminal plans, with **zero** duplicate ids and **zero** slot/declared disagreements. | Read the id6 from the `- Id:` FRONT MATTER, never from the filename. The corrected mechanism makes this stronger, not weaker: the filename resolver is wrong by DESIGN for most canonical names too, not merely for a few legacy stragglers. A filename-derived key would also reintroduce the very name-coupling this plan removes. |
| F-7 | HIGH | The re-key is a PURE, LOSSLESS transformation at `afb948ce`. Prototyped: 732 path keys -> 732 id6 entries, no id6 collisions, no key lacking a declared id6, and re-running `derive_plan_status` over the live tree against the re-keyed fixture yields **0** mismatches. Independently, the current path-keyed test also yields 0 mismatches today (`6 passed`). Re-verified at review on the CURRENT head (`f5c6114b`, 291 commits after `afb948ce`): the same 777 / 882 / 732 / 0-mismatch figures still hold, and the value multiset is carried exactly. The compared 732 break down as 470 `executed`, 133 `draft`, 66 `to-review`, 33 `null`, 22 `approved`, 8 `reviewed` (the `null` third of that tail is F-13's subject). | The change preserves coverage exactly (732 before, 732 after) and is verifiable as green-to-green. No coverage is traded for durability. The premise is not stale: it was re-measured at review rather than trusted from authoring. |
| F-8 | MEDIUM | The failure message misdiagnoses. "Compared N paths; expected at least 700 paths in common" sits in a test named `test_whole_tree_derivation_is_unchanged` in a file about history-order derivation, so it points a reader at `derive_plan_status` rather than at the renames that actually caused it. | Fixing the key without fixing the message leaves the "reddens on an unrelated change and is then misdiagnosed" half of the bug alive. E-03 owns this. |
| F-9 | LOW | Plan `5xzld0` (`Status: executed`, Set `renamescan`) correctly excludes `.json` so a rename never rewrites this fixture: `_REFERENCE_TEXT_SUFFIXES = _TEXT_SUFFIXES + (".py",)` yields `.md`/`.txt`/`.py` only. Its F-6 records the reason; its Deferred section names the residue and assigns "Carrier: p0a5kr". | Confirms this plan is the assigned carrier, and confirms the exclusion must STAY. The fix must make the fixture rename-proof by KEY CHOICE, not by making it rewritable. |
| F-10 | LOW | The fixture is the repo's ONLY instance of this coupling class. Of five `tests/fixtures/**/*.json` files mentioning a plans path, `runner_shared_premove_fingerprints.json` is read by nothing (a retained historical capture), `run_summary/stranded-run-state.json` matches only in a `_README` note, and the two `awphysical` hits are synthetic sandbox destinations. | Scope is correctly one fixture and one test. No sibling fixture needs the same treatment, so this plan needs no follow-on. |
| F-11 | HIGH (added at review, PR-001) | A PURE fraction-of-baseline floor is VACUOUS against a shrinking fixture, and OQ-01 resolved to it while stating the opposite ("an id6-keyed intersection that silently fell to a handful of entries would make the guard vacuous while still passing, which is the failure mode the original 700 was defending against"). Measured arithmetic: a baseline truncated to 10 entries with all 10 found scores 100 percent and PASSES `found >= 0.95 * len(baseline)`; so does 1 entry of 1. The fraction's denominator is the fixture itself, so shrinking the fixture shrinks the bar in lockstep. | The resolution as written removes the exact protection its own rationale says must remain. E-03 now keeps an absolute `len(baseline) >= 700` as a NON-VACUITY floor beside the fraction. The absolute is legitimate here and was not before, because it bounds a frozen AUTHORED artifact rather than the live-tree intersection that rotted. |
| F-12 | MEDIUM (added at review, PR-002) | The 95-percent coverage floor is FAR LESS SENSITIVE than the assertion it replaces, in the one direction that still matters. Measured at the 732-entry re-keyed fixture: the coverage assertion first fires only when MORE THAN 36 baseline ids go missing from the live terminal tree. The old absolute 700 fired at 33 losses, so sensitivity to the genuine remaining cause (a plan deleted, or moved OUT of a terminal dir, or its `- Id:` changed) is slightly WORSE, not better. | Not a defect in the direction the plan fixes (renames and shards now cost ZERO, down from one each), and the tolerance is deliberate. Recorded so a reader does not believe the fraction strictly dominates the absolute, and so the 95 figure is a known, cited choice rather than an unexamined default. |
| F-13 | HIGH (added at review, PR-003) | 33 of the 732 values the re-key must carry are JSON `null`, not status strings (`derive_plan_status` returns `None` when a plan's history declares no status event; plan `63h054` E-01 specified "`null` for None"). E-01 said only "carry the EXISTING frozen value across unchanged" and its Expected outcome spoke of a value multiset without naming `null`, so an executor writing the natural `if value:` or `if not status: continue` transform silently drops 33 entries and converts 33 real comparisons into none. Independently measured: a naive `sorted(values)` comparison CRASHES with `TypeError: '<' not supported between instances of 'NoneType' and 'str'`, so V-01's own evidence command needs a `None`-safe sort key. | Would reduce coverage from 732 to 699 while every stated check still passed, since 699 id-shaped keys with an equal value multiset satisfies every literal condition E-01 listed except the count. E-01 now names `null` explicitly and V-01 requires the `None`-safe comparison. |
| F-14 | MEDIUM (added at review, PR-004) | Keying by id6 introduces a failure mode path-keying was structurally immune to: a path is unique by construction, an id6 is unique only by CONVENTION. Two terminal plans declaring the same `- Id:` make a dict build silently keep the last one visited and drop the other from comparison; a terminal plan declaring no `- Id:` yields `None` and collapses every such plan onto one key. Measured clean today (882 terminal plans, 882 declared ids, 0 collisions, 0 missing), and `check.id6-collision` polices it repo-wide, but the guard must not depend on that check having been run. | Silent coverage loss is precisely the defect class this plan exists to end, so re-keying must not open a new instance of it. E-02 now collects duplicates and `None`-id files and asserts both empty, naming the offending paths. |
| F-15 | MEDIUM (added at review, PR-005) | E-04's mandate to "extract whatever logic both this test and `test_whole_tree_derivation_is_unchanged` need into a module-level helper" was under-specified in a way that defeats its own purpose: the whole-tree guard resolves its root from `_repo_root()`, while the new test needs a TEMPORARY root, so a helper that hard-codes the root or performs its own assertions cannot be driven by both and the "cannot drift apart" guarantee would be false. E-04 also did not say that the discriminating negative must be produced by editing plan HISTORY rather than the baseline value, and a baseline edit would prove only that two unequal strings compare unequal. | A shared helper that only one caller can actually use is not shared. E-04 now specifies a root-parameterized, assertion-free helper returning data, mandates a history-edit negative, and names two perturbations measured to flip the derived status (`draft` on a later-dated record; `approved` after deleting the `executed` record). |
| F-16 | MEDIUM (added at review, PR-006) | F-3's central claim is measured TRUE but materially UNDERSTATED, and the understatement is in the plan's own favor. F-3 says "No live terminal plan is sharded yet" and describes the annihilation as hypothetical ("Simulated ... sharding every terminal plan drops the intersection from 732 to 0"). But `aw archive plans` has a BARE SWEEP mode whose default age is 14 days (`plans_archive.DEFAULT_SWEEP_AGE_DAYS = 14`), and `plans_archive.sweep_candidates` returns 614 plans TODAY. Of those, 614 are inside the 732-key compared intersection, so a single `aw archive plans --apply` with no arguments leaves the path-keyed intersection at 118, against the floor of 700. | Strengthens rather than weakens the plan, and matters for how a reviewer weighs its `- Priority: low`. The breaking operation is a single argument-free command whose candidate set is already 614 strong, not a full-tree sharding an operator would have to go out of their way to perform. Recorded in F-3 rather than left as an exercise. |
| F-17 | LOW (added at review, PR-007) | F-6's count is right in total but its arithmetic is misattributed, which misdirects a reader about WHY the wrong resolver fails. F-6 says `filename_slot_id6` "fails on 102 of the 777 baseline keys, whose legacy names carry no id6 identity slot". Measured: of those 102, only **4** genuinely fail to parse as clustered names; the other **98** parse fine and are rejected by `selectors.filename_slot_id6`'s deliberate all-letters guard (`_HAS_DIGIT_RE`, which mirrors `check_engine._is_real_id6` so an ordinary slug word like `assess` is not mistaken for an id6). Restricted to the 732 keys E-01 actually carries, the failure count is **95**, not 102. | The conclusion ("read the id6 from the `- Id:` front matter, never from the filename") is correct and unchanged, and the corrected figure makes it STRONGER: the resolver is wrong for a designed reason that applies to most canonical names too, not merely for a handful of legacy stragglers. F-6 and E-01 now carry the 95 figure and the real mechanism. |

## Proposed changes (ordered, validatable)

1. Re-key `tests/fixtures/derive_plan_status_baseline.json` from path to id6 by carrying the 732 currently-compared frozen values across unchanged INCLUDING the 33 `null` values, dropping the 45 uncomparable `pending/` keys and resurrecting none of them (E-01; F-1, F-4, F-5, F-6, F-7, F-13, F-17).
2. Re-key the reader in `DerivationIsUnchangedTests` to intersect on id6, reading each plan once, reporting mismatches with id6 plus current path, and failing loudly on a duplicate or absent declared id6 (E-02; F-2, F-3, F-14).
3. Replace the single absolute 700 floor with TWO assertions: a 95-percent-of-baseline coverage floor whose message names missing ids as the cause and re-keying as the remedy, and a retained `len(baseline) >= 700` non-vacuity floor on the fixture's own size (E-03; F-8, F-11, F-12).
4. Add a constructed regression test that renames and shards plan files without touching `- Id:` and proves the comparison is unmoved, plus a discriminating negative produced by a plan-history edit proving a real derivation change is still caught; share one root-parameterized, assertion-free helper between it and the whole-tree guard (E-04; F-3, F-15, F-16).

## Deferred / out of scope (with reason)

- Adding a committed generator/regeneration script for the baseline. Plan `63h054` deliberately chose an untracked scratch capture and there is no `scripts/` dir or `make` target; introducing a supported regeneration path is a separate design decision with its own review, and `AW_CONFORMANCE_UPDATE_GOLDENS` is cited in records but exists in NO `.py` file, so there is no live precedent to copy. This plan's E-01 is a one-time transformation, not a tool.
  - Carrier-Declined: No obligation is created. Once the baseline is keyed by id6 it is invariant to the moves that would have forced a regeneration (F-3, F-7), so the need a generator would serve is removed by this plan rather than postponed. Anyone wanting one is proposing new tooling, not discharging a debt this plan leaves.
- Re-keying any other fixture. Per F-10 this is the only member of the class.
  - Carrier-Declined: Nothing to carry. F-10 establishes by inspection that the other four `tests/fixtures/**/*.json` files mentioning a plans path are either read by no test, matched only in prose, or synthetic, so there is no second instance for a carrier to own.
- Changing `il.derive_plan_status` or any lifecycle code. The defect is entirely in the fixture's key choice and the test's assertion; `derive_plan_status` takes text only and has zero path coupling.
  - Carrier-Declined: Not an omission. `derive_plan_status(text: str)` has no path parameter anywhere in its chain, so there is no coupling in it to fix; changing it would be an unrelated behavior change and would invalidate the very baseline this plan preserves.
- Backfilling the ~150 live terminal plans absent from the baseline. Growing coverage is a different goal from making existing coverage durable, and a fresh capture cannot be distinguished from a re-baseline of a regression.
  - Carrier-Declined: Deliberately not pursued rather than deferred. A fresh capture records whatever the derivation does TODAY, so if a regression already shipped it would be frozen in as the new truth, which is the one thing an anti-regression baseline must never do. Coverage of 732 plans is preserved exactly (F-7); no gap is left behind.
- Migrating `test_history_order.py` onto `tests/support.FIXTURES`. Unrelated tidying; see Step 0.
  - Carrier-Declined: Cosmetic, with no defect behind it. The test resolves its own fixture path correctly today; the constant would shorten two lines and change no behavior, so there is nothing for a carrier to track.

## Scope check

- Over-scope: none. Both declared paths are edited; no production module, no other test, and no spec is touched.
- Under-scope: none. The two declared paths are together sufficient: the fixture holds the key, the test holds both the reader and the assertions, and F-10 establishes no sibling fixture shares the coupling. Re-checked at review: `grep` finds `derive_plan_status_baseline` referenced from exactly one `.py` file (`tests/test_history_order.py`, two occurrences: the module docstring and the path expression) and from no Makefile, `pyproject.toml`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/`, or spec, so no second consumer of the path keys exists to update.

## Required tests / validation

- `python3 -m pytest tests/test_history_order.py` must pass, with the new E-04 test present and the pre-existing five fixture tests still green.
- A full bare `python3 -m pytest` must pass, to prove nothing else consumed the fixture's path keys. BASELINE MEASURED AT REVIEW on the current head `f5c6114b`: `3246 passed, 2 skipped, 3 warnings in 57.42s`, with 207 deselected as `slow`/`livecorpus`. The bar is therefore zero failures, not a failing-set delta; a single failure is a real regression and must not be pasted through as pre-existing.
- Structural proof of E-01 read directly off the fixture: entry count 732, every key matching `^[0-9a-z]{6}$`, and the sorted multiset of values identical before and after the re-key, compared with a `None`-safe sort key so the 33 `null` values do not crash the comparison (F-13).
- Negative/discriminating proof (E-04): renaming and sharding plan files leaves the comparison unmoved, while a genuine derived-status change, produced by editing plan HISTORY and not the baseline, is still reported as a mismatch. Without the negative, a test that trivially compares nothing would also pass.
- Non-vacuity proof of E-03's second assertion (F-11): a temporarily TRUNCATED fixture (for example 10 entries, all of which resolve to live plans, so coverage is 100 percent) must FAIL the size floor. A fraction-only implementation passes that case, so this is the evidence that distinguishes the two.

## Spec / documentation sync

N/A. No `.spec.md` governs this fixture's key choice, no user-facing doc or README documents the baseline (grep finds it in no Makefile, `pyproject.toml`, `CONTRIBUTING.md`, `docs/`, or `CHANGELOG.md`), and the change is invisible outside the self-test suite. Accordingly no spec path is declared in `- Scope-Paths:`. The rationale for keying by id6 is recorded in this plan and in backlog `p0a5kr`.

## Open questions

### OQ-01: Should the coverage floor be a fraction of the baseline or dropped entirely?

- Blocking: no
- Status: resolved
- Owner: agent aw oc run
- Resolution or deferral rationale: Resolved as BOTH, corrected at review (F-11). The authored resolution chose a fraction alone and justified it with a requirement a fraction cannot meet: it correctly said "an id6-keyed intersection that silently fell to a handful of entries would make the guard vacuous while still passing", but a pure `found >= 0.95 * len(baseline)` is itself vacuous against a shrinking fixture, because the fixture is the denominator. Measured: a baseline truncated to 10 entries with all 10 found scores 100 percent and passes; so does 1 of 1. So E-03 now carries TWO floors that guard different failures. The FRACTION (`found >= 0.95 * len(baseline)`) catches baseline ids that have gone missing from the live tree and cannot be tripped by a rename or a shard, since neither changes `- Id:`. The ABSOLUTE (`len(baseline) >= 700`) catches a truncated or under-regenerated fixture. Keeping an absolute is not a relapse: the rotting property of the old 700 came from bounding the live-tree INTERSECTION, which every file move shrank, whereas this one bounds a frozen AUTHORED artifact whose count changes only when a human edits it. The backlog names (b) as acceptable and this uses it for the coverage half, keeping (a), its stated preference, for the key. The 95 figure's real sensitivity is recorded in F-12 rather than left implicit: it first fires when more than 36 baseline ids go missing.

### OQ-02: Re-key only the compared intersection, or all 777 baseline keys?

- Blocking: no
- Status: resolved
- Owner: agent aw oc run
- Resolution or deferral rationale: Resolved by measurement (F-5): re-keying all 777 resurrects 38 pending-era ids now living in terminal directories whose derived status has legitimately changed since capture (e.g. `63h054` frozen `approved`, now `executed`), producing 38 false mismatches. Re-keying the current 732-entry intersection preserves today's coverage exactly (F-7) and loses nothing real, since the 45 `pending/` keys were already uncomparable by construction (F-4).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the output of a command run against the REWRITTEN fixture that prints: total entry count; the count of keys matching `^[0-9a-z]{6}$`; whether any key contains `/`; the count of `null` values; and whether the sorted list of values equals the sorted list of the 732 values carried from the old file (compare against `git show HEAD:tests/fixtures/derive_plan_status_baseline.json`, do not trust a remembered number). Expected: 732 entries, 732 id-shaped keys, no key containing `/`, exactly 33 `null` values, value multisets EQUAL. SORT WITH A `None`-SAFE KEY (F-13): a bare `sorted(values)` raises `TypeError: '<' not supported between instances of 'NoneType' and 'str'` because of those 33 nulls, so use a key such as `lambda v: (v is None, v or "")` and paste the command you actually ran. Also paste proof that NO pending-era id from F-5 gained an entry at all: print the intersection of the 45 pending-era ids with the rewritten fixture's key set and show it is EMPTY (measured empty at review for the correct transform, which is a stronger and simpler check than comparing their values).
  - Observed evidence: PASS. 732 entries, 732 id-shaped keys, 0 with '/', exactly 33 nulls, sorted values equal old values, 0 pending-era keys.
    Ran validation script against rewritten fixture and HEAD:
    ```
    $ python3 -c '
    import json
    import re
    import subprocess
    from pathlib import Path

    root = Path(".")
    fixture_path = root / "tests/fixtures/derive_plan_status_baseline.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    # 1. Total entry count
    print("Total entry count:", len(new_data))

    # 2. Count of keys matching ^[0-9a-z]{6}$
    id_pattern = re.compile(r"^[0-9a-z]{6}$")
    matching_keys_count = sum(1 for k in new_data if id_pattern.match(k))
    print("Count of keys matching ^[0-9a-z]{6}$:", matching_keys_count)

    # 3. Whether any key contains /
    keys_with_slash = [k for k in new_data if "/" in k]
    print("Any key contains /:", bool(keys_with_slash))

    # 4. Count of null values
    null_count = sum(1 for v in new_data.values() if v is None)
    print("Count of null values:", null_count)

    # 5. Value multiset comparison against git show HEAD
    head_raw = subprocess.check_output(
        ["git", "show", "HEAD:tests/fixtures/derive_plan_status_baseline.json"],
        text=True,
    )
    head_data = json.loads(head_raw)

    _TERMINAL_DIRS = ("/executed/", "/superseded/", "/not-executed/")
    terminal_plan_paths = [
        p.relative_to(root).as_posix()
        for bucket in ("executed", "superseded", "not-executed")
        for p in sorted(root.glob(f".aw/records/plans/{bucket}/**/*.ipd.md"))
    ]
    old_intersection = sorted(
        p for p in set(terminal_plan_paths) & set(head_data.keys())
        if any(d in p for d in _TERMINAL_DIRS)
    )
    old_carried_values = [head_data[p] for p in old_intersection]
    new_values = list(new_data.values())

    none_safe_key = lambda v: (v is None, v or "")
    sorted_old = sorted(old_carried_values, key=none_safe_key)
    sorted_new = sorted(new_values, key=none_safe_key)
    print("Sorted old values == sorted new values:", sorted_old == sorted_new)

    # 6. Intersection of 45 pending-era ids with rewritten fixture key set
    pending_keys = set(head_data.keys()) - set(old_intersection)
    pending_ids = set()
    for p in pending_keys:
        m = re.search(r"-([0-9a-z]{6})-[^/]+\.ipd\.md$", p)
        if m:
            pending_ids.add(m.group(1))

    intersection_with_pending = pending_ids & set(new_data.keys())
    print("Count of pending-era ids in head fixture:", len(pending_ids))
    print("Intersection of 45 pending-era ids with new fixture:", sorted(intersection_with_pending))
    print("Is intersection with pending-era ids empty:", len(intersection_with_pending) == 0)
    '
    Total entry count: 732
    Count of keys matching ^[0-9a-z]{6}$: 732
    Any key contains /: False
    Count of null values: 33
    Sorted old values == sorted new values: True
    Count of pending-era ids in head fixture: 45
    Intersection of 45 pending-era ids with new fixture: []
    Is intersection with pending-era ids empty: True
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste the full output of `python3 -m pytest tests/test_history_order.py -o addopts=""` showing the suite green with the id6-keyed reader. Then paste evidence that the intersection is computed on ids and is 732 (the same number the path-keyed test compared at `afb948ce` and re-measured at review on `f5c6114b`, proving coverage was preserved and not silently reduced). Then TEMPORARILY perturb one terminal plan's `## Workflow history` so its derived status changes, re-run, and paste the failure line to prove the mismatch report actually names the id6, the current path, the expected status, and the derived status; restore the file and paste `git status --short` showing the perturbation reverted. USE A PERTURBATION MEASURED TO WORK (F-15): appending a later-dated `- YYYY-MM-DD draft (agent): ...` record flips the derived status to `draft`; deleting the `executed` record flips it to `approved`. Do NOT use the dated cross-reference note `AGENTS.md` sanctions, which was measured at review NOT to change the derived status on any of the 262 non-`executed` compared entries and would produce a green run mistaken for a broken guard. Finally, paste evidence for the F-14 guards: the count of distinct declared ids over the live terminal tree beside the file count (expected equal, 882 and 882 at review), and a demonstration that the new duplicate/absent-id assertion FAILS when fed a temporary tree containing two plans declaring the same `- Id:`.
  - Observed evidence: PASS. test_history_order.py 7 passed; intersection count is 732 on ids; p7dqwz perturbation produced expected failure naming id, path, expected status, and derived status; F-14 guards verified (equal file and id count 995, duplicate id assertion caught).
    1. Full output of pytest with `-o addopts=""`:
    ```
    $ python3 -m pytest tests/test_history_order.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1239507195
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 7 items

    tests/test_history_order.py .......                                      [100%]

    ============================== 7 passed in 1.66s ===============================
    ```
    2. Intersection computed on ids and equals 732:
    ```
    $ python3 -c '
    import json
    from pathlib import Path
    from tests.test_history_order import _compare_plan_derivations, _repo_root

    root = _repo_root()
    baseline_file = root / "tests/fixtures/derive_plan_status_baseline.json"
    with open(baseline_file, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    res = _compare_plan_derivations(root, baseline)
    print("Intersection computed on ids count:", len(res.found_ids))
    print("All found keys match ^[0-9a-z]{6}$:", all(len(k) == 6 for k in res.found_ids))
    print("Mismatches count:", len(res.mismatches))
    '
    Intersection computed on ids count: 732
    All found keys match ^[0-9a-z]{6}$: True
    Mismatches count: 0
    ```
    3. Perturbed terminal plan `p7dqwz` (`.aw/records/plans/executed/20260823-artifactenginefix-01-p7dqwz-corrective-parameterized-artifact-engine-stale-research-inde.ipd.md`) deleting executed line, flipping derived status to approved:
    ```
    $ python3 -m pytest tests/test_history_order.py::DerivationIsUnchangedTests::test_whole_tree_derivation_is_unchanged -o addopts=""
    =================================== FAILURES ===================================
    ______ DerivationIsUnchangedTests.test_whole_tree_derivation_is_unchanged ______
    ...
    E       AssertionError: Lists differ: ["p7dqwz (.aw/records/plans/executed/20260[134 chars]ed'"] != []
    E       First list contains 1 additional elements.
    E       First extra element 0:
    E       "p7dqwz (.aw/records/plans/executed/20260823-artifactenginefix-01-p7dqwz-corrective-parameterized-artifact-engine-stale-research-inde.ipd.md): expected 'executed', got 'approved'"
    E       : derive_plan_status changed on 1 plans:
    E       p7dqwz (.aw/records/plans/executed/20260823-artifactenginefix-01-p7dqwz-corrective-parameterized-artifact-engine-stale-research-inde.ipd.md): expected 'executed', got 'approved'
    ```
    Reverted and verified:
    ```
    $ git checkout -- .aw/records/plans/executed/20260823-artifactenginefix-01-p7dqwz-corrective-parameterized-artifact-engine-stale-research-inde.ipd.md && git status --short
     M tests/fixtures/derive_plan_status_baseline.json
     M tests/test_history_order.py
    ```
    4. F-14 guards (distinct ids vs file count and duplicate id demonstration):
    ```
    $ python3 -c '
    import tempfile, unittest
    from pathlib import Path
    from agent_workflows import selectors
    from tests.test_history_order import _compare_plan_derivations, _fixture_plan_text, _repo_root

    root = _repo_root()
    terminal_files = [p for bucket in ("executed", "superseded", "not-executed") for p in (root / ".aw/records/plans" / bucket).glob("**/*.ipd.md")]
    declared_ids = [selectors.read_front_matter_id(p.read_text(encoding="utf-8")) for p in terminal_files]
    distinct_ids = set(declared_ids)
    print("Terminal file count:", len(terminal_files))
    print("Distinct declared ids count:", len(distinct_ids))
    print("None declared ids count:", sum(1 for i in declared_ids if i is None))
    print("Equal file count and distinct id count:", len(terminal_files) == len(distinct_ids))

    with tempfile.TemporaryDirectory() as tmpdir:
        tmproot = Path(tmpdir)
        exec_dir = tmproot / ".aw/records/plans/executed"
        exec_dir.mkdir(parents=True, exist_ok=True)
        (exec_dir / "20260901-demo-01-dupl01-first.ipd.md").write_text(_fixture_plan_text("dupl01", "- 2026-09-01 draft (agent): ok", status="draft"), encoding="utf-8")
        (exec_dir / "20260901-demo-02-dupl01-second.ipd.md").write_text(_fixture_plan_text("dupl01", "- 2026-09-01 draft (agent): ok", status="draft"), encoding="utf-8")
        res = _compare_plan_derivations(tmproot, {"dupl01": "draft"})
        tc = unittest.TestCase()
        try:
            tc.assertEqual(res.duplicate_ids, {}, f"Duplicate declared id6 found in live terminal plans: {res.duplicate_ids}")
        except AssertionError as e:
            print("AssertionError caught as expected:")
            print(e)
    '
    Terminal file count: 995
    Distinct declared ids count: 995
    None declared ids count: 0
    Equal file count and distinct id count: True
    AssertionError caught as expected:
    {'dupl01': ['.aw/records/plans/executed/20[100 chars]md']} != {}
    + {}
    - {'dupl01': ['.aw/records/plans/executed/20260901-demo-01-dupl01-first.ipd.md',
    -             '.aw/records/plans/executed/20260901-demo-02-dupl01-second.ipd.md']} : Duplicate declared id6 found in live terminal plans: {'dupl01': ['.aw/records/plans/executed/20260901-demo-01-dupl01-first.ipd.md', '.aw/records/plans/executed/20260901-demo-02-dupl01-second.ipd.md']}
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste the source of BOTH new assertions (the fraction expression with its message, and the `len(baseline) >= 700` non-vacuity floor with its message). Then paste the output of a command that computes the coverage ratio over the live tree and shows it clears the 95-percent threshold, printing `found`, `len(baseline)`, and the computed threshold as numbers.
    THEN THE TWO DISCRIMINATING NEGATIVES, both of which must FIRE. (a) COVERAGE: with a temporary copy of the fixture carrying enough extra ids that exist in no live plan, show the failure text naming MISSING IDS and re-keying, and show it does NOT claim `derive_plan_status` regressed. ADD AT LEAST 39 PHANTOM IDS, not "a few": measured at review against the 732-entry re-keyed fixture, 3, 10 and even 38 phantom ids all leave the assertion PASSING (`732 >= 0.95 * 770` is true), and 39 is the smallest count that fires. A paste showing a green run after adding three phantom ids is evidence of nothing and must not be offered as a negative. (b) NON-VACUITY: truncate a temporary copy of the fixture to 10 entries that ALL resolve to live plans, so coverage is 100 percent, and show the run still FAILS on the size floor. This is the assertion F-11 exists for, and a fraction-only implementation passes it.
    Finally, state explicitly that no absolute `700` remains as a bound on the live-tree INTERSECTION (paste a search showing the only surviving `700` is the fixture-size floor, and quote its line so a reader can see which quantity it bounds).
  - Observed evidence: PASS. Both new assertions in place; coverage ratio 100.0% (732/732 >= 695.4); both discriminating negatives fired (39 phantom ids failed coverage, 10 entries failed size floor); sole surviving 700 bounds fixture size.
    1. Source of both new assertions in `tests/test_history_order.py`:
    ```python
        # The size floor is deliberately absolute and is NOT the rotting kind:
        # it bounds the fixture itself, a frozen authored artifact whose entry
        # count changes only when someone edits it, ensuring the coverage
        # fraction cannot become vacuous if the fixture is truncated or emptied.
        self.assertGreaterEqual(
            len(baseline),
            700,
            f"Baseline fixture shrank to {len(baseline)} entries; expected at least 700. "
            "The fixture itself shrank and must be re-keyed from the committed file rather than re-captured.",
        )
    ...
        coverage_threshold = 0.95 * len(baseline)
        missing_count = len(baseline) - len(result.found_ids)
        self.assertGreaterEqual(
            len(result.found_ids),
            coverage_threshold,
            f"Coverage below threshold: found {len(result.found_ids)} of {len(baseline)} "
            f"baseline entries ({missing_count} missing, required >= {coverage_threshold:.1f}). "
            "Baseline ids are missing from the live terminal tree (a plan was deleted, moved "
            "out of a terminal directory, or had its - Id: changed), NOT that derive_plan_status "
            "regressed. A legitimate mass change requires re-keying the fixture.",
        )
    ```
    2. Coverage ratio over live tree:
    ```
    $ python3 -c '
    import json
    from tests.test_history_order import _compare_plan_derivations, _repo_root
    root = _repo_root()
    baseline = json.load(open(root / "tests/fixtures/derive_plan_status_baseline.json", encoding="utf-8"))
    res = _compare_plan_derivations(root, baseline)
    found = len(res.found_ids)
    baseline_len = len(baseline)
    threshold = 0.95 * baseline_len
    ratio = found / baseline_len
    print(f"found: {found}")
    print(f"len(baseline): {baseline_len}")
    print(f"threshold (0.95 * len(baseline)): {threshold:.1f}")
    print(f"coverage ratio: {ratio:.4f} ({ratio * 100:.2f}%)")
    print(f"clears 95% threshold: {found >= threshold}")
    '
    found: 732
    len(baseline): 732
    threshold (0.95 * len(baseline)): 695.4
    coverage ratio: 1.0000 (100.00%)
    clears 95% threshold: True
    ```
    3. The two discriminating negatives:
    (a) COVERAGE: 39 phantom IDs added to fixture:
    ```
    AssertionError: 732 not greater than or equal to 732.4499999999999 : Coverage below threshold: found 732 of 771 baseline entries (39 missing, required >= 732.4). Baseline ids are missing from the live terminal tree (a plan was deleted, moved out of a terminal directory, or had its - Id: changed), NOT that derive_plan_status regressed. A legitimate mass change requires re-keying the fixture.
    ```
    (b) NON-VACUITY: Truncated fixture with 10 entries (all live plans):
    ```
    AssertionError: 10 not greater than or equal to 700 : Baseline fixture shrank to 10 entries; expected at least 700. The fixture itself shrank and must be re-keyed from the committed file rather than re-captured.
    ```
    4. Surviving `700` search:
    ```
    $ grep -n "700" tests/test_history_order.py
    155:            700,
    156:            f"Baseline fixture shrank to {len(baseline)} entries; expected at least 700. "
    ```
    The only surviving `700` in `test_history_order.py` bounds `len(baseline)` (the fixture size). No absolute 700 remains as a bound on the live-tree intersection.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Paste the output of `python3 -m pytest tests/test_history_order.py -o addopts="" -v` listing the new test by name and passing. Paste the new test's body showing it renames EVERY plan file and moves one into a `YYYYMM/` shard without touching any `- Id:`, and that it asserts both the unmoved-comparison case and the discriminating negative (a real derivation change, produced by a history edit, IS reported). Paste the shared helper's signature showing it takes a repository root and a baseline mapping, returns data, and contains no `assert` (F-15), together with the two call sites proving the whole-tree guard and the new test both use it. Then prove the test is not vacuous by reintroducing path-keying in the helper, re-running, and pasting the FAILURE; restore and paste the green run again. Finally paste the tail of a bare full `python3 -m pytest` (the `N passed` summary line) proving the whole suite is green; the bar is zero failures against the review-measured baseline of `3246 passed, 2 skipped`.
  - Observed evidence: PASS. test_history_order.py 7 passed with new test; rename and sharding verified with discriminating negative; shared helper takes root and baseline with no asserts; path-keying reintroduction failed as expected; full suite 3994 passed.
    1. Output of `python3 -m pytest tests/test_history_order.py -o addopts="" -v`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=3236267261
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 7 items

    tests/test_history_order.py::DerivationIsUnchangedTests::test_whole_tree_derivation_is_unchanged PASSED [ 14%]
    tests/test_history_order.py::DerivationIsUnchangedTests::test_derivation_comparison_invariant_to_rename_and_sharding PASSED [ 28%]
    tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_b_oldest_first PASSED [ 42%]
    tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_c_mixed_blocks PASSED [ 57%]
    tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_a_newest_first PASSED [ 71%]
    tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_d_negative_cross_day_backwards PASSED [ 85%]
    tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_e_discriminating_single_date_tie PASSED [100%]

    ============================== 7 passed in 1.61s ===============================
    ```
    2. Body of new test `test_derivation_comparison_invariant_to_rename_and_sharding`:
    ```python
    def test_derivation_comparison_invariant_to_rename_and_sharding(self):
        """Prove id6-keyed comparison is invariant to file renaming and archive sharding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = Path(tmpdir)
            plans_dir = tmproot / ".aw" / "records" / "plans"
            exec_dir = plans_dir / "executed"
            super_dir = plans_dir / "superseded"
            notexec_dir = plans_dir / "not-executed"
            for d in (exec_dir, super_dir, notexec_dir):
                d.mkdir(parents=True, exist_ok=True)

            plan1_file = exec_dir / "20260901-demo-01-plan01-first-plan.ipd.md"
            plan1_history = (
                "- 2026-09-03 executed (agent): done\n"
                "- 2026-09-02 approved (agent): ok\n"
                "- 2026-09-01 draft (agent): ok"
            )
            plan1_file.write_text(
                _fixture_plan_text("plan01", plan1_history, status="executed"),
                encoding="utf-8",
            )

            plan2_file = super_dir / "20260901-demo-02-plan02-second-plan.ipd.md"
            plan2_history = (
                "- 2026-09-02 approved (agent): ok\n"
                "- 2026-09-01 draft (agent): ok"
            )
            plan2_file.write_text(
                _fixture_plan_text("plan02", plan2_history, status="approved"),
                encoding="utf-8",
            )

            plan3_file = notexec_dir / "20260901-demo-03-plan03-third-plan.ipd.md"
            plan3_history = "- 2026-09-01 draft (agent): ok"
            plan3_file.write_text(
                _fixture_plan_text("plan03", plan3_history, status="draft"),
                encoding="utf-8",
            )

            baseline = {
                "plan01": "executed",
                "plan02": "approved",
                "plan03": "draft",
            }

            # 1. Verify baseline matches before moves
            res0 = _compare_plan_derivations(tmproot, baseline)
            self.assertEqual(res0.found_ids, {"plan01", "plan02", "plan03"})
            self.assertEqual(res0.mismatches, [])

            # 2. Physically rename every plan file and move one into a YYYYMM/ shard
            shard_dir = exec_dir / "202609"
            shard_dir.mkdir(parents=True, exist_ok=True)
            new_plan1_file = shard_dir / "20260901-renamed-01-plan01-sharded.ipd.md"
            plan1_file.rename(new_plan1_file)

            new_plan2_file = super_dir / "20260901-renamed-02-plan02-renamed.ipd.md"
            plan2_file.rename(new_plan2_file)

            new_plan3_file = notexec_dir / "20260901-renamed-03-plan03-renamed.ipd.md"
            plan3_file.rename(new_plan3_file)

            # Assert comparison still finds every entry and reports zero mismatches
            res_after_moves = _compare_plan_derivations(tmproot, baseline)
            self.assertEqual(res_after_moves.found_ids, {"plan01", "plan02", "plan03"})
            self.assertEqual(res_after_moves.mismatches, [])
            self.assertEqual(res_after_moves.duplicate_ids, {})
            self.assertEqual(res_after_moves.missing_id_paths, [])

            # 3. Discriminating negative: mutate plan history so derived status genuinely changes
            mutated_history = (
                "- 2026-09-04 draft (agent): reopened\n"
                + plan1_history
            )
            new_plan1_file.write_text(
                _fixture_plan_text("plan01", mutated_history, status="draft"),
                encoding="utf-8",
            )

            res_negative = _compare_plan_derivations(tmproot, baseline)
            self.assertEqual(len(res_negative.mismatches), 1)
            self.assertIn("plan01", res_negative.mismatches[0])
            self.assertIn(
                "expected 'executed', got 'draft'", res_negative.mismatches[0]
            )
    ```
    3. Shared helper signature and call sites:
    Signature (contains no assertions and returns `DerivationComparisonResult` data):
    ```python
    def _compare_plan_derivations(
        root: Path, baseline: dict[str, str | None]
    ) -> DerivationComparisonResult:
    ```
    Call sites in `tests/test_history_order.py`:
    - Line 161 in `test_whole_tree_derivation_is_unchanged`: `result = _compare_plan_derivations(root, baseline)`
    - Lines 239, 258, 273 in `test_derivation_comparison_invariant_to_rename_and_sharding`: `res = _compare_plan_derivations(tmproot, baseline)`
    4. Non-vacuity proof by reintroducing path-keying in helper:
    ```
    AssertionError: Items in the second set but not the first:
    'plan01'
    'plan02'
    'plan03'
    FAILED tests/test_history_order.py::DerivationIsUnchangedTests::test_derivation_comparison_invariant_to_rename_and_sharding
    ```
    Restored and verified clean: 7 passed in 1.11s.
    5. Bare full `python3 -m pytest` tail:
    ```
    3994 passed, 2 skipped, 3 warnings in 305.61s (0:05:05)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` with no `- Readiness:` field, since readiness is an output of review and not of authoring. `/plan-review` has now run (see `## Workflow history` and the typed review record), so the field it wrote is the review's attestation; explicit human approval (`aw ipd set approved ... --by-human`) is still required before execution.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. Two test-only files change and no production module does. The frozen anti-regression fixture stops being keyed by repo-relative path and starts being keyed by plan `id6`, carrying the SAME 732 frozen values (including 33 `null`s) with none re-derived, so the 45 already-uncomparable `pending/`-era keys are dropped and none is resurrected. Its single reader intersects on id6 instead of path, reads each plan once, names the current path in any mismatch, and now fails loudly if a declared id6 is duplicated or absent. The one rotting assertion becomes two: a coverage fraction of the baseline, plus a RETAINED `len(baseline) >= 700` bounding the fixture's own size so the fraction cannot go vacuous. A new constructed test renames and shards plans without touching an `- Id:` and proves the comparison is unmoved, with a history-edit negative proving a real derivation change is still caught. Coverage is preserved exactly (732 before, 732 after, 0 mismatches, re-measured at review on `f5c6114b`). WHAT THE REVIEW CHANGED, because it affects what is being accepted: the authored plan's fraction-only floor was measurably vacuous against a shrinking fixture and its own OQ-01 rationale required otherwise (F-11), so the absolute floor is kept for that purpose; E-01 would have silently dropped 33 entries to a natural falsy-filter transform (F-13); and F-3's urgency was understated, since one argument-free `aw archive plans --apply` would take the path-keyed intersection from 732 to 118 today, not in some hypothetical future (F-16).

Execution contract: commit only the two paths in `- Scope-Paths:`, via `aw commit <plan> -- tests/fixtures/derive_plan_status_baseline.json tests/test_history_order.py`. Do not push. Paste actual runner output for every `V-*`; a remembered result is not evidence, and the full-suite bar is zero failures against the review-measured `3246 passed, 2 skipped` on `f5c6114b`. The fixture must be produced by mechanical transformation of the committed file, never hand-edited entry by entry (plan `63h054` E-01).

SCOPE FENCE, A DECLARATION FOR RECONCILIATION RATHER THAN A STOP DIRECTIVE. The intended surface is exactly the two declared paths: `tests/fixtures/derive_plan_status_baseline.json` (re-keyed) and `tests/test_history_order.py` (the reader, the two assertions, the shared helper, and one new test). Specifically DO NOT: change `ipd_lifecycle.derive_plan_status`, `derive_status_from_events`, or `_plan_status_events`, whose output this fixture is the frozen record OF, so an edit there invalidates the baseline it is being compared against; call `derive_plan_status` to GENERATE any fixture value, which re-baselines a live regression as the new truth; add `.json` to `artifact_core._REFERENCE_TEXT_SUFFIXES` or otherwise make the fixture rename-rewritable, since plan `5xzld0` F-6 excluded it deliberately and this plan achieves durability by KEY CHOICE instead; relax the terminal-bucket restriction in the reader (F-4 records the four backlog items that restriction closed); edit the five pre-existing `HistoryOrderFixtureTests` cases or `_fixture_plan_text`'s emitted shape beyond what E-04 needs to author temp plans; re-key or otherwise touch any other `tests/fixtures/**/*.json` (F-10 establishes there is no second instance); add a tenth duplicate `- Id:` regex instead of consuming `selectors.read_front_matter_id` / `selectors.declared_id6`; or write any assertion that reads production source with `inspect`, `ast`, regex or substring search (GUIDING_PRINCIPLES P16). An out-of-scope edit that proves NECESSARY is to be MADE and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

Post-gate lifecycle move: after every `E-*` is performed and every `V-*` verified with pasted evidence, `aw ipd lint --phase pre-transition` must report conforming. The terminal transition is then UNCONDITIONALLY owed, with a CONDITIONAL owner: in a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd finalize` itself. Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`. Backlog `p0a5kr` carries `- Blocks-Release: next`, inherited here; the gate is discharged when this plan reaches `executed`, not when it is approved.
