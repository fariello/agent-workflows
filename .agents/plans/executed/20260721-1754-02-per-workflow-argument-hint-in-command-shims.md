# IPD: per-workflow argument hint in generated command shims (fix the generic/empty $ARGUMENTS line)

- Date: 2026-07-21
- Concern: installer/shim UX (the generated slash-command body) across ALL workflows
- Scope: `agent_workflows/engine.py` (the `Workflow` dataclass, `parse_manifest`, and the shim body/frontmatter renderer), `.agents/workflows/index.md` (an optional new manifest column), and `tests/` (shim-generation coverage). Product code + manifest; behavior-preserving for workflows that add no hint.
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-07-21, human ("Approved. Go.") after /plan-review (APPROVE WITH REVISIONS APPLIED; A4/PR-001, PR-002, PR-003 fixed; OQ1/OQ2 resolved from evidence).

## Workflow history

- 2026-07-21 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): applied Steps 1-6 in the mandated order. `engine.py`: `Workflow.arg_hint` field (Step 1); `parse_manifest` explicit 5-cell branch before any 5-column row (Step 2, PR-001); `shim_body` arguments-line logic - empty keeps the generic line byte-identical, `none` omits it, else a specific clause - plus Claude `argument-hint` from the hint (Steps 3-4). During execution a related detector needed updating (found by `test_shim_expected_does_not_warn`): the `is_stale_shim_customized` structural allowlist hard-coded the exact generic arguments line + Claude hint, so hinted shims were misflagged as customized; fixed the allowlist to recognize the "If the user provided arguments," and `argument-hint: "[` PREFIXES (in-scope: the renderer change requires the detector to accept the generated lines). Added `ArgHintShimTests` + a real-manifest no-drop guard. `index.md`: header documents the column; hints populated for whatnext/list-workflows/assess/advise/handoff (Step 5). DECISIONS D97 + CHANGELOG (Step 6). Validation: no em/en dashes, `aw check-local-leaks .` clean, `python -m pytest -q` = 316 passed, 1 skipped (was 310; +6). The /whatnext shim now renders the focus-filter clause instead of the generic line (the wart the maintainer reported). Status approved -> executed; moved to `executed/`.
- 2026-07-21 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; A1-A5 (all FIXED). Verified against `engine.py`: `Workflow` dataclass `:178-184`, `parse_manifest` `:346-367` (3/4-cell branches + `else: continue` silent-drop), `shim_body` `:394` (the real renderer name; plan had said `render_command_body`), body/frontmatter `:460-479`; and `tests/test_installer.py:26` (manifest parse) + `:422-434` (the customization-detection fixtures). A4 (MEDIUM, FIXED): flagged the `else: continue` silent-drop trap - a 5-column row lands only via fall-through and vanishes; Step 2 now mandates an explicit 5-cell branch + Step-2-before-Step-5 ordering + a no-drop test. A5/PR-002 (FIXED): corrected the renderer name to `shim_body`. PR-003 (FIXED): the unset-path body must stay byte-identical or `is_shim_customized_vs_expected` spuriously flags every installed shim; added the byte-identical guard + tests. OQ1 resolved from evidence (keep unset byte-identical, `none` sentinel to drop); OQ2 resolved from consistency (clause form). No open questions remain. Readiness: GO - PENDING HUMAN APPROVAL.
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
| A4 | MEDIUM | Low | software engineer | correctness / sequencing | `parse_manifest`'s final branch is `else: continue` (`engine.py:360-361`): a row that is not exactly 3 or 4 cells is SILENTLY dropped and its workflow vanishes with no error. Adding 5-column rows (Step 5) before the parser handles 5 cells (Step 2) would silently delete those workflows. Raised + fixed by plan-review (PR-001): explicit 5-cell branch + Step-2-before-Step-5 ordering + a no-drop test. | `engine.py:360-361` |
| A5 | LOW | Low | maintainer | accuracy / regression | The plan named the renderer `render_command_body`; the actual function is `shim_body` (`engine.py:394`). Also the unset-path body must stay byte-identical or `is_shim_customized_vs_expected` will flag every installed shim as customized. Raised + fixed by plan-review (PR-002 name, PR-003 byte-identical guard). | `engine.py:394`, `:472-479` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | A1 | Add an OPTIONAL `arg_hint: str = ""` field to the `Workflow` dataclass. | `agent_workflows/engine.py:178-184` | Low | dataclass accepts a hint; default empty; existing constructions unaffected |
| 2 | A1 | Extend `parse_manifest` to read an OPTIONAL 5th column (`command|body|lens|description|arg-hint`), keeping 3- and 4-column rows working exactly as today. An empty/absent 5th cell -> `arg_hint=""`. SILENT-DROP TRAP (plan-review PR-001): the current parser's final branch is `else: continue` (`engine.py:360-361`), so ANY row that is not exactly 3 or 4 cells is silently skipped and its workflow VANISHES from the manifest (no error). Therefore this Step MUST land BEFORE Step 5 populates any 5-column row, and the parser must add an explicit `len(cells) == 5` branch (5-cell -> command/body/lens/description/arg_hint). Do not leave a 5-column row parseable only by the fall-through. | `engine.py:326-367` | Low | 3/4/5-column rows all parse; 5th cell maps to arg_hint; missing = ""; NO existing workflow disappears from the parsed set (assert whatnext + list-workflows still present) |
| 3 | A1,A2 | In the shim BODY renderer (the function is `shim_body`, `engine.py:394`; plan-review PR-002 corrected the earlier `render_command_body` name), at the arguments line (`engine.py:476-477`): if `workflow.arg_hint` is non-empty, render "If the user provided arguments, <arg_hint>: $ARGUMENTS"; if it is the `none` sentinel, OMIT the arguments line entirely; if it is unset/empty, keep TODAY's exact generic line for backward-compat (so no existing shim regresses, OQ1 resolved to this). | `engine.py:472-479` | Low | hint present -> specific line; sentinel `none` -> no arguments line; unset -> byte-identical current generic line (no regression) |
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
- Under-scope: the change MUST be backward-compatible - every existing 3/4-column manifest row and every current shim (for a workflow with no hint) must render exactly as before unless it opts in. Add a test proving a no-hint workflow's shim is BYTE-IDENTICAL to today (plan-review PR-003: `is_shim_customized_vs_expected` treats generated == expected as "not customized", so a drift in the unset-path body would spuriously flag every installed shim as customized). Also guard against the silent-drop trap (PR-001): a test asserting no workflow disappears once 5-column rows exist.

## Required tests / validation

- `tests/` (shim generation - extend the existing engine/installer tests, esp. `tests/test_installer.py` around `test_parse_manifest_has_core_and_catalog:26` and `generate_shim_members`): (a) a 5-column row parses and sets `arg_hint`; (b) 3- and 4-column rows still parse with `arg_hint=""`; (c) a workflow WITH a hint renders the specific line (and Claude `argument-hint`) in both tool shims; (d) a workflow with `arg-hint: none` renders NO arguments line; (e) a workflow with no hint renders the current generic line BYTE-IDENTICAL (no regression; PR-003); (f) OpenCode frontmatter still `agent: build`; (g) after 5-column rows are added to the real `index.md`, `parse_manifest` still returns `whatnext` and `list-workflows` (no silent drop; PR-001).
- `python -m pytest -q` GREEN; paste ACTUAL output (baseline this session 310 passed, 1 skipped; expect additions).
- `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- `index.md` manifest header comment (the documented column contract), the populated rows, DECISIONS (the new column + shim contract), CHANGELOG 1.3.0.

## Open questions

- OQ1 (no-hint default behavior): RESOLVED from evidence (plan-review). Option (a): when a workflow declares NO arg-hint, keep TODAY's generic line byte-identical; a workflow drops the line only with an explicit `arg-hint: none` sentinel. This is not merely a preference: `is_shim_customized_vs_expected` treats generated == expected as "not customized" (PR-003), so the unset path MUST stay byte-identical or every installed no-hint shim would be spuriously flagged as customized. Option (b) is rejected on that regression.
- OQ2 (hint phrasing surface): RESOLVED from consistency (plan-review). Use the full clause form "If the user provided arguments, <arg_hint>: $ARGUMENTS", because the unset path is pinned to today's clause ("If the user provided arguments, ... for this workflow: $ARGUMENTS", OQ1/PR-003); a divergent "Arguments: <hint>" shape for the hinted path would be gratuitously inconsistent. `arg_hint` text is authored to slot into that clause (e.g. "narrow the survey to a concern/area/path, e.g. `security`; omit to survey everything").

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
