# IPD: hard cutover remove old verbs and sweep references

- Date: 2026-08-18
- Kind: child
- Concern: awcmdsurf Order 05 (spec 20260818-1525-01, D1 hard cutover). With the new grammar fully in place (Orders 01-04), REMOVE the old verbs and the argv shim, then sweep + update EVERY in-repo reference to a removed verb across shipped docs/workflows/tests. This is the terminal, breaking Order; it runs LAST so all prior intermediate states stayed runnable.
- Scope: cli.py removals + a repo-wide reference sweep. IN: remove parsers + dispatch for `plans`, `plans-mv`, `plans-find`, `plans-index`, `plans-set-assign`, `plans-archive`, `plan-names`, `list`, and the old `todo` action-list behavior superseded by the attention alias; remove the `plans <verb>` argv-rewrite shim (cli.py:4023-4031); update every reference in `.aw/system/workflows/**`, `AGENTS.md`, `RELEASING.md`, `CONTRIBUTING.md`, READMEs, and `tests/**` to the new grammar; advance spec 20260818-1525-01 to implemented (orchestrator does the spec transition). OUT: the behavior of the new verbs (Orders 01-04); the check engine / selector grammar (Sets D/E).
- Status: reviewed
- Set: awcmdsurf
- Order: 5
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1z3byy

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from spec 20260818-1525-01 D1 + investigation (old parsers cli.py:532/545/576/600/619/642/660/1626; argv shim cli.py:4023-4031; dispatch chain 4018-4241).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against cli.py:532-660, cli.py:1626, and cli.py:4023-4031; cutover sequencing and reference sweep completeness sound; structural lint conforming; no findings; no open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE; re-review (opencode): verified removal targets + argv shim 4023-4031; hard-cutover reference sweep is the completeness gate; conforming; no findings.
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. RAN the actual repo-wide enumeration (which prior passes asserted "sound" without running). PR-001 (MEDIUM, UNDER-SCOPE): removed-verb references also live IN `agent_workflows/**/*.py` (docstrings/help/comments: plans_refs.py:8/141, plans.py, plans_index.py, plans_archive.py, attention_contract.py, engine.py, cli.py) - NOT covered by the docs+workflows+tests sweep, so the shipped source would keep advertising dead verbs. Extended E-04 + E-06 to sweep `agent_workflows/**/*.py` user-facing verb strings (excluding kept function names + DECISIONS.md/CHANGELOG.md history). Confirmed the overall sweep is bounded/tractable (a handful of files per target). Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.

## Goal

Complete the hard cutover: delete the old verbs + argv shim now that the new grammar covers every
operation, and update every in-repo reference so no removed verb survives anywhere. After this Order,
`aw plans-mv`/`aw plan-names`/`aw plans`/`aw list` etc. are argparse errors and the whole repo speaks
the new grammar.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: remove old CLI verbs + shim

- [ ] E-01 Remove the old plan-family parsers and their dispatch entries: `plans` (cli.py:545; dispatch 4112), `plans-index` (576; 4114), `plans-find` (600; 4118), `plans-set-assign` (619; 4122), `plans-mv` (642; 4126), `plans-archive` (660; 4130), `plan-names` (1626; 4134). Remove the `plans <verb>` argv-rewrite shim (cli.py:4023-4031). Keep the BACKEND modules (plans_index/plans_refs/plans_archive/normalize_plan_names) - they are now reached only via the new verbs.
  - Depends on: none
  - Expected outcome: `aw plans`, `aw plans-mv`, `aw plan-names`, etc. all produce an argparse "invalid choice" error; the new verbs still work.
  - Execution state: pending
- [ ] E-02 Remove the old `list` verb (cli.py:532; dispatch 4106) now that `list-repos` exists (Order 04), and the old `todo` action-list body (`_run_todo`, cli.py:3479) now that `todo` aliases attention (Order 04) - keep the action-ledger READ verbs (`show`/`complete`/`dismiss`/`reopen`/`history`) which are a separate concern.
  - Depends on: none
  - Expected outcome: `aw list` errors; `aw list-repos` works; `aw todo` shows the attention board; `aw show`/etc. unaffected.
  - Execution state: pending

### Task group 2: sweep + update in-repo references

- [ ] E-03 Sweep the SHIPPED workflow bodies + framework docs for removed-verb references and rewrite to the new grammar: `.aw/system/workflows/**/*.md` (esp. assess, release-review, plan-review, setup-repo, ipd-lifecycle), `.aw/system/workflows/index.md`. Map: `plans-mv`->`rename plans`, `plans-set-assign`->`group plans`, `plans-find`->`find plans`, `plans-index`->`index plans`, `plans-archive`->`archive plans`, `plan-names`->`check plans names`, `aw plans`(board)->`aw ipd`/`aw ipd board`, `aw list`->`aw list-repos`. Use `rg` to enumerate; update each hit.
  - Depends on: E-01,E-02
  - Expected outcome: `rg -n "plans-mv|plans-set-assign|plans-find|plans-index|plans-archive|plan-names|aw plans\b|aw list\b" .aw/system/` returns nothing (or only the new grammar).
  - Execution state: pending
- [ ] E-04 Sweep + update the top-level docs AND in-code user-facing references. (a) Docs: `AGENTS.md`, `RELEASING.md`, `CONTRIBUTING.md`, any `README.md`/`.aw/records/*/README.md` referencing a removed verb (regenerate the AGENTS.md managed block via the engine generator if the reference lives there, else edit in place; no em/en dashes). (b) IN-CODE under `agent_workflows/**/*.py`: module DOCSTRINGS, `help=`/`description=` strings, and code COMMENTS that mention a removed VERB (verified present, e.g. `plans_refs.py:8` docstring "aw plans mv ...", `:141` comment; plus plans.py/plans_index.py/plans_archive.py/attention_contract.py/engine.py/cli.py). Rewrite user-facing verb mentions to the new grammar (`aw plans mv`->`aw rename plans`, `aw plan-names`->`aw check plans names`, etc.). CRITICAL: do NOT rename backend FUNCTION names (`run_mv`/`run_set_assign`/`run_index` stay, kept per E-01), and do NOT rewrite historical logs `DECISIONS.md`/`CHANGELOG.md` (their old-verb mentions are accurate history). Only user-facing verb strings/docstrings/comments change.
  - Depends on: E-01,E-02
  - Expected outcome: `rg -n "<removed-verb set>"` over AGENTS.md/RELEASING.md/CONTRIBUTING.md/READMEs AND `agent_workflows/` returns nothing that is a stale user-facing verb mention (kept function names + DECISIONS.md/CHANGELOG.md history excluded).
  - Execution state: pending
- [ ] E-05 Sweep + update the TESTS: any test invoking a removed verb (`tests/test_cli.py`, `tests/test_plans_board.py`, `tests/test_plan_status.py`, and any test asserting `aw plans*`/`aw plan-names`/`aw list`) is rewritten to the new grammar. Prefer updating assertions to the new verb; where a test specifically tested the OLD verb's existence, retarget it to the NEW verb's behavior.
  - Depends on: E-01,E-02
  - Expected outcome: `rg -n "plans-mv|plan-names|aw plans\b|aw list\b" tests/` returns nothing; the suite exercises the new grammar.
  - Execution state: pending

### Task group 3: verify the cutover

- [ ] E-06 Run the FULL serial suite (`python3 -m pytest -p no:xdist`) + `aw sanitize --agent` + `aw check all` + `aw index all --check` + `aw attention --check`, and a final `rg` proving NO removed verb survives as a user-facing reference anywhere in tracked files - INCLUDING `agent_workflows/**/*.py` (docstrings/help/comments), `.aw/system/`, docs, and tests - EXCLUDING kept backend function names and the historical logs DECISIONS.md/CHANGELOG.md. Paste all tails.
  - Depends on: E-01,E-02,E-03,E-04,E-05
  - Expected outcome: full suite green; all checks clean; the removed-verb grep is empty repo-wide.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Old parsers + dispatch lines enumerated in the investigation (cli.py:532/545/576/600/619/642/660/1626; dispatch 4106/4112/4114/4118/4122/4126/4130/4134; argv shim 4023-4031).
- Backends stay; only the CLI entry points are removed. `_run_plans` (board) is relocated to `ipd board` in Order 04, so its `plans` parser is removed here.
- Reference sites to sweep: shipped workflows under `.aw/system/workflows/`, AGENTS.md (managed block via engine generator), RELEASING/CONTRIBUTING, READMEs, tests.
- No em/en dashes in user-facing prose (agent execution contract).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Removal must be LAST. | Orders 01-04 add the new grammar alongside old; only here is old removed, so every prior state was runnable. |
| F2 | Backends are shared. | Removing CLI entry points does not touch the backend modules; low risk. |
| F3 | References are broad. | An exhaustive `rg` sweep (docs+workflows+tests) is the acceptance gate (E-06). |
| F4 | AGENTS.md is partly generated. | Update the engine generator source where the reference is in the managed block, else edit in place. |
| F5 | Removed-verb refs also live IN `agent_workflows/**/*.py` (docstrings/help/comments), not only docs/tests. | Empirically enumerated: plans_refs.py:8/141, plans.py, plans_index.py, plans_archive.py, attention_contract.py, engine.py, cli.py all mention old verbs. E-04 must sweep these too (rewriting user-facing verb strings, NOT the kept function names), or the shipped source keeps advertising dead verbs. DECISIONS.md/CHANGELOG.md are history and excluded. |

## Proposed changes (ordered, validatable)

1. Remove plan-family verbs + argv shim (E-01). 2. Remove old list/todo body (E-02). 3. Sweep shipped workflows/docs (E-03). 4. Sweep top-level docs (E-04). 5. Sweep tests (E-05). 6. Full verify + repo-wide grep (E-06).

## Deferred / out of scope (with reason)

- New-verb behavior: Orders 01-04. Check engine/selectors: Sets D/E.
- The spec status transition to implemented is done by the ORCHESTRATOR after this Order, not here.

## Scope check

- Over-scope: none - only removal + reference sweep.
- Under-scope: none - E-06's repo-wide grep is the completeness gate for the hard cutover.

## Required tests / validation

Full serial suite + all `--check`s + `aw sanitize --agent` + the repo-wide removed-verb grep (E-06).

## Spec / documentation sync

Docs/workflows/AGENTS.md updated to the new grammar (E-03,E-04). Spec 20260818-1525-01 -> implemented
by the orchestrator after this Order completes the Set.

## Open questions

### OQ-01: any external consumers of the old verbs to warn?

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: NO - the maintainer confirmed agent-workflows is not yet widely used and prefers a clean hard cutover over back-compat (spec 20260818-1525-01 D1). No deprecation shims.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste argparse errors for `aw plans`, `aw plans-mv`, `aw plan-names`, `aw plans-index` and success of their new equivalents.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw list` error + `aw list-repos` success + `aw todo` == attention; `aw show` still works.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `rg` over `.aw/system/` showing no removed-verb reference remains.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `rg` over AGENTS.md/RELEASING.md/CONTRIBUTING.md/READMEs showing none stale.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `rg` over `tests/` showing none stale; the suite exercises the new grammar.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the full serial suite tail + `aw check all`/`aw index all --check`/`aw attention --check`/`aw sanitize --agent` clean + the empty repo-wide removed-verb grep.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification + commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions only after
`aw ipd lint --phase pre-transition` conforms and every V is `pass`. Terminal Order of awcmdsurf;
depends on 01-04. On Set completion the orchestrator advances spec 20260818-1525-01 to implemented.
