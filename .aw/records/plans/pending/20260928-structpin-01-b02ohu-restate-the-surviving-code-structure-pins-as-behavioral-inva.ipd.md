# IPD: Restate the six surviving code-structure pins as behavioral invariants and delete the dead census tables

- Date: 2026-09-28
- Kind: child
- Concern: SIX TESTS STILL READ PRODUCTION SOURCE TO ASSERT CODE STRUCTURE, which `GUIDING_PRINCIPLES.md` P16 prohibits outright, and one of them was REINTRODUCED four days AFTER the sweep that deleted its ancestor. Measured at HEAD `a314c925`: exactly FOUR test files in the whole suite call `inspect.getsource`/`ast.parse`/`ast.walk`/`ast.unparse`, and one of the four (`tests/test_carrier_scan_single_item_contract.py`) is the sanctioned exception. The other three hold six pins, enumerated in Findings as A1..A6. The resurrection is the load-bearing fact, because it shows the written policy alone does not hold: commit `80db6750` (2026-09-23) deleted 366 code-structure tests, `19313eed` (2026-09-24) removed `OneOriginatingDefinitionTests` from `tests/test_term.py` (verified by reading `19313eed^:tests/test_term.py`, where that class sits with its `ast.parse` walk), and then `64c04288` (2026-09-28T14:09) ADDED `SingleOriginatingDefinitionTests` to `tests/test_interactivity_resolver.py`, whose own docstring says it is "Recovered from commit `19313eed^:tests/test_term.py`". P16 itself landed LATER the same day, in `6a6eb66c` (2026-09-28T18:16), so the recovery predates the written prohibition and nothing mechanical noticed. The backlog item states the general defect: a count-shaped pin is "a tax on correct changes and a false signal about incorrect ones", since a badly-wired new call site and a well-wired one produce the same number.
- Scope: Restate or delete the SIX surviving code-structure pins (A1..A6) so each asserts the invariant it stands for through the code's observable behavior, and delete THREE dead census residues (D1..D3) that no test reads. Every replacement is proven feasible by measurement recorded in Findings, so this plan changes test mechanism WITHOUT weakening any claim. EXCLUDES the guard that stops new pins being written, which is Order 02 (`76ic0k`) and depends on this plan landing first. EXCLUDES every row in Findings marked LEGITIMATE or BEHAVIORAL, naming them explicitly so a later reader does not re-litigate them. EXCLUDES `tests/test_walkthrough_id6.py`, whose literal `24` is a census over the live RECORDS tree rather than over code structure; it is filed separately (see Deferred).
- Scope-Paths: tests/test_runner_shared.py, tests/test_host_capability_wiring.py, tests/test_interactivity_resolver.py, tests/test_spec_review_attestation.py, tests/test_lifecycle_style.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 5zyuc8
- Set: structpin
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: b02ohu

## Workflow history

- 2026-09-28 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `5zyuc8`, whose 2026-09-28 maintainer ruling is that tests pinning code structure, call counts, or census numbers "must be eliminated". The item's own nine named tests are ALL GONE already (verified one by one, recorded in Findings), so this plan carries the RESIDUE the item's SUGGESTED WORK asks for: the six pins that survive in the tree today. Every proposed replacement was EXECUTED against HEAD before being written down, so no E-item proposes a mechanism that has not been shown to work; the measurements are pasted in Findings. One proposal was REFUTED by that measurement and is recorded as such: substituting `vars(module)` for `ast.parse` in A3 does NOT preserve the test's claim, because `vars()` cannot distinguish a local definition from a re-export, so A3 takes a different route than the obvious one.
- 2026-09-28 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Leave the suite with ZERO code-structure pins outside the one sanctioned exception, while every invariant those
pins stood for remains asserted through behavior the code actually exhibits when it runs.

The test of success is not "the `ast` import is gone". It is that a well-wired new call site, the change the
backlog item watched turn nine tests red, provokes no failure, while a genuinely broken wiring still does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the three pins whose behavioral replacement is already present or proven

- [ ] E-01 DELETE A4 OUTRIGHT, `test_runner_shared_references_preflight_host_capabilities` in `tests/test_host_capability_wiring.py`, BECAUSE ITS BEHAVIORAL SIBLING IN THE SAME FILE IS STRICTLY STRONGER AND ALREADY PASSES. The pin `ast.parse`s `runner_shared.__file__`, unions every `ast.Name.id`, `FunctionDef.name`, `alias.name` and `Attribute.attr` in the module, and asserts the STRING `"preflight_host_capabilities"` appears somewhere in that set; its own docstring calls itself the "Inverse of E-01 baseline (where rg -c exits 1 with zero call sites)", i.e. it is a call-site census by construction. It therefore passes when the name appears in a dead branch, an unreachable import, or a comment-adjacent alias, which is precisely the "false signal about incorrect ones" half of the backlog item's general defect. The next test in the same file, `test_execute_item_core_refuses_when_host_capability_unavailable_and_starts_no_session`, DRIVES `runner_shared.execute_item_core` with `hsp.forced_runner_safety_verdicts({hsp.CAP_COMMIT_GATEWAY: (False, ...)})` and asserts the item ends `fail-gate`, the refusal is recorded, the `host-capability-unavailable` event is written, and `spawn_executor`/`spawn_verifier` are never called; that proves the gate is REACHED and REFUSES, which is what the deleted test was a proxy for. Do NOT replace it with anything: a second test asserting the same reachability would be the duplication P8 forbids. Delete the now-unused `ast` and `Path`-for-source imports ONLY if nothing else in the file uses them; check rather than assume.
  - Depends on: none
  - Expected outcome: `test_runner_shared_references_preflight_host_capabilities` absent from `tests/test_host_capability_wiring.py`; the file's remaining tests pass; a pasted `python3 -m pytest tests/test_host_capability_wiring.py` showing the surviving count (authoring baseline: the file's tests are part of the 28 that pass in `tests/test_host_capability_wiring.py tests/test_interactivity_resolver.py tests/test_walkthrough_id6.py` together, so re-derive the per-file number at execution rather than trusting that aggregate).
  - Execution state: pending

- [ ] E-02 REMOVE THE TWO `inspect.getsource` + `assertIn` LINES OF A2 IN `tests/test_runner_shared.py::test_set_plan_approved_durable_history_pin`, KEEPING EVERY OTHER ASSERTION IN THAT TEST. The two lines read the source of `runner_shared.initialize_run_core` and `runner_shared.execute_item_core` and assert the literal spellings `"set_plan_approved_fn(repo, id6)"` and `'set_plan_approved(repo, item["id6"])'` appear in them, with the stated intent that the call passes "exactly two arguments". Both are satisfiable by a COMMENT containing that text and both break on a rename or a reformat that splits the call across lines, so neither proves what it claims. The SAME test already proves the real property behaviorally, immediately below: it patches `host.run_checked` with a capturing fake, calls `host.set_plan_approved(pathlib.Path("/tmp/repo"), "pln001")` for both hosts, and asserts on the captured argv (`--actor` value, `-m` value). Keep the `inspect.signature` assertions in the same test untouched: `signature(...).parameters["message"].default` interrogates a CALLABLE, not source text, and a required-versus-defaulted parameter is a caller-visible API contract, which is the BEHAVIORAL row in Findings and not a pin.
  - Depends on: none
  - Expected outcome: no `inspect.getsource` call remains anywhere in `tests/test_runner_shared.py` (verified by search, pasted); `test_set_plan_approved_durable_history_pin` still asserts the argv and the signature defaults, and passes.
  - Execution state: pending

- [ ] E-03 REPLACE A5 AND A6 IN `tests/test_interactivity_resolver.py` WITH A MONKEYPATCH REACHABILITY PROOF, WHICH IS MEASURED TO WORK FOR ALL FIVE DELEGATIONS. `SingleOriginatingDefinitionTests` holds two pins: `test_exactly_one_originating_is_interactive_in_package` walks every `*.py` in the package with `ast.parse` and asserts exactly one top-level `def is_interactive` lives in `term.py` (an architectural placement pin, P16's fourth prohibition verbatim), and `test_sanctioned_delegations_are_closed_and_reach_term_resolver` `ast.parse`s five named modules and asserts each named function's body CONTAINS a `Call` to `is_interactive`/`is_forced_noninteractive` (a spelling pin over a hardcoded `SANCTIONED_DELEGATIONS` list of five `(file, func)` pairs, which goes stale the moment a delegation is rehomed). Replace BOTH with one test that proves the property they actually want, that every delegation's answer is DECIDED BY the one resolver: for each of the five, patch `term.is_interactive` to return `True` then `False` and assert the delegation's own return value FOLLOWS it. Measured at HEAD, all five flip: `artifact_adopt.leak_gate_is_interactive(environ={})`, `git_commit_helper._is_interactive()`, `runner_stop.interrupt_menu_is_safe()`, `runner_shared.is_interactive_run()` each returned `True` under the `True` patch and `False` under the `False` patch, and `engine.is_interactive_session(SimpleNamespace(yes=False))` did likewise. This is strictly stronger than the pins: a delegation that merely MENTIONS the resolver but returns a hardcoded value passes the old test and fails this one. ALSO PIN `engine.is_interactive_session`'S SHORT CIRCUIT, measured to return `False` for `SimpleNamespace(yes=True)` even while the resolver is patched `True`, because that branch is real behavior the pins never covered and deleting them must not lose it. Keep `SANCTIONED_DELEGATIONS` as the loop's data (it is now a list of things to EXERCISE, not a census to match), and delete `_is_pure_delegation`, which exists only to serve the AST route.
  - Depends on: none
  - Expected outcome: no `ast.parse`/`ast.walk` call remains in `tests/test_interactivity_resolver.py` (verified by search, pasted); the replacement test drives all five delegations under both patch values plus the `yes=True` short circuit, and passes; `_is_pure_delegation` deleted.
  - Execution state: pending

### Task group 2: the two pins needing a designed replacement, and the one the obvious fix would break

- [ ] E-04 REPLACE A1, `test_add_output_mode_flags_not_reforked_in_hosts` in `tests/test_runner_shared.py`, WITH AN OPTION-SURFACE AND REFUSAL COMPARISON ACROSS BOTH HOSTS. The pin is the purest structural assertion in the suite: it `ast.parse`s `oc_runipd.py` and `agy_runipd.py`, asserts each `_add_output_mode_flags` has exactly ONE `FunctionDef` and exactly ONE body statement after stripping the docstring, `ast.unparse`s that statement and string-compares it to `"runner_shared.add_output_mode_flags"`, then walks for `add_argument`/`add_mutually_exclusive_group`. Its own docstring already concedes the coverage bound ("It cannot detect a runtime rebinding"). The invariant is that BOTH HOSTS' OUTPUT-MODE FLAGS COME FROM ONE REGISTRAR AND THEREFORE CANNOT DIVERGE, which is observable on the built parsers. Measured at HEAD: `runner_shared.add_output_mode_flags` applied to a bare `ArgumentParser` yields option strings `--quiet, --raw, --verbose, -v` (plus argparse's own `-h/--help`) and exactly one mutually exclusive group `['--quiet', '--raw']`; each host's `start` subparser independently yields `['--quiet','--raw','--verbose','-v']` and the SAME single exclusive group; and `parse_args(["--raw","--quiet"])` refuses on BOTH hosts with exit code 2, stderr `runipd start: error: argument --quiet: not allowed with argument --raw` and `runagy start: error: ...` respectively. Assert THAT: build the reference surface from the shared registrar, build both hosts' `start` and `resume` subparsers, and assert the option set and the exclusive-group partition agree with the reference and with each other, plus the observable `--raw --quiet` refusal per host. A re-fork that reproduces the surface exactly is then INDISTINGUISHABLE and permitted, which is correct and is the point: the contract is the surface, not the number of `def`s. Keep the class's other two tests (`test_output_mode_help_text_pinned_by_value_per_host`, `test_verbosity_default_asymmetry_on_both_hosts`) untouched; they build real parsers and are the LEGITIMATE operator-visible flag surface.
  - Depends on: none
  - Expected outcome: no `ast.parse`/`ast.unparse`/`ast.walk` call remains in `tests/test_runner_shared.py` (verified by search, pasted, and this is the last of them given E-02 and E-06); the replacement asserts the option set, the exclusive-group partition and the per-host refusal for `start` and `resume`; shown RED against a deliberate local divergence (add a stray flag to one host's subparser, observe failure, revert) so it is proven non-vacuous.
  - Execution state: pending

- [ ] E-05 REWRITE A3, `test_no_divergent_codefined_constants_in_runner_shared`, AS AN IDENTITY-PARTITIONED VALUE CHECK, AND DO NOT USE `vars()` AS THE ENUMERATOR, BECAUSE MEASUREMENT REFUTES THAT SUBSTITUTION. The pin `ast.parse`s all three modules to collect module-level UPPER_CASE assignments, then compares RESOLVED values via `getattr`. The value comparison is already behavioral; only the ENUMERATION is structural. The obvious fix is `vars(mod)` filtered by `isupper()`, and IT DOES NOT PRESERVE THE TEST'S CLAIM: measured at HEAD, `vars()` finds 39 UPPER names common to all three modules, but 38 of them are the IDENTICAL OBJECT as `runner_shared`'s (`getattr(oc, k) is getattr(rs, k)`), i.e. they are re-exports or `from . import` bindings for which divergence is impossible by construction, and only ONE name is genuinely co-defined: `DEFAULT_STALL_TIMEOUT`, assigned independently in all three modules (`runner_shared.py`, `oc_runipd.py`, `agy_runipd.py`) and equal to `900.0` in each. So a `vars()` rewrite would silently widen the test from 1 real subject to 39 mostly-vacuous ones. Rewrite it to use the IDENTITY PARTITION as the mechanism: enumerate with `vars()`, then for each common UPPER name assert EITHER the host binding IS the shared object (a re-export, nothing to diverge) OR its value EQUALS the shared value (a genuine co-definition that must agree). That is one assertion covering both cases, it reads no source, it needs no hardcoded list, and it extends itself when a constant is added or a re-export becomes a co-definition. State the residual bound in the test's docstring honestly: a co-defined constant deliberately intended to differ per host would now have to be excluded by name, and none exists today.
  - Depends on: none
  - Expected outcome: the rewritten test reads no source, asserts the identity-or-equality partition over the common UPPER names, and passes; the pasted measurement showing 39 common names of which 38 are identity re-exports and 1 (`DEFAULT_STALL_TIMEOUT`) is genuinely co-defined; shown RED by locally setting one host's `DEFAULT_STALL_TIMEOUT` to a different value, then reverted.
  - Execution state: pending

### Task group 3: the dead residue no test reads

- [ ] E-06 DELETE THE THREE DEAD CENSUS RESIDUES D1..D3, WHICH ARE UNREACHABLE DATA RATHER THAN TESTS. (a) `tests/test_spec_review_attestation.py::OneSharedPredicateTests` is a `unittest.TestCase` with ZERO test methods: verified by AST that its body is exactly `[Expr, Assign, Assign]` (a docstring plus `DEFINITIONS` and `CALL_SITES`), and each table name has exactly one reference in the repository, its own definition. Its docstring even records the history, "Two source-census tests became one table". Delete the class; the predicate-sharing property it describes is covered by `check.spec-review-unattested` and the setter tests in the same file, so nothing is lost. Confirm that coverage before deleting rather than asserting it. (b) In `tests/test_runner_shared.py`, delete the orphaned census tables whose reader was removed: `ALL_SHARED_RUN_CHECKED_CALLERS`, `HOST_NAMING_ONLY`, `REDOCUMENTED_SINCE_MOVE`, `INTEGRATION_CAUSE_SHARED` and `LANE_INTEGRATION_WRAPPED` each have exactly ONE repository reference (their own definition), and `RELOCATED_RUN_CHECKED_CALLERS`, `NATIVE_SHARED_RUN_CHECKED_CALLERS`, `REHOMED_BACKLOG_CLOSE_CALL_SITES` and `UNMOVABLE` have exactly TWO, each referenced only by another dead table, so the set is closed and removable together. They carry per-symbol call counts as data (`"build_lane_outcome": 3`, `("oc_runipd","run_checked"): 3`), which is the census shape the backlog item names. The file header already records that the harness reading them "was deleted in `19313eed`". Re-measure the reference counts at execution before deleting; do not trust these numbers. (c) In `tests/test_lifecycle_style.py`, delete `MODULE_PATH = REPO / "agent_workflows" / "lifecycle_style.py"`, a production-source path constant with no reader (one reference, its own definition), left behind by a deleted source pin. Also drop any import left unused by these three deletions, checking rather than assuming.
  - Depends on: none
  - Expected outcome: all three residues gone; a pasted re-measurement of each name's reference count taken BEFORE deletion (to catch a reader added since authoring); `python3 -m pytest tests/test_spec_review_attestation.py tests/test_runner_shared.py tests/test_lifecycle_style.py` green with no collection error.
  - Execution state: pending

### Task group 4: prove the sweep is complete

- [ ] E-07 RUN THE WHOLE-SUITE SCAN AGAIN AND RECONCILE THE TEST-COUNT DELTA, because "the six I knew about are gone" is not the same claim as "none remain", and this plan's value rests on the stronger one. Re-run the scan that produced the Findings table (over every `tests/**/*.py`, for calls to `inspect.getsource`/`getsourcelines`/`getsourcefile` and `ast.parse`/`ast.walk`/`ast.unparse`) and confirm exactly ONE file remains, `tests/test_carrier_scan_single_item_contract.py`. The scan must match the ATTRIBUTE FORM of these calls; a search for the bare names would also match the sanctioned exception's own target strings. Note the scan's own bound honestly: it matches `inspect.getsource(...)` and `ast.parse(...)` as attribute calls, so an aliased import (`from ast import parse`) would evade it; measured at authoring, NO test file uses an aliased or from-import form of either module, so the attribute form is sufficient today, and E-07 must re-confirm that rather than assume it. Then reconcile the bare-suite test count against the execution baseline, attributing every removed test to the E-item that removed it. Report any surviving file this plan did not predict rather than adjusting the scan to exclude it.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: pasted scan output listing exactly one file; pasted `rg` (or equivalent) output showing no aliased/from-import of `ast` or `inspect` in `tests/`; pasted bare `python3 -m pytest` green; a written reconciliation mapping the count delta to E-items.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `GUIDING_PRINCIPLES.md` P16 is the canonical home of this policy, landed in commit `6a6eb66c` ("docs: add policy and principles against code-pinning tests"). It prohibits production source inspection by name (`inspect.getsource`, `inspect.getsourcelines`, `ast.parse`, `read_text()`), count or census pins, text/banner/docstring pins, and architectural placement pins; and it carries ONE narrow exception, for "where the text or file itself is the artifact under test".
- The repository has already swept three times: `856acd63` ("replace source-text pins with behavioral tests (46 -> 6 in 18 files)"), `ba4f205b` ("replace the signal-safety, sandbox and delegation pins with behavior (52 -> 30)"), and `80db6750` ("delete 366 tests that pinned code structure instead of behaviour"). This plan is the residue, not the sweep.
- The sanctioned exception is exercised in exactly three places today, all of which this plan leaves alone: `tests/test_leak_sanitizer.py` and `tests/test_local_leaks.py` read the leak engine's OWN source because that source is the artifact under test (the engine builds sensitive literals from fragments so its own file is not a leak), and `tests/test_artifact_adopt.py` reads `Path(__file__)`, its own module, not production code.
- The suite is run BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, so `python3 -m pytest` is already quiet, parallel and scoped. Adding `-n0`, a second `-q`, or `-p no:randomly` is forbidden by the execution contract. `tests/deselect_notice.py` prints the deselected count in every run.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `a314c925`. The whole-suite scan used `ast` over every `tests/**/*.py`, looking for calls to `inspect.getsource`/`getsourcelines`/`getsourcefile` and `ast.parse`/`ast.walk`/`ast.unparse`. It found FOUR files and 23 call sites:

```
tests/test_carrier_scan_single_item_contract.py: 7 hits -> ['ast.parse', 'ast.walk']
tests/test_host_capability_wiring.py: 5 hits -> ['ast.parse', 'ast.walk']
tests/test_interactivity_resolver.py: 4 hits -> ['ast.parse', 'ast.walk']
tests/test_runner_shared.py: 7 hits -> ['ast.parse', 'ast.unparse', 'ast.walk', 'inspect.getsource']
TOTAL files: 4
```

Attributing the `tests/test_runner_shared.py` hits to their owning tests:

```
  line  4845  ast.parse    in test_no_divergent_codefined_constants_in_runner_shared
  line  4924  inspect.getsource  in test_set_plan_approved_durable_history_pin
  line  4930  inspect.getsource  in test_set_plan_approved_durable_history_pin
  line  5108  ast.parse    in test_add_output_mode_flags_not_reforked_in_hosts
  line  5129  ast.unparse  in test_add_output_mode_flags_not_reforked_in_hosts
  line  5148  ast.unparse  in test_add_output_mode_flags_not_reforked_in_hosts
  line  5156  ast.walk     in test_add_output_mode_flags_not_reforked_in_hosts
```

### The six pins in scope

| Id | Test (by symbol) | Mechanism | Invariant it stands for | Route |
| --- | --- | --- | --- | --- |
| A1 | `test_add_output_mode_flags_not_reforked_in_hosts` | `ast.parse` + one-statement body count + `ast.unparse` string compare | Both hosts' output-mode flags come from one registrar and cannot diverge | E-04, option-surface + exclusive-group + refusal comparison |
| A2 | `test_set_plan_approved_durable_history_pin` (two lines only) | `inspect.getsource` + `assertIn` on a literal call spelling | The call passes exactly two arguments | E-02, delete; the same test already captures argv |
| A3 | `test_no_divergent_codefined_constants_in_runner_shared` | `ast.parse` to enumerate UPPER assignments | No co-defined constant's shared value matches neither host | E-05, identity-partitioned value check |
| A4 | `test_runner_shared_references_preflight_host_capabilities` | `ast.parse` symbol census, asserts a name is present | The capability gate is reachable from the dispatch point | E-01, delete; behavioral sibling is stronger |
| A5 | `test_exactly_one_originating_is_interactive_in_package` | `ast.parse` over the package, one `def` in `term.py` | One originating interactivity decision | E-03, monkeypatch flip over all five delegations |
| A6 | `test_sanctioned_delegations_are_closed_and_reach_term_resolver` | `ast.parse` five modules, assert a `Call` node exists | Each delegation reaches the resolver | E-03, same replacement |

### The three dead residues

| Id | Location | What | Measured reference count |
| --- | --- | --- | --- |
| D1 | `tests/test_spec_review_attestation.py::OneSharedPredicateTests` | A `TestCase` with zero test methods; AST body is `[Expr, Assign, Assign]` | `DEFINITIONS` 1, `CALL_SITES` 1 (definition only) |
| D2 | `tests/test_runner_shared.py` census tables | Nine tables carrying per-symbol call counts as data | Five at 1, four at 2 (each referenced only by another dead table) |
| D3 | `tests/test_lifecycle_style.py::MODULE_PATH` | Production-source path constant | 1 (definition only) |

### The backlog item's own nine tests are already gone

Checked one by one, because the item's SUGGESTED WORK only makes sense once the named cases are accounted for. `mp289j` LANDED (`.aw/records/plans/executed/20260908-reverify-01-mp289j-run-the-existing-verifier-prompt-against-an-already-executed.ipd.md`, `- Status: executed`) and rewrote all nine; the later sweeps then deleted the rewrites. `tests/test_runner_telemetry_integration.py` and `tests/test_rununify_main.py` no longer exist. `VerifierTurnArgvRoutingTests` survives with two behavioral tests and neither is the pin. `OcTelemetryWiringTests` survives with one test whose only `assertEqual(len(...), 1)` counts EMITTED TELEMETRY FILES, an output, not a call site. `HostResumeSpellingTests` survives with two tests that drive a real `Popen` and assert on argv. So this plan carries the RESIDUE, and the item's five-file list is history rather than a work list.

### Explicitly NOT in scope, recorded so a reader does not re-litigate them

- LEGITIMATE CENSUS, where the number IS the operator-visible contract: `tests/test_releases_cli.py::ReleasesParserTests::test_subcommands_are_exactly_list_show_new` (a declared subparser set, paired with an adversarial negative that drives `parse_args` to exit 2); `tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves` (asserts a RELATION between the parser and `COMMAND_INVENTORY`, so it is self-extending and needs no edit when a command is added correctly, and is the model form); `tests/test_host_capability_extension.py::RequirementMapTests::test_requirement_map_structure_and_coverage`; and the flag-surface tests in `tests/test_runner_shared.py` that build real parsers.
- BEHAVIORAL, using `inspect.signature` on a CALLABLE rather than reading source: `tests/test_reap_contract.py::test_clean_shutdown_signature_binds_product_call` (uses `.bind()`, which is behavior), `tests/test_lane_reaper_callshape.py`, `tests/test_run_selection_policy.py::test_allow_mixed_waives_only_type_mixing` (a NEGATIVE API-surface contract: no bypass knob exists, which is a security property), and `tests/test_term.py::FullRowStylingTests::test_lifecycle_row_styling`.
- THE SANCTIONED EXCEPTION: `tests/test_carrier_scan_single_item_contract.py` parses production source, and should be KEPT. Its subject is a quadratic-performance hazard with no behavioral proxy (its header explicitly forbids adding timing assertions as flaky), it asserts ZERO counts as invariants (its one numeric assertion is a `>=` non-vacuity floor), it is self-extending, and it documents its own scope and known hole. Order 02 must allowlist it, not delete it.

## Proposed changes (ordered, validatable)

1. E-01 deletes A4, the weakest pin, whose replacement already exists and passes. Smallest possible first change, and it establishes the pattern the rest follow.
2. E-02 removes A2's two lines, keeping the behavioral remainder of the same test.
3. E-03 replaces A5 and A6 together, since both serve one property and share the hardcoded delegation list.
4. E-04 replaces A1, the largest single rewrite, with the parser-surface comparison.
5. E-05 rewrites A3's enumerator using the identity partition, the one item where the obvious substitution was measured and rejected.
6. E-06 deletes D1..D3, the dead residue, last, so a collection error introduced by an earlier item cannot be misattributed to it.

Items are INDEPENDENT (each declares `Depends on: none`) and are ordered for reviewability, not by necessity. They touch overlapping FILES but disjoint tests; `tests/test_runner_shared.py` is touched by E-02, E-04, E-05 and E-06, so an executor doing them in one pass must keep the edits separable and re-run the file's tests after each.

## Deferred / out of scope (with reason)

- THE GUARD THAT STOPS NEW PINS BEING WRITTEN is Order 02 (`76ic0k`), not this plan. It must land AFTER this one, because a guard added while A1..A6 still exist is red on arrival and its only remedies are a six-entry allowlist (which institutionalizes the pins) or deleting them in the same change (which merges two reviewable concerns).
  - Carrier: 76ic0k
- `tests/test_walkthrough_id6.py::TestWalkthroughDeclaredIdMatchesSlot` asserts `len(all_files) == 24` and `len(exempt) == 11` over the LIVE `.aw/records/walkthroughs/` tree. This is the same "tax on correct changes" shape and it is a LIVE TRIPWIRE: measured at HEAD the tree holds exactly 24 non-README walkthroughs, so the next walkthrough any agent writes turns it red, and the file carries no `livecorpus` marker so it runs in the default suite and would block every concurrent lane's integration. It is nonetheless OUT OF SCOPE here: it is a census over the RECORDS tree, not over CODE STRUCTURE, and the backlog item's SUGGESTED WORK scopes this carrier to code structure. Broadening would be the opportunistic scope growth the execution contract forbids.
  - Carrier: zf1m48
- `tests/test_reaskscore_composed.py::TestSharedConstants::test_terminal_states_three_copies_are_mutually_equal` asserts `len(runner_shared.TERMINAL_STATES) == 24`. This is a runtime data structure, not source text, and the surrounding mutual-equality assertions are the real invariant, so the literal adds nothing and goes stale when a status is legitimately added. Left alone deliberately: it is neither a source pin nor in the item's stated scope, and one redundant literal beside a correct set-equality is not worth widening this plan.
  - Carrier: aaoapo
- `tests/test_term.py::AuthoredSixteenColorPaletteTests` asserts `len(T.STAGE_COLOR_16) == 20` on the line after asserting `set(T.STAGE_COLOR_16) == set(LS.ALL_STAGES)`, so the literal is a cross-check on a derived equality rather than a standalone census. Same reasoning as the row above, and carried by the same item, which names both cases explicitly.
  - Carrier: aaoapo

## Scope check

- Over-scope: none. Every E-item names one test or one closed set of dead names, and all five `Scope-Paths` entries are test files. No production module is touched, which is the correct shape for a plan that changes only how existing behavior is asserted.
- Under-scope: this plan does not prevent a SEVENTH pin being written tomorrow; that is Order 02's whole job, and the resurrection recorded in the Concern is the evidence that the written policy alone is insufficient. It also leaves the two runtime-data literals and the walkthrough census named in Deferred.

## Required tests / validation

Every item's validation demands the actual pasted output of a bare `python3 -m pytest` (or a file-scoped run where the item is file-local), per the execution contract. The suite baseline measured at authoring HEAD `a314c925` is:

```
NOTE: 207 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
3235 passed, 2 skipped, 3 warnings in 53.34s
```

Re-derive that baseline at execution rather than trusting it; the tree moves. Net test count is EXPECTED TO FALL: E-01 removes one test, E-03 replaces two with one, E-06 removes a method-less class (no tests) and dead data (no tests). A green run with a LOWER count is the expected outcome, not a regression, and each validation item must state the delta it expects and reconcile it.

Two items (E-04, E-05) additionally require a RED-then-GREEN demonstration, because a replacement asserting a surface can pass vacuously if it compares a thing to itself. Deliberately break the property locally, paste the failure, revert, paste the pass.

## Spec / documentation sync

N/A. P16 in `GUIDING_PRINCIPLES.md` already states the policy this plan applies, and restating it here or in `CONTRIBUTING.md` would be the duplication P8 forbids. No `.spec.md` file describes the suite's assertion mechanisms, so no spec amendment is owed and no spec path appears in `Scope-Paths`. Order 02 owns the one documentation pointer the Set adds, since that pointer describes the GUARD, which does not exist until Order 02 lands.

## Open questions

### OQ-01: Should A1's replacement permit a re-fork that reproduces the option surface exactly?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as YES, permit it, and additionally assert object identity where identity is what the repository already relies on. This is not a maintainer judgement, because the repository has already settled the same question twice in the same shape. FIRST, `GUIDING_PRINCIPLES.md` P16 answers the general form directly, prohibiting "architectural placement pins" and directing an author to "Test the behavioral contract of the modules instead", so a test refusing a re-fork that is behaviorally indistinguishable is the thing P16 forbids, not a stronger version of it. SECOND, the repository already has a NON-AST mechanism for the single-definition claim and it is in live use: `tests/test_recovone_single_definition.py::TestSingleDefinitionIdentity::test_identity_pins` asserts `assertIs(getattr(host, name), getattr(runner_shared, name))` over three symbols across both hosts, which proves one definition is SHARED without reading a line of source. Measured at authoring, `runner_shared.add_output_mode_flags` exists and both hosts' `start` and `resume` subparsers expose the identical option set (`--quiet`, `--raw`, `--verbose`, `-v`) and the identical single mutually exclusive group (`['--quiet','--raw']`), with `--raw --quiet` refused on both hosts at exit 2. So E-04 stands as written AND may add the `assertIs`-style identity assertion if the executor finds the shared registrar is referenced by name in both hosts; that is an addition inside E-04's stated scope, not a restructuring, and it is strictly behavioral. The maintenance motive behind the original lift (`xw4rb7`/`t0ovw6`), one registrar to edit rather than two, is served by that identity assertion without any AST walk.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a search over `tests/test_host_capability_wiring.py` showing zero matches for `test_runner_shared_references_preflight_host_capabilities` and zero for `ast.parse`, pasted; plus a pasted `python3 -m pytest tests/test_host_capability_wiring.py` showing all remaining tests pass, including `test_execute_item_core_refuses_when_host_capability_unavailable_and_starts_no_session` by name (confirm it is not silently skipped by its `pytest.skip` guard on `RUNNER_ACTION_TO_CONTRACT_ACTION`, which would mean the retained coverage is vacuous; if it DOES skip, say so and stop, because then E-01's premise fails).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a search over `tests/test_runner_shared.py` for `inspect.getsource` returning zero matches, pasted; plus a pasted run of `test_set_plan_approved_durable_history_pin` showing it passes, and a quoted excerpt of the retained argv assertions proving the behavioral half survived the edit.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a search over `tests/test_interactivity_resolver.py` for `ast.` returning zero matches and for `_is_pure_delegation` returning zero, pasted; plus a pasted run of the file showing the replacement passes. The replacement must be shown NON-VACUOUS: temporarily make ONE delegation ignore the resolver (return a hardcoded `True`), paste the resulting failure naming that delegation, revert, paste the pass. Also paste the `yes=True` short-circuit assertion result for `engine.is_interactive_session`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: a search over `tests/test_runner_shared.py` for `ast.parse`, `ast.unparse` and `ast.walk` returning zero matches, pasted. The replacement shown RED then GREEN: add a stray flag (or drop the mutual exclusion) on ONE host's `start` subparser, paste the failure showing it names the diverging host and the differing option or group, revert, paste the pass. Also paste the observed `--raw --quiet` refusal for both hosts including the exit code and the stderr line, confirming the refusal is asserted by observation rather than assumed (authoring baseline to reproduce: exit 2, `runipd start: error: argument --quiet: not allowed with argument --raw` and the `runagy start:` equivalent).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted re-measurement at execution HEAD of the common UPPER-name partition (authoring baseline to reproduce or refute: 39 common names, 38 identity re-exports, 1 genuine co-definition `DEFAULT_STALL_TIMEOUT` equal to `900.0` in all three modules). If that partition has CHANGED, report the new numbers and confirm the rewritten test still covers the genuine co-definitions. Then RED-then-GREEN: set one host's `DEFAULT_STALL_TIMEOUT` to a different value, paste the failure showing it names the constant and prints all three values, revert, paste the pass. The test must be confirmed to read no source (search for `ast.` and `getsource` in the test body, pasted).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: for each of D1, D2 and D3, the reference count re-measured BEFORE deletion and pasted (authoring baselines: `DEFINITIONS` 1, `CALL_SITES` 1; the nine `tests/test_runner_shared.py` tables at 1 or 2; `MODULE_PATH` 1). If any count is HIGHER than its baseline, a reader was added since authoring: do not delete that name, report it instead. Plus an AST-derived confirmation that `OneSharedPredicateTests` holds zero test methods, pasted, taken before deletion. Plus a pasted `python3 -m pytest tests/test_spec_review_attestation.py tests/test_runner_shared.py tests/test_lifecycle_style.py` showing green with no collection error.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: a pasted bare `python3 -m pytest` at the end of execution, green, with the test count stated and the delta from the re-derived execution baseline RECONCILED item by item (which E-item removed or merged which tests). A count that fell by an unexplained amount is a FAILURE of this item, not a pass. Plus the final whole-suite scan output, pasted, showing exactly ONE remaining file, `tests/test_carrier_scan_single_item_contract.py` (the sanctioned exception). Any other surviving file must be named and explained rather than ignored.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTE ONLY WHAT THIS PLAN DECLARES. The five `Scope-Paths` entries are the whole authorized surface, and every one is a test file: if execution appears to require editing a module under `agent_workflows/`, STOP and report, because this plan changes how existing behavior is ASSERTED and must not change the behavior itself. A replacement that needs a production edit to pass has found a real defect, which is a new carrier, not a widening of this one.

DO NOT WEAKEN AN ASSERTION TO MAKE IT PASS. Every replacement here must prove at least as much as the pin it removes, and two items (E-04, E-05) demand a RED-then-GREEN demonstration precisely because a surface comparison can pass vacuously. If a replacement cannot be made non-vacuous, leave the pin in place, mark the item incomplete, and report it: a pin honestly labelled is better than a green test proving nothing, which is the exact failure this plan exists to remove.

HONESTY. Paste actual runner output; never claim a test run you did not perform. The net test count is expected to FALL, so state the delta and reconcile it rather than presenting a lower green count as unchanged. If a reference count measured at execution exceeds its authoring baseline, a reader was added since authoring: report it and do not delete that name.

COMMIT DISCIPLINE. Commit through `aw commit <plan> -- <paths>`, path-scoped to the files this plan names, never `git add -A`/bare/`-a`, and never push. Other agents may be working in this checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`.

LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item must carry pasted evidence before this plan moves to `.aw/records/plans/executed/`. Use the tooled transition; do not hand-edit `- Status:`. This plan is Order 01 of Set `structpin`: Order 02 (`76ic0k`) declares `executed:b02ohu` and must not execute before this plan reaches `executed`, because the guard it adds would be red on arrival while A1..A6 still exist.
