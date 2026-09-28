# IPD: Return EXIT_CORRUPTED_LEDGER from the three run readers that hardcode exit 2

- Date: 2026-09-28
- Kind: child
- Concern: `aw runs show|evidence|verify-ledger` report ledger corruption with exit 2 (the invalid-invocation code) instead of `EXIT_CORRUPTED_LEDGER` (5), so a machine caller cannot distinguish a damaged ledger from a mistyped command.
- Scope: Replace the hardcoded `2` with `run_cli.EXIT_CORRUPTED_LEDGER` at the three corruption sites in `run_cli._run_show`, `run_cli._run_evidence`, and `run_cli._run_verify_ledger` (both the returned code and the `exit_code` key in the machine payload); correct the module docstring's exit-code contract, which currently states the wrong code; and add behavioral coverage asserting the code and payload for every affected verb. Out of scope: the unrelated `except Exception` fallbacks, `EXIT_NOT_A_LEDGER`, and the spec-5.6-versus-`run_cli` table reconciliation.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_cli_corruption_exit.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: z63xoh
- Blocks-Release: next
- Set: z63xoh
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: fuuw94

## Workflow history

- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `z63xoh`; resolved the item's DECISION NEEDED from repository evidence (see Findings F-3/F-4) and widened scope from the one verb the item named to the three that actually carry the defect (F-2).

## Goal

Make ledger corruption report one exit code across the whole `aw run`/`aw runs` surface. Eight handlers already return `EXIT_CORRUPTED_LEDGER` (5); three sites return a bare `2`, which this CLI otherwise uses for "bad invocation or missing ledger". A wrapper that branches on 5 to say "your ledger is damaged, recover it" currently sees 2 from these three verbs and cannot tell that case from "you typed the command wrong".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: use the module's own constant at the three divergent sites

- [ ] E-01 In `run_cli._run_show`, replace the `store.LedgerCorruption` handler's hardcoded `"exit_code": 2` and `return 2` with `EXIT_CORRUPTED_LEDGER`. Change ONLY the `LedgerCorruption` branch; leave the adjacent `except Exception` branch (which is a read failure, not corruption) at `EXIT_INVALID_INVOCATION`, and keep `"corrupted": True` in the payload.
  - Depends on: none
  - Expected outcome: `aw runs show <corrupt-ledger>` exits 5, and its `--agent` payload carries `"exit_code": 5` alongside the unchanged `"corrupted": true`.
  - Execution state: pending

- [ ] E-02 In `run_cli._run_evidence`, make the same single-branch change to its `store.LedgerCorruption` handler. This is a byte-identical duplicate of the `_run_show` handler (F-2), so it must move in the same pass or the asymmetry merely relocates.
  - Depends on: E-01
  - Expected outcome: `aw runs evidence <corrupt-ledger>` exits 5 with `"exit_code": 5` and `"corrupted": true`.
  - Execution state: pending

- [ ] E-03 In `run_cli._run_verify_ledger`, replace the `not chain_ver.clean` branch's `"exit_code": 2` and `return 2` with `EXIT_CORRUPTED_LEDGER`. Note this site reports corruption through a `verify_chain(raise_on_error=False)` RETURN VALUE rather than a raised `LedgerCorruption`, so it is not found by grepping for the exception (F-2); its `chain_clean: False` payload key is unchanged.
  - Depends on: E-02
  - Expected outcome: `aw runs verify-ledger <corrupt-ledger>` exits 5, and its payload keeps `"chain_clean": false` while `"exit_code"` becomes 5.
  - Execution state: pending

### Task group 2: correct the stated contract and pin the behavior

- [ ] E-04 Correct the module docstring's `Contract:` block in `run_cli.py`, whose exit-code line currently reads `exit 2 = invocation error, missing ledger, or corrupted hash chain / unparseable JSON`. Corruption is no longer part of that line; state exit 5 for the corrupted hash chain / unparseable JSON class, matching `EXIT_CORRUPTED_LEDGER`'s own definition comment. Leave the `WRONG-FORMAT IS NOT CORRUPTION` paragraph and the exit-7 line untouched: `e6b9kt` settled that distinction and this plan does not revisit it.
  - Depends on: E-03
  - Expected outcome: the docstring no longer contradicts the `EXIT_CORRUPTED_LEDGER` definition in the same module; a reader who trusts the docstring gets the shipped code.
  - Execution state: pending

- [ ] E-05 Add `tests/test_run_cli_corruption_exit.py`: build a real two-record ledger with `run_ledger_store.RunLedgerStore.append`, tamper `prev_hash` on the second record to break the chain, then drive each verb as a subprocess and assert on the exit code and the machine payload. Table-drive it over the verbs so all six corruption-reporting readers are one row each: `show`, `evidence`, `verify-ledger` (the three this plan fixes) AND `status`, `next`, `resume` (the three that already return 5, included as the control that proves the fix converges on existing behavior rather than inventing a new code). Assert the payload keys too (`corrupted: true` for `show`/`evidence`, `chain_clean: false` for `verify-ledger`), so the machine-readable signal is pinned whichever code is chosen later. Build the ledger in a `tempfile` directory, never under the checkout's gitignored `.aw/records/runs/`.
  - Depends on: E-04
  - Expected outcome: a new test module that fails on the pre-fix tree for exactly the three rows in scope and passes on the post-fix tree for all six.
  - Execution state: pending

- [ ] E-06 Add one more row to the same new test file asserting the MISSING-ledger case is NOT affected: `aw runs show /nonexistent/ledger.jsonl` must still exit `EXIT_INVALID_INVOCATION` (2). This is the separating assertion that gives the fix its meaning, because the whole point is that 2 and 5 become distinguishable; without it the suite would still pass if someone made every failure return 5.
  - Depends on: E-05
  - Expected outcome: the test file pins BOTH sides of the contract: corrupt ledger -> 5, absent ledger -> 2.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE EXIT TABLE LIVES IN THE MODULE UNDER CHANGE. `run_cli` defines its own constants (`EXIT_OK` 0, `EXIT_INCOMPLETE` 1, `EXIT_INVALID_INVOCATION` 2, `EXIT_BLOCKED` 3, `EXIT_INVALID_EVIDENCE` 4, `EXIT_CORRUPTED_LEDGER` 5, `EXIT_OPERATIONAL` 6, `EXIT_NOT_A_LEDGER` 7) under the comment `exit-code table (awoptimize Order 07 E-03)`. The fix is to USE an existing constant, not to add one.
- A SECOND, DISAGREEING EXIT TABLE EXISTS AND IS EXPLICITLY OUT OF SCOPE. `run_evidence` carries a comment stating that this package `ships TWO exit tables that DISAGREE at the same numbers`, and names which one governs here: `run_cli`'s table governs the READ-ONLY inspection commands (`aw runs show|evidence|verify-ledger`). That is the authority for the verbs this plan touches, and the same comment records that `Reconciling the two tables is a separate concern that no plan currently owns`. This plan does not take that on; it aligns three sites with the table already declared to govern them.
- WRONG FORMAT IS NOT CORRUPTION, AND THAT PATH IS SEPARATE. `run_cli._emit_not_a_ledger` is deliberately kept apart from every corruption path (its docstring: `the message must not contain the word corrupt`), returning `EXIT_NOT_A_LEDGER` with `corrupted: false`, per `e6b9kt`. Editing the corruption branches cannot disturb it, and no E-item touches it.
- MACHINE PAYLOADS HERE ARE BARE DICTS, NOT `aw.agent/v1`. `_emit_error`'s docstring records this as a deliberate, separately-owned gap (`DELIBERATELY NOT AN aw.agent/v1 RECORD (F-16)`, `run_cli` imports `agent_schema` zero times). So the payload change in scope is the value of the existing `exit_code` key, and this plan must NOT convert these sites to the agent schema.
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

## Proposed changes (ordered, validatable)

1. `_run_show`: `LedgerCorruption` branch returns `EXIT_CORRUPTED_LEDGER` and emits `"exit_code": EXIT_CORRUPTED_LEDGER` (E-01).
2. `_run_evidence`: same one-branch change (E-02).
3. `_run_verify_ledger`: broken-chain branch returns `EXIT_CORRUPTED_LEDGER` and emits it (E-03).
4. Module docstring `Contract:` block: move the corruption class off the exit-2 line and onto an exit-5 line (E-04).
5. New `tests/test_run_cli_corruption_exit.py` pinning exit code and payload for all six corruption-reporting readers (E-05).

A DELIBERATE BEHAVIOR CHANGE, STATED PLAINLY. This alters a machine-visible contract: three verbs that returned 2 on a corrupt ledger will return 5. That is the point of the item, the direction is the one eight sibling handlers already implement, and F-7 records that no in-repo consumer branches on the old value. An out-of-tree wrapper that treats "nonzero" as failure is unaffected; one that specifically tests `== 2` to mean "bad invocation" gets MORE correct behavior, since a corrupt ledger was never a bad invocation.

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
- Full bare suite `python3 -m pytest` must pass, with actual output pasted. Bare per AGENTS: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.
- Direct end-to-end measurement of all six verbs against a tampered ledger, with the observed exit codes pasted.

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

- [ ] V-01 validates E-01
  - Required evidence: paste the observed exit code and full `--agent` payload for `aw runs show <tampered-ledger>`. Must show exit `5` and a payload containing BOTH `"exit_code":5` and `"corrupted":true`. Also paste the adjacent `except Exception` branch source to show it still reads `EXIT_INVALID_INVOCATION`, proving only the corruption branch moved.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the observed exit code and `--agent` payload for `aw runs evidence <tampered-ledger>`: exit `5`, payload with `"exit_code":5` and `"corrupted":true`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the observed exit code and `--agent` payload for `aw runs verify-ledger <tampered-ledger>`: exit `5`, payload with `"exit_code":5` AND the unchanged `"chain_clean":false`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the corrected `Contract:` block from the `run_cli` module docstring beside the `EXIT_CORRUPTED_LEDGER: int = 5` definition line, showing the two now agree and that the exit-7 wrong-format line is unchanged. Additionally paste `grep -n "corrupted hash chain" agent_workflows/run_cli.py` showing that phrase is no longer on the exit-2 line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THREE pasted artifacts. (1) The PRE-fix run of `python3 -m pytest tests/test_run_cli_corruption_exit.py` showing the three in-scope rows FAILING with observed `2 != 5`, which proves the test detects the bug. (2) The POST-fix run of the same file showing `N passed`. (3) The bare full suite `python3 -m pytest` with its real summary line. A test that was never observed red does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: TWO pasted artifacts. (1) The observed exit code of `aw runs show /nonexistent/ledger.jsonl`, which must still be `2`, proving exit 2 still means invalid invocation and that the two classes are now distinguishable. (2) A single measurement sweep over all six corruption-reporting readers (`show`, `evidence`, `verify-ledger`, `status`, `next`, `resume`) against one tampered ledger, showing ALL SIX at exit `5`: pre-fix this sweep read `2,2,2,5,5,5` (F-3) and post-fix it must read `5,5,5,5,5,5`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is `to-review` and has NOT been reviewed or approved; it must not execute until a human approves it. Per the execution contract: commit only the files changed, limited to the declared `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste actual runner output for every test claim; do not assert a passing suite that was not run.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` carries real observed evidence, run `aw ipd lint --phase pre-transition` and confirm it reports conforming, then move this plan to `.aw/records/plans/executed/` via the tooled transition. Do not mark it executed while any `V-*` result is `pending`. The backlog item `z63xoh` carries `- Blocks-Release: next`, which this plan inherits; the item reaches `graduated` on handoff and may only close `done` once this plan is genuinely executed, which is what preserves the release gate.

- Size assessment: standard
- Cohesion rationale: not required
