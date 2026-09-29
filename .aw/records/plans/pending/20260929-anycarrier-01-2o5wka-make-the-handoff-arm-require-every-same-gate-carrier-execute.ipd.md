# IPD: Make the HANDOFF arm require every same-gate carrier executed, matching the runner

- Date: 2026-09-29
- Kind: child
- Concern: THE SHARED CLOSE PREDICATE AND THE RUNNER APPLY DIFFERENT RULES TO IDENTICAL FACTS, AND THE PERMISSIVE ONE IS THE ONE A HAND CLOSE GOES THROUGH. `check_engine.evaluate_blocking_close`'s HANDOFF arm returns its verdict INSIDE the carrier loop, the instant it finds ONE executed same-gate carrier, so it implements ANY-carrier semantics. `runner_shared.evaluate_backlog_close` collects EVERY unexecuted IPD carrier and refuses when that list is non-empty, i.e. ALL-carrier semantics, and its own comment records why ("measured at authoring, `dh0uno` has TWO carriers, so that rule would have closed it while half its work was unwritten"). Measured at HEAD `2121d304` in ONE tree, with no lane and no `--gate-dir` split involved (so this is NOT the `10pcd5` coupling): on a fixture whose gated item has one carrier in `plans/executed/` and one in `plans/pending/`, `evaluate_blocking_close` returned `legitimate=True, path='HANDOFF'` while `evaluate_backlog_close` returned `close=False`, reason `IPD carrier(s) not executed: .aw/records/plans/pending/20260101-s-01-dddddd-p.ipd.md`. Driven end to end, `aw backlog set bbbbbb --status done` exited 0 and moved the item into `backlog/done/` with half its work unwritten. Because `evaluate_blocking_close` backs the SETTER, the `aw check` rule `check.blocking-item-closed-without-gate` and the opt-in pre-commit hook, the runner is protected by its own stricter outer predicate and a hand close is not.
- Scope: IN: (a) in `check_engine.evaluate_blocking_close`'s HANDOFF arm, require EVERY same-gate carrier to be executed/implemented rather than returning on the first, which means moving the verdict OUT of the carrier loop; (b) align the ANY-shaped remedy advice in `check_engine.release_gate_warnings`, whose `gates_map[gate] = gates_map.get(gate, False) or is_exec` fold makes `check.orphaned-live-blocker` advise `--status done` as soon as one carrier is executed, i.e. the exact close (a) begins refusing; (c) keep SATISFIED (`--evidence`), DE-GATED, the `graduated` arm, the `parked` WARN and the priority-demotion WARN unchanged; (d) REPLACE the one test that pins the permissive semantics (`tests/test_backlog_handoff_close.py::test_case_5_two_carriers_pending_and_executed_allowed`, measured as the ONLY suite failure under the fix) with its tightened counterpart plus an all-executed allowance case; (e) update the repo-local "Close-legitimacy rule" paragraph in `AGENTS.md` (BELOW the managed block) and the backlog README where they describe HANDOFF; (f) record the grandfathering answer OQ-01 resolves. OUT: the runner's own close path (already ALL-carrier and correct, so it is the REFERENCE this plan converges on, not a thing to edit); the residual UNGATED-sibling divergence measured in F-06, which `check.from-backlog-gate-mismatch` already flags and which OQ-02 defers with its reason; plan-SCOPE coverage (owned by `rwhbci`/`2a6phj`, still out); the positional-spelling bypass (owned by pending `47ttnv`); making `- Blocks-Release: -` resolve.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_backlog_handoff_close.py, tests/test_check_engine_release_gate.py, AGENTS.md, .aw/records/backlog/README.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: lsbd32
- Blocks-Release: next
- Set: anycarrier
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2o5wka

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `lsbd32`. Every authored finding was DRIVEN at HEAD `2121d304`, not inferred: the divergence reproduced on a scratch fixture, the hand close reproduced end to end through `aw backlog set` (exit 0 into `done/`), the corpus was re-measured (706 items, 374 gated, 351 carried, 36 multi-carrier, 18 multi-carrier AND gated, 7 exposed RIGHT NOW), and the fix was PROTOTYPED against the full suite to measure its blast radius before a line of it was planned (exactly 1 failing test of 3246, and `aw check release-gates` still CONFORMS). That prototype was reverted; the tree is clean.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

One rule decides whether a release-blocking backlog item may close `done` on the HANDOFF route, and it is the STRICTER one the runner already applies: every same-gate carrier must have executed. A hand close of a multi-carrier gated item stops being accepted while half its work is unwritten, and the predicate stops contradicting the runner it shares a tree with.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce the divergence before changing anything

- [ ] E-01 RE-MEASURE the divergence at the executing HEAD on a scratch fixture, and confirm the ARM SHAPE you are about to edit rather than trusting this plan's quotation of it. Build a temp repo carrying one `planned` release resolving `next`, a gated backlog item (`- Id: bbbbbb`, `- Blocks-Release: next`), a carrier `cccccc` under `.aw/records/plans/executed/` and a carrier `dddddd` under `.aw/records/plans/pending/`, both carrying `- From-Backlog: bbbbbb` and `- Blocks-Release: next`. Paste, side by side: `check_engine.evaluate_blocking_close(root, item, "done")` (its `legitimate` and `path`) and `runner_shared.evaluate_backlog_close(root, "bbbbbb", [<the executed carrier's repo-relative path>])` (its `close` and `reason`). Then drive the HAND CLOSE end to end: `aw backlog set bbbbbb --status done --dir <repo>`, pasting the exit code and the item's resulting directory. If the two predicates already AGREE, STOP and report rather than proceeding.
  - Depends on: none
  - Expected outcome: `legitimate=True, path='HANDOFF'` against `close=False, reason='IPD carrier(s) not executed: ...pending/...'`; the hand close exits 0 and the item lands in `backlog/done/`.
  - ALREADY DRIVEN AT AUTHORING at HEAD `2121d304`, so treat this as confirmation and do NOT expect the stop condition to fire. Observed verbatim: `check_engine.evaluate_blocking_close -> legitimate=True path=HANDOFF`, reason `gate 'next' handed off to a From-Backlog plan or spec`; `runner_shared.evaluate_backlog_close -> close=False rule=None`, reason `IPD carrier(s) not executed: .aw/records/plans/pending/20260101-s-01-dddddd-p.ipd.md`; and `aw backlog set: 20260101-s-01-bbbbbb-i.backlog.md -> done` at exit 0 with the file present in `done/`.
  - RECORD THE ARM ORDER, because E-03 preserves it deliberately: the `done` branch tests DE-GATED first (no `Blocks-Release`), then HANDOFF, then SATISFIED (`--evidence`), then fails closed with three fixes. HANDOFF short-circuits BEFORE evidence is consulted. E-03 must not reorder these; it changes only WHEN the HANDOFF arm is allowed to return.
  - Execution state: pending

- [ ] E-02 MEASURE THE CORPUS BEFORE THE FIX, so the grandfathering question OQ-01 answers is decided on counts rather than on a guess, and so V-08 has a baseline to compare against. Using `check_engine._from_backlog_carrier_index` (the ONE shared walk; do NOT call `find_from_backlog_artifacts` in a per-item loop, which `tests/test_carrier_scan_single_item_contract.py` mechanically forbids), report over the live tree: total backlog items; how many carry `- Blocks-Release:`; how many have at least one carrier; how many have MORE than one; how many have more than one AND a gate; the carrier-count distribution; and, for each item that has a gate, more than one carrier, at least one EXECUTED carrier and at least one UNEXECUTED one, its id6, its current status directory, and its executed/unexecuted counts. Separately paste `aw check release-gates` on the UNCHANGED tree.
  - Depends on: E-01
  - Expected outcome: a concrete exposed set, and a conforming `aw check release-gates` baseline.
  - MEASURED AT AUTHORING for comparison (re-measure; these WILL drift as plans execute, and a drifted number is expected, not a defect): 706 items, 374 gated, 351 with at least one carrier, 36 multi-carrier, 18 multi-carrier AND gated, distribution `{1: 315, 2: 18, 3: 3, 4: 8, 5: 4, 6: 1, 9: 2}`. SEVEN items were exposed right then: `1ap48y` (done, 4 carriers, 3 executed), `7m0aro` (graduated, 2, 1), `ciesaj` (graduated, 2, 1), `dh0uno` (done, 3, 1), `h7qsje` (done, 3, 2), `kjzlgw` (done, 9, 8), `vqv9im` (graduated, 4, 2). Note the backlog item's own figures were taken on 2026-09-28 (653 items, 31 multi-carrier, 16 multi-carrier+gated) and this is the same measurement one day later; the SHAPE is the durable claim, not the integers.
  - FOUR OF THOSE SEVEN ARE ALREADY `done`, which is the fact OQ-01 turns on, so do not skip past it: `1ap48y`, `dh0uno`, `h7qsje` and `kjzlgw` were closed under the permissive arm and their verdicts flip to `legitimate=False` under the fix. Paste each one's verdict BEFORE the fix too, so the pair can be compared in V-08.
  - Execution state: pending

### Task group 2: pin the intended behavior in tests before the fix

- [ ] E-03 REWRITE the one test that pins the permissive semantics and add the cases that pin the new rule, in `tests/test_backlog_handoff_close.py`, BEFORE touching the predicate. Behavior only, driven through `cli.main(["backlog", "set", ...])` and/or `check_engine.evaluate_blocking_close` on `git init` scratch repos: (1) REPLACE `test_case_5_two_carriers_pending_and_executed_allowed`, whose docstring reads "(5) TWO carriers, one pending and one executed -> allowed (rc 0)", with the tightened expectation: rc 1, the item does NOT move to `done/`, and stderr names the unexecuted carrier; (2) ADD an ALL-EXECUTED allowance case: two carriers, BOTH under `executed/`, close allowed rc 0 and `verdict.path == "HANDOFF"`; (3) ADD a three-carrier case with two executed and one pending -> refused, so the rule is pinned as universal rather than as "two"; (4) ADD a MIXED-KIND case: one executed plan plus one `approved` (not `implemented`) same-gate SPEC carrier -> refused, and the same spec `implemented` -> allowed, which pins that the tightening spans both carrier kinds `_carrier_is_executed` handles; (5) keep every other case in the file passing UNCHANGED, explicitly including case (2) (single executed carrier -> allowed), case (6) SATISFIED and case (7) DE-GATED. Update the file's module docstring, which currently enumerates case (5) as "TWO carriers, one pending and one executed -> allowed".
  - Depends on: E-02
  - Expected outcome: the rewritten case (1) and the new cases (3) and (4)-refused-half FAIL against unchanged code; (2), (4)-allowed-half and every pre-existing case PASS before and after.
  - THIS IS A DELIBERATE TEST REVERSAL AND MUST BE NAMED AS ONE, not quietly edited. Measured at authoring by prototyping the fix against the FULL suite: `test_case_5_two_carriers_pending_and_executed_allowed` is the ONLY test in the repository that fails (`1 failed, 3245 passed, 2 skipped` of 3246 selected), and it fails at `self.assertEqual(rc, 0)` with `AssertionError: 1 != 0`. So it is not incidental collateral; it is an intentional assertion of the ANY-carrier rule, written by `2a6phj` under OQ-03. Do NOT delete it: rewrite it, and say in its docstring that it previously asserted the opposite and which plan reversed it, so a future reader does not "restore" the permissive behavior as a regression fix.
  - DO NOT ADD CODE-PINNING TESTS. No `inspect`, no `ast`, no regex over `check_engine.py`, no assertion that the verdict-returning statement sits outside the loop. The observable contract is the verdict and the CLI exit code; `tests/test_carrier_scan_single_item_contract.py` is the repository's one sanctioned AST guard and its own docstring fences it to call SHAPES in `agent_workflows/`, which is not this.
  - Execution state: pending

### Task group 3: the fix

- [ ] E-04 IN `check_engine.evaluate_blocking_close`, HANDOFF arm: MOVE the verdict out of the carrier loop so it is returned only when EVERY same-gate carrier satisfies `_carrier_is_executed`. Concretely, the loop keeps appending to `same_gate_carriers` and stops returning; after it, return the HANDOFF verdict when `same_gate_carriers` is non-empty AND all of them are executed. Leave `_carrier_is_executed` itself UNTOUCHED (it already answers correctly for both a plan, by `executed` path segment including a sharded `executed/YYYYMM/`, and a spec, by its `- Status: implemented` field). Leave the existing not-shipped refusal below it in place: it already names every carrier it found, which is precisely why this change needs no new message. Update the docstring's `HANDOFF` line from "an executed plan or implemented spec" to EVERY same-gate carrier, and cite this plan plus backlog `lsbd32` and the runner function it now agrees with.
  - Depends on: E-03
  - Expected outcome: E-03's cases (1), (3) and (4)-refused-half pass; every other case in the file still passes.
  - THE MINIMAL EDIT IS KNOWN TO WORK AND IS RECORDED HERE SO IT IS NOT RE-DERIVED WRONG, but VERIFY the anchor against the shipped source before applying it, because `ooydp3` already rewrote the gate comparison in this arm once (it is `_same_release(...)` today, not a `==`) and another plan may move it again. Prototyped at authoring: replacing the in-loop `if _carrier_is_executed(_p): return CloseVerdict(...)` with a post-loop `if same_gate_carriers and all(_carrier_is_executed(_c) for _c in same_gate_carriers): return CloseVerdict(...)` produced exactly the intended single test failure and left `aw check release-gates` conforming.
  - DO NOT REORDER THE ARMS while doing this. HANDOFF must still be tested before SATISFIED. The change is real but narrow: a multi-carrier item with an unexecuted sibling AND a valid `--evidence` citation now falls THROUGH to SATISFIED and is allowed there, which is correct (evidence is an independent escape the maintainer's rule already grants) and is why E-03 case (6) must keep asserting `path == "SATISFIED"` rather than merely `rc == 0`.
  - DO NOT ALSO "FIX" THE UNGATED-SIBLING HOLE HERE. F-06 measures a residual divergence that survives this change, and OQ-02 defers it with its reason. Widening the same-gate FILTER in this item would change which carriers the arm considers, which is a different decision with a different blast radius, and it would make V-04's before/after comparison unreadable.
  - Execution state: pending

- [ ] E-05 ALIGN `check_engine.release_gate_warnings` so its `check.orphaned-live-blocker` remedy stops advising the close E-04 now refuses. Today it folds carrier state with `gates_map[gate] = gates_map.get(gate, False) or is_exec`, i.e. ANY-executed, and then advises `aw backlog set <id6> --status done` on that basis. Change the fold to ALL-executed (so the `--status done` advice is emitted only when every same-gate carrier is executed) and keep the other branch's `--status graduated` advice for the mixed and none-executed cases. Preserve two documented properties of this function: it stays PLANS-ONLY (its comment records that spec carriers deliberately produce no warning here, and widening that is a separate behavior change), and it keeps using the shared index rather than a per-item scan.
  - Depends on: E-04
  - Expected outcome: a mixed executed/pending carrier set yields the `graduated` advice, not the `done` advice; an all-executed set still yields `done`.
  - THE BUG HERE IS THE SAME BUG IN A SECOND PLACE, which is why this is one plan and not two: the `or is_exec` fold IS the ANY-carrier rule expressed as a boolean accumulator. Leaving it would leave `aw check` telling an operator to run a command the setter refuses, which is the "advises the one route that cannot refuse" defect `2a6phj`'s own review already caught once in this exact function.
  - MEASURED AT AUTHORING: `release_gate_warnings` returns ZERO `check.orphaned-live-blocker` warnings on the live tree right now (the rule inspects `open/` items only, and the exposed multi-carrier items are `done`/`graduated`). So this change is NOT observable on the real corpus and MUST be validated on a synthetic fixture; do not report "no warnings changed on the repo" as evidence that it works.
  - Execution state: pending

### Task group 4: make the prose match the shipped rule

- [ ] E-06 UPDATE THE HUMAN-FACING RULE STATEMENTS to say EVERY carrier. (a) `AGENTS.md`, the repo-local paragraph beginning "Close-legitimacy rule for a release-blocking backlog item", which sits BELOW `<!-- /aw:block -->` (do NOT edit inside a managed block): fix (1) currently reads "HANDOFF, an EXECUTED plan (or an implemented spec) carrying `- From-Backlog: <this id6>` and the same `- Blocks-Release: <R>`"; make it require EVERY same-gate carrier, and add one sentence saying a multi-carrier item stays `graduated` until the last carrier executes. (b) `.aw/records/backlog/README.md`, where the lifecycle and promotion sections describe reaching `done` after "the plan executes": make the multi-carrier case explicit in the same voice. User-facing prose: no em or en dashes.
  - Depends on: E-05
  - Expected outcome: both documents state the ALL-carrier rule; `git diff` shows no edit inside `<!-- aw:block -->`.
  - VERIFY THE MANAGED-BLOCK BOUNDARY BY LINE NUMBER BEFORE EDITING, because getting this wrong ships a repo-local rule into every managed target. Measured at authoring: `<!-- /aw:block -->` is at `AGENTS.md:125` and the paragraph to edit begins at `AGENTS.md:224`, comfortably below it. Re-check rather than trusting those offsets.
  - `engine.py` IS DELIBERATELY NOT IN SCOPE-PATHS, and this differs from `2a6phj`, which DID have to edit it, so do not copy that plan's conclusion. Measured at authoring: `grep -rn "Close-legitimacy\|FAILS CLOSED unless" agent_workflows/ tools/` returns NOTHING, so this paragraph is repo-local prose and is not installed from `engine.py`. The managed hook TEMPLATE in `engine.py` does mention "HANDOFF via a From-Backlog plan", but it describes WHICH ARM exists rather than how many carriers it requires, so it stays true. CONFIRM BOTH with a fresh grep and, if either turns out false, STOP and report rather than silently adding a sixth path.
  - Execution state: pending

### Task group 5: validate, including the corpus effect

- [ ] E-07 RUN THE FULL SUITE BARE and reconcile it against the prototype measurement. Run `python3 -m pytest` with NO added flags (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; adding `-n0` makes it several times slower here and a second `-q` suppresses the summary line this plan requires you to paste). Paste the actual summary line. Then paste `aw check release-gates` and `aw check` on the changed tree.
  - Depends on: E-06
  - Expected outcome: the suite passes with no failures; `aw check release-gates` still CONFORMS with 0 errors.
  - THE EXPECTED DELTA IS KNOWN, so an unexpected failure is a real signal and must not be waved through: the prototype produced exactly `1 failed, 3245 passed, 2 skipped` where the single failure was the test E-03 rewrites. After E-03 rewrites it, the suite must be GREEN. Any OTHER failing test means this plan's premise is incomplete: report it rather than adjusting the test to match the code.
  - Execution state: pending

- [ ] E-08 RE-MEASURE THE CORPUS AFTER THE FIX and record the grandfathering outcome OQ-01 resolves. Re-run E-02's measurement on the changed tree and paste, for each of the already-`done` exposed items, its verdict BEFORE and AFTER. Confirm by reading the code (not by assuming) that `check.blocking-item-closed-without-gate` is COMMIT-SCOPED, so those historical closes are not retroactively flagged, and paste the `aw check release-gates` result that demonstrates it. If any historical item IS flagged, STOP and report: that is the one outcome that would require a maintainer grandfathering decision before this ships.
  - Depends on: E-07
  - Expected outcome: the historical `done` items' verdicts flip to `legitimate=False` in isolation, yet `aw check release-gates` CONFORMS with 0 errors because the rule only examines a close STAGED in the current commit.
  - THIS IS THE ITEM THAT ANSWERS "DO WE NEED TO GRANDFATHER 16 ITEMS?", and the answer measured at authoring is NO, which is why OQ-01 is resolved rather than blocking. Under the prototype, all four already-`done` exposed items (`1ap48y`, `dh0uno`, `h7qsje`, `kjzlgw`) returned `legitimate=False`, AND `aw check release-gates` still reported `CONFORMS 388 release-gates checked, errors 0, warnings 0`. The mechanism is recorded in the rule's own comment ("only a backlog item whose close-to-`done` is STAGED in THIS commit is examined, so historical `done/` items closed before this guard existed are grandfathered") and in the hook module's docstring. Re-derive it; do not cite this plan as the proof.
  - THE THREE `graduated` EXPOSED ITEMS ARE THE REAL FORWARD EFFECT and should be reported as such, not as a problem: `7m0aro`, `ciesaj` and `vqv9im` will now be REFUSED a `done` close until their remaining carriers execute. That is the intended behavior change and it is exactly what the runner would already have refused.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The close-legitimacy predicate is deliberately SINGLE-SOURCED: `check_engine.evaluate_blocking_close` backs the setter (`backlog.run_set`), `set_records.close_on_answer`, the `aw check` rule `check.blocking-item-closed-without-gate`, and `hooks.backlog_blocking_close_gate`. `AGENTS.md` states this as the reason they "cannot diverge", so a fix applied inside that one function reaches every surface without touching four call sites.
- A plan's bucket is read from its PATH, never from its `- Status:` field; `runner_shared.plan_bucket`'s docstring records that a plan stays in `pending/` through its whole non-terminal life. A spec's state is the opposite: it lives in its `- Status:` field. `check_engine._carrier_is_executed` already encodes both halves of that asymmetry and explains it in its own docstring.
- Per-item carrier lookups must use `find_from_backlog_artifacts` (O(corpus) once, correct for ONE known item) and bulk work must use `_from_backlog_carrier_index` (one shared walk). `tests/test_carrier_scan_single_item_contract.py` enforces this with an AST guard scoped to `agent_workflows/`, and the index docstring records the measurement behind it (65 per-item calls 11.13 s versus 207 ms for one shared walk).
- Tests in this repository must assert OUTCOMES, never code structure: no `inspect`, no `ast` over production source, no symbol censuses (`GUIDING_PRINCIPLES` P16, restated in `AGENTS.md`). `tests/test_backlog_handoff_close.py` is the model: every case drives `cli.main` on a `git init` scratch repo with `AW_HOME`/`XDG_CONFIG_HOME` isolated to temp dirs.
- The suite is run BARE (`python3 -m pytest`), because `addopts` already carries `-q -n auto --dist=worksteal -m 'not slow'`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Finding | Why it matters |
|---|---|---|---|
| F-01 | HIGH | `check_engine.evaluate_blocking_close`'s HANDOFF arm returns `CloseVerdict(True, "ok", ..., "HANDOFF")` from INSIDE the `for _p, carrier_br in find_from_backlog_artifacts(...)` loop, guarded by `if _carrier_is_executed(_p)`. It therefore stops at the FIRST executed carrier and never examines the rest: ANY-carrier semantics. | This is the defect. Every other finding is either its blast radius or a surface that repeats it. |
| F-02 | HIGH | `runner_shared.evaluate_backlog_close` builds `unexecuted` across ALL IPD carriers and returns `close=False` with `"IPD carrier(s) not executed: " + ", ".join(sorted(unexecuted))` when it is non-empty: ALL-carrier semantics. Its comment states the reason, naming the live case ("measured at authoring, `dh0uno` has TWO carriers, so that rule would have closed it while half its work was unwritten"). | The correct rule ALREADY EXISTS in this repository, with its rationale recorded, so this plan is a convergence onto a shipped decision rather than a new policy. It also settles WHICH way to converge. |
| F-03 | HIGH | Driven end to end at HEAD `2121d304`: with one executed and one pending carrier, `aw backlog set bbbbbb --status done` printed `aw backlog set: ...-bbbbbb-i.backlog.md -> done`, exited 0, and the item landed in `backlog/done/`. | The divergence is not academic and not confined to a helper's return value. A hand close (no runner) of a multi-carrier gated item SUCCEEDS today. |
| F-04 | MED | `check_engine.release_gate_warnings` folds carrier state with `gates_map[gate] = gates_map.get(gate, False) or is_exec` and then advises `Fix: aw backlog set <id6> --status done` when that boolean is True. | The same ANY-carrier rule in a second place. Fixing only the predicate would leave `aw check` recommending a command the setter refuses, which is the exact class of defect `2a6phj`'s review caught in this very function. |
| F-05 | MED | `tests/test_backlog_handoff_close.py::test_case_5_two_carriers_pending_and_executed_allowed` asserts `rc == 0` for "TWO carriers, one pending and one executed", and the file's module docstring enumerates it as "(5) TWO carriers, one pending and one executed -> allowed". Prototyping the fix against the full suite produced `1 failed, 3245 passed, 2 skipped`, that test being the only failure, at `assertEqual(rc, 0)` with `1 != 0`. | The permissive behavior is EXPLICITLY PINNED, so this plan must reverse a test on purpose and label it. It also bounds the change: exactly one test, not a broad breakage. |
| F-06 | MED | A residual divergence SURVIVES the same-gate fix. Measured on a fixture whose sibling carrier has NO `- Blocks-Release:` line at all: the same-gate filter drops that sibling, so `evaluate_blocking_close` returns `legitimate=True, path='HANDOFF'` while the runner (which filters by carrier KIND, not by gate) still returns `close=False`. `check_release_gate_consistency` does flag it as `check.from-backlog-gate-mismatch`. | Honest bounding of the fix. The two predicates filter carriers differently (gate versus kind), so full convergence is a larger change. OQ-02 defers it WITH the reason, and E-04 forbids widening the filter opportunistically. |
| F-07 | MED | Corpus at HEAD `2121d304`: 706 items, 374 gated, 351 carried, 36 multi-carrier, 18 multi-carrier AND gated, distribution `{1: 315, 2: 18, 3: 3, 4: 8, 5: 4, 6: 1, 9: 2}`. SEVEN items are exposed right now (gate + multi-carrier + at least one executed + at least one unexecuted): four already `done` (`1ap48y`, `dh0uno`, `h7qsje`, `kjzlgw`) and three `graduated` (`7m0aro`, `ciesaj`, `vqv9im`). | The backlog item asked whether 16 exposed items need grandfathering. The answer needs the finer split: only 7 are actually mixed-state, and only 4 are already closed. |
| F-08 | MED | Under the prototype, all four already-`done` exposed items returned `legitimate=False` in isolation, yet `aw check release-gates` still reported `CONFORMS 388 release-gates checked, errors 0, warnings 0`. `check_release_gate_consistency`'s Rule 1 is COMMIT-SCOPED by construction, its comment stating that "historical `done/` items closed before this guard existed are grandfathered (never retroactively flagged)". | This is what lets OQ-01 resolve rather than block. No grandfathering mechanism has to be BUILT, because the existing commit scoping already provides it. Without this measurement the plan would have needed a maintainer decision first. |
| F-09 | LOW | `release_gate_warnings` emits ZERO `check.orphaned-live-blocker` findings on the live tree today (it inspects `open/` items only; the exposed items are `done`/`graduated`). | E-05's change is invisible on the real corpus, so it must be validated on a synthetic fixture. A "no warnings changed" observation would be vacuous evidence. |
| F-10 | LOW | The four other pending plans touching this predicate do not collide with the HANDOFF arm: `ghna7l` (`reviewed`) edits `check_live_bug_gate` and states five times over that it must NOT route through `evaluate_blocking_close`; `47ttnv` and `2misq5` own the positional-spelling bypass in `status_set.py`; `eikajx` owns `set_records`/`record_history`. | Justifies `- Item-Dependencies: none` by evidence rather than by omission. Note `ghna7l` and this plan share `agent_workflows/check_engine.py` and `tests/test_check_engine_release_gate.py` in Scope-Paths, which is not a hazard: the runner isolates each plan in its own worktree and merges through a revalidation gate. |
| F-11 | LOW | The `llbr2b` spec (`to-review`) tabulates both predicates in Sections 3.4 and 3.5. Section 3.4 already states the runner's rule as "if any carrier is an IPD, EVERY IPD carrier is terminal `executed`", while 3.5 states the predicate's HANDOFF as "a `From-Backlog` plan or spec carrying the SAME `Blocks-Release`" with no carrier-count qualifier. | After this plan the two sections agree in substance, and 3.5's wording becomes merely less specific rather than wrong. The spec is `to-review`, not approved, and no `.spec.md` is in Scope-Paths; the spec-sync section states why no amendment is required. |

## Proposed changes (ordered, validatable)

1. Reproduce the divergence and the successful hand close on a scratch fixture; record the arm order (E-01).
2. Measure the corpus and the `aw check release-gates` baseline, including the four already-`done` exposed items' current verdicts (E-02).
3. Reverse the one permissive test on purpose and add all-executed, three-carrier and mixed-kind cases (E-03).
4. Move the HANDOFF verdict out of the carrier loop so it requires every same-gate carrier executed (E-04).
5. Change `release_gate_warnings`'s ANY fold to ALL so its remedy stops naming a refused close (E-05).
6. Update the `AGENTS.md` repo-local paragraph and the backlog README to state the ALL-carrier rule (E-06).
7. Run the bare full suite plus `aw check` and reconcile against the prototype's known delta (E-07).
8. Re-measure the corpus and record that commit scoping grandfathers the historical closes (E-08).

## Deferred / out of scope (with reason)

- THE UNGATED-SIBLING RESIDUE (F-06). The two predicates filter carriers on different axes: `evaluate_blocking_close` keeps only carriers whose gate `_same_release` matches the item's, while the runner keeps every carrier whose KIND is IPD. So a carrier with no `- Blocks-Release:` line is invisible to the former and blocking to the latter, and that gap survives this plan. It is deferred rather than folded in because closing it changes WHICH carriers the arm considers (a different blast radius from WHEN it may return), and because `check.from-backlog-gate-mismatch` already flags that shape as an error today. OQ-02 records it.
- THE RUNNER'S OWN CLOSE PATH. `runner_shared.evaluate_backlog_close` is already ALL-carrier and is the reference this plan converges onto. Editing it would be editing the correct side.
- PLAN-SCOPE COVERAGE. Whether a carrier's declared scope covers the whole item is the adjacent question raised by backlog `rwhbci` and left open by `2a6phj` OQ-02. Unchanged here: this plan counts carriers, it does not read their scope.
- THE POSITIONAL-SPELLING BYPASS. `aw backlog set done <item>` (positional) does not run the predicate at all; pending `47ttnv` owns that, with `2misq5` owning its residue. A fix here would collide.
- WIDENING `release_gate_warnings` TO SPEC CARRIERS. Its comment records the plans-only asymmetry as deliberate and "a separate behavior change". E-05 preserves it.
- MAKING `- Blocks-Release: -` RESOLVE. Out of scope and separately pinned by `ghna7l` E-05.

## Scope check

- Over-scope: none. Five paths, exactly the declared `- Scope-Paths:`. `agent_workflows/check_engine.py` (E-04, E-05), `tests/test_backlog_handoff_close.py` (E-03), `tests/test_check_engine_release_gate.py` (E-05's synthetic fixture, since `release_gate_warnings` is exercised there today), `AGENTS.md` and `.aw/records/backlog/README.md` (E-06). `agent_workflows/engine.py` is deliberately EXCLUDED on the measurement in E-06, and `agent_workflows/backlog.py`, `agent_workflows/set_records.py`, `agent_workflows/cli.py` and `agent_workflows/hooks/backlog_blocking_close_gate.py` are excluded because they CALL the shared predicate and need no edit for its rule to change, which is the single-sourcing property `AGENTS.md` claims and V-06 verifies.
- Under-scope: the residual ungated-sibling divergence (F-06) leaves the two predicates still not identical, so this plan closes the measured HAND-CLOSE hole rather than achieving total convergence; OQ-02 owns the remainder. `release_gate_warnings` stays plans-only. No `.spec.md` is amended, for the reason in the spec-sync section.

## Required tests / validation

- `tests/test_backlog_handoff_close.py`, rewritten case (5) plus new all-executed, three-carrier and mixed-kind cases, each on its own `git init` scratch repo with `AW_HOME`/`XDG_CONFIG_HOME` isolated, driven through `cli.main(["backlog", "set", ...])` and `check_engine.evaluate_blocking_close`. Assertions are on exit codes, the item's resulting directory, stderr content and `verdict.path`.
- `tests/test_check_engine_release_gate.py`, a synthetic multi-carrier fixture for `release_gate_warnings` proving the mixed case advises `graduated` and the all-executed case advises `done` (required because F-09 measures zero such warnings on the live tree).
- The full suite BARE: `python3 -m pytest`, summary line pasted. The reconciliation target is known from the prototype (`1 failed, 3245 passed, 2 skipped` before E-03's rewrite; green after).
- `aw check release-gates` and `aw check` on the changed tree, pasted, with 0 errors.
- The before/after corpus measurement, including each already-`done` exposed item's verdict on both sides, demonstrating that commit scoping grandfathers them.
- No test may pin code structure (no `inspect`, no `ast` over `check_engine.py`, no assertion about where the return statement sits).

## Spec / documentation sync

- `AGENTS.md`: the repo-local "Close-legitimacy rule" paragraph, BELOW `<!-- /aw:block -->`, fix (1), restated as EVERY same-gate carrier (E-06a).
- `.aw/records/backlog/README.md`: the HANDOFF/promotion prose, made explicit about the multi-carrier case (E-06b).
- NO `.spec.md` AMENDMENT IS REQUIRED, and this is a deliberate judgement rather than an omission, so it is stated with its reason. The only spec tabulating these predicates is `llbr2b`, which is `to-review` and NOT approved, and its Section 3.4 ALREADY states the ALL-carrier rule for the runner ("if any carrier is an IPD, EVERY IPD carrier is terminal `executed`"). Section 3.5 describes the shared predicate's HANDOFF without a carrier-count qualifier, so after this plan it is less specific than the code but not contradicted by it. Amending a `to-review` spec to track an implementation detail it deliberately abstracts would add churn without adding contract. Consequently NO path in `- Scope-Paths:` ends in `.spec.md`, and the runners' end-of-run spec-edit reconciliation should report zero declared and zero actual spec edits. If an executor finds that `llbr2b` has since been APPROVED and its 3.5 row now reads as a positive ANY-carrier claim, STOP and report: that would make this a spec amendment, which must be declared in `- Scope-Paths:` before the run starts.
- `CHANGELOG.md` is NOT in scope: this corrects an internal predicate's agreement with the runner and ships no new user-facing surface, flag or command.

## Open questions

### OQ-01: Must the exposed multi-carrier items be grandfathered when the gate tightens?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, no maintainer decision needed, because the existing commit scoping already provides the grandfathering the backlog item worried about. The item flagged "16 live gated items exposed today" and asked whether to grandfather them. Measured (F-07, F-08): only 7 are actually mixed-state, of which 4 are already `done` (`1ap48y`, `dh0uno`, `h7qsje`, `kjzlgw`) and 3 are `graduated`. Under the prototyped fix all four `done` items' verdicts flip to `legitimate=False` in isolation, yet `aw check release-gates` still reports `CONFORMS ... errors 0, warnings 0`, because `check_release_gate_consistency`'s Rule 1 examines only a close STAGED IN THE CURRENT COMMIT and its comment states that historical closes are "grandfathered (never retroactively flagged)". So no retroactive flagging occurs, no exemption list is needed, and no historical record has to be rewritten. The three `graduated` items are the intended FORWARD effect: they will be refused a `done` close until their remaining carriers execute, which is exactly what the runner would already have refused. E-08 re-derives this and STOPS if any historical item is in fact flagged, which is the one outcome that would escalate this to the maintainer.

### OQ-02: Should the same-gate carrier filter be widened so an ungated sibling carrier also blocks the close?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED as out of scope, non-blocking, WITH AN EXPLICIT TRIGGER, and with the measurement recorded so the decision is informed rather than forgotten (F-06). TRIGGER: file a new backlog item in the `anycarrier` Set as the final act of executing this plan (E-08's report names it), to be picked up only if `check.from-backlog-gate-mismatch` is ever WEAKENED or made advisory, since that rule is what makes the residue visible today; absent that, it stays deferred indefinitely. WHY IT IS NOT FOLDED IN: the two predicates filter carriers on different axes (this one by same-resolved-gate, the runner by carrier kind), so an ungated sibling carrier is invisible here and blocking there, and that divergence survives this plan. Excluded because (a) it changes WHICH carriers the arm considers rather than WHEN the arm may return, a materially different blast radius on the same high-traffic predicate; (b) that shape is ALREADY an error under `check.from-backlog-gate-mismatch`, so it is reported today even though the close would succeed; and (c) a gated item whose carrier drops the gate is a broken handoff whose right fix is probably to repair the carrier's gate, not to widen a close predicate. It does not gate this plan: every E-item and V-item above is executable and verifiable with this question left open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the fixture construction (or the script) and BOTH predicate verdicts side by side, showing `evaluate_blocking_close` -> `legitimate=True, path='HANDOFF'` and `evaluate_backlog_close` -> `close=False` naming the pending carrier in its reason. PASTE the `aw backlog set ... --status done` invocation with its exit code and the item's resulting directory listing. PASTE the observed arm order (DE-GATED, HANDOFF, SATISFIED, fail-closed). A verdict pair that AGREES fails this item and means STOP.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the pre-fix corpus numbers (totals, gated, carried, multi-carrier, multi-carrier AND gated, the distribution) and the enumerated exposed set with each item's id6, status directory and executed/unexecuted counts. PASTE each already-`done` exposed item's pre-fix verdict. PASTE `aw check release-gates` on the unchanged tree. Numbers that differ from this plan's authoring measurement are EXPECTED and acceptable; what fails this item is an absent measurement, or a measurement taken with a per-item `find_from_backlog_artifacts` loop instead of the shared index.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the rewritten case (5) source INCLUDING its docstring, which must state that it previously asserted the opposite and name this plan as the reversal. PASTE the new all-executed, three-carrier and mixed-kind cases. PASTE a pre-fix targeted run showing the rewritten case and the new refusal cases FAILING against unchanged code (this is the before-failing proof; a test that passes before the fix proves nothing). PASTE the updated module docstring enumeration. Any use of `inspect`, `ast`, or a regex over `check_engine.py` FAILS this item outright.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the committed HANDOFF arm. The verdict-returning statement must sit OUTSIDE the carrier loop and be guarded by an all-carriers-executed condition; a `return` still inside the `for` body fails this item. PASTE the updated docstring `HANDOFF` line. PASTE a post-fix re-run of E-01's exact fixture showing the two predicates now AGREE (`legitimate=False` against `close=False`), plus a two-executed-carrier fixture showing `legitimate=True, path='HANDOFF'` so the fix is proved not to be a blanket refusal. PASTE `git diff` for this file showing the arms were NOT reordered and `_carrier_is_executed` was NOT modified.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the committed fold and the two remedy branches. PASTE the synthetic-fixture test output proving a MIXED carrier set advises `aw backlog set <id6> --status graduated` and an ALL-EXECUTED set advises `--status done`. PASTE evidence the function is still plans-only and still uses the shared index. An observation that the live tree's warning count is unchanged does NOT satisfy this item: F-09 measured that count at zero, so it is vacuous.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE the rewritten `AGENTS.md` paragraph and the changed backlog README prose, both stating EVERY same-gate carrier, with no em or en dashes. PASTE the line numbers of `<!-- /aw:block -->` and of the edited paragraph, proving the edit is below the marker. PASTE `git diff --stat` showing `agent_workflows/engine.py` ABSENT. PASTE the fresh grep output that justified excluding it (no "Close-legitimacy"/"FAILS CLOSED unless" match under `agent_workflows/`), and the grep proving the managed hook template's HANDOFF sentence remains true. PASTE a demonstration that the setter, `aw check` and the hook all pick up the new rule WITHOUT being edited: for one fixture, the setter's refusal, the `check.blocking-item-closed-without-gate` verdict path, and `hooks.backlog_blocking_close_gate.check`'s result.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: PASTE the ACTUAL bare `python3 -m pytest` summary line (for example `N passed in M.MMs`), with no failures. The command must be bare: a pasted invocation carrying `-n0`, an extra `-q`, or `-p no:randomly` FAILS this item. PASTE `aw check release-gates` and `aw check` output with 0 errors. If any test other than the one E-03 rewrote failed at any point, PASTE it and its resolution.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: PASTE the post-fix corpus measurement beside the pre-fix one from V-02. PASTE each already-`done` exposed item's verdict BEFORE and AFTER, showing the flip to `legitimate=False`. PASTE `aw check release-gates` on the changed tree showing CONFORMS with 0 errors despite those flips, and PASTE the quoted commit-scoping comment (or the code) that explains why, derived at execution rather than cited from this plan. PASTE the three `graduated` items now refused a `done` close. A single retroactive finding against a historical item fails this item and means STOP and report.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the five declared `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`; this checkout is shared and another agent's uncommitted work is not yours to sweep in. Do not create or push a tag or release.

SEQUENCE MATTERS AND IS NOT NEGOTIABLE. E-03 (the test reversal) lands BEFORE E-04 (the fix), so the before-failing proof V-03 demands actually exists; writing the fix first makes that evidence unobtainable and V-03 unsatisfiable.

THE ONE THING MOST LIKELY TO GO WRONG is treating F-05's failing test as collateral damage and "repairing" it back to `assertEqual(rc, 0)`. It asserts the ANY-carrier rule deliberately, authored by `2a6phj` under its OQ-03. This plan REVERSES it on purpose, and E-03 requires the new docstring to say so, precisely so a later reader does not restore the hole as a regression fix.

STOP CONDITIONS, each of which means report rather than proceed: the two predicates already agree at the executing HEAD (E-01); any test beyond the one E-03 rewrites fails (E-07); any HISTORICAL `done` item is retroactively flagged by `aw check release-gates` (E-08), which would escalate OQ-01's grandfathering question to the maintainer; or `llbr2b` has become APPROVED with a positive ANY-carrier claim in Section 3.5, which would turn this into a spec amendment requiring a declared `.spec.md` in `- Scope-Paths:` before the run starts.

POST-GATE LIFECYCLE. This plan is `to-review` and requires `/plan-review` and explicit human approval before execution. Do not self-approve and do not write a `- Readiness:` field; that field is `/plan-review`'s output and hand-writing it forges the attestation the auto-approve predicate reads. After execution, move this file to `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence. Backlog `lsbd32` inherits nothing further: this plan carries its `- Blocks-Release: next` gate, so the item may close `done` on the HANDOFF route once this plan is executed, and it stays a release blocker until then.
