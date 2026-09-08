# IPD: Map the verifier verdict through one fail-closed table so a schema-valid rejection is not recorded as verified

- Date: 2026-09-08
- Kind: child
- Concern: The verifier PROMPT asks for a three-value verdict but the GATE that consumes it can express only two outcomes, and its fallback is the permissive one. `build_verifier_prompt` instructs the model to write `"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED"` (`oc_runipd.py:4915`, `agy_runipd.py:2575`). The consuming gate is `oc_runipd.py:6422-6434`, duplicated BYTE-IDENTICALLY at `agy_runipd.py:3686-3698` (verified 2026-09-08 by extracting both spans and comparing: identical):
  `verify_verdict = str(v_data.get("verdict", "")).upper()`; `if "BLOCKED" in verify_verdict or "NOT CONFORMING" in verify_verdict:` -> `blocked`/`partial`; `else:` -> `verified`.
  `CORRECTION_REQUIRED` matches neither substring, so a schema-valid REJECTION lands in the `else` and is recorded `verified`. MEASURED at HEAD `44d4950d` by running that branch on the real strings: `VERIFIED`, `CORRECTION_REQUIRED`, `FAILED`, `REJECTED`, `''` and `garbage` ALL yield `verified`; only `BLOCKED` and `NOT CONFORMING` downgrade. So two of the three DOCUMENTED verdicts fail open, as does any typo, any unknown value, and an absent key. The `except Exception:` arm at `oc_runipd.py:6432` also reads unparseable JSON with exit 0 as `verified`.
  THE CORRECT STATE AUTHORITY ALREADY EXISTS AND IS NOT WIRED UP. `run_state.py:34` defines `STATE_CORRECTION_REQUIRED`, `run_state.py:141-146` defines the legal edge `verifying -> correction_required` with `verifier`/`runtime` authority, `run_state.py:149-154` defines `correction_required -> runnable` (a rejected turn returns to runnable rather than completing), `verify_roles.py:369` grants the verifier role that exact `state_authority`, and `agy_verifier.py:49`/`:204` already use `FINAL_CORRECTION_REQUIRED` properly. NEITHER RUNNER IMPORTS ANY OF IT: an AST walk of both drivers for `run_state`, `verify_roles` and `run_recovery` returns ZERO matches (re-measured 2026-09-08). The real importers are `agy_verifier`, `host_runner`, `host_sandbox_profile`, `migration_complex`, `orchestrate_isolation`, `security_hardening`. This is a WIRING GAP between two of the repository's own components, not a missing concept.
  SEVERITY, STATED HONESTLY BECAUSE IT DECIDES THE SHAPE: this is LATENT, not an active leak, and the backlog item itself revised it down. All 34 recorded verification outcomes carry exactly `VERIFIED` (re-measured 2026-09-08 across every `outcomes/*-verification.json`: `Counter({'VERIFIED': 34})`, zero `CORRECTION_REQUIRED`, zero `BLOCKED`, zero unparseable). So a correct gate would have changed the outcome of ZERO historical turns, which REMOVES the "failing closed will start blocking lanes that currently merge" objection: there is no behavior change to negotiate on the existing corpus. It remains worth fixing before the verifier population becomes more willing to reject, because `self_finalize` defaults True (`oc_runipd.py:3062`) and the first genuine rejection would be converted to `verified` and auto-merged.
- Scope: Replace the private two-way substring test in BOTH runners with ONE shared fail-closed verdict mapping that consumes the existing state authority, so all three documented verdicts map explicitly and ANY unrecognized, absent, or unparseable verdict is NOT verified. Add a guard asserting neither runner carries its own verdict test. EXCLUDES changing what the verifier turn DOES or how its prompt is built; excludes the `correction_required -> runnable` REQUEUE behavior beyond recording the state (see OQ-01, deliberately deferred); excludes the verification-skipped defect (sibling `t74o5q`), the model/rate-card record (sibling `vlf75p`), and the unconsumed-evidence defect (sibling `rbftpl`).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_refork_guard.py
- Item-Dependencies: none
- Status: to-review
- Set: runverdict
- Order: 5
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 1bfppy
- Blocks-Release: next
- From-Backlog: wyw936

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `wyw936`, which carries `- Blocks-Release: next`; this plan inherits that gate. EVERY claim in the item was re-measured at HEAD `44d4950d` rather than trusted, and the item held up in full: the eight-string verdict truth table reproduced exactly, the two gate bodies are still BYTE-IDENTICAL across the two hosts (extracted and compared programmatically, not eyeballed), the shared state machine is still unimported by both drivers (AST walk, zero matches), and the corpus is still 34/34 `VERIFIED` with zero rejections and zero unparseable files. FOUR THINGS THE ITEM DID NOT SAY that changed this plan. FIRST, its cited line numbers are all stale by roughly 4250 lines (it cites `oc_runipd.py:2169-2184`; the gate is at `:6422-6434`), which is expected for these two files and is why the gate below forbids line-number navigation. SECOND, the item's severity note names `oc_runipd.py:1427` as `self_finalize`'s default; it is `:3062` now, and the default is indeed `True`. THIRD, the item's `RELATION` says to fix sibling `t74o5q` first because it "fired 23 times"; that sibling's CENTRAL MECHANISM was already fixed at `1549c018` (2026-08-28 02:42 UTC) and all 23 failures predate it, so the ordering advice is obsolete and this plan declares no dependency on it. FOURTH, and this is the design decision the item left open: the item's fix sketch says to "follow the declared transition back to runnable instead of finalizing", which is TWO changes (record the rejection correctly, and requeue on it). This plan does the FIRST and defers the SECOND to OQ-01 with the reason, because requeuing changes retry accounting and the `--retry-budget` contract, and bundling it would make a small provable mapping fix into a scheduling change.
  THE ITEM'S OWN BEHAVIOR-CHANGE WARNING IS FALSIFIED BY ITS OWN MEASUREMENT and this plan records that rather than repeating the warning: with 34/34 `VERIFIED` in the corpus, a fail-closed gate would have blocked nothing historically. The warning stays true PROSPECTIVELY (a garbled verdict from a good turn will now block), and E-05's remedy text is what makes that survivable.

## Goal

Make a verifier's rejection actually reject, and make an unrecognized verdict fail closed, once, in one place both hosts share.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared fail-closed mapping

- [ ] E-01 ADD ONE SHARED VERDICT MAPPING to `runner_shared.py` that takes the raw verdict value and returns the runner's disposition pair, mapping the THREE documented verdicts EXPLICITLY and treating everything else as NOT verified. Locate the current gate by SYMBOL (`build_verifier_prompt`'s consumer inside `execute_item`, the `v_outcome_file` block), never by the line numbers in this plan.
  SITE IT IN `runner_shared.py`, NOT IN `oc_runipd.py`. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and zero flow back, so adding it to oc for agy to import would make it 48 and deepen the layering defect backlog `cnwy8g` owns. `runner_shared` is where both hosts already bind shared decisions (`determine_action` `:2727`, `action_for` `:2735`, `DriverError` `:159`).
  CONSUME THE EXISTING STATE VOCABULARY rather than inventing tokens: `run_state.py:34` already defines `STATE_CORRECTION_REQUIRED`, and `run_state.py` imports NO first-party module at all (AST-verified), so importing it into `runner_shared` cannot create a cycle. Check that before writing the import and say what you found.
  DO NOT DROP THE SUBSTRING MATCH FOR `NOT CONFORMING` WITHOUT CHECKING WHAT WRITES IT. `NOT CONFORMING` is not one of the three documented verdicts and appears in the gate only as a substring test; find out whether any prompt, tool, or historical outcome file actually produces it (grep the prompts and the 34 outcome files). If nothing does, say so and keep it as an accepted alias rather than silently deleting a case a real verifier might still emit; if something does, it is a fourth documented value and must be in the table.
  - Depends on: none
  - Expected outcome: one function in `runner_shared.py` mapping `VERIFIED`, `CORRECTION_REQUIRED` and `BLOCKED` explicitly, anything else to NOT verified; it consumes `run_state`'s existing token rather than a new string; no import cycle; the `NOT CONFORMING` question answered from evidence.
  - Execution state: pending

- [ ] E-02 ROUTE BOTH RUNNERS THROUGH IT AND DELETE BOTH PRIVATE COPIES. The two spans are byte-identical today (measured), so this is one behavior change applied twice, not two changes.
  THE `except Exception:` ARM IS PART OF THE DEFECT, NOT SEPARATE. `verify_disp = "verified" if v_rc == 0 else "unverified"` on unparseable JSON (`oc_runipd.py:6432`, agy `:3696`) means a malformed outcome file with a zero exit reads as verified. Route it through the same mapping so an unreadable verdict is an UNREADABLE verdict, not a passing one. The `else:` arm at `oc_runipd.py:6434` (no outcome file at all) is a DIFFERENT fact and belongs to sibling `t74o5q`; do not change its meaning here, but do not let it silently become the new fail-open path either.
  PRESERVE THE `BLOCKED` BEHAVIOR EXACTLY. `BLOCKED` today yields `verify_disp = "blocked"` AND `disposition = "partial"`. That is correct and must be byte-unchanged, so the fix cannot be claimed as an improvement while regressing the one case that already worked.
  - Depends on: E-01
  - Expected outcome: both runners call the shared mapping; neither retains a substring test; the unparseable-JSON path fails closed; `BLOCKED`'s two-value outcome is unchanged.
  - Execution state: pending

### Task group 2: prove it against the whole corpus

- [ ] E-03 BUILD THE REGRESSION CORPUS FROM THE 34 REAL OUTCOME FILES and assert every one still maps to `verified`. This is the item's own requirement and it is the evidence that the fix breaks nothing: all 34 carry exactly `VERIFIED` (measured 2026-09-08).
  READ THEM AS FIXTURES, NOT FROM THE LIVE TREE. `.aw/records/runs/` is gitignored and several existing tests fail in a lane worktree precisely because they read live run state (roughly 32 environmental failures inside a lane). A test that reads the live corpus will pass here and fail in isolation. Copy the 34 verdict VALUES into a fixture, or generate the eight-string table plus the corpus values, and say which you did.
  - Depends on: E-02
  - Expected outcome: a test asserting all 34 historical verdict values still map to `verified`, driven by a fixture rather than the live gitignored tree.
  - Execution state: pending

- [ ] E-04 ASSERT THE FULL TRUTH TABLE, both the cases that must now fail closed and the two that must not regress. The eight strings measured at HEAD are the minimum set: `VERIFIED` -> verified; `CORRECTION_REQUIRED` -> NOT verified; `BLOCKED` -> blocked plus `partial`; `NOT CONFORMING` -> blocked plus `partial`; `FAILED`, `REJECTED`, `''`, `garbage` -> NOT verified. Add the absent-key case and the malformed-JSON case.
  PASTE THE BEFORE CONTRAST, not just the after. Six of those ten currently return `verified`; a V-item showing only the post-fix table cannot demonstrate the defect existed. Run the pre-fix branch on the same ten inputs and paste both tables side by side.
  - Depends on: E-02
  - Expected outcome: a table-driven test over at least ten inputs including the absent key and malformed JSON; the pre-fix and post-fix results both pasted.
  - Execution state: pending

- [ ] E-05 MAKE THE REFUSAL SAY WHAT TO DO, because a gate that only refuses gets worked around. When the mapping records NOT verified, the run must state which verdict it read, that the verdict is not a pass, and the constructive next step. This is the prospective cost the backlog item warns about (a garbled verdict from an otherwise-good turn will now block a lane), and a named remedy is what makes it survivable rather than mysterious.
  DO NOT DEFINE A REFUSAL RECORD TYPE. Pending plan `r2i1b1` owns the per-item refusal record with its required remedy field, and pending Set `runnoop` (`bsc457`) owns the end-of-run remedy summary. Emit a plain reason string through the existing reporting path; if `r2i1b1` has landed, carry its record instead. Check its status on disk rather than assuming either way.
  DO NOT LOSE THE LANE. An unverified turn already does not auto-merge, because `integration_is_earned` (`oc_runipd.py:3684`) refuses when validation is ON and `verify_disp != "verified"`, and its refusal reason is already explicit ("a green suite deliberately does NOT override an explicit verifier verdict"). Confirm that path still holds after E-02 and that the lane is preserved for a human; that is the recovery route.
  - Depends on: E-02
  - Expected outcome: a NOT-verified mapping produces an operator-visible reason naming the verdict read and the next step; no refusal record type defined here; `integration_is_earned`'s refusal and lane preservation confirmed unchanged.
  - Execution state: pending

- [ ] E-06 ADD THE ANTI-RE-FORK GUARD the backlog item asks for: a test that fails if either runner defines its own verdict test again. Register the shared symbol in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` with BOTH runners listed, which its `test_the_table_covers_both_runners` already enforces, and add an AST assertion that neither driver contains a `"BLOCKED" in`-style substring test on a verdict.
  ASSERT ON BEHAVIOR AND OBJECT IDENTITY, NOT ONLY ON SOURCE TEXT. Grep cannot distinguish a shared object from a textually identical copy, which is exactly how `render_stream` was extracted and then re-forked in the other driver with nothing noticing; the one-sided versions of this guard were RETIRED for that reason. So assert the mapping resolves to the SAME object from `oc_runipd`, `agy_runipd` and `runner_shared`, AND mutation-check the guard.
  - Depends on: E-01, E-02
  - Expected outcome: a `REFORK_TABLE` row covering both runners; an object-identity assertion across all three modules; an AST assertion that no driver carries a private verdict substring test; the guard mutation-checked.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE STATE MACHINE IS ALREADY WRITTEN AND ALREADY GRANTS THE AUTHORITY. `run_state.py` defines `STATE_CORRECTION_REQUIRED` (`:34`), the edge `verifying -> correction_required` with `verifier`/`runtime` authority (`:141-146`), and `correction_required -> runnable` (`:149-154`). `verify_roles.py:369` grants the verifier role that `state_authority` explicitly. `run_state.py` imports NO first-party module (AST-verified), so it is safe to import from `runner_shared`.
- THE RUNNERS DO NOT USE IT. AST walk of both drivers for `run_state`/`verify_roles`/`run_recovery`: zero matches. The importers are `agy_verifier`, `host_runner`, `host_sandbox_profile`, `migration_complex`, `orchestrate_isolation`, `security_hardening`.
- `agy_verifier.py` IS THE WORKED EXAMPLE of doing this right: `FINAL_CORRECTION_REQUIRED` (`:49`) and `finalization = verifier_decision if not reasons else FINAL_CORRECTION_REQUIRED` (`:204`). Read it before designing the mapping; it already chose the fail-closed direction.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`; `oc_runipd` imports zero from agy. A shared symbol goes in `runner_shared`.
- THE VERIFIER'S VERDICT IS NOT COMPLETION AUTHORITY BY DESIGN. Spec `25kzda` §1.2 says the skeptical verifier's "output is advisory until the deterministic checker reproduces each machine-testable assertion", and §4.4 says its findings "require a correction or human disposition rather than being silently treated as machine truth". A fail-closed mapping is consistent with that: it does not grant the verifier new power, it stops the runner from DISCARDING a rejection.
- `.aw/records/runs/` IS GITIGNORED. A test reading it passes in the primary checkout and fails in a lane worktree; roughly 32 tests fail inside a lane for exactly this reason. Use fixtures.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.py:6422-6434`, `agy_runipd.py:3686-3698` | The verdict gate is a two-way substring test whose fallback is `verified`, so `CORRECTION_REQUIRED` (a documented verdict) is recorded as a pass. The two spans are BYTE-IDENTICAL across hosts. | ran the branch on ten inputs; extracted both spans and compared programmatically |
| F-2 | HIGH | same | Six of eight measured inputs fail open: `VERIFIED`, `CORRECTION_REQUIRED`, `FAILED`, `REJECTED`, `''`, `garbage` all -> `verified`. Only `BLOCKED` and `NOT CONFORMING` downgrade. | measured truth table |
| F-3 | HIGH | `oc_runipd.py:6432`, `agy_runipd.py:3696` | `except Exception: verify_disp = "verified" if v_rc == 0 else "unverified"` makes unparseable JSON with exit 0 read as verified. | source read, both hosts |
| F-4 | HIGH | `run_state.py:34`, `:141-154`; `verify_roles.py:369`; `agy_verifier.py:49`, `:204` | The correct state authority, the legal edges, the role grant, and a working implementation all EXIST. | source read |
| F-5 | HIGH | both drivers | Neither driver imports `run_state`, `verify_roles` or `run_recovery`. This is a wiring gap, not a missing concept. | AST walk over `Import`/`ImportFrom` nodes, zero matches |
| F-6 | MED | `oc_runipd.py:4915`, `agy_runipd.py:2575` | The prompt asks for three values while the gate can express two, so the schema and its consumer disagree by construction. | source read |
| F-7 | MED | 34 outcome files | The corpus is 34/34 exactly `VERIFIED`, zero rejections, zero unparseable. So this is LATENT and a correct gate would have changed ZERO historical outcomes, which FALSIFIES the item's "will start blocking lanes that currently merge" objection retrospectively. | `Counter({'VERIFIED': 34})` over every `outcomes/*-verification.json` |
| F-8 | MED | `oc_runipd.py:3062`, `:3684` | `self_finalize` defaults True, and `integration_is_earned` gates auto-merge on `verify_disp == "verified"` when validation is ON. So the fail-open path corrupts what is WRITTEN into the gate variable rather than bypassing the gate, and the first genuine rejection would be converted and merged. | source read |
| F-9 | LOW | backlog `wyw936` | The item's line numbers are stale by roughly 4250 lines (`:2169-2184` cited, `:6422-6434` actual), and its ordering advice to fix `t74o5q` first is obsolete because that sibling's mechanism was fixed at `1549c018`. | grep by symbol; `git log -S` on the fix |

## Proposed changes (ordered, validatable)

1. E-01 adds ONE shared fail-closed mapping in `runner_shared.py`, consuming `run_state`'s existing token.
2. E-02 routes both runners through it, deletes both private copies, closes the unparseable-JSON hole, and preserves `BLOCKED` exactly.
3. E-03 pins the 34-value historical corpus as a fixture so the fix provably breaks nothing.
4. E-04 asserts the full ten-input truth table with the pre-fix contrast pasted.
5. E-05 makes a NOT-verified mapping say which verdict it read and what to do next, without defining a refusal record.
6. E-06 guards against the two copies returning, by object identity and AST, mutation-checked and symmetric.

## Deferred / out of scope (with reason)

- REQUEUING ON `correction_required` (the `correction_required -> runnable` edge). OQ-01. Deferred deliberately: recording the rejection correctly is provable in isolation, while requeuing changes retry accounting and interacts with `--retry-budget` (bounded 0..10 by `run_recovery.validate_retry_budget`) and with `run_queue`'s `--retry-incomplete` status set. Bundling would turn a mapping fix into a scheduling change with a much larger blast radius.
- VERIFICATION SKIPPED ENTIRELY (no outcome file written): sibling `t74o5q`. Its central mechanism was already fixed at `1549c018`, and the `else:` arm this plan leaves alone is its surface, not this plan's.
- THE MODEL AND RATE-CARD RECORD: sibling `vlf75p`. This item concerns a gate that cannot reject; that one concerns a record that cannot attribute.
- VERIFIER EVIDENCE NEVER CONSUMED: sibling `rbftpl`.
- The per-item refusal RECORD and its remedy field: pending plan `r2i1b1`. The end-of-run remedy summary: pending Set `runnoop` (`bsc457`). This plan emits a reason through the existing path and consumes their record if it has landed.
- CHANGING THE VERIFIER PROMPT or the three-value schema. The prompt is already right; the consumer is wrong.
- Making the verifier's verdict COMPLETION authority. Spec `25kzda` §1.2 and §4.4 deliberately make it advisory to the deterministic checker. This plan stops a rejection being discarded; it does not promote the verdict.

## Scope check

- Over-scope: `runner_shared.py` is in scope ONLY to hold the shared mapping. Do NOT change `determine_action`, `action_for`, or `DriverError`. Do NOT edit `run_state.py`, `verify_roles.py` or `agy_verifier.py`: this plan CONSUMES them and must not reshape them.
- Under-scope: stated rather than left as `none`. A rejected turn is recorded correctly but is NOT requeued (OQ-01), and the rejection is not machine-readable in `--json`/`--agent` (that surface belongs to `r2i1b1`).

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Verdict cases belong in `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`; the sharing guard belongs in `tests/test_runner_refork_guard.py`. Fixtures, never the gitignored live run tree. Note `tests/test_runner_shared.py::WrapperTests` counts per-runner call sites deliberately, so if the wiring changes a counted site, reflect it rather than working around it.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) governs verification. THIS PLAN MOVES THE CODE TOWARD IT AND DOES NOT AMEND IT, so no spec file is declared in `- Scope-Paths:`. The relevant approved text, quoted rather than paraphrased: §1.2 defines the skeptical verifier as one whose "output is advisory until the deterministic checker reproduces each machine-testable assertion"; §4.2's `RUN-FRESH-VERIFIER` row requires a "valid evidence-linked envelope" and assigns the action `RETRY, then FAIL ITEM`; and §4.4 says verifier findings "require a correction or human disposition rather than being silently treated as machine truth". A gate that converts `CORRECTION_REQUIRED` into `verified` violates all three, so fixing it needs no amendment.
TWO THINGS TO CHECK RATHER THAN ASSUME. FIRST, §4.2's `RUN-FRESH-VERIFIER` action is `RETRY, then FAIL ITEM`, which is the REQUEUE behavior OQ-01 defers. If the spec is read as REQUIRING the retry, then deferring it leaves a spec gap rather than a design choice, and that must be reported to the maintainer rather than resolved silently. Read the row and say which. SECOND, do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Should a `correction_required` verdict requeue the item to runnable, or only be recorded correctly?

- Blocking: no
- Status: open
- Owner: this plan's executor for the reading, the maintainer for the scheduling decision
- Resolution or deferral rationale: NOT blocking, because recording the rejection correctly already fixes the measured defect (a rejection being discarded and auto-merged), and the plan is complete and provable without the requeue. `run_state.py:149-154` DECLARES the `correction_required -> runnable` edge, so the design intent exists, and spec §4.2's `RUN-FRESH-VERIFIER` row says `RETRY, then FAIL ITEM`, which points the same way. The cost of doing it here: requeuing consumes a retry, so it interacts with `--retry-budget` (bounded 0..10 by `run_recovery.validate_retry_budget`) and with `run_queue`'s `--retry-incomplete` status set, and a verifier that rejects repeatedly could loop. The executor MUST read the spec row and report whether deferring leaves a spec gap; if it does, this becomes a maintainer decision before execution rather than after.

### OQ-02: Is `NOT CONFORMING` a real verdict any producer emits, or a dead substring?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-01 already instructs that it be KEPT as an accepted alias unless evidence shows otherwise, which is the safe default either way. The question is recorded because the answer changes the table's shape: if a producer emits it, it is a fourth documented value and the prompt should say so; if nothing does, it is a dead branch kept for safety and should be labelled as such rather than left looking authoritative. Measured starting point: all 34 historical outcome files carry `VERIFIED` and none carries `NOT CONFORMING`, and the prompt at `oc_runipd.py:4915` offers only the three values. Grep the prompts and any verifier tooling before answering.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the mapping as written and its location in `runner_shared.py`. Paste a `python3 -c` showing it resolves to the SAME object from `oc_runipd`, `agy_runipd` and `runner_shared`. Paste an AST walk showing `run_state.py` still imports no first-party module, and that importing `runner_shared` in a fresh interpreter succeeds (proving no cycle). State OQ-02's answer with the grep that decided it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a diff of both gate sites showing the substring test GONE from each. Paste the `BLOCKED` case's two outputs (`verify_disp` and `disposition`) before and after, showing them IDENTICAL, since that is the one case that already worked. Paste the malformed-JSON case with exit 0 showing it now fails closed, and paste the no-outcome-file case showing its meaning is UNCHANGED (that is `t74o5q`'s surface, not this plan's).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the fixture and the test asserting all 34 historical verdict values still map to `verified`, with the actual runner output. State whether the fixture holds copied values or generated ones, and paste proof the test does NOT read `.aw/records/runs/` (which is gitignored and would make the test pass here and fail in a lane).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste TWO truth tables side by side over the same ten-plus inputs (`VERIFIED`, `CORRECTION_REQUIRED`, `BLOCKED`, `NOT CONFORMING`, `FAILED`, `REJECTED`, `''`, `garbage`, absent key, malformed JSON): the PRE-FIX results and the POST-FIX results. The pre-fix table is the load-bearing half; without it the test cannot demonstrate the defect existed. Paste the test's actual runner output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL operator-visible output for a `CORRECTION_REQUIRED` turn, showing the verdict read and the next step. Paste `r2i1b1`'s `- Status:` line and directory read at validation time, and state which branch applied. Paste proof no refusal record type was defined here (a grep for a record/dataclass definition in the changed files, returning nothing). Paste `integration_is_earned`'s refusal for the NOT-verified case and proof the lane is preserved.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `REFORK_TABLE` row showing BOTH runners listed, and `tests/test_runner_refork_guard.py` passing. Paste the AST assertion and show it FAILS under a mutation that reintroduces a private substring test in ONE driver, then passes after revert. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT edit `run_state.py`, `verify_roles.py`, `run_recovery.py` or `agy_verifier.py`: this plan CONSUMES that state machine and must not reshape it. Do NOT change the verifier PROMPT or its three-value schema. Do NOT implement the `correction_required -> runnable` requeue (OQ-01). Do NOT define a refusal record type. Do NOT change the no-outcome-file branch's meaning (sibling `t74o5q`). Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT edit spec `25kzda`, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day, and the backlog item's own citations were stale by roughly 4250 lines. Find `build_verifier_prompt`, `execute_item`'s `v_outcome_file` block, `integration_is_earned`, `STATE_CORRECTION_REQUIRED`, and `FINAL_CORRECTION_REQUIRED` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 1bfppy --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `wyw936`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits. If OQ-01 resolves that the requeue is REQUIRED by spec §4.2 and is deferred to a follow-on, do NOT close the item: file the follow-on carrying the same gate and mark the item `graduated` instead, so the release gate is not dropped.
