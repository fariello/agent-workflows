# IPD: CLI help + docstrings + records READMEs + managed-sections regen + dead-code + typing + sdist

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S4-D04, S4-D05, S5-K01, S6-V02, S5-DC01, S2-Q01, S6-C01 (the lower-risk cleanup tail): CLI `--help` strings + module docstrings still cite `.agents/` (code correct); relocated `.aw/records/**/README.md` stubs + tracked `.agents/README.md` describe the old layout; the self-install manifest `.aw/system/managed-sections.json` is keyed entirely on legacy `.agents/workflows/*` (150 keys, 0 `.aw/`); `DEFAULT_FRAMEWORK_VERSION` is a hardcoded second version source; dead constants/aliases linger; the pre-existing companion-dir typing errors (cli.py) and an sdist `.gitignore` inclusion + stale CI/shell comments; plus a pre-existing SyntaxWarning (plans_refs.py:204 invalid `\`` escape).
- Scope: Prose/annotation/manifest/dead-code cleanup with no behavioral change to the fixed verbs. OUT: shipped workflow bodies/AGENTS.md (Order 02), release mechanics (Order 03), and the version NUMBER (S6-V01, maintainer).
- Status: to-review
- Set: awretrofit
- Order: 5
- Highest E allocated: 07
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: euqxi3

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 findings S4-D04/D05, S5-K01, S6-V02, S5-DC01, S2-Q01, S6-C01 (Set awretrofit Order 05).

## Goal

Remove the remaining post-migration drift and latent cruft so the framework is internally consistent
and honest: CLI help + docstrings + record-README stubs describe the real `.aw/` layout, the
self-install manifest is regenerated against the shipped tree, the second version source and dead
constants are removed, and the pre-existing typing error + SyntaxWarning + minor packaging nits are cleared.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: help + docstrings (D04)

- [ ] E-01 Update the CLI `--help` strings that cite moved paths (cli.py: the `plans`/`plans-index`/`plans --write-index`/`research`/`ipd lint --all` help at ~66/69/111/570/579/706) to `.aw/records/...`; and the stale docstrings in `__init__.py` (4/25), `_compat.py` (3-6), `hatch_build.py` (8/19), `versioning.py` (251/262) to the `.aw/system/...` canonical path. Keep the legacy-fallback CODE unchanged (docstrings only).
  - Depends on: none
  - Expected outcome: `aw <verb> --help` shows `.aw/records/...`; the four packaging modules' docstrings name `.aw/system/...`. No behavior change.
  - Execution state: pending

### Task group 2: record-README stubs (D05)

- [ ] E-02 Retitle/repath the tracked `.aw/records/**/README.md` stubs (plans, prompts, docs, docs/research, docs/specs, backlog, comms) from `# .agents/...` self-references to their real `.aw/records/...` location, and decide the tracked `.agents/README.md` (repoint it as a legacy pointer to `.aw/` OR remove it - propose remove since the tree moved).
  - Depends on: none
  - Expected outcome: each `.aw/records/**/README.md` describes its own `.aw/records/...` path; `.agents/README.md` no longer misdescribes a vanished tree.
  - Execution state: pending

### Task group 3: self-install manifest (K01)

- [ ] E-03 Regenerate `.aw/system/managed-sections.json` against the `.aw/system/` tree (via the manifest machinery / `aw install` self-update, NOT hand-edit) so its keys are `.aw/system/workflows/...` not the 150 stale `.agents/workflows/*` keys; verify install/update prune/diff behaves correctly with the rekeyed manifest.
  - Depends on: none
  - Expected outcome: `grep -c '.agents/workflows' managed-sections.json` -> 0; a self-install/update is a clean no-op (no spurious "vanished managed file" prune).
  - Execution state: pending

### Task group 4: version second-source + dead code + latent warnings (V02, DC01, Q01, C01)

- [ ] E-04 Resolve `DEFAULT_FRAMEWORK_VERSION` (project_context.py:57) as a second version source: derive it from `versioning`/the baked VERSION, or document it as an explicit floor with a comment tying it to the release process (do not leave a bare literal that silently drifts).
  - Depends on: none
  - Expected outcome: no bare hand-maintained version literal that can diverge from the resolver.
  - Execution state: pending

- [ ] E-05 Remove the dead constants/aliases: `plans_index.PLANS_DIR` (unused), `_compat._DATA_RELATIVE` (unused alias); annotate or derive `versioning.py`'s legacy default (latent landmine). Confirm zero remaining references before removal.
  - Depends on: none
  - Expected outcome: dead constants removed; modules still import; grep shows no references.
  - Execution state: pending

- [ ] E-06 Fix the pre-existing companion-dir typing errors (cli.py ~3373/3428: `Any|None` passed where `str|Path` expected) by narrowing/asserting the companion dir is non-None at the callsite; and fix the `plans_refs.py:204` docstring SyntaxWarning (invalid `\`` escape -> raw string or escaped). Optionally add hatchling sdist `exclude=[".gitignore"]` and refresh the stale `.agents/` comments in `tests.yml:114` + `install-workflows.sh:9`.
  - Depends on: none
  - Expected outcome: the two LSP typing errors clear; no SyntaxWarning from plans_refs import; (optional) sdist omits `.gitignore`; CI/shell comments say `.aw/`.
  - Execution state: pending

### Task group 5: verification

- [ ] E-07 Run the full serial suite + `aw sanitize --agent` + `aw attention --check`; confirm no behavioral regression from the prose/manifest/dead-code changes and that the manifest rekey did not disturb install semantics.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: full serial suite >= 982 passed / 1 skipped; sanitize + attention clean.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The legacy-fallback CODE is correct and stays; only PROSE/annotations are stale here (unlike Orders 01/02/04 which fix behavior).
- `managed-sections.json` is a generated manifest (manifest.py `DEFAULT_MANIFEST_RELPATH = .aw/system/managed-sections.json`); regenerate via the machinery, never hand-edit.
- ruff/ruff-format run in pre-commit; the SyntaxWarning is a genuine latent bug (invalid escape) worth fixing even though it is pre-existing.

## Findings

| id | area | evidence | class |
|---|---|---|---|
| D04a | CLI help | cli.py ~66/69/111/570/579/706 | stale prose |
| D04b | docstrings | __init__.py 4/25, _compat.py 3-6, hatch_build.py 8/19, versioning.py 251/262 | stale prose (code correct) |
| D05 | record READMEs | `.aw/records/**/README.md` titled `# .agents/...`; tracked `.agents/README.md` | stale self-reference |
| K01 | managed-sections.json | 150 `.agents/workflows` keys, 0 `.aw/` | stale generated manifest |
| V02 | DEFAULT_FRAMEWORK_VERSION | project_context.py:57 `"1.2.1"` | second version source |
| DC01 | dead code | plans_index.PLANS_DIR (unused), _compat._DATA_RELATIVE (unused), versioning legacy default | dead/latent |
| Q01 | typing | cli.py ~3373/3428 Any|None vs str|Path | pre-existing type error |
| C01 | packaging/CI prose | sdist `.gitignore`; tests.yml:114; install-workflows.sh:9; plans_refs.py:204 SyntaxWarning | minor nits |

## Proposed changes (ordered, validatable)

1. E-01 help+docstrings. 2. E-02 record READMEs. 3. E-03 manifest regen. 4. E-04 version second-source.
5. E-05 dead code. 6. E-06 typing + SyntaxWarning + optional sdist/CI/shell nits. 7. E-07 verify.

## Deferred / out of scope (with reason)

- The version NUMBER (S6-V01): maintainer decision, Section 9.
- Any behavioral verb/install/migration change: Orders 01/02/04.

## Scope check

- Over-scope: none - each item is a reproduced finding. The optional C01 nits are low-value but low-risk;
  keep them grouped here rather than spawning a further Order.
- Under-scope: none - this Order is the full lower-risk cleanup tail from the run.

## Required tests / validation

- `aw <verb> --help` + docstrings show `.aw/...`; `grep -c '.agents/workflows' managed-sections.json` -> 0;
  a self-install/update is a clean no-op; no bare version literal; dead constants gone (imports still work);
  cli.py typing errors clear; `python3 -c "import agent_workflows.plans_refs"` emits no SyntaxWarning.
- Full serial suite >= 982 passed / 1 skipped; `aw sanitize --agent` + `aw attention --check` clean.

## Spec / documentation sync

- Prose-only; no spec status change. The manifest regen (E-03) is the one item with install-semantics
  risk - verified by a clean self-install no-op.

## Open questions

### OQ-01: Remove the tracked `.agents/README.md`, or repoint it as a legacy pointer?

- Blocking: no
- Status: open
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: Proposed: REMOVE it (the tree it describes moved to `.aw/`, and a
  stale pointer is worse than none). Left OPEN for the maintainer to confirm at Order-05 approval, since
  some may prefer a one-line `.agents/README.md` -> "moved to .aw/, run `aw migrate-layout`" breadcrumb
  for users landing in a half-migrated checkout. Non-blocking; either choice is Low risk.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `aw plans/plans-index/research/ipd --help` show `.aw/...` (no `.agents/`); the four packaging-module docstrings name `.aw/system/...`. Paste grep/help excerpts.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: each `.aw/records/**/README.md` describes its own `.aw/records/...` path; `.agents/README.md` removed or repointed per OQ-01. Paste heads + the decision applied.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `grep -c '.agents/workflows' .aw/system/managed-sections.json` -> 0; a self-install/update dry-run is a clean no-op (no vanished-managed-file prune). Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `DEFAULT_FRAMEWORK_VERSION` is derived or documented as an explicit floor (no bare drifting literal). Paste the changed lines.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `grep -rn "PLANS_DIR" plans_index.py` / `_DATA_RELATIVE` _compat.py -> 0 refs; modules still import. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: cli.py has no `Any|None`-vs-`str|Path` LSP error at the companion callsites; `python3 -W error::SyntaxWarning -c "import agent_workflows.plans_refs"` succeeds; (optional) sdist omits `.gitignore`; tests.yml/install-workflows.sh comments updated. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: full serial suite >= 982 passed / 1 skipped; `aw sanitize --agent` + `aw attention --check` clean. Paste summaries.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line) AND the OQ-01
decision (remove vs repoint `.agents/README.md`). The executor implements E-01..E-07, pastes actual
evidence (help/grep excerpts, manifest no-op, imports, LSP clear, suite summary), commits only the
scoped paths (`agent_workflows/cli.py`, `__init__.py`, `_compat.py`, `hatch_build.py`,
`agent_workflows/versioning.py`, `agent_workflows/plans_index.py`, `agent_workflows/project_context.py`,
`agent_workflows/plans_refs.py`, `.aw/records/**/README.md`, `.agents/README.md`,
`.aw/system/managed-sections.json`, `pyproject.toml`, `.github/workflows/tests.yml`,
`install-workflows.sh`), never pushes, runs `aw ipd lint --phase pre-transition` + the full suite, and
the orchestrator owns the move to `executed/`. LOW-MEDIUM risk (E-03 manifest regen is the only
install-semantics-touching item; verified by a clean no-op).
