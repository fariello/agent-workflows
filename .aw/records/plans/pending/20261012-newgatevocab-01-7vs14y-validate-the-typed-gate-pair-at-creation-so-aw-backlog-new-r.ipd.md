# IPD: Validate the typed gate pair at creation so aw backlog new refuses an invalid Gate-Kind or Gate-Ref

- Date: 2026-10-12
- Kind: child
- Concern: `aw backlog new --status blocked` writes a typed gate pair OUTSIDE the closed vocabulary, producing a record that the at-rest checker reports as a violation from the moment it is born. RE-MEASURED 2026-10-12 at lane HEAD `fb0072a17` in a scratch repo: `--gate-kind bogus-kind --gate-ref x` exits 0 and writes `- Gate-Kind: bogus-kind`; `--gate-kind date --gate-ref notadate` exits 0 and writes the malformed ref; `aw backlog check` on the result then exits 1 with `backlog.gate-kind-invalid` and `backlog.gate-ref-invalid`. CAUSE: `backlog.run_new` checks only presence (`if status == "blocked" and (not item.gate_kind or not item.gate_ref)`) and never consults `attention_contract.GATE_KINDS` or `attention_contract.validate_gate_ref`, although the at-rest validator `backlog.validate_item` checks both and the SET verbs were already closed by executed plan `ju3rhs` through the shared `attention_contract.validate_gate_flags`.
- Scope: IN: make `backlog.run_new` consume the existing shared validator `attention_contract.validate_gate_flags` for a `blocked` item, so an out-of-vocabulary kind or a kind-invalid ref is refused at the point of typing with rc 2 and no file written; pin that with behavioral tests driving the real CLI; record the fix in `CHANGELOG.md`. OUT (reasons under "Deferred"): adding a `--gate-summary` flag to `aw backlog new`; validating gate flags passed with a NON-blocked status (they are never rendered, so cannot reach disk); `aw specs new` and `aw ipd scaffold` (neither declares `--gate-kind`/`--gate-ref`, measured); any change to `GATE_KINDS` or a per-kind ref regex.
- Scope-Paths: agent_workflows/backlog.py, tests/test_backlog_new_gate_vocabulary.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: go8ztx
- Blocks-Release: next
- Set: newgatevocab
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7vs14y
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Record: .aw/records/reviews/20261012-newgatevocab-01-7vs14y-validate-the-typed-gate-pair-at-creation-so-aw-backlog-new-r.review.md Round 1

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `go8ztx`. The item's measurement was re-reproduced at lane HEAD `fb0072a17` rather than trusted, and widened by one axis it did not record (a valid kind with a malformed ref is also written). The prerequisite the item named as sequencing (plan `ju3rhs`'s shared validator) was confirmed `executed` and its symbol `attention_contract.validate_gate_flags` present. The fix's blast radius was measured by applying the candidate edit in the lane and running 20 candidate test modules (1431 passed, 0 broken), then reverting.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw backlog new` refuse, at the point of typing, any `blocked` item whose `Gate-Kind` is outside the closed vocabulary or whose `Gate-Ref` fails its kind's validator, so the create verb can no longer write a record the at-rest checker immediately rejects, and so create and set share one gate-pair validator.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: consume the shared validator at creation

- [ ] E-01 FIRST, before any edit, run the bare suite `python3 -m pytest` at the execution HEAD and save its summary line and failing-test names as the baseline V-01 compares against. Then, in `backlog.run_new`, immediately after the existing presence check that emits `"aw backlog new: a blocked item requires --gate-kind and --gate-ref"`, add: when `status == "blocked"`, call `A.validate_gate_flags("aw backlog new", item.gate_kind, item.gate_ref)`, and on a non-None result write it to stderr and return 2. Keep the existing presence message unchanged (it is pinned by `tests/test_backlog.py` `test_new_blocked_requires_gate` only on rc, but the message is user-facing and needs no change). Do not touch any other branch.
  - Depends on: none
  - Expected outcome: `aw backlog new --status blocked --gate-kind bogus-kind --gate-ref x ... --apply` exits 2 with `aw backlog new: --gate-kind must be one of ['artifact', 'date', 'decision', 'external', 'issue', 'todo']` and writes no file; `--gate-kind date --gate-ref notadate` exits 2 with `aw backlog new: --gate-ref is invalid for kind 'date': 'notadate'` and writes no file; `--gate-kind todo --gate-ref TODO.md` still exits 0 and writes the item.
  - Execution state: pending

### Task group 2: pin the behavior

- [ ] E-02 Create `tests/test_backlog_new_gate_vocabulary.py` with outcome tests that drive `agent_workflows.cli.main` (`backlog new ... --dir <tmp> --apply`) in a temp git repo and assert on rc, stderr, and the files present under the backlog tree: (a) out-of-vocabulary kind refused, rc 2, stderr names `--gate-kind`, zero backlog files written; (b) valid kind with malformed ref (`date`/`notadate`) refused, rc 2, stderr names `--gate-ref`, zero files; (c) one valid pair per kind in `GATE_KINDS` (for example `artifact docs/x.md`, `date 2026-12-01`, `decision D12`, `external vendor-fix`, `issue https://example.com/i/1`, `todo TODO.md`) succeeds with rc 0 and the written file carries the exact `- Gate-Kind:`/`- Gate-Ref:` lines; (d) a created valid blocked item passes `aw backlog check` (rc 0), proving create and check now agree; use a `date` pair for this case so the verdict cannot depend on whether an `artifact`/`todo` ref resolves to a real file in the scratch repo; (e) `--status open` with an invalid `--gate-kind`/`--gate-ref` writes NO `- Gate-Kind:` or `- Gate-Ref:` line, asserting the at-rest safety property only and NOT the rc, so the test does not freeze the current silent discard of those flags as desired behavior. Locate written files from the path in the verb's `wrote` line (a scratch repo without `.aw/` resolves to the legacy `.agents/backlog/` root, measured at review), not from a hard-coded root. No test reads production source.
  - Depends on: E-01
  - Expected outcome: the new module passes with E-01 applied, and cases (a) and (b) fail when E-01 is reverted.
  - Execution state: pending

### Task group 3: document

- [ ] E-03 Add one `- Fixed:` line to the pending `## 2.0.0 (pending)` section of `CHANGELOG.md`, beside the existing ju3rhs entry beginning "Fixed: `aw specs set`, `aw backlog set`, and `aw set` now refuse a Gate-Kind outside the documented vocabulary", stating that `aw backlog new --status blocked` now refuses the same invalid kinds and refs instead of writing a record the checker later reports. User-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: `CHANGELOG.md` diff is exactly one added line in the pending section.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The gate vocabulary and per-kind ref grammar are owned by `agent_workflows/attention_contract.py` (`GATE_KINDS`, `validate_gate_ref`), per spec `attention-visible-backlog-tier` Section 8.4; the point-of-typing validator `attention_contract.validate_gate_flags` was added by executed plan `ju3rhs` and is already consumed by `status_set` (`_ac.validate_gate_flags("aw set", gk, gr, gs)`).
- `backlog.run_new` already validates the sibling release-exemption pair at the point of typing via `backlog.validate_release_exempt_flags`; this plan makes the gate pair follow the same pattern.
- `backlog._render_item` writes `- Gate-Kind:`/`- Gate-Ref:` only when `item.status == "blocked"`, which is why non-blocked gate flags cannot reach disk.
- Tests must assert outcomes (rc, stderr, files on disk), never production-source structure (AGENTS.md, GUIDING_PRINCIPLES P16).
- Run the suite bare: `python3 -m pytest` (repo-local development contract in AGENTS.md).
- Cite code by SYMBOL or quoted content string (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | Out-of-vocabulary kind is written on create. | At `fb0072a17`: `backlog new --dir <scratch> --summary "s bogus-kind" --status blocked --gate-kind bogus-kind --gate-ref x --priority low --work-kind chore --apply` -> `wrote .../backlog/blocked/20261012-pc86co-01-pc86co-s-bogus-kind.backlog.md`, rc=0. |
| F-02 | A valid kind with a malformed ref is ALSO written (not recorded by the item). | Same run: `--gate-kind date --gate-ref notadate` -> wrote `...z5fu23...`, rc=0. |
| F-03 | The at-rest checker rejects both at once, so create and check disagree. | `backlog check --dir <scratch>` -> `backlog.gate-kind-invalid: Gate-Kind not in [...]: 'bogus-kind'`, `backlog.gate-ref-invalid: Gate-Ref invalid for kind 'date': 'notadate'`, `2 violation(s)`, rc=1. |
| F-04 | The prerequisite the item called "sequencing" is satisfied. | `ju3rhs` lives under `.aw/records/plans/executed/` with `- Status: executed`; `attention_contract.validate_gate_flags` exists and enforces presence, `GATE_KINDS` membership, `validate_gate_ref`, and optional summary safety. |
| F-05 | Blast radius of the fix is zero existing tests. | Candidate E-01 applied in the lane, then `python3 -m pytest` over 20 modules (`test_backlog`, `test_backlog_descriptive_safety`, `test_descriptive_refusal_hoist`, `test_backlog_duplicate_guard`, `test_history_date_clock`, `test_bidi_control_rejection`, `test_descriptive_length_classes`, `test_gate_pair_validation_parity`, `test_releases`, `test_releases_cli`, `test_history_provenance`, `test_plan_priority_required`, `test_defect_report`, `test_status_set`, `test_support_section`, `test_prompts_new`, `test_specs_status_dirs`, `test_specs_releases_descriptive_safety`, `test_backlog_gate_follows_status`, `test_backlog_transition_gate`) -> `1431 passed in 13.41s`. Every existing `run_new` blocked fixture already uses a valid pair (`todo`/`TODO.md`, `artifact`/...). The probe edit was then reverted (`git status --short` empty). |
| F-06 | With the candidate fix, the three measured inputs behave as intended. | `bogus-kind x` -> `aw backlog new: --gate-kind must be one of ['artifact', 'date', 'decision', 'external', 'issue', 'todo']` rc=2; `date notadate` -> `aw backlog new: --gate-ref is invalid for kind 'date': 'notadate'` rc=2; `todo TODO.md` -> wrote, rc=0. |
| F-07 | `aw specs new` and `aw ipd scaffold` cannot reach this hole. | `aw specs new --help | grep -c gate` -> 0; `aw ipd scaffold --help | grep -c gate` -> 0. |
| F-09 | Re-measured at review (HEAD `005039ed2`, scratch repo): `bogus-kind x`, `date notadate`, `artifact docs/x.md` and `--status open --gate-kind bogus` all exit 0 and write; `aw backlog check` reports exactly the two violations of F-03; the open item carries no gate line. | Review transcript, recorded in the review record. |
| F-08 | `aw backlog new` has no `--gate-summary` flag, so `validate_gate_flags` is called with `summary=None` (its summary check is skipped, correctly). | `cli.py` `p_backlog_new` declares only `--gate-kind` and `--gate-ref`. |

## Proposed changes (ordered, validatable)

1. E-01: one guarded call to `A.validate_gate_flags` in `backlog.run_new` for `status == "blocked"`, placed after the existing presence check and before the release-exemption validation, so refusal precedes any write.
2. E-02: new outcome test module covering refusal of a bad kind, refusal of a bad ref, acceptance of every valid kind, create/check agreement, and the unchanged non-blocked path.
3. E-03: one CHANGELOG line.

## Deferred / out of scope (with reason)

- `--gate-summary` on `aw backlog new`: a feature, not part of this defect; the item does not ask for it.
  - Carrier-Declined: Not owed. No defect exists without the flag (summary is optional at rest), and nobody has asked for it; filing a carrier would schedule unrequested feature work.
- Validating `--gate-kind`/`--gate-ref` passed with a non-blocked `--status`: `_render_item` writes the gate only for `blocked`, so such values never reach disk and the contract is not violated; E-02(e) pins only that safety property (no gate line on disk), leaving a future refusal of the discarded flags free to land without a test rewrite.
  - Carrier-Declined: Not owed. The values are discarded before render, so no invalid record can result; there is no defect to carry.
- `aw specs new` / `aw ipd scaffold`: measured (F-07) to declare no gate flags, so the hole is unreachable there.
  - Carrier-Declined: Not owed. Measured unreachable (F-07); there is no surface to fix.
- Changing `GATE_KINDS` or any per-kind regex: owned by spec Section 8.4, not in question here.
  - Carrier-Declined: Not owed. No change to the vocabulary is proposed or needed by this defect.

## Scope check

- Over-scope: none.
- Under-scope: none known. The existing presence message is retained; if the executor finds a test asserting stderr text that the new refusal changes, that test is in-scope repair and must be declared at finalize with `--scope-reason`.

## Required tests / validation

- New module `tests/test_backlog_new_gate_vocabulary.py` passes, and fails on cases (a)/(b) with E-01 reverted (V-01, V-02).
- `aw backlog check` agrees with `aw backlog new` on a valid blocked item (V-02).
- Full bare suite `python3 -m pytest` shows no new failures versus the pre-change baseline measured at the same HEAD (V-01).
- `aw ipd lint` conforms; `aw check` introduces no new finding.

## Spec / documentation sync

- Specs: N/A. Spec `attention-visible-backlog-tier` Section 8.4 already defines the closed gate vocabulary; this plan makes one verb conform to it and changes no contract, so no `.spec.md` is touched or listed in Scope-Paths.
- Docs: `.aw/records/backlog/README.md` already lists `--gate-kind --gate-ref` on `aw backlog new` and needs no change. `CHANGELOG.md` updated by E-03.

## Open questions

### OQ-01: Should the new refusal replace the existing presence-only message?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `validate_gate_flags` would emit `aw backlog new: requires --gate-kind and --gate-ref` for a missing pair, which is less specific than the existing `a blocked item requires --gate-kind and --gate-ref`. Keeping the presence check first preserves that message and adds only the vocabulary/ref refusal, the least disruptive option. Evidence: F-05 (no test breaks either way).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste (1) the `git diff agent_workflows/backlog.py` showing only the added guarded `A.validate_gate_flags` call in `run_new`; (2) the actual CLI transcript, produced by `backlog.run_new` via `python3 -m agent_workflows backlog new --dir <scratch> ... --apply`, for `bogus-kind x` (rc 2, `--gate-kind must be one of` message), `date notadate` (rc 2, `--gate-ref is invalid` message), and `todo TODO.md` (rc 0, `wrote`), plus a listing of the scratch backlog tree showing only the valid item exists; (3) the tail of the bare `python3 -m pytest` run including its `N passed` summary, with any failure compared against a baseline run at the same HEAD before E-01.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the actual runner output of `python3 -m pytest -o addopts="" tests/test_backlog_new_gate_vocabulary.py -v` showing every case passing, AND the output of the same command with E-01 temporarily reverted showing cases (a) and (b) failing (then restore E-01 and paste `git diff --stat` proving it is back).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff CHANGELOG.md` showing exactly one added `- Fixed:` line in the `## 2.0.0 (pending)` section that names `aw backlog new` and contains no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any execution. It carries `- Blocks-Release: next` inherited from backlog `go8ztx` because it fixes a live bug (AGENTS.md: we do not ship known bugs). It depends on no pending plan: its only prerequisite, `ju3rhs`, is already `executed` (F-04). The change makes previously-accepted input refuse, which is the point; F-05 found no existing test or fixture relying on an invalid pair at creation.

Open questions: OQ-01 is resolved; none remain. Start with `aw ipd begin 7vs14y`. Execution contract (AGENTS.md): commit ONLY the files this plan changed, limited to its declared `Scope-Paths` plus any under-scope repair declared at execution time, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste ACTUAL runner output for every test claim. Verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed commit attempt.

SCOPE FENCE: `- Scope-Paths:` is a declaration so finalize can reconcile what was edited against what was declared, not a stop condition; an out-of-scope edit the work genuinely requires is made and justified at finalize with `--scope-reason`, and a declared-but-unmodified path is acknowledged with `--scope-ack`. STOP and report only for a genuinely unsafe condition, such as an unresolvable concurrent edit to `agent_workflows/backlog.py` or an absent `attention_contract.validate_gate_flags`.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` above must carry pasted evidence with a non-pending `Result` before the plan moves to `.aw/records/plans/executed/`. Under `aw oc run` / `aw agy run` the RUNNER performs the finalize and the move; executed by hand, the executor performs it via `aw ipd finalize 7vs14y`, and the executor must NOT run it under a runner. Never hand-edit the status line or hand-move the file, and never tag or release. Do NOT set backlog item `go8ztx` to any status: this plan is its release-gate carrier, and the item's close is governed by the handoff rule once this plan is executed.
