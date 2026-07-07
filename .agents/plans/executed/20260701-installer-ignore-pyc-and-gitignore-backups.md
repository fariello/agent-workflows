# IPD: Installer excludes __pycache__/*.pyc, and gitignores its backups dir in the target

- Date: 2026-07-01
- Concern: installer correctness + hygiene (framework tooling)
- Scope: `.agents/workflows/install-workflows.py` (source-file collection, prune walker,
  and gitignore handling), plus doc/decision sync (`README.md`, `ARCHITECTURE.md`,
  `DECISIONS.md`). Also this repo's own `.gitignore` for the backups dir.
- Status: EXECUTED (approved 2026-07-01; all steps applied and validated on scratch repos + a-consuming-repo dry-run)
- Author: OpenCode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Two related installer hygiene fixes surfaced while updating `a consuming repo clone`:

1. **Do not propagate Python build cruft.** The installer copies every file under the
   source `.agents/workflows/` via `rglob("*")`. A stray `__pycache__/…​.pyc` (e.g. from
   running `python3 -m py_compile install-workflows.py`) would be installed into every
   target. Observed live: a `.pyc` appeared in the a-consuming-repo dry-run and had to be
   manually removed from the source to avoid polluting the target.
2. **Keep the installer's own backups out of version control.** The installer writes
   overwrite/prune backups to `.agent-workflows-installer-backups/` in the target. That
   directory is currently not gitignored, so it shows as untracked and can be
   accidentally committed (`git add -A`). The installer should add it to the target's
   `.gitignore`, and this repo should ignore it too.

## Project conventions discovered (Step 0)

- Guiding principles: P8 (single source of truth - the two `rglob` sites must share one
  exclusion rule), P10 (safety/reversibility - backups are the safety net; keeping them
  out of commits protects the repo), P6 (KISS). Authoring convention: no em dashes.
- Contributor contract: `CONTRIBUTING.md` doc-sync checklist (record design changes in
  DECISIONS; keep README/ARCHITECTURE accurate).
- Plan location/format: `.agents/plans/pending/`, template `assess/templates/ipd.md`.
- Relevant existing design: **the installer deliberately does NOT modify `.gitignore`
  today**; `check_gitignore` (`:693-707`) only *warns* if `workflow-artifacts/` is
  ignored. This IPD narrowly extends that policy to add ONE ignore line for the
  installer's own backups dir, which is different from the `workflow-artifacts/` case
  (backups are local scratch, not a committed deliverable). This is a policy change and
  must be recorded in DECISIONS.
- `.agent-workflows-installer-backups/` is defined once via `create_backup_path`
  (`:315-316`).

## Evidence (verified)

- Source collection walks all files: `collect_source_members` `:233-240` uses
  `source_root.rglob("*")` and only excludes `SOURCE_EXCLUDED_NAMES`
  (`install-workflows.py`, `install-workflows.sh`) and `:Zone.Identifier`. No
  `__pycache__`/`.pyc` exclusion. `SOURCE_EXCLUDED_NAMES` is at `:71-76`.
- Prune candidate walk: `collect_target_framework_files` `:448-455` uses the same
  `rglob("*")` with the same name-only exclusion. If a `.pyc` were ever installed, this
  site also needs the exclusion, or it would treat the target `.pyc` as a stale
  framework file (or as present-in-source) inconsistently.
- Backups path: `create_backup_path` `:315-316` -> `.agent-workflows-installer-backups/`.
- `.gitignore` policy: `check_gitignore` `:693-707` warns only; the installer never
  writes `.gitignore` (the claim is at `ARCHITECTURE.md:144-146`: "The installer does
  not modify `.gitignore`; it only warns if the target repo ignores
  `workflow-artifacts/`...").
- Live repro: a-consuming-repo dry-run listed
  `.agents/workflows/__pycache__/install-workflows.cpython-314.pyc [install, dry-run]`
  and, after the real run, `.agent-workflows-installer-backups/` was untracked and not
  ignored.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| P1 | High | Low | Operator / QA | `.pyc`/`__pycache__` propagates to targets | `collect_source_members` copies any file under the source, including `__pycache__/*.pyc`. Installs build cruft into every target and pollutes their git status. | `install-workflows.py:233-240` |
| P2 | Medium | Low | Maintainer (P8) | Prune walker shares the same gap, causing accidental deletion | If only the source-collect site is fixed, a stray `.pyc` in a target under `.agents/workflows/` is excluded from `desired` (source) but still included in `present` (prune walk `:448-455`), so `orphans = present - desired` (`prune_stale:477-479`) marks it stale and **deletes it** (the `in_framework_namespace` defense-in-depth at `:485` does not stop it - a `.pyc` there IS in-namespace). The exclusion must be applied at BOTH `rglob` sites via one shared rule so a `.pyc` is neither installed nor pruned. | `:448-455`, `:477-479,485` vs `:233-240` |
| P3 | Medium | Low | Operator | Installer backups can be committed | `.agent-workflows-installer-backups/` is untracked and not ignored in the target; `git add -A` would commit local backup scratch. | `:315-316`; live on a-consuming-repo |
| P4 | Low | Low | Maintainer | This repo does not ignore the backups dir either | Running the installer against `ai-coding` itself (self-install) would also leave an untracked backups dir. | `ai-coding/.gitignore` |

## Proposed changes (ordered, validatable)

Fix by default; all Low Remediation Risk (single installer + one gitignore line;
backups and git staging provide reversibility; no application-runtime code). No em dashes.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | P1, P2 | Add one shared helper, e.g. `is_ignored_source_path(path) -> bool`, that returns True for any path with a `__pycache__` path component or a `.pyc`/`.pyo` suffix (in addition to the existing `SOURCE_EXCLUDED_NAMES` and `:Zone.Identifier` checks). Apply it at BOTH `rglob` sites: `collect_source_members` (`:233-240`) and `collect_target_framework_files` (`:448-455`). Single rule, used in both places (P8). | `install-workflows.py` | Low | A `.pyc`/`__pycache__` in the source is never collected for install; a `.pyc` in a target is never treated as a framework file (neither installed nor pruned). Unit-style check via a scratch repo. |
| 2 | P3 | Add the installer's backups dir to the TARGET `.gitignore`: a new function (e.g. `ensure_backups_gitignored`) that idempotently appends the backups line if absent, honoring `--dry-run` (report only) and creating `.gitignore` if absent. Idempotency is a simple "line already present?" check (a single ignore line needs NO BEGIN/END marker block - keep it simpler than the AGENTS updater; KISS). Match this repo's `.gitignore` style (a `# comment header` then the pattern - see Open Question 1, resolved). Stage the change with git and report it in the summary. This is a deliberate, narrow exception to the "installer does not modify .gitignore" policy: it manages only its own scratch dir, not user or artifact ignores. | `install-workflows.py` | Low | Fresh target: `.gitignore` gains exactly one `.agent-workflows-installer-backups/` line (under a comment); re-run does not duplicate it; `--dry-run` reports without writing; the line is staged with git. |
| 3 | P3 | Keep `check_gitignore`'s `workflow-artifacts/` WARNING behavior unchanged (that dir is a committed deliverable, a different case). Only the backups dir is auto-ignored. Confirm no interaction. | `install-workflows.py` (verification) | Low | `workflow-artifacts/` still only warns, never auto-ignored; the two behaviors are independent. |
| 4 | P4 | Add `.agent-workflows-installer-backups/` to THIS repo's `.gitignore` (ai-coding), so self-installs and local testing do not leave an untracked/committable backups dir. | `ai-coding/.gitignore` | Low | `git check-ignore .agent-workflows-installer-backups/` returns a match in ai-coding. |
| 5 | P1, P3 | Doc + decision sync: add a `DECISIONS.md` entry (next Dxx) recording (a) the installer excludes `__pycache__`/`*.pyc`/`*.pyo` from the copied set (at both walk sites); (b) the installer now auto-ignores ONLY its own backups dir in the target `.gitignore`, a narrow exception to "does not modify .gitignore", with rationale (local scratch, must not be committed) and the contrast with the `workflow-artifacts/` warn-only policy (committed deliverable). Correct the claim at `ARCHITECTURE.md:144-146` ("The installer does not modify `.gitignore`; it only warns...") to state the one exception (adds only its own backups-dir ignore line). README makes no `.gitignore` claim to update (verified: no `gitignore` mention in README). | `DECISIONS.md`, `ARCHITECTURE.md` | Low | DECISIONS entry present; `ARCHITECTURE.md:144-146` no longer states an absolute "never modifies .gitignore"; wording accurate. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | No finding deferred on Remediation-Risk grounds. All Low risk and fixed. | - |

## Scope check

- Over-scope: do NOT broaden the `.gitignore` auto-edit beyond the single backups dir;
  do NOT change the `workflow-artifacts/` warn-only policy; do NOT add new flags. Keep
  the exclusion rule to build cruft (`__pycache__`, `.pyc`, `.pyo`), not a general
  ignore-file mechanism.
- Under-scope: the prune-walker exclusion (P2) is easy to forget; it is explicitly
  included so the two walk sites cannot diverge.

## Required tests / validation

Exercise on a throwaway git repo under `/tmp/opencode/`; do NOT test against a real repo:

1. Put a `__pycache__/x.pyc` under a copy of the source workflows (or rely on a stray
   one) and confirm a dry-run/real install never lists or copies it.
2. Fresh install into a scratch repo: `.gitignore` gains exactly one
   `.agent-workflows-installer-backups/` line; a second run does not duplicate it.
3. `--dry-run` reports the intended `.gitignore` change without writing it.
4. A pre-existing `.gitignore` with unrelated content is preserved (only the one line
   appended); a repo with no `.gitignore` gets one created with just that line.
5. `workflow-artifacts/` warn-only behavior is unchanged.
6. Prune correctness (guards P2): place a `.pyc` in the target `.agents/workflows/` and
   confirm the installer neither installs nor prunes it. This specifically pins the P2
   bug: pre-fix, that `.pyc` would appear in `present` but not `desired` and be deleted
   by `prune_stale`; post-fix (prune walk excludes it) it is left untouched.
7. `python3 -m py_compile install-workflows.py` and `sh -n install-workflows.sh` pass;
   no em dashes in changed Markdown.
8. Final dry-run against `a consuming repo clone` shows no `.pyc` and would add the backups
   ignore line (report-only; do not apply here as part of testing).

## Spec / documentation sync

DECISIONS entry + ARCHITECTURE correction (Step 5) are the doc sync. The `.gitignore`
auto-edit is a user-visible behavior change, so per `CONTRIBUTING.md` it must be
recorded and the docs corrected (ARCHITECTURE currently states the installer never
modifies `.gitignore`).

## Open questions

1. **Backups-ignore line placement/label:** RESOLVED during plan-review by inspecting
   this repo's `.gitignore` style (comment header + entries, e.g. `# Local scratch /
   working files` then `tmp/`). Use the same style: a `# agent-workflows installer local
   backups` comment then `.agent-workflows-installer-backups/`. Confirm only if a
   different label is preferred.
2. **Also ignore `.pyc` broadly in the target?** No - out of scope; the installer should
   ignore only its own backups dir, not impose a Python ignore policy on arbitrary
   targets. (Recorded so it is a conscious non-goal.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review`).
2. On approval, execute the ordered changes, run the validation, sync docs.
3. Move this IPD out of `pending/` to `.agents/plans/done/`.
4. Commit/push per the session's selective-commit instruction (only this session's
   changes; leave other agents' work untouched).
