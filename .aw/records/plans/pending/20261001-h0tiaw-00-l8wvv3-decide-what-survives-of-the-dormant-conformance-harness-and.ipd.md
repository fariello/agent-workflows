# IPD: Decide what survives of the dormant conformance harness and revive exactly that

- Date: 2026-10-01
- Kind: orchestrator
- Concern: `tests/conformance_matrix.py` is a 577-line harness whose structural half HAS NO EXECUTOR. Measured in this lane at HEAD `b6792ad4a`: eight of its public symbols (`SCENARIOS`, `required_scenarios`, `MatrixRow`, `MatrixReport`, `build_matrix`, `render_matrix_report`, `semantic_facts_from_human`, `outcome_family`, plus `ANSI_RE`, `GOLDEN_DIR` and `USAGE_ERROR_FLAG`) are imported by NOTHING under `tests/`, while only four (`run_cli`, `REPO_ROOT`, `LIVE_SAFE_LEAVES`, `RUNNABLE_ARGV`, `EXEMPTION_REGISTRY`, `semantic_facts_from_agent`) have live importers. The two former drivers were deleted by test-trimming commit `19313eed7` (2026-09-24): `test_cli_conformance_matrix.py` (224 lines, the structural + live-scenario + fact-parity + alias gates) and `test_cli_quality_gates.py` (the schema, ANSI, golden, accessibility, truncation, parity and budget gates). THE COST IS NOT HYPOTHETICAL AND IS ALREADY VISIBLE IN THREE PLACES. (1) `tests/fixtures/conformance_goldens/` holds twelve committed `.golden` files that NO test reads (`rg '\.golden' --glob '!*.golden'` returns zero hits), and one of them has ALREADY DRIFTED: `check_findings.human.golden` disagrees with today's render on two `Fix:` lines, meaning a reviewed-bytes artifact silently went stale. (2) `agent_workflows/command_surface.py` reasons about `required_scenarios` in three separate comments as if it were enforced, and ONE of them already admits the truth ("`conformance_matrix` is currently a dead surface with no live importer (F-05), so the obligation is currently latent rather than enforced"), so the inventory's own documentation is split between two beliefs. (3) `CONTRIBUTING.md` step 6 instructs every new-leaf author to add their leaf to `LIVE_SAFE_LEAVES` "so the harness exercises it live (ANSI-free agent stream, exit-code parity, fact-parity, help, usage error, no-color)", and of those six promises only exit-code parity is executed today, by `tests/test_exit_contract_conformance.py`. So a contributor follows a documented step that buys them five sixths of nothing.
- Scope: IN: decide, from measurement rather than from the harness's own docstring, WHICH of the two deleted drivers' gates are worth reviving, and revive exactly those as two children: the cheap structural + alias + ANSI gate (Order 01) and the renderer-level golden/schema/accessibility/budget gate (Order 02). Also IN: retire the harness's two STALE exemption entries, whose cited owner (`dtq6jr`) is now `done`, and reconcile the `CONTRIBUTING.md` promise and the `command_surface.py` comments with whatever ends up enforced. OUT (each with a named reason in the Deferred section): re-adding the expensive 16-leaf-by-5-scenario live sweep as a default-collected test (measured 98.74s for the 13 cheap leaves alone, and 48.75s for one human pass over all 16); the `FactParityTests` human-banner gate, which is VACUOUS today (measured: 0 of 16 live-safe leaves emit the `AW <command>` banner `semantic_facts_from_human` requires, so every subtest silently degrades to the exit-code fallback that `test_exit_contract_conformance.py` already owns); extending coverage to `mutation` leaves, which is plan `vfv2db`'s declared scope; and fixing the two leaves the revival proves non-conformant, which belong to their filed owners.
- Scope-Paths: .aw/records/plans/pending/20261001-h0tiaw-00-l8wvv3-decide-what-survives-of-the-dormant-conformance-harness-and.ipd.md
- Item-Dependencies: none
- Status: draft
- Coverage: fail
- Coverage-Fingerprint: 51a73bc827677433d6efa1612d6e15d018d9f162943812c0c14f3c51b9c19d30
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: low
- From-Backlog: h0tiaw
- Set: h0tiaw
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: l8wvv3

## Workflow history
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: No orphaned golden and no orphaned symbol, checked across both children together

- 2026-10-06 coverage fail (aw oc run): fingerprint 51a73bc82767, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `h0tiaw`, graduating it. The item asked two open questions and BOTH ARE ANSWERED HERE FROM REPOSITORY EVIDENCE rather than deferred. "Whether the driver was ever written (check git history)": YES, two of them, and `git show 19313eed7^:tests/test_cli_conformance_matrix.py` plus `git show 19313eed7^:tests/test_cli_quality_gates.py` recover both verbatim, so this is a restoration from a known-good source and not a reconstruction from a docstring. "Whether the intended contract is still the one the helpers encode, since reviving a stale harness can assert obsolete promises": PARTLY, and the measurement is what splits this Set in two. The item's own framing ("latent coverage debt, not a live defect") was MEASURED AND IS WRONG ON ONE POINT: `check_findings.human.golden` has already drifted from today's render, so a reviewed-bytes artifact is stale right now, which is a live (if low-impact) defect and not merely latent debt. Three of the harness's encoded promises are OBSOLETE and this Set deliberately does NOT revive them: the human-banner fact-parity gate is vacuous on all 16 live-safe leaves, `test_declared_absent_leaves_are_only_the_known_prompts_family` pins a set that has since grown from one member to two, and two `known_broken` exemptions cite an owner that is now `done`. The rest are sound and cheap. THIS ORCHESTRATOR CARRIES ONLY the child-completion checklist; every deliverable belongs to a child.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave the repository with no dormant test harness: every symbol in `tests/conformance_matrix.py` either
has a live executor asserting a promise that is still true, or is deleted, and the three places that
currently describe the harness as enforced (`CONTRIBUTING.md` step 6, two `command_surface.py` comments,
the twelve unread golden files) agree with what is actually executed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

THIS ORCHESTRATOR CARRIES NO WORK OF ITS OWN. Both items below confirm that a CHILD completed; neither
produces a deliverable, establishes a baseline, or reconciles a record. That is deliberate and
mechanical: the runner RETIRES an orchestrator once every child is `executed` and deliberately SKIPS the
pre-transition `E-*`/`V-*` checkpoint, on the premise that a parent's own items are performed by nobody,
so work parked here would be marked complete having never been performed (`AGENTS.md`). The checklist
exists because most Sets are run by a human or agent told simply to "execute h0tiaw" with no runner
involved, and deleting it causes exactly the partial execution it prevents.

### Task group 1: the two children, in dependency order

- [ ] E-01 CONFIRM dq9bj9 REACHED executed
  - Depends on: none
  Confirm child 01 (`dq9bj9`, revive the structural matrix gate and retire the two stale exemptions) is
  `executed`, with its own validation evidence present. This child is FIRST because it is the one that
  touches `tests/conformance_matrix.py` itself: it deletes the stale `dtq6jr` exemptions, removes the
  symbols nothing will execute, and corrects the module docstring. Child 02 only ADDS a test module and
  reads `ANSI_RE`/`GOLDEN_DIR` from the harness, so running it second means it reads a harness that is
  already correct rather than one mid-edit.
  - Expected outcome: `dq9bj9` is in `.aw/records/plans/executed/` with `- Status: executed`, every `V-*`
    carrying pasted evidence, and `tests/test_conformance_matrix_structure.py` existing and passing in the
    DEFAULT (unmarked) suite.
  - Execution state: pending

- [ ] E-02 CONFIRM 9i2hge REACHED executed
  - Depends on: E-01
  Confirm child 02 (`9i2hge`, restore the renderer-level quality gates and reconcile the drifted golden)
  is `executed`. This child is SECOND for the dependency stated in E-01 and for a second reason: it is the
  only child that resolves the one LIVE defect this Set found (the drifted `check_findings.human.golden`),
  so sequencing it last means the golden is reconciled against a tree whose harness edits have already
  landed and will not move it again.
  - Expected outcome: `9i2hge` is `executed`, `tests/test_cli_quality_gates.py` exists and passes in the
    DEFAULT suite, all twelve `.golden` files have a reader, and the drifted
    `check_findings.human.golden` is either regenerated with the diff reviewed and quoted in the plan or
    the render is corrected, with the choice justified rather than defaulted.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `dq9bj9` | `.aw/records/plans/pending/20261001-h0tiaw-01-dq9bj9-revive-the-dormant-conformance-matrix-as-a-live-structural-g.ipd.md` | Revives the cheap structural gate (zero undeclared leaves, full scenario-row coverage per declared leaf, the widened `declared_absent` pin, the alias byte-equivalence pairs) as a DEFAULT-COLLECTED module; retires the three stale `dtq6jr` exemptions; resolves each dead harness symbol to either an executor or deletion; reconciles the three `command_surface.py` comments that reason from `required_scenarios`. | none |
| 02 | `9i2hge` | `.aw/records/plans/pending/20261001-h0tiaw-02-9i2hge-restore-the-renderer-level-output-quality-gates-so-the-four.ipd.md` | Restores the renderer-level gates (schema validity, ANSI posture, deterministic byte goldens, ASCII accessibility, stream truncation accounting, fact parity, byte/token budget) as a DEFAULT-COLLECTED module over the four reviewed fixtures; gives all twelve `.golden` files a reader; resolves the drifted `check_findings.human.golden` with its diff quoted; reconciles `CONTRIBUTING.md` step 6. | executed:dq9bj9 |

## Completion criteria (the whole Set is done only when)

- EVERY SYMBOL in `tests/conformance_matrix.py` either has a live executor or is gone. No third category
  survives: a symbol kept with no executor is precisely the condition backlog `h0tiaw` filed, so leaving one
  means the Set did not finish.
- BOTH revived modules are DEFAULT-COLLECTED, meaning they run under a bare `python3 -m pytest` with no
  `-m ''` override. A revived gate marked `slow` would run in CI only inside the step carrying
  `continue-on-error: true`, which cannot fail a build (F-09).
- ALL TWELVE `.golden` files under `tests/fixtures/conformance_goldens/` have a reader, and the one drifted
  golden is resolved with its diff quoted in the child's evidence rather than regenerated silently (OQ-02).
- THE THREE PROSE SITES that describe this harness as enforced agree with what is now enforced:
  `CONTRIBUTING.md` step 6's six named checks, and the three `agent_workflows/command_surface.py` comments
  reasoning from `required_scenarios`, one of which currently states the opposite of the other two (F-10).
- NO LEAF IS FIXED BY THIS SET and no exemption is added to silence a red sweep. The two non-conformant
  leaves the revived `declared_absent` pin names stay with their filed owners (`68sur3`, `lbbo9s`), and the
  registry's own "CEILING, NOT A CONVENIENCE" rule is respected: entries are REMOVED here, never added.

## Cross-IPD validation

- NO DOUBLE OWNERSHIP OF `tests/conformance_matrix.py`. Both children declare it, which is legitimate (01
  edits the registry, the docstring and the symbol set; 02 only READS `ANSI_RE` and `GOLDEN_DIR` from it),
  but after both execute the file must contain exactly one coherent state. Verify by confirming 02's
  imports resolve against 01's post-edit module: if 01 deleted a symbol 02 imports, the suite fails at
  collection, which is why the dependency edge runs 01 FIRST.
- NO ORPHANED GOLDEN AND NO ORPHANED SYMBOL, checked across both children together rather than within
  either. After both execute, `rg '\.golden' --glob '!*.golden'` must return a hit (today zero, F-07), and a
  per-symbol sweep of `tests/conformance_matrix.py`'s public names must show every one either imported by a
  test or absent from the module. Neither child can establish this alone: 01 owns the symbols, 02 owns the
  goldens, and the item's complaint is about the UNION.
- THE BARE SUITE DELTA IS EMPTY ACROSS THE SET, not merely per child. Each child runs `python3 -m pytest`
  bare and reports a failure-set delta against its own base; this orchestrator additionally requires that
  the Set as a whole introduces no failure, which is the case that catches a 01 edit that only breaks under
  02's new imports.
- THE TWO NEW MODULES DO NOT RE-ASSERT WHAT ALREADY PASSES ELSEWHERE. `test_command_surface_declarations.py`
  already asserts zero undeclared leaves and `test_model_vocab.py::test_10_zero_undeclared_leaves` asserts
  it again; child 01's module adds the SCENARIO-COVERAGE and `declared_absent` assertions those do not
  make. Verify the overlap is stated rather than silently tripled.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- AN ORCHESTRATOR'S CHECKLIST IS ORCHESTRATION ONLY (`AGENTS.md`). Both items here confirm a child; neither
  does work. The runner's ORCHESTRATOR COVERAGE GATE asks a model whether a parent carries work no child
  covers and refuses unattended when it does, so a parent-only deliverable would block the run rather than
  silently pass.
- THE DEFAULT SUITE IS THE ONLY GATE THAT BINDS. `pyproject.toml` `addopts` is
  `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, and `.github/workflows/tests.yml` runs
  `python -m pytest tests/ -n auto -rfEs` with no `-m ''`, so a `slow`-marked test runs in CI only in a
  step carrying `continue-on-error: true` ("ADVISORY until the known slow failures are fixed"). A revived
  gate marked `slow` is therefore worth strictly less than one that is not, which is the single fact that
  shaped how this Set is split: both children land DEFAULT-COLLECTED tests, and the expensive live sweep
  the old driver carried is deferred rather than revived as an advisory no-op.
- NO CODE-PINNING TESTS (`GUIDING_PRINCIPLES` 16). Neither child may read production source, count
  callers, or pin a docstring. Both restored modules drive real code: child 01 builds the matrix from the
  real parser and runs the real CLI, child 02 renders real `CommandResult` values.
- THE 90s HANG BUDGET IS PER TEST (`conftest.py` `_DEFAULT_TEST_TIMEOUT = 90.0`), overridable per test with
  `@pytest.mark.timeout(<seconds>)` and ignored for nothing. Any revived test that drives subprocesses must
  be measured against it rather than assumed cheap; `tests/test_exit_contract_conformance.py` sets
  `@pytest.mark.timeout(500)` for exactly this reason.

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | THE ITEM'S FIRST OPEN QUESTION IS ANSWERED: BOTH DRIVERS EXISTED AND BOTH ARE RECOVERABLE. `git show 19313eed7^:tests/test_cli_conformance_matrix.py` returns a 224-line module with five test classes (`UndeclaredLeafGuardTests`, `LiveScenarioConformanceTests`, `FactParityTests`, `AliasEquivalenceTests`, plus the matrix row assertions), and `git show 19313eed7^:tests/test_cli_quality_gates.py` returns the seven-gate renderer module. The trim commit is `19313eed7` "test: trim test suite from 9,136 to under 2,000 tests" (2026-09-24), which deleted both among roughly 200 other modules. So this Set is a RESTORATION from a known-good source, which is materially cheaper and lower-risk than the reconstruction the item feared. | Both `git show` invocations run in this lane; `git show --stat 19313eed7` read for the deletion list. |
| F-02 | THE HARNESS'S STRUCTURAL HALF IS DEAD AND ITS LIVE HALF IS NOT. Grepping each public symbol across `tests/`, `agent_workflows/`, `docs/` and `tools/`: `run_cli` has three importers (`test_agent_surface_conformance.py`, `test_exit_contract_conformance.py`, `test_index_check_agent_records.py`), and `LIVE_SAFE_LEAVES`, `RUNNABLE_ARGV`, `EXEMPTION_REGISTRY`, `REPO_ROOT` and `semantic_facts_from_agent` each have one or two. `SCENARIOS`, `required_scenarios`, `MatrixRow`, `MatrixReport`, `build_matrix`, `render_matrix_report`, `semantic_facts_from_human`, `outcome_family`, `ANSI_RE`, `GOLDEN_DIR`, `USAGE_ERROR_FLAG`, `RunResult`, `Exemption` and `_pinned_env` have ZERO importers outside the module. That split is what makes this a two-child Set rather than one: the live half needs nothing, the dead half needs either an executor or deletion. | A per-symbol `rg` sweep over `tests/ agent_workflows/ docs/ tools/` excluding the module itself. |
| F-03 | THE STRUCTURAL GATE IS GREEN TODAY AND COSTS HALF A SECOND, so reviving it is nearly free. Driven in-process: `find_undeclared_leaves(_build_parser())` returns `set()`, `build_matrix` produces 1193 rows over 163 declarations and 152 parser leaves with `undeclared == []` and ZERO leaves missing a required scenario. Timed: 0.669s to import and 0.513s for the whole structural pass. This is the cheapest durable gate in the Set and it is the one the three `command_surface.py` comments already assume exists. | The matrix built and timed in-process at HEAD `b6792ad4a`. |
| F-04 | ONE OF THE OLD DRIVER'S STRUCTURAL ASSERTIONS IS NOW FALSE, so a verbatim restoration would land RED. `test_declared_absent_leaves_are_only_the_known_prompts_family` asserts `set(report.declared_absent) == {"prompts set"}`; measured today `declared_absent` is `['prompts set', 'upgrade-test']`. Both absences are real and both are FILED: `prompts set` is declared `mutation` with no parser leaf (open backlog `68sur3`, "prompts set dispatched but unregistered"), and the bare `upgrade-test` group is declared `read` with `agent_record_kind="result"` while exiting 2 from an argparse usage block (open backlog `lbbo9s` at `Blocks-Release: next`). So child 01 must WIDEN the pin to both members and cite both owners, NOT delete the assertion: the pin's whole value is that a THIRD silent absence fails. | `build_matrix` driven; both backlog items read; `aw find backlog` for each id6. |
| F-05 | TWO EXEMPTION ENTRIES ARE STALE AND ONE IS NOW ACTIVELY WRONG. `EXEMPTION_REGISTRY` carries three `known_broken` entries citing `dtq6jr` ("Crashes with ImportError: cannot import name 'format_agent_json'"); backlog `dtq6jr` is `done`. Driven today, `config show --agent` emits a schema-valid `result` record at exit 0 with exit parity, so it CONFORMS and its exemption suppresses a passing leaf. `config get` and `config is` emit nothing on stdout when invoked with no positional argument, but WITH their required argument (`config get interactive`, `config is interactive`) both emit a schema-valid `error` record at exit 2 with exit parity, so they conform too and belong in `RUNNABLE_ARGV`, not in the exemption registry. The registry's own banner says "THE REGISTRY IS A CEILING, NOT A CONVENIENCE" and that "a `known_broken` entry REQUIRES a filed item id"; three entries now cite a closed one. | `dtq6jr` located in `.aw/records/backlog/done/`; all three leaves driven with and without positional arguments, with records validated through `agent_schema.validate_agent_record`. |
| F-06 | THE FACT-PARITY GATE IS VACUOUS ON EVERY LIVE-SAFE LEAF, so reviving it would add 32 subprocess invocations that assert only what another test already owns. `semantic_facts_from_human` returns an outcome only when stdout's first non-empty line starts with `AW ` and its second carries an uppercase status word. Measured across all 16 `LIVE_SAFE_LEAVES`: ZERO produce that banner (`status` opens `agent-workflows status`, `backlog check` opens `aw backlog check: all backlog items conform.`, `layout` opens `AW Workspace Layout Model` whose second line is `INFO     Read-only inspection...`). So all 16 subtests fall into the `assertEqual(agent.returncode, human.returncode)` fallback, which is precisely what `test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership` already drives. The helper is not WRONG (it returns `findings` correctly for a synthesized `CommandResult` render), it is just never reached by a leaf in the curated set; `runs query schema` DOES emit the banner but is not in `LIVE_SAFE_LEAVES`. | All 16 leaves driven through `semantic_facts_from_human`; 13 further read/check leaves probed, of which only `runs query schema` banners; the helper driven directly on a synthesized render returning `{'outcome_family': 'findings'}`. |
| F-07 | THE GOLDENS ARE UNREAD AND ONE HAS ALREADY DRIFTED, which is the one LIVE defect in this item. `tests/fixtures/conformance_goldens/` holds 12 tracked `.golden` files and `rg '\.golden' --glob '!*.golden'` over the whole tree returns zero hits, so nothing reads them. Re-rendering the four fixtures the deleted `test_cli_quality_gates.py` defined: eleven match byte for byte and `check_findings.human.golden` does NOT, differing on two `Fix:` lines (the golden says `run 'aw rename plans a.md' or rename to match ...` where today's render says `a.md does not carry a clustered identity prefix; run 'aw rename plans a.md --to-id6 --apply' or rename to match ...`, and similarly adds `--rename --apply` to the regroup hint). Note the goldens were LAST TOUCHED on 2026-10-01 by `f8ff56ec1`, a run that edited four `.human.golden` files by hand to track a renderer change, so the tree contains evidence of someone maintaining files that no test reads. | `git ls-files` count; the `rg` sweep; all twelve goldens re-rendered and diffed in-process; `git log -1 --stat` on the fixture directory. |
| F-08 | THE RENDERER-LEVEL GATES ARE CHEAP AND GREEN, so child 02 is a low-risk restoration. Driven in-process over the four fixtures: all four agent records validate (`validate_agent_record` returns `[]`), all four agent and JSON renders are ANSI-free while the human render carries ANSI only with `color=True`, `FINDINGS` and `[ERROR]` both appear in the monochrome render, `Term(color=False, unicode=False)` degrades glyphs to `FAIL`/`OK`/`->`, `render_stream` under `limit=3` over 10 items reports `emitted=3, omitted=7, total=10, complete=False`, `--fields findings` shrinks the record from 341 to 130 bytes while retaining all seven envelope keys, and the largest record is 341 bytes against the module's 1200-byte and 400-token budgets. The whole gate shape runs in 0.790s. | Each assertion driven in-process at HEAD `b6792ad4a` and its value printed. |
| F-09 | THE EXPENSIVE LIVE SWEEP IS WHAT THE TRIM WAS RIGHT TO CUT, and the numbers say do not revive it. One human pass over all 16 live-safe leaves takes 48.75s, dominated by `doctor` at 27.62s and `attention` at 7.54s; `doctor --agent` alone takes 63.13s. The old driver's five scenarios over the 13 CHEAP leaves (excluding `doctor`, `attention`, `status`) measured 98.74s, so the full 16-by-5 sweep is several minutes. Against a 90s per-test budget that forces either `@pytest.mark.timeout(500)` or splitting, and against the default `-m 'not slow'` it forces a `slow` marker, which in CI means the advisory `continue-on-error: true` step. A gate that cannot fail CI is not a gate, so this Set deliberately revives the structural and renderer halves (both default-collected) and defers the live sweep to a carrier rather than reviving it as an advisory no-op. | Each leaf timed individually, human and agent; the 13-leaf five-scenario sweep timed end to end; `pyproject.toml` `addopts` and `.github/workflows/tests.yml` read. |
| F-10 | THREE PLACES IN THE TREE ALREADY DESCRIBE THIS HARNESS AS ENFORCED, AND ONE OF THEM CONTRADICTS THE OTHER TWO. `CONTRIBUTING.md` step 6 tells a new-leaf author to add to `LIVE_SAFE_LEAVES` "so the harness exercises it live (ANSI-free agent stream, exit-code parity, fact-parity, help, usage error, no-color)" - six promises, of which exactly one (exit-code parity) is executed. `agent_workflows/command_surface.py` reasons from `required_scenarios` in three comments, two of which treat it as binding ("declaring the wrong class demands the wrong coverage", "`status` obliges a `domain_failure` row while `next` does not") while the third states the opposite and is correct ("`conformance_matrix` is currently a dead surface with no live importer (F-05), so the obligation is currently latent rather than enforced"). Whichever gates this Set lands, those three sites must end up agreeing with them, which is why both children carry a reconciliation item rather than leaving the prose to rot. | `CONTRIBUTING.md` step 6 read; all three `command_surface.py` comments read; the third traced to commit `55f82301b` `work(69rdv6)`. |
| F-11 | THE ALIAS GATE IS GREEN AND HAS NO OTHER OWNER. `AliasEquivalenceTests` asserted that `spec check` and `sanitize` are agent-byte-equivalent to `specs check` and `check-local-leaks`; driven today both pairs agree on returncode AND on stdout byte for byte (2.8s and 12.2s respectively). Twelve leaves are declared `command_class="alias"` and `discover_parser_leaves`' own docstring says "`AliasEquivalenceTests` owns alias behavior", naming a class that no longer exists. A grep for alias byte-equivalence across `tests/` finds no replacement. So this is real uncovered ground, but the 12.2s `sanitize` pair makes it the one revived assertion with a nontrivial cost, which child 01 must measure against the 90s budget rather than assume. | Both pairs driven and compared; `discover_parser_leaves`' docstring read; `rg` for a replacement owner. |

## Proposed changes (ordered, validatable)

1. E-01 confirms child `dq9bj9` executed: the structural matrix gate revived as a default-collected
   module, the `declared_absent` pin widened to both filed absences, the two stale `dtq6jr` exemptions
   retired, the dead symbols either executed or deleted, and the `command_surface.py` comments reconciled.
2. E-02 confirms child `9i2hge` executed: the renderer-level schema, ANSI, golden, accessibility,
   truncation, parity and budget gates revived as a default-collected module, the twelve goldens given a
   reader, the one drifted golden resolved with its diff quoted, and `CONTRIBUTING.md` step 6 reconciled.

## Deferred / out of scope (with reason)

- THE 16-LEAF-BY-5-SCENARIO LIVE SWEEP from `LiveScenarioConformanceTests` (F-09). Measured at several
  minutes, which forces either a `slow` marker (CI-advisory, `continue-on-error: true`, so unable to fail
  a build) or a per-test timeout override plus a split. Reviving it as an advisory no-op would restore the
  APPEARANCE of coverage without the enforcement, which is the exact failure mode this Set exists to end.
  Its two load-bearing assertions are also partly owned already: exit-code parity by
  `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership` (itself
  `slow`, which is a separate honest limit), and agent-stream schema validity over 42 read/check leaves by
  `tests/test_agent_surface_conformance.py`, which IS default-collected. What remains genuinely uncovered
  is the per-leaf `--no-color` and `--help` scenario sweep. A carrier is filed with the measured timings so
  whoever takes it starts from numbers rather than re-measuring.
  - Carrier: 2wowfy
- THE HUMAN-BANNER FACT-PARITY GATE from `FactParityTests` (F-06). Vacuous on all 16 live-safe leaves, so
  reviving it would add 32 subprocess invocations asserting only the exit-code equality another test
  already drives. The underlying property (a human render and an agent record must carry the same semantic
  facts) is worth having, but making it non-vacuous means either curating leaves that DO emit the standard
  banner (`runs query schema` does) or widening `semantic_facts_from_human` to the table and rich renders
  it deliberately refuses. Both are design work, not restoration, and child 02 covers the parity property
  at the RENDERER level where it is cheap and non-vacuous. Carrier filed with the 0-of-16 measurement.
  - Carrier: 2wowfy
- EXTENDING CONFORMANCE TO `mutation` LEAVES. Declared scope of pending plan `vfv2db` (backlog `w78faq`),
  which measured eleven mutation leaves emitting human prose under `--agent` and declares
  `tests/conformance_matrix.py` in its own `- Scope-Paths:`. Both children here touch that file, so the
  two meet; both run in isolated worktrees through the merge-and-revalidate gate, so the file overlap is
  not a hazard, but the SEMANTIC boundary is stated so it is not discovered at merge: this Set changes only
  `EXEMPTION_REGISTRY` entries and the module docstring, and adds no `LIVE_SAFE_LEAVES` member, while
  `vfv2db` adds a mutation arm and a fixture. Neither needs the other's change.
  - Carrier: vfv2db
- FIXING THE TWO LEAVES THE REVIVED `declared_absent` PIN NAMES (F-04). `prompts set` is declared with no
  parser leaf (`68sur3`) and the bare `upgrade-test` group declares `agent_record_kind="result"` while
  exiting 2 from argparse (`lbbo9s`, `Blocks-Release: next`). Child 01 PINS both as known and cites both
  owners; fixing either is that owner's work and would widen this chore into two bug fixes.
  - Carrier: 68sur3
- THE SECOND OF THOSE TWO, tracked separately because it carries a release gate this Set must not absorb.
  - Carrier: lbbo9s
- `tests/test_exit_contract_conformance.py` BEING `slow` AND THEREFORE CI-ADVISORY. Noticed while measuring
  F-09: the one live membership gate that survived the trim runs only in the advisory step, so the live
  half of the conformance story is not CI-enforced either. That is a pre-existing condition this Set
  neither worsens nor fixes, and changing it means making a 185s test cheap, which is the same design
  problem as the deferred sweep.
  - Carrier: 2wowfy
- THE `f8ff56ec1` HAND-EDITED GOLDENS (F-07), where a run updated four `.human.golden` files that no test
  reads. Child 02 gives them a reader, which is the fix; auditing whether that run's four edits were each
  correct is not needed, because once a reader exists the files are asserted against the live render and
  any remaining error surfaces as a failure rather than as a silent wrong byte.
  - Carrier-Declined: giving the files a reader SUBSUMES the audit. A separate audit would re-derive by
    hand exactly what child 02's `V-*` evidence derives mechanically, and would produce no artifact the
    test does not.

## Scope check

- Over-scope: none. This orchestrator's only `- Scope-Paths:` entry is its own file, which is correct for a
  plan that produces no deliverable: it confirms two children and writes nothing else. The children carry
  `tests/conformance_matrix.py`, the two new test modules, and the prose reconciliations, each declared on
  the child that performs it.
- Under-scope: the risk is that child 01's revival of the structural gate turns up a THIRD `declared_absent`
  member or a newly undeclared leaf landed by a concurrent lane between authoring and execution, making the
  pin red on arrival. That is the gate working as designed, and the correct response is to measure the new
  member, locate or file its owner, and widen the pin with the citation, exactly as E-01's child does for
  the two known members. It is NOT to delete the assertion.

## Required tests / validation

- BOTH CHILDREN REACHING `executed` with their own `V-*` evidence pasted, which is the only thing this
  orchestrator asserts. No test is run by this plan.
- `aw ipd lint --phase pre-transition` conforming on this plan before the terminal move, and `aw check`
  reporting no new drift.
- THE RETIREMENT PRECONDITION the runner enforces: every child `executed` on disk. If either child refuses
  its transition, this plan stays in `pending/` and that refusal is the finding to report, not a failure of
  the run.

## Spec / documentation sync

No spec amendment, and no `.spec.md` file is declared in `- Scope-Paths:`, so a run executing this Set must
announce no declared spec edits and none may be made. Checked rather than assumed: `rg` over
`.aw/records/specs/` for `conformance_matrix`, `EXEMPTION_REGISTRY`, `LIVE_SAFE_LEAVES` and
`conformance_goldens` returns no spec text, so no shipped contract specifies this harness. The contract the
harness MEASURES is `docs/cli-output-contract.md`, which is a normative document rather than a spec record,
and neither child changes it: both assert the behavior it already describes.

Two prose reconciliations are required and each is declared on the child that performs it, not here.
`CONTRIBUTING.md` step 6 currently promises six live checks of which one is executed, and is reconciled by
child 02 once the final enforced set is known. The three `agent_workflows/command_surface.py` comments that
reason from `required_scenarios` are reconciled by child 01, which is the child that makes two of them true
and the third (the "dead surface with no live importer" note) obsolete.

## Open questions

### OQ-01: Should the dead harness symbols be deleted outright instead of given executors

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT AUTHORING, SPLIT BY MEASURED VALUE RATHER THAN UNIFORMLY.
  The deciding measurements are F-03 (the structural pass is green and costs 0.513s), F-08 (the renderer
  gates are green and cost 0.790s), F-11 (the alias gate is green, uncovered elsewhere, and costs 15s),
  F-06 (the human-banner parity helper is vacuous on every curated leaf), and F-09 (the live sweep costs
  minutes and can only land as a CI-advisory). So: REVIVE the structural, alias and renderer gates, because
  each is cheap, green, default-collectable and asserts a promise the tree already makes in prose. DELETE
  or DEFER the rest, with `semantic_facts_from_human` and `outcome_family` the judgement call child 01
  owns: they are the only dead symbols whose property is worth keeping but whose current form is vacuous,
  so child 01 either keeps them with a non-vacuous executor or deletes them and lets the deferred carrier
  reintroduce them with a working predicate. Leaving a third category (symbols kept with no executor) is
  what created this item and is not an option either child may take.

### OQ-02: Should the drifted check_findings.human.golden be regenerated or should the render be corrected

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: REGENERATE THE GOLDEN, with the diff quoted in child 02's
  evidence, because the drift is the render becoming MORE correct rather than less. The golden's `Fix:`
  text reads `run 'aw rename plans a.md' or rename to match ...` while today's render reads `a.md does not
  carry a clustered identity prefix; run 'aw rename plans a.md --to-id6 --apply' or rename to match ...`,
  and the second regroup line likewise gained `--rename --apply`. Both additions make the suggested command
  actually runnable: a bare `aw rename plans <file>` without `--apply` previews only, which is the
  repository's documented default for every mutating verb. So the live render is right and the golden is
  stale. Child 02 must nonetheless QUOTE the full diff as evidence rather than regenerating silently,
  because `AW_CONFORMANCE_UPDATE_GOLDENS=1` regeneration with no review is how a golden stops being a
  reviewed artifact, and that is a precondition for this gate being worth anything at all.

## Coverage findings

- "- NO ORPHANED GOLDEN AND NO ORPHANED SYMBOL, checked across both children together rather than within"
- "- THE BARE SUITE DELTA IS EMPTY ACROSS THE SET, not merely per child. Each child runs `python3 -m pytest`"
- "- THE TWO NEW MODULES DO NOT RE-ASSERT WHAT ALREADY PASSES ELSEWHERE. `test_command_surface_declarations.py`"
- "- `aw ipd lint --phase pre-transition` conforming on this plan before the terminal move, and `aw check`"

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the output of `ls .aw/records/plans/executed/ | grep dq9bj9` showing the plan
    present in the terminal directory, and `rg -n '^- Status:' <that path>` showing `executed`. PASTE the
    bare-suite line from a `python3 -m pytest tests/test_conformance_matrix_structure.py` run (or whatever
    module name child 01 chose, named explicitly) showing it COLLECTED AND PASSING WITHOUT a `-m ''`
    override, which is what proves it is default-collected rather than `slow`-marked. PASTE
    `rg -n 'dtq6jr' tests/conformance_matrix.py` returning NOTHING, which proves the stale exemptions are
    gone. State explicitly which dead symbols child 01 kept and which it deleted, and for every symbol
    KEPT, name the test that executes it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `ls .aw/records/plans/executed/ | grep 9i2hge` and the plan's `- Status:` line.
    PASTE the passing run of the restored quality-gates module, again showing default collection with no
    `-m ''`. PASTE the `check_findings.human.golden` diff (the two `Fix:` lines) as it was resolved, and
    state which direction was taken and why, matching OQ-02's resolution or justifying a departure from it.
    PASTE a command proving all twelve `.golden` files now have a reader, for example an `rg` for the
    golden path or directory from the test module. Finally, QUOTE the reconciled `CONTRIBUTING.md` step 6
    text and state, promise by promise, which of its six named checks is now executed and by which test.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is an ORCHESTRATOR and performs no work. Executing it means confirming both children reached
`executed` on disk and then transitioning this plan, which `aw oc run` / `aw agy run` do automatically once
every child qualifies (retirement is gated on EVERY child being `executed` and on nothing else, and the
runner names which precondition it hit when it refuses). A refusal leaves this plan in `pending/` and is not
a failure of the run.

Approval is required before execution and must come from a human; this plan carries no `- Readiness:` field,
because that field is an OUTPUT of `/plan-review` and writing one at authoring would forge the attestation
an auto-approve predicate reads first. The executing agent commits only through
`aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Each child owns its own commits; this
plan's own transition is the only change it makes.
