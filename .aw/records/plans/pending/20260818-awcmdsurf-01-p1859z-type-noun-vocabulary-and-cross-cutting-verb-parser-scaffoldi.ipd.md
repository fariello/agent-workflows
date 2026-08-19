# IPD: type-noun vocabulary and cross-cutting verb parser scaffolding

- Date: 2026-08-18
- Kind: child
- Concern: awcmdsurf Order 01 (spec 20260818-1525-01). Lay the foundation for the noun-verb grammar: a single shared TYPE-noun vocabulary + a type->backend resolver, and the top-level argparse scaffolding for six cross-cutting verbs (`check`/`find`/`search`/`index`/`rename`/`group`), each dispatching to a thin router (the seventh verb `archive` is stood up by Order 03, which owns it, to avoid breaking the existing `aw archive` signature mid-Set). Added ALONGSIDE the existing verbs (nothing removed here) so every intermediate state stays runnable; removal is Order 05.
- Scope: agent_workflows/cli.py (new parsers + dispatch) + a new small module for the type vocabulary. IN: the TYPE-noun constant + singular aliases + a resolver mapping each type to its backend module/callable; six new verb subparsers (`check`/`find`/`search`/`index`/`rename`/`group`; `archive` deferred to Order 03) (parsers + thin routers that currently delegate to the existing backends or a not-yet-wired stub for engine-dependent parts); a shared `--json`/`--agent` convention helper; tests. OUT: the actual read-verb behavior (Order 02), mutation-verb behavior (Order 03), the ipd merge (Order 04), removals (Order 05), the check ENGINE (Set D awcheck) and the full selector parser (Set E awselect).
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awcmdsurf
- Order: 1
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: p1859z

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from spec 20260818-1525-01 + cli.py investigation (flat dispatch chain cli.py:4018-4241; backend module map).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against cli.py:369-1747, cli.py:1600, plans_refs.py:33, and artifact_core.py:255-262; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED; re-review (opencode): PR-001 fixed - Order 01 no longer stands up `archive` (would break `aw archive <id6>` mid-Set); defers archive parser to Order 03; six verbs here. Conforming.
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. Empirically confirmed the six new verb names (check/find/search/index/rename/group) are collision-free top-level (all `invalid choice` today; only archive collides, already deferred). PR-001 (this pass, LOW-MEDIUM): `TYPE_BACKENDS` was described as a "pure data map" that "names" functions, ambiguous enough that an executor could store function OBJECTS - forcing eager backend imports and the exact cycles the map avoids; made E-02 explicit that the values are DOTTED-NAME STRINGS resolved lazily by the router, and that importing artifact_types must import no backend. Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.

## Goal

Introduce the shared vocabulary and parser skeleton the whole redesign builds on: one closed TYPE-noun
set with singular aliases, a resolver that maps a type to its backend, and six cross-cutting verb
subparsers wired to thin routers (`archive` is added by Order 03). This Order adds surface WITHOUT removing anything, so the CLI stays
fully runnable and the suite stays green; later Orders fill in behavior and Order 05 removes the old
verbs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: the type vocabulary + resolver

- [ ] E-01 Create `agent_workflows/artifact_types.py` defining the closed TYPE-noun vocabulary and normalization: a tuple `ARTIFACT_TYPES = ("plans", "specs", "prompts", "research", "backlog", "walkthroughs", "roadmaps", "comms")`; a `normalize_type(token)` that accepts the plural, the singular alias (`plan`->`plans`, `spec`->`specs`, `prompt`->`prompts`, `walkthrough`->`walkthroughs`, `roadmap`->`roadmaps`, `comm`/`comms`->`comms`, `research`->`research`, `backlog`->`backlog`), and `all`, returning the canonical plural or `all`, or raising a `ValueError` with a clear message listing valid types for an unknown token; and `expand_types(token)` returning the concrete list a verb should act on (`all` -> every type that verb supports, given a supported-subset argument).
  - Depends on: none
  - Expected outcome: `normalize_type("plan")=="plans"`, `normalize_type("all")=="all"`, `normalize_type("bogus")` raises ValueError mentioning the valid set; `expand_types("all", supported=("plans","specs"))==["plans","specs"]`.
  - Execution state: pending
- [ ] E-02 In `artifact_types.py`, add a `TYPE_BACKENDS` mapping from each type+verb to a DOTTED-NAME STRING (e.g. the literal string `"plans_refs.run_mv"`), NOT a function object - storing the callable would force an eager `import` at module load and reintroduce the import cycles this map exists to avoid. The router resolves a string to a callable lazily at dispatch time (e.g. `mod, attr = value.rsplit(".",1); getattr(importlib.import_module("agent_workflows."+mod), attr)`). Contents, grounded in the investigation: plans -> {index: `"plans_index.run_index"`, find: `"plans_index.run_find"`, rename: `"plans_refs.run_mv"`, group: `"plans_refs.run_set_assign"`, archive: `"plans_archive.run_archive"`}; research -> {index: `"research_index.run_index"`, find: `"research_index.run_find"`, rename: `"research_refs.run_mv"`, group: `"research_refs.run_set_assign"`, archive: `"research_archive.run_archive"`}; specs -> {check: `"specs.run_check"`}; backlog -> {check: `"backlog.run_check"`}. A missing type/verb key resolves to None (the router reports "not supported for <type>" with exit 2). This module must import NONE of those backend modules at load time.
  - Depends on: E-01
  - Expected outcome: `TYPE_BACKENDS["plans"]["rename"] == "plans_refs.run_mv"` (a STRING); an unsupported (type, verb) pair yields None; importing `artifact_types` does NOT import plans_refs/plans_index/etc. (verify e.g. via `sys.modules` before/after).
  - Execution state: pending

### Task group 2: shared machine-output + exit-code convention

- [ ] E-03 Add a small shared helper (in `artifact_types.py` or a new `cli_common.py`) codifying the spec's exit-code convention (0 ok / 1 findings / 2 cannot-run) and a `--json`/`--agent` flag pair added uniformly to the new verb parsers. Reuse the existing `artifact_core.drift_exit_code` (artifact_core.py:262) and `render_agent_drift` (artifact_core.py:255) so the new verbs match the established `Drift` convention rather than inventing a second one.
  - Depends on: none
  - Expected outcome: a helper that, given a verb result, returns the correct exit code and can emit `--json` or `--agent` output consistently; unit-tested for the three exit codes.
  - Execution state: pending

### Task group 3: the six verb parsers + thin routers

- [ ] E-04 In `agent_workflows/cli.py` `_build_parser` (cli.py:369-1747), register SIX NEW top-level subparsers - `check`, `find`, `search`, `index`, `rename`, `group` - each taking a positional `type` (validated via `artifact_types.normalize_type`), the verb-appropriate selectors/flags (a minimal `selector` positional `nargs="*"` for now; the full selector grammar is Set E awselect), and the shared `--json`/`--agent`. DO NOT touch the existing top-level `archive` verb in this Order: it currently has a `target` positional (cli.py:1600, research-only) and generalizing it to a `type`-first signature would BREAK `aw archive <id6>` for the whole window between this Order and Order 03. The `archive` verb is generalized by Order 03 (awcmdsurf-03), which owns archive and can flip its signature + wire `aw archive research`/`aw archive plans` in one atomic step. Add each of the six new verbs to the dispatch chain (cli.py:4018-4241) routing to a thin `_run_<verb>(args, term)` that resolves the backend via `TYPE_BACKENDS` and either delegates (where a backend exists) or prints "not yet wired / not supported for <type>" (exit 2) for the parts later Orders fill.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: `aw check --help`, `aw find --help`, `aw search --help`, `aw index --help`, `aw rename --help`, `aw group --help` all parse; each rejects an unknown type with a clear error; the existing `aw archive <id6>` research path is UNCHANGED (still works exactly as before, because `archive` is not modified in this Order).
  - Execution state: pending
- [ ] E-05 Add `tests/test_awcmdsurf_vocab_and_parsers.py` covering: `normalize_type`/`expand_types` (happy + unknown + `all`), `TYPE_BACKENDS` lookups (supported + None), the exit-code helper (0/1/2), and that each of the six new verbs parses `--help` and errors on an unknown type. Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail (the new parsers must not break existing dispatch).
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: the new module passes; full serial suite green (existing verbs unaffected; new verbs added alongside).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The CLI is a single-file argparse tree: `_build_parser` (cli.py:369-1747), a FLAT `if args.command == ...` dispatch chain (cli.py:4018-4241), `main` (cli.py:4244).
- A top-level `archive` verb already exists but is RESEARCH-only (cli.py:1600 -> research_archive.run_archive); the new grammar generalizes it, so Order 01 must not break the existing path.
- Two alias mechanisms exist: native argparse `aliases=` (only `attention`/`att` cli.py:1363, `check-local-leaks`/`sanitize` cli.py:1687) and a pre-parse argv rewrite for `plans <verb>` (cli.py:4023-4031). The redesign removes the argv shim in Order 05.
- Backends are imported LAZILY inside the dispatch chain today; keep that pattern (routers do the import) to avoid cycles.
- The `Drift`/`drift_exit_code`/`render_agent_drift` convention (artifact_core.py:247-266) is the established machine-output contract; reuse it, do not invent a second.
- `.type.md` facets + `ARTIFACT_TYPE_FACETS` (plans_refs.py:33) already exist; the TYPE-noun vocabulary is the CLI-facing sibling (nouns, not facets) - keep them consistent but distinct (a facet is a filename token; a type-noun is a CLI argument).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Single-file flat dispatch. | New verbs are added as more `if args.command ==` blocks; low risk, no framework change. |
| F2 | `archive` already taken (research, `target` positional cli.py:1600). | Order 01 does NOT touch `archive` (that would break `aw archive <id6>` mid-Set); Order 03 owns generalizing it atomically. |
| F3 | Backends already exist + are lazily imported. | Routers delegate; no backend rewrite. `TYPE_BACKENDS` is a pure data map of DOTTED-NAME STRINGS (not function objects), resolved lazily by the router, so importing artifact_types imports no backend and no cycle forms. |
| F5 | The six new verb names (check/find/search/index/rename/group) are collision-free at the top level. | Verified: all six currently `invalid choice`; only `archive` collides (deferred to Order 03). Safe to add as new subparsers. |
| F4 | Selector grammar is a separate Set (E). | Order 01 ships a minimal `selector nargs="*"`; awselect replaces it. Keep the parser shape forward-compatible. |

## Proposed changes (ordered, validatable)

1. New `artifact_types.py`: `ARTIFACT_TYPES`, `normalize_type`, `expand_types`, `TYPE_BACKENDS` (E-01,E-02).
2. Shared exit-code + `--json`/`--agent` helper reusing `drift_exit_code` (E-03).
3. Seven new verb subparsers + thin routers in cli.py, generalizing the existing `archive` (E-04).
4. Test module + full suite (E-05).

## Deferred / out of scope (with reason)

- Read-verb behavior (find/search/index): Order 02.
- Mutation-verb behavior (rename/group/archive): Order 03.
- plans->ipd merge, list-repos, todo alias: Order 04.
- Removing old verbs + the argv shim: Order 05.
- `check` engine internals: Set D (awcheck). Full selector grammar: Set E (awselect).

## Scope check

- Over-scope: none - only vocabulary + parser scaffolding; behavior is later Orders.
- Under-scope: none for THIS layer - it establishes the shared pieces every later Order needs.

## Required tests / validation

`tests/test_awcmdsurf_vocab_and_parsers.py` (E-05) + the full serial suite. Each V-item pins one E.

## Spec / documentation sync

No doc/AGENTS.md change here (the grammar is documented when it is complete, Order 05). Spec
20260818-1525-01 stays draft; advanced by the orchestrator when the Set completes.

## Open questions

### OQ-01: put the shared helper in `artifact_types.py` or a new `cli_common.py`?

- Blocking: no
- Status: open
- Owner: opencode (resolve during execution)
- Resolution or deferral rationale: cosmetic module placement. Recommendation: keep the type vocab in `artifact_types.py` and the exit-code/output helper wherever it reads cleanest (a `cli_common.py` if it grows); either satisfies the E-items. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python snippet showing `normalize_type` for a plural/singular/`all`/unknown and `expand_types("all", supported=...)`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `TYPE_BACKENDS` lookups for a supported (plans,rename) and an unsupported pair (None).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the exit-code helper returning 0/1/2 for the three result cases + a `--json`/`--agent` sample.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `--help` for each of the six new verbs, an unknown-type error, and a run proving the existing `aw archive <id6>` research path is unchanged (archive untouched this Order).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the tail of the full serial suite showing the new module + total pass count with no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification + commits) performs each E,
verifies each V with pasted evidence, commits ONLY changed files path-scoped (never `git add -A`), never
pushes, and moves this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase
pre-transition` conforms and every V-item is `pass`. First Order of the awcmdsurf Set; precedes 02-05.
