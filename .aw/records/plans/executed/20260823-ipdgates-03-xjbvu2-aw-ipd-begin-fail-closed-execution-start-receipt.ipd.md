# IPD: aw ipd begin fail-closed execution-start receipt

- Date: 2026-08-23
- Kind: child
- Concern: There is no durable, inspectable proof that an IPD passed the pre-execution gate at a known base HEAD before work began. p7dqwz's terminal record retained no pre-execution evidence, so scope/lifecycle claims could not be independently checked after the fact. A scope check performed only against the final working tree is insufficient (product changes may already be committed; unrelated concurrent edits may exist), so the allowlist and base MUST be frozen BEFORE execution.
- Scope: Add `aw ipd begin <plan> --actor <agent/model>` as the authoritative single-IPD execution entry and its receipt. Touch: a new narrowly-named single-IPD lifecycle module (e.g. `agent_workflows/ipd_lifecycle.py`), agent_workflows/cli.py (register the `ipd begin` verb + flags + help), reuse agent_workflows/run_freeze.py (`freeze_requirements`), agent_workflows/ipd_lint.py (invoke the pre-execution phase), and a new tests/test_ipd_lifecycle_cli.py. Does NOT implement finalize (Order 04) or remove bypasses (Order 07); it produces only the receipt that finalize will later require.
- Scope-Paths: grandfathered
- Status: executed
- Set: ipdgates
- Order: 3
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: xjbvu2
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
- 2026-08-24 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us, ipdrunner run-20260824T150827Z-2301181): E-01..E-03 performed, V-01..V-03 verified. Added agent_workflows/ipd_lifecycle.py (fail-closed `begin` receipt: runs pre-execution lint, freezes requirements + Scope-Paths via run_freeze, captures base HEAD, refuses dirty/ambiguous baseline + missing actor, writes an atomic resumable receipt to the gitignored .aw/state/ipd-lifecycle/<id6>.receipt.json), registered `aw ipd begin` in cli.py with help + 0/1/2 exit codes, declared the leaf in command_surface.py, and added tests/test_ipd_lifecycle_cli.py (15 tests). Documented the receipt in the ipd-lifecycle workflow doc + the ipd-structure spec Section 11 (aw specs note). pytest -n auto = 2249 passed, 1 skipped. One decision recorded (09-xjbvu2-D1: command_surface.py declaration is a mechanical consequence of the E-02 verb). Status set to executed and git mv pending -> executed.
- 2026-08-24 approved (aw set, --by-human): status set to approved

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-03).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified run_freeze.freeze_requirements (run_freeze.py:131, fail-closed) and the ipd_lint pre-execution checkpoint (ipd_lint.py:668). PR-001/PR-002 (resolved OQ-01's LOCATION half from repo evidence - `.aw/state/` is the documented gitignored home for "transaction journals/receipts", .gitignore:55-60 - rather than asking the human; corrected Step-0 which cited only workflow-artifacts/). PR-003 + OQ-01 lifetime resolved by human after a good challenge ("why the anchor? won't it thrash my multi-agent workflow?"): the base-HEAD anchor is needed to attribute changes to THIS execution in a multi-plan concurrent worktree, but my initial "stale when HEAD moved" rec WOULD have thrashed concurrent agents - so the resolved rule is PERSIST with a PATH-OVERLAP collision guard (HEAD movement never invalidates; only a plan-digest change or an intervening commit touching this plan's Scope-Paths does). This preserves the concurrent multi-agent workflow and feeds Order 04 OQ-01 ("this execution's changes" = diff restricted to Scope-Paths since base). E-01/V-01/gate updated.
- 2026-08-23 renumber-pointer-fix (opencode its_direct/pt3-claude-opus-4.8-1m-us): corrected two prose references "remove bypasses (Order 06)" -> "(Order 07)" after a new Order 05 (finalize scope reconciliation, D141) was inserted and rollback/remove-bypass shifted to 06/07. Pointer-only; no substantive change, so `Status: reviewed` is retained.

## Goal

Provide `aw ipd begin <plan> --actor <agent/model>` as the fail-closed start of single-IPD execution: it runs `aw ipd lint --phase pre-execution`, freezes the plan's requirements and `Scope-Paths` with the existing `run_freeze` primitives, binds a receipt to (plan Id, plan content digest, base HEAD, actor/model, timestamp), and atomically writes a resumable LOCAL lifecycle receipt. Any failure mode - lint exit 1/2, a dirty or ambiguous baseline, a missing actor/model, or an interrupted write - MUST leave NO valid receipt and therefore NO execution authority, so that finalize (Order 04) cannot later succeed without independently-inspectable proof that the approved plan and its scope passed the pre-execution gate at a specific base HEAD.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The receipt and its binding

- [x] E-01 In a new single-IPD lifecycle module, implement the begin receipt: run the pre-execution lint phase; if it does not conform, write nothing and exit nonzero. On conformance, freeze the plan requirements and `Scope-Paths` via `run_freeze.freeze_requirements`, capture the base HEAD (refusing a dirty or ambiguous worktree/baseline with an actionable diagnostic), require a non-empty `--actor <agent/model>`, and build a receipt record binding {plan Id, plan content digest, frozen requirement/scope digest, base HEAD, actor/model, timestamp}. Write it ATOMICALLY to the gitignored `.aw/state/` tree (location resolved per OQ-01, e.g. `.aw/state/ipd-lifecycle/<id6>.receipt.json`) so an interrupted write leaves no partial/valid receipt; make it resumable (a re-read returns the same receipt deterministically). LIFETIME (OQ-01 resolved): the receipt PERSISTS across unrelated intervening commits (HEAD movement does NOT invalidate it, preserving the concurrent multi-agent workflow); it is invalidated only by a plan-digest change or an intervening commit that touched a path inside this plan's `Scope-Paths`. Order 04's finalize enforces the path-overlap collision check; `begin` only needs to record the base HEAD + frozen `Scope-Paths` that make that check possible.
  - Depends on: none
  - Expected outcome: a conforming pre-execution run yields exactly one atomic, resumable receipt bound to the plan+scope+base; any failure yields none.
  - Execution state: performed

### Task group 2: The CLI verb

- [x] E-02 Register `aw ipd begin <plan> --actor <agent/model>` in `cli.py` calling the E-01 module, with help/usage text describing the receipt and the fail-closed contract, and the shared exit-code convention (0 ok / 1 findings / 2 cannot-run). Resolve the `<plan>` selector via the standard resolver. Do not mutate the plan or any tracked file (the receipt is local-only).
  - Depends on: E-01
  - Expected outcome: `aw ipd begin` is a usable CLI entry that produces the receipt and self-documents via `--help`.
  - Execution state: performed

### Task group 3: Prove fail-closed

- [x] E-03 Add `tests/test_ipd_lifecycle_cli.py` begin-command tests: a conforming plan yields a receipt capturing plan Id, requirement/scope digest, exact `Scope-Paths`, base HEAD, actor/model, timestamp, and the pre-execution lint output; a changed plan digest INVALIDATES a prior receipt; lint exit 1/2, a missing `--actor`, a dirty/ambiguous baseline, and a simulated interrupted write each leave NO valid receipt; and a resume reads the same receipt deterministically. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: every fail-closed path is proven to produce no execution authority, and the happy path is fully bound and resumable.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `run_freeze.freeze_requirements()` (`agent_workflows/run_freeze.py:131`) supplies stable requirement digests; reuse it rather than inventing a second digest engine.
- `aw ipd lint` already owns the phase checkpoints (`--phase pre-execution`); this command INVOKES it, it does not reimplement lint.
- The repo already has a gitignored home for exactly this kind of artifact: `.aw/state/` (`.gitignore:55-60`), whose comment explicitly names "runtime scratch, migration transaction journals/**receipts**". The begin receipt MUST live there (local-only, never committed) - see OQ-01 (location resolved from this evidence; only lifetime remains a human decision).
- `Scope-Paths` is defined by Order 02 (dependency); begin freezes whatever the approved plan declares.

## Findings

Freezing the scope+base BEFORE work is what makes a later scope comparison meaningful; checking only the end-state working tree cannot distinguish this IPD's changes from pre-existing commits or concurrent edits. The receipt is the anchor finalize (Order 04) binds its evidence to.

## Proposed changes (ordered, validatable)

1. Implement the atomic, resumable, fail-closed begin receipt bound to plan+scope+base+actor (E-01).
2. Register the `aw ipd begin` CLI verb with help + exit codes (E-02).
3. Test every fail-closed path + happy-path binding + resume (E-03).

## Deferred / out of scope (with reason)

- Terminal finalization and path comparison: Order 04.
- Removing raw `aw set executed`: Order 07.
- `Scope-Paths` schema/grammar: Order 02 (dependency).

## Scope check

- Over-scope: none.
- Under-scope: none; the receipt, its binding, the CLI verb, and fail-closed tests are included.

## Required tests / validation

- `tests/test_ipd_lifecycle_cli.py` begin tests per E-03.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Amend the IPD lifecycle spec (via its managed verb) and `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` to document `aw ipd begin` and the receipt; update CLI `--help`. (Docs may be batched into Order 04's transaction doc if cleaner, but the begin contract must be documented before the Set completes.)

## Open questions

### OQ-01: What is the begin receipt's LIFETIME / staleness rule? (location resolved from evidence)

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: LOCATION resolved from repository evidence: the receipt lives under the existing gitignored `.aw/state/` tree (`.gitignore:55-60` names it the home for "migration transaction journals/receipts"), e.g. `.aw/state/ipd-lifecycle/<id6>.receipt.json`, local-only, never committed. LIFETIME resolved by human (2026-08-23, /plan-review): the receipt PERSISTS across unrelated intervening commits - HEAD moving does NOT invalidate it - so the maintainer's concurrent multi-agent workflow (multiple agents committing on the same branch on DISJOINT file sets) never triggers a needless re-`begin`. The validity rule is PATH-OVERLAP-scoped, not HEAD-identity-scoped: a receipt is invalidated only by (a) a change to the plan's own content digest (already required), or (b) an intervening commit since the frozen base that modified a path INSIDE this plan's `Scope-Paths` (a genuine same-file collision - rare, worth flagging). Unrelated intervening commits on disjoint paths are ignored. This directly informs Order 04's OQ-01 ("this execution's changes" = the diff restricted to this plan's `Scope-Paths` since base): finalize refuses on (a) this execution touching a path OUTSIDE `Scope-Paths`, or (b) another commit touching a path INSIDE `Scope-Paths` since base.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: a test shows a conforming run writes exactly one atomic receipt (under `.aw/state/`) binding plan Id/digest/frozen `Scope-Paths`/base HEAD/actor/timestamp; lint-nonconform, dirty/ambiguous baseline, missing actor, and interrupted write each leave no valid receipt; a re-read is deterministic (resume); and the receipt PERSISTS (remains valid + resumable) after an unrelated intervening commit on DISJOINT paths (proving HEAD movement alone does not invalidate it - the path-overlap collision enforcement itself is Order 04's finalize test).
  - Observed evidence: `agent_workflows/ipd_lifecycle.py::begin` runs `ipd_lint.lint_file(..., checkpoint="pre-execution")`, then `run_freeze.freeze_requirements`, captures base HEAD via `run_evidence.get_git_head`, refuses a dirty tree via `get_git_dirty_digest`, and writes `.aw/state/ipd-lifecycle/<id6>.receipt.json` atomically (`tempfile.mkstemp` + `os.replace`). A concrete happy-path receipt (temp git repo): `{plan_id: abc123, plan_content_digest: a0356e5d..., requirement_digest: e78c46f9..., scope_paths: [agent_workflows/demo.py, tests/test_demo.py], base_head: bfd0d7bf..., actor: opencode/its_direct, timestamp: 2026-08-24T17:27:23Z, pre_execution.disposition: conforming}`; `git check-ignore` confirms it is under the gitignored `.aw/state/` tree. `tests/test_ipd_lifecycle_cli.py::BeginHappyPathTests` proves the binding, gitignore/untracked, deterministic resume, digest-invalidation, and persistence across an unrelated disjoint commit; `BeginFailClosedTests` proves missing-actor / dirty-worktree / non-conforming-lint (exit 1) / missing-id / interrupted-write (mock `os.replace` raising) each leave NO valid receipt and no leftover temp file.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: `aw ipd begin --help` documents the fail-closed contract; the verb resolves the plan selector, produces the receipt, mutates no tracked file, and returns the correct exit codes (0/1/2).
  - Observed evidence: `aw ipd begin --help` prints the fail-closed contract + the receipt location + "Exit 0 = receipt written, 1 = gate findings, 2 = cannot run" (verified). `ipd_lifecycle.run_begin` resolves the `<plan>` via `selectors.resolve(repo_root, "plans", selector)` (refusing no-match/ambiguous as exit 2). `tests/test_ipd_lifecycle_cli.py::BeginCliTests` proves: happy path exit 0 + receipt written; unresolved selector exit 2; non-conforming exit 1; and `test_cli_mutates_no_tracked_file` asserts `git status --porcelain` shows no modified/staged tracked file (only the gitignored receipt). The verb is registered in `cli.py` (dispatch `ipd_cmd == "begin"`) and declared in `command_surface.py` so the CLI conformance harness passes.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: `tests/test_ipd_lifecycle_cli.py` begin tests pass (happy binding + every fail-closed path + resume + digest-invalidation); `pytest -n auto` is green (pasted).
  - Observed evidence: `pytest tests/test_ipd_lifecycle_cli.py -v` -> `15 passed in 0.54s` (BeginHappyPathTests 6, BeginFailClosedTests 5, BeginCliTests 4). Full suite `pytest -n auto` -> `2249 passed, 1 skipped in 126.81s (0:02:06)`. Registering the new `ipd begin` leaf also required declaring it in `command_surface.py` (mechanical CLI-surface conformance consequence of E-02; DECISION 09-xjbvu2-D1); the CLI conformance harness (`test_command_surface_declarations.py`, `test_cli_conformance_matrix.py`) is green. `aw specs check` conforms; `check-local-leaks` clean.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the fail-closed pre-execution receipt and its CLI entry.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved - receipt location is `.aw/state/ipd-lifecycle/` (from repo evidence); lifetime PERSISTS with a path-overlap collision guard (human, 2026-08-23), preserving the concurrent multi-agent workflow.
2. Scope fence: touch ONLY the new single-IPD lifecycle module, `cli.py` (begin verb), `ipd_lint.py` (invoke pre-execution phase), reuse `run_freeze.py`, and `tests/test_ipd_lifecycle_cli.py`, plus the lifecycle doc/spec via managed verbs. Do NOT implement finalize or remove bypasses. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output and the receipt path/digest; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. The receipt is local-only and MUST NOT be committed (confirm it is gitignored).
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the existing lifecycle workflow, since `aw ipd finalize` does not exist until Order 04).
