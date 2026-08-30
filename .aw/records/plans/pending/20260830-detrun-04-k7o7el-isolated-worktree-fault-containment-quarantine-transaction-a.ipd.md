# IPD: Isolated worktree fault containment, quarantine transaction, and commit gateway trailers

- Date: 2026-08-30
- Kind: child
- Concern: Worktree mutation failures currently risk leaving dirty paths in the main working tree or aborting entire multi-item runs rather than containing errors item-locally.
- Scope: Implement worktree allocation with path leases, the 7-step deterministic containment transaction for failed/out-of-scope mutations, the quarantine bundle directory, the exhaustive 6-class `ABORT RUN` engine, and the commit gateway appending `AW-Run:` and `AW-Item:` trailers. Implements spec 25kzda Sections 4.1, 4.2, 5.1, and 5.7.
- Scope-Paths: agent_workflows/worktree_containment.py, agent_workflows/commit_gateway.py, agent_workflows/orchestrate_isolation.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_fault_containment.py
- Item-Dependencies: executed:kaygwo
- Status: reviewed
- Set: detrun
- Order: 4
- Highest E allocated: 07
- Author: antigravity
- Id: k7o7el
- Blocks-Release: next

## Workflow history
- 2026-08-30 /plan-review pass 2 (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN reaffirmed on STRONGER evidence; residue narrowed to ONE item; PR-101..PR-111. SELF-CORRECTION (PR-109): pass 1 rejected E-01 by citing `orchestrate_isolation.py` (1152 lines) as "the canonical worktree lease manager", repeating the plan's own Step-0 bullet. That citation is FALSE. `worktree_lease.py:4-16` states plainly that `orchestrate_isolation.analyze_concurrency_eligibility` "never creates a git worktree or session, and there is NO per-path exclusive-ownership lease" in it. The CORRECT citation is `agent_workflows/worktree_lease.py` (222 lines), and it is far more damning than pass 1's: it ships `allocate_worktree` (:70), `teardown_worktree` (:106), `LeaseTable.claim`/`release` (:164/:183) as a real single-writer path lease, and `path_is_worker_forbidden`/`assert_worker_scope` (:208/:214) already fencing coordinator-owned paths - byte-for-byte E-01's two named deliverables. Both runners already CONSUME it (`oc_runipd.py:480`, `agy_runipd.py:590`) and so does `aw work begin` (`work_cmd.py:250`). NEW BLOCKER (PR-104): E-02 step 4 + step 7 (delete item-created untracked paths, then tear down) CONTRADICTS a deliberate shipped behavior AND an approved plan. `oc_runipd.py:2501` PRESERVES a non-integrated lane on purpose ("forward-progress rule: never discard work"), recording `preserved_worktree` + a `worktree-preserved` event; APPROVED `wtiso-03` (`rchpms`) E-09/E-10 adds a five-way retention classifier in which an `unknown` untracked file BLOCKS teardown and explicitly forbids "ignored means disposable". Two teardown policies cannot both be authoritative; the approved `wtiso` orchestrator `bl9q3d` settles it in `rchpms`'s favor (`:87`, `:91`, `:97`), so new OQ-02 is RESOLVED from repository evidence and E-02 may only return as an EXTENSION of that gate. NEW BLOCKER (PR-106): E-04's `CommitGateway` forks `git_commit_helper.offer_commit` (:133), which AGENTS.md itself names as the tooled commit path "immune by construction"; the only unbuilt part is the two trailer lines. NEW (PR-102): E-01's `.aw/state/worktrees/` path is wrong - the shipped constant is `worktree_lease.WORKTREES_SUBDIR = ".aw/worktrees"` (:32), gitignored at `.gitignore:73` and hardcoded in `ipd_set_plan.py:474` + `check_engine.py:1007`; `.aw/state/worktrees` greps to ZERO. NEW (PR-105): `ownership_conflict` greps to ZERO while `run_ledger_schema.LANE_OUTCOMES` (:112) is a CLOSED frozenset already containing `unknown_outcome`, so E-03's vocabulary would fork ledger state. Surviving residue is now ONE item: the `AW-Run:`/`AW-Item:` trailers (still zero hits across 556 files) as a ~20-line change to the SHIPPED helper, sequenced after `rununify`.
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001/PR-003. E-01 duplicates the APPROVED 7-plan `wtiso` Set and the shipped `orchestrate_isolation.py` (1152 lines) that this plan's own conventions section names as the canonical lease manager. E-05 collides with APPROVED `rununify` (`5e4sb6`). Depends on child 03, itself REPLAN. Genuine residue: the `AW-Run:`/`AW-Item:` trailers (zero hits today) plus CommitGateway, and the 7-step containment transaction / 6-class abort classifier, as an EXTENSION of `orchestrate_isolation.py`. Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened 7-step containment transaction, quarantine bundle hashing, abort escalation rules, and commit gateway trailers.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE. Verdict unchanged; pass-1 evidence CORRECTED and the residue narrowed
from three items to ONE (/plan-review 2026-08-30 pass 2, PR-101..PR-111 BLOCKER).** Verified at HEAD
`32cd5495`.

RETRACTION OF A PASS-1 CITATION (PR-109). Pass 1 rejected E-01 by citing
`agent_workflows/orchestrate_isolation.py` (1152 lines) as "the canonical worktree lease manager". That
citation is FALSE, and pass 1 inherited it uncritically from this plan's own Step-0 bullet.
`worktree_lease.py:4-16` says the opposite in so many words: the concurrency ANALYZER in
`orchestrate_isolation` "only decides whether lanes MAY run in parallel and CARRIES a caller-supplied
`worktree_path`/`session_id`; it never creates a git worktree or session, and there is NO per-path
exclusive-ownership lease in the tree". The verdict does not change, because the CORRECT citation is
worse for this plan:

| E-01 proposes | Shipped in `agent_workflows/worktree_lease.py` (222 lines) |
| --- | --- |
| allocate a clean isolated worktree | `allocate_worktree` (`:70`) - real `git worktree add -b aw/lane/<id>`, resolves + freezes `base_commit`, fail-closed `WorktreeError`, no partial claim |
| tear it down | `teardown_worktree` (`:106`) |
| acquire single-writer path leases before mutation | `LeaseTable.claim` (`:164`) - atomic, fail-closed on ANY conflict, `LeaseConflictError`; `release` (`:183`); `snapshot` (`:190`) for checkpointing |
| protect coordinator-owned paths | `FORBIDDEN_WORKER_PATH_HINTS` (`:199`) + `path_is_worker_forbidden` (`:208`) + `assert_worker_scope` (`:214`), already fencing `.aw/records/plans/`, `backlog/`, `walkthroughs/`, `runs/`, and `events.jsonl` |

It is not merely shipped, it is already CONSUMED at all three call sites this plan would touch:
`oc_runipd.allocate_isolation_worktree` (`oc_runipd.py:480`), `agy_runipd.allocate_isolation_worktree`
(`agy_runipd.py:590`), and `work_cmd.run_work_begin` (`work_cmd.py:250`, which also writes a durable
lease JSON). E-01 would be a SECOND worktree allocator and a SECOND lease table (P8, single source of
truth).

E-01 also names the WRONG PATH (PR-102). It writes worktrees under `.aw/state/worktrees/`. The shipped
constant is `worktree_lease.WORKTREES_SUBDIR = ".aw/worktrees"` (`:32`), gitignored at `.gitignore:73`,
hardcoded in `ipd_set_plan.py:474`, and specially excluded from scope-drift by
`check_engine.py:1007`. `.aw/state/worktrees` greps to ZERO hits repo-wide. An executor following E-01
literally would create an untracked, unrecognized second worktree root that the scope checker does not
exempt.

NEW BLOCKER FOUND THIS PASS - E-02 CONTRADICTS A DELIBERATE SHIPPED BEHAVIOR AND AN APPROVED PLAN
(PR-104). E-02's containment steps 4 and 7 ("remove only untracked paths proven to have been created by
this item", then "tear down the isolated worktree") collide head-on with two authorities:

- SHIPPED: `oc_runipd.py:2500-2530` (twin at `agy_runipd.py`) deliberately does the OPPOSITE. When a
  lane is not integrated it PRESERVES the worktree, recording `preserved_worktree`,
  `preserved_branch`, and a `worktree-preserved` event, under an explicit comment: "PRESERVE it
  attributably rather than tearing it away (forward-progress rule: never discard work)".
- APPROVED: `wtiso-03` (`rchpms`) E-09/E-10 adds `lane_status.classify_output` plus
  `harvest_and_teardown_gate`, in which ANY `unknown` untracked file sets `teardown_authorized ==
  False` and preserves the lane, and which explicitly forbids the "ignored means disposable" shortcut.
  That plan's own review named this F6/F7.

So E-02 is not filling a gap; it is proposing a THIRD, conflicting teardown policy. Which policy is authoritative is settled by repository evidence, not by a review edit: the approved
`wtiso` orchestrator `bl9q3d` assigns teardown/retention to `rchpms` (`:87`, `:91`) and binds later work
to EXTEND `lane_status.py` rather than fork it (`:97`). See resolved OQ-02.

NEW BLOCKER - E-04 FORKS THE HOUSE COMMIT PATH (PR-106). `git_commit_helper.offer_commit`
(`git_commit_helper.py:133`) already does everything E-04's `CommitGateway` lists: stages ONLY explicit
paths (`add -- <paths>`, `:225`), commits path-scoped (`commit -m msg -- <our_staged>`, `:245`), never
`--no-verify` (so hooks run), never pushes, snapshots the index BEFORE staging and rolls back only its
own paths on failure (`:228`, `:246`). AGENTS.md names this exact path as the one "immune by
construction" to index pollution, and `aw commit` (`work_cmd.run_commit:439`) is its CLI. A new
`commit_gateway.py` would fork the one commit path the repository contract points every agent at.

NEW - E-03 WOULD FORK LEDGER VOCABULARY (PR-105). E-03 escalates to `ownership_conflict` /
`unknown_outcome`. `unknown_outcome` is real and canonical: `run_ledger_schema.LANE_OUTCOMES`
(`run_ledger_schema.py:112`) is a CLOSED frozenset containing it, and `run_recovery.UNKNOWN_OUTCOME`
(`:51`) plus `set_stop_policy.ACTION_RECONCILE_UNKNOWN` (`:37`) already implement
detection-and-reconciliation. `ownership_conflict` greps to ZERO. Writing it as a ledger outcome would
either fail the closed-set validator or require widening it; the plan says nothing about either.

UNCHANGED FROM PASS 1 (re-verified at `32cd5495`):

- E-05 edits BOTH `oc_runipd.py` and `agy_runipd.py`, fighting APPROVED `rununify` (`5e4sb6`), whose
  whole charter is collapsing their duplication. Parent-Set OQ-03 (blocking) still owns this.
- `Item-Dependencies: executed:kaygwo` inherits every blocker of child 03, itself REPLAN with two of
  its own blocking open questions.
- The `wtiso` Set (7 plans, `bl9q3d`, all `approved`) owns worktree isolation and the driver-owned
  control plane end to end, including the retention/teardown gate (`rchpms`) and the typed host
  capability contract (`1o4eif`).

WHAT SURVIVES, now ONE item rather than three: the `AW-Run: <run-id>` / `AW-Item: <id6>` commit
trailers. Re-verified this pass: ZERO matches across 556 searched files. This is genuine, valuable, and
small - roughly a `trailers: Sequence[str]` parameter on the SHIPPED `offer_commit`, appended after a
blank line per Git trailer convention, plus a matching `aw commit` flag and a test. It is NOT a new
module, and it should land AFTER `rununify` so it is wired once.

Original goal, retained for the record: provide a robust worktree isolation and fault-containment
system that isolates mutations, quarantines and rolls back out-of-scope or failed item mutations,
restricts run aborts to six fatal integrity violations, and formats commit trailers immutably.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Worktree allocation and path lease management

- [ ] E-01 Implement `WorktreeContext` in `agent_workflows/worktree_containment.py` integrating with `orchestrate_isolation.py` to allocate clean, isolated worktrees under `.aw/state/worktrees/` and acquire single-writer path leases before mutation starts.
  - Depends on: none
  - Expected outcome: **DO NOT BUILD (PR-101/PR-102/PR-109). SHIPPED, and already consumed at every call site this item would touch.** `agent_workflows/worktree_lease.py` (222 lines) provides `allocate_worktree` (`:70`, real `git worktree add -b aw/lane/<id>` with a frozen `base_commit` and fail-closed `WorktreeError`), `teardown_worktree` (`:106`), `LeaseTable.claim`/`release`/`snapshot` (`:164`/`:183`/`:190`, an atomic single-writer path lease that fails closed on ANY conflict), and coordinator-path fencing via `FORBIDDEN_WORKER_PATH_HINTS` + `path_is_worker_forbidden` + `assert_worker_scope` (`:199`/`:208`/`:214`) - i.e. BOTH of this item's stated deliverables. Consumers already exist: `oc_runipd.py:480`, `agy_runipd.py:590`, `work_cmd.py:250`. **CORRECTION to pass 1 (PR-109):** pass 1 cited `orchestrate_isolation.py` as "the canonical worktree lease manager"; that is false and `worktree_lease.py:4-16` says so explicitly ("it never creates a git worktree or session, and there is NO per-path exclusive-ownership lease in the tree"). The correct citation is `worktree_lease.py`, which is a stronger rejection, not a weaker one. **Also WRONG PATH (PR-102):** `.aw/state/worktrees/` greps to ZERO; the shipped constant is `WORKTREES_SUBDIR = ".aw/worktrees"` (`worktree_lease.py:32`), gitignored (`.gitignore:73`), hardcoded in `ipd_set_plan.py:474`, and scope-drift-exempted in `check_engine.py:1007`. Building E-01 literally would create a second, unrecognized worktree root. Original expected outcome: Mutating actions run in an isolated worktree; coordinator-owned paths and non-leased paths are protected.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Do not tick this box.

### Task group 2: Deterministic containment transaction

- [ ] E-02 Implement `contain_item_failure()` in `agent_workflows/worktree_containment.py` executing the 7-step containment transaction (terminate worker, freeze/hash quarantine bundle, restore baseline, verify clean worktree, release leases).
  - Depends on: E-01
  - Expected outcome: **DO NOT BUILD AS WRITTEN - CONTRADICTS A SHIPPED BEHAVIOR AND AN APPROVED PLAN (PR-104, new this pass).** Steps 4 and 7 (delete item-created untracked paths, then tear the worktree down) are the OPPOSITE of two authorities. (a) SHIPPED: `oc_runipd.py:2500-2530` (twin in `agy_runipd.py`) deliberately PRESERVES a non-integrated lane, recording `preserved_worktree`, `preserved_branch`, and a `worktree-preserved` event under the explicit comment "PRESERVE it attributably rather than tearing it away (forward-progress rule: never discard work)". (b) APPROVED: `wtiso-03` (`rchpms`) E-09/E-10 adds `lane_status.classify_output` + `harvest_and_teardown_gate`, where ANY `unknown` untracked file yields `teardown_authorized == False` and PRESERVES the lane, and which explicitly forbids the "ignored means disposable" shortcut (its F6/F7). Three conflicting teardown policies cannot coexist, and the approved `wtiso` orchestrator `bl9q3d` already picks the winner: criterion 15 (`:91`) and criterion 7 (`:87`) assign teardown/retention to `rchpms`, and `:97` binds any later child to EXTEND `lane_status.py` rather than fork it. See resolved OQ-02. Also note the quarantine bundle destination `.aw/records/runs/<run-id>/quarantine/<item-id6>/` sits under a GITIGNORED tree (`.aw/.gitignore:15`), so the bundle is box-local and ephemeral - fine, but the plan should say so rather than implying a durable record. A containment transaction may therefore only EXTEND `wtiso-03`'s classifier/harvest gate (adding the evidence bundle and the `contained: true` receipt), never replace it and never delete what that gate would preserve. Original expected outcome: Out-of-scope changes or failed validation restore isolated worktree to baseline with `contained: true` evidence, writing `.aw/records/runs/<run-id>/quarantine/<item-id6>/` bundle, allowing independent queue items to proceed.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Resolved OQ-02 assigns teardown/retention to approved `wtiso-03` (`rchpms`); this item may only return as an EXTENSION of that gate. Do not tick this box.

- [ ] E-03 Implement the exhaustive 6-class `ABORT RUN` classifier and containment escalation engine in `agent_workflows/worktree_containment.py` (corrupt ledger, lease conflict, unknown outcome, push attempt, hook bypass, identity ambiguity).
  - Depends on: E-02
  - Expected outcome: **KEEP THE SUBSTANCE, FIX THE VOCABULARY, AND FIND IT A HOME (PR-105).** The 6-class abort taxonomy from spec 25kzda 4.1 is not obviously shipped as a single classifier, so the idea is defensible. Two defects as written. (1) VOCABULARY FORK: `unknown_outcome` is canonical - `run_ledger_schema.LANE_OUTCOMES` (`:112`) is a CLOSED frozenset containing it, and `run_recovery.UNKNOWN_OUTCOME` (`:51`) + `set_stop_policy.ACTION_RECONCILE_UNKNOWN` (`:37`) already implement detect-and-reconcile - so the classifier must EMIT the shipped value, not define its own. `ownership_conflict` greps to ZERO; adding it to a closed frozenset is a schema change the plan never mentions, and `worktree_lease.LeaseConflictError` (`:39`) is the existing in-code signal for that condition. (2) NO HOME: it cannot live in a `worktree_containment.py` that must not exist (E-01), and it depends on E-02, whose teardown half resolved OQ-02 reassigns to approved `wtiso-03`. Original expected outcome: Only the 6 enumerated fatal classes abort the full run; containment failures escalate to `ownership_conflict` or `unknown_outcome` when baseline restoration cannot be proven.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Transitively blocked by E-02. Do not tick this box.

### Task group 3: Commit gateway and trailers

- [ ] E-04 Implement `CommitGateway` in `agent_workflows/commit_gateway.py` executing path-scoped `git commit -- <paths>` with appended `AW-Run: <run-id>` and `AW-Item: <id6>` trailers while respecting commit hooks and conventional commit syntax.
  - Depends on: E-01
  - Expected outcome: **THE ONE SURVIVING ITEM - but as a ~20-line EXTENSION, not a new module (PR-106/PR-107).** The TRAILERS are genuinely unbuilt: `AW-Run`/`AW-Item` re-verified this pass at ZERO matches across 556 searched files. The GATEWAY around them is not: `git_commit_helper.offer_commit` (`git_commit_helper.py:133`) already stages only explicit paths (`add -- <paths>`, `:225`), commits path-scoped (`commit -m msg -- <our_staged>`, `:245`), never passes `--no-verify` (so hooks run and a hook refusal is a real failure), never pushes, and snapshots the index BEFORE staging so a failure resets only its own paths (`:228`/`:246`). AGENTS.md names that exact function as the tooled path "immune by construction", and `aw commit` (`work_cmd.run_commit:439`) is its CLI. So `commit_gateway.py` would fork the one commit path the repository contract points every agent at (P8). CORRECT SHAPE: add a `trailers: Sequence[str] = ()` parameter to `offer_commit`, append `AW-Run: <run-id>` / `AW-Item: <id6>` after a blank line per Git trailer convention, thread it from `aw commit`, and test the formatting (including a multiline body and an existing-trailer block). Sequence AFTER `rununify` (parent OQ-03) so the runner wiring lands once. Original expected outcome: Commits are created only by the engine gateway, scoped to action-owned paths, with verifiable run/item trailers separated by a blank line at the end of the commit body.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). The trailer work is REAL and is this plan's only surviving contribution, but it is not executable from THIS plan: it declares the wrong deliverable (a new module rather than an extension of `git_commit_helper.py`), the wrong Scope-Paths, and depends on E-01, which must not be built. Re-author it in the successor. Do not tick this box.

### Task group 4: Runner integration

- [ ] E-05 Integrate worktree isolation, containment rollback, and commit gateway into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: **DO NOT BUILD AS WRITTEN (REPLAN, PR-103).** Edits BOTH runners, fighting APPROVED `rununify` (`5e4sb6`), whose charter is collapsing their duplication; parent-Set OQ-03 (blocking) owns the sequencing. Two further reasons it cannot proceed: the runners ALREADY execute items in confined worktrees (`oc_runipd.py:2120` allocates via `worktree_lease`, `:2447` tears down, `:2500` preserves on non-integration), so "runner executes items in confined worktrees" is already true; and the containment half depends on E-02, which resolved OQ-02 reassigns to approved `wtiso-03`. Original expected outcome: Runner executes items in confined worktrees, invokes commit gateway for lifecycle transitions, and executes containment on check failures.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blocked by approved-Set collision (`rununify`) and parent OQ-03. Do not tick this box.

### Task group 5: Test suite coverage and edge cases

- [ ] E-06 Create `tests/test_fault_containment.py` covering worktree allocation, baseline restoration on scope violation, quarantine bundle generation, abort classification, and commit trailer formatting.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: **CANNOT BE WRITTEN AS SPECIFIED (PR-108).** It tests five items that should not be built, and its first two named surfaces are already covered: worktree allocation and lease behavior are exercised by `tests/test_work_primitives.py` and `tests/test_ipd_set_executor.py` (both import `worktree_lease`), so a new module would fork that coverage. "Comprehensive coverage" is also unfalsifiable as an acceptance bar. Retarget onto the surviving residue only: trailer formatting, in or beside the existing `tests/test_git_commit_helper.py`. Original expected outcome: Full pytest suite passes with comprehensive fault containment and commit gateway coverage.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Do not tick this box.

- [ ] E-07 Add adversarial containment tests: pre-existing dirty file conflict, untracked file deletion safety, containment escalation on failed rollback, and trailer formatting with multiline commit bodies.
  - Depends on: E-06
  - Expected outcome: **PARTIALLY SALVAGEABLE, MOSTLY NOT (PR-108).** Two of its four cases are already owned elsewhere: "pre-existing dirty file conflict" is shipped as `oc_runipd.dirty_tree_overlap` (`:544`), which refuses integration when main's un-owned dirty paths overlap an incoming lane's changes; "untracked file deletion safety" is exactly APPROVED `wtiso-03` E-09/E-10's `unknown`-blocks-teardown case (its `test_unknown_blocks_teardown`). "Containment escalation on failed rollback" depends on E-02/E-03. Only the fourth case survives: trailer formatting with a multiline commit body - keep it, and add the adversarial cases the item omits (a body that already ends in a trailer block, and a body ending without a trailing newline). Original expected outcome: All adversarial containment tests assert correct containment receipts and fail-closed escalation.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Do not tick this box.

## Project conventions discovered (Step 0)

CORRECTED /plan-review 2026-08-30 pass 2 (PR-109/PR-110). The first bullet was FACTUALLY WRONG and pass
1 repeated it instead of checking it. This section is the root cause of E-01: the plan looked for a
lease manager, named the wrong module, concluded none existed, and proposed a new one.

- **WRONG, and the source of E-01's duplication:** `orchestrate_isolation.py` is NOT the worktree lease
  manager. `worktree_lease.py:4-16` states it "never creates a git worktree or session, and there is NO
  per-path exclusive-ownership lease" in it; `orchestrate_isolation` only ANALYZES parallel-lane
  eligibility and CARRIES a caller-supplied `worktree_path`. The actual canonical module is
  `agent_workflows/worktree_lease.py` (`allocate_worktree:70`, `teardown_worktree:106`,
  `LeaseTable:144`, `assert_worker_scope:214`), consumed by `oc_runipd.py:480`, `agy_runipd.py:590`, and
  `work_cmd.py:250`.
- **MISSED, and the source of E-04's duplication:** `git_commit_helper.offer_commit`
  (`git_commit_helper.py:133`) is the single canonical path-scoped commit path (staged-paths-only, never
  `--no-verify`, never push, index snapshot before staging), named in AGENTS.md as the tooled path
  "immune by construction" and exposed as `aw commit`.
- **WRONG PATH:** worktrees live at `.aw/worktrees/<lane>` (`worktree_lease.WORKTREES_SUBDIR:32`,
  `.gitignore:73`, `ipd_set_plan.py:474`, `check_engine.py:1007`), NOT `.aw/state/worktrees/`, which
  greps to ZERO hits.
- **MISSED:** `run_ledger_schema.LANE_OUTCOMES` (`:112`) is a CLOSED outcome vocabulary already
  containing `unknown_outcome`; `worktree_lease.LeaseConflictError` (`:39`) is the existing
  ownership-conflict signal. E-03 must emit these, not invent `ownership_conflict`.
- ACCURATE: commit trailers follow Git trailer conventions (`Key: Value` at the end of the body,
  separated by a blank line).
- ACCURATE BUT INCOMPLETE: quarantine bundles would live under
  `.aw/records/runs/<run-id>/quarantine/<item-id6>/`. Note that `.aw/records/runs/` is GITIGNORED
  (`.aw/.gitignore:15`) as "box-local, ephemeral working material", so such a bundle is not a durable
  tracked record; the plan should not imply otherwise.

## Findings

CORRECTED /plan-review 2026-08-30 pass 2 (PR-111). The first finding is FALSE as stated, and it is the
premise E-02 rests on.

- **FALSE:** "the runner aborts without cleanly isolating and rolling back". The runner does NOT abort,
  and it DOES isolate: the item ran in an isolated `.aw/worktrees/<id6>` worktree on an `aw/lane/<id6>`
  branch all along (`oc_runipd.py:2120`), so an out-of-scope edit lands on the lane branch and the MAIN
  tree is untouched. Spec 25kzda 5.2 states this outcome explicitly: "A failed item therefore normally
  has nothing to undo in the main worktree." What the runner does instead is PRESERVE the lane
  (`oc_runipd.py:2500-2530`, `worktree-preserved` event) by deliberate policy. The real gap is narrower
  than the finding claims: there is no evidence BUNDLE and no `contained: true` receipt. Restating the
  gap that way is what let OQ-02 be resolved from repository evidence.
- TRUE but already owned: "a failed containment must escalate rather than risk corrupted state". This is
  the fail-closed principle the shipped code already applies (`worktree_lease` raises rather than
  partially claiming; `oc_runipd.integrate_lane_branch:576` refuses on a contaminated base via
  `dirty_tree_overlap:544`; `ipd_lifecycle` classifies ambiguous evidence `unknown-outcome`). The
  missing piece is a single named CLASSIFIER, not the principle.
- MISSING FROM THE SURVEY: the plan never checked `worktree_lease.py`, `git_commit_helper.py`, or the
  approved `wtiso-03` retention gate - the three artifacts that between them already own E-01, E-04's
  gateway, and E-02's teardown decision. That omission, not a craft defect, is why this plan is REPLAN.

## Proposed changes (ordered, validatable)

SUPERSEDED /plan-review 2026-08-30 pass 2 (PR-103..PR-108). Step 1 duplicates `worktree_lease.py`; step 2
contradicts shipped teardown policy and approved `wtiso-03`; step 4 forks `git_commit_helper.py`; step 5
fights approved `rununify`; step 6 forks existing lease coverage.

The replacement shape, in order, and it is ONE change plus TWO decisions:

1. **Honor resolved OQ-02:** teardown/retention belongs to approved `wtiso-03` (`rchpms`) per the
   `wtiso` orchestrator (`bl9q3d:87`, `:91`, `:97`). Anything in task group 2 must EXTEND
   `lane_status.harvest_and_teardown_gate`, never fork or override it.
2. **Decide OQ-03** (blocking, inherited from the parent Set): sequence against `rununify`.
3. **Add trailer support to the SHIPPED commit path.** A `trailers: Sequence[str] = ()` parameter on
   `git_commit_helper.offer_commit`, appending `AW-Run: <run-id>` / `AW-Item: <id6>` after a blank line
   per Git trailer convention; threaded through `aw commit` (`work_cmd.run_commit`). No new module.
4. **Test it** in or beside `tests/test_git_commit_helper.py`: single-line body, multiline body, a body
   that already ends in a trailer block, and a body with no trailing newline.
5. **As an EXTENSION only (resolved OQ-02):** add the quarantine evidence bundle and `contained: true` receipt as an
   EXTENSION of `wtiso-03`'s classifier/harvest gate, and emit the SHIPPED
   `run_ledger_schema.LANE_OUTCOMES` values rather than a new `ownership_conflict`.

Original sequence, retained for the record:

1. ~~Implement `WorktreeContext` in `worktree_containment.py` (E-01).~~ Shipped as `worktree_lease.py`.
2. ~~Implement 7-step `contain_item_failure()` transaction and quarantine bundles (E-02).~~ Teardown/retention is approved `wtiso-03`'s (resolved OQ-02); only an evidence-bundle EXTENSION survives.
3. Implement 6-class `ABORT RUN` classifier and escalation (E-03) - substance keepable, vocabulary must be the shipped one.
4. ~~Implement `CommitGateway` with `AW-Run:`/`AW-Item:` trailers (E-04).~~ Trailers KEEP; gateway is `offer_commit`.
5. ~~Integrate with runner dispatch loop (E-05).~~ Defer behind `rununify`.
6. ~~Cover with comprehensive unit and adversarial tests in `test_fault_containment.py` (E-06, E-07).~~ Retarget to the trailers.

## Deferred / out of scope (with reason)

- **Skeptical verifier session launch**: Deferred to child plan `detrun-05` (`7f7782`).
- **Ledger hash chaining**: Deferred to child plan `detrun-05` (`7f7782`).

## Scope check

CORRECTED /plan-review 2026-08-30 pass 2 (PR-101..PR-108).

- Over-scope: SEVERE. Two new modules where canonical homes already exist.
  `worktree_containment.py` forks `worktree_lease.py`'s allocator, lease table, and worker-path fencing;
  `commit_gateway.py` forks `git_commit_helper.offer_commit`, the path the repository contract itself
  names as the commit path to use. E-05 edits both runners against approved `rununify`. E-06 forks lease
  coverage that `tests/test_work_primitives.py` and `tests/test_ipd_set_executor.py` already carry. The
  declared `Scope-Paths` reflects this: 3 of its 6 entries (`worktree_containment.py`,
  `commit_gateway.py`, `tests/test_fault_containment.py`) are files that should not exist, and it names
  `orchestrate_isolation.py`, which the plan cites for a capability that module does not have.
- Under-scope: no reconciliation with the APPROVED `wtiso` Set that owns this exact territory - in
  particular `wtiso-03` (`rchpms`), whose E-09/E-10 retention classifier and `unknown`-blocks-teardown
  gate DIRECTLY CONTRADICT E-02 steps 4/7, and `wtiso-07` (`1o4eif`), which owns the typed host
  capability contract that the spec's `isolated_worktree`/`commit_gateway` capabilities belong to. Also
  missing: recognition that the runner ALREADY isolates in `.aw/worktrees/<id6>` and already preserves
  rather than discards, that `.aw/records/runs/` is gitignored so a quarantine bundle is not a durable
  record, and that `run_ledger_schema.LANE_OUTCOMES` is a closed set the escalation vocabulary must
  respect.
- Original text, retained for the record: "Over-scope: none. Strictly implements worktree isolation,
  containment, and commit gateway mechanics. Under-scope: none. Covers all 7 steps of the containment
  transaction, quarantine bundles, and the 6 abort classes."

## Required tests / validation

CORRECTED /plan-review 2026-08-30 pass 2 (PR-108). Both items were unachievable or misleading as written.

- ~~`python3 -m pytest tests/test_fault_containment.py`~~ - the module does not exist and should not be
  created; its first two surfaces are already covered by `tests/test_work_primitives.py` and
  `tests/test_ipd_set_executor.py`.
- ~~Test demonstrating out-of-scope change quarantined and restored with independent item succeeding~~ -
  not achievable as stated: "restored" presumes the E-02 teardown policy that resolved OQ-02 assigns to approved `wtiso-03`, and
  the shipped behavior is to PRESERVE the lane, not restore-and-remove it. Written literally, this test
  would assert a regression against `oc_runipd.py:2500`.
- The honest bar for the replacement: the full suite at no-worsening against a FRESHLY MEASURED
  baseline, with the `git rev-parse HEAD` it was measured at pasted. Do NOT claim `aw check plans`
  passes: measured this pass at HEAD `32cd5495` it exits with 232 findings, essentially all
  `check.lifecycle-transition-invalid` and `check.scope-drift` owned by other Sets. Plus a test proving
  the trailers are appended after a blank line on a multiline body, and a test proving
  `git_commit_helper.offer_commit` is CALLED rather than reimplemented.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 4.1, 4.2, 5.1, and 5.7.
- Documents commit trailers and fault containment in `.aw/records/plans/README.md`.

## Open questions

### OQ-01: Does containment delete untracked files created by other processes?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 4.1
- Resolution or deferral rationale: RESOLVED against the spec, BUT THE ANSWER IS CONTESTED IN-TREE
  (caveat added /plan-review 2026-08-30 pass 2, PR-104). The spec answer is accurate as a reading of
  25kzda 4.1 step 4. However the question it asks is the WRONG one: the live dispute is not whether
  containment deletes ANOTHER process's untracked files, it is whether containment may delete the ITEM'S
  OWN untracked files at all. Approved `wtiso-03` (`rchpms`) E-09/E-10 says an untracked file it cannot
  CLASSIFY (`unknown`) must BLOCK teardown and preserve the lane, and explicitly forbids treating
  ignored files as disposable; shipped `oc_runipd.py:2500` already preserves. "Proven to have been
  created by this item" is precisely the proof `wtiso-03`'s classifier exists to adjudicate. Superseded in practice by resolved OQ-02.

### OQ-02: Is lane teardown-vs-preserve owned by approved `wtiso-03`, or by a 25kzda containment transaction?

- Blocking: yes
- Status: resolved
- Owner: resolved from the APPROVED `wtiso` orchestrator `bl9q3d`
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE (/plan-review pass 2, NEW). Raised
  because THREE policies claim one decision: (1) SHIPPED `oc_runipd.py:2500-2530` preserves a
  non-integrated lane on purpose ("forward-progress rule: never discard work"), recording
  `preserved_worktree` + a `worktree-preserved` event; (2) APPROVED `wtiso-03` (`rchpms`) E-09/E-10 adds
  `lane_status.classify_output` + `harvest_and_teardown_gate`, where an `unknown` untracked file sets
  `teardown_authorized == False`; (3) this plan's E-02 steps 4/7 restore to baseline, delete
  item-created untracked paths, and tear the worktree down.
  **The approved `wtiso` orchestrator already answers this, so it is not a maintainer question.**
  `20260828-wtiso-00-bl9q3d-...ipd.md:91` assigns completion criterion 15 - "Removing a lane is always
  preceded by a durable event proving its content was integrated, abandoned, or preserved" - to
  `[owner: rchpms teardown gate + 2c122z durable events]`, and `:87` assigns criterion 7's
  "unknown ignored files PREVENT teardown" to `[owner: rchpms ... unknown-blocks-teardown]`. The same
  plan's Cross-IPD validation (`:97`) states the binding no-drift rule verbatim: `lane_status.py` is the
  ONE predicate library and "If a later child needs a predicate the module lacks, it EXTENDS
  `lane_status.py`; it does not fork a parallel rule implementation."
  THEREFORE: teardown/retention is owned by `rchpms` (with durable events from `2c122z`). A 25kzda
  containment transaction is legitimate ONLY as an EXTENSION of `lane_status.harvest_and_teardown_gate`
  that adds the evidence BUNDLE and the `contained: true` receipt; it MUST NOT delete anything the gate
  would preserve, and MUST NOT introduce a second classification or teardown rule. E-02 as written
  violates all three clauses, which is why it is `blocked` rather than repairable in place.

### OQ-03: Must the trailer work be sequenced after `rununify`?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN (/plan-review pass 2). Inherited verbatim from parent Set
  `detrun` (`r4mbcw`) OQ-03 and recorded here because E-05 is this plan's own item. `rununify` (`5e4sb6`,
  approved) exists to collapse the duplication between `oc_runipd.py` and `agy_runipd.py`; E-05 adds new
  code to both. Recommendation: `rununify` first, then wire trailers once into the unified runner. The
  trailer change to `git_commit_helper.offer_commit` itself is runner-independent and could land earlier;
  only the RUNNER WIRING is gated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`worktree_lease.py`, `git_commit_helper.py`), contradicts approved `wtiso-03`'s teardown gate, or collides with approved `rununify`; collecting this evidence would mean proving a duplicate or a regression was built.** Original required evidence: Python test showing worktree creation, lease acquisition, and lease release.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`worktree_lease.py`, `git_commit_helper.py`), contradicts approved `wtiso-03`'s teardown gate, or collides with approved `rununify`; collecting this evidence would mean proving a duplicate or a regression was built.** Original required evidence: Test session showing out-of-scope mutation rolled back to baseline with `contained: true` and quarantine bundle written to disk.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`worktree_lease.py`, `git_commit_helper.py`), contradicts approved `wtiso-03`'s teardown gate, or collides with approved `rununify`; collecting this evidence would mean proving a duplicate or a regression was built.** Original required evidence: Test demonstrating only the 6 fatal classes aborting the run, with other failures cascading item-locally, and escalation on failed restoration.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`worktree_lease.py`, `git_commit_helper.py`), contradicts approved `wtiso-03`'s teardown gate, or collides with approved `rununify`; collecting this evidence would mean proving a duplicate or a regression was built.** Original required evidence: Git log of test commit showing correctly formatted `AW-Run:` and `AW-Item:` trailers and path-scoped contents.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`worktree_lease.py`, `git_commit_helper.py`), contradicts approved `wtiso-03`'s teardown gate, or collides with approved `rununify`; collecting this evidence would mean proving a duplicate or a regression was built.** Original required evidence: End-to-end runner test with a simulated scope violation verifying containment and subsequent queue progress.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`worktree_lease.py`, `git_commit_helper.py`), contradicts approved `wtiso-03`'s teardown gate, or collides with approved `rununify`; collecting this evidence would mean proving a duplicate or a regression was built.** Original required evidence: `pytest tests/test_fault_containment.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`worktree_lease.py`, `git_commit_helper.py`), contradicts approved `wtiso-03`'s teardown gate, or collides with approved `rununify`; collecting this evidence would mean proving a duplicate or a regression was built.** Original required evidence: Adversarial test suite asserting clean rollback and escalation on simulated dirty state conflicts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30, reaffirmed pass 2 on stronger evidence
with a narrower residue).** Do NOT execute and do NOT approve. All 7 E-items are `Execution state:
blocked` with an execution note, and all 7 V-items' evidence is NOT TO BE COLLECTED, so nothing here can
be ticked. An executor reaching this gate must STOP and report.

PASS-2 CORRECTION TO MY OWN EARLIER EVIDENCE: pass 1 rejected E-01 by citing
`orchestrate_isolation.py` as "the canonical worktree lease manager", repeating this plan's own Step-0
bullet without checking it. That is FALSE (`worktree_lease.py:4-16` says that module "never creates a git
worktree or session" and holds "NO per-path exclusive-ownership lease"). The correct citation is
`worktree_lease.py`, which rejects E-01 more completely, not less. Do not rely on the pass-1 citation.

Open questions: THREE, ONE of them still BLOCKING and needing YOU:
- OQ-03 (blocking, YOURS): sequence the runner wiring after `rununify` (`5e4sb6`)? Recommendation: yes.
  This is a scope/priority call the repository cannot make; it also decides how long this plan's
  `Blocks-Release: next` gate is delayed. Inherited from parent Set OQ-03.
- OQ-02 (was blocking, now RESOLVED from repository evidence, not from you): the approved `wtiso`
  orchestrator `bl9q3d` already assigns teardown/retention to `rchpms` (`:87`, `:91`) and binds later
  work to EXTEND `lane_status.py` rather than fork it (`:97`). Containment may only add the evidence
  bundle and receipt on top of that gate.
- OQ-01: accurate against the spec, but it asks the wrong question; superseded by OQ-02's finding.

Retirement: retire with the parent Set `detrun` (`r4mbcw`). Prepend a `RETIRED 2026-08-30: <reason>;
superseded by <path/commit>` header and `git mv` to `.aw/records/plans/superseded/`. Do NOT file under
`executed/`; nothing was implemented.

Release gate: carries `- Blocks-Release: next`. Re-gate the surviving residue onto its successor, or have
the maintainer clear the gate explicitly.

SURVIVING RESIDUE, now ONE item rather than three:

1. The `AW-Run: <run-id>` / `AW-Item: <id6>` commit trailers. Re-verified this pass at ZERO matches across
   556 searched files. Correct shape: a `trailers: Sequence[str] = ()` parameter on the SHIPPED
   `git_commit_helper.offer_commit`, appended after a blank line per Git trailer convention, threaded
   through `aw commit` (`work_cmd.run_commit`), plus tests for a multiline body, a body that already ends
   in a trailer block, and a body with no trailing newline. Not a new module.

Conditionally salvageable, as an EXTENSION of `lane_status.harvest_and_teardown_gate` only (resolved
OQ-02): the quarantine evidence bundle and the
`contained: true` receipt, authored as an EXTENSION of `wtiso-03`'s `harvest_and_teardown_gate`; and the
6-class abort taxonomy from spec 25kzda 4.1, emitting the SHIPPED `run_ledger_schema.LANE_OUTCOMES`
values.

Explicit prohibitions for the replacement: do NOT create `worktree_containment.py` (forks
`worktree_lease.py`'s allocator, `LeaseTable`, and `assert_worker_scope`); do NOT create
`commit_gateway.py` (forks `git_commit_helper.offer_commit`, the path AGENTS.md names as the one immune by
construction); do NOT write worktrees under `.aw/state/worktrees/` (the constant is
`worktree_lease.WORKTREES_SUBDIR = ".aw/worktrees"`); do NOT delete or force-teardown a lane's untracked
files (resolved OQ-02: approved `wtiso-03` owns that gate and an `unknown` file must PREVENT teardown); do NOT introduce the reason code `ownership_conflict`
(`LANE_OUTCOMES` is a closed set and `worktree_lease.LeaseConflictError` is the existing signal); and do
NOT edit `oc_runipd.py`/`agy_runipd.py` before `rununify` lands.

Scope fence for the replacement: `agent_workflows/git_commit_helper.py`, `agent_workflows/work_cmd.py`,
and `tests/test_git_commit_helper.py`. Both runners, `cli.py`, and the `wtiso` surfaces are actively
contended in this SHARED CHECKOUT: verify `git diff --cached --name-only` before every commit and unstage
anything not yours. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do
NOT claim `aw check plans` passes - measured at HEAD `32cd5495` it exits with 232 findings, essentially all
`check.lifecycle-transition-invalid` and `check.scope-drift` owned by other Sets; the bar is no-worsening
against a fresh baseline. Do not write a validation that presupposes its own feature or that asserts a
regression against shipped behavior, as the original "quarantined and restored" item did.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never
`git add -A`, never push. Post-gate lifecycle is `aw ipd finalize`, never a hand-move. Do not create or
push a tag or release.
