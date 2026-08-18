# IPD: CLI help + docstrings + records READMEs + managed-sections regen + dead-code + typing + sdist

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S4-D04, S4-D05, S5-K01, S6-V02, S5-DC01, S2-Q01, S6-C01 (the lower-risk cleanup tail): CLI `--help` strings + module docstrings still cite `.agents/` (code correct); relocated `.aw/records/**/README.md` stubs + tracked `.agents/README.md` describe the old layout; the self-install manifest `.aw/system/managed-sections.json` is keyed entirely on legacy `.agents/workflows/*` (150 keys, 0 `.aw/`); `DEFAULT_FRAMEWORK_VERSION` is a hardcoded second version source; dead constants/aliases linger; the pre-existing companion-dir typing errors (cli.py) and an sdist `.gitignore` inclusion + stale CI/shell comments; plus a pre-existing SyntaxWarning (plans_refs.py:204 invalid `\`` escape).
- Scope: Prose/annotation/manifest/dead-code cleanup with no behavioral change to the fixed verbs. OUT: shipped workflow bodies/AGENTS.md (Order 02), release mechanics (Order 03), and the version NUMBER (S6-V01, maintainer).
- Status: executed
- Set: awretrofit
- Order: 5
- Highest E allocated: 07
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: euqxi3

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 findings S4-D04/D05, S5-K01, S6-V02, S5-DC01, S2-Q01, S6-C01 (Set awretrofit Order 05).
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Re-verified all findings against CURRENT code (post Orders 02/06/07). PR-001 (LOW): E-02 README list corrected to the FLAT 8-stub set. PR-002 (LOW): sanitize-after-regen moved with E-03 to Order 09. OQ-01 for the maintainer. GO - PENDING HUMAN APPROVAL.
- 2026-08-17 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved; OQ-01 resolved = REMOVE .agents/README.md. Implemented E-01/E-02/E-04/E-05/E-06 in commit 8ba0bef (help+docstrings -> .aw/; 8 record READMEs retitled + .agents/README.md removed; DEFAULT_FRAMEWORK_VERSION documented as floor; dead plans_index.PLANS_DIR + _compat._DATA_RELATIVE removed + versioning legacy-default landmine fixed; companion typing guards + plans_refs SyntaxWarning fixed + CI/shell comments). E-03 (managed-sections regen, K01) SPLIT to Order 09 (needs a full self-install). V-01/V-02/V-04/V-05/V-06/V-07 verified; full serial suite 1004 passed / 1 skipped (no behavioral change); sanitize + attention clean; 0 tracked .agents/ files. pre-transition lint conforming; moved pending -> executed/.

## Goal

Remove the remaining post-migration drift and latent cruft so the framework is internally consistent
and honest: CLI help + docstrings + record-README stubs describe the real `.aw/` layout, the
self-install manifest is regenerated against the shipped tree, the second version source and dead
constants are removed, and the pre-existing typing error + SyntaxWarning + minor packaging nits are cleared.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: help + docstrings (D04)

- [x] E-01 Update the CLI `--help` strings that cite moved paths (cli.py: the `plans`/`plans-index`/`plans --write-index`/`research`/`ipd lint --all` help at ~66/69/111/570/579/706) to `.aw/records/...`; and the stale docstrings in `__init__.py` (4/25), `_compat.py` (3-6), `hatch_build.py` (8/19), `versioning.py` (251/262) to the `.aw/system/...` canonical path. Keep the legacy-fallback CODE unchanged (docstrings only).
  - Depends on: none
  - Expected outcome: `aw <verb> --help` shows `.aw/records/...`; the four packaging modules' docstrings name `.aw/system/...`. No behavior change.
  - Execution state: performed

### Task group 2: record-README stubs (D05)

- [x] E-02 Retitle/repath the tracked `.aw/records/**/README.md` stubs still titled `# .agents/...` to their real FLAT `.aw/records/...` location. **plan-review PR-001 (post-Order-07):** the 8 stubs still needing it are `backlog, comms, plans, prompts, research, roadmaps, specs, walkthroughs` (verified) - the layout is FLAT (no `.aw/records/docs/`); `prompt-library/README.md` is ALREADY correct (Order 07), so exclude it. Also decide the tracked `.agents/README.md` per OQ-01 (remove vs one-line legacy pointer).
  - Depends on: none
  - Expected outcome: each of the 8 flat `.aw/records/*/README.md` describes its own `.aw/records/...` path; `.agents/README.md` no longer misdescribes a vanished tree.
  - Execution state: performed

### Task group 3: self-install manifest (K01) - SPLIT to Order 09

- E-03 (regenerate `.aw/system/managed-sections.json`, 150 stale `.agents/workflows/*` keys) was SPLIT
  OUT to a new Order 09 (2026-08-17): the designed regeneration is a full `aw install .` on this repo,
  which also rewrites shims/AGENTS.md/config/state - a broad self-install operation that warrants its
  own isolated, carefully-verified pass rather than being bundled with this LOW-risk prose cleanup. The
  stale manifest is a self-install-only concern (prune/diff when running `aw install` ON this framework
  repo), not a shipped-artifact defect. Tracked as Order 09; K01 finding recorded there.

### Task group 4: version second-source + dead code + latent warnings (V02, DC01, Q01, C01)

- [x] E-04 Resolve `DEFAULT_FRAMEWORK_VERSION` (project_context.py:57) as a second version source: derive it from `versioning`/the baked VERSION, or document it as an explicit floor with a comment tying it to the release process (do not leave a bare literal that silently drifts).
  - Depends on: none
  - Expected outcome: no bare hand-maintained version literal that can diverge from the resolver.
  - Execution state: performed

- [x] E-05 Remove the dead constants/aliases: `plans_index.PLANS_DIR` (unused), `_compat._DATA_RELATIVE` (unused alias); annotate or derive `versioning.py`'s legacy default (latent landmine). Confirm zero remaining references before removal.
  - Depends on: none
  - Expected outcome: dead constants removed; modules still import; grep shows no references.
  - Execution state: performed

- [x] E-06 Fix the pre-existing companion-dir typing errors (cli.py ~3373/3428: `Any|None` passed where `str|Path` expected) by narrowing/asserting the companion dir is non-None at the callsite; and fix the `plans_refs.py:204` docstring SyntaxWarning (invalid `\`` escape -> raw string or escaped). Optionally add hatchling sdist `exclude=[".gitignore"]` and refresh the stale `.agents/` comments in `tests.yml:114` + `install-workflows.sh:9`.
  - Depends on: none
  - Expected outcome: the two LSP typing errors clear; no SyntaxWarning from plans_refs import; (optional) sdist omits `.gitignore`; CI/shell comments say `.aw/`.
  - Execution state: performed

### Task group 5: verification

- [x] E-07 Run the full serial suite + `aw sanitize --agent` + `aw attention --check`; confirm no behavioral regression from the prose/manifest/dead-code changes and that the manifest rekey did not disturb install semantics.
  - Depends on: E-01, E-02, E-04, E-05, E-06
  - Expected outcome: full serial suite >= 982 passed / 1 skipped; sanitize + attention clean.
  - Execution state: performed

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
| C01 | packaging/CI prose | sdist `.gitignore`; tests.yml:114; install-workflows.sh:9; plans_refs.py:204 SyntaxWarning (CONFIRMED live via py_compile -W error) | minor nits |
| PR-001 | plan-review (post-Order-07) | E-02 README list cited `docs/research`,`docs/specs` | LOW: layout is FLAT; the 8 stubs are backlog/comms/plans/prompts/research/roadmaps/specs/walkthroughs; prompt-library already correct. FIXED in E-02. |
| PR-002 | plan-review (sanitize) | managed-sections.json holds this repo's file hashes | LOW: MOVED with E-03/K01 to Order 09 (the sanitize-after-regen check goes there). |

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
- Status: resolved
- Owner: human maintainer (2026-08-17)
- Resolution or deferral rationale: REMOVE it (maintainer chose option (a) at approval). The tree it
  described moved to `.aw/`; a stale pointer is worse than none. E-02 `git rm`s `.agents/README.md`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `aw plans/plans-index/research/ipd --help` show `.aw/...` (no `.agents/`); the four packaging-module docstrings name `.aw/system/...`. Paste grep/help excerpts.
  - Observed evidence: Updated 6 cli.py help strings (66/69/111/570/579/706) -> `.aw/records/...`. `aw research --help` -> "Research-artifact tooling for .aw/records/research"; `aw plans --help` -> ".aw/records/plans" + "--write-index (Re)generate .aw/records/plans/STATUS.md". Docstrings in __init__.py/_compat.py/hatch_build.py/versioning.py now lead with `.aw/system/...` (legacy `.agents/workflows/` retained as a labeled mention). cli.py:408 `--source .aw/system or legacy .agents/workflows` legitimately keeps legacy. Imports OK.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: each `.aw/records/**/README.md` describes its own `.aw/records/...` path; `.agents/README.md` removed or repointed per OQ-01. Paste heads + the decision applied.
  - Observed evidence: All 8 flat stubs retitled: `# .aw/records/{backlog,comms,plans,prompts,research,roadmaps,specs,walkthroughs}/` with 0 remaining `.agents/` body refs (docs-family flattened; prompt-library already correct from Order 07). OQ-01 resolved = REMOVE: `git rm .agents/README.md`; `git ls-files .agents/` -> 0 (no tracked legacy files remain).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `DEFAULT_FRAMEWORK_VERSION` is derived or documented as an explicit floor (no bare drifting literal). Paste the changed lines.
  - Observed evidence: `DEFAULT_FRAMEWORK_VERSION = "1.2.1"` (project_context.py:57) now carries a block comment documenting it as an EXPLICIT FLOOR (fallback only when no baked `.aw/system/VERSION`; the git-tag resolver baked at release time is authoritative; importing versioning at module load would add a fragile import-time dep). Not a bare undocumented literal.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `grep -rn "PLANS_DIR" plans_index.py` / `_DATA_RELATIVE` _compat.py -> 0 refs; modules still import. Paste.
  - Observed evidence: Removed dead `plans_index.PLANS_DIR` and `_compat._DATA_RELATIVE` (both had 0 references, verified repo-wide). Also fixed the `versioning.py` legacy default (real latent bug: docstring said `.aw/system/VERSION` but code defaulted `.agents/workflows/VERSION`) to prefer `.aw/system/VERSION` with legacy fallback. `import agent_workflows.plans_index, agent_workflows._compat, agent_workflows.versioning` -> OK.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: cli.py has no `Any|None`-vs-`str|Path` LSP error at the companion callsites; `python3 -W error::SyntaxWarning -c "import agent_workflows.plans_refs"` succeeds; (optional) sdist omits `.gitignore`; tests.yml/install-workflows.sh comments updated. Paste.
  - Observed evidence: Added non-None guards before `move_companion`/`validate_companion_preflight` (cli.py `_run_storage_move`/preflight): the two `Any|None` LSP errors cleared. SyntaxWarning fixed (plans_refs.py:204 docstring rewritten to plain text; `py_compile -W error` -> clean). tests.yml:114 + install-workflows.sh:8 comments updated to `.aw/`. sdist `.gitignore`: NOT applied - hatchling injects it and a sdist `exclude` does not override (verified); documented in pyproject.toml as the one optional C01 nit left (harmless dev-meta; wheel unaffected).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: full serial suite >= 982 passed / 1 skipped; `aw sanitize --agent` + `aw attention --check` clean. Paste summaries.
  - Observed evidence: full serial suite `1004 passed, 1 skipped in 187.20s` (unchanged - pure prose/annotation/dead-code, no behavioral regression). `aw sanitize --agent` clean; `aw attention --check: the view is valid.` `git ls-files .agents/` -> 0.
  - Result: pass

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
