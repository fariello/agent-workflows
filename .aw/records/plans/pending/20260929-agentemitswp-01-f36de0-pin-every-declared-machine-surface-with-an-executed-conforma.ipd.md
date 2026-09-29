# IPD: Pin every declared machine surface with an executed conformance sweep so a dropped emit cannot pass CI

- Date: 2026-09-29
- Kind: child
- Concern: THE TOOLKIT DECLARES 160 LEAVES AS EMITTING AN `aw.agent/v1` RESULT AND EXECUTES ALMOST NONE OF THAT CLAIM, so a machine surface can be deleted, or can crash, without a single test going red. This is the CLASS that backlog `kjr5ol` was filed to carry: commit `4cfa2283` deleted `return get_renderer(ctx).emit(res, ctx)` from the no-project branch of `attention.run`, the branch kept BUILDING a `CommandResult` and discarding it, and nothing failed. Measured in this lane at HEAD `58dc1c70`, driving all 67 `read`/`check`/`bare` leaves that declare `agent_record_kind="result"` with `--agent` by subprocess: only 28 emitted a schema-valid terminal record with exit parity, and 13 did not emit one at all. SIX of those 13 are the pre-commit/pre-push gate leaves (`ipd-executed-gate`, `ipd-status-untooled-gate`, `precommit-scope-gate`, `backlog-blocking-close-gate`, `ipd-dependency-statement-gate`, `prepush-authorization-gate`), whose `hooks/*.main` write prose to stderr and return a bare int, never constructing a `CommandResult` at all, so `--agent` is accepted and silently ignored - the exact same invisible-silence failure mode as the original defect, on six leaves, today. The remaining 7 split into one already-owned crash and six legitimately-exempt surfaces (see Findings). The declaration field that would have caught all of this, `CommandDeclaration.agent_record_kind`, is READ BY NO CODE ANYWHERE: `rg agent_record_kind` outside `command_surface.py` returns nothing, so it is documentation that no gate consumes. And `tests/conformance_matrix.py`, a 378-line harness built to close exactly this gap, has ZERO importers: the two test files its own docstring names as its consumers do not exist, and its `build_matrix` marks every non-curated leaf `covered_by="declaration"`, meaning "asserted, never run".
- Scope: Make the declared machine surface an EXECUTED contract instead of a documented intention, and fix the six gate leaves the sweep proves are broken. IN: a behavioral conformance test that drives every leaf declaring `agent_record_kind="result"` with `--agent` in a subprocess and asserts a schema-valid terminal record with exit parity, wired to the orphaned `tests/conformance_matrix.py` rather than rebuilt; an explicit, per-entry JUSTIFIED exemption registry so a leaf is either executed or documented as to why it cannot be, with no silent third category; routing the six hook-gate leaves through `get_renderer(...).emit(...)` so they honor the `--agent`/`--json` flags their declarations promise; and a NON-PROJECT cwd axis, because the original bug only manifested outside an AW project and a sweep run only in the repo tree cannot see it. OUT (each with a reason, none of them incidental): the `aw config` family's eight `format_agent_json` ImportError crash sites, which are ALREADY OWNED by open backlog item `dtq6jr` at `- Priority: high` with its own `Blocks-Release: next` gate and its own required test matrix, so fixing them here would duplicate a filed item and steal its validation; `aw find`/`aw path`'s bare-path output, which `docs/cli-output-contract.md` Section 12 and `agent_record_kind="raw_path"` SANCTION as deliberate token efficiency, so asserting an envelope there would break a documented contract rather than fix a defect; widening `agent_schema` to admit exit 3; any change to `emit`'s signature or to `BaseRenderer`; converting `mutation`-class leaves (79 of them) to the sweep, which needs a write-isolation design this plan does not attempt; and any static analysis of production source (`inspect`/`ast`/regex over `.py` files), which AGENTS.md P16 forbids outright.
- Scope-Paths: tests/conformance_matrix.py, tests/test_agent_surface_conformance.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/status_untooled_gate.py, agent_workflows/hooks/precommit_scope_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/hooks/prepush_authorization_gate.py
- Item-Dependencies: none
- Status: to-review
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

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog item `kjr5ol`, which carries `- Blocks-Release: next`; this plan INHERITS that gate as required. Authoring MEASURED the item's residual ask rather than transcribing it, and the measurement contradicts the item in one direction and vindicates it in another. Recorded here because an executor who trusts the item's prose will both look for a test that does not exist and conclude the sweep is unnecessary.
  THE ITEM'S CITED PINS ARE MISNAMED OR DELETED, so do not go looking for them. It says the fix was pinned in `tests/test_attention.py::AttentionNoProjectMachinePathTests` and `tests/test_awretrofit_project_root_climb.py` case (e). The FIRST NAME DOES NOT EXIST and never did (`git log -S` finds no commit adding that string); the live pin is `tests/test_attention.py::NoProjectAgentEnvelopeTests`, which does exist and PASSES (measured: `1 passed`). The SECOND FILE WAS DELETED WHOLESALE by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), so `attention.py`'s own comment citing it as live protection is now stale. See F-01 and F-02. The attention branch itself is therefore NOT the outstanding work: `emit` is present at both no-project sites and covered. The outstanding work is the CLASS, which is what this plan takes.
  THE ITEM'S CORE CLAIM IS TOO OPTIMISTIC, AND THAT IS THE FINDING THAT JUSTIFIES THE SCOPE. It records that "a crude grep at execution time found no second instance" and asks only for a conformance test to make that a contract. Driving the surface instead of grepping it found SIX LIVE INSTANCES of the same silent-ignore class (the hook-gate leaves, F-05), which no grep for a discarded `CommandResult` could ever have found because those handlers never construct one - they bypass the renderer entirely while their declarations advertise `--agent` and `agent_record_kind="result"`. So the item's "grep is not a contract" instinct was right for a reason stronger than it knew, and E-05 fixes the six rather than merely reporting them.
  ONE FOUND DEFECT IS DELIBERATELY NOT TAKEN, and a reviewer should read the omission as intentional. The sweep also caught all eight `aw config --agent` branches crashing with `ImportError: cannot import name 'format_agent_json'` (a symbol never defined in `term.py`, in any commit, on any branch). That is ALREADY FILED as open backlog `dtq6jr` (high, `Blocks-Release: next`) with an enumerated seven-verb evidence table and an explicit "any fix MUST come with tests driving ALL SEVEN verbs" requirement. Folding it in here would duplicate a live item and absorb its gate; instead E-02's exemption registry records it as a KNOWN-BROKEN leaf citing `dtq6jr`, so the sweep neither goes red on someone else's bug nor pretends the leaf conforms. See F-06 and OQ-01.

## Goal

Make every leaf that DECLARES an `aw.agent/v1` result actually produce one, verified by executing it rather than by declaring it, so deleting an `emit` call or shipping a machine branch that never reaches the renderer turns a test red instead of passing silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the sweep exist and fail on today's real defects

- [ ] E-01 GIVE `tests/conformance_matrix.py` A RUNNABLE-ARGV TABLE AND A NON-PROJECT CWD OPTION, so the sweep can drive leaves the current harness cannot reach. Two additions, both to the existing module, because it already holds `run_cli`, `_pinned_env`, and `semantic_facts_from_agent` and re-implementing those would fork the harness.
  ADD THE ARGV TABLE. Today `LIVE_SAFE_LEAVES` covers 16 entries and only 13 of the 67 candidate leaves, so 54 are unreachable; the dominant reason is that a leaf needs REQUIRED POSITIONAL ARGUMENTS and argparse exits 2 with a usage error before the handler runs. Measured: 26 of the 67 fail exactly this way (F-03). Add a table mapping a leaf to argv that makes it RUNNABLE AND READ-ONLY (for example `config get aw_home`, `runs show <a run id>`, `path records`), keeping the existing safety precondition: no writes, no network. A leaf that cannot be made runnable read-only belongs in E-02's exemption registry, NOT in this table.
  ADD THE CWD PARAMETER. `run_cli` hardcodes `cwd=str(REPO_ROOT)`. Thread an optional `cwd` through so a scenario can run from a directory that is NOT an AW project, because that is the precise condition under which the `kjr5ol` defect manifested and a sweep confined to the repo tree is blind to it (the repo-tree run of `attention --agent` exits 1 with findings and never reaches the no-project branch at all; measured).
  DO NOT CHANGE `required_scenarios` OR `build_matrix` SEMANTICS in this item. They encode the Order-04/05 declaration contract and the coverage-row vocabulary; E-03 consumes them as they stand.
  - Depends on: none
  - Expected outcome: `conformance_matrix` exposes a runnable-argv mapping and `run_cli(..., cwd=<dir>)` works, with the existing `REPO_ROOT` default unchanged for every current caller.
  - Execution state: pending

- [ ] E-02 WRITE THE EXEMPTION REGISTRY AS DATA WITH A MANDATORY REASON, before any assertion consumes it, so the sweep has exactly two categories and no silent third. Each entry maps a leaf to a typed reason and a citation. The three reason kinds the measurement actually produced, and no others invented speculatively:
  `sanctioned_raw` for a leaf whose non-envelope output is a DOCUMENTED contract, not a defect. Exactly the two the docs sanction: `find` (Section 12 of `docs/cli-output-contract.md`: "When `--agent` is passed to `aw find` ... `find` emits bare repo-relative paths, maximizing token efficiency") and `path` (declared `agent_record_kind="raw_path"`). The citation must be that doc section or that declaration field, so a future reader can check the claim rather than trust it.
  `known_broken` for a leaf whose failure is REAL and owned elsewhere. Exactly the `config` family, citing backlog `dtq6jr`. THE ENTRY MUST CARRY THE ITEM ID, because that is what makes the exemption temporary rather than permanent: when `dtq6jr` lands, its executor deletes the entry and the sweep starts enforcing the leaf.
  `not_runnable` for a leaf that cannot be driven read-only (an interactive prompt, a destructive precondition), with the reason naming WHAT blocks it.
  THE REGISTRY IS A CEILING, NOT A CONVENIENCE. State in a module comment that adding an entry to silence a red sweep is the failure mode this plan exists to prevent, and that a `known_broken` entry REQUIRES a filed item id. Do not add a blanket wildcard or a "skip everything else" default; that would restore the `covered_by="declaration"` hole in a new shape.
  - Depends on: none
  - Expected outcome: a registry whose every entry carries a reason kind and a resolvable citation, with no unexplained entries and no catch-all.
  - Execution state: pending

- [ ] E-03 WRITE THE SWEEP TEST IN `tests/test_agent_surface_conformance.py` AND SHOW IT RED ON THE SIX GATE LEAVES BEFORE FIXING THEM. This is the failing-first evidence for E-05, so it must be authored and run BEFORE E-05 changes any handler.
  THE UNIVERSE IS COMPUTED, NOT LISTED: enumerate `command_surface.discover_parser_leaves(cli._build_parser())`, keep leaves whose declaration has `command_class` in `read`/`check`/`bare` AND `agent_record_kind == "result"`, then subtract E-02's registry. Computing it is what makes a NEWLY ADDED leaf enforced automatically; a hand-written list would freeze coverage at today's surface and is the reason the original bug survived.
  PER LEAF, ASSERT FOUR THINGS, each chosen because a real measured failure violates it: stdout is NON-EMPTY (this is the assertion the `kjr5ol` defect would have tripped, and the six gate leaves trip today); a terminal `result`/`summary`/`error` record parses out of the JSONL (via the harness's `semantic_facts_from_agent`); `agent_schema.validate_agent_record` returns `[]` on it; and the record's `exit` EQUALS the process exit code, which is the contract's own Exit Code Parity rule.
  FAIL WITH THE LEAF NAME AND THE STREAMS. A sweep that reports "3 leaves failed" costs the next maintainer a re-derivation. Assert per leaf (subtest or parametrization) and put the leaf, the argv, the exit code, and a stdout/stderr excerpt in the failure message.
  NO STATIC ANALYSIS, per AGENTS.md P16 and the backlog item's own reasoning. Drive the CLI as a subprocess and assert on real stdout, real stderr, and real exit codes. Do not read `agent_workflows/*.py`, do not count `emit` callers, do not regex for a discarded `CommandResult`: a grep is precisely what failed to find the six gate leaves.
  - Depends on: E-01, E-02
  - Expected outcome: the sweep runs over the computed universe and FAILS, naming at minimum the six hook-gate leaves; that failing output is captured as E-05's baseline.
  - Execution state: pending

- [ ] E-04 ADD THE NON-PROJECT-CWD CASE THAT PINS THE ORIGINAL DEFECT'S EXACT CONDITION, as a separate test from the broad sweep because it asserts a specific record rather than a general shape. Using E-01's `cwd`, run `attention --agent` from a bare `git init` directory that is NOT an AW project and assert: stdout non-empty, one `aw.agent/v1` record, `outcome == "cannot-run"`, `exit == 2` matching the process code, `validate_agent_record` clean, and the temp path ABSENT from stdout (the branch sanitizes its summary deliberately; emitting the checked directory would leak an absolute path and `agent_schema` refuses one).
  ALSO ASSERT THE HUMAN PATH IS UNCHANGED at exit 3 with prose on stderr and EMPTY stdout, because the 3-versus-2 split is intentional and documented at the site, and a test that quietly normalized the human code would break an operator contract while looking like a cleanup.
  CORRECT THE STALE COMMENT while here: `attention.run`'s no-project branch cites `tests/test_awretrofit_project_root_climb.py::NoProjectSubprocessMatrixTests` as live protection, and that FILE NO LONGER EXISTS (deleted by `19313eed`). Re-point it at the live `NoProjectAgentEnvelopeTests` and at this new case. This is a comment-only edit to a file NOT in `- Scope-Paths:`; if the executor prefers to keep the scope closed, record the stale citation as a finding and file it instead of editing outside declared scope. Do not silently widen the commit.
  - Depends on: E-01
  - Expected outcome: a test that fails if the no-project `emit` is deleted again, and passes at HEAD; the stale citation either corrected or filed.
  - Execution state: pending

### Task group 2: fix what the sweep proves is broken

- [ ] E-05 MAKE THE SIX HOOK-GATE LEAVES HONOR `--agent`/`--json` BY ROUTING THEM THROUGH THE RENDERER, turning E-03 green for them. Each `hooks/*.main` currently does `exit_code, messages = check()`, writes prose to `sys.stderr`, and returns the bare int; none constructs a `CommandResult`, so `--agent` is accepted and ignored. The six: `executed_transition_gate`, `status_untooled_gate`, `precommit_scope_gate`, `backlog_blocking_close_gate`, `ipd_dependency_statement_gate`, `prepush_authorization_gate`.
  BUILD A `CommandResult` AND `emit` IT on the machine surfaces, mapping each gate's `messages` to `Diagnostic` entries so a consumer reads structured refusals instead of parsing prose. Follow the sibling pattern already shipped in `attention.run`'s no-project branch: guard on `ctx.is_agent or ctx.is_json`, emit, and leave the human path untouched.
  THE HUMAN PATH MUST NOT CHANGE, AND THIS IS THE HARD CONSTRAINT OF THE ITEM. These are GIT HOOK ENTRYPOINTS invoked by `pre-commit`, and a human's commit refusal message is the only thing standing between them and a bypassed gate. Keep the stderr prose and the returned exit code BYTE-IDENTICAL when neither flag is passed. `tests/test_executed_transition_gate_e2e.py` drives `ipd-executed-gate` through a real hook shim, so it is the regression witness that the hook still refuses correctly.
  MIND THE EXIT CONTRACT. These declare `exit_contract=(0, 1)` or `(0, 1, 2)`; all are inside `agent_schema`'s admissible 0/1/2, so no exit-code change is needed and none should be made. A refusal is exit 1, whose valid outcome is `findings` or `fail` and NOT a positive outcome, because the anti-greenwashing invariant forbids reporting `clean` for refused work.
  ROUTE THE FLAGS THROUGH. `cli._dispatch` calls each gate as `_gate.main([])`, discarding argv, so a `--agent` reaching the parser never reaches the handler. Thread the output context (pass the parsed argv through, or construct the context in `_dispatch` and hand it over). Note this touches `agent_workflows/cli.py`, which is NOT in `- Scope-Paths:`: ADD IT to the plan's scope before committing, or implement the threading entirely inside the hook modules. Declare which route was taken; do not commit an undeclared path.
  - Depends on: E-03
  - Expected outcome: all six leaves emit a schema-valid record with exit parity under `--agent`, the human stderr output and exit codes are unchanged, and E-03's six failures clear.
  - Execution state: pending

- [ ] E-06 WIRE THE SWEEP INTO THE DEFAULT SUITE, so the contract runs unprompted rather than on request. Confirm the new test file is collected by a BARE `python3 -m pytest` and is NOT marked `slow` or `livecorpus`, since both are deselected by default (`pyproject.toml` `addopts`) and a gate that does not run in the default suite would not have caught the original bug.
  IF THE SWEEP IS TOO SLOW FOR THE DEFAULT SUITE, say so with the MEASURED number rather than guessing: it spawns one subprocess per leaf across roughly 50 leaves. If it must be marked `slow`, that is a REAL WEAKENING of the gate and must be recorded as a finding plus a filed follow-up, not waved through, because `slow` tests do not run in the default suite an agent uses before committing.
  - Depends on: E-05
  - Expected outcome: a bare `python3 -m pytest` collects and runs the sweep, with the measured wall time recorded and OQ-02 decided on that number.
  - Execution state: pending

- [ ] E-07 CORRECT `tests/conformance_matrix.py`'s DOCSTRING TO NAME ITS REAL CONSUMER. It currently names two files (`test_cli_conformance_matrix.py`, `test_cli_quality_gates.py`) as the tests that consume it, and NEITHER EXISTS, so the module reads as covered when it is orphaned. Point it at the file E-03 adds.
  THIS IS THE SAME DEFECT CLASS THE PLAN IS ABOUT, one level up: a written claim of coverage that nothing checks, exactly like the unconsumed `agent_record_kind` field and the deleted test `attention.py` still cites. Leaving it is how the next maintainer concludes the sweep already existed.
  - Depends on: E-03
  - Expected outcome: the docstring names only files that exist on disk.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `emit` IS BOTH THE WRITE AND THE EXIT CODE, which is the mechanical reason this defect class is silent. `renderers.BaseRenderer.emit` is defined once, overridden by no subclass, and returns `result.exit_code`; the canonical call is `return get_renderer(ctx).emit(res, ctx)`. Dropping the `return ... emit(...)` therefore costs nothing at runtime, raises nothing, and lets control fall through to a human-only branch. `emit` additionally writes NOTHING when `render` yields an empty string while still returning the exit code, so "exited correctly" never implies "emitted".
- VALIDATION IS TEST-TIME, NOT RUNTIME. `emit` never calls `agent_schema.validate_agent_record`; the path is `render` -> `CommandResult.to_agent_record` -> `render_jsonl_record`. So an invalid record is only caught if a test looks, which is why E-03 must call the validator explicitly rather than assume the renderer did.
- EXIT 3 IS UNEMITTABLE ON A MACHINE SURFACE. `agent_schema.validate_agent_record` admits `exit` only in `(0, 1, 2)`, so the human/machine 3-versus-2 asymmetry on the no-project path is deliberate and load-bearing, not an inconsistency to tidy. `attention.run`'s own comment records the measurement: adding the missing `emit` with exit 3 would raise in the renderer and reproduce the empty stdout.
- THE COMMAND SURFACE IS ENUMERABLE WITHOUT TOUCHING DISPATCH, which is what makes a computed universe feasible. `command_surface.discover_parser_leaves(parser)` walks argparse recursively and dedupes aliases by object identity; `find_undeclared_leaves(parser)` reports drift. Measured live: 151 parser leaves, 161 declared, 0 undeclared. There is NO `name -> callable` registry (`cli._dispatch` is a hand-written `if/elif` chain with 55 comparisons and no `set_defaults(func=...)`), so enumeration must go through the parser, not through handlers.
- `agent_record_kind` IS DECLARED AND CONSUMED BY NOTHING. `rg agent_record_kind` outside `command_surface.py` returns no hits, so the field asserting that 160 leaves emit a `result` record is inert documentation. E-03 is what converts it into an enforced claim.
- TESTS MUST ASSERT OUTCOMES, NOT CODE STRUCTURE (AGENTS.md P16). No `inspect`, no `ast`, no regex over production source, no caller-count assertions. This bars the tempting static check ("find every `CommandResult` with no nearby `emit`") and is independently justified here: a proximity grep produces false positives at a 45-line window (`aw find` builds at one line and emits 55 lines later) and is defeated entirely by a factory helper, while missing all six gate leaves, which never build a `CommandResult` to be found.
- `XDG_CONFIG_HOME` ISOLATES USER CONFIG for a subprocess test; verified in this lane that pointing it at a throwaway directory causes `config.json` to be written there and leaves the real config untouched.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The item's cited pin `AttentionNoProjectMachinePathTests` DOES NOT EXIST and never did; the live pin is `tests/test_attention.py::NoProjectAgentEnvelopeTests`, which passes. | `grep -c` returns 0 for the cited name; `git log -S` finds no commit adding it. `python3 -m pytest tests/test_attention.py::NoProjectAgentEnvelopeTests` -> `1 passed in 1.93s`. |
| F-02 | The item's second cited pin, `tests/test_awretrofit_project_root_climb.py`, was DELETED wholesale, and `attention.py` still cites it as live protection. | File absent from the tree; removed by commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests". Two stale citations remain in `attention.py`'s no-project comment block. |
| F-03 | Of 67 candidate leaves (`read`/`check`/`bare` with `agent_record_kind="result"`), only 28 emit a schema-valid terminal record with exit parity; 13 emit NO record; 26 are unreachable because argparse exits 2 on missing required positionals before the handler runs. | Subprocess sweep of all 67 with `--agent`, classifying stdout into crash / silent / invalid / conforming. |
| F-04 | `tests/conformance_matrix.py` (378 lines) has ZERO importers, and both consumer files named in its own docstring are absent. Its `build_matrix` marks every non-curated leaf `covered_by="declaration"`, i.e. asserted but never executed. | `rg conformance_matrix` finds only the module itself plus two prose comments in `command_surface.py`. `LIVE_SAFE_LEAVES` covers 13 of the 67 candidates; `attention` appears only as `--check`, the sub-branch that KEPT its emit. |
| F-05 | SIX hook-gate leaves accept `--agent` and silently ignore it, emitting nothing to stdout: the same invisible failure mode as the original defect, live today. Their declarations advertise `agent_record_kind="result"` and list `--agent` in `legacy_flags`. | `ipd-executed-gate --agent` -> rc 0, stdout EMPTY; same for `ipd-status-untooled-gate`, `precommit-scope-gate`, `backlog-blocking-close-gate`, `ipd-dependency-statement-gate`; `prepush-authorization-gate --agent` -> rc 1, stdout EMPTY, prose on stderr. Each `hooks/*.main` does `exit_code, messages = check()`, writes stderr, returns the int; no `CommandResult` is built. `cli._dispatch` calls them as `main([])`, discarding argv. |
| F-06 | All eight `aw config --agent` branches crash with `ImportError: cannot import name 'format_agent_json'`; the symbol is defined in NO file, in NO commit, on ANY branch, so the branches were dead on arrival. ALREADY OWNED by backlog `dtq6jr`. | 8 identical import statements in `cli.py` across 7 handlers (`_run_config_show` holds two). `config show/get/is/set --agent` all -> rc 1 with the traceback. `rg "def format_agent_json"` -> no hits; `git log --all -S "def format_agent_json"` -> no commits. |
| F-07 | `config remove --agent` is doubly broken: past the ImportError it would emit `outcome="not_found"`, which is NOT in `agent_schema.VALID_OUTCOMES` and would fail validation. | `cli.py` `_run_config_remove` passes `outcome="clean" if was_removed else "not_found"`; `'not_found' in VALID_OUTCOMES` -> `False`. Recorded for `dtq6jr`'s executor, not fixed here. |
| F-08 | Six leaves emit output with no terminal record for SANCTIONED reasons, not defects: `find`, `research find`, `research pending`, `research check-miscategorized`, `completion`, `config exclude list` print raw lines or generated text. `docs/cli-output-contract.md` Section 12 explicitly blesses bare paths under `--agent` for discovery verbs. | Driven individually: each writes non-empty stdout that is not JSONL. `path` declares `agent_record_kind="raw_path"`. This is why E-02's registry needs a `sanctioned_raw` kind rather than treating every non-envelope leaf as broken. |
| F-09 | The repo-tree run of `attention --agent` CANNOT see the original bug: it exits 1 with lane findings and never reaches the no-project branch. Only a non-project cwd reaches it. | `attention --agent` from the worktree -> rc 1, `outcome:"findings"`. From a bare `git init` dir -> the `cannot-run` record at exit 2. This is why E-01 must add a `cwd` axis. |
| F-10 | Baseline suite at authoring HEAD `58dc1c70`: `3246 passed, 2 skipped, 3 warnings in 53.64s` from a bare `python3 -m pytest`. | Full bare run in this lane. |

## Proposed changes (ordered, validatable)

1. Extend `tests/conformance_matrix.py` with a runnable-argv table and a `cwd` parameter on `run_cli` (E-01).
2. Add the justified exemption registry with its three reason kinds and mandatory citations (E-02).
3. Add `tests/test_agent_surface_conformance.py` computing its universe from the parser and asserting the four per-leaf properties; capture it RED on the six gate leaves (E-03).
4. Add the non-project-cwd case pinning the original defect's exact condition, and correct or file the stale comment citation (E-04).
5. Route the six hook-gate leaves through `get_renderer(...).emit(...)` with the human path byte-identical, turning E-03 green (E-05).
6. Confirm default-suite collection and correct the harness docstring (E-06).

## Deferred / out of scope (with reason)

- THE `aw config` FAMILY'S EIGHT CRASH SITES (F-06, F-07). Already owned by open backlog `dtq6jr` (high, `Blocks-Release: next`), which enumerates all seven verbs and requires tests driving each. Fixing it here would duplicate a filed item, absorb its release gate, and steal its validation. E-02 records it as `known_broken` citing `dtq6jr` so the sweep neither goes red on it nor claims it conforms. F-07 is new information that item does not yet have and should be handed to it.
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
- Status: open
- Owner: none
- Resolution or deferral rationale: DEFERRED TO MEASUREMENT WITHIN THIS PLAN, not past it, deliberately, because guessing decides it wrongly in both directions. The sweep spawns one subprocess per leaf over roughly 50 leaves; unmeasured, that is somewhere between a few seconds under `-n auto` and a minute. The default `addopts` deselects `slow` and `livecorpus`, so marking it `slow` means an agent running a bare `python3 -m pytest` before committing does NOT run this gate, which materially weakens it: the original bug shipped precisely because the default suite was silent. Note the repository has a measured precedent in the other direction too: `livecorpus` exists because one always-on test cost a run 2h 10m and $55.02 with nothing integrated, so "always on" is not automatically right either. THE ANSWER IS PRODUCED BY E-06 AND VERIFIED BY V-06, which require the executor to paste the MEASURED wall time and then either keep the file default-collected (proving it ran in the bare invocation) or, if it must be marked `slow`, record that weakening as a finding and file a follow-up. Nothing outlives this plan: it closes either with the sweep in the default suite, or with the weakening recorded and a filed item id pasted in V-06.
- Carrier-Declined: No durable carrier is owed, because this question is ANSWERED BY THIS PLAN rather than deferred beyond it. E-06 performs the measurement and V-06 requires the number and the resulting decision to be pasted as evidence, so the obligation cannot survive the plan's own validation gate unresolved. The one branch that DOES create future work (the sweep proving too slow for the default suite) already carries its own obligation inside V-06, which demands a filed follow-up id pasted as evidence; filing that item NOW would assert a slowness nobody has measured, which is the speculative-debt failure mode rather than an honest carrier.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the committed diff of `tests/conformance_matrix.py`. Paste the LITERAL output of calling `run_cli` twice with the same argv, once with no `cwd` and once with `cwd=<a temp non-project dir>`, showing DIFFERENT results for `attention --agent` (repo tree: exit 1 `findings`; temp dir: exit 2 `cannot-run`), which proves the axis is real and not cosmetic. CONFIRM the `REPO_ROOT` default is unchanged by pasting a `run_cli` call with no `cwd` argument still running in the repo. For the argv table, paste a table of every entry with the exit code observed when driven, and CONFIRM each is read-only by pasting `git status --short` before and after the full table run, showing NO new or modified files. State the COUNT of the 67 candidates now reachable and the count still unreachable; if the reachable count did not increase, say so plainly rather than reporting success.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the committed registry. For EVERY entry, paste the reason kind and its citation, and verify the citation RESOLVES: for `sanctioned_raw`, quote the sentence from `docs/cli-output-contract.md` Section 12 (or the `raw_path` declaration) that licenses it; for `known_broken`, paste the output of resolving backlog `dtq6jr` (for example `aw find backlog dtq6jr`) proving the item exists and is live; for `not_runnable`, name the specific blocker. CONFIRM there is NO catch-all, wildcard, or default-skip, by pasting the registry's full text and stating that every exempted leaf is named individually. CONFIRM no entry silences a leaf that E-03 could actually drive: paste the intersection of the registry with E-01's argv table and show it is EMPTY. CONFIRM the module comment stating that adding an entry to silence a red sweep is the prohibited failure mode is present, by quoting it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the committed test file and the RED run captured BEFORE E-05, including the full failure list. CONFIRM the red run names all six gate leaves from F-05; if it names fewer, state which are missing and why, rather than proceeding. CONFIRM by QUOTING the test code that the universe is COMPUTED from `discover_parser_leaves` plus the declaration predicate and is NOT a hand-written list, and that the four per-leaf assertions (non-empty stdout, terminal record present, `validate_agent_record` empty, exit parity) are all present. PASTE a grep of the test file for `inspect`, `ast.parse`, and any read of `agent_workflows/*.py` source returning NOTHING, per AGENTS.md P16. CONFIRM failures are per-leaf and name the leaf, by pasting one failure message in full. PASTE the count of leaves in the computed universe and reconcile it against F-03's 67 minus the registry size.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the committed test and its PASSING run. Paste the actual record asserted on, showing `outcome":"cannot-run"`, `"exit":2`, and `validate_agent_record` returning `[]`. PASTE a grep of stdout for the temp directory path and for `/home/` returning NOTHING, proving the summary stays sanitized. PASTE the human-path assertion's observed values: exit 3, prose on stderr, stdout EMPTY. THEN PASTE THE MUTATION THAT PROVES THE TEST HAS TEETH: delete `return get_renderer(ctx).emit(res, ctx)` from the no-project machine branch of `attention.run`, paste the FAILING output of this test AND of E-03's sweep, revert, and paste both green again. Without that mutation this item is not validated, because a test that passes at HEAD proves nothing about whether it would catch the regression. STATE which route E-04's comment correction took (edited `attention.py` with the path added to scope, or filed as a separate item) and paste either the diff or the filed item id.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the committed diff for all six hook modules (and for `cli.py` if the threading route was taken). PASTE THE BEFORE/AFTER MATRIX for all six leaves: with `--agent`, with `--json`, and with NEITHER, recording exit code, stdout, and stderr for each. BEFORE must reproduce F-05 (empty stdout under `--agent`); AFTER must show a schema-valid record with `exit` equal to the process code, pasted with `validate_agent_record` returning `[]`. PROVE THE HUMAN PATH IS BYTE-IDENTICAL: capture the no-flag stderr and exit code before and after into files and paste a `diff` showing NO differences, for a refusing case AND a passing case on at least one gate. CONFIRM a refusal does NOT report a positive outcome, by pasting the exit-1 record and showing its outcome is not in `('clean','ok','conforms')`, per the anti-greenwashing invariant. PASTE `python3 -m pytest tests/test_executed_transition_gate_e2e.py` passing with its count. STATE explicitly whether `agent_workflows/cli.py` was modified; if yes, confirm it was ADDED to `- Scope-Paths:` before the commit and paste the updated field.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the BARE `python3 -m pytest` output including its `N passed` summary line, and reconcile the total against F-10's `3246 passed, 2 skipped`, explaining every difference against a named E-item rather than waving it through. PROVE the sweep actually RAN in that bare invocation (for example by pasting a targeted `--collect-only` for the new file under the default `addopts`, or the node ids in the run), because a test that exists but is deselected is the exact hole this plan closes. PASTE THE MEASURED WALL TIME of the sweep and state the OQ-02 decision it drives: if marked `slow`, paste the finding recording the weakening and the filed follow-up id; if left default, paste the timing that justifies it. Paste the corrected `conformance_matrix.py` docstring and CONFIRM it no longer names a nonexistent consumer, by pasting an `ls` of each file it names.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste the committed docstring diff. For EVERY file the corrected docstring names, paste an `ls -la` of that path proving it exists. PASTE a grep of the docstring for the two stale names (`test_cli_conformance_matrix.py`, `test_cli_quality_gates.py`) returning NOTHING. CONFIRM the named consumer is the file E-03 actually added, by pasting its path from the commit.
    ALSO CARRY THE WHOLE-PLAN CLOSEOUT EVIDENCE HERE, as the last item before commit: PASTE `python3 -m agent_workflows check`; PASTE `aw ipd lint` reporting conforming; PASTE `aw sanitize --agent`; and PASTE `git diff --cached --name-only` immediately before committing, which must list ONLY paths drawn from `- Scope-Paths:` (as amended per V-05) and nothing else. If any co-worker path appears, unstage it precisely with `git restore --staged <path>` and say so.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive pass: a sweep is worthless without fixing what it finds, and the six gate fixes are unverifiable without the sweep that proves them broken first. Splitting them would land either a red test suite or an unpinned fix.

EXECUTION ORDER IS LOAD-BEARING, NOT ADVISORY. E-03 must be authored and captured RED before E-05 changes any handler. An executor who fixes the gates first destroys the failing-first evidence and can then only assert the sweep passes, which does not demonstrate it would ever fail. The same applies to V-04's mutation: the deletion-and-revert is the only evidence that the regression is actually caught.

The executor follows the repository execution contract: commit ONLY the declared paths through `aw commit <plan> -- <paths>`, never `git add -A`, never push, and paste ACTUAL runner output for every claim of passing tests. If E-05's threading requires `agent_workflows/cli.py`, AMEND `- Scope-Paths:` in this plan before staging it rather than committing an undeclared path. Do NOT touch the `aw config` family; it belongs to backlog `dtq6jr`, and hand F-07 to that item rather than fixing it here.

Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence, including the V-04 mutation and the V-05 byte-identical human-path diff.
