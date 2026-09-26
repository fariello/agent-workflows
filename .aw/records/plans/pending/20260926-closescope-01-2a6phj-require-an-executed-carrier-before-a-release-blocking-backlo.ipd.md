# IPD: Require an executed carrier before a release-blocking backlog item closes done on the handoff route

- Date: 2026-09-26
- Kind: child
- Concern: THE HANDOFF ARM OF THE CLOSE-LEGITIMACY PREDICATE CLOSES A RELEASE-BLOCKING ITEM `done` ON THE MERE EXISTENCE OF A PLAN. `check_engine.evaluate_blocking_close`'s `done` branch returns `legitimate=True, path="HANDOFF"` as soon as `find_from_backlog_artifacts` yields ANY plan or spec carrying `- From-Backlog: <item>` with the same `- Blocks-Release:`, whatever that carrier's lifecycle state. So an item can be closed the moment a plan is AUTHORED, before a line of its code exists, and closed even when the plan covers only part of the item. Measured on the live case that motivated backlog `rwhbci`: `x7wfyx` was closed `done` on 2026-09-22 (commit `0c5b4074`) citing plan `dy9ymn` while `dy9ymn` was still pending and whose Scope says it "EXCLUDES telling the agent its remaining turn budget, which is x7wfyx's other half"; `dy9ymn` did not execute until 2026-09-23 (`f1eb82fa`), and `x7wfyx` had to be hand-reopened to `graduated` on 2026-09-24. Re-measured at HEAD `f46b6775` on a scratch repo (F-1): a `graduated` gated item whose only carrier is a pending plan closes `done` through `aw backlog set <id> --status done` with exit 0. This contradicts the repo's own lifecycle language (`graduated` "means the design is handed off while `done` means the code is written and validated").
- Scope: IN: (a) in `evaluate_blocking_close`'s HANDOFF arm, accept a carrier only if it is in a terminal EXECUTED state (a plan under an `executed/` directory; a spec whose `- Status:` is `implemented`), per the maintainer's 2026-09-26 ruling (OQ-01); when same-gate carriers exist but none is executed, REFUSE with a reason and fixes that steer to `graduated`; (b) keep SATISFIED (`--evidence`) and DE-GATED unchanged, and keep `graduated` legitimate; (c) align the WARN-severity `check.orphaned-live-blocker` remedy text in `check_engine.release_gate_warnings`, which today tells the operator to `aw backlog set done` an item whose plan merely exists, i.e. the exact close this plan refuses; (d) update the repo-local "Close-legitimacy rule" paragraph in AGENTS.md (BELOW the managed block) and the backlog README where it describes HANDOFF; (e) behavioral tests through `aw backlog set` on scratch repos. OUT: plan-SCOPE coverage analysis (OQ-02); the positional-spelling bypass (F-5, Deferred); the runner's own close path (`runner_shared.evaluate_backlog_close`, already stricter).
- Scope-Paths: agent_workflows/check_engine.py, AGENTS.md, .aw/records/backlog/README.md, agent_workflows/cli.py, agent_workflows/engine.py, tests/test_check_engine_release_gate.py, tests/test_backlog_handoff_close.py, .aw/records/backlog/open/*-posgate-01-*.backlog.md
- Item-Dependencies: executed:ooydp3
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: rwhbci
- Blocks-Release: next
- Set: closescope
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2a6phj

## Workflow history

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED, none deferred, none open; 6 decisions D-1..D-6 recorded. Reviewed at HEAD 21b22c3b, which is AFTER `ooydp3` executed, so E-01's premise was testable now and I drove it. `aw ipd lint --phase author --agent` reported `clean`/`findings: 0` before revision; the lane-input copy was byte-identical to the tracked file and the tree was clean, so no pre-review snapshot. EVERY AUTHORED FINDING REPRODUCED, several driven end to end: F-1 on a scratch repo post-`ooydp3` (`evaluate_blocking_close` -> `legitimate=True, path='HANDOFF'` with a PENDING carrier; `aw backlog set item01 --status done` rc 0 and the item moved to `done/`); F-3, F-4 and F-5 confirmed verbatim in the shipped text and by driving both `aw backlog set` spellings on one fixture (positional rc 0 with NO carrier at all, `--status` rc 1 with the three fixes). SIX SUBSTANTIVE CORRECTIONS. (1) THE PLAN'S OWN CLOSING INSTRUCTION IS REFUSED BY THE RULE IT SHIPS: the gate says to close `rwhbci` `done` with `--evidence` citing the executed plan, but measured, `rwhbci`'s ONLY carrier is THIS plan, so at close time the rule requires an executed carrier while `--evidence` is checked only AFTER the HANDOFF arm; worse, `evaluate_blocking_close` short-circuits HANDOFF BEFORE evidence, so the close's legitimacy depends on arm ORDER, which E-03 changes. New E-10 owns the self-close and the arm-order question, and the gate now states the sequence. (2) `engine.py` DOES CONTAIN A HANDOFF DEFINITION, contrary to the plan's twice-stated verified claim: the managed `_BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE`/`_BLOCK` hook comment says "HANDOFF via a From-Backlog plan" and is INSTALLED INTO EVERY MANAGED REPO, so leaving it stale ships the old rule to every target; `engine.py` added to Scope-Paths and E-07 extended. (3) THE WARN REMEDY E-05 FIXES NAMES THE BYPASS SPELLING: its `Fix:` line is `aw backlog set done <id6>`, the POSITIONAL form F-5 proves never runs the predicate, so today it advises the one route that cannot refuse; E-05 must emit the `--status` spelling. (4) BLAST RADIUS MEASURED AND ABSENT FROM THE PLAN: 45 live gated items carry a carrier, 17 keep closing and 28 would now be REFUSED; one (`ms06pi`) has a `- Status: approved` SPEC carrier, so E-02 case (4) must pin `approved` as refused (it pins only approved-vs-implemented by directory). New E-11 measures the corpus before and after. (5) E-03's `_status_meta` for specs is the right reader but the plan never says `find_from_backlog_artifacts` returns only `(path, blocks_release)` and NO status, so the helper must re-read each file; stated. (6) V-02's evidence list omitted case (5) and the SATISFIED/DE-GATED cases, and E-06 said "if convenient" for a before-failing test; both tightened. Full record: `.aw/records/reviews/20260926-closescope-01-2a6phj-require-an-executed-carrier-before-a-release-blocking-backlo.review.md`.
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
  - ALREADY RE-MEASURED AT REVIEW, POST-`ooydp3`, so treat this as confirmation rather than discovery and do NOT expect the stop condition to fire: at HEAD `21b22c3b` (after `ooydp3` executed) `evaluate_blocking_close` returned `legitimate=True, path='HANDOFF'`, reason `gate 'next' handed off to a From-Backlog plan or spec`, for a PENDING carrier, and `aw backlog set item01 --status done --yes` exited 0 moving the item to `backlog/done/`. `ooydp3` left the arm's SHAPE intact and changed only the gate comparison (`_same_release`), which is the call you will see in the arm.
  - RECORD THE ARM ORDER, because E-03 and E-10 both depend on it: the `done` branch tests DE-GATED first (no `Blocks-Release`), then HANDOFF, then SATISFIED (`--evidence`), then fails closed. HANDOFF therefore SHORT-CIRCUITS BEFORE evidence is consulted, so today a gated item with a pending carrier closes `HANDOFF` even when `--evidence` was supplied. Paste the arm order you observe; E-10 decides what it must become.
  - Execution state: pending

- [ ] E-02 ADD `tests/test_backlog_handoff_close.py` (new) BEFORE the fix, behavior only (no source-text or AST pins, per the 2026-09-26 test-policy ruling), each case on its own `git init` scratch repo in a `TemporaryDirectory` built as in E-01 and driven through `cli.main(["backlog", "set", "item01", "--status", ..., "--dir", repo, "--message", ...])`: (1) PENDING same-gate plan only -> `done` REFUSED (rc 1), the item file STILL in `graduated/`, and stderr names `graduated` as the remedy; (2) the same plan moved to `plans/executed/` (with `- Status: executed`) -> `done` allowed (rc 0, item in `done/`); (3) PENDING plan, target `graduated` from `open` -> allowed (rc 0); (4) SPEC carrier: a spec under `specs/approved/` with `- Status: approved`, `From-Backlog: item01` and the same gate -> refused; the same spec with `- Status: implemented` under `specs/implemented/` -> allowed; (5) TWO carriers, one pending and one executed -> allowed (OQ-03); (6) SATISFIED unchanged: pending plan only, `--evidence <an in-tree records path>` -> allowed; (7) DE-GATED unchanged: pending plan only, `--blocks-release -` in the same call -> allowed; (8) a SUPERSEDED or NOT-EXECUTED plan as the only carrier -> refused (terminal is not executed). Isolate `AW_HOME` and `XDG_CONFIG_HOME` to temp dirs.
  - Depends on: E-01
  - Expected outcome: cases (1), (4)-refused-half and (8) FAIL against the unchanged code; (2), (3), (4)-allowed-half, (5), (6), (7) PASS before and after.
  - CASE (4) MUST PIN THE `approved` SPEC BY ITS `- Status:` FIELD, not merely by its directory, and it is not hypothetical: measured at review, live item `ms06pi` is `graduated` with `Blocks-Release: next` and its ONLY carrier is a spec whose `- Status:` is `approved`, so this exact shape exists in the corpus today and will be refused by E-03. Assert the refusal on the `approved` spec and the allowance on the `implemented` one, and note that E-03 reads the FIELD (`_status_meta`), so a spec sitting in `specs/approved/` with an `implemented` field, or the reverse, must behave per the FIELD; add that mismatch as case (9) so the reader knows which of the two the rule trusts.
  - CASE (6) IS THE ONE MOST LIKELY TO PASS VACUOUSLY. Because the `done` branch evaluates HANDOFF BEFORE SATISFIED (E-01), a `--evidence` close with a pending carrier is allowed TODAY through HANDOFF, not through SATISFIED. So asserting only rc 0 would keep passing after E-03 for the WRONG reason, or fail if E-10 reorders the arms. Assert the verdict's `path` field is `SATISFIED` (via `evaluate_blocking_close` directly, alongside the CLI rc), so the case proves which arm allowed it.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 IN `check_engine.evaluate_blocking_close`, `target_status == "done"` branch, HANDOFF arm: among the same-gate carriers from `find_from_backlog_artifacts`, return the HANDOFF verdict only if at least one is EXECUTED. Define executed with a small module-level helper (for example `_carrier_is_executed(path)`) reading the facts the tree already records: a plan (`.ipd.md`) whose path has an `executed` directory segment, or a spec (`.spec.md`) whose `_status_meta` is `implemented`. Do NOT use `is_retired`: it is also True for `superseded`, `not-executed`, `parked` and `done`, which are terminal but not finished (case 8). Update the docstring's `HANDOFF` line accordingly and cite the 2026-09-26 ruling and backlog `rwhbci`.
  - Depends on: E-02
  - Expected outcome: E-02 cases (1), (4) and (8) now pass; every other case still passes.
  - THE HELPER MUST RE-READ THE FILE; THE CARRIER LOOKUP DOES NOT CARRY STATUS. `find_from_backlog_artifacts` returns `(path, blocks_release)` pairs ONLY (measured: both `find_from_backlog_plans` and `find_from_backlog_specs` build `(p, mbr.group(1) if mbr else "")`), so there is no status in hand. For a plan, prefer the DIRECTORY segment, which is the repository's own definition of a bucket, and note the in-tree precedent and its warning: `runner_shared.plan_bucket` does exactly this and its docstring states plainly that a plan's `- Status:` field CANNOT tell you the bucket ("a plan STAYS in `pending/` for its entire non-terminal life"), and that it "does no IO and must not learn to". So use the path for plans and the FIELD for specs, and say in the code comment why the two differ, because a reader will otherwise read it as an inconsistency. Also handle the SHARDED executed tree: `aw plans archive` creates `executed/YYYYMM/` shards, so match an `executed` SEGMENT anywhere in the path rather than requiring the parent directory (measured: no shards exist today, so a parent-only test would pass every current test and break the first time one is created).
  - ARM ORDER IS NOT "UNCHANGED" IN EFFECT, even if the lines do not move, so do not assert that it is. Today HANDOFF short-circuits before SATISFIED, so a `--evidence` close with a pending carrier is allowed BY HANDOFF. After this item that same call falls through to SATISFIED and is allowed for a DIFFERENT reason. The outcome is the same for that case, which is why this is safe, but the VERDICT PATH changes and E-02 case (6) asserts on it. E-10 decides whether the order itself should change.
  - Execution state: pending

- [ ] E-04 GIVE THE NEW REFUSAL ITS OWN REASON AND FIXES. When same-gate carriers exist but none is executed, and neither SATISFIED nor DE-GATED applies, return `CloseVerdict(False, "error", ...)` whose reason names the unexecuted carrier path(s) and says the gate is handed off but the work has not shipped, and whose FIRST fix is `aw backlog set <item> --status graduated` (keep the item as a release blocker until the plan executes), followed by the existing evidence and de-gate fixes. Keep the no-carrier refusal's existing wording unchanged. `backlog.run_set` already prints `verdict.reason` and each fix, so no caller edit is needed; confirm by reading it.
  - Depends on: E-03
  - Expected outcome: E-02 case (1)'s stderr contains `graduated` and the pending plan's filename.
  - Execution state: pending

- [ ] E-05 ALIGN THE TWO SURFACES THAT SHARE OR ADVERTISE THE PREDICATE. (a) `check_engine.release_gate_warnings`'s `check.orphaned-live-blocker` message currently reads "close it `done` (the gate is preserved via handoff). Fix: aw backlog set done <id6>" for any open item with a same-gate From-Backlog PLAN, executed or not; after E-03 that advice is refused for a pending plan. Make the remedy depend on the carrier: executed -> the `done` advice in the CORRECTED spelling below; not executed -> `aw backlog set <id6> --status graduated`. (b) The `backlog-blocking-close-gate` help text in `agent_workflows/cli.py` (the `_LEAF_HELP`-style entry containing "HANDOFF: a From-Backlog blocking plan") must say an EXECUTED From-Backlog plan. The hook and `check.blocking-item-closed-without-gate` call the same predicate, so they need no logic change; E-06 proves the rule follows. Add a test to `tests/test_check_engine_release_gate.py` for (a): an open gated item with a pending same-gate plan yields a warning whose text names `graduated`, and with an executed plan names the `--status done` spelling.
  - Depends on: E-04
  - Expected outcome: the new `release_gate_warnings` test passes; `aw backlog-blocking-close-gate --help` (or the leaf help) says EXECUTED.
  - THE REMEDY ALSO NAMES THE WRONG SPELLING, WHICH IS A SECOND DEFECT IN THE SAME STRING AND IS WORSE THAN THE STALENESS THIS ITEM SET OUT TO FIX. Its `Fix:` line is `aw backlog set done {_id6}`, the POSITIONAL form, and F-5 measures that this form does NOT run the close predicate at all (driven: with NO valid carrier, positional exits 0 and moves the item to `done/`; `--status done` exits 1 with the three fixes). So the advisory currently steers an operator onto the one route that cannot refuse, which would let them close an item this plan's whole purpose is to hold open. Emit `aw backlog set <id6> --status done` in the executed branch. This is IN scope because it is the same string this item already edits, and it does not fix F-5 itself (still Deferred, carried by E-09); it stops the repository from advertising the bypass.
  - ALSO NOTE THE WARN INDEX IS PLANS-ONLY (`_iter_plan_ipds` plus `From-Backlog`), so a SPEC carrier never produces this warning at all. Do NOT widen it here: E-03 makes the predicate spec-aware, and widening the advisory is a separate behavior change with its own test surface. Say so in the code comment so the asymmetry reads as deliberate rather than as an oversight.
  - Execution state: pending

- [ ] E-06 PROVE THE COMMIT-SCOPED RULE FOLLOWS, behaviorally. In `tests/test_check_engine_release_gate.py`, extend the `test_rule_blocking_item_closed_without_gate_reachable` pattern: a staged `done` gated item whose only same-gate carrier is a PENDING plan now yields `check.blocking-item-closed-without-gate` from `check_engine.check_release_gates(repo)`; the same with an EXECUTED plan yields none. WRITE IT BEFORE E-03 IS APPLIED AND SHOW IT FAILING; this is not optional ("if convenient" removed at review), because a test written only after the fix cannot distinguish "the rule follows the predicate" from "the rule never fired on this fixture for some unrelated reason".
  - Depends on: E-03
  - Expected outcome: pending-carrier case reports the rule; executed-carrier case is clean; the pending case FAILS against the pre-E-03 predicate.
  - Execution state: pending

### Task group 3: docs, follow-up, suite

- [ ] E-07 UPDATE THE CLOSE-RULE PROSE. (a) AGENTS.md, the repo-local paragraph beginning "Close-legitimacy rule for a release-blocking backlog item" (BELOW `<!-- /aw:block -->`; do NOT edit inside the managed block): fix (1) becomes HANDOFF to an EXECUTED plan (or an implemented spec) carrying `- From-Backlog: <this id6>` and the same gate, plus one sentence that before the carrier executes the item stays `graduated`. (b) `.aw/records/backlog/README.md`: the "Promotion to a plan" section says "author an IPD ... then `aw backlog set <item> --status done` with a history line citing the plan id", which contradicts the `graduated` section of the same README and the ruling; change it to `graduated` at authoring and `done` after the plan executes, keeping the lifecycle-section line ("reaching `done` still requires a handoff, cited evidence, or an explicit de-gate") consistent. User-facing prose: no em or en dashes.
  - Depends on: E-05
  - Expected outcome: all three surfaces describe the executed-carrier rule and none tells an author to close `done` at plan authoring.
  - THE PLAN'S "`engine.py` NEEDS NO CHANGE" CLAIM IS FALSE AND THIS IS THE HIGHEST-LEVERAGE CORRECTION IN THIS ITEM. Measured at review: `rg -n HANDOFF agent_workflows/engine.py` HITS, in the managed pre-commit templates `_BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE` and `_BACKLOG_CLOSE_GATE_PRECOMMIT_BLOCK`, whose comment reads "refuse committing a release-blocking backlog item closed to `- Status: done` without a preserved-or-satisfied gate (HANDOFF via a From-Backlog plan, DE-GATED, or a persisted evidence citation)". That text is WRITTEN INTO EVERY MANAGED TARGET REPO's `.pre-commit-config.yaml`, so leaving it stale ships the OLD rule definition to every consumer, which is strictly worse than a stale line in this repo's own AGENTS.md. So (c): update that phrase in BOTH templates to name an EXECUTED From-Backlog plan (or an implemented spec). `agent_workflows/engine.py` is now DECLARED in `- Scope-Paths:` for exactly this. Note the managed AGENTS.md prose itself needs NO change: its "Acting on a backlog item" point (5) already says "set the item to `graduated`, NOT `done`", which this plan strengthens rather than contradicts (verified at review).
  - THE ALREADY-INSTALLED CONFIG IS NOT REWRITTEN BY THIS EDIT, and say so rather than implying a fleet-wide fix: `create_backlog_close_gate_hook` is idempotent and no-clobber, so a repo that already wired the hook keeps its existing text until someone re-runs the installer. This item corrects what NEW installs and future appends emit. Do not attempt to migrate installed configs here.
  - Execution state: pending

- [ ] E-09 FILE THE OUT-OF-SCOPE BYPASS (F-5) as a durable carrier: `aw backlog new --summary "aw backlog set done <id> (positional) skips the release-gate close predicate" --set posgate --work-kind bug --priority high --slug positional-set-skips-close-gate --blocks-release next --body "<F-5 evidence>" --apply`. Paste the id6 it mints, and replace the first Deferred row's `- Carrier-Declined:` line with `- Carrier: <that id6>`.
  - Depends on: none
  - Expected outcome: a new open backlog item exists for F-5 and the Deferred row names it as its carrier.
  - Execution state: pending

- [ ] E-10 DECIDE AND RECORD HOW THIS PLAN'S OWN BACKLOG ITEM CLOSES, which the gate currently instructs in a way the new rule may refuse. Measured at review: `rwhbci`'s ONLY carrier is THIS plan (`find_from_backlog_artifacts(repo, "rwhbci")` -> the single pending `2a6phj` path), so the close is a SELF-CLOSE and its legitimacy depends on when it runs relative to this plan's own finalize, and on the arm order E-03 leaves in place. Establish the answer by DRIVING it after E-03, not by reasoning: with this plan still in `pending/`, run `evaluate_blocking_close(repo, <rwhbci path>, "done", evidence=<the executed plan path>)` and paste the verdict; then with the plan in `executed/`, paste it again. Write the resulting sequence into the gate's closing sentence so the executor performs the close in an order that is legitimate, and note which arm allowed it (`HANDOFF` once the plan is executed, or `SATISFIED` via evidence).
  - Depends on: E-03
  - Expected outcome: a stated, driven sequence for closing `rwhbci` that the shipped rule allows, with the arm named.
  - IN A RUNNER LANE THIS IS ALREADY SOLVED AND MUST NOT BE RE-INVENTED. `runner_shared.evaluate_backlog_close` is STRICTER (every IPD carrier terminal `executed`, plus an EARNED check) and handles exactly this timing with `executed_overrides`, documented as "a worker asserting a fact about its OWN item", because at close time main still shows the finalizing plan in `pending/`. So a runner-executed close of `rwhbci` works; a HAND close performed before this plan reaches `executed/` is the exposed case. State both, and prefer the runner path.
  - DO NOT "FIX" THIS BY WEAKENING THE RULE FOR SELF-CARRIERS. An exception for "the carrier is the plan doing the closing" would re-open the exact hole this plan closes (`x7wfyx` was closed citing a plan that had not run). The remedy is ORDERING (close after finalize), not an exemption.
  - Execution state: pending

- [ ] E-11 MEASURE THE CORPUS IMPACT BEFORE AND AFTER, because the plan states none and the number is large. Enumerate every `open` or `graduated` backlog item carrying `- Blocks-Release:` that has at least one `From-Backlog` carrier, and classify each by whether any carrier is EXECUTED (plan in `executed/`) or `implemented` (spec). Paste the two counts and the refused list. Measured at review for reference, to be RE-DERIVED at execution because the population moves: 45 live gated items carry a carrier, 17 would still close `done`, and 28 would now be REFUSED (one of them, `ms06pi`, via an `approved` SPEC carrier). Then state plainly in the plan whether any of those 28 is expected to be closed soon by a human, since for them the new refusal is the intended behavior and not a regression.
  - Depends on: E-03
  - Expected outcome: the before/after classification is recorded with counts re-derived at execution; no item is silently newly-refused without appearing in this list.
  - THIS IS NOT A GATE ON THE CHANGE, it is disclosure. Every one of those refusals is the ruling working as intended (an item whose code has not shipped stays `graduated`), so a large count is EXPECTED. What would be a defect is shipping it without anyone knowing the size, which is how a tightening turns into a surprise for whoever next tries to close an item.
  - Execution state: pending

- [ ] E-08 RUN THE BARE SUITE `python3 -m pytest` before the change (at E-01) and after E-07; compare failing node IDs. Also run `python3 -m agent_workflows check release-gates --agent` on the real tree before and after and paste both, since the stricter HANDOFF can surface findings on items already staged or on live open blockers.
  - Depends on: E-07, E-09, E-10, E-11
  - Expected outcome: the after-minus-before failing node set is empty; any new `check release-gates` output is explained item by item.
  - THE BEFORE-STATE IS MEASURED AND IS CLEAN: at review `aw check release-gates --agent` reported `conforms`, `findings: 0`, exit 0. So ANY finding after the change is new and must be explained item by item rather than waved off as pre-existing. Note the rule is commit-scoped (it examines items whose close is STAGED), so a clean run does NOT mean the 28 items E-11 lists are unaffected; those surface at close time, not in this sweep.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One shared predicate: `check_engine.evaluate_blocking_close` backs `backlog.run_set` (the `--status` spelling), `check.blocking-item-closed-without-gate` (via `check_release_gate_consistency`), and the opt-in hook `hooks/backlog_blocking_close_gate` (which calls that rule). Changing the predicate changes all three; AGENTS.md states "so they cannot diverge".
- Carrier discovery: `find_from_backlog_artifacts` returns plans first then specs, as `(path, blocks_release)` pairs, across every lifecycle directory. It carries NO status, so any state question means re-reading the file (F-11).
- ARM ORDER in the `done` branch is DE-GATED, then HANDOFF, then SATISFIED, then fail-closed. HANDOFF short-circuits, so today a `--evidence` close with a pending carrier is allowed BY HANDOFF and the evidence is never read. E-03 changes which arm allows that call even though the lines do not move.
- A PLAN's bucket is its DIRECTORY, never its `- Status:` field (`runner_shared.plan_bucket`: a plan stays in `pending/` through `draft`/`to-review`/`reviewed`/`approved`, and that function "does no IO and must not learn to"). A SPEC's state IS its field (`implemented`). The two readers therefore differ by necessity.
- `.aw/records/plans/executed/` can be SHARDED into `YYYYMM/` subdirectories by `aw plans archive`, so an executed test must match a path SEGMENT, not the parent directory name.
- The managed pre-commit hook text in `engine.py` DOES define HANDOFF and is installed into target repos, so the close rule has a THIRD prose home beyond AGENTS.md and the backlog README (F-8). `create_backlog_close_gate_hook` is idempotent and no-clobber, so already-installed configs keep their old text.
- Terminal-state vocabulary: `is_retired` treats `executed`, `superseded`, `not-executed`, `parked`, `done`, `archive`, `shipped` as retired, which is broader than "executed". The runner's own close decision (`runner_shared.evaluate_backlog_close`) already requires "every IPD carrier ... terminal `executed`" and reads the bucket with `runner_shared.plan_bucket`; this plan applies the milder "at least one executed" form the ruling names.
- `graduated` is already an explicit legitimate branch in `evaluate_blocking_close` ("`graduated` preserves gate ... `done` still requires handoff, evidence, or explicit de-gating").
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`. `tests/test_check_engine_release_gate.py` provides `_create_minimal_repo`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-6 were measured by the author at HEAD `f46b6775` on 2026-09-26 unless noted. F-7 through
F-11 were measured at `/plan-review` (2026-09-26, HEAD `21b22c3b`, which is AFTER `ooydp3` executed),
each by DRIVING the predicate or the CLI on a scratch repo, or by enumerating the live corpus.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `evaluate_blocking_close` HANDOFF arm | A pending same-gate plan is enough to close a gated item `done`. | scratch repo: `backlog set item01 --status done --message close` -> rc 0, `aw backlog set: ... -> done`, item now in `backlog/done/` |
| F-2 | HIGH | live history | The motivating close happened while the carrier was pending and covered half the item. | `0c5b4074 2026-09-22 backlog: close x7wfyx done on a verified gate handoff`; `f1eb82fa 2026-09-23 lifecycle(dy9ymn): finalize dy9ymn -> executed`; `x7wfyx` history `2026-09-24 graduated (aw set): ... Item A outstanding` |
| F-3 | MEDIUM | `release_gate_warnings` | The WARN remedy instructs the exact close this plan refuses. | message text "close it `done` (the gate is preserved via handoff). Fix: aw backlog set done {_id6}" for any open item with a same-gate plan, no state check |
| F-4 | MEDIUM | `.aw/records/backlog/README.md` "Promotion to a plan" | Tells authors to close `done` when the IPD is authored. | "author an IPD under `.aw/records/plans/pending/`, then `aw backlog set <item> --status done` with a history line citing the plan id" |
| F-5 | HIGH | `cli` backlog `set` dispatch -> `status_set.run_set_command` | The POSITIONAL spelling never runs the predicate at all: a gated item with NO carrier closes `done`. Out of scope here (Deferred), but it bounds what this fix protects. | scratch repo, carrier id changed to `zzzzzz`: `backlog set done item01 --yes` -> rc 0, item in `done/`; the `--status` spelling on the same repo -> rc 1 with the three fixes. Previously noted as decision D1 of executed plan `zhr6mc` ("the positional form ... does NOT run `check_engine.evaluate_blocking_close`"), and never filed as an item. |
| F-6 | INFO | `evaluate_blocking_close` SATISFIED arm | Any in-tree records path satisfies `--evidence` (e.g. the release file itself), so SATISFIED remains an honest-but-unverified escape. Unchanged by design (the ruling keeps it). | scratch repo: `--evidence .aw/records/releases/...release.md` -> allowed |
| F-7 | HIGH | this plan's own gate, and backlog `rwhbci` | **THE PLAN'S CLOSING INSTRUCTION IS THE VERY CLOSE ITS OWN RULE POLICES, AND ITS LEGITIMACY DEPENDS ON ORDER.** The gate says to close `rwhbci` `done` with `--evidence` citing the executed plan. Measured: `rwhbci`'s ONLY carrier is THIS plan, so it is a self-close; and the `done` branch evaluates HANDOFF BEFORE SATISFIED, so today the close succeeds through HANDOFF (a pending carrier) and `--evidence` is never consulted. After E-03, a hand close performed while this plan is still in `pending/` falls through to SATISFIED and depends entirely on the evidence path resolving. In a runner lane it is already solved by the stricter `runner_shared.evaluate_backlog_close` plus `executed_overrides` ("a worker asserting a fact about its OWN item"). New E-10 drives the sequence and writes it into the gate. | `find_from_backlog_artifacts(repo, "rwhbci")` -> one pending path, this plan; `evaluate_blocking_close(repo, <rwhbci>, "done")` -> `legitimate=True, path='HANDOFF'` TODAY, with and without `--evidence`; the arm order read in the `done` branch; `evaluate_backlog_close`'s override docstring |
| F-8 | HIGH | `agent_workflows/engine.py` managed pre-commit templates | **THE PLAN'S TWICE-STATED "`engine.py` CARRIES NO HANDOFF DEFINITION (CHECKED)" IS FALSE, AND THE STALE TEXT SHIPS TO EVERY MANAGED REPO.** `_BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE` and `_BACKLOG_CLOSE_GATE_PRECOMMIT_BLOCK` both carry the comment "without a preserved-or-satisfied gate (HANDOFF via a From-Backlog plan, DE-GATED, or a persisted evidence citation)", and that text is written into a target repo's `.pre-commit-config.yaml`. Leaving it stale propagates the OLD rule definition outward, which is worse than a stale line in this repo. `engine.py` is now declared and E-07 gains part (c). | `rg -n HANDOFF agent_workflows/engine.py` -> hit at the template; both template constants read; `create_backlog_close_gate_hook` confirmed idempotent/no-clobber, so installed configs are NOT retro-fixed |
| F-9 | HIGH | `release_gate_warnings`' `Fix:` line | **THE WARN REMEDY NAMES THE BYPASS SPELLING, so it currently steers an operator onto the one route that cannot refuse.** Its text is `Fix: aw backlog set done {_id6}`, the POSITIONAL form, which F-5 measures never runs the predicate. E-05 already edits this string, so correcting the spelling to `aw backlog set <id6> --status done` is in scope and does not fix F-5 itself. | driven on one fixture with NO valid carrier: `backlog set done item01 --yes` -> rc 0, item in `done/`; `backlog set item01 --status done` -> rc 1 with the three fixes; the message string read in `release_gate_warnings` |
| F-10 | MEDIUM | the live corpus | **THE BLAST RADIUS IS 28 ITEMS AND THE PLAN STATES NONE.** Of 45 live (`open`/`graduated`) gated items carrying a `From-Backlog` carrier, 17 have at least one EXECUTED carrier and would still close, while 28 would now be REFUSED. One of the 28 (`ms06pi`) is carried by a SPEC whose `- Status:` is `approved`, so E-02 case (4)'s refused half is a shape that exists in the corpus today rather than a hypothetical. Every refusal is the ruling working as intended; shipping it without stating the size is the defect. New E-11 re-derives it. | enumeration over `backlog._iter_items` filtered to `open`/`graduated` with `- Blocks-Release:`, each resolved through `find_from_backlog_artifacts` and classified by carrier directory; `ms06pi`'s carrier read (`specs/approved/...spec.md`, `- Status: approved`) |
| F-11 | MEDIUM | E-03's proposed helper | The carrier lookup carries NO status, and the plans-vs-specs readers must differ. `find_from_backlog_artifacts` returns `(path, blocks_release)` only, so the helper must re-read each file; and a PLAN's `- Status:` cannot identify its bucket (a plan stays in `pending/` through `draft`/`to-review`/`reviewed`/`approved`), which is why `runner_shared.plan_bucket` reads the DIRECTORY and its docstring forbids it from doing IO. So: path for plans, `_status_meta` field for specs, with the asymmetry explained in the comment. Also `aw plans archive` shards into `executed/YYYYMM/`, so match an `executed` SEGMENT rather than the parent name. | both `find_from_backlog_*` bodies read; `plan_bucket`'s docstring ("a plan STAYS in `pending/` for its entire non-terminal life", "must not learn to" do IO); `.aw/records/plans/executed/` confirmed to hold no shard directories today |

## Proposed changes (ordered, validatable)

1. E-01 re-measures on the post-`ooydp3` tree and records the arm order.
2. E-02 adds the behavioral close tests (failing half first), pinning the `approved` spec case and the SATISFIED verdict path.
3. E-03 requires an executed carrier in the HANDOFF arm, reading the directory for plans and the field for specs, shard-safe (F-11).
4. E-04 gives the refusal a `graduated`-first remedy.
5. E-05 aligns the WARN remedy, corrects its bypass spelling (F-9), and the hook help text.
6. E-06 proves the commit-scoped rule follows the predicate, with a before-failing test.
7. E-07 updates AGENTS.md (repo-local), the backlog README, and the managed `engine.py` hook templates (F-8).
8. E-09 files F-5 as a backlog item; E-10 settles this plan's own self-close sequence (F-7); E-11 records the 28-item blast radius (F-10).
9. E-08 bare suite and live `check release-gates` before and after, against a measured-clean before-state.

## Deferred / out of scope (with reason)

- The positional `aw backlog set done <id>` spelling bypassing the close predicate entirely (F-5).
  - Carrier-Declined: to be replaced by the backlog item E-07 files; the id6 does not exist until E-09 runs, and E-09 requires the executor to replace this line with `- Carrier: <minted id6>`. It is a separate dispatch-path defect with its own tests, and fixing it here would widen this plan past the ruling.
- Checking that a citing plan's SCOPE covers the whole item (the original question in `rwhbci`).
  - Carrier-Declined: superseded by the maintainer's 2026-09-26 ruling (OQ-02), which answers the obligation-tracking hole by timing (close only after execution) rather than by prose analysis of Scope text, which no deterministic predicate can do reliably.

## Scope check

- Over-scope: none. E-05 and E-07 are required consequences: without them three shipped surfaces (the WARN remedy, the README, and the managed hook template) instruct or define a close the predicate refuses.
- Under-scope: four gaps closed at review. `agent_workflows/engine.py` was declared NOT to need a change on a claim that is FALSE (F-8): its managed pre-commit templates define HANDOFF and are installed into every target repo, so it is now declared and E-07 gains part (c). The WARN remedy's `Fix:` line names the POSITIONAL bypass spelling (F-9), corrected in E-05. This plan's own `rwhbci` close is a self-close whose legitimacy depends on ordering and arm precedence (F-7), now owned by E-10. And the 28-item live blast radius was unstated (F-10), now E-11.
- `agent_workflows/backlog.py` and `agent_workflows/hooks/backlog_blocking_close_gate.py` remain deliberately NOT declared: the first prints whatever reason and fixes the verdict carries (confirmed by reading it), and the hook delegates to the rule.
- Scope-Paths justification: `check_engine.py` (predicate, helper, and WARN text), `cli.py` (hook help text only), `engine.py` (the two managed hook-template HANDOFF phrases only), AGENTS.md (repo-local paragraph), backlog README, two test files, and the new backlog item E-09 files.

## Required tests / validation

- `tests/test_backlog_handoff_close.py` (new): nine end-to-end cases through `aw backlog set --status`; refused halves shown FAILING before E-03. Case (6) asserts the verdict's `path` is `SATISFIED`, not merely rc 0, because HANDOFF currently short-circuits before evidence and would otherwise pass for the wrong reason. Case (4) covers an `approved` spec (a live shape, F-10) and case (9) a directory/field mismatch, so the reader can tell which of the two the rule trusts.
- `tests/test_check_engine_release_gate.py`: WARN remedy per carrier state; commit-scoped rule follows the predicate.
- `python3 -m pytest tests/test_backlog_handoff_close.py tests/test_check_engine_release_gate.py tests/test_backlog.py tests/test_status_set.py -o addopts="" -q`.
- Bare `python3 -m pytest` before and after; `check release-gates --agent` before and after.

## Spec / documentation sync

- No `.spec.md` is edited. The close rule is stated in AGENTS.md (repo-local section) and the backlog README, both declared; spec `llbr2b` (to-review) describes HANDOFF as "a `From-Backlog` plan or spec carrying the SAME `Blocks-Release`" in its inventory table, which is a description of shipped behavior that its own review will refresh, and it is not an approved contract this plan must amend. Draft spec `pqsx96`'s I-07 row likewise describes rather than prescribes.
- AGENTS.md's own prose is edited ONLY below the managed block, and the managed AGENTS.md text needs NO change (its "Acting on a backlog item" point (5) already says `graduated`, NOT `done`, which this plan strengthens).
- CORRECTED AT REVIEW: the claim that "the managed source `engine.py` carries no HANDOFF definition (checked)" is FALSE (F-8). Its managed pre-commit templates DO define HANDOFF ("HANDOFF via a From-Backlog plan") and that text is installed into every managed target repo's `.pre-commit-config.yaml`, so MANAGED TEXT DOES CHANGE here. `engine.py` is declared and E-07(c) updates both template constants. Already-installed configs are not retro-fixed (`create_backlog_close_gate_hook` is no-clobber), which is stated rather than implied.

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
- Resolution or deferral rationale: ONE, from the ruling's wording ("only when the citing plan is EXECUTED", singular) and the maintainer's instruction text for this graduation ("require at least one citing plan (or spec) in a terminal EXECUTED state"). The runner's stricter all-IPD-carriers rule (`runner_shared.evaluate_backlog_close`) is left as is; the manual setter is deliberately the milder gate so a human can close an item whose remaining carriers were retired. E-02 case (5) pins it; tightening later is a one-line change. CONFIRMED AT REVIEW that the divergence is deliberate and documented rather than accidental: `evaluate_backlog_close`'s own comment gives the measured reason for ALL ("`dh0uno` has TWO carriers, so [one-executed] would have closed it while half its work was unwritten"), and it adds an EARNED check the manual setter has no basis for. So the two predicates will knowingly disagree on a multi-carrier item: the runner refuses, a human may close. That asymmetry is the ruling's, and it is recorded here so a later reader does not "fix" it as a bug.

### OQ-04: How does this plan's OWN backlog item close, given its only carrier is this plan?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: BY ORDERING, not by an exemption, and the sequence is driven in E-10 rather than assumed. Measured at review: `rwhbci`'s only carrier is this plan, and the `done` branch tests HANDOFF before SATISFIED, so today the close succeeds through HANDOFF on a PENDING carrier (exactly the hole this plan closes) whether or not `--evidence` is passed. After E-03, a legitimate close requires either that this plan already sits in `executed/` (HANDOFF) or that the cited evidence resolves (SATISFIED). In a runner lane this is already handled by the stricter `runner_shared.evaluate_backlog_close` plus `executed_overrides`, documented as "a worker asserting a fact about its OWN item" for precisely this timing. An exemption for self-carriers is REJECTED: it would re-open the `x7wfyx` failure mode. E-10 records the driven sequence and the gate states it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the scratch-repo `aw backlog set ... --status done` exit code and output, the item's resulting path, and the `evaluate_blocking_close` verdict fields; paste the current HANDOFF-arm lines as read after `ooydp3`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_backlog_handoff_close.py -o addopts="" -v` BEFORE E-03 showing, PER NODE ID, cases (1), (4)-refused and (8) FAILING and (2), (3), (4)-allowed, (5), (6), (7), (9) passing. Use `-v` so each case is individually visible rather than a bare count. Also paste case (6)'s asserted verdict `path` (it must be `SATISFIED`, not `HANDOFF`) and case (4)'s `approved`-spec refusal, since those two are the ones that would otherwise pass for the wrong reason.
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
  - Required evidence: paste the `release_gate_warnings` and help-text diffs, the new warning test passing, and the rendered help line containing EXECUTED. ALSO paste the corrected `Fix:` string showing it now names `--status done` and NOT the positional `aw backlog set done <id6>`, plus the driven proof the old spelling bypasses the gate (F-9), so the correction is justified by evidence rather than style.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_check_engine_release_gate.py -o addopts="" -q` passing, and the pending-carrier case failing against the pre-E-03 predicate.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the AGENTS.md diff (showing it lies below `<!-- /aw:block -->`), the backlog README diff, and the `engine.py` diff covering BOTH managed hook-template constants. Paste `rg -n HANDOFF agent_workflows/engine.py` BEFORE and AFTER: before must show the stale "HANDOFF via a From-Backlog plan" phrasing (the plan originally claimed there were no hits, which review measured false), after must show the executed-carrier wording. Do NOT re-assert "no managed text changes"; managed text DOES change here and the diff is the evidence. Also state that installed target configs are not retro-fixed.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and both `check release-gates --agent` outputs with any new finding explained. The BEFORE state was measured clean at review (`conforms`, `findings: 0`, exit 0), so explain any after-finding item by item rather than calling it pre-existing.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the `aw backlog new` output with the minted id6, `aw backlog check` clean for it, and the Deferred row diff now carrying `- Carrier: <that id6>`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste BOTH driven verdicts for `rwhbci` (this plan in `pending/`, then in `executed/`), each showing `legitimate`, `path` and `reason`, and paste the gate's closing sentence as edited, showing the sequence an executor must follow and which arm authorizes the close. If the close is only legitimate once this plan is `executed`, say so explicitly rather than leaving the order implicit.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the re-derived enumeration with BOTH counts (carriers-with-at-least-one-executed vs would-be-refused) and the refused id6 list. At review this was 45 carried / 17 closable / 28 refused, including `ms06pi` via an `approved` spec; a materially different split is fine and expected, but paste the numbers you actually measured rather than these.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The HANDOFF route to `done` for a release-blocking backlog item now requires a carrier that has actually shipped (a plan in `executed/`, or an `implemented` spec); before that, `aw backlog set --status done` refuses and points at `graduated`. SATISFIED (`--evidence`) and DE-GATED (`--blocks-release -`) are unchanged. Because one predicate backs the setter, `aw check`'s commit-scoped rule and the opt-in hook, all three tighten together; the advisory WARN, the hook help, the AGENTS.md repo-local rule and the backlog README are aligned. A separate, more serious bypass found while measuring (the positional `aw backlog set done` spelling skips the predicate entirely) is FILED, not fixed. Implements the maintainer's 2026-09-26 ruling, graduates backlog `rwhbci`, inherits `- Blocks-Release: next`, and runs after `ooydp3`, which rewrites the same comparison.

THREE THINGS A HUMAN SHOULD LOOK AT DELIBERATELY, all added at review. FIRST, THIS AFFECTS 28 LIVE ITEMS. Measured: of 45 `open`/`graduated` gated items carrying a `From-Backlog` carrier, 17 keep closing and 28 would now be REFUSED until their carrier executes, one of them (`ms06pi`) through an `approved` SPEC carrier. Every refusal is the ruling working as intended, but the size was unstated and is worth seeing before approval; E-11 re-derives it at execution. SECOND, THE MANAGED HOOK TEXT SHIPS OUTWARD. The plan twice asserted, as verified, that `engine.py` carries no HANDOFF definition; it does, in the pre-commit templates that are WRITTEN INTO EVERY MANAGED TARGET REPO, so approving this also approves changing managed text (E-07(c)). Already-installed configs are not retro-fixed. THIRD, THE PLAN'S OWN CLOSE IS THE CASE ITS RULE POLICES. `rwhbci`'s only carrier is this plan, so closing it is a self-close whose legitimacy depends on ordering and on the fact that HANDOFF is evaluated BEFORE evidence; E-10 drives the sequence and no self-carrier exemption is added, because that would re-open the `x7wfyx` hole.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `check_engine.py`, `evaluate_blocking_close`'s `done` branch plus one helper, and `release_gate_warnings`' message; in `cli.py`, the `backlog-blocking-close-gate` help string only; in `engine.py`, the two managed hook-template HANDOFF phrases only; the AGENTS.md paragraph below the managed block; the backlog README's two HANDOFF passages; two test files; one new backlog item. An edit outside the declared paths, if one proves necessary, is made and then justified at finalize with `--scope-reason` per out-of-scope path; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-02 must show the refused cases FAILING before the fix, PER NODE ID (use `-v`), and E-06's pending-carrier case must also be shown failing first. Three claims here are specifically easy to fake and must be DRIVEN, not described: E-02 case (6)'s verdict `path` (it must read `SATISFIED`, since rc 0 alone is satisfied today by HANDOFF), E-10's two `rwhbci` verdicts, and E-11's before/after enumeration.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if E-01 finds the HANDOFF close already refused for a pending carrier, retire this plan rather than execute it (measured at review, post-`ooydp3`, it is NOT refused, so do not expect this). If making the HANDOFF arm stricter would also change the SATISFIED or DE-GATED outcome for any E-02 case, stop: those two are explicitly unchanged by the ruling. And do NOT add a self-carrier exemption to make this plan's own `rwhbci` close easier (E-10); fix the ORDER instead, because an exemption re-opens the `x7wfyx` failure this plan exists to close.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). THEN, AND ONLY THEN, close backlog `rwhbci`, in this ORDER, because the rule this plan ships polices exactly this close: finalize FIRST so this plan sits in `executed/`, and only after that run `aw backlog set rwhbci --status done --evidence <the executed plan path>`. The `--status` spelling is required (the positional form skips the predicate entirely, F-5). In a runner lane the driver performs this close through the stricter `runner_shared.evaluate_backlog_close`, which handles the same-run timing with `executed_overrides`; a HAND close attempted while this plan is still in `pending/` is the case E-10 measures, and it must not be forced through by weakening the rule.
