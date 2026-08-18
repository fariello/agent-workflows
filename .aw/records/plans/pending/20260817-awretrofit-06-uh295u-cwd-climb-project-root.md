# IPD: Repo-scoped verbs climb to the project root (find .aw/.agents upward) + verbose no-project message

- Date: 2026-08-17
- Kind: child
- Concern: Maintainer report (2026-08-17): `aw att` run from a repo SUBDIRECTORY (e.g. a nested dir like `<repo>/.aw/state`) prints nothing and exits 0, because repo-scoped verbs resolve the project root as bare cwd/`--dir` with no upward climb (attention.py:510; and ~a dozen siblings: backlog.py:280/337/439, plans_index.py:302, plans_refs.py:316, plans_archive.py:152, research_*.py, specs.py:297, cli._run_plans cli.py:2803). Worse, run from a non-project dir (e.g. `~`) the empty output is indistinguishable from "a clean project", giving the user no clue why they see nothing (P3 self-documenting failure).
- Scope: Add ONE canonical "find the project root by climbing the directory tree for a `.aw/` or `.agents/` marker" helper (git-style), wire the repo-scoped verbs through it so they work from any subdirectory, and when NO project root is found print a clear, verbose message telling the user to check they are inside the repo directory (instead of silent empty output). OUT: changing what each verb DOES once the root is found (Orders 01/02/04 own that).
- Status: reviewed
- Set: awretrofit
- Order: 6
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: uh295u

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from a maintainer report during release-review run 20260817-153418 (Set awretrofit Order 06).
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Structural preflight conforming. Re-verified against current code (post Orders 01/02/07): `find_project_root` does not yet exist; all ~12 resolver sites still do `Path(getattr(args,"dir",None) or ".")` with no climb (attention.py shifted :510->:526 by the Order-07 _classify_tree edit; other lines stable). PR-001 (LOW): clarified the E-02/E-03 interaction - climb is ONE flow (found->use; none->short-circuit with the verbose message, NOT a silent cwd-empty fallback) so the fix cannot accidentally reproduce the silent-empty output it removes; also flagged the `aw attention --check` fail-closed nuance for the no-project case. OQ-01 resolved (AW markers only, not bare .git). No open questions. GO - PENDING HUMAN APPROVAL.
- 2026-08-17 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified against attention.py:526, backlog.py:280/337/439, specs.py:297, and sibling resolver sites; structural lint conforming; no findings; no open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Make repo-scoped `aw` verbs work from any subdirectory of a project (like `git`), and replace silent
empty output with a clear message when no project is found - so a user in `~` or a repo subdir
understands what to do instead of seeing nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: canonical project-root finder

- [ ] E-01 Add ONE canonical helper (e.g. `project_context.find_project_root(start: Path) -> Optional[Path]`) that climbs from `start` (default cwd) toward the filesystem root and returns the first ancestor containing a `.aw/` OR `.agents/` directory (the project markers), else None. Stop at the filesystem root; do not cross above the user's home unnecessarily; be symlink-safe. Pure, side-effect-free, unit-tested in isolation.
  - Depends on: none
  - Expected outcome: `find_project_root(<repo>/.aw/state)` returns `<repo>`; `find_project_root(<tmp-with-no-marker>)` returns None.
  - Execution state: pending

### Task group 2: wire the repo-scoped verbs + verbose no-project message

- [ ] E-02 Route the repo-scoped verbs through the helper when the user did NOT pass an explicit `--dir`: `aw attention` (attention.py:510), `aw plans` board + `--write-index` (cli.py:2803), `aw backlog` (backlog.py:280/337/439), `aw specs` (specs.py:297), and the plans/research `_dirs`/`_roots`/`_repo_root` resolvers (plans_index.py:302, plans_refs.py:316, plans_archive.py:152, research_index.py:262, research_refs.py:232, research_cmd.py:276, research_archive.py:220). An explicit `--dir` is honored verbatim (no climb). When climbing finds a root, use it; when it does not, fall back to cwd (so behavior in a real project subdir improves and nothing regresses at repo root).
  - Depends on: E-01
  - Expected outcome: `aw att` (and the other verbs) run from `<repo>/.aw/state` produce the same output as from `<repo>`; from `<repo>` itself, unchanged.
  - Execution state: pending

- [ ] E-03 When a repo-scoped verb finds NO project root (no `.aw/`/`.agents/` at cwd or any ancestor), print a clear, verbose message to stderr - e.g. "aw <verb>: no AW project found here. Checked <cwd> and its parents for a .aw/ (or legacy .agents/) directory. Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>." - instead of silent empty output. Keep the exit code sensible (non-zero "nothing to do because no project", distinct from a clean project with nothing to show, which stays exit 0 with its normal empty-but-labeled board). `aw attention --check` fail-closed semantics preserved.
  - **Contract clarification (plan-review PR-001):** the E-02 "fall back to cwd" and this E-03 "no-project message" are ONE coherent flow, not two behaviors. The verb ALWAYS climbs first. If a marker root is found -> use it and run normally. If NONE is found -> the verb SHORT-CIRCUITS with the E-03 message + the distinct exit code; it does NOT then also run its normal logic against cwd and print an empty board (that would reproduce the confusing silent-empty output this Order removes). "Fall back to cwd" in E-02 means only that an EXPLICIT `--dir` (or the resolved marker root) is what's used; there is no silent cwd-empty path. The one nuance: `aw attention --check` must keep its fail-closed exit semantics even in the no-project case (decide + document whether "no project" is check-valid or a distinct code).
  - Depends on: E-01
  - Expected outcome: `aw att` from `~` prints the verbose no-project message (not nothing); `aw att` from a clean project still prints its normal board/empty-state; `aw att` from a repo subdir climbs and prints the real board.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add falsifiable tests: (a) `find_project_root` returns the root from a nested subdir and None with no marker; (b) `aw attention`/`aw plans`/`aw backlog` run from a subdirectory of a `.aw/` project resolve the same root as from the top (parametrized); (c) the no-project message is emitted (and is verbose / mentions checking the repo dir) when run from a markerless dir; (d) an explicit `--dir` still bypasses the climb. Each must fail against the pre-fix cwd-only behavior.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: new tests green; a spot-check shows the subdir test fails against the pre-fix code.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Repo-scoped verbs currently do `Path(getattr(args, "dir", None) or ".")` with no climb (~a dozen sites, enumerated in Concern). `--dir` is the explicit override and MUST stay verbatim.
- `resolve_project_context` already canonicalizes an explicit repo path but does not itself climb from a subdir; the new helper feeds it the climbed root.
- Markers: `.aw/` (current) OR `.agents/` (legacy) - either identifies a project root. git presence is NOT required (a `.aw/` tree can exist without git), so climb for the AW markers, not `.git` (though a `.git` ancestor is a reasonable secondary hint if needed).
- P3 (self-documenting): silent empty output is the specific defect; the fix is a helpful message, not just resolution.

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| U01 | project-root resolution | attention.py:526 (was :510 pre-Order-07) + ~11 sibling sites (backlog.py:280/337/439, specs.py:297, plans_index.py:302, plans_refs.py:316, plans_archive.py:152, research_index.py:262, research_refs.py:232, research_cmd.py:276, research_archive.py:220, cli.py:2803) - all still `Path(getattr(args,"dir",None) or ".")` with no climb (re-verified at review) | no upward climb -> broken from a repo subdir |
| U02 | empty-output UX | `aw att` from `~` and from `.aw/state` both print nothing, exit 0 | indistinguishable "no project" vs "clean project" (P3) |
| PR-001 | plan-review (contract) | E-02 "fall back to cwd" vs E-03 "no-project message" | LOW/IN-SCOPE: clarified in E-03 that these are ONE flow (climb; found->use; none->short-circuit with message, NOT a silent cwd-empty path). FIXED in plan. |

## Proposed changes (ordered, validatable)

1. E-01 `find_project_root` helper (climb for `.aw/`/`.agents/`).
2. E-02 wire the repo-scoped verbs (climb when no explicit `--dir`).
3. E-03 verbose no-project message (distinct exit semantics).
4. E-04 falsifiable tests (subdir resolution, no-project message, `--dir` bypass).

## Deferred / out of scope (with reason)

- What each verb DOES once the root is found (Orders 01/02/04).
- Install/setup/migration commands that legitimately operate on cwd or an explicit target (not survey verbs) - leave unless a specific one is reported; the climb targets SURVEY/record verbs.

## Scope check

- Over-scope: none - a single shared helper + wiring + message is the minimal general fix (P6/P7).
- Under-scope: none for the reported defect; if a specific non-survey verb also needs climbing it can be
  added, but the enumerated survey/record verbs are the ones that silently mislead.

## Required tests / validation

- `aw att` (and `aw plans`, `aw backlog`) from `<repo>/.aw/state` produce the same output as from `<repo>`.
- `aw att` from a markerless dir prints the verbose no-project message; from a clean project prints its board.
- Explicit `--dir <repo>` from anywhere still works verbatim (no climb).
- Full serial suite >= 982 passed / 1 skipped; `aw attention --check` fail-closed semantics preserved.

## Spec / documentation sync

- No spec change; this is a UX/ergonomics fix. Consider a one-line note in the relevant workflow/help that
  verbs work from any subdir (help text lives in Order 05; cross-reference, do not duplicate).

## Open questions

### OQ-01: Climb by AW markers only, or also treat a `.git` ancestor as a project root?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: Climb for the AW markers (`.aw/` or `.agents/`) as the primary and
  sufficient signal - that is what makes a directory an AW project, and a `.aw/` tree can exist without
  git. Do NOT treat a bare `.git` ancestor (with no AW marker) as an AW project root; that would resolve
  a non-AW git repo as if it were one and reintroduce the confusing empty board. If no AW marker is found
  anywhere up the tree, that is precisely the "no project" case E-03 handles with the verbose message.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a unit test: `find_project_root(<repo>/.aw/state)` -> `<repo>`; `find_project_root(<repo>/a/b/c)` (nested) -> `<repo>`; `find_project_root(<markerless-tmp>)` -> None; symlink-safe. Paste test output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw att` (and `aw plans`, `aw backlog`) run from `<repo>/.aw/state` produce output equal to running from `<repo>`; a test parametrizes subdir-vs-top. Paste the two outputs (or a test asserting equality). Explicit `--dir` still verbatim.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw att` from a markerless dir prints the verbose no-project message (mentions checking you are in the repo / passing --dir) to stderr; `aw att` from a clean project still prints its normal board and exits 0. Paste both.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: all new tests pass; documented fail-before/pass-after (the subdir-resolution test fails against the pre-fix cwd-only code); full serial suite >= 982 passed / 1 skipped; `aw attention --check` fail-closed preserved. Paste.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-01..E-04, pastes actual evidence (the subdir-vs-top output equality, the no-project message,
the `--dir` bypass, the full serial suite), commits only the scoped paths (`agent_workflows/project_context.py`
for the helper, `agent_workflows/attention.py`, `agent_workflows/cli.py`, `agent_workflows/backlog.py`,
`agent_workflows/specs.py`, `agent_workflows/plans_index.py`, `agent_workflows/plans_refs.py`,
`agent_workflows/plans_archive.py`, `agent_workflows/research_index.py`, `agent_workflows/research_refs.py`,
`agent_workflows/research_cmd.py`, `agent_workflows/research_archive.py`, and the new/edited tests), never
pushes, runs `aw ipd lint --phase pre-transition` + the full suite before transition, and the orchestrator
owns the move to `executed/`. MEDIUM risk (touches root resolution across many verbs) - mitigated by the
`--dir`-verbatim rule, the cwd fallback (no regression at repo root), and per-verb subdir tests.
