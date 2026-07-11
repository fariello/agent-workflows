# IPD: Plan filename convention `YYYYMMDD-HHMM-NN-<slug>.md` + `/setup-repo` normalization

- Date: 2026-07-11
- Concern: A more precise, collision-proof plan-file naming convention, and a guided, safe way to
  bring existing installed repos into conformance. Auditability + honest identity of plan files
  (P2), self-documenting/learn-as-you-go (P3), safety/reversibility of the rename (P10).
- Scope: (1) Change the documented plan-filename convention from `YYYYMMDD-<slug>.md` (D45) to
  `YYYYMMDD-HHMM-NN-<slug>.md`; (2) add a DETERMINISTIC Python helper that scans a repo's plan
  lifecycle dirs, reports files whose names do not conform, and computes + (on confirmation)
  performs `git mv` normalization; (3) wire `/setup-repo` to run that check and offer to normalize;
  (4) reconcile all doc sites + a new DECISIONS entry. Does NOT build an `aw` CLI verb (noted as a
  later follow-on).
- Status: PENDING (convention + behavior decided interactively with the maintainer 2026-07-11; see
  "Decisions taken"). Independent of the two other pending IPDs; see "Sequencing".
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Self-note: under the NEW convention this very file would normalize to something like
  `20260711-HHMM-01-plan-filename-convention-hhmm-nn.md`; it is named in the CURRENT `YYYYMMDD-<slug>`
  scheme (consistent with its siblings) and would be picked up by the normalizer once adopted.

## Decisions taken (maintainer, 2026-07-11)

1. **Format:** `YYYYMMDD-HHMM-NN-<descriptive slug>.md`. `YYYYMMDD` = date, `HHMM` = creation time
   (24h), `NN` = a two-digit sequence, `<slug>` = lowercase kebab-case.
2. **`NN` scope:** per `YYYYMMDD-HHMM` timestamp (distinguishes files created in the same minute).
   `00` is RESERVED for an orchestrator prompt/plan (a top-level plan coordinating the `01+` child
   plans of the same timestamp); ordinary plans start at `01`.
3. **`00` reservation is convention-only, NOT enforced.** The validator treats `00` as a valid NN
   but does not try to verify a `00` file "is really" an orchestrator (human judgment). Legacy files
   normalize to `01+`, never `00`, unless the user explicitly designates one.
4. **Slug rule:** lowercase, `[a-z0-9-]` only, hyphen-separated. Normalizing a nonconforming slug
   lowercases it and collapses runs of non-`[a-z0-9]` to a single hyphen
   (e.g. `My Plan_v2` -> `my-plan-v2`), trimming leading/trailing hyphens.
5. **Legacy fill (`YYYYMMDD-<slug>` -> new):** derive `HHMM` from the file's FIRST git-commit time
   (UTC); if untracked or git unavailable, fall back to `0000`. Assign `NN` by ordering files that
   collide on the same resulting `YYYYMMDD-HHMM` (`01, 02, ...`), stable-sorted by existing name.
6. **Scope of governance + scan:** ALL plan lifecycle dirs -
   `pending/ reusable/ executed/ superseded/ not-executed/` (and the `done/` alias if present).
   Historical/terminal files ARE included in the scan and MAY be normalized, but every rename is
   previewed and confirmed (P4 history is preserved via `git mv`, not violated by a rename).
7. **Rename mechanics + safety:** `/setup-repo` shows a full preview (old -> new for every affected
   file across all dirs), asks for confirmation, then `git mv`s each (history-preserving), staging
   but NEVER committing (matches the installer's stage-not-commit posture). Untracked files use a
   plain filesystem move. The user reviews and commits.
8. **Where the logic lives:** a DETERMINISTIC Python helper (scan/parse/plan/execute), which the
   LLM `/setup-repo` prose drives for the ask-user interaction. An `aw plans normalize` /
   `--check` CLI verb is a natural later follow-on, noted but NOT built here.
9. **Sequencing:** independent IPD; sequence-agnostic vs. the two other pending IPDs; reconcile the
   shared doc sites against whichever lands first (see "Sequencing").

## Goal

Give plan files a precise, sortable, collision-proof identity - a batch of plans created in one
session (an orchestrator `00` plus its `01+` children, all sharing one `YYYYMMDD-HHMM`) reads as a
group, and no two files can silently collide on the same date. Then make conformance easy and safe:
`/setup-repo` detects any nonconforming plan files in an installed repo, shows exactly what would be
renamed, and - only on the user's say-so - normalizes them with history-preserving `git mv`, staged
for the user to review and commit.

## Why

1. **Collision-proofing and ordering.** `YYYYMMDD-<slug>` cannot distinguish two plans authored the
   same day without slug luck, and does not order within a day. `YYYYMMDD-HHMM-NN` sorts
   chronologically and is unique per minute+sequence.
2. **Orchestrator/child grouping.** Real multi-plan sessions (an orchestrator that spawns child
   plans) had no way to show the relationship in the filename. `00` = orchestrator, `01+` = children
   sharing the timestamp makes the batch self-evident in a plain `ls`.
3. **Honest, safe migration (P2 + P10).** A convention change is worthless if existing repos drift.
   `/setup-repo` making conformance a previewed, confirmed, reversible `git mv` (never a silent or
   auto-committed rewrite) is what makes adopting it painless without risking history or surprising
   the user.
4. **Deterministic + testable (repo pattern).** Filename parsing/normalization is mechanical, so it
   belongs in a Python helper with unit tests, not ad hoc LLM prose (consistent with
   `setup_tools.py`, `scan_secrets.py`, etc.).

## Project conventions discovered (Step 0)

- **Current convention (to be revised):** `YYYYMMDD-<slug>.md`, established by `DECISIONS.md` **D45**
  (line ~1327). There is NO code today that validates or generates plan filenames - the convention
  is documented prose only. This IPD introduces the first mechanical enforcement.
- **Doc sites that state the filename rule** (verified during plan-review - grep for
  `YYYYMMDD-<slug>` found EXACTLY these four forward-facing sites; `index.md` does NOT state the
  filename rule, only the lifecycle dirs, so it is NOT in this set):
  - `.agents/workflows/assess/assess.md:89`
  - `.agents/workflows/setup-repo/setup-repo.md:94`
  - `.agents/workflows/assess/templates/ipd.md:79`
  - `AGENTS.md:13` (the AGENT-PLANS block; also update the `/setup-repo` prose that WRITES this
    block into targets, setup-repo.md Step 1b).
  Plus a new `DECISIONS.md` entry (NOT by editing D45 - P4). Re-grep `YYYYMMDD` at execution time to
  confirm no new site has appeared.
- **`/setup-repo` seam:** `setup-repo.md:82-104` is Step 1b (Plan/IPD lifecycle). The naming rule is
  stated at :94; the detection list (Step 0, :50-54) checks whether `.agents/plans/*` and the
  lifecycle contract exist. The new "check + offer to normalize filenames" behavior slots into
  Step 1b as an additional conformance check.
- **Helper seam:** `.agents/workflows/setup-repo/tools/setup_tools.py` is an argparse tool
  (`main()` at :180, discrete functions, `--format text|json`). The new normalizer is a DEDICATED
  sibling module `.agents/workflows/setup-repo/tools/normalize_plan_names.py` (OQ1 resolved: keep it
  separate from `setup_tools.py` for cleaner concerns + easier testing). It reads neighboring
  `VERSION` for `--version` like the other tools; zero third-party deps.
- **Lifecycle dirs (post the superseded/not-executed IPD):** `PLAN_LIFECYCLE_SUBDIRS` in
  `engine.py` is the single source of truth for the bucket set; the normalizer should scan those
  same dir names (plus `done/`) so it cannot drift.
- **House rule:** no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

### 1. Add a deterministic filename normalizer helper
Add `.agents/workflows/setup-repo/tools/normalize_plan_names.py` (stdlib only, zero deps),
providing:
- `parse_name(filename) -> Parsed | None`: recognizes BOTH the new
  `YYYYMMDD-HHMM-NN-<slug>.md` and the legacy `YYYYMMDD-<slug>.md`; returns structured fields or
  None for unrecognized.
- `is_conformant(filename) -> bool`: True only for the full new format with a valid lowercase slug.
- `normalized_name(path, git_time=None) -> str`: computes the conforming name, filling `HHMM` from
  the file's first git-commit time (UTC) or `0000`, assigning `NN` per same-minute collision order
  (never `00` for auto-normalized files), and normalizing the slug to lowercase kebab-case.
- `scan(repo_root, subdirs) -> list[Rename]`: returns the (old -> new) rename plan for every
  nonconforming file across the given lifecycle dirs. Edge rules (R3-2..R3-5, plan-review):
  - **Idempotency (R3-3):** files that are already conformant are EXCLUDED from the plan entirely
    (never re-timed or re-numbered), so a second run is a no-op.
  - **NN assignment (R3-2):** compute the next free NN per `YYYYMMDD-HHMM` over the WHOLE batch,
    counting BOTH already-present conformant files at that timestamp AND earlier entries in this
    same plan; assign in a deterministic stable order (sort candidates by existing filename). Never
    assign `00` (reserved for a human-designated orchestrator).
  - **Target-collision (R3-4):** if a computed target name already exists on disk (a coincidence,
    or a prior partial run), advance NN to the next free value; if that is impossible or ambiguous,
    record the file as a CONFLICT and skip it (report it; do not clobber). `git mv` must never
    overwrite an existing path.
  - **Empty slug (R3-5):** if slug-normalization yields an empty string (e.g. an all-punctuation
    slug), use the fallback slug `untitled`.
- `apply(renames, repo_root, use_git) -> list[str]`: performs `git mv` (or filesystem mv if
  untracked), staged not committed; returns actions. Aborts an individual move (and reports) if its
  target already exists, so nothing is ever clobbered.
- A CLI: `--repo <dir> --check` (report only, JSON or text, nonzero exit if nonconforming found)
  and `--repo <dir> --apply` (perform the staged renames). `--version` like the sibling tools.
First-commit time (R3-1, plan-review - the naive command is wrong on TWO axes, both verified live):
- **Timezone:** `%aI`/`%aI` emit the author's LOCAL tz (e.g. `-04:00`), but HHMM must be UTC
  (decision 1). Use `TZ=UTC git log ... --date=format-local:%Y%m%d-%H%M --format=%ad` (the
  `format-local` + `TZ=UTC` combination converts to UTC), NOT `%aI`.
- **`--follow` quirk:** `--follow` combined with `--diff-filter=A` can report a DIFFERENT (earlier)
  commit than the file's first appearance under its current path, because `--follow` traces through
  prior renames (verified: on a renamed plan file the two commands returned `10:37` vs `20:27`).
  DECISION FOR EXECUTION: use `--follow` deliberately (we WANT the original creation time across the
  `done/`->`executed/` and `YYYY-MM-DD`->`YYYYMMDD` renames this repo already did), and take the
  EARLIEST such author time. Document this choice in code so it is not "fixed" into the wrong one.
- Concrete: `TZ=UTC git -C <repo> log --follow --diff-filter=A --date=format-local:%Y%m%d-%H%M
  --format=%ad -- <file>` then take the last (oldest) line. Guard: non-git repo, untracked file, or
  empty output -> fall back to `0000`. Use author-date (`%ad`), not commit-date, as the creation
  proxy.

### 2. Wire `/setup-repo` to check + offer normalization (Step 1b)
Extend `setup-repo.md` Step 1b prose: after establishing the lifecycle dirs, run
`normalize_plan_names.py --repo . --check`; if nonconforming files exist, PRESENT the full
old -> new preview, explain the convention, and ASK whether to normalize. On yes, run `--apply`
(staged `git mv`), then remind the user the renames are staged-not-committed. On no, leave
everything and record it as a noted gap. Classify this as its own conformance line
(conformant / files-need-normalizing / not-applicable).

### 3. Update the naming rule everywhere (P8)
Change the four verified doc sites in Step 0 (`assess.md:89`, `setup-repo.md:94`, `ipd.md:79`,
`AGENTS.md:13`) from `YYYYMMDD-<slug>.md` to `YYYYMMDD-HHMM-NN-<slug>.md`, including the
`NN`/`00`-orchestrator semantics and the lowercase-kebab slug rule. Update the `/setup-repo` Step 1b
prose that WRITES the AGENT-PLANS block into targets so targets learn the new convention. Keep
`done/` alias language unchanged. `index.md` needs no change (it does not state the filename rule).

### 4. New `DECISIONS.md` entry (extends/refines D45)
`### D<next>. Plan filename convention: `YYYYMMDD-HHMM-NN-<slug>` + `/setup-repo` normalization`.
Record the format and every sub-rule (NN per-minute, 00=orchestrator convention-only, legacy fill
from git time, lowercase-kebab slug, all-buckets scope, git-mv-staged-not-committed migration), that
it refines D45's filename rule (D45 not edited - P4), and Deliberately NOT done: the `aw` CLI verb
and enforced-orchestrator semantics. Confirm the next D-number at execution time.

### 5. Normalize THIS repo's own plan files
Run the new helper against this repo's `.agents/plans/*` and, with the preview, `git mv` its
existing `YYYYMMDD-<slug>.md` files to the new format (dogfooding; this repo is the reference
example). Executed plans included, each rename previewed. Historical DECISIONS text and
workflow-artifacts are NOT touched (only plan filenames).

### 6. Tests
- New `tests/test_normalize_plan_names.py`: `parse_name`/`is_conformant` accept the new format and
  the legacy format, reject junk; `normalized_name` fills HHMM from an injected git-time and `0000`
  on fallback, assigns NN by same-minute order (never 00), and slug-normalizes
  (`My Plan_v2` -> `my-plan-v2`); `scan` produces a correct collision-safe rename plan over a temp
  tree with mixed conforming/legacy/same-minute files across multiple buckets; `apply` performs the
  moves (git-tracked -> staged `git mv`; untracked -> filesystem mv) and leaves nothing committed;
  `--check` exits nonzero when nonconforming files exist, zero when clean; already-conforming files
  are left untouched (idempotent).
- Reuse the `tests/support.py` git-repo helpers; stdlib unittest only.

### 7. CI drift-guard for THIS repo (OQ2 resolved: yes)
Add a test (e.g. in `tests/test_normalize_plan_names.py` or a small `tests/test_plan_names.py`) that
walks this repo's own `.agents/plans/*` and asserts every plan file is `is_conformant`, failing if a
nonconforming name is ever committed. This keeps the reference repo exemplary and prevents silent
drift after adoption. It runs in the existing suite (so the cross-OS CI already covers it); no new
workflow file needed. It must run AFTER change #5 (this repo's files normalized) or it would fail on
the pre-normalization names. Downstream repos are unaffected - they rely on the `/setup-repo` check,
not this test.

## Directory / format spec (authoritative)

`YYYYMMDD-HHMM-NN-<slug>.md`

- `YYYYMMDD` - creation date, UTC.
- `HHMM` - creation time, 24-hour, UTC (from git first-commit time when normalizing legacy files).
- `NN` - two-digit sequence within that exact `YYYYMMDD-HHMM`. `00` reserved (by convention, not
  enforced) for an orchestrator prompt/plan; ordinary plans start at `01`.
- `<slug>` - lowercase kebab-case, `[a-z0-9-]+`, no leading/trailing hyphen.
- Example batch: `20260711-1430-00-migrate-orchestrator.md` (orchestrator) with
  `20260711-1430-01-migrate-schema.md`, `20260711-1430-02-migrate-backfill.md` (its children).

## Deferred / out of scope

- **`aw plans normalize` / `aw plans check` CLI verb.** A deterministic CLI surface for the same
  helper is a natural ergonomic follow-on, but this IPD delivers the helper + `/setup-repo` wiring;
  the CLI verb is deferred to keep scope bounded. (Noted so it is not lost.)
- **Enforcing that `00` is an orchestrator.** Convention-only (decision 3); a machine-checkable
  "is-orchestrator" rule is fuzzy and deferred.
- **Renaming non-plan lifecycle-bearing dirs** (e.g. a project's `.agents/prompts/`). The convention
  is documented as directory-agnostic, but the helper scans only the plan buckets; a project can
  point it elsewhere later.
- **Auto-committing the renames.** Never; stage-not-commit is the posture (P10).

## Scope check (P6 / P7)

The format change is a one-line-per-doc-site edit. The genuinely new surface is one small,
well-bounded, testable Python helper (parse/normalize/scan/apply) plus `/setup-repo` prose - no new
subsystem, no dependency, no CLI surface (deferred). The normalizer scans the buckets from the
single source of truth (`PLAN_LIFECYCLE_SUBDIRS` + `done/`) so it cannot drift. General-case:
nothing project-specific; every installed repo benefits identically.

## Required tests / validation

Automated: change-6 tests; full `python3 -m unittest discover -s tests -t .` green. Manual: in a
scratch repo with a mix of legacy `YYYYMMDD-<slug>.md`, an uppercase/underscore slug, and two
same-minute files, run `--check` (see the preview + nonzero exit), run `/setup-repo` and confirm the
ask-and-normalize flow, verify the resulting names conform and history is preserved
(`git log --follow` on a renamed file), and confirm nothing was committed. Re-run `--check` -> clean
(idempotent).

## Spec / documentation sync

All Step 0 doc sites reconciled (change #3); `/setup-repo` + this repo's `AGENTS.md` updated
(changes #2, #3); DECISIONS entry added (change #4); this repo's own plan files normalized
(change #5). Satisfies P8. No user-visible WORKFLOW behavior change beyond the new conformance check.

## Sequencing (vs. the two other pending IPDs)

Independent (decision 9). This changes the filename FORMAT; the superseded/not-executed IPD changes
the lifecycle DIRS; the `.agents`-tree READMEs IPD adds READMEs. They share doc sites (D45,
`assess.md`, `ipd.md`, `setup-repo.md`, `index.md`, `AGENTS.md`), so whichever executes first sets
the baseline and the others reconcile against it - flag this in each execution to avoid doc drift.
Concrete couplings: (a) the normalizer's bucket list should include `superseded/`+`not-executed/`
(so if that IPD has not landed yet, scan the buckets that exist and it will pick up the new ones
once present, since it reads `PLAN_LIFECYCLE_SUBDIRS`); (b) the READMEs IPD's `plans-README.md`
should state the NEW filename convention if this IPD has landed. No hard ordering required.

## Open questions (RESOLVED with the maintainer 2026-07-11)

1. Helper home: **RESOLVED - a dedicated `.agents/workflows/setup-repo/tools/normalize_plan_names.py`
   module** (not folded into `setup_tools.py`), for cleaner separation and easier unit testing.
2. CI drift-guard: **RESOLVED - YES.** Add a check to THIS repo's own test suite that every file in
   `.agents/plans/*` conforms to the new convention, so agent-workflows itself cannot drift back to
   a nonconforming plan filename after adoption. It reuses the normalizer's `is_conformant` (see the
   new change #7). Downstream repos are unaffected (they get the `/setup-repo` check, not our CI).

## Plan-review revisions applied (2026-07-11)

Reviewed by `plan-review`. Claims verified against source: no code validates plan filenames today
(this is net-new); `setup_tools.py` is an argparse tool (`main()` at :180); the filename rule lives
at `assess.md:89`, `setup-repo.md:94`, `ipd.md:79`, `AGENTS.md:13` (NOT `index.md` - corrected);
`/setup-repo` Step 1b (setup-repo.md:82-104) is the wiring seam. Fixes applied (the normalizer core
had real correctness gaps; all Low RR to FIX on paper, and fixing them is what prevents a
data-moving bug):

- R3-1 (BLOCKER-if-unfixed, correctness): the proposed git first-commit-time command was wrong on
  TWO axes, both verified live - `%aI` emits LOCAL tz (HHMM must be UTC) and `--follow` +
  `--diff-filter=A` returns a different commit than the current-path first-add (`10:37` vs `20:27`
  on a renamed file). Pinned the exact `TZ=UTC ... --date=format-local:%Y%m%d-%H%M --format=%ad
  --follow` command, take-the-oldest semantics, and the `0000` fallback.
- R3-2/R3-3/R3-4/R3-5 (correctness/idempotency): specified the `scan` edge rules - already-conformant
  files excluded (idempotent no-op re-run), deterministic per-minute NN assignment counting existing
  conformant files, target-already-exists -> bump-or-report-CONFLICT (never clobber via `git mv`),
  and an `untitled` fallback for an empty normalized slug.
- R3-6 (doc accuracy, P8): corrected the doc-site set to the four verified locations; `index.md`
  removed from the list (it does not state the filename rule).

Verified that dogfooding (change #5) is real: 23 existing plan files in THIS repo would be
normalized. The approach (deterministic helper + `/setup-repo` preview+confirm + staged `git mv`) is
sound; no scope or approach changed in review. Reviewing is not executing.

Open questions then RESOLVED interactively with the maintainer (2026-07-11): OQ1 - dedicated
`normalize_plan_names.py` module (not folded into `setup_tools.py`); OQ2 - YES add a CI drift-guard
to this repo's own suite, added as change #7 (runs after #5).

## Approval and execution gate

Proposal only; not auto-executed. On approval: implement changes 1-7 (note #7, the CI drift-guard,
runs after #5 normalizes this repo's own files), run the full suite green, do the manual validation,
then move this IPD to `.agents/plans/executed/` (under the NEW name) with an execution-record
summary.
