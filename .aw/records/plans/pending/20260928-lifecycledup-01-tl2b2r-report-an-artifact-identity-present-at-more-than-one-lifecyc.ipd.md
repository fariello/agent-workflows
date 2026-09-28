# IPD: Report an artifact identity present at more than one lifecycle location, in one shared predicate

- Date: 2026-09-28
- Kind: child
- Concern: Nothing in `aw check` asks whether ONE artifact identity occupies MORE THAN ONE lifecycle directory. The nearest rule, `check.id6-collision` (emitted by `check_engine.check_collisions`), keys on the DECLARED `- Id:` and therefore answers a different question: "is one id6 declared by two files". It catches the plans case INCIDENTALLY, only because both copies carry the same `- Id:`, and it is silent for every artifact that declares none. Measured in this tree 2026-09-28: 19 of 38 specs and 17 of 17 prompts declare no `- Id:`, so for those populations a duplicated lifecycle location is COMPLETELY INVISIBLE. Reproduced on a synthetic legacy-named plan pair (`pending/` + `executed/`): the default-scope sweep reported only `check.ipd-lint-diagnostic` and no duplicate finding of any kind. The structural symptom the backlog item asks to detect ("the same plan id6 or filename stem present in more than one lifecycle directory") therefore has no rule, and the one partial reading it does have is keyed on the wrong field and phrased as an identity-declaration conflict rather than as a lifecycle-placement violation, so its remedy text sends an operator to the wrong fix.
- Scope: Add ONE deterministic reader that answers "which artifact identities occupy more than one lifecycle location", register its rule, and wire it into the once-per-sweep cross-tree seam so `aw check` reports it. IN: the shared predicate, its rule-registry entry, the cross-tree wiring, the terminal-inclusive scope decision, and its regression tests. OUT: the runner-side integration refusal that consumes this predicate (Order 2 owns it, and it is a separate deliverable on a separate surface); any change to `check.id6-collision`'s own behavior, message or severity; the backlog-tree analogue (`5bmq5f`, already `done`); and any repair of an existing duplicate, because this tree has NONE (measured).
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: wlyg3g
- Blocks-Release: next
- Set: lifecycledup
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: tl2b2r

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wlyg3g`, which this plan graduates jointly with Order 2 (`46u3tu`). GATE NOTE: item `wlyg3g` carries `- Blocks-Release: next`, so this plan INHERITS it, per the every-live-bug-gates-the-release rule.
  THE ITEM'S CENTRAL MECHANISM CLAIM IS FALSE AS WRITTEN, AND THAT IS WHY THIS SET IS TWO PLANS RATHER THAN THE ITEM'S FOUR-POINT SKETCH. The item says "`git merge-tree` reports the merge as clean, because the two paths are different files and git has no concept of a lifecycle". MEASURED 2026-09-28 (F-01, F-02): for the EXACT shape the item describes, where the lane holds a `pending/` copy the base also had and main has since `git mv`-ed it to `executed/`, git DETECTS a rename/modify collision and CONFLICTS. `git merge-tree --write-tree main lane` exits 1 emitting three index stages, and the real `git merge --no-ff` exits 1 with `CONFLICT (content)`. Driven end-to-end through `oc_runipd.integrate_lane_branch`, that shape returns `integrated=False`, `kind='fail-merge'`, leaves ONE copy on main and does NOT regress the lifecycle. So the item's headline scenario is ALREADY REFUSED today, and a plan built on its stated premise would have added a gate for a condition git already catches.
  BUT THE DEFECT IS REAL IN A DIFFERENT AND STRICTLY WORSE SHAPE, WHICH THE ITEM DOES NOT NAME (F-03). When the plan is ABSENT AT THE MERGE BASE, the two copies are an ADD/ADD at different paths with no rename source to collide, and git merges CLEAN. Driven through the real runner: `integrated=True`, `kind='integrated'`, and main afterwards holds the plan at BOTH `pending/` (`- Status: to-review`) and `executed/` (`- Status: executed`). That is the silent lifecycle regression the item is about, reached by a path the item did not identify, and it is worse than the described one because no conflict, no prompt and no refusal occurs anywhere. It is also the COMMON shape for a lane that AUTHORS a plan, which is exactly what this very turn does.
  SO THE STRUCTURAL CHECK IS THE LOAD-BEARING FIX, NOT THE MERGE GATE, and the item's own fix-sketch ordering (check first) is correct for a reason it does not state: the merge gate can only refuse shapes it predicts, while the structural rule catches the condition HOWEVER it arises, including by hand-merge, by a botched `git mv`, or by the add/add path above. Order 1 therefore ships the reader and Order 2 consumes it; Order 2 depends on Order 1 because a refusal with its own private duplicated predicate is the two-readers drift this repository has already paid for.
  ITEM FIX-SKETCH POINT 3 IS DELIBERATELY NOT IN THIS SET, and F-09 records why: its consumer `ut0vzr` is ALREADY `executed`, so the per-lane REGRESSION/SAME/AHEAD verdict it asks for has no live caller, and the lane-state vocabulary it would duplicate already shipped as `runner_shared.classify_lane_integration`'s `LANE_SUPERSEDED`. Building it now would add a second lane classifier for a workflow that has run.

## Goal

Make "one artifact identity, two lifecycle locations" a condition `aw check` REPORTS, deterministically and for every record type, instead of a condition that is visible only when both copies happen to declare the same `- Id:`. The payoff is that the lifecycle regression backlog `wlyg3g` describes becomes detectable however it arose, which is the only reading that also covers a hand-merge, and that Order 2's integration refusal has one predicate to consume rather than its own copy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared predicate

- [ ] E-01 Add ONE pure reader to `agent_workflows/check_engine.py` that answers "which artifact identities occupy more than one lifecycle location", returning FACTS (a mapping of identity to the sorted list of paths holding it) and emitting no `Drift`, so both this plan's rule and Order 2's refusal consume the same function. Give it a name that says PLACEMENT rather than duplication, and make the return shape include, per identity, the lifecycle bucket of each path, because Order 2 needs the buckets to phrase its refusal and recomputing them there would be the second reader this item exists to avoid.
  KEY ON BOTH IDENTITY READINGS, NOT ONE, AND RECORD WHICH FIRED. The declared `- Id:` (via `check_engine._read_declared_id`) and the FILENAME STEM are different keys covering different populations, and the whole defect this plan fixes is that only the first is read today. The stem is what the item's own repro command uses (`for f in .aw/records/plans/*/*.ipd.md; do basename "$f"; done | sort | uniq -d`, item line 55) and it is the ONLY key that sees the no-declared-`Id:` population; MEASURED 2026-09-28 in this tree, that population is 19 of 38 specs and 17 of 17 prompts, versus 0 of 870 plans and 0 of 666 backlog items. So a declared-Id-only reader would be correct for plans today and silent for the majority of specs and for every prompt.
  DO NOT TRUST `artifact_naming.parse_clustered`'s `id6` GROUP AS AN IDENTITY. It accepts a LEGACY name and returns a garbage slot: `selectors.py` records that `parse_clustered("20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md")` parses conformant with `id6='assess'` while that record's real declared Id is `wvlk84`, and `artifact_core.ID6_RE` matches `assess`. Two guards already exist in-tree for exactly this and must be reused rather than re-invented: `check_engine._identity_slot_token`, which rejects an `HHMM` set segment, and `check_engine._is_real_id6`, which discriminates a slug word from an id6. Prefer the whole filename stem as the second key over the parsed slot, since the stem needs no discrimination at all.
  THE BUCKET MUST BE THE FIRST PATH COMPONENT UNDER THE TYPE ROOT, NOT THE PARENT DIRECTORY NAME. `aw archive plans` shards a disposition into `<disposition>/YYYYMM/`, so `executed/202609/x.ipd.md`'s parent is `202609` and reading the parent would classify a sharded plan as a bucket named after a month, making two shards of one disposition look like two lifecycle locations. `plans_index` already resolves disposition as the first component for this reason; take the same reading.
  IMPORT THE BUCKET ENUMERATION FROM `lifecycle_dirs.LIFECYCLE_SUBDIRS` RATHER THAN RE-LISTING IT. `check_engine` does NOT import `lifecycle_dirs` today and carries its own `_RETIRED_PATH_SEGMENTS` frozenset, but that set is a LIVENESS classifier (it answers "is this retired"), not the lifecycle enumeration, and keying placement off it would conflate the two questions. `lifecycle_dirs` is a declared LEAF MODULE that imports nothing from the package, so importing it introduces no cycle; verify that at execution and record the import direction.
  - Depends on: none
  - Expected outcome: a pure function exists, returns per-identity path lists with buckets, is keyed on both the declared `- Id:` and the filename stem with the firing key recorded, resolves a sharded path to its disposition rather than its month, returns empty for this repository, and emits no `Drift`; the `lifecycle_dirs` import direction is recorded as cycle-free with evidence.
  - Execution state: pending

- [ ] E-02 Register the rule id in `check_engine.RULE_REGISTRY` with an explicit severity, assurance, determinism and invariant, and wire the predicate into the ONCE-PER-SWEEP cross-tree seam in `check_engine.check_types` where `check_collisions` already rides, each cross-tree rule inside its own `try/except` so one failure cannot suppress another.
  REGISTRATION IS NOT BOOKKEEPING AND OMITTING IT IS A SILENT DEFECT. An id absent from `RULE_REGISTRY` falls to `_DEFAULT_RULESPEC`, which is `error` with an EMPTY invariant, so a missing entry makes the rule blocking by accident and drops its traceability with no diagnostic.
  CHOOSE `error` AND STATE WHY, BUT KNOW THAT `warning` IS NOT THE SOFTER OPTION IT LOOKS LIKE. `artifact_core.drift_exit_code` exempts ONLY `info`, so a `warning` fails the gate exactly as an `error` does; the honest choice is `error` (the condition is a real lifecycle contradiction and the item asks for it to be "DETECTED and refused") or `info` if it must not go red, and there is no middle. This tree currently has ZERO instances (MEASURED, F-05), so `error` reds nothing today. If `warning` is chosen anyway, note it interacts with `tests/test_work_gate_severity.py`, which enumerates every `warning`-severity registry entry and asserts none appears in a refusal output; that file is NOT in this plan's `Scope-Paths`, so choosing `warning` would require declaring it.
  DO NOT PUT `duplicate` IN THE RULE ID. A prohibition on that substring is live convention in this repository, recorded at `check_engine`'s own `check.graduated-to-repeated` entry (which explains why it is named `-repeated`); its enforcing test was deleted by commit `19313eed` and MUST NOT be cited as though it still ran. Prefer a placement-shaped id.
  CLAIM `invariant=""` WITH A WRITTEN REASON UNLESS YOU AMEND THE CATALOG. The invariant catalog in spec `pqsx96` has no invariant covering artifact PLACEMENT: `I-09` is filename-grammar conformance and `I-16` is setid semantics, and claiming either would file this rule under a contract it does not test. An empty invariant with a stated reason is established precedent (`check.scope-path-target-stale`, `check.priority-invalid`). Amending the catalog instead is legitimate but would put a `.spec.md` in `Scope-Paths`, which this plan deliberately does not do; if you amend, declare it, per AGENTS.md.
  - Depends on: E-01
  - Expected outcome: the id is registered with a deliberate severity, an assurance class, a determinism tag and either a real `I-*` or `""` plus a written reason; the id contains no `duplicate`; `aw check` reports the finding on a fixture holding two copies and stays silent on this repository; a raised predicate does not suppress a sibling cross-tree rule.
  - Execution state: pending

- [ ] E-03 Make the finding's `location`, `detail` and `recovery` name BOTH paths and BOTH statuses, and say which copy the lifecycle reading considers stale. The item's whole point is that this regression "would be recorded as a NORMAL commit by a legitimate verb" with "no fabricated evidence and no hook violation", so the message is the entire remedy surface and a finding that names one path leaves an operator to find the other by hand.
  THIS IS A MEASURED COMPLAINT ABOUT THE SIBLING DEFECT, NOT A STYLE PREFERENCE. Backlog `5bmq5f` (the backlog-tree analogue, now `done`) recorded that its diagnostic "names the same basename twice, so it reads as though a file duplicates itself" and that "reporting the two DIRECTORIES would make the fix obvious without a filesystem search". Do not reproduce that defect on the plans tree.
  SAY WHICH SIDE IS TERMINAL RATHER THAN WHICH IS NEWER, and do not order the two copies by mtime or by date-in-filename. `run_selection_policy.is_in_terminal_directory` already owns the terminal-directory reading, and `runner_shared`'s records-only re-derivation messages already phrase this exact stale-snapshot trap ("THE INCOMING BRANCH HOLDS A STALE LIFECYCLE SNAPSHOT ... TAKING ITS SIDE WOULD REVERT N real execution(s)"); reuse that framing so the two surfaces agree.
  - Depends on: E-02
  - Expected outcome: one finding names every path holding the identity, each path's bucket, each copy's `- Status:`, and which copy sits in a terminal directory; a test asserts the required substrings are present and that the message does not name one basename twice.
  - Execution state: pending

- [ ] E-04 Add the regression tests to `tests/test_check_engine.py` in that file's established shape, and make the LEGACY row load-bearing rather than decorative.
  THE TEST TABLE MUST CONTAIN AT LEAST FOUR ROWS AND EACH EXISTS FOR A STATED REASON: (a) MODERN names with the same declared `- Id:` in `pending/` and `executed/`, which must report the new rule; note this row ALSO reports `check.id6-collision` today (MEASURED), so the expected set must include both and the test must not assert the new rule is the only finding; (b) LEGACY names with NO declared `- Id:` in the same two directories, which is the row that FAILS TODAY and is the only proof the stem key does any work, since a declared-Id-only implementation passes (a) and fails (b); (c) a SHARDED path (`executed/202609/`) alongside `pending/`, which must still report exactly one finding and must NOT read the shard month as a bucket; (d) a CLEAN row, two genuinely different artifacts, which must report nothing, since every row above passes for a rule that fires unconditionally.
  FOLLOW THE FILE'S EXISTING DISCIPLINE, WHICH ITS HEADER STATES: assert rule ids as EXACT LITERAL STRINGS rather than as "a finding appeared", and write the expected set as the FULL SWEEP's so incidental findings a fixture legitimately trips are declared instead of masked. Reuse the `_plan_text`/`_tree`/`_rules`/`_counts` helpers; `_plan_text` deliberately emits a fully IPD-conformant body because `check.ipd-lint-diagnostic` runs the real linter, so a stub body adds an unrelated finding to every row.
  ASSERT THE SCOPE DECISION EXPLICITLY, because it is the one that can silently disable the whole rule. A default-scope sweep applies the retired filter, which hides the `executed/` half of the very pair being looked for; `check_collisions` hardcodes `include_retired=True` for its id6 pass for this reason. Add a row proving the rule fires under DEFAULT scope with one copy in a terminal directory, not only under `include_retired=True`.
  - Depends on: E-03
  - Expected outcome: all four rows pass, including the legacy row; a test demonstrates the legacy row FAILS against a declared-Id-only implementation (so the stem key is proven load-bearing rather than asserted); the default-scope row passes; bare `python3 -m pytest` is green with its summary line pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The rule registry IS the canonical rule list. `check_engine.RULE_REGISTRY` is the single source of `{severity, assurance, determinism, invariant}`; there is no docs table (`rg 'check\.setid-collision' docs/` returns nothing). An unregistered id silently becomes `error` with an empty invariant via `_DEFAULT_RULESPEC`.
- A `warning` FAILS the gate. `artifact_core.drift_exit_code` returns 1 for any finding whose severity is not `info`, so the only non-failing severity is `info`.
- Findings are `artifact_core.Drift`, a NamedTuple whose first three positional fields (`location`, `rule`, `detail`) are the load-bearing shape; the trailing six are stamped from the registry by `check_engine.enrich_drift`.
- Cross-tree rules ride a once-per-sweep seam in `check_engine.check_types`, each in its own `try/except`, so one raising rule cannot suppress another.
- `lifecycle_dirs` is a declared LEAF MODULE that imports nothing from `agent_workflows`, expressly so `layout`, `plans` and `attention_contract` can import it cycle-free. `LIFECYCLE_SUBDIRS['plans']` is `('pending', 'executed', 'superseded', 'not-executed', 'reusable')`.
- `check_engine` does NOT import `lifecycle_dirs` today; it carries its own `_RETIRED_PATH_SEGMENTS`, which is a liveness classifier and not the lifecycle enumeration.
- `artifact_naming` is the ONLY module that knows filename shape, and `parse_clustered` returns a garbage `id6` slot for a legacy name; `check_engine._identity_slot_token` and `_is_real_id6` are the in-tree guards.
- `check_engine._iter_plan_ipds` enumerates every `*.ipd.md` under the plans roots recursively and does NOT apply the retired filter, so it already sees every lifecycle directory; `_iter_type_files(..., include_retired=True)` is the per-type equivalent. Its `sorted(rglob(...))` is load-bearing against a measured CI flake in first-seen-wins passes.
- `check_engine._check_identity_slots`'s own docstring FORBIDS adding a declared-duplicate case there, because `check.id6-collision` already owns that fact and emitting both would give one problem two remedies.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The item's premise that git merges the described shape CLEAN is FALSE. For a lane holding a `pending/` copy that the base also had, against a main that `git mv`-ed it to `executed/`, `git merge-tree --write-tree main lane` exits 1 emitting three index stages and `CONFLICT (content)`; the real `git merge --no-ff` exits 1 the same way. | Driven 2026-09-28 in a throwaway repo reproducing the item's `d7qoxv` shape byte for byte. Also driven across eight variants (lane-touches-plan x main-diverges x `merge.renames=false`): every lane-touches-plan variant CONFLICTED. | The merge gate is NOT the load-bearing fix, and the plan must not be built on the item's stated mechanism. Recorded in the workflow history so a reviewer sees the correction. |
| F-02 | End-to-end through the REAL runner, that shape is already refused: `oc_runipd.integrate_lane_branch` returned `integrated=False`, `kind='fail-merge'`, cause token `git-merge-conflict`, shape `semantic`, leaving ONE copy on main at `- Status: executed`. | Driven 2026-09-28 against a real lane worktree built with `git worktree add` and a real `WorktreeHandle`. | Order 2 must not claim to fix this variant; it already refuses. Order 2's subject is the variant in F-03. |
| F-03 | The REAL defect is the ADD/ADD shape the item does not name: when the plan is ABSENT AT THE MERGE BASE, there is no rename source to collide, git merges CLEAN, and the runner returns `integrated=True`, `kind='integrated'`, leaving main holding the plan at BOTH `pending/` (`- Status: to-review`) and `executed/` (`- Status: executed`). | Driven 2026-09-28 through `oc_runipd.integrate_lane_branch`; the probe printed `*** DEFECT REPRODUCED: integration SUCCEEDED with the plan in TWO lifecycle dirs ***`. Confirmed for a `superseded/` terminal directory too. | This is the condition both orders target. It is strictly worse than the item's shape: no conflict, no prompt, no refusal. It is also the COMMON shape for a lane that AUTHORS a plan. |
| F-04 | `aw check` has NO rule keyed on artifact PLACEMENT. Of 50 registered rules, the only location-adjacent ids are `check.setid-collision`, `check.id6-collision` and `check.collisions-not-checked`, all keyed on DECLARED fields. | `[k for k in check_engine.RULE_REGISTRY if any(w in k for w in ('duplicate','collision','multip','locat','place'))]` driven 2026-09-28. | E-01/E-02 add the missing reading; the item's fix-sketch point 1 is correct. |
| F-05 | `check.id6-collision` catches the MODERN plans case INCIDENTALLY but is SILENT for an artifact declaring no `- Id:`. On a modern fixture the default sweep reported `check.id6-collision`; on a legacy fixture with no `- Id:` it reported only `check.ipd-lint-diagnostic` and no duplicate finding at all. | Both fixtures driven 2026-09-28 via `check_engine.check_collisions` and `check_types(root, ['all'])`. | E-01 must key on the filename stem as well, and E-04's legacy row is the only proof that key works. |
| F-06 | The no-declared-`Id:` population is real and concentrated outside plans: 19 of 38 specs and 17 of 17 prompts declare none; plans (0 of 870) and backlog (0 of 666) all do. | Driven 2026-09-28 over `check_engine._iter_type_files(root, t, include_retired=True)` with `_read_declared_id`. | The stem key is not hypothetical robustness; it is the only reading covering most specs and every prompt. |
| F-07 | This repository currently has ZERO duplicated artifact locations, so the defect is LATENT and an `error` severity reds nothing today. | `for f in .aw/records/plans/*/*.ipd.md .aw/records/plans/*/*/*.ipd.md; do basename "$f"; done \| sort \| uniq -d` returns empty; the per-name scan over all 870 plans reports no duplicate filenames. Matches the item's own measurement. | E-02 can choose `error` without breaking the tree, and no repair work is in scope. |
| F-08 | The item's claim that "`aw check`'s 3 duplicate findings are all set-id collisions" is STALE. The live sweep reports ZERO collision findings of any kind; its 3 default-scope findings are `check.ipd-uncarried-obligation`. | `check_engine.check_types(Path('.'), ['all'])` driven 2026-09-28, and again with `include_retired=True`. | Do not cite that number as a baseline. The re-scoping landed in commit `c6648722`. |
| F-09 | Item fix-sketch point 3 (a per-lane REGRESSION/SAME/AHEAD verdict for the lane-triage workflow) has NO live consumer: `ut0vzr` is `executed`, and no lane-triage workflow file exists under `.aw/system/workflows/`. The lane-state vocabulary it would duplicate already shipped as `runner_shared.classify_lane_integration`, whose `LANE_SUPERSEDED` state exists precisely to distinguish "plan reached a terminal directory by another route" from "work at risk". | `aw find plans ut0vzr` reports `executed`; `ls .aw/system/workflows/ \| grep -iE 'lane\|triage'` returns nothing. | Point 3 is deliberately out of scope for this Set, recorded here rather than silently dropped. |
| F-10 | `runner_shared` ALREADY imports `check_engine` (lazily, e.g. `from agent_workflows import check_engine as _ce`) and its own comments state the convention "NO NEW PATH LITERAL. Enumeration goes through `check_engine._iter_spec_records`". `check_engine` does not import `runner_shared`. | `rg` over both modules 2026-09-28. | A predicate in `check_engine` is consumable by Order 2 with no cycle and no new path literal, which is why the reader lives here and not in `runner_shared`. |
| F-11 | The suite baseline at authoring is `2937 passed, 2 skipped, 3 warnings in 45.62s` from a bare `python3 -m pytest` (201 deselected as `slow`/`livecorpus`). | Driven 2026-09-28 in this lane. | Both orders compare against this, and a bare run is required by AGENTS.md. |

## Proposed changes (ordered, validatable)

1. E-01 adds the shared placement reader to `check_engine`, keyed on both the declared `- Id:` and the filename stem, resolving each path to its lifecycle bucket via `lifecycle_dirs` and shard-safely.
2. E-02 registers the rule and wires the reader into the once-per-sweep cross-tree seam, with a deliberate severity and a stated invariant decision.
3. E-03 makes the finding name both paths, both buckets, both statuses and the terminal side.
4. E-04 adds the four-row regression table, including the legacy row that proves the stem key is load-bearing and the default-scope row that proves the retired filter does not hide the pair.

## Deferred / out of scope (with reason)

- The runner-side integration refusal: Order 2 (`46u3tu`) owns it. It is a different surface with a different test harness, and it consumes this plan's predicate.
  - Carrier: 46u3tu
- Item fix-sketch point 3, the lane-triage REGRESSION/SAME/AHEAD verdict: no live consumer, and it would fork a second lane classifier. See F-09.
  - Carrier-Declined: NOTHING IS OWED, because the consumer this work exists to serve has already run. `ut0vzr`, the lane-triage plan whose E-04 asked a human to make this judgement by hand, is `executed`, and no lane-triage workflow file exists under `.aw/system/workflows/` to call a computed verdict (F-09). The vocabulary it would produce also already shipped: `runner_shared.classify_lane_integration`'s `LANE_SUPERSEDED` exists precisely to distinguish "the plan reached a terminal directory by another route" from "work at risk". So filing a carrier would schedule a SECOND lane classifier for a workflow that has finished, which is the one-reader violation this repository has repeatedly paid for. If a future lane-triage pass needs the verdict, that is its own item with its own live consumer.
- The backlog-tree analogue (`5bmq5f`): already `done`, and `backlog.id-duplicate` plus `attention.duplicate-id` already cover that tree.
  - Carrier-Declined: Nothing is owed. The analogue item is `done`, and the backlog tree already has TWO readers for this condition (`backlog.id-duplicate` in `aw backlog check` and `attention.duplicate-id` in `aw attention`, the latter being what caught the real 36-item `graduated/`+`done/` population). A carrier would assert an uncovered gap on a tree that is in fact the better-covered one; the gap this plan fixes is on the OTHER trees.
- Any change to `check.id6-collision`: out of scope deliberately. Its docstring explains why it owns the declared-duplicate fact, and two rules reporting one problem with two remedies is the defect `_check_identity_slots` was written to avoid.
  - Carrier-Declined: This row is a PROHIBITION, not a deferred repair, so there is nothing to carry. `check_engine._check_identity_slots`'s own docstring forbids adding a declared-duplicate case on the stated ground that `check.id6-collision` already reports that fact and emitting both would hand an operator two findings and two remedies for one problem. Filing a carrier would schedule the undoing of a deliberate design decision.
- Repairing an existing duplicate: there are none (F-07).
  - Carrier-Declined: Nothing is owed because there is nothing to repair. MEASURED (F-07): zero duplicated artifact locations in this tree, matching the item's own measurement. A carrier here would name repair work with an empty subject; if the new rule ever fires, the finding itself is the record and the repair is that finding's own work.
- Amending the invariant catalog in spec `pqsx96`: not in `Scope-Paths`. E-02 takes the `invariant=""`-with-reason route instead; amending would require declaring the spec edit.
  - Carrier-Declined: No obligation survives this plan. `invariant=""` with a written reason is ESTABLISHED, endorsed precedent in the registry (`check.scope-path-target-stale`, `check.priority-invalid`), not a placeholder awaiting repair, so the rule is fully and correctly registered either way and no successor inherits a defect. The catalog amendment is a separate editorial decision about a spec this plan deliberately does not declare; filing a carrier would assert that the rule is under-registered, which the precedent contradicts.

## Scope check

- Over-scope: none. Both declared paths are edited by E-01 through E-04.
- Under-scope: none for this plan's stated goal. Two adjacent surfaces are consciously excluded and carried elsewhere: the runner refusal (Order 2) and the catalog amendment (not taken, with the reason above). If E-02 chooses `warning`, `tests/test_work_gate_severity.py` becomes an undeclared path and the executor must stop and re-declare rather than edit it.

## Required tests / validation

- `python3 -m pytest` bare, per AGENTS.md, with the actual summary line pasted. Do not pass `-n0`, an extra `-q`, or `-p no:randomly`.
- The four fixture rows of E-04, each asserted with exact literal rule ids against the FULL SWEEP's expected set.
- A falsification pass for the stem key: demonstrate the legacy row fails against a declared-Id-only implementation.
- `aw check` on this repository must report no new finding (F-07 predicts zero).
- `aw ipd lint --phase pre-transition` conforming before any terminal move.

## Spec / documentation sync

No spec amendment is taken. The invariant catalog in spec `pqsx96` has no placement invariant, and E-02 therefore registers `invariant=""` with a written reason, which is established precedent in the registry. Amending the catalog would be legitimate and arguably better, but it would put a `.spec.md` in `Scope-Paths` and make this a spec-amending plan; that is deliberately Order-independent future work and is recorded here rather than done silently. No `docs/` change is needed because the rule registry is the canonical rule list (F-04's method) and no docs table enumerates rule ids.

## Open questions

### OQ-01: Should the new rule's severity be `error` or `info`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to `error` from repository evidence. The item asks for the condition to be "DETECTED and refused rather than committed silently", and `error` is the only severity that both fails the gate and says the condition is a real violation. `warning` was considered and rejected as an illusory middle: `artifact_core.drift_exit_code` exempts only `info`, so `warning` fails the gate identically while additionally entangling `tests/test_work_gate_severity.py`, a file this plan does not declare. `info` was rejected because it would not refuse. The cost of `error` is zero today, since this tree has no instances (F-07). A maintainer may overrule at approval at the cost of one registry field.

### OQ-02: Should the predicate key on the declared `- Id:`, the filename stem, or both?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to BOTH, from measurement. Declared-`Id:`-only is silent for 19 of 38 specs and 17 of 17 prompts (F-06), which is most of two record types. Stem-only would miss a pair that was renamed between the two copies, which is exactly what `aw rename plans --to-id6` produces. Keying on both, and recording which key fired, costs one field in the return shape and is what makes E-04's legacy row pass. The item's own repro uses the stem, which is corroborating rather than decisive.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new function's signature and the driven output of calling it on (a) this repository, which must return an EMPTY result, and (b) a fixture holding one identity at two lifecycle locations, which must return that identity with both paths AND both buckets. Paste the driven output of calling it on a fixture whose terminal copy sits at `executed/202609/`, showing the bucket resolves to `executed` and NOT to `202609`. Paste a driven check that the function returns no `Drift` (e.g. the type of each returned value). Paste the evidence that importing `lifecycle_dirs` into `check_engine` introduces no cycle, as an actual import of `check_engine` succeeding plus the statement that `lifecycle_dirs` imports nothing from the package.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `RULE_REGISTRY` entry verbatim, showing severity, assurance, determinism and invariant, with the written reason if the invariant is `""`. Paste the driven output of `check_engine.check_types(fixture, ['all'])` reporting the new rule id, and of the same call on this repository showing the id ABSENT. Paste the rule id and confirm it contains no `duplicate` substring. Paste driven evidence that a raising predicate does not suppress a sibling cross-tree rule (e.g. patch the predicate to raise, then show `check.id6-collision` still reported).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste ONE finding's full `location`, `detail` and `recovery` text for a two-copy fixture, showing both paths, both buckets, both `- Status:` values and which side is terminal. Paste the assertion that the message does not name one basename twice (the `5bmq5f` defect), as the driven message text plus the check applied to it.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` summary line and compare it to the F-11 baseline `2937 passed, 2 skipped, 3 warnings in 45.62s`, accounting for every added test. Paste the four fixture rows' names and their exact asserted rule sets. Paste the FALSIFICATION result for the legacy row: the driven failure output of the legacy row against a declared-Id-only implementation (temporarily disable the stem key, show the row FAILS, restore it, show it passes). Paste the default-scope row's result proving the retired filter does not hide the terminal copy. Paste `aw check` on this repository showing no new finding.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is `to-review` and carries no `- Readiness:` field, because readiness is an output of `/plan-review` and writing one here would forge that attestation.

Execution contract. Commit ONLY the two declared `Scope-Paths` through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. If a change appears necessary outside those two paths, STOP and report rather than widening scope: the one foreseeable case is `tests/test_work_gate_severity.py`, reachable only by choosing `warning` against OQ-01's resolution. Do not modify the backlog item's requirements, and do not set its status; the runner sets `graduated` on verification.

This plan inherits `- Blocks-Release: next` from item `wlyg3g` and must not silently drop it.

Post-gate lifecycle. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted, concrete evidence. A bare claim that tests passed is not evidence; the actual `python3 -m pytest` summary line is. Order 2 (`46u3tu`) declares `- Item-Dependencies: executed:tl2b2r`, so finalizing this plan is what unblocks it.
