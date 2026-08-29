# IPD: Phase 2: move lifecycle authority into the driver (driver-created begin/finalize receipts, worker-role lifecycle verbs refuse, OBSERVED from git+process facts, five-way output classifier + verified harvest, optional aw lane status/note)

- Date: 2026-08-28
- Kind: child
- Concern: The driver already wraps begin/finalize (oc_runipd.driver_begin oc_runipd.py:338, driver_finalize oc_runipd.py:395; agy_runipd.py:459/514) but authority still leaks to the worker in three ways x03wgn Section 2/5 forbids. (1) STALE-ON-SELF-EXECUTION (backlog xmqv5l): begin freezes a whole-file `plan_content_digest` (ipd_lifecycle.py:729 via plan_content_digest ipd_lifecycle.py:254-256), and `receipt_is_current` (ipd_lifecycle.py:580-586) invalidates the receipt whenever that byte digest changes; but a correct self-execution MUST edit the same plan (mark E performed, fill V evidence, append Workflow history), so `finalize_precheck` refuses `the begin receipt ... is STALE` (ipd_lifecycle.py:918-925) on every self-finalizing run and merge-back is left substantially-complete. (2) NO WORKER-ROLE REFUSAL: nothing stops an in-lane `aw ipd begin/finalize` from forking a second receipt/run the driver cannot see (x03wgn Section 2 "Receipt ownership does not mean agent tool compliance", Section 3 `AW-LIFECYCLE-ROLE-001`); the sync_receipt_into_worktree copy (oc_runipd.py:462-476) hides the split. (3) OUTCOME OVER-TRUST: reconcile_disposition (oc_runipd.py:1756-1776) reads the agent-written `outcome.json` `disposition == "executed"` (oc_runipd.py:1770-1773) and there is no five-way output-retention classifier before force teardown (teardown_isolation_worktree -> worktree_lease.teardown_worktree force=True, oc_runipd.py:455/:459). Research x03wgn Section 2 (control-authority class, retention table), Section 5 (lane result formation, output harvest), Section 8 "Phase 2" prescribe: the DRIVER owns begin/finalize as mechanical prerequisites, worker-role verbs refuse deterministically, the receipt binds REQUIREMENTS+base HEAD not the whole file (fixes xmqv5l), outcome is OBSERVED from git+process facts with agent output advisory-only, and every changed item is classified into one of five retention classes with `unknown` blocking teardown.
- Scope: Rebind the begin receipt to a requirement+scope+base-HEAD digest (NOT whole-file bytes) so a normal self-execution stays valid while a scope/requirements edit still invalidates it (fixes xmqv5l); make worker-role `aw ipd begin`/`aw ipd finalize` return the deterministic `AW-LIFECYCLE-ROLE-001` corrective error and NOT run (driver keeps owning them); implement a driver-OBSERVED outcome derived from git+process facts that is authoritative over any agent `outcome.json`; implement the five-way output classifier (tracked-publish/local-retain/secret-local/discardable/unknown) with a verified harvest before teardown where `unknown` BLOCKS teardown; add optional read-only `aw lane status` + `aw lane note`. Apply the driver-side changes symmetrically to BOTH oc_runipd.py and agy_runipd.py. Does NOT relocate machine state out of repo (Phase 4), does NOT introduce the typed ExecutionContext/PathResolver or AST guard (Phase 3), does NOT implement real candidate-merge integration or crash recovery (Phase 5), does NOT add the OS sandbox (Phase 6).
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lane_status.py, agent_workflows/cli.py, tests/test_ipd_lifecycle_cli.py, tests/test_receipt_requirement_digest.py, tests/test_worker_role_refusal.py, tests/test_driver_observed_outcome.py, tests/test_output_classifier.py, tests/test_lane_status_note.py
- Item-Dependencies: executed:qcqhj7
- Status: to-review
- Set: wtiso
- Order: 3
- Highest E allocated: 12
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rchpms
- From-Backlog: xmqv5l

## Workflow history
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Move lifecycle authority fully into the driver so a forgetful, tool-omitting, or lying in-lane agent still yields a correct integrated result: rebind the begin receipt to the frozen requirement+scope+base-HEAD digest (not the whole-file byte digest) so a normal self-execution that edits its own checklist no longer goes stale (fixing xmqv5l) while a scope/requirements edit still invalidates it; make worker-role `aw ipd begin`/`finalize` refuse with a deterministic corrective error instead of forking a hidden second receipt; derive the lane outcome from OBSERVED git+process facts with the agent's `outcome.json` reduced to advisory; and classify every lane change into exactly one of five retention classes with a verified harvest where `unknown` blocks teardown. Acceptance is pasted command output and observed git/filesystem/process state, never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: rebind the receipt to requirements+scope+base, not whole-file bytes (fixes xmqv5l) (x03wgn Section 2 control-authority class; Section 8 Phase 2)

- [ ] E-01 In `ipd_lifecycle.py`, add a pure function `frozen_region_digest(text: str) -> str` that hashes ONLY the invariants that must not change mid-execution: the frozen `Scope-Paths` allowlist (reuse `_frozen_scope_paths`, ipd_lifecycle.py:307-324) plus the requirement categories (reuse `_requirements_from_plan`, ipd_lifecycle.py:259-304, i.e. Scope + E-item action text + V-item row text), serialized deterministically (sorted keys) via `hashlib.sha256`. It MUST NOT include the mutable execution/validation STATE (`Execution state:`, `Result:`, `Observed evidence:`), the `## Workflow history`, or the checkbox `[ ]`/`[x]` markers. Add it beside `plan_content_digest` (ipd_lifecycle.py:254-256); do not delete `plan_content_digest` (other callers/tests reference it).
  - Depends on: none
  - Expected outcome: `frozen_region_digest(t)` returns a stable 64-char hex string; for two plan texts that differ ONLY in E `Execution state:`/V `Result:`/`Observed evidence:`/`## Workflow history`/checkbox marks the digest is IDENTICAL, and for two texts that differ in a `Scope-Paths` entry or an E-item action text the digest DIFFERS.
  - Execution state: pending

- [ ] E-02 In `ipd_lifecycle.begin` (ipd_lifecycle.py:594-749), write the new `frozen_region_digest` into the receipt as a `frozen_region_digest` field alongside the existing `requirement_digest`/`scope_paths`/`base_head` (receipt dict at ipd_lifecycle.py:724-739); keep writing `plan_content_digest` (do not break the receipt schema for readers) but it is no longer the validity key. Bump `RECEIPT_SCHEMA_VERSION` and record the change in the schema constant's comment.
  - Depends on: E-01
  - Expected outcome: a receipt written by `begin(...)` contains a non-empty `frozen_region_digest` equal to `frozen_region_digest(plan_text)` and still contains `requirement_digest`, `scope_paths`, `base_head`, and `plan_content_digest`; `RECEIPT_SCHEMA_VERSION` is incremented.
  - Execution state: pending

- [ ] E-03 In `ipd_lifecycle.receipt_is_current` (ipd_lifecycle.py:580-586), change the validity key from `plan_content_digest` to `frozen_region_digest`: the receipt is current iff `receipt.get("frozen_region_digest") == frozen_region_digest(plan_text)`. For a legacy receipt lacking the field (older schema), fall back to the old whole-file comparison so a pre-Phase-2 receipt is not spuriously accepted. Update the docstring to state the new invariant and cite xmqv5l.
  - Depends on: E-02
  - Expected outcome: `receipt_is_current(receipt, edited_text)` returns True when `edited_text` differs from the begin text ONLY in checklist state/evidence/history, and returns False when `edited_text` changes a `Scope-Paths` entry or an E/V requirement line; a receipt with no `frozen_region_digest` uses the legacy whole-file rule.
  - Execution state: pending

### Task group 2: worker-role lifecycle verbs refuse deterministically (x03wgn Section 2 "Receipt ownership does not mean agent tool compliance"; Section 3 AW-LIFECYCLE-ROLE-001)

- [ ] E-04 In `ipd_lifecycle.py`, add a pure predicate `worker_role_active(env: Mapping[str,str]) -> bool` that returns True iff the process environment marks a managed worker lane (`env.get("AW_EXECUTION_ROLE") == "worker"`, the selector x03wgn Section 3 exports), and add a constant `LIFECYCLE_ROLE_ERROR = "AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not run them"`.
  - Depends on: none
  - Expected outcome: `worker_role_active({"AW_EXECUTION_ROLE":"worker"})` is True; `worker_role_active({})` and `worker_role_active({"AW_EXECUTION_ROLE":"coordinator"})` are False; `LIFECYCLE_ROLE_ERROR` starts with the exact token `AW-LIFECYCLE-ROLE-001`.
  - Execution state: pending

- [ ] E-05 In the `aw ipd begin` and `aw ipd finalize` CLI dispatch (cli.py begin parser cli.py:1109, finalize parser cli.py:1137; their handlers in the `ipd_command` dispatch), guard both verbs so that when `worker_role_active(os.environ)` is True they print `LIFECYCLE_ROLE_ERROR` to stderr and exit with the existing cannot-run code `ipd_lifecycle.EXIT_CANNOT_RUN` WITHOUT writing a receipt, moving the plan, or running the gate. The driver's own in-process calls (oc_runipd.driver_begin oc_runipd.py:338, driver_finalize oc_runipd.py:395) run in the coordinator role and are unaffected.
  - Depends on: E-04
  - Expected outcome: invoking `aw ipd begin <plan> --actor x` with `AW_EXECUTION_ROLE=worker` in the environment exits `EXIT_CANNOT_RUN`, prints a line containing `AW-LIFECYCLE-ROLE-001`, and writes NO receipt file; the same command with no `AW_EXECUTION_ROLE` runs the normal gate.
  - Execution state: pending

- [ ] E-06 In `oc_runipd.py`, set `AW_EXECUTION_ROLE=worker` in the child environment of the isolated agent turn (the env built for `run_opencode`) and NOT in the driver's own process, so a worker subprocess that calls `aw ipd begin/finalize` hits E-05's refusal while the coordinator's `driver_begin`/`driver_finalize` (which run in the driver process) do not. Mirror the env export in `agy_runipd.py` (`run_agy_turn`, agy_runipd.py:1703).
  - Depends on: E-05
  - Expected outcome: a unit test inspecting the child env dict built by the isolated `oc_runipd` turn asserts `env["AW_EXECUTION_ROLE"] == "worker"`, and the driver's own `os.environ` at `driver_begin` time does NOT have `AW_EXECUTION_ROLE == "worker"`; the agy child env asserts the same key.
  - Execution state: pending

### Task group 3: OBSERVED outcome from git+process facts, agent output advisory (x03wgn Section 5 lane result formation; Section 2 "Outcome and decisions need different truth models")

- [ ] E-07 In `ipd_lifecycle.py` (or a small helper reused by both drivers), add a pure function `observe_lane_outcome(base_commit, head_commit, changed_files, porcelain_status, process_exit, plan_bucket) -> dict` that derives the authoritative outcome ONLY from those observed facts (git base/tip, changed paths, `git status --porcelain=v2` cleanliness, process exit code, and whether the plan file is in `executed/`), returning at least `{observed_disposition, integrated_to_target, changed_paths, dirty}`. It takes NO agent `outcome.json` as input.
  - Depends on: none
  - Expected outcome: `observe_lane_outcome(...)` with a plan in `executed/` and a clean tree returns `observed_disposition == "executed"`; with `process_exit != 0` returns `"failed-safely"`; with an unmoved plan and a nonempty diff returns `"partial"`; the function never reads a filesystem `outcome.json`.
  - Execution state: pending

- [ ] E-08 In `oc_runipd.reconcile_disposition` (oc_runipd.py:1756-1776), make the driver-OBSERVED disposition from E-07 AUTHORITATIVE: compute `observe_lane_outcome(...)` from real git facts and use it as the returned disposition; keep the agent `outcome.json` (oc_runipd.py:1758-1762) as an ADVISORY field only, and add a recorded `outcome_conflict: true` marker when the agent JSON claims `disposition == "executed"` (oc_runipd.py:1770-1773) but the observed git state is NOT `executed`. A fabricated `outcome.json` must NOT be able to promote an un-integrated lane to `executed`. Mirror the change in `agy_runipd.reconcile_disposition` (agy_runipd.py:1823).
  - Depends on: E-07
  - Expected outcome: for a lane whose plan is NOT in `executed/` and whose tree is un-integrated, `reconcile_disposition` returns a non-`executed` disposition EVEN WHEN the agent `outcome.json` says `disposition:"executed"`, and the returned record carries `outcome_conflict == True`; for a genuinely integrated lane the observed disposition is `executed`.
  - Execution state: pending

### Task group 4: five-way output classifier + verified harvest, unknown blocks teardown (x03wgn Section 2 retention table; Section 5 output harvest)

- [ ] E-09 In a new `agent_workflows/lane_status.py`, add a pure function `classify_output(path, tracked, ignored_rules, secret_rules, discard_rules) -> str` returning exactly one of `"tracked-publish"`, `"local-retain"`, `"secret-local"`, `"discardable"`, `"unknown"` per x03wgn Section 2's retention table: a tracked changed/added path is `tracked-publish`; a path matching an explicit secret rule is `secret-local`; a path matching an explicit discard (cache/temp/build) rule is `discardable`; a path matching an explicit local-retain rule is `local-retain`; ANY other untracked/ignored path is `unknown` (no broad-glob or "ignored means disposable" shortcut, per the table's forbidden note).
  - Depends on: none
  - Expected outcome: `classify_output` returns `tracked-publish` for a tracked path, `secret-local` for a secret-rule match, `discardable` only for an explicit discard-rule match, `local-retain` for an explicit retain-rule match, and `unknown` for an untracked path with no matching rule (a bare ignored path with no discard rule is `unknown`, never `discardable`).
  - Execution state: pending

- [ ] E-10 In `lane_status.py`, add `harvest_and_teardown_gate(lane_items) -> dict` that, for a lane's classified items, (a) records a verified harvest for each `local-retain` item (copy destination path + a recomputed `source_digest`/`dest_digest` that must match), and (b) returns `{teardown_authorized: bool, blocking_unknowns: [...]}` where `teardown_authorized` is False whenever ANY item classifies as `unknown` OR any `local-retain` harvest digest mismatches. Then wire it into the pre-teardown path of BOTH drivers (before `teardown_isolation_worktree`, oc_runipd.py:455/:459; agy_runipd.py:573) so a lane with an `unknown` item is PRESERVED (skip force-teardown, record a `worktree-preserved` event) instead of force-removed.
  - Depends on: E-09
  - Expected outcome: `harvest_and_teardown_gate` returns `teardown_authorized == False` with a non-empty `blocking_unknowns` when a lane has an `unknown` item, and `True` only when every item is tracked-publish/local-retain(verified)/secret-local/discardable; a driver unit test with an `unknown` lane file observes teardown REFUSED (worktree dir still exists) and a `worktree-preserved` event recorded.
  - Execution state: pending

### Task group 5: optional read-only aw lane status / aw lane note (x03wgn Section 1 "optional aw lane commands"; Behavior layer, not Authority)

- [ ] E-11 In `lane_status.py`, add `lane_status(repo, id6) -> dict` (READ-ONLY: current lane branch/base/tip, changed paths, and per-path retention class from E-09; mutates nothing) and `lane_note(repo, id6, text) -> Path` that appends an advisory, timestamped note into the lane submissions area (never into a receipt, ledger, or the plan's authoritative status). Neither performs a lifecycle transition.
  - Depends on: E-09
  - Expected outcome: `lane_status(...)` returns a dict with the lane's classified changed paths and mutates no tracked/authoritative file (a before/after `git status` is identical); `lane_note(...)` appends the given text to an advisory submissions file and returns its path, touching no receipt/ledger/plan-status.
  - Execution state: pending

- [ ] E-12 Register `aw lane` with read-only `status` and `note` subcommands in `cli.py` (a new `lane` subparser beside the existing `ipd` subparser cli.py:832), dispatching to `lane_status.lane_status` / `lane_status.lane_note`; document in the help text that these are advisory/behavior aids and never a lifecycle authority (x03wgn control-plane principle: Behavior != Authority).
  - Depends on: E-11
  - Expected outcome: `aw lane status <id6>` prints the lane's classified paths and exits 0 without mutating tracked/authoritative state; `aw lane note <id6> --message x` exits 0 and appends the note; `aw lane --help` shows both subcommands marked read-only/advisory.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The two host drivers are deliberate near-parity twins: `oc_runipd.py` and `agy_runipd.py` share function shapes (`driver_begin` oc:338/agy:459, `driver_finalize` oc:395/agy:514, `sync_receipt_into_worktree` oc:462/agy:580, `build_lane_outcome` oc:479/agy:605, `teardown_isolation_worktree` oc:455/agy:573, `reconcile_disposition` oc:1756/agy:1823, `run_agy_turn` agy:1703). Any driver-side change MUST land in both to avoid drift (same rule Phase 1 followed).
- The begin receipt already binds a `requirement_digest` (frozen Scope + E + V, via `_requirements_from_plan` ipd_lifecycle.py:259-304 -> `run_freeze.freeze_requirements`), `scope_paths` (`_frozen_scope_paths` ipd_lifecycle.py:307-324), and `base_head` (ipd_lifecycle.py:730-732). Only `plan_content_digest` (the whole-file byte hash, ipd_lifecycle.py:729/:254-256) is the over-tight key that xmqv5l blames; the requirement/scope invariants needed for the fix are ALREADY captured, so the fix is to switch the validity key, not to invent new frozen data.
- `receipt_is_current` (ipd_lifecycle.py:580-586) is the single validity predicate consulted by `finalize_precheck` (ipd_lifecycle.py:918-925) and thus by the driver's `driver_finalize` and by emics4n merge-back; changing it in one place fixes both self-finalize and merge-back (xmqv5l IMPACT line).
- The receipt is written atomically (`_atomic_write_json` ipd_lifecycle.py:550-568) and is gitignored under `.aw/state/ipd-lifecycle/<id6>.receipt.json` (`receipt_path_for` ipd_lifecycle.py:249-251); tests init a git repo and .gitignore that path (tests/test_ipd_lifecycle_cli.py:29-38).
- `reconcile_disposition` currently trusts the agent `outcome.json` `disposition:"executed"` (oc_runipd.py:1770-1773) but ALREADY checks the git `plan_bucket == "executed"` first (oc_runipd.py:1768-1769); the observed-authority change tightens the existing order so git state wins on conflict.
- Existing worker-forbidden path predicate `worktree_lease.path_is_worker_forbidden` (Phase 1 reused it) is available if the classifier needs a forbidden-path notion; the classifier here uses explicit rule sets per the retention table, not path-forbidding.
- Tests are `unittest`-style, git-backed throwaway repos, launched with `PYTHONPATH` pinned to repo root (tests/test_ipd_lifecycle_cli.py header; tests/test_oc_runipd.py header).

## Findings

| # | Finding | Evidence (x03wgn section + real file:line + backlog) |
|---|---|---|
| F1 | The receipt's whole-file `plan_content_digest` is the sole validity key, so any self-execution edit invalidates it. | backlog xmqv5l ROOT CAUSE; `receipt_is_current` ipd_lifecycle.py:580-586; `plan_content_digest` ipd_lifecycle.py:254-256; receipt write ipd_lifecycle.py:729. |
| F2 | A correct execution MUST mutate the plan (mark E performed, fill V evidence, append history), so the digest ALWAYS goes stale and finalize refuses. | backlog xmqv5l CONTRADICTION + OBSERVED (7kbtkw run left substantially-complete); `finalize_precheck` STALE refusal ipd_lifecycle.py:918-925. |
| F3 | The requirement/scope/base invariants that legitimately must not change ARE already frozen; only the whole-file digest is wrong to use as the key. | backlog xmqv5l FIX(b) "digest only the FROZEN region ... excluding the mutable checklist"; `requirement_digest` ipd_lifecycle.py:730; `_requirements_from_plan` ipd_lifecycle.py:259-304; `_frozen_scope_paths` ipd_lifecycle.py:307-324. |
| F4 | Receipt ownership does not enforce agent tool compliance; nothing stops a worker forking a second `aw ipd begin`/`finalize`. | x03wgn Section 2 "Receipt ownership does not mean agent tool compliance"; Section 3 `AW-LIFECYCLE-ROLE-001: runner owns begin/finalize for managed lanes`; the receipt-copy that hides a split is oc_runipd.py:462-476. |
| F5 | The driver can derive the product outcome from observable git+process facts; the agent's outcome file is advisory and can be missing or inaccurate. | x03wgn Section 2 "Outcome and decisions need different truth models" (Missing outcome JSON is a recoverable completeness problem), Section 5 "Lane result formation" (do not assume HEAD contains all work / import submissions but treat observed git state as authoritative); the over-trust site is oc_runipd.py:1770-1773. |
| F6 | Every changed/created item must be placed in exactly one of five retention classes; `unknown` must preserve the lane, and "ignored means disposable" is forbidden. | x03wgn Section 2 "Durable, local-retained, secret, discardable, and unknown" retention table (unknown -> "Worktree and branch remain preserved"; discardable -> "broad globs and 'ignored means disposable' are forbidden"); Section 5 "Output harvest and durable publication" (copy rather than link; verify digests before deletion). |
| F7 | Teardown currently force-removes the worktree with no retention gate. | x03wgn Section 2 retention table + Section 5 ("Any unknown file ... blocks teardown and preserves the lane"); `teardown_isolation_worktree` -> `worktree_lease.teardown_worktree(force=True)` oc_runipd.py:455/:459, agy_runipd.py:573. |
| F8 | Optional `aw lane` commands are a Behavior/Feedback aid, NOT an Authority mechanism; correctness must not depend on them. | x03wgn Section 1 "Behavior/Feedback/Authority" table (optional `aw lane` commands under Behavior, "May correctness depend on it? No"). |
| F9 | Both host drivers must change symmetrically. | x03wgn Section 8 Phase 2 (runner-general); oc_runipd.py + agy_runipd.py twin structure (driver_begin/finalize/reconcile_disposition/teardown parity). |

## Proposed changes (ordered, validatable)

1. E-01/E-02/E-03: add `frozen_region_digest`, write it into the receipt, and switch `receipt_is_current` to it (with legacy fallback) - the xmqv5l fix.
2. E-04/E-05/E-06: `worker_role_active` predicate + `AW-LIFECYCLE-ROLE-001` refusal wired into `aw ipd begin/finalize`, with the driver exporting `AW_EXECUTION_ROLE=worker` only into the worker child env in both drivers.
3. E-07/E-08: `observe_lane_outcome` derives the authoritative disposition from git+process facts; `reconcile_disposition` makes it win over the advisory agent `outcome.json` and records `outcome_conflict` on a fabricated success, in both drivers.
4. E-09/E-10: five-way `classify_output` + `harvest_and_teardown_gate` (verified digests, `unknown` blocks teardown) wired into both drivers' pre-teardown path with a `worktree-preserved` event.
5. E-11/E-12: optional read-only `aw lane status`/`aw lane note` (advisory, no lifecycle authority).

## Deferred / out of scope (with reason)

- Relocating machine state out of the repo (XDG state dir), removing the `sync_receipt_into_worktree` copy entirely: Phase 4 (child 58ha43). This child keeps the in-repo `.aw/state` receipt location and the copy; it only changes the receipt's validity key and adds the worker-role refusal.
- The typed `ExecutionContext`/`PathResolver` keyed by git-common-dir + the AST guard: Phase 3 (child 7p9n2v). `worker_role_active` here reads a single env selector as an interim role signal, not the full resolver.
- Real candidate-merge integration, expected-tip recheck, publication projection, full crash recovery, cross-platform locks: Phase 5 (child 2c122z). This child's harvest gate only decides teardown-vs-preserve; it does not perform the integration merge.
- A generated closure/reconciliation turn for material-decision attribution (`BLOCKED_DECISION`): out of scope; this child implements the OBSERVED outcome and retention classification, not the decision-attribution closure turn (x03wgn Section 2 "Outcome and decisions need different truth models" decision half). Reason: closure-turn machinery depends on Phase 5 reconciliation and is not needed to fix xmqv5l or the outcome-over-trust bug.
- OS-sandbox hard enforcement of the worker role: Phase 6 (child 1o4eif). The env-based `worker_role_active` refusal is the operational-default guidance layer x03wgn scopes, not the hardened boundary.

## Scope check

- Over-scope: none. Every E-item is an x03wgn Section 2/5/8 Phase-2 authority item; no Phase 3-6 resolver/relocation/integration/sandbox work is done here.
- Under-scope: none. All four mandatory adversarial guards are covered: (a) the xmqv5l regression (begin -> mark all E performed + fill V evidence + append history -> finalize succeeds, no stale refusal) is V-03's `test_self_execution_edits_keep_receipt_current`; (b) the guard-not-too-loose case (editing Scope-Paths/requirements DOES invalidate) is V-03's `test_scope_or_requirement_edit_invalidates_receipt`; (c) a forgetful agent that writes NO `outcome.json` still gets an accurate driver-derived outcome is V-07/V-08's `test_missing_outcome_json_still_observed`; (d) a fabricated `outcome.json` claiming success does NOT override observed git state is V-08's `test_fabricated_success_outcome_does_not_override_git`. The worker-role refusal (V-05) and `unknown`-blocks-teardown (V-10) are additional adversarial guards.

## Required tests / validation

- New adversarial + unit tests (named exactly):
  - `tests/test_receipt_requirement_digest.py::test_frozen_region_digest_ignores_checklist_state`, `::test_self_execution_edits_keep_receipt_current`, `::test_scope_or_requirement_edit_invalidates_receipt`, `::test_legacy_receipt_without_frozen_region_uses_whole_file`.
  - `tests/test_worker_role_refusal.py::test_worker_role_begin_refuses_with_role_error`, `::test_worker_role_finalize_refuses_and_writes_no_receipt`, `::test_coordinator_role_begin_runs_normally`.
  - `tests/test_driver_observed_outcome.py::test_missing_outcome_json_still_observed`, `::test_fabricated_success_outcome_does_not_override_git`, `::test_observed_executed_only_when_integrated`.
  - `tests/test_output_classifier.py::test_five_way_classification`, `::test_unknown_blocks_teardown`, `::test_local_retain_digest_mismatch_blocks_teardown`.
  - `tests/test_lane_status_note.py::test_lane_status_is_read_only`, `::test_lane_note_appends_advisory_only`.
  - Existing `tests/test_ipd_lifecycle_cli.py` extended with `::test_self_finalize_after_checklist_edits_no_stale_refusal` (the end-to-end xmqv5l regression through `finalize_precheck`).
- Full-suite regression: `python3 -m pytest -p no:randomly -q` must stay green. Paste ACTUAL output.

## Spec / documentation sync

- N/A for a standalone spec doc in Phase 2. The receipt-schema change is captured by `RECEIPT_SCHEMA_VERSION` (E-02) and the new tests; the `AW-LIFECYCLE-ROLE-001` contract and the five-way retention classes are documented inline in the code (docstrings) and cited to x03wgn. A consolidated `state-taxonomy`/`lifecycle-authority` spec is owned by the Phase 0 characterization child (8zgybk) and the orchestrator's cross-IPD checks, not re-authored here (would duplicate/fork the frozen taxonomy).

## Open questions

### OQ-01: Should `frozen_region_digest` exclude the `## Findings`/`## Proposed changes` prose too, or only the execution/validation STATE + history + checkboxes?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Exclude ONLY the mutable execution/validation state, `## Workflow history`, and checkbox marks, matching xmqv5l FIX(b) ("excluding the mutable checklist (E/V states, Observed evidence, Workflow history)"). Requirement text (E/V action/row text) and `Scope-Paths` ARE frozen (they are the reviewed contract). Findings/Proposed-changes prose is NOT part of the frozen requirement set that `_requirements_from_plan` extracts, so it is naturally outside the digest; a normal execution does not edit it, and if it did, that is not a scope/requirement change so it correctly does not invalidate the receipt. This keeps the guard tight on the reviewed contract (adversarial guard (b)) without re-staling on legitimate self-execution edits (adversarial guard (a)).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_receipt_requirement_digest.py::test_frozen_region_digest_ignores_checklist_state` exits 0 showing `1 passed`. The test builds a plan text, computes `frozen_region_digest`, then produces a second text differing ONLY in E `Execution state:`/V `Result:`/`Observed evidence:`/`## Workflow history`/`[x]` marks and asserts the two digests are EQUAL (`assertEqual`), and a third text changing an E-item action line asserts the digest DIFFERS (`assertNotEqual`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_receipt_requirement_digest.py -k receipt_carries_frozen_region` exits 0 showing `passed`; the test calls `ipd_lifecycle.begin(...)` on a ready plan and asserts the written receipt JSON has a non-empty `frozen_region_digest` equal to `ipd_lifecycle.frozen_region_digest(plan_text)` and still contains `requirement_digest`, `scope_paths`, `base_head`, `plan_content_digest`, and that `RECEIPT_SCHEMA_VERSION` increased from the prior value asserted in the test.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_receipt_requirement_digest.py::test_self_execution_edits_keep_receipt_current tests/test_receipt_requirement_digest.py::test_scope_or_requirement_edit_invalidates_receipt tests/test_receipt_requirement_digest.py::test_legacy_receipt_without_frozen_region_uses_whole_file` exits 0 showing `3 passed`. `test_self_execution_edits_keep_receipt_current` (ADVERSARIAL guard (a), the xmqv5l regression): begin -> read stored receipt -> mutate the plan text to mark every E `performed`, fill each V `Observed evidence`/`Result: pass`, and append a `## Workflow history` line, then assert `receipt_is_current(stored, edited_text) is True`. `test_scope_or_requirement_edit_invalidates_receipt` (ADVERSARIAL guard (b), guard-not-too-loose): begin -> change a `Scope-Paths` entry (and separately an E-item action line) -> assert `receipt_is_current(stored, edited_text) is False`. The legacy test builds a receipt dict WITHOUT `frozen_region_digest` and asserts the whole-file fallback still governs.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_worker_role_refusal.py -k worker_role_predicate` exits 0 showing `passed`; the test asserts `ipd_lifecycle.worker_role_active({"AW_EXECUTION_ROLE":"worker"}) is True`, `... ({}) is False`, `... ({"AW_EXECUTION_ROLE":"coordinator"}) is False`, and `ipd_lifecycle.LIFECYCLE_ROLE_ERROR.startswith("AW-LIFECYCLE-ROLE-001")`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_worker_role_refusal.py::test_worker_role_begin_refuses_with_role_error tests/test_worker_role_refusal.py::test_worker_role_finalize_refuses_and_writes_no_receipt tests/test_worker_role_refusal.py::test_coordinator_role_begin_runs_normally` exits 0 showing `3 passed`. ADVERSARIAL guard: the begin/finalize tests run the CLI (subprocess `python3 -m agent_workflows ipd begin <plan> --actor x` / `... finalize ...`) with `AW_EXECUTION_ROLE=worker` in the environment and assert exit code `== ipd_lifecycle.EXIT_CANNOT_RUN`, stderr contains `AW-LIFECYCLE-ROLE-001`, and NO receipt file exists at `receipt_path_for(...)` afterward; the coordinator test runs the same begin with NO `AW_EXECUTION_ROLE` and asserts a receipt IS written (normal gate ran).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_worker_role_refusal.py -k child_env_marks_worker` exits 0 showing `passed`; the test builds the isolated-turn child env dict from `oc_runipd` and asserts `env["AW_EXECUTION_ROLE"] == "worker"`, and (agy parity) the `agy_runipd` child env asserts the same key; it also asserts the driver's own `os.environ.get("AW_EXECUTION_ROLE")` at `driver_begin` call time is not `"worker"`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_driver_observed_outcome.py::test_missing_outcome_json_still_observed tests/test_driver_observed_outcome.py::test_observed_executed_only_when_integrated` exits 0 showing `2 passed`. ADVERSARIAL guard (c): `test_missing_outcome_json_still_observed` calls `observe_lane_outcome(...)` with facts for a lane whose plan is in `executed/` and a clean tree and NO `outcome.json` present, asserting `observed_disposition == "executed"`; the same with `process_exit=1` asserts `"failed-safely"`. `test_observed_executed_only_when_integrated` asserts an unmoved plan + nonempty diff returns `"partial"`, never `"executed"`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_driver_observed_outcome.py::test_fabricated_success_outcome_does_not_override_git` exits 0 showing `1 passed`. ADVERSARIAL guard (d): the test constructs a run where the plan is NOT in `executed/` and the tree is un-integrated, writes an agent `outcome.json` with `{"disposition":"executed"}` into the outcomes dir (oc_runipd.py:1756), calls `reconcile_disposition`, and asserts the returned disposition is NOT `"executed"` AND the returned record has `outcome_conflict == True`; a companion assertion with a genuinely integrated lane (plan in `executed/`) returns `"executed"` with no conflict. Include the agy-parity assertion via `-k` in the same file if colocated.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_output_classifier.py::test_five_way_classification` exits 0 showing `1 passed`; the test asserts `classify_output` returns `"tracked-publish"` for a tracked path, `"secret-local"` for a secret-rule match, `"discardable"` ONLY for an explicit discard-rule match, `"local-retain"` for a retain-rule match, and `"unknown"` for an untracked path with no matching rule (explicitly asserting a bare ignored path with no discard rule is `"unknown"`, not `"discardable"`).
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_output_classifier.py::test_unknown_blocks_teardown tests/test_output_classifier.py::test_local_retain_digest_mismatch_blocks_teardown` exits 0 showing `2 passed`. ADVERSARIAL guard: `test_unknown_blocks_teardown` builds a lane with one `unknown` untracked file, calls the driver pre-teardown path, and asserts `harvest_and_teardown_gate(...)["teardown_authorized"] is False` with the file in `blocking_unknowns`, that the worktree directory STILL EXISTS after the teardown call, and that a `worktree-preserved` event was recorded; `test_local_retain_digest_mismatch_blocks_teardown` forces a copied `local-retain` dest digest to differ from source and asserts `teardown_authorized is False`. A companion fully-classified clean lane asserts `teardown_authorized is True` and teardown proceeds.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_status_note.py::test_lane_status_is_read_only tests/test_lane_status_note.py::test_lane_note_appends_advisory_only` exits 0 showing `2 passed`; `test_lane_status_is_read_only` captures `git status --porcelain` before and after `lane_status(...)` and asserts they are byte-identical and the returned dict contains the lane's classified changed paths; `test_lane_note_appends_advisory_only` calls `lane_note(...)`, asserts the note text is appended to the returned advisory submissions file, and asserts NO receipt/ledger/plan-status file changed (the receipt at `receipt_path_for(...)` is unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_status_note.py -k cli_lane_subcommands` exits 0 showing `passed`; the test invokes `python3 -m agent_workflows lane status <id6>` (exit 0, prints classified paths, `git status` unchanged before/after) and `python3 -m agent_workflows lane note <id6> --message hello` (exit 0, note appended), and asserts `python3 -m agent_workflows lane --help` output contains both `status` and `note` and the word `advisory` (or `read-only`). Plus paste the full-suite `python3 -m pytest -p no:randomly -q` result showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one authority-relocation surface (make the driver, not the worker, own the lifecycle truth) delivered as a single coordinated Phase-2 cut across the twin drivers plus the shared `ipd_lifecycle`/`lane_status` predicates; the E-items are interdependent facets of that one move (the receipt rebind is what makes driver self-finalize viable at all; the worker-role refusal closes the fork the rebind would otherwise leave open; the OBSERVED outcome is what makes an advisory outcome.json safe; the retention gate is what makes teardown safe once the driver owns the result) and are not independently shippable without leaving lifecycle authority partially in the worker's hands, so they are one cohesive exception rather than separable standard plans.

This child inherits the Set's shared anti-greenwash execution contract from orchestrator bl9q3d verbatim:

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: this child IS the xmqv5l fix; once E-01..E-03 land, its own self-finalize should no longer hit the stale refusal - V-03's regression test proves it.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.

Post-gate lifecycle move: after every V-item shows pasted passing evidence and the full suite is green, run `aw ipd lint --phase pre-transition` on this file, then `aw ipd finalize` it. Commit ONLY the Scope-Paths files, path-scoped, never push. The four mandatory adversarial guards - V-03 `test_self_execution_edits_keep_receipt_current` (the xmqv5l regression), V-03 `test_scope_or_requirement_edit_invalidates_receipt` (guard-not-too-loose), V-07 `test_missing_outcome_json_still_observed` (forgetful agent still observed), and V-08 `test_fabricated_success_outcome_does_not_override_git` (lying outcome cannot override git) - must each show pasted passing output before this plan may move to executed/.
