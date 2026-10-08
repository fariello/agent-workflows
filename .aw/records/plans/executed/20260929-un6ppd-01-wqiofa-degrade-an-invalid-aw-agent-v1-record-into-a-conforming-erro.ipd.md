# IPD: Degrade an invalid aw.agent/v1 record into a conforming error record instead of a traceback

- Date: 2026-09-29
- Kind: child
- Concern: `agent_schema.assert_valid_agent_record` raises `ValueError` from inside the machine serializer `render_jsonl_record`, and no machine surface catches it, so a record that fails validation in production does not degrade to a diagnostic: the CLI dies with a Python traceback, writes ZERO bytes to stdout, and exits 1, a code whose published meaning is "domain findings". Measured live at this lane's HEAD on three separate verbs from a plain command line.
- Scope: ONE new guarded serializer seam in `agent_workflows/agent_schema.py` (a conforming last-resort error record built from RULE TEXT ONLY, never from the offending value) plus its adoption at the four machine emission sites in `agent_workflows/renderers.py`, a strict-mode escape hatch that keeps the suite fail-loud, the contract amendment in `docs/cli-agent-protocol.md` and `docs/cli-output-contract.md`, and new tests. NOT the hand-built record sites outside `renderers.py`, which span four modules (`attention.py`, `run_viewer.py`, `partition.py`, and two callers in `run_analytics_cli.py`) and whose own unsanitized inputs are a separate defect this plan measures and hands to carrier `enygec`. NOT any widening of the validator's permitted value sets. NOT the human or `--json` renderers, which never call the validator.
- Scope-Paths: agent_workflows/agent_schema.py, agent_workflows/renderers.py, docs/cli-agent-protocol.md, docs/cli-output-contract.md, tests/test_agent_record_guard.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: un6ppd
- Set: un6ppd
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: wqiofa

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: wqiofa verified (set un6ppd, attempt 1).
- 2026-10-03 approved (aw set): status set to approved

- 2026-10-02 readiness re-check (agent (aw ipd recheck-readiness)): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-09-30, findings PR-202..F-05. Recomputed at HEAD `22d50ce93`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS via /plan-review; PR-202 through PR-207 fixed, PR-201 left OPEN at BLOCKER and escalated as blocking OQ-05. Reviewed at HEAD `3324a45f`; `aw ipd lint --phase author` was `clean` before any edit; suite re-measured `3387 passed, 2 skipped, 3 warnings in 60.65s`. THE DIAGNOSIS IS EXCELLENT AND BOTH CORRECTIONS OF THE BACKLOG ITEM ARE RIGHT. F-01 reproduces exactly (`emit` wraps only the write, so the raising `render` call is outside every handler). F-02 reproduces on all three verbs from a plain command line: each exits 1 with ZERO stdout bytes and a `ValueError`, while the human path of the same command exits 2 with a clean message. F-06, the correction that changes the design, reproduces decisively: a substitute carrying the validator message verbatim RE-TRIPS the path rule while the ANSI, bad-exit and bad-outcome classes do not, and a rule-text-only substitute validates clean for every class. F-04, F-07, F-08, F-09, F-10 (including commit `5adf3774` and the now-fixed projection case), F-13, F-14 and F-15 all verify, and all three carriers exist and are live with `enygec` gating the release. ONE BLOCKER IS STRUCTURAL AND IS NOT REPAIRABLE WITH BOUNDED EDITS (PR-201, OQ-05): E-04 requires `BaseRenderer.emit` to return 2 "when the agent renderer substituted a record", and NO MECHANISM EXISTS, because `render()` returns a bare `str`, `emit` is defined once on `BaseRenderer` and inherited by all three renderers, and it returns `result.exit_code` to 98 call sites; every route (re-parse the line, side-channel, widen the shared signature) costs something this plan's own Scope check protects, and the parity rule is additionally ill-defined for `render_stream`, which returns a MULTI-LINE payload where one substituted line among forty valid ones has no single referent. Escalated rather than guessed: the choice is an architecture and published-contract call. FOUR FIXED PROBLEMS. PR-202: F-12's baseline was 141 tests stale (`3246` against a measured `3387`) and was a comparison target in two places, so an executor would have chased a phantom regression. PR-203: E-01's reducer read as a first-colon split, which measurably returns the WHOLE message with the offending value intact for the `Unknown outcome` and `exit`-range classes, and fails INVISIBLY because neither residue is a home path or an ANSI escape, so V-02's no-leak probe would pass. PR-204: E-01's ANSI assertion was targeted at a home-path message that can never contain an escape, so it could not fail. PR-205: F-07/OQ-03's `"A fatal or cannot-run execution diagnostic"` gloss is real but lives in `docs/cli-output-contract.md:181`, not the `cli-agent-protocol.md` kind table it was attributed to, and both files are in `Scope-Paths`. PR-206: F-05's fourth class fires only under `--verbose`. PR-207: the history arrived oldest-first and was ONE LINE from failing `aw check plans` (the same-date group masked it; appending any later-dated entry flips it to ordered), so it was swapped and re-verified. Full findings and four decisions in `.aw/records/reviews/20260929-un6ppd-01-wqiofa-degrade-an-invalid-agent-record-into-a-conforming-error-record.review.md`.
- 2026-09-29 to-review (opencode): authored from backlog item `un6ppd`. The item's premise was re-measured at lane HEAD `95d1d114` and CONFIRMED, but its severity characterization was found to UNDERSTATE the defect in a way that changes the design: the crash is not merely a latent risk awaiting "the next verb to invent an exit value", it is reachable TODAY from a plain command line on three shipped verbs via ordinary user input (F-02, F-03). One of the item's two suggested implementation details was also measured to be WRONG and would reproduce the crash inside its own handler (F-06); the plan records that correction rather than inheriting it.
- 2026-09-29 draft (opencode): created.

## Goal

Make a machine surface that cannot build a conforming `aw.agent/v1` record report that fact AS a conforming `aw.agent/v1` record, so an automated consumer receives a parseable refusal with the contract's own error semantics instead of an unparseable traceback on stderr and an exit code that means something else entirely. Keep the validator itself strict and keep the raise reachable, so nonconforming records still fail loudly in the test suite and the anti-greenwashing gate is not weakened into a warning.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the guarded serializer seam

- [x] E-01 Add a rule-text extraction helper to `agent_schema` that reduces each string returned by `validate_agent_record` to its RULE TEXT, discarding the quoted offending value, and add a module constant for the last-resort diagnostic text.
  DO NOT IMPLEMENT THIS AS A SPLIT ON THE FIRST COLON, which is the obvious reading of "rule prefix" and is MEASURABLY WRONG FOR TWO OF THE FIVE CLASSES (F-16, PR-203). Measured per class at review: `"Unsanitized absolute home path in field 'next': '<value>'"` and `"ANSI escape code detected in field 'next': '<value>'"` both split safely, but `"Unknown outcome 'nonsense'; expected one of (...)"` contains NO colon before its offending value and `"Field 'exit' must be an integer in (0, 1, 2), got '7'"` likewise, so a first-colon split returns the ENTIRE message with the value intact for both. Neither residue is a home path or an ANSI escape, so the no-leak probe in V-02 would PASS while the reducer silently fails its own stated contract; that invisibility is why the requirement is stated as a property rather than a delimiter. DEFINE THE REDUCER AGAINST THE VALIDATOR'S ACTUAL MESSAGE SHAPES, enumerated from `validate_agent_record`'s own branches, and assert PER CLASS that the offending value is ABSENT from the reduced text. The FIELD NAME must survive wherever the message carries one, since that is what keeps the diagnostic actionable.
  - Depends on: none
  - Expected outcome: for EVERY violation class in F-05, the reduced text does not contain the offending value (asserted directly against the literal value, which is the only assertion that catches the two classes a delimiter split mangles), and the field name survives wherever the original message named one. TARGET EACH REGEX AT A CLASS WHOSE MESSAGE CAN ACTUALLY CARRY THAT RESIDUE (PR-204): assert `_HOME_PATH_RE` finds nothing in the reduced HOME-PATH class message and `_ANSI_ESCAPE_RE` finds nothing in the reduced ANSI class message. Do not assert the absence of ANSI in a home-path message, which is where this item's first wording put it: that input never contained an escape, so the assertion cannot fail and proves nothing.
  - Execution state: performed

- [x] E-02 Add the guarded serializer function to `agent_schema` beside `render_jsonl_record`: it attempts the strict render, and on `ValueError` builds a conforming substitute error record (`kind: error`, `outcome: error`, `exit: 2`, `verified: false`, `complete: false`) carrying E-01's rule-text-only violations, then validates THAT record with the same strict validator before returning it, and falls back to a module-constant literal record if even the substitute fails.
  - Depends on: E-01
  - Expected outcome: the new function returns a single-line JSONL string for every record the existing `render_jsonl_record` accepts, byte-identical to it; for each of the five distinct violation classes measured in F-05 it returns a substitute line that `validate_agent_record` accepts with an empty error list; it never raises `ValueError` for any input; and its returned substitute for the home-path case contains no substring matching `_HOME_PATH_RE`.
  - Execution state: performed

- [x] E-03 Add the strict-mode escape hatch to the guarded serializer so the raise stays reachable, defaulting to STRICT under pytest (via the shipped `PYTEST_CURRENT_TEST` precedent) and to GUARDED in production, with an explicit keyword parameter overriding both.
  - Depends on: E-02
  - Expected outcome: called with the explicit strict keyword, the function re-raises the original `ValueError` with its full unredacted message; called with the explicit guarded keyword, it returns the substitute; called with neither from inside the test suite it raises, so an existing or future test that builds a nonconforming record still fails loudly rather than silently receiving a substitute record.
  - Execution state: performed

### Task group 2: adoption at the machine emission sites

- [x] E-04 Point all four `AgentRenderer` methods (`render`, `render_item`, `render_summary`, and the summary/item calls inside `render_stream`) at the guarded serializer instead of `render_jsonl_record`, and make `BaseRenderer.emit` return exit code 2 when the agent renderer substituted a record, so the embedded `exit` and the process exit code still agree.
  - Blocked by: OQ-05. THE EXIT-CODE HALF OF THIS ITEM HAS NO STATED MECHANISM AND CANNOT BE IMPLEMENTED AS WRITTEN (F-17, PR-201). `BaseRenderer.render` returns a bare `str`, so no substitution signal crosses the render/emit boundary; `emit` is defined ONCE on `BaseRenderer`, inherited unmodified by all three renderers, and returns `result.exit_code` to 98 call sites. Every route to the required value costs something this plan's own Scope check protects, and OQ-05 holds the choice: re-parse the emitted line, carry a side-channel on `self` or the context, or widen `render()`'s shared signature. DO NOT PICK ONE SILENTLY. The serializer-adoption half (the four call sites) is independent of OQ-05 and may be performed; the `emit` change must wait for the answer.
  - Depends on: E-03
  - Expected outcome: `AgentRenderer().emit(<result whose record is invalid>, <agent context>)` WRITES a conforming single line to the context stdout rather than raising, and returns the exit code OQ-05 resolves to; where that is 2, the embedded `exit` field of that line equals the returned integer, satisfying the parity rule for the SINGLE-RECORD case. THE PARITY CLAIM IS SCOPED TO ONE RECORD PER EMISSION DELIBERATELY: `render_stream` returns `"".join(lines)`, a MULTI-LINE payload, so when one item line of forty is substituted the rule has no single referent and the other lines are already valid and already in the string; that sub-case is part of OQ-05 and this item must not assert parity over a stream until it is answered. Every currently-valid result still emits its byte-identical previous line and returns its previous exit code; `HumanRenderer` and `JsonRenderer` are not modified, because neither calls the validator.
  - Execution state: performed

### Task group 3: contract and coverage

- [x] E-05 Amend both contract documents to state the substitution behavior and its exit-code consequence, and add `tests/test_agent_record_guard.py` pinning the guarded seam, the strict mode, the no-leak property, the parity property, and the end-to-end CLI behavior of the three live crash sites this plan does and does not fix.
  - Depends on: E-04
  - Expected outcome: `docs/cli-agent-protocol.md` and `docs/cli-output-contract.md` each state that a record failing validation is replaced by a conforming error record carrying exit 2 rather than crashing, and that the substitute names the violated RULES and not the offending values; the new test file fails on the pre-E-02 tree and passes after E-04; and it documents by assertion that `aw attention <path under the home directory> --agent` still crashes because its record is built OUTSIDE `renderers.py`, which is this plan's disclosed honesty bound.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- ASSERT ON OBSERVABLE BEHAVIOR, never on code structure (`AGENTS.md`, GUIDING_PRINCIPLES P16). Every test E-05 adds calls a function or drives the CLI and asserts on returned strings, parsed JSON records, exit codes, and stream contents; none reads production source with `inspect`, `ast`, or regex, none counts callers, and none pins a docstring.
- THE ANTI-GREENWASHING VALIDATOR IS THE POINT OF THE MODULE AND MUST NOT BE WEAKENED. `agent_schema`'s own docstring names the "anti-greenwashing outcome invariants" as one of the five things it defines, and `validate_agent_record` implements them as explicit `Greenwash violation:` and `Exit code mismatch:` branches. This plan therefore adds a GUARD AT THE SERIALIZER and changes no rule, no permitted value set, and no branch of `validate_agent_record`.
- THE SUBSTITUTE MUST BE `kind: error` WITH `exit: 2`, and this is forced rather than chosen. `validate_agent_record`'s `elif kind == "error":` branch refuses any error record whose `exit` is not 2 and refuses `complete: True`. Measured: an error record carrying `exit: 0` yields `['Error record must carry exit=2, got exit=0']` and one carrying `exit: 1` the same for 1. So there is no conforming way to substitute an error record while preserving the original result's exit code, which is why E-04 must move the process exit code too (F-08).
- A `PYTEST_CURRENT_TEST` TEST-MODE GUARD IS AN ESTABLISHED SHAPE HERE, so E-03 follows a precedent rather than inventing one. `runner_shared._assert_probe_spawn_is_permitted` reads exactly that variable to refuse a real model spawn from inside the suite, and its docstring states the reasoning this plan reuses: "`PYTEST_CURRENT_TEST` is set by pytest and by nothing else, so a real `aw oc run` never sees it and this function never fires there."
- THE VALIDATOR IS ALREADY CALLED DEFENSIVELY AT THE HAND-BUILT SITES, which is why those sites are a different defect. `attention.unresolved_selector_agent_record`'s own comment says it validates to "Fail closed on our OWN record rather than trusting it by eye", and `run_viewer.emit_unresolvable_target_refusal`'s docstring says the record "is a conformant `aw.agent/v1` error record ... because the conformance matrix asserts an agent summary's `exit` agrees with the process return code". Both intend the strict raise; what they lack is input sanitization (F-03).
- STREAM SEPARATION IS A PUBLISHED CONTRACT THIS PLAN MUST HONOR. `docs/cli-output-contract.md` section 7 reserves stdout "strictly for final structured results (the interactive human view or machine JSONL records)" and commits that handlers "exit cleanly without dumping Python stack traces". The current behavior violates the second clause outright, which is the contract basis for this fix.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S PREMISE IS CORRECT AND LIVE AT THIS LANE'S HEAD. `CommandResult.to_agent_record`'s last statement before `return rec` is `_schema.assert_valid_agent_record(rec)`; `AgentRenderer.render` is two lines (`rec = result.to_agent_record(context)` then `return _schema.render_jsonl_record(rec)`) and catches nothing; `render_jsonl_record` itself calls `assert_valid_agent_record(record)` before `json.dumps`; and `assert_valid_agent_record` raises `ValueError`. `BaseRenderer.emit` wraps only the stdout WRITE in `try/except (BrokenPipeError, OSError)`, so the render call that raises is outside every handler. | Read of all four symbols at HEAD `95d1d114`; `emit`'s `try` block read and confirmed to wrap only `ctx.stdout.write`/`flush`. |
| F-02 | **THE CRASH IS REACHABLE TODAY FROM A PLAIN COMMAND LINE, NOT ONLY BY A FUTURE VERB, AND THIS IS THE FINDING THAT RAISES THE STAKES.** The item says the remaining risk is "the next verb to invent an exit value". Measured at HEAD `95d1d114`, three shipped verbs crash on ordinary user input with no code change at all: `python3 -m agent_workflows attention <a path under the home directory> --agent` exits 1 with a `ValueError` traceback and EMPTY stdout, the same command with `--json` does likewise, and `python3 -m agent_workflows runs <same path> --agent` does likewise. The trigger is not the exit code at all: it is the validator's unsanitized-home-path rule firing on a user-supplied selector token echoed back into the refusal record. | Three CLI invocations run in this lane with `AW_NO_REEXEC=1`, each with its exit code, empty stdout, and final traceback line captured; the human path of the same command shown exiting 2 with a normal message, proving the crash is machine-surface-specific. |
| F-03 | THE THREE LIVE CRASH SITES ARE HAND-BUILT RECORDS OUTSIDE `renderers.py`, so this plan's seam does NOT fix them and must not claim to. `attention.unresolved_selector_agent_record` calls `_agent_schema.assert_valid_agent_record(record)` directly and `run_viewer.emit_unresolvable_target_refusal` likewise; both interpolate the raw user token into `unresolved_selectors`/`unresolved_targets` AND into their `error` string. `partition`'s agent branch calls `render_jsonl_record` directly with a record whose `unknown` list carries user-supplied ids, and `run_analytics_cli` has two direct `render_jsonl_record` callers. Their real defect is UNSANITIZED INPUT, which a serializer guard would mask rather than fix. | `grep` for `assert_valid_agent_record` and `render_jsonl_record` across `agent_workflows/`, every hit classified as renderer-mediated or hand-built; direct probe of `attention.unresolved_selector_agent_record` with a home-path token raising on three fields at once. |
| F-04 | A FIFTH TRIGGER EXISTS THAT IS RENDERER-MEDIATED AND THEREFORE IN SCOPE, which is what makes E-04 load-bearing rather than theoretical. `run_analytics_cli.run_export_leaf` builds `NextAction(f"aw runs submit {bundle.root}", "submit")` where `bundle.root` comes from `_export_destination`, which returns `Path(str(explicit))` verbatim for an operator-supplied `--out`. So `aw runs export --out <a directory under the home directory> --agent` routes an absolute home path into the `next` field and through `AgentRenderer`. Measured on the seam directly: a `CommandResult` whose `next_actions` carries `aw install /home/<name>/proj` raises `ValueError: ... Unsanitized absolute home path in field 'next'` and writes zero bytes. | Read of `_export_destination` (its docstring states an explicit `--out` "is honored as given") and of the `NextAction` construction; a renderer probe with a home path in `next_actions` capturing the raise and the empty stdout; a subprocess probe confirming process exit 1 with an empty stdout. |
| F-05 | THE TRIGGER CLASS IS MUCH WIDER THAN THE `exit` VALUE THE ITEM NAMES, so a fix keyed on exit codes would be inadequate. Measured through `AgentRenderer`, FIVE distinct violation classes each produce the crash: (1) an out-of-range `exit`; (2) a home path in `next`; (3) a home path in a nested `evidence` value **(verbose only)**; (4) a home path in an `evidence` detail or a diagnostic `fix` **(VERBOSE ONLY, and this qualifier was missing from the first wording of this row, PR-206)**; and (5) an ANSI escape in a diagnostic rule. Separately through `render_summary`, inconsistent `total`/`emitted`/`omitted` counts raise. Every one writes zero bytes first. CLASS 4'S PRECONDITION IS LOAD-BEARING FOR ANY REPRODUCTION: in compact mode `CommandResult.to_agent_record` projects each diagnostic to `location` and `rule` only and each evidence item through `sanitize_evidence_item`, so `fix` and `detail` never reach the record and the class does not fire at all. Re-measured at review: class 4 raises with `verbose=True` and does NOT raise with `verbose=False`. | Seven renderer probes, one per class, each with the raised message and the empty captured stdout recorded; re-measured at review with the compact/verbose pair for class 4 shown explicitly. |
| F-06 | **ONE OF THE ITEM'S TWO SUGGESTED IMPLEMENTATION DETAILS IS MEASURABLY WRONG AND WOULD REPRODUCE THE CRASH INSIDE ITS OWN HANDLER.** The item proposes a substitute record "that reports the validation failure itself". Measured: for the home-path class, the validator's message EMBEDS the offending value (`Unsanitized absolute home path in field 'x': '/home/<name>/p'`), so a substitute carrying that message verbatim in an `error` field FAILS the very same rule, yielding `Unsanitized absolute home path in field 'error': ...`. The ANSI, bad-exit, and bad-outcome classes do not re-trip. So the substitute must carry RULE TEXT ONLY, which is why E-01 exists as a separate item. Measured also that a rule-prefix-only substitute validates clean for all three tested classes. | A probe building the item's proposed substitute for four violation classes and re-validating each, showing the home-path class re-trips and the other three do not; a second probe showing the rule-prefix-only substitute validates with an empty error list for every class tried. |
| F-07 | THE ITEM'S SUGGESTED `outcome: cannot-run` IS THE LESS HONEST OF THE TWO ADMISSIBLE WORDS. `validate_agent_record` accepts either `error` or `cannot-run` for an error record, so both conform (re-verified: both validate clean on the floor record). But `docs/cli-output-contract.md` section 11.4 scopes `cannot-run` to "Missing mandatory arguments, unknown subcommands, or invalid selectors", which describes a refusal to START. A record that failed validation AFTER the work ran is an internal fault, which `docs/cli-output-contract.md` glosses at its kind list as "A fatal or cannot-run execution diagnostic" (`docs/cli-output-contract.md:181`). CITATION CORRECTED AT REVIEW (PR-205): that gloss was first attributed to `docs/cli-agent-protocol.md`'s kind table, where it does NOT appear; that table's row reads only "One of `result`, `summary`, `item`, `error`." with no gloss, so E-05's amendment to THAT file is additive rather than adjacent to existing prose. This plan therefore uses `error`. | Both contract sections read; the validator's `elif kind == "error":` branch read, confirming both words conform so the choice is semantic rather than forced; the gloss located by `grep` at `docs/cli-output-contract.md:181` and confirmed absent from `docs/cli-agent-protocol.md`. |
| F-08 | THE PROCESS EXIT CODE MUST MOVE TO 2, AND THAT IS A REAL BEHAVIOR CHANGE THIS PLAN MUST DECLARE RATHER THAN HIDE. The contract states "The embedded `exit` field in every record MUST equal the process exit code" and the validator refuses an error record whose `exit` is not 2. So substituting an error record for a result that would have exited 0 or 1 forces the process to exit 2. Before this plan that same case exits 1 by accident of the uncaught exception, so no caller can currently be relying on a meaningful code for it. | The parity sentence quoted from `docs/cli-output-contract.md` section 10; two validator probes refusing `exit: 0` and `exit: 1` on an error record; the measured pre-fix exit code of 1 from the F-02 and F-04 subprocess probes. |
| F-09 | NO SHIPPED TEST ASSERTS THAT THE RENDERER RAISES, so this plan breaks no existing contract test and E-03's strict mode is a forward-looking guarantee rather than a fix for a failing test. Searching all of `tests/` for an `assertRaises` paired with `agent_schema`, `render_jsonl_record`, `to_agent_record`, `AgentRenderer`, or `assert_valid` returns ZERO hits. Only five test files reference the schema or the renderer at all, and their uses are positive assertions that a produced record VALIDATES. | A combined search over `tests/` for `assertRaises` intersected with the five symbol names, returning nothing; the five referencing test files listed and their call sites classified as positive validation. |
| F-10 | A PRIOR AUTHOR ALREADY HIT THIS CLASS AND WORKED AROUND IT IN PRODUCTION CODE, which is independent evidence that the defect costs real time. `run_analytics_cli`'s `_emit_query_agent` carries a multi-paragraph comment recording that `render_summary(..., context=ctx)` with `ctx.fields` set "RAISES `ValueError` ... because the two contracts disagree, and any caller passing `--fields` to a summary crashes", and states the bug "lives in `renderers.py` / `agent_schema.py`, neither of which is in this plan's `Scope-Paths`". That specific instance was later fixed by plan `gygujf` (which widened `_PRESERVED_FIELDS`), and the workaround comment is now stale; but the CLASS it describes is exactly this item's. | The comment read in full; the projection case re-probed at this HEAD and confirmed NO LONGER raising; `git log` identifying commit `5adf3774` "preserve per-kind required fields under --fields projection (gygujf)" as the fix. |
| F-11 | THE FIX BELONGS IN `agent_schema` AND NOT IN EACH RENDERER METHOD. There are FOUR emission points inside `AgentRenderer` (`render`, `render_item`, `render_summary`, plus `render_stream` which calls the latter two) and two further direct `render_jsonl_record` callers in `run_analytics_cli` and one in `partition`. A guard written into `AgentRenderer.render` alone would leave the item and summary paths crashing, which F-05's `render_summary` count probe shows is a live class. | `grep` for `render_jsonl_record` across `agent_workflows/` locating all seven call sites; `render_stream` read confirming it delegates to `render_item` and `render_summary` rather than serializing itself. |
| F-12 | THE SUITE IS GREEN, and the baseline is a LIVE POPULATION that drifts, so it is context and not a bar. Re-measured at review on HEAD `3324a45f`: **`3387 passed, 2 skipped, 3 warnings in 60.65s`** from a BARE `python3 -m pytest`. The authoring figure was `3246 passed, 2 skipped` at HEAD `95d1d114`, i.e. 141 tests lower, because the tree gained tests between authoring and review (PR-202). RE-DERIVE IT AT EXECUTION rather than comparing against either number, and COMPARE FAILING NODE IDS rather than totals, which is the only comparison that survives a moving tree. | Bare `python3 -m pytest` run at HEAD `95d1d114` (authoring) and re-run at HEAD `3324a45f` (review), both summary lines captured. |
| F-13 | NO SPEC GOVERNS THE `aw.agent/v1` RECORD SHAPE, so the amendment owed is to the two DOCS and not to a `.spec.md`. Searching `.aw/records/specs/` for `aw.agent/v1`, `agent_schema`, and `assert_valid_agent_record` returns hits in only three specs, and each is incidental: `command-surface-redesign` notes in its history that the canonical machine format "is now aw.agent/v1" and that "the 0/1/2 exit classification carries over unchanged"; `pip-distribution` pins two field NAMES of `aw status`; `uonrjg` discusses color and a retracted non-TTY promise. None defines the record kinds, the validator, or its failure mode. | Three searches over `.aw/records/specs/`, every hit read in context and classified; `grep` for `assert_valid_agent_record` across the specs tree returning zero hits. |
| F-15 | THE THREE CARRIER ITEMS WERE FILED AT AUTHORING TIME, so every exclusion in this plan points at a live item rather than at an intention. `enygec` carries the unsanitized selector echo at the hand-built sites and is the one that GATES THE RELEASE (`- Work-Kind: bug`, `- Blocks-Release: next`), because the three surviving CLI crashes are a live user-reachable defect; `7tixnq` carries the `--json` leak posture and `o8vgss` the stale workaround comment, both `chore` and neither release-gating. Filing them at authoring rather than at execution means this plan's Deferred section cites real id6 values a reviewer can resolve now. | `aw backlog new --apply` run three times in this lane, each written path captured; the three items read back with their `- Id:`, `- Work-Kind:` and `- Blocks-Release:` fields. |
| F-14 | THE LAST-RESORT FLOOR RECORD IS PROVABLY CONFORMING, so E-02's final fallback cannot itself become a new crash. A record built only from module constants (`kind: error`, `outcome: error`, `exit: 2`, `verified: false`, `complete: false`, a fixed `cmd`, a fixed `error` sentence with no interpolation, and `next: null`) validates with an empty error list. Re-verified at review: `validate_agent_record(floor)` returns `[]`, and the same record refuses at `exit: 0` and `exit: 1`, confirming F-08's forcing argument. | A probe validating exactly that literal record, returning `[]`; re-run at review together with the exit 0/1/2 sweep. |
| F-16 | ADDED AT REVIEW (PR-203). **THE NAIVE RULE-TEXT REDUCER FAILS FOR TWO OF FIVE CLASSES, AND FAILS INVISIBLY.** Measured per class: a split on the first colon safely drops the value for `Unsanitized absolute home path in field 'next': '<value>'` and for `ANSI escape code detected in field 'next': '<value>'`, but `Unknown outcome 'nonsense'; expected one of (...)` carries its value BEFORE any colon and `Field 'exit' must be an integer in (0, 1, 2), got '7'` carries its value after a comma-separated tuple containing no delimiting colon, so for both the split returns the WHOLE message with the offending value intact. | Neither residue is a home path or an ANSI escape, so V-02's no-leak probe PASSES while the reducer breaks its own contract. E-01 is therefore specified as a per-class PROPERTY (the literal offending value must be absent) rather than as a delimiter rule, and V-01 demands the per-class table. |
| F-17 | ADDED AT REVIEW (PR-201). **E-04'S `emit` EXIT-CODE CHANGE HAS NO MECHANISM, AND EVERY ROUTE TO ONE COSTS SOMETHING THIS PLAN PROMISES NOT TO SPEND.** `BaseRenderer.render` returns a bare `str`, so a substitution cannot signal across the render/emit boundary; `emit` is defined ONCE on `BaseRenderer`, inherited unmodified by `HumanRenderer`, `AgentRenderer` and `JsonRenderer`, and returns `result.exit_code` to 98 call sites across `agent_workflows/`. The three available routes are re-parsing the emitted line, a side-channel on `self` or the context, and widening `render()`'s shared signature; the plan's own Scope check forbids modifying the other two renderers, which the third route does. SEPARATELY the parity rule is ILL-DEFINED for `render_stream`, which returns `"".join(lines)`: with one substituted item among forty valid ones, "the embedded `exit` equals the process exit code" has no single referent. | This is the plan's one genuine blocker and it is escalated as OQ-05 rather than guessed, because choosing among the three is an architecture and published-contract decision. The serializer-adoption half of E-04 is unaffected and remains performable. |

## Proposed changes (ordered, validatable)

1. Add the rule-text reducer and the last-resort diagnostic constant to `agent_schema`, so a violation can be reported without echoing the value that violated it (F-06) (E-01).
2. Add the guarded serializer to `agent_schema`: strict render, then a rule-text-only substitute error record which is itself strictly validated, then the constant floor record (F-14) (E-02).
3. Add the strict-mode parameter defaulting to strict under pytest via the shipped `PYTEST_CURRENT_TEST` precedent, keeping the raise reachable (E-03).
4. Adopt the guarded serializer at the four `AgentRenderer` emission points and move `emit`'s returned exit code to 2 when a substitution happened, preserving the published parity rule (F-08, F-11) (E-04).
5. Amend both contract docs and add the new test file, including the assertions that record this plan's honesty bound (F-03) (E-05).

## Deferred / out of scope (with reason)

- THE HAND-BUILT CRASH SITES IN `attention.py`, `run_viewer.py` AND `partition.py` ARE OUT OF SCOPE, and this is the most important exclusion in the plan because it is the one a reader will most expect to be covered: two of them are the verbs measured crashing in F-02. They build their records BY HAND and call the validator directly, so this plan's renderer-mediated seam does not run for them and they keep crashing after it lands (F-03). Their actual defect is different in kind: a raw user-supplied selector token is interpolated into three record fields with no `normalize_repo_path` call, so the honest fix is to SANITIZE THE INPUT at each site, not to catch the symptom at the serializer. Routing them through the guard would actively make things worse, because the operator would receive a generic conforming refusal instead of the answer to the question they asked, and the real bug (an unsanitized echo) would be permanently masked. Fixing them also means touching three further modules and deciding, per verb, what a selector should be SHOWN AS once sanitized, which is a per-surface product decision rather than a serializer change.
  - Carrier: enygec
- THE TWO DIRECT `render_jsonl_record` CALLERS IN `run_analytics_cli` ARE OUT OF SCOPE for the same reason and are covered by the same carrier. They are hand-built records that bypass `AgentRenderer` entirely; one is the query refusal and one the query stream. Converting them to the guarded serializer is a mechanical follow-up once this seam exists, but it is not free: the query path's records carry a `view` and `caveats` payload whose sanitization posture has not been measured, and measuring it is the carrier's work.
  - Carrier: enygec
- WIDENING ANY PERMITTED VALUE SET IN `validate_agent_record` is rejected rather than deferred. The item's own history records that `quqyc4`'s OQ-01 proposed exactly that (admit `exit: 3`) and that its execution REVERSED the decision, choosing instead to make the machine surface exit 2 and leave the human surface at 3, because widening would "promote exit 3 into two published contracts at the moment its only other emitter was removed". That ruling stands and this plan does not reopen it. The separate live question of the human path exiting 3 while the published classification lists only 0/1/2 is already carried by backlog `c6vs7y`.
  - Carrier-Declined: Nothing is owed by this plan. The widening question was decided against on the record by `quqyc4` decision 03-quqyc4-D1, and the surviving residual is already carried by `c6vs7y`, so naming a carrier here would duplicate a live item.
- MAKING THE VALIDATOR ITSELF NON-RAISING, for example by having `assert_valid_agent_record` return a status instead of raising, is rejected rather than deferred. It is the anti-greenwashing gate and roughly a dozen callers, including three defensive hand-built sites and one test, depend on the raise as their fail-closed mechanism; converting it would silently turn every one of those into a no-op unless each is also updated. The guard belongs at the SERIALIZER, which is the single place where "we must emit bytes now" is true.
  - Carrier-Declined: Nothing is owed. This is a design decision resolved from evidence in OQ-01, not deferred work, and the strict raise remains available and is kept reachable by E-03.
- THE HUMAN AND `--json` RENDERERS ARE NOT TOUCHED. Measured: with a `CommandResult` carrying both an out-of-range `exit` and a home path in `next`, `JsonRenderer.emit` and `HumanRenderer.emit` both return normally and write output, because neither calls the validator. So there is nothing to guard there. That `JsonRenderer` consequently emits an unsanitized home path is a REAL and different concern about `--json`'s leak posture, not a crash, and it is not this plan's.
  - Carrier: 7tixnq
  - Carrier-Evidence: .aw/records/backlog/done/20260929-7tixnq-01-7tixnq-json-renderer-leak-posture.backlog.md
- THE STALE WORKAROUND COMMENT IN `run_analytics_cli._emit_query_agent` IS NOT CORRECTED HERE. It asserts a defect that measurement shows was fixed by `gygujf` (F-10), so it now misleads a reader about live behavior. It is a comment-only edit in a file outside this plan's `- Scope-Paths:`, and bundling it would widen the fence for no functional gain.
  - Carrier: o8vgss
  - Carrier-Evidence: .aw/records/backlog/done/20260929-o8vgss-01-o8vgss-stale-projection-workaround-comment.backlog.md

## Scope check

- Over-scope: none DECLARED, but OQ-05 may widen it and that is the honest statement rather than a promise this plan cannot keep. Two of the three mechanisms OQ-05 enumerates would touch `HumanRenderer`/`JsonRenderer` or the shared abstract `render()` signature, which this section otherwise promises not to modify; if the maintainer picks one of those, this Scope check and the Deferred row asserting the two renderers are untouched must both be amended in the same change (F-17, PR-201). `agent_workflows/agent_schema.py` carries E-01's reducer and constant plus E-02's and E-03's guarded serializer; `agent_workflows/renderers.py` carries E-04's four call-site changes and the `emit` change as OQ-05 resolves it; the two `docs/` files carry E-05's amendment; `tests/test_agent_record_guard.py` is new and carries E-05's tests. No existing rule, permitted value set, or branch of `validate_agent_record` is modified. No hand-built record site is touched. `HumanRenderer` and `JsonRenderer` are not modified. No `.spec.md` is touched (F-13). No `.aw/` record changes at all beyond this plan: the three carrier items were filed at AUTHORING time and already exist, so execution creates no record of its own.
- Under-scope: A user can still crash `aw attention --agent`, `aw attention --json` and `aw runs --agent` with a home-path selector after this plan lands, because those records are built outside `renderers.py` (F-02, F-03). That is a disclosed limit rather than an omission, it is asserted as such by an E-05 test so it cannot rot into a false claim, and it is handed to carrier `enygec`, which was filed at authoring time and carries `- Blocks-Release: next` because those surviving crashes are a live user-reachable bug. What this plan completes is the CLASS the item actually carries, the unguarded raise at the shared machine serializer, plus the one live renderer-mediated trigger (F-04).

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted. COMPARE FAILING NODE IDS, NOT TOTALS: the count is a live population that moved 141 tests between authoring and review (F-12, PR-202), so re-derive the pre-change baseline in the execution lane and compare sets. The review-time figure for context is `3387 passed, 2 skipped, 3 warnings` at HEAD `3324a45f`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_agent_record_guard.py -o addopts=""` for the per-test counts on the new file.
- `python3 -m pytest tests/test_agent_field_projection.py tests/test_agent_schema_paths.py tests/test_attention.py tests/test_partition.py tests/test_backlog_duplicate_guard.py tests/test_run_analytics.py tests/test_run_viewer.py -o addopts=""` as the targeted regression set: every test file that references the schema or the renderer (F-09) plus the two that drive the hand-built sites.
- A DELIBERATE-FAILURE DEMONSTRATION for E-05: the new tests must be shown FAILING on the pre-E-02 tree with `ValueError` in the traceback, since a guard that was never red proves nothing.
- A NO-LEAK PROBE, which is the single most important check in this plan: for EVERY violation class in F-05, assert the substitute record's serialized line contains no substring matching `agent_schema._HOME_PATH_RE` and none matching `_ANSI_ESCAPE_RE`, and additionally assert the literal offending value does not appear anywhere in the line. Paste the number of classes probed and the count of leaks, which must be zero. Run `aw sanitize --agent` afterwards as an independent second opinion.
- A BYTE-IDENTITY PROBE for E-02 and E-04: over a cross product of CURRENTLY-VALID results spanning every branch of `to_agent_record` (each of `clean`/`ok`/`conforms`/`findings`/`fail`/`preview`/`cannot-run`/`error`; `verified` true and false; `complete` true and false; `applied` true, false and unset; with and without `changes`, `evidence`, `diagnostics`, `next_actions`, `target`, `checked`; compact and `verbose`; with and without `fields`; and more than five changes to exercise the count-collapse branch), assert the guarded serializer's output is byte-identical to `render_jsonl_record`'s and that `emit`'s returned exit code is unchanged. Paste the number of inputs compared and the count of disagreements, which must be zero.
- A PARITY PROBE for E-04: for each violation class, parse the emitted line and assert its `exit` field equals the integer `emit` returned, and that both are 2 (F-08).
- A STRICT-MODE PROBE for E-03: assert the explicit strict call re-raises `ValueError` with the ORIGINAL unredacted message; assert that a call with no explicit mode from inside the suite ALSO raises, which is what keeps future tests fail-loud; and assert the explicit guarded call returns a conforming substitute even under pytest.
- A FLOOR PROBE for E-02: force the substitute-construction path to fail (for example by validating a substitute built with a deliberately broken `cmd`) and assert the constant floor record is returned and validates clean, so the guard has no third failure mode (F-14).
- AN END-TO-END CLI MEASUREMENT for E-05, run as a SUBPROCESS so the real process exit code is observed rather than an in-process return value: `aw runs export --out <a directory under the home directory> --agent` must now write one conforming line to stdout and exit 2 rather than exiting 1 with an empty stdout (F-04). Paste stdout, the exit code, and the empty stderr.
- AN HONESTY-BOUND MEASUREMENT for E-05, also as a subprocess: `aw attention <a path under the home directory> --agent`, the same with `--json`, and `aw runs <same path> --agent` must be shown STILL crashing with `ValueError`, empty stdout and exit 1, proving F-03's exclusion is real and this plan's effect is not overstated.
- `aw ipd lint` on this plan, reporting conforming.
- `aw check` to confirm no new drift, and `aw backlog check` to confirm the three carrier items (`enygec`, `7tixnq`, `o8vgss`) are well-formed and still live.
- `aw sanitize --agent` before commit, since this plan's evidence blocks quote command output including tracebacks and home-path probes.
- `git diff --cached --name-only` immediately before committing, which must list exactly the five paths in `- Scope-Paths:` plus this plan, and nothing another party changed.

## Spec / documentation sync

No `.spec.md` is in `- Scope-Paths:` and none is owed. Searching `.aw/records/specs/` for `aw.agent/v1`, `agent_schema` and `assert_valid_agent_record` finds the record protocol is governed by the two `docs/` contracts and not by any spec: the only three hits are incidental (`command-surface-redesign`'s history line noting the canonical machine format "is now aw.agent/v1" with "the 0/1/2 exit classification carries over unchanged", `pip-distribution` pinning two `aw status` field names, and `uonrjg`'s color discussion), and `assert_valid_agent_record` appears in zero specs (F-13).

BOTH `docs/` CONTRACTS ARE AMENDED BY E-05, and both are in `- Scope-Paths:` so the change is declared and reconcilable. `docs/cli-agent-protocol.md` gains a statement that a record which fails validation is REPLACED by a conforming `kind: error` record carrying `exit: 2` and naming the violated rules, so an agent knows the substitution is a defined outcome rather than a malformed answer. `docs/cli-output-contract.md` section 11.4 gains the same, beside its existing `exit: 2` cannot-run text, and its section 7 broken-pipe clause is extended to name the validation-failure case, since that section already promises handlers "exit cleanly without dumping Python stack traces" and this plan is what makes that promise true for the machine surface.

NO PROTOCOL VERSION BUMP IS REQUIRED, and the precedent for that judgement is on the record. `docs/cli-agent-protocol.md`'s stability clause promises a bump for "any breaking change to record shape or field meaning". This plan adds no field, removes none, changes no field's meaning, and widens no permitted value set. It changes only what happens in a case that currently produces NO RECORD AT ALL, so no consumer can be parsing it today. That is the same reasoning `quqyc4` recorded when it declined a bump for the sibling fix.

THE ONE BEHAVIOR CHANGE THAT IS OBSERVABLE TO A CALLER is the process exit code for the failing case, from an accidental 1 to a deliberate 2 (F-08). It is stated in both docs by E-05 rather than left implicit, because a caller reading `$?` sees it.

## Open questions

### OQ-01: Which surface stays fail-loud, given the validator is the anti-greenwashing gate?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, and this is the question the item explicitly says "needs a maintainer's view", so it must be argued rather than assumed. The item's framing is that catching the raise risks letting "a nonconforming record ship". THE ANSWER IS THAT THE GUARD DOES NOT SHIP THE NONCONFORMING RECORD AT ALL: it DISCARDS it and emits a DIFFERENT, conforming record that says validation failed. So the anti-greenwashing property is preserved exactly, because the invalid record never reaches stdout in either design; the only difference is whether the consumer gets a parseable refusal or a traceback. There is therefore no genuine tension to adjudicate on that axis, and no maintainer ruling is needed for it. WHAT IS CHOSEN, and why: (1) PRODUCTION IS GUARDED, because `docs/cli-output-contract.md` section 7 already promises handlers "exit cleanly without dumping Python stack traces", so the current behavior violates a published contract and the guard is what satisfies it; (2) THE TEST SUITE STAYS STRICT via E-03, because a test that builds a nonconforming record must FAIL rather than quietly receive a substitute, and the `PYTEST_CURRENT_TEST` precedent in `runner_shared._assert_probe_spawn_is_permitted` is the shipped mechanism for exactly this production/test split; (3) THE SUBSTITUTE IS ITSELF STRICTLY VALIDATED before emission, so the guard cannot become a hole through which a malformed record escapes. The residual judgement genuinely left to the maintainer is the EXIT CODE consequence (F-08), which is why it is called out in the gate prose rather than buried here.

### OQ-02: Should the substitute carry the validator's message, or only the rule text?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as RULE TEXT ONLY, and this OVERRIDES the item's suggestion on measured grounds rather than preference. The item proposes a record "that reports the validation failure itself". Measured (F-06): the validator's message for the unsanitized-path rule EMBEDS the offending value, so a substitute carrying it verbatim fails that same rule and the guard would raise inside its own handler, reproducing the exact crash it exists to prevent. This is not hypothetical, it is the FIRST class an implementer would test, and it is also the class that causes all three live CLI crashes (F-02). Three further considerations point the same way. First, the offending value is by construction the thing the sanitizer refused, usually a machine-local absolute path, so echoing it into a machine payload is precisely the leak `agent_schema`'s path rules exist to prevent and would put a maintainer's home directory into an agent's context. Second, the rule text plus the FIELD NAME is enough to act on, which is the actionability bar; E-01 therefore preserves the field name and discards only the quoted value. Third, an unredacted message remains available to a developer through E-03's strict mode, so nothing is lost for debugging. The full message is NOT written to stderr as a consolation either, because section 7 reserves stderr for diagnostics and a leaked home path is no more acceptable there than on stdout.

### OQ-03: Should the substitute's outcome be `error` or `cannot-run`?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as `error`. Both conform, so this is a semantics choice and not a forced one: `validate_agent_record`'s error branch accepts either word (F-07). `cannot-run` is REFUSED because `docs/cli-output-contract.md` section 11.4 scopes it to "Missing mandatory arguments, unknown subcommands, or invalid selectors", all of which are refusals to START, and it is the word the shipped no-project and unresolvable-selector refusals use for exactly that meaning. A record that failed validation AFTER the command did its work is the opposite case: the work ran and the REPORT could not be rendered. `docs/cli-agent-protocol.md`'s kind table glosses `error` as "A fatal or cannot-run execution diagnostic", which covers it. Keeping the two words distinct also preserves a real signal for a consumer: `cannot-run` means nothing happened, while `error` here means something happened and could not be reported, which is a materially different thing to retry.

### OQ-04: Should the guarded serializer replace `render_jsonl_record` or sit beside it?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as A NEW FUNCTION BESIDE IT, with `render_jsonl_record` left byte-for-byte unchanged. Changing `render_jsonl_record` in place would silently convert all SEVEN of its call sites (F-11), three of which are the hand-built sites this plan deliberately excludes (F-03) and whose authors chose the strict raise on the record, with comments saying so: `attention`'s "Fail closed on our OWN record rather than trusting it by eye" and `run_viewer`'s statement that the record is conformant "because the conformance matrix asserts an agent summary's `exit` agrees with the process return code". Silently guarding those would mask the unsanitized-input defect that is their real bug, and would do it invisibly, since no diff would appear at those sites. A separate function makes adoption EXPLICIT and per-site, which is what lets this plan's fence be honest about which surfaces it fixes and which it does not.

### OQ-05: How does `BaseRenderer.emit` learn that the agent renderer substituted a record, and what does parity mean for a multi-record stream?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-201
- Carrier-Declined: RESOLVED BEFORE EXECUTION, NOT CARRIED ONWARD, so there is nothing for a downstream carrier to own. This question carries `- Blocking: yes`, which makes `aw ipd lint` report `IPD-Q501` at EVERY checkpoint including `author` (verified at review: the plan goes from one diagnostic to zero only when this is answered), so the plan cannot reach `approved` or be dispatched while it stands. It therefore cannot outlive this plan the way a deferred obligation can: either the maintainer names a mechanism and E-04 implements it inside this plan's own execution, or they reject the exit-code coupling entirely and E-04 is rescoped here. Filing a backlog item would create a second home for a decision this plan is REQUIRED to settle first, and would let the plan execute with the question still open, which is exactly what the blocking flag exists to prevent.
- Resolution or deferral rationale: Resolved on 2026-10-02 per maintainer ruling: descope exit-code coupling on `BaseRenderer.emit`. `AgentRenderer` emits conforming substitute record directly; `emit` continues returning `result.exit_code` without mutating its return signature or adding stateful side channels. Stream emissions continue unaffected.


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/agent_schema.py` as it stands after E-01 ONLY, showing the reducer and the constant added and NO change to `validate_agent_record`, `is_valid_agent_record`, `assert_valid_agent_record`, `render_jsonl_record`, `RECORD_KINDS`, `VALID_OUTCOMES`, or the permitted `exit` tuple. PASTE A PER-CLASS TABLE, one row for each of F-05's five classes plus the `Unknown outcome` class, showing the ORIGINAL message, the REDUCED text, and an explicit assertion that the literal offending value is ABSENT from the reduced text. The per-class form is required rather than a single probe because a delimiter-based reducer passes for two classes and silently fails for two others while leaking neither a home path nor an ANSI escape (F-16, PR-203), so only a direct absent-value assertion per class catches it. Target the regexes where the residue can exist (PR-204): `_HOME_PATH_RE.search` returns None on the reduced HOME-PATH message, and `_ANSI_ESCAPE_RE.search` returns None on the reduced ANSI message. Show the field name surviving for the classes whose original message named one, including the out-of-range `exit` class. Quote the last-resort constant's text and confirm in one sentence that it interpolates nothing.
  - Observed evidence:
    `git diff agent_workflows/agent_schema.py` for E-01 additions:
    ```diff
    +# --------------------------------------------------------------------------------------------------
    +# Rule Text Extraction & Degradation Constants (Order 01 / wqiofa)
    +# --------------------------------------------------------------------------------------------------
    +
    +LAST_RESORT_ERROR_DIAGNOSTIC: str = "aw.agent/v1 record failed schema validation"
    +
    +_REDUCER_RULES: Sequence[tuple[re.Pattern[str], str]] = (
    +    # 1. Unsanitized home paths and ANSI escapes in path_prefix fields
    +    (re.compile(r"^(Unsanitized absolute home path in field '[^']+'): .*$"), r"\1"),
    +    (re.compile(r"^(ANSI escape code detected in field '[^']+'): .*$"), r"\1"),
    +    # 2. Exit field range violation
    +    (re.compile(r"^(Field 'exit' must be an integer in \(0, 1, 2\)), got .*$"), r"\1"),
    +    # 3. Outcome field violations
    +    (re.compile(r"^Unknown outcome '[^']*'; (expected one of .*)$"), r"Unknown outcome; \1"),
    +    (re.compile(r"^(Field 'outcome' must be a string), got .*$"), r"\1"),
    +    # 4. Schema and Kind violations
    +    (re.compile(r"^(Invalid schema: expected '[^']+'), got .*$"), r"\1"),
    +    (re.compile(r"^Invalid kind: '[^']*' must be one of (.*)$"), r"Invalid kind: must be one of \1"),
    +    # 5. Anti-greenwash invariants
    +    (re.compile(r"^Greenwash violation: outcome cannot be '[^']*' (when .*)$"), r"Greenwash violation: outcome cannot be positive \1"),
    +    (re.compile(r"^Greenwash violation: outcome cannot be positive for '[^']*' (state)$"), r"Greenwash violation: outcome cannot be positive for incomplete \1"),
    +    # 6. Exit code parity mismatches
    +    (re.compile(r"^(Exit code mismatch: exit=0 incompatible with negative outcome).*$"), r"\1"),
    +    (re.compile(r"^(Exit code mismatch: exit=1 incompatible with clean outcome).*$"), r"\1"),
    +    (re.compile(r"^(Exit code mismatch: exit=2 requires outcome 'cannot-run' or 'error'), got .*$"), r"\1"),
    +    # 7. Summary record counts
    +    (re.compile(r"^Summary counts inconsistent: emitted \([^)]*\) \+ omitted \([^)]*\) != total \([^)]*\)$"), "Summary counts inconsistent: emitted + omitted != total"),
    +    # 8. Error record invariants
    +    (re.compile(r"^(Error record must carry exit=2), got exit=.*$"), r"\1"),
    +    (re.compile(r"^(Error record must carry outcome 'error' or 'cannot-run'), got .*$"), r"\1"),
    +)
    +
    +
    +def reduce_violation_to_rule_text(violation: str) -> str:
    +    """Reduce a validation error string to its rule text, discarding the quoted offending value."""
    +    for pattern, repl in _REDUCER_RULES:
    +        if pattern.match(violation):
    +            return pattern.sub(repl, violation)
    +    if ": '" in violation or ': "' in violation:
    +        prefix, _, _ = violation.partition(": ")
    +        if prefix:
    +            return redact_home_paths(_ANSI_ESCAPE_RE.sub("", prefix))
    +    return redact_home_paths(_ANSI_ESCAPE_RE.sub("", violation))
    ```
    Verified: NO changes made to `validate_agent_record`, `is_valid_agent_record`, `assert_valid_agent_record`, `render_jsonl_record`, `RECORD_KINDS`, `VALID_OUTCOMES`, or the permitted `exit` tuple.

    Per-class reduction probe:
    | Violation Class | Original Message | Reduced Text | Offending Value Absent? | Field Name Kept? |
    |---|---|---|---|---|
    | exit-range | `Field 'exit' must be an integer in (0, 1, 2), got '7'` | `Field 'exit' must be an integer in (0, 1, 2)` | True | True |
    | next-home-path | `Unsanitized absolute home path in field 'next': '/home/user/repo'` | `Unsanitized absolute home path in field 'next'` | True | True |
    | evidence-home-path | `Unsanitized absolute home path in field 'evidence': '/home/user/evidence'` | `Unsanitized absolute home path in field 'evidence'` | True | True |
    | evidence-detail-home-path | `Unsanitized absolute home path in field 'evidence.detail': '/home/user/detail'` | `Unsanitized absolute home path in field 'evidence.detail'` | True | True |
    | diagnostic-ansi | `ANSI escape code detected in field 'diagnostics.rule': '\x1b[31mred\x1b[0m'` | `ANSI escape code detected in field 'diagnostics.rule'` | True | True |
    | unknown-outcome | `Unknown outcome 'nonsense'; expected one of ('ok', 'clean', 'findings', 'fail', 'preview', 'error', 'cannot-run', 'conforms')` | `Unknown outcome; expected one of ('ok', 'clean', 'findings', 'fail', 'preview', 'error', 'cannot-run', 'conforms')` | True | N/A |

    Targeted regex verification:
    `_HOME_PATH_RE.search(home_red)` -> `None`
    `_ANSI_ESCAPE_RE.search(ansi_red)` -> `None`
    Field names survived for all applicable classes (`exit`, `next`, `evidence`, `evidence.detail`, `diagnostics.rule`).
    `LAST_RESORT_ERROR_DIAGNOSTIC` = `"aw.agent/v1 record failed schema validation"`; it is a static literal string that interpolates no dynamic values.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/agent_schema.py` after E-02, showing the guarded serializer and the untouched strict path. Paste the NO-LEAK PROBE from Required tests in full: for every one of F-05's five violation classes, the substitute line with the count of `_HOME_PATH_RE` matches, `_ANSI_ESCAPE_RE` matches, and literal-offending-value occurrences, all of which must be zero; paste the number of classes probed. Paste a probe showing `validate_agent_record` returns `[]` for each substitute, which is the proof the guard cannot emit a nonconforming record (OQ-01). Paste the BYTE-IDENTITY PROBE for the currently-valid cross product with the number of inputs compared and zero disagreements. Paste the FLOOR PROBE showing the constant floor record is returned when substitute construction itself fails, and that it validates clean (F-14). Explicitly confirm the guard never raises `ValueError` for any input tried, naming how many inputs that was.
  - Observed evidence:
    `git diff agent_workflows/agent_schema.py` after E-02:
    ```diff
    +LAST_RESORT_ERROR_RECORD: Dict[str, Any] = {
    +    "schema": SCHEMA_VERSION,
    +    "kind": "error",
    +    "cmd": "aw",
    +    "exit": 2,
    +    "outcome": "error",
    +    "verified": False,
    +    "complete": False,
    +    "error": LAST_RESORT_ERROR_DIAGNOSTIC,
    +    "next": None,
    +}
    +
    +LAST_RESORT_JSONL_RECORD: str = (
    +    json.dumps(LAST_RESORT_ERROR_RECORD, separators=(",", ":"), ensure_ascii=False)
    +    + "\n"
    +)
    +
    +def build_substitute_error_record(
    +    errors: Sequence[str],
    +    cmd: Optional[str] = None,
    +) -> Dict[str, Any]:
    +    clean_cmd = "aw"
    +    if isinstance(cmd, str) and cmd.strip():
    +        stripped = cmd.strip()
    +        if not _HOME_PATH_RE.search(stripped) and not _ANSI_ESCAPE_RE.search(stripped):
    +            clean_cmd = stripped
    +    reduced_rules = [reduce_violation_to_rule_text(err) for err in errors]
    +    if reduced_rules:
    +        error_msg = f"Invalid aw.agent/v1 record: {'; '.join(reduced_rules)}"
    +    else:
    +        error_msg = LAST_RESORT_ERROR_DIAGNOSTIC
    +    return {
    +        "schema": SCHEMA_VERSION,
    +        "kind": "error",
    +        "cmd": clean_cmd,
    +        "exit": 2,
    +        "outcome": "error",
    +        "verified": False,
    +        "complete": False,
    +        "error": error_msg,
    +        "next": None,
    +    }
    ```
    The strict path `render_jsonl_record` is completely unmodified.

    No-leak probe (5 F-05 classes probed):
    - Class `exit-range`:
      substitute line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2); Greenwash violation: outcome cannot be positive when verified=False","next":null}`
      validate_agent_record errors: `[]`
      _HOME_PATH_RE matches: 0, _ANSI_ESCAPE_RE matches: 0, literal offending value occurrences: 0
    - Class `next-home-path`:
      substitute line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: Greenwash violation: outcome cannot be positive when verified=False","next":null}`
      validate_agent_record errors: `[]`
      _HOME_PATH_RE matches: 0, _ANSI_ESCAPE_RE matches: 0, literal offending value occurrences: 0
    - Class `evidence-home-path`:
      substitute line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: Greenwash violation: outcome cannot be positive when verified=False","next":null}`
      validate_agent_record errors: `[]`
      _HOME_PATH_RE matches: 0, _ANSI_ESCAPE_RE matches: 0, literal offending value occurrences: 0
    - Class `evidence-detail-home-path`:
      substitute line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: Greenwash violation: outcome cannot be positive when verified=False","next":null}`
      validate_agent_record errors: `[]`
      _HOME_PATH_RE matches: 0, _ANSI_ESCAPE_RE matches: 0, literal offending value occurrences: 0
    - Class `diagnostic-ansi`:
      substitute line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: Greenwash violation: outcome cannot be positive when verified=False; ANSI escape code detected in field 'diagnostics[0].rule'","next":null}`
      validate_agent_record errors: `[]`
      _HOME_PATH_RE matches: 0, _ANSI_ESCAPE_RE matches: 0, literal offending value occurrences: 0

    Byte-identity probe:
    Compared 256 valid records across the combinatorial cross product of outcomes, flags, diagnostics, changes, and evidence. Disagreements: 0.

    Floor probe:
    Forced substitute construction failure via mock on `build_substitute_error_record`.
    Returned line: `{"schema":"aw.agent/v1","kind":"error","cmd":"aw","exit":2,"outcome":"error","verified":false,"complete":false,"error":"aw.agent/v1 record failed schema validation","next":null}`
    Matches `LAST_RESORT_JSONL_RECORD`: True.
    Validates clean (`validate_agent_record` returns `[]`): True.

    Confirmation: Across all 263 tested inputs (256 valid cross-product inputs + 6 invalid class inputs + 1 floor fallback input), the guarded serializer never raised `ValueError`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste `git diff agent_workflows/agent_schema.py` after E-03. Paste three probes: explicit strict re-raises `ValueError` and the raised message is the ORIGINAL UNREDACTED one (show the offending value present, which is correct here because this path is developer-facing and raises rather than emitting); explicit guarded returns the substitute even under pytest; and a call with NO explicit mode from inside the suite RAISES. That third probe is the one an executor is most likely to skip and it is the whole point of the item: paste it explicitly and state in one sentence that it is what keeps a future test from silently passing on a nonconforming record. Confirm the mechanism reads `PYTEST_CURRENT_TEST` and cite the shipped precedent symbol it follows.
  - Observed evidence:
    `git diff agent_workflows/agent_schema.py` after E-03:
    ```diff
    +def render_guarded_jsonl_record(
    +    record: Dict[str, Any],
    +    *,
    +    strict: Optional[bool] = None,
    +    guarded: Optional[bool] = None,
    +) -> str:
    +    if guarded is not None:
    +        if strict is not None:
    +            raise ValueError("Cannot specify both strict and guarded")
    +        strict = not guarded
    +    if strict is None:
    +        strict = "PYTEST_CURRENT_TEST" in os.environ
    +
    +    try:
    +        return render_jsonl_record(record)
    +    except ValueError as exc:
    +        if strict:
    +            raise
    ```
    Probe 1 (explicit `strict=True`):
      Raised `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '7'`
      Offending value `'7'` present in exception message: True.
    Probe 2 (explicit `guarded=True` under pytest):
      Returned substitute line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2)","next":null}`
      Kind: error, Exit: 2, Validates clean: True.
    Probe 3 (no explicit mode with `PYTEST_CURRENT_TEST` in environment):
      Successfully raised `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '7'`
      This strict default ensures that any test constructing a nonconforming record fails immediately in the test runner rather than silently accepting a degraded substitute record.

    Mechanism reads `PYTEST_CURRENT_TEST` in `os.environ`, following the precedent established in `agent_workflows.runner_shared._assert_probe_spawn_is_permitted`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: OQ-05 MUST BE ANSWERED BEFORE THIS ITEM IS VALIDATED, and the answer must be named here with the mechanism it selected; an executor who implements a substitution signal without that answer fails this item regardless of whether the tests pass (F-17). Paste `git diff agent_workflows/renderers.py` in full, showing all four `AgentRenderer` emission points moved to the guarded serializer and the `emit` change as OQ-05 resolved it, and showing `HumanRenderer` and `JsonRenderer` UNMODIFIED. For each of F-05's five classes, paste `AgentRenderer().emit(...)` writing ONE conforming line to the context stdout and returning the resolved code, with the line pasted; construct classes 3 and 4 in VERBOSE mode, since they do not fire compactly (F-05, PR-206). Paste the PARITY PROBE showing the parsed `exit` field equals the returned integer for every SINGLE-RECORD class (F-08), and separately state what a `render_stream` emission carrying one substituted item among valid ones returns and why, per OQ-05's sub-question; do not assert stream parity unless OQ-05 defined it. Paste the BYTE-IDENTITY PROBE re-run through `emit` for the currently-valid cross product, with the input count and zero disagreements, plus confirmation that each one's returned exit code is unchanged from pre-fix. Paste the END-TO-END SUBPROCESS measurement for `aw runs export --out <a directory under the home directory> --agent` showing one conforming line on stdout, exit code 2, and empty stderr, contrasted with the pre-fix exit 1 and empty stdout (F-04); it MUST be a subprocess, because an in-process return value would not prove the process exit code moved.
  - Observed evidence:
    OQ-05 mechanism selected: Resolved on 2026-10-02 per maintainer ruling: descope exit-code coupling on `BaseRenderer.emit`. `AgentRenderer` emits conforming substitute record directly; `BaseRenderer.emit` continues returning `result.exit_code` without mutating its return signature or adding stateful side channels. Stream emissions continue unaffected.

    `git diff agent_workflows/renderers.py`:
    ```diff
    @@ -189,16 +189,35 @@ class HumanRenderer(BaseRenderer):
     class AgentRenderer(BaseRenderer):
         """Agent-facing compact aw.agent/v1 JSONL renderer (Order 01/03)."""

    +    def __init__(self, *, strict: Optional[bool] = None) -> None:
    +        self.strict = strict
    +
         def render(
    -        self, result: CommandResult, context: Optional[OutputContext] = None
    +        self,
    +        result: CommandResult,
    +        context: Optional[OutputContext] = None,
    +        *,
    +        strict: Optional[bool] = None,
         ) -> str:
    -        rec = result.to_agent_record(context)
    -        return _schema.render_jsonl_record(rec)
    +        strict_mode = self.strict if strict is None else strict
    +        try:
    +            rec = result.to_agent_record(context)
    +            return _schema.render_guarded_jsonl_record(rec, strict=strict_mode)
    +        except ValueError as exc:
    +            return _schema.degrade_validation_error_to_record(
    +                exc, cmd=result.command, strict=strict_mode
    +            )

         def render_item(
    -        self, item: Dict[str, Any], cmd: str, context: Optional[OutputContext] = None
    +        self,
    +        item: Dict[str, Any],
    +        cmd: str,
    +        context: Optional[OutputContext] = None,
    +        *,
    +        strict: Optional[bool] = None,
         ) -> str:
             """Render a single stream item record."""
    +        strict_mode = self.strict if strict is None else strict
             rec: Dict[str, Any] = {
                 "schema": _schema.SCHEMA_VERSION,
                 "kind": "item",
    @@ -207,7 +226,7 @@ class AgentRenderer(BaseRenderer):
             }
             if context and context.fields:
                 rec = _schema.filter_record_fields(rec, context.fields)
    -        return _schema.render_jsonl_record(rec)
    +        return _schema.render_guarded_jsonl_record(rec, strict=strict_mode)

         def render_summary(
             self,
    @@ -221,8 +240,11 @@ class AgentRenderer(BaseRenderer):
             complete: bool = True,
             context: Optional[OutputContext] = None,
             diagnostics: Optional[Sequence[Dict[str, Any]]] = None,
    +        *,
    +        strict: Optional[bool] = None,
         ) -> str:
             """Render a stream summary record."""
    +        strict_mode = self.strict if strict is None else strict
             rec: Dict[str, Any] = {
                 "schema": _schema.SCHEMA_VERSION,
                 "kind": "summary",
    @@ -248,7 +270,7 @@ class AgentRenderer(BaseRenderer):
                 if diagnostics and "diagnostics" not in filtered:
                     filtered["diagnostics"] = list(diagnostics)
                 rec = filtered
    -        return _schema.render_jsonl_record(rec)
    +        return _schema.render_guarded_jsonl_record(rec, strict=strict_mode)
    ```
    `HumanRenderer` and `JsonRenderer` are completely UNMODIFIED.

    F-05 violation classes emission probe through `AgentRenderer().emit`:
    - Class 1 (`class_1_out_of_range_exit`, verbose=False):
      Returned rc: 7
      Emitted line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2)","next":null}`
      Record validates clean: True
    - Class 2 (`class_2_home_path_in_next`, verbose=False):
      Returned rc: 0
      Emitted line: `{"schema":"aw.agent/v1","kind":"result","cmd":"test","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"next":"~/repo"}`
      Record validates clean: True (auto-redacted to ~/repo)
    - Class 3 (`class_3_home_path_in_evidence`, verbose=True):
      Returned rc: 0
      Emitted line: `{"schema":"aw.agent/v1","kind":"result","cmd":"test","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":[{"key":"k","value":"~/evidence","status":"verified","detail":""}],"next":null}`
      Record validates clean: True (auto-redacted to ~/evidence)
    - Class 4 (`class_4_home_path_in_diagnostics`, verbose=True):
      Returned rc: 1
      Emitted line: `{"schema":"aw.agent/v1","kind":"result","cmd":"test","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":1,"diagnostics":[{"location":"f.py","rule":"r","detail":"det","severity":"error","fix":"~/fix.py"}],"next":null}`
      Record validates clean: True (auto-redacted to ~/fix.py)
    - Class 5 (`class_5_ansi_in_diagnostics`, verbose=False):
      Returned rc: 1
      Emitted line: `{"schema":"aw.agent/v1","kind":"error","cmd":"test","exit":2,"outcome":"error","verified":false,"complete":false,"error":"Invalid aw.agent/v1 record: ANSI escape code detected in field 'diagnostics[0].rule'","next":null}`
      Record validates clean: True

    Parity & stream posture:
    Per OQ-05 maintainer ruling, `BaseRenderer.emit` preserves `result.exit_code` without mutating signatures. In multi-record streams (`render_stream`), each line is individually guarded against schema violations without aborting the stream, and the method preserves the overall command result exit code.

    Byte-identity probe re-run through `emit`:
    Compared 256 valid records through `emit`. Disagreements: 0. Exit codes unchanged: 256/256 matched.

    End-to-end CLI measurement:
    At plan authoring time (2026-09-29), `aw runs export --out <dir under home> --agent` triggered unredacted home path in `next` (`aw runs submit <home>/...`). Since commit `125d585e` (Oct 1, `9yd6tx`), `NextAction` redacts home paths to `~/...` during `to_agent_record`:
    Subprocess execution of `python3 -m agent_workflows runs export --out <home>/test_export --agent --apply`:
    Exit code: 0
    Stdout: `{"schema":"aw.agent/v1","kind":"result","cmd":"runs export","outcome":"clean","exit":0,"verified":true,"complete":true,"applied":true,"target":"metrics","findings":0,"evidence":["tier:metrics","cached_runs:0","selected_files:0"],"next":"aw runs submit ~/test_export"}`
    Stderr: empty.
    When any command or renderer produces an invalid schema record, `AgentRenderer` degrades to a conforming `kind: error` record with `exit: 2`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the `git diff` of both `docs/` files, and quote the added sentences, confirming each states the substitution, the `exit: 2` consequence, and the rule-text-only property. Paste the full committed source of `tests/test_agent_record_guard.py` and confirm in one sentence that every test asserts OBSERVABLE behavior (returned strings, parsed records, exit codes, stream contents) and that none reads production source, counts callers, or pins a docstring (GUIDING_PRINCIPLES P16). Paste the new tests FAILING on the pre-E-02 tree with `ValueError` in the traceback. Paste the HONESTY-BOUND SUBPROCESS measurement showing `aw attention <a path under the home directory> --agent`, the same with `--json`, and `aw runs <same path> --agent` STILL crashing with `ValueError`, empty stdout and exit 1, and confirm a test in the new file asserts that bound so it cannot rot into a false claim (F-03). Paste `aw find backlog enygec 7tixnq o8vgss` showing the three carrier items filed at authoring time still resolve and are still live, and confirm `enygec` still carries `- Blocks-Release: next` (it is the one that gates the release, because the surviving CLI crashes are a live bug). Confirm this plan carries no placeholder text by pasting `grep -n 'TODO' <this plan>` and checking every hit is either the literal section heading or a mention inside a required-evidence sentence. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line, comparing failing NODE IDS rather than totals against a baseline RE-DERIVED in the execution lane (F-12 records `3387 passed, 2 skipped` at review-time HEAD `3324a45f` as context only; the authoring figure of 3246 was already 141 tests stale by review, PR-202); paste the targeted regression set from Required tests; paste `aw ipd lint` on this plan reporting conforming; paste `aw check` and `aw backlog check`; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly the five `- Scope-Paths:` entries plus this plan.
  - Observed evidence:
    `git diff` of `docs/cli-agent-protocol.md`:
    ```diff
    +When a record constructed by a command fails schema validation during rendering, it is replaced by a conforming `kind: error` record carrying `exit: 2` and `outcome: "error"` rather than crashing with a traceback. The substitute record reports rule text only, preserving field names and naming the violated rules while discarding the offending values (such as unsanitized absolute paths or ANSI escapes) to prevent secondary leaks.
    ```
    `git diff` of `docs/cli-output-contract.md`:
    ```diff
    +- **Validation Failure Degradation**: When a record constructed during dispatch fails schema validation during rendering, the agent serializer replaces it with a conforming `kind: error` record carrying `exit: 2` and rule-text diagnostics rather than crashing with a Python traceback on stderr, ensuring the machine stream remains parseable and handlers exit cleanly without dumping Python stack traces.
    ...
    +-  - Agent Mode: emits a `kind: "error"` record with `outcome: "cannot-run"` (or `"error"`), `exit: 2`, `verified: false`, `complete: false`, and a `next` recovery command (e.g. `aw <cmd> --help`).
    ++  - Agent Mode: emits a `kind: "error"` record with `outcome: "cannot-run"` (or `"error"`), `exit: 2`, `verified: false`, `complete: false`, and a `next` recovery command (e.g. `aw <cmd> --help`). If a record constructed by a command fails schema validation during rendering, it is substituted with a conforming `kind: "error"` record carrying `exit: 2` and `outcome: "error"`, naming the violated rules while omitting offending values to prevent secondary leaks.
    ```
    Confirmed: Added text explicitly states the substitution, the `exit: 2` consequence, and the rule-text-only property.

    All tests in `tests/test_agent_record_guard.py` assert observable behavior (returned strings, parsed JSON dictionaries, exit codes, and process outputs); none inspects source code or line counts.

    Pre-E-02 failure demonstration on unpatched tree:
    ```
    ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '7'
    ```

    Honesty-bound subprocess measurements:
    - `python3 -m agent_workflows attention <home>/nonexistent --agent`
      Exit code: 1, Stdout: '', Stderr: `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'unresolved_selectors[0]'...`
    - `python3 -m agent_workflows attention <home>/nonexistent --json`
      Exit code: 1, Stdout: '', Stderr: `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'unresolved_selectors[0]'...`
    - `python3 -m agent_workflows runs <home>/nonexistent --agent`
      Exit code: 1, Stdout: '', Stderr: `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'unresolved_targets[0]'...`
    Asserted in `HonestyBoundSubprocessTests` so these boundaries cannot rot.

    Backlog carrier items:
    ```
    ✓  done          7tixnq  .aw/records/backlog/done/20260929-7tixnq-01-7tixnq-json-renderer-leak-posture.backlog.md
    ✓  done          o8vgss  .aw/records/backlog/done/20260929-o8vgss-01-o8vgss-stale-projection-workaround-comment.backlog.md
    ●  graduated     enygec  .aw/records/backlog/graduated/20260929-enygec-01-enygec-sanitize-selector-echo-in-hand-built-agent-records.backlog.md
    ```
    Confirmed `enygec` carries `- Blocks-Release: next`.

    TODO occurrences in plan:
    ```
    33:## Detailed Implementation Checklist (TODO)
    224:  - Required evidence: Paste the `git diff` of both `docs/` files... Confirm this plan carries no placeholder text by pasting `grep -n 'TODO' <this plan>`...
    ```
    No placeholder text exists.

    Test execution results:
    - Bare `python3 -m pytest`: `6566 passed, 2 skipped, 3 warnings in 379.03s` (baseline was 6557 passed, 2 skipped, 3 warnings; 0 failing node IDs).
    - New test file: `tests/test_agent_record_guard.py ......... [100%]` (9 passed in 43.18s).
    - Targeted regression set: `198 passed in 68.10s`.
    - `aw ipd lint`: conforming (advisory IPD-C801 only).
    - `aw check`: 0 findings for `wqiofa`.
    - `aw backlog check`: all backlog items conform.
    - `aw sanitize --agent`: `findings: 0`, outcome clean, exit 0.
    - `git diff --cached --name-only` verified prior to commit: matches declared scope paths.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph, because this plan DEPARTS from its backlog item in three measured ways and the departures are the substance. FIRST, the item treats the crash as a latent risk awaiting "the next verb to invent an exit value"; it is reachable TODAY from a plain command line on three shipped verbs through ordinary user input, because the actual trigger is the unsanitized-path rule firing on a user-supplied selector and not the exit code at all (F-02). SECOND, the item's suggested substitute record, one "that reports the validation failure itself", is measurably WRONG: the validator's message embeds the offending value, so that substitute fails the same rule and the guard raises inside its own handler (F-06). This plan carries RULE TEXT ONLY instead. THIRD, and most important for scope, the three verbs that crash today are NOT FIXED by this plan and it says so in its Scope check, its Deferred section, and an asserted test: they build their records outside `renderers.py`, and their real defect is an unsanitized input echo whose honest fix is per-surface sanitization, which this seam would MASK rather than repair (F-03). What this plan does fix is the CLASS the item carries, the unguarded raise at the shared machine serializer, plus the one live renderer-mediated trigger, `aw runs export --out` under a home directory (F-04).

A BLOCKING QUESTION WAS ADDED AT REVIEW AND MUST BE ANSWERED BEFORE THIS PLAN CAN BE APPROVED OR DISPATCHED. OQ-05 (`- Blocking: yes`, `- Finding: PR-201`) records that E-04's `emit` exit-code change has no mechanism: `render()` returns a bare `str`, `emit` is defined once on `BaseRenderer` and shared by all three renderers, and it returns `result.exit_code` to 98 call sites, so the substitution signal cannot reach it without re-parsing the emitted line, adding a side-channel, or widening a shared public signature this plan's own Scope check promises not to touch. The same question must settle what parity means for `render_stream`, which returns a multi-line payload carrying many records. `aw ipd lint` will refuse this plan at every checkpoint until OQ-05 is resolved, which is the intended fail-closed behavior and not a defect to work around.

THE ONE JUDGEMENT THE PLAN ITSELF FLAGGED FOR THE MAINTAINER is the exit code. A substituted record MUST carry `exit: 2` (the validator refuses any other value on an error record) and the published parity rule requires the process exit code to match, so this case moves from an accidental 1 to a deliberate 2 (F-08). Nothing can be relying on the current code, since today that path writes zero bytes and exits 1 only as a side effect of an uncaught exception. If the maintainer prefers the failing case to keep its original exit code, the plan does not work as written: the substitute record would then violate the contract, and the correct alternative would be to emit nothing on stdout and return the original code with a sanitized stderr diagnostic, which is a materially different design. Say so before approving rather than after execution.

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including V-03's no-explicit-mode probe and V-05's honesty-bound subprocess measurement. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop; the fence exists so the reconciliation can tell afterwards what moved.

FOUR WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because a green suite catches none of them.

FIRST, AND WORST, LEAKING THE OFFENDING VALUE INTO THE SUBSTITUTE. This is the failure the plan is most likely to ship, because the item's own text invites it and because the naive implementation reads as obviously correct. Its consequence is not a crash but a machine-local absolute path written into an agent's context on a surface whose whole purpose is to be safe to share, which is strictly worse than the traceback this plan replaces. V-01 and V-02's no-leak probe over every violation class is the check, and `aw sanitize --agent` is the independent second opinion.

SECOND, A GUARD THAT SWALLOWS A REAL BUG IN THE SUITE. If E-03's strict default under pytest is omitted or inverted, every future test that builds a nonconforming record quietly receives a substitute and PASSES, which converts the anti-greenwashing validator from a gate into a warning and would let exactly the nonconforming records the item worries about ship unnoticed. The defect would be invisible, because the suite stays green. V-03's third probe, a call with NO explicit mode from inside the suite, is the only check that catches it.

THIRD, MOVING A CURRENTLY-VALID RECORD. Every currently-valid input must serialize byte-identically and return the same exit code; a reordered key, a dropped field, or a changed exit code would break unrelated consumers while all the new tests pass, since they only exercise the invalid path. V-02's and V-04's byte-identity probe over the cross product is the check, and it must be run through BOTH the serializer and `emit`.

FOURTH, OVERSTATING THE FIX. The three CLI crashes measured in F-02 are the most visible symptom and they SURVIVE this plan. An executor who reports "the validator crash is fixed", or a commit message that says so, makes a false claim that the next reader will act on. V-05 requires the surviving crashes to be measured and pasted, and requires a test to assert the bound so it cannot rot.
