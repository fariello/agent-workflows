# IPD: untracked-file safety convention (managed .gitignore block) + install-time tracking warning

- Date: 2026-07-23
- Concern: data-exposure safety - give agents and users a reliable, passive way to keep sensitive/provisional files OUT of git, and warn at install that agent-workflows git-tracks IPDs/prompts/research by default
- Scope: add an agent-workflows-managed `aw:block` to the target repo's ROOT `.gitignore` (rendered in `#`-comment syntax) carrying the maintainer's field-tested untracked-safety patterns and rationale; make block removal style-aware so uninstall strips it too; and print an honest install-time tracking warning that also scans for and reports any already-tracked files matching the untracked patterns (with the `git rm --cached` remedy). Product code + tests + docs. DEPENDS ON IPD 01 (manifest) and IPD 02 (sectioned `aw:block` mechanism), both executed.
- Status: to-review
- Set: install-safety-and-ownership
- Order: 3
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-23 created as a draft stub (opencode its_direct/pt3-claude-opus-4.8-1m-us): captured from a maintainer request during the install-manifest discussion, spun out as its own prioritized safety IPD. Preliminary; to be fleshed out later.
- 2026-07-23 fleshed out to a full IPD (opencode its_direct/pt3-claude-opus-4.8-1m-us): with IPD 01 and IPD 02 now executed, converted the stub into findings + ordered validatable steps + tests + docs. Maintainer decisions taken at authoring: Q1 the agent-facing explanation lives ONLY in the managed `.gitignore` comment (no AGENTS.md section, zero always-loaded token cost); Q2 the install-time warning is informational AND scans for already-tracked files matching the untracked patterns, reporting each with the `git rm --cached` remedy (no interactive consent gate); Q3 uninstall MUST also strip the `#`-styled `.gitignore` block, so `_strip_managed_block` becomes style-aware and uninstall gains the `.gitignore` target.

## Goal

On install, add to the target repo's root `.gitignore` an agent-workflows-managed `aw:block` (in `#`-comment syntax, reusing the IPD-02 mechanism) containing the maintainer's field-tested "deliberately-untracked local artifacts" patterns and their DO-NOT-REMOVE rationale, so any file named `*.untracked.*` / `*.untracked` or living under a `*untracked*/` directory is reliably kept out of git by a passive guard that works WITH `git add .`/`git add -A`/the hooks/the sanitizer. Print an honest, plain-language install-time warning that agent-workflows tracks IPDs/prompts/research by default (useful, but be careful what goes in them), name the safety valves (the untracked naming plus the comms/prompts `local/` lanes, D81/D94), and scan the repo for files that ALREADY match the untracked patterns yet are git-tracked, warning per file with the `git rm --cached` remedy. Make block removal style-aware so `aw uninstall` strips the `.gitignore` block too (identifiable AND removable), leaving the user's other `.gitignore` lines intact.

Why it matters: the maintainer has repeatedly hit a failure mode where sensitive IPDs/notes that should have stayed local got committed because a lifecycle directive (or an agent) overrode the intent to keep them untracked. A passive, name-based, tooling-cooperating guard is the escape hatch; the honest warning + already-tracked scan close the "I did not realize it was tracked" gap.

## Marker syntax (from IPD 02, first `#`-comment instance)

The managed-block markers render in the target file's OWN comment syntax: bare `<!-- aw:... -->` in Markdown, `#`-prefixed `# <!-- aw:... -->` in `#`-comment files. `.gitignore` is the first `#`-comment instance and uses `AW_STYLE_HASH` (`engine.py:726`). The block is one logical `aw:block` with a single `aw:untracked` section; per-section identity/drift are tracked in the IPD-01 manifest keyed by `.gitignore#aw:untracked` + normalized hash.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| N1 | HIGH | Low | adopter/security | data exposure | There is no reliable, agent-obvious way to keep a sensitive/provisional file OUT of git; lifecycle directives push agents to commit under `.agents/plans/`, and a blanket `git add .` stages anything. A passive, name-based ignore guard (maintainer field-tested) fixes this. | maintainer report; `agents_pointer_prose` execution-contract inlines "commit ... path-scoped" pressure `engine.py:630-640` |
| N2 | MEDIUM | Low | maintainer | identifiability/removability | The block must be added in the agent-workflows-managed, identifiable, REMOVABLE way (IPD 02 `aw:block`) so it is not mistaken for user lines and can be cleanly uninstalled. `merge_aw_block` is reusable with `style=AW_STYLE_HASH` + `file_key=".gitignore"`, but `_strip_managed_block` hardcodes `AW_STYLE_MARKDOWN` (`engine.py:2745`), so uninstall would NOT remove a `#`-styled block. | `merge_aw_block` `engine.py:858`, `_strip_managed_block` `:2734-2772` (markdown-only `:2745`), `remove_agents_pointer` `:2775` |
| N3 | MEDIUM | Low | adopter | honesty (P2) | Users are not told that IPDs/prompts/research are git-tracked by default; the install must say so plainly and point at the safety valves (untracked naming + comms/prompts `local/` lanes, D81/D94). | `create_setup_artifacts` nested `local/` `.gitignore` `engine.py:3414-3447`; DECISIONS D81/D94 |
| N4 | MEDIUM | Low | adopter | already-tracked caveat | A `.gitignore` pattern only stops FUTURE tracking; a file already committed stays tracked even if renamed to match. The install must SCAN for files that match the untracked patterns but are already git-tracked and warn per file with the `git rm --cached` remedy, so the guard is not silently over-trusted. | git semantics; `git ls-files` |
| N5 | LOW | Low | maintainer | commit plumbing | A new root-`.gitignore` mutation must reach `prompt_and_run_commit` to be committed (not left staged-dirty). Today only the backups branch adds `.gitignore` to `files_to_commit` (`engine.py:2518-2522`); the new status must be threaded parallel to `backups_ignore_status`. | `prompt_and_run_commit` `:2462-2581`, result dict `:3566-3578`, `run()` `:3696-3704` |

## Proposed changes (ordered, validatable; checkpointed)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | N1,N2 | Define the canonical untracked-safety section: a module-level constant holding the maintainer's field-tested comment + patterns (`*.untracked.*`, `*.untracked`, `**/*untracked*/`) as the body of a single `aw:untracked` section. Add `untracked_safety_sections() -> list[AwSection]` returning it. | `agent_workflows/engine.py` | Low | constant present; section body byte-matches the approved text; patterns exactly the three approved |
| 2 | N2,N5 | `ensure_untracked_gitignore(plan, use_git) -> str`: read the root `.gitignore` (absent = empty), `merge_aw_block(existing, untracked_safety_sections(), style=AW_STYLE_HASH, manifest=plan.manifest, file_key=".gitignore")`, write atomically + backup (mirroring `ensure_backups_gitignored`), stage when `use_git`, honor `dry_run`, return a status string. Call it in `install_into_repo` right AFTER `ensure_backups_gitignored`; add its status to the result dict; thread it into `run()` -> `prompt_and_run_commit` parallel to `backups_ignore_status` so `.gitignore` is committed, not left staged. Idempotent: a second install is an empty diff (own-hash match via the manifest). | `agent_workflows/engine.py` (`install_into_repo`, `prompt_and_run_commit`, result dict, `run()`) | Low | fresh repo gets the `# <!-- aw:block -->` + `# <!-- aw:untracked -->` block with the three patterns; reinstall empty diff; block committed (not left staged); a pre-existing user `.gitignore` keeps its lines (block appended); manifest records `.gitignore#aw:untracked` |
| 3 | N2 | Make removal style-aware: add a `style` parameter to `_strip_managed_block` (default `AW_STYLE_MARKDOWN` for back-compat) and try BOTH the markdown and hash styles when stripping; have `uninstall_repo`/`remove_agents_pointer` (or a sibling) also strip the `.gitignore` `#`-styled block, leaving the user's other `.gitignore` lines intact. Removal is ONLY on explicit uninstall, never on a normal install. | `agent_workflows/engine.py` (`_strip_managed_block`, uninstall path) | Low | uninstall strips the `.gitignore` aw:block; user's other `.gitignore` lines preserved; a repo with only the markdown block still uninstalls; no-op when absent |
| 4 | N3,N4 | Install-time warning: after the install writes, print a plain-language notice that agent-workflows tracks IPDs/prompts/research by default (useful but be careful), naming the untracked convention and the comms/prompts `local/` lanes as safety valves; then SCAN via `git ls-files` for tracked files whose path matches the untracked patterns and print each with the `git rm --cached <path>` remedy (the caveat that ignoring does not untrack). Informational only (no interactive gate); skipped cleanly in a non-git repo. | `agent_workflows/engine.py` (a `warn_tracking_and_scan(plan, use_git)` helper called from the install summary path) | Low | warning text present and honest; the scan lists an already-tracked `foo.untracked.md` with the remedy; a clean repo prints the notice with no per-file warnings; non-git repo does not crash |
| 5 | N1,N2,N3,N4,N5 | Tests: the `.gitignore` block is written in `#` syntax with the three patterns + rationale; reinstall empty diff; a pre-existing user `.gitignore`'s lines are preserved; the block is committed (parallel to backups); manifest records the section; uninstall strips the `#`-styled block and preserves user lines; the tracking warning prints; the already-tracked scan reports a matching tracked file with the remedy and stays silent on a clean repo; non-git safe. | `tests/test_installer.py`, `tests/test_setup_artifacts.py`, `tests/test_manifest.py` | Medium | full suite green; paste ACTUAL output |
| 6 | N1 | Docs/decision sync: DECISIONS entry (pin at execution) for the untracked-safety convention (patterns, managed `#`-styled `aw:block`, install warning + already-tracked scan, uninstall symmetry, agent guidance lives in the `.gitignore` comment per Q1); CHANGELOG 1.3.0; note the convention in the manifest README / relevant docs; cross-reference D81/D94 (the `local/` lanes) and IPD 02. | `DECISIONS.md`, `CHANGELOG.md`, docs | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| An `aw:untracked-safety` AGENTS.md section authorizing agents to use the naming | Low | scope (Q1) | Maintainer chose the `.gitignore` comment as the single home (zero always-loaded token cost). Revisit only if agents demonstrably fail to discover the convention. | A later per-directive section IPD if needed. |
| Leak-sanitizer flagging sensitive-looking tracked files | Medium | complexity | The already-tracked SCAN here is name-pattern-based only; content heuristics belong to the sanitizer. | A sanitizer lens IPD. |
| An interactive consent gate on the tracking warning | Low | scope (Q2) | Maintainer chose informational (no gate); keeps install flow simple. | The interactive-questions IPD (06) if consent is later wanted. |
| Unifying the untracked convention with the comms/prompts `local/` lanes | Low | scope | They are complementary (name-based vs directory-lane); cross-reference is enough. | Only if a real overlap problem appears. |

## Scope check

- Over-scope: none - the managed `.gitignore` block + style-aware removal + the install warning/scan + tests + docs. No AGENTS.md section (Q1), no content heuristics (sanitizer's job), no consent gate (Q2).
- Under-scope: MUST add the block in the identifiable/removable `aw:block` way via the IPD-02 mechanism (N2) and MUST make uninstall strip the `#`-styled block (Q3/N2); MUST keep a pre-existing user `.gitignore`'s own lines intact; MUST be idempotent (reinstall empty diff via the manifest); MUST commit the `.gitignore` change (not leave it staged, N5); MUST print an honest tracking warning AND scan for already-tracked matches with the `git rm --cached` remedy (N3/N4); MUST be safe in a non-git repo and under `--dry-run`.

## Required tests / validation

- `.gitignore` block: fresh repo gets `# <!-- aw:block -->` + `# <!-- aw:untracked -->` + the three patterns (`*.untracked.*`, `*.untracked`, `**/*untracked*/`) + the DO-NOT-REMOVE rationale; a pre-existing user `.gitignore` keeps its lines and gets the block appended; reinstall is an empty diff (manifest own-hash match); the manifest records `.gitignore#aw:untracked`.
- Commit plumbing (N5): after `aw install --yes` the `.gitignore` change is committed, not left staged-but-uncommitted (mirror the D85 no-silent-dirty guard).
- Uninstall (Q3/N2): `aw uninstall` strips the `#`-styled `.gitignore` block and leaves the user's other lines intact; a markdown-only repo still uninstalls; absent block is a no-op.
- Warning + scan (N3/N4): the tracking notice prints with the safety valves named; a repo containing a tracked `foo.untracked.md` prints that path with the `git rm --cached` remedy; a clean repo prints the notice with no per-file warnings; a non-git repo does not crash.
- Full suite `python -m pytest -q` GREEN; paste ACTUAL output. `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- DECISIONS (the untracked-safety convention: patterns, managed `#`-styled `aw:block`, install warning + already-tracked scan, uninstall symmetry, Q1/Q2/Q3 decisions), CHANGELOG 1.3.0, a note in the manifest README / relevant docs. Cross-reference D81/D94 (the `local/` lanes) and IPD 02 (the sectioning mechanism).

## Open questions

- OQ-Q1 (agent guidance home): RESOLVED (maintainer, authoring). The explanation lives ONLY in the managed `.gitignore` comment; no AGENTS.md section (zero always-loaded token cost).
- OQ-Q2 (warning shape / already-tracked): RESOLVED (maintainer, authoring). Informational warning (no consent gate) PLUS a scan that reports already-tracked files matching the untracked patterns with the `git rm --cached` remedy.
- OQ-Q3 (uninstall symmetry): RESOLVED (maintainer, authoring). Uninstall MUST strip the `#`-styled `.gitignore` block; `_strip_managed_block` becomes style-aware. Removal only on explicit uninstall.
- OQ-patterns: RESOLVED by the maintainer's field-tested block: exactly `*.untracked.*`, `*.untracked`, `**/*untracked*/` (supersedes the earlier stub's narrower pair). Case-sensitive as written (git default); no case-folding added.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. DEPENDS ON IPD 01 (manifest) and IPD 02 (sectioned `aw:block`), both executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. Never modify a target repo's `.gitignore` beyond the single managed `aw:block` (leave the user's own lines untouched), and never auto-remove the block except on an explicit uninstall.

CHECKPOINTED EXECUTION: (0) characterization of current `.gitignore`/uninstall behavior FIRST; (1) untracked-safety section constant; (2) `ensure_untracked_gitignore` + install wiring + commit plumbing; (3) style-aware `_strip_managed_block` + uninstall wiring; (4) tracking warning + already-tracked scan; (5) tests; (6) docs. Re-run the full suite at each checkpoint; pause and report if scope grows.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute in checkpoints, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
