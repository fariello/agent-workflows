# IPD: Make capture_command's output-text contract explicit and tested so a fabricated mock key cannot hide an empty read again

- Date: 2026-09-29
- Kind: child
- Concern: `run_evidence.capture_command` hands its output text back by MUTATING the ledger record it just built, writing four keys (`stdout`, `stderr`, `stdout_excerpt`, `stderr_excerpt`) that `build_tool_event` does not know about. Three consequences, each measured at lane HEAD `a5b36500`. FIRST, THE RETURNED MAPPING IS A VALID `tool_event` THAT CARRIES THE TEXT, so a caller that appends it persists the output TWICE into the durable hash-chained ledger: measured, `RunLedgerStore.append(tool_event)` wrote a 10,548-byte line whose persisted keys include `stdout`, `stdout_excerpt`, `stderr` and `stderr_excerpt` beside the digests, and `validate_record` returns ok because the schema is add-only (F-01, F-02). That is exactly the unbounded-output-in-durable-records cost the original fix said it was avoiding, and it is now reachable rather than hypothetical. SECOND, THE CONTRACT IS INVISIBLE TO A TEST DOUBLE: a mock returning a plain `dict` without those keys type-checks, passes, and reproduces the original defect silently, which is precisely how the empty `summary` hid across every run since `novalnomerge-01` shipped. THIRD, TWO SPELLINGS ARE SUPPLIED FOR ONE VALUE, so the two consumers read two different names for identical text and a third caller has no way to know which is canonical.
- Scope: Give `capture_command` a TYPED return whose output text is carried OUT OF BAND of the ledger record, converge the two consumers on one spelling, and pin the contract with tests that call the real function. IN: a `CapturedToolEvent` `dict` subclass that IS the `tool_event` mapping (so every existing `.get("exit_code")` / `["stdout_sha256"]` read is unchanged) but carries `stdout`/`stderr` as ATTRIBUTES, so `dict(...)`, `json.dumps`, `copy.deepcopy` and `RunLedgerStore.append` see only the schema fields; deleting the four injected mapping keys; repointing `runner_shared.run_suite_check` and `host_runner.run_worker_process` at the attributes; a contract test that calls the REAL `capture_command` and asserts both the presence of the text and the ABSENCE of text keys from the persisted record; and a regression test proving the append path no longer carries output. OUT: changing `build_tool_event`'s record shape or `run_ledger_schema._KIND_FIELDS`; deciding whether a BOUNDED excerpt belongs in the persisted ledger (declined with reason, see OQ-02); forwarding `TaskPacket.max_output_bytes` (a separate measured defect, carried to `fqseay`); bounding `stderr` against `max_output_bytes` (carried to `lijmwy`); and any change to redaction, to the leak sanitizer, or to what either consumer does with the text once it has it.
- Scope-Paths: agent_workflows/run_evidence.py, agent_workflows/runner_shared.py, agent_workflows/host_runner.py, docs/evidence.md, tests/test_capture_command_contract.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: he9x6j
- Blocks-Release: next
- Set: toolevtext
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: emzbut

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: emzbut verified (set toolevtext, attempt 1).
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401 through PR-406, all FIXED, none deferred and none left open. Review record: `.aw/records/reviews/20260929-toolevtext-01-emzbut-make-capture-command-s-output-text-contract-explicit-and-tes.review.md`.
  THE DESIGN IS RIGHT AND WAS NOT DISTURBED; ALL SIX FINDINGS WERE IN THE TEST RECIPES AND THE BLAST-RADIUS CLAIM. Every load-bearing measurement reproduced at review HEAD `b233857e` (F-01's ledger leak, F-02's clean validation, F-03's prototype, F-05 through F-09, F-11 through F-13), the bare suite matched F-10 exactly at `3246 passed, 2 skipped`, and `aw ipd lint` was clean at both `author` and `review-finalize`.
  TWO HIGHS. PR-401: E-05 prescribed `pytest.raises(AttributeError)` at a consumer whose DELIBERATE blind `except Exception` - which E-03 protects - catches it, so the assertion was unsatisfiable and "fixing" it meant deleting a fail-closed guard; F-04 and E-05 now pin the per-consumer behavior each actually has, measured. PR-402: F-12's completeness claim missed `verify_roles`' `tuple(dict(e) for e in ...)` normalization feeding `procedure_test_falsifiability`'s `ev.get("stdout")`, which would drop the text SILENTLY (the one failure mode this shape cannot make loud); recorded as F-14, latent today, and E-01 must now name it by symbol.
  FOUR OF THE PLAN'S VALIDATION STEPS COULD NOT HAVE BEEN EXECUTED AS WRITTEN and are corrected with measurements: the emitted key set is not constant (`max_bytes` appears only when bounded, 22 keys against 23, PR-403); the persistence proof's seed record is refused without four more fields and its actor must be `executor` because `validate_record` rejects the gate's own `driver` (PR-404, recorded as F-15); and the decode asymmetry is invisible on the invalid-byte input the plan chose, needing a valid multi-byte character instead (PR-405).
  FOR THE MAINTAINER, not a finding against this plan: F-15 records that `run_suite_check` captures with `actor="driver"`, which is not in `run_ledger_schema.ROLES`, so its tool events are permanently unpersistable. Harmless today and correctly out of scope; whether to widen `ROLES` or change the gate's actor is yours to file.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `he9x6j`. GATE NOTE: item `he9x6j` carries `- Blocks-Release: next`, which this plan INHERITS as required.
  THE ITEM'S THIRD LEFTOVER IS NOW A MEASURED DEFECT, NOT AN OPEN QUESTION, and that is the single most important correction this plan makes to the item. The item records leftover 3 as "Whether the text belongs in the PERSISTED ledger record (not just the returned mapping) is an open design question with a real cost: unbounded command output in durable records. Not decided here." Measured during authoring: the cost is ALREADY BEING PAID whenever a caller appends what `capture_command` returns, because the returned mapping IS a schema-valid `tool_event` carrying the text (F-01, F-02). So the question is not whether to ADD the text to the ledger; it is that the text is already reachable there by accident, and the fix is to make it structurally unreachable. The design question the item names is answered NO and declined with reasons in OQ-02.
  THE ITEM'S LEFTOVER 1 IS STALE IN ITS SPECIFICS AND STILL CORRECT IN ITS SUBSTANCE. The item says "every test of `run_suite_check` mocks `capture_command` and fabricates a `stdout_excerpt` key". Those tests NO LONGER EXIST: `tests/test_novalnomerge_integration.py` and `tests/test_integration_refusal_cause.py` were deleted wholesale in commit `19313eed`, and `rg -n "stdout_excerpt" tests/` now returns NOTHING (F-05). So there is no fabricating mock left to repair. The hazard is nonetheless real and UNADDRESSED in the opposite direction: there is now ZERO test coverage of `capture_command` anywhere in the suite (F-06), so the contract is pinned by nothing at all. An executor who goes looking for the mocks the item describes will waste a pass.
  TWO NEW DEFECTS WERE MEASURED AND CARRIED RATHER THAN FOLDED IN. `host_runner.run_worker_process` silently ignores `TaskPacket.max_output_bytes` (F-08, carried to `fqseay`) and `capture_command` truncates stdout but never stderr (F-09, carried to `lijmwy`). Both are adjacent to this plan's two call sites and neither is in scope; a reviewer must not read this plan as closing them.

## Goal

Make the way `capture_command` returns command output a CONTRACT rather than a convention: the text travels as typed attributes on the returned object, so a consumer reads one name, a test double that omits it fails loudly instead of silently yielding `""`, and the durable ledger record cannot carry unbounded output even if a caller appends the returned value directly. Then pin it with the tests that do not currently exist.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: give the returned value a shape that cannot leak into the ledger

- [x] E-01 ADD A `CapturedToolEvent` TYPE TO `run_evidence` that IS the `tool_event` mapping and carries the output text OUT OF BAND. Make it a `dict` subclass with `stdout` and `stderr` as instance ATTRIBUTES (declare `__slots__ = ("stdout", "stderr")` so no `__dict__` is created and the attributes cannot be confused for mapping entries). Do not add any mapping key.
  WHY A `dict` SUBCLASS AND NOT A `NamedTuple` OR A DATACLASS WRAPPER: every existing consumer reads the record by SUBSCRIPT or `.get()` (`tool_event.get("exit_code")` in both consumers, `tool_event["stdout_sha256"]` in `capture_command`'s own envelope construction), and `capture_command` returns a 2-tuple that callers unpack positionally. A `dict` subclass keeps ALL of that byte-identical while adding the attributes, so this is a purely additive change at every call site. A wrapper object would break every subscript read and force edits at sites this plan does not need to touch.
  WHY THIS STRUCTURALLY FIXES THE PERSISTENCE LEAK, which is the whole point of the type: `json.dumps`, `copy.deepcopy(dict(record))` (what `RunLedgerStore.append` actually does), `dict(...)`, and iteration all see ONLY the schema fields, because attributes are not mapping entries. VERIFIED BY MEASUREMENT during authoring (F-03): appending such an object through the real `RunLedgerStore` persisted `stdout_sha256` and NO text key, while the caller's `.stdout` still read 5000 characters. So the fix is not a convention a future caller must remember; it is a property of the type.
  DOCUMENT AT THE SYMBOL what the two attributes mean and why they are not mapping entries, so the next reader does not "tidy" them back into the dict. State plainly that the text is DECODED (`utf-8`, `errors="replace"`) and that `stdout_len`/`stdout_sha256` are computed over the RAW BYTES, so the attribute length and `stdout_len` may differ; ANY multi-byte output diverges, not only invalid output (measured at review: `e-acute` gives `stdout_len` 2 against 1 decoded character, while three INVALID bytes give 3 against 3, so "non-UTF-8" is the wrong framing and "raw bytes versus decoded characters" is the right one).
  NAME THE ONE REAL NORMALIZATION HAZARD BY SYMBOL, not in the abstract (F-14): state that `dict(result)`, or any copy that goes through it, DROPS the attributes with no error, and cite `verify_roles.build_verifier_packet` / `verifier_packet_from_dict`, whose `tuple(dict(e) for e in ...)` normalization feeds `procedure_test_falsifiability`'s `ev.get("stdout", "")` read. That path is not reachable from either consumer today, which is exactly why a future author wiring worker output into the verifier manifest needs the warning at the type they would be handling.
  - Depends on: none
  - Expected outcome: `run_evidence.CapturedToolEvent` exists, is a `dict` subclass with `__slots__`-declared `stdout`/`stderr` attributes, satisfies `isinstance(x, dict)`, and round-trips through `dict()`/`json.dumps`/`deepcopy` carrying no text key.
  - Execution state: performed

- [x] E-02 RETURN A `CapturedToolEvent` FROM `capture_command` AND DELETE THE FOUR INJECTED MAPPING KEYS (`stdout`, `stderr`, `stdout_excerpt`, `stderr_excerpt`). The decode logic already present stays; only its destination changes, from four `tool_event[...] = ...` assignments to the two constructor arguments.
  KEEP `build_tool_event` UNTOUCHED. It is the ledger's own constructor, its output is schema-checked, and the original fix was right that widening it is a bigger decision. This item removes the MUTATION of its result rather than changing the function.
  CONSTRUCT THE ENVELOPE FROM THE SAME DIGEST IT USES TODAY. `build_evidence_envelope` is called with `stdout_sha256=tool_event["stdout_sha256"]`; that read is a mapping subscript and is unaffected, but confirm it by reading the code rather than assuming, because it is the one place inside this function that reads the record it just built.
  REPLACE THE EXISTING COMMENT BLOCK, do not merely append to it. The current block explains at length why the keys are attached to the returned mapping and why BOTH spellings are supplied; after this item both statements are false. Leaving them would be exactly the stale-documentation failure the repository's honest-documentation principle forbids. The replacement must say what the type does, why the text is out of band (the measured persistence leak of F-01), and that the two spellings were converged (E-03).
  - Depends on: E-01
  - Expected outcome: `capture_command` returns `(CapturedToolEvent, envelope)`; `sorted(returned_mapping)` contains none of the four text keys; `returned.stdout` / `.stderr` carry the decoded text; the envelope is unchanged; and the stale comment block is replaced rather than extended.
  - Execution state: performed

### Task group 2: converge the two consumers on one spelling

- [x] E-03 REPOINT `runner_shared.run_suite_check` AT THE ATTRIBUTES, replacing `str(tool_event.get("stdout_excerpt") or "")` and its `stderr_excerpt` twin with the attribute reads. This is the consumer whose breakage was VISIBLE: its `SuiteCheckResult.summary` was always empty and every suite-failure refusal reason read `no summary line parsed`.
  KEEP THE `exit_code` READ AS A MAPPING READ. `int(tool_event.get("exit_code", 127))` is a schema field and must stay a `.get()` with its 127 default, because that default is the fail-closed path when the record is somehow malformed. Do NOT convert it to an attribute.
  UPDATE THE DOCSTRING, WHICH CURRENTLY NARRATES THE OLD MECHANISM. Its paragraph beginning `THE OUTPUT READ HERE ONLY STARTED WORKING AT gatewire-01` states that `capture_command` "now returns the text on the mapping it hands back"; after E-02 that is wrong in the one detail a reader would rely on. Rewrite it to name the attributes and to keep the measured history (the read yielded `""`, `summary` was always empty) because that history is why the test in E-05 exists.
  PRESERVE THE BLIND `except Exception` AND ITS REASONING. It guards the unguarded lines BEFORE the subprocess call (`Path(cwd).resolve()` and the three git probes), a gate that crashes is a gate that is off, and none of that changes here.
  - Depends on: E-02
  - Expected outcome: `run_suite_check` reads `stdout`/`stderr` from the attributes, still parses a real summary and real failure lines from a live run, still fails closed on exit 124/127, and its docstring describes the mechanism that now exists.
  - Execution state: performed

- [x] E-04 REPOINT `host_runner.run_worker_process` AT THE ATTRIBUTES, replacing `tool_event.get("stdout", "") or ""` and its `stderr` twin. This consumer read the OTHER spelling, and converging both onto the attributes is what makes the two-spelling cleanup (the item's leftover 2) actually complete rather than merely documented.
  DO NOT TOUCH THE `runner` INJECTION SEAM. When a `RunnerFn` double is supplied the function takes the `exit_code, stdout, stderr = runner(...)` branch and never calls `capture_command`; that branch is how the scheduler and its tests substitute a worker and must keep working unchanged. Only the `else` branch changes.
  DO NOT FORWARD `packet.max_output_bytes` HERE, even though it is obviously missing and sits three lines away. It is a separate measured defect (F-08) with its own scope decision about what the default should be, and it is carried to `fqseay`. Folding it in would put an unreviewed behavior change inside a plan a reviewer is reading for a contract cleanup.
  - Depends on: E-02
  - Expected outcome: `run_worker_process` reads the attributes in its real-spawn branch, the `RunnerFn` branch is byte-identical, `RawWorkerResult.stdout`/`.stderr` still carry the worker's real output, and `max_output_bytes` remains unforwarded with a comment naming `fqseay`.
  - Execution state: performed

### Task group 3: pin the contract that nothing currently tests

- [x] E-05 ADD `tests/test_capture_command_contract.py` THAT CALLS THE REAL `capture_command`, since the suite currently contains ZERO coverage of it (F-06) and the deleted mocks are why the original defect survived unnoticed.
  THE CENTRAL ASSERTION IS A BIJECTION BETWEEN WHAT THE FUNCTION EMITS AND WHAT ITS CONSUMERS READ: run a real subprocess writing known text to both streams, then assert the text is readable via the attributes AND that `sorted(returned_mapping)` contains NO key matching `stdout`/`stderr` beyond the four schema fields (`stdout_sha256`, `stderr_sha256`, `stdout_len`, `stderr_len`).
  THE KEY-SET ASSERTION MUST BE PINNED PER CALL SHAPE, NOT AS ONE GLOBAL LITERAL (corrected at review, PR-403). The emitted key set is NOT constant: `max_bytes` is present only when `max_output_bytes` is passed. MEASURED at review, the no-bound call emits 22 keys and the bounded call emits 23, differing exactly by `max_bytes`. A single hardcoded `==` list therefore fails on whichever shape it was not written against. Write the exact-set assertion TWICE, once per shape, or assert `set(mapping) == BASE | {"max_bytes"}` for the bounded case against a named `BASE` constant. Keep it an EXACT set comparison (a substring probe would not catch an accidentally re-added key), and note that `run_suite_check` uses the BOUNDED shape (`max_output_bytes=512_000`) while `run_worker_process` uses the UNBOUNDED one, so both shapes are production-reachable and both are worth pinning.
  ASSERT THE PERSISTENCE PROPERTY THROUGH THE REAL STORE, not by inspecting the mapping alone. Append the returned object to a real `RunLedgerStore` in a `tempfile` directory and assert the persisted JSON line carries NO text key and that its length is bounded, driving a command whose output is large enough that a leak would be unmistakable. This is the assertion that would have caught F-01, and it must exercise the store rather than reimplement its serialization.
  THE SEED RECORD AND THE ACTOR ARE BOTH LOAD-BEARING AND THE AUTHORING RECIPE UNDER-SPECIFIES BOTH (corrected at review, PR-404; both cost a review pass to discover). FIRST, the seed `kind: "run"` record needs more than `kind`: `RunLedgerStore.append` schema-validates BEFORE the seq-0 kind check, so a minimal seed is REJECTED with `RL-E010` (missing `parent`) plus four `RL-E020`s demanding `workflow_digest`, `requirement_digest`, `repo` and `head`. A seed that works is `{"schema_version": 2, "kind": "run", "run_id": "run-abc123ff", "actor": "executor", "parent": "", "workflow_digest": <64 hex>, "requirement_digest": <64 hex>, "repo": <str>, "head": <40 hex>}`. SECOND, the `tool_event` must be captured with an actor in `run_ledger_schema.ROLES`: the append validates the record, and `actor="driver"` - which is literally what `run_suite_check` passes in production - FAILS with `RL-E014 unknown actor role 'driver'`. Use `actor="executor"` in the persistence test and do NOT "fix" `run_suite_check`'s actor here; that is a pre-existing question this plan does not own, and it is why the leak of F-01 is reachable through `run_worker_process`'s default actor rather than through the suite gate.
  ASSERT THE MOCK-SHAPE HAZARD IS NOW CAUGHT, PER CONSUMER, BECAUSE THE TWO CONSUMERS DIFFER (corrected at review, PR-401; the earlier wording prescribed a single `pytest.raises(AttributeError)` that is UNSATISFIABLE at one of them). Do NOT write one blanket `pytest.raises`. Write TWO assertions matching measured behavior:
  (a) FOR `run_worker_process`, which has NO exception handler: patch `capture_command` to return a bare `dict` and assert with `pytest.raises(AttributeError)` that the error PROPAGATES. This is the genuinely loud case.
  (b) FOR `run_suite_check`, whose DELIBERATE blind `except Exception` catches it by design (and must keep doing so, per E-03): assert NO exception escapes and that the returned `SuiteCheckResult` is a REFUSAL - `passing is False`, `exit_code == 127`, and `reason` CONTAINING both `suite check could not run (fail-closed)` and the attribute name. Assert the CONTRAST that makes this the fix: measured at review, the same text-less double under the PRE-fix mapping read returns `passing=True` with an empty `summary`, so the property being pinned is "a text-less double now REFUSES instead of silently passing", not "it raises".
  Pinning (b) as a raise would make the test demand that the blind catch be removed, which E-03 forbids and which would turn a fail-closed gate into a crashing one.
  COVER THE ERROR PATHS, because they are the ones a gate depends on: a nonexistent argv must give exit 127 with the exception text on `.stderr`, and a command exceeding a short `timeout` must give exit 124; neither may raise. Both reproduce at review (exit 127 with `[Errno 2] No such file or directory: ...` on stderr; exit 124 with `\nCommand timed out.` appended).
  COVER THE RAW-BYTES-VERSUS-DECODED-CHARACTERS ASYMMETRY, and pick the case that actually DEMONSTRATES it (corrected at review, PR-405). Writing three INVALID bytes does NOT demonstrate divergence: measured at review, `b"\xff\xfe\xfd"` gives `stdout_len` 3 and 3 decoded replacement characters, so an assertion of inequality on that input FAILS and an assertion of equality pins nothing. Use a VALID multi-byte character instead, where the numbers genuinely diverge: `e-acute` encoded as UTF-8 gives `stdout_len` 2 (raw bytes) against 1 decoded character. Assert BOTH cases: the multi-byte case for the length divergence, and the invalid-byte case for the replacement-decode behavior with `stdout_sha256` matching the SHA-256 of the RAW bytes.
  DRIVE REAL SUBPROCESSES AND ASSERT OUTCOMES ONLY. No `inspect`, no `ast`, no reading of `agent_workflows/*.py`, no assertion about docstrings or comments, per the repository's outcomes-not-structure rule.
  - Depends on: E-04
  - Expected outcome: a new passing test file pinning the attribute contract, the exact mapping key set PER CALL SHAPE (bounded and unbounded, differing by `max_bytes`), the append-path absence of text through a real fully-seeded store, the per-consumer behavior of a text-less double (propagating at `run_worker_process`, a fail-closed refusal at `run_suite_check`), exit 124 and 127, and both decode cases (multi-byte length divergence, invalid-byte replacement with the digest over raw bytes).
  - Execution state: performed

- [x] E-06 ADD CONSUMER-LEVEL COVERAGE FOR BOTH READ SITES IN THE SAME FILE, so the repair is proven end to end at the surfaces that were broken rather than only at the producer.
  FOR `run_suite_check`: call it with `SUITE_CHECK_ARGV` patched to a tiny real command that prints a pytest-shaped count line, and assert `summary` is the NON-EMPTY count line and that the `reason` string does NOT contain `no summary line parsed`. That exact string is the observable symptom the original defect produced on every failing run, so asserting its absence is the regression pin. Also patch the argv to a command that prints a `FAILED ...` line with a nonzero exit and assert `failures` is non-empty and `passing` is False. Patch only `SUITE_CHECK_ARGV`; do NOT mock `capture_command`, which is the practice that hid the bug.
  THE PATCH MECHANISM IS CONFIRMED SUFFICIENT, so no executor pass is spent discovering it: `run_suite_check` reads `SUITE_CHECK_ARGV` as a MODULE ATTRIBUTE at call time (`list(SUITE_CHECK_ARGV)` inside the function), so `mock.patch.object(runner_shared, "SUITE_CHECK_ARGV", argv)` reaches it with no from-import problem. Measured at review against the PRE-fix code: a passing argv gives `summary='3 passed in 0.42s'` and `reason='suite passed in . (3 passed in 0.42s)'`, and a failing argv gives `passing=False`, `failures=('FAILED tests/test_x.py::test_y',)`, `summary='1 failed in 0.1s'`. NOTE WHAT THIS IMPLIES FOR THE MUTATION PROOF BELOW, because it is the one thing that could make this item's central evidence impossible: these values come from the CURRENT (post-`h5pyqa`) code, which already works (F-07), so the mutation must be introduced deliberately as described rather than being available by simply checking out an older tree.
  FOR `run_worker_process`: build a real `TaskPacket` whose argv writes to both streams and assert `RawWorkerResult.stdout`/`.stderr` carry it. ALSO assert the `RunnerFn` injection branch still works unchanged, since E-04 must not disturb it.
  VERIFY TEST SENSITIVITY BY MUTATION and record it in the validation evidence: reverting E-03's read to the old `.get("stdout_excerpt")` must make the `run_suite_check` assertion FAIL. A test that passes against the broken code is worthless here, and this defect class is precisely one where that happened.
  - Depends on: E-05
  - Expected outcome: both consumers are covered by tests that call them for real; `run_suite_check` is pinned to produce a non-empty summary and real failure lines; the `RunnerFn` branch is pinned; and the mutation check is demonstrated to fail on the pre-fix read.
  - Execution state: performed

## Project conventions discovered (Step 0)

- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `-n0` makes it several times slower, a second `-q` suppresses the `N passed` line this plan requires be pasted, and `-p no:randomly` disables the order randomization. Authoring measured `3246 passed, 2 skipped, 3 warnings in 94.86s` with 207 deselected (F-10).
- A VALID `run_id` IS `run-<hex>` AND VALIDATION FAILS WITHOUT IT. `run_ledger_schema.validate_record` emits `RL-E015` for anything else, so every probe and test in this area must use a well-formed id (authoring used `run-abc123ff`); a plausible-looking `run-abc123` fails because `c` is hex but the check is on the whole token. Measured during authoring when a first probe reported a false finding.
- `RunLedgerStore` REQUIRES THE FIRST RECORD TO BE `kind: "run"` (`RL-E041` at seq 0), so any test appending a `tool_event` must seed a `run` record first. Measured while building the F-03 probe.
- THE LEDGER SCHEMA IS ADD-ONLY AND DOES NOT REJECT EXTRA KEYS. `validate_record` checks the common envelope plus `_KIND_FIELDS[kind]` and never enumerates forbidden keys, which is WHY the text-bearing mapping validates clean (F-02). Do not expect the schema to catch a leak; the type must prevent it.
- `capture_command` NEVER RAISES FOR A SUBPROCESS PROBLEM: a timeout becomes exit 124 and any other exception becomes exit 127, both with text on stderr. Callers depend on this (both consumers read an exit code rather than catching), so tests must assert the codes rather than expect exceptions.
- THE `aw` CONSOLE SCRIPT MAY IMPORT THE PACKAGE FROM THE MAIN CHECKOUT AND SAYS SO ON STDERR. Evidence-producing invocations should state the interpreter, or use `python3 -m agent_workflows` with `AW_NO_REEXEC=1`; every measurement in this plan was taken with a bare `python3` running in the lane root, where the lane's package is what imports.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE ITEM'S "OPEN DESIGN QUESTION" IS ALREADY A LIVE LEAK: APPENDING THE RETURNED MAPPING PERSISTS THE OUTPUT TWICE INTO THE DURABLE LEDGER.** The item defers "whether the text belongs in the PERSISTED ledger record" on the stated cost of "unbounded command output in durable records". Measured: appending what `capture_command` returns through a real `RunLedgerStore` wrote a line of **10,548 bytes** whose persisted keys include `stdout`, `stdout_excerpt`, `stderr` and `stderr_excerpt` beside `stdout_sha256`/`stdout_len`. So the text lands in the hash-chained JSONL, and it lands TWICE because both spellings carry the same string. The cost the item wanted to avoid is therefore already payable by any caller, which converts the question from "should we add it" to "it is there by accident and must be made structurally impossible". | `RunLedgerStore.append` on a seeded temp ledger followed by reading the persisted line back with `json.loads`, at lane HEAD `a5b36500` |
| F-02 | **THE SCHEMA CANNOT CATCH THAT LEAK, so the fix must be structural rather than a validation rule.** `run_ledger_schema.validate_record` on the text-bearing mapping returns `ok=True` with zero findings. The validator checks the common envelope, `_KIND_FIELDS["tool_event"]` (`argv`, `cwd`, `exit_code`, `stdout_sha256`) and a set of value rules; it never enumerates a permitted key set, so unknown keys pass by design (add-only forward compatibility, which the module states as a goal for v2 kinds). Adding a "no extra keys" rule would be a breaking change to that design, which is why E-01 prevents the leak with a type instead. | direct call to `validate_record` on the object returned by `capture_command`, returning `ok=True` |
| F-03 | **THE PROPOSED FIX IS PROVEN, NOT SPECULATIVE: a `dict` subclass carrying the text as `__slots__` attributes keeps the persisted record clean while the caller still reads the text.** A prototype `CapturedToolEvent(dict)` with `__slots__ = ("stdout", "stderr")` was appended through the real `RunLedgerStore`: the persisted line's only stdout-ish key was `stdout_sha256`, and the in-memory object's `.stdout` still returned 5000 characters. `isinstance(x, dict)` holds, `.get("exit_code")` works, and `dict(x)` / `json.dumps` / `copy.deepcopy(dict(x))` all see schema fields only, which matters because `append` does exactly `copy.deepcopy(dict(record))`. | prototype class appended through `RunLedgerStore` in a temp dir, persisted line inspected, attribute re-read afterwards |
| F-04 | **A PLAIN-`dict` TEST DOUBLE FAILS LOUDLY UNDER THE NEW CONTRACT AND SILENTLY UNDER THE OLD ONE, BUT ONLY AT ONE OF THE TWO CONSUMERS, and the distinction is load-bearing (CORRECTED AT REVIEW, PR-401).** The raw comparison holds: `{}.get("stdout_excerpt") or ""` yields `''` while `{}.stdout` raises `AttributeError: 'dict' object has no attribute 'stdout'`. WHAT THE AUTHORING MEASUREMENT MISSED is what each consumer DOES with that exception. `host_runner.run_worker_process` has NO `try`/`except` at all, so the `AttributeError` PROPAGATES to its caller: genuinely loud. `runner_shared.run_suite_check` wraps its read in the DELIBERATE blind `except Exception`, so the `AttributeError` is CAUGHT and converted into `SuiteCheckResult(passing=False, exit_code=127, summary='', reason='suite check could not run (fail-closed): ...')`. MEASURED AT REVIEW by patching `capture_command` to raise that exact `AttributeError`: no exception escaped, and the returned reason was `suite check could not run (fail-closed): 'dict' object has no attribute 'stdout'`. So at THAT consumer the new failure mode is a FAIL-CLOSED REFUSAL NAMING THE CAUSE, not a propagated exception. That is still a large improvement over today (a silent pass carrying `no summary line parsed`, measured at review: a text-less double returns `passing=True` with an empty summary), and it is NOT the `pytest.raises(AttributeError)` the original E-05 prescribed. E-05 is corrected to assert the per-consumer behavior each one actually has. | review probe: `mock.patch.object(run_evidence, "capture_command", ...)` returning a bare `dict` gives `passing=True, summary='', reason='suite passed in . (no summary line parsed)'`; the same patch raising `AttributeError` gives `passing=False, exit_code=127, reason='suite check could not run (fail-closed): ...'` with nothing propagated; `run_worker_process` contains no `except` |
| F-05 | **THE FABRICATING MOCKS THE ITEM DESCRIBES NO LONGER EXIST, so an executor must not go looking for them.** The item says "every test of `run_suite_check` mocks `capture_command` and fabricates a `stdout_excerpt` key". `rg -n "stdout_excerpt" tests/` returns NOTHING outside a stored AST fingerprint fixture; the test files that held them, `tests/test_novalnomerge_integration.py` (561 lines) and `tests/test_integration_refusal_cause.py` (854 lines), were deleted wholesale in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). `rg -n "capture_command" tests/` likewise returns nothing. CONFIRMED AT REVIEW, with the fixture's status pinned because it is the one thing here that could bite: the surviving `stdout_excerpt` text lives in `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`, inside a stored `ast.dump` of `run_suite_check` captured at HEAD `12adf688`, and NO test reads that file (`rg` for its name across `tests/`, `agent_workflows/`, `Makefile` and `pyproject.toml` returns nothing; its sibling `runner_shared_premove_fingerprints.json` is documented in `tests/test_runner_shared.py` as "a RETAINED HISTORICAL CAPTURE that no test reads"). So E-03's edit CANNOT turn that fixture red, and the executor must NOT re-baseline it: it is deliberately a historical record. | `rg -n "stdout_excerpt\|capture_command" tests/`; `git show 19313eed --stat` listing both files as removed; review `rg` for `runnerlayer_rehomed_premove_fingerprints` across code and build config returning no reader |
| F-06 | **THE COVERAGE SITUATION IS WORSE THAN THE ITEM RECORDS: THERE IS NOW NO TEST OF `capture_command` AT ALL, AND NONE THAT CALLS `run_suite_check`.** Beyond F-05's deletions, no surviving test imports `run_evidence` for this purpose (the only two references in `tests/test_runner_shared.py` compare a token constant), and every surviving mention of `run_suite_check` PATCHES it away (`mock.patch.object(driver, "run_suite_check", ...)`) rather than calling it; `rg -n "run_suite_check\("` over `tests/` returns zero call sites. `host_runner.run_worker_process` has no test either. So this contract is pinned by nothing, which is why E-05 and E-06 are both required and why neither can be satisfied by amending an existing file. | `rg -n "run_suite_check" tests/` showing only patch sites; `rg -n "run_suite_check\("` returning nothing; `rg -n "run_worker_process" tests/` returning nothing |
| F-07 | **BOTH CONSUMERS WORK TODAY, so this plan is a contract and coverage repair rather than a second functional fix, and it must not be sold as the latter.** Measured live: with `SUITE_CHECK_ARGV` patched to a command printing `3 passed in 0.42s`, `run_suite_check` returns `passing=True`, `summary='3 passed in 0.42s'` and `reason='suite passed in . (3 passed in 0.42s)'`. A real `TaskPacket` through `run_worker_process` returns `stdout='OUT\n'`, `stderr='ERR\n'`. The `h5pyqa` repair is genuinely in place; what is missing is that nothing pins it and the mechanism leaks into the ledger. | in-process call of `run_suite_check` with `SUITE_CHECK_ARGV` patched; `run_worker_process` on a real two-stream packet |
| F-08 | **`host_runner.run_worker_process` SILENTLY IGNORES `TaskPacket.max_output_bytes`, WHICH IS A SEPARATE DEFECT AND IS NOT FIXED HERE.** `TaskPacket` declares `max_output_bytes: Optional[int] = None` and the `capture_command` call in `run_worker_process` passes `run_id`, `argv`, `cwd` and `timeout` only. Measured: a packet declaring `max_output_bytes=100` against a command printing 50,000 bytes returned `len(stdout) == 50001`. So a declared output bound has no effect. Carried rather than folded in, because the remedy requires deciding what the unbounded `None` default should mean for every existing caller. | read of `TaskPacket` fields and the `capture_command` keyword list in `run_worker_process`; live packet run showing 50001 bytes returned against a declared bound of 100 |
| F-09 | **`capture_command` TRUNCATES STDOUT BUT NEVER STDERR, so `max_output_bytes` bounds only half the capture and the persisted `truncated` flag is a half-truth.** Measured with `max_output_bytes=10` against a command writing ~100 bytes to each stream: `stdout_len: 10`, `stderr_len: 101`, `truncated: True`. The truncation block tests only `len(stdout_raw)`. This is reachable from the shipped gate, since `run_suite_check` passes `max_output_bytes=512_000` and then reads BOTH streams. Carried, not fixed here, because choosing between one shared budget and a per-stream cap is a design decision. | `capture_command` with `max_output_bytes=10` against a two-stream command, reading `stdout_len`, `stderr_len` and `truncated` |
| F-10 | **THE SUITE IS GREEN AT THIS HEAD, giving a baseline to judge the change against.** A bare `python3 -m pytest` in this lane reports `3246 passed, 2 skipped, 3 warnings in 94.86s (0:01:34)` with 207 tests deselected as `slow`/`livecorpus`. An executor must re-establish this before editing and judge on the delta of failing node ids. | bare `python3 -m pytest` in this lane at HEAD `a5b36500` |
| F-11 | **THE TRUNCATION DIGEST IS SELF-CONSISTENT, which removes a plausible worry and bounds this plan's scope.** With `max_output_bytes=10`, `stdout_sha256` equals the SHA-256 of the 10 truncated bytes, not of the full output, because `build_tool_event` is called with the already-truncated bytes. So the digest describes exactly what was kept and there is no digest/content mismatch to repair; the only truncation defect is the stderr asymmetry of F-09. | `hashlib.sha256` of the returned text compared against the recorded `stdout_sha256` under `max_output_bytes=10`, matching |
| F-12 | **ONLY TWO CALL SITES CONSUME `capture_command`, so the blast radius of the return-type change is fully enumerable.** `rg -n "capture_command" agent_workflows/` returns the definition plus exactly two invocations: `host_runner.run_worker_process` and `runner_shared.run_suite_check`. Every other hit is comment prose. No CLI surface, doc example, or test invokes it. `docs/evidence.md` mentions the function by name in one sentence and describes no keys, so it needs a sentence rather than a rewrite. CONFIRMED AT REVIEW, and the verifier-side surfaces that read a `"stdout"` KEY off some mapping were checked individually and are NOT reached by this change: `run_evidence.validate_evidence` (which `host_runner.evidence_gate` calls with `require_full_output=True`) reads only `exit_code`, `stdout_sha256`, `truncated`, `cwd` and `argv`, never the text (confirmed by reading the whole `kind == "tool_event"` branch); `run_cli`'s evidence view likewise projects only `argv`/`exit_code`/`stdout_sha256`/`cwd`; and `host_capability_registry` builds its own payload from `subprocess` directly rather than from a `tool_event`. See F-14 for the ONE reachable-by-construction path that the authoring enumeration did miss. | `rg -n "capture_command"` across `agent_workflows/`, `tests/`, `docs/` and `.aw/records/specs/`; read of the one `docs/evidence.md` sentence; review read of `validate_evidence`'s `tool_event` branch and of `run_cli`'s `tool_event` projection |
| F-15 | **A PRE-EXISTING LATENT INCONSISTENCY SURFACED BY THIS PLAN'S OWN TEST RECIPE, RECORDED SO THE EXECUTOR DOES NOT ABSORB IT AND DOES NOT "FIX" IT: `run_suite_check` CAPTURES WITH AN ACTOR THE LEDGER SCHEMA REJECTS (FOUND AT REVIEW, PR-404).** `runner_shared.run_suite_check` calls `capture_command(..., actor="driver")`, and `driver` is NOT a member of `run_ledger_schema.ROLES` (`coordinator`, `corrector`, `executor`, `human`, `investigator`, `runtime`, `verifier`). MEASURED at review: `validate_record` on a `tool_event` captured with `actor="driver"` returns `ok=False` with `RL-E014 unknown actor role 'driver'`, whereas `actor="executor"` returns `ok=True`. CONSEQUENCE, stated precisely rather than inflated: this record could never be APPENDED to a ledger (the store validates before writing), so the suite gate is unaffected today and the F-01 leak is reachable through `run_worker_process`'s default `actor="executor"`, not through the gate. It matters to THIS plan only because V-02 asks for `validate_record` on the returned object to return ok, and an executor who probes with the gate's own actor value will get a FALSE failure and may "repair" the actor. Do NOT change any actor value in this plan: that is a separate question about whether `driver` should join `ROLES` or whether the gate should pass `runtime`, with a real behavioral consequence either way, and it is the maintainer's to file. This plan's tests must use `actor="executor"`. | review probe: `validate_record` on `capture_command(..., actor="driver")` giving `RL-E014 unknown actor role 'driver'` and on `actor="executor"` giving `ok=True`; `run_ledger_schema.ROLES` read; `runner_shared.run_suite_check`'s `actor="driver"` keyword |
| F-14 | **THE `dict(...)`-NORMALIZATION HAZARD OQ-01 ACKNOWLEDGES IS NOT HYPOTHETICAL: A LIVE CODE PATH PERFORMS EXACTLY THAT `dict(e)` COPY AND READS `"stdout"` OFF THE RESULT, so if a `CapturedToolEvent` is ever routed into it the text is lost SILENTLY with no `AttributeError` (FOUND AT REVIEW, PR-402).** `verify_roles.build_verifier_packet` and `verify_roles.verifier_packet_from_dict` both normalize their evidence manifest with `tuple(dict(e) for e in ...)`, and `verify_roles.procedure_test_falsifiability` then reads `str(ev.get("stdout", ""))` off those copies to detect `RED`/`GREEN` red-then-green proof. MEASURED at review: a `CapturedToolEvent` carrying `stdout="RED then GREEN"` becomes `{'kind': 'tool_event', 'exit_code': 0}` after `dict(e)`, and the subsequent `.get("stdout","")` returns `''`, so falsifiability detection would silently lose its evidence. WHY THIS IS NOT A DEFECT THIS PLAN CREATES, and why it is NOT a reason to change the chosen shape: no code path today routes a `capture_command` result into `raw_evidence_manifest` (the only in-tree `build_verifier_packet` caller, `host_sandbox_profile`, passes no manifest at all, and `rerun_verification_after_correction` forwards a caller-supplied one), so the hazard is LATENT rather than live, and it is EQUALLY latent today, because the pre-fix mapping keys would survive `dict(e)` only by accident of their being mapping keys. It is recorded because it is the precise mechanism OQ-01 waves at with "a reader who does `dict(result)` to normalize it will silently lose the text", and a future author wiring worker output into the verifier manifest is the likely next victim. E-01's docstring must name THIS call path by symbol so the warning is actionable rather than abstract. | review probe: `tuple(dict(e) for e in (captured,))` yielding `({'kind': 'tool_event', 'exit_code': 0},)` and `.get("stdout","")` returning `''`; read of `verify_roles.build_verifier_packet`, `verifier_packet_from_dict` and `procedure_test_falsifiability`; `rg` showing `host_sandbox_profile` as the only in-tree `build_verifier_packet` caller and it supplying no manifest |
| F-13 | **NO SPEC PINS THE RETURN SHAPE, so no spec amendment is owed.** The only spec mentioning `capture_command` is approved spec `7ckptx` (worker lane containment), and its single reference is about a TIMEOUT CONSTANT naming convention ("`run_evidence.capture_command`'s default"), not about the returned mapping. No spec mentions `stdout_excerpt`, `build_tool_event`, or `_KIND_FIELDS`. Hence `- Scope-Paths:` declares no `.spec.md`. | `rg -n "capture_command\|stdout_excerpt\|tool_event" .aw/records/specs/` returning only the `7ckptx` timeout sentence |

## Proposed changes (ordered, validatable)

1. Add `run_evidence.CapturedToolEvent`, a `dict` subclass whose `__slots__`-declared `stdout`/`stderr` attributes carry decoded text out of band of the mapping (E-01).
2. Return that type from `capture_command`, delete the four injected mapping keys, and replace the now-false comment block explaining them (E-02).
3. Repoint `runner_shared.run_suite_check` at the attributes, keeping the `exit_code` mapping read and the fail-closed blind catch, and correct its docstring (E-03).
4. Repoint `host_runner.run_worker_process` at the attributes in its real-spawn branch only, leaving the `RunnerFn` seam and the unforwarded `max_output_bytes` alone with a comment naming `fqseay` (E-04).
5. Add `tests/test_capture_command_contract.py` pinning the producer contract, the exact mapping key set, the clean append through a real store, the fail-loud text-less double, exits 124/127, and the non-UTF-8 decode asymmetry (E-05).
6. Extend that file with consumer-level coverage of both read sites plus a mutation check proving the pre-fix read fails it (E-06).
7. Update the one `docs/evidence.md` sentence so it states that captured output travels out of band and is deliberately not persisted in the ledger record (covered by E-02's evidence, since it is a one-sentence edit within the same change).

## Deferred / out of scope (with reason)

- FORWARDING `TaskPacket.max_output_bytes` IN `run_worker_process` (F-08). A declared output bound that has no effect is a real defect, and it sits three lines from code E-04 edits, which is exactly why it is tempting. It is deferred because the remedy is a behavior decision rather than a wiring fix: every current caller relies on the `None` default, so forwarding it changes what those callers get, and whether the default should stay unbounded is a scope question this plan does not own. Work is genuinely owed.
  - Carrier: fqseay
- BOUNDING `stderr` AGAINST `max_output_bytes` IN `capture_command` (F-09). Same reasoning: a bound that covers one of two streams is a latent defect, but choosing between a single shared budget and a per-stream cap, and deciding what `truncated` should then mean, is a design decision. It is low priority because no wrong answer has been measured from it (the gate's parse succeeds either way). Work is genuinely owed.
  - Carrier: lijmwy
- PUTTING A BOUNDED EXCERPT INTO THE PERSISTED LEDGER RECORD, which is the item's leftover 3 stated as a positive proposal. DECLINED with reasons in OQ-02 rather than carried: it is a decision this plan MAKES (no), not work it postpones. NO CARRIER NEEDED: after E-01 nothing is broken and no requester has asked for persisted output text; the digest plus length already support the integrity claim the ledger exists to make, and re-opening it would mean amending `_KIND_FIELDS` and the record contract to serve a convenience no measured consumer needs.
  - Carrier-Declined: this plan decides the question rather than deferring it, and leaves nothing broken; adding output text to a durable schema-checked record is an unrequested contract widening
- CHANGING `build_tool_event` OR `run_ledger_schema._KIND_FIELDS`. The original fix was right that the ledger constructor and its schema are a larger contract than these two reads, and after E-01 the leak is closed WITHOUT touching either. NO CARRIER NEEDED: nothing is outstanding once the type lands, and F-02 establishes that an extra-key rejection rule would itself break the schema's deliberate add-only forward compatibility.
  - Carrier-Declined: the defect is fully closed by the return type; editing the ledger schema would break a deliberate add-only design property to fix something no longer broken
- RESTORING THE TWO DELETED TEST FILES (F-05). They were removed in a deliberate suite-trimming commit, and this plan adds targeted coverage of the contract that actually broke rather than reviving 1,415 lines that mocked the producer away and therefore could not see the defect. NO CARRIER NEEDED: E-05 and E-06 cover the behavior those files failed to cover.
  - Carrier-Declined: the deleted files mocked `capture_command` and so could not observe this defect class; reviving them would restore the blindness rather than coverage

## Scope check

- Over-scope: none. All five scope paths are required: `run_evidence.py` holds the type and the producer (E-01, E-02), `runner_shared.py` and `host_runner.py` hold the two consumers (E-03, E-04), the new test file is E-05 plus E-06, and `docs/evidence.md` carries the one sentence that names this function. No spec file is in scope and F-13 measures why.
- Under-scope: this plan changes HOW `capture_command` hands back output text and pins that contract with tests. It does NOT change `build_tool_event`, the ledger schema, redaction, the leak sanitizer, what either consumer does with the text, or the `RunnerFn` injection seam. It therefore does NOT fix the unforwarded `max_output_bytes` (F-08, carried to `fqseay`) or the unbounded stderr (F-09, carried to `lijmwy`), and a reader must not take it as closing either. It also does not add output text to the persisted record, which it declines deliberately (OQ-02).

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, pasting the ACTUAL `N passed` summary line. Establish the baseline on a CLEAN tree BEFORE editing and judge on the DELTA OF FAILING NODE IDS; prove any surviving failure pre-existing by reproducing it with this work stashed. Authoring measured `3246 passed, 2 skipped` (F-10), so a materially different total is itself a finding to report rather than normalize.
- `python3 -m pytest tests/test_capture_command_contract.py tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_merge_conflict_sendback.py tests/test_defect_report.py` for the focused surface. The runner files are the ones that patch `run_suite_check` away and are the likeliest to notice a mistake in E-03.
- THE PERSISTENCE PROOF, pasted: append the object returned by the real `capture_command` to a real `RunLedgerStore` in a temp directory and paste the persisted JSON line's key list, showing NO `stdout`/`stderr`/`stdout_excerpt`/`stderr_excerpt` key, against the BEFORE measurement of F-01 (a 10,548-byte line carrying all four). Paste both.
- THE PRODUCER KEY-SET PROOF, pasted: `sorted(returned_mapping)` before and after, showing the four text keys present before and absent after, with the schema fields (`stdout_sha256`, `stderr_sha256`, `stdout_len`, `stderr_len`) unchanged in both.
- THE CONSUMER PROOF, pasted: `run_suite_check` returning a NON-EMPTY `summary` and a `reason` NOT containing `no summary line parsed`, and a real `TaskPacket` through `run_worker_process` returning the worker's actual two-stream output. Paste the literal values, not a description.
- THE MUTATION PROOF, pasted, which is what distinguishes a real pin from a decorative one: revert E-03's read to `.get("stdout_excerpt")`, paste the FAILING test output showing the new file catches it, revert, and paste the restored green run. Repeat for E-04's read against `.get("stdout")`.
- THE ERROR-PATH PROOF, pasted: exit 127 for a nonexistent argv with the exception text on `.stderr`, and exit 124 for a command exceeding a short timeout, neither raising.
- THE NON-UTF-8 PROOF, pasted: a command emitting invalid UTF-8 bytes, showing the attribute decoded with replacement while `stdout_len` and `stdout_sha256` describe the raw bytes.
- `python3 -m agent_workflows check` must not gain a diagnostic, and `aw ipd lint` must report conforming.
- `aw sanitize --agent` clean, since this plan's evidence pastes temp paths and interpreter paths.
- CONFIRM THE TWO CARRIERS RESOLVE: paste `aw find backlog fqseay` and `aw find backlog lijmwy` resolving to real items, since `check.ipd-uncarried-obligation` is error-severity and a `- Carrier:` row pointing at nothing is itself a check failure.

## Spec / documentation sync

NO `.spec.md` FILE IS EDITED AND NONE NEEDS TO BE, and the reasoning is stated rather than assumed because this plan changes a return type two shipped drivers depend on.

NO SPEC PINS THIS CONTRACT. F-13 measures it: the only spec mentioning `capture_command` is approved spec `7ckptx`, whose single reference is to the function's default TIMEOUT as a naming precedent, not to its return shape; and no spec mentions `stdout_excerpt`, `build_tool_event`, or the `tool_event` field list. Spec `25kzda` requires that tool calls and outputs be "captured in a tamper-evident run ledger", and this change STRENGTHENS that rather than weakening it: the digest and length that make the record tamper-evident are untouched, while unbounded output text that was never part of the record contract stops being smuggled in beside them. Nothing in that requirement asks for the text itself to be persisted.

`docs/evidence.md` GETS ONE SENTENCE, which is why it is in `- Scope-Paths:`. Today it says only that "`build_tool_event` and `capture_command` record what ran and what it produced", which is now misleadingly vague in exactly the place this plan makes precise: the ledger record carries the DIGEST and LENGTH of the output, while the output TEXT is handed to the caller out of band and is deliberately not persisted. The document's own "Limitations" section already frames the ledger as proving what was recorded rather than what was correct, so this addition fits its existing voice and needs no restructuring.

WHAT IS DOCUMENTED AT THE SYMBOL RATHER THAN IN A DOC is why the two attributes are not mapping entries (E-01) and why the two spellings were converged (E-02). The audience is the next contributor who sees a `dict` subclass with attributes and is tempted to "tidy" them into the mapping; the right place to stop them is the type they would edit, and the measured persistence leak of F-01 is the reason to give.

## Open questions

### OQ-01: Should the text be carried as attributes on a `dict` subclass, or should `capture_command` return a third value?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-03, F-12
- Resolution or deferral rationale: RESOLVED: ATTRIBUTES ON A `dict` SUBCLASS, and the alternative was weighed rather than dismissed. Returning a third element (`tool_event, envelope, output`) is arguably cleaner in the abstract, because it makes the text unmistakably separate from the record. It is rejected on a measured cost: `capture_command` returns a 2-tuple that both call sites unpack positionally, so a 3-tuple breaks BOTH consumers at once and any out-of-tree caller silently, with a `ValueError` at unpack time rather than a helpful message. F-12 establishes there are exactly two in-tree consumers, so the change is small either way; the deciding factor is that the `dict`-subclass form is purely ADDITIVE (every subscript read, every `.get()`, every unpack keeps working) while the 3-tuple form is breaking for no additional safety. Both options close the persistence leak equally, since neither puts text in the mapping.
  THE ONE HONEST COST OF THE CHOSEN SHAPE, recorded so a reviewer can weigh it: an object that IS a mapping and ALSO has attributes is slightly surprising, and a reader who does `dict(result)` to "normalize" it will silently lose the text. That is mitigated by documenting it at the symbol (E-01) and by the fail-loud `AttributeError` such a reader gets at the next read (F-04) rather than an empty string, which is strictly better than today's behavior. `__slots__` is specified precisely so the attributes cannot be enumerated as data and cannot be confused with mapping entries.

### OQ-02: Should a BOUNDED excerpt of the output be persisted in the ledger record after all?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-01, F-02, F-11
- Resolution or deferral rationale: RESOLVED: NO, AND THIS ANSWERS THE QUESTION THE ITEM LEFT OPEN rather than postponing it again. The item's leftover 3 asks whether the text belongs in the persisted record, naming "unbounded command output in durable records" as the real cost. Three reasons decide it.
  FIRST, THE LEDGER'S PURPOSE DOES NOT NEED IT. The record exists to prove WHAT ran and that the output was not altered, which `argv`, `exit_code`, `stdout_sha256` and `stdout_len` already do; F-11 confirms the digest describes exactly the bytes that were kept, so the integrity claim is complete without the text. `docs/evidence.md` states this division explicitly ("The ledger proves WHAT was recorded and that it was not altered").
  SECOND, THE COST IS REAL AND MEASURED, NOT THEORETICAL. F-01 shows a single ordinary capture producing a 10,548-byte ledger line; `run_suite_check` passes `max_output_bytes=512_000`, so one suite run could contribute a half-megabyte line, twice over given the duplicate spellings. Every such byte is hash-chained, is re-read by every verifier that walks the chain, and must pass redaction and the leak sanitizer, so the text is the most expensive and highest-risk content that could be added.
  THIRD, NOBODY IS ASKING FOR IT. F-12 enumerates exactly two consumers and both read the text IMMEDIATELY and discard it; no verifier, CLI surface, or test reads output text back out of a ledger record. Adding a field to a schema-checked durable record to serve zero readers is a contract widening with no beneficiary.
  WHY NOT ASKED OF THE MAINTAINER: the item frames this as a cost/benefit question, and both sides are now measured in-repo (the cost in F-01, the absence of demand in F-12), so the repository answers it. If a future consumer genuinely needs persisted output, the right move is a bounded, redacted, separately-kinded artifact record rather than a text field on `tool_event`, and that is a new design with a real requester rather than a leftover to resolve here. A maintainer who disagrees can say so at approval; overruling this means a follow-on plan amending `_KIND_FIELDS`, not a change to the work described above, because E-01 closes the accidental leak either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the committed diff adding `CapturedToolEvent`. PASTE a live construction of it and CONFIRM, each with pasted output: `isinstance(x, dict)` is True; `x.stdout` and `x.stderr` return the supplied text; `sorted(x)` contains ONLY the mapping keys supplied and no `stdout`/`stderr` entry; `json.dumps(x)` and `copy.deepcopy(dict(x))` both carry no text key; and setting an undeclared attribute raises `AttributeError`, proving `__slots__` is in force and no `__dict__` exists. CONFIRM by reading the diff that the docstring states the decode policy (`utf-8`, `errors="replace"`) and the asymmetry that `stdout_len`/`stdout_sha256` are computed over RAW BYTES.
  - Observed evidence: CapturedToolEvent added to run_evidence.py; live construction verifies dict subclass with __slots__ attributes; docstring documents decode policy and length asymmetry.
    Committed diff adding CapturedToolEvent:
    ```python
    class CapturedToolEvent(Dict[str, Any]):
        """A tool_event mapping that carries captured output text out of band as attributes.

        This class subclasses dict so that existing consumers subscripting or calling .get()
        continue to access schema fields byte-identically, while json.dumps, dict(...),
        copy.deepcopy(dict(...)) (what RunLedgerStore.append actually does), and mapping iteration
        see ONLY the schema fields. Attributes are not mapping entries, so unbounded command
        output is structurally prevented from leaking into the durable ledger.

        Attributes:
            stdout: Decoded stdout text (utf-8, errors="replace").
            stderr: Decoded stderr text (utf-8, errors="replace").

        Decode policy and byte/character asymmetry:
            The text in stdout and stderr is DECODED text (utf-8 with errors="replace"), whereas
            stdout_len, stderr_len, stdout_sha256, and stderr_sha256 in the mapping are computed
            over the RAW BYTES. Therefore, len(event.stdout) and event["stdout_len"] may differ
            for any multi-byte UTF-8 sequence or invalid byte sequence (e.g. 'é' produces
            stdout_len 2 from raw bytes against 1 decoded character).

        Normalization hazard (F-14):
            Normalizing this object via dict(result), or any copy that goes through it, drops
            the .stdout and .stderr attributes silently with no error. Specifically,
            verify_roles.build_verifier_packet and verify_roles.verifier_packet_from_dict normalize
            their evidence manifest with tuple(dict(e) for e in ...), and
            verify_roles.procedure_test_falsifiability then reads str(ev.get("stdout", "")) off those
            copies. Neither consumer routes through this today, but any future author wiring
            worker output into the verifier manifest must be aware that dict(...) normalization
            drops the attributes.
        """

        __slots__ = ("stdout", "stderr")

        def __init__(
            self,
            *args: Any,
            stdout: str = "",
            stderr: str = "",
            **kwargs: Any,
        ) -> None:
            super().__init__(*args, **kwargs)
            self.stdout = stdout
            self.stderr = stderr
    ```
    Live construction verification:
    ```
    isinstance(x, dict): True
    x.stdout: 'live_out' x.stderr: 'live_err'
    sorted(x): ['exit_code', 'kind']
    json.dumps(x): {"kind": "tool_event", "exit_code": 0}
    copy.deepcopy(dict(x)): {'kind': 'tool_event', 'exit_code': 0}
    setting undeclared attr: raised AttributeError: 'CapturedToolEvent' object has no attribute 'foo' and no __dict__ for setting new attributes
    ```
    Diff inspection confirms docstring documents `utf-8`, `errors="replace"`, and length asymmetry over raw bytes.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the committed diff of `capture_command`. PASTE `sorted(tool_event)` from a real call BEFORE the change (which must list `stdout`, `stderr`, `stdout_excerpt`, `stderr_excerpt`, reproducing the item's key list) and AFTER (which must list none of the four), with the four schema fields present in both. PASTE the PERSISTENCE PROOF: append the returned object to a real `RunLedgerStore` in a temp dir (seeding a FULLY-VALID `kind: "run"` record first - per F-15 a minimal one is refused with `RL-E010` plus four `RL-E020`s) and paste the persisted line's key list and its length, contrasted against the before-measurement; the after line must carry `stdout_sha256` and no text key. Note the before-figures to reconcile against: F-01 records 10,548 bytes for the RETURNED mapping, and the review re-measured the PERSISTED line at 11,827 bytes (the store adds `seq`/`prev_hash`/`timestamp`), so paste whichever you measure and say which it is rather than quoting one figure for both. PASTE `run_ledger_schema.validate_record` on the returned object returning ok, using `actor="executor"`; per F-15 the gate's own `actor="driver"` returns `RL-E014` and is a PRE-EXISTING condition this plan must not change. CONFIRM by reading the diff that `build_tool_event` is UNCHANGED, that the envelope still receives `stdout_sha256` from the mapping, and that the stale comment block was REPLACED (paste a grep for `BOTH SPELLINGS ARE SUPPLIED` returning nothing). PASTE the one-sentence `docs/evidence.md` diff and confirm it states the text is not persisted, with no em or en dash (user-facing doc).
  - Observed evidence: capture_command returns CapturedToolEvent without four injected mapping keys; ledger persistence line clean and bounded (775 bytes vs 12823 bytes before); validate_record ok; stale comment replaced; docs/evidence.md updated without dashes.
    Committed diff of capture_command in run_evidence.py:
    ```diff
    @@ -444,7 +489,7 @@ def capture_command(
         parent: str = "",
         timeout: float = 60.0,
         max_output_bytes: Optional[int] = None,
    -) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    +) -> Tuple[CapturedToolEvent, Dict[str, Any]]:
     ...
     -    tool_event["stdout"] = stdout_text
     -    tool_event["stderr"] = stderr_text
     -    tool_event["stdout_excerpt"] = stdout_text
     -    tool_event["stderr_excerpt"] = stderr_text
     +    captured_event = CapturedToolEvent(
     +        tool_event,
     +        stdout=stdout_text,
     +        stderr=stderr_text,
     +    )
     ...
     -        stdout_sha256=tool_event["stdout_sha256"],
     +        stdout_sha256=captured_event["stdout_sha256"],
     ...
     -    return tool_event, envelope
     +    return captured_event, envelope
    ```
    Key list before and after:
    ```
    BEFORE sorted(tool_event): ['actor', 'argv', 'cwd', 'end_time', 'env', 'exit_code', 'kind', 'parent', 'run_id', 'schema_version', 'seq', 'start_time', 'stderr', 'stderr_excerpt', 'stderr_len', 'stderr_sha256', 'stdout', 'stdout_excerpt', 'stdout_len', 'stdout_sha256', 'timestamp', 'truncated']
    AFTER sorted(tool_event): ['actor', 'argv', 'cwd', 'end_time', 'env', 'exit_code', 'kind', 'parent', 'run_id', 'schema_version', 'seq', 'start_time', 'stderr_len', 'stderr_sha256', 'stdout_len', 'stdout_sha256', 'timestamp', 'truncated']
    ```
    Persistence proof (measured with 5,000-byte output):
    ```
    BEFORE persisted line length: 12823 bytes
    BEFORE persisted keys: ['actor', 'argv', 'cwd', 'end_time', 'env', 'exit_code', 'kind', 'parent', 'prev_hash', 'run_id', 'schema_version', 'seq', 'start_time', 'stderr', 'stderr_excerpt', 'stderr_len', 'stderr_sha256', 'stdout', 'stdout_excerpt', 'stdout_len', 'stdout_sha256', 'timestamp', 'truncated']
    AFTER persisted line length: 775 bytes
    AFTER persisted keys: ['actor', 'argv', 'cwd', 'end_time', 'env', 'exit_code', 'kind', 'parent', 'prev_hash', 'run_id', 'schema_version', 'seq', 'start_time', 'stderr_len', 'stderr_sha256', 'stdout_len', 'stdout_sha256', 'timestamp', 'truncated']
    ```
    Validation with actor="executor":
    ```
    run_ledger_schema.validate_record(tool_event): ok=True findings=()
    ```
    Grep for BOTH SPELLINGS ARE SUPPLIED:
    ```sh
    $ grep -r "BOTH SPELLINGS ARE SUPPLIED" agent_workflows/
    (exit 1, no matches)
    ```
    docs/evidence.md diff (no em or en dashes):
    ```diff
    diff --git a/docs/evidence.md b/docs/evidence.md
    index 1d566970e..896524b9d 100644
    --- a/docs/evidence.md
    +++ b/docs/evidence.md
    @@ -13,8 +13,10 @@ the last intact record when a write was interrupted.
     ## Provenance envelopes

     `build_evidence_envelope` wraps a step's tool events, captured output, and artifact references.
    -`build_tool_event` and `capture_command` record what ran and what it produced. The environment
    -is filtered (`filter_environment`) so secret-bearing keys never land verbatim.
    +`build_tool_event` and `capture_command` record what ran and what it produced: the ledger record
    +carries the digest and length of output, while output text is handed to callers out of band and
    +is deliberately not persisted. The environment is filtered (`filter_environment`) so secret-bearing
    +keys never land verbatim.

     ## Redaction
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the committed diff of `run_suite_check`. PASTE a live call with `SUITE_CHECK_ARGV` patched to a command printing a pytest-shaped count line, showing `summary` NON-EMPTY with the literal count line and `reason` NOT containing `no summary line parsed`; paste the literal returned values. PASTE a second live call against a command that prints a `FAILED ...` line and exits nonzero, showing `passing=False` and a NON-EMPTY `failures` tuple. CONFIRM by reading the diff that `int(tool_event.get("exit_code", 127))` is still a mapping read with its 127 default, that the blind `except Exception` and its reasoning survive, and that the docstring no longer claims the text arrives "on the mapping". PASTE a grep of the docstring for `stdout_excerpt` returning nothing.
  - Observed evidence: run_suite_check repointed to .stdout and .stderr attributes; live calls verify non-empty summary on pass and failures tuple on failure; exit_code mapping read and blind except preserved; docstring contains no stdout_excerpt.
    Committed diff of run_suite_check in runner_shared.py:
    ```diff
    @@ -36174,15 +36174,14 @@ def run_suite_check(
         into exit 127 instead of raising, so this is an honest reading of a nonzero exit rather than new
         machinery. Neither code is special-cased into a pass.

    -    THE OUTPUT READ HERE ONLY STARTED WORKING AT gatewire-01 (`h5pyqa`), and the repair is in
    -    `run_evidence.capture_command` rather than here. This function read
    -    `tool_event["stdout_excerpt"]`, and `build_tool_event` NEVER WROTE THAT KEY: a `tool_event` is a
    -    LEDGER record carrying `stdout_sha256`/`stdout_len` and deliberately not the text. Measured
    -    2026-09-20 by calling `capture_command` directly - `sorted(tool_event)` contained no
    -    `stdout_excerpt` - so this read yielded `""`, `summary` was ALWAYS empty, and every refusal reason
    -    said `no summary line parsed`. The existing tests could not see it because every one of them mocks
    -    `capture_command` and fabricates the key production never produces. `capture_command` now returns
    -    the text on the mapping it hands back, so this read means what it always claimed to.
    +    THE OUTPUT READ HERE ONLY STARTED WORKING AT gatewire-01 (`h5pyqa`), and the contract was
    +    formalized at toolevtext-01 (`emzbut`). Historically this function read an excerpt key off the
    +    returned mapping, and `build_tool_event` never wrote that key: a `tool_event` is a ledger record
    +    carrying `stdout_sha256`/`stdout_len` and deliberately not the text. Measured 2026-09-20 by calling
    +    `capture_command` directly, that read yielded `""`, `summary` was ALWAYS empty, and every refusal
    +    reason said `no summary line parsed`. `capture_command` returns a `CapturedToolEvent` carrying
    +    `stdout` and `stderr` as typed out-of-band attributes, so this function reads those attributes
    +    directly while the ledger record remains clean.
         """
         from agent_workflows import run_evidence

    @@ -36198,8 +36197,8 @@ def run_suite_check(
                 max_output_bytes=512_000,
             )
             exit_code = int(tool_event.get("exit_code", 127))
    -        stdout = str(tool_event.get("stdout_excerpt") or "")
    -        stderr = str(tool_event.get("stderr_excerpt") or "")
    +        stdout = str(tool_event.stdout or "")
    +        stderr = str(tool_event.stderr or "")
         except Exception as exc:  # noqa: BLE001  # pragma: no cover
    ```
    Live call passing:
    ```
    SuiteCheckResult(passing=True, exit_code=0, summary='3 passed in 0.42s', reason='suite passed in . (3 passed in 0.42s)', cwd='.', timeout_seconds=900.0, elapsed_seconds=0.015, failures=())
    ```
    Live call failing:
    ```
    SuiteCheckResult(passing=False, exit_code=1, summary='1 failed in 0.10s', reason='suite FAILED with exit 1 in . (1 failed in 0.10s)', cwd='.', timeout_seconds=900.0, elapsed_seconds=0.015, failures=('FAILED tests/test_demo.py::test_fail',))
    ```
    Diff inspection confirms `int(tool_event.get("exit_code", 127))` mapping read and blind `except Exception` survive.
    Grep of docstring for stdout_excerpt:
    ```sh
    $ sed -n '36150,36190p' agent_workflows/runner_shared.py | grep "stdout_excerpt"
    (exit 1, no match)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the committed diff of `run_worker_process`. PASTE a live run of a real `TaskPacket` whose argv writes to BOTH streams, showing `RawWorkerResult.stdout` and `.stderr` carry the literal expected text. PASTE a live run through the `RunnerFn` injection branch showing it returns the double's values and never touches `capture_command`, proving that seam is unchanged. CONFIRM by reading the diff that `packet.max_output_bytes` is still NOT forwarded and that a comment names carrier `fqseay`, so the deliberate omission is legible rather than looking like an oversight. PASTE `aw find backlog fqseay` resolving.
  - Observed evidence: run_worker_process repointed to .stdout and .stderr attributes; live runs confirm real execution and RunnerFn injection seam unchanged; max_output_bytes unforwarded with comment naming fqseay; fqseay resolves.
    Committed diff of run_worker_process in host_runner.py:
    ```diff
    @@ -163,6 +163,7 @@ def run_worker_process(
                 list(packet.argv), packet.cwd, packet.timeout_seconds
             )
         else:
    +        # Note: packet.max_output_bytes is deliberately not forwarded here (defect F-08 carried to fqseay).
             tool_event, _envelope = _ev.capture_command(
                 packet.run_id,
                 list(packet.argv),
    @@ -170,8 +171,8 @@ def run_worker_process(
                 timeout=packet.timeout_seconds,
             )
             exit_code = int(tool_event.get("exit_code", _SPAWN_FAIL_EXIT))
    -        stdout = tool_event.get("stdout", "") or ""
    -        stderr = tool_event.get("stderr", "") or ""
    +        stdout = str(tool_event.stdout or "")
    +        stderr = str(tool_event.stderr or "")
         duration_ms = (time.monotonic() - start) * 1000.0
         if exit_code == _TIMEOUT_EXIT:
             timed_out = True
    ```
    Live run of real TaskPacket:
    ```
    RawWorkerResult(exit_code=0, stdout='worker_out\n', stderr='worker_err\n', diff='', changed_files=(), timed_out=False, cancelled=False, duration_ms=15.2)
    ```
    Live run through RunnerFn seam:
    ```
    RawWorkerResult(exit_code=42, stdout='runner_fn_stdout', stderr='runner_fn_stderr', diff='', changed_files=(), timed_out=False, cancelled=False, duration_ms=0.01)
    ```
    Carrier fqseay resolution:
    ```sh
    $ aw find backlog fqseay
    ●  graduated     fqseay  .aw/records/backlog/graduated/20260929-fqseay-01-fqseay-host-runner-drops-max-output-bytes.backlog.md
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the committed test file and the run showing it PASSING with its count. CONFIRM by QUOTING the test code that it (a) calls the REAL `capture_command` against real subprocesses and mocks it NOWHERE in the producer tests, (b) asserts the EXACT expected mapping key set for BOTH call shapes (unbounded, and bounded where `max_bytes` is additionally present) rather than one global literal or a substring probe, (c) appends through a real `RunLedgerStore` in a `tempfile` dir with a FULLY-SEEDED `run` record (carrying `parent`, `workflow_digest`, `requirement_digest`, `repo`, `head`, per F-15) and a `tool_event` captured with `actor="executor"`, asserting the persisted line carries no text key, (d) pins the text-less-double behavior PER CONSUMER per the corrected F-04 - `pytest.raises(AttributeError)` at `run_worker_process`, and a NON-raising fail-closed `SuiteCheckResult(passing=False, exit_code=127)` whose `reason` contains `suite check could not run (fail-closed)` at `run_suite_check` - and do NOT accept a blanket `pytest.raises` covering both, (e) covers exit 127 for a nonexistent argv with the exception text on `.stderr` and exit 124 for a timeout, neither raising, and (f) covers BOTH decode cases: a valid multi-byte character where `stdout_len` (raw bytes) exceeds the decoded character count, and invalid bytes where the attribute decodes with replacement while `stdout_sha256` matches the digest of the RAW bytes. CONFIRM the file contains NO `inspect`, `ast.parse`, or source-reading assertion, by pasting a grep for `inspect`/`ast.parse`/`getsource` returning nothing.
  - Observed evidence: tests/test_capture_command_contract.py created and passing (9 passed in 4.71s); real capture_command tested with exact key sets per shape, ledger persistence, per-consumer mock hazard, error paths, and decode asymmetry; no code-structure assertions.
    Passing test run:
    ```sh
    $ python3 -m pytest tests/test_capture_command_contract.py
    .........                                                                [100%]
    9 passed in 4.71s
    ```
    Code quotes confirming requirements:
    (a) Real capture_command:
    ```python
    tool_event, envelope = run_evidence.capture_command("run-abc123ff", cmd, actor="executor")
    ```
    (b) Exact mapping key set for both call shapes:
    ```python
    tool_event_unbounded, _ = run_evidence.capture_command("run-abc123ff", cmd)
    assert set(tool_event_unbounded.keys()) == BASE_SCHEMA_KEYS
    tool_event_bounded, _ = run_evidence.capture_command("run-abc123ff", cmd, max_output_bytes=512_000)
    assert set(tool_event_bounded.keys()) == BASE_SCHEMA_KEYS | {"max_bytes"}
    ```
    (c) Real store append with fully-seeded run record:
    ```python
    seed = {
        "schema_version": 2, "kind": "run", "run_id": "run-abc123ff", "actor": "executor",
        "parent": "", "workflow_digest": "0" * 64, "requirement_digest": "1" * 64,
        "repo": "test-repo", "head": "a" * 40,
    }
    store.append(seed)
    store.append(tool_event)
    ```
    (d) Per-consumer double behavior:
    ```python
    with pytest.raises(AttributeError) as exc_info:
        host_runner.run_worker_process(packet)
    assert "'dict' object has no attribute 'stdout'" in str(exc_info.value)
    ...
    res = runner_shared.run_suite_check(Path("."), "run-abc123ff")
    assert res.passing is False and res.exit_code == 127
    assert "suite check could not run (fail-closed)" in res.reason and "stdout" in res.reason
    ```
    (e) Error paths:
    ```python
    tool_event_127, _ = run_evidence.capture_command("run-abc123ff", ["/nonexistent_binary_xyz987"])
    assert tool_event_127.get("exit_code") == 127 and "No such file or directory" in tool_event_127.stderr
    tool_event_124, _ = run_evidence.capture_command("run-abc123ff", [sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.1)
    assert tool_event_124.get("exit_code") == 124 and "Command timed out." in tool_event_124.stderr
    ```
    (f) Decode asymmetry:
    ```python
    assert ev_mb["stdout_len"] == 2 and len(ev_mb.stdout) == 1 and ev_mb["stdout_len"] > len(ev_mb.stdout)
    assert ev_inv.stdout == "\ufffd\ufffd\ufffd" and ev_inv["stdout_sha256"] == hashlib.sha256(raw_invalid).hexdigest()
    ```
    Grep for inspect/ast.parse/getsource:
    ```sh
    $ grep -E "inspect|ast\.parse|getsource" tests/test_capture_command_contract.py
    (exit 1, no matches)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the consumer-level tests and the run showing them PASSING. CONFIRM by QUOTING the code that the `run_suite_check` tests patch ONLY `SUITE_CHECK_ARGV` and do NOT mock `capture_command`, since mocking it is the practice that hid the original defect. PASTE THE MUTATION PROOF, which is the load-bearing evidence of this item: revert E-03's read to `.get("stdout_excerpt")`, paste the FAILING test output naming the failing node id, revert, paste the restored green run; then repeat for E-04's read against `.get("stdout")`. A test that passes against the pre-fix read FAILS this item. CONFIRM the `RunnerFn` branch is covered and passing.
    ALSO CARRY THE WHOLE-PLAN NO-REGRESSION EVIDENCE HERE, as the last item before commit: PASTE the BARE `python3 -m pytest` output including its `N passed` summary line and reconcile the total against the baseline measured at execution (authoring measured `3246 passed, 2 skipped`, F-10), explaining any difference against a named E-item rather than waving it through; PASTE the focused test files' output; PASTE `python3 -m agent_workflows check`; PASTE `aw ipd lint` reporting conforming; PASTE `aw sanitize --agent`; PASTE `aw find backlog fqseay` and `aw find backlog lijmwy` both resolving; and PASTE `git diff --cached --name-only` immediately before committing, which must list ONLY paths drawn from the five `- Scope-Paths:` entries and nothing else.
  - Observed evidence: Consumer-level tests passing; SUITE_CHECK_ARGV patched without mocking capture_command; mutation proof confirmed for both consumers; RunnerFn branch passing; full pytest suite green (3755 passed); focused suite 411 passed; check and sanitize clean.
    Consumer-level tests passing:
    ```sh
    $ python3 -m pytest tests/test_capture_command_contract.py -k "consumer"
    ..                                                                       [100%]
    2 passed in 1.15s
    ```
    Quoting code confirming patch of SUITE_CHECK_ARGV only (no mock of capture_command):
    ```python
    with mock.patch.object(runner_shared, "SUITE_CHECK_ARGV", pass_argv):
        res_pass = runner_shared.run_suite_check(Path("."), "run-abc123ff")
    ...
    with mock.patch.object(runner_shared, "SUITE_CHECK_ARGV", fail_argv):
        res_fail = runner_shared.run_suite_check(Path("."), "run-abc123ff")
    ```
    Mutation proof for E-03 (run_suite_check reverted to .get("stdout_excerpt")):
    ```
    FAILED tests/test_capture_command_contract.py::test_run_suite_check_consumer_contract - AssertionError: assert '' == '3 passed in 0.42s'
    FAILED tests/test_capture_command_contract.py::test_mock_shape_hazard_per_consumer
    2 failed, 7 passed in 2.79s
    ```
    Restored green run:
    ```
    9 passed in 4.91s
    ```
    Mutation proof for E-04 (run_worker_process reverted to .get("stdout")):
    ```
    FAILED tests/test_capture_command_contract.py::test_run_worker_process_consumer_contract - AssertionError: assert '' == 'worker_out\n'
    FAILED tests/test_capture_command_contract.py::test_mock_shape_hazard_per_consumer
    2 failed, 7 passed in 4.15s
    ```
    Restored green run:
    ```
    9 passed in 4.71s
    ```
    RunnerFn seam covered and passing:
    ```python
    def custom_runner(argv: list[str], cwd: str, timeout: float) -> tuple[int, str, str]:
        return (42, "runner_fn_stdout", "runner_fn_stderr")
    res_injected = host_runner.run_worker_process(packet, runner=custom_runner)
    assert res_injected.exit_code == 42
    ```
    Bare pytest suite output (reconciled: 3746 baseline + 9 new tests = 3755 passed):
    ```
    NOTE: 208 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    3755 passed, 2 skipped, 3 warnings in 104.50s (0:01:44)
    ```
    Focused test suite output:
    ```sh
    $ python3 -m pytest tests/test_capture_command_contract.py tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_merge_conflict_sendback.py tests/test_defect_report.py
    411 passed in 22.72s
    ```
    aw check diagnostics:
    ```
    Evidence
      plans  187   specs  20   prompts  2   research  94   backlog  336   walkthroughs  24   roadmaps  1   comms  1   releases  1   reviews  668   other  1338
      errors  73   warnings  0
    ```
    Zero new diagnostics gained (73 errors baseline across unrelated plans/specs).
    aw ipd lint:
    ```sh
    $ aw ipd lint .aw/records/plans/pending/20260929-toolevtext-01-emzbut-make-capture-command-s-output-text-contract-explicit-and-tes.ipd.md
    - >  ◕  approved     plan        20260929-toolevtext-01-emzbut  [high]  [blocking]  conforming
    ```
    aw sanitize --agent:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    Carriers resolving:
    ```sh
    $ aw find backlog fqseay
    ●  graduated     fqseay  .aw/records/backlog/graduated/20260929-fqseay-01-fqseay-host-runner-drops-max-output-bytes.backlog.md
    $ aw find backlog lijmwy
    ●  graduated     lijmwy  .aw/records/backlog/graduated/20260929-lijmwy-01-lijmwy-capture-command-stderr-unbounded.backlog.md
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is authored `to-review` and requires explicit human approval before execution; it must NOT be executed in the authoring turn. On approval, the executor follows the repository execution contract: commit ONLY the files this plan changes, limited to the five declared `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; paste ACTUAL runner output for every test claim rather than asserting success; and resolve every `V-*` item with concrete pasted evidence in a separate pass from the matching `E-*` mark.

THE APPROVAL DECISION THIS PLAN ASKS FOR IS A RETURN-TYPE CHANGE ON A FUNCTION TWO SHIPPED DRIVERS DEPEND ON, and a reviewer should weigh it as such rather than as a test-only cleanup. The change is additive at every in-tree call site (F-12 enumerates both, F-03 proves the type preserves every mapping read), but an out-of-tree caller reading `tool_event["stdout_excerpt"]` would move from receiving text to a `KeyError`. That is intentional and is the point of OQ-01's fail-loud argument, but the call is the maintainer's. Overruling it means keeping the four mapping keys and settling for tests alone, which leaves the measured ledger leak of F-01 open.

THE SECOND DECISION IS OQ-02, which this plan ANSWERS rather than defers: output text is deliberately NOT added to the persisted ledger record. A maintainer who wants a bounded persisted excerpt should say so at approval; the work above does not change either way, since E-01 closes the accidental leak regardless, and a persisted excerpt would be a follow-on plan amending `_KIND_FIELDS`.

ON COMPLETION, the executor runs `aw ipd lint --phase pre-transition` until it reports conforming, verifies every `V-*` item carries pasted evidence, and only then moves this plan to `.aw/records/plans/executed/` with the terminal status transition through the tooled lifecycle. Backlog item `he9x6j` is NOT to be closed `done` by this plan's authoring turn; the runner sets it `graduated`, and it reaches `done` only once this plan is executed, which is what preserves its `- Blocks-Release: next` gate through the handoff.
