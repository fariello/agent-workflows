# IPD: Installer updates framework-namespace files by default (drop the --force papercut)

- Date: 2026-07-01
- Concern: installer usability / correctness (framework tooling)
- Scope: `.agents/workflows/install-workflows.py` (conflict/overwrite policy for
  framework-namespace files), plus doc sync in `README.md`, `ARCHITECTURE.md`, and a
  `DECISIONS.md` entry. Also the shell wrapper help text if it mentions `--force`.
- Status: EXECUTED (approved 2026-07-01; --force removed per OQ1; all steps applied and validated)
- Author: OpenCode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Make "update an existing install" work by simply re-running the installer, without
requiring `--force`. Today, when a target repo has an older copy of a framework file
(the normal case for an update - e.g. `index.md` after a new lens is added upstream),
the installer treats it as a "conflict", aborts the entire run, and tells the user to
re-run with `--force`. That is friction that trains users to reflexively pass `--force`
(which then also disables the guard on genuinely user-owned surfaces), and it is
internally inconsistent with the installer's own prune-by-default behavior (DECISIONS
D15), which *deletes* stale framework files by default. Overwriting a stale
framework-namespace file is strictly safer than deleting one, so it should also be the
default. User-owned surfaces (the `AGENTS.md` prose region) keep their existing careful,
idempotent handling (D21) and are unaffected.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md`. Most relevant: P3 (self-documenting /
  learn-as-you-go: an update should not need a magic flag), P10 (safety and
  reversibility: default to non-destructive, reversible action), P8 (single source of
  truth), P6 (KISS).
- Contributor contract: `CONTRIBUTING.md` doc-sync checklist (update DECISIONS on a
  design change; keep README/ARCHITECTURE accurate). Authoring convention: no em dashes.
- Plan location/format: `.agents/plans/pending/`, template `assess/templates/ipd.md`.
- Stack: single Python installer (argparse), stdlib only; Python 3.7+ floor.
- The relevant existing decision: **D15** (clean, git-aware sync; prune stale framework
  files by default, justified by "strict namespace scope, backups, `--dry-run`, git
  staging, and `--no-prune`"). This IPD extends the same posture to overwrites.
- **D21** governs the `AGENTS.md` prose region (marker-delimited, idempotent, backed
  up). That is the one genuinely user-owned surface and must remain conflict-guarded /
  careful; this change does not touch it.

## Evidence: the current behavior (verified)

- `write_file` (`install-workflows.py:363-400`): if a destination exists, differs from
  source, and `not plan.force`, it records a conflict and returns without writing
  (lines 383-385).
- `install_all` (`:426-436`): if any conflict exists and `not plan.force`, it raises
  `SystemExit`, aborting the whole run ("No files were installed or pruned").
- Everything routed through `write_file` is framework-namespace: `body_members`
  (the `.agents/workflows/` tree, lines 417-421) and `shim_members` (the generated
  `.opencode/commands/` and `.claude/commands/` shims, lines 423-424). No user-owned
  file flows through it; `AGENTS.md` is handled by a separate, marker-based updater.
- Confirmed live against `a consuming repo clone`: a routine update (only the new
  `generalization` manifest row differs) is refused with "Run again with --force".

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| I1 | Medium | Low | Operator / Novice (P3) | Update requires `--force` | The normal update path (target has an older framework file) is refused unless `--force` is passed, aborting the whole sync. Updating should be the default behavior of an updater. | `install-workflows.py:383-385,426-436`; live repro on a-consuming-repo |
| I2 | Medium | Low | Maintainer (consistency) | Internal inconsistency with D15 | The installer *prunes* (deletes) stale framework files by default but *refuses to overwrite* them by default, though the same mitigations (namespace scope, backups, dry-run, git staging, escape hatch) apply and overwriting is safer than deleting. | `DECISIONS.md` D15 vs. `:383-385` |
| I3 | High | Low | Security-minded operator | `--force` is an over-broad hammer | Because the only way to update is `--force`, users learn to always pass it. If a future change routes any user-owned file through `write_file`, `--force` would silently clobber it. Making framework overwrite the default keeps `--force` unnecessary for normal use, so it is not habitual. | `:383` (single global gate) |
| I4 | Low | Low | Operator | `--force` semantics will be vestigial | If framework files overwrite by default, `--force` has little left to gate (all current write_file inputs are framework-owned). It should either be removed or redefined to only cover a genuine future user-owned case. Leaving it as a no-op would confuse. | `:141` (arg), `:383,387,393` |
| I5 | **BLOCKER** | Low | QA/QC (found in plan-review) | Backup is gated on `--force`, so overwrite-by-default would skip backups | The backup only runs when `plan.force` is true: `if destination.exists() and plan.force and plan.backup:` (`:393`). If Step 1 makes overwrite the default WITHOUT changing this condition, a default (no-flag) update would overwrite framework files with NO backup - silent, irreversible loss of any local state, directly violating P10 and the plan's own safety claim. The fix must drop `and plan.force` from the backup condition so backups fire on every overwrite unless `--no-backup`. | `install-workflows.py:393` (backup condition) |

## Proposed changes (ordered, validatable)

Fix by default. All Low Remediation Risk to fix (single installer, backups + git
staging provide reversibility, no application-runtime code) - note I5 is BLOCKER
*severity* but its fix is a one-line, Low-risk condition change. The Step 1(a) and 1(b)
changes must land together: enabling default overwrite (1a) without fixing the backup
gate (1b) would ship the I5 silent-data-loss bug. No em dashes.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | I1, I2, I5 | In `write_file`, overwrite a differing framework-namespace file by default, rather than recording a conflict. Concretely: (a) remove the `if not plan.force: conflicted; return` gate (`:383-385`) so the `action = "overwrite"` path runs by default; (b) **critically, change the backup condition at `:393` from `if destination.exists() and plan.force and plan.backup:` to `if destination.exists() and plan.backup:`** so a backup is written on EVERY overwrite (default included), suppressed only by `--no-backup`. Without (b), a no-flag overwrite would skip the backup (see I5). Preserve the `[destination is directory]` conflict (a real error, not a stale file). | `install-workflows.py` (`write_file`, ~383-397) | Low | Re-running on a target with an older framework file updates it with NO `--force`, writes a backup under `.agent-workflows-installer-backups/`, and stages it; dry-run shows `[overwrite]` not a conflict abort. |
| 2 | I1, I2 | Since no framework file conflicts anymore, simplify `install_all`: the conflict-abort block (`:426-436`) now only fires for the residual hard errors (e.g. destination-is-directory). Keep an abort for those genuine errors with a clear message; drop the "run again with --force" instruction for the stale-file case. | `install-workflows.py` (`install_all`) | Low | A normal update completes end to end (install + prune) in one run; a genuine error (dir where a file should be) still aborts with an actionable message. |
| 3 | I3, I4 | Resolve `--force`'s role (see Open Question 1). Default recommendation: **keep `--force` as a no-op-safe alias for now but stop advertising it as required for updates**, OR remove it if the maintainer prefers. Do NOT silently keep it as the only update path. Update `--help` text and the shell wrapper accordingly. | `install-workflows.py` (arg + help), `install-workflows.sh` | Low | `--help` no longer implies `--force` is needed to update; behavior with/without `--force` is identical for framework files. |
| 4 | I1, I5 | Verify safety guarantees AFTER the Step 1(b) change: backups now occur on overwrite-by-default because the `and plan.force` coupling was removed from `:393` (NOTE: pre-change, backups did NOT fire without `--force` - that was the I5 bug, not a preexisting guarantee). Confirm `--no-backup` still suppresses them, and that prune scope, the migration logic, and the `AGENTS.md` marker updater are untouched. | (verification; the only code change is Step 1(b)) | Low | Overwritten file appears under `.agent-workflows-installer-backups/<ts>/` on a no-flag run; `--no-backup` suppresses it; `AGENTS.md` region still idempotent; prune unchanged. |
| 5 | I2, I4 | Doc + decision sync: add a `DECISIONS.md` entry (next Dxx) recording "framework-namespace files update-by-default, consistent with D15's prune-by-default; overwrite always backs up unless `--no-backup`; `--force` no longer needed for updates; user-owned `AGENTS.md` prose still guarded per D21." Verified current wording: `README.md:58-59` lists `--force` as an *available* flag (it does not claim it is required) and `ARCHITECTURE.md:139` describes `--no-prune`; adjust the `README.md:58-59` flag list to match the resolved role of `--force` (Open Question 1: kept-as-alias vs. removed), and add a one-line "to update, just re-run the installer" note. Do not overstate the current defect. | `DECISIONS.md`, `README.md`, `ARCHITECTURE.md` | Low | New DECISIONS entry present; README states re-running is the update path; the `--force` mention matches its resolved role; no doc claims `--force` is required. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | No finding deferred on Remediation-Risk grounds. `--force`'s fate is an Open Question (design intent), not a risk deferral. | - |

## Scope check

- Over-scope: do NOT change prune behavior, the `AGENTS.md` marker updater, the
  migration logic, or add new flags/config. The change is confined to the overwrite
  decision for framework-namespace files and the now-simplified conflict handling.
- Under-scope: none identified; the fix addresses the root cause (blanket conflict gate)
  rather than only the symptom.

## Required tests / validation

Installer-behavior change; validate by exercising it against a scratch target (not a
real repo) plus a dry-run on a-consuming-repo:

1. Create a throwaway git repo under `/tmp/opencode/`, install the framework, then
   modify one framework file (e.g. delete a manifest row from `index.md`) to simulate
   an older version. Re-run the installer with NO flags: it updates the file, writes a
   backup, stages it, and completes (install + prune) without `--force`.
2. `--dry-run` shows `[overwrite]` for the differing file, not a conflict abort.
3. **I5 regression guard (must pass):** a NO-flag (default) overwrite writes a backup
   under `.agent-workflows-installer-backups/<ts>/` mirroring the file's path; then
   confirm `--no-backup` on a default overwrite suppresses it. (Pre-fix, no backup was
   written without `--force`; this test pins the fix.)
4. Destination-is-directory still aborts with a clear error.
5. `AGENTS.md` prose region remains idempotent (re-run does not stack blocks) and its
   prose is preserved.
6. Prune scope unchanged: a stale framework file (renamed upstream) is still pruned;
   nothing outside the framework namespace is touched.
7. Dry-run against `a consuming repo clone` now shows the `generalization` update as
   `[overwrite]`/install with no conflict abort and no `--force`.
8. No em dashes in changed Markdown; `python3 -m py_compile install-workflows.py` and
   `sh -n install-workflows.sh` pass.

## Spec / documentation sync

The DECISIONS entry + README/ARCHITECTURE updates (Step 5) are the doc sync. This
changes installer behavior (a user-visible contract), so per `CONTRIBUTING.md` the
decision must be recorded and the docs kept accurate.

## Open questions

1. **What to do with `--force`?** Options: (a) keep it as a harmless accepted flag
   (back-compat, becomes a near-no-op); (b) remove it entirely; (c) redefine it to gate
   a future genuinely-user-owned surface. Recommendation: (a) for now (least surprising,
   preserves any scripts that pass it), and revisit if a user-owned write path is ever
   added. Needs your call.
2. **`--no-prune` and `--no-backup` unchanged?** Assumption: yes, both remain as-is.
   Confirm.
3. **Any appetite to also add a concise "Updating an existing install" note to README**
   beyond fixing `--force` wording? (Low value-add; flag only.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs.
3. Only then move this IPD out of `pending/` (this project uses `.agents/plans/done/`).
4. After this ships and is committed/pushed, update `a consuming repo clone` by simply
   re-running the installer (no `--force` needed) - the original task that surfaced
   this finding.
