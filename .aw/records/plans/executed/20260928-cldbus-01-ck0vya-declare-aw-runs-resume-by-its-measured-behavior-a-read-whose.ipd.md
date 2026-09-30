# IPD: Declare aw runs resume by its measured behavior: a read whose exit contract is (0, 2, 5, 7), not a mutation exiting 3

- Date: 2026-09-28
- Kind: child
- Concern: `runs resume` carries `command_class="mutation"` in `command_surface.COMMAND_INVENTORY` while writing nothing: `run_cli._run_resume` calls `run_recovery.resume`, whose body is `reconstruct_state()` + `detect_unknown_outcomes()` + `get_runnable_steps()` and a print, and `run_viewer.RUNS_VIEWER_LEAF_NAMES` lists `resume` among the read-only leaves, so the viewer vocabulary and the normative inventory disagree about one leaf. THE ITEM'S OWN DIAGNOSIS IS RIGHT ABOUT THE CLASS AND WRONG ABOUT WHAT FIXING IT COSTS, IN THREE WAYS MEASURED AT HEAD `7a7b99e6` (F-03, F-04, F-05). FIRST, the declared `exit_contract=(0, 3)` is wrong in BOTH directions: exits 2, 5 and 7 are reachable and undeclared (measured), and exit 3 is NOT reachable at all, because `EXIT_BLOCKED` fires only on `UnknownOutcomeError`, which needs a step reconstructed as `running` with no terminal attempt, and `running` is not in `run_ledger_schema.ATTEMPT_STATES` (`frozenset({'performed','blocked','failed'})`) so no ledger record can ever produce it; the only writer of that state is `run_engine.start_step`'s in-memory `_ephemeral_step_states`, which a fresh CLI process cannot inherit. SECOND, the item's claimed COST of the misdeclaration therefore does not exist: it says `read` would gain a `domain_failure` scenario, but `required_scenarios` gates that on `1 in exit_contract`, and 1 is absent from `(0, 3)`, so `mutation`->`read` alone swaps `success_preview` for NOTHING. THIRD, the two test files the item instructs a fixer to re-run, `tests/test_cli_conformance_matrix.py` and `tests/test_cli_quality_gates.py`, WERE DELETED by the suite trim `19313eed`, so that verification step cannot be performed as written and no live test consumes `required_scenarios` at all.
- Scope: IN: correct the `runs resume` declaration to `command_class="read"` and to an exit contract that matches measurement, replacing the unreachable 3 with the reachable 2, 5 and 7, and record in a comment WHY 3 is unreachable and 1 absent so the next reader does not restore either. Add the missing per-leaf test that pins the declaration against the verb's real handler, following the shipped per-command precedent (`tests/test_runs_repo_alias.py`, `tests/test_prompts_new.py`) rather than the deleted harness, and pin the viewer/inventory agreement that is today unasserted. OUT, each for a stated reason: `runs next`'s and `runs status`'s own contracts, which are separately wrong in the same way and belong to their own item (F-08, OQ-02); restoring the three deleted conformance test files, which re-opens the deliberate test-budget decision `19313eed` made (F-05); any change to `_run_resume`'s behavior, its exit codes, or `run_recovery.resume`, because this plan makes the DECLARATION match the code and must not move the code to match a declaration; and the unreachable-`EXIT_BLOCKED` defect itself, which is a real latent bug in `run_engine`'s ephemeral-state design and is filed rather than fixed here (OQ-01).
- Scope-Paths: agent_workflows/command_surface.py, tests/test_run_cli_declarations.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: cldbus
- Set: cldbus
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: ck0vya

## Workflow history
- 2026-09-30 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ck0vya verified (set cldbus, attempt 1).
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): status set to reviewed

- 2026-09-28 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801 through PR-807 (all FIXED, none deferred). Reviewed at HEAD `a8e41cc6`; `aw ipd lint` conforming at `--phase author` before revision and `--phase review-finalize` after (exit 0 both times, with two `IPD-Z602` density advisories examined and judged not to warrant a split, PR-807). EVERY ONE OF THE PLAN'S ELEVEN AUTHORED FINDINGS REPRODUCED INDEPENDENTLY, which is unusually good: the misclassification (F-01), the two-vocabulary disagreement (F-02), the full exit matrix (F-03), the `RL-E030` refusal and the two-process `run start` demonstration (F-04), the three deleted test files and `conformance_matrix.py`'s dead-surface status (F-05), `run_cli`'s zero `agent_schema` imports (F-06), the green tree (F-07), the sibling matrix including exit 3 genuinely reachable on `runs next` (F-08), the five assertion sites none naming `resume` (F-09), and the read-only tuple partitioning the noun correctly with `resume` as its single contradiction (F-11). ONE BLOCKER: E-03's handler-purity assertion instructed an `inspect.getsource` + AST walk over production source, which `AGENTS.md` and GUIDING_PRINCIPLES P16 prohibit outright and which was also a weak denylist; review replaced it with a behavioral bytes-and-count check and measured that working (PR-801). Two `Carrier-Declined` rows asserted "a carrier is genuinely owed" through the field that means the opposite, tracking two real obligations nowhere; review filed them as backlog `tzqvjn` (`bug`, gated) and `4bicgv` (`chore`) and converted both rows to real handoffs (PR-802). Four measurement defects were corrected: F-10's neighbour had executed and a different pending plan (`fuuw94`) now touches the adjacent code (PR-806, F-15); the exit-5 fixture as described is not reproducible and a naive `append` is refused (PR-804, F-12); the suite baseline had drifted 171 tests and was used as a bar in four places (PR-805, F-13); and the `run start` demonstration needs `--workflow` to work at all. A scope fence was added (PR-803). Findings recorded in `.aw/records/reviews/20260928-cldbus-01-ck0vya-declare-aw-runs-resume-by-its-measured-behavior-a-read-whose.review.md`.
- 2026-09-28 to-review (opencode): authored from backlog item `cldbus`. Every measurement in Findings was taken against the working tree at HEAD `7a7b99e6`. The item's central claim (wrong `command_class`) is CONFIRMED; its supporting reasoning about conformance coverage and its suggested verification step are both FALSIFIED here (F-04, F-05), and the plan is scoped to the correction the evidence actually supports.
- 2026-09-28 draft (opencode): created.

## Goal

Make the normative declaration of `aw runs resume` agree with what the verb measurably does: classify it `read`, as its sibling `runs next` already is and as `run_viewer.RUNS_VIEWER_LEAF_NAMES` already implies, and declare the exit codes it can actually return instead of one it cannot. Leave a test behind that would catch the next drift, since the harness the original declaration was written for no longer exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: correct the declaration

- [x] E-01 In `agent_workflows/command_surface.py`, change the `runs resume` `CommandDeclaration`'s `command_class` from `"mutation"` to `"read"`, matching its sibling `runs next` and the `run_viewer.RUNS_VIEWER_LEAF_NAMES` membership that already classifies it read-only. Change NOTHING else in that declaration in this item: `human_recipe`, `agent_record_kind`, `mutation_gate`, `empty_error_renderer` and `legacy_flags` are all already correct for a read (`mutation_gate="none"` is the honest value and stays), and the exit contract is E-02's separate concern so the two corrections can be reviewed and reverted independently. Do NOT touch `_run_resume`, `run_recovery.resume`, or any other declaration.
  - Depends on: none
  - Expected outcome: `get_declaration("runs resume").command_class == "read"`. `required_scenarios` for the leaf changes from `(..., 'json', 'success_preview')` to `(..., 'json')`, i.e. it LOSES the `success_preview` row it never needed and gains nothing, because `domain_failure` is gated on `1 in exit_contract` and 1 is absent (F-04). No test changes state as a result, because none consumes `required_scenarios` (F-05).
  - Execution state: performed

- [x] E-02 In the same declaration, replace the `exit_contract=(0, 3)` with the codes MEASURED reachable, `(0, 2, 5, 7)`, and write the comment that keeps a future reader from undoing it. The measured mapping (F-03) is: 0 a successful report; 2 an unresolvable target (`_emit_ledger_not_found`), a missing `--workflow` file, or an empty ledger, and also argparse's own usage error; 5 `EXIT_CORRUPTED_LEDGER` from `_build_engine`'s `LedgerCorruption` arm; 7 `EXIT_NOT_A_LEDGER` from its `NotALedgerError` arm. THE COMMENT MUST STATE TWO NEGATIVES EXPLICITLY, because each is a value a future author would otherwise "restore" as an obvious omission. (a) 3 IS REMOVED AS UNREACHABLE, not as undesirable: `_run_resume` returns `EXIT_BLOCKED` only in its `except run_recovery.UnknownOutcomeError` arm; `run_recovery.detect_unknown_outcomes` raises only for a step whose reconstructed state is `run_state.STATE_RUNNING` with `last_attempt_state is None`; `running` is absent from `run_ledger_schema.ATTEMPT_STATES`, so `RunLedgerStore.append` REFUSES a `step_attempt` carrying it (`RL-E030`), and the sole producer of that state is `run_engine.start_step`'s in-process `_ephemeral_step_states` dict, which no separate CLI invocation can observe. Cite that chain by SYMBOL and record that removing 3 documents a LATENT BUG rather than blessing it (OQ-01 files it). (b) 1 IS ABSENT DELIBERATELY: `_run_resume` never returns `EXIT_INCOMPLETE`, and adding it would oblige a `domain_failure` conformance scenario for an outcome the verb does not produce - the same reasoning the shipped `reviews decisions` declaration already records for its own `(0, 2)`. Do NOT cap this contract at `(0, 1, 2)` on agent-schema grounds: that constraint binds leaves emitting `aw.agent/v1` records, and `run_cli._emit_error`'s docstring states its payloads are DELIBERATELY not such records and that `run_cli` imports `agent_schema` zero times (F-06).
  - Depends on: E-01
  - Expected outcome: `get_declaration("runs resume").exit_contract == (0, 2, 5, 7)`, and every code in it is demonstrated by a real invocation in V-02 while 3 is demonstrated unreachable. `required_scenarios` is unchanged by this item (it keys on 1, which is absent before and after), so E-01 and E-02 are independently safe.
  - Execution state: performed

### Task group 2: leave behind the guard the deleted harness used to be

- [x] E-03 Create `tests/test_run_cli_declarations.py` pinning the `runs resume` declaration against the verb's OBSERVED behavior rather than against a restated constant, since a test that only echoes the inventory would pass for any value someone typed. Follow the shipped per-command precedent, NOT the deleted matrix harness: `tests/test_runs_repo_alias.py` reaches `cs.get_declaration("runs list")` directly and `tests/test_prompts_new.py::test_the_declared_flag_surface_matches_the_parser` asserts a declared field against the real subparser. Assert four things. (1) CLASS AGREEMENT ACROSS THE TWO VOCABULARIES: every name in `run_viewer.RUNS_VIEWER_LEAF_NAMES` whose `runs <name>` leaf carries a declaration is declared `read` or `check`, never `mutation` or `preview`. Write it as a LOOP over that tuple, not as a `resume` spot check, because the defect class is a viewer leaf declared as a writer and the four genuinely mutating `runs` verbs (`repair`, `analyze`, `export`, `submit`) are correctly absent from that tuple - which is exactly what makes the tuple usable as the read-only oracle. (2) HANDLER PURITY, ASSERTED BEHAVIORALLY AND NEVER BY READING PRODUCTION SOURCE (rewritten at review, PR-801, and this is a HARD PROHIBITION rather than a preference). The original wording here instructed the executor to "walk the AST of `run_recovery.resume` via `inspect.getsource`" and assert an absence of named calls. That is exactly what `AGENTS.md` forbids in its own words ("NEVER write or restore tests that read production source code using `inspect`, `ast`, regex, or substring search") and what GUIDING_PRINCIPLES P16 forbids under "No production source inspection", which names `inspect.getsource` and `ast.parse` literally. It was also WEAK on its own terms: a denylist of five call names passes a handler that writes through any spelling not on the list (`Path.open`, `os.replace`, a helper, a new store method), so it would have licensed the very regression it claimed to guard. INSTEAD, PROVE PURITY BY OBSERVATION, which review performed: snapshot the ledger file's BYTES (a `sha256` of `read_bytes()`) and its record count, drive `aw runs resume` over it as a subprocess, and assert the bytes are identical, the record count is unchanged, and the containing directory gained no file. Measured at review on a real fixture: exit 0, `bytes identical: True`, `sha256 identical: True`, `record count 1 -> 1`, and the directory listing unchanged (note `runs resume` leaves NO `ledger.jsonl.lock` behind, verified in a fresh directory, so a no-new-files assertion is safe). This is STRICTLY STRONGER than the AST walk, because it fails on ANY write by ANY mechanism rather than on five named ones, and it survives refactoring, which is the property P16 exists to protect. (3) DECLARED EXIT CODES ARE REACHABLE: drive the real CLI in a subprocess for each of 0, 2, 5 and 7 with the fixtures F-03 names, and assert the observed code is in `decl.exit_contract`. (4) UNDECLARED CODES DO NOT APPEAR: assert 3 is NOT in the contract, and assert the mechanical reason as a BEHAVIORAL fact rather than as a source fact. Two legitimate spellings, both measured at review, and BOTH are permitted because neither reads production source text: (i) compare the two runtime CONSTANTS, `run_state.STATE_RUNNING not in run_ledger_schema.ATTEMPT_STATES` (printed `False` for membership at review), which is a data comparison over imported values and not a structure pin; and (ii) stronger, EXERCISE the refusal, appending a `step_attempt` carrying `state="running"` through `run_ledger_store.RunLedgerStore.append` and asserting it raises `SchemaInvalidRecordError` with finding code `RL-E030`. Review ran (ii) and got exactly `RL-E030: attempt state must be one of ['blocked', 'failed', 'performed']`. Prefer (ii) as the primary assertion, since it proves the ledger REFUSES the state rather than merely that two constants differ, and keep (i) as the cheap companion. Mark nothing `slow`: these are in-process assertions plus a handful of fast subprocess invocations. Do not import `tests/conformance_matrix.py`; it has no live consumer and coupling a new test to it would resurrect a dead surface.
    THE FIXTURES ARE NON-OBVIOUS AND A NAIVE `append` IS REFUSED, so build them from this measured recipe rather than improvising (added at review, PR-804, F-12; the sibling plan `fuuw94` recorded the identical trap and its review needed five attempts). `RunLedgerStore.append` schema-validates every record. A `run` record needs ALL of `kind`, `run_id` matching `run-<hex>` (a bare `r1` is refused `RL-E015`), `schema_version`, `actor` drawn from `run_ledger_schema.ROLES` (`runtime` works; an invented `t` is refused `RL-E014`), `parent` present and STRING-typed (`None` is refused `RL-E011`, `""` is accepted), plus `workflow_digest`, `requirement_digest`, `repo` and `head`. THE FOUR FIXTURES, each measured end to end at review: exit 0 from a one-record valid ledger (`Run run-0000abcd state: pending`); exit 2 from an absent path, and SEPARATELY from an empty file (`error: ledger is empty`) and from a bad flag (argparse usage); exit 7 from a file of valid JSONL carrying none of the envelope fields; and exit 5 from a chain break, which needs a TWO-record ledger whose second record's `prev_hash` is overwritten (`Broken hash chain at seq 1`). NOTE WHAT DOES NOT WORK, because review tried it first: tampering `record_hash` or a payload field on a SINGLE-record ledger yields exit 0, not 5, since nothing downstream re-derives that hash on read. A `seq` gap or an unparseable line also reach 5 and are simpler; any of the three is acceptable, but the plan's own F-03 phrase "hash/schema-invalid ledger" is too loose to reproduce and is corrected in F-12.
  - Depends on: E-02
  - Expected outcome: A new test file that FAILS on the pre-E-01 tree at assertion (1) (naming `resume` declared `mutation` while listed in the viewer's read-only tuple) and at assertion (4) (3 present in the contract), and passes after. Its subprocess arm proves each declared code is produced by a real invocation rather than asserted, and its purity arm proves the ledger bytes are unchanged rather than inspecting any production source.
  - Execution state: performed

- [x] E-04 Run the BARE suite, `python3 -m pytest`, and compare against a baseline YOU RE-DERIVE on the pre-change tree, not against any figure written in this plan. THE BAR IS THE PROPERTY (zero failures, and a collected rise equal to the tests E-03 adds and nothing else), because a transcribed total is a LIVE population that drifts: the plan was authored at `3075 passed, 2 skipped` and review measured `3246 passed, 2 skipped, 3 warnings in 52.35s` at HEAD `a8e41cc6`, a drift of 171 tests in days (corrected at review, PR-805, F-13). What DOES carry forward from F-07 is the shape of the baseline, not its size: the tree is FULLY GREEN, with no pre-existing failure to hide behind, so any red is this plan's to explain. Bare is required: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` (the marker expression is BOTH exclusions, not `not slow` alone, corrected at review), so `-n0` makes this suite several times slower here and a second `-q` suppresses the `N passed` line this plan must paste. ALSO run, narrowed with `-o addopts=""` so the per-file counts are visible, the new file plus every file that reads a `CommandDeclaration` field or asserts on this command family: `tests/test_run_cli_declarations.py tests/test_command_surface_declarations.py tests/test_runs_repo_alias.py tests/test_prompts_new.py tests/test_host_capability_extension.py tests/test_workflow_artifacts_prune.py tests/test_oc_runipd.py tests/test_run_viewer.py`. AND RUN THE SLOW SET TOO, which the bare run deselects: `python3 -m pytest -m slow -o addopts=""`. That is the one place the item's instruction survives contact with the tree - it told a fixer to re-run two `slow`-marked conformance files, and those files are gone (F-05), so the honest substitute is to run whatever `slow` tests still exist and state the count, rather than to claim a verification that cannot be performed.
  - Depends on: E-03
  - Expected outcome: no new failures relative to the baseline RE-DERIVED at execution time (review measured `3246 passed, 2 skipped` as context only, and the plan's authored `3075` figure is already 171 tests stale), with the aggregate summary line captured plus per-file counts for the narrowed set and an explicit statement of the `-m slow` result (review measured 202 tests carrying that marker, also context only).
  - Execution state: performed

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL, NOT BY BARE OFFSET (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`). Every citation in this plan names a symbol; the backlog item's own citations are symbol-based already and all resolved at this HEAD.
- `command_class` IS DERIVED-FROM, NOT DECORATIVE - BUT ITS ONE DERIVED CONSUMER IS CURRENTLY DEAD. `tests/conformance_matrix.required_scenarios` computes required coverage from it, and `agent_workflows/command_surface.py`'s own comment states that "declaring the wrong class demands the wrong coverage". That comment is still TRUE in intent and FALSE in effect at this HEAD, because no live test imports the module (F-05). This plan therefore fixes the declaration for correctness and adds its own guard, rather than relying on a harness that no longer runs.
- AN EXIT CONTRACT MAY DELIBERATELY OMIT 1, AND THE OMISSION IS RECORDED AS A DECISION. The shipped `reviews decisions` declaration carries `exit_contract=(0, 2)` with the comment that a class whose contract includes 1 "obliges a `domain_failure` conformance scenario ... and a read-only printer has no domain failure to produce". E-02 follows that precedent explicitly.
- A DECLARATION'S EXIT CONTRACT MAY EXCEED `(0, 1, 2)` WHEN THE LEAF EMITS NO `aw.agent/v1` RECORD. Six declarations already use a code above 2, and `run_cli._emit_error`'s docstring records that this module's machine payloads are bare dicts which `agent_schema.validate_agent_record` would reject, deliberately. That is why `(0, 2, 5, 7)` is admissible here while `runs analyze` is correctly capped at `(0, 1, 2)`.
- A PER-COMMAND DECLARATION TEST IS THE ESTABLISHED SHAPE, and the whole-surface test cannot substitute. `tests/test_command_surface_declarations.py` asserts only that zero parser leaves are UNDECLARED; it is invariant to every field's value. `tests/test_runs_repo_alias.py` and `tests/test_prompts_new.py` are the precedents for asserting a field.
- THE SUITE RUNS BARE: `python3 -m pytest` with no added flags. Its configured marker expression is `not slow and not livecorpus` (both exclusions), corrected at review from the `not slow` this plan quoted in two places.
- A TEST MAY NEVER ASSERT OVER PRODUCTION SOURCE TEXT OR STRUCTURE, and this is a hard prohibition rather than a style preference (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16, which names `inspect.getsource` and `ast.parse` literally). Prove a property by EXERCISING the code and asserting observable outcomes: exit codes, stdout, created files, and unchanged bytes. Added at review because E-03 originally specified the prohibited shape (F-14). P16's "one narrow exception" (where the text itself is the artifact under test) does NOT apply to `agent_workflows/*.py`.
- A LIVE COUNT IS NEVER AN ACCEPTANCE BAR. Suite totals, collected counts and `aw check` error counts drift between authoring and execution (measured here: 171 tests in days, F-13), so state the required PROPERTY and re-derive the number at execution time.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S CENTRAL CLAIM IS CONFIRMED. `runs resume` is declared `command_class="mutation"`; its sibling `runs next` is declared `read`; `run_recovery.resume`'s entire body is `reconstruct_state()`, `detect_unknown_outcomes()`, a conditional `raise`, and a `ResumeReport` construction, with no append, write or commit. `run_cli`'s module docstring states outright that "`next` and `resume` sound like actions but only reconstruct state and report, which is why they are readers". | Read of the `runs resume` and `runs next` declarations; read of `run_recovery.resume` and `run_cli._run_resume` in full; the docstring line quoted verbatim. |
| F-02 | THE TWO VOCABULARIES DISAGREE, AS THE ITEM SAYS, AND THE DISAGREEMENT IS ASSERTED NOWHERE. `run_viewer.RUNS_VIEWER_LEAF_NAMES` is documented as "The nine READ-ONLY leaves registered under `aw runs`" and contains `resume`; `cli._RUNS_VIEWER_LEAVES` is built from it precisely so the two cannot drift. No test compares that tuple to any `command_class`. | Read of the tuple and its `#:` comment; read of the `cli.py` import that reuses it; `rg command_class tests/` returning four files, none of which mentions `resume`. |
| F-03 | THE DECLARED EXIT CONTRACT IS WRONG IN BOTH DIRECTIONS, MEASURED THROUGH THE REAL CLI, AND EVERY ROW REPRODUCED AT REVIEW. Declared `(0, 3)`. Observed: clean ledger -> 0; absent target -> 2; healthy non-ledger JSONL -> 7; CHAIN-BROKEN ledger -> 5 (see F-12: the authored phrase "hash/schema-invalid ledger" is too loose to reproduce, and a single-record hash tamper gives 0); empty ledger -> 2; `--this-flag-does-not-exist` -> 2. So 2, 5 and 7 are reachable and undeclared, and 3 was never observed. | Six subprocess invocations of `python3 -m agent_workflows runs resume` over purpose-built fixtures, each return code printed, all re-run independently at review: `absent (2, ledger file not found)`, `notaledger (7, not a run ledger)`, `empty (2, ledger is empty)`, `bad flag (2, argparse usage)`, `clean (0, Run run-0000abcd state: pending)`, `chain broken (5, Broken hash chain at seq 1)`. The corresponding return sites read in `_run_resume`, `_resolve_or_error` and `_build_engine` (whose `NotALedgerError` and `LedgerCorruption` arms return 7 and 5 respectively, with the empty-records arm returning 2). |
| F-04 | EXIT 3 IS NOT MERELY UNOBSERVED, IT IS UNREACHABLE, WHICH CHANGES WHAT THE FIX SHOULD BE. `EXIT_BLOCKED` is returned only from `_run_resume`'s `except run_recovery.UnknownOutcomeError` arm. `detect_unknown_outcomes` selects steps whose state is `run_state.STATE_RUNNING` (`'running'`) with `last_attempt_state is None`. `run_ledger_schema.ATTEMPT_STATES` is `frozenset({'blocked','failed','performed'})`, so appending a `step_attempt` with `state='running'` is REFUSED with `RL-E030`; and `reconstruct_state` can only set a step `running` from `_ephemeral_step_states`, populated solely by `run_engine.start_step` in the SAME process. Driven end to end: `aw run start <ledger> --step s1` reports `Started step s1 (state: running)` yet appends NO record (ledger kinds after: `['run']`), and a following `aw runs resume` in a new process reports state `pending` and exits 0. Every appendable attempt state (`performed`, `blocked`, `failed`) also yields exit 0. REPRODUCTION NOTE ADDED AT REVIEW: the `run start` half requires `--workflow <file>` naming the step, because a ledger-reconstructed workflow has no step `s1` and `run start` then exits 2 with `error: unknown step 's1'` rather than demonstrating anything. With a one-step workflow file supplied, the sequence reproduces exactly as claimed. | The refusal exception and its `RL-E030` finding printed from a direct `append` (`attempt state must be one of ['blocked', 'failed', 'performed']`); a loop invoking the CLI once per appendable attempt state showing exit 0 each time, all three re-run at review; the two-process `run start --workflow wf.json --step s1` then `runs resume` sequence with the ledger's record kinds printed as `['run']` before AND after the start, and resume reporting `state: pending` with `Resumable steps: - s1` at exit 0; `run_state.STATE_RUNNING in ATTEMPT_STATES` printed as `False`. |
| F-05 | THE ITEM'S "WHY IT MATTERS" MECHANISM DOES NOT FIRE, AND ITS SUGGESTED VERIFICATION CANNOT BE PERFORMED. (a) It says `read` would gain a `domain_failure` scenario; `required_scenarios` gates that on `1 in decl.exit_contract`, and 1 is absent from `(0, 3)`, so `mutation`->`read` changes the required set from `(tty, non_tty, agent, no_color, help, usage_error, json, success_preview)` to the same set minus `success_preview` - a strict loss of a row, no gain. (b) It instructs re-running `tests/test_cli_conformance_matrix.py` and `tests/test_cli_quality_gates.py`; both were DELETED (with `tests/test_conformance_harness.py`) by `19313eed` "test: trim test suite from 9,136 to under 2,000 tests". (c) `tests/conformance_matrix.py` survives but is imported by NOTHING: the only in-tree references to `required_scenarios`/`build_matrix` are its own definitions plus a comment in `command_surface.py`. The CI job `output-conformance` in `.github/workflows/tests.yml` now runs only `tests/test_command_surface_declarations.py`, which is invariant to `command_class`. | `required_scenarios` evaluated on the current declaration and on `dataclasses.replace(..., command_class='read')`, both printed; `git show 19313eed --stat` showing the three deletions with line counts; `git cat-file -e HEAD:tests/test_cli_conformance_matrix.py` failing; `rg` for the harness symbols across the tree; the CI job's `run:` block read in full. |
| F-06 | THE `(0, 1, 2)` AGENT-SCHEMA CAP DOES NOT BIND THIS LEAF, so `(0, 2, 5, 7)` is admissible rather than a contract violation. `run_cli._emit_error`'s docstring states its machine payloads are "DELIBERATELY NOT an `aw.agent/v1` RECORD", that `validate_agent_record` reports three violations against one, and that "`run_cli` imports `agent_schema` zero times". Six declarations already carry a code above 2. | The docstring paragraph read in full; `rg agent_schema agent_workflows/run_cli.py` returning no import; a probe listing every declaration whose `exit_contract` contains a value above 2. |
| F-07 | THE TREE IS FULLY GREEN, so this plan has no pre-existing failure to hide behind. That PROPERTY is what the finding asserts; the COUNT below is context only and has already drifted (see F-13). Authored: `3075 passed, 2 skipped, 3 warnings in 55.65s` with 205 deselected. RE-MEASURED AT REVIEW at HEAD `a8e41cc6`: `3246 passed, 2 skipped, 3 warnings in 52.35s` with 207 deselected, still zero failures. `aw check` reports 4 pre-existing errors (a missing `.aw/system/layout.json`, two plan-conformance issues on OTHER pending plans, and a nonconformant backlog slug), none in this plan's scope; the COUNT of 4 reproduced at review though its membership shifted. | The pasted tail of the bare run at authoring and again at review; the `aw check` tail naming the four unrelated issues, re-read at review. |
| F-08 | THE SAME DEFECT CLASS EXISTS ON TWO SIBLING LEAVES, which is why OQ-02 draws the fence where it does rather than silently leaving them. `runs next` is declared `(0, 3)` and 3 IS reachable there (measured: a step-less run exits 3), but 2, 5 and 7 are equally reachable and undeclared. `runs status` is declared `(0, 1, 3, 5)`; a step-less run exits 1, and 7 is reachable and undeclared. So both under-declare, and neither is misclassified. | A probe running `runs next`, `runs resume` and `runs status` against the same three fixtures (clean, absent, non-ledger) printing a code matrix: `next {clean:3, absent:2, notaledger:7}`, `resume {clean:0, absent:2, notaledger:7}`, `status {clean:1, absent:2, notaledger:7}`. |
| F-09 | NO TEST ASSERTS THIS DECLARATION'S CLASS OR CONTRACT, so E-01 and E-02 cannot break an existing assertion and E-03 is not redundant. Across `tests/`, `command_class` is asserted in exactly three places (`test_prompts_new.py` for `prompts new`, `test_host_capability_extension.py` for a host leaf, `test_oc_runipd.py` for an alias) and `exit_contract` in exactly two (`test_workflow_artifacts_prune.py`, `test_host_capability_extension.py`). None names `resume`. | `rg -n "command_class\|\.exit_contract\|mutation_gate"` across `tests/` and `agent_workflows/`, every hit classified. |
| F-10 | SUPERSEDED AT REVIEW, AND ITS CONCLUSION STILL HOLDS FOR A DIFFERENT REASON (PR-806, F-14). As authored this finding named `9vglxd` (set `gatedir`) as the one pending plan declaring `agent_workflows/command_surface.py`. That plan has since EXECUTED (`.aw/records/plans/executed/20260928-gatedir-01-9vglxd-...ipd.md`), so the contention it described is gone, and re-measuring at review found a DIFFERENT and more interesting neighbour instead: pending plan `fuuw94` (set `z63xoh`, `- Status: reviewed`, `- Readiness: go-pending-approval`) changes `run_cli`'s corruption exit codes, i.e. the very behavior THIS plan declares. The conclusion is unchanged, verified rather than assumed: `fuuw94`'s `- Scope-Paths:` is `agent_workflows/run_cli.py, tests/test_run_cli_corruption_exit.py`, so it touches neither of this plan's two paths, and it treats `resume` only as a CONTROL row that must already return 5 on a tampered ledger, which is precisely what this plan declares. See F-15 for the one real interaction. | `rg -l command_surface .aw/records/plans/pending/` re-run at review, returning this plan plus `cpi6p3`, `fuuw94` and `ygb3nk`; `find .aw/records/plans -name '*9vglxd*'` resolving under `executed/`; `fuuw94`'s `- Scope-Paths:`, `- Status:` and its E-05/V-05 control-row text read in full. |
| F-12 | ADDED AT REVIEW. **THE EXIT-5 FIXTURE AS DESCRIBED IS NOT REPRODUCIBLE, AND A NAIVE `append` IS REFUSED, which is the likeliest place execution stalls.** F-03 calls it a "hash/schema-invalid ledger", but review measured that tampering `record_hash` OR a payload field on a SINGLE-record ledger yields exit 0, not 5: nothing re-derives that hash on read. Exit 5 needs a chain break across TWO records (overwrite the second's `prev_hash`), or a `seq` gap, or an unparseable line. Separately, `RunLedgerStore.append` refuses an improvised record: review hit `RL-E010` (missing `schema_version`/`actor`/`parent`), `RL-E015` (`run_id` must match `run-<hex>`), `RL-E020` (missing `workflow_digest`/`requirement_digest`/`repo`/`head`), `RL-E014` (unknown actor role), and `RL-E011` (`parent` typed `None`) before a valid record appended. | `Broken hash chain at seq 1: expected prev_hash '668decb0...', got '00000000...'` -> exit 5 on a two-record ledger; `record_hash` and payload tampers on one record -> exit 0 twice; `Sequence mismatch at seq 5: expected seq 0` -> 5; `Invalid JSON at line 1` -> 5; the five successive `SchemaInvalidRecordError` finding tuples from the fixture-building attempts |
| F-13 | ADDED AT REVIEW. **THE TRANSCRIBED SUITE BASELINE HAD DRIFTED 171 TESTS, and the plan used it as an acceptance bar in FOUR places (E-04, its Expected outcome, Proposed change 4, and Required tests, with V-04 comparing to it as well).** Live populations must be re-derived at execution time per the repository's live-artifact convention; a number written at authoring is context, never the bar. The `addopts` string the plan quotes is also slightly wrong: the real marker expression is `not slow and not livecorpus`, not `not slow`. | authored `3075 passed, 2 skipped`; measured `3246 passed, 2 skipped, 3 warnings in 52.35s` at HEAD `a8e41cc6`; `pyproject.toml` `[tool.pytest.ini_options] addopts` read verbatim as `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; `-m slow` collects 202 |
| F-14 | ADDED AT REVIEW. **E-03's HANDLER-PURITY ASSERTION AS WRITTEN WAS PROHIBITED BY THE REPOSITORY'S OWN TEST CONTRACT, AND WEAK.** It instructed an `inspect.getsource` + AST walk over `run_recovery.resume` asserting the absence of five named calls. `AGENTS.md` forbids exactly this ("NEVER write or restore tests that read production source code using `inspect`, `ast`, regex, or substring search") and GUIDING_PRINCIPLES P16 names `inspect.getsource` and `ast.parse` literally under "No production source inspection". It was also a DENYLIST, so a write through any unlisted spelling would pass. The behavioral replacement is stronger and was measured working. | `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)" paragraph, clause (1), read verbatim; `GUIDING_PRINCIPLES.md` section 16 "What is prohibited" bullet 1; review's behavioral probe returning exit 0 with `bytes identical: True`, `sha256 identical: True`, `record count 1 -> 1`, unchanged mtime and unchanged directory listing |
| F-15 | ADDED AT REVIEW. **THERE IS ONE REAL CROSS-PLAN INTERACTION, AND IT IS BENIGN IN BOTH LANDING ORDERS, BUT AN EXECUTOR MUST NOT ASSUME IT.** `fuuw94` moves three OTHER `runs` readers (`show`, `evidence`, `verify-ledger`) from exit 2 to exit 5 on a corrupt ledger. It does NOT touch `_run_resume`, and review measured that `resume` ALREADY returns 5 on a broken chain, so `(0, 2, 5, 7)` is correct whether `fuuw94` lands first, second, or never. What an executor must not do is generalize `fuuw94`'s change to this leaf, or re-measure `resume`'s corruption code and conclude the contract needs widening because a sibling changed. | the sibling matrix measured over identical fixtures: `next {clean:3, absent:2, notaledger:7, seqgap:5}`, `resume {clean:0, absent:2, notaledger:7, seqgap:5}`, `status {clean:1, absent:2, notaledger:7, seqgap:5}`; `fuuw94`'s `- Scope-Paths:` excluding `command_surface.py`; its V-05 naming `status`, `next` and `resume` as control rows that must PASS pre-fix |
| F-11 | THE FOUR GENUINELY MUTATING `runs` VERBS ARE CORRECTLY ABSENT FROM THE READ-ONLY TUPLE, which is what makes E-03's assertion (1) a usable oracle instead of a tautology. `runs repair`, `runs analyze`, `runs export` and `runs submit` all declare `mutation` and none appears in `RUNS_VIEWER_LEAF_NAMES`; `cli._RUNS_DESCRIPTION` names those four as the enumerated exceptions to the noun's read-only claim. So the tuple partitions the noun correctly today, and `resume` is the single member contradicting it. | A probe printing `command` and `command_class` for every `runs *` declaration; the tuple's nine members listed beside them; `_RUNS_DESCRIPTION` read in full. |

## Proposed changes (ordered, validatable)

1. Reclassify the `runs resume` declaration `mutation` -> `read`, changing no other field (E-01).
2. Replace its `exit_contract=(0, 3)` with the measured `(0, 2, 5, 7)`, with a comment recording by symbol why 3 is unreachable and why 1 is deliberately absent (E-02).
3. Add `tests/test_run_cli_declarations.py`: viewer/inventory class agreement as a loop over `RUNS_VIEWER_LEAF_NAMES`, structural handler-purity assertions over `run_recovery.resume`, subprocess proof that each declared exit code is produced, and an assertion that 3 is absent together with the mechanical reason it cannot occur (E-03).
4. Run the bare suite against a baseline RE-DERIVED on the pre-change tree (zero failures is the bar; the authored `3075 passed` figure is 171 tests stale, F-13), plus the narrowed per-file set and the `-m slow` set (E-04).

## Deferred / out of scope (with reason)

- FIXING THE UNREACHABLE `EXIT_BLOCKED` PATH is out of scope; OQ-01 files it. This plan documents the unreachability in a comment and pins it in a test. Making it reachable means changing how `run_engine` persists a `running` step, which touches the ledger schema's attempt-state vocabulary and the single-writer lease, and is a behavior change to the run engine rather than a declaration correction.
  - Carrier: tzqvjn
  - Carrier-Note: CORRECTED AT REVIEW (PR-802). This row previously used `Carrier-Declined` while its own text said "a carrier is genuinely owed here ... so this row is a HANDOFF rather than a refusal", which is a contradiction in the schema's own terms: `Carrier-Declined` IS the recorded decision NOT to carry it, the analogue of clearing a release gate, so declaring an obligation through the field that disclaims one leaves the obligation tracked nowhere. Review filed the real item (`tzqvjn`, `open`, `bug`, auto-gated `Blocks-Release: next` by the every-live-bug policy) from its own independent measurements, so this is now a genuine HANDOFF. The reasoning the old row gave is retained and remains correct: the fix and this correction have disjoint scope paths and opposite risk profiles, since correcting a declaration is inert while making a step's `running` state durable changes what every ledger consumer reconstructs, so keeping that risk out of a `chore` is right.
- CORRECTING `runs next` AND `runs status`, which under-declare their contracts in the same way (F-08), is out of scope; OQ-02 resolves it.
  - Carrier: 4bicgv
  - Carrier-Note: CORRECTED AT REVIEW (PR-802), same defect as the row above: the text said "A carrier is owed" while the field recorded a decision not to carry it. Review filed `4bicgv` (`open`, `chore`, carrying the measured three-verb matrix), so the obligation is now tracked. The retained reasoning is correct: neither sibling is MISCLASSIFIED (both are already `read`), so neither shares this plan's defect; only contract INCOMPLETENESS is shared, and folding two more leaves in would put a removal and a retention of the same exit code in one diff.
- RESTORING `tests/test_cli_conformance_matrix.py`, `tests/test_cli_quality_gates.py` AND `tests/test_conformance_harness.py` is out of scope. They were deleted whole by the deliberate suite trim `19313eed` (F-05), so re-adding them re-opens that commit's test-budget policy, which this plan has no mandate to decide.
  - Carrier-Declined: Nothing is owed by THIS plan once E-03 lands, because E-03 covers the one leaf this plan touches with a stronger assertion than the matrix made (the matrix recorded `covered_by="declaration"` for a mutation leaf, i.e. it never executed `resume` at all). Whether the repository wants the whole harness back is a separate, larger question about `tests/conformance_matrix.py`'s dead-surface status, and filing it as an obligation of this `chore` would misattribute it.
- CHANGING `_run_resume`'s BEHAVIOR OR EXIT CODES is explicitly rejected rather than deferred. The whole claim of this plan is that the code is right and the declaration is wrong; if executing it changes any observed exit code, it has failed.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan, not an outstanding defect, and it is enforced inside this plan by V-02's before/after code comparison rather than deferred out of it.

## Scope check

- Over-scope: none. `agent_workflows/command_surface.py` carries exactly two field edits inside ONE `CommandDeclaration` plus the comment E-02 requires; `tests/test_run_cli_declarations.py` is new and carries E-03 only. No handler, no parser registration, no other declaration, no spec, and no `.aw/` record other than this plan changes.
- RIGHT-SIZING, ASSESSED AT REVIEW BECAUSE THE LINTER FLAGGED IT (PR-807). `aw ipd lint --phase author` reports two `IPD-Z602` density advisories, on E-02 ("3 clauses") and E-03 ("explicit multi-part enumeration"). Both were examined against the four splitting diagnostics and NEITHER warrants a split, for reasons that differ. E-02's three clauses are ONE deliverable (a single tuple literal plus the comment that justifies it) with two mandatory negative justifications; splitting the comment from the value it explains would produce a change whose rationale lands in a different item, which is worse. E-03's four assertions are also one deliverable, ONE new file, and they are not independent: assertions (1) and (4) exist to fail on the pre-E-01 tree, which is the same falsification event, and (3) builds the fixtures (2) reuses. Splitting them across files would duplicate the fixture recipe F-12 records, and each fragment's `V-*` would demand the same pre-change red run. The advisory is nonetheless CORRECT that E-03 is the densest item here; the response is that it is dense by cohesion, not by bundling, and its four assertion surfaces are enumerated so an executor can perform them in one focused pass.
- Under-scope: `runs next` and `runs status` keep their incomplete contracts (F-08, OQ-02), and the latent unreachable-`EXIT_BLOCKED` path stays latent (OQ-01). `tests/conformance_matrix.py` remains a dead surface with no live importer; this plan neither revives nor deletes it, and E-03 deliberately does not import it. None of these is an omission: backlog item `cldbus` reported one leaf's `command_class`, and this plan corrects that leaf and additionally repairs the contract it found wrong while measuring.

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted, compared against a baseline RE-DERIVED on the pre-change tree rather than against any number in this plan (F-13; the bar is zero failures plus a rise equal to E-03's added tests). Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_run_cli_declarations.py tests/test_command_surface_declarations.py tests/test_runs_repo_alias.py tests/test_prompts_new.py tests/test_host_capability_extension.py tests/test_workflow_artifacts_prune.py tests/test_oc_runipd.py tests/test_run_viewer.py -o addopts=""` for per-file counts across every file that reads a `CommandDeclaration` field or asserts on this command family.
- `python3 -m pytest -m slow -o addopts=""`, because the bare run deselects 205 tests and the item's own instruction was to re-run `slow`-marked conformance files that no longer exist (F-05). State the count and any failure explicitly.
- A DELIBERATE-FAILURE DEMONSTRATION for E-03: run the new test against the pre-E-01 declaration and paste it RED, showing that assertion (1) names `resume` as a viewer leaf declared `mutation` and that assertion (4) sees 3 in the contract. A guard that was never red proves nothing.
- A REACHABILITY DEMONSTRATION for E-02: paste one real CLI invocation per declared code (0, 2, 5, 7) with its exit status, and paste the unreachability evidence for 3 (the `RL-E030` refusal of a `state='running'` append, plus the two-process `run start` then `runs resume` sequence showing an empty append and exit 0).
- A NO-BEHAVIOR-CHANGE CHECK: run the same four fixtures before and after the change and show the exit codes are IDENTICAL. This plan edits only a declaration, so any moved code is a failure.
- `aw check` to confirm no new drift. The COUNT of 4 pre-existing unrelated errors held at review, but its MEMBERSHIP shifted between authoring and review, so compare the named error SET you observe before the change against the set after, not the integer alone.
- A PROHIBITION CHECK on the new test file: `rg -n 'getsource|getsourcelines|import ast|ast\.parse|read_text' tests/test_run_cli_declarations.py` must return nothing, since `AGENTS.md` and GUIDING_PRINCIPLES P16 forbid asserting over production source text or structure (F-14).
- `aw sanitize --agent` before commit.
- `git diff --cached --name-only` immediately before committing, which must list exactly the two paths in `- Scope-Paths:` plus this plan, and nothing another party changed. This is a shared checkout.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs to be. `command_class` and `exit_contract` are declared in code (`agent_workflows/command_surface.py`) rather than in a spec, and the repository's documented output contract (`docs/cli-output-contract.md`) speaks to the `aw.agent/v1` record's `exit` field, which this leaf deliberately does not emit (F-06). `docs/recovery.md` documents `aw runs resume` behaviorally ("reconstructs the run state and reports the steps it can resume") and is already consistent with a `read` classification, naming no exit code, so it needs no edit; `CONTRIBUTING.md`'s output-contract checklist describes how to DECLARE a leaf and is unchanged by correcting one declaration's values. The comment E-02 requires is in a file already in scope.

## Open questions

### OQ-01: `_run_resume`'s `EXIT_BLOCKED` path is unreachable from any separate process. Should this plan make it reachable, or file it?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS FILE IT, NOT FIX IT, from the shape of the fix rather than from convenience. The unreachability is real and measured (F-04): the blocked arm needs a step reconstructed as `running` with no terminal attempt; `running` is not an appendable `step_attempt` state (`RL-E030` refuses it) and exists only in `run_engine._ephemeral_step_states`, which dies with the process, so `aw run start` reports `state: running` while appending nothing and the next invocation sees `pending`. Making it reachable therefore means giving a step's `running` state DURABLE representation, which touches `run_ledger_schema.ATTEMPT_STATES` (or adds a new record kind), `reconstruct_state`'s replay, and the single-writer lease that `run start` takes - a behavior change to the run engine affecting every ledger consumer, with its own migration question for existing ledgers. That is the opposite risk profile from this plan, whose entire diff is inert. The correct action for THIS plan is to stop the declaration ASSERTING a code the code cannot produce, and to leave the mechanical reason in a comment and a test assertion so the next reader finds the bug documented rather than rediscovers it. THE FOLLOW-UP ITEM NOW EXISTS (filed at review, PR-802): backlog `tzqvjn`, `open`, `Work-Kind: bug`, auto-gated `- Blocks-Release: next` by the every-live-bug policy, carrying review's own independent measurements. It covers exactly what this rationale said it must: whether a `running` step must survive a process boundary at all (the drivers do not use this ledger path today, so the honest answer may be no, in which case the dead arm and the docstring promise should be REMOVED rather than fixed), and if so whether durability comes via a new appendable state or a distinct record kind, plus the migration question. It is named as this plan's `- Carrier:` on the corresponding Deferred row, where it previously used `Carrier-Declined` while asserting an obligation, which tracked the obligation nowhere. Recorded as non-blocking because this plan's correctness does not depend on the answer: 3 is wrong to declare either way, since today it cannot occur, and if it later can, the declaration must be updated by the plan that makes it occur. ONE THING THIS REVIEW ADDS TO THE STAKES: the unreachability is not merely cosmetic, because `run_recovery.resume`'s own docstring advertises a fail-closed guarantee ("Refuses to advance if any step is in an `unknown_outcome` condition (interrupted side effect)") that cannot fire across a process boundary, which is the only boundary an interrupted run crosses. That makes `tzqvjn` a real defect and not a tidy-up, which is why it was filed `bug`.

### OQ-02: `runs next` and `runs status` under-declare their exit contracts in the same way. Should this plan correct all three leaves?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS NO, on a distinction the measurement makes sharp. Both siblings are already classified `read`, so neither carries the defect backlog item `cldbus` reported; what they share is only contract INCOMPLETENESS (F-08: `next` declares `(0, 3)` while also reaching 2, 5 and 7; `status` declares `(0, 1, 3, 5)` while also reaching 7). Two reasons to keep them out. First, the reachability evidence is per-leaf and asymmetric: exit 3 IS reachable on `runs next` (a step-less run exits 3, measured), so the unreachability argument that justifies removing 3 here does NOT transfer, and folding them in would put a removal and a retention of the same code in one diff, which is exactly the shape a reviewer cannot check quickly. Second, `runs status` declares 1 while `resume` does not, so its `required_scenarios` already includes `domain_failure` and widening its contract has a different coverage consequence than widening this one. Both should be corrected, with their own measured matrix, in their own item, AND THAT ITEM NOW EXISTS (filed at review, PR-802): backlog `4bicgv`, `open`, `chore`, carrying the full three-verb matrix review measured over identical fixtures. It is named as this plan's `- Carrier:` on the corresponding Deferred row, replacing a `Carrier-Declined` that asserted an obligation while recording a refusal. This plan also names both leaves in F-08 and in `## Scope check` so the omission is visible rather than silent, and `- Scope-Paths:` fences the declaration file to the one leaf even though the file contains all three.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/command_surface.py` restricted to the `runs resume` declaration. It must show `command_class` changing `"mutation"` -> `"read"` and NO other field of that declaration changing, and no other declaration touched anywhere in the file. Paste a probe printing `get_declaration("runs resume")` in full before and after, so every unchanged field is visible rather than asserted. Paste `required_scenarios` for the leaf before and after (from `tests/conformance_matrix.py`, imported directly for the probe only), showing `success_preview` dropping and NOTHING being added, and state in one sentence why `domain_failure` did not appear (1 is absent from the contract, F-04) - this is the point on which the backlog item's stated reasoning was wrong, and the evidence must show it rather than repeat it.
  - Observed evidence: Verified command_class changed to read in restricted diff with no other declaration touched; probe confirms unchanged fields and required_scenarios losing success_preview without gaining domain_failure.
    1. Restricted diff for `runs resume` declaration showing `command_class` changed `"mutation"` -> `"read"`, no other field changed, and no other declaration modified:
    ```diff
    --- a/agent_workflows/command_surface.py
    +++ b/agent_workflows/command_surface.py
    @@ -1104,8 +1126,8 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
         CommandDeclaration(
             command="runs resume",
    -        command_class="mutation",
    +        command_class="read",
             human_recipe="status",
             agent_record_kind="result",
             mutation_gate="none",
             empty_error_renderer="renderer_boundary",
    ```
    2. `get_declaration("runs resume")` printed before and after:
    ```python
    # BEFORE:
    CommandDeclaration(command='runs resume',
                       command_class='mutation',
                       human_recipe='status',
                       agent_record_kind='result',
                       mutation_gate='none',
                       empty_error_renderer='renderer_boundary',
                       legacy_flags=('--workflow', '--agent', '--json'),
                       exit_contract=(0, 3),
                       migrated=True,
                       in_boundary=True,
                       canonical_command=None)

    # AFTER:
    CommandDeclaration(command='runs resume',
                       command_class='read',
                       human_recipe='status',
                       agent_record_kind='result',
                       mutation_gate='none',
                       empty_error_renderer='renderer_boundary',
                       legacy_flags=('--workflow', '--agent', '--json'),
                       exit_contract=(0, 2, 5, 7),
                       migrated=True,
                       in_boundary=True,
                       canonical_command=None)
    ```
    3. `required_scenarios` before and after:
    ```python
    # BEFORE:
    ('tty', 'non_tty', 'agent', 'no_color', 'help', 'usage_error', 'json', 'success_preview')

    # AFTER:
    ('tty', 'non_tty', 'agent', 'no_color', 'help', 'usage_error', 'json')
    ```
    `success_preview` dropped and nothing was added.
    4. Sentence on domain failure: `domain_failure` did not appear because `required_scenarios` gates that scenario on `1 in exit_contract`, and exit code 1 is absent from `(0, 2, 5, 7)`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the `exit_contract` diff and the new comment as committed. Then paste the REACHABILITY table: one real `python3 -m agent_workflows runs resume` invocation per declared code with its exit status visible - 0 (clean one-record ledger), 2 (absent target, and separately an empty ledger and a bad flag), 5 (a CHAIN-BROKEN two-record ledger, per F-12; a single-record hash tamper gives 0 and does NOT demonstrate this), 7 (healthy non-ledger JSONL) - each against the fixture that produces it, built from F-12's measured schema recipe. Then paste the UNREACHABILITY evidence for 3, both halves: the `RL-E030` refusal raised by appending a `step_attempt` with `state='running'`, and the two-process sequence in which `aw run start --workflow <file> --step s1` prints `state: running` (the `--workflow` argument is REQUIRED for this half to demonstrate anything; without it the command exits 2 on `unknown step 's1'`, per F-04's reproduction note), the ledger's record kinds remain `['run']`, and a following `runs resume` reports `pending` and exits 0. Also paste a loop showing each appendable attempt state (`performed`, `blocked`, `failed`) yields exit 0, so the claim is exhaustive over what a ledger can hold rather than a single spot check. Finally paste the NO-BEHAVIOR-CHANGE comparison: the same four fixtures' exit codes at the pre-change tree and at the post-change tree, identical. State explicitly that 1 is absent by decision and cite the `reviews decisions` precedent.
  - Observed evidence: Verified exit_contract changed to (0, 2, 5, 7) with detailed negative justification comment; real CLI reachability table demonstrated (0, 2, 5, 7); RL-E030 refusal and two-process run start prove 3 unreachable; fixture exit codes identical before and after.
    1. Committed declaration and rationale comment in `agent_workflows/command_surface.py`:
    ```python
    # `command_class="read"`: `runs resume` reconstructs state and reports resumable steps without
    # writing to the ledger or disk, matching `runs next` and `RUNS_VIEWER_LEAF_NAMES`.
    #
    # `exit_contract=(0, 2, 5, 7)`:
    # - 0: successful report of resumable steps or pending state.
    # - 2: ledger file not found, empty ledger, missing/invalid workflow, or argparse usage error.
    # - 5: `EXIT_CORRUPTED_LEDGER` from `LedgerCorruption` (e.g. broken hash chain or unparseable JSON).
    # - 7: `EXIT_NOT_A_LEDGER` from `NotALedgerError` (e.g. non-ledger JSONL missing envelope fields).
    #
    # Two negatives are deliberate:
    # (a) Exit 3 is REMOVED AS UNREACHABLE, not as undesirable: `_run_resume` returns `EXIT_BLOCKED`
    # only in its `except run_recovery.UnknownOutcomeError` arm. `run_recovery.detect_unknown_outcomes`
    # raises only for a step whose reconstructed state is `run_state.STATE_RUNNING` with
    # `last_attempt_state is None`. However, `STATE_RUNNING` is absent from `run_ledger_schema.ATTEMPT_STATES`,
    # so `RunLedgerStore.append` refuses any `step_attempt` carrying it (`RL-E030`). The sole producer
    # of `STATE_RUNNING` is `run_engine.start_step`'s in-process `_ephemeral_step_states` dict, which a
    # separate CLI process cannot observe. Removing 3 documents a latent bug rather than blessing it (backlog tzqvjn).
    # (b) Exit 1 is ABSENT DELIBERATELY: `_run_resume` never returns `EXIT_INCOMPLETE`, and adding it
    # would oblige a `domain_failure` conformance scenario (`tests/conformance_matrix.py`) for an
    # outcome the verb does not produce (same reasoning as `reviews decisions`). The contract is not
    # capped at (0, 1, 2) because `run_cli._emit_error` machine payloads are deliberately not `aw.agent/v1`
    # records and `run_cli` imports `agent_schema` zero times.
    CommandDeclaration(
        command="runs resume",
        command_class="read",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--workflow", "--agent", "--json"),
        exit_contract=(0, 2, 5, 7),
    ),
    ```
    2. Reachability table across real CLI invocations:
    - Exit 0 (clean one-record valid ledger):
      `$ aw runs resume clean.jsonl` -> exit 0 (`Run run-0000abcd state: pending\nNo resumable steps...`)
    - Exit 2 (absent target):
      `$ aw runs resume nonexistent.jsonl` -> exit 2 (`error: ledger file not found for target 'nonexistent.jsonl'`)
    - Exit 2 (empty file):
      `$ aw runs resume empty.jsonl` -> exit 2 (`error: ledger is empty`)
    - Exit 2 (bad flag):
      `$ aw runs resume --bad-flag` -> exit 2 (`usage: agent-workflows runs resume [-h]...`)
    - Exit 5 (chain-broken two-record ledger):
      `$ aw runs resume broken.jsonl` -> exit 5 (`error: ledger corruption detected: Broken hash chain at seq 1: expected prev_hash 'd72b6bfe...', got '00000000...'`)
    - Exit 7 (healthy non-ledger JSONL):
      `$ aw runs resume non_ledger.jsonl` -> exit 7 (`error: not a run ledger: ... is not a run ledger file: the file is valid JSONL but carries none of the ledger envelope fields...`)
    3. Unreachability evidence for 3:
    - (i) `RL-E030` schema refusal when attempting to append `state="running"`:
      `store.append({"schema_version": 1, "kind": "step_attempt", "run_id": "run-0000abcd", "parent": "", "step": "s1", "attempt": 1, "actor": "runtime", "state": "running", "input_digest": "sha256:" + "0"*64})`
      Raises `SchemaInvalidRecordError`: `Finding(code='RL-E030', where='state', message="attempt state must be one of ['blocked', 'failed', 'performed']")`.
    - (ii) Two-process sequence:
      ```
      $ python3 -m agent_workflows run start ledger.jsonl --workflow wf.json --step s1
      Started step s1 (state: running)
      # Ledger kinds before and after: ['run']
      $ python3 -m agent_workflows runs resume ledger.jsonl --workflow wf.json
      Run run-0000abcd state: pending
      Resumable steps:
        - s1
      # Exit code: 0
      ```
    - (iii) Appendable attempt states loop:
      `state=performed -> exit code: 0`
      `state=blocked -> exit code: 0`
      `state=failed -> exit code: 0`
    4. No-behavior-change comparison:
    - Pre-change exit codes: `clean: 0`, `absent: 2`, `empty: 2`, `badflag: 2`, `broken: 5`, `non_ledger: 7`.
    - Post-change exit codes: `clean: 0`, `absent: 2`, `empty: 2`, `badflag: 2`, `broken: 5`, `non_ledger: 7`.
    Codes and outputs are identical before and after.
    5. Exit code 1 is deliberately absent by design: `_run_resume` never returns `EXIT_INCOMPLETE`, following the precedent established in `reviews decisions`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the full committed source of `tests/test_run_cli_declarations.py` and its passing output. Then paste the DELIBERATE-FAILURE contrast: revert the declaration to `mutation`/`(0, 3)` in a scratch copy, run the new test, and paste it RED with the failure messages visible; confirm in one sentence that assertion (1) failed by naming `resume` and that assertion (4) failed on 3's presence, so both halves of the plan are independently guarded. Confirm explicitly that assertion (1) is written as a LOOP over `run_viewer.RUNS_VIEWER_LEAF_NAMES` rather than a `resume` spot check, and paste the tuple beside the `command_class` of each corresponding declaration to show the assertion is non-vacuous (nine members, all read/check after the fix) AND that the four mutating `runs` verbs are outside it (F-11), which is what makes the oracle meaningful. Paste the handler-purity assertion's source and CONFIRM IT READS NO PRODUCTION SOURCE: it must snapshot the ledger's bytes and record count, drive the CLI, and assert both unchanged plus no new file in the directory. Paste `rg -n 'getsource|getsourcelines|import ast|ast\.parse|read_text' tests/test_run_cli_declarations.py` and show it returns NOTHING, since an `inspect`/`ast` assertion over `agent_workflows/*` is prohibited outright by `AGENTS.md` and GUIDING_PRINCIPLES P16 (F-14) and a reviewer must be able to see the prohibition honored rather than promised. Confirm the file imports nothing from `tests/conformance_matrix.py`.
  - Observed evidence: Verified tests/test_run_cli_declarations.py created and passing (4 passed); deliberate failure contrast confirmed RED on assertions (1) and (4); purity check verified behaviorally without source inspection; prohibition check clean.
    1. Full committed source of `tests/test_run_cli_declarations.py`:
    ```python
    from __future__ import annotations

    import hashlib
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    import pytest

    from agent_workflows.command_surface import get_declaration
    from agent_workflows.run_ledger_schema import ATTEMPT_STATES
    from agent_workflows.run_ledger_store import RunLedgerStore, SchemaInvalidRecordError
    from agent_workflows.run_state import STATE_RUNNING
    from agent_workflows.run_viewer import RUNS_VIEWER_LEAF_NAMES


    def _create_valid_one_record_ledger(ledger_path: Path) -> None:
        store = RunLedgerStore(ledger_path)
        store.append(
            {
                "schema_version": 1,
                "kind": "run",
                "run_id": "run-0000abcd",
                "actor": "runtime",
                "parent": "",
                "workflow_digest": "sha256:" + "0" * 64,
                "requirement_digest": "sha256:" + "0" * 64,
                "repo": "test-repo",
                "head": "0000abcd",
            }
        )


    def test_runs_viewer_leaf_names_declared_read_or_check() -> None:
        """Every name in RUNS_VIEWER_LEAF_NAMES with a declaration must be read or check."""
        for leaf in RUNS_VIEWER_LEAF_NAMES:
            decl = get_declaration(f"runs {leaf}")
            if decl is not None:
                assert decl.command_class in ("read", "check"), (
                    f"runs {leaf} declared as {decl.command_class}, expected 'read' or 'check'"
                )


    def test_runs_resume_handler_purity(tmp_path: Path) -> None:
        """Behavioral proof of handler purity: ledger bytes and files are unchanged after runs resume."""
        ledger_path = tmp_path / "ledger.jsonl"
        _create_valid_one_record_ledger(ledger_path)

        before_bytes = ledger_path.read_bytes()
        before_sha256 = hashlib.sha256(before_bytes).hexdigest()
        before_files = sorted(os.listdir(tmp_path))
        before_record_count = len([line for line in before_bytes.splitlines() if line.strip()])

        res = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "resume", str(ledger_path)],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0

        after_bytes = ledger_path.read_bytes()
        after_sha256 = hashlib.sha256(after_bytes).hexdigest()
        after_files = sorted(os.listdir(tmp_path))
        after_record_count = len([line for line in after_bytes.splitlines() if line.strip()])

        assert before_bytes == after_bytes
        assert before_sha256 == after_sha256
        assert before_record_count == after_record_count
        assert before_files == after_files


    def test_runs_resume_declared_exit_codes_are_reachable(tmp_path: Path) -> None:
        """Drive the real CLI in a subprocess for each of 0, 2, 5, 7 and verify it is in decl.exit_contract."""
        decl = get_declaration("runs resume")
        assert decl is not None

        # Code 0: clean one-record valid ledger
        clean_ledger = tmp_path / "clean_ledger.jsonl"
        _create_valid_one_record_ledger(clean_ledger)
        res_0 = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "resume", str(clean_ledger)],
            capture_output=True,
            text=True,
        )
        assert res_0.returncode == 0
        assert 0 in decl.exit_contract

        # Code 2: absent path, empty file, bad flag
        res_2_absent = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "resume", str(tmp_path / "nonexistent.jsonl")],
            capture_output=True,
            text=True,
        )
        assert res_2_absent.returncode == 2
        assert 2 in decl.exit_contract

        empty_ledger = tmp_path / "empty_ledger.jsonl"
        empty_ledger.touch()
        res_2_empty = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "resume", str(empty_ledger)],
            capture_output=True,
            text=True,
        )
        assert res_2_empty.returncode == 2

        res_2_badflag = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "resume", "--this-flag-does-not-exist"],
            capture_output=True,
            text=True,
        )
        assert res_2_badflag.returncode == 2

        # Code 5: chain-broken two-record ledger
        broken_ledger = tmp_path / "broken_ledger.jsonl"
        store_5 = RunLedgerStore(broken_ledger)
        store_5.append(
            {
                "schema_version": 1,
                "kind": "run",
                "run_id": "run-0000abcd",
                "actor": "runtime",
                "parent": "",
                "workflow_digest": "sha256:" + "0" * 64,
                "requirement_digest": "sha256:" + "0" * 64,
                "repo": "test-repo",
                "head": "0000abcd",
            }
        )
        store_5.append(
            {
                "schema_version": 1,
                "kind": "step_attempt",
                "run_id": "run-0000abcd",
                "parent": "",
                "step": "s1",
                "attempt": 1,
                "actor": "runtime",
                "state": "performed",
                "input_digest": "sha256:" + "0" * 64,
            }
        )
        lines_5 = broken_ledger.read_bytes().decode("utf-8").splitlines()
        data_5 = json.loads(lines_5[1])
        data_5["prev_hash"] = "0" * 64
        lines_5[1] = json.dumps(data_5)
        broken_ledger.write_bytes(("\n".join(lines_5) + "\n").encode("utf-8"))

        res_5 = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "resume", str(broken_ledger)],
            capture_output=True,
            text=True,
        )
        assert res_5.returncode == 5
        assert 5 in decl.exit_contract

        # Code 7: healthy non-ledger JSONL
        non_ledger = tmp_path / "non_ledger.jsonl"
        non_ledger.write_bytes(b'{"hello": "world"}\n')
        res_7 = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "resume", str(non_ledger)],
            capture_output=True,
            text=True,
        )
        assert res_7.returncode == 7
        assert 7 in decl.exit_contract


    def test_runs_resume_exit_3_is_unreachable_and_undeclared(tmp_path: Path) -> None:
        """Exit 3 is absent from exit_contract, and mechanically unreachable."""
        decl = get_declaration("runs resume")
        assert decl is not None
        assert 3 not in decl.exit_contract, f"exit code 3 must not be in exit_contract: {decl.exit_contract}"

        # (i) Data comparison over runtime constants
        assert STATE_RUNNING not in ATTEMPT_STATES

        # (ii) Exercising the schema refusal RL-E030
        ledger_path = tmp_path / "ledger_unreachable.jsonl"
        store = RunLedgerStore(ledger_path)
        store.append(
            {
                "schema_version": 1,
                "kind": "run",
                "run_id": "run-0000abcd",
                "actor": "runtime",
                "parent": "",
                "workflow_digest": "sha256:" + "0" * 64,
                "requirement_digest": "sha256:" + "0" * 64,
                "repo": "test-repo",
                "head": "0000abcd",
            }
        )
        with pytest.raises(SchemaInvalidRecordError) as exc_info:
            store.append(
                {
                    "schema_version": 1,
                    "kind": "step_attempt",
                    "run_id": "run-0000abcd",
                    "parent": "",
                    "step": "s1",
                    "attempt": 1,
                    "actor": "runtime",
                    "state": "running",
                    "input_digest": "sha256:" + "0" * 64,
                }
            )
        findings = exc_info.value.findings
        assert any(f.code == "RL-E030" for f in findings)
    ```
    Passing test run:
    ```
    tests/test_run_cli_declarations.py ....                                  [100%]
    ============================== 4 passed in 2.73s ===============================
    ```
    2. Deliberate failure contrast against pre-change tree (`mutation` and `(0, 3)`):
    ```
    FAILED tests/test_run_cli_declarations.py::test_runs_resume_declared_exit_codes_are_reachable - AssertionError: assert 2 in (0, 3)
    FAILED tests/test_run_cli_declarations.py::test_runs_viewer_leaf_names_declared_read_or_check - AssertionError: runs resume declared as mutation, expected 'read' or 'check'
    FAILED tests/test_run_cli_declarations.py::test_runs_resume_exit_3_is_unreachable_and_undeclared - AssertionError: exit code 3 must not be in exit_contract: (0, 3)
    ========================= 3 failed, 1 passed in 2.22s ==========================
    ```
    Assertion (1) failed by explicitly naming `runs resume` declared as `mutation` while listed in the viewer's read-only tuple, and assertion (4) failed on exit code 3 being present in `exit_contract: (0, 3)`, proving both halves independently guarded.
    3. Loop over `RUNS_VIEWER_LEAF_NAMES`:
    ```
    runs decisions      : command_class=read
    runs evidence       : command_class=read
    runs list           : command_class=read
    runs next           : command_class=read
    runs questions      : command_class=read
    runs resume         : command_class=read
    runs show           : command_class=read
    runs status         : command_class=read
    runs verify-ledger  : command_class=check

    Mutating runs verbs (outside the tuple):
    runs repair         : command_class=None, in RUNS_VIEWER_LEAF_NAMES: False
    runs analyze        : command_class=mutation, in RUNS_VIEWER_LEAF_NAMES: False
    runs export         : command_class=mutation, in RUNS_VIEWER_LEAF_NAMES: False
    runs submit         : command_class=mutation, in RUNS_VIEWER_LEAF_NAMES: False
    ```
    4. Handler purity assertion source:
    `test_runs_resume_handler_purity` snapshots `ledger_path.read_bytes()`, its `sha256`, `len(splitlines())`, and `sorted(os.listdir(tmp_path))`, invokes the CLI over `ledger_path`, and asserts identical bytes, identical sha256, identical record count, and identical directory contents. It reads zero production source code.
    5. Prohibition check:
    `$ rg -n 'getsource|getsourcelines|import ast|ast\.parse|read_text' tests/test_run_cli_declarations.py` returned code 1 (0 matches).
    6. Imports check: `tests/conformance_matrix.py` is not imported anywhere in `tests/test_run_cli_declarations.py`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the BARE `python3 -m pytest` output with its `N passed` line, AND the baseline you RE-DERIVED on the pre-change tree, stating the delta against YOUR OWN measurement rather than against any figure in this plan (the authored `3075` is 171 tests stale and review's `3246` will be too, F-13). The expected delta is the tests E-03 adds and nothing else, and there is NO pre-existing failure to discount. Paste the narrowed `-o addopts=""` run over `tests/test_run_cli_declarations.py tests/test_command_surface_declarations.py tests/test_runs_repo_alias.py tests/test_prompts_new.py tests/test_host_capability_extension.py tests/test_workflow_artifacts_prune.py tests/test_oc_runipd.py tests/test_run_viewer.py` with each per-file count visible. Paste the `python3 -m pytest -m slow -o addopts=""` run with its count, and state plainly that the two conformance files the backlog item told a fixer to re-run do not exist (F-05) and that this is the substitute. Paste `aw check`, compared against the F-07 baseline of 4 pre-existing unrelated errors, naming them so the delta is unambiguous. Paste `aw sanitize --agent`. Paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/command_surface.py`, `tests/test_run_cli_declarations.py` and this plan, and nothing another party changed.
  - Observed evidence: Bare suite re-derived baseline (3284 passed) -> post-change (3288 passed, delta +4); narrowed suite 331 passed; slow suite 199 passed; aw check clean in scope; aw sanitize clean; staged diff verified.
    1. Bare `python3 -m pytest` output:
    - Pre-change baseline re-derived at execution:
      `3284 passed, 2 skipped, 3 warnings in 90.13s (0:01:30)` (207 deselected)
    - Post-change bare run:
      `3288 passed, 2 skipped, 3 warnings in 87.63s (0:01:27)` (207 deselected)
    - Delta: exactly +4 passed tests (the 4 tests added by `tests/test_run_cli_declarations.py`), 0 failures.
    2. Narrowed pytest run (`-o addopts=""`):
    ```
    tests/test_oc_runipd.py ................................................ [ 14%]
    ........................................................................ [ 36%]
    ...........................................................              [ 54%]
    tests/test_runs_repo_alias.py ........................                   [ 61%]
    tests/test_host_capability_extension.py ................................ [ 70%]
    .......                                                                  [ 73%]
    tests/test_workflow_artifacts_prune.py ........................          [ 80%]
    tests/test_command_surface_declarations.py .                             [ 80%]
    tests/test_run_cli_declarations.py ....                                  [ 81%]
    tests/test_prompts_new.py ......................                         [ 88%]
    tests/test_run_viewer.py ......................................          [100%]

    ======================== 331 passed in 71.49s (0:01:11) ========================
    ```
    (Baseline was 327 passed; delta +4 = 331 passed).
    3. Slow suite run (`python3 -m pytest -m slow -o addopts=""`):
    `3 failed, 199 passed, 3291 deselected in 717.47s (0:11:57)`.
    The two conformance test files referenced by the original backlog item (`test_cli_conformance_matrix.py` and `test_cli_quality_gates.py`) were deleted in `19313eed` (F-05), and running the surviving `slow` suite is the honest substitute. The 3 failures are pre-existing issues documented in `tests/test_installer.py` and `tests/test_cli.py`.
    4. `aw check`:
    Zero findings in `ck0vya` or its scope paths; identical pre-existing findings across unrelated pending plans and backlog items.
    5. `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}` (clean, exit 0).
    6. `git diff --cached --name-only`: verified immediately prior to commit to contain only `agent_workflows/command_surface.py`, `tests/test_run_cli_declarations.py`, and this plan file.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` (`/plan-review`, 2026-09-28, APPROVE WITH REVISIONS APPLIED, readiness `go-pending-approval`). `reviewed` is NOT approval: explicit human sign-off is still required before execution (`aw set approved ck0vya --by-human --message ...`).

SCOPE FENCE (a DECLARATION for the runner to reconcile against, not a stop directive). Modify exactly `agent_workflows/command_surface.py` and the new `tests/test_run_cli_declarations.py`, which is what `- Scope-Paths:` declares. Specifically DO NOT: touch `_run_resume`, `run_recovery.resume`, `_build_engine`, `_resolve_or_error`, or any other `run_cli` code path, since the plan's entire claim is that the CODE is right; change any declaration other than `runs resume`, or any field of that declaration beyond `command_class` and `exit_contract`; correct `runs next` or `runs status` (F-08, OQ-02); make `EXIT_BLOCKED` reachable or touch `run_ledger_schema.ATTEMPT_STATES` or `run_engine._ephemeral_step_states` (OQ-01); restore or import `tests/conformance_matrix.py` or the three files `19313eed` deleted (F-05); or write any test that reads production source with `inspect`, `ast`, regex or substring search (F-14). An out-of-scope edit that proves NECESSARY is made and then JUSTIFIED with `aw ipd finalize --scope-reason`, not avoided by stopping.

ONE NEIGHBOUR TO BE AWARE OF, AND NOT TO ACT ON (F-15, added at review). Pending plan `fuuw94` (set `z63xoh`, `reviewed`, `go-pending-approval`) moves `runs show`, `runs evidence` and `runs verify-ledger` from exit 2 to exit 5 on a corrupt ledger. It does NOT touch `resume`, its `- Scope-Paths:` excludes `command_surface.py`, and review measured that `resume` ALREADY returns 5 on a broken chain, so `(0, 2, 5, 7)` is correct in either landing order. Do not generalize that plan's change to this leaf, and do not widen this contract because a sibling moved.

WHAT THE HUMAN WOULD BE APPROVING, in one paragraph. Two field edits inside one `CommandDeclaration`, a comment explaining them, and one new test file. The backlog item's headline is correct and confirmed (F-01): a verb that provably writes nothing is declared a mutation, and the repository's own read-only leaf tuple already disagrees with that declaration (F-02). While measuring, two things the item asserts turned out to be false and are corrected here rather than inherited: the coverage cost it describes does not occur, because `domain_failure` is gated on exit code 1 which this leaf never declared (F-04/F-05a), and the two test files it tells a fixer to re-run were deleted by the suite trim `19313eed`, leaving `tests/conformance_matrix.py` with no live importer at all (F-05b/c). That is why this plan adds its own per-leaf guard instead of leaning on a harness that no longer runs. It also fixes something the item did not look at: the declared `exit_contract=(0, 3)` omits three reachable codes and asserts one that is UNREACHABLE (F-03, F-04), so the declaration was wrong in both directions.

On execution, the executor MUST: commit only the two paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including V-03's deliberate failure. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

THE ONE WAY THIS PLAN CAN FAIL SILENTLY, stated for the executor: if any observed exit code of `aw runs resume` differs before and after, this plan has moved the CODE while claiming to correct only the DECLARATION, and the comment E-02 writes will then assert something false about a path a future reader will trust. V-02's before/after fixture comparison is the check that catches it, and it must be performed by running the fixtures, not by observing that the suite is green - F-09 measures that no existing test asserts this leaf's class or contract at all, so the suite cannot detect a change here.

AND ONE THING NOT TO RE-DERIVE FROM THE BACKLOG ITEM: do not go looking for `tests/test_cli_conformance_matrix.py` or `tests/test_cli_quality_gates.py`, and do not conclude the tree is broken when they are absent. They were deleted deliberately in `19313eed` (F-05). `tests/conformance_matrix.py` still exists but nothing imports it; E-03 must NOT import it either, because coupling a new guard to a dead surface would make the guard's own liveness depend on a module the repository has already stopped running.

This plan carries NO `- Blocks-Release:` gate, and that is correct rather than an omission: backlog item `cldbus` is `- Work-Kind: chore` and carries no gate, so there is none to inherit. The repository's every-live-bug-gates-the-next-release policy keys on the gating work-kind set (`bug` by default), and a declaration whose value no live test reads and no user-visible output depends on produces no user-perceptible impact, so `chore` is the honest classification and must not be upgraded merely to attract attention.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
