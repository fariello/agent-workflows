# IPD: Make a tool identity mismatch fail only the item instead of aborting the run

- Date: 2026-10-12
- Kind: child
- Concern: Both host drivers still ABORT THE WHOLE RUN when the nested-`aw` tool-identity probe mismatches. `oc_runipd.run_queue` and `agy_runipd.run_queue` each carry `except ToolIdentityError: ... save_state(run_dir, state); raise` (comment "RUN-FATAL") ahead of the item-local `except DriverError`, and `runner_shared.assert_child_tool_identity` raises with the text "ABORTING RUN: nested `aw` tool-identity mismatch ... This is run-fatal by design". The maintainer ruled on 2026-10-08 (`tb6lw3` OQ-02, Option B) that the abort set is "Corrupt run ledger" ONLY and that a tool identity error is an ITEM failure, and amended spec `25kzda` 4.1 accordingly; this backlog item (`03y5g6`, `Blocks-Release: next`) is the named carrier for the code change, and Set `fixfirst` (`lxb1ew` criteria 4 and 5, `iksylm` E-04 (c)) currently records the shipped abort as the one permitted divergence from the spec.
- Scope: Replace the run-fatal arm in BOTH `run_queue` loops with one shared item-local handler (`runner_shared`) that marks only the offending item failed (`fail-gate`, refusal code `tool-identity-mismatch`), closes its open attempt, records an event, and lets the loop continue so `cascade_dependency_blocked` stops its dependents and independent items still dispatch; reword the `ToolIdentityError` message so it no longer claims to abort; update the existing tests that assert or rely on the abort; add behavioral tests on both hosts; update the stale run-fatal comments; record the change in the CHANGELOG, in spec `25kzda`'s history, and in the stale C-10 row of to-review spec `llbr2b`. The tool-identity PROBE itself (what it compares, when it runs, its memo) is unchanged.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_tool_identity_item_failure.py, tests/test_agy_runipd_cli.py, tests/test_action_table_runner_parity.py, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/to-review/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md, .aw/records/plans/pending/20261012-toolidfail-01-s2tn4q-make-a-tool-identity-mismatch-fail-only-the-item-instead-of.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 03y5g6
- Blocks-Release: next
- Set: toolidfail
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: s2tn4q
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010. Record: .aw/records/reviews/20261012-toolidfail-01-s2tn4q-make-a-tool-identity-mismatch-fail-only-the-item-instead-of.review.md

- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog 03y5g6; abort arms, raise site, and dependent tests measured at authoring HEAD 59cc98897.

## Goal

A nested-`aw` tool-identity mismatch fails ONLY the item whose begin step probed it: that item ends `fail-gate` with a named refusal, its dependents are cascaded, and every independent queued item still runs. The run no longer raises out of `run_queue`, which brings shipped behavior into agreement with amended spec `25kzda` 4.1 ("only corrupt run ledger aborts the run") and removes the one named divergence Set `fixfirst` records.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: shared item-local handling

- [ ] E-01 In `agent_workflows/runner_shared.py`: (a) reword the `ToolIdentityError` raised by `runner_shared.assert_child_tool_identity` so it starts "nested `aw` tool-identity mismatch; failing this item" (not "ABORTING RUN"), keeps the expected module / child resolved / probe cwd / child version lines unchanged, and replaces the closing "run-fatal by design ... Marking a single item blocked would be misleading" sentences with one stating that the item is failed without a fix-it turn, its dependents are cascaded, independent items continue, and the remedy is to fix the runner's installation (or `PYTHONPATH`) and resume with `--retry-incomplete` (spec `25kzda` 4.1, `tb6lw3` OQ-02 Option B). Leave the probe, the `tool-identity-mismatch` event, and the `_TOOL_IDENTITY_VERIFIED` memo semantics unchanged (a mismatch is still not memoized, so each later item re-probes and fails on its own if the mismatch persists). (b) Add a public helper `fail_item_on_tool_identity(run_dir, state, item, exc, *, save_state, append_jsonl, host_labels) -> None` that: sets `item["status"] = "fail-gate"`, `item["tool_identity_error"] = str(exc)`; closes the item's LAST attempt if one exists and it has no `ended_at` (tolerate an absent or empty `attempts` list) (set `ended_at = utc_now()`, `disposition = "fail-gate"`); calls `record_refusal(item, code="tool-identity-mismatch", reason=<first line of str(exc)>, remedy=f"fix the runner's installation (or PYTHONPATH) so a nested `aw` resolves this runner's own package, then re-queue with `{host_labels.command} resume --retry-incomplete <run-id>`")` (`HostLabels.command` already INCLUDES the run verb, so append only the `resume` subcommand, never a second `run`: plan `z3si7r`; measured, `aw oc run resume --help` and `aw agy run resume --help` both list `--retry-incomplete`); appends a `{"event": "ipd-tool-identity-failed", "id6": ..., "error": str(exc)}` event; calls `save_state(run_dir, state)`; prints one stderr line naming the id6 and that independent items continue.
  - Depends on: none
  - Expected outcome: `runner_shared.fail_item_on_tool_identity` exists; the raised message contains no "ABORTING RUN" and no "run-fatal"; probe behavior unchanged.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/oc_runipd.py` `run_queue`, replace the body of `except ToolIdentityError:` (currently `save_state(run_dir, state)` then `raise`) with `except ToolIdentityError as exc:` calling `runner_shared.fail_item_on_tool_identity(run_dir, state, runnable, exc, save_state=save_state, append_jsonl=append_jsonl, host_labels=runner_shared.OC_HOST_LABELS)` and falling through to the next loop iteration (no `raise`, no `break`). Keep the arm BEFORE `except DriverError` so the item is labelled by the dedicated handler rather than the generic `failed-safely` arm. Rewrite the arm's comment to cite `tb6lw3` OQ-02 Option B and backlog `03y5g6` instead of "RUN-FATAL", and update the module comment block above the `from agent_workflows.runner_shared import (ToolIdentityError as ToolIdentityError, ...)` statement (the paragraph beginning "THAT DIVERGENCE WAS A REAL DEFECT AND IS FILED AS `232wcg`", which says "a run-fatal tool-identity mismatch" and "The ABORT-RUN escalation spec 25kzda 1.4/A1 reserves for the identity class was therefore lost") so it no longer describes the mismatch as run-fatal: keep the `232wcg` history (one class is still what lets the dedicated arm catch the shared raise) and state that the dedicated arm now exists to label the item `fail-gate` with a named refusal rather than the generic `failed-safely`.
  - Depends on: E-01
  - Expected outcome: a `ToolIdentityError` from `execute_item` no longer propagates out of `oc_runipd.run_queue`.
  - Execution state: pending

- [ ] E-03 Mirror E-02 in `agent_workflows/agy_runipd.py` `run_queue` with `host_labels=runner_shared.AGY_HOST_LABELS`, and update the comment block above `from agent_workflows.runner_shared import (ToolIdentityError, assert_child_tool_identity as ...)` (the paragraph "AND THE ONE DEFINITION REALLY IS ONE NOW", which says "losing the ABORT-RUN escalation spec 25kzda 1.4/A1 reserves for the identity class") with the same rewording as E-02, and the `RuntimeError`-guard comment near `_oc_enforce_dependency_preflight` that mentions "defeat an `except ToolIdentityError` upstream" only as far as needed to stay true.
  - Depends on: E-01
  - Expected outcome: a `ToolIdentityError` from `execute_item` no longer propagates out of `agy_runipd.run_queue`; both hosts call the same helper.
  - Execution state: pending

### Task group 2: tests

- [ ] E-04 Create `tests/test_tool_identity_item_failure.py`, parametrized over both hosts (`("oc", oc_runipd)`, `("agy", agy_runipd)`), driving the REAL `run_queue` with `execute_item` patched (pattern: `tests/test_agy_runipd_cli.py::ToolIdentityAbortsTests`). FIXTURE RULE, measured at review: `run_queue` RELOADS state from disk at the top of every iteration (`state = load_state(run_dir)`), so a fake `execute_item` that mutates `status` in memory without calling the host's `save_state(run_dir, state)` leaves the item `queued` on disk and it is re-dispatched forever (a review probe of exactly that shape hit the suite's 60s hang guard; adding `mod.save_state(rd, st)` made it return). Every fake that sets a status MUST persist it (no `AW_NO_DRIVER_RESTART` override is needed once it does). Cases: (a) two INDEPENDENT queued items where the fake `execute_item`, for the FIRST item, first reproduces the real begin-step precondition (F-02) by appending an OPEN attempt (`{"number": 1, "started_at": <ts>}`, no `ended_at`), setting `status = "running"` and persisting, then raises `runner_shared.ToolIdentityError`; and for the second sets `status = "executed"` and persists: `run_queue` RETURNS (no exception), both id6s were dispatched in order, the first is `fail-gate` with `refusal.code == "tool-identity-mismatch"`, a `tool_identity_error` key, and its last attempt now carries `ended_at` and `disposition == "fail-gate"`, the second is `executed`, `events.jsonl` contains exactly one `ipd-tool-identity-failed` event for the first id6, and the returned exit code is `1` (`run_exit_code` yields 1 for one `fail-gate` plus one `executed`, re-measured at review). (b) a second item that DEPENDS on the first, expressed as the queue entry's `"dependencies": ["executed:<first>"]` field (re-measured at review: with this field and a first item that fails item-locally, both hosts' `cascade_dependency_blocked` writes `fail-depend` and the second is never dispatched): assert it is never dispatched and ends `fail-depend` (accept legacy `dependency-blocked` too, as membership in the pair, since `cascade_dependency_blocked`'s docstring still names the legacy token). (c) the real `runner_shared.assert_child_tool_identity` with `_TOOL_IDENTITY_VERIFIED` cleared (snapshot and restore it in teardown, since the memo is module-global and an earlier test in the same xdist worker may have filled it, which would make the function return early and the case pass vacuously) and `runner_shared.subprocess.run` patched (scoped `mock.patch.object`) to return a `CompletedProcess` whose stdout names a foreign `.../agent_workflows/__init__.py`: it raises `ToolIdentityError` whose message does NOT contain "ABORTING RUN" and DOES contain "failing this item", writes a `tool-identity-mismatch` event, and leaves the memo empty. No source reading, inspect, or ast (P16).
  - Depends on: E-02, E-03
  - Expected outcome: new file passes post-fix; cases (a) and (b) fail against pre-fix code (the exception propagates out of `run_queue`).
  - Execution state: pending

- [ ] E-05 Rewrite `tests/test_agy_runipd_cli.py::ToolIdentityAbortsTests::test_tool_identity_aborts` (it asserts `with self.assertRaises(agy_runipd.ToolIdentityError)` and that only `agy001` is dispatched) as `ToolIdentityFailsItemTests::test_tool_identity_fails_only_the_item`, asserting `run_queue` returns, both items are dispatched in order (`["agy001", "agy002"]`), and the first is `fail-gate` with `refusal.code == "tool-identity-mismatch"`. Keep the existing fake raising for EVERY item (both then end `fail-gate`, each persisted by the shared helper, so the loop terminates with no fake-side `save_state`); assert the second's status too, so the test also shows a persistent mismatch fails each item individually rather than aborting.
  - Depends on: E-03
  - Expected outcome: the rewritten test passes post-fix and asserts the item-local behavior.
  - Execution state: pending

- [ ] E-08 Replace the stop device in `tests/test_action_table_runner_parity.py::test_consumer_retry_incomplete_requeue_exclusion`, which raises `runner_shared.ToolIdentityError("stop dispatch")` under `contextlib.suppress(runner_shared.ToolIdentityError)` only to halt dispatch (after E-02/E-03 that raise no longer escapes and the item would become `fail-gate`, breaking its `fld_entry["status"] == "queued"` assertion), with a test-local `class _StopDispatch(Exception)` that no `run_queue` arm catches, leaving every assertion unchanged. (Measured at review: this exact substitution, applied to a scratch copy of the test against CURRENT code, passes on both hosts, `1 passed`, so the device is sound before and after E-02/E-03.)
  - Depends on: E-02, E-03
  - Expected outcome: the parity test passes post-fix on both hosts with unchanged assertions.
  - Execution state: pending

### Task group 3: records and user-facing note

- [ ] E-06 Add one `- Fixed:` line to the pending 2.0.0 section of `CHANGELOG.md`: a mismatch between the runner's own `agent_workflows` package and the one a nested `aw` call would load now fails only the affected item (with a `tool-identity-mismatch` refusal) instead of stopping the whole `aw oc run` / `aw agy run`; other independent items keep running. User-facing prose: no em or en dashes.
  - Depends on: E-02, E-03
  - Expected outcome: CHANGELOG carries the line; a dash check on it finds nothing.
  - Execution state: pending

- [ ] E-07 Record the spec reconciliation: (a) run `aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "Code conformed to the 4.1 abort set by plan s2tn4q (backlog 03y5g6): a runner tool-identity mismatch now fails only the item (fail-gate, refusal tool-identity-mismatch); the shipped run abort named as a divergence by Set fixfirst is removed"` (history only; no normative text changes, since 4.1 and 5.5 already state the ruled behavior). (b) In to-review spec `llbr2b`, rewrite the `C-10` row of its constraint table (currently it locates the check in `oc_runipd` by a stale line offset and ends "Explicitly run-fatal today rather than item-local, and that is correct") so the location cites `runner_shared.assert_child_tool_identity`, the behavior reads "item-local: the item fails `fail-gate`, independent items continue (spec `25kzda` 4.1, `tb6lw3` OQ-02 Option B, plan `s2tn4q`)", and the rationale keeps INVARIANT (the probe still gates every transition the item would perform; what changed is only the blast radius). Do not change the spec's `- Status:`.
  - Depends on: E-02, E-03
  - Expected outcome: `25kzda` carries one new history note; `llbr2b` C-10 no longer claims run-fatal.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One definition, both hosts: shared runner behavior lives in `runner_shared` and both `oc_runipd` and `agy_runipd` call it (runnerlayer `1f7xno`, backlog `cnwy8g`; the `ToolIdentityError` class itself was unified for exactly this reason, `232wcg`). Hence a shared helper rather than two inline arms.
- Refusals are written through `render_stream.record_refusal` (re-exported by `runner_shared`), which redacts absolute paths in `reason`/`remedy`; the probe message carries absolute module paths, so routing through it is required, not cosmetic.
- Canonical terminal vocabulary is `TERMINAL_STATES_CANONICAL` (statusvocab `cyamvi`); new writers use canonical tokens (`fail-gate`), not legacy aliases (`failed-safely`/`blocked`). `fail-gate` is non-retryable in `TURN_RETRY_CLASSIFICATION` (correct: a re-run turn cannot fix an installation) and IS requeued by `--retry-incomplete` (correct: a human fixes the installation and resumes).
- `cascade_dependency_blocked` runs at the top of each `run_queue` iteration, so an item left in a non-success terminal status cascades its dependents on the next pass with no extra call.
- Tests drive the real `run_queue` with `execute_item` patched (`tests/test_agy_runipd_cli.py::ToolIdentityAbortsTests`, `tests/test_action_table_runner_parity.py`); no source-reading tests (GUIDING_PRINCIPLES P16).
- Suite runs bare: `python3 -m pytest` (repo-local development contract in `AGENTS.md`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Both hosts re-raise `ToolIdentityError` out of `run_queue`. | `oc_runipd.run_queue`: `except ToolIdentityError:` / `# lanetruth Order 01 (af7i6p) E-04 / OQ-02: RUN-FATAL` / `save_state(run_dir, state)` / `raise`; `agy_runipd.run_queue`: same arm, comment "RUN-FATAL. Must precede the item-local `except DriverError`". |
| F-02 | The only raise site is the begin step of `execute_item_core`, BEFORE `driver_begin` and BEFORE lane allocation. | `runner_shared.execute_item_core`: `if self_finalize and not is_review and not is_production:` / `assert_child_tool_identity(run_dir / "events.jsonl", cwd=repo)` precedes `_call_driver_begin(...)` and the later `allocate_isolation_worktree(repo, item["id6"])`. So at raise time no plan transition happened and no lane exists; the item has an open attempt (`item.setdefault("attempts", []).append(attempt)`, `item["status"] = "running"` earlier in the same function). Item-local failure therefore has nothing to contain or reclaim. |
| F-03 | The message asserts the superseded policy. | `runner_shared.assert_child_tool_identity`: "ABORTING RUN: nested `aw` tool-identity mismatch ... This is run-fatal by design (plan af7i6p OQ-02; spec 25kzda 1.4/A1 reserves ABORT RUN for the identity/integrity class)". Spec `25kzda` 1.4 A1 now reads "`ABORT RUN` is restricted to corrupt run ledger only". |
| F-04 | The spec already states the target behavior; only code diverges. | Spec `25kzda` 4.1 "Exhaustive `ABORT RUN` set" has one row, "Corrupt run ledger"; its history line "2026-10-09 note ... tool identity error handled as item failure carrier 03y5g6"; `run_evidence.ABORT_CLASSES == ("Corrupt run ledger",)`. |
| F-05 | Two existing tests depend on the abort. | `tests/test_agy_runipd_cli.py::ToolIdentityAbortsTests` (`with self.assertRaises(agy_runipd.ToolIdentityError)`); `tests/test_action_table_runner_parity.py::test_consumer_retry_incomplete_requeue_exclusion` (`raise runner_shared.ToolIdentityError("stop dispatch")` under `contextlib.suppress(runner_shared.ToolIdentityError)`). |
| F-06 | Exit code for a mixed outcome is already nonzero. | Measured at authoring: `runner_shared.run_exit_code([{status: fail-gate}, {status: executed}], stopped=False)` returned `1`. |
| F-07 | A stale to-review spec endorses the old behavior. | Spec `llbr2b` C-10 row: "Explicitly run-fatal today rather than item-local, and that is correct". |
| F-08 | The mechanism already works for the generic `DriverError` path, so the target behavior is demonstrated, not hypothesized. | Measured at review with a scratch test driving the real `run_queue` on both hosts with `execute_item` patched to raise `runner_shared.DriverError` for the first item: independent case dispatched `['agy001', 'agy002']`, ended `[('agy001', 'failed-safely'), ('agy002', 'executed')]`, returned `1`; dependent case (`"dependencies": ["executed:agy001"]`) dispatched `['agy001']`, ended `[('agy001', 'failed-safely'), ('agy002', 'fail-depend')]`, returned `1`. The same probe hung (60s hang guard) until the fake persisted its status with `save_state`, which is why E-04 now states the fixture rule. |
| F-09 | Host comment blocks outside the two `except` arms also assert the run-fatal policy. | `oc_runipd.py` paragraph "THAT DIVERGENCE WAS A REAL DEFECT AND IS FILED AS `232wcg`": "a run-fatal tool-identity mismatch", "The ABORT-RUN escalation spec 25kzda 1.4/A1 reserves for the identity class was therefore lost"; `agy_runipd.py` paragraph "AND THE ONE DEFINITION REALLY IS ONE NOW": "losing the ABORT-RUN escalation spec 25kzda 1.4/A1 reserves". The original upper-case `rg "ABORTING RUN\|RUN-FATAL"` would not have caught these. |

## Proposed changes (ordered, validatable)

1. E-01: reword the error and add `runner_shared.fail_item_on_tool_identity` (one definition).
2. E-02 / E-03: both `run_queue` arms call it and continue, still ordered before `except DriverError`.
3. E-04 / E-05 / E-08: new two-host behavioral tests; existing abort-asserting test rewritten; parity test's stop device replaced.
4. E-06 / E-07: CHANGELOG line, `25kzda` history note, `llbr2b` C-10 row.

Alternatives considered and rejected: (i) delete the `except ToolIdentityError` arm and let `except DriverError` catch it: works mechanically (it subclasses `DriverError`) but writes the legacy `failed-safely` status, which `TURN_RETRY_CLASSIFICATION` marks retryable, and gives no named refusal, so the morning report could not distinguish an installation problem from a host crash. (ii) Mark ALL remaining items failed on first mismatch: re-creates the abort under another name and contradicts the ruling "fail ONLY that one item". Re-probing per item (the memo stays empty on mismatch) is the honest behavior: if the mismatch is transient or cwd-specific, later items succeed; if persistent, each fails individually with the same named refusal.

## Deferred / out of scope (with reason)

- Changing the probe (what it compares, the `-P` / sys.path stripping, the memo): not part of the ruling; the probe's correctness is unchanged.
  - Carrier-Declined: not an obligation; the ruling changes only the blast radius of a mismatch, and the probe is correct as shipped, so nothing is owed.
- Updating Set `fixfirst` plans (`lxb1ew` criteria 4 and 5, `iksylm` E-04 (c) and E-05): they are written conditionally ("until backlog `03y5g6` lands"), so the executor of `iksylm` adapts by observation; editing another Set's reviewed plans is outside this plan's authority.
  - Carrier: iksylm
- Adding a dedicated row to spec `25kzda` 5.5's mapping table / group (b) list: the existing group (b) wording and the 4.1 ruling already cover the class, and adding a member changes the stated "(8 members)" count, a normative edit better owned by a spec-amendment plan if the maintainer wants it.
  - Carrier-Declined: no defect; 5.5 group (b) "identity or type ambiguity" and the 4.1 one-row abort table already state the ruled behavior, so a dedicated row would be editorial, and it is the maintainer's call whether to add one.

## Scope check

- Over-scope: none.
- Under-scope: none known. Review and production actions never reach the probe (`not is_review and not is_production` guard, F-02), so they need no change.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_tool_identity_item_failure.py -v`: all cases pass post-fix; cases (a) and (b) shown failing against pre-fix `oc_runipd.py`/`agy_runipd.py`. Procedure (never `git stash`, never `git checkout -- <file>` over uncommitted work): `cp` the two fixed host files to a gitignored scratch path, write the pre-fix bodies with `git show <begin-HEAD>:agent_workflows/oc_runipd.py > agent_workflows/oc_runipd.py` (same for `agy_runipd.py`), run the file and paste the failures (expected: `ToolIdentityError` propagates out of `run_queue` in (a) and (b)), `cp` the fixed files back, and paste `git diff --stat -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing the fix restored.
- `python3 -m pytest -o addopts="" tests/test_agy_runipd_cli.py tests/test_action_table_runner_parity.py tests/test_runner_shared.py tests/test_retry_class_mapping.py tests/test_runfresh_end_to_end.py tests/test_suppress_narrowing.py -q`: pass.
- Full suite bare: `python3 -m pytest`, summary line pasted.
- `rg -n -i "run-fatal|aborting run|abort-run escalation" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` and `rg -n "ABORTING RUN|run-fatal by design" agent_workflows/runner_shared.py` return nothing. (Case-insensitive on the hosts because the stale module comments say lowercase "a run-fatal tool-identity mismatch" and "the ABORT-RUN escalation"; the `runner_shared` pattern stays narrow because `runner_shared.orchestrator_refusal_text`'s docstring legitimately says "RUN-FATAL" about an unrelated raise.)

## Spec / documentation sync

- Spec `25kzda` (approved): history note only via `aw specs note` (E-07 a). WHY no normative edit: 4.1 and 5.5 already state the ruled behavior (F-04); this plan makes the code conform, and the note records the closure of the divergence the spec history names. Declared in `Scope-Paths` so the runner announces it.
- Spec `llbr2b` (to-review): C-10 row corrected (E-07 b). WHY: it asserts "run-fatal ... and that is correct", contradicting the maintainer's 2026-10-08 ruling; leaving it would let a reviewer of `llbr2b` re-derive the abort. Declared in `Scope-Paths`.
- `CHANGELOG.md`: one Fixed line (E-06).
- In-code comments in both hosts updated (E-02, E-03).

## Open questions

### OQ-01: Which terminal status should the failed item carry?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `fail-gate`, from repository evidence: it is canonical (`TERMINAL_STATES_CANONICAL`), non-retryable per turn (`TURN_RETRY_CLASSIFICATION` row "lifecycle gate or clean-base gate refused; not a host failure to retry without human action"), requeued by `--retry-incomplete`, and the refusal code `tool-identity-mismatch` distinguishes it. `failed-safely` was rejected (legacy alias, turn-retryable).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- agent_workflows/runner_shared.py` showing the reworded message and the new `fail_item_on_tool_identity`; paste the empty output of `rg -n "ABORTING RUN|run-fatal by design" agent_workflows/runner_shared.py`; paste the passing line of E-04 case (c), which observes the real `assert_child_tool_identity` raising the new message.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `except ToolIdentityError as exc:` arm from `git diff -- agent_workflows/oc_runipd.py` (no `raise`, calls the shared helper, still precedes `except DriverError`); paste the oc-host passing lines of E-04 cases (a) and (b), which drive `oc_runipd.run_queue` (dispatch observed through the patched `execute_item`), plus the same cases FAILING against pre-fix `oc_runipd.py` (procedure in Required tests); paste the empty output of `rg -n -i "run-fatal|aborting run|abort-run escalation" agent_workflows/oc_runipd.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: same as V-02 for `agent_workflows/agy_runipd.py` and the agy-host cases, including the pre-fix failure and the empty case-insensitive `rg` over `agent_workflows/agy_runipd.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste full output of `python3 -m pytest -o addopts="" tests/test_tool_identity_item_failure.py -v` post-fix (every parametrized case name visible and passing), and quote the case (a) assertions on `refusal.code`, the closed last attempt (`ended_at` present, `disposition == "fail-gate"`), the second item's `executed` status, the `ipd-tool-identity-failed` event, and the exit code `1`; and quote the case (c) memo snapshot/clear/restore so the case cannot pass on a pre-filled memo.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_agy_runipd_cli.py -q` summary (all pass) and the diff of the rewritten test showing the abort assertion replaced by the item-local assertions.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff -- CHANGELOG.md` showing the single added Fixed line, and the empty output of `git diff -- CHANGELOG.md | grep -nP "^\+.*[\x{2013}\x{2014}]"`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the new `25kzda` history line (`git diff` of the spec file shows only that addition) and the rewritten `llbr2b` C-10 row; paste `aw specs check` output for both spec paths (conforming), and the full suite bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_action_table_runner_parity.py -q` summary (all pass) and the diff of that test showing only the stop-device change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Reviewers should push hardest on F-02 (that nothing needs containment because the raise precedes begin and lane allocation) and on the pre-fix failure of E-04 (a)/(b), so the new tests cannot pass vacuously.

Execution contract: open questions: all resolved (OQ-01). Scope fence: `Scope-Paths` is a declaration; an out-of-scope edit that proves necessary is made and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Commit only the paths in `Scope-Paths` through `aw commit s2tn4q -- <paths>`, never `git add -A`, never push. Verify the staged set with `git diff --cached --name-only` before committing. You MUST paste the ACTUAL runner output for every test claim (never a claimed pass you did not run); run the suite bare as `python3 -m pytest`. Lifecycle: under `aw oc run` / `aw agy run` the runner owns `aw ipd begin` and `aw ipd finalize`, so do not call them yourself; when executing by hand, run `aw ipd begin s2tn4q` before E-01 and `aw ipd finalize` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Backlog `03y5g6` is not set `done` by authoring; it closes via the From-Backlog handoff once this plan is executed, carrying `Blocks-Release: next`.
