# IPD: Require an executed carrier before a release-blocking backlog item closes done on the handoff route

- Date: 2026-09-26
- Kind: child
- Concern: THE HANDOFF ARM OF THE CLOSE-LEGITIMACY PREDICATE CLOSES A RELEASE-BLOCKING ITEM `done` ON THE MERE EXISTENCE OF A PLAN. `check_engine.evaluate_blocking_close`'s `done` branch returns `legitimate=True, path="HANDOFF"` as soon as `find_from_backlog_artifacts` yields ANY plan or spec carrying `- From-Backlog: <item>` with the same `- Blocks-Release:`, whatever that carrier's lifecycle state. So an item can be closed the moment a plan is AUTHORED, before a line of its code exists, and closed even when the plan covers only part of the item. Measured on the live case that motivated backlog `rwhbci`: `x7wfyx` was closed `done` on 2026-09-22 (commit `0c5b4074`) citing plan `dy9ymn` while `dy9ymn` was still pending and whose Scope says it "EXCLUDES telling the agent its remaining turn budget, which is x7wfyx's other half"; `dy9ymn` did not execute until 2026-09-23 (`f1eb82fa`), and `x7wfyx` had to be hand-reopened to `graduated` on 2026-09-24. Re-measured at HEAD `f46b6775` on a scratch repo (F-1): a `graduated` gated item whose only carrier is a pending plan closes `done` through `aw backlog set <id> --status done` with exit 0. This contradicts the repo's own lifecycle language (`graduated` "means the design is handed off while `done` means the code is written and validated").
- Scope: IN: (a) in `evaluate_blocking_close`'s HANDOFF arm, accept a carrier only if it is in a terminal EXECUTED state (a plan under an `executed/` directory; a spec whose `- Status:` is `implemented`), per the maintainer's 2026-09-26 ruling (OQ-01); when same-gate carriers exist but none is executed, REFUSE with a reason and fixes that steer to `graduated`; (b) keep SATISFIED (`--evidence`) and DE-GATED unchanged, and keep `graduated` legitimate; (c) align the WARN-severity `check.orphaned-live-blocker` remedy text in `check_engine.release_gate_warnings`, which today tells the operator to `aw backlog set done` an item whose plan merely exists, i.e. the exact close this plan refuses; (d) update the repo-local "Close-legitimacy rule" paragraph in AGENTS.md (BELOW the managed block) and the backlog README where it describes HANDOFF; (e) behavioral tests through `aw backlog set` on scratch repos. OUT: plan-SCOPE coverage analysis (OQ-02); the positional-spelling bypass (F-5, Deferred); the runner's own close path (`runner_shared.evaluate_backlog_close`, already stricter).
- Scope-Paths: agent_workflows/check_engine.py, AGENTS.md, .aw/records/backlog/README.md, agent_workflows/cli.py, tests/test_check_engine_release_gate.py, tests/test_backlog_handoff_close.py, .aw/records/backlog/open/*-posgate-01-*.backlog.md
- Item-Dependencies: executed:ooydp3
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: rwhbci
- Blocks-Release: next
- Set: closescope
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2a6phj

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog rwhbci on the maintainer's 2026-09-26 ruling that a HANDOFF may close a release-blocking item done only when the citing plan is EXECUTED (OQ-01). Re-measured at HEAD f46b6775: a graduated gated item with only a PENDING same-gate plan closes done via `aw backlog set <id> --status done` (exit 0). Ordered after ooydp3, which rewrites the same carrier_br == blocks_release comparison.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A release-blocking backlog item can reach `done` through the HANDOFF route only once a carrier plan has actually executed (or a carrier spec is implemented); until then the item stays `graduated`, the release gate stays visibly outstanding, and every surface that shares the predicate says so.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce and prove the failure

- [ ] E-01 RE-MEASURE at the executing HEAD, AFTER `ooydp3` has executed (it replaces the `carrier_br == blocks_release` test with a resolved-release comparison, so read the HANDOFF arm fresh and edit what is there, not what this plan quotes). Build a scratch git repo with one `planned` release `rel001`, a `graduated` backlog item `item01` carrying `- Blocks-Release: next`, and a plan under `.aw/records/plans/pending/` carrying `- From-Backlog: item01` and `- Blocks-Release: next`; commit. Run `aw backlog set item01 --status done --dir <repo> --message close` and paste the exit code and the item's resulting directory. Also paste `check_engine.evaluate_blocking_close(repo, <item path>, "done")` (its `legitimate` and `path` fields). If the close is already refused, STOP and report.
  - Depends on: none
  - Expected outcome: exit 0; the item moves to `backlog/done/`; the verdict is `legitimate=True, path='HANDOFF'`.
  - Execution state: pending

- [ ] E-02 ADD `tests/test_backlog_handoff_close.py` (new) BEFORE the fix, behavior only (no source-text or AST pins, per the 2026-09-26 test-policy ruling), each case on its own `git init` scratch repo in a `TemporaryDirectory` built as in E-01 and driven through `cli.main(["backlog", "set", "item01", "--status", ..., "--dir", repo, "--message", ...])`: (1) PENDING same-gate plan only -> `done` REFUSED (rc 1), the item file STILL in `graduated/`, and stderr names `graduated` as the remedy; (2) the same plan moved to `plans/executed/` (with `- Status: executed`) -> `done` allowed (rc 0, item in `done/`); (3) PENDING plan, target `graduated` from `open` -> allowed (rc 0); (4) SPEC carrier: a spec under `specs/approved/` with `- Status: approved`, `From-Backlog: item01` and the same gate -> refused; the same spec with `- Status: implemented` under `specs/implemented/` -> allowed; (5) TWO carriers, one pending and one executed -> allowed (OQ-03); (6) SATISFIED unchanged: pending plan only, `--evidence <an in-tree records path>` -> allowed; (7) DE-GATED unchanged: pending plan only, `--blocks-release -` in the same call -> allowed; (8) a SUPERSEDED or NOT-EXECUTED plan as the only carrier -> refused (terminal is not executed). Isolate `AW_HOME` and `XDG_CONFIG_HOME` to temp dirs.
  - Depends on: E-01
  - Expected outcome: cases (1), (4)-refused-half and (8) FAIL against the unchanged code; (2), (3), (4)-allowed-half, (5), (6), (7) PASS before and after.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 IN `check_engine.evaluate_blocking_close`, `target_status == "done"` branch, HANDOFF arm: among the same-gate carriers from `find_from_backlog_artifacts`, return the HANDOFF verdict only if at least one is EXECUTED. Define executed with a small module-level helper (for example `_carrier_is_executed(path)`) reading the facts the tree already records: a plan (`.ipd.md`) whose path has an `executed` directory segment, or a spec (`.spec.md`) whose `_status_meta` is `implemented`. Do NOT use `is_retired`: it is also True for `superseded`, `not-executed`, `parked` and `done`, which are terminal but not finished (case 8). Keep the arm's ordering relative to SATISFIED and DE-GATED unchanged. Update the docstring's `HANDOFF` line accordingly and cite the 2026-09-26 ruling and backlog `rwhbci`.
  - Depends on: E-02
  - Expected outcome: E-02 cases (1), (4) and (8) now pass; every other case still passes.
  - Execution state: pending

- [ ] E-04 GIVE THE NEW REFUSAL ITS OWN REASON AND FIXES. When same-gate carriers exist but none is executed, and neither SATISFIED nor DE-GATED applies, return `CloseVerdict(False, "error", ...)` whose reason names the unexecuted carrier path(s) and says the gate is handed off but the work has not shipped, and whose FIRST fix is `aw backlog set <item> --status graduated` (keep the item as a release blocker until the plan executes), followed by the existing evidence and de-gate fixes. Keep the no-carrier refusal's existing wording unchanged. `backlog.run_set` already prints `verdict.reason` and each fix, so no caller edit is needed; confirm by reading it.
  - Depends on: E-03
  - Expected outcome: E-02 case (1)'s stderr contains `graduated` and the pending plan's filename.
  - Execution state: pending

- [ ] E-05 ALIGN THE TWO SURFACES THAT SHARE OR ADVERTISE THE PREDICATE. (a) `check_engine.release_gate_warnings`'s `check.orphaned-live-blocker` message currently reads "close it `done` (the gate is preserved via handoff). Fix: aw backlog set done <id6>" for any open item with a same-gate From-Backlog PLAN, executed or not; after E-03 that advice is refused for a pending plan. Make the remedy depend on the carrier: executed -> the existing `done` advice; not executed -> `aw backlog set <id6> --status graduated`. (b) The `backlog-blocking-close-gate` help text in `agent_workflows/cli.py` (the `_LEAF_HELP`-style entry containing "HANDOFF: a From-Backlog blocking plan") must say an EXECUTED From-Backlog plan. The hook and `check.blocking-item-closed-without-gate` call the same predicate, so they need no logic change; E-06 proves the rule follows. Add a test to `tests/test_check_engine_release_gate.py` for (a): an open gated item with a pending same-gate plan yields a warning whose text names `graduated`, and with an executed plan names `done`.
  - Depends on: E-04
  - Expected outcome: the new `release_gate_warnings` test passes; `aw backlog-blocking-close-gate --help` (or the leaf help) says EXECUTED.
  - Execution state: pending

- [ ] E-06 PROVE THE COMMIT-SCOPED RULE FOLLOWS, behaviorally. In `tests/test_check_engine_release_gate.py`, extend the `test_rule_blocking_item_closed_without_gate_reachable` pattern: a staged `done` gated item whose only same-gate carrier is a PENDING plan now yields `check.blocking-item-closed-without-gate` from `check_engine.check_release_gates(repo)`; the same with an EXECUTED plan yields none. Write this test before E-03 is applied if convenient, and show it failing.
  - Depends on: E-03
  - Expected outcome: pending-carrier case reports the rule; executed-carrier case is clean.
  - Execution state: pending

### Task group 3: docs, follow-up, suite

- [ ] E-07 UPDATE THE CLOSE-RULE PROSE. (a) AGENTS.md, the repo-local paragraph beginning "Close-legitimacy rule for a release-blocking backlog item" (BELOW `<!-- /aw:block -->`; do NOT edit inside the managed block): fix (1) becomes HANDOFF to an EXECUTED plan (or an implemented spec) carrying `- From-Backlog: <this id6>` and the same gate, plus one sentence that before the carrier executes the item stays `graduated`. Verified at authoring that the managed block contains no HANDOFF definition (its "Acting on a backlog item" point (5) already says `graduated`, not `done`), so `agent_workflows/engine.py` needs no change; re-grep at execution and declare it via `--scope-reason` if that has changed. (b) `.aw/records/backlog/README.md`: the "Promotion to a plan" section says "author an IPD ... then `aw backlog set <item> --status done` with a history line citing the plan id", which contradicts the `graduated` section of the same README and the ruling; change it to `graduated` at authoring and `done` after the plan executes, keeping the lifecycle-section line ("reaching `done` still requires a handoff, cited evidence, or an explicit de-gate") consistent. User-facing prose: no em or en dashes.
  - Depends on: E-05
  - Expected outcome: both documents describe the executed-carrier rule and neither tells an author to close `done` at plan authoring.
  - Execution state: pending

- [ ] E-09 FILE THE OUT-OF-SCOPE BYPASS (F-5) as a durable carrier: `aw backlog new --summary "aw backlog set done <id> (positional) skips the release-gate close predicate" --set posgate --work-kind bug --priority high --slug positional-set-skips-close-gate --blocks-release next --body "<F-5 evidence>" --apply`. Paste the id6 it mints, and replace the first Deferred row's `- Carrier-Declined:` line with `- Carrier: <that id6>`.
  - Depends on: none
  - Expected outcome: a new open backlog item exists for F-5 and the Deferred row names it as its carrier.
  - Execution state: pending

- [ ] E-08 RUN THE BARE SUITE `python3 -m pytest` before the change (at E-01) and after E-07; compare failing node IDs. Also run `python3 -m agent_workflows check release-gates --agent` on the real tree before and after and paste both, since the stricter HANDOFF can surface findings on items already staged or on live open blockers.
  - Depends on: E-07, E-09
  - Expected outcome: the after-minus-before failing node set is empty; any new `check release-gates` output is explained item by item.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One shared predicate: `check_engine.evaluate_blocking_close` backs `backlog.run_set` (the `--status` spelling), `check.blocking-item-closed-without-gate` (via `check_release_gate_consistency`), and the opt-in hook `hooks/backlog_blocking_close_gate` (which calls that rule). Changing the predicate changes all three; AGENTS.md states "so they cannot diverge".
- Carrier discovery: `find_from_backlog_artifacts` returns plans first then specs, as `(path, blocks_release)` pairs, across every lifecycle directory.
- Terminal-state vocabulary: `is_retired` treats `executed`, `superseded`, `not-executed`, `parked`, `done`, `archive`, `shipped` as retired, which is broader than "executed". The runner's own close decision (`runner_shared.evaluate_backlog_close`) already requires "every IPD carrier ... terminal `executed`" and reads the bucket with `runner_shared.plan_bucket`; this plan applies the milder "at least one executed" form the ruling names.
- `graduated` is already an explicit legitimate branch in `evaluate_blocking_close` ("`graduated` preserves gate ... `done` still requires handoff, evidence, or explicit de-gating").
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`. `tests/test_check_engine_release_gate.py` provides `_create_minimal_repo`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775` on 2026-09-26 unless noted.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `evaluate_blocking_close` HANDOFF arm | A pending same-gate plan is enough to close a gated item `done`. | scratch repo: `backlog set item01 --status done --message close` -> rc 0, `aw backlog set: ... -> done`, item now in `backlog/done/` |
| F-2 | HIGH | live history | The motivating close happened while the carrier was pending and covered half the item. | `0c5b4074 2026-09-22 backlog: close x7wfyx done on a verified gate handoff`; `f1eb82fa 2026-09-23 lifecycle(dy9ymn): finalize dy9ymn -> executed`; `x7wfyx` history `2026-09-24 graduated (aw set): ... Item A outstanding` |
| F-3 | MEDIUM | `release_gate_warnings` | The WARN remedy instructs the exact close this plan refuses. | message text "close it `done` (the gate is preserved via handoff). Fix: aw backlog set done {_id6}" for any open item with a same-gate plan, no state check |
| F-4 | MEDIUM | `.aw/records/backlog/README.md` "Promotion to a plan" | Tells authors to close `done` when the IPD is authored. | "author an IPD under `.aw/records/plans/pending/`, then `aw backlog set <item> --status done` with a history line citing the plan id" |
| F-5 | HIGH | `cli` backlog `set` dispatch -> `status_set.run_set_command` | The POSITIONAL spelling never runs the predicate at all: a gated item with NO carrier closes `done`. Out of scope here (Deferred), but it bounds what this fix protects. | scratch repo, carrier id changed to `zzzzzz`: `backlog set done item01 --yes` -> rc 0, item in `done/`; the `--status` spelling on the same repo -> rc 1 with the three fixes. Previously noted as decision D1 of executed plan `zhr6mc` ("the positional form ... does NOT run `check_engine.evaluate_blocking_close`"), and never filed as an item. |
| F-6 | INFO | `evaluate_blocking_close` SATISFIED arm | Any in-tree records path satisfies `--evidence` (e.g. the release file itself), so SATISFIED remains an honest-but-unverified escape. Unchanged by design (the ruling keeps it). | scratch repo: `--evidence .aw/records/releases/...release.md` -> allowed |

## Proposed changes (ordered, validatable)

1. E-01 re-measures on the post-`ooydp3` tree.
2. E-02 adds the behavioral close tests (failing half first).
3. E-03 requires an executed carrier in the HANDOFF arm.
4. E-04 gives the refusal a `graduated`-first remedy.
5. E-05 aligns the WARN remedy and the hook help text.
6. E-06 proves the commit-scoped rule follows the predicate.
7. E-07 updates AGENTS.md (repo-local) and the backlog README.
8. E-09 files F-5 as a backlog item.
9. E-08 bare suite and live `check release-gates` before and after.

## Deferred / out of scope (with reason)

- The positional `aw backlog set done <id>` spelling bypassing the close predicate entirely (F-5).
  - Carrier-Declined: to be replaced by the backlog item E-07 files; the id6 does not exist until E-09 runs, and E-09 requires the executor to replace this line with `- Carrier: <minted id6>`. It is a separate dispatch-path defect with its own tests, and fixing it here would widen this plan past the ruling.
- Checking that a citing plan's SCOPE covers the whole item (the original question in `rwhbci`).
  - Carrier-Declined: superseded by the maintainer's 2026-09-26 ruling (OQ-02), which answers the obligation-tracking hole by timing (close only after execution) rather than by prose analysis of Scope text, which no deterministic predicate can do reliably.

## Scope check

- Over-scope: none. E-05 and E-07 are required consequences: without them two shipped surfaces (the WARN remedy and the README) instruct a close the predicate refuses.
- Under-scope: `agent_workflows/backlog.py`, `agent_workflows/hooks/backlog_blocking_close_gate.py`, and `agent_workflows/engine.py` are deliberately NOT declared: the first prints whatever reason and fixes the verdict carries, the hook delegates to the rule, and the managed block has no HANDOFF definition (verified by grep at authoring).
- Scope-Paths justification: `check_engine.py` (predicate and WARN text), `cli.py` (hook help text only), AGENTS.md (repo-local paragraph), backlog README, two test files, and the new backlog item E-09 files.

## Required tests / validation

- `tests/test_backlog_handoff_close.py` (new): eight end-to-end cases through `aw backlog set --status`; refused halves shown FAILING before E-03.
- `tests/test_check_engine_release_gate.py`: WARN remedy per carrier state; commit-scoped rule follows the predicate.
- `python3 -m pytest tests/test_backlog_handoff_close.py tests/test_check_engine_release_gate.py tests/test_backlog.py tests/test_status_set.py -o addopts="" -q`.
- Bare `python3 -m pytest` before and after; `check release-gates --agent` before and after.

## Spec / documentation sync

- No `.spec.md` is edited. The close rule is stated in AGENTS.md (repo-local section) and the backlog README, both declared; spec `llbr2b` (to-review) describes HANDOFF as "a `From-Backlog` plan or spec carrying the SAME `Blocks-Release`" in its inventory table, which is a description of shipped behavior that its own review will refresh, and it is not an approved contract this plan must amend. Draft spec `pqsx96`'s I-07 row likewise describes rather than prescribes.
- AGENTS.md is edited ONLY below the managed block; the managed source `engine.py` carries no HANDOFF definition (checked), so no managed text changes.

## Open questions

### OQ-01: May a HANDOFF close a release-blocking item `done` before the citing plan executes?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: NO. Maintainer ruling 2026-09-26 (recorded on backlog `rwhbci` during batch graduation): "a HANDOFF may close a release-blocking item done only when the citing plan is EXECUTED; before that the item stays graduated. Implement in check_engine.evaluate_blocking_close and amend the AGENTS.md close rule."

### OQ-02: Should the predicate also check that the plan's Scope covers the whole item?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No, resolved by the OQ-01 ruling. The `x7wfyx` failure was a close at authoring time; under the ruling the item stays `graduated` until execution, and the residual half-coverage case is caught by the durable-carrier rule (`check.ipd-uncarried-obligation`), which is what flagged `dy9ymn` in the first place.

### OQ-03: With several same-gate carriers, is ONE executed carrier enough, or must ALL be executed?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: ONE, from the ruling's wording ("only when the citing plan is EXECUTED", singular) and the maintainer's instruction text for this graduation ("require at least one citing plan (or spec) in a terminal EXECUTED state"). The runner's stricter all-IPD-carriers rule (`runner_shared.evaluate_backlog_close`) is left as is; the manual setter is deliberately the milder gate so a human can close an item whose remaining carriers were retired. E-02 case (5) pins it; tightening later is a one-line change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the scratch-repo `aw backlog set ... --status done` exit code and output, the item's resulting path, and the `evaluate_blocking_close` verdict fields; paste the current HANDOFF-arm lines as read after `ooydp3`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_backlog_handoff_close.py -o addopts="" -q` BEFORE E-03 with cases (1), (4)-refused and (8) FAILING and the rest passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the predicate diff and the same pytest command passing in full after E-03, with the count.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the stderr of E-02 case (1) after the change, showing the reason, the pending plan's filename, and `--status graduated` as the first fix.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `release_gate_warnings` and help-text diffs, the new warning test passing, and the rendered help line containing EXECUTED.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_check_engine_release_gate.py -o addopts="" -q` passing, and the pending-carrier case failing against the pre-E-03 predicate.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the AGENTS.md diff (showing it lies below `<!-- /aw:block -->`), the backlog README diff, and the `rg -n HANDOFF agent_workflows/engine.py` result re-confirming no managed text changes.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and both `check release-gates --agent` outputs with any new finding explained.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the `aw backlog new` output with the minted id6, `aw backlog check` clean for it, and the Deferred row diff now carrying `- Carrier: <that id6>`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The HANDOFF route to `done` for a release-blocking backlog item now requires a carrier that has actually shipped (a plan in `executed/`, or an `implemented` spec); before that, `aw backlog set --status done` refuses and points at `graduated`. SATISFIED (`--evidence`) and DE-GATED (`--blocks-release -`) are unchanged. Because one predicate backs the setter, `aw check`'s commit-scoped rule and the opt-in hook, all three tighten together; the advisory WARN, the hook help, the AGENTS.md repo-local rule and the backlog README are aligned. A separate, more serious bypass found while measuring (the positional `aw backlog set done` spelling skips the predicate entirely) is FILED, not fixed. Implements the maintainer's 2026-09-26 ruling, graduates backlog `rwhbci`, inherits `- Blocks-Release: next`, and runs after `ooydp3`, which rewrites the same comparison.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `check_engine.py`, `evaluate_blocking_close`'s `done` branch plus one helper, and `release_gate_warnings`' message; in `cli.py`, the `backlog-blocking-close-gate` help string only; the AGENTS.md paragraph below the managed block; the backlog README's two HANDOFF passages; two test files; one new backlog item. An edit outside the declared paths, if one proves necessary, is made and then justified at finalize with `--scope-reason` per out-of-scope path; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-02 must show the refused cases FAILING before the fix.

GENUINE STOP CONDITION: if E-01 finds the HANDOFF close already refused for a pending carrier (for example because `ooydp3` changed it), retire this plan rather than execute it.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `rwhbci` `done` with `--evidence` citing the executed plan: under the rule this plan ships, that close is legitimate exactly because this plan is then executed.
