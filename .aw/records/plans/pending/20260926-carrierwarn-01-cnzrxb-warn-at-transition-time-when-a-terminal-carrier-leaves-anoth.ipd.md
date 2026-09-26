# IPD: Warn at transition time when a terminal carrier leaves another plan's obligations uncarried

- Date: 2026-09-26
- Kind: child
- Concern: When a plan or backlog item that a pending plan names as a Deferred/open-question Carrier goes terminal, the transition says nothing; the loss is found later by someone else as a check.ipd-uncarried-obligation commit refusal or a red fail-closed aw check plans CI step (main went red on 2026-09-26, fixed by hand in b20b7a74).
- Scope: IN: check_engine.find_obligations_carried_by reverse lookup reusing the existing carrier parsers and resolver; warnings plus a carrier_referrers evidence record on ipd finalize (covering orchestrator rollup), aw backlog set done|parked on both spellings, and terminal plan status sets; outcome tests; one CHANGELOG line. OUT: refusing the transition; aw attention surfacing; auto re-pointing.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_lifecycle.py, agent_workflows/backlog.py, agent_workflows/status_set.py, tests/test_carrier_reverse_lookup.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: zi2uzu
- Set: carrierwarn
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: cnzrxb

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zi2uzu: warn at finalize, rollup and backlog done/parked when another pending plan names the transitioning artifact as a Carrier.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When a plan or backlog item that other pending plans name as a `- Carrier:` goes terminal, say so AT THAT MOMENT: the transition prints (and records in its evidence) each pending plan row whose obligation just lost its carrier, so the executor can re-point it in the same turn instead of discovering it later as a `check.ipd-uncarried-obligation` refusal or a red `aw check plans` CI step. The transition WARNS; it never refuses.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reverse lookup

- [ ] E-01 Add `check_engine.find_obligations_carried_by(repo_root, id6, *, include_untracked=False) -> List[CarriedObligation]` where `CarriedObligation` is a NamedTuple `(plan_path, plan_id6, locator, line, other_live_carriers)`. Implementation: iterate pending-lane plans exactly as `check_durable_carrier` does (`_iter_type_files(repo_root, "plans", include_untracked=...)`, skipping paths without `pending` in `parts`); cheap pre-filter (skip a plan whose text does not contain `id6`); obligations from `_deferred_section_obligations(text) + _question_obligations(ipd_lint.parse(text).open_questions)`; keep an obligation when `ipd_schema.parse_carrier_ids(fields.get(CARRIER_FIELD))` good-tokens contain `id6` AND it carries no `Carrier-Evidence`/`Carrier-Declined`; compute `other_live_carriers` as the other good tokens that `_resolve_carrier(carrier_index, tok)` reports `ok` (build `_carrier_index` once, lazily, only if some plan matched). Never raises (returns `[]` on any exception, matching the module's fail-isolated shape). Also add `format_carrier_warnings(id6, rows) -> List[str]` producing one line per row: `warning: <plan filename> <locator> names <id6> as its carrier, which is now terminal; re-point it (Carrier: <live id6>), cite Carrier-Evidence, or add Carrier-Declined` and, when `other_live_carriers` is non-empty, `(still carried by <ids>)` instead of the remedy.
  - Depends on: none
  - Expected outcome: a pure, reusable reverse lookup built only from the existing parsers and resolver; no second parser.
  - Execution state: pending

### Task group 2: Call it at the three transitions

- [ ] E-02 In `ipd_lifecycle._complete_after_commit`, on the COMPLETE branch (just before the final `return FinalizeResult(EXIT_OK, ..., f"finalized {plan_id} -> executed ...")`), call `find_obligations_carried_by(repo_root, plan_id)`; store the rows in `evidence["carrier_referrers"]` (list of dicts: plan, id6, locator, line, still_carried_by) and append the `format_carrier_warnings` lines to the success message. Wrap in `try/except Exception` so a lookup failure can never turn a completed finalize into a failure. Because `run_finalize` and `status_set`'s finalize branch both print `result.message`, both CLI routes surface it.
  - Depends on: E-01
  - Expected outcome: `aw ipd finalize <B> --apply` prints one warning per pending row carried by B; exit code unchanged.
  - Execution state: pending

- [ ] E-03 Confirm, do not duplicate, the rollup path: `ipd_lifecycle.retire_orchestrator` runs the same `_finalize_transaction` under the finalize lock (the `return _finalize_transaction(` call ~:3908), which returns through `_complete_after_commit` (~:4575), so E-02's hook already fires for a rollup. Add NO second call there (it would print each warning twice). If execution finds a rollup success path that does NOT pass through `_complete_after_commit`, add the E-02 post-processing on that path only.
  - Depends on: E-02
  - Expected outcome: a rollup retirement's `FinalizeResult` carries `evidence["carrier_referrers"]` and the warning lines exactly once.
  - Execution state: pending

- [ ] E-04 In `backlog.run_set`, after the successful write (`sys.stdout.write(f"aw backlog set: {src.name} -> {new_status}\n")`) and only when `new_status in ("done", "parked")` and `item.id`, write each `format_carrier_warnings(item.id, rows)` line to stderr. In `status_set.apply_status_change` callers (the positional `aw backlog set done|parked <id6>` and `aw set done <id6>` path, inside `run_set_command`'s per-record loop after `apply_status_change` returns and `changed` is True), do the same for a `backlog` record reaching `done` or `parked`, and for a `plans` record reaching a terminal status (`superseded`/`not-executed`/`executed` via `aw ipd set`), since those also discharge a carrier. Warn only; never change the exit code.
  - Depends on: E-01
  - Expected outcome: every setter route that makes a carrier terminal warns once per affected row.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-05 Create `tests/test_carrier_reverse_lookup.py` with a git-initialised scratch repo (use `tests/support.ready_plan_text` for plan fixtures): (a) plan A (pending) with a Deferred row `- Carrier: <B id6>`; plan B pending, begun, in-scope work committed, then `ipd_lifecycle.finalize(B, apply=True)`: exit 0, `result.evidence["carrier_referrers"]` names A's row, and `result.message` contains `A`'s filename and `deferred row 1`; (b) a backlog item C named by plan A's OQ (`Status: deferred`, `- Carrier: <C id6>`); `cli.main(["backlog","set",<C path>,"--status","done","--dir",repo])` exits 0 and stderr names A's OQ id; (c) the same with A's row ALSO naming a live carrier: the warning says `still carried by`; (d) finalizing a plan no pending plan names: no `carrier_referrers` rows, message has no `warning:`; (e) a row with `- Carrier-Declined:` naming B is not reported.
  - Depends on: E-02, E-04
  - Expected outcome: five outcome tests passing.
  - Execution state: pending

### Task group 4: Record and verify

- [ ] E-06 Add one `- Added:` line to `## 2.0.0 (pending)` in `CHANGELOG.md`: finishing a plan with `aw ipd finalize`, or closing or parking a backlog item, now warns when another pending plan still names it as the carrier of deferred work or an open question, so the plan can be re-pointed before `aw check plans` fails. No em or en dashes.
  - Depends on: E-02
  - Expected outcome: one line, no dashes.
  - Execution state: pending

- [ ] E-07 Measure the cost on the real repository: time `aw backlog set <open item> --status open --dry-run` (or an equivalent read-only call of `find_obligations_carried_by(Path('.'), '<a real carrier id6>')`) warm, and record the number here; then run the bare suite `python3 -m pytest`, `python3 -m agent_workflows check plans --agent`, and `aw sanitize --agent`.
  - Depends on: E-05, E-06
  - Expected outcome: the lookup adds well under a second (the pre-filter reads ~65 pending plan files; measured at authoring: 3 ms for the substring scan; the full `_carrier_index` build is ~1 s and is only paid when some plan matches); 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Transitions WARN and `aw check` GATES: `backlog.run_set` already warns (not refuses) on parking a release blocker via `evaluate_blocking_close` `severity == "warn"`, and the durable-carrier rule's enforcement lives in `check_engine.check_durable_carrier` (wired in `check_content` ~:1118-1120) and in `aw ipd lint --phase pre-transition`.
- One evaluator, many surfaces: `evaluate_durable_carrier`, `_deferred_section_obligations`, `_question_obligations`, `_carrier_index`, `_resolve_carrier` (~:5816-5930) and `ipd_schema.parse_carrier_ids` (~:1520) are the only carrier parsers; this plan must reuse them, never re-parse.
- `FinalizeResult` (`ipd_lifecycle`, NamedTuple with `message`, `evidence`) is printed by both `run_finalize` and `status_set`'s finalize branch, and recorded by the runner for rollups.
- Tests: outcome only (maintainer standing rule); no test pins parser source or message wording beyond the plan filename and locator a human needs.
- Commit via `aw commit cnzrxb -- <paths>`; never push. Line numbers at HEAD `92679444`, approximate.

## Findings

| # | Location (HEAD 92679444) | Finding |
| --- | --- | --- |
| F-1 | backlog item `zi2uzu` body: "in that window aw check reports a clean tree while a live plan's obligations have no carrier" | FALSE. `check_durable_carrier` sweeps every pending plan on every `aw check plans` / `aw check all`, independent of which plan was touched, and `.github/workflows/tests.yml` runs `aw check plans (plan conformance; fail closed)`. So in that window `aw check` reports the finding; it is fail-closed in CI, and on 2026-09-26 it turned main red (fixed by hand in `b20b7a74`, which re-cited plan `8ud1is`'s Deferred row 1 from the executed `0yrtne` to `Carrier-Evidence`). What IS true is the item's timing point: nothing warns at the TRANSITION, so the break is discovered later by someone else (a commit refusal, or CI). |
| F-2 | `check_engine.check_durable_carrier` (~:6126), `_resolve_carrier` (~:5904) | Confirmed; the brief's ~:6083 / ~:5861-5888 shifted by ~43 lines (HEAD moved by `ooydp3`). Terminal statuses are `_CARRIER_TERMINAL_STATUSES` = executed, superseded, not-executed, done, parked, so `parked` discharges a carrier too (the brief's "done|parked" is correct). |
| F-3 | `ipd_lifecycle._complete_after_commit` success return (~:4627-4634) | Confirmed. `retire_orchestrator` (~:3636) runs the same `_finalize_transaction` under the lock (~:3908), so it reaches `_complete_after_commit` as well; E-02 therefore already covers rollups. BRIEF CLAIM REFINED: the brief lists the rollup (~:3881) as a separate call site; adding one there would double-warn, so E-03 verifies coverage instead of adding a call. |
| F-4 | measured at authoring, this repo | `check_durable_carrier(Path('.'))` returned 22 findings in ~0.9 s; `_carrier_index` ~1.1 s. A substring pre-filter over the 65 pending plans took 3 ms. So the lookup must pre-filter before building the index, or `aw backlog set done` gains ~1 s (a user-perceptible slowdown under this repo's own `bug` test). |
| F-5 | the positional `aw backlog set done <id6>` route | Goes through `status_set.run_set_command`, not `backlog.run_set` (see plan `wd6npl` F-7), so E-04 wires both. |

## Proposed changes (ordered, validatable)

1. E-01 reverse lookup plus formatter, reusing the existing parsers.
2. E-02 finalize, E-03 rollup, E-04 backlog/plan setters: warn and record.
3. E-05 outcome tests; E-06 CHANGELOG; E-07 cost measurement and suite.

## Deferred / out of scope (with reason)

- Surfacing orphaned carriers in `aw attention` (the item's second suggested shape).
  - Carrier-Declined: `aw check plans` already reports the condition tree-wide and CI fails closed on it (F-1); a third surface adds no information the transition warning plus `aw check` do not already give.
- Auto-re-pointing the orphaned row.
  - Carrier-Declined: choosing the new carrier is a judgement (another plan, evidence, or a decline with reason); the tool cannot make it.
- Making the transition REFUSE instead of warn.
  - Carrier-Declined: the obligation belongs to a DIFFERENT plan than the one transitioning, and refusing would block finishing correct work over another plan's bookkeeping; the repo precedent is that transitions warn and `aw check` gates.

## Scope check

- Over-scope: E-04 also warns on plan terminal transitions through `status_set` (`aw ipd set superseded|not-executed`), not only backlog; same concern, same call.
- Under-scope: none known.

## Required tests / validation

Outcome tests only (maintainer standing rule): `tests/test_carrier_reverse_lookup.py`, five tests asserting what an operator sees (the warning naming the affected plan and row, the recorded evidence, silence when nothing refers), through `ipd_lifecycle.finalize` and `cli.main`. No test pins parser internals. Run the suite BARE: `python3 -m pytest`. E-07 records the measured cost so a reviewer can dispute the number.

## Spec / documentation sync

No `.spec.md` is amended: the durable-carrier contract (plan `rnkqrc`, enforced by `check_durable_carrier`) is unchanged; this adds an advisory at transition time. `CHANGELOG.md` gains one line (E-06).

## Open questions

### OQ-01: Warn or refuse at the transition?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Warn, per the maintainer's brief and the repository precedent (transitions warn, `aw check` gates; e.g. `backlog.run_set` warns on parking a release blocker). The enforcement already exists in `aw check plans`, fail-closed in CI (F-1).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "from pathlib import Path; from agent_workflows import check_engine as ce; print(ce.find_obligations_carried_by(Path('.'), '<id6 named as a Carrier by some pending plan here>'))"` listing that plan's row, and the same call with an id6 no plan names printing `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste test (a) and (d) from E-05 passing (node ids), and the `result.message` text from (a) as printed by the test (or by a scratch `aw ipd finalize ... --apply` run) showing the warning line with A's filename and `deferred row 1`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a scratch run (or a test in `tests/test_carrier_reverse_lookup.py`, added if needed) of `ipd_lifecycle.retire_orchestrator(..., apply=True)` on an orchestrator whose id6 a pending plan names as carrier, showing `exit_code 0`, `evidence["carrier_referrers"]` non-empty, and each warning line appearing exactly once in `result.message`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste test (b) and (c) passing, plus a scratch run of the POSITIONAL `aw backlog set done <C id6> --yes --no-commit` showing the same warning on stderr and exit 0.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_carrier_reverse_lookup.py -o addopts="" -v` showing 5 passed (6 if V-03 added one).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff CHANGELOG.md` showing one added `- Added:` line and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the timing command and its output (warm, three runs) for the reverse lookup on this repository, the final summary line of a BARE `python3 -m pytest` showing 0 failed, and exit codes of `python3 -m agent_workflows check plans --agent` (no new finding naming a touched file) and `aw sanitize --agent` (0).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one reverse lookup and the three transition families that can discharge a carrier; each call is a warning and an evidence record, no behavior gate.

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: new advisory output on `aw ipd finalize`, orchestrator rollup, `aw backlog set done|parked`, and terminal `aw ipd set`, naming pending plans whose carrier just went terminal; a new `carrier_referrers` evidence key on `FinalizeResult`; five outcome tests; one CHANGELOG line. No exit code changes.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`; within `check_engine.py` only the new function(s) beside the carrier helpers, within `ipd_lifecycle.py` only `_complete_after_commit` and `retire_orchestrator`, within `backlog.py` only the tail of `run_set`, within `status_set.py` only `run_set_command`'s per-record loop. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Genuine stop condition: a co-worker's concurrent edit to `backlog.run_set` (plans `wd6npl` and `2yqt0a` also edit it) that cannot be safely combined; the runner isolates lanes, so this applies only to hand execution.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit cnzrxb -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize cnzrxb --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). Backlog `zi2uzu` carries no `- Blocks-Release:`; after execution set it `done` with `--evidence` citing the executed plan.
