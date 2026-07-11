# IPD: Extend the plan lifecycle with `superseded/` and `not-executed/`

- Date: 2026-07-10
- Concern: Auditability and honesty of the plan lifecycle - an honest home for plans drafted but never run.
- Scope: Add two terminal lifecycle states (`superseded/`, `not-executed/`) to the plan lifecycle the installer scaffolds and the docs describe; reconcile all docs that currently say "three states"; update the `/setup-repo` AGENT-PLANS prose and this repo's own `AGENTS.md`; add a dated `DECISIONS.md` entry extending D45.
- Status: PENDING (open questions resolved with the maintainer 2026-07-10; scope trimmed - see "Decisions taken" below)
- Note: the per-lifecycle-dir READMEs originally proposed here were SPLIT OUT into a separate follow-on IPD (see "Deferred / out of scope"), so this plan stays lean and focused on the auditability fix.

## Decisions taken (maintainer, 2026-07-10)

These resolve the open questions and trim scope; the body below reflects them:

1. **Two directories** (`superseded/` + `not-executed/`), not one merged `retired/`. The `ls`-level
   visual separation of "replaced" vs "deliberately rejected" is wanted, even though both are
   terminal not-run states. (Keeps the plan's original 5-dir design.)
2. **Split the per-dir READMEs into a separate follow-on IPD.** This IPD ships the dirs + docs only.
   That also removes the `create_setup_artifacts()` template-plumbing wrinkle from THIS plan (adding
   two dirs is a pure tuple extension; no template files are read).
3. **AGENT-PLANS block stays delivered by the LLM `/setup-repo` workflow** (not installer-managed).
   We only update that prose and this repo's own hand-maintained `AGENTS.md`. No new engine
   marker-block generator (that would be its own IPD if ever wanted).
4. **Dir/tuple order:** `pending, executed, superseded, not-executed, reusable`.

## Goal

Give the plan lifecycle an honest home for plans that were **drafted but never run**. Today the lifecycle is binary-plus-reusable - `pending/` (queued) -> `executed/` (ran + verified), with `reusable/` alongside - and there is no correct place for a plan that was **replaced by a better plan** or **deliberately not run**. Such plans currently must either sit in `pending/` (falsely implying "still queued"), be forced into `executed/` (falsely claiming "implemented and verified", a direct auditability defect), or be silently deleted (losing the record of *why we chose not to do something*, which is often as valuable as why we did). This IPD adds `superseded/` and `not-executed/` and wires them into the installer's dir-creation. (Per-directory READMEs that make the buckets self-documenting were split into a separate follow-on IPD - see "Decisions taken".)

## Why

1. **Auditability (the core driver).** A repo whose whole value proposition is reproducible, honest agent process must never file an un-run plan under `executed/`. GUIDING_PRINCIPLES P2 ("honest documentation over aspirational") demands a truthful state for "drafted, not run." The two new states make that state expressible instead of forcing a lie or a deletion.
2. **Two genuinely distinct not-run outcomes.** They are not the same and should not share a bucket:
   - `superseded/` - the plan was **replaced** by a better/subsequent plan (it was not wrong to draft; it is simply no longer the live path). Carries a pointer to its successor.
   - `not-executed/` - we **deliberately decided not to run it**, with no replacement (explored, rejected, or overtaken by events).
3. **Never silently delete process history.** Retiring a plan should preserve it with a recorded reason, `git mv`'d (history intact), not `rm`'d.
4. **Orientation in target repos (addressed by the split-out follow-on).** The installer creates empty `.gitkeep`-only lifecycle dirs today; a developer/agent browsing `.agents/plans/superseded/` has no in-repo explanation of what belongs there or how to retire a plan into it. A one-screen README per dir fixes that (mirrors the 2026-07-09 target-directory-READMEs precedent); that work is the separate follow-on IPD, not this one. Meanwhile the `/setup-repo` AGENT-PLANS prose (change #2) documents the buckets.
5. **Real, demonstrated need.** The consuming project `a-private-repo` hit exactly this: a reshaped IPD (`build-07`) was superseded by two successors and had nowhere honest to go; its AGENTS.md already had to describe both `superseded` and `not-executed` by hand. This IPD lifts that ad-hoc need into the framework's installed convention.

## Project conventions discovered (Step 0)

- **Lifecycle source of truth:** `DECISIONS.md` **D45** (lines ~1327-1353) defines the THREE states (`pending`/`reusable`/`executed`; `done/` an accepted alias for `executed/`) and the `YYYYMMDD-<slug>.md` filename rule. This IPD extends D45 and gets its own dated entry (next after the latest D-number).
- **Installer dir-creation seam:** `agent_workflows/engine.py:1970` -
  `PLAN_LIFECYCLE_SUBDIRS = ("pending", "reusable", "executed")`; iterated by
  `create_setup_artifacts()` (engine.py:2079-2114) to write `.agents/plans/<sub>/.gitkeep`
  no-clobber (`_create_if_absent`, engine.py:2018-2034), staged not committed, `--dry-run`-aware.
  Extending the tuple is therefore the entire mechanical change for the two new dirs; the
  `.gitkeep`s for them are created automatically.
- **README-per-dir precedent (relevant to the SPLIT-OUT follow-on, not this IPD):** IPD
  `.agents/plans/executed/20260709-target-directory-readmes.md` established bundling README
  templates under source `.agents/workflows/templates/` and writing them from the installer
  no-clobber "so the installer code remains clean and free of inline markdown strings." NOTE a
  wrinkle the follow-on must resolve: `create_setup_artifacts(repo_root, use_git, dry_run)` has NO
  `source_root`, whereas the template-reading precedent (`ensure_workflow_artifacts_readme`, takes
  `plan`) reads `plan.source_root/templates/`. Per-dir READMEs thus need `source_root`/`plan`
  threaded in (or the rejected inline-string approach). That plumbing lives in the follow-on IPD,
  NOT here.
- **AGENTS.md:** two managed blocks. `AGENT-WORKFLOWS` (installer-generated by
  `agents_pointer_block()`, engine.py:544-556). **`AGENT-PLANS`** (AGENTS.md:9-17) is
  **hand-edited** - no code emits it; the LLM `/setup-repo` workflow adds it to targets
  (setup-repo.md:97-102). It currently enumerates the three states; it is the contract to extend.
- **Docs that currently say "three states"** (P8 single-source-of-truth: all must be reconciled):
  AGENTS.md:9-17, `DECISIONS.md` D45, `.agents/workflows/assess/assess.md:81-91`,
  `.agents/workflows/assess/templates/ipd.md:76-79`, `.agents/workflows/setup-repo/setup-repo.md:52-53,88-104`,
  `.agents/workflows/index.md:105-106`.
- **Tests:** `tests/test_setup_artifacts.py` loops `("pending","reusable","executed")` (line 48) and
  asserts `len(created) == 5` (lines 84-85); `tests/test_installer.py:235-272` is the README
  create + no-clobber + no-prune pattern to copy. No test asserts AGENTS.md block *content*.
  `tests/test_packaging.py` - templates under `.agents/workflows/templates/` ride into the wheel
  via pyproject force-include (no forbidden-list change).
- **Scope note (P7 general case):** `agent-workflows` manages `.agents/plans/` only; it does NOT
  manage `.agents/prompts/`. This IPD is about the PLANS lifecycle. The convention is
  directory-agnostic, so the AGENTS.md/README wording notes that a project which also keeps
  `.agents/prompts/` (or any other lifecycle-bearing dir) SHOULD mirror the same five buckets - but
  the installer only scaffolds `.agents/plans/` (unchanged).

## Proposed changes (ordered, validatable)

### 1. Add the two states to the installer's dir set
`engine.py:1970` - extend to (in the decided order):
`PLAN_LIFECYCLE_SUBDIRS = ("pending", "executed", "superseded", "not-executed", "reusable")`.
(`not-executed` is a valid path segment; hyphen is fine.) `create_setup_artifacts` then creates
`.agents/plans/{superseded,not-executed}/.gitkeep` no-clobber automatically. This is the entire
code change - no template plumbing, no signature change.

### 2. Extend the `/setup-repo` AGENT-PLANS prose and this repo's own `AGENTS.md`
The `AGENT-PLANS` block stays delivered by the LLM `/setup-repo` workflow (decision 3), NOT the
installer. Update:
- `/setup-repo`'s prose (setup-repo.md:88-104) so the AGENT-PLANS block it writes into TARGET repos
  enumerates the FIVE states, states the `superseded` vs `not-executed` distinction, and the rules:
  "never file an un-run plan in `executed/`", "never silently delete process history", and the
  retirement convention (prepend `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` and
  `git mv` the file into `superseded/` or `not-executed/`, preserving history).
- This repo's own hand-maintained `AGENTS.md:9-17` to match (it is the live example).

### 3. Reconcile every "three states" doc site (P8)
Update the doc sites listed in Step 0 to the five-state lifecycle, referencing the new DECISIONS
entry. Keep `done/` as the documented alias for `executed/` (unchanged). Sites that ENUMERATE the
lifecycle states (verified during plan-review, 2026-07-10; these are the complete set):
- `.agents/workflows/assess/assess.md:85` ("canonical three-state lifecycle ...").
- `.agents/workflows/setup-repo/setup-repo.md:51` and `:89` (Step 0 detection + Step 1b creation;
  both say "three-state" / list the three).
- `.agents/workflows/assess/templates/ipd.md:76-78` (the lifecycle-move guidance).
- `.agents/workflows/index.md:105-106` (the setup-repo capability description listing
  `pending/ + reusable/ + executed/`).
- D45 is NOT edited (append-only history, P4); the NEW DECISIONS entry (change #4) carries the
  extension and is referenced from the updated sites.

Verified during plan-review that `ARCHITECTURE.md` and `README.md` do NOT enumerate the state set
(they only reference `pending/` and "execution" in pipeline diagrams, and use "reusable" to describe
workflows, not the lifecycle bucket), so they need no change. `prompts/*` are historical reference
material, out of scope. Do a final `grep -rl "reusable" --include=*.md` at execution time to confirm
no new enumerating site has appeared since.

### 4. Add a dated `DECISIONS.md` entry (extends D45)
New `### D<next>. Plan lifecycle gains `superseded/` and `not-executed/``, in the repo's
bold-lead-bullet format (Context / Decision / Applied to this repo / Forward-facing docs updated /
Historical records untouched / Deliberately NOT done), referencing and extending D45. It MUST
record:
- **Why TWO directories, not one merged `retired/`** (the `ls`-level visual separation of "replaced"
  vs "deliberately rejected" was chosen deliberately over header-only disambiguation), so a future
  reader does not "simplify" it back and lose the distinction.
- The `superseded/` vs `not-executed/` semantics and the `RETIRED YYYY-MM-DD: <reason>; superseded
  by <path/commit>` + `git mv` retirement convention (never file un-run in `executed/`, never
  silently delete).
- Under **Deliberately NOT done**: the per-dir READMEs (split to a follow-on IPD) and any
  installer-managed AGENT-PLANS block (delivery stays via LLM `/setup-repo`).
- Confirm the correct next D-number at execution time (latest committed is D46; a newer entry may
  have landed - use the actual next integer).

### 5. Tests
- `tests/test_setup_artifacts.py`, two edits (verified against the current file during plan-review):
  - `test_install_creates_all_artifacts_and_guidance` (loop at line 48): add `superseded` and
    `not-executed` to the `for sub in (...)` tuple so the two new dirs' `.gitkeep`s are asserted.
  - `test_engine_returns_created_list` (assertion at lines 84-85): change `len(created) == 5` to
    `== 7` (five plan-dir gitkeeps + `.gitleaksignore` + secret-scan CI). Update the inline comment.
  - `test_idempotent_rerun_creates_nothing_new`, `test_no_clobber_preserves_existing_files`, and
    `test_dry_run_reports_without_writing` need NO change (they assert emptiness / preservation /
    dry-run-shape, all order- and count-independent), but re-run them to confirm green.
- No README test and no packaging-template change here - those move to the follow-on IPD.

## Directory README content specs (RESERVED for the split-out follow-on IPD)

These drafted specs are NOT built in this IPD (the per-dir READMEs were split out - decision 2).
They are kept here so the follow-on IPD can reuse them verbatim. Voice/length mirrors
`templates/shim-README.md` / `workflow-artifacts-README.md` (short, h1 title, one bolded guidance
line, imperative). Each ~6-10 lines:

- **pending/** - "Implementation Plan Documents (IPDs) queued or under review/implementation. Named
  `YYYYMMDD-<slug>.md`. Move to `executed/` ONLY after the change is implemented, verified, and
  tested (with a post-execution summary)."
- **executed/** - "IPDs that were implemented, verified, and tested. Terminal, append-only history;
  do not edit past records. (`done/` is an accepted alias.)"
- **superseded/** - "IPDs REPLACED by a better/subsequent plan - kept for the record, not the live
  path. On retiring, prepend `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` and
  `git mv` here (preserve history). Never silently delete."
- **not-executed/** - "IPDs we DELIBERATELY decided not to run (no replacement) - explored/rejected
  or overtaken by events. Same `RETIRED …` header + `git mv` retirement convention. Never file an
  un-run plan in `executed/` (that falsely claims implementation)."
- **reusable/** - "Recurring/standing plans, rollouts, and process docs executed repeatedly or read
  across sessions. Not a terminal state; entries live here as long as they are reused."

## Deferred / out of scope

- **Per-lifecycle-dir READMEs (SPLIT OUT into a follow-on IPD).** Shipping a README into every
  `.agents/plans/*` dir is independent of the auditability fix and adds template files, packaging
  surface, tests, and the `create_setup_artifacts()` `source_root` plumbing wrinkle noted in Step 0.
  It gets its own focused IPD: `20260711-agents-tree-directory-readmes.md`, which broadened during
  scoping to document the WHOLE installed `.agents/` tree (a `.agents/README.md`, the
  `.agents/plans/` family incl. the two new buckets, and one authored README per top-level
  `.agents/workflows/<capability>/`). The per-bucket content specs above are reserved for it. Rationale for splitting: keep this auditability change lean and
  low-risk (decision 2).
- **Installer-managed AGENT-PLANS block.** Making `aw install` emit/refresh a marker-delimited
  AGENT-PLANS block (like AGENT-WORKFLOWS) so install-only repos get the lifecycle contract
  deterministically is a bigger change with its own engine generator + idempotent-refresh + tests.
  Deferred (decision 3); delivery stays via the LLM `/setup-repo`. Could be a future IPD.
- **`.agents/prompts/` scaffolding.** `agent-workflows` does not manage a prompts dir; this IPD does
  not add one. The convention is documented as directory-agnostic so a consuming project can mirror
  it under `.agents/prompts/` by hand.
- **Automated retirement tooling** (an `aw retire <plan> --superseded-by …` command). Nice future
  ergonomics; the convention (header + `git mv`) is manual for now.

## Scope check (P6 KISS / P7 general case)

Five dirs may look like scope creep; each earns its place: `pending`/`executed`/`reusable` exist;
`superseded` vs `not-executed` are genuinely distinct not-run outcomes and are already needed in the
wild (a-private-repo). The maintainer chose two dirs over one merged `retired/` for `ls`-level clarity
(decision 1). After splitting out the READMEs (decision 2), THIS IPD is a one-tuple edit + doc
reconciliation + a `/setup-repo` prose update + a DECISIONS entry - no new code paths, no template
plumbing, no new subsystem. General-case: nothing project-specific; the prose is neutral.

## Required tests / validation

**Automated:** the `test_setup_artifacts.py` update in change #5; full
`python3 -m unittest discover -s tests -t .` green. **Manual:** run the installer (`--dry-run` then
real) into a scratch repo; confirm all five `.agents/plans/*` dirs exist with `.gitkeep`; re-run and
confirm no clobber / nothing new created; confirm the `/setup-repo` AGENT-PLANS prose and this
repo's `AGENTS.md` read five states; confirm a hand `git mv` of a plan into `superseded/` with a
`RETIRED …` header reads cleanly.

## Spec / documentation sync

All "three states" sites reconciled (change #3); DECISIONS entry added (change #4); `/setup-repo`
prose + this repo's `AGENTS.md` updated (change #2). This satisfies P8 (single source of truth; no
drift). The per-dir READMEs are handled by the split-out follow-on IPD.

## Open questions (RESOLVED with the maintainer 2026-07-10 - see "Decisions taken")

1. Retired-plan model: **RESOLVED** - two dirs (`superseded/` + `not-executed/`), not one merged
   `retired/` (decision 1).
2. Per-dir READMEs bundled or split: **RESOLVED** - split into a follow-on IPD; this plan ships dirs
   + docs only (decision 2). (This also settles the earlier create-if-absent-vs-managed sub-question,
   which now lives in the follow-on.)
3. AGENT-PLANS delivery: **RESOLVED** - stays LLM `/setup-repo`-delivered; not installer-managed
   (decision 3).
4. Dir/tuple order: **RESOLVED** - `pending, executed, superseded, not-executed, reusable`
   (decision 4).

## Plan-review revisions applied (2026-07-10)

Reviewed by `plan-review` after the scope trim. All plan claims were re-verified against source:
`PLAN_LIFECYCLE_SUBDIRS` at `engine.py:1970` is used ONLY by the two creation loops (2095, 2104) -
no ordering/membership dependency elsewhere, and plan dirs are outside the framework namespace so
`prune_stale`/`uninstall_repo` never touch them, making the tuple edit fully safe. The
`test_setup_artifacts.py` line refs (loop at 48; `== 5` at 84-85) and the doc-site line refs
(`assess.md:85`, `setup-repo.md:51/89`, `ipd.md:76-78`, `index.md:105-106`) are accurate. Fixes
applied in place (all Low Remediation Risk):

- PR-1 (doc-sync completeness, P8): broad `grep` found `ARCHITECTURE.md` and `README.md` also
  mention "reusable"/the lifecycle, but VERIFIED neither ENUMERATES the state set (workflow-"reusable"
  wording + `pending/`-only pipeline diagrams), so they need no change. Recorded this in change #3
  with the exact site list and a "re-grep at execution time" guard so the P8 reconciliation is
  provably complete.
- PR-2 (durability of the design rationale, P4): change #4 now REQUIRES the DECISIONS entry to
  record WHY two dirs and not one merged `retired/`, so a future reader cannot silently collapse the
  distinction. Also added a "confirm the next D-number at execution time" note (latest committed is
  D46; newer entries may have landed).
- PR-3 (test precision): change #5 now names the two exact test methods to edit
  (`test_install_creates_all_artifacts_and_guidance` loop; `test_engine_returns_created_list`
  5->7 count) and states the other three tests need no change but must be re-run green.

The architecture (a pure tuple extension + doc reconciliation, READMEs split out) is sound and
low-risk; no scope or approach changed in this review. Reviewing is not executing.

## Approval and execution gate

Open questions are resolved and scope is trimmed; the plan is ready for a final review/approval.
Do not implement until approved. On approval: implement changes 1-5, run the full test suite green,
do the manual installer validation, then move this IPD to `.agents/plans/executed/` with an
execution-record summary. Draft the split-out per-dir-README follow-on IPD separately.
