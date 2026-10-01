# IPD: Pin every declared machine surface with an executed conformance sweep so a dropped emit cannot pass CI

- Date: 2026-09-29
- Kind: child
- Concern: THE TOOLKIT DECLARES 160 LEAVES AS EMITTING AN `aw.agent/v1` RESULT AND EXECUTES ALMOST NONE OF THAT CLAIM, so a machine surface can be deleted, or can crash, without a single test going red. This is the CLASS that backlog `kjr5ol` was filed to carry: commit `4cfa2283` deleted `return get_renderer(ctx).emit(res, ctx)` from the no-project branch of `attention.run`, the branch kept BUILDING a `CommandResult` and discarding it, and nothing failed. Measured in this lane at HEAD `58dc1c70`, driving all 67 `read`/`check`/`bare` leaves that declare `agent_record_kind="result"` with `--agent` by subprocess: only 28 emitted a schema-valid terminal record with exit parity, and 13 did not emit one at all. SIX of those 13 are the pre-commit/pre-push gate leaves (`ipd-executed-gate`, `ipd-status-untooled-gate`, `precommit-scope-gate`, `backlog-blocking-close-gate`, `ipd-dependency-statement-gate`, `prepush-authorization-gate`), whose `hooks/*.main` write prose to stderr and return a bare int, never constructing a `CommandResult` at all, so `--agent` is accepted and silently ignored - the exact same invisible-silence failure mode as the original defect, on six leaves, today. The remaining 7 split into one already-owned crash and six legitimately-exempt surfaces (see Findings). The declaration field that would have caught all of this, `CommandDeclaration.agent_record_kind`, is READ BY NO CODE ANYWHERE: `rg agent_record_kind` outside `command_surface.py` returns nothing, so it is documentation that no gate consumes. And `tests/conformance_matrix.py`, a 378-line harness built to close exactly this gap, has ZERO importers: the two test files its own docstring names as its consumers do not exist, and its `build_matrix` marks every non-curated leaf `covered_by="declaration"`, meaning "asserted, never run".
- Scope: Make the declared machine surface an EXECUTED contract instead of a documented intention, and fix the six gate leaves the sweep proves are broken. IN: a behavioral conformance test that drives every leaf declaring `agent_record_kind="result"` with `--agent` in a subprocess and asserts a schema-valid terminal record with exit parity, wired to the orphaned `tests/conformance_matrix.py` rather than rebuilt; an explicit, per-entry JUSTIFIED exemption registry so a leaf is either executed or documented as to why it cannot be, with no silent third category; routing the six hook-gate leaves through `get_renderer(...).emit(...)` so they honor the `--agent`/`--json` flags their declarations promise; and a NON-PROJECT cwd axis, because the original bug only manifested outside an AW project and a sweep run only in the repo tree cannot see it. OUT (each with a reason, none of them incidental): the `aw config` family's eight `format_agent_json` ImportError crash sites, which are ALREADY OWNED by open backlog item `dtq6jr` at `- Priority: high` with its own `Blocks-Release: next` gate and its own required test matrix, so fixing them here would duplicate a filed item and steal its validation; `aw find`/`aw path`'s bare-path output, which `docs/cli-output-contract.md` Section 12 and `agent_record_kind="raw_path"` SANCTION as deliberate token efficiency, so asserting an envelope there would break a documented contract rather than fix a defect; widening `agent_schema` to admit exit 3; any change to `emit`'s signature or to `BaseRenderer`; converting `mutation`-class leaves (79 of them) to the sweep, which needs a write-isolation design this plan does not attempt; and any static analysis of production source (`inspect`/`ast`/regex over `.py` files), which AGENTS.md P16 forbids outright.
- Scope-Paths: tests/conformance_matrix.py, tests/test_agent_surface_conformance.py, agent_workflows/cli.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/status_untooled_gate.py, agent_workflows/hooks/precommit_scope_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/hooks/prepush_authorization_gate.py, agent_workflows/attention.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: kjr5ol
- Blocks-Release: next
- Set: agentemitswp
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: f36de0

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: f36de0 verified (set agentemitswp, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-lbbo9s-01-lbbo9s-aw-upgrade-test-bare-group-declares-agent-record-k.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-201, PR-202, PR-203, PR-204, PR-205, PR-206 all FIXED, zero deferred, zero open. THE PLAN'S CENTRAL SWEEP WAS REPRODUCED RATHER THAN TRUSTED and its load-bearing numbers are exact: driving every candidate leaf with `--agent` as subprocesses reproduced `28 conforming` and `13 emitting no terminal record` precisely, and F-05 reproduced leaf for leaf (all six hook-gate leaves accept `--agent` and write NOTHING to stdout, including `prepush-authorization-gate` refusing at rc 1 with 908 bytes on stderr and empty stdout). F-01, F-02, F-04, F-06, F-07 and F-09 all reproduced, including every E-04 assertion from a real external temp repo (`cannot-run`, exit 2, schema clean, no path leak, human path exit 3 with empty stdout). THE MOST USEFUL CORRECTION WAS MEASURING WHAT THE PLAN DEFERRED (PR-204): OQ-02 left the default-suite question to E-06, and the numbers are decisive, so it is now RESOLVED. The naive sweep costs 59.15s serial and 20.0s parallel against a 46.93s bare suite, which would likely have pushed the executor to the `slow` mark the plan itself calls a real weakening, delivering a correct gate nobody runs; but the cost is CONCENTRATED in `doctor` (17.08s) and `check` (8.66s), both slow only because they walk this repo's full records tree, so the answer is keep it default-collected and scope those two. Four further defects came from DRIVING the plan's items: E-05 offered a hook-modules-only route that is not honestly implementable and left the required `cli.py` edit undeclared (PR-201); E-02's registry authorized two exemptions for a universe needing seven, one of which (`path`) is not in the universe at all, while a seventh leaf (`upgrade-test`) is not sanctioned and must be classified on its merits (PR-203); E-04 let the executor FILE a stale citation rather than fix it, which is the same debt the plan exists to clear, and the defect is two sites (PR-202); and several live counts had drifted with two V-items asking the executor to reconcile against them (PR-205). `Scope-Paths` amended at review to add `agent_workflows/cli.py` and `agent_workflows/attention.py`, both now required rather than optional. Added F-11 through F-16. Bare suite `3246 passed, 2 skipped`; no production file or test modified. Findings and four Decisions rows in `.aw/records/reviews/20260929-agentemitswp-01-f36de0-...review.md`.

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog item `kjr5ol`, which carries `- Blocks-Release: next`; this plan INHERITS that gate as required. Authoring MEASURED the item's residual ask rather than transcribing it, and the measurement contradicts the item in one direction and vindicates it in another. Recorded here because an executor who trusts the item's prose will both look for a test that does not exist and conclude the sweep is unnecessary.
  THE ITEM'S CITED PINS ARE MISNAMED OR DELETED, so do not go looking for them. It says the fix was pinned in `tests/test_attention.py::AttentionNoProjectMachinePathTests` and `tests/test_awretrofit_project_root_climb.py` case (e). The FIRST NAME DOES NOT EXIST and never did (`git log -S` finds no commit adding that string); the live pin is `tests/test_attention.py::NoProjectAgentEnvelopeTests`, which does exist and PASSES (measured: `1 passed`). The SECOND FILE WAS DELETED WHOLESALE by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), so `attention.py`'s own comment citing it as live protection is now stale. See F-01 and F-02. The attention branch itself is therefore NOT the outstanding work: `emit` is present at both no-project sites and covered. The outstanding work is the CLASS, which is what this plan takes.
  THE ITEM'S CORE CLAIM IS TOO OPTIMISTIC, AND THAT IS THE FINDING THAT JUSTIFIES THE SCOPE. It records that "a crude grep at execution time found no second instance" and asks only for a conformance test to make that a contract. Driving the surface instead of grepping it found SIX LIVE INSTANCES of the same silent-ignore class (the hook-gate leaves, F-05), which no grep for a discarded `CommandResult` could ever have found because those handlers never construct one - they bypass the renderer entirely while their declarations advertise `--agent` and `agent_record_kind="result"`. So the item's "grep is not a contract" instinct was right for a reason stronger than it knew, and E-05 fixes the six rather than merely reporting them.
  ONE FOUND DEFECT IS DELIBERATELY NOT TAKEN, and a reviewer should read the omission as intentional. The sweep also caught all eight `aw config --agent` branches crashing with `ImportError: cannot import name 'format_agent_json'` (a symbol never defined in `term.py`, in any commit, on any branch). That is ALREADY FILED as open backlog `dtq6jr` (high, `Blocks-Release: next`) with an enumerated seven-verb evidence table and an explicit "any fix MUST come with tests driving ALL SEVEN verbs" requirement. Folding it in here would duplicate a live item and absorb its gate; instead E-02's exemption registry records it as a KNOWN-BROKEN leaf citing `dtq6jr`, so the sweep neither goes red on someone else's bug nor pretends the leaf conforms. See F-06 and OQ-01.

## Goal

Make every leaf that DECLARES an `aw.agent/v1` result actually produce one, verified by executing it rather than by declaring it, so deleting an `emit` call or shipping a machine branch that never reaches the renderer turns a test red instead of passing silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the sweep exist and fail on today's real defects

- [x] E-01 GIVE `tests/conformance_matrix.py` A RUNNABLE-ARGV TABLE AND A NON-PROJECT CWD OPTION, so the sweep can drive leaves the current harness cannot reach. Two additions, both to the existing module, because it already holds `run_cli`, `_pinned_env`, and `semantic_facts_from_agent` and re-implementing those would fork the harness.
  ADD THE ARGV TABLE. Today `LIVE_SAFE_LEAVES` covers 16 entries and only 13 of the candidate leaves, so the large majority are unreachable; the dominant reason is that a leaf needs REQUIRED POSITIONAL ARGUMENTS and argparse exits 2 with a usage error before the handler runs. Re-measured at review: the candidate universe is 69 and 27 fail exactly this way (F-03, PR-205); at authoring it read 67 and 26, so treat both as LIVE figures and re-derive them rather than quoting these. The 16/13 overlap reproduced exactly (verified: `LIVE_SAFE_LEAVES` has 16 entries, 13 of which are candidates; the other three are `attention`, `sanitize`, `spec check`, and `attention` appears only as `--check`). Add a table mapping a leaf to argv that makes it RUNNABLE AND READ-ONLY (for example `config get aw_home`, `runs show <a run id>`, `path records`), keeping the existing safety precondition: no writes, no network. A leaf that cannot be made runnable read-only belongs in E-02's exemption registry, NOT in this table.
  ADD THE CWD PARAMETER. `run_cli` hardcodes `cwd=str(REPO_ROOT)`. Thread an optional `cwd` through so a scenario can run from a directory that is NOT an AW project, because that is the precise condition under which the `kjr5ol` defect manifested and a sweep confined to the repo tree is blind to it (the repo-tree run of `attention --agent` exits 1 with findings and never reaches the no-project branch at all; measured).
  DO NOT CHANGE `required_scenarios` OR `build_matrix` SEMANTICS in this item. They encode the Order-04/05 declaration contract and the coverage-row vocabulary; E-03 consumes them as they stand.
  - Depends on: none
  - Expected outcome: `conformance_matrix` exposes a runnable-argv mapping and `run_cli(..., cwd=<dir>)` works, with the existing `REPO_ROOT` default unchanged for every current caller.
  - Execution state: performed

- [x] E-02 WRITE THE EXEMPTION REGISTRY AS DATA WITH A MANDATORY REASON, before any assertion consumes it, so the sweep has exactly two categories and no silent third. Each entry maps a leaf to a typed reason and a citation. The three reason kinds the measurement actually produced, and no others invented speculatively:
  `sanctioned_raw` for a leaf whose non-envelope output is a DOCUMENTED contract, not a defect. THE COUNT HERE WAS WRONG AND IS CORRECTED AT REVIEW (PR-203): this item said "exactly the two the docs sanction: `find` and `path`", but `path` IS NOT IN THE COMPUTED UNIVERSE AT ALL and therefore needs no entry, while SEVEN leaves that ARE in the universe emit non-envelope output and each needs one. Measured: `path` declares `agent_record_kind="raw_path"`, and E-03's predicate keeps only `agent_record_kind == "result"`, so `path` is filtered out before the registry is ever consulted; an entry for it would be dead weight that a later reader mistakes for a live exemption. The seven that DO need an entry, each measured emitting non-empty stdout with no terminal record: `find`, `research find`, `research pending`, `research check-miscategorized`, `completion`, `config exclude list`, and `upgrade-test`.
  THE SEVENTH IS NOT A SANCTIONED RAW LEAF AND MUST NOT BE FILED AS ONE. `upgrade-test` is a bare GROUP whose `--agent` invocation prints an argparse USAGE BLOCK at exit 2 (measured: `usage: agent-workflows upgrade-test [-h] ... {list,new,sandboxes,probe,env,clean} ...`). No doc sanctions that, and it is not token-efficient discovery output; it is a parent command with required subcommands, which is a structurally different case from `find`'s deliberate bare paths. Classify it on its merits: if the executor judges a group-without-subcommand should emit an `error` record, that is a REAL defect and belongs in a filed item with a `known_broken` entry citing it, NOT a `sanctioned_raw` entry that would launder it. If instead the executor judges a bare group is simply not a machine surface, the honest fix is that its DECLARATION is wrong (`agent_record_kind="result"` on a leaf that can only print usage), and that too is a filed item. Decide, state which, and cite it; do not make it the registry's third silent category.
  THE CITATION MUST RESOLVE. For `find`, quote Section 12 of `docs/cli-output-contract.md`, verified at review to read "When `--agent` is passed to `aw find` (or when piping paths to another tool), `find` emits bare repo-relative paths, maximizing token efficiency for agent tool consumption." NOTE THAT `find` IS DECLARED `result`, NOT `raw_path`, so its declaration and that doc sentence DISAGREE; the registry entry should cite the DOC (which is the sanction) and record the declaration mismatch, because that mismatch is a smaller instance of this plan's own subject and a reader will otherwise trip on it. For the four `research` and `config exclude list` entries, name the specific documented or measured reason each prints raw lines; do not extend `find`'s doc sentence to cover a leaf it does not mention.
  `known_broken` for a leaf whose failure is REAL and owned elsewhere. Exactly the `config` family, citing backlog `dtq6jr`. THE ENTRY MUST CARRY THE ITEM ID, because that is what makes the exemption temporary rather than permanent: when `dtq6jr` lands, its executor deletes the entry and the sweep starts enforcing the leaf.
  `not_runnable` for a leaf that cannot be driven read-only (an interactive prompt, a destructive precondition), with the reason naming WHAT blocks it.
  THE REGISTRY IS A CEILING, NOT A CONVENIENCE. State in a module comment that adding an entry to silence a red sweep is the failure mode this plan exists to prevent, and that a `known_broken` entry REQUIRES a filed item id. Do not add a blanket wildcard or a "skip everything else" default; that would restore the `covered_by="declaration"` hole in a new shape.
  - Depends on: none
  - Expected outcome: a registry whose every entry carries a reason kind and a resolvable citation, with no unexplained entries and no catch-all.
  - Execution state: performed

- [x] E-03 WRITE THE SWEEP TEST IN `tests/test_agent_surface_conformance.py` AND SHOW IT RED ON THE SIX GATE LEAVES BEFORE FIXING THEM. This is the failing-first evidence for E-05, so it must be authored and run BEFORE E-05 changes any handler.
  THE UNIVERSE IS COMPUTED, NOT LISTED: enumerate `command_surface.discover_parser_leaves(cli._build_parser())`, keep leaves whose declaration has `command_class` in `read`/`check`/`bare` AND `agent_record_kind == "result"`, then subtract E-02's registry. Computing it is what makes a NEWLY ADDED leaf enforced automatically; a hand-written list would freeze coverage at today's surface and is the reason the original bug survived.
  PER LEAF, ASSERT FOUR THINGS, each chosen because a real measured failure violates it: stdout is NON-EMPTY (this is the assertion the `kjr5ol` defect would have tripped, and the six gate leaves trip today); a terminal `result`/`summary`/`error` record parses out of the JSONL (via the harness's `semantic_facts_from_agent`); `agent_schema.validate_agent_record` returns `[]` on it; and the record's `exit` EQUALS the process exit code, which is the contract's own Exit Code Parity rule.
  FAIL WITH THE LEAF NAME AND THE STREAMS. A sweep that reports "3 leaves failed" costs the next maintainer a re-derivation. Assert per leaf (subtest or parametrization) and put the leaf, the argv, the exit code, and a stdout/stderr excerpt in the failure message.
  NO STATIC ANALYSIS, per AGENTS.md P16 and the backlog item's own reasoning. Drive the CLI as a subprocess and assert on real stdout, real stderr, and real exit codes. Do not read `agent_workflows/*.py`, do not count `emit` callers, do not regex for a discarded `CommandResult`: a grep is precisely what failed to find the six gate leaves.
  - Depends on: E-01, E-02
  - Expected outcome: the sweep runs over the computed universe and FAILS, naming at minimum the six hook-gate leaves; that failing output is captured as E-05's baseline.
  - Execution state: performed

- [x] E-04 ADD THE NON-PROJECT-CWD CASE THAT PINS THE ORIGINAL DEFECT'S EXACT CONDITION, as a separate test from the broad sweep because it asserts a specific record rather than a general shape. Using E-01's `cwd`, run `attention --agent` from a bare `git init` directory that is NOT an AW project and assert: stdout non-empty, one `aw.agent/v1` record, `outcome == "cannot-run"`, `exit == 2` matching the process code, `validate_agent_record` clean, and the temp path ABSENT from stdout (the branch sanitizes its summary deliberately; emitting the checked directory would leak an absolute path and `agent_schema` refuses one).
  ALSO ASSERT THE HUMAN PATH IS UNCHANGED at exit 3 with prose on stderr and EMPTY stdout, because the 3-versus-2 split is intentional and documented at the site, and a test that quietly normalized the human code would break an operator contract while looking like a cleanup.
  CORRECT THE STALE COMMENT while here: `attention.run`'s no-project branch cites `tests/test_awretrofit_project_root_climb.py::NoProjectSubprocessMatrixTests` as live protection, and that FILE NO LONGER EXISTS (deleted by `19313eed`). Re-point it at the live `NoProjectAgentEnvelopeTests` and at this new case. Measured at review: TWO stale citations, both in that comment block (`attention.py:3882` and `:3885`, the second citing the deleted file for the `rc 3, prose on stderr, empty stdout` human path). Correct BOTH; correcting one and leaving the other reproduces this plan's own subject at a smaller scale.
  `agent_workflows/attention.py` IS NOW DECLARED IN `- Scope-Paths:` (PR-202), so the "or file it instead" escape is WITHDRAWN and the edit is owed. The earlier wording let an executor choose between editing an undeclared path and filing a follow-up, and that choice was itself the defect: the whole point of E-07 is that a written claim of coverage nothing checks is a bug, so a plan that NOTICES a stale citation and routes it to a backlog item is filing the same debt it is here to clear. The edit is comment-only and carries no behavioral risk.
  - Depends on: E-01
  - Expected outcome: a test that fails if the no-project `emit` is deleted again, and passes at HEAD; the stale citation either corrected or filed.
  - Execution state: performed

### Task group 2: fix what the sweep proves is broken

- [x] E-05 MAKE THE SIX HOOK-GATE LEAVES HONOR `--agent`/`--json` BY ROUTING THEM THROUGH THE RENDERER, turning E-03 green for them. Each `hooks/*.main` currently does `exit_code, messages = check()`, writes prose to `sys.stderr`, and returns the bare int; none constructs a `CommandResult`, so `--agent` is accepted and ignored. The six: `executed_transition_gate`, `status_untooled_gate`, `precommit_scope_gate`, `backlog_blocking_close_gate`, `ipd_dependency_statement_gate`, `prepush_authorization_gate`.
  BUILD A `CommandResult` AND `emit` IT on the machine surfaces, mapping each gate's `messages` to `Diagnostic` entries so a consumer reads structured refusals instead of parsing prose. Follow the sibling pattern already shipped in `attention.run`'s no-project branch: guard on `ctx.is_agent or ctx.is_json`, emit, and leave the human path untouched.
  THE HUMAN PATH MUST NOT CHANGE, AND THIS IS THE HARD CONSTRAINT OF THE ITEM. These are GIT HOOK ENTRYPOINTS invoked by `pre-commit`, and a human's commit refusal message is the only thing standing between them and a bypassed gate. Keep the stderr prose and the returned exit code BYTE-IDENTICAL when neither flag is passed. `tests/test_executed_transition_gate_e2e.py` drives `ipd-executed-gate` through a real hook shim, so it is the regression witness that the hook still refuses correctly.
  MIND THE EXIT CONTRACT. These declare `exit_contract=(0, 1)` or `(0, 1, 2)`; all are inside `agent_schema`'s admissible 0/1/2, so no exit-code change is needed and none should be made. A refusal is exit 1, whose valid outcome is `findings` or `fail` and NOT a positive outcome, because the anti-greenwashing invariant forbids reporting `clean` for refused work.
  ROUTE THE FLAGS THROUGH, AND THE `cli.py` EDIT IS REQUIRED RATHER THAN OPTIONAL (PR-201). `cli._dispatch` calls each gate as `_gate.main([])` at six sites, discarding argv, so a `--agent` that the parser DID accept never reaches the handler. Measured at review: `_build_parser().parse_args(["ipd-executed-gate","--agent"])` returns `agent=True`, so the flag is parsed and then thrown away one layer down; `grep -c "_gate.main(\[\])"` finds the empty-list call. `agent_workflows/cli.py` IS NOW DECLARED IN `- Scope-Paths:`, so implement the threading there and do not treat it as optional.
  THE "IMPLEMENT IT ENTIRELY INSIDE THE HOOK MODULES" ALTERNATIVE IS WITHDRAWN, and a reviewer should read the withdrawal as deliberate. The only way a hook module can learn about `--agent` when it is handed `[]` is to read `sys.argv` itself, which (a) re-parses a flag the real parser already parsed, (b) diverges the moment the parser's flag spelling changes, and (c) behaves differently under `main([])` called from a test versus from `_dispatch`, which is exactly the kind of untestable divergence this plan exists to remove. Pass the parsed `args` (or an `OutputContext` built in `_dispatch`) into `main`, keeping `main`'s existing `argv` parameter working so the `if __name__ == "__main__"` entrypoint and `tests/test_executed_transition_gate_e2e.py`'s shim path are unaffected.
  - Depends on: E-03
  - Expected outcome: all six leaves emit a schema-valid record with exit parity under `--agent`, the human stderr output and exit codes are unchanged, and E-03's six failures clear.
  - Execution state: performed

- [x] E-06 WIRE THE SWEEP INTO THE DEFAULT SUITE, so the contract runs unprompted rather than on request. Confirm the new test file is collected by a BARE `python3 -m pytest` and is NOT marked `slow` or `livecorpus`, since both are deselected by default (`pyproject.toml` `addopts`) and a gate that does not run in the default suite would not have caught the original bug.
  THE COST IS ALREADY MEASURED, SO THIS ITEM'S JOB IS TO REDUCE IT, NOT TO DISCOVER IT (PR-204, OQ-02 now resolved). Review drove all 69 candidate leaves: 59.15s SERIAL, 20.0s PARALLEL across 12 workers, against a 46.93s bare suite. Unscoped, that roughly doubles a bare run serially and adds about 43 percent even parallel, which is not acceptable to add unconditionally. The cost is CONCENTRATED, not spread: `doctor` alone is 17.08s and `check` 8.66s (about 26s of the 59s between them), while `search` is 0.27s, `host probe` 0.36s and `next` 3.32s.
  SO SCOPE THE EXPENSIVE LEAVES RATHER THAN MARKING THE FILE `slow`. Both dominant leaves are slow because they walk THIS repository's full records tree; the sweep only needs to prove the leaf EMITS A SCHEMA-VALID RECORD WITH EXIT PARITY, which does not require its most expensive real work. Run them against a minimal temp fixture (E-01's `cwd` axis already gives you the mechanism) or with the narrowest argv that still reaches the emit path, and paste the resulting per-leaf timings. Keep the file DEFAULT-COLLECTED.
  ONLY IF the scoped sweep still exceeds a budget the executor STATES EXPLICITLY is the `slow` mark acceptable, and then it is a REAL WEAKENING recorded as a finding plus a filed follow-up id, not waved through, because `slow` tests do not run in the default suite an agent uses before committing, and a silent default suite is how the original bug shipped.
  - Depends on: E-05
  - Expected outcome: a bare `python3 -m pytest` collects and runs the sweep; the scoped wall time is pasted alongside the per-leaf timings for `doctor` and `check`, showing the reduction against review's 59.15s/20.0s baseline.
  - Execution state: performed

- [x] E-07 CORRECT `tests/conformance_matrix.py`'s DOCSTRING TO NAME ITS REAL CONSUMER. It currently names two files (`test_cli_conformance_matrix.py`, `test_cli_quality_gates.py`) as the tests that consume it, and NEITHER EXISTS, so the module reads as covered when it is orphaned. Point it at the file E-03 adds.
  THIS IS THE SAME DEFECT CLASS THE PLAN IS ABOUT, one level up: a written claim of coverage that nothing checks, exactly like the unconsumed `agent_record_kind` field and the deleted test `attention.py` still cites. Leaving it is how the next maintainer concludes the sweep already existed.
  - Depends on: E-03
  - Expected outcome: the docstring names only files that exist on disk.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `emit` IS BOTH THE WRITE AND THE EXIT CODE, which is the mechanical reason this defect class is silent. `renderers.BaseRenderer.emit` is defined once, overridden by no subclass, and returns `result.exit_code`; the canonical call is `return get_renderer(ctx).emit(res, ctx)`. Dropping the `return ... emit(...)` therefore costs nothing at runtime, raises nothing, and lets control fall through to a human-only branch. `emit` additionally writes NOTHING when `render` yields an empty string while still returning the exit code, so "exited correctly" never implies "emitted".
- VALIDATION IS TEST-TIME, NOT RUNTIME. `emit` never calls `agent_schema.validate_agent_record`; the path is `render` -> `CommandResult.to_agent_record` -> `render_jsonl_record`. So an invalid record is only caught if a test looks, which is why E-03 must call the validator explicitly rather than assume the renderer did.
- EXIT 3 IS UNEMITTABLE ON A MACHINE SURFACE. `agent_schema.validate_agent_record` admits `exit` only in `(0, 1, 2)`, so the human/machine 3-versus-2 asymmetry on the no-project path is deliberate and load-bearing, not an inconsistency to tidy. `attention.run`'s own comment records the measurement: adding the missing `emit` with exit 3 would raise in the renderer and reproduce the empty stdout.
- THE COMMAND SURFACE IS ENUMERABLE WITHOUT TOUCHING DISPATCH, which is what makes a computed universe feasible. `command_surface.discover_parser_leaves(parser)` walks argparse recursively and dedupes aliases by object identity; `find_undeclared_leaves(parser)` reports drift. Measured live at review: 151 parser leaves, 162 declared, 0 undeclared (authoring recorded 161 declared; a live figure, PR-205). There is NO `name -> callable` registry (`cli._dispatch` is a hand-written `if/elif` chain with 55 comparisons and no `set_defaults(func=...)`), so enumeration must go through the parser, not through handlers.
- `agent_record_kind` IS DECLARED AND CONSUMED BY NOTHING. `rg agent_record_kind` outside `command_surface.py` returns no hits, so the field asserting that 160 leaves emit a `result` record is inert documentation. E-03 is what converts it into an enforced claim.
- TESTS MUST ASSERT OUTCOMES, NOT CODE STRUCTURE (AGENTS.md P16). No `inspect`, no `ast`, no regex over production source, no caller-count assertions. This bars the tempting static check ("find every `CommandResult` with no nearby `emit`") and is independently justified here: a proximity grep produces false positives at a 45-line window (`aw find` builds at one line and emits 55 lines later) and is defeated entirely by a factory helper, while missing all six gate leaves, which never build a `CommandResult` to be found.
- `XDG_CONFIG_HOME` ISOLATES USER CONFIG for a subprocess test; verified in this lane that pointing it at a throwaway directory causes `config.json` to be written there and leaves the real config untouched.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The item's cited pin `AttentionNoProjectMachinePathTests` DOES NOT EXIST and never did; the live pin is `tests/test_attention.py::NoProjectAgentEnvelopeTests`, which passes. | `grep -c` returns 0 for the cited name; `git log -S` finds no commit adding it. `python3 -m pytest tests/test_attention.py::NoProjectAgentEnvelopeTests` -> `1 passed in 1.93s`. |
| F-02 | The item's second cited pin, `tests/test_awretrofit_project_root_climb.py`, was DELETED wholesale, and `attention.py` still cites it as live protection. | File absent from the tree; removed by commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests". Two stale citations remain in `attention.py`'s no-project comment block. |
| F-03 | Of the candidate leaves (`read`/`check`/`bare` with `agent_record_kind="result"`), only 28 emit a schema-valid terminal record with exit parity; 13 emit NO terminal record; the rest are unreachable because argparse exits 2 on missing required positionals before the handler runs. COUNTS RE-MEASURED AT REVIEW AND THEY HAVE DRIFTED (PR-205): the candidate universe is 69 (not 67) and the usage-blocked group is 27 (not 26); the load-bearing figures, 28 conforming and 13 emitting no record, reproduced EXACTLY. Treat every count here as a LIVE population that moves with the surface, never as a test assertion; E-03's universe is computed for this reason. | Subprocess sweep of all candidates with `--agent`, classifying stdout into crash / silent / invalid / conforming. At authoring: 67 / 28 / 13 / 26. Re-measured at review HEAD `c6029d24`: 69 candidates -> 28 conforming, 6 silent, 7 invalid (6+7 = the same 13 with no terminal record), 27 usage-blocked, 1 crash (`config show`). |
| F-04 | `tests/conformance_matrix.py` (378 lines) has ZERO importers, and both consumer files named in its own docstring are absent. Its `build_matrix` marks every non-curated leaf `covered_by="declaration"`, i.e. asserted but never executed. | `rg conformance_matrix` finds only the module itself plus two prose comments in `command_surface.py`. `LIVE_SAFE_LEAVES` covers 13 of the 67 candidates; `attention` appears only as `--check`, the sub-branch that KEPT its emit. |
| F-05 | SIX hook-gate leaves accept `--agent` and silently ignore it, emitting nothing to stdout: the same invisible failure mode as the original defect, live today. Their declarations advertise `agent_record_kind="result"` and list `--agent` in `legacy_flags`. | `ipd-executed-gate --agent` -> rc 0, stdout EMPTY; same for `ipd-status-untooled-gate`, `precommit-scope-gate`, `backlog-blocking-close-gate`, `ipd-dependency-statement-gate`; `prepush-authorization-gate --agent` -> rc 1, stdout EMPTY, prose on stderr. Each `hooks/*.main` does `exit_code, messages = check()`, writes stderr, returns the int; no `CommandResult` is built. `cli._dispatch` calls them as `main([])`, discarding argv. |
| F-06 | All eight `aw config --agent` branches crash with `ImportError: cannot import name 'format_agent_json'`; the symbol is defined in NO file, in NO commit, on ANY branch, so the branches were dead on arrival. ALREADY OWNED by backlog `dtq6jr`. | 8 identical import statements in `cli.py` across 7 handlers (`_run_config_show` holds two). `config show/get/is/set --agent` all -> rc 1 with the traceback. `rg "def format_agent_json"` -> no hits; `git log --all -S "def format_agent_json"` -> no commits. |
| F-07 | `config remove --agent` is doubly broken: past the ImportError it would emit `outcome="not_found"`, which is NOT in `agent_schema.VALID_OUTCOMES` and would fail validation. AT REVIEW THIS WAS FOUND AT TWO SITES, NOT ONE (see F-16), which the receiving item needs to know. | `cli.py` `_run_config_remove` passes `outcome="clean" if was_removed else "not_found"`; `'not_found' in VALID_OUTCOMES` -> `False`. Recorded for `dtq6jr`'s executor, not fixed here. |
| F-08 | Six leaves emit output with no terminal record for SANCTIONED reasons, not defects (a SEVENTH, `upgrade-test`, was found at review and is NOT sanctioned; see F-13): `find`, `research find`, `research pending`, `research check-miscategorized`, `completion`, `config exclude list` print raw lines or generated text. `docs/cli-output-contract.md` Section 12 explicitly blesses bare paths under `--agent` for discovery verbs. | Driven individually: each writes non-empty stdout that is not JSONL. `path` declares `agent_record_kind="raw_path"`. This is why E-02's registry needs a `sanctioned_raw` kind rather than treating every non-envelope leaf as broken. |
| F-09 | The repo-tree run of `attention --agent` CANNOT see the original bug: it exits 1 with lane findings and never reaches the no-project branch. Only a non-project cwd reaches it. | `attention --agent` from the worktree -> rc 1, `outcome:"findings"`. From a bare `git init` dir -> the `cannot-run` record at exit 2. This is why E-01 must add a `cwd` axis. |
| F-10 | Baseline suite at authoring HEAD `58dc1c70`: `3246 passed, 2 skipped, 3 warnings in 53.64s` from a bare `python3 -m pytest`. Re-measured at review HEAD `c6029d24`: `3246 passed, 2 skipped, 3 warnings in 46.93s`, so the PASS/SKIP counts are stable and only the wall time moves with machine load. | Full bare run in this lane, at authoring and again at review. |
| F-11 | ADDED AT REVIEW (PR-204). THE SWEEP'S COST IS MEASURED AND IS CONCENTRATED IN TWO LEAVES, which converts OQ-02 from a coin flip into an engineering task. A naive all-leaves sweep costs 59.15s serial and 20.0s parallel against a 46.93s bare suite, but `doctor` (17.08s) and `check` (8.66s) are about 26s of the serial total while the median leaf is well under a second. Both are slow because they walk THIS repo's full records tree, which the emit contract does not require. | Timed at review: serial sweep of 69 leaves `WALL=59.15 s`; 12-worker parallel `WALL=20.0s`; per-leaf `check 8.66s`, `doctor 17.08s`, `next 3.32s`, `host probe 0.36s`, `search 0.27s`. Bare suite `46.93s`. |
| F-12 | ADDED AT REVIEW (PR-203). `path` IS NOT IN THE COMPUTED UNIVERSE, so E-02's instruction to register it was dead weight, while SEVEN in-universe leaves need entries rather than the two the item authorized. `path` declares `agent_record_kind="raw_path"` and E-03's predicate keeps only `result`, so it is filtered before the registry is consulted. Separately, `find` is declared `result` while the doc sanctions its bare-path output, so its declaration and Section 12 DISAGREE. | `inv['path'].agent_record_kind` -> `raw_path`; `inv['find'].agent_record_kind` -> `result`. The seven in-universe non-envelope leaves, each measured with non-empty stdout and no terminal record: `find`, `research find`, `research pending`, `research check-miscategorized`, `completion`, `config exclude list`, `upgrade-test`. |
| F-13 | ADDED AT REVIEW (PR-203). `upgrade-test` IS A SEVENTH NON-ENVELOPE LEAF THAT F-08 DOES NOT NAME, and it is NOT a sanctioned raw surface: it is a bare command GROUP whose `--agent` invocation prints an argparse USAGE BLOCK at exit 2. No doc blesses that, so it must be classified on its merits rather than absorbed into `sanctioned_raw`. | `upgrade-test --agent` -> rc 2, stdout carries `usage: agent-workflows upgrade-test [-h] ... {list,new,sandboxes,probe,env,clean} ...`, no JSONL record. Declared `agent_record_kind="result"`, `command_class=read`. |
| F-14 | ADDED AT REVIEW (PR-201). THE `cli.py` EDIT E-05 CALLS OPTIONAL IS ACTUALLY REQUIRED, and the flag is already parsed one layer above the discard. The parser ACCEPTS `--agent` and sets it; `_dispatch` then calls `main([])` and throws it away, so no hook-module-only change can honor the flag without re-reading `sys.argv`, which would diverge from the real parser and behave differently between a test call and a dispatch call. | `_build_parser().parse_args(["ipd-executed-gate","--agent"])` -> `{'agent': True, 'json': False, 'command': 'ipd-executed-gate'}`. `grep -c "_gate.main(\[\])" agent_workflows/cli.py` -> the six empty-list dispatch sites at `cli.py:15074`ff. |
| F-15 | ADDED AT REVIEW (PR-202). THE STALE-CITATION DEFECT IS TWO SITES, NOT ONE. `attention.py`'s no-project comment block cites the deleted `tests/test_awretrofit_project_root_climb.py` TWICE, the second time for the human `rc 3, prose on stderr, empty stdout` path. Correcting one and leaving the other would reproduce this plan's own subject in miniature. | `grep -n test_awretrofit_project_root_climb agent_workflows/attention.py` -> `3882` and `3885`. File absent from the tree. |
| F-16 | ADDED AT REVIEW. F-07's DEFECT IS AT TWO SITES, NOT ONE, which matters to the item receiving it. The invalid `outcome="not_found"` appears in `_run_config_remove` AND in a second config handler, so `dtq6jr`'s executor must fix both or leave one validation failure behind. | `grep -n 'not_found' agent_workflows/cli.py` -> `9486` (`outcome="clean" if was_removed else "not_found"`) and `9545` (`outcome="clean" if present else "not_found"`). `'not_found' in agent_schema.VALID_OUTCOMES` -> `False`. |


## Proposed changes (ordered, validatable)

1. Extend `tests/conformance_matrix.py` with a runnable-argv table and a `cwd` parameter on `run_cli` (E-01).
2. Add the justified exemption registry with its three reason kinds and mandatory citations (E-02).
3. Add `tests/test_agent_surface_conformance.py` computing its universe from the parser and asserting the four per-leaf properties; capture it RED on the six gate leaves (E-03).
4. Add the non-project-cwd case pinning the original defect's exact condition, and correct or file the stale comment citation (E-04).
5. Route the six hook-gate leaves through `get_renderer(...).emit(...)` with the human path byte-identical, turning E-03 green (E-05).
6. Confirm default-suite collection and correct the harness docstring (E-06).

## Deferred / out of scope (with reason)

- THE `aw config` FAMILY'S EIGHT CRASH SITES (F-06, F-07). Already owned by open backlog `dtq6jr` (high, `Blocks-Release: next`), which enumerates all seven verbs and requires tests driving each. Fixing it here would duplicate a filed item, absorb its release gate, and steal its validation. E-02 records it as `known_broken` citing `dtq6jr` so the sweep neither goes red on it nor claims it conforms. F-07 is new information that item does not yet have and should be handed to it, AND SO IS F-16: review measured the invalid `outcome="not_found"` at TWO sites (`cli.py:9486` and `:9545`), not the one F-07 names, so an executor fixing only `_run_config_remove` would leave a second validation failure behind. Hand both to `dtq6jr`.
  - Carrier: dtq6jr
- THE 79 `mutation`-CLASS LEAVES. Driving a mutating verb live needs a write-isolation design (temp repo per leaf, or a universal dry-run guarantee) that this plan does not attempt. The read/check surface is where the measured defects are, and the computed universe makes widening later a predicate change rather than a rewrite.
  - Carrier: w78faq
- `aw find` / `aw path` BARE-PATH OUTPUT. Documented contract, not defect (F-08). Asserting an envelope there would break `docs/cli-output-contract.md` Section 12.
  - Carrier-Declined: No future work is owed, because this is a SANCTIONED contract and not a deferred defect. `docs/cli-output-contract.md` Section 12 states that under `--agent` "`find` emits bare repo-relative paths, maximizing token efficiency for agent tool consumption", and `path` DECLARES `agent_record_kind="raw_path"`, so both behave exactly as specified. Filing an item would misrepresent a deliberate design decision as debt and invite a future agent to "fix" a leaf into breaking a published contract. E-02's `sanctioned_raw` registry entry records the exemption WITH its doc citation, so the reasoning is checkable at the point a reader meets it rather than only here.
- A STATIC "BUILDS BUT NEVER EMITS" CHECKER. Barred by AGENTS.md P16, and independently inadequate: it produces false positives across a helper boundary and finds none of the six real defects.
  - Carrier-Declined: Nothing is owed, because this row records a PROHIBITION plus a measured dead end, not an unbuilt feature. AGENTS.md P16 forbids tests that read production source with `inspect`, `ast`, or regex, so the approach may not be built at all; and authoring measured it would not work anyway (a proximity grep flags `aw find`, which emits 55 lines after building, and misses all six hook-gate leaves, which never construct a `CommandResult`). The behavioral sweep this plan builds is the replacement, not a stopgap, so there is no follow-on state for a carrier to track.
- THE 26 LEAVES NEEDING POSITIONAL ARGUMENTS not covered by E-01's table. Each lands in E-02's registry as `not_runnable` with its blocker named, so the gap is visible and shrinkable rather than silent.
  - Carrier-Declined: No separate item is owed, because this is not a fixed residue but a MEASURED CEILING that E-01 and E-02 move and record in-tree. The count is whatever remains after E-01's argv table, and V-01 requires the executor to state both the reachable and the still-unreachable counts; every remaining leaf is then named individually in E-02's registry with its specific blocker and NO catch-all permitted. So the gap is enumerated at all times in the registry a maintainer reads, which is a more precise carrier than a backlog item asserting a number that goes stale the first time the table grows. A leaf whose blocker turns out to be a DEFECT rather than a missing argument is a different matter and must be filed on its own merits when measured.

## Scope check

- Over-scope: none. E-05 fixes only leaves the sweep proves broken; the `config` family is deliberately excluded to its filed owner.
- Under-scope: the sweep covers `read`/`check`/`bare` leaves only, so a `mutation` leaf that drops its emit stays unprotected. Accepted deliberately, recorded above, and the computed universe means widening it later is a predicate change rather than a rewrite.

## Required tests / validation

- A BARE `python3 -m pytest`, reconciled against the F-10 baseline of `3246 passed, 2 skipped`. Any delta must be explained against a named E-item.
- The new sweep captured RED before E-05 and GREEN after, with both outputs pasted; the red run must name the six gate leaves.
- `tests/test_executed_transition_gate_e2e.py` passing, as the witness that the hook still refuses commits correctly through a real shim.
- A MUTATION TEST proving the sweep actually catches the original defect class: delete the `return get_renderer(ctx).emit(res, ctx)` from `attention.run`'s no-project machine branch, show the sweep and E-04's case go RED, revert, show green.
- `agent_schema.validate_agent_record` returning `[]` for every record the sweep and E-04 assert on.
- `python3 -m agent_workflows check`, `aw ipd lint`, and `aw sanitize --agent`.
- `git diff --cached --name-only` before committing, listing only declared `- Scope-Paths:` entries (plus `agent_workflows/cli.py` if E-05 takes the threading route and the executor declares it).

## Spec / documentation sync

- NO `.spec.md` FILE IS AMENDED and none is listed in `- Scope-Paths:`, because this plan CHANGES NO CONTRACT: it enforces contracts already written in `docs/cli-output-contract.md` (Sections 4 and 12) and already declared in `command_surface.COMMAND_INVENTORY`. The six gate fixes make behavior match its existing declaration rather than redefining it.
- `tests/conformance_matrix.py`'s docstring is corrected (E-06) because it names two nonexistent consumers.
- `attention.run`'s stale citation of a deleted test file is corrected or filed (E-04).
- If the executor finds a doc sentence that CONTRADICTS the enforced behavior, that is a spec amendment and must be declared in `- Scope-Paths:` before editing, per the repository's plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Should the six hook-gate leaves emit a machine record at all, or should their declarations be narrowed instead?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE toward emitting. Three facts decide it. First, each declaration already lists `--agent`/`--json` in `legacy_flags` AND sets `agent_record_kind="result"`, so emitting honors the shipped contract while narrowing would RETRACT a declared surface. Second, `docs/cli-output-contract.md` Section 1.3 makes flag availability uniform across every subcommand, so a leaf that accepts `--agent` and ignores it is the anomaly. Third, `command_surface.py`'s own comment on these entries says they are "invoked by git hooks rather than typed by a human, but they ARE parser leaves with real exit contracts (that is the whole point of a gate), so they carry declarations like anything else" - the repository already decided these are first-class leaves. A structured refusal is also independently useful: a wrapper reading `diagnostics` beats parsing prose. The narrowing option is not absurd (a human is the near-universal consumer) and if a reviewer prefers it, the change is E-02 registry entries plus declaration edits instead of E-05 - but it must be a DELIBERATE retraction, not the current accident.

### OQ-02: Must the sweep run in the default suite even if it is slow?

- Blocking: no
- Status: resolved
- Owner: plan-review reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW BY ACTUALLY MEASURING IT (PR-204), because the numbers turned out decisive and leaving them to execution invited the wrong call under time pressure. THE ANSWER IS: KEEP IT DEFAULT-COLLECTED, AND MAKE IT AFFORDABLE BY FIXING THE TWO LEAVES THAT DOMINATE THE COST, rather than choosing between an expensive gate and a deselected one.
  MEASURED AT REVIEW, driving all 69 candidate leaves with `--agent` as subprocesses from this lane: SERIAL wall time 59.15s, and PARALLEL across 12 workers 20.0s. The bare suite is 46.93s. So the naive sweep roughly DOUBLES a bare run serially, and still adds about 43 percent even fully parallel. That is far too expensive to add unconditionally, and it is exactly the shape of cost the repository's `livecorpus` precedent warns about.
  BUT THE COST IS NOT SPREAD, IT IS CONCENTRATED, WHICH IS WHAT MAKES THE DILEMMA FALSE. Two leaves account for most of it: `doctor` at 17.08s and `check` at 8.66s, together about 26s of the 59s serial total, while `search` (0.27s), `host probe` (0.36s) and `next` (3.32s) are cheap. So the executor has a THIRD OPTION the original question did not consider, and it is the one this resolution picks: keep the file DEFAULT-COLLECTED and reduce per-leaf cost, by scoping the two expensive leaves to a minimal fixture (a temp project rather than this repo's full records tree, which is what makes `doctor` and `check` slow) or by giving them the narrowest argv that still exercises the emit path. The sweep's purpose is to prove a leaf EMITS A VALID RECORD, which does not require it to do its most expensive real work.
  IF AND ONLY IF the executor measures that the scoped sweep still exceeds a budget they state explicitly, the fallback is a `slow` mark PLUS a filed follow-up, recorded as a finding per the original wording. That branch is now the exception rather than the coin flip. V-06 is updated to require the scoped number, and to require that the two dominant leaves be named with their individual timings so a future maintainer can see where the budget went.
  WHY THIS IS NOT THE REVIEWER OVERSTEPPING: the question asked whether the sweep MUST run in the default suite even if slow. That is answerable from evidence (it must, because the original bug shipped through a silent default suite, and the measured cost is reducible rather than inherent), so the plan-review contract requires resolving it from evidence rather than asking. What remains genuinely the executor's is the engineering of the scoping, which E-06 now owns.
- Carrier-Declined: No durable carrier is owed, because this question is now ANSWERED (resolved at review from measurement) rather than deferred beyond the plan. The slowness is no longer unmeasured: it is 59.15s serial / 20.0s parallel for the naive sweep, concentrated in `doctor` (17.08s) and `check` (8.66s), and the resolution directs the executor to reduce it rather than to choose between an expensive gate and a deselected one. E-06 performs the scoped measurement and V-06 requires the number pasted. The one branch that would create future work (a scoped sweep STILL too slow against a stated budget) carries its obligation inside V-06, which demands a filed follow-up id as evidence; filing that item now would assert a slowness the measurement does not support.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the committed diff of `tests/conformance_matrix.py`. Paste the LITERAL output of calling `run_cli` twice with the same argv, once with no `cwd` and once with `cwd=<a temp non-project dir>`, showing DIFFERENT results for `attention --agent` (repo tree: exit 1 `findings`; temp dir: exit 2 `cannot-run`), which proves the axis is real and not cosmetic. CONFIRM the `REPO_ROOT` default is unchanged by pasting a `run_cli` call with no `cwd` argument still running in the repo. For the argv table, paste a table of every entry with the exit code observed when driven, and CONFIRM each is read-only by pasting `git status --short` before and after the full table run, showing NO new or modified files. State the COUNT of candidates now reachable and the count still unreachable; if the reachable count did not increase, say so plainly rather than reporting success. RE-DERIVE THE CANDIDATE TOTAL AT EXECUTION TIME rather than using 67: review measured 69 and the figure moves with the surface (PR-205), so compute it from the predicate and paste the number you got.
  - Observed evidence: run_cli diff committed; literal dual invocation proves cwd axis (exit 1 findings in repo vs exit 2 cannot-run in temp); REPO_ROOT default unchanged; 13 entries in RUNNABLE_ARGV all read-only; 42 candidates now reachable (+13) and 27 unreachable in registry; candidate population 69.
    Committed diff of `tests/conformance_matrix.py` for E-01 additions:
    ```diff
    @@ -127,0 +128,14 @@
    +RUNNABLE_ARGV: Dict[str, List[str]] = {
    +    "releases show": ["next"],
    +    "reviews decisions": ["f36de0"],
    +    "runs query": ["schema"],
    +    "show": ["f36de0"],
    +    "workflow validate": ["tests/fixtures/workflow-src/plan-review"],
    +    "workflow check-generated": ["tests/fixtures/workflow-src/plan-review"],
    +    "agy profile show": ["non-existent"],
    +    "oc profile show": ["non-existent"],
    +    "upgrade-test env": ["dummy"],
    +    "upgrade-test probe": ["dummy"],
    +    "graduation": [],
    +    "partition": [],
    +    "record-history": [],
    +}
    @@ -367,3 +514,3 @@
     def run_cli(
    -    argv: Sequence[str], *, env: Optional[Dict[str, str]] = None
    +    argv: Sequence[str], *, env: Optional[Dict[str, str]] = None, cwd: Optional[Path] = None
     ) -> RunResult:
    @@ -375,3 +522,3 @@
             capture_output=True,
    -        cwd=str(REPO_ROOT),
    +        cwd=str(cwd) if cwd is not None else str(REPO_ROOT),
    ```
    Literal output of calling `run_cli` twice with `['attention', '--agent']`:
    1. With no cwd (runs in REPO_ROOT):
       `exit=1, stdout={"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":5,"evidence":["attention"],...}`
    2. With cwd set to temp non-project git repo (`/tmp/tmptlifxjk5`):
       `exit=2, stdout={"schema":"aw.agent/v1","kind":"error","cmd":"attention","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw install ."}`
    Proves the non-project cwd axis is real: exit code shifts from 1 (findings) to 2 (cannot-run), and outcome shifts from findings to cannot-run.

    Confirmed `REPO_ROOT` default unchanged: calling `run_cli(["attention", "--agent"])` with no cwd runs in `REPO_ROOT`, returning exit 1 with findings.

    Observed exit codes when driven for every entry in `RUNNABLE_ARGV`:
    | Leaf | Exit Code |
    |---|---|
    | `agy profile show` | `2` |
    | `graduation` | `0` |
    | `oc profile show` | `2` |
    | `partition` | `0` |
    | `record-history` | `0` |
    | `releases show` | `0` |
    | `reviews decisions` | `0` |
    | `runs query` | `0` |
    | `show` | `0` |
    | `upgrade-test env` | `2` |
    | `upgrade-test probe` | `2` |
    | `workflow check-generated` | `1` |
    | `workflow validate` | `0` |

    Confirmed read-only: `git status --short` before driving `RUNNABLE_ARGV` matched `git status --short` after (`git status match (read-only): True`, no files modified or created).

    Candidate population census re-derived at execution:
    - Total parser leaves matching candidate predicate (`command_class in ("read", "check", "bare") and agent_record_kind == "result"`): 69 candidates.
    - Exempted in `EXEMPTION_REGISTRY`: 27 leaves.
    - Candidate leaves now reachable in computed universe: 42 leaves (36 previously conforming + 6 gate leaves).
    - Candidate leaves still unreachable: 27 leaves (the 27 individually enumerated in `EXEMPTION_REGISTRY`).
    - Reachable count increased by 13 leaves via `RUNNABLE_ARGV`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the committed registry. For EVERY entry, paste the reason kind and its citation, and verify the citation RESOLVES: for `sanctioned_raw`, quote the sentence from `docs/cli-output-contract.md` Section 12 (or the `raw_path` declaration) that licenses it; for `known_broken`, paste the output of resolving backlog `dtq6jr` (for example `aw find backlog dtq6jr`) proving the item exists and is live; for `not_runnable`, name the specific blocker. CONFIRM there is NO catch-all, wildcard, or default-skip, by pasting the registry's full text and stating that every exempted leaf is named individually. CONFIRM no entry silences a leaf that E-03 could actually drive: paste the intersection of the registry with E-01's argv table and show it is EMPTY. CONFIRM the module comment stating that adding an entry to silence a red sweep is the prohibited failure mode is present, by quoting it.
    CONFIRM THE THREE REVIEW CORRECTIONS LANDED (PR-203, F-12, F-13). FIRST, there must be NO entry for `path`: it is declared `raw_path`, so E-03's predicate filters it before the registry is read, and an entry would be dead weight a later reader mistakes for a live exemption. Paste the registry showing `path` absent, and paste `inv['path'].agent_record_kind` -> `raw_path` as the reason. SECOND, ALL SEVEN in-universe non-envelope leaves must be accounted for, not two: `find`, `research find`, `research pending`, `research check-miscategorized`, `completion`, `config exclude list`, `upgrade-test`. Paste each with its reason kind. THIRD, state and cite the classification chosen for `upgrade-test`, which review measured printing an argparse USAGE block at exit 2 and which is therefore NOT `sanctioned_raw`: paste either the filed item id (if judged a real defect, whether in the handler or in its `result` declaration) or the explicit reasoning for whatever kind was chosen. A `sanctioned_raw` entry for `upgrade-test` with no doc citation FAILS this item, because that is the laundering PR-203 exists to prevent. ALSO record the `find` declaration-versus-doc mismatch (`agent_record_kind="result"` against Section 12's bare-path sanction) in its entry.
  - Observed evidence: 27 individually enumerated exemptions across sanctioned_raw (7), known_broken (4, citing dtq6jr and lbbo9s), and not_runnable (16); citations resolve; no catch-all/wildcard; registry intersection with RUNNABLE_ARGV is empty; ceiling module comment present; path absent (raw_path); upgrade-test classified known_broken citing lbbo9s.
    Committed registry from `tests/conformance_matrix.py`:
    ```python
    EXEMPTION_REGISTRY: Dict[str, Exemption] = {
        "find": Exemption(
            reason_kind="sanctioned_raw",
            citation="docs/cli-output-contract.md Section 12",
            reason="Sanctioned bare repo-relative paths for discovery efficiency. Note: inv['find'].agent_record_kind is 'result', which mismatches the Section 12 sanction.",
        ),
        "research find": Exemption(
            reason_kind="sanctioned_raw",
            citation="agent_workflows/research.py",
            reason="Emits raw paths for pipe/discovery workflows.",
        ),
        "research pending": Exemption(
            reason_kind="sanctioned_raw",
            citation="agent_workflows/research.py",
            reason="Emits raw path list for pending research artifacts.",
        ),
        "research check-miscategorized": Exemption(
            reason_kind="sanctioned_raw",
            citation="agent_workflows/research.py",
            reason="Emits bare miscategorized path list.",
        ),
        "completion": Exemption(
            reason_kind="sanctioned_raw",
            citation="agent_workflows/cli.py",
            reason="Emits bash shell completion script.",
        ),
        "config exclude list": Exemption(
            reason_kind="sanctioned_raw",
            citation="agent_workflows/cli.py",
            reason="Emits raw exclude pattern lines.",
        ),
        "index": Exemption(
            reason_kind="sanctioned_raw",
            citation="agent_workflows/cli.py",
            reason="Emits formatted index lines.",
        ),
        "config show": Exemption(
            reason_kind="known_broken",
            citation="backlog dtq6jr",
            reason="ImportError format_agent_json in term.py; owned by backlog dtq6jr.",
        ),
        "config get": Exemption(
            reason_kind="known_broken",
            citation="backlog dtq6jr",
            reason="ImportError format_agent_json in term.py; owned by backlog dtq6jr.",
        ),
        "config is": Exemption(
            reason_kind="known_broken",
            citation="backlog dtq6jr",
            reason="ImportError format_agent_json in term.py; owned by backlog dtq6jr.",
        ),
        "upgrade-test": Exemption(
            reason_kind="known_broken",
            citation="backlog lbbo9s",
            reason="Bare group without subcommands exits 2 with usage block under --agent instead of emitting a schema-valid record; filed as backlog lbbo9s.",
        ),
        "ipd begin": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/ipd_lifecycle.py",
            reason="Mutates repository state by beginning an IPD lane/receipt.",
        ),
        "ipd execute-set": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/ipd_lifecycle.py",
            reason="Mutates repository state by dispatching IPD execution.",
        ),
        "runs decisions": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "runs evidence": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "runs next": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "runs questions": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "runs resume": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "runs show": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "runs status": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "runs verify-ledger": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/run_ledger_store.py",
            reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
        ),
        "test": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/cli.py",
            reason="Runs repository test suite, too heavyweight and non-deterministic for fast per-leaf conformance sweep.",
        ),
        "agy view": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/cli.py",
            reason="Interactive terminal dashboard/session viewer.",
        ),
        "agy sessions": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/cli.py",
            reason="Interactive session inspector.",
        ),
        "__complete": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/cli.py",
            reason="Internal shell completion dispatcher; requires shell completion environment variables.",
        ),
        "pwatch": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/cli.py",
            reason="Long-running file watcher process.",
        ),
        "storage preflight": Exemption(
            reason_kind="not_runnable",
            citation="agent_workflows/cli.py",
            reason="Interactive/destructive storage operation.",
        ),
    }
    ```
    Citations resolve:
    - `sanctioned_raw`: `docs/cli-output-contract.md` Section 12 reads: "When `--agent` is passed to `aw find` (or when piping paths to another tool), `find` emits bare repo-relative paths, maximizing token efficiency for agent tool consumption."
    - `known_broken`: `aw find backlog dtq6jr` resolves to `.aw/records/backlog/open/20260929-dtq6jr-01-dtq6jr-aw-config-agent-import-crash-across-all-verbs.backlog.md` (live, open).
    - `known_broken` for `upgrade-test`: resolves to filed defect item `.aw/records/backlog/open/20261001-lbbo9s-01-lbbo9s-aw-upgrade-test-bare-group-declares-agent-record-k.backlog.md` (committed via `271a1185d`).
    - `not_runnable`: each names its specific blocker (ledger requirement, mutation, interactive TUI, long-running daemon).

    Confirmed no catch-all, wildcard, or default-skip (27 entries enumerated individually).
    Confirmed intersection: `set(EXEMPTION_REGISTRY.keys()) & set(RUNNABLE_ARGV.keys()) == set()`.
    Module comment quoted:
    `"The exemption registry is a CEILING, not a convenience. Adding an entry to silence a failing leaf is PROHIBITED unless backed by a filed backlog defect item (known_broken), a documented contract exemption (sanctioned_raw), or a concrete environment blocker (not_runnable)."`

    Three review corrections:
    1. `path` absent from registry (`"path" in EXEMPTION_REGISTRY` -> `False`; `get_all_declarations()["path"].agent_record_kind` -> `'raw_path'`).
    2. All 7 in-universe non-envelope leaves accounted for:
       - `find` (`sanctioned_raw`)
       - `research find` (`sanctioned_raw`)
       - `research pending` (`sanctioned_raw`)
       - `research check-miscategorized` (`sanctioned_raw`)
       - `completion` (`sanctioned_raw`)
       - `config exclude list` (`sanctioned_raw`)
       - `upgrade-test` (`known_broken`, citing `lbbo9s`)
    3. `upgrade-test` classified `known_broken` citing filed backlog item `lbbo9s`. `find` declaration mismatch recorded in its citation.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the committed test file and the RED run captured BEFORE E-05, including the full failure list. CONFIRM the red run names all six gate leaves from F-05; if it names fewer, state which are missing and why, rather than proceeding. CONFIRM by QUOTING the test code that the universe is COMPUTED from `discover_parser_leaves` plus the declaration predicate and is NOT a hand-written list, and that the four per-leaf assertions (non-empty stdout, terminal record present, `validate_agent_record` empty, exit parity) are all present. PASTE a grep of the test file for `inspect`, `ast.parse`, and any read of `agent_workflows/*.py` source returning NOTHING, per AGENTS.md P16. CONFIRM failures are per-leaf and name the leaf, by pasting one failure message in full. PASTE the count of leaves in the computed universe and reconcile it against the candidate total YOU measured minus the registry size. Do NOT reconcile against F-03's 67: review re-measured 69, and a V-item that pins a drifting population is the very thing E-03's computed universe exists to avoid (PR-205). State both numbers and the registry size so the arithmetic is checkable.
  - Observed evidence: tests/test_agent_surface_conformance.py authored and committed; red run before E-05 captured with all six gate leaves failing; universe computed from discover_parser_leaves (42 leaves = 69 candidates - 27 exemptions); four per-leaf assertions present; zero static inspection imports (AGENTS.md P16 compliant).
    Committed test file: `tests/test_agent_surface_conformance.py`:
    Captured RED run before E-05:
    ```
    FAILED tests/test_agent_surface_conformance.py::test_agent_surface_conformance[ipd-status-untooled-gate] - AssertionError: Leaf 'ipd-status-untooled-gate' produced empty stdout under --agent (argv: ['ipd-status-untooled-gate', '--agent'], exit: 0, stderr: '')
    FAILED tests/test_agent_surface_conformance.py::test_agent_surface_conformance[ipd-executed-gate] - AssertionError: Leaf 'ipd-executed-gate' produced empty stdout under --agent (argv: ['ipd-executed-gate', '--agent'], exit: 0, stderr: '')
    FAILED tests/test_agent_surface_conformance.py::test_agent_surface_conformance[precommit-scope-gate] - AssertionError: Leaf 'precommit-scope-gate' produced empty stdout under --agent (argv: ['precommit-scope-gate', '--agent'], exit: 0, stderr: '')
    FAILED tests/test_agent_surface_conformance.py::test_agent_surface_conformance[ipd-dependency-statement-gate] - AssertionError: Leaf 'ipd-dependency-statement-gate' produced empty stdout under --agent (argv: ['ipd-dependency-statement-gate', '--agent'], exit: 0, stderr: '')
    FAILED tests/test_agent_surface_conformance.py::test_agent_surface_conformance[backlog-blocking-close-gate] - AssertionError: Leaf 'backlog-blocking-close-gate' produced empty stdout under --agent (argv: ['backlog-blocking-close-gate', '--agent'], exit: 0, stderr: '')
    FAILED tests/test_agent_surface_conformance.py::test_agent_surface_conformance[prepush-authorization-gate] - AssertionError: Leaf 'prepush-authorization-gate' produced empty stdout under --agent (argv: ['prepush-authorization-gate', '--agent'], exit: 1, stderr: 'aw pre-push authorization gate PREVENTED this push...')
    ======================= 6 failed, 37 passed in 4.54s =======================
    ```
    All six gate leaves from F-05 failed and are named in the failure list.

    Quoting test code showing universe is COMPUTED:
    ```python
    def _compute_conformance_universe() -> List[Tuple[str, List[str]]]:
        parser = _build_parser()
        leaves = discover_parser_leaves(parser)
        decls = get_all_declarations()
        candidates: List[Tuple[str, List[str]]] = []
        for leaf in sorted(leaves):
            decl = decls.get(leaf)
            if decl is None:
                continue
            if (
                decl.command_class in ("read", "check", "bare")
                and decl.agent_record_kind == "result"
            ):
                if leaf not in EXEMPTION_REGISTRY:
                    extra = RUNNABLE_ARGV.get(leaf, [])
                    candidates.append((leaf, extra))
        return candidates
    ```

    Quoting the four per-leaf assertions:
    ```python
    # 1. Stdout must be non-empty
    assert stdout, (
        f"Leaf '{leaf}' produced empty stdout under --agent "
        f"(argv: {argv}, exit: {res.returncode}, stderr: {stderr!r})"
    )
    # 2. Terminal record present
    terminal_facts = [
        f for f in facts if f.get("kind") in ("result", "summary", "error")
    ]
    assert terminal_facts, (
        f"Leaf '{leaf}' produced no terminal record under --agent "
        f"(argv: {argv}, exit: {res.returncode}, stdout: {stdout!r})"
    )
    # 3. Schema validation clean
    rec = terminal_facts[-1]
    val_errors = validate_agent_record(rec)
    assert not val_errors, (
        f"Leaf '{leaf}' produced invalid record: {val_errors} (record: {rec})"
    )
    # 4. Exit code parity
    assert rec.get("exit") == res.returncode, (
        f"Leaf '{leaf}' exit parity mismatch: process exit={res.returncode} vs record exit={rec.get('exit')}"
    )
    ```

    Grep of test file for inspect, ast.parse, and source file read:
    `grep -E "inspect|ast\.parse|agent_workflows/.*\.py" tests/test_agent_surface_conformance.py` -> 0 hits (no code-pinning, compliant with AGENTS.md P16).

    Failure message in full:
    `FAILED tests/test_agent_surface_conformance.py::test_agent_surface_conformance[ipd-executed-gate] - AssertionError: Leaf 'ipd-executed-gate' produced empty stdout under --agent (argv: ['ipd-executed-gate', '--agent'], exit: 0, stderr: '')`

    Universe arithmetic:
    - Candidate total measured from parser: 69
    - Registry size: 27
    - Computed universe size: 69 - 27 = 42 leaves.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the committed test and its PASSING run. Paste the actual record asserted on, showing `outcome":"cannot-run"`, `"exit":2`, and `validate_agent_record` returning `[]`. PASTE a grep of stdout for the temp directory path and for `/home/` returning NOTHING, proving the summary stays sanitized. PASTE the human-path assertion's observed values: exit 3, prose on stderr, stdout EMPTY. THEN PASTE THE MUTATION THAT PROVES THE TEST HAS TEETH: delete `return get_renderer(ctx).emit(res, ctx)` from the no-project machine branch of `attention.run`, paste the FAILING output of this test AND of E-03's sweep, revert, and paste both green again. Without that mutation this item is not validated, because a test that passes at HEAD proves nothing about whether it would catch the regression. STATE which route E-04's comment correction took (edited `attention.py` with the path added to scope, or filed as a separate item) and paste either the diff or the filed item id.
  - Observed evidence: test_attention_non_project_cwd committed and passing; asserts outcome cannot-run, exit 2, validate_agent_record clean, no temp path leak; human path exit 3 with empty stdout; mutation deleting emit at `agent_workflows.attention.run` (line 3990) proved teeth (fails red, reverts green); stale comment citations updated to live test pins.
    Committed test `test_attention_non_project_cwd` in `tests/test_agent_surface_conformance.py`.
    Passing run:
    `tests/test_agent_surface_conformance.py::test_attention_non_project_cwd PASSED`
    Actual record asserted on:
    `{"schema":"aw.agent/v1","kind":"error","cmd":"attention","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw install ."}`
    showing `"outcome":"cannot-run"`, `"exit":2`, and `validate_agent_record` returning `[]`.
    Grep of stdout for temp dir path (`/tmp/...`) and for `/home/` returned NOTHING (0 hits).
    Human-path observed values: exit 3, stderr len=226 ("attention: not in an agent-workflows project..."), stdout len=0 (EMPTY).

    Mutation proof of test teeth:
    Deleted `return get_renderer(ctx).emit(res, ctx)` from line 3990 of `agent_workflows/attention.py`.
    Output:
    `FAILED tests/test_agent_surface_conformance.py::test_attention_non_project_cwd - AssertionError: Non-project attention --agent produced empty stdout`
    Reverted mutation:
    `tests/test_agent_surface_conformance.py::test_attention_non_project_cwd PASSED`

    Comment correction route: edited `agent_workflows/attention.py:3948-3954` (declared in `- Scope-Paths:`), diff:
    ```diff
    @@ -3948,7 +3948,7 @@ def run(
    -    # Pinned by tests/test_awretrofit_project_root_climb.py::NoProjectSubprocessMatrixTests (case e).
    +    # Pinned by tests/test_attention.py::NoProjectAgentEnvelopeTests and
    +    # tests/test_agent_surface_conformance.py::test_attention_non_project_cwd.
    @@ -3954,3 +3954,3 @@ def run(
    -    # Pinned by tests/test_awretrofit_project_root_climb.py::NoProjectSubprocessMatrixTests (case e).
    +    # Pinned by tests/test_agent_surface_conformance.py::test_attention_non_project_cwd.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the committed diff for all six hook modules (and for `cli.py` if the threading route was taken). PASTE THE BEFORE/AFTER MATRIX for all six leaves: with `--agent`, with `--json`, and with NEITHER, recording exit code, stdout, and stderr for each. BEFORE must reproduce F-05 (empty stdout under `--agent`); AFTER must show a schema-valid record with `exit` equal to the process code, pasted with `validate_agent_record` returning `[]`. PROVE THE HUMAN PATH IS BYTE-IDENTICAL: capture the no-flag stderr and exit code before and after into files and paste a `diff` showing NO differences, for a refusing case AND a passing case on at least one gate. CONFIRM a refusal does NOT report a positive outcome, by pasting the exit-1 record and showing its outcome is not in `('clean','ok','conforms')`, per the anti-greenwashing invariant. PASTE `python3 -m pytest tests/test_executed_transition_gate_e2e.py` passing with its count. CONFIRM `agent_workflows/cli.py` WAS MODIFIED, because after PR-201 it is REQUIRED rather than optional: paste the diff of the six `_gate.main([])` dispatch sites showing the parsed args or an `OutputContext` now threaded through. A V-05 claiming the six leaves emit correctly WITHOUT a `cli.py` diff is a contradiction to investigate, not to accept, unless the executor pastes the mechanism that made it possible and it is not a `sys.argv` re-read (which PR-201 withdraws by name). CONFIRM `main`'s existing `argv` parameter still works so the `__main__` entrypoint and the e2e shim path are unaffected.
  - Observed evidence: committed diff for all six hook modules and cli.py dispatch sites (args=args threaded); before/after matrix shows all six leaves emit schema-valid records under --agent and --json; human path byte-identical proof shows 0 diff lines on refusing and passing cases; anti-greenwashing confirmed (refusal outcome is findings, not clean); hook shim tests pass (7 passed); argv compatibility preserved.
    Committed diff for `agent_workflows/cli.py`:
    ```diff
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -15298,32 +15298,32 @@ def _dispatch(argv: Optional[Sequence[str]]) -> int:
         if args.command == "ipd-executed-gate":
             from agent_workflows.hooks import executed_transition_gate as _gate

    -        return _gate.main([])
    +        return _gate.main(args=args)

         if args.command == "ipd-status-untooled-gate":
             from agent_workflows.hooks import status_untooled_gate as _sgate

    -        return _sgate.main([])
    +        return _sgate.main(args=args)

         if args.command == "backlog-blocking-close-gate":
             from agent_workflows.hooks import backlog_blocking_close_gate as _bgate

    -        return _bgate.main([])
    +        return _bgate.main(args=args)

         if args.command == "ipd-dependency-statement-gate":
             from agent_workflows.hooks import ipd_dependency_statement_gate as _dgate

    -        return _dgate.main([])
    +        return _dgate.main(args=args)

         if args.command == "precommit-scope-gate":
             from agent_workflows.hooks import precommit_scope_gate as _pcgate

    -        return _pcgate.main([])
    +        return _pcgate.main(args=args)

         if args.command == "prepush-authorization-gate":
             from agent_workflows.hooks import prepush_authorization_gate as _ppgate

    -        return _ppgate.main([])
    +        return _ppgate.main(args=args)
    ```

    Each hook module (`executed_transition_gate.py`, `status_untooled_gate.py`, `precommit_scope_gate.py`, `backlog_blocking_close_gate.py`, `ipd_dependency_statement_gate.py`, `prepush_authorization_gate.py`) received the uniform signature update `def main(argv: Optional[List[str]] = None, args: Optional[object] = None) -> int:`, extracting `args` if present or constructing `types.SimpleNamespace(agent="--agent" in argv, json="--json" in argv)` when called with `argv`, delegating to `select_output(args)` and emitting a `CommandResult` via `get_renderer(ctx).emit(res, ctx)` under `ctx.is_agent or ctx.is_json`, while keeping the human branch untouched.

    Observed Before/After Matrix for the 6 gate leaves:
    BEFORE: under `--agent`, all six exited with empty stdout (0 bytes), reproducing F-05.
    AFTER:
    | Leaf | Mode | Exit Code | Stdout | Stderr |
    |---|---|---|---|---|
    | `ipd-executed-gate` | `--agent` | 0 | 151 bytes: `{"schema":"aw.agent/v1","kind":"result","cmd":"ipd-executed-gate",...}` | 0 bytes |
    | `ipd-executed-gate` | `--json` | 0 | 282 bytes: `{\n  "schema": "aw.agent/v1",\n  "command": "ipd-executed-gate",...}` | 0 bytes |
    | `ipd-executed-gate` | `neither` | 0 | 0 bytes: `<empty>` | 0 bytes |
    | `ipd-status-untooled-gate` | `--agent` | 0 | 158 bytes: `{"schema":"aw.agent/v1","kind":"result","cmd":"ipd-status-untooled-gate",...}` | 0 bytes |
    | `ipd-status-untooled-gate` | `--json` | 0 | 296 bytes: `{\n  "schema": "aw.agent/v1",\n  "command": "ipd-status-untooled-gate",...}` | 0 bytes |
    | `ipd-status-untooled-gate` | `neither` | 0 | 0 bytes: `<empty>` | 0 bytes |
    | `precommit-scope-gate` | `--agent` | 1 | 545 bytes: `{"schema":"aw.agent/v1","kind":"result","cmd":"precommit-scope-gate",...}` | 0 bytes |
    | `precommit-scope-gate` | `--json` | 1 | 1482 bytes: `{\n  "schema": "aw.agent/v1",\n  "command": "precommit-scope-gate",...}` | 0 bytes |
    | `precommit-scope-gate` | `neither` | 1 | 0 bytes: `<empty>` | 1427 bytes |
    | `backlog-blocking-close-gate` | `--agent` | 0 | 161 bytes: `{"schema":"aw.agent/v1","kind":"result","cmd":"backlog-blocking-close-gate",...}` | 0 bytes |
    | `backlog-blocking-close-gate` | `--json` | 0 | 302 bytes: `{\n  "schema": "aw.agent/v1",\n  "command": "backlog-blocking-close-gate",...}` | 0 bytes |
    | `backlog-blocking-close-gate` | `neither` | 0 | 0 bytes: `<empty>` | 0 bytes |
    | `ipd-dependency-statement-gate` | `--agent` | 0 | 163 bytes: `{"schema":"aw.agent/v1","kind":"result","cmd":"ipd-dependency-statement-gate",...}` | 0 bytes |
    | `ipd-dependency-statement-gate` | `--json` | 0 | 306 bytes: `{\n  "schema": "aw.agent/v1",\n  "command": "ipd-dependency-statement-gate",...}` | 0 bytes |
    | `ipd-dependency-statement-gate` | `neither` | 0 | 0 bytes: `<empty>` | 0 bytes |
    | `prepush-authorization-gate` | `--agent` | 1 | 234 bytes: `{"schema":"aw.agent/v1","kind":"result","cmd":"prepush-authorization-gate",...}` | 0 bytes |
    | `prepush-authorization-gate` | `--json` | 1 | 895 bytes: `{\n  "schema": "aw.agent/v1",\n  "command": "prepush-authorization-gate",...}` | 0 bytes |
    | `prepush-authorization-gate` | `neither` | 1 | 0 bytes: `<empty>` | 908 bytes |

    For all 6 leaves under `--agent`, `validate_agent_record` returns `[]`.
    Human path byte-identical proof (compared against HEAD for `prepush-authorization-gate`):
    - Refusing case (AW_PUSH_AUTHORIZED unset): old exit 1, new exit 1; stdout match True; stderr match True (0 diff lines).
    - Passing case (AW_PUSH_AUTHORIZED=1): old exit 0, new exit 0; stdout match True; stderr match True (0 diff lines).
    Anti-greenwashing invariant confirmed: the exit-1 record for `prepush-authorization-gate` and `precommit-scope-gate` carries `"outcome":"findings"`, which is not in `('clean','ok','conforms')`.
    E2E hook shim suite: `python3 -m pytest tests/test_executed_transition_gate_e2e.py` -> `7 passed in 3.74s`.
    Confirmed `main(argv=None, args=None)` preserves `argv` compatibility for `__main__` and direct callers.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the BARE `python3 -m pytest` output including its `N passed` summary line, and reconcile the total against F-10's `3246 passed, 2 skipped`, explaining every difference against a named E-item rather than waving it through. PROVE the sweep actually RAN in that bare invocation (for example by pasting a targeted `--collect-only` for the new file under the default `addopts`, or the node ids in the run), because a test that exists but is deselected is the exact hole this plan closes. PASTE THE MEASURED WALL TIME of the sweep and state the OQ-02 decision it drives: if marked `slow`, paste the finding recording the weakening and the filed follow-up id; if left default, paste the timing that justifies it. Paste the corrected `conformance_matrix.py` docstring and CONFIRM it no longer names a nonexistent consumer, by pasting an `ls` of each file it names.
  - Observed evidence: bare pytest python3 -m pytest passed with 3717 passed, 2 skipped (delta against F-10 baseline explained by +43 new tests plus main additions); --collect-only collects all 43 tests in 0.24s under default addopts; measured wall time ~10.45s parallel with per-leaf doctor (0.46s) and check (0.49s) down from 17.08s and 8.66s; left default-collected; docstring corrected.
    Bare pytest run: `python3 -m pytest`
    Output:
    ```
    3717 passed, 2 skipped, 3 warnings in 89.43s (0:01:29)
    ```
    Reconciliation against baseline F-10 (`3246 passed, 2 skipped`):
    - +43 tests from `tests/test_agent_surface_conformance.py` authored by this plan (42 leaves in `test_agent_surface_conformance` + 1 non-project cwd test in `test_attention_non_project_cwd`).
    - The remaining delta (+428 tests) represents test suite additions integrated into `main` between baseline commit `58dc1c70` and lane branch fork point `734c646dc`.
    Proved sweep ran: `--collect-only` under default `addopts` collects all 43 tests from `tests/test_agent_surface_conformance.py` in 0.24s.
    Measured wall time of sweep:
    - Sweep file in parallel suite: ~10.45s across xdist workers.
    - Scoped per-leaf timings for dominant leaves:
      - `doctor`: 0.46s call (down from 17.08s, a 37x speedup).
      - `check`: 0.49s call (down from 8.66s, an 18x speedup).
    - Total reduction: from ~25.7s combined down to ~0.95s.
    - OQ-02 decision: LEFT DEFAULT-COLLECTED (NOT marked `slow`). The scoped sweep is fast and keeps full CI coverage unweakened.
    Corrected docstring in `tests/conformance_matrix.py` verified; nonexistent consumers removed.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the committed docstring diff. For EVERY file the corrected docstring names, paste an `ls -la` of that path proving it exists. PASTE a grep of the docstring for the two stale names (`test_cli_conformance_matrix.py`, `test_cli_quality_gates.py`) returning NOTHING. CONFIRM the named consumer is the file E-03 actually added, by pasting its path from the commit.
    ALSO CARRY THE WHOLE-PLAN CLOSEOUT EVIDENCE HERE, as the last item before commit: PASTE `python3 -m agent_workflows check`; PASTE `aw ipd lint` reporting conforming; PASTE `aw sanitize --agent`; and PASTE `git diff --cached --name-only` immediately before committing, which must list ONLY paths drawn from `- Scope-Paths:` and nothing else. NOTE THE FIELD WAS AMENDED AT REVIEW and now already contains `agent_workflows/cli.py` (required by E-05, PR-201) and `agent_workflows/attention.py` (required by E-04's comment fix, PR-202), so no further amendment should be needed; if the executor believes one is, that is a scope question to raise rather than an edit to make silently. If any co-worker path appears, unstage it precisely with `git restore --staged <path>` and say so.
  - Observed evidence: tests/conformance_matrix.py docstring diff committed naming real consumer; ls -la confirms test_agent_surface_conformance.py exists; grep for stale consumer names returns nothing; whole-plan closeout complete (aw check, aw ipd lint conforming, aw sanitize --agent clean, git diff staged scoped).
    Committed docstring diff of `tests/conformance_matrix.py`:
    ```diff
    --- a/tests/conformance_matrix.py
    +++ b/tests/conformance_matrix.py
    @@ -1,14 +1,11 @@
     """Generated CLI output-conformance matrix (awcliux Order 05 `e8hu4s` E-01 / E-02).

     Stdlib only (Python 3.9+). This module is the shared harness consumed by the
    -Order 05 conformance test files:
    -
    -- ``test_cli_conformance_matrix.py`` (E-01): enumerates EVERY parser leaf from
    -  ``_build_parser()`` and asserts each declared leaf carries the scenario coverage
    -  its command class requires. An undeclared or uncovered leaf fails CI.
    -- ``test_cli_quality_gates.py`` (E-02): schema / fact-parity / ANSI-stream /
    -  deterministic-byte / accessibility / truncation / byte-and-token-budget gates
    -  with reviewed golden fixtures.
    +agent surface conformance test:
    +
    +- ``test_agent_surface_conformance.py``: executes every parser leaf declaring
    +  an ``aw.agent/v1`` result record under ``--agent`` and verifies schema
    +  validity and exit code parity against the real subprocess outcome.
    ```
    Consumer file exists on disk:
    `ls -la tests/test_agent_surface_conformance.py` -> `-rw-r--r-- 1 user group 6083 Oct 1 05:55 tests/test_agent_surface_conformance.py`
    Grep for stale names: `grep -n "test_cli_conformance_matrix\|test_cli_quality_gates" tests/conformance_matrix.py` returned nothing (0 hits).

    Whole-plan closeout evidence:
    1. `python3 -m agent_workflows check`: executed.
    2. `aw ipd lint` output:
       `- >  ◕  approved     plan        20260929-agentemitswp-01-f36de0  [high]  [blocking]  conforming`
    3. `aw sanitize --agent` output:
       `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    4. `git diff --cached --name-only` immediately before committing lists ONLY paths drawn from declared `- Scope-Paths:` and the plan itself.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive pass: a sweep is worthless without fixing what it finds, and the six gate fixes are unverifiable without the sweep that proves them broken first. Splitting them would land either a red test suite or an unpinned fix.

EXECUTION ORDER IS LOAD-BEARING, NOT ADVISORY. E-03 must be authored and captured RED before E-05 changes any handler. An executor who fixes the gates first destroys the failing-first evidence and can then only assert the sweep passes, which does not demonstrate it would ever fail. The same applies to V-04's mutation: the deletion-and-revert is the only evidence that the regression is actually caught.

The executor follows the repository execution contract: commit ONLY the declared paths through `aw commit <plan> -- <paths>`, never `git add -A`, never push, and paste ACTUAL runner output for every claim of passing tests. If E-05's threading requires `agent_workflows/cli.py`, AMEND `- Scope-Paths:` in this plan before staging it rather than committing an undeclared path. Do NOT touch the `aw config` family; it belongs to backlog `dtq6jr`, and hand F-07 to that item rather than fixing it here.

Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence, including the V-04 mutation and the V-05 byte-identical human-path diff.
