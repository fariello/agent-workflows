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
- **Doc sites that state the filename rule** (all must be reconciled - P8): `DECISIONS.md` D45 (via a
  new entry, not by editing D45), `AGENTS.md` AGENT-PLANS block (line ~13), `.agents/workflows/
  setup-repo/setup-repo.md:94` ("files are named `YYYYMMDD-<slug>.md`"), `.agents/workflows/assess/
  templates/ipd.md:78-79`, `.agents/workflows/assess/assess.md` (Step 0 lifecycle bullet),
  `.agents/workflows/index.md` (lifecycle mention). Re-grep at execution time to confirm the set.
- **`/setup-repo` seam:** `setup-repo.md:82-104` is Step 1b (Plan/IPD lifecycle). The naming rule is
  stated at :94; the detection list (Step 0, :50-54) checks whether `.agents/plans/*` and the
  lifecycle contract exist. The new "check + offer to normalize filenames" behavior slots into
  Step 1b as an additional conformance check.
- **Helper seam:** `.agents/workflows/setup-repo/tools/setup_tools.py` is an argparse tool
  (`main()` at :180, discrete functions, `--format text|json`). The new normalizer can be a sibling
  module or an extension here (execution-time choice; a dedicated `normalize_plan_names.py` keeps
  concerns separate and is the leaning). It reads neighboring `VERSION` for `--version` like the
  other tools; zero third-party deps.
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
  nonconforming file across the given lifecycle dirs, with collision-safe NN assignment computed
  over the whole batch (so two same-minute legacy files get `01`/`02`, and NEW-format files already
  present are respected when choosing the next free NN).
- `apply(renames, repo_root, use_git) -> list[str]`: performs `git mv` (or filesystem mv if
  untracked), staged not committed; returns actions.
- A CLI: `--repo <dir> --check` (report only, JSON or text, nonzero exit if nonconforming found)
  and `--repo <dir> --apply` (perform the staged renames). `--version` like the sibling tools.
Uses `git log --diff-filter=A --follow --format=%aI -- <file>` (or equivalent) for first-commit
time; guarded so a non-git repo or untracked file falls back to `0000`.

### 2. Wire `/setup-repo` to check + offer normalization (Step 1b)
Extend `setup-repo.md` Step 1b prose: after establishing the lifecycle dirs, run
`normalize_plan_names.py --repo . --check`; if nonconforming files exist, PRESENT the full
old -> new preview, explain the convention, and ASK whether to normalize. On yes, run `--apply`
(staged `git mv`), then remind the user the renames are staged-not-committed. On no, leave
everything and record it as a noted gap. Classify this as its own conformance line
(conformant / files-need-normalizing / not-applicable).

### 3. Update the naming rule everywhere (P8)
Change every doc site in Step 0 from `YYYYMMDD-<slug>.md` to `YYYYMMDD-HHMM-NN-<slug>.md`, including
the `NN`/`00`-orchestrator semantics and the lowercase-kebab slug rule. Update the `/setup-repo`
AGENT-PLANS prose (and this repo's own `AGENTS.md` AGENT-PLANS block) so targets learn the new
convention. Keep `done/` alias language unchanged.

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

## Open questions

1. Helper home: a dedicated `normalize_plan_names.py` (leaning) vs. extending `setup_tools.py`.
   Execution-time call; dedicated module keeps concerns separate and is easier to test.
2. Should `--check` be added to the framework's own `verify`/CI so THIS repo stays conformant going
   forward (a guard against regressions), or is `/setup-repo` + the one-time normalization enough?
   (Leaning: add a lightweight check to this repo's test suite so its own plan names cannot drift.)

## Approval and execution gate

Proposal only; not auto-executed. On approval: implement changes 1-6, run the full suite green, do
the manual validation, normalize this repo's own plan files (previewed), then move this IPD to
`.agents/plans/executed/` (under the NEW name) with an execution-record summary. Optionally run
`/plan-review` first to harden it.
