# IPD: Key the derive_plan_status baseline by plan id6 so a terminal-plan rename or archive shard cannot erode the floor

- Date: 2026-09-29
- Kind: child
- Concern: `tests/test_history_order.py::DerivationIsUnchangedTests` compares a frozen baseline keyed by repo-relative PATH against the live terminal-plan tree, so any operation that moves a terminal plan (`aw rename plans`, `aw group plans --rename`, `aw archive plans`) silently shrinks the compared set toward a hard `assertGreaterEqual(..., 700)` floor and reddens the suite with a message that names the wrong cause.
- Scope: Re-key the baseline fixture and its only reader from path to plan `id6`, the repo's stable cross-tree handle, and replace the frozen absolute floor with a coverage assertion that names the real cause when it fails. Pure re-key of already-frozen values; the `derive_plan_status` algorithm and every other test are untouched.
- Scope-Paths: tests/fixtures/derive_plan_status_baseline.json, tests/test_history_order.py
- Item-Dependencies: none
- Status: to-review
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

- 2026-09-29 draft (agent aw oc run): created.
- 2026-09-29 to-review (agent aw oc run): graduated backlog `p0a5kr`; premise re-measured at `afb948ce` and the fix direction chosen on measured evidence (see Findings).

## Goal

Make the `derive_plan_status` anti-regression guard invariant to where a terminal plan FILE lives, so that renaming or archiving a plan cannot erode it, and so that when it does fail it fails for the one reason it exists to catch: the derivation changed. Re-key the fixture from path to `id6` and make the coverage assertion self-diagnosing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-key the fixture

- [ ] E-01 Rewrite `tests/fixtures/derive_plan_status_baseline.json` as a mapping of plan `id6` -> frozen derived status, by PURE RE-KEY of the existing file rather than by fresh capture. For each of the current 777 path keys that (a) resolves to a live file under `executed/`, `superseded/`, or `not-executed/` and (b) is in the intersection the test compares today, read that file's text, take its declared id6 via `selectors.read_front_matter_id`, and carry the EXISTING frozen value across unchanged. Emit sorted-by-id6 JSON with a trailing newline. Do NOT call `derive_plan_status` to produce the values: re-deriving would silently re-baseline a real regression as the new truth, destroying the only evidence the guard holds. Drop the 45 `pending/` keys (all 45 are already uncomparable dead weight, see F-4) and do NOT resurrect them by id6 (see F-5, which is the trap in this task).
  - Depends on: none
  - Expected outcome: The fixture is a JSON object of exactly 732 entries; every key matches `^[0-9a-z]{6}$`; the multiset of VALUES is identical to the multiset of the 732 values carried over (so no status was invented, changed, or re-derived); no key is a path; no `pending/`-era entry survives.
  - Execution state: pending

### Task group 2: re-key the reader and fix the diagnosis

- [ ] E-02 In `tests/test_history_order.py::DerivationIsUnchangedTests.test_whole_tree_derivation_is_unchanged`, build the live side as an `id6 -> (repo-relative path, derived status)` map over the same three terminal buckets it globs today, reading each plan's text ONCE and taking both `selectors.read_front_matter_id(text)` and `il.derive_plan_status(text)` from that one string. Intersect on id6 instead of on path. Keep the existing terminal-bucket restriction (it is load-bearing, see F-4) and keep the `mismatches` comparison and its first-20 truncation. Report each mismatch as `<id6> (<current path>): expected <frozen>, got <derived>` so a failure still names a file a human can open even though the key no longer is one.
  - Depends on: E-01
  - Expected outcome: The test intersects on id6, performs exactly one read per terminal plan, and its mismatch lines carry id6, the plan's CURRENT path, the expected status, and the derived status.
  - Execution state: pending

- [ ] E-03 Replace the frozen `assertGreaterEqual(len(intersection), 700)` with a coverage assertion expressed as a FRACTION of the baseline actually carried: require that at least 95 percent of the fixture's entries are found in the live terminal tree. Write the failure message to name the real cause and the remedy, i.e. that baseline ids are missing from the live terminal tree (a plan was deleted, or moved out of a terminal directory, or had its `- Id:` changed), NOT that `derive_plan_status` regressed, and say that a legitimate mass change requires re-keying the fixture. A rename or an archive shard must not be able to trip this, because neither changes a plan's `- Id:`.
  - Depends on: E-02
  - Expected outcome: The floor is relative to `len(baseline)`, not an absolute; the message names missing ids and the real cause; the assertion is arithmetically unreachable by any number of renames or archive shards.
  - Execution state: pending

- [ ] E-04 Add a behavioral regression test in `tests/test_history_order.py` that proves the decoupling by CONSTRUCTION rather than by assertion about the live tree: build a temporary repo containing a handful of terminal plans plus an id6-keyed baseline, run the same intersect-and-compare logic, then physically rename every plan file (and additionally move one into a `YYYYMM/` shard subdirectory, the shape `aw archive plans` produces) WITHOUT touching any `- Id:`, and assert the comparison still finds every entry and still reports zero mismatches. Then, as the discriminating negative, mutate one plan's history so its derived status genuinely changes and assert the test's comparison DOES report that one plan as a mismatch. Extract whatever logic both this test and `test_whole_tree_derivation_is_unchanged` need into a module-level helper so the guard and its proof cannot drift apart.
  - Depends on: E-03
  - Expected outcome: A new test that fails if the path-coupling is ever reintroduced and that still catches a real derivation change; both the whole-tree guard and the new test call one shared helper.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The canonical id6 readers live in `agent_workflows/selectors.py`: `selectors.read_front_matter_id(text)` is the documented public text reader ("Return the `- Id:` id6 from a record's METADATA REGION, or ``None``", bounded to `metadata_region` so a QUOTED `- Id:` in a body is not read as a declaration), and `selectors.declared_id6(path)` is its whole-file twin. Both host runners re-export the former. Because `il.derive_plan_status` takes TEXT ONLY, a loop that already reads the text can take the id6 from the same string with no extra read; E-02 relies on this.
- Do NOT add a tenth duplicate `- Id:` regex. `selectors.declares_id6` documents the existing byte-identical twins (`plans_refs`, `plans_index`, `check_engine`, `artifact_rename`, `record_history`, `plans_archive`, `specs`, `releases`, `ipd_authoring`, `work_cmd`, `hooks/executed_transition_gate`, `research_index`); this plan consumes the canonical reader instead of adding to that list.
- GUIDING_PRINCIPLES P16 ("Test outcomes and behavior, never code structure or text") governs this fixture class. Its "one narrow exception" is that "Content verification is permissible only where the text or file itself is the artifact under test", which is exactly this guard's warrant: the derived status of frozen plan text IS the artifact. This plan keeps the guard and narrows its key; it does not weaken it into a structural assertion.
- The baseline has NO generator script by deliberate choice. E-01 of plan `63h054` (`.aw/records/plans/executed/20260924-historder-01-63h054-...ipd.md`) instructs "Write a small script (untracked scratch is fine)" and warns "Do NOT hand-write or edit this file: it is a machine capture, and a hand-touched entry destroys the only evidence that the derivation is unchanged." E-01 here honors that by transforming keys mechanically and carrying values across verbatim, never by hand-authoring a status.
- `tests/support.py` defines `FIXTURES` as "Static, checked-in test fixtures (decoupled from the mutable live plans board)", but `test_history_order.py` builds its own path from a local `_repo_root()` helper and does not use it. This plan does not churn that; noted so a reviewer does not read the omission as an oversight.

## Findings

| Id | Severity | Finding | Consequence |
|---|---|---|---|
| F-1 | HIGH | The baseline keys repo-relative PATHS (777 keys, all at slash-depth 4) and `DerivationIsUnchangedTests` intersects them against a live glob of `executed/`, `superseded/`, `not-executed/`, then asserts `assertGreaterEqual(len(intersection), 700)`. Measured at `afb948ce`: live terminal population 882, baseline 777, intersection 732, margin 32. | Confirms the backlog premise exactly. Every terminal-plan move costs one key, so ~33 renames redden a test that has nothing to do with renaming. |
| F-2 | HIGH | `plans_refs._find_plan_by_id` resolves an id6 by `rglob("*.md")` over the WHOLE plans tree with NO disposition filter, and `plans_refs.apply_renames` moves the file in place via `artifact_core.git_mv`. Verified live: resolving `5xzld0` returns a path under `.aw/records/plans/executed/`. | A terminal plan is fully renameable today. The eroding operation is reachable, not hypothetical. |
| F-3 | HIGH | `aw archive plans` is a SECOND, far worse eroder that the backlog item does not mention: `plans_archive` shards terminal plans into `YYYYMM/` subdirectories inside each terminal dir, changing path depth. No live terminal plan is sharded yet (all 882 at depth 4; zero baseline keys deeper). Simulated at `afb948ce`: sharding every terminal plan drops the path-keyed intersection from 732 to **0**. | The first real `aw archive plans` run does not erode the floor, it annihilates it. This raises the fix's urgency above the backlog's "about 33 renames" framing and is the strongest argument for option (a). |
| F-4 | MEDIUM | 45 of the 777 baseline keys are `pending/` paths and are ALREADY uncomparable: the test globs only the three terminal buckets and re-filters with `_TERMINAL_DIRS`. The in-file comments record why (a pending plan's derived status legitimately changes on approval, which reddened this guard on main; backlog `shw0eh`, `kcahc0`, `u4k33q`, `iyca6n`). | Dropping them in E-01 loses no coverage and removes a standing trap. The terminal-only restriction must be PRESERVED, not relaxed, when re-keying. |
| F-5 | HIGH | A naive id6 re-key RESURRECTS those 45 dead `pending/` keys and breaks the suite. Measured: 38 of the 45 pending-era ids are now live in a TERMINAL directory, and for **all 38** the derived status has legitimately changed from the frozen pending-era value (e.g. `63h054` frozen `approved`, now `executed`). Keying by id6 removes the very path signal that was silently suppressing them. | This is the one real hazard in the change and the reason E-01 says to re-key only the CURRENT intersection. An executor who instead re-keys all 777 keys ships 38 false mismatches. |
| F-6 | MEDIUM | `filename_slot_id6` is the WRONG resolver for this task: it fails on 102 of the 777 baseline keys, whose legacy names carry no id6 identity slot (e.g. `20260101-instsafe-07-qrokie-...`, `20260704-guided-onboarding-00-ksvzgc-...`). By contrast `declared_id6` succeeds on **all 882** live terminal plans, with **zero** duplicate ids and **zero** slot/declared disagreements. | Read the id6 from the `- Id:` FRONT MATTER, never from the filename. A filename-derived key would also reintroduce the very name-coupling this plan removes. |
| F-7 | HIGH | The re-key is a PURE, LOSSLESS transformation at `afb948ce`. Prototyped: 732 path keys -> 732 id6 entries, no id6 collisions, no key lacking a declared id6, and re-running `derive_plan_status` over the live tree against the re-keyed fixture yields **0** mismatches. Independently, the current path-keyed test also yields 0 mismatches today (`6 passed`). | The change preserves coverage exactly (732 before, 732 after) and is verifiable as green-to-green. No coverage is traded for durability. |
| F-8 | MEDIUM | The failure message misdiagnoses. "Compared N paths; expected at least 700 paths in common" sits in a test named `test_whole_tree_derivation_is_unchanged` in a file about history-order derivation, so it points a reader at `derive_plan_status` rather than at the renames that actually caused it. | Fixing the key without fixing the message leaves the "reddens on an unrelated change and is then misdiagnosed" half of the bug alive. E-03 owns this. |
| F-9 | LOW | Plan `5xzld0` (`Status: executed`, Set `renamescan`) correctly excludes `.json` so a rename never rewrites this fixture: `_REFERENCE_TEXT_SUFFIXES = _TEXT_SUFFIXES + (".py",)` yields `.md`/`.txt`/`.py` only. Its F-6 records the reason; its Deferred section names the residue and assigns "Carrier: p0a5kr". | Confirms this plan is the assigned carrier, and confirms the exclusion must STAY. The fix must make the fixture rename-proof by KEY CHOICE, not by making it rewritable. |
| F-10 | LOW | The fixture is the repo's ONLY instance of this coupling class. Of five `tests/fixtures/**/*.json` files mentioning a plans path, `runner_shared_premove_fingerprints.json` is read by nothing (a retained historical capture), `run_summary/stranded-run-state.json` matches only in a `_README` note, and the two `awphysical` hits are synthetic sandbox destinations. | Scope is correctly one fixture and one test. No sibling fixture needs the same treatment, so this plan needs no follow-on. |

## Proposed changes (ordered, validatable)

1. Re-key `tests/fixtures/derive_plan_status_baseline.json` from path to id6 by carrying the 732 currently-compared frozen values across unchanged, dropping the 45 uncomparable `pending/` keys and resurrecting none of them (E-01; F-1, F-4, F-5, F-6, F-7).
2. Re-key the reader in `DerivationIsUnchangedTests` to intersect on id6, reading each plan once and reporting mismatches with id6 plus current path (E-02; F-2, F-3).
3. Replace the absolute 700 floor with a 95-percent-of-baseline coverage assertion whose message names missing ids as the cause and re-keying as the remedy (E-03; F-8).
4. Add a constructed regression test that renames and shards plan files without touching `- Id:` and proves the comparison is unmoved, plus a discriminating negative proving a real derivation change is still caught; share one helper between it and the whole-tree guard (E-04; F-3).

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
- Under-scope: none. The two declared paths are together sufficient: the fixture holds the key, the test holds both the reader and the assertion, and F-10 establishes no sibling fixture shares the coupling.

## Required tests / validation

- `python3 -m pytest tests/test_history_order.py` must pass, with the new E-04 test present and the pre-existing five fixture tests still green.
- A full bare `python3 -m pytest` must pass, to prove nothing else consumed the fixture's path keys.
- Structural proof of E-01 read directly off the fixture: entry count 732, every key matching `^[0-9a-z]{6}$`, and the sorted multiset of values identical before and after the re-key.
- Negative/discriminating proof (E-04): renaming and sharding plan files leaves the comparison unmoved, while a genuine derived-status change is still reported as a mismatch. Without the negative, a test that trivially compares nothing would also pass.

## Spec / documentation sync

N/A. No `.spec.md` governs this fixture's key choice, no user-facing doc or README documents the baseline (grep finds it in no Makefile, `pyproject.toml`, `CONTRIBUTING.md`, `docs/`, or `CHANGELOG.md`), and the change is invisible outside the self-test suite. Accordingly no spec path is declared in `- Scope-Paths:`. The rationale for keying by id6 is recorded in this plan and in backlog `p0a5kr`.

## Open questions

### OQ-01: Should the coverage floor be a fraction of the baseline or dropped entirely?

- Blocking: no
- Status: resolved
- Owner: agent aw oc run
- Resolution or deferral rationale: Resolved from repository evidence in favor of a fraction (backlog option (b) applied to the floor, on top of option (a) for the key). Some floor must remain, because an id6-keyed intersection that silently fell to a handful of entries would make the guard vacuous while still passing, which is the failure mode the original 700 was defending against. An ABSOLUTE floor is what rots, so E-03 expresses it as 95 percent of `len(baseline)`, which cannot be tripped by a rename or a shard (neither changes `- Id:`) but still fires if plans are deleted or lose their ids. The backlog names (b) as an acceptable direction and this uses it only for the floor, keeping (a), its stated preference, for the key.

### OQ-02: Re-key only the compared intersection, or all 777 baseline keys?

- Blocking: no
- Status: resolved
- Owner: agent aw oc run
- Resolution or deferral rationale: Resolved by measurement (F-5): re-keying all 777 resurrects 38 pending-era ids now living in terminal directories whose derived status has legitimately changed since capture (e.g. `63h054` frozen `approved`, now `executed`), producing 38 false mismatches. Re-keying the current 732-entry intersection preserves today's coverage exactly (F-7) and loses nothing real, since the 45 `pending/` keys were already uncomparable by construction (F-4).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the output of a command run against the REWRITTEN fixture that prints: total entry count; the count of keys matching `^[0-9a-z]{6}$`; whether any key contains `/`; and whether the sorted list of values is byte-identical to the sorted list of the 732 values carried from the old file (compare against `git show HEAD:tests/fixtures/derive_plan_status_baseline.json`, do not trust a remembered number). Expected: 732 entries, 732 id-shaped keys, no key containing `/`, value multisets EQUAL. Also paste proof that none of the 38 pending-era resurrection ids named in F-5 gained an entry whose value disagrees with its current derivation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste the full output of `python3 -m pytest tests/test_history_order.py -o addopts=""` showing the suite green with the id6-keyed reader. Then paste evidence that the intersection is computed on ids and is 732 (the same number the path-keyed test compared at `afb948ce`, proving coverage was preserved and not silently reduced). Then TEMPORARILY perturb one terminal plan's `## Workflow history` so its derived status changes, re-run, and paste the failure line to prove the mismatch report actually names the id6, the current path, the expected status, and the derived status; restore the file and paste `git status --short` showing the perturbation reverted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste the new assertion's source (the fraction expression and its message). Then paste the output of a command that computes the coverage ratio over the live tree and shows it clears the 95-percent threshold. Then paste a demonstration that the message names the real cause: with a temporary copy of the fixture carrying a few extra ids that exist in no live plan, show the failure text naming MISSING IDS and re-keying, and show it does NOT claim `derive_plan_status` regressed. State explicitly that no absolute `700` remains in the file (paste a search proving it).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the output of `python3 -m pytest tests/test_history_order.py -o addopts="" -v` listing the new test by name and passing. Paste the new test's body showing it renames EVERY plan file and moves one into a `YYYYMM/` shard without touching any `- Id:`, and that it asserts both the unmoved-comparison case and the discriminating negative (a real derivation change IS reported). Then prove the test is not vacuous by reintroducing path-keying in the helper, re-running, and pasting the FAILURE; restore and paste the green run again. Finally paste the tail of a bare full `python3 -m pytest` (the `N passed` summary line) proving the whole suite is green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval (`aw ipd set approved ... --by-human`) before execution; no `- Readiness:` field is written here, since that is an output of review and not of authoring.

Execution contract: commit only the two paths in `- Scope-Paths:`, via `aw commit <plan> -- tests/fixtures/derive_plan_status_baseline.json tests/test_history_order.py`. Do not push. Paste actual runner output for every `V-*`; a remembered result is not evidence. The fixture must be produced by mechanical transformation of the committed file, never hand-edited entry by entry (plan `63h054` E-01).

Post-gate lifecycle move: after every `E-*` is performed and every `V-*` verified with pasted evidence, `aw ipd lint --phase pre-transition` must report conforming before the plan is transitioned to `.aw/records/plans/executed/` through the tooled lifecycle. Backlog `p0a5kr` carries `- Blocks-Release: next`, inherited here; the gate is discharged when this plan reaches `executed`, not when it is approved.
