# IPD: Return EXIT_CORRUPTED_LEDGER from the three run readers that hardcode exit 2

- Date: 2026-09-28
- Kind: child
- Concern: `aw runs show|evidence|verify-ledger` report ledger corruption with exit 2 (the invalid-invocation code) instead of `EXIT_CORRUPTED_LEDGER` (5), so a machine caller cannot distinguish a damaged ledger from a mistyped command.
- Scope: Replace the hardcoded `2` with `run_cli.EXIT_CORRUPTED_LEDGER` at the three corruption sites in `run_cli._run_show`, `run_cli._run_evidence`, and `run_cli._run_verify_ledger` (both the returned code and the `exit_code` key in the machine payload); correct the module docstring's exit-code contract, which currently states the wrong code; and add behavioral coverage asserting the code and payload for every affected verb. Out of scope: the unrelated `except Exception` fallbacks, `EXIT_NOT_A_LEDGER`, and the spec-5.6-versus-`run_cli` table reconciliation.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_cli_corruption_exit.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: z63xoh
- Blocks-Release: next
- Set: z63xoh
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: fuuw94
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-701..PR-705 all FIXED

- 2026-09-28 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701..PR-705 all FIXED, none deferred, no finding escalated. Reviewed at HEAD `9c665d00` in a lane worktree; `aw ipd lint --phase author --agent` conformed before revision (exit 0, `findings: 0`). ALL SEVEN authored findings reproduced exactly, including the `2,2,2,5,5,5` six-verb sweep and both git-provenance claims. E-01..E-03 were staged IN MEMORY via a pytest plugin outside the tree and the bare suite was unchanged at `3160 passed, 2 skipped` with the post-fix sweep reading `5,5,5` and both payload keys preserved (F-10), so the change is verified safe before approval. Review added F-08..F-11. The two consequential findings: E-04 as written would have traded one false docstring claim for another, because the `Contract:` block lists only exits 0/1/2/7 and `EXIT_INVALID_INVOCATION` is also the read-failure code the preserved `except Exception` branches return (F-08); and E-05's ledger fixture is refused by schema validation in five distinct ways that the plan did not record, which is the likeliest place execution stalls (F-09). Also recorded that a docstring the plan quotes faithfully cites a deleted test file (F-11). No production code was modified by this review.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `z63xoh`; resolved the item's DECISION NEEDED from repository evidence (see Findings F-3/F-4) and widened scope from the one verb the item named to the three that actually carry the defect (F-2).

## Goal

Make ledger corruption report one exit code across the whole `aw run`/`aw runs` surface. Eight handlers already return `EXIT_CORRUPTED_LEDGER` (5); three sites return a bare `2`, which this CLI otherwise uses for "bad invocation or missing ledger". A wrapper that branches on 5 to say "your ledger is damaged, recover it" currently sees 2 from these three verbs and cannot tell that case from "you typed the command wrong".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: use the module's own constant at the three divergent sites

- [x] E-01 In `run_cli._run_show`, replace the `store.LedgerCorruption` handler's hardcoded `"exit_code": 2` and `return 2` with `EXIT_CORRUPTED_LEDGER`. Change ONLY the `LedgerCorruption` branch; leave the adjacent `except Exception` branch (which is a read failure, not corruption) at `EXIT_INVALID_INVOCATION`, and keep `"corrupted": True` in the payload.
  - Depends on: none
  - Expected outcome: `aw runs show <corrupt-ledger>` exits 5, and its `--agent` payload carries `"exit_code": 5` alongside the unchanged `"corrupted": true`.
  - Execution state: performed

- [x] E-02 In `run_cli._run_evidence`, make the same single-branch change to its `store.LedgerCorruption` handler. This is a byte-identical duplicate of the `_run_show` handler (F-2), so it must move in the same pass or the asymmetry merely relocates.
  - Depends on: E-01
  - Expected outcome: `aw runs evidence <corrupt-ledger>` exits 5 with `"exit_code": 5` and `"corrupted": true`.
  - Execution state: performed

- [x] E-03 In `run_cli._run_verify_ledger`, replace the `not chain_ver.clean` branch's `"exit_code": 2` and `return 2` with `EXIT_CORRUPTED_LEDGER`. Note this site reports corruption through a `verify_chain(raise_on_error=False)` RETURN VALUE rather than a raised `LedgerCorruption`, so it is not found by grepping for the exception (F-2); its `chain_clean: False` payload key is unchanged.
  - Depends on: E-02
  - Expected outcome: `aw runs verify-ledger <corrupt-ledger>` exits 5, and its payload keeps `"chain_clean": false` while `"exit_code"` becomes 5.
  - Execution state: performed

### Task group 2: correct the stated contract and pin the behavior

- [x] E-04 Correct the module docstring's `Contract:` block in `run_cli.py`, whose exit-code line currently reads `exit 2 = invocation error, missing ledger, or corrupted hash chain / unparseable JSON`. Corruption is no longer part of that line; state exit 5 for the corrupted hash chain / unparseable JSON class, matching `EXIT_CORRUPTED_LEDGER`'s own definition comment. Leave the `WRONG-FORMAT IS NOT CORRUPTION` paragraph and the exit-7 line untouched: `e6b9kt` settled that distinction and this plan does not revisit it.

  WRITE THE EXIT-2 LINE AS A RESIDUAL, NOT AS A NEW ENUMERATION. The block lists only exits 0, 1, 2 and 7 (measured at review: exits 3, 4, 5 and 6 appear nowhere in it, F-8), so deleting the corruption clause leaves `exit 2 = invocation error, missing ledger` reading as if those were the only two causes when `EXIT_INVALID_INVOCATION` is also the module's generic read-failure code, including at the `except Exception` branches E-01/E-02 deliberately leave alone. State exit 2 as covering a bad invocation, a missing ledger, and an unexpected read failure, then add the exit-5 line beside it. DO NOT expand the block into a full eight-code table: the module's constant definitions are the authority for that, adding four lines the plan measured nothing about would be gold-plating, and the sole defect here is one clause asserting the wrong code.
  - Depends on: E-03
  - Expected outcome: the docstring no longer contradicts the `EXIT_CORRUPTED_LEDGER` definition in the same module; a reader who trusts the docstring gets the shipped code; and the surviving exit-2 line does not imply that a read failure now exits 5.
  - Execution state: performed

- [x] E-05 Add `tests/test_run_cli_corruption_exit.py`: build a real two-record ledger with `run_ledger_store.RunLedgerStore.append`, tamper `prev_hash` on the second record to break the chain, then drive each verb as a subprocess and assert on the exit code and the machine payload. Table-drive it over the verbs so all six corruption-reporting readers are one row each: `show`, `evidence`, `verify-ledger` (the three this plan fixes) AND `status`, `next`, `resume` (the three that already return 5, included as the control that proves the fix converges on existing behavior rather than inventing a new code). Assert the payload keys too (`corrupted: true` for `show`/`evidence`, `chain_clean: false` for `verify-ledger`), so the machine-readable signal is pinned whichever code is chosen later. Build the ledger in a `tempfile` directory, never under the checkout's gitignored `.aw/records/runs/`.

  THE LEDGER FIXTURE IS THE HARD PART OF THIS E-ITEM, AND A NAIVE `append` CALL IS REFUSED BY SCHEMA VALIDATION, so budget for it rather than discovering it mid-execution. `RunLedgerStore.append` validates every record and raises `SchemaInvalidRecordError`; review needed five attempts to land a valid pair. The measured minimum (F-09) is: a `common` mapping of `schema_version=2` (an INT, not the string `"1"`), `actor` drawn from `run_ledger_schema.ROLES` (for example `coordinator`; an arbitrary label such as `test` is refused `RL-E014`), `parent`, and `run_id` matching `run_ledger_schema._RUN_ID_RE` (`^run-[0-9a-f]{8,}$`, so `r1` is refused `RL-E015`); a seq-0 `kind="run"` additionally carrying `repo`, `workflow_digest`, `requirement_digest` and `head`; and a seq-1 record of a kind in `RECORD_KINDS` (`item`, `requirement` and `note` are NOT in it) whose required fields come from `run_ledger_schema._KIND_FIELDS`, for which the measured-working choice is `kind="step_attempt"` with `step`, `state` and `attempt` (an int). DERIVE the role and the kind's field list from those module symbols rather than transcribing review's literals, so the fixture tracks the schema instead of pinning a snapshot of it. Confirm the fixture is genuinely broken before asserting anything on it: `verify_chain(raise_on_error=False).clean` must be True BEFORE the tamper and False after, which is what distinguishes a real chain break from a fixture that merely fails to build.
  - Depends on: E-04
  - Expected outcome: a new test module that fails on the pre-fix tree for exactly the three rows in scope and passes on the post-fix tree for all six, built on a fixture whose chain is proven clean-then-broken rather than assumed.
  - Execution state: performed

- [x] E-06 Add one more row to the same new test file asserting the MISSING-ledger case is NOT affected: `aw runs show /nonexistent/ledger.jsonl` must still exit `EXIT_INVALID_INVOCATION` (2). This is the separating assertion that gives the fix its meaning, because the whole point is that 2 and 5 become distinguishable; without it the suite would still pass if someone made every failure return 5.
  - Depends on: E-05
  - Expected outcome: the test file pins BOTH sides of the contract: corrupt ledger -> 5, absent ledger -> 2.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE EXIT TABLE LIVES IN THE MODULE UNDER CHANGE. `run_cli` defines its own constants (`EXIT_OK` 0, `EXIT_INCOMPLETE` 1, `EXIT_INVALID_INVOCATION` 2, `EXIT_BLOCKED` 3, `EXIT_INVALID_EVIDENCE` 4, `EXIT_CORRUPTED_LEDGER` 5, `EXIT_OPERATIONAL` 6, `EXIT_NOT_A_LEDGER` 7) under the comment `exit-code table (awoptimize Order 07 E-03)`. The fix is to USE an existing constant, not to add one.
- A SECOND, DISAGREEING EXIT TABLE EXISTS AND IS EXPLICITLY OUT OF SCOPE. `run_evidence` carries a comment stating that this package `ships TWO exit tables that DISAGREE at the same numbers`, and names which one governs here: `run_cli`'s table governs the READ-ONLY inspection commands (`aw runs show|evidence|verify-ledger`). That is the authority for the verbs this plan touches, and the same comment records that `Reconciling the two tables is a separate concern that no plan currently owns`. This plan does not take that on; it aligns three sites with the table already declared to govern them.
- WRONG FORMAT IS NOT CORRUPTION, AND THAT PATH IS SEPARATE. `run_cli._emit_not_a_ledger` is deliberately kept apart from every corruption path (its docstring: `the message must not contain the word corrupt`), returning `EXIT_NOT_A_LEDGER` with `corrupted: false`, per `e6b9kt`. Editing the corruption branches cannot disturb it, and no E-item touches it.
- MACHINE PAYLOADS HERE ARE BARE DICTS, NOT `aw.agent/v1`. `_emit_error`'s docstring records this as a deliberate, separately-owned gap (`DELIBERATELY NOT AN aw.agent/v1 RECORD (F-16)`, `run_cli` imports `agent_schema` zero times). So the payload change in scope is the value of the existing `exit_code` key, and this plan must NOT convert these sites to the agent schema. CAVEAT MEASURED AT REVIEW (F-11): the same docstring also claims `tests/test_run_cli_ledger_message.py` pins the payload key set, and that FILE NO LONGER EXISTS. The convention above still holds (it rests on the bare-dict shape and the zero `agent_schema` imports, both verified), but do not go looking for that test, and do not treat its absence as licence to reshape the payload.
- CITE BY SYMBOL. Per spec `ipd-structure-and-linting` Section 10.2 (advisory `IPD-C801`), code is cited by symbol or quoted string rather than a bare line offset; the backlog item's own `run_cli.py:295-308` and `:708, :850, :878, :971` citations have already rotted (F-1), which is the hazard that convention exists to prevent.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-1 | THE ITEM'S LINE CITATIONS HAVE ROTTED; the defect has not. The item cites `run_cli.py:295-308` for the bug and `:708, :850, :878, :971` for the four correct sites. Today there are TEN `except store.LedgerCorruption` handlers at ten different offsets, and eight of them (not four) already pass `EXIT_CORRUPTED_LEDGER`. The described asymmetry is still real, so the item is confirmed, not invalidated; only its offsets and its count are stale. | `grep -c "except store.LedgerCorruption" agent_workflows/run_cli.py` -> `10`; `grep -n "EXIT_CORRUPTED_LEDGER" agent_workflows/run_cli.py \| grep -v "int = 5"` -> eight usage sites; none of the cited offsets (295-308, 708, 850, 878, 971) holds the described code. |
| F-2 | THE DEFECT IS AT THREE SITES, NOT THE ONE THE ITEM NAMES. `_run_show` and `_run_evidence` carry byte-identical `LedgerCorruption` handlers, both with `{"ok": False, "error": err_msg, "corrupted": True, "exit_code": 2}` and `return 2`. `_run_verify_ledger` reports the same corruption via `verify_chain(raise_on_error=False)`'s return value with `"exit_code": 2` and `return 2`, which is why an exception-name grep misses it. The arithmetic closes: 10 `LedgerCorruption` handlers = 8 already correct (F-1) + the 2 hardcoded ones, and `verify-ledger` is the third site because it never raises. Fixing only `show` would leave two verbs diverging and the bug still filed-and-shipped. | `grep -c '"corrupted": True, "exit_code": 2' agent_workflows/run_cli.py` -> `2` (the two identical handlers); `grep -n "chain_clean" agent_workflows/run_cli.py` -> the `False` branch carrying the third `"exit_code": 2`; measured exits in F-3. |
| F-3 | THE SPLIT IS NOT "READ-ONLY IS LENIENT", WHICH IS THE ITEM'S OPEN DECISION. `status`, `next`, and `resume` are equally read-only inspection verbs and they already return 5 on the same tampered ledger. So read-only posture cannot be the reason `show` returns 2; three read-only verbs return 5 and three return 2. The item's second option is refuted by measurement. | Measured on a two-record ledger with `prev_hash` tampered at seq 1: `show` -> 2, `evidence` -> 2, `verify-ledger` -> 2, `status` -> 5, `next` -> 5, `resume` -> 5. |
| F-4 | THE SPLIT IS MIGRATION RESIDUE, AND GIT SAYS SO. `show`/`evidence`/`verify-ledger` were introduced by `a7ce5ce9` (`feat(run): evidence capture, validators, completion predicates, and run CLI`), whose `run_cli.py` contains ZERO `EXIT_` constants and only bare `return 2` (twelve of them). The exit-code table was added later by `caf658b4` (`awoptimize Order 07 (7yqm1v)`), which used the new constants in the verbs it was adding and did not retrofit the three pre-existing readers. No commit ever decided that `show` should be lenient. | `git log --oneline --diff-filter=A -- agent_workflows/run_cli.py` -> `a7ce5ce9`; `git show a7ce5ce9:agent_workflows/run_cli.py \| grep -n "EXIT_\|return 2"` -> twelve bare `return 2`, no constants; `git log --oneline -S EXIT_CORRUPTED_LEDGER -- agent_workflows/run_cli.py \| tail -1` -> `caf658b4`. |
| F-5 | THE MODULE DOCSTRING ASSERTS THE WRONG CONTRACT, so the bug is also documented-as-intended. Its `Contract:` block says `exit 2 = invocation error, missing ledger, or corrupted hash chain / unparseable JSON`, which directly contradicts `EXIT_CORRUPTED_LEDGER: int = 5  # hash chain / schema / torn-line corruption` in the same file. Whichever code wins, one of these two statements must change, which is why E-04 is not optional polish. | Both strings quoted from `agent_workflows/run_cli.py`. |
| F-6 | THE COVERAGE THE ITEM RELIES ON NO LONGER EXISTS. The item says the behavior is `now PINNED` in `tests/test_run_recovery_cli.py` and that fixing the code `requires updating that one row`. That file was deleted wholesale by `19313eed` (`test: trim test suite from 9,136 to under 2,000 tests`, 2737 deletions). `EXIT_CORRUPTED_LEDGER` and any assertion of exit 5 now grep to ZERO across `tests/`. So this fix breaks no existing row, and it must ADD coverage rather than edit a row; E-05 exists because of this finding. | `git show 19313eed --stat -- tests/test_run_recovery_cli.py` -> `2737 ----`; `grep -rn "EXIT_CORRUPTED_LEDGER" tests/` -> no matches; `ls tests/test_run_recovery_cli.py` -> No such file. |
| F-7 | NO IN-REPO CONSUMER BRANCHES ON 2 FROM THESE VERBS, so the change is low-blast-radius. The in-tree references to these verbs are suggestion strings in prose (`Inspect them with aw runs show <run-id>`, `inspect it with: aw runs verify-ledger <run-id>`) and command-surface registry entries, none of which read an exit code. The `run_viewer` comment about `verify-ledger <absent>` concerns the MISSING-ledger case (a genuine `EXIT_INVALID_INVOCATION` 2), which this plan does not touch. | `grep -rn "runs show\|runs evidence\|verify-ledger" --include=*.py agent_workflows/` reviewed; matches in `runner_shared`, `run_evidence`, `run_viewer`, `command_surface`. |
| F-8 | ADDED AT REVIEW. **THE `Contract:` BLOCK E-04 EDITS IS A PARTIAL TABLE, NOT A FULL ONE, so deleting the corruption clause needs care.** The block enumerates exits 0, 1, 2 and 7 ONLY; exits 3 (`EXIT_BLOCKED`), 4 (`EXIT_INVALID_EVIDENCE`), 5 (`EXIT_CORRUPTED_LEDGER`) and 6 (`EXIT_OPERATIONAL`) are absent from it entirely. Two consequences for E-04. FIRST, striking the corruption clause leaves `exit 2 = invocation error, missing ledger`, which reads as an exhaustive pair while `EXIT_INVALID_INVOCATION` is ALSO what the `except Exception` read-failure branches return, the very branches E-01/E-02 deliberately preserve; so the surviving line must name the read-failure case or the docstring trades one falsehood for another. SECOND, E-04 must NOT be read as licence to write out all eight codes: the constant block is the authority and four unmeasured lines would be gold-plating. E-04 now states both. | Read of the `Contract:` block: four exit lines, for 0, 1, 2 and 7; read of the eight `EXIT_*` constant definitions; the `except Exception` branches at `_run_show` and `_run_evidence` both emitting `"exit_code": 2` and returning 2. |
| F-9 | ADDED AT REVIEW. **THE E-05 LEDGER FIXTURE IS NON-OBVIOUS AND A NAIVE `append` IS REFUSED, which is the likeliest place this plan stalls in execution.** `RunLedgerStore.append` schema-validates and raises `SchemaInvalidRecordError`. Review needed five attempts. Measured requirements: `schema_version` must be the INT `2` (the string `"1"` is refused `RL-E011`); `actor` must be in `run_ledger_schema.ROLES` (`test` is refused `RL-E014`, `coordinator` works); `run_id` must match `_RUN_ID_RE` = `^run-[0-9a-f]{8,}$` (`r1` is refused `RL-E015`); a `kind="run"` record also needs `repo`, `workflow_digest`, `requirement_digest`, `head`; and `item`/`requirement`/`note` are NOT in `RECORD_KINDS` (all three refused `RL-E013`), while `step_attempt` works with the `_KIND_FIELDS`-declared `step`, `state` and `attempt` (int). The working pair then verifies `clean=True` before tamper and `clean=False` after, with `ChainBreak(seq=1, reason='prev_hash mismatch')`. E-05 now carries this so the executor does not rediscover it. | Five successive scratch builds with their exact `SchemaInvalidRecordError` findings pasted; the module symbols `ROLES`, `_RUN_ID_RE`, `RECORD_KINDS`, `_KIND_FIELDS` read directly; the final fixture's `verify_chain(raise_on_error=False)` before/after. |
| F-10 | ADDED AT REVIEW. **EVERY AUTHORED FINDING REPRODUCED, AND THE FIX WAS MEASURED SAFE BEFORE APPROVAL.** F-1 (10 handlers, 8 already correct), F-2 (the two byte-identical handlers plus the `chain_clean: False` third site), F-3 (the sweep reads exactly `2,2,2,5,5,5`), F-4 (`a7ce5ce9` has 0 `EXIT_` constants and 12 bare `return 2`; `caf658b4` added the table), F-5 (the docstring clause), F-6 (`tests/test_run_recovery_cli.py` absent, `2737` deletions, `EXIT_CORRUPTED_LEDGER` greps to zero in `tests/`) and F-7 all hold. Staging E-01..E-03 IN MEMORY then re-running the bare suite gives `3160 passed, 2 skipped`, identical to the unpatched baseline, and the post-fix sweep reads `5,5,5` with `corrupted:true` and `chain_clean:false` both preserved. `tests/test_run_viewer.py` and `tests/test_runs_repo_alias.py` (the two modules nearest this surface) give `60 passed` under the staging. | The six reproductions; the in-memory plugin source; the two bare full-suite runs; the before/after sweeps; the targeted 60-test run; `git status --short` empty throughout. |
| F-11 | ADDED AT REVIEW. **ONE CITATION THE PLAN INHERITS IS STALE, THOUGH IT IS QUOTED FAITHFULLY AND IS HARMLESS HERE.** The plan's Step-0 conventions cite `_emit_error`'s docstring, which says `tests/test_run_cli_ledger_message.py` "still pins the unknown-target payload's key set exactly". That file DOES NOT EXIST (almost certainly removed by the same `19313eed` suite trim F-6 already measures). The plan quoted the docstring accurately, so this is the docstring's defect and not the plan's, and it does not touch the fix: all three in-scope sites call `_emit_machine` directly, never `_emit_error`, so no claim in that docstring is load-bearing for E-01..E-03. Recorded so an executor who goes looking for that file does not conclude the plan is wrong, and so the dangling reference is on the record. | `ls tests/test_run_cli_ledger_message.py` -> No such file; read of the `_emit_error` docstring sentence; `grep -n "_emit_machine("` showing the three in-scope sites at the `LedgerCorruption` and `chain_clean` branches all use `_emit_machine`. |

## Proposed changes (ordered, validatable)

1. `_run_show`: `LedgerCorruption` branch returns `EXIT_CORRUPTED_LEDGER` and emits `"exit_code": EXIT_CORRUPTED_LEDGER` (E-01).
2. `_run_evidence`: same one-branch change (E-02).
3. `_run_verify_ledger`: broken-chain branch returns `EXIT_CORRUPTED_LEDGER` and emits it (E-03).
4. Module docstring `Contract:` block: move the corruption class off the exit-2 line and onto an exit-5 line, keeping the exit-2 line honest about the read-failure case the `except Exception` branches still return (E-04, per F-8).
5. New `tests/test_run_cli_corruption_exit.py` pinning exit code and payload for all six corruption-reporting readers, on a fixture built per the measured schema requirements in F-9 (E-05).

A DELIBERATE BEHAVIOR CHANGE, STATED PLAINLY. This alters a machine-visible contract: three verbs that returned 2 on a corrupt ledger will return 5. That is the point of the item, the direction is the one eight sibling handlers already implement, and F-7 records that no in-repo consumer branches on the old value. An out-of-tree wrapper that treats "nonzero" as failure is unaffected; one that specifically tests `== 2` to mean "bad invocation" gets MORE correct behavior, since a corrupt ledger was never a bad invocation. MEASURED SAFE AT REVIEW (F-10): with E-01..E-03 staged in memory the bare suite is unchanged at `3160 passed, 2 skipped` and the two nearest modules give `60 passed`, so no shipped test pins the old value and the change is verified against the suite before approval rather than after.

## Deferred / out of scope (with reason)

- RECONCILING `run_cli`'s TABLE WITH SPEC 5.6's. `run_evidence`'s comment records that the two disagree at 4 and above and that no plan owns the reconciliation. That is a spec-amending change across two surfaces; this plan deliberately stays inside the table already declared to govern these three verbs, and does not make the disagreement worse (it removes one divergence within `run_cli`).
  - Carrier-Declined: This plan owes nothing here, and naming a carrier would misattribute a PRE-EXISTING condition to it. The disagreement is recorded in-tree already, at the definition site, by `run_evidence`'s own comment ("this package ships TWO exit tables that DISAGREE at the same numbers ... Reconciling the two tables is a separate concern that no plan currently owns") and by spec `25kzda` Section 5.6's explicit `UNRECONCILED CONFLICT` note, which assigns the work to whoever binds abort classes to exit codes. So the obligation is durably captured where a future implementer will actually encounter it and does not depend on this plan to survive. This plan strictly REDUCES divergence: it removes one of the two disagreements inside `run_cli` and adds none, so nothing it does is left unfinished. Searched for an existing owner before declining (`aw find backlog "exit table"` -> no matching backlog); filing a new item for a conflict two authoritative sites already document would duplicate the record, not preserve it.
- THE `except Exception` FALLBACKS at the same handlers. They catch read failures, not corruption, and `EXIT_INVALID_INVOCATION` is defensible there. Changing them would widen a one-class fix into a judgement about every unexpected read error.
  - Carrier-Declined: Nothing is owed. This row records a deliberate BOUNDARY rather than outstanding work: an unexpected read failure is not the ledger-corruption class this item is about, and `EXIT_INVALID_INVOCATION` is a defensible code for it. No defect is left behind by not touching it, so naming a carrier would assert an obligation that does not exist.
- `EXIT_NOT_A_LEDGER` AND THE WRONG-FORMAT PATH (`e6b9kt`). Settled, separate, and untouched.
  - Carrier-Declined: Nothing is owed. This path is already CORRECT and was deliberately settled by `e6b9kt` (`_emit_not_a_ledger`'s docstring records that its message must not contain the word corrupt, and it returns `corrupted: false`). The row exists to state a prohibition on this plan, not to defer work; carrying it forward would invite a future plan to reopen a closed decision.
- CONVERTING THESE PAYLOADS TO `aw.agent/v1`. `_emit_error`'s docstring records this as a known, separately-owned gap affecting every emit site in the module; doing it here would silently change what every existing consumer parses.
  - Carrier-Declined: This plan owes nothing, and the obligation is already durably recorded at its own definition site rather than depending on this plan. `_emit_error`'s docstring states it explicitly ("DELIBERATELY NOT AN `aw.agent/v1` RECORD (F-16)"), names the reason, and notes that `tests/test_run_cli_ledger_message.py` pins the current payload shape. It is a whole-module contract change across every emit site, not a residue of this three-line fix, and this plan neither creates nor widens it: it changes the VALUE of an existing `exit_code` key and adds no new payload shape.

## Scope check

- Over-scope: none. Every edit is inside one of the two declared Scope-Paths, and the three deferrals above are the things a reader might expect to be swept in.
- Under-scope: the backlog item names only `aw runs show`. This plan also fixes `evidence` and `verify-ledger` (F-2) because they are the same defect in the same module, and leaving them would ship the asymmetry the item exists to remove. The item's requirements are not modified: its named verb is fixed, and its DECISION NEEDED is answered from evidence (F-3/F-4) rather than reinterpreted.

## Required tests / validation

- `python3 -m pytest tests/test_run_cli_corruption_exit.py` must pass post-fix, with the pasted `N passed` line.
- The same file must FAIL pre-fix for the three in-scope rows. Capture that before applying E-01..E-03 (or by stashing them), because a test that never failed proves nothing about the bug.
- Full bare suite `python3 -m pytest` must pass, with actual output pasted. Bare per AGENTS: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. RE-DERIVE YOUR OWN BEFORE-BASELINE AND STATE THE DELTA AGAINST IT, rather than against any number in this plan; review measured `3160 passed, 2 skipped` on a clean tree and the tree moves by tens of tests a day, so a transcribed total is meaningless by the time this executes. Review also measured the bare suite at the SAME count with E-01..E-03 staged in memory (F-10), so a non-zero delta beyond the tests E-05/E-06 add is this plan's to explain.
- `python3 -m pytest -o addopts="" -q tests/test_run_viewer.py tests/test_runs_repo_alias.py` as the targeted neighbour set: these are the two modules nearest this surface, and review measured `60 passed` under the staged change (F-10), so a failure here is an implementation defect rather than an inherent consequence.
- Direct end-to-end measurement of all six verbs against a tampered ledger, with the observed exit codes pasted.
- STAGE ANY PRE-FIX COMPARISON IN MEMORY, NOT BY MUTATING A TRACKED FILE. `agent_workflows/run_cli.py` is a shared-checkout file and a `git stash`/`git checkout` restore around a minute-long suite run can discard a co-worker's concurrent edit. Patch or wrap the three handlers from a scratch script or a pytest plugin outside the tree (review used `-p` with a plugin on `PYTHONPATH`), and paste `git status --short` empty before and after each proof. Where a stash is genuinely unavoidable, scope it to the single path and say so.

## Spec / documentation sync

- NO SPEC AMENDMENT REQUIRED, verified rather than assumed. No `.spec.md` states an exit code for `aw runs show|evidence|verify-ledger` on corruption. Spec `25kzda` Section 5.6 tabulates RUN aggregate exit codes and explicitly flags its own `4`-and-above conflict with `run_cli.py` as UNRECONCILED, assigning that reconciliation to whoever binds abort classes to exit codes; it does not govern these three readers (`run_evidence`'s comment names `run_cli`'s table as the one in force for them). `Scope-Paths` therefore declares no spec file, which is why the runners' spec-edit announcer will report none for this plan.
- DOCS: `docs/recovery.md` mentions `aw runs verify-ledger` reporting a broken chain but states no exit code, so it needs no change. `docs/cli-agent-protocol.md` describes the `aw.agent/v1` envelope, which these bare-dict payloads deliberately do not use (F-5 note / `_emit_error` docstring), so it is not in scope.
- THE IN-FILE CONTRACT IS THE DOCUMENTATION THAT MUST CHANGE: E-04 corrects the `run_cli` module docstring, which is the only place stating the wrong code.

## Open questions

### OQ-01: Should `aw runs show` return 5 like its siblings, or is it deliberately lenient because it is a read-only inspection verb?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as "return 5", so this is not a human decision. The item framed this as a genuine choice and asked that it not be assumed; two independent lines of evidence settle it. FIRST, the leniency rationale is refuted by measurement: `status`, `next`, and `resume` are equally read-only and already return 5 on the same tampered ledger (F-3), so read-only posture does not predict the code. SECOND, git shows the split is residue, not a decision: the three divergent readers predate the exit-code table entirely (`a7ce5ce9` has only bare `return 2`), and the commit that introduced the constants (`caf658b4`) applied them to the verbs it added without retrofitting the older readers (F-4). No commit, comment, spec, or test ever asserts leniency for `show`. The item's fallback instruction ("if lenient, the constant should still be used for the payload and the divergence documented at the definition site") is therefore not triggered. Escalation would be asking the maintainer to re-decide something the repository already answers, which the plan-authoring contract directs against.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the observed exit code and full `--agent` payload for `aw runs show <tampered-ledger>`. Must show exit `5` and a payload containing BOTH `"exit_code":5` and `"corrupted":true`. Also paste the adjacent `except Exception` branch source to show it still reads `EXIT_INVALID_INVOCATION`, proving only the corruption branch moved.
  - Observed evidence: PASS. Details:
    Observed command output on tampered ledger:
    ```sh
    $ python3 -m agent_workflows runs show /tmp/.../corrupted_run.ledger.jsonl --agent
    {"corrupted":true,"error":"error: ledger corruption detected: Broken hash chain at seq 1: expected prev_hash '5cdcea55a7b3357c267c494c8465a394a82118abefae6c22d8c5f27bd61224b9', got '0000000000000000000000000000000000000000000000000000000000000000'","exit_code":5,"ok":false}
    Exit code: 5
    ```

    Adjacent `except Exception` branch in `_run_show` (agent_workflows/run_cli.py lines 528-534) showing it is preserved and returns exit 2 (EXIT_INVALID_INVOCATION):
    ```python
    except Exception as exc:
        err_msg = f"error: failed to read ledger: {exc}"
        if machine:
            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
        else:
            print(err_msg)
        return 2
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the observed exit code and `--agent` payload for `aw runs evidence <tampered-ledger>`: exit `5`, payload with `"exit_code":5` and `"corrupted":true`.
  - Observed evidence: PASS. Details:
    Observed command output on tampered ledger:
    ```sh
    $ python3 -m agent_workflows runs evidence /tmp/.../corrupted_run.ledger.jsonl --agent
    {"corrupted":true,"error":"error: ledger corruption detected: Broken hash chain at seq 1: expected prev_hash 'b43ef4c402bd3f471be96b67e234d3ed8ad2801797e7ec6a9b322e3a9ad42099', got '0000000000000000000000000000000000000000000000000000000000000000'","exit_code":5,"ok":false}
    Exit code: 5
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the observed exit code and `--agent` payload for `aw runs verify-ledger <tampered-ledger>`: exit `5`, payload with `"exit_code":5` AND the unchanged `"chain_clean":false`.
  - Observed evidence: PASS. Details:
    Observed command output on tampered ledger:
    ```sh
    $ python3 -m agent_workflows runs verify-ledger /tmp/.../corrupted_run.ledger.jsonl --agent
    {"chain_clean":false,"error":"Broken chain at seq 1: prev_hash mismatch (expected '6fe7fe097bac2dd37848a11d07c2022fc8cf9f7316e1f3d6acec6eb6224d3ee9', got '0000000000000000000000000000000000000000000000000000000000000000')","exit_code":5,"ok":false,"records_checked":1}
    Exit code: 5
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the corrected `Contract:` block from the `run_cli` module docstring beside the `EXIT_CORRUPTED_LEDGER: int = 5` definition line, showing the two now agree and that the exit-7 wrong-format line is unchanged. Additionally paste `grep -n "corrupted hash chain" agent_workflows/run_cli.py` showing that phrase is no longer on the exit-2 line. THEN CONFIRM THE SURVIVING EXIT-2 LINE IS NOT ITSELF NOW FALSE (F-8): it must still cover the unexpected-read-failure case, because `EXIT_INVALID_INVOCATION` is what the `except Exception` branches E-01/E-02 preserve return, and a line reading only `invocation error, missing ledger` would imply those branches exit 5. Also confirm the block was NOT expanded into a full eight-code table; only the corruption clause moves and the exit-5 line is added.
  - Observed evidence: PASS. Details:
    Corrected `Contract:` block (agent_workflows/run_cli.py lines 21-29):
    ```python
    Contract:
      * exit 0 = success / clean / complete;
        exit 1 = incomplete / invalid evidence / unsatisfied requirements;
        exit 2 = invocation error, missing ledger, or unexpected read failure;
        exit 5 = corrupted hash chain / unparseable JSON;
        exit 7 = the target is healthy JSONL of some OTHER format, i.e. not a ledger at all.
      * WRONG-FORMAT IS NOT CORRUPTION. A file that carries none of the ledger envelope fields gets a
        'not a run ledger file' verdict (exit 7), never a corruption verdict: reporting healthy driver
        event logs as corrupt accused good data of damage it did not have (`e6b9kt`).
    ```

    Constant definition (agent_workflows/run_cli.py lines 55-63):
    ```python
    EXIT_CORRUPTED_LEDGER: int = 5  # hash chain / schema / torn-line corruption
    EXIT_OPERATIONAL: int = (
        6  # operational failure (lock contention, illegal transition, unauthorized)
    )
    EXIT_INVALID_INVOCATION: int = 2  # bad invocation / missing ledger
    EXIT_NOT_A_LEDGER: int = (
        7  # the target is healthy JSONL but is NOT a ledger (wrong format, NOT corruption)
    )
    ```

    Grep output confirming "corrupted hash chain" is on the exit-5 line and no longer on the exit-2 line:
    ```sh
    $ grep -n "corrupted hash chain" agent_workflows/run_cli.py
    25:    exit 5 = corrupted hash chain / unparseable JSON;
    ```
    Surviving exit-2 line correctly states: `exit 2 = invocation error, missing ledger, or unexpected read failure;` covering unexpected read failure (from the preserved `except Exception` branches). The block was not expanded into an eight-code table.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FIVE pasted artifacts. (1) The PRE-fix run of `python3 -m pytest tests/test_run_cli_corruption_exit.py` showing the three in-scope rows FAILING with observed `2 != 5`, which proves the test detects the bug, AND the three control rows (`status`, `next`, `resume`) PASSING in that same pre-fix run, which is what makes them controls rather than decoration. (2) The POST-fix run of the same file showing `N passed`. (3) YOUR OWN re-derived clean-tree bare baseline, then the post-change bare `python3 -m pytest`, with the delta stated against your baseline and accounted for by the tests E-05/E-06 add; do not state a delta against any number transcribed from this plan (F-10). (4) THE FIXTURE'S OWN INTEGRITY PROOF: `verify_chain(raise_on_error=False).clean` True BEFORE the tamper and False after, with the `ChainBreak` reason, so the record shows a real chain break rather than a fixture that merely failed to build (F-9). (5) `git status --short` empty, proving the pre-fix comparison was staged in memory and no tracked file was mutated. A test that was never observed red does not satisfy this item.
  - Observed evidence: PASS. Details:
    (1) PRE-fix run of pytest tests/test_run_cli_corruption_exit.py before applying edits to run_cli.py:
    ```
    FAILED tests/test_run_cli_corruption_exit.py::test_corrupted_ledger_readers[evidence]
    FAILED tests/test_run_cli_corruption_exit.py::test_corrupted_ledger_readers[show]
    FAILED tests/test_run_cli_corruption_exit.py::test_corrupted_ledger_readers[verify-ledger]
    3 failed, 5 passed in 2.68s
    ```
    Observed assertions: `AssertionError: Verb 'aw runs show' exited 2, expected 5` (`assert 2 == 5`), `AssertionError: Verb 'aw runs evidence' exited 2, expected 5` (`assert 2 == 5`), `AssertionError: Verb 'aw runs verify-ledger' exited 2, expected 5` (`assert 2 == 5`). Control rows `status`, `next`, `resume`, along with `missing_ledger` and `fixture_integrity`, passed in this pre-fix run.

    (2) POST-fix run of pytest tests/test_run_cli_corruption_exit.py:
    ```
    8 passed in 2.47s
    ```

    (3) Suite baseline and post-change comparison:
    Re-derived clean-tree bare baseline:
    ```
    3312 passed, 2 skipped, 3 warnings in 213.80s (0:03:33)
    ```
    Post-change bare pytest run:
    ```
    3320 passed, 2 skipped, 3 warnings in 144.53s (0:02:24)
    ```
    Delta: exactly +8 passed, fully accounted for by the 8 tests added in tests/test_run_cli_corruption_exit.py (6 reader cases + 1 missing ledger case + 1 fixture integrity test).

    (4) Fixture integrity proof:
    `verify_chain(raise_on_error=False).clean` is True before tamper and False after tamper:
    ```
    Before tamper clean: True
    After tamper clean: False ChainBreak(seq=1, expected='a42952e22ca2a14e23af60d2a290356e38f3bb86a224a8684e78e04c95445a60', actual='0000000000000000000000000000000000000000000000000000000000000000', reason='prev_hash mismatch')
    ```
    Also pinned by `test_fixture_integrity` passing.

    (5) Clean tree verification before modifying tracked files:
    `git status --short` was empty at turn start; `tests/test_run_cli_corruption_exit.py` was created and run against untracked/unmodified `agent_workflows/run_cli.py`, capturing the red state without mutating tracked files.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: TWO pasted artifacts. (1) The observed exit code of `aw runs show /nonexistent/ledger.jsonl`, which must still be `2`, proving exit 2 still means invalid invocation and that the two classes are now distinguishable. (2) A single measurement sweep over all six corruption-reporting readers (`show`, `evidence`, `verify-ledger`, `status`, `next`, `resume`) against one tampered ledger, showing ALL SIX at exit `5`: pre-fix this sweep read `2,2,2,5,5,5` (F-3) and post-fix it must read `5,5,5,5,5,5`.
  - Observed evidence: PASS. Details:
    (1) Observed command output for nonexistent ledger:
    ```sh
    $ python3 -m agent_workflows runs show /nonexistent/ledger.jsonl --agent
    {"error":"ledger file not found for target '/nonexistent/ledger.jsonl'","exit_code":2,"ok":false}
    Exit code: 2
    ```

    (2) Sweep over all six corruption-reporting readers against one tampered ledger:
    ```
    SWEEP RESULTS:
      show: exit 5
      evidence: exit 5
      verify-ledger: exit 5
      status: exit 5
      next: exit 5
      resume: exit 5
    SWEEP CODES: [5, 5, 5, 5, 5, 5]
    ```
    Post-fix reads 5, 5, 5, 5, 5, 5 (converged from pre-fix 2, 2, 2, 5, 5, 5).
  - Result: pass

## Approval and execution gate

This plan is `to-review` and has NOT been reviewed or approved; it must not execute until a human approves it. Per the execution contract: commit only the files changed, limited to the declared `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste actual runner output for every test claim; do not assert a passing suite that was not run.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` carries real observed evidence, run `aw ipd lint --phase pre-transition` and confirm it reports conforming, then move this plan to `.aw/records/plans/executed/` via the tooled transition. Do not mark it executed while any `V-*` result is `pending`. The backlog item `z63xoh` carries `- Blocks-Release: next`, which this plan inherits; the item reaches `graduated` on handoff and may only close `done` once this plan is genuinely executed, which is what preserves the release gate.

- Size assessment: standard
- Cohesion rationale: not required
