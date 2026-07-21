# IPD: per-workflow argument hint in generated command shims (fix the generic/empty $ARGUMENTS line)

- Date: 2026-07-21
- Concern: installer/shim UX (the generated slash-command body) across ALL workflows
- Scope: `agent_workflows/engine.py` (the `Workflow` dataclass, `parse_manifest`, and the shim body/frontmatter renderer), `.agents/workflows/index.md` (an optional new manifest column), and `tests/` (shim-generation coverage). Product code + manifest; behavior-preserving for workflows that add no hint.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after the maintainer observed that running `/whatnext` (no argument) in OpenCode shows a dangling generic line: "If the user provided arguments, treat them as the target path(s) and/or flags for this workflow:" with nothing after it and no hint of what a focus argument does. This text is injected by engine.py for EVERY command, so it cannot be fixed from a single workflow file.

## Goal

Let each workflow declare a SHORT, workflow-specific argument hint that the installer renders into the generated command shim (both OpenCode and Claude), replacing the generic "target path(s) and/or flags" wording, and OMIT the arguments line entirely for workflows that take no arguments. This fixes the dangling/empty and uninformative `$ARGUMENTS` line the maintainer saw, for all commands at once.

Why it matters: the shim is what the user actually reads when they invoke a slash command. Today it (1) shows a generic line even for commands whose arguments mean something specific (e.g. /whatnext's focus filter, /list-workflows' filter, /assess's concern), and (2) shows a confusing empty trailing colon when no argument is given. A per-workflow hint makes the shim self-documenting (assess-self-documentation), and dropping the line for no-arg workflows removes noise.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P9 design instructions for the model; self-documenting; KISS). No em/en dashes.
- Shim generation (verified): `agent_workflows/engine.py` renders the body at `:472-479` with the fixed line `"If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS"`; Claude frontmatter carries a generic `argument-hint: "[optional target path or flags]"` (`:464`), OpenCode carries `agent: build` (`:469`). `$ARGUMENTS` is the substitution token both tools expand.
- Manifest parsing (verified): `parse_manifest` (`:326-366`) already accepts BOTH 3-column (`command|body|description`) and 4-column (`command|body|lens|description`) rows (`:352-364`). The `Workflow` dataclass (`:178-184`) has `command/body/description/lens=""`. Adding an OPTIONAL trailing column + an optional dataclass field is backward-compatible with every existing row.
- The manifest header comment (`index.md:20`) says "Keep the columns stable: `command | body | lens | description`" - this IPD updates that documented contract to add the optional 5th column.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| A1 | MEDIUM | Low | novice / power user | self-documentation | The shim's argument line is generic ("target path(s) and/or flags") for every command and gives no idea what a specific command's argument does. | `engine.py:476-477` |
| A2 | LOW | Low | any user | UX noise | With no argument, the shim shows a trailing "... for this workflow:" with an empty value; for commands that take NO argument, the line should not appear at all. | `engine.py:476-477` (unconditional) |
| A3 | LOW | Low | maintainer | consistency | Claude's `argument-hint` frontmatter (`:464`) is also generic and unrelated to the actual command. It should reflect the same per-workflow hint (or a neutral default). | `engine.py:464` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | A1 | Add an OPTIONAL `arg_hint: str = ""` field to the `Workflow` dataclass. | `agent_workflows/engine.py:178-184` | Low | dataclass accepts a hint; default empty; existing constructions unaffected |
| 2 | A1 | Extend `parse_manifest` to read an OPTIONAL 5th column (`command|body|lens|description|arg-hint`), keeping 3- and 4-column rows working exactly as today. An empty/absent 5th cell -> `arg_hint=""`. | `engine.py:326-366` | Low | 3/4/5-column rows all parse; 5th cell maps to arg_hint; missing = "" |
| 3 | A1,A2 | In the shim BODY renderer: if `workflow.arg_hint` is non-empty, render "If the user provided arguments, <arg_hint>: $ARGUMENTS"; if it is empty, render a neutral fallback that still explains $ARGUMENTS OR (decide at review, OQ1) OMIT the arguments line entirely for no-arg workflows. Recommended: emit the hint line when arg_hint is set; when unset, keep a single generic line for backward-compat (so no existing behavior regresses) UNLESS a workflow opts out with an explicit `arg-hint: none` sentinel that drops the line. | `engine.py:472-479` | Low | hint present -> specific line; sentinel `none` -> no arguments line; unset -> current generic line (no regression) |
| 4 | A3 | Claude frontmatter `argument-hint` uses the workflow's `arg_hint` when set (rendered as `"[<arg_hint-derived>]"`), else the current neutral default; `none` -> omit or empty. Keep OpenCode frontmatter unchanged (`agent: build`). | `engine.py:460-470` | Low | Claude shim shows the per-workflow hint; OpenCode unchanged |
| 5 | A1 | Populate `arg-hint` for the commands whose arguments mean something, starting with the ones the maintainer hit: `whatnext` ("optional focus filter: a concern, area, or path to narrow the survey, e.g. security or release; omit to survey everything"), `list-workflows`, `assess`, `advise`, `handoff`. Set `arg-hint: none` for genuinely no-argument commands (decide the set at execution). Update the `index.md` manifest header comment to document the optional column. | `.agents/workflows/index.md` | Low | the named rows carry hints; the shim for /whatnext now reads the focus-filter hint instead of the generic line |
| 6 | - | Docs/decision sync: a DECISIONS entry (pin at execution) for the per-workflow arg-hint manifest column + shim contract; CHANGELOG 1.3.0 note. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; links resolve; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Reason | Where |
|------|--------|-------|
| The /whatnext BEHAVIOR changes (chat-history, todowrite, 1-3 cap, save-to-TODO) | Different concern (workflow prose, not the installer). | IPD 20260721-1754-01 |
| Re-generating shims into already-installed target repos | The installer regenerates shims on the next `aw install`; this IPD changes the generator only. Targets pick it up on reinstall. | n/a (documented, not automated here) |

## Scope check

- Over-scope: none. The dataclass field + parser column + renderer branch + populating a few hints + docs. No change to what any workflow DOES.
- Under-scope: the change MUST be backward-compatible - every existing 3/4-column manifest row and every current shim (for a workflow with no hint) must render exactly as before unless it opts in. Add a test proving a no-hint workflow's shim is unchanged.

## Required tests / validation

- `tests/` (shim generation - extend the existing engine/installer tests): (a) a 5-column row parses and sets `arg_hint`; (b) 3- and 4-column rows still parse with `arg_hint=""`; (c) a workflow WITH a hint renders the specific line (and Claude `argument-hint`) in both tool shims; (d) a workflow with `arg-hint: none` renders NO arguments line; (e) a workflow with no hint renders the current generic line unchanged (no regression); (f) OpenCode frontmatter still `agent: build`.
- `python -m pytest -q` GREEN; paste ACTUAL output (baseline this session 310 passed, 1 skipped; expect additions).
- `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- `index.md` manifest header comment (the documented column contract), the populated rows, DECISIONS (the new column + shim contract), CHANGELOG 1.3.0.

## Open questions

- OQ1 (no-hint default behavior): when a workflow declares NO arg-hint, should the shim (a) keep today's generic line (safest, zero regression) with an explicit `arg-hint: none` sentinel to DROP the line, or (b) drop the line by default and require an explicit hint to show one? Lean: (a) - keep the generic line for unset (no regression), add a `none` sentinel to drop it, and populate real hints for the arg-taking commands. Confirm at review.
- OQ2 (hint phrasing surface): render the hint as a full clause ("If the user provided arguments, <hint>: $ARGUMENTS") vs a shorter "Arguments: <hint> ($ARGUMENTS)". Lean: the clause form for continuity. Decide at review.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
