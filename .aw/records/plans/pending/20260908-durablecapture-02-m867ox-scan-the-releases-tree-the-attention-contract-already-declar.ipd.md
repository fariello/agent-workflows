# IPD: Scan the releases tree the attention contract already declares tracked and guard the two lists against drifting again

- Date: 2026-09-08
- Kind: child
- Concern: `releases` is a DECLARED tracked tree with a full status map and a `TreePolicy`, and it is never scanned, so every release record is invisible to `aw attention` while the view reports `valid: true`. Two lists encode one fact and they have drifted. MEASURED AT HEAD `a2e0438a` by importing both modules: `attention_contract.TRACKED_TREES` is `('specs', 'plans', 'research', 'backlog', 'releases')`, and `artifact_core.SCAN_ROOTS` contains no releases path at all (it holds four root docs, three `.agents/` roots, and seven `.aw/records/` roots, none of them releases). Resolving each tracked tree against the scan roots: `specs`, `plans`, `research` and `backlog` each match at least one root; `releases` matches NONE.
  CONFIRMED EMPIRICALLY, and the numbers are worse than the item recorded because the corpus grew. `aw attention --format json` returns 848 items: plans 557, backlog 158, research 105, specs 28, and ZERO releases, with `valid: true` and zero violations, while `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` exists on disk. The item measured 749 items and the same zero.
  THE POLICY IS NOT THE GAP, WHICH NARROWS THE FIX. `releases` DOES have a `TreePolicy` (`.agents/releases`, `tracked=True`, `owner='aw releases'`, reason "release records (ship-gate anchors); tracked lifecycle planned/blocked/shipped"), and `attention._classify_tree('.aw/records/releases/x.release.md')` correctly returns that policy, and `attention_contract` carries the status map (`planned`->ready, `blocked`->blocked, `shipped`->done). So classification and mapping both work; the file is simply never handed to them, because `core.iter_scan_files` never yields it. The fix is one scan root plus a guard, not a new policy.
  WHY IT MATTERS MORE THAN A MISSING COUNT. Releases anchor the whole `Blocks-Release` mechanism, and `AGENTS.md` instructs agents to consume `aw attention` for the cross-tree view and states it "surfaces the outstanding release-blocker set for the active release". If the release records are invisible to that view, any conclusion an agent draws about release readiness from `aw attention` alone was drawn without them. Note `aw check releases` IS wired fail-closed in CI (`.github/workflows/tests.yml:157-159`), so release records are VALIDATED but not SURFACED, and that split is exactly what makes this easy to miss.
- Scope: Add the releases scan root(s) so the declared tracked tree is actually scanned, decide the `reviews` tree deliberately (a `TreePolicy` either tracked or explicitly excluded WITH a reason, matching how the other five exclusions are recorded), and add a consistency check asserting every `TRACKED_TREES` entry has at least one `SCAN_ROOTS` entry so this class of drift cannot recur silently. EXCLUDES retiring `TODO.md` (sibling backlog `ld08f1`, whose plan is authored alongside this one); excludes per-requirement spec tracking (`f1sw71`); excludes the durable-carrier predicate (pending plan `rnkqrc`, from `jys5dp`); excludes changing any release record or the `Blocks-Release` resolution logic.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/attention_contract.py, tests/test_artifact_core.py, tests/test_attention_contract.py
- Item-Dependencies: none
- Status: to-review
- Set: durablecapture
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m867ox
- From-Backlog: v7u6vm

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `v7u6vm`. The item carries no `- Blocks-Release:` so none is inherited or invented, though the defect is ABOUT the release-gating surface, which is worth noting rather than confusing with a gate.
  EVERY CLAIM RE-MEASURED at HEAD `a2e0438a` by importing the modules rather than reading them, and all three held: the two lists disagree exactly as described, `releases` matches no scan root, and `aw attention` returns zero releases with `valid: true`. Two numbers moved and one claim needed CORRECTING.
  THE CORRECTION MATTERS BECAUSE IT SHRINKS THE WORK. The item says releases "has a status->class map ... and is never scanned", which is right, but it does not say that `releases` ALREADY HAS a `TreePolicy` and that `_classify_tree` already resolves a `.aw/records/releases/` path to it. Measured both. So an executor must NOT add a policy (that would be a second, conflicting entry); the single missing piece is the scan root. Stated in E-01 so the cheap fix is not mistaken for an incomplete one.
  NUMBERS UPDATED: 848 attention items (plans 557, backlog 158, research 105, specs 28), not the item's 749; and the reviews tree now holds 82 records, which strengthens its point that an absent policy for a consequential tree should be a DECISION rather than an omission.
  THE `reviews` HALF IS A DECISION, NOT AN IMPLEMENTATION, and E-03 is written to force that honestly. The item observes that the five EXCLUDED trees each carry a recorded reason (measured: walkthroughs "narrative records; no lifecycle status in v1 (OQ8)", roadmaps "intent, not commitment", prompts and comms "deferred to Phase 3 (OQ3)", docs-prompts "the evergreen copy-paste prompt LIBRARY"), while `reviews` is simply absent. Given that `check.review-finding-unescalated` treats an unescalated review finding as an ERROR, that absence is consequential enough to deserve a reason either way. E-03 therefore requires a recorded decision and forbids silently tracking 82 records into the view without measuring what that does to it.
  SIBLING BOUNDARY, checked rather than assumed: pending plan `rnkqrc` (from `jys5dp`) names BOTH this item and `ld08f1` in its deferred section ("THE `releases` TREE having no scan root, and the `reviews` tree having no TreePolicy: both found while investigating, both their own items"), so there is no overlap and this work is unowned.

## Goal

Make the attention view actually cover the five trees it claims to cover, and make a sixth divergence fail a test instead of hiding behind `valid: true`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: scan the tree that is already declared and already classified

- [ ] E-01 ADD THE RELEASES SCAN ROOT(S) TO `SCAN_ROOTS`, and add nothing else. Locate `SCAN_ROOTS` by SYMBOL in `artifact_core.py`; the item cites `:158` for the `TODO.md` entry and line numbers move.
  DO NOT ADD A `TreePolicy` FOR RELEASES. One already exists and `_classify_tree` already resolves a `.aw/records/releases/` path to it (measured: returns the `.agents/releases` policy, `tracked=True`, `owner='aw releases'`). A second entry would be two policies for one tree, which is the duplication this repository's shared-authority discipline exists to prevent.
  ADD BOTH PATH GENERATIONS, matching how every other records-class tree is listed. `SCAN_ROOTS` carries `.agents/plans` AND `.aw/records/plans`, and `.agents/backlog` AND `.aw/records/backlog`, because the layout migrated. Decide whether `.agents/releases` belongs beside `.aw/records/releases` and say why; the `TreePolicy` root is the `.agents/` spelling, and `_classify_tree` rewrites `.aw/records/<type>` to `.agents/<type>` before matching, so both spellings resolve to the same policy.
  VERIFY THE RECORD ACTUALLY APPEARS, which is the item's own acceptance condition. Adding a root that `iter_scan_files` skips for an unrelated reason (an ignore rule, a name filter, a `is_nonartifact_name` match) would look like a fix and change nothing.
  - Depends on: none
  - Expected outcome: `releases` resolves to at least one scan root; the existing release record appears in `aw attention` output as `tree: releases`; no second `TreePolicy` was added; both path generations considered with the decision stated.
  - Execution state: pending

- [ ] E-02 CONFIRM THE STATUS MAPPING PRODUCES THE RIGHT CLASS for a real release record, rather than assuming the map is correct because it exists. `attention_contract` maps `planned`->ready, `blocked`->blocked, `shipped`->done. The one record on disk exercises exactly one of those three.
  CHECK ALL THREE VALUES, not just the one on disk. A map that has never run is not a map that works, and a release record is cheap to synthesize in a temporary repo. If a status value in the release-record contract has NO entry in the map, that is a finding to report, not a gap to paper over.
  DO NOT CHANGE THE MAP to make an output look tidier. If a mapping is wrong, report it: the map is a contract other surfaces read, and `aw check releases` is fail-closed in CI on the record shape.
  - Depends on: E-01
  - Expected outcome: each of the three release statuses maps to its declared attention class, demonstrated on synthesized records; any unmapped status value reported rather than silently added.
  - Execution state: pending

### Task group 2: decide reviews deliberately

- [ ] E-03 GIVE THE `reviews` TREE A RECORDED DECISION, either a `TreePolicy` with `tracked=True` or one with `tracked=False` AND a reason, in the same shape the five existing exclusions use. Measured, the tree holds 82 records and has NEITHER a policy nor a scan root, so it is the only consequential tree that is absent rather than decided.
  THE FIVE EXISTING EXCLUSIONS ARE THE TEMPLATE, and each carries a real reason: walkthroughs "narrative records; no lifecycle status in v1 (OQ8)", roadmaps "intent, not commitment; no lifecycle status in v1 (OQ8)", prompts and comms "deferred to Phase 3 (OQ3)", docs-prompts "the evergreen copy-paste prompt LIBRARY, not a lifecycle-tracked artifact tree". Match that standard: a reason that says only "not tracked" is not a reason.
  IF YOU CHOOSE TRACKED, MEASURE WHAT IT DOES TO THE VIEW BEFORE COMMITTING TO IT. 82 records entering an 848-item view is a 10 percent increase, and a review record's native status vocabulary must map onto the cross-tree classes or `aw attention` will report an invalid view. Do NOT track it without a status map, and do NOT invent a map without checking what a review record actually carries.
  THE ARGUMENT FOR DECIDING RATHER THAN DEFERRING, so the decision is made on the merits: `check.review-finding-unescalated` treats an unescalated review finding as an ERROR, so a review record carrying gating findings is consequential. That is an argument that its exclusion should be a DECISION with a reason; it is NOT by itself an argument that the tree must be tracked, since the finding is already policed by `aw check`. Either answer is defensible; silence is not.
  - Depends on: none
  - Expected outcome: a `TreePolicy` for reviews exists with an explicit `tracked` value and, if excluded, a reason meeting the standard of the existing five; if tracked, a status map and the measured effect on the view's item count and validity.
  - Execution state: pending

### Task group 3: make the drift impossible to repeat silently

- [ ] E-04 ADD THE CONSISTENCY CHECK the item asks for: assert that every tree in `TRACKED_TREES` has at least one corresponding entry in `SCAN_ROOTS`. This is the item's requirement 3 and it is what stops a sixth tree being declared and never scanned.
  ASSERT THE RELATIONSHIP, NOT A HARDCODED LIST. A test that pins the current five names passes forever and catches nothing; the point is that ADDING a tracked tree without a scan root must fail. Derive both sides from the modules at test time.
  CONSIDER THE REVERSE DIRECTION AND DECIDE IT EXPLICITLY. Several `SCAN_ROOTS` entries are deliberately NOT tracked trees (`DECISIONS.md`, `README.md`, `ARCHITECTURE.md`, `TODO.md`, `.aw/records/walkthroughs`, `.aw/records/roadmaps`, `.aw/records/prompt-library`), so a symmetric assertion would fail immediately and wrongly. State that the check is deliberately one-directional and why, or the next reader will "fix" it into a false failure. NOTE `TODO.md`'s presence in `SCAN_ROOTS` is itself the subject of sibling backlog `ld08f1`; do not resolve that here.
  MAKE THE FAILURE MESSAGE CONSTRUCTIVE. This repository records that a gate stating only a prohibition gets complied with by DELETION, and here the destructive fix is obvious and wrong: a failing check could be silenced by removing a tree from `TRACKED_TREES`. The message must name the tree and say the constructive action is to add its scan root.
  - Depends on: E-01, E-03
  - Expected outcome: a test deriving both lists from the modules and asserting every tracked tree has a scan root; the one-directional design stated with its reason; a failure message naming the tree and the constructive fix.
  - Execution state: pending

- [ ] E-05 MUTATION-CHECK THE GUARD, because a consistency check that cannot fail is decoration. Add a fake tree to `TRACKED_TREES` with no scan root, show the check FAILS and names that tree, revert, show it passes. Then remove the releases scan root added in E-01, show the check FAILS again (proving it would have caught the original defect), and restore.
  THE SECOND MUTATION IS THE LOAD-BEARING ONE: it demonstrates the guard would have caught the ACTUAL bug that motivated this plan, rather than only a synthetic one.
  - Depends on: E-04
  - Expected outcome: two mutations, each failing with the tree named, each passing after revert; the second reproduces the original defect.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE POLICY AND THE MAP ALREADY EXIST FOR RELEASES. `TreePolicy(name='releases', root='.agents/releases', tracked=True, owner='aw releases', reason='release records (ship-gate anchors); tracked lifecycle planned/blocked/shipped (awrelease)')`, and `attention._classify_tree` rewrites `.aw/records/<type>` to `.agents/<type>` before matching, so a `.aw/records/releases/` path already resolves. Only the scan root is missing.
- EVERY RECORDS-CLASS TREE IS LISTED IN BOTH GENERATIONS. `SCAN_ROOTS` carries `.agents/plans` and `.aw/records/plans`, `.agents/backlog` and `.aw/records/backlog`, because the layout migrated. Follow that shape.
- THE FIVE EXCLUSIONS EACH CARRY A REAL REASON, which is the standard E-03 must meet.
- AN UNCLASSIFIED FILE IS ONLY FLAGGED UNDER `.agents/`. `attention.scan` appends `attention.unclassified-tree` drift only when the path starts with `.agents/`, so a root-level or `.aw/records/`-level file with no policy is dropped SILENTLY. That is why the releases gap produced `valid: true` rather than a violation, and it is the same mechanism sibling `ld08f1` reports for `TODO.md`.
- VALIDATION AND SURFACING ARE SEPARATE, AND BOTH EXIST. `aw check releases` is wired fail-closed in CI (`.github/workflows/tests.yml:157-159`) while `aw attention` never sees the tree. Do not read the passing CI check as evidence the view is complete.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `attention_contract.TRACKED_TREES`, `artifact_core.SCAN_ROOTS` | `releases` is declared tracked and matches NO scan root, while the other four tracked trees each match at least one. | resolved every tracked tree against `SCAN_ROOTS` by import; releases -> none |
| F-2 | MED | measured | `aw attention --format json` returns 848 items (plans 557, backlog 158, research 105, specs 28) and ZERO releases, with `valid: true` and zero violations, while a release record exists on disk. The item measured 749; the corpus grew, the zero did not change. | ran the command and counted by `tree` |
| F-3 | CORRECTION | `attention_contract.TREE_POLICY`; `attention._classify_tree` | THE ITEM UNDERSTATES WHAT EXISTS: `releases` ALREADY has a `TreePolicy` (tracked, owned by `aw releases`) and `_classify_tree('.aw/records/releases/x.release.md')` already resolves to it. So the fix is ONE scan root, and adding a policy would create a duplicate. | printed `TREE_POLICY`; called `_classify_tree` on a releases path |
| F-4 | MED | `attention.scan` | An unclassified file is flagged as drift ONLY when its path starts with `.agents/`; anything else is dropped silently. That is why this defect reports `valid: true` instead of a violation. | source read of the `pol is None` branch |
| F-5 | MED | `attention_contract.TREE_POLICY` | `reviews` has NEITHER a policy nor a scan root, unlike the five trees deliberately excluded WITH reasons. The tree holds 82 records. | printed `TREE_POLICY`; `ls .aw/records/reviews \| wc -l` -> 82 |
| F-6 | MED | `check_engine` | `check.review-finding-unescalated` treats an unescalated review finding as an ERROR, which is why the reviews exclusion deserves a recorded reason. It does NOT by itself require the tree be tracked, since the finding is already policed. | rule read |
| F-7 | LOW | `.github/workflows/tests.yml:157-159` | `aw check releases` is fail-closed in CI, so release records are validated but not surfaced. That split is what made this easy to miss. | file read |
| F-8 | LOW | `artifact_core.SCAN_ROOTS` | `SCAN_ROOTS` legitimately contains entries that are NOT tracked trees (four root docs plus walkthroughs, roadmaps, prompt-library), so the E-04 guard must be ONE-directional or it fails wrongly. `TODO.md` is among them and is sibling `ld08f1`'s subject. | list read |
| F-9 | CONFIRMED-NOT-OVERLAPPING | pending plan `rnkqrc` | That plan (from `jys5dp`) names BOTH the releases scan root and the reviews policy in its deferred section as "both their own items", so this work is unowned. | read its deferred section |

## Proposed changes (ordered, validatable)

1. E-01 adds the releases scan root(s), adding no policy, and verifies a record actually appears.
2. E-02 exercises all three release statuses through the existing map.
3. E-03 decides `reviews` explicitly, to the standard the five existing exclusions set.
4. E-04 adds the one-directional consistency guard with a constructive failure message.
5. E-05 mutation-checks it, including a mutation that reproduces the original defect.

## Deferred / out of scope (with reason)

- RETIRING `TODO.md`, and its presence in `SCAN_ROOTS`. Sibling backlog `ld08f1`, whose plan is authored alongside this one. The two touch the same list, so they must not both edit it: this plan ADDS a releases entry and does not remove or repolicy the `TODO.md` entry.
- PER-REQUIREMENT SPEC TRACKING. Backlog `f1sw71`.
- THE DURABLE-CARRIER PREDICATE. Pending plan `rnkqrc` (from `jys5dp`), which explicitly defers both halves of this item to their own items.
- CHANGING ANY RELEASE RECORD, the `Blocks-Release` resolution logic, or `aw check releases`. This plan makes existing records VISIBLE; it does not change what they mean or how they validate.
- MAKING THE UNCLASSIFIED-FILE DRIFT FIRE OUTSIDE `.agents/` (F-4). That would surface this class of gap generally, and is a genuinely attractive change, but it would immediately flag the four root docs and three untracked `.aw/records/` trees that are in `SCAN_ROOTS` by design, so it needs its own decision about what to exempt. The E-04 guard closes the specific hazard without that blast radius.
- ADDING A SIXTH TRACKED TREE. Out of scope; the guard exists so that whoever does must add its scan root.

## Scope check

- Over-scope: `attention_contract.py` is in scope ONLY for the reviews policy decision (E-03). Do NOT add a releases policy, do NOT edit the existing five exclusions, and do NOT change any status map to make output tidier.
- Under-scope: stated rather than left as `none`. After this plan a file under a `.aw/records/` tree with no policy is STILL dropped silently rather than flagged as drift (F-4), and `TODO.md` is still scanned and discarded (sibling `ld08f1`). Both are named above with their owners.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. THE GUARD'S HOME, verified rather than assumed: `tests/test_attention_registry.py` DOES NOT EXIST. The two modules that already assert on these lists are `tests/test_artifact_core.py` (which pins three `SCAN_ROOTS` members) and `tests/test_attention_contract.py`. Put the E-04 cross-list guard where it can see BOTH, and say which you chose and why; extend those modules rather than creating a third that asserts on the same two lists. Synthesize release records in a temporary repo for E-02 rather than depending on the single record in this checkout, since a test pinned to one live record breaks when that record ships.

## Spec / documentation sync

The controlling spec is `.aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`, which owns `TRACKED_TREES`, the `TreePolicy` set, and the cross-tree class mapping. THIS PLAN MAY NEED TO AMEND IT, and that must be decided by READING rather than assumed either way.
CHECK TWO THINGS AND REPORT BOTH. FIRST, whether that spec enumerates the tracked trees or the excluded trees as a CLOSED list; if it does, E-03's reviews decision changes that list and the spec file MUST be added to `- Scope-Paths:` before execution, because the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual. SECOND, whether it states that a declared tracked tree is scanned; if it does, this plan is bringing the code INTO compliance and needs no amendment, and that is worth recording as the justification. Note the spec `.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md` separately PREDICTED the `TODO.md` half of this class of bug in its own text, which is evidence these specs do discuss scan behavior and should be read rather than skipped.
If E-03 tracks the reviews tree, its native status vocabulary becomes part of the cross-tree mapping and that IS a contract change requiring the amendment. Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Should the reviews tree be tracked or explicitly excluded?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer if tracking is chosen
- Resolution or deferral rationale: NOT blocking, because E-03 requires a RECORDED DECISION either way and an explicit exclusion with a reason fully discharges the item's requirement 2. The considerations, measured rather than guessed: the tree holds 82 records; a review record's findings are already policed by `check.review-finding-unescalated` as an ERROR, so tracking adds surfacing rather than enforcement; and tracking requires a native-status-to-class map that does not exist today, plus a spec amendment, since the mapping is a contract. The cheaper and probably correct answer is an explicit exclusion whose reason says the findings are policed by `aw check` and the record has no independent lifecycle status. Choosing to TRACK is defensible but is a maintainer-scope decision because it changes a contract and a 10 percent view increase, so escalate rather than deciding it inside this plan.

### OQ-02: Should `.agents/releases` be added beside `.aw/records/releases`?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because adding only the `.aw/records/` spelling fixes the measured defect in this repository and the plan is complete either way. It matters for consistency and for pre-migration repositories: `SCAN_ROOTS` lists BOTH generations for plans and for backlog, and the releases `TreePolicy` root is the `.agents/` spelling, so omitting it would make releases the only records-class tree listed in one generation. Recommend adding both for symmetry, and state whether any repository this toolkit manages still materializes `.agents/releases`, since an unused root costs a directory probe per scan and nothing else.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `SCAN_ROOTS` before and after. Paste the resolution of every `TRACKED_TREES` entry against it, showing releases now matches. Paste `aw attention --format json` counted by `tree` BEFORE and AFTER, showing releases going from 0 to at least 1 and the other four counts unchanged. Paste proof no second `TreePolicy` for releases was added (print `TREE_POLICY` and show one releases entry). State the OQ-02 decision.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste, for EACH of `planned`, `blocked` and `shipped`, a synthesized release record and the attention class it received, matching the declared map. Paste the release-record status vocabulary you compared against, and if any value has no map entry, name it. Confirm the tests synthesize records rather than reading the single live one.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new `TreePolicy` for reviews as written, with its `tracked` value and its reason. Paste the five existing exclusion reasons beside it so a reader can see the standard was met. If TRACKED: paste the status map, the BEFORE and AFTER attention item counts, `valid:` in both cases, and the spec amendment; and state that the maintainer approved the contract change. If EXCLUDED: state why, and confirm no scan root was added for it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the guard as written, showing it DERIVES both lists from the modules rather than hardcoding names. Paste it passing. Paste the failure message text and confirm it names the offending tree and states the constructive fix (add a scan root) rather than only the prohibition. Paste the recorded reason the check is one-directional, and the list of `SCAN_ROOTS` entries that are legitimately not tracked trees.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste BOTH mutations in full. Mutation 1: add a fake tracked tree with no scan root, paste the FAILING output naming it, revert, paste passing. Mutation 2: remove the releases scan root added in E-01, paste the FAILING output, restore, paste passing. Mutation 2 is the load-bearing one because it proves the guard would have caught the real defect; a V-05 pasting only mutation 1 has not shown that.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the three paths in `- Scope-Paths:`. Do NOT add a `TreePolicy` for releases (one exists). Do NOT edit the five existing exclusions or any status map. Do NOT remove or repolicy the `TODO.md` entry in `SCAN_ROOTS` (sibling `ld08f1`). Do NOT change any release record, the `Blocks-Release` resolution, or `aw check releases`. Do NOT make the unclassified-file drift fire outside `.agents/`. Do NOT edit the attention spec unless the spec-sync reading requires it, and never spec `25kzda`'s §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `SCAN_ROOTS`, `TRACKED_TREES`, `TREE_POLICY`, `TreePolicy`, `iter_scan_files`, `attention.scan`, and `_classify_tree` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. This plan and sibling `ld08f1`'s plan both edit `artifact_core.py`, so that re-verification is not boilerplate here. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved m867ox --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `v7u6vm`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited.
