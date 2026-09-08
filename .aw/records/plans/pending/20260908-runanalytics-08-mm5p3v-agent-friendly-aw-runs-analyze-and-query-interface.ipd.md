# IPD: Agent-friendly aw runs analyze and query interface

- Date: 2026-09-08
- Kind: child
- Concern: Give humans and agents a stable, collision-safe way to build, inspect, and query analytics without scraping the SPA.
- Scope: Register fixed `aw runs analyze` and `aw runs query` leaves, define flags and exit codes, generate agent-oriented outputs, and preserve existing viewer/ledger routing.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/run_analytics_cli.py, agent_workflows/run_analytics_query.py, tests/test_run_analytics_cli.py, tests/test_run_viewer.py, tests/test_cli_conformance_matrix.py
- Item-Dependencies: executed:6eq3oq
- Status: reviewed
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 8
- Highest E allocated: 08
- Author: Codex
- Id: mm5p3v

## Workflow history

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-093..PR-102, ALL TEN FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE ROOT FINDING IS THAT A NEW LEAF IS NOT JUST A PARSER CHANGE AND THE PLAN'S OWN `Scope-Paths` COULD NOT HAVE SHIPPED IT (PR-093, F-1): every parser leaf MUST carry a `CommandDeclaration` in `command_surface.COMMAND_INVENTORY` (129 declarations today), because `find_undeclared_leaves` is asserted empty by `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves`, and the plan declared neither `command_surface.py` nor that test file, so registering two leaves would have failed a named fail-closed CI job with no in-scope file to fix it in. SECOND, AND IT IS A DIRECTION VIOLATION (PR-094, F-2): `aw runs` is documented in code as "the READING half of the run surface ... Read-only, except the opt-in `repair` verb", and `analyze` WRITES (updates cache, publishes a bundle), so it is the SECOND mutating verb on a read noun and its `command_class` must be `mutation`, which changes its required scenario set. THIRD, THE COLLISION TEST AS WRITTEN WOULD HAVE PASSED VACUOUSLY AND HIDDEN A REAL BUG (PR-095, F-3): measured, `aw runs -- status` does NOT resolve a run named `status`; it returns ALL 135 runs, because `resolve_target_runs`' final fallback greps the raw `state.json` TEXT for `"<token>"` and `status` is a JSON KEY name; `analyze` and `query` match 0 runs today, so the plan's assertion would pass while proving nothing. FOURTH, THE AGENT PROTOCOL ALREADY EXISTS AND THE PLAN PROPOSED A SECOND ONE (PR-096, F-4): `agent_schema.SCHEMA_VERSION` is `aw.agent/v1` with a closed `RECORD_KINDS` and a 13-value `VALID_OUTCOMES`, and `tests/test_cli_quality_gates.py` enforces a 1200-byte / 400-token budget per agent record, which a "distributions" or "slices" view will breach by construction unless it paginates. FIFTH, THE SPEC-SYNC SECTION LEFT A DISCOVERY TO THE EXECUTOR THAT IS ALREADY ANSWERED (PR-097, F-5): spec `20260818-1525-01-command-surface-redesign` is `Status: implemented` and normative, so "if the repository maintains a controlling CLI grammar spec" is not an open question. ALSO FIXED: the `--` escape hardcodes `run_viewer.run_viewer_cli` so an escaped token can never reach a leaf, which makes one of the plan's promised behaviors already true and the other untestable as phrased (PR-098, F-6); no browser-launch precedent exists in the package, so `--open` is greenfield and needs an explicit no-op-by-default proof (PR-099, F-7); the three E-items were mechanically sized and the Set orchestrator's own OQ-01 names this plan's siblings for the same defect (PR-100, F-8, split to EIGHT); the gate carried no execution contract, the eighth sibling in a row (PR-101, F-9); and 78 escaped backticks rendered as literal backslashes, the worst count in the Set (PR-102, F-10).

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): defined fixed command grammar, analysis controls, a versioned agent protocol, and routing compatibility tests.

## Goal

Make `aw runs analyze` the one command that updates cache and produces the local report bundle, and `aw runs query` the concise structured interface agents can use for facts and findings. Fixed leaf names must preserve the current `aw runs -- <target>` collision escape and never create dynamic commands.

REGISTERING A LEAF IS A THREE-FILE CONTRACT, NOT A PARSER EDIT. Measured: `command_surface.COMMAND_INVENTORY` holds 129 declarations, `find_undeclared_leaves` is asserted EMPTY by `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves`, and that file runs as a NAMED fail-closed CI job across six Python versions. So each new leaf needs a parser registration, a `CommandDeclaration`, and the scenario coverage the declaration's `command_class` implies (F-1).

AND `analyze` MUTATES, ON A NOUN DOCUMENTED READ-ONLY. `aw runs`' own description says "the READING half of the run surface ... Read-only, except the opt-in `repair` verb". `analyze` updates a cache and publishes a bundle, making it the SECOND exception. That is defensible but must be DECLARED (`command_class="mutation"`) and stated in the noun's help, not slipped in (F-2).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE. Authored with THREE E-items, as were all ten children of this Set (31 items). E-03 as authored bundled routing, compatibility, failure semantics, discoverability and help output, which are five unrelated test surfaces; E-02 bundled ten query views with a schema-versioning contract and output-format matrix. Seven siblings were already split for the identical reason (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7, `8hald1` 3->8, `aflsz3` 3->9, `6eq3oq` 3->8). Split into EIGHT items across four groups (surface contract / analyze / query / routing and failure).

### Task group 1: The surface contract

- [ ] E-01 Declare both leaves in `command_surface.COMMAND_INVENTORY` and satisfy the conformance matrix, because the parser edit alone cannot merge.
  MEASURED, AND THIS IS WHY THE ITEM EXISTS. `command_surface.COMMAND_INVENTORY` carries 129 `CommandDeclaration`s; `discover_parser_leaves(_build_parser())` reports 124 parser leaves; `find_undeclared_leaves` returns exactly `{oc profile add, oc profile default, oc profile list, oc profile remove, oc profile show}` today, and `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves` asserts that set is EMPTY, so those five are a live pre-existing failure in that file and MUST NOT be conflated with this plan's work. That file is `pytestmark = pytest.mark.slow`, so the BARE suite (`addopts` supplies `-m 'not slow'`) DESELECTS it entirely; it runs in the dedicated `output-conformance` CI job across Python 3.9 through 3.14. So a bare green suite proves nothing about leaf conformance and the executor MUST run that file explicitly.
  EACH DECLARATION DRIVES ITS OWN REQUIRED SCENARIO SET, computed by `tests/conformance_matrix.required_scenarios`: every leaf needs `tty`, `non_tty`, `agent`, `no_color`, `help`, `usage_error`; `json` is added for a `read`/`check`/`bare` class or a declared `--json`; `domain_failure` for a read/check whose `exit_contract` includes 1; `success_preview` for a `mutation` or `preview` class. Choose `command_class` deliberately: `query` is `read`, `analyze` is `mutation` (F-2).
  - Depends on: none
  - Expected outcome: both leaves declared with a deliberate `command_class`, `human_recipe`, `agent_record_kind`, `mutation_gate` and `exit_contract`; `find_undeclared_leaves` returns the SAME five pre-existing `oc profile *` entries and no new one; the conformance matrix reports a full scenario row set for both new leaves.
  - Execution state: pending

- [ ] E-02 Register both leaves through the existing viewer-or-leaf routing action, as REAL subparsers.
  USE `_ViewerOrLeafSubParsersAction`, WHOSE DOCSTRING ALREADY EXPLAINS WHY. It routes `aw runs`' first positional to a leaf subparser when it exactly matches a registered leaf name, else to the sibling viewer parser, because plain argparse cannot hold `targets nargs="*"` plus `add_subparsers()` (measured on CPython 3.14 in that docstring: every non-empty argv exits 2). Register via the established `_register_run_leaf` path onto `runs_sub`.
  DO NOT COPY THE `repair` PATTERN. `repair` is routed from the first POSITIONAL inside `run_viewer`, not as a subparser, and the docstring records the exact cost: "A positionally-routed leaf is invisible to the normative command surface, so declaring it in `COMMAND_INVENTORY` would register as declaration/parser DRIFT and fail `tests/test_cli_conformance_matrix.py`. It also gets no argparse help." Confirmed by measurement: `repair` appears in NO declaration. A positionally-routed `analyze` would therefore be undeclarable, which contradicts E-01.
  ALSO UPDATE THE NOUN'S OWN HELP AND DESCRIPTION. `_RUNS_DESCRIPTION` currently says "Read-only, with ONE exception: the `repair` verb", which becomes false the moment `analyze` lands.
  - Depends on: E-01
  - Expected outcome: both leaves are real subparsers discoverable by `discover_parser_leaves`, with native argparse help and usage errors; `_RUNS_DESCRIPTION` and the `runs` help epilog updated so the read-only claim stays true; no positional routing added; the nine existing leaves and the bare viewer route identically.
  - Execution state: pending

### Task group 2: analyze

- [ ] E-03 Implement `analyze`'s option surface with documented precedence and no interactive prompt.
  `aw runs analyze [TARGET ...]` defaults to all canonical runs and latest output. `--output`, `--path`, `--list`, `--latest`, `--keep-snapshot`, `--rebuild` and the machine-readable modes need documented precedence and exit codes. Resolve every path through Order 01's (`xbwq8n`) resolver and containment predicate; never compose the `.aw/records/runs` literal, which Order 01 exists to remove from six sites.
  EXIT CODES ARE NOT FREE-FORM BUT ARE NOT LIMITED TO 0/1/2 EITHER. Measured across the 129 declarations: 89 declare `(0,1,2)`, 30 declare `(0,2)`, and eight declare a code above 2 (`run start` and `run record` at `(0,2,3,5,6)`, `runs status` at `(0,1,3,5)`, `run finalize` at `(0,1,4,6)`, `runs next` and `runs resume` at `(0,3)`, `run cancel` at `(0,5,6)`, `ipd execute-set` at `(0,1,2,3)`). But `agent_schema.validate_agent_record` REQUIRES the record's `exit` field to be in `(0,1,2)` for a `result`, `summary` or `error` kind, so a leaf emitting an agent record cannot report a higher code IN THE RECORD. Reconcile the two deliberately rather than discovering the conflict at test time.
  - Depends on: E-02
  - Expected outcome: every flag has documented precedence and a tested exit code; the command never prompts; paths come from Order 01's resolver; the declared `exit_contract` is consistent with what `validate_agent_record` accepts in an agent record, with the reconciliation stated.
  - Execution state: pending

- [ ] E-04 Implement `--open` as an explicit, defaulted-off side effect, which is greenfield here.
  NO BROWSER-LAUNCH PRECEDENT EXISTS IN THIS PACKAGE. Measured: a repo-wide search for `webbrowser`, `xdg-open` or an `--open` flag finds nothing relevant (`--open-questions` is an unrelated flag on another verb). So there is no house pattern to copy and no existing test double. Build the launch behind an injectable seam so tests can assert it was NOT called, and treat "never launched without `--open`" as the property under test rather than a claim.
  - Depends on: E-03
  - Expected outcome: analysis without `--open` provably never launches anything (asserted by a stub that FAILS if invoked, not by inspection); supported, unsupported and launch-failure platforms each yield a documented exit code and remedy; no new runtime dependency.
  - Execution state: pending

### Task group 3: query

- [ ] E-05 Implement the allowlisted query grammar over the cached and companion data.
  Views: overview, schema, metrics, distributions, slices, findings, evidence, data quality, cache status, and explain-taxonomy/price. Filters and groupings come from an ALLOWLISTED schema. Arbitrary SQL, expression evaluation, filesystem paths outside the resolved roots, and unrestricted field projection are excluded, which is the correct posture and is preserved.
  CONSUME ORDER 06'S REFUSALS RATHER THAN RE-DERIVING THEM. Order 06 (`aflsz3`) returns `cannot-determine` for five of the sixteen required analyses on measured grounds, and Order 07 (`6eq3oq`) renders those as refusal panels. `query metrics` must surface the same refusal with the same observed n, not compute a number Order 06 declined to compute. A query interface that answers what the engine refused is a second, weaker engine.
  - Depends on: E-02
  - Expected outcome: every view implemented over an allowlisted filter/group schema with no expression evaluation and no path escape; an under-powered or refused slice returns Order 06's refusal verdict verbatim with its observed n; a rejected filter names the allowlist rather than echoing the input.
  - Execution state: pending

- [ ] E-06 Emit `query` results through the EXISTING `aw.agent/v1` envelope, and respect its measured budget.
  DO NOT INVENT A SECOND PROTOCOL. Measured: `agent_schema.SCHEMA_VERSION` is `aw.agent/v1`; `RECORD_KINDS` is the closed set `('result','summary','item','error')`; `VALID_OUTCOMES` is a closed 13-value set (`clean`, `ok`, `conforms`, `findings`, `fail`, `preview`, `stale`, `skipped`, `partial`, `unverified`, `changed-unverified`, `cannot-run`, `error`); `validate_agent_record` enforces kind-specific mandatory fields plus explicit ANTI-GREENWASHING rules (a positive outcome with `verified=False` is an error); and `filter_record_fields` already implements bounded field projection preserving mandatory envelope fields. The plan's "versioned query protocol" is therefore this envelope plus a `data` payload, not a new schema. Note `cannot-run` is the closest existing outcome for a refused slice; if none fits, that is a deliberate schema question, not a licence to add a value silently.
  THE BUDGET IS THE HARD PART AND IT IS MEASURED. `tests/test_cli_quality_gates.py` enforces `BYTE_BUDGET = 1200` and `TOKEN_BUDGET = 400` per agent record, with an explicit `test_fields_projection_shrinks_record`. A `distributions` or `slices` view over 29766 fact rows breaches that by construction. So bounded default limits are not a nicety: they are what makes the view conformant. Decide the default limit and the pagination shape HERE.
  - Depends on: E-05
  - Expected outcome: every view emits a valid `aw.agent/v1` record that passes `validate_agent_record`, stays inside the measured 1200-byte / 400-token budget by DEFAULT, and paginates rather than truncating silently; units, missingness and provenance travel in `data`; `--fields` projection reuses `filter_record_fields`; JSONL streaming is used where a record set is inherently long.
  - Execution state: pending

### Task group 4: Routing and failure

- [ ] E-07 Prove the routing and collision matrix against what the escape hatch ACTUALLY does.
  THE PLAN'S COLLISION TEST WOULD HAVE PASSED VACUOUSLY, MEASURED. `aw runs -- analyze` and `aw runs -- query` today print `no matching runs found` and exit 0, because `resolve_target_runs` matches neither. So asserting "`aw runs -- analyze` resolves that word as a viewer target" passes BEFORE any code is written and proves nothing about the escape.
  WORSE, THE ESCAPE HAS A REAL PRE-EXISTING BUG THIS TEST WOULD BRUSH PAST. `aw runs -- status` does NOT resolve a run named `status`: it returns ALL 135 runs. Measured cause: `resolve_target_runs`' final fallback greps the raw `state.json` TEXT for `"<token>"` and `status` is a JSON KEY name present in every file, so the "setid" fallback matches on a key rather than a value. Report this; do NOT fix it here (it is `run_viewer` target resolution, owned by Order 01's discovery work and outside this plan's concern), and do not write a test that depends on the buggy behavior.
  ALSO: THE ESCAPE CANNOT REACH A LEAF BY CONSTRUCTION. `_dispatch` handles `--` pre-parse and hardcodes a call into `run_viewer.run_viewer_cli` after forcing `runs_command = None`, so an escaped token is ALWAYS a viewer target and can never route to `analyze` or `query`. That makes half the promised behavior already true and structurally guaranteed; assert it at the dispatch level rather than as a behavioral coincidence.
  - Depends on: E-04, E-06
  - Expected outcome: the nine existing leaves and the bare viewer route byte-identically (goldens); a fixture run or Set actually NAMED `analyze`/`query` is created so the escape test is non-vacuous, and the escape reaches the viewer while the bare form reaches the leaf; the `"status"` key-collision bug is REPORTED with its measurement and not depended upon; no test asserts a behavior that already passes pre-change without saying so.
  - Execution state: pending

- [ ] E-08 Prove the failure semantics, help discoverability, and cache reuse.
  Malformed filters, missing corpus, corrupt cache, partial analysis, open failure and unsupported schema each return a documented code and an actionable remedy. Analyze twice to prove cache reuse; mutate or resume one fixture and prove selective rebuild.
  DROP THE UNTESTABLE CLAIM. The authored tests promise "Help and README command snippets are executable", and there is NO mechanism for that: `tests/test_cli_output_docs_rollout.py` asserts docs CONTENT (that they describe exit codes, accessibility, schema kinds) and executes no snippet; no test in the suite runs a documented command line. Either build that mechanism as a declared deliverable or state the claim as documentation review; do not imply coverage that does not exist.
  - Depends on: E-07
  - Expected outcome: each named failure class has a test asserting its exit code AND a remedy string; cache hit and selective-rebuild are demonstrated on fixtures; help output is asserted via the conformance matrix's `help` scenario rather than an ad hoc snapshot; the snippet-executability claim is either implemented or explicitly downgraded, never left implied.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw runs` uses a custom viewer-or-leaf subparser whose registration order is load-bearing. New fixed leaves must be added through its established leaf table/routing mechanism. VERIFIED: `_ViewerOrLeafSubParsersAction` (`cli.py:623`) routes the first positional to a leaf subparser when it exactly matches a registered name, else re-parses with the sibling viewer parser; its docstring records that plain argparse cannot express `targets nargs="*"` plus `add_subparsers()` (measured on CPython 3.14).
- A NEW LEAF IS A THREE-FILE CONTRACT, NOT A PARSER EDIT. `command_surface.COMMAND_INVENTORY` holds 129 declarations; `find_undeclared_leaves` is asserted EMPTY by `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves`; `tests/conformance_matrix.required_scenarios` derives the required scenario set from the declaration's `command_class` and `exit_contract`. Neither `command_surface.py` nor that test file was in the authored `Scope-Paths`.
- THE CONFORMANCE GATE IS INVISIBLE TO THE BARE SUITE. `tests/test_cli_conformance_matrix.py` carries `pytestmark = pytest.mark.slow` and `pyproject.toml` `addopts` supplies `-m 'not slow'`, so a bare `python3 -m pytest` DESELECTS it. It runs in the dedicated `output-conformance` CI job across Python 3.9-3.14. A bare green suite is therefore NOT evidence of leaf conformance; run the file explicitly.
- FIVE LEAVES ARE UNDECLARED TODAY AND ARE NOT THIS PLAN'S FAULT. `find_undeclared_leaves` returns `{oc profile add, oc profile default, oc profile list, oc profile remove, oc profile show}`, a live pre-existing failure of that test. Do not fix it here and do not report it as this plan's regression; state the baseline set so a new entry is attributable.
- `aw runs` IS THE READING NOUN AND `analyze` BREAKS THAT. `cli.py`'s help says "the READING half of the run surface" and `_RUNS_DESCRIPTION` says "Read-only, with ONE exception: the `repair` verb". `analyze` updates a cache and publishes a bundle, so it is the SECOND exception and must be declared `command_class="mutation"` and reflected in the noun's help.
- Existing fixed viewer leaves take a ledger-style target, but analytics leaves require distinct parsers; do not force them through a helper whose arguments do not fit.
- Current help documents the `--` escape for targets colliding with a leaf. Keep and extend that contract. MEASURED CAVEAT: the escape is handled PRE-PARSE in `_dispatch`, which forces `runs_command = None` and hardcodes `run_viewer.run_viewer_cli`, so an escaped token can NEVER reach a leaf. Half the plan's promised behavior is therefore structurally guaranteed already.
- THE ESCAPE HAS A PRE-EXISTING KEY-COLLISION BUG. Measured: `aw runs -- status` returns ALL 135 runs rather than a run named `status`, because `resolve_target_runs`' last fallback greps the raw `state.json` text for `"<token>"` and `status` is a JSON key present in every file. `analyze` and `query` match 0 runs today, so a naive collision test passes vacuously.
- NO SETID OR RUN ID COLLIDES WITH ANY LEAF NAME, EXISTING OR PROPOSED. Measured across 78 run-corpus setids, 345 run/id6 tokens and 639 tracked plan setids and id6s: zero matches against the nine leaves plus `repair`, `analyze` and `query`. So the escape is a contract to preserve, not a live need, and a collision test needs a PURPOSE-BUILT fixture to be non-vacuous.
- Agent output conventions use `--agent` JSONL and `--json`; integrate rather than emit ad hoc prose. VERIFIED AND STRONGER THAN STATED: `agent_schema.SCHEMA_VERSION` is `aw.agent/v1` with closed `RECORD_KINDS` and a 13-value `VALID_OUTCOMES`, `validate_agent_record` enforces anti-greenwashing invariants, and `filter_record_fields` already provides bounded projection. There is no room for a second protocol.
- THE AGENT RECORD BUDGET IS ENFORCED AND SMALL. `tests/test_cli_quality_gates.py` sets `BYTE_BUDGET = 1200` and `TOKEN_BUDGET = 400` per record. A distributions or slices view over the measured 29766 fact rows breaches that by construction, so bounded default limits and pagination are conformance requirements, not ergonomics.
- EXIT CODES ABOVE 2 EXIST BUT NOT INSIDE AN AGENT RECORD. Measured: eight declarations use a code above 2 (`run start`/`run record` `(0,2,3,5,6)`, `runs status` `(0,1,3,5)`, `run finalize` `(0,1,4,6)`, `runs next`/`runs resume` `(0,3)`, `run cancel` `(0,5,6)`, `ipd execute-set` `(0,1,2,3)`), while `validate_agent_record` requires the record's `exit` field to be in `(0,1,2)`.
- `--open` is an explicit user side effect. Analysis without it must never launch a browser. NOTE IT IS GREENFIELD: no `webbrowser`, `xdg-open` or comparable call exists anywhere in the package, so there is no pattern to copy and the no-launch property must be proven with an injectable seam.
- A NORMATIVE, IMPLEMENTED CLI GRAMMAR SPEC EXISTS. `.aw/records/specs/20260818-1525-01-command-surface-redesign.spec.md` is `Status: implemented` and normative (Section 3 "The target grammar"), and its R4 already requires documented exit codes and `--json`/`--agent` on cross-cutting verbs. The plan's "if the repository maintains a controlling CLI grammar spec" is answered.

## Findings

Recommended command contract:

- `aw runs analyze [TARGET ...]`: analyze source runs, update safe caches, publish latest report. MUTATION class, the second exception to the read-only noun.
- `aw runs analyze --path`: print the latest HTML path without opening it.
- `aw runs analyze --list`: list report/snapshot/export artifacts and cache summary.
- `aw runs query <view>`: return facts/findings for agents without parsing HTML. READ class.
- `aw runs query findings --limit 10 --format json`: ranked evidence records.
- `aw runs query metrics --group-by model,phase --metric cost --stat median`: bounded aggregation using the same engine. NOTE the `model` grouping is near-empty for historical data (Order 06 measured model identity resolvable for 2 of 179 attempts), so this exact example must render an honest empty state rather than appear to work.
- `aw runs query explain --taxonomy <rule-id>` or `--price <price-id>`: provenance and interpretation.

Arbitrary SQL, expression evaluation, filesystem paths outside the resolved roots, and unrestricted field projection are excluded. Filters and groupings come from an allowlisted schema.

### Findings (review, measured 2026-09-08 at HEAD `3ec92ca4`)

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | plan `Scope-Paths`; `command_surface.py`; `tests/test_cli_conformance_matrix.py` | **A NEW LEAF CANNOT SHIP FROM THE AUTHORED `Scope-Paths`.** Every parser leaf MUST carry a `CommandDeclaration`: `COMMAND_INVENTORY` holds 129, `find_undeclared_leaves` is asserted EMPTY by `test_no_undeclared_parser_leaves`, and that file is a NAMED fail-closed CI job across Python 3.9-3.14. The plan declared neither `command_surface.py` nor the test file, so registering two leaves would fail CI with no in-scope file to fix it in. Compounding it, the file is `pytest.mark.slow` and the bare suite deselects it, so the plan's own validation would have reported green | called `discover_parser_leaves` and `find_undeclared_leaves` on the real parser; read the test and its `pytestmark`; read the CI job |
| F-2 | HIGH | `cli.py:111-127`, `_RUNS_DESCRIPTION`; plan E-01 | **`analyze` MUTATES ON A NOUN DOCUMENTED READ-ONLY, AND THE PLAN NEVER SAID SO.** `aw runs` is "the READING half of the run surface" and its description says "Read-only, with ONE exception: the `repair` verb". `analyze` updates a cache and publishes a bundle, making it the second exception. This changes its `command_class` to `mutation`, which changes its required scenario set (`success_preview` instead of `domain_failure`), and falsifies the noun's own description text | read the help constants and `required_scenarios`; confirmed the direction split at `cli.py:111` |
| F-3 | HIGH | plan required tests; `run_viewer.resolve_target_runs` | **THE COLLISION TEST WOULD HAVE PASSED VACUOUSLY AND WALKED PAST A REAL BUG.** Measured: `aw runs -- analyze` and `aw runs -- query` print `no matching runs found` and exit 0 today, so the assertion passes before any code exists. And `aw runs -- status` does NOT resolve a run named `status`; it returns ALL 135 runs, because the final fallback greps raw `state.json` TEXT for `"<token>"` and `status` is a JSON KEY in every file. A test written as authored proves nothing and risks pinning the buggy behavior | ran all three commands; called `resolve_target_runs` directly for each token (135/0/0); confirmed `"status" in state.json` |
| F-4 | HIGH | plan E-02's "versioned query protocol"; `agent_schema`; `tests/test_cli_quality_gates.py` | **THE AGENT PROTOCOL ALREADY EXISTS AND THE BUDGET MAKES THE PROPOSED VIEWS NON-CONFORMANT BY DEFAULT.** `SCHEMA_VERSION` is `aw.agent/v1` with a closed `RECORD_KINDS`, a 13-value `VALID_OUTCOMES`, anti-greenwashing invariants, and an existing `filter_record_fields` projection. Separately `BYTE_BUDGET = 1200` / `TOKEN_BUDGET = 400` per record is enforced, which a `distributions` or `slices` view over 29766 rows breaches by construction unless bounded and paginated | imported `agent_schema` and printed the constants; read `validate_agent_record` and the quality-gate budgets |
| F-5 | MEDIUM | plan spec-sync section; spec `20260818-1525-01` | **THE SPEC-SYNC SECTION DEFERS A DISCOVERY THAT IS ALREADY ANSWERED.** It says "If the repository maintains a controlling CLI grammar spec, execution must amend it before registering leaves". That spec exists, is `Status: implemented`, and is normative (Section 3 "The target grammar (normative)"; R4 already mandates documented exit codes and `--json`/`--agent`). Leaving it conditional invites either an unnecessary spec edit or a silent divergence, and no `.spec.md` is declared in `Scope-Paths` | listed `.aw/records/specs/`; read the spec's status and normative sections |
| F-6 | MEDIUM | `cli.py:10616-10633`; plan required tests | **THE `--` ESCAPE CANNOT REACH A LEAF BY CONSTRUCTION, SO ONE PROMISED BEHAVIOR IS ALREADY GUARANTEED AND THE OTHER IS MISPHRASED.** `_dispatch` handles `--` pre-parse, forces `runs_command = None`, and hardcodes `run_viewer.run_viewer_cli`. So an escaped token is always a viewer target; "fixed leaves win without `--`" is a property of the routing action, and the two halves are enforced in different places. A behavioral test alone would not distinguish them | read the pre-parse block and the routing action; ran `aw runs -- status` and `aw runs -- <real-run-id>` |
| F-7 | MEDIUM | plan E-01's `--open`; package-wide | **`--open` IS GREENFIELD WITH NO PRECEDENT AND NO TEST DOUBLE.** A repo-wide search for `webbrowser`, `xdg-open` or an `--open` flag finds nothing relevant (only an unrelated `--open-questions`). So "must never launch a browser" has no existing seam to assert against, and inspection is not proof; it needs an injectable launcher that FAILS the test if invoked | grepped the package for every launch mechanism |
| F-8 | MEDIUM | plan E-01..E-03; orchestrator `5lxvl3` OQ-01 | **MECHANICALLY SIZED.** E-03 bundled routing, compatibility, failure semantics, discoverability and help output across five unrelated test surfaces; E-02 bundled ten query views with a schema-versioning contract and an output-format matrix. All ten children carry exactly three items and the count-based lint passes at three by construction. Eighth sibling with this finding | orchestrator plan read; item content counted against the workflow's split diagnostics |
| F-9 | MEDIUM | plan gate as authored | The gate carried two sentences and NO execution contract: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-measure warning, no stop conditions. Eighth consecutive sibling with the same omission | plan read; seven sibling review records read |
| F-10 | LOW | plan source (78 escaped backticks); suite baseline; docs-snippet claim | Seventy-eight escaped backtick pairs rendered as literal backslashes, the worst count in the Set (after 6, 4, 10, 18, 16, 4 and 20). No baseline was recorded despite requiring a bare suite run: measured `2 failed, 5655 passed, 3 skipped, 2 xfailed in 100.25s`, both failures pre-existing and pinned to the live plan corpus. Also "Help and README command snippets are executable" has NO mechanism: `tests/test_cli_output_docs_rollout.py` asserts docs CONTENT and executes no snippet | `grep -o` count before the fix; bare suite run; read the docs test |

## Proposed changes (ordered, validatable)

1. E-01 declares both leaves and satisfies the conformance matrix; E-02 registers them as real subparsers and corrects the noun's read-only claim.
2. E-03 implements `analyze`'s flags with reconciled exit codes; E-04 makes `--open` provably opt-in behind an injectable seam.
3. E-05 implements the allowlisted query grammar and forwards Order 06's refusals; E-06 emits through the existing `aw.agent/v1` envelope inside its measured budget.
4. E-07 proves routing and collision behavior with a non-vacuous fixture; E-08 proves failure semantics, cache reuse, and drops the unimplementable snippet claim.

## Deferred / out of scope (with reason)

- Export and submit are Order 09 (`ixis0c`) because their consent and sensitivity model differs.
- Dynamic aliases such as `aw analyze` or config-created leaves are excluded to prevent command collisions.
- A long-running API server or MCP server is not required; agents can invoke the deterministic CLI directly.
- Automatic browser launch and automatic network action are excluded.
- The SPA, the report bundle and its schemas are Order 07 (`6eq3oq`); the taxonomy, pricing, statistics and findings are Order 06 (`aflsz3`); the run-root resolver and reserved namespace are Order 01 (`xbwq8n`); the cache is Order 02 (`bzz5e6`). This plan CONSUMES all of them and reimplements none.
- THE FIVE UNDECLARED `oc profile *` LEAVES ARE A PRE-EXISTING FAILURE OF `test_no_undeclared_parser_leaves` AND ARE NOT FIXED HERE. They are the measured baseline against which a NEW undeclared leaf becomes attributable.
- THE `"status"` KEY-COLLISION BUG in `resolve_target_runs` is REPORTED, not fixed: it is target-resolution behavior in `run_viewer`, adjacent to Order 01's discovery work, and fixing it would change what every existing viewer invocation matches.
- Building a docs-snippet execution harness is out of scope unless E-08 elects to; the alternative is to state the claim as documentation review rather than coverage.

## Scope check

- Over-scope: no source parsing, statistics, HTML implementation, telemetry, export, or transport. Specifically, and each for a measured reason: do NOT compose the `.aw/records/runs` literal (Order 01 owns the resolver); do NOT introduce a second agent protocol or add a value to `RECORD_KINDS`/`VALID_OUTCOMES` without saying so (the closed sets are enforced by `validate_agent_record`); do NOT raise `BYTE_BUDGET`/`TOKEN_BUDGET` to make a view fit (bound and paginate the view instead); do NOT route a leaf positionally like `repair` (it becomes undeclarable, contradicting E-01); do NOT fix the five `oc profile *` declarations or the `"status"` resolution bug; do NOT compute a statistic Order 06 owns or answer a slice Order 06 refused; and do NOT edit a spec, since none is declared in `Scope-Paths`.
- `command_surface.py` and `tests/test_cli_conformance_matrix.py` ARE now in `Scope-Paths`, necessarily: a leaf cannot be declared without the first, and the matrix's pre-existing-baseline assertion may need its known-set updated in the second. Both edits must be minimal.
- An out-of-scope edit is not forbidden outright, it must be JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.
- Under-scope: includes all user-requested analyze options, direct agent access, stable schemas, errors, help, and collision tests. The declaration contract (E-01), the mutation-class correction (E-02), the exit-code reconciliation (E-03), the injectable launch seam (E-04), the refusal forwarding (E-05), the budget-conformant envelope (E-06) and the non-vacuous collision fixture (E-07) were all under-scope before review.

## Required tests / validation

Baseline, measured bare at HEAD `3ec92ca4`: `2 failed, 5655 passed, 3 skipped, 2 xfailed in 100.25s`. Both failures (`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` and `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`) are pinned to the live mutable plan corpus and are PRE-EXISTING. Re-measure in the executing worktree and compare failing NODE IDS; the criterion is an empty delta against your own baseline, never a total.

THE BARE SUITE IS NOT SUFFICIENT FOR THIS PLAN, AND THAT IS THE SINGLE MOST IMPORTANT LINE HERE. `tests/test_cli_conformance_matrix.py` is `pytest.mark.slow` and `addopts` supplies `-m 'not slow'`, so a bare run DESELECTS the one gate that proves a leaf is declared and covered. Run it EXPLICITLY (`python3 -m pytest tests/test_cli_conformance_matrix.py tests/test_cli_quality_gates.py tests/test_cli_output_docs_rollout.py`), which is exactly what the `output-conformance` CI job does, and paste both that output AND the bare-suite output.

- Declaration conformance: `find_undeclared_leaves` returns the SAME five pre-existing `oc profile *` entries and no new one; the matrix reports a full required scenario row set for `runs analyze` and `runs query`, with the scenario set matching each leaf's `command_class` (`mutation` gets `success_preview`, `read` gets `domain_failure` when its contract includes 1).
- Parser and dispatch tests for every flag and format, defaults, incompatibilities, target resolution, and exit code. Assert the declared `exit_contract` is consistent with `validate_agent_record`'s `(0,1,2)` requirement for any record the leaf emits.
- `aw runs` viewer and every existing fixed leaf retain behavior, asserted with goldens rather than by inspection.
- COLLISION TESTS MUST BE NON-VACUOUS. Create a fixture run or Set actually NAMED `analyze` and one named `query` (measured: zero of 78 corpus setids, 345 run tokens and 639 tracked plan setids/id6s collide with any leaf name, so nothing in the tree exercises this). Then assert the bare form reaches the LEAF and the `--` form reaches the VIEWER. Assert the dispatch-level guarantee too: `_dispatch`'s pre-parse block forces `runs_command = None`, so an escaped token structurally cannot reach a leaf. Record that `aw runs -- analyze` returns `no matching runs found` exit 0 BEFORE the change, so the test is shown to distinguish fixed from unfixed.
- Report, and do NOT depend on, the measured `"status"` key-collision behavior (`aw runs -- status` returns all 135 runs because the setid fallback greps raw JSON text for a key name).
- Analyze twice to prove cache reuse; mutate/resume one fixture and prove selective rebuild.
- Query golden tests for all views, filters, groupings, units, missingness, provenance, row limits, streaming JSONL, and schema version. EVERY record must pass `validate_agent_record` AND stay inside the measured 1200-byte / 400-token budget by default; include a test that a `distributions` view over a corpus-scale fixture (about 30000 rows) is bounded rather than budget-breaking. Include a test that a slice Order 06 refused returns that refusal with its observed n rather than a computed number.
- Open behavior asserted with a stub that FAILS if invoked, for supported/unsupported/failure systems, and never called without `--open`. Inspection is not evidence; there is no existing precedent to copy.
- Help discoverability asserted via the conformance matrix's `help` scenario. The authored "README command snippets are executable" claim must be implemented as a real harness or downgraded to documentation review, because no such mechanism exists today.
- No test may reach the network, launch a browser, spend real time, or parse the live corpus as its assertion source.
- Bare `python3 -m pytest` and `git diff --check`. Run the bare suite BARE; do not add `-n0`, a second `-q`, or `-p no:randomly`, since `pyproject.toml` `addopts` already supplies the intended flags. The conformance files are a SEPARATE explicit invocation, per the paragraph above.

## Spec / documentation sync

Order 10 (`9xycbh`) publishes the full command and agent-protocol reference.

THE CONTROLLING CLI GRAMMAR SPEC EXISTS AND IS SETTLED, so the authored conditional is replaced by a fact. `.aw/records/specs/20260818-1525-01-command-surface-redesign.spec.md` is `Status: implemented` with a normative Section 3 and an R4 already requiring documented exit codes plus `--json`/`--agent`. Adding two leaves under an existing noun is consistent with that grammar and does NOT amend it: the spec governs the noun-verb shape and the cross-cutting verbs, not the leaf census under `aw runs`. THIS PLAN DECLARES NO `.spec.md` IN `Scope-Paths` AND MUST EDIT NONE. If execution concludes the grammar contract genuinely must change (for example because a mutating leaf on the reading noun is judged a grammar violation rather than a documented exception), that is a STOP-and-raise for the maintainer, not a unilateral edit.

TWO DOCUMENTATION OBLIGATIONS THIS REVIEW ADDS. FIRST, `aw runs`' own description must stop claiming a single mutating exception once `analyze` lands, or the help text becomes false. SECOND, Order 10 must document that `query` forwards Order 06's refusals rather than computing them, since an agent that receives `cannot-determine` needs to know it came from the engine's measured refusal and not from a query error. RE-MEASURE every count here at execution; the parser and the declaration inventory both grow.

## Open questions

"No open questions" was not accurate: the plan required four decisions it specified nowhere. All four are answerable from repository evidence or from measurement rather than by asking, so each is recorded resolved with its basis. Every reviewed sibling in this Set carried the same inaccurate claim.

### OQ-01: What `command_class` does each leaf declare, given `analyze` mutates on a read-only noun?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as `query` = `read` and `analyze` = `mutation`, with the noun's own description corrected. `aw runs` is documented as "the READING half of the run surface ... Read-only, except the opt-in `repair` verb", and `analyze` updates a cache and publishes a bundle, so it is genuinely the second exception. The class is not cosmetic: `tests/conformance_matrix.required_scenarios` derives the required scenario set from it, so a `mutation` leaf must cover `success_preview` while a `read` leaf whose contract includes 1 must cover `domain_failure`. REJECTED: declaring `analyze` as `read` to avoid touching the description, because it would be a false declaration in the normative inventory and would demand the wrong scenario coverage. Moving `analyze` to the WRITING noun `aw run`, rejected because the maintainer-visible contract the plan was asked to build is `aw runs analyze` and `aw run` is the ledger-transaction noun (`start`/`record`/`cancel`/`finalize`), where an analytics build does not belong. Routing it positionally like `repair` to dodge declaration, rejected on the routing action's own recorded grounds: a positionally-routed leaf is invisible to `discover_parser_leaves`, gets no argparse help, and declaring it would register as drift.

### OQ-02: Does `query` define a new protocol, or emit the existing envelope?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as the EXISTING `aw.agent/v1` envelope with a `data` payload, bounded by default. Measured: `agent_schema.SCHEMA_VERSION` is `aw.agent/v1`, `RECORD_KINDS` is the closed set `('result','summary','item','error')`, `VALID_OUTCOMES` is a closed 13-value set, `validate_agent_record` enforces kind-specific mandatory fields plus anti-greenwashing rules, and `filter_record_fields` already implements bounded projection preserving mandatory fields. So the "versioned query protocol" the plan describes is this envelope, already versioned. REJECTED: a parallel schema with its own version, because two envelopes drift and every agent consumer would need to detect which it received. Raising `BYTE_BUDGET`/`TOKEN_BUDGET` so a distributions view fits, rejected because the budget exists precisely to stop a machine convention bloating, and the correct fix is a bounded default limit with pagination. Adding a `VALID_OUTCOMES` value for a refused slice without discussion, rejected because that set is a cross-cutting contract; `cannot-run` is the closest existing fit and a genuine gap is a maintainer question, not a silent addition.

### OQ-03: How is the leaf-name collision behavior tested, given nothing in the tree collides?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as a PURPOSE-BUILT fixture plus a dispatch-level assertion. Measured: zero of 78 run-corpus setids, 345 run/id6 tokens and 639 tracked plan setids and id6s collide with any leaf name existing or proposed, and `aw runs -- analyze` today prints `no matching runs found` and exits 0, so the authored assertion passes before any code is written. Also measured: `_dispatch` handles `--` pre-parse, forces `runs_command = None` and hardcodes `run_viewer.run_viewer_cli`, so an escaped token structurally cannot reach a leaf; that half is a code property to assert directly rather than a behavior to observe. REJECTED: asserting against the real corpus, because nothing in it collides so the test is vacuous. Asserting via `aw runs -- status`, rejected because that command returns ALL 135 runs (the setid fallback greps raw `state.json` text and `status` is a JSON key), so a test built on it would pin a bug as expected behavior. Fixing that bug here, rejected as out of scope: it is `run_viewer` target resolution adjacent to Order 01's discovery work, and changing it would alter what every existing viewer invocation matches.

### OQ-04: Does registering two leaves amend the implemented CLI grammar spec?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as NO, with the reasoning recorded because the authored text left it as a discovery. `.aw/records/specs/20260818-1525-01-command-surface-redesign.spec.md` exists, is `Status: implemented`, and its Section 3 is normative, so the plan's "if the repository maintains a controlling CLI grammar spec" is answered rather than open. That spec governs the noun-verb SHAPE, the closed TYPE-noun set and the seven cross-cutting verbs; the leaf census under an existing noun is not part of its normative grammar, and its R4 (documented exit codes, `--json`/`--agent`) is a requirement this plan SATISFIES rather than changes. REJECTED: amending the spec to enumerate the new leaves, because it does not enumerate the existing nine either, and editing an implemented spec to record a conformant addition would make every future leaf a spec change. Leaving the question conditional, rejected because an executor discovering an implemented spec mid-run would plausibly edit it, which the fence now forbids. NOTE the one genuine escalation: if a mutating leaf on the reading noun is judged a grammar violation rather than a documented exception, that IS a maintainer question and a STOP-and-raise.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both `CommandDeclaration`s with their chosen `command_class`, `human_recipe`, `agent_record_kind`, `mutation_gate` and `exit_contract`. Paste `find_undeclared_leaves` output showing the SAME five pre-existing `oc profile *` entries and no new one (re-measure; five at review). Paste the EXPLICIT run of `tests/test_cli_conformance_matrix.py` (it is `pytest.mark.slow` and the bare suite deselects it, so a bare green run is NOT evidence) showing a full required scenario row set for both new leaves.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `discover_parser_leaves` output containing `runs analyze` and `runs query` as real leaves. Paste the updated `_RUNS_DESCRIPTION` and `runs` help epilog showing the read-only claim now names both exceptions. Paste goldens proving the nine existing leaves and the bare viewer route byte-identically. Paste proof no positional routing was added (a grep for the `repair` pattern is acceptable).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste each flag exercised with its documented precedence and exit code, including the incompatible-flag cases. Paste the reconciliation between the declared `exit_contract` and `validate_agent_record`'s `(0,1,2)` requirement, naming which codes appear in an agent record and which only as a process exit. Paste proof every path came from Order 01's resolver (a grep showing no `.aw/records/runs` literal was added).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the injectable launch seam and a test where the stub RAISES if invoked, showing analysis without `--open` passes. Paste the supported, unsupported and launch-failure paths with their exit codes and remedy strings. State that no browser-launch precedent existed in the package before this item, so the seam is new rather than reused.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste each view returning results over an allowlisted filter/group schema. Paste a rejected filter naming the allowlist rather than echoing input, and a rejected path outside the resolved roots. Paste a slice Order 06 REFUSED returning that refusal with its observed n rather than a computed number, and paste the `--group-by model` case rendering an honest empty state at Order 06's measured 1.1 percent identity coverage.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `validate_agent_record` passing for every view's record. Paste the measured byte and approximate-token size of the LARGEST default record against the enforced 1200 / 400 budget, and paste a `distributions` view over a corpus-scale fixture (about 30000 rows) staying bounded, with pagination visible rather than silent truncation. Paste `--fields` projection reusing `filter_record_fields`. Paste the explicit `tests/test_cli_quality_gates.py` run.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the PURPOSE-BUILT fixture named `analyze` (and one named `query`) and show the bare form reaching the LEAF while the `--` form reaches the VIEWER. Paste the pre-change behavior (`aw runs -- analyze` -> `no matching runs found`, exit 0 at review) proving the test distinguishes fixed from unfixed rather than passing vacuously. Paste the dispatch-level assertion that `runs_command` is forced to `None` on the escape path. Paste the measured `"status"` key-collision result (135 runs at review) as a REPORTED observation with a statement that no test depends on it.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste each failure class (malformed filter, missing corpus, corrupt cache, partial analysis, open failure, unsupported schema) with its exit code AND its remedy string. Paste analyze-twice cache reuse and a selective rebuild after mutating one fixture. State explicitly whether the docs-snippet executability claim was IMPLEMENTED as a harness or DOWNGRADED to documentation review, since no such mechanism exists today; an implied claim is a failed validation.
  - Observed evidence:
  - Result: pending

Additionally, and NOT as a separate V-item because it validates no single E-item: V-08 must also carry bare `python3 -m pytest` and `git diff --check` from the executing worktree, PLUS the explicit conformance invocation (`tests/test_cli_conformance_matrix.py tests/test_cli_quality_gates.py tests/test_cli_output_docs_rollout.py`), against the baseline the executor measured itself, comparing failing NODE IDS and never totals.

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: both leaves share the routing-sensitive command surface and the same agent schema, so one owner must prevent grammar drift. NOTE THE SCOPE OF THAT ARGUMENT: it justifies ONE PLAN, not one ITEM. The shared surface is real, which is why the two leaves belong together; that does not make the declaration contract, the parser registration, the analyze flags, the launch seam, the query grammar, the envelope conformance, the routing matrix and the failure semantics one deliverable, which is why the eight items exist (F-8).

EXECUTION CONTRACT. This plan requires explicit human approval (`aw ipd set approved mm5p3v --by-human --message ...`), and its `Item-Dependencies` refuse dispatch until `6eq3oq` (Order 07) is `executed`. That dependency is load-bearing: Order 07 owns the bundle layout and companion schemas this command publishes and queries, and Order 06 (`aflsz3`) beneath it decides which analyses exist and which are refused. Order 09 (`ixis0c`) depends on this plan and Order 10 (`9xycbh`) documents it, so the command grammar, the exit contracts and the record shapes are CONTRACTS, not internal details.

- Commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index you never staged. `cli.py` and `command_surface.py` are high-traffic shared files and other agents work concurrently in this checkout; if either is being changed under you and the changes cannot be safely combined, STOP and report rather than overwriting.
- THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT. Never fill an `Observed evidence:` field from memory or from a matching execution checkmark. THIS PLAN HAS A SPECIFIC TRAP: the bare suite DESELECTS `tests/test_cli_conformance_matrix.py` (it is `pytest.mark.slow`), so a green bare run does NOT show your leaves are declared and covered. Paste BOTH the bare run and the explicit conformance run.
- RE-MEASURE EVERY NUMBER IN THIS PLAN. Every figure (129 declarations, 124 parser leaves, the five `oc profile *` undeclared entries, the 1200/400 budget, the eight above-2 exit contracts, 135 runs matched by `status`, zero collisions across 78/345/639 tokens) is a review-time snapshot of a tree that grows. Re-derive them; do not cite them as current.
- RE-LOCATE EVERY CITED SYMBOL BY NAME, not by line number.
- Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

Preserve fixed grammar: configuration and data may never manufacture top-level or leaf commands. FIVE STOP CONDITIONS. If a bare suite is green and you are about to report the leaves conformant, STOP: the gate that proves it is `slow`-marked and was not run. If you find yourself routing a leaf positionally to avoid a declaration, STOP: the routing action's own docstring records that this makes the leaf undeclarable and help-less. If you find yourself raising `BYTE_BUDGET`, adding a `VALID_OUTCOMES` value, or minting a second agent schema version, STOP: bound the view instead, and a genuine schema gap is a maintainer question. If you find yourself fixing the five `oc profile *` declarations or the `"status"` resolution bug, STOP: both are pre-existing, out of scope, and their baselines are what make a new regression attributable. And if you conclude the implemented grammar spec must be amended, STOP and raise it rather than editing an implemented spec.
