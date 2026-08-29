# IPD: Runner graceful-quit protocol: adopt spec c4gd2h

- Date: 2026-08-29
- Kind: orchestrator
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h (approved 2026-08-29) defines a graceful-quit protocol for `aw oc run` / `aw agy run`, which today has NO graceful stop: SIGTERM makes the driver print `Terminated` and exit while its child `opencode` is reparented to init and keeps writing the tree, `driver.lock` is left holding a dead PID (`run_lock`, oc_runipd.py:738-756, never unlinks the lock file), and the working tree is left mid-edit. The driver installs NO signal handlers of its own (verified: the only signal references in oc_runipd.py are inside `terminate_process`, :1632-1670). This orchestrator sequences the 6-child adoption of spec c4gd2h and closes backlog kjzlgw.
- Scope: ORCHESTRATOR - authors NO product code. Its own execution work is (E-01) whole-Set verification only. The children carry all implementation. This plan owns the child table + dependency chain, the shared anti-greenwash execution contract every child inherits, the Set completion criteria, and the cross-IPD no-drift checks. It cites spec c4gd2h as binding and each child names the spec requirement ids (R1-R23) and acceptance criteria (A1-A10) it implements.
- Scope-Paths: .aw/records/plans/pending/20260829-runstop-00-zpbx7o-runner-graceful-quit-protocol-adopt-spec-c4gd2h.ipd.md, .aw/records/walkthroughs/
- Item-Dependencies: none
- Status: approved
- Set: runstop
- Order: 0
- Highest E allocated: 01
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: zpbx7o
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-008. Found the Set built on two unverified premises about the existing code and recorded both with evidence in the owning orchestrator: (1) an automatic requeue-and-resume path ALREADY exists (`run_queue` -> `reconcile_interrupted` -> `requeue_interrupted`, oc_runipd.py:2474-2476, :2448-2464) that flips every interrupted item back to `queued` with no operator gate, so Phase 4's spec-R19 resume refusal is a MODIFICATION of that path rather than new code beside it, and two existing tests pin today's behavior and must be consciously updated; (2) `fcntl` is imported unconditionally at driver top level (oc_runipd.py:17, agy_runipd.py:18), verified empirically to make the module unimportable without it, so spec A10's "portable subset still provides level 1" cannot hold on Windows while CI does run windows-latest - raised as new BLOCKING OQ-02 since `71vjbn` E-07 and its own Deferred section contradict each other, and `wtiso` Phase 5 already owns `platform_lock` (P8). Fixed a false Scope-check claim: A8 (the SIGKILL-bypass criterion proving the shared routine covers crash, spec R5's other half) is claimed by NO child; E-01 now owns verifying it or recording it UNVERIFIED. Corrected the completion criteria's validation command: a bare `python -m pytest -q` silently deselects the `slow` marker (pyproject.toml:122), which is exactly where this Set's real-subprocess signal tests live; now `make test-all`. Corrected a stale factual claim that backlog kjzlgw is `open` (it is already `graduated`, keeping its release gate) and recorded the verified spec-transition mechanics (`approved -> implemented` is refused; needs `implementing` first plus resolvable `--evidence`). Added `.aw/records/walkthroughs/` to Scope-Paths, since E-01 had no legal path to write its own verification record. Added CID-4 (refusal wired into the real requeue path) and CID-5 (no second lock abstraction or reaper), and hardened CID-1/CID-3 after verifying the two drivers carry byte-identical duplicate `terminate_process` copies, which a per-file "one cleanup routine" check would pass.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Adopt spec c4gd2h across a 6-child, dependency-ordered migration that gives `aw oc/agy run` four stop levels over ONE unconditional clean-shutdown invariant, so no stop ever leaves an orphaned agent process, a stale lock, an incoherent ledger, or a contaminated tree. Every child is authored greenwash-proof: acceptance is a pasted command result or an observation of real process/git/filesystem state, never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: whole-Set verification (orchestrator authors no code)

- [ ] E-01 After ALL children (runstop-01..06) are in `executed/`, run the whole-Set verification: confirm every child's V-items were satisfied with pasted evidence, confirm spec c4gd2h acceptance criteria A1-A10 hold against the real repo, and confirm no cross-IPD drift (CID-1..CID-5). Write the verification record to `.aw/records/walkthroughs/` (declared in `Scope-Paths`; without that path E-01 had no legal place to write its own output). Author no product code here. Note that A8 is NOT owned by any child (see the child table's A8 row): E-01 must verify it directly or record it as UNVERIFIED with the reason, never silently drop it.
  - Depends on: none
  - Expected outcome: a single verification record at the declared `.aw/records/walkthroughs/` path demonstrating each of A1-A10 with pasted command evidence (A8 verified here or explicitly recorded UNVERIFIED); any failing criterion blocks the Set (this orchestrator stays not-executed).
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Depends on | Spec ids |
|---|---|---|---|---|
| 00 | zpbx7o | Orchestrator (this) | - | R1-R23, A1-A10 |
| 01 | 2ouj70 | Phase 0: the ONE shared clean-shutdown routine (reap tree, release lock, coherent ledger, quarantine tree) + characterization tests pinning today's broken behavior | - | R1-R6, R23, A9 |
| 02 | gq6m2u | Phase 1: durable, idempotent, monotonic stop-request flag + the cooperative checkpoint poll | executed:2ouj70 | R7-R9, R11 |
| 03 | 1qxuke | Phase 2: levels 1-2 (stop-after-call, stop-after-set) at between-turn checkpoints | executed:gq6m2u | R20, A1, A4 |
| 04 | foi1b3 | Phase 3: level 3 (stop-now) at the next OBSERVED safe checkpoint, KNOWN disposition | executed:1qxuke | R10, R18, A3 |
| 05 | m0z0ti | Phase 4: level 4 (stop-now-force), `unknown_outcome`, resume refusal | executed:foi1b3 | R18-R19, R21-R22, A2, A6 |
| 06 | 71vjbn | Phase 5: trigger UX (escalating SIGINT, SIGTERM) + `aw oc/agy run stop <run-id>` | executed:m0z0ti | R12-R17, A5, A7, A10 |
| - | (unowned) | **A8 (SIGKILL bypass -> the NEXT run's reconciliation detects the stale lock and orphaned state) is claimed by NO child.** Verified 2026-08-29: `grep -n '\bA8\b'` over all six children returns nothing. A8 is the criterion proving the shared routine covers CRASH as well as stop, so dropping it would let the Set pass while spec R5's crash half went untested. E-01 verifies it directly or records it UNVERIFIED with the reason. | - | A8 |

Why this order: the invariant (Phase 0) must exist before any level can end in it; the flag+poll (Phase 1) must exist before any level can be requested; levels are added cheapest-first (between-turn, then turn-internal, then interrupt); the trigger UX lands last so it wires to all four levels at once instead of being rewritten per level.

Sequencing dependency OUTSIDE this Set: the out-of-repo stop-flag location (spec OQ-03) requires `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`). Phase 1 therefore resolves the flag path through the shared accessor rather than hardcoding a root, and records that the out-of-repo guarantee is fully realized only once `wtiso` lands. This Set does not depend on `wtiso` for correctness on a shared checkout.

### Two pre-existing repository facts every child MUST build on (verified 2026-08-29, not assumed)

Both were missing from the children as authored, and each would have caused a child to be executed against a false premise. They are recorded HERE, in the owning orchestrator, and cross-referenced by CID-4/CID-5 rather than being duplicated per child (P8).

1. **An automatic requeue-and-resume path ALREADY EXISTS and structurally conflicts with spec R19.** `run_queue` calls `reconcile_interrupted(...)` then `requeue_interrupted(...)` unconditionally on EVERY start/resume (`oc_runipd.py:2474-2476`; `agy_runipd.py:2551-2552`), and `requeue_interrupted` flips every `interrupted` item straight back to `queued` with `recovery_next = True` (`oc_runipd.py:2448-2464`) with NO operator gate. `reconcile_interrupted` (`oc_runipd.py:2402`) is also the EXISTING crash-reconciliation routine, and it currently promotes an item to `executed` purely from `plan_bucket(path) == "executed"` (:2423). Consequences the children must honor rather than rediscover: (a) Phase 4's "refuse to blindly resume an `unknown_outcome` item" (`m0z0ti` E-04) is a MODIFICATION of this existing auto-requeue path, not new code beside it, so `m0z0ti` must make `requeue_interrupted` refuse-or-skip the indeterminate item instead of adding a second gate that the existing call already bypassed; (b) spec R5's "ONE cleanup routine shared by all four levels AND crash recovery" means `reconcile_interrupted` is that pre-existing crash half, so Phase 0 must reconcile with it rather than introduce a parallel routine; (c) two existing tests pin the current auto-requeue behavior (`tests/test_oc_runipd.py:421-427`, `:1043`) and MUST be consciously updated, not deleted, when the refusal lands.
2. **`fcntl` is imported UNCONDITIONALLY at driver module top level, so the A10 "portable subset" is unreachable as spec'd without a lock change this Set declares out of scope.** `oc_runipd.py:17` and `agy_runipd.py:18` do a bare `import fcntl`; verified empirically that with `fcntl` masked, `import agent_workflows.oc_runipd` raises `ModuleNotFoundError: No module named 'fcntl'`, i.e. the module cannot even LOAD on Windows, so "level 1 and the out-of-band `stop` still work" cannot hold there. Meanwhile CI genuinely runs `windows-latest` (`.github/workflows/tests.yml:24`, `:72`) with no Windows skip guard in the driver tests. `71vjbn` E-07 as authored only monkeypatches `sys.platform` (which does NOT exercise the real import failure) while its own Deferred section rules out replacing `fcntl`; those two statements cannot both stand. Note also that a cross-platform lock abstraction is ALREADY owned elsewhere: `wtiso` Phase 5 (`2c122z`) explicitly plans `platform_lock` replacing raw `fcntl` plus a Windows Job Object process-tree kill. This Set therefore MUST NOT invent a second lock abstraction (P8). See OQ-02 for the human decision on how A10 is honestly satisfied.

## The shared anti-greenwash execution contract (every child inherits this verbatim)

Acceptance for every `V-*` item in this Set is a PASTED command result or an observation of real process/git/filesystem state, never an agent's prose claim:

- A process-reaping claim MUST be proven by a process-table observation (no descendant of the driver alive, nothing reparented to init), not by asserting the code called a kill.
- A lock-release claim MUST be proven by the lock being absent or re-acquirable, not by reading code.
- A ledger-coherence claim MUST be proven by parsing the ledger after the stop.
- A tree-cleanliness claim MUST be proven by `git status --porcelain` output.
- No test may use a wall-clock sleep to define a checkpoint (spec R10).
- No test may spawn a real network-using agent; the child is a controllable local fake.

## Completion criteria (the whole Set is done only when)

- All six children are in `.aw/records/plans/executed/` with every `V-*` carrying real observed evidence.
- Spec c4gd2h acceptance criteria A1-A10 all demonstrably hold, with pasted output; A8 verified by E-01 directly or explicitly recorded UNVERIFIED with its reason (never silently dropped).
- CID-1..CID-5 (below) pass.
- The FULL suite is green via `make test-all` (i.e. `python -m pytest tests/ -m ''`), NOT a bare `python -m pytest -q`. This matters concretely: the default `addopts` in `pyproject.toml:122` is `-q -n auto --dist=worksteal -m 'not slow'`, so a bare `python -m pytest -q` SILENTLY DESELECTS the `slow` subprocess/integration tests. Since every stop level is validated by spawning a real driver subprocess and delivering real signals, this Set's own tests are precisely the class the default run skips. Each child inherits this: a bare `pytest -q` is not acceptable evidence for this Set.
- Spec `c4gd2h` is moved to `implemented` with cited evidence (not before). Mechanics verified 2026-08-29: `aw spec set implemented c4gd2h` is REFUSED from `approved` (actual output: `FAIL Validation error ...: Illegal spec transition approved -> implemented`), so the spec must first go `approved -> implementing` (child `2ouj70` already owns that transition) and the final call requires a resolvable `--evidence` citation to an executed IPD (`agent_workflows/specs.py:517-521`, `_evidence_resolvable` at :908).
- Backlog `kjzlgw` is closed via HANDOFF. Correction (verified 2026-08-29): the item is ALREADY `graduated`, not `open`, at `.aw/records/backlog/graduated/20260827-runnerstop-01-kjzlgw-...backlog.md`, and `graduated` is explicitly a legitimate release-gated state that keeps `Blocks-Release: next` and maps to `active` in `aw attention` (`check_engine.evaluate_blocking_close`). So no gate is currently dropped; the remaining step is the `graduated -> done` close once the code is written and validated, which passes the close-legitimacy predicate via HANDOFF because this plan carries both `From-Backlog: kjzlgw` and the same `Blocks-Release: next`.

## Cross-IPD validation

- CID-1 Exactly ONE cleanup routine exists and all four levels plus crash recovery call it (spec R5, A9). Prove with an AST or import-graph check scoped to `agent_workflows/`, NOT a text grep (the guard test itself contains the symbol).
- CID-2 No child introduced a second stop-flag path or a raw `<repo>/.aw/state` construction (spec OQ-03; the `wtiso` Phase 3 AST guard forbids it).
- CID-3 Both drivers (`oc_runipd.py`, `agy_runipd.py`) expose the same four levels and the same `stop` verb; no level exists in one driver only. Note the two drivers currently carry BYTE-IDENTICAL duplicate `terminate_process` implementations (`oc_runipd.py:1632-1670` vs `agy_runipd.py:1720-1757`; verified by `diff`, differing only in a docstring line), so a CID-1 check that merely counts "one cleanup routine per file" would pass while two copies exist. CID-1's AST/import-graph check MUST be repo-wide across `agent_workflows/`, not per-file.
- CID-4 The `unknown_outcome` resume refusal is wired INTO the existing auto-requeue path, not beside it: assert `requeue_interrupted` (`oc_runipd.py:2448`, `agy_runipd.py:2525`) cannot return an `unknown_outcome` item as requeued, driving it through the real `run_queue` entry (`oc_runipd.py:2474-2476`) rather than by calling the refusal helper directly. Also assert the two pre-existing tests that pin today's auto-requeue (`tests/test_oc_runipd.py:421-427`, `:1043`) were consciously UPDATED, not deleted.
- CID-5 No child introduced a second lock abstraction or a second process-tree reaper. `platform_lock` and the Windows Job Object kill are owned by `wtiso` Phase 5 (`2c122z`); this Set consumes or defers to them (P8). Prove with an AST/import check scoped to `agent_workflows/`.

## Deferred / out of scope (with reason)

- Unifying `oc_runipd.py` and `agy_runipd.py` (backlog `dhuape`): children land symmetrically in both, but de-duplication is a separate concern.
- Crash-recovery redesign: consumed from research `ud28vy`, not re-specified (spec non-goal; GUIDING_PRINCIPLES P8 single source of truth).
- Worktree isolation (Set `wtiso`): a sequencing dependency for the flag location, not work this Set performs.
- Pause/resume-mid-turn: explicit spec non-goal. A stopped turn is stopped, not suspended.
- `stop --all` across concurrent runs (spec OQ-02, non-blocking): ship per-run-id first.

## Scope check

- Over-scope: none. The orchestrator writes no product code.
- Under-scope: PARTIALLY, and now recorded rather than denied. The original claim "every acceptance criterion A1-A10 by at least one child" was FALSE: **A8 is claimed by no child** (verified by grep over all six children), so E-01 now owns verifying it or recording it UNVERIFIED. Every spec requirement R1-R23 IS claimed by exactly one child. Two further under-scope gaps are now recorded above as the "two pre-existing repository facts" (the existing auto-requeue path that spec R19 must modify, and the unconditional `fcntl` import that blocks A10) and gated by CID-4/CID-5 plus OQ-02.

## Required tests / validation

Whole-Set verification (E-01), performed only after all six children are `executed/`:

- Re-run each child's validation commands; confirm the pasted evidence in each child's V-items matches a fresh run.
- Demonstrate spec c4gd2h A1-A10 against the real repo with pasted output (A8 verified here or recorded UNVERIFIED with its reason).
- Run CID-1..CID-5.
- `make test-all` (`python -m pytest tests/ -m ''`) green overall. A bare `python -m pytest -q` is NOT sufficient: it deselects the `slow` marker (`pyproject.toml:122`), which is exactly where this Set's real-subprocess signal tests live.
- Confirm the whole Set ran on a POSIX host and state plainly which A10 rows were verified on Windows and which were not, per OQ-02's resolution.

## Open questions

### OQ-01: Should the `stop` verb also be exposed as a top-level `aw run stop`?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: `runstop-06` implements `aw oc run stop` and `aw agy run stop` per spec R14. A unified `aw run stop` presupposes the runner unification in backlog `dhuape`; deferred to that work rather than pre-building a facade here.

### OQ-02: How is spec A10 (the portable subset) honestly satisfied, given that the drivers cannot import at all on Windows?

- Blocking: yes
- Status: open
- Owner: human maintainer
- Context: This decides whether `71vjbn` E-07 is executable as written or must be rescoped. Spec A10 requires that "on a platform without POSIX signal semantics, the documented portable subset still provides level 1 and the out-of-band `stop` command, and the unsupported triggers fail loudly rather than silently doing nothing." That cannot hold as written: `oc_runipd.py:17` and `agy_runipd.py:18` do an unconditional `import fcntl`, and with `fcntl` masked `import agent_workflows.oc_runipd` raises `ModuleNotFoundError`, so on Windows the module does not load at all and NOTHING works, portable subset included. CI does run `windows-latest` (`.github/workflows/tests.yml:24`). `71vjbn` E-07 only monkeypatches `sys.platform`, which does not exercise the real import failure, while `71vjbn`'s own Deferred section rules out replacing `fcntl`; those two statements are mutually inconsistent. A cross-platform lock is ALREADY owned by `wtiso` Phase 5 (`2c122z`: `platform_lock` + a Windows Job Object process-tree kill), so this Set inventing one would duplicate it (P8). The candidate resolutions are: (A) narrow A10 for this Set to a DOCUMENTED POSIX-only limitation, rescoping E-07 to assert the honest failure mode and forbidding any claim of a working Windows subset; (B) make this Set depend on `wtiso` Phase 5 so A10 can be genuinely satisfied, which serializes runstop behind eight more plans; or (C) keep A10 as written and accept that `71vjbn` E-07 must implement a Windows lock primitive, contradicting its current Deferred entry. Until this is decided, `71vjbn` is NOT safely executable and the Set is NO-GO.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a pasted whole-Set verification record, written at the declared `.aw/records/walkthroughs/` path, showing (1) for each spec acceptance criterion A1-A10 the command run and its actual output, with A8 either verified or explicitly recorded UNVERIFIED plus its reason; (2) a per-child table confirming each child's V-items carry real observed evidence (prose-only evidence fails this item); (3) pasted output for CID-1 through CID-5, where CID-1's check is repo-wide across `agent_workflows/` (a per-file check would pass against the two byte-identical `terminate_process` copies and is not acceptable); (4) pasted `make test-all` output, since a bare `pytest -q` deselects the `slow` tests this Set depends on; and (5) the A10 platform statement required by OQ-02, naming which rows were verified on Windows and which were not.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited verbatim by every child):

- Open questions: OQ-01 here is resolved and spec OQ-01/OQ-03 are RESOLVED in c4gd2h, but **OQ-02 (how spec A10 is honestly satisfied) is OPEN and BLOCKING**, so this Set is NO-GO until the maintainer decides it. Children `2ouj70` through `m0z0ti` (Phases 0-4) do not depend on OQ-02 and may be approved and executed independently once the two pre-existing repository facts above are folded into `2ouj70` and `m0z0ti`; `71vjbn` (Phase 5) MUST NOT be executed until OQ-02 is resolved, because its E-07 and its own Deferred section currently contradict each other.
- Scope fence: touch ONLY the declared `Scope-Paths` of the child being executed. Widening requires a new plan, not an in-place edit.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only (`git commit -m msg -- <path>`); never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: run `aw ipd begin <child> --actor <agent/model>` BEFORE executing (fail-closed: no receipt, no execution authority), then `aw ipd finalize` after validation passes. Never hand-move a plan to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
