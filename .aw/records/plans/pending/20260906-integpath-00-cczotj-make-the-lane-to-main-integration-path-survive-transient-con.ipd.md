# IPD: Make the lane-to-main integration path survive transient contention

- Date: 2026-09-06
- Kind: orchestrator
- Concern: The path from a VERIFIED lane to main is the least reliable part of this toolkit, and it fails by losing work that was already paid for. FOUR DEFECTS, each measured, each on that one path: a refused integration is TERMINAL on first attempt so transient dirt in main permanently strands a verified lane (`5wdoze`); neither runner checks whether main is dirty BEFORE starting, so the refusal arrives hours and dollars later for a condition knowable at startup (`p8ni63`); no verb retries just the merge, while `resume --retry-incomplete` re-dispatches finished work as paid agent turns and orphans the lane that already holds it (`yocdq4`); and the executed-transition pre-commit hook refuses EVERY legitimate lane merge, so recovery routinely requires `--no-verify` (`rnl3b7`).
  MEASURED COST, TWO INCIDENTS. Run `run-20260905T050043Z-639569` (34 items, 7h40m, $165.90) lost SEVEN of 34 items to transient dirt: four refused integration on overlapping dirty paths, three cascaded to `dependency-blocked`. All four lanes merged clean against main afterwards, so nothing was ever in conflict; they were refused because of WHEN the attempt happened. Recovery took a full session of hand merges, four of five needing `--no-verify`. Then on 2026-09-06 `mm6wuz` stranded $39.42 of verified work with THREE accumulated lanes and needed another hand recovery (`0f8abfab`, `b2bda903`).
  THE FOUR ARE ONE PROBLEM SEEN FROM FOUR ANGLES, which is why they are one Set rather than four singletons: prevention before a run (`p8ni63`), survival during a run (`5wdoze`), recovery after a run (`yocdq4`), and the gate that blocks every recovery route (`rnl3b7`). They also share code: three of the four modify `dirty_tree_overlap` or `integrate_lane_branch`, which are DUPLICATED across both runners and already DRIFTED (measured 0.72 and 0.65 similarity), so landing them independently would mean writing each change twice into two diverging copies.
- Scope: ORCHESTRATOR - authors NO product code. Its own execution work is (E-01) the whole-Set verification that the integration path now survives the two measured incidents on both hosts, and (E-02) the durable record of what the Set did and did not close. Children carry every implementation. This plan owns the child table, the sequencing decision, the anti-regression contract every child inherits, and the Set completion criteria. It explicitly EXCLUDES relaxing any refusal: every child makes a refusal SURVIVABLE or VISIBLE, never absent.
- Scope-Paths: .aw/records/plans/pending, tests
- Item-Dependencies: none
- Status: to-review
- Set: integpath
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: cczotj
- From-Backlog: 5wdoze

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the orchestrator for the four `integdefer` backlog items, on the maintainer's ruling to shape them as ONE Set with the hook fix FIRST. All four children are authored and lint-conforming BEFORE this orchestrator was completed, which is deliberate: an orchestrator whose child table names rows that resolve to no plan REFUSES retirement (`runner_shared.evaluate_set_retirement` reports `unauthored-child-rows`), and the `rununify` Set is currently stuck in exactly that state with rows `03+` and `last` unauthored. So this Set has no placeholder rows. EVERY BACKLOG CLAIM WAS RE-VERIFIED at HEAD rather than trusted, since the items are from 2026-09-05 and both runners churned heavily; two item claims were found FALSE and are corrected in the children rather than propagated: `rnl3b7`'s headline explanation that `76gsmv` passed the hook because git chose rename detection (all four commits are `R0xx` renames of identical shape and the hook handles `R` explicitly), and `yocdq4`'s ordering note that `txc9l1` blocks this work (it has since executed). The four lanes all four items cite as live evidence are GONE, so every child reproduces its condition synthetically. FRESH EVIDENCE THE ITEMS COULD NOT HAVE HAD: `mm6wuz` stranded $39.42 with three lanes on 2026-09-06, which is `yocdq4`'s predicted orphaning measured in the wild.

## Goal

Make a verified lane reach main reliably: refuse for the right reasons, survive the transient ones, recover cheaply from the rest, and never require a bypass to do it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO product code. Its execution work is whole-Set verification and the durable record; the children carry every change.

- [ ] E-01 VERIFY THE WHOLE SET against the two MEASURED INCIDENTS, on BOTH hosts, after all four children have executed. This is the Set's central claim and it must be falsifiable rather than asserted from four green child suites.
  REPRODUCE INCIDENT ONE (`run-20260905T050043Z-639569`): a lane finalizes, finds an overlapping dirty path in main, and the dirt clears while other work is still running. Assert the item DEFERS and later INTEGRATES with no agent turn spent, and that a `--no-verify` was NOT required at any point.
  REPRODUCE INCIDENT TWO (`mm6wuz`, 2026-09-06): an item holding a verified lane is resumed. Assert the FIRST lane is integrated rather than a second being allocated, and that `git branch --list 'aw/lane/<id6>*'` shows no `_attempt2`.
  ASSERT THE STARTUP GATE FIRES for a dirty base and can be overridden explicitly, since prevention is the child that stops both incidents from beginning.
  DO BOTH HOSTS EXPLICITLY. The runner suites are asymmetric (the agy side has far fewer tests and several of the largest diverged symbols have zero agy coverage), so four green child suites can still leave an agy-side regression. If a host cannot be demonstrated, say so plainly rather than inferring from the other.
  - Depends on: none
  - Expected outcome: both incidents are survived on both hosts with no paid turns, no orphaned lanes, and no hook bypass; the startup gate refuses a dirty base and honors its override.
  - Execution state: pending

- [ ] E-02 RECORD WHAT THE SET CLOSED AND WHAT IT DID NOT, as a durable artifact, because this Set deliberately leaves several named things open and a reader six months from now must not have to infer which.
  STATE THE RESIDUALS EXPLICITLY, each already named by a child: content-based narrowing of the dirty-overlap false-positive rate (declined by the maintainer 2026-09-05 as low-value relative to the ladder); path-category allowlists (REJECTED, not deferred, because they reason about who probably wrote a file rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits); `h1ksy6`, which fixes the same function but WIDENS its input set and must be reconciled with the ladder rather than stacked on it; `a8eufb`, which would let the runner tell its own dirt from a co-worker's and is NECESSARY BUT NOT SUFFICIENT here because trailers mark commits while the motivating incident was 130+ uncommitted files; and why `76gsmv` passed the hook, which child 01 leaves as a deferred open question rather than guessing.
  NAME THE SIBLING SETS this one does NOT cover, so the boundary is legible: `integearn` (`32ij2j`, `xtklpd`) covers a lane whose integration was never ATTEMPTED because the earned-integration gate refused, which is a different failure from the four here; `scopeattr` (`hyx1dg`) and `depreview` (`yf9fj9`, `phawyy`) came from the same recovery sessions but are unrelated mechanisms.
  - Depends on: E-01
  - Expected outcome: a durable record naming every residual with its reason and every sibling Set with its boundary; no residual is left as an unstated assumption.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

All four children are AUTHORED, `to-review`, and `aw ipd lint` conforming. There are NO placeholder rows: an orchestrator whose table declares a row resolving to no plan refuses retirement (`unauthored-child-rows`), which is the state `rununify` is stuck in.

| Order | Id | What it does | Depends on |
|---|---|---|---|
| 01 | `29wvmj` | Teach the executed-transition hook to recognize a legitimate lane merge, via IN-TREE evidence (a `lifecycle(<id6>): finalize` commit on the incoming side) rather than the gitignored journal that cannot travel with a branch. FIRST because children 03 and 04 make integration happen MORE often, so every one of those merges would trip this hook and multiply the `--no-verify` habit. From `rnl3b7`. | none |
| 02 | `6sb3yu` | Extract `dirty_tree_overlap` and `integrate_lane_branch` into `runner_shared.py` as ONE implementation each. Measured safe: the only BEHAVIORAL difference between the two copies is one commit-subject label (`aw agy run` versus `aw oc run`); the rest of the 44-line diff is comment. Pure de-duplication, no behavior change, so children 03 and 04 each write their change ONCE. From `5wdoze` (seam only). | `executed:29wvmj` |
| 03 | `51vw4y` | The maintainer-approved three-rung deferral ladder: defer-and-re-attempt while other work exists, a doubly-bounded poll when nothing else is dispatchable, a timeout-bounded ask suppressed without a TTY, then terminal. Plus a SEPARATE `--integration-retry-limit`, never the correction budget. From `5wdoze`. | `executed:6sb3yu` |
| 04 | `rl67b0` | Add `aw <host> integrate <id6>` (no agent turn, through the revalidate gate), then have `resume` call it automatically BEFORE an item is eligible for re-dispatch, so finished work is merged rather than reproduced and orphaned. From `yocdq4`. | `executed:51vw4y` |

NOT A CHILD OF THIS SET, and deliberately so: `p8ni63` (the startup dirty-base gate) remains OPEN backlog. It is prevention rather than recovery, it is a separate refusal surface with its own consent flag (`--allow-dirty-base`), and it does not touch the two functions children 02 through 04 share. E-01 still VERIFIES it if it has landed by then; if it has not, E-01 records that and the Set's completion criteria do not depend on it.

Hard constraints every child inherits, stated once here:
- CHILDREN ARE SEQUENTIAL, not parallel. All four declare `oc_runipd.py` or `agy_runipd.py`, the two highest-contention files in the repository, and three other pending Sets also declare them. Declaring these parallel would guarantee merge conflicts.
- NO CHILD MAY RELAX A REFUSAL. Every refusal in this path exists because integrating over a contaminated base can clobber or half-finish work. A child may make a refusal SURVIVABLE (defer and retry), CHEAPER TO RECOVER FROM (the verb), or CORRECTLY SCOPED (the hook). None may remove one.
- EVERY RE-ATTEMPT ROUTES THROUGH `orchestrate_isolation.execute_merge_and_revalidate_gate`. A lane verified against yesterday's main is not verified against today's, and `git merge-tree` cleanliness proves absence of TEXTUAL conflict only. No child may substitute it for the gate.
- A CHILD MUST LAND IN BOTH RUNNERS OR IN NEITHER, and any guard it adds must assert over BOTH. A one-sided guard is how `render_stream` was extracted and then re-forked in the other driver with nothing noticing.
- NO CHILD RESOLVES DIRT. This repository's policy for un-owned dirty state is to leave it strictly alone. Children report, wait, ask, and refuse; none stashes, resets, or cleans.
- EVERY CHILD PRESERVES THE LANE on a refusal. The lane is the evidence and the recovery route.

## Completion criteria (the whole Set is done only when)

- Both MEASURED INCIDENTS are survived on BOTH hosts (E-01), with no paid agent turn spent re-doing finished work and no lane orphaned.
- A legitimate lane merge needs NO `--no-verify`, and the hand-edit case is still refused (child 01).
- `dirty_tree_overlap` and `integrate_lane_branch` have exactly ONE implementation each, asserted by object identity and by a SYMMETRIC guard over both runners (child 02).
- A dirty-overlap refusal is NON-TERMINAL and is re-attempted, bounded by both a count and main's activity staleness, with the reason reported either way (child 03).
- `aw <host> integrate <id6>` exists on both hosts and a bare `resume` integrates an already-verified lane with no agent turn and no second lane (child 04).
- EVERY re-attempt provably ran the revalidate gate, not a bare merge.
- No refusal was relaxed: each child's refusal conditions are unchanged or narrower-for-a-stated-reason, never absent.
- The residuals and sibling boundaries are recorded (E-02).

## Cross-IPD validation

- CID-1: exactly ONE implementation of `dirty_tree_overlap` and `integrate_lane_branch`, verified by object identity and by an AST check that NEITHER runner defines them, with the guard symmetric over both.
- CID-2: no child relaxed a refusal. For each child, its refusal conditions before and after are compared and any narrowing carries a stated reason.
- CID-3: every integration attempt in the Set's final state routes through the revalidate gate; no code path reaches `git merge` on the strength of `merge-tree` alone.
- CID-4: both incidents survived on BOTH hosts, demonstrated rather than inferred from green child suites, since the agy suite is materially thinner.
- CID-5: no `--no-verify` is required anywhere in the recovered path.

## Project conventions discovered (Step 0)

- THE REFUSAL ITSELF IS CORRECT AND MUST SURVIVE. `integrate_lane_branch` refuses BEFORE running the gate so it never integrates over a contaminated base, leaving main untouched and the lane preserved. This Set changes the DISPOSITION after a refusal, never the refusal condition.
- THE TWO KEY FUNCTIONS ARE DUPLICATED AND ALREADY DRIFTED: measured 0.72 similarity for `dirty_tree_overlap` and 0.65 for `integrate_lane_branch`, neither in `runner_shared.py`. Three of the four backlog items independently ask for shared placement, citing `cnwy8g` on the 40-symbol import coupling.
- THE DRIFT IS COMMENTARY, NOT DESIGN, which is what makes child 02 a safe pure move: the only behavioral difference is one commit-subject host label.
- BINDING, NOT COPYING, IS THE ESTABLISHED PATTERN: `agy_runipd.py` already imports 46 names from `oc_runipd.py` with the `as <same-name>` re-export form, and its comments record that `ruff` stripped 6 such re-exports until a symmetry test caught it.
- INFORMING AN AGENT IS NECESSARY AND NOT SUFFICIENT: `k1nity` measured byte-identical duplicate commits on 3+ resumed runs DESPITE an explicit recovery notice. Every correctness guarantee in this Set must live in a deterministic code path, never in prose the agent is expected to honor.
- AN ORCHESTRATOR WITH AN UNAUTHORED CHILD ROW CANNOT RETIRE. `runner_shared.evaluate_set_retirement` returns `unauthored-child-rows` and the runner leaves the plan pending; `rununify` is stuck this way with rows `03+`/`last`. Hence this Set's table has no placeholders.
- Run the suite BARE: `python3 -m pytest`. The suite is NOT green at HEAD, so judge on the DELTA. Validate `tests/test_run_viewer.py` in the REAL checkout, since it reads the gitignored `.aw/records/runs/`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | **INCIDENT ONE:** run `run-20260905T050043Z-639569`, 34 items, 7h40m, $165.90. Four items refused integration on dirty-path overlap (`76gsmv` 08:06:32, `eyh1fu` 08:51:26, `txc9l1` 10:48:33, `uyeko5` 11:47:04); three more cascaded to `dependency-blocked`. Seven of 34 lost to transient dirt, and all four lanes merged clean afterwards. | backlog `5wdoze` event excerpts |
| F-2 | **INCIDENT TWO, fresh evidence the items could not have had:** `mm6wuz` stranded $39.42 of verified work on 2026-09-06 with THREE accumulated lanes (`aw/lane/mm6wuz`, `_attempt2`, `_attempt3`), recovered by hand. That is `yocdq4`'s predicted orphaning measured in the wild. | `git branch --list 'aw/lane/mm6wuz*'`; commits `0f8abfab`, `b2bda903` |
| F-3 | Recovery routinely requires a bypass: four of five recovery merges used `--no-verify`, each with a real `lifecycle(<id6>): finalize` commit on the lane (`c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`). A gate bypassed as routine practice teaches that the bypass is normal. | backlog `rnl3b7` |
| F-4 | THE THREE-WAY CODE OVERLAP that makes this one Set: `dirty_tree_overlap` and `integrate_lane_branch` are duplicated across both runners at 0.72 and 0.65 similarity, absent from `runner_shared.py`, and modified by three of the four children. | AST + `difflib` measurement 2026-09-06 |
| F-5 | **TWO BACKLOG CLAIMS ARE FALSE and are corrected in the children rather than propagated.** `rnl3b7` attributes the hook's inconsistency to git rename detection; all four commits are `R0xx` renames of identical shape and the hook branches on `R` explicitly with `-M` enabled, so there is no rename-vs-add defect to fix. `yocdq4` says `txc9l1` is blocked behind this work; `txc9l1` has EXECUTED. | `git log --diff-filter=R` per id6; `executed_transition_gate.py:108`, `:118`; `ls .aw/records/plans/executed/*txc9l1*` |
| F-6 | ALL FOUR CITED LANES ARE GONE (branches deleted, plans in `executed/`), so every child reproduces its condition synthetically rather than pointing at live evidence. | `git rev-parse --verify` fails for all four |
| F-7 | The hook defect is structural, not incidental: its evidence journal lives under gitignored `.aw/state/`, so it can never travel with a lane branch. REPRODUCED synthetically: a lane carrying a real finalize commit, merged with `--no-ff --no-commit`, is refused with `MERGE_HEAD` present. | live reproduction 2026-09-06; `executed_transition_gate.py:152-172` |
| F-8 | `p8ni63` is NOT a child of this Set and remains open backlog: it is prevention rather than recovery, has its own consent flag, and does not touch the two shared functions. Named here so its absence is a decision rather than an omission. | backlog `p8ni63` |

## Proposed changes (ordered, validatable)

1. Children 01 through 04 execute in order, each carrying its own findings and validations (see the child table).
2. Verify the whole Set against both measured incidents on both hosts (E-01).
3. Record the residuals and the sibling-Set boundaries durably (E-02).

## Deferred / out of scope (with reason)

- CONTENT-BASED NARROWING of the dirty-overlap false-positive rate (skipping the refusal when main's dirty version of a path is byte-identical to the merge result). Considered and DELIBERATELY DECLINED by the maintainer on 2026-09-05 as low-value relative to the ladder.
- PATH-CATEGORY ALLOWLISTS ("docs are safe", "review records are harmless"). EXPLICITLY REJECTED rather than deferred: they reason about who probably wrote a file instead of whether it can conflict, which is the fail-open inference `d07nz2` prohibits. Narrow on content, never on category.
- THE STARTUP DIRTY-BASE GATE (`p8ni63`). Prevention, separate refusal surface, own consent flag, no shared code with children 02 through 04. Stays open backlog; E-01 verifies it opportunistically.
- RECONCILING `h1ksy6`, which fixes the same function but WIDENS its input set, making refusal MORE reachable. It is diagnostic-only and does not address "then what". These two must be reconciled rather than stacked blindly, and that needs `h1ksy6` to have a plan first.
- KNOW-YOUR-OWN-DIRT (`a8eufb`). Would improve every message in this Set once ownership is knowable, and is NECESSARY BUT NOT SUFFICIENT here: trailers mark COMMITS, while the motivating incident was 130+ UNCOMMITTED working-tree files from a stray `aw install`, carrying no trailer at all.
- THE `integearn` SET (`32ij2j`, `xtklpd`). Covers a lane whose integration was never ATTEMPTED because the earned-integration gate refused on a pre-existing red test, plus the report that called it COMPLETED. A different failure on the same path, deliberately a separate Set so each can be reviewed independently.
- `scopeattr` (`hyx1dg`) AND `depreview` (`yf9fj9`, `phawyy`). Surfaced during the same recovery sessions but unrelated mechanisms.
- CLEANING UP THE EXISTING ORPHANED LANES (`mm6wuz`'s three, and any others). Not this Set's business; the fix is that new ones stop being created.

## Scope check

- Over-scope: none. This orchestrator authors no product code; its Scope-Paths are the plans directory and tests, matching the `rununify` orchestrator's precedent.
- Under-scope, stated rather than left as `none`: this Set does not include the startup gate (`p8ni63`), does not reconcile `h1ksy6`, does not implement `a8eufb`, does not cover the `integearn` failure mode, and does not clean up existing orphaned lanes. Each is excluded with a reason above.

## Required tests / validation

- Each child runs its own validation; this orchestrator's E-01 adds the WHOLE-SET verification against both measured incidents on BOTH hosts.
- `python3 -m pytest` BARE at the Set's end, with the `N passed` summary line pasted. MEASURE YOUR OWN BEFORE-BASELINE: the suite is NOT green at HEAD (`1 failed, 5612 passed` at authoring, the failure being pre-existing `test_orchestrator_retirement::RealRepositorySets`), so the criterion is that the AFTER failure set minus the BEFORE set is EMPTY.
- VALIDATE IN THE REAL CHECKOUT for `tests/test_run_viewer.py` (reads the gitignored `.aw/records/runs/`).
- CID-1 through CID-5 each demonstrated with pasted evidence, not asserted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change is authorized by this orchestrator. Child 04 adds a VERB to the run surface and must check spec `25kzda`'s command table itself; child 03 adds two flags and must check its flag table. Neither may edit the spec's §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

A CHANGELOG entry is warranted for the Set as a whole, since it adds an operator-facing verb, two flags, and changes what a bare `resume` does. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Should `p8ni63` (the startup dirty-base gate) be pulled in as a fifth child?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, keep it separate. Three reasons. It is PREVENTION rather than recovery, so it fails differently: it refuses a run before any work exists, where all four children handle work that already exists and must not be lost. It shares NO code with children 02 through 04 (it adds a startup preflight, not a change to `dirty_tree_overlap` or `integrate_lane_branch`), so the shared-extraction argument that binds these four does not apply to it. And it carries its own consent surface (`--allow-dirty-base`) whose default is a maintainer decision independent of anything here. Pulling it in would add a fifth sequential child to a Set already serializing four against the two highest-contention files, for no shared-code benefit. E-01 verifies it opportunistically if it has landed.

### OQ-02: Should the children be parallelized to reduce the Set's wall-clock time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. All four declare `oc_runipd.py` or `agy_runipd.py`, and children 02 through 04 modify the SAME two functions in sequence: 02 extracts them, 03 wraps one in a ladder, 04 reuses the ladder's re-attempt path. Parallelizing would guarantee conflicts on the repository's highest-contention files, and the dependency chain is real rather than conservative (each child's `Item-Dependencies` names its predecessor for a stated reason). The runner isolates each item in its own worktree and re-checks dependencies at dispatch, so a queued-together Set is already safe to run unattended; sequential execution is the correct shape, not a limitation.

### OQ-03: Should this Set wait for `rununify` to converge the two runners first?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and waiting would be indefinite. `rununify` cannot currently retire: its child table declares rows `03+` and `last` that resolve to no plan, so `evaluate_set_retirement` reports `unauthored-child-rows`, and its E-02 characterization baseline is also unexecuted. Blocking four measured, cost-bearing defects behind a Set that is itself stalled would repeat the pattern its own findings warn about, where five plans deferred to a convergence item while landing duplicated code meanwhile. Child 02 instead extracts EXACTLY the two functions this Set needs, which REDUCES `rununify`'s remaining work rather than colliding with it: those two symbols move from the diverged set into the shared module, and the Set's symmetric guard prevents them re-forking.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste BOTH incidents reproduced and survived, for BOTH hosts. Incident one: a lane refused on dirty overlap, DEFERRED, then INTEGRATED after the dirt cleared, with the merge commit on main and NO agent turn spent. Incident two: an item with a verified lane resumed, showing the FIRST lane integrated and `git branch --list 'aw/lane/<id6>*'` containing NO `_attempt2`. For both, paste evidence that NO `--no-verify` was used anywhere. State whether `p8ni63` had landed and, if so, paste the startup gate refusing a dirty base and honoring its override. If a host could not be demonstrated, SAY SO PLAINLY; an inferred agy result is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the durable record's path and its residuals section, confirming all five named residuals appear with their reasons (content narrowing declined, category allowlists rejected, `h1ksy6` unreconciled, `a8eufb` insufficient-for-uncommitted-dirt, and why `76gsmv` passed the hook still unknown). Confirm the three sibling Sets are named with their boundaries (`integearn`, `scopeattr`, `depreview`). Paste the CID-1 through CID-5 evidence, each demonstrated rather than asserted, including the object-identity check for the two extracted functions and proof the anti-re-fork guard is SYMMETRIC over both runners.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

THIS ORCHESTRATOR AUTHORS NO PRODUCT CODE. Its Scope-Paths are the plans directory and tests. If executing it appears to require a change to `agent_workflows/`, that is a child's work and the child table is wrong; stop and report rather than editing product code from here.

RETIREMENT: this plan retires to `executed` only when EVERY child is `executed` on disk. The runner performs that transition itself once the condition holds (`runner_shared.evaluate_set_retirement`), spending no agent turn, so an Order-0 parent in the queue is correct and needs no human step. It REFUSES to retire while any child row resolves to no plan; this table has no such rows by construction, which is the state `rununify` is stuck in.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: the suite is NOT green at HEAD and this Set does not make it green. Judge on the DELTA, and do not report the pre-existing `test_orchestrator_retirement` failure as this Set's.

THE CLAIM THIS SET MAKES IS THAT VERIFIED WORK STOPS GETTING LOST, so V-01 is what earns it. Four green child suites are NOT sufficient evidence: each child tests its own mechanism, and the failure this Set exists to prevent is an INTERACTION (a refusal that is terminal, times a recovery route that is blocked, times a resume that orphans the lane). Reproduce the incidents end to end or the Set has not been verified.

DO NOT LET A CHILD RELAX A REFUSAL TO MAKE ITS TESTS PASS. Every refusal here exists because integrating over a contaminated base can clobber or half-finish real work. If a child's tests only pass once a refusal is weakened, that child is wrong, not the refusal.

On completion, close backlog `5wdoze`? NO. Its substance is the deferral ladder, which child 03 delivers, and `- From-Backlog: 5wdoze` on this orchestrator records provenance only. Each child closes its own item: `29wvmj` closes `rnl3b7`, `51vw4y` closes `5wdoze`, `rl67b0` closes `yocdq4`. `p8ni63` stays OPEN and is not this Set's to close.
