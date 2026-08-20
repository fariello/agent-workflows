# IPD: single aw slash-command namespace over the workflows

- Date: 2026-08-19
- Kind: child
- Concern: Collapse the many per-workflow slash-command shims into a single `/aw <verb>` dispatcher shim per host, keeping the existing per-workflow shims as back-compat aliases and verifying each host's command grammar.
- Scope: `agent_workflows/engine.py` (shim generator), `.aw/system/workflows/index.md` (manifest prose only, no row schema change), generated shims under `.opencode/commands/` and `.claude/commands/`, `tests/test_installer.py`. First slice only: generate the `/aw` dispatcher and keep per-workflow shims as aliases; deeper migration (deprecating or pruning the aliases) is deferred.
- Status: reviewed
- Set: backlog-medhigh-260819
- Order: 5
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ckw2ze

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body drafted from investigation of the real shim generator and host command formats.
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-05-1 size assessment corrected `exception`->`standard` (neither the >18-leaf nor the >5-group threshold is exceeded; 6 leaves / 3 groups), PR-05-2 canonical serial-runner note (E-06). Anchors verified (engine.py:132/573/666/807/821; /assess shim `$ARGUMENTS` dispatch precedent in both hosts). OQ-01/OQ-02 remain non-blocking OPEN (maintainer product decisions on canonical surface + bare `/aw`, deferred to a follow-on). Verdict per open questions: REVIEWED - OPEN QUESTIONS; readiness NO-GO until the maintainer accepts the alias-retention slice at approval.

## Goal

Add a single `/aw <verb> [args]` slash-command dispatcher, generated once per host
(`.opencode/commands/aw.md`, `.claude/commands/aw.md`), that routes to any workflow by verb,
while the existing per-workflow shims continue to be generated as back-compat aliases so no
current invocation breaks. A per-host grammar-verification test asserts that both the new
dispatcher and the aliases are valid for each host's command format.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Dispatcher shim generation

- [ ] E-01 Add an `aw_dispatcher_shim(workflows, tool, target_layout)` helper (or extend `shim_body`) in `agent_workflows/engine.py` that produces the `/aw` dispatcher body: frontmatter valid for the given host (OpenCode `agent: build`; Claude `argument-hint`), a "read the manifest, resolve the first argument as the workflow verb, then read and execute that workflow's body" instruction referencing `.aw/system/workflows/index.md`, and a `$ARGUMENTS` line so the verb plus its remaining args are passed through.
  - Depends on: none
  - Expected outcome: A pure function returns a syntactically valid dispatcher shim string for `tool="opencode"` and `tool="claude"`; the verb is the first token of `$ARGUMENTS`.
  - Execution state: pending

- [ ] E-02 Wire the dispatcher into `generate_shim_members` so one `aw.md` is written per `COMMAND_SHIM_DIRS` entry (`.opencode/commands/aw.md`, `.claude/commands/aw.md`) IN ADDITION to the existing per-workflow shims.
  - Depends on: E-01
  - Expected outcome: `generate_shim_members(...)` returns keys `.opencode/commands/aw.md` and `.claude/commands/aw.md` alongside every existing per-workflow shim key.
  - Execution state: pending

### Task group 2: Back-compat aliases and grammar verification

- [ ] E-03 Confirm the existing per-workflow shims remain generated unchanged (they ARE the back-compat aliases), and add a short manifest-prose note in `.aw/system/workflows/index.md` "Running a workflow (by tool)" describing `/aw <verb>` as the primary surface and the per-workflow `/name` commands as retained aliases. Do not change the manifest column schema or any row.
  - Depends on: E-02
  - Expected outcome: Existing shim keys are byte-identical to before (no alias regression); index.md documents the `/aw` surface and the alias relationship.
  - Execution state: pending

- [ ] E-04 Add a per-host grammar-verification helper the tests will call (a small `validate_shim_grammar(text, tool)` predicate or reuse of the existing `is_stale_shim_customized` / structural checks) that asserts a shim string is well formed for a host: YAML frontmatter fences present, required per-host fields present (`agent:` for opencode, `description:` for both), a body that references a workflow body path, and a `$ARGUMENTS` line when arguments are expected.
  - Depends on: E-01
  - Expected outcome: `validate_shim_grammar(dispatcher, "opencode")` and `(..., "claude")` return true for the generated dispatcher and for a sample per-workflow alias; malformed input returns false.
  - Execution state: pending

### Task group 3: Tests and closeout

- [ ] E-05 Add `tests/test_command_shims.py` with cases asserting: (a) `generate_shim_members` emits `.opencode/commands/aw.md` and `.claude/commands/aw.md`; (b) the existing per-workflow shims (aliases) are still emitted (e.g. `assess.md`, `handoff.md`, `verify.md`) with unchanged content; (c) the dispatcher passes `validate_shim_grammar` for BOTH hosts; (d) the dispatcher body carries a `$ARGUMENTS` passthrough and references the manifest.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: New test module passes and fails if any of the four assertions regress.
  - Execution state: pending

- [ ] E-06 Run the full serial test suite (canonical `make test-serial` / `python3 -m unittest discover -s tests -t .`; `python3 -m pytest -p no:xdist` is equivalent only with the `.[test]` extra), capture the runner output, and close backlog item q19z5t to done only if the executed slice satisfies the item (single `/aw` namespace generated per host + back-compat aliases retained + per-host grammar verified); otherwise leave a note that a follow-on Order is needed for alias deprecation/pruning.
  - Depends on: E-05
  - Expected outcome: Full suite green with pasted output; q19z5t moved to done (or annotated with the follow-on note) via `aw backlog set`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Slash-command shims are GENERATED, never hand-maintained, from the manifest table in `.aw/system/workflows/index.md` (`agent_workflows/engine.py:24`, index.md:19-27).
- The two host shim directories are declared in one place: `COMMAND_SHIM_DIRS = (".opencode/commands", ".claude/commands")` (`agent_workflows/engine.py:132-135`).
- Shim content is built by `shim_body(command, workflow, tool, target_layout)` (`agent_workflows/engine.py:666`) and mapped to paths by `generate_shim_members(...)` (`agent_workflows/engine.py:821`), which writes one shim per non-catalog row plus a per-dir README.
- Per-host frontmatter already differs and is handled by `tool`: OpenCode emits `agent: build`; Claude emits `argument-hint` (`agent_workflows/engine.py:739-767`).
- Argument passthrough is already `$ARGUMENTS` for both hosts (`agent_workflows/engine.py:769-777`).
- Parameterized verb-dispatch is ALREADY proven: `/assess <concern>` and `/advise <persona>` collapse a whole catalog into one arg-dispatched shim (`agent_workflows/engine.py:691-725`, `is_concern_catalog_row` at `:807`), and the emitted files show it working in both hosts (`.opencode/commands/assess.md:10`, `.claude/commands/assess.md:10`).
- Installer shim tests live in `tests/test_installer.py` (e.g. `test_shim_generation_collapses_catalog` at line 145, `ArgHintShimTests` at line 50); the new test module mirrors these.
- No em/en dashes in user-facing prose (AGENTS.md contract).

## Findings

| # | Question | Finding | Evidence |
|---|---|---|---|
| 1 | Where do the per-workflow shims live and how are they generated? | Generated from the manifest into `.opencode/commands/` and `.claude/commands/`; one file per non-catalog manifest row. | `agent_workflows/engine.py:132-135`, `:821-856`; `.claude/commands/` listing (22 files), `.opencode/commands/` listing (same set) |
| 2 | How does each host invoke a slash command? | OpenCode reads `.opencode/commands/<name>.md`; Claude reads `.claude/commands/<name>.md`. Both are markdown with YAML frontmatter and a body that says "read and execute" the workflow body. | index.md:100-101, `agent_workflows/engine.py:739-791` |
| 3 | Is a single `/aw <verb>` arg-dispatch expressible in EACH host? | Yes, in BOTH. The existing `/assess <concern>` and `/advise <persona>` shims already dispatch on the first argument via `$ARGUMENTS` in both `.opencode/commands/assess.md` and `.claude/commands/assess.md`. A `/aw` shim is the same pattern generalized to route by verb into the manifest. | `.opencode/commands/assess.md:8-10`, `.claude/commands/assess.md:8-10`, `agent_workflows/engine.py:691-725,769-777` |
| 4 | How can back-compat aliases coexist? | The existing per-workflow shims are already generated per row; keeping that loop unchanged and ADDING one `aw.md` per host means the aliases coexist for free during transition. No row schema change is required. | `agent_workflows/engine.py:846-856` |
| 5 | Is this genuinely a first slice of a larger item? | Yes. The full item implies eventually deprecating/pruning per-workflow shims and picking the canonical surface. This slice adds the dispatcher and keeps aliases; deprecation/pruning is deferred. | Backlog q19z5t Summary |

Feasibility verdict: `/aw <verb>` argument dispatch IS expressible in both OpenCode and Claude
Code, because both already ship an argument-dispatched shim (`/assess`, `/advise`) using the
identical `$ARGUMENTS` mechanism. Nothing in either host grammar blocks it.

## Proposed changes (ordered, validatable)

1. Add a dispatcher-shim generator (E-01) that emits a host-valid `/aw` body routing the first argument as a workflow verb into `.aw/system/workflows/index.md`.
2. Emit `aw.md` per host from `generate_shim_members` while keeping every existing per-workflow shim (E-02).
3. Retain the per-workflow shims as back-compat aliases and document the new surface in index.md prose (E-03).
4. Add a per-host grammar-verification predicate (E-04).
5. Add `tests/test_command_shims.py` asserting dispatcher generation, alias retention, per-host grammar validity, and `$ARGUMENTS` passthrough (E-05).
6. Run the full serial suite and close q19z5t (E-06).

## Deferred / out of scope (with reason)

- Deprecating, hiding, or pruning the per-workflow alias shims: deferred to a follow-on Order. Removing them is a behavior change that needs a maintainer decision on the canonical surface and a deprecation window; this slice only ADDS the dispatcher and keeps aliases.
- A verb catalog/help mode for `/aw` (e.g. bare `/aw` listing all verbs): reasonable next step but not required for the first slice; the dispatcher can defer to the manifest and `/list-workflows` for now.
- Changing the manifest column schema or introducing a per-row "namespace" flag: not needed; the dispatcher reads the existing manifest at runtime.
- Runtime behavioral end-to-end tests that actually launch OpenCode/Claude and invoke `/aw`: out of scope (no host runtime in CI); grammar verification is static.

## Scope check

- Over-scope: none. Alias deprecation and a verb-help mode are explicitly deferred, not attempted here.
- Under-scope: This slice does not pick a single canonical surface (dispatcher vs aliases); that is a deliberate deferral captured in OQ-01 and the deferred section, and does not block delivering a working `/aw` dispatcher with aliases retained.

## Required tests / validation

- New `tests/test_command_shims.py` asserting: `.opencode/commands/aw.md` and `.claude/commands/aw.md` are generated; existing per-workflow alias shims are still generated with unchanged content; the dispatcher passes `validate_shim_grammar` for both hosts; the dispatcher body contains a `$ARGUMENTS` passthrough and references the manifest.
- Full serial test suite (the repo's real runner) must pass with pasted output before transition.

## Spec / documentation sync

- Update `.aw/system/workflows/index.md` "Running a workflow (by tool)" prose (E-03) to describe `/aw <verb>` as the primary surface with per-workflow `/name` commands retained as aliases. No manifest row/schema change.
- No dedicated spec exists for the shim generator; the generated shim READMEs are auto-managed and need no manual edit.

## Open questions

### OQ-01: Which surface becomes canonical, and do the per-workflow aliases get deprecated later?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: This slice keeps both the `/aw` dispatcher and the per-workflow aliases so nothing breaks. Whether to eventually deprecate/prune the aliases (and on what timeline) is a maintainer product decision, captured for a follow-on Order, now filed as backlog awslashdeprecate-01 (21ni81: add a deprecation warning to the per-workflow aliases). It does not block delivering the dispatcher.

### OQ-02: Should bare `/aw` (no verb) list the available verbs or route to getting-started?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: The first slice can have the dispatcher instruct the agent to consult the manifest / `/list-workflows` when no verb is given. A dedicated in-shim verb listing is a nice-to-have deferred to the follow-on.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: A test or REPL call showing `aw_dispatcher_shim(...)` returns a string with valid frontmatter fences and a `$ARGUMENTS` line for both `tool="opencode"` (contains `agent: build`) and `tool="claude"` (contains `argument-hint`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Assertion output showing `generate_shim_members(parse_manifest(source), source)` contains keys `.opencode/commands/aw.md` and `.claude/commands/aw.md` while still containing the existing per-workflow shim keys.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Diff/assertion showing the per-workflow alias shim contents are unchanged from before this change, and an index.md diff adding the `/aw` surface note.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Test output showing `validate_shim_grammar(dispatcher, tool)` is true for both hosts and false for a deliberately malformed shim string.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `tests/test_command_shims.py` run output showing all four assertions pass.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted full serial suite output (green) and the `aw backlog set q19z5t --status done` result (or the follow-on note if only partially satisfiable).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is authoring-only and must not be executed until it carries an explicit human
`approved` status. On execution, the executor commits ONLY the files it changes, path-scoped,
never `git add -A` and never pushing, and pastes the ACTUAL runner output before claiming tests
pass. Completion requires `aw ipd lint --phase pre-transition` conforming and every `V-*` item
verified with concrete evidence; only then is the terminal transition (workflow-history line,
terminal `Status: executed`, `git mv` to `.aw/records/plans/executed/`, path-scoped lifecycle
commit) performed as a post-gate step. No tag, release, or registry upload is part of this plan.
