# IPD: A README.md in every directory of the installed `.agents/` tree

- Date: 2026-07-11
- Concern: Orientation and self-documentation of an installed repo's `.agents/` tree (P3
  self-documenting; P2 honest docs). A developer or agent browsing any `.agents/` directory should
  understand what it is for without reading source or the central manifest.
- Scope: Add a `README.md` to (a) the user-owned `.agents/` + `.agents/plans/` family (installer-
  generated, no-clobber), and (b) each top-level framework capability dir
  `.agents/workflows/<capability>/` (authored source, copied+pruned like other framework files).
  Leaf dirs (`lenses/`, `personas/`, `tools/`, `templates/`, `references/`) do NOT get their own
  README; their PARENT capability README describes them.
- Status: PENDING (scope decided interactively with the maintainer 2026-07-10/11; see "Decisions
  taken"). Sequenced AFTER the superseded/not-executed IPD
  (`20260710-plan-lifecycle-superseded-notexecuted-dirs.md`), because this documents the two new
  buckets (`superseded/`, `not-executed/`) that IPD creates.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Decisions taken (maintainer, 2026-07-10/11)

1. **Every directory in the installed `.agents/` tree gets an explanatory README** - but at
   **top-level depth**, not every leaf. A capability README must clearly explain the purpose of its
   own subdirectories, so leaf dirs are documented by their parent rather than each carrying a file.
2. **One standalone IPD** for all the READMEs (this one), superseding the narrow
   "plan-lifecycle-dir-readmes" stub the superseded/not-executed IPD referenced.
3. **Sequenced after** the superseded/not-executed IPD so the `.agents/plans/` READMEs can name all
   five lifecycle buckets (incl. `superseded/` + `not-executed/`).

## Goal

Make the installed `.agents/` tree self-documenting: anyone (human or agent) who opens a directory
finds a short README explaining what belongs there and what to do with it, without needing
`index.md` or the source repo. This closes the real gap - the user-owned `.agents/plans/*` dirs are
currently empty `.gitkeep`-only with no explanation - and adds light orientation to each framework
capability dir, with the capability README describing its leaf subdirs so we avoid a per-leaf
maintenance burden.

## Two categories, two mechanics (the crux)

The installed `.agents/` tree (verified by installing into a scratch repo, 2026-07-11) splits into
two ownership classes that MUST use different mechanics:

- **Category 1 - user-owned dirs (installer-GENERATED, no-clobber).** `.agents/` (root),
  `.agents/plans/`, and the five lifecycle buckets `pending/ reusable/ executed/ superseded/
  not-executed/`. The installer creates these (empty, `.gitkeep`-only today); they are the USER's
  working dirs. Their READMEs are written from templates NO-CLOBBER (never overwrite a user's own),
  exactly like `workflow-artifacts/README.md` (`ensure_workflow_artifacts_readme`, engine.py:2037-
  2076). NOT clean-synced/pruned (they are outside the framework namespace,
  `in_framework_namespace` engine.py:664-671).
- **Category 2 - framework-owned dirs (AUTHORED source, copied+pruned).** The top-level capability
  dirs under `.agents/workflows/`. Their READMEs are plain authored files committed in THIS repo's
  source under `.agents/workflows/<capability>/README.md`; the installer already copies every
  framework file into targets and prunes stale ones (`collect_source_members` /
  `install_all` / `prune_stale`), so these need ZERO installer code - just author the files. Two
  already exist: `.agents/workflows/README.md` and `.agents/workflows/release-review/README.md`.

## Project conventions discovered (Step 0)

- **Installed `.agents/` tree (30 dirs).** Category 1: `.agents/plans/{pending,reusable,executed}`
  today (+`superseded`,`not-executed` after the prior IPD). Category 2: `.agents/workflows/` +
  16 top-level capability dirs: `advise assess assess-all benchmark getting-started incident
  list-workflows migrate plan-review release-notes release-review scaffold setup-repo spec
  templates verify`. Leaf subdirs live under `advise/` (personas), `assess/` (lenses templates
  tools references), `benchmark/` (tools), `release-review/` (templates), `setup-repo/` (tools),
  `verify/` (tools).
- **Existing READMEs (do not duplicate/clobber):** `.agents/workflows/README.md` (short, points to
  `aw install`) and `.agents/workflows/release-review/README.md` (the release-review runbook's own).
- **Three README mechanics already in the engine to model on:**
  - shim-dir READMEs: `generate_shim_members` reads `templates/shim-README.md` (engine.py:517-537)
    and writes `<shimdir>/README.md`; pruning explicitly SKIPS README.md (engine.py:730, 931).
  - `workflow-artifacts/README.md`: `ensure_workflow_artifacts_readme` (engine.py:2037-2076) reads
    `plan.source_root/templates/workflow-artifacts-README.md`, writes NO-CLOBBER, stages, dry-run
    aware. **This is the model for Category 1** and it already has `plan.source_root`, which
    resolves the "create_setup_artifacts has no source_root" wrinkle the prior IPD flagged - the new
    generated READMEs are written by a plan-aware function, not by `create_setup_artifacts`.
  - authored capability READMEs: just files under source `.agents/workflows/**`, copied+pruned.
- **README voice/format precedent:** short, h1 title, imperative, "To install/update, run: aw
  install <dir>" where relevant (see `.agents/workflows/README.md`, `templates/shim-README.md`).
- **Packaging (P8/no-regression):** Category 2 READMEs ride into the wheel automatically (they are
  under `.agents/workflows/**`, force-included). Category 1 templates live under
  `.agents/workflows/templates/` (also force-included), so `tests/test_packaging.py` needs no
  forbidden-list change; optionally assert the new templates are present.
- **House rule:** no em dashes in authored Markdown; hyphens or parentheticals.

## Proposed changes (ordered, validatable)

### 1. Category 1 templates (user-owned, generated no-clobber)
Add templates under source `.agents/workflows/templates/`:
`agents-README.md` (the `.agents/` root), `plans-README.md` (the `.agents/plans/` lifecycle
overview), and one per bucket: `plans-pending-README.md`, `plans-reusable-README.md`,
`plans-executed-README.md`, `plans-superseded-README.md`, `plans-not-executed-README.md`. Content
per the specs below (the per-bucket specs are lifted from the superseded/not-executed IPD).

NOTE (R2-1, plan-review): `.agents/workflows/templates/` is INSIDE the framework namespace, so its
files are copied into every target (verified: the existing `shim-README.md` and
`workflow-artifacts-README.md` already land at `<target>/.agents/workflows/templates/`). These 7
new template files will likewise be present in targets. This is the EXISTING pattern, accepted as-is
here to avoid scope creep (moving generation-templates out of the installed tree is a separate
cleanup, not this IPD). Just be aware the target's `templates/` dir grows by 7 files; that is
intended, not a leak to fix in this plan.

### 2. Write the Category 1 READMEs from the installer (no-clobber)
Add a plan-aware engine function (model on `ensure_workflow_artifacts_readme`, which already has
`plan.source_root`) that, for each Category 1 dir, writes `<dir>/README.md` from its template if
absent: `.agents/README.md`, `.agents/plans/README.md`, and `.agents/plans/<bucket>/README.md` for
each of the five buckets. Stage when newly created, honor `--dry-run`, never overwrite an existing
file. Call it from the same install orchestration that calls `ensure_workflow_artifacts_readme`
(engine.py:2162, 2264) and `create_setup_artifacts`. Do NOT fold this into `create_setup_artifacts`
(that function lacks `source_root`); keep the mechanics matched to the artifacts-README path.
NOTE the bucket list MUST come from `PLAN_LIFECYCLE_SUBDIRS` (the single source of truth the prior
IPD extends) so it cannot drift from the dirs actually created.

### 3. Category 2 authored capability READMEs (source files, no installer change)
Author `README.md` under source `.agents/workflows/<capability>/` for every top-level capability
that lacks one (all 16 except `release-review/`, which already has one; `.agents/workflows/README.md`
already covers the `workflows/` root). This INCLUDES `templates/`, which gets the short meta-README
described in OQ2 (resolved: yes). Each README: one-screen, states the capability's purpose,
how to invoke it (native `/command` or "read and execute <body>"), and - where the capability has
leaf subdirs - a short "Subdirectories" list explaining each (e.g. `assess/README.md` explains
`lenses/`, `templates/`, `tools/`, `references/`). This satisfies the maintainer's condition that
leaf dirs are clearly explained without each carrying its own file. Keep them consistent with
`index.md` (reference it as the catalog; do not duplicate the full table - P8).

### 4. Reconcile the prior IPD's reserved specs
The superseded/not-executed IPD reserved the five per-bucket README specs "for the follow-on"; this
IPD is that follow-on. Use those specs verbatim for the bucket templates (change #1).

### 5. Add a dated `DECISIONS.md` entry
New `### D<next>. Self-documenting `.agents/` tree: a README per directory` (bold-lead-bullet
format). Record the two-category split and mechanics, the top-level-depth decision (leaves described
by their parent, to bound maintenance and avoid duplicating `index.md`), and under Deliberately NOT
done: per-leaf READMEs. Confirm the next D-number at execution time.

### 6. Tests
- `tests/test_setup_artifacts.py` (or a new `tests/test_readmes.py`): after `aw install` into a
  temp repo, assert each Category 1 README exists (`.agents/README.md`, `.agents/plans/README.md`,
  and one per bucket driven by `engine.PLAN_LIFECYCLE_SUBDIRS`), assert no-clobber (a pre-existing
  user README is preserved), assert idempotent re-run creates nothing new, assert `--dry-run` writes
  nothing. NOTE (R2-3): because the Category 1 READMEs are written by a SEPARATE plan-aware function
  (not `create_setup_artifacts`), they do NOT change `test_engine_returns_created_list`'s
  `.gitkeep`-count assertion; assert the READMEs independently rather than folding into that count.
- `tests/test_installer.py`: assert a representative Category 2 capability README (e.g.
  `.agents/workflows/assess/README.md`) is installed into a target and is pruned/not-orphaned like
  other framework files (mirrors the existing README create/preserve test).
- `tests/test_packaging.py`: optionally assert the new Category 1 templates are bundled in the wheel
  (should be automatic via force-include).

## Directory README content specs

Voice/length mirrors `.agents/workflows/README.md` / `templates/shim-README.md` (short, h1 title,
one bolded guidance line where useful, imperative). Category 1 (generated):

- **`.agents/README.md`** - "Agent tooling for this repo. `workflows/` holds the installed
  agent-workflows framework (managed by `aw install`; do not hand-edit). `plans/` holds YOUR
  Implementation Plan Documents (IPDs) through their lifecycle. See `workflows/index.md` for the
  workflow catalog."
- **`.agents/plans/README.md`** - the lifecycle overview: the five buckets and what each is for,
  the plan-filename naming rule (see the naming-convention note below), `done/` accepted as an alias
  for `executed/`, and the retirement convention (`RETIRED YYYY-MM-DD: <reason>; superseded by
  <path/commit>` + `git mv`; never file an un-run plan in `executed/`; never silently delete).
- **pending/** - "IPDs queued or under review/implementation. Named per the plan-filename
  convention. Move to `executed/` ONLY after the change is implemented, verified, and tested."

NAMING-CONVENTION NOTE (R2-2, plan-review): the filename string these READMEs state MUST match
whichever convention is current at execution time. If the filename-convention IPD
(`20260711-plan-filename-convention-hhmm-nn.md`) has landed, use `YYYYMMDD-HHMM-NN-<slug>.md`
(with the `NN`/`00`-orchestrator + lowercase-kebab rules); otherwise use the then-current
`YYYYMMDD-<slug>.md`. Do NOT hard-code a stale format; check the live D45-successor at execution.
- **executed/** - "IPDs implemented, verified, and tested. Terminal, append-only history; do not
  edit past records. (`done/` is an accepted alias.)"
- **superseded/** - "IPDs REPLACED by a better/subsequent plan - kept for the record, not the live
  path. Prepend `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` and `git mv` here
  (preserve history). Never silently delete."
- **not-executed/** - "IPDs we DELIBERATELY decided not to run (no replacement) - explored/rejected
  or overtaken by events. Same `RETIRED ...` header + `git mv` convention. Never file an un-run plan
  in `executed/`."
- **reusable/** - "Recurring/standing plans, rollouts, and process docs run repeatedly or read
  across sessions. Not a terminal state; entries live here as long as they are reused."

Category 2 (authored, per capability): one screen each, purpose + how-to-invoke + a "Subdirectories"
list for those with leaves. Draft at execution time from each capability body's own description and
`index.md` (do not duplicate the catalog).

## Deferred / out of scope

- **Per-leaf-dir READMEs** (`lenses/`, `personas/`, `tools/`, `templates/`, `references/`).
  Deliberately not done (decision 1): the parent capability README describes them. Bounds the
  ongoing maintenance load and avoids duplicating `index.md` (P6/P8). A future IPD could add them if
  a real need appears.
- **Auto-refresh of Category 1 READMEs on upgrade.** Default is create-if-absent (matches
  `workflow-artifacts/README.md`); a managed/refreshed variant would clobber local edits and is not
  built here.

## Scope check (P6 / P7)

Category 2 is authored files only (no code, no new subsystem). Category 1 reuses the existing
no-clobber artifacts-README mechanic (one small plan-aware function), and drives its bucket list
from `PLAN_LIFECYCLE_SUBDIRS` so it cannot drift. Top-level-only depth bounds the file count
(~15 authored + 7 generated) and keeps `index.md` the single catalog (P8). Nothing project-specific;
the READMEs are neutral and general-case.

## Required tests / validation

Automated: the change-6 tests; full `python3 -m unittest discover -s tests -t .` green. Manual: `aw
install --dry-run` then real into a scratch repo; confirm every `.agents/` dir (root, plans, five
buckets, and each top-level capability) has a README reading correctly; re-run confirms no clobber /
nothing new; confirm a user-authored README in any Category 1 dir is preserved.

## Spec / documentation sync

New DECISIONS entry (change #5). No user-visible WORKFLOW behavior change. `index.md` stays the
catalog; capability READMEs reference it rather than duplicating it (P8).

## Open questions (RESOLVED with the maintainer 2026-07-11)

1. Overview + per-bucket READMEs: **RESOLVED - keep BOTH.** `.agents/plans/README.md` gives the
   whole-lifecycle picture AND each of the five buckets gets its own short README, so a browser
   landing directly in (say) `superseded/` understands it in isolation. Total Category-1 generated
   files: `.agents/README.md` + `.agents/plans/README.md` + 5 bucket READMEs = 7.
2. README for `templates/`: **RESOLVED - YES**, add a short meta-README at
   `.agents/workflows/templates/README.md`: "Source templates the installer copies/generates into
   targets (shim and directory READMEs); not workflows themselves - edit here to change what
   installed repos get." So every top-level dir including the meta-dir is self-documenting.

## Plan-review revisions applied (2026-07-11)

Reviewed by `plan-review`. All claims verified against source: engine line refs (shim README
517/537, `in_framework_namespace` 664-671 = only `.agents/workflows/**`+shim dirs so `.agents/plans`
is never pruned, prune README-skip 730/931, `ensure_workflow_artifacts_readme` 2037-2076 called at
2162/2264), the 16 top-level capability dirs, and that `collect_source_members` installs EVERY file
under `.agents/workflows/` via `rglob` (so authored Category-2 READMEs need zero installer code) all
check out. The two-category / two-mechanic architecture is sound. Fixes applied (all Low RR):

- R2-1 (KISS/consistency): noted that `.agents/workflows/templates/` files are copied into targets
  (verified the existing two templates already land there), so the 7 new templates will too;
  accepted as the existing pattern to avoid scope creep, but now called out rather than silent.
- R2-2 (doc-consistency): the `.agents/plans/README.md` + `pending/` specs no longer hard-code
  `YYYYMMDD-<slug>.md`; they defer to whichever filename convention is live at execution time
  (cross-refs the filename-convention IPD).
- R2-3 (test precision): clarified Category 1 READMEs are written by a separate function and do NOT
  affect `test_engine_returns_created_list`'s count; assert them independently.

No scope or approach changed; the review tightened accuracy and doc-drift resistance. Reviewing is
not executing.

## Approval and execution gate

Proposal only; not auto-executed. Sequenced AFTER the superseded/not-executed IPD. On approval:
implement changes 1-6, run the full suite green, do the manual installer validation, then move this
IPD to `.agents/plans/executed/` with an execution-record summary.
