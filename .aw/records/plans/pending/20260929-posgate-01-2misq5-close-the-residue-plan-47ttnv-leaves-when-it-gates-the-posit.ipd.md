# IPD: Close the residue plan 47ttnv leaves when it gates the positional backlog set spelling: the one existing test that depends on the bypass, and the duplicate release gate le31pr carries

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `le31pr` files the same defect as backlog `mawwlc`, whose fix is already authored as pending plan `47ttnv`. So the CODE defect has a carrier and this plan must not re-fix it. What has NO carrier is the residue that lands the moment `47ttnv` executes: `tests/test_backlog_production.py::TestBacklogProductionE08::test_case5a_agent_sets_done_itself` currently DEPENDS on the bypass returning exit 0 and breaks (measured, whole-suite: `1 failed, 3245 passed`), and `le31pr` itself carries `- Blocks-Release: next` for a defect `mawwlc` already gates, so one defect gates the release twice and a fixed blocker stays live in `aw attention`.
- Scope: Make `47ttnv` executable without breaking the suite, and resolve the duplicate gate this item creates. THREE deliverables. (1) Correct `tests/test_backlog_production.py::test_case5a_agent_sets_done_itself` so its fake agent's illegitimate-close attempt is expressed in a way that survives the gate `47ttnv` installs, WITHOUT weakening what that test pins (it pins `BACKLOG-GRADUATE-LEGITIMACY`, i.e. that a run REFUSES to mark an item `graduated` when the agent closed it itself; it does not pin the close's exit code). (2) Close backlog `le31pr` as the duplicate, through a legitimate gate path rather than a hand edit, and record `mawwlc` as the survivor. (3) Add the regression pin that a run-level production check cannot be silently disarmed by a setter refusal, which is the general lesson of (1). EXCLUDES the fix itself: calling `evaluate_blocking_close` on the positional path, `--evidence` plumbing, the `AGENTS.md` and `runner_shared` docstring corrections, and the paired-spelling test file are ALL `47ttnv`'s E-01 through E-07 and are not touched here; this plan DEPENDS on that plan being executed. EXCLUDES unifying the two dispatch paths (backlog `fcnz1r`) and the audit of already-closed items (backlog `mbjuv5`).
- Scope-Paths: tests/test_backlog_production.py, .aw/records/backlog/open/20260926-posgate-01-le31pr-positional-set-skips-close-gate.backlog.md
- Item-Dependencies: executed:47ttnv
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: le31pr
- Blocks-Release: next
- Set: posgate
- Order: 1
- Highest E allocated: 03
- Author: aw oc run model=opencode
- Id: 2misq5

## Workflow history

- 2026-09-29 to-review (aw oc run model=opencode): authored from backlog `le31pr`; the defect was independently reproduced and the post-fix residue was MEASURED by simulating `47ttnv`'s gate against the whole suite (see `## Findings`).

## Goal

Let `47ttnv` land green. It installs a refusal on a code path that one existing test drives with `check=True`, so executing it as written turns the suite red; this plan corrects that test without weakening it, and retires the duplicate release gate that backlog `le31pr` would otherwise leave pointing at an already-fixed defect.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: let 47ttnv land green

- [ ] E-01 Correct `tests/test_backlog_production.py::TestBacklogProductionE08::test_case5a_agent_sets_done_itself` so it survives the gate `47ttnv` installs. WHAT THAT TEST ACTUALLY PINS, because the correction must preserve it exactly: its docstring says "agent writes conformant plan AND sets item done itself: must NOT end graduated, fails naming BACKLOG-GRADUATE-LEGITIMACY, item restored to open", and its assertions are on the QUEUE ITEM (`status == "fail-gate"`, `refusal["code"] == "BACKLOG-GRADUATE-LEGITIMACY"`) and on the absence of a `graduated/` file. It asserts NOTHING about the setter's exit code. Its `fake_agent` writes a conforming PENDING plan via `_write_conforming_plan(target, id6="pln201", backlog_id6="bkl201", gate="next")` and then shells `["python3","-m","agent_workflows","backlog","set","done","bkl201","--no-commit"]` with `check=True`. Post-`47ttnv` that call exits 1, `check=True` raises `CalledProcessError`, and the test errors BEFORE `run_queue` ever evaluates the production check, so the property is not merely broken but UNTESTED. THE CORRECT FIX IS TO STOP ASSERTING THE CLOSE SUCCEEDS, NOT TO MAKE THE CLOSE LEGITIMATE: the scenario under test is a MISBEHAVING agent, so the honest expression is that the agent ATTEMPTS the close and the run refuses to graduate regardless of whether the setter accepted it. Drop `check=True` on that one `subprocess.run` (or assert the refusal explicitly) so the fake agent's attempt is tolerated, and leave every existing assertion byte-unchanged. DO NOT make the close legitimate by executing the carrier plan or passing `--evidence`: that would change the scenario from "agent closed an item it must not close" into "agent closed an item legitimately", which is a DIFFERENT case (5a's sibling `test_case5b` covers the graduated-before-handoff variant) and would silently delete the coverage 5a exists to provide. DO NOT switch the fake agent to the `--status` spelling either: a misbehaving agent is exactly the caller that would reach for the positional one, and after `47ttnv` both spellings refuse identically, so the spelling is no longer the variable.
  - Depends on: none
  - Expected outcome: with `47ttnv`'s change applied, `test_case5a_agent_sets_done_itself` passes for BOTH hosts in `_HOSTS`, still asserting `fail-gate`, still asserting `refusal["code"] == "BACKLOG-GRADUATE-LEGITIMACY"`, and still asserting zero files in `.aw/records/backlog/graduated/`.
  - Execution state: pending

- [ ] E-02 Add ONE regression test, beside the corrected case in `tests/test_backlog_production.py`, pinning the GENERAL property E-01's failure exposed: a run-level production check must still fire when the agent's illegitimate mutation was REFUSED by a setter rather than performed. THIS IS THE ACTUAL LESSON AND IT IS NOT HYPOTHETICAL: for as long as the bypass existed, `test_case5a` proved `BACKLOG-GRADUATE-LEGITIMACY` fires when the close SUCCEEDS; nothing proved it fires when the close is refused, and after `47ttnv` the refused case is the ONLY case a real misbehaving agent can produce, so without this pin the whole check would be reachable only through a state the CLI no longer permits. Drive the same host-parameterized `run_queue` path the neighbouring cases use (reuse `_make_test_repo`, `_write_backlog_item`, `_write_conforming_plan`, `_patch_host_agent`, and the `for host_label, mod in _HOSTS` / `subTest` shape), with a `fake_agent` whose close attempt is REFUSED, and assert the queue item still reaches `fail-gate` with the `BACKLOG-GRADUATE-LEGITIMACY` code and the item is still not `graduated`. Assert on OUTCOMES only (queue status, refusal code, on-disk directory), never by reading production source with `inspect`/`ast`/regex and never by counting callers (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).
  - Depends on: E-01
  - Expected outcome: a new test in `TestBacklogProductionE08` that passes post-`47ttnv` for both hosts, and that would FAIL if the production legitimacy check were keyed on the setter's exit status rather than on the item's on-disk state.
  - Execution state: pending

### Task group 2: retire the duplicate release gate

- [ ] E-03 Close backlog `le31pr` as a duplicate of `mawwlc`, through a LEGITIMATE gate path, and record why. `le31pr` carries `- Status: open`, `- Work-Kind: bug`, `- Priority: high` and `- Blocks-Release: next` for the SAME defect `mawwlc` carries, so after `47ttnv` executes the release is gated twice for one fixed defect and `aw attention` shows a live release blocker that no longer exists. THE CLOSE IS ITSELF GATED, WHICH IS THE POINT: `le31pr` is release-blocking, so `aw backlog set done` refuses it unless the gate is preserved or released, and after `47ttnv` that refusal holds on BOTH spellings. Use the HANDOFF path, which is the honest one and needs no new flag: THIS plan carries `- From-Backlog: le31pr` and inherits `- Blocks-Release: next`, so once this plan is `executed` it IS the executed carrier `check_engine.evaluate_blocking_close` looks for, and the close becomes legitimate by construction. Therefore perform this item LAST, after this plan's own transition to `executed`, with `aw backlog set le31pr --status done --message ...` naming `mawwlc` as the survivor and this plan as the carrier. DO NOT hand-edit the item's `- Status:` line and DO NOT clear its gate with `--blocks-release -`: a hand edit bypasses the predicate that is the whole subject of this Set, and de-gating would assert the defect never blocked the release. DO NOT touch `mawwlc`, which is correctly `graduated` to `47ttnv`. If the runner closes `le31pr` automatically on this plan's execution (the `From-Backlog` handoff it already performs for a graduating item), VERIFY that rather than repeating it, and record which actor performed the close.
  - Depends on: E-01, E-02
  - Expected outcome: `le31pr` is `done` with a history line naming `mawwlc` as the surviving item and this plan as the gate carrier; `mawwlc` is untouched; `aw check release-gates` reports no `check.blocking-item-closed-without-gate` finding for `le31pr`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A PLAN MAY NOT RE-FIX WORK ANOTHER PENDING PLAN OWNS. `47ttnv` (`- Status: to-review`, `- From-Backlog: mawwlc`, `- Blocks-Release: next`) already specifies the code fix across seven E-items, including the paired-spelling test file `tests/test_backlog_positional_close_gate.py`. Authoring a second fix for the same defect would produce two plans editing `status_set.run_set_command` with overlapping `- Scope-Paths:`, which is exactly the duplicate-carrier shape `production_checks.backlog_graduate_count` refuses via its `duplicate_active` clause. So this plan DEPENDS on `47ttnv` (`- Item-Dependencies: executed:47ttnv`) and covers only what it leaves behind.
- THE CLOSE-LEGITIMACY PREDICATE IS THE SINGLE AUTHORITY. `check_engine.evaluate_blocking_close` returns a `CloseVerdict` (`legitimate`, `severity`, `reason`, `fixes`, `path`, `rule`) and is consumed by `backlog.run_set`, `set_records.close_on_answer`, `check_engine.check_release_gate_consistency`, and the opt-in `hooks/backlog_blocking_close_gate`. E-03 consumes it through the CLI rather than reimplementing any part of the judgement.
- THE HANDOFF PATH IS WHAT MAKES A GATED CLOSE LEGITIMATE WITHOUT DE-GATING. `evaluate_blocking_close`'s HANDOFF branch accepts an EXECUTED plan (or implemented spec) carrying `From-Backlog: <item id6>` AND the same `Blocks-Release`; `check_engine.find_from_backlog_plans` is the single-item scan that finds it. That is why E-03 is ordered after this plan's own execution rather than attempted during it.
- RUN-LEVEL PRODUCTION CHECKS ARE KEYED ON ON-DISK STATE, NOT ON A SETTER'S EXIT CODE. `production_checks.backlog_graduate_count` walks the plans tree and reads each plan's `- From-Backlog:` and disposition; `backlog_gate_handoff` compares the item's `- Blocks-Release:` against each produced plan's. Neither observes whether a setter the agent invoked succeeded, which is precisely why E-02's pin is meaningful and why E-01's `check=True` removal does not weaken the case.
- `AGENTS.md` FORBIDS RETROACTIVE GATING AND IN-PLACE EDITS TO EXECUTED PLANS. The gate rule "governs LIVE items only", so E-03 closes a live item and touches nothing in `done/`; and executed plan `zhr6mc`, whose decision D1 first recorded this defect, is NOT edited even though its D1 prose is imprecise about `--evidence` (that correction is `47ttnv`'s E-04, on the `runner_shared` docstring, not on the executed plan).

## Findings

THE DEFECT IS REAL AND WAS REPRODUCED INDEPENDENTLY on this worktree, in a temp repo with a `planned` release `rel001`, one `- Work-Kind: bug` / `- Priority: high` item carrying `- Blocks-Release: next`, no `From-Backlog` carrier and no evidence, each row a fresh repo driven through `python3 -m agent_workflows`:

| Invocation | rc | Lands in | Gate line after | stderr |
|---|---|---|---|---|
| `backlog set <path> --status done --yes` | 1 | `open/` | present | `refused: backlog item carries Blocks-Release 'next'; c...` |
| `backlog set done bkl001 --yes` | **0** | **`done/`** | **present** | **(empty)** |
| `backlog set done bkl001 --evidence nope/absent.md --yes` | **0** | **`done/`** | present | **(empty)** |
| `backlog set parked bkl001 --yes` | 0 | `parked/` | present | **(empty; no parking warning)** |
| `set done bkl001 --yes` (untyped surface) | **0** | **`done/`** | present | **(empty)** |

- F-01 THE ITEM'S CLAIM IS EXACTLY CORRECT. Row 2 closes a release-gated item satisfying none of the three legitimacy paths at exit 0 with empty stderr, while row 1 is the same close through the other spelling and is refused. Confirmed structurally too: `grep -c evaluate_blocking_close agent_workflows/status_set.py` returns `0`.
- F-02 THE FIX IS ALREADY AUTHORED AND OWNED BY A DIFFERENT ITEM. Pending plan `47ttnv` (`- Set: gatebypass`, `- From-Backlog: mawwlc`) specifies E-01 through E-07 covering the predicate call, post-mutation text, `--evidence`/`prior_priority`, the `runner_shared` docstring, `AGENTS.md`, `command_surface`, and a new paired-spelling test file. Its own F-10 already NAMES `le31pr` as a duplicate and raises the resolution as its OQ-01, explicitly deferring it with `Carrier-Declined`/`Carrier: le31pr`. So `le31pr`'s legitimate remaining work is the residue, not the fix.
- F-03 THE RESIDUE IS MEASURABLE AND IS EXACTLY ONE TEST. `47ttnv`'s gate was SIMULATED on this tree by temporarily inserting the predicate call into `run_set_command`'s pre-flight at the position its E-01 specifies (after the `validate_transition_allowed` loop, before the `_plan_executed` delegation), then running the BARE full suite. Result: `1 failed, 3245 passed, 2 skipped` with the sole failure `tests/test_backlog_production.py::TestBacklogProductionE08::test_case5a_agent_sets_done_itself`, erroring as `subprocess.CalledProcessError: Command '['python3','-m','agent_workflows','backlog','set','done','bkl201','--no-commit']' returned non-zero exit status 1` and printing `FAIL refused: gate 'next' is handed off to From-Backlog carrier(s) (20260927-demo-01-pln201-test-plan.ipd.md) but the work has not shipped (carrier is not executed/implemented)`. The simulation was then fully reverted (`git status` clean). `47ttnv` does NOT mention this test anywhere, and `tests/test_backlog_production.py` is NOT in its `- Scope-Paths:`, so as written it cannot legally fix it.
- F-04 THE FAILURE MODE IS WORSE THAN A RED TEST. Because the shell-out uses `check=True`, the exception is raised INSIDE `fake_agent`, so `run_queue` never evaluates `BACKLOG-GRADUATE-LEGITIMACY` at all. The case would therefore not merely fail, it would stop testing the property it exists to test, which is why E-02 adds the refused-path pin rather than trusting the corrected 5a alone.
- F-05 THE REFUSAL REASON IS THE HANDOFF BRANCH, NOT THE NO-CARRIER BRANCH, and that detail decides E-01's correction. Verified directly against the predicate with 5a's exact fixture state (gated item plus a PENDING `From-Backlog` plan carrying the same gate): `legitimate=False severity=error path=None`, reason `gate 'next' is handed off to From-Backlog carrier(s) (...) but the work has not shipped (carrier is not executed/implemented)`. So the close is refused because 5a's fake agent writes a PENDING carrier, which is precisely the illegitimate state 5a is simulating; making that close succeed would require executing the carrier and would destroy the scenario.
- F-06 FOUR OTHER TESTS DRIVE THE POSITIONAL SPELLING AND ARE ALL UNAFFECTED, which is why the residue is one test and not a class. `tests/test_attention.py` (a parse-only `--priority med` rejection), `tests/test_backlog.py` (two `parked` cases), `tests/test_backlog_gate_follows_status.py` (`_positional_spelling` pairs, whose `-> done` case carries no gate), and `tests/test_status_set.py` (fixtures with no `Blocks-Release`) all passed under the simulation. `tests/test_backlog_gate_follows_status.py` is also the established both-spellings template, already pinning nineteen properties in paired `_status_spelling`/`_positional_spelling` form.
- F-07 THE DUPLICATE GATE IS A CONCRETE, NOT COSMETIC, COST. `le31pr` and `mawwlc` both carry `- Blocks-Release: next` for one defect. `aw attention` surfaces the outstanding release-blocker set, so leaving `le31pr` live after `47ttnv` ships reports a release blocker that is already fixed, and `AGENTS.md`'s rule that a live `bug` MUST carry the gate means the item cannot simply be de-gated while it stays open. Closing it needs the gate preserved, which the HANDOFF path does.
- F-08 THE SAME DISPATCH FORK EXISTS ON `aw specs set` AND IS ALREADY GATED THERE, which is evidence this repository treats spelling parity as a real property rather than a nicety. `status_set.validate_transition_allowed` carries the specs `->reviewed` attestation and the approval gate with comments stating the reasoning verbatim ("the POSITIONAL `aw specs set approved <selector>` spelling routes to THIS function while the `--status` spelling routes to the forked `specs.run_set` ... a gate installed in only one of them is bypassed by choosing the other"). The backlog close gate is the one such gate that was never given its second caller. Not this plan's work (it is `47ttnv`'s), recorded because it shows the fix's shape is already established in the same function.

## Proposed changes (ordered, validatable)

1. `tests/test_backlog_production.py`: correct `test_case5a_agent_sets_done_itself` so the fake agent's illegitimate close ATTEMPT no longer aborts the test, preserving every existing assertion (E-01).
2. `tests/test_backlog_production.py`: add one host-parameterized regression test pinning that `BACKLOG-GRADUATE-LEGITIMACY` still fires when the agent's close was REFUSED (E-02).
3. Backlog `le31pr`: close `done` through the HANDOFF path once this plan is `executed`, naming `mawwlc` as the survivor (E-03).

## Deferred / out of scope (with reason)

- THE CODE FIX ITSELF (the predicate call on the positional path, `--evidence` plumbing, `prior_priority`, the `parked`/demote warn branches, the `AGENTS.md` and `runner_shared.close_backlog_item` corrections, `command_surface`'s `--evidence` declaration, and the paired-spelling test file). Owned end to end by pending plan `47ttnv` as E-01 through E-07. Duplicating any of it here would put two live plans on `status_set.run_set_command` with overlapping scope.
  - Carrier: 47ttnv
- UNIFYING THE TWO `aw backlog set` DISPATCH PATHS. The durable root-cause fix for this whole class, which has now been found three times on the same fork (`43p53n` gate clearing, `nobugship`/`gatefollows` gate defaulting, and this). It needs a spec-level decision about which behaviors are canonical, because the paths differ deliberately in ways each separately pinned (`git_mv` single staged rename versus `atomic_write` plus `unlink`, the history sidecar written by one only, `--gate-dir` honored by one only, multi-selector batch semantics on one only) and `run_set_command` serves five CLI surfaces plus `work_cmd`'s `aw finish`.
  - Carrier: fcnz1r
- THE RETROACTIVE AUDIT of items already closed `done` through the ungated spelling. An audit and per-item decision, never a bulk rewrite, because `AGENTS.md` states the gate rule governs LIVE items only and that gating a closed item "would assert a history that did not happen".
  - Carrier: mbjuv5
- CORRECTING EXECUTED PLAN `zhr6mc`'s DECISION D1, which says the positional form "cannot even accept `--evidence`" when argparse does accept it (the flag is registered once on the shared `backlog set` subparser) and `status_set` merely discards it. `AGENTS.md` forbids changing what an executed plan records. The live prose that repeats the same imprecision is `runner_shared.close_backlog_item`'s docstring, and correcting that is `47ttnv`'s E-04.
  - Carrier-Declined: This owes nothing durable. The inaccuracy exists only in a terminal historical record that must not be rewritten, and the one LIVE copy of the same claim is already carried by `47ttnv` E-04, so filing an item would create a task whose only legal action is the one another plan already performs. A `## Workflow history` line pointing at `47ttnv` could be appended to `zhr6mc` (which adds to the record without rewriting it) if a maintainer wants the cross-reference, but nothing depends on it.

## Scope check

- Over-scope: none. Both declared paths are touched by numbered items: `tests/test_backlog_production.py` (E-01, E-02) and the `le31pr` backlog file (E-03, via `aw backlog set`, which rewrites and relocates it).
- Under-scope: this plan does not fix the defect its own backlog item describes, and that is deliberate rather than an omission: `47ttnv` owns that fix, carries `mawwlc`'s gate, and is already `to-review`. The consequence a reviewer should weigh is the ordering constraint it creates: `- Item-Dependencies: executed:47ttnv` means this plan cannot execute first, and E-01's correction is only verifiable once `47ttnv`'s gate exists, since on today's tree the corrected test passes either way. If a maintainer would rather see the residue folded INTO `47ttnv` (adding `tests/test_backlog_production.py` to its `- Scope-Paths:` and one E-item), that is a legitimate alternative and would make this plan unnecessary apart from E-03; it is raised as OQ-01.

## Required tests / validation

`python3 -m pytest tests/test_backlog_production.py` is the primary surface, run against a tree that ALSO carries `47ttnv`'s change, since that is the only tree on which E-01 and E-02 are meaningful. Both host parameterizations in `_HOSTS` must be exercised (the file's cases loop `for host_label, mod in _HOSTS` under `subTest`), so the pasted output must show the run covering both rather than one.

Plus the BARE full suite, `python3 -m pytest` per the execution contract (no `-n0`, no extra `-q`, no `-p no:randomly`), to confirm the combined tree is green: the pre-existing measurement on the simulated tree was `1 failed, 3245 passed, 2 skipped`, so the target is that same run with zero failures.

Plus `aw check release-gates` for E-03, which is the authority on `check.blocking-item-closed-without-gate` and must report no finding for `le31pr` after the close, and `aw ipd lint --phase pre-transition` on this plan before any terminal move.

Every assertion added or changed is an OUTCOME assertion (queue item status, refusal code, on-disk directory, exit code). No test may read production source with `inspect`, `ast`, regex or substring search, assert caller counts or symbol censuses, or pin a comment banner (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).

## Spec / documentation sync

NO `.spec.md` FILE IS AMENDED, and `- Scope-Paths:` declares none, so the run-end spec-edit reconciliation should report no declared and no actual spec edits. This was checked rather than assumed: the close-legitimacy contract lives in `AGENTS.md`'s `## Release gates (Blocks-Release)` section and in `check_engine.evaluate_blocking_close`'s own docstring, not in a spec, and the only spec mentioning the backlog gate is approved spec `artifact-metadata-storage` (`2vev8j`) Section 7, which files the separate history-sidecar write-order defect that `47ttnv` defers and this plan does not touch. `AGENTS.md` itself is NOT edited here: the sentence that needs correcting once both spellings are gated is `47ttnv`'s E-05, and editing it from two plans would conflict.

## Open questions

### OQ-01: Fold this residue into 47ttnv instead of carrying it as a separate plan?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: le31pr
- Resolution or deferral rationale: NOT BLOCKING, because the work is identical either way: one test correction, one added regression test, one gated close. It is raised because the alternative is arguably tidier and the maintainer may prefer it. THE CASE FOR FOLDING: `47ttnv`'s change is what breaks the test, so a reviewer could reasonably hold that the plan making a change owes the test fix, which would mean adding `tests/test_backlog_production.py` to `47ttnv`'s `- Scope-Paths:` plus one E-item, and reducing this plan to E-03 alone. THE CASE FOR KEEPING IT SEPARATE, which is the recommendation on the evidence: `47ttnv` is already authored, seven items deep, and its scope fence and spec-sync section were written on the premise that it touches four source files and one new test file; reopening it to absorb a second test file widens a release-blocking plan late, and `le31pr` needs a carrier anyway for the duplicate-gate close (E-03), which `47ttnv` explicitly declined with `Carrier: le31pr`. Keeping them separate also keeps the dependency honest and machine-readable via `- Item-Dependencies: executed:47ttnv`. The decision is the maintainer's because it is about how to apportion scope between two plans, not a technical question the repository can answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_backlog_production.py::TestBacklogProductionE08::test_case5a_agent_sets_done_itself -v` run against a tree carrying BOTH `47ttnv`'s change and this correction, showing the test PASSING and showing both `_HOSTS` subTests exercised. PROVE THE CORRECTION DID NOT HOLLOW THE TEST OUT, which a passing run alone does not show: paste `git diff -- tests/test_backlog_production.py` for this case and confirm by inspection that the `self.assertEqual(item["status"], "fail-gate")`, the `refusal.get("code") == "BACKLOG-GRADUATE-LEGITIMACY"` assertion, and the `len(grad_files) == 0` assertion are all byte-unchanged, and that the only change is to how the fake agent's close attempt is invoked. Paste also the BEFORE state for contrast: the `CalledProcessError` failure this test produces on a `47ttnv`-patched tree WITHOUT this correction, naming the test and quoting the `refused: gate 'next' is handed off ...` line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_backlog_production.py -v` showing the new refused-path test passing for both hosts, and list its collected name. PROVE IT IS A REAL PIN AND NOT A TAUTOLOGY: make the production legitimacy check blind to the on-disk item state (for example by temporarily short-circuiting the `backlog_graduate_count`/legitimacy evaluation the case depends on), paste the FAILING output naming the new test, then restore and paste the passing run again. State explicitly in the evidence which line was temporarily changed and confirm it was reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the exact `aw backlog set` command used to close `le31pr` and its output, then paste the resulting item file showing `- Status: done`, the PRESERVED `- Blocks-Release: next` line (HANDOFF preserves the gate; it does not clear it), and the appended `## Workflow history` line naming `mawwlc` as the survivor and this plan as the carrier. Paste `aw check release-gates` showing no `check.blocking-item-closed-without-gate` and no `check.from-backlog-gate-mismatch` finding for `le31pr`. Paste `git diff --cached --name-only` for the close commit proving `mawwlc`'s file is NOT among the staged paths. Finally paste `aw attention --format json` (or the relevant rows) showing `le31pr` no longer appears in the live release-blocker set while `mawwlc` is accounted for by `47ttnv`. If the runner performed the close automatically rather than a manual command, say so and paste the run evidence instead of a command you did not run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It requires `/plan-review` and then explicit human approval before execution; the `- Readiness:` field is deliberately ABSENT, because it is an output of review and writing one here would forge the attestation the auto-approve predicate reads.

ORDERING IS A HARD PRECONDITION, not a preference: `- Item-Dependencies: executed:47ttnv` means this plan MUST NOT execute until `47ttnv` is executed. On today's tree E-01's corrected test passes with or without the correction, so executing this plan first would mark a validation verified against a tree where it proves nothing. The runner re-checks dependency edges at dispatch and will mark this item `dependency-blocked` rather than running it early.

Executing agent: commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Do not mark any `V-*` verified without pasting the actual runner output its `Required evidence` demands. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` carries observed evidence.

Backlog handoff: this plan carries `- From-Backlog: le31pr` and inherits that item's `- Blocks-Release: next`, so the gate travels with the work. The item moves to `graduated` (not `done`) on authoring. Its close to `done` is E-03 of this very plan and is legitimate only once this plan is `executed`, at which point this plan is itself the executed HANDOFF carrier the close predicate requires.
