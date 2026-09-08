# IPD: Point a driver run at the verb that can help it instead of failing on a missing ledger

- Date: 2026-09-08
- Kind: child
- Concern: The ledger-model run readers refuse a DRIVER run id with a bare `error: ledger file not found for target '<id>'`, naming a file the driver never writes and offering nothing. `aw runs resume` is the verb whose `--help` promises exactly the situation a crashed driver leaves behind ("Reconstruct run state ... report resumable steps ... Refuses when a side effect was interrupted mid-flight"), so it is the first verb an operator or agent reaches for, and it is the one that cannot help. The action that CAN help, `aw runs repair`, exists and is documented, but nothing connects the two, so recovering a crashed driver run means hand-reading `events.jsonl`, `state.json` and `outcomes/*.json`.
- Scope: Make the refusal ACTIONABLE rather than building a second resume engine. When a target resolves to a real DRIVER run directory (one holding `state.json`/`events.jsonl` but no `ledger.jsonl`), say so and name `aw runs repair <id>`, on every ledger-model reader that shares the refusal and in all three renderers. Explicitly NOT undoing the `e6b9kt` fix that stopped `events.jsonl` being parsed as a ledger, and explicitly NOT unifying the two run models.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_recovery_cli.py, tests/test_run_noun_split.py
- Item-Dependencies: none
- Status: to-review
- Set: runrecon
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: d91i3e
- From-Backlog: sv8z1e
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `sv8z1e`, inheriting its `Blocks-Release: next` gate. THIS IS A NARROWING: one of the item's two concrete defects is ALREADY FIXED and is not graduated. The item's closing paragraph reports a DISCOVERABILITY DEFECT, that `aw runs repair` is matched as a magic first positional so `aw runs --help` never mentions it and `aw runs repair --help` prints the generic `runs` help, and calls it "arguably the cheapest real fix in this whole Set". IT LANDED IN `1273806c` ("fix(runs): document `aw runs repair` and make its --help reach the right page") on 2026-09-02, the SAME DAY the item was written. Measured at HEAD `44d4950d`: `aw runs repair --help` prints the dedicated `REPAIR_HELP` page and exits 0, and `aw runs --help` mentions `repair` three times including "Read-only, except the opt-in 'repair' verb". The mechanism is a deliberate in-handler help branch (`run_viewer.py:2413-2419`) with the tradeoff recorded in the comment at `:2307-2312`. So that half of the item is DEAD and this plan does not re-implement it. THE SURVIVING HALF REPRODUCES EXACTLY, measured against a real driver run in the live repo: `aw runs resume run-20260908T030601Z-1811892` prints `error: ledger file not found for target '...'`, exits 2 unpiped, and mentions `repair` ZERO times, while that run directory holds `events.jsonl`, `state.json`, `outcomes/`, `manifest.json` and no `ledger.jsonl`. ONE MEASUREMENT THAT WIDENS THE ITEM: the item frames this as a `resume` problem, but the SAME unhelpful refusal is emitted by FIVE leaves. `runs show`, `runs status`, `runs verify-ledger`, `runs evidence` and `runs next` all print the identical `ledger file not found` line and exit 2 on the same driver run id. The string appears four times in `run_cli.py` (`:284`, `:390`, `:513`, `:629`), so fixing only `resume` would leave four copies of the dead end. E-01 centralizes it. Following the item's own option 4, which it calls "materially more attractive than building a second resume engine".
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Turn the dead end into a signpost. An operator or agent who points a ledger-model reader at a driver run should be told that it IS a driver run, that these readers serve a different run model, and which verb to use instead. The measured harm is the manual archaeology the current message forces; the fix is a message, not an engine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: recognize a driver run and say so once

- [ ] E-01 Centralize the refusal so the fix cannot be applied to one leaf and missed on four. The message `f"ledger file not found for target '{target}'"` is duplicated FOUR times in `run_cli.py`: `_run_show` (`:283-284`), the sibling at `:389-390`, the sibling at `:512-513`, and `_resolve_or_error` (`:626-631`), which is already the shared helper shape and returns `EXIT_INVALID_INVOCATION`. Route the three inline copies through one refusal builder (extending `_resolve_or_error`, or a new helper it delegates to) so there is ONE definition of this refusal. VERIFY THE LEAF SET BY RUNNING IT rather than by reading dispatch: measured at HEAD `44d4950d` against the real driver run `run-20260908T030601Z-1811892`, all of `runs show`, `runs status`, `runs verify-ledger`, `runs evidence` and `runs next` print the identical line and exit 2, while `runs decisions` and `runs questions` fail differently (a missing projection path) and are OUT of this item's scope.
  - Depends on: none
  - Expected outcome: one refusal builder; all five affected leaves emit the identical improved message, demonstrated leaf by leaf.
  - Execution state: pending

- [ ] E-02 Detect a DRIVER run directory positively rather than inferring it from the ledger's absence. A driver run directory holds `state.json` and `events.jsonl` (and typically `manifest.json`, `outcomes/`, `prompts/`, `sessions/`); a ledger run owns `ledger.jsonl` (`store.LEDGER_FILENAME`). Probe the same roots `resolve_ledger_path` already searches (`:251-260`: `.aw/state/runs/<t>/`, `.aw/records/runs/<t>/`, `.aw/runs/<t>/`) for a directory named `<target>` containing `state.json` or `events.jsonl`. Return a THREE-WAY answer, not a boolean: the target is a ledger run, a driver run, or unknown. A boolean would force the unknown case into one of the other two and produce a confidently wrong message, which is the failure mode this plan exists to remove.
  - Depends on: E-01
  - Expected outcome: given a real driver run id the detector says "driver run" and names the directory it found; given a nonexistent id it says "unknown"; given a ledger run it says "ledger run".
  - Execution state: pending

- [ ] E-03 Emit the actionable message for the driver-run case, and keep the honest one for the unknown case. For a driver run: state that the target IS a driver run, that these readers serve the ledger run model, and give the literal command `aw runs repair <id>`. Mention `events.jsonl` explicitly, because that is the file the operator will otherwise go looking for and the reason the current message reads as a contradiction (the run plainly exists on disk). For an UNKNOWN target keep today's message essentially as-is: it is CORRECT there, and inventing a `repair` suggestion for a target that resolves to nothing would be exactly the fail-open behavior a sibling plan is closing. PRESERVE THE EXIT CODE: 2 (`EXIT_INVALID_INVOCATION`, `run_cli.py:58`) in both cases, since this plan changes guidance and not the invocation contract.
  - Depends on: E-02
  - Expected outcome: `aw runs resume <driver-run-id>` names the run model and suggests `aw runs repair <id>` while still exiting 2; `aw runs resume totalgibberish` is unchanged from HEAD `44d4950d`.
  - Execution state: pending

- [ ] E-04 Honor the refusal in ALL THREE renderers, not just the human one. The machine paths are what an automated consumer reads, and a human-only signpost leaves the gap where it does the most damage. `_emit_error` (called at `:284`, `:390`, `:513`, `:629`) is the shared emitter and `_machine(args)` is computed alongside each call, so this is one change at the emitter rather than per-leaf. For `--agent`/`--json`, carry the suggested command as STRUCTURED data (the same `NextAction`-style `next` field the rest of the CLI uses), not only as prose inside a message string. CHECK THE AGENT SCHEMA BEFORE CHOOSING THE EXIT FIELD: `agent_schema` admits `exit` only in `(0, 1, 2)` and requires an error record to carry exactly 2, and exit 2 is already what these paths return, so this case is compliant as-is; do not change the code and assume that stays true.
  - Depends on: E-03
  - Expected outcome: `--agent` and `--json` both carry the suggestion in a machine-readable field, both emit schema-valid records, and all three renderers agree on the exit code.
  - Execution state: pending

### Task group 2: do not break the fix that created this situation

- [ ] E-05 PRESERVE THE `e6b9kt` FIX, and confirm its existing pins still hold. `resolve_ledger_path` (`:231-265`) deliberately NEVER resolves a bare run id to `<...>/runs/<target>/events.jsonl`, and its docstring (`:236-239`) records why: doing so made `aw run show <any-real-run>` parse healthy driver data as a ledger and report it corrupt. The `--help` text repeats the warning. This plan must NOT weaken that: the detector added in E-02 may READ the driver directory to CLASSIFY the target, but must never hand `events.jsonl` to a ledger parser, and `resolve_ledger_path` must keep returning `None` for a driver run id. Also preserve the EXPLICIT-PATH escape hatch (`:247-249`, `:241-242`): a caller pointing at a file verbatim is honored whatever it is named. THE REGRESSION PINS ALREADY EXIST and this item's job is to keep them green rather than to write them: `tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict` asserts the `None` result (`:1071-1076`), the real-ledger resolution (`:1078-1083`), the explicit-path honoring (`:1085-1089`), and that a real run id reports missing rather than corrupt (`:1093-1096`), plus four `EXIT_NOT_A_LEDGER` assertions for `show`/`verify-ledger`/`evidence`/`status` pointed at `events.jsonl` directly (`:1098-1118`). Those last four are the sharpest fence on this plan: they prove the wrong-format verdict is DISTINCT from the not-found refusal this plan is changing, so the new message must not leak into them.
  - Depends on: E-02
  - Expected outcome: `resolve_ledger_path` behavior is byte-for-byte unchanged, no ledger parser ever sees `events.jsonl`, and every existing assertion in `TestLedgerResolutionAndWrongFormatVerdict` still passes UNMODIFIED.
  - Execution state: pending

- [ ] E-06 Extend the EXISTING test class that already owns this exact surface and fixture, rather than starting a new module. `tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict` (`:1041`) is the `e6b9kt` regression suite: it already builds a fixture DRIVER run directory holding `events.jsonl`, already asserts `resolve_ledger_path(self.run_id, self.tmp) is None` (`:1071-1076`), already asserts a real ledger DOES resolve (`:1078-1083`), already asserts the explicit-path escape hatch (`:1085-1089`), and already asserts `runs show` on a real run id returns `EXIT_INVALID_INVOCATION` without claiming corruption (`:1093-1096`). So E-05's pin is largely written and the new assertions belong beside it. Measure exit codes UNPIPED (`cmd >/dev/null 2>&1; echo $?`) for any shell-level check; the in-process `_cli` helper (`:1064-1067`) returns the rc directly and is the right tool inside tests. Cover: (a) each of the five affected leaves against the fixture DRIVER run -> exit 2, message names the driver model and `aw runs repair`; (b) an unknown target -> today's message, exit 2, and NO `repair` suggestion; (c) a fixture LEDGER run -> normal success, unaffected; (d) the explicit-path case still honored; (e) all three renderers for case (a), following the existing machine-output test's shape (`:1120-1129`); (f) `resolve_ledger_path` still `None` for the driver run id. DO NOT add a test that reads the live `.aw/records/runs/`: `tests/test_run_viewer.py:1-30` records that 23 existing tests do exactly that and that 14 fail in a bare worktree, so such a test would be unrunnable in CI and in every isolated lane worktree.
  - Depends on: E-04, E-05
  - Expected outcome: all six cases pinned inside `TestLedgerResolutionAndWrongFormatVerdict` using its existing fixture, passing in a bare worktree; case (a) fails against HEAD `44d4950d`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE TWO RUN MODELS ARE DELIBERATELY DISJOINT and that is not the defect. Ledger runs own `ledger.jsonl`; driver runs (`aw oc run`/`aw agy run`) write `events.jsonl` plus `state.json` and `outcomes/`. The item is explicit that the narrow `e6b9kt` fix was right and must not be undone.
- `resolve_ledger_path` (`:231-265`) carries the whole rationale in its docstring and searches a fixed candidate list; the explicit-path branch (`:247-249`) precedes the id resolution.
- The exit vocabulary already exists (`run_cli.py:46-62`); `EXIT_INVALID_INVOCATION` is 2 and is what these refusals already return. Reuse it rather than adding a code.
- `_resolve_or_error` (`:618-632`) is already the extracted shape for this refusal; three inline copies predate it. That makes E-01 a consolidation onto an existing helper rather than a new abstraction.
- `aw runs repair` is routed from the first positional token rather than a subparser, deliberately, so every READ path on `aw runs` stays side-effect free (`run_viewer.py:2403-2408`, rationale at `:2307-2312`). Its help is printed by an in-handler branch (`:2413-2419`) because argparse cannot render help for a non-subparser. Know this before suggesting the command: `aw runs repair <id>` is correct, and the verb is real and documented.
- `repair_run` (`run_viewer.py:2357`) REFUSES while a live driver holds the run (`:2364`, `:2374-2379`), which is the right shape and the reason `repair` is a safe thing to point at: it will not silently reconcile a run that is still alive.
- MEASURE EXIT CODES UNPIPED. Recorded repeatedly in this repository after a piped `$?` produced a false finding.
- New tests on this surface must use a FIXTURE, per the explicit instruction at `tests/test_run_viewer.py:1-30`.
- THE TEST HOME ALREADY EXISTS AND SO DOES THE FIXTURE. `tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict` (`:1041`) is the `e6b9kt` regression suite, building a fixture driver run with `events.jsonl` and asserting the resolver's `None`, the real-ledger resolution, the explicit-path hatch, and the four `EXIT_NOT_A_LEDGER` wrong-format verdicts. Extend it; do not create a parallel module. Note there is NO `tests/test_run_cli.py` despite the module being `run_cli.py`, so the naming does not lead you to the right file.
- THE MODULE DISTINGUISHES TWO REFUSALS and this plan touches only one: `EXIT_NOT_A_LEDGER` (an explicit path to a file that is not a ledger) versus `EXIT_INVALID_INVOCATION` (a target that resolved to no ledger at all). The new driver-run message belongs to the SECOND; leaking it into the first would blur a distinction the existing tests exist to hold.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | HALF THE ITEM IS ALREADY FIXED AND IS NOT GRADUATED. The discoverability defect (`aw runs repair` invisible in `--help`, `repair --help` reaching the generic page) landed in `1273806c` on 2026-09-02, the same day the item was written. | `git log` for `1273806c`; measured at `44d4950d`: `aw runs repair --help` prints `REPAIR_HELP` and exits 0, `aw runs --help` mentions `repair` 3 times |
| F-2 | The surviving gap reproduces exactly: `aw runs resume <driver-run-id>` prints `error: ledger file not found for target '...'`, exits 2 unpiped, and mentions `repair` zero times. | measured at `44d4950d` against `run-20260908T030601Z-1811892` |
| F-3 | The run plainly EXISTS on disk, which is what makes the message read as a contradiction: the directory holds `events.jsonl`, `state.json`, `outcomes/`, `manifest.json`, `prompts/`, `sessions/`, and no `ledger.jsonl`. | directory listing at `44d4950d` |
| F-4 | THE ITEM UNDERSTATES THE SPREAD: five leaves emit the identical dead end, not one. `runs show`, `runs status`, `runs verify-ledger`, `runs evidence` and `runs next` all print the same line and exit 2 on the same driver run id. | measured at `44d4950d` |
| F-5 | The message is duplicated four times in the module, so a per-leaf fix would leave copies behind. | `run_cli.py:284`, `:390`, `:513`, `:629` |
| F-6 | `runs decisions` and `runs questions` fail DIFFERENTLY (a missing projection path under `.aw/workflow-artifacts/exec-set/`), so they are a separate concern and are excluded. | measured at `44d4950d` |
| F-7 | The behavior being complained about is correct-by-design and must not be reverted: `resolve_ledger_path` deliberately never maps a run id to `events.jsonl`, because doing so made a healthy run report as corrupt (`e6b9kt`). | `run_cli.py:236-239`; the same warning in `aw runs resume --help` |
| F-8 | The verb worth pointing at is real, documented, and refuses safely: `repair_run` will not reconcile a run a live driver still holds. | `run_viewer.py:2357`, `:2364`, `:2374-2379` |
| F-9 | `aw run resume` does not exist as the item's prose implies; `resume` is a `runs` leaf. `aw run` offers `start`, `record`, `cancel`, `finalize`, `as`, `ipd` and rejects `resume` with an invalid-choice error. The verb to fix is `aw runs resume`. | measured at `44d4950d` |
| F-10 | The exit code needs no change and is already schema-compatible: these paths return `EXIT_INVALID_INVOCATION` (2), and the agent schema requires exactly 2 for an error record. | `run_cli.py:58`; `agent_schema` error-record rule |
| F-11 | The sibling item `ydbhfd` (same Set, still `open`) covers the wrong FACTS (the viewer ignoring `outcomes/*.json`); this plan covers the missing ACTION. Independent, and neither blocks the other. | backlog item `ydbhfd`, status read at `44d4950d` |
| F-12 | THE TEST HOME AND FIXTURE ALREADY EXIST, which shrinks E-06 substantially: `TestLedgerResolutionAndWrongFormatVerdict` already builds a fixture driver run and already pins the resolver's `None`, the real-ledger resolution, and the explicit-path hatch. | `tests/test_run_recovery_cli.py:1041`, `:1071-1076`, `:1078-1083`, `:1085-1089` |
| F-13 | The module already distinguishes the wrong-format verdict from the not-found refusal, with four assertions pinning `EXIT_NOT_A_LEDGER` for `show`/`verify-ledger`/`evidence`/`status` on an explicit `events.jsonl` path. The new message must not leak into that class. | `tests/test_run_recovery_cli.py:1098-1118` |

## Proposed changes (ordered, validatable)

1. Consolidate the four duplicated refusals onto one builder (E-01).
2. Detect a driver run directory positively, with a three-way answer (E-02).
3. Emit the actionable driver-run message; leave the unknown-target message honest (E-03).
4. Carry the suggestion in all three renderers as structured data (E-04).
5. Preserve `resolve_ledger_path`'s `e6b9kt` behavior and pin it (E-05).
6. Pin the six-case matrix with fixture-based tests, exit codes unpiped (E-06).

## Deferred / out of scope (with reason)

- THE DISCOVERABILITY FIX. Already landed in `1273806c` (F-1). Re-implementing it would be duplicated work against shipped code.
- BUILDING A SECOND RESUME ENGINE, or making the drivers additionally emit a real `ledger.jsonl`. Both are the item's options 1; it names the risk itself, that unifying the models is "a much larger change and risks re-creating the exact confusion `e6b9kt` fixed", and it explicitly rates option 4 (make the error actionable) as "materially more attractive" now that `aw runs repair` ships as the de facto reconcile action. This plan takes option 4.
- THE STALE `driver.lock` HANDLING the item asks about (point 3). It belongs to `repair`, not to a refusal message: `repair_run` already refuses while a live driver holds the run and already reasons about lock liveness. If a stale lock still wedges `repair`, that is a defect in `repair` and needs its own item with a measured reproduction, which this plan does not have.
- `runs decisions` / `runs questions`. They fail on a missing projection path, not on the ledger refusal (F-6). Same surface, different defect.
- THE SIBLING ITEM `ydbhfd` (wrong FACTS: the viewer reporting `abandoned?` while `outcomes/*.json` records the true disposition). Independent and separately owned; the item notes it is the cheaper win, but it is not this plan's.
- RENAMING OR RE-HOMING `resume`. The two models legitimately both want the word, and a rename is a public-surface change with no measured demand.

## Scope check

- Over-scope: E-01 touches four call sites and five leaves, where the item names only `resume`. Justified by F-4/F-5, which are measured: fixing one leaf would leave four copies of the same dead end.
- Under-scope: the discoverability half is dropped as already-fixed. No second resume engine, no run-model unification, no `driver.lock` work, no `decisions`/`questions` fix.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` at authoring time is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and note tests on this surface are known to fail in a bare worktree when they read live run state, which is why new tests here must be fixture-based.
- `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_noun_split.py` for the focused surface.
- The five-leaf reproduction from F-4 re-run after the change, every exit code measured UNPIPED, against BOTH a fixture driver run and (for a sanity check only, not as a test) a real one.
- `aw sanitize --agent` before treating pasted output as shareable, since run ids and paths appear in the evidence.

## Spec / documentation sync

Spec `25kzda` (`aw run deterministic run and verify`, `- Status: approved`) governs the run surface, and this plan changes only a REFUSAL MESSAGE and its structured payload, not the exit vocabulary, the resolver contract, or any verb's shape. No spec text is contradicted, so no `.spec.md` file is edited and none is declared in `Scope-Paths`. The `aw runs resume --help` text already warns that a run id resolves only to a `ledger.jsonl` and that the drivers' `events.jsonl` is a different format; that warning stays TRUE and becomes better paired with an action. If the executor finds the improved message contradicts any spec sentence, STOP and declare the spec path before editing it, per the plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Should the suggestion be `aw runs repair <id>` alone, or should it also name the read verbs that DO work on a driver run?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE FROM THE CODE, recorded so the message is designed rather than improvised. `aw runs` (bare, with a target) renders driver runs today, so a driver-run refusal could name both the read path and the repair action. RECOMMENDATION: name `aw runs repair <id>` as the ACTION and `aw runs <id>` as the read, and nothing else; a message listing every working verb becomes a menu nobody reads, and the item's complaint was the absence of one clear next step. Verify `aw runs <driver-run-id>` actually renders before suggesting it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "ledger file not found" agent_workflows/run_cli.py` BEFORE (4 hits) and AFTER (one definition), and paste the improved message as emitted by EACH of the five affected leaves (`show`, `status`, `verify-ledger`, `evidence`, `next`) against the same driver run, with each exit code measured unpiped. Five separate outputs; a single leaf does not validate this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the detector's three-way output for three inputs: a real driver run id (-> driver run, naming the directory found), a nonexistent id (-> unknown), and a ledger run (-> ledger run). Paste the code showing the return is three-valued and not a boolean.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the full driver-run refusal text showing it names the run model, mentions `events.jsonl`, and gives `aw runs repair <id>`, with its unpiped exit code (must be 2). Then paste `aw runs resume totalgibberish` BEFORE and AFTER, showing the unknown-target message is unchanged and carries NO repair suggestion.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the raw `--agent` and `--json` records for the driver-run refusal, showing the suggestion in a structured field rather than only inside a message string, and showing each record's `exit` agrees with the unpiped process exit code. Confirm both records are schema-valid (paste a validator call or the test that asserts it).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff -- agent_workflows/run_cli.py` limited to `resolve_ledger_path` showing NO behavioral change to its candidate list or return, paste a call showing it returns `None` for a driver run id, paste the new regression test's name and passing result, and paste an explicit-path invocation still being honored.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all six cases (a)-(f) with commands, UNPIPED exit codes and output, the new tests' names, and the `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_noun_split.py` summary line. Paste evidence the tests are FIXTURE-based (the fixture setup code) and a run from a bare worktree or clean temp dir proving they do not depend on live run records. For case (a) paste the test failing against pre-change code.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note that this plan deliberately graduates only PART of backlog item `sv8z1e`: the discoverability half shipped in `1273806c` and the evidence is in F-1.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
