RETIRED 2026-08-30: superseded by `.aw/records/plans/pending/20260830-runcodes-01-wlxkoz-the-deterministic-run-finding-code-vocabulary-over-the-shipp.ipd.md` (`runcodes-01`, id `wlxkoz`). This plan was `REJECT - NEEDS REPLAN` twice, and its SECOND review removed its last surviving substantive item after finally performing the inventory the first pass had deferred: the fresh-verifier harness ships TWICE, as an enforced contract (`agy_verifier.run_fresh_verifier:142` over the 2158-line `verify_roles.py`) and as a live runner turn (`oc_runipd.py:1663`, launched `:2281` with `fresh_session=True`). It is therefore retired rather than re-scoped: after that removal what remained was a vocabulary layer, not a plan to build modules. What its residue turned into: the 13 `RUN-*` finding codes of spec 25kzda 4.2 with their verbatim messages, recovery commands, and failure actions (each re-verified at ZERO hits at HEAD `738980ec`), plus `--unverifiable-ok` aggregate neutrality and the 0..10 retry-budget bound, all carried forward as a thin data layer over the SHIPPED `run_evidence.py`. What did NOT survive, and why: E-02/E-03/E-04/E-06 ship as `run_ledger_store.py` (hash-chained, self-verifying via `verify_chain:529`), `aw run show|evidence|verify-ledger`, `run_evidence.py`, and `run_recovery.py`; building E-04 in particular would have created a SECOND completion authority in the one component whose entire value is being the single trustworthy one, so two disagreeing checkers would mean neither can authorize completion. This plan's BLOCKING OQ-03 is DISCHARGED, not inherited: it demanded the per-check mapping of the 13 codes onto existing predicates before any were written, and that mapping is now measured and recorded as Finding F3 of the successor (nine BOUND to shipped predicates, two UNBOUND pending sibling plans `m73aet`/`mjx7ne`, two UNBOUND-UNBUILT). Its other blocking question (OQ-02, `rununify` sequencing) is dissolved by the successor deferring the runner wiring entirely. Release gate PRESERVED, not dropped: the successor carries `- Blocks-Release: next` and `- From-Spec: 25kzda`. Retired, not deleted; NOT filed under `executed/`, because nothing here was ever implemented.

# IPD: Fresh skeptical verifier session, tamper-evident run ledger, and deterministic completion checker

- Date: 2026-08-30
- Kind: child
- Concern: Work-item completion currently relies on agent exit status and post-execution linter rather than a fresh skeptical audit, hash-chained ledger, and deterministic proof boundary.
- Scope: Implement the fresh skeptical verifier session harness, append-only hash-chained run ledger, the deterministic completion checker implementing all 13 common checks, run resume mechanics, aggregate exit code calculation, and `--unverifiable-ok` neutrality handling. Implements spec 25kzda Sections 1.1, 4.2, 5.1, 5.3, 5.5, and 5.6.
- Scope-Paths: agent_workflows/run_verifier.py, agent_workflows/run_ledger.py, agent_workflows/deterministic_checker.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_deterministic_checker.py
- Item-Dependencies: executed:k7o7el
- Status: superseded
- Set: detrun
- Order: 5
- Highest E allocated: 08
- Author: antigravity
- Id: 7f7782
- Blocks-Release: next

## Workflow history
- 2026-08-31 superseded (aw set): RETIRED: superseded by runcodes-01 (wlxkoz). REJECT - NEEDS REPLAN twice, and its SECOND review removed its last substantive item after doing the inventory the first pass deferred: the fresh-verifier harness ships TWICE (agy_verifier.run_fresh_verifier:142 over verify_roles.py, and a live runner turn at oc_runipd.py:1663/:2281). Residue CARRIED FORWARD: the 13 RUN-* codes of spec 25kzda 4.2 with verbatim messages, recovery commands and failure actions (each re-verified ZERO hits at HEAD 738980ec), plus --unverifiable-ok aggregate neutrality and the 0..10 retry bound, as a thin data layer over the SHIPPED run_evidence.py. NOT carried: E-02/E-03/E-04/E-06 ship as run_ledger_store.py (verify_chain:529), the aw run inspection verbs, run_evidence.py and run_recovery.py; building E-04 would create a SECOND completion authority, so two disagreeing checkers would mean neither can authorize completion. Its BLOCKING OQ-03 is DISCHARGED not inherited: the demanded per-code mapping is measured and recorded as Finding F3 of the successor (9 BOUND, 2 UNBOUND pending m73aet/mjx7ne, 2 UNBOUND-UNBUILT). Release gate PRESERVED on the successor (Blocks-Release: next, From-Spec: 25kzda), not dropped.
- 2026-08-31 to-review (aw set): REVERTING MY OWN ERRONEOUS APPROVAL. I set this approved on 2026-08-30 from the maintainer's blanket instruction 'I APPROVE all the reviewed IPDs', which swept up a plan whose OWN newest /plan-review verdict is REJECT - NEEDS REPLAN. The --by-human attestation was real but the maintainer plainly did not intend to approve a do-not-execute plan; approving on status alone without reading each verdict was my mistake. Flagged by a peer agent (comms fyi 20260831-0126-01) and independently verified: all FIVE detrun plans carry REJECT, not just bmh754. Returning to to-review so 'approved' does not license a rebuild of shipped machinery.
- 2026-08-30 approved (aw set, --by-human): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- 2026-08-30 /plan-review pass 2 (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN reaffirmed; the LAST surviving residue is GONE; PR-201..PR-209. THE DEFERRED INVENTORY IS NOW DONE, and it kills the residue pass 1 preserved. Pass 1 said "the fresh skeptical verifier session harness (E-01) is real work not obviously shipped (`agy_verifier.py` is only 301 lines ...)" and deferred the inventory. Line count was the wrong metric. E-01 IS SHIPPED TWICE OVER: (a) as a PURE contract, `agy_verifier.py` ships `MODE_FRESH_SESSION` vs `MODE_SAME_SESSION_AUDIT` (:42-43), `run_fresh_verifier` (:142), `assert_distinct_sessions` (:131) raising `SessionIdentityCollisionError`, and `finalize_run` (:219) refusing to let a same-session audit finalize - i.e. exactly "zero executor memory inheritance" - consuming `verify_roles.py` (2158 lines), which ships `build_verifier_packet` (:825, frozen requirements + diff + evidence manifest with executor prose STRIPPED, `ExecutorProseLeakError`), 9 verification procedures (:1196-1717), `SelfVerificationForbiddenError`, and `route_verifier_findings` (:1973); (b) as a LIVE runner turn, `oc_runipd.build_verifier_prompt` (:1663) opens "You are an independent, skeptical verifier running in a fresh OpenCode session" and `:2281` launches it with `fresh_session=True` (:1828) and DOWNGRADES the disposition when the verifier finds unmet criteria (:2259). So E-01's stated outcome - "launches a brand-new host session with zero executor memory inheritance, passes frozen predicates + diff, returns structured machine-parseable findings" - is already true end to end. NEW COLLISION (PR-203): E-03 proposes ADDING `aw runs show|evidence|verify` while APPROVED `runnamecollapse-01` (`0soncw`) is retiring `aw run` and collapsing those exact subcommands under `aw runs`; the verbs already exist as `aw run show|evidence|verify-ledger`, so E-03 is a rename that another approved plan owns and would fight. CONFIRMED SHIPPED (PR-202): `run_ledger_store.py` ships `GENESIS_HASH` (:44), `compute_record_hash` (:206), `verify_chain` (:529), `BrokenChainError`/`SequenceGapError`/`UnparseableLineError`, `LEDGER_FILENAME = "ledger.jsonl"` (:49) - E-02's exact deliverable, at E-02's exact path; and `:373` explicitly warns that the drivers' `events.jsonl` is a DIFFERENT thing, the very confusion E-02 would re-create. CONFIRMED SHIPPED (PR-205): resume is `run_recovery.resume` (:366) with `detect_unknown_outcomes` (:351) and fail-closed `UnknownOutcomeError`, plus `retry_budget_remaining` (:340) - E-06's and half of E-05's outcome. GENUINE RESIDUE, and it is thin: the 13 `RUN-*` codes grep to ZERO (verified each individually) and `--unverifiable-ok` greps to ZERO, so the naming/wiring layer on top of the shipped predicates is real - but it is a wiring task over `run_evidence.py`, not the new `deterministic_checker.py` E-04 proposes, and building a second completion authority is the one duplication that is worse than none.
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001. E-02/E-03/E-04/E-06 are ALREADY SHIPPED: hash-chained append-only ledger with corruption refusal (`run_ledger_store.py`: prev_hash/GENESIS_HASH/BrokenChainError), `aw run show|evidence|verify-ledger` (`run_cli.py`), completion predicates + false-completion validators (`run_evidence.py`), resume/cancel/crash recovery (`run_recovery.py`), plus `run_ledger_schema.py`, `run_freeze.py`, `run_gates.py`. Building a second ledger and a second completion authority in the one component that must be the single trustworthy authority is worse than none: two disagreeing checkers mean neither can authorize completion. Residue: the fresh verifier harness (E-01), after inventorying `run_evidence.py`. Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened 13 common deterministic checks, ledger hash chaining, run resume validation, and exit code aggregation.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE (/plan-review 2026-08-30, PR-001 BLOCKER).** This plan is the second-worst
duplication in the Set after child 01. Verified at HEAD `d4d265b6`:

| This plan's E-item | Already shipped as | Evidence |
| --- | --- | --- |
| E-02 append-only hash-chained ledger + `verify_ledger` | `run_ledger_store.py` | `prev_hash` chaining, `GENESIS_HASH`, `BrokenChainError`, `compute_record_hash`, single-writer lock, typed `LedgerCorruption` refusal, redaction hooks (`agent_workflows/run_ledger_store.py:405,476,507`) |
| E-03 `aw runs show/evidence/verify` | `aw run show`, `aw run evidence`, `aw run verify-ledger` | `agent_workflows/run_cli.py`; `aw run --help` lists them |
| E-04 deterministic completion checker | `run_evidence.py` completion predicates + false-completion validators | module docstring E-01..E-03: capture provenance, mechanically validate against "every known false-completion class", deterministic completion predicates |
| E-06 resume mechanics | `run_recovery.py` | E-02 "resume / cancel / crash recovery"; `aw run resume` shipped and "refuse on interrupted side effects" |
| record vocabulary the checker needs | `run_ledger_schema.py` | typed records separating REQUIRED / ATTEMPTED / OBSERVED / VERIFIED |
| requirement freezing the checker compares against | `run_freeze.py` | frozen requirement digests, `requirement_revision`, evidence invalidation |
| human-gate `needs_input` behavior | `run_gates.py` | "consent is NEVER synthesized"; headless stop with stable `needs_input` |

Creating `run_ledger.py` beside the shipped `run_ledger_store.py`, and `deterministic_checker.py`
beside the shipped `run_evidence.py`, would give the repo two ledgers and two completion authorities.
That is precisely the drift GUIDING_PRINCIPLES P8 forbids, and in a component whose entire value is
being the SINGLE trustworthy authority, a second implementation is worse than none: two disagreeing
checkers mean neither can be trusted to authorize completion.

**THE DEFERRED INVENTORY IS NOW DONE, AND IT REMOVES THE LAST SURVIVING RESIDUE (pass 2, PR-201).**
Pass 1 kept E-01 on the grounds that the verifier harness was "real work not obviously shipped
(`agy_verifier.py` is only 301 lines ...)" and explicitly deferred the inventory to a replacement plan.
Line count was the wrong metric, and deferring the inventory was the wrong call: 301 lines is small
because the module CONSUMES `verify_roles.py` (2158 lines). E-01 is shipped TWICE, as a pure contract
and as a live runner turn.

(a) THE PURE CONTRACT, `agent_workflows/agy_verifier.py`:

| E-01 proposes | Shipped |
| --- | --- |
| brand-new session, zero executor memory inheritance | `MODE_FRESH_SESSION` vs `MODE_SAME_SESSION_AUDIT` (`:42-43`); `assert_distinct_sessions` (`:131`) raises `SessionIdentityCollisionError`; `finalize_run` (`:219`) raises `SameSessionCannotFinalizeError` so a same-session audit CANNOT finalize |
| pass frozen predicates + diff | consumes `verify_roles.build_verifier_packet` (`verify_roles.py:825`): frozen requirements, base/head identity, actual diff, untracked inventory, evidence manifest, declared scope, prior attempts - with executor conclusion prose STRIPPED and `ExecutorProseLeakError` if it leaks |
| enforce read-only tool policy | `verify_roles` role contracts: `ProductMutationForbiddenError`, `SelfVerificationForbiddenError`, `enforce_role_action` (`:637`), and terminal authority reserved to the coordinator (`TerminalAuthorityError`) |
| return structured machine-parseable findings | `FreshVerifierResult` (`:98`) with `to_dict()`; `verify_roles` `ProcedureFinding`/`ProcedureResult`/`VerificationReport` (`:1065-1103`) across NINE procedures (`:1196-1717`) plus `route_verifier_findings` (`:1973`) |

(b) THE LIVE RUNNER TURN, already wired: `oc_runipd.build_verifier_prompt` (`:1663`) opens with "You are
an independent, skeptical verifier running in a fresh OpenCode session to audit the execution of this
IPD"; `:2281` launches it as "Turn 2: independent skeptical verification in a fresh session"; `:1828`
documents `fresh_session=True` meaning "a clean session with no inherited context"; and `:2259`
DOWNGRADES the disposition when the verifier finds unmet criteria, so it is load-bearing rather than
advisory. `agy_runipd.py` carries the twin.

So E-01's entire stated outcome is already true. Pass 1's own stated precondition ("a replacement plan
must first inventory `run_evidence.py`") is hereby discharged, and the answer is that the inventory
removes the item rather than scoping it.

WHAT IS GENUINELY UNBUILT, and it is thin and is NOT a module:

- The 13 `RUN-*` finding codes of spec 25kzda 4.2. Verified individually this pass: `RUN-FROZEN-IDENTITY`,
  `RUN-STRUCTURE-PREFLIGHT`, `RUN-BASELINE-OWNERSHIP`, `RUN-LEDGER-INTEGRITY`, `RUN-HOST-CAPABILITY`,
  `RUN-HOST-ATTEMPT`, `RUN-FRESH-VERIFIER`, `RUN-SCOPE-DELTA`, `RUN-COMMIT-CONTENTS`,
  `RUN-COMMIT-GATEWAY`, `RUN-NO-PUSH`, `RUN-CHECK-FRESHNESS`, `RUN-CROSS-TREE` - all ZERO hits. What is
  missing is the stable CODE VOCABULARY and its exact messages/recovery commands, mapped onto predicates
  that mostly already exist in `run_evidence.py`'s false-completion validators. That is a naming and
  wiring layer over the shipped authority, not a second authority.
- `--unverifiable-ok` aggregate neutrality: ZERO hits. Genuinely unbuilt, and small.
- Several of the 13 depend on things that do not exist yet and are owned elsewhere:
  `RUN-COMMIT-GATEWAY`/`RUN-COMMIT-CONTENTS` need the `AW-Run:`/`AW-Item:` trailers (sibling `k7o7el`'s
  sole surviving residue), and `RUN-HOST-CAPABILITY` needs the runner-safety capability vocabulary that
  approved `wtiso-07` (`1o4eif`) claims. So the check family cannot be authored as one unit anyway.

Original goal, retained for the record: provide the skeptical verification and deterministic authority
layer that launches unpolluted verifier sessions, records a tamper-evident hash-chained run ledger,
evaluates deterministic repository state for completion authorization, supports safe run resumption,
and computes honest aggregate exit codes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fresh skeptical verifier session harness

- [ ] E-01 Create `agent_workflows/run_verifier.py` implementing the fresh skeptical verifier turn harness.
  - Depends on: none
  - Expected outcome: **DO NOT BUILD (pass-2 RETRACTION of pass-1's "salvageable residue" call, PR-201). SHIPPED TWICE.** (a) Pure contract: `agy_verifier.py` ships `MODE_FRESH_SESSION`/`MODE_SAME_SESSION_AUDIT` (`:42-43`), `run_fresh_verifier` (`:142`), `assert_distinct_sessions` (`:131`, raises `SessionIdentityCollisionError`), and `finalize_run` (`:219`, a same-session audit CANNOT finalize) - that IS "zero executor memory inheritance", enforced rather than hoped. It consumes `verify_roles.py` (2158 lines) for the frozen-requirements/diff/evidence packet with executor prose stripped (`build_verifier_packet:825`, `ExecutorProseLeakError`), the read-only role policy (`ProductMutationForbiddenError`, `SelfVerificationForbiddenError`, `enforce_role_action:637`), and structured findings (`ProcedureFinding`/`VerificationReport:1065-1103`, nine procedures at `:1196-1717`). (b) Live runner turn: `oc_runipd.build_verifier_prompt:1663` ("an independent, skeptical verifier running in a fresh OpenCode session"), launched at `:2281` with `fresh_session=True` (`:1828`), and it DOWNGRADES the disposition on unmet criteria (`:2259`); `agy_runipd.py` twins it. Pass 1 judged this "not obviously shipped" from a 301-line file size; the file is small because it consumes a 2158-line module. Creating `run_verifier.py` would be a THIRD verifier path. Original expected outcome: Launches a brand-new host session with zero executor memory inheritance, passes frozen predicates + diff, enforces read-only tool policy, and returns structured machine-parseable findings.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. This was pass 1's sole surviving residue; the inventory pass 1 deferred has now been done and removes it. Do not tick this box.

### Task group 2: Tamper-evident run ledger and inspection tools

- [ ] E-02 Create `agent_workflows/run_ledger.py` implementing the append-only, hash-chained run ledger (`.aw/records/runs/<run-id>/ledger.jsonl`).
  - Depends on: none
  - Expected outcome: **DO NOT BUILD (PR-202). SHIPPED as `agent_workflows/run_ledger_store.py`, at THIS ITEM'S EXACT PATH.** `LEDGER_FILENAME = "ledger.jsonl"` (`:49`), `GENESIS_HASH` (`:44`), `compute_record_hash` (`:206`), `prev_hash` assignment under a single-writer lock (`:411-417`), and `verify_chain` (`:529`) returning a typed `ChainVerification` - i.e. this item's `verify_ledger(path) -> bool`, only better typed. Tamper detection is typed and distinct: `BrokenChainError` (`:71`), `SequenceGapError` (`:85`), `UnparseableLineError` (`:95`), `SchemaInvalidRecordError` (`:105`). Note especially `:373`, which already warns that the drivers' `events.jsonl` is a DIFFERENT artifact from a run `ledger.jsonl` - the exact confusion a second ledger module would re-create. A second ledger in the one component whose value is being the single trustworthy record is worse than none. Original expected outcome: Each event record binds to the prior record hash, event payload digest, and captured evidence IDs; provides `verify_ledger(path) -> bool` proving ledger integrity.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Do not tick this box.

- [ ] E-03 Add `aw runs show <run-id>`, `aw runs evidence <run-id>`, and `aw runs verify <run-id>` inspection commands in `agent_workflows/cli.py`.
  - Depends on: E-02
  - Expected outcome: **DO NOT BUILD - SHIPPED, AND NOW A COLLISION WITH AN APPROVED PLAN (PR-203, new this pass).** All three verbs already exist under the `run` noun: `aw run show`, `aw run evidence`, `aw run verify-ledger` (measured from `aw run --help`; dispatch in `run_cli.py`, help text "Run ledger inspection and verification tooling ... Read-only; makes no writes"). So the only delta this item actually proposes is the `run` -> `runs` RENAME plus `verify-ledger` -> `verify`. That rename is EXACTLY the scope of APPROVED `runnamecollapse-01` (`0soncw`), whose title is "Collapse run inspection under aw runs and retire the aw run noun" and whose Scope is "The CLI naming surface only ... No change to ledger semantics". Two plans must not both re-name the same verb group; and note the plan's own metadata is internally inconsistent here, since `aw runs` ALSO already exists today as the driver-run viewer. Original expected outcome: Users can inspect run event timelines, list captured command outputs, and verify cryptographic ledger integrity offline.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Naming is owned by approved `runnamecollapse-01` (`0soncw`). Do not tick this box.

### Task group 3: Deterministic completion checker

- [ ] E-04 Create `agent_workflows/deterministic_checker.py` implementing the comprehensive suite of all 13 deterministic completion checks from spec Section 4.2 (`RUN-FROZEN-IDENTITY`, `RUN-STRUCTURE-PREFLIGHT`, `RUN-BASELINE-OWNERSHIP`, `RUN-LEDGER-INTEGRITY`, `RUN-HOST-CAPABILITY`, `RUN-HOST-ATTEMPT`, `RUN-FRESH-VERIFIER`, `RUN-SCOPE-DELTA`, `RUN-COMMIT-CONTENTS`, `RUN-COMMIT-GATEWAY`, `RUN-NO-PUSH`, `RUN-CHECK-FRESHNESS`, `RUN-CROSS-TREE`).
  - Depends on: E-01, E-02
  - Expected outcome: **SPLIT: THE CODE VOCABULARY IS REAL, THE MODULE AND THE AUTHORITY CLAIM ARE NOT (PR-204).** GENUINE: all 13 `RUN-*` codes grep to ZERO, verified individually this pass, so the stable finding-code vocabulary with 25kzda 4.2's exact messages and recovery commands is unbuilt and worth building. NOT GENUINE: (1) a new `deterministic_checker.py` beside the shipped `run_evidence.py` (1099 lines) would be a SECOND completion authority, and `run_evidence.py`'s docstring already claims exactly this item's role - "completion a deterministic PREDICATE over frozen requirements, valid captured evidence, repository identity, and independent verifier decisions - not prose emitted by an executor" - with E-02 validators against "every known false-completion class with distinct stable reason codes" (missing output, fabricated text, stale HEAD, wrong cwd/worktree, mismatched command, expired host probe, truncated output, failed exit, absent artifact, hash mismatch, executor-authored verifier decision) and E-03 `is_complete`/`evaluate_completion`. Two disagreeing checkers mean NEITHER can authorize completion. (2) "alone authorizes ... terminal transitions" contradicts the shipped authority: `verify_roles` reserves terminal authority to the coordinator (`TerminalAuthorityError`) and `aw ipd finalize` owns the lifecycle transition. (3) It CANNOT be one item anyway: `RUN-COMMIT-GATEWAY`/`RUN-COMMIT-CONTENTS` need the `AW-Run:`/`AW-Item:` trailers (sibling `k7o7el`'s residue, unbuilt) and `RUN-HOST-CAPABILITY` needs the capability vocabulary approved `wtiso-07` (`1o4eif`) claims. CORRECT SHAPE: map each of the 13 codes onto an EXISTING `run_evidence.py` predicate, build only the genuinely missing ones, and state the mapping before writing code. Original expected outcome: Deterministic checker evaluates real repository/git state, verifies commit trailers, reruns check recipes, and alone authorizes `verified` outcomes and terminal transitions.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. The code-vocabulary substance survives into a successor as a wiring layer over `run_evidence.py`; the module and the sole-authority claim do not. Do not tick this box.

- [ ] E-05 Implement aggregate exit code calculation (0, 1, 2, 3, 4, 130), retry budget enforcement (0..10), and `--unverifiable-ok` aggregate neutrality handling in `agent_workflows/deterministic_checker.py`.
  - Depends on: E-04
  - Expected outcome: **PARTLY GENUINE, WRONG HOME, AND ONE PART ALREADY SHIPPED (PR-206).** GENUINE: `--unverifiable-ok` greps to ZERO - unbuilt, small, and worth keeping. ALREADY SHIPPED: retry budget enforcement is `run_recovery.retry_budget_remaining` (`:340`) over `count_retries` with a `DEFAULT_RETRY_LIMIT`, so "retry budget enforcement (0..10)" is a bounds question on an existing helper, not new machinery. PARTLY SHIPPED: exit 130 on interrupt already exists (`oc_runipd.py:3200`). WRONG HOME: it targets `deterministic_checker.py`, a module that must not exist (E-04). Also note bundling three unrelated concerns (exit-code aggregation, retry bounds, a new flag) in one E-item is the right-sizing smell the checklist rule warns about; they are three independent test surfaces. Original expected outcome: Run exit codes reflect exact outcome states; contractless prompts contribute aggregate neutrality under `--unverifiable-ok` without falsifying item-level `ran` / `unavailable` state.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Split it in the successor; `--unverifiable-ok` is the only wholly-unbuilt part. Do not tick this box.

### Task group 4: Run resume mechanics and runner integration

- [ ] E-06 Implement safe run resumption (`aw <host> run --resume <run-id>`) in `agent_workflows/deterministic_checker.py` and wire verifier sessions, ledger recording, and deterministic checks into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-01, E-02, E-04, E-05
  - Expected outcome: **DO NOT BUILD (PR-205/PR-207). Resume is SHIPPED and the runner wiring collides with an approved Set.** `run_recovery.resume` (`:366`) reconstructs state from the ledger and reports resumable steps, refusing to advance when `detect_unknown_outcomes` (`:351`) finds an interrupted side effect - "the fail-closed guarantee against a silent rerun of a possibly-completed side effect" - requiring explicit `reconcile_unknown_outcome` (`:390`), which "never guesses". `aw run resume` is a shipped verb; `aw ipd execute-set --resume` exists (`cli.py:1001`) and `runipd resume <run-id>` exists (`oc_runipd.py:3043`). Separately, this item edits BOTH `oc_runipd.py` and `agy_runipd.py`, fighting APPROVED `rununify` (`5e4sb6`) - parent-Set OQ-03. Original expected outcome: Resume validates ledger integrity, re-evaluates dependency satisfaction for skipped nodes, and continues execution on the frozen DAG without option mutation.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blocked by shipped duplication AND by the `rununify` collision (OQ-02 below). Do not tick this box.

### Task group 5: Test suite coverage and edge cases

- [ ] E-07 Create `tests/test_deterministic_checker.py` covering fresh verifier session invocation, ledger hash chaining, all 13 common deterministic checks, exit code aggregation, run resumption, and inspection CLI commands.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: **CANNOT BE WRITTEN AS SPECIFIED (PR-208).** It tests six items that must not be built, and four of its six named surfaces are already covered by shipped test modules (`tests/test_run_recovery_cli.py`, `tests/test_run_evidence_completion.py`, `tests/test_run_viewer.py` - all three named in APPROVED `runnamecollapse-01`'s own Scope-Paths, which is independent proof the CLI and recovery surfaces have live coverage). "Complete branch coverage" is also unfalsifiable as an acceptance bar and no coverage tool or threshold is named. Retarget onto the residue only: the 13 `RUN-*` code vocabulary and `--unverifiable-ok`, extending the existing modules. Original expected outcome: Full pytest suite passes with complete branch coverage on verification and ledger validation.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Do not tick this box.

- [ ] E-08 Add adversarial verification tests: tampered ledger detection, stale check output rejection, verifier memory inheritance refusal, and resume with modified options rejection.
  - Depends on: E-07
  - Expected outcome: **THREE OF FOUR CASES ARE ALREADY OWNED BY SHIPPED CODE (PR-208).** "Tampered ledger detection" is `run_ledger_store.verify_chain` (`:529`) with typed `BrokenChainError`/`SequenceGapError`. "Stale check output rejection" is a named `run_evidence.py` false-completion class ("stale HEAD", "wrong cwd", "truncated output", "hash mismatch"). "Verifier memory inheritance refusal" is `agy_verifier.assert_distinct_sessions` (`:131`) raising `SessionIdentityCollisionError` plus `finalize_run` (`:219`) raising `SameSessionCannotFinalizeError`. Only "resume with modified options rejection" is arguably unproven; check `run_recovery`/`run_freeze` first, since `run_freeze.py` exists precisely to freeze what must not change mid-run. Writing these fresh would fork adversarial coverage rather than add it. Original expected outcome: All adversarial edge case tests assert correct fail-closed rejection and exact error codes.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Do not tick this box.

## Project conventions discovered (Step 0)

CORRECTED /plan-review 2026-08-30 pass 2 (PR-209). The first bullet is another self-refutation: it states
the ledger path as a discovered CONVENTION, which is true only because a ledger already ships there - and
then E-02 proposes to create that file.

- **SELF-REFUTING:** `.aw/records/runs/<run-id>/ledger.jsonl` is a convention because
  `run_ledger_store.LEDGER_FILENAME = "ledger.jsonl"` (`:49`) ALREADY writes it, with `GENESIS_HASH`
  (`:44`), `compute_record_hash` (`:206`), and `verify_chain` (`:529`). E-02 must CONSUME
  `RunLedgerStore` (`:297`), not create the file.
- **MISSED, and decisive:** `agent_workflows/agy_verifier.py` (fresh-session verifier contract) and
  `agent_workflows/verify_roles.py` (2158 lines: verifier packet, role least-privilege, nine verification
  procedures, corrective routing). Missing these two is the root cause of E-01, and pass 1's failure to
  inventory them is why the residue survived a whole review.
- **MISSED:** `agent_workflows/run_evidence.py` (1099 lines) already IS the deterministic completion
  authority, including the false-completion validator taxonomy. Root cause of E-04.
- **MISSED:** `agent_workflows/run_recovery.py` already ships resume + unknown-outcome fail-closed +
  retry budget. Root cause of E-06 and half of E-05.
- **NOT A CONVENTION:** the exit-code matrix (0/1/2/3/4/130) is spec-DERIVED, not discovered. Only 130
  demonstrably exists today (`oc_runipd.py:3200`). Label spec-derived values as such so a reader does not
  go looking for shipped code.
- **NOT A CONVENTION:** "resume requires identical host and cannot alter frozen queue options" is a spec
  requirement, not observed behavior; `run_freeze.py` is the module that would enforce it, and the plan
  never cites it.
- **MISSED:** the CLI verbs E-03 proposes already exist as `aw run show|evidence|verify-ledger`, and
  APPROVED `runnamecollapse-01` (`0soncw`) owns renaming them under `aw runs`.

## Findings

CORRECTED /plan-review 2026-08-30 pass 2 (PR-201/PR-202). The first finding is FALSE in both halves, and
it is the premise the whole plan rests on.

- **FALSE (half 1):** "does not record a cryptographic hash-chained event ledger". It does:
  `run_ledger_store.py` appends `prev_hash`-chained records under a single-writer lock (`:411-417`) from
  `GENESIS_HASH` (`:44`) and verifies the chain (`verify_chain:529`) with typed corruption errors. What
  the DRIVER writes is a separate, deliberately different `events.jsonl` - a distinction
  `run_ledger_store.py:373` calls out explicitly.
- **FALSE (half 2):** "does not ... launch a skeptical second turn for semantic cross-checks". It does,
  and it is load-bearing: `oc_runipd.py:2281` runs "Turn 2: independent skeptical verification in a fresh
  session" from the prompt at `:1663`, with `fresh_session=True` (`:1828`), and DOWNGRADES the disposition
  when the verifier finds unmet criteria (`:2259`). The `agy` twin exists.
- TRUE and important: "verification authority must be independent of agent self-reporting and host
  transport success". This is exactly what `verify_roles.py` (role least-privilege,
  `SelfVerificationForbiddenError`, coordinator-only terminal authority) and `run_evidence.py`
  (host exit 0 is not completion evidence) already implement. The principle is right; the plan simply did
  not look for its implementation.
- MISSING FROM THE SURVEY: the genuine gap, once the above are removed, is only the 13 `RUN-*` finding
  codes (ZERO hits each) and `--unverifiable-ok` (ZERO hits). That is a vocabulary-and-wiring gap over a
  shipped authority, and it is the only thing a successor should carry.

## Proposed changes (ordered, validatable)

SUPERSEDED /plan-review 2026-08-30 pass 2 (PR-201..PR-208). Steps 1, 2, 3, and 6 duplicate shipped
modules; step 4 would create a second completion authority; step 3 additionally collides with approved
`runnamecollapse-01`; step 7 forks existing coverage.

The replacement shape, and it is deliberately small:

1. **Map before writing.** For each of the 13 `RUN-*` codes, name the EXISTING `run_evidence.py`
   predicate (or shipped module) that already evaluates it, and mark only the genuine gaps. Publish that
   table in the successor plan before any code. This is the step whose absence produced this plan.
2. **Add the finding-code vocabulary** with spec 25kzda 4.2's exact messages and recovery commands, as a
   thin layer over `run_evidence.py`, extending that module rather than creating
   `deterministic_checker.py`. Terminal authority stays with the coordinator and `aw ipd finalize`.
3. **Add `--unverifiable-ok`** aggregate neutrality (ZERO hits today) without falsifying item-level state.
4. **Defer the three coupled codes**: `RUN-COMMIT-GATEWAY` and `RUN-COMMIT-CONTENTS` until the
   `AW-Run:`/`AW-Item:` trailers land (sibling `k7o7el`'s residue); `RUN-HOST-CAPABILITY` until the
   capability vocabulary lands under approved `wtiso-07` (`1o4eif`).
5. **Touch no runner** until `rununify` (`5e4sb6`) lands (OQ-02 below).
6. **Extend existing tests** (`tests/test_run_evidence_completion.py`, `tests/test_run_recovery_cli.py`)
   rather than creating `tests/test_deterministic_checker.py`.

Original sequence, retained for the record:

1. ~~Implement fresh verifier session launcher in `run_verifier.py` (E-01).~~ Shipped as `agy_verifier.py` + `verify_roles.py`, and live in both runners.
2. ~~Implement hash-chained ledger in `run_ledger.py` (E-02).~~ Shipped as `run_ledger_store.py`.
3. ~~Add `aw runs show/evidence/verify` CLI commands (E-03).~~ Shipped as `aw run show|evidence|verify-ledger`; renaming is approved `runnamecollapse-01`'s.
4. Implement all 13 checks in `deterministic_checker.py` (E-04) - the CODE VOCABULARY survives; the module and the sole-authority claim do not.
5. Implement exit code aggregation and `--unverifiable-ok` neutrality (E-05) - `--unverifiable-ok` survives; retry budget ships as `run_recovery.retry_budget_remaining`.
6. ~~Implement `--resume` mechanics and integrate with runner dispatch loop (E-06).~~ Shipped as `run_recovery.resume`; runner wiring fights `rununify`.
7. ~~Cover with comprehensive unit and adversarial tests in `test_deterministic_checker.py` (E-07, E-08).~~ Retarget to the residue; extend existing modules.

## Deferred / out of scope (with reason)

- **External third-party API transaction verification**: Requires custom remote receipt capturing, deferred per spec Section 6.1.
- **Hardware-enforced TEE attestation**: Beyond repository scope; cryptographic hashing is standard SHA-256.

## Scope check

CORRECTED /plan-review 2026-08-30 pass 2 (PR-201..PR-208).

- Over-scope: SEVERE, and concentrated in the worst possible place. THREE new modules where canonical
  homes exist: `run_verifier.py` forks `agy_verifier.py` + `verify_roles.py` (and a live runner turn);
  `run_ledger.py` forks `run_ledger_store.py` at the same on-disk path; `deterministic_checker.py` forks
  `run_evidence.py`, which is the repository's completion authority. E-04 further claims it "alone
  authorizes ... terminal transitions", contradicting `verify_roles`' coordinator-only terminal authority
  and `aw ipd finalize`. E-03 adds CLI verbs that already exist and whose rename approved
  `runnamecollapse-01` (`0soncw`) owns. E-06 edits both runners against approved `rununify` (`5e4sb6`).
  Of the 7 declared `Scope-Paths` entries, 4 are files that should not exist or should not be touched.
- Under-scope: no inventory of the ELEVEN shipped `run_*` modules (`run_engine`, `run_state`,
  `run_ledger_schema`, `run_ledger_store`, `run_evidence`, `run_freeze`, `run_gates`, `run_packet`,
  `run_recovery`, `run_cli`, `run_viewer`) nor of `verify_roles.py`/`agy_verifier.py`; no reconciliation
  with the two approved plans in its territory; no recognition that three of the 13 checks are BLOCKED on
  work owned elsewhere (trailers in `k7o7el`, capability vocabulary in `wtiso-07`); and no mapping of the
  13 codes onto the shipped predicates, which is the one analysis that would have prevented the plan.
- Original text, retained for the record: "Over-scope: none. Strictly implements verification, ledger
  integrity, run resumption, and completion authority. Under-scope: none. Covers all 13 checks in spec
  Section 4.2 and the complete exit code matrix."

## Required tests / validation

CORRECTED /plan-review 2026-08-30 pass 2 (PR-208). Both items were unachievable or already-true as written.

- ~~`python3 -m pytest tests/test_deterministic_checker.py`~~ - the module does not exist and should not be
  created; four of its six surfaces are already covered by `tests/test_run_evidence_completion.py`,
  `tests/test_run_recovery_cli.py`, and `tests/test_run_viewer.py`.
- ~~`aw runs verify <run-id>` demonstrating ledger integrity validation~~ - NOT a valid acceptance test for
  this plan: the shipped verb is `aw run verify-ledger` and it ALREADY does this, so the test would pass
  before any work began. It also presumes E-03's rename, which approved `runnamecollapse-01` owns.
- The honest bar for the replacement: the full suite at no-worsening against a FRESHLY MEASURED baseline
  with the `git rev-parse HEAD` it was measured at pasted. Do NOT claim `aw check plans` passes: measured
  at HEAD `09378e88` it exits with 232 findings, essentially all `check.lifecycle-transition-invalid` and
  `check.scope-drift` owned by other Sets. Plus a test asserting each NEW `RUN-*` code's exact message and
  recovery command, and a test proving `run_evidence.py`'s predicates are CALLED rather than
  reimplemented.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 1.1, 4.2, 5.1, 5.3, 5.5, and 5.6.
- Updates `.aw/records/runs/README.md` documenting the ledger structure and verification CLI.

## Open questions

### OQ-01: Does a skeptical verifier session have tool write access?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 1.1, and CONFIRMED IN SHIPPED CODE
- Resolution or deferral rationale: RESOLVED - No, and this is no longer merely a spec reading
  (confirmation added /plan-review 2026-08-30 pass 2). The answer is already ENFORCED:
  `verify_roles.py` reserves product mutation away from the verifier role
  (`ProductMutationForbiddenError`, `check_code_mutation_allowed:676`, `enforce_role_action:637`), and the
  correction path the question describes also ships as `route_verifier_findings` (`:1973`), which turns
  every verifier finding into either a bounded in-scope correction or an explicit pending corrective-IPD
  artifact, plus `invalidate_evidence_on_correction` (`:2097`) and
  `rerun_verification_after_correction` (`:2131`). So this question describes shipped behavior, not work
  to do.

### OQ-02: Must this plan's runner wiring be sequenced after `rununify`?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN (/plan-review pass 2). Inherited from parent Set `detrun`
  (`r4mbcw`) OQ-03 and recorded here because E-06 is this plan's own item. `rununify` (`5e4sb6`, approved)
  exists to collapse the duplication between `oc_runipd.py` and `agy_runipd.py`; E-06 adds new code to
  both. Recommendation: `rununify` first, then wire once. Note the residue that survives this review (the
  `RUN-*` code vocabulary and `--unverifiable-ok`) is mostly runner-INDEPENDENT and could land earlier;
  only the wiring is gated. This is a scope/priority call the repository cannot make, and it also decides
  how long this plan's `Blocks-Release: next` gate is delayed.

### OQ-03: Which of the 13 `RUN-*` checks are already evaluated by `run_evidence.py`?

- Blocking: yes
- Status: open
- Owner: successor plan author (an ANALYSIS obligation, not a maintainer decision)
- Resolution or deferral rationale: OPEN, and deliberately assigned to the successor rather than answered
  here (/plan-review pass 2, NEW). Partially discharged by this review: all 13 CODES grep to ZERO, so the
  code vocabulary is unbuilt; and `run_evidence.py`'s docstring enumerates a false-completion taxonomy
  (missing output, fabricated text, stale HEAD, wrong cwd, wrong worktree, mismatched command, expired
  host probe, truncated output, failed exit, absent artifact, hash mismatch, executor-authored verifier
  decision, redaction conflict) that visibly overlaps `RUN-HOST-ATTEMPT`, `RUN-CHECK-FRESHNESS`,
  `RUN-FROZEN-IDENTITY`, and `RUN-FRESH-VERIFIER`. What remains is a per-check mapping, which is
  authoring work, not review work: producing it inside a review would be writing the successor plan.
  BLOCKING because without it the successor cannot know which checks to build, and it is exactly the step
  whose omission produced E-04. Also note three checks are blocked on other owners regardless
  (`RUN-COMMIT-GATEWAY`/`RUN-COMMIT-CONTENTS` need `k7o7el`'s trailers; `RUN-HOST-CAPABILITY` needs
  `wtiso-07`'s capability vocabulary).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: Test showing verifier spawned in a separate session without executor history and returning structured finding objects.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: Python test writing sequential ledger events, validating hash chain integrity, and detecting tampered records.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: CLI session running `aw runs show` and `aw runs verify` against a completed run ledger.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: Test suite executing all 13 common deterministic checks against passing and failing synthetic repository states.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: Test verifying exact exit code return values across all 6 exit classes including `--unverifiable-ok` neutrality.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: End-to-end runner test executing a verified IPD lifecycle with ledger creation, deterministic checker sign-off, and clean `--resume` continuation.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: `pytest tests/test_deterministic_checker.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item duplicates shipped code (`agy_verifier.py`/`verify_roles.py`, `run_ledger_store.py`, `run_evidence.py`, `run_recovery.py`, `aw run show|evidence|verify-ledger`) or collides with approved `runnamecollapse-01`/`rununify`; collecting this evidence would mean proving a duplicate - or a second completion authority - was built.** Original required evidence: Adversarial pytest assertions verifying rejection of tampered ledgers and stale check command evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30, reaffirmed pass 2; the last surviving
residue is now GONE).** Do NOT execute and do NOT approve. All 8 E-items are `Execution state: blocked`
with an execution note, and all 8 V-items' evidence is NOT TO BE COLLECTED, so nothing here can be ticked.
An executor reaching this gate must STOP and report.

PASS-2 CORRECTION TO MY OWN EARLIER CALL: pass 1 kept E-01 (the fresh verifier harness) as "the
salvageable residue, after an inventory of `run_evidence.py`", judging it "not obviously shipped" partly
because `agy_verifier.py` "is only 301 lines". THAT INVENTORY IS NOW DONE AND IT REMOVES THE ITEM. Line
count was the wrong metric: the module is small because it consumes `verify_roles.py` (2158 lines). E-01
ships twice - as an enforced contract (`agy_verifier.run_fresh_verifier:142`,
`assert_distinct_sessions:131`, `finalize_run:219`; `verify_roles.build_verifier_packet:825` with
executor prose stripped, nine verification procedures, role least-privilege) and as a LIVE runner turn
(`oc_runipd.build_verifier_prompt:1663`, launched at `:2281` with `fresh_session=True`, downgrading the
disposition at `:2259`). Deferring an inventory is how a duplicate survives a review; do not defer it
again.

E-02/E-03/E-04/E-06 remain shipped as `run_ledger_store.py`, `aw run show|evidence|verify-ledger`,
`run_evidence.py`, and `run_recovery.py`. Building E-04 in particular would create a SECOND completion
authority in the one component whose entire value is being the single trustworthy one: two disagreeing
checkers mean neither can authorize completion. The plan also declares `Item-Dependencies: executed:k7o7el`,
inheriting every blocker of child 04, itself REPLAN.

Open questions: THREE, TWO blocking:
- OQ-02 (blocking, YOURS): sequence the runner wiring after `rununify` (`5e4sb6`)? Recommendation: yes.
  A scope/priority call the repository cannot make; it also sets how long `Blocks-Release: next` waits.
- OQ-03 (blocking, the SUCCESSOR AUTHOR'S, not yours): produce the per-check mapping of the 13 `RUN-*`
  codes onto existing `run_evidence.py` predicates BEFORE writing any. Partially discharged here (all 13
  codes grep to ZERO; the shipped false-completion taxonomy visibly covers several). Not answerable inside
  a review without authoring the successor.
- OQ-01: resolved, and now confirmed as SHIPPED behavior (`verify_roles` forbids verifier product
  mutation; `route_verifier_findings:1973` is the correction path it describes).

Retirement: retire with the parent Set `detrun` (`r4mbcw`). Prepend a `RETIRED 2026-08-30: <reason>;
superseded by <path/commit>` header and `git mv` to `.aw/records/plans/superseded/`. Do NOT file under
`executed/`; nothing was implemented.

Release gate: carries `- Blocks-Release: next`. Re-gate the residue below onto its successor, or have the
maintainer clear the gate explicitly.

SURVIVING RESIDUE, now a vocabulary-and-wiring layer rather than any module:

1. The 13 `RUN-*` finding codes of spec 25kzda 4.2 with their exact messages and recovery commands.
   Verified individually this pass: every one greps to ZERO. Build them as a thin layer over
   `run_evidence.py`, only after the OQ-03 mapping says which are genuinely missing.
2. `--unverifiable-ok` aggregate neutrality. ZERO hits; wholly unbuilt and small.
3. Bounds-checking the retry budget (0..10) on the SHIPPED `run_recovery.retry_budget_remaining` (`:340`),
   and completing the exit-code matrix (only 130 demonstrably exists, `oc_runipd.py:3200`).

Deferred by dependency, not by choice: `RUN-COMMIT-GATEWAY` and `RUN-COMMIT-CONTENTS` need the
`AW-Run:`/`AW-Item:` trailers (sibling `k7o7el`'s sole residue, unbuilt); `RUN-HOST-CAPABILITY` needs the
runner-safety capability vocabulary approved `wtiso-07` (`1o4eif`) claims.

Explicit prohibitions for the replacement: do NOT create `run_verifier.py` (forks `agy_verifier.py` +
`verify_roles.py` + a live runner turn); do NOT create `run_ledger.py` (forks `run_ledger_store.py` at the
same on-disk path, and `:373` already warns about confusing it with the drivers' `events.jsonl`); do NOT
create `deterministic_checker.py` (forks `run_evidence.py`, the completion authority); do NOT claim any
new checker "alone authorizes terminal transitions" (`verify_roles` reserves terminal authority to the
coordinator and `aw ipd finalize` owns the transition); do NOT rename the `aw run` verb group (approved
`runnamecollapse-01`, `0soncw`); do NOT edit `oc_runipd.py`/`agy_runipd.py` before `rununify` lands; and do
NOT create `tests/test_deterministic_checker.py` when `tests/test_run_evidence_completion.py`,
`tests/test_run_recovery_cli.py`, and `tests/test_run_viewer.py` already cover these surfaces.

Scope fence for the replacement: `agent_workflows/run_evidence.py` plus its test module, and nothing else
until OQ-02 and OQ-03 are answered. `cli.py`, `run_cli.py`, and both runners are actively contended in
this SHARED CHECKOUT and are claimed by approved `runnamecollapse-01` and `rununify`: verify
`git diff --cached --name-only` before every commit and unstage anything not yours. If it seems to need
more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do
NOT claim `aw check plans` passes - measured at HEAD `09378e88` it exits with 232 findings owned by other
Sets; the bar is no-worsening against a fresh baseline. Do not write a validation that already passes
before the work begins, as the original `aw runs verify <run-id>` item did.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never
`git add -A`, never push. Post-gate lifecycle is `aw ipd finalize`, never a hand-move. Do not create or
push a tag or release.
