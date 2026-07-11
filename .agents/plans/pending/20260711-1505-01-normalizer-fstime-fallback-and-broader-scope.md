# IPD: normalizer - filesystem-time fallback, broader scan scope, exclusions, and non-numeric renaming

- Date: 2026-07-11
- Concern: Correctness and reach of `normalize_plan_names.py` (the plan-filename normalizer shipped in
  D48). A follow-on that (a) fills the creation time from filesystem stat when there is no git
  commit, instead of `0000`; (b) scans more of the `.agents/` tree with tiered priority and force
  flags; (c) supports exclusion patterns so reference inputs are protected; (d) can rename files
  that do not start with a number, and handle additional legacy date shapes.
- Scope: `.agents/workflows/setup-repo/tools/normalize_plan_names.py` + its tests + the `/setup-repo`
  prose that drives it + docs/DECISIONS. Does NOT change the canonical convention itself
  (`YYYYMMDD-HHMM-NN-<slug>.md`, D48) - only how files are FOUND, TIMED, EXCLUDED, and renamed.
- Status: PENDING (behavior decided interactively with the maintainer 2026-07-11; see "Decisions
  taken"). Follow-on to D48.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Motivation (survey evidence)

A read-only survey of all 23 `a local checkout dir/*/.agents` trees (plans/ + prompts/, `*.md`, excl README) found
391 files. With a loose leading-number regex `^[0-9][^A-Za-z]*`:

- 381 start with a numeric blob, across shapes: `YYYYMMDD-HHMM-` (213), `YYYYMMDD-` (96),
  `YYYYMMDD-HHMM-NN-` (35, canonical), `YYYYMMDD-NN-` (29), `YYYY-MM-DD-` (8).
- 10 do NOT start with a number - ALL under `prompts/`; 6 of those are nested
  `prompts/pending/<suite>/sources/*.md` reference inputs (e.g. `Prompt - Getting to Yes.md`), plus
  `reference-docs-analysis.md`, `prompt_ipd_reviewer.md`, `session-restart-document-generator-prompt.md`,
  and `MASTER-CONTEXT-...-20260711.md`.

Findings that drive this IPD: (1) the offenders are in `prompts/`, which the shipped tool does not
scan; (2) `YYYY-MM-DD-` and `YYYYMMDD-NN-` legacy shapes exist that the current `_LEGACY_RE`
(`^\d{8}-`) does not recognize; (3) some non-numeric files are genuine reference inputs that must NOT
be renamed, so protection must be by structure (nesting) AND pattern (exclusions).

## Decisions taken (maintainer, 2026-07-11)

1. **Time fallback order:** git first-commit (author) time UTC -> `st_birthtime` (if the platform/FS
   exposes it) -> `st_ctime` -> `st_mtime` -> `0000`. Replaces today's straight-to-`0000` fallback.
   All times formatted as UTC `YYYYMMDD-HHMM` (and the DATE part may come from the fs time too when a
   file has no usable date in its name).
2. **Scan scope (tiered) + force flags:** recurse ALL directories under `.agents/`. Priority tiers:
   `plans/` (most important), then `prompts/`, then everything else. Default run targets
   `plans/` + `prompts/`. Flags: `--plans` (force only plans), `--prompts` (force only prompts),
   `--all` (everything under `.agents/`). The maintainer expects "almost all to conform" and assumes
   other users want the same, so broad coverage is the intent - bounded by exclusions.
3. **Recursion + rename eligibility:** walk fully (so nothing is missed in REPORTING), but only
   auto-rename a `*.md` whose IMMEDIATE PARENT is a recognized lifecycle dir
   (`pending/executed/superseded/not-executed/reusable/done`, under a scanned area). Files nested
   deeper (e.g. `.../<suite>/sources/foo.md`) are REPORTED but not renamed unless explicitly opted
   in. This protects reference inputs by structure.
4. **Exclusions:** "everything except those that match X or are in Y directory." Exclusion =
   fnmatch/glob patterns matched against the repo-relative path, with (a) a sensible BUILT-IN default
   set that protects obvious non-plans, (b) additional patterns from config, and (c) repeatable
   `--exclude PATTERN` on the CLI. An excluded file is reported as excluded, never renamed.
5. **Non-numeric renaming:** opt-in `--rename-non-numeric`. Off by default (a non-numeric,
   non-excluded file is reported as NEEDS-DECISION rather than silently renamed). When on, a
   non-numeric file whose parent is a lifecycle dir and which is not excluded is renamed to
   `YYYYMMDD-HHMM-NN-<slug>` using the time-fallback date/time and a slug derived from its old name.

## Project conventions discovered (Step 0)

- Tool today (`.agents/workflows/setup-repo/tools/normalize_plan_names.py`, D48): `LIFECYCLE_SUBDIRS`
  local constant; `_NEW_RE` (canonical) and `_LEGACY_RE = ^\d{8}-<slug>`; `scan(repo_root, subdirs)`
  iterates `PLANS_DIR/<sub>/*.md` (NOT recursive, plans-only); `_time_and_date_for` returns
  `git_first_commit_hhmm(...)` or `f"{parsed.date}-0000"`; `apply` does `git mv` staged, never
  clobbers. Stdlib only, standalone (no import back to the package). CLI: `--repo --format
  --apply --version`.
- `/setup-repo` Step 1b drives it via `--check` -> preview -> ask -> `--apply` (setup-repo.md).
- Config: the CLI (`aw`) has a JSON config at `~/.config/agent-workflows/` (D46) with an `ignore`
  glob list; but this tool is STANDALONE (copied into targets, no package import), so its config
  input must be self-contained. Decision for this IPD: exclusions come from EXACTLY two sources -
  built-in defaults + repeatable `--exclude` CLI flags. No repo-local dotfile and no coupling to the
  `aw` package config in this IPD (N-3: a dotfile mechanism is neither designed nor needed here; if
  a persistent per-repo exclude list is wanted later it is its own small IPD).
- Tests: `tests/test_normalize_plan_names.py` (14) covers parse/slug/scan/apply/idempotent/no-clobber
  + a repo drift-guard. Must extend, keep green.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

### 1. Filesystem-time fallback (decision 1)
Add `fs_stamp(path) -> (date, time)` returning a `("YYYYMMDD", "HHMM")` PAIR (not a hyphen-joined
string - see N-1) that tries `os.stat().st_birthtime` (guard with `getattr(st, "st_birthtime",
None)`; absent on Linux ext4), then `st_ctime`, then `st_mtime`, converting each to UTC.
Rewrite `_time_and_date_for` to return a `(date, time)` PAIR chosen from a SINGLE atomic source, in
order (N-2 - never mix a name-date with a fallback-time):
  1. git first-commit stamp (both date and time), else
  2. `fs_stamp` (both date and time), else
  3. the name's own date if it has one, with time `0000`, else
  4. `("00000000", "0000")` only if truly nothing is available (should not happen: fs stat always
     succeeds for an existing file, so 3/4 are effectively unreachable once fs_stamp is in).
Keep git as the preferred source (true creation across past renames via `--follow`). The caller uses
the returned pair directly; do NOT reconstruct-then-`split("-")` a string (N-1).

### 2. Recognize more legacy shapes (survey finding)
Extend parsing so a small ordered set of legacy regexes recognizes: `YYYYMMDD-<slug>`,
`YYYYMMDD-NN-<slug>` (has NN, no time), `YYYYMMDD-HHMM-<slug>` (has time, no NN), and
`YYYY-MM-DD[-NN]-<slug>` (hyphenated date). At PARSE time, a hyphenated `YYYY-MM-DD` date is
immediately normalized to compact `YYYYMMDD` in the returned `Parsed.date`, so downstream code never
sees a date containing hyphens (N-1: this is what keeps the internal date/time as clean tokens and
avoids any `split("-")` ambiguity). `Parsed` carries `date`/`time`/`nn` as separate fields (already
does); normalization maps each shape to canonical `YYYYMMDD-HHMM-NN-<slug>`, PRESERVING any real
time/NN already present and filling only the missing pieces from the time fallback (change #1).
Ambiguity guard: `YYYYMMDD-NN-` (2-digit) vs `YYYYMMDD-HHMM-` (4-digit) is decided by the digit
count of the first post-date group, so `20260709-01-foo` is read as NN=01 (no time) and
`20260709-1044-foo` as time=1044 (no NN). `is_conformant` stays strict (only the exact canonical
form with a clean lowercase-kebab slug).

### 3. Broader, tiered, flag-controlled scan (decisions 2, 3)
Rework `scan` to walk `.agents/` recursively. Areas: default `plans/` + `prompts/`; `--plans`,
`--prompts`, `--all` (everything under `.agents/`, still rename-eligibility-gated). Recognize the
lifecycle subdir set under any scanned area. Rename-eligible = `*.md` whose IMMEDIATE parent is a
lifecycle dir; deeper files are reported (as `nested`, not renamed) unless `--include-nested` is
given. Report every file with a status: conformant / to-rename / excluded / nested / non-numeric /
conflict.

`--all` reporting noise (N-5): even with `--all`, only files under a recognized lifecycle dir (at any
depth) are REPORTED; the framework tree `.agents/workflows/**` and other non-lifecycle `*.md` are
NOT listed (they are framework-owned and out of the convention's scope). So `--all` widens WHICH
top-level areas under `.agents/` are searched for lifecycle dirs, not "print every markdown file in
.agents/". This keeps `--all` output usable and avoids flooding with hundreds of framework files.
The framework's own `.agents/workflows/` is never a rename target regardless of flags.

### 4. Exclusions (decision 4)
Add `--exclude PATTERN` (repeatable) and a built-in default exclude set (at minimum: `*/sources/*`,
`README.md`, and an all-caps context-doc guard like `*/MASTER-CONTEXT-*`). Exclusions are fnmatch
globs on the repo-relative POSIX path. An excluded file is reported `excluded`, never renamed. A
`--no-default-excludes` escape hatch lets a user opt out of the built-ins.

### 5. Non-numeric renaming (decision 5)
Add `--rename-non-numeric`. Off by default: a non-numeric, non-excluded, lifecycle-parent file is
reported `non-numeric (needs --rename-non-numeric)`. On: rename it to canonical using the
time-fallback date/time and a slug from the old stem (lowercased-kebab; strip a trailing/leading date
if present, e.g. `MASTER-CONTEXT-...-20260711` -> slug `master-context-...`; empty -> `untitled`).
Never touch excluded or nested files even with this flag (nesting needs `--include-nested` too).

### 6. `/setup-repo` prose + docs
Update Step 1b to mention the new flags and that the check now covers `plans/` and `prompts/` by
default, protects reference inputs, and offers `--rename-non-numeric` for stragglers. Update the
tool's module docstring and `--help`. No change to the canonical convention docs (D48 unchanged).

### 7. DECISIONS D50
Record the time-fallback order, the tiered scan + force flags, recursion/eligibility rule, the
exclusion mechanism + built-in defaults, and opt-in non-numeric renaming. Note it refines the D48
tool without changing the convention.

### 8. Tests
Extend `tests/test_normalize_plan_names.py`:
- fs-time fallback: an untracked file with a known `st_mtime` normalizes to that UTC date+time (not
  `0000`); a committed file still uses git time (git wins). Also exercise the `st_birthtime`-absent
  path (Linux) by asserting the helper degrades to `st_ctime`/`st_mtime` without error (N-4).
- new legacy shapes: `YYYYMMDD-NN-`, `YYYYMMDD-HHMM-`, `YYYY-MM-DD-` (and `YYYY-MM-DD-NN-`) all
  normalize correctly, preserving present time/NN; explicitly assert the hyphenated-date case does
  NOT raise (N-1 regression guard) and yields a compact `YYYYMMDD` date; assert the NN-vs-HHMM
  disambiguation (`...-01-` -> NN, `...-1044-` -> time).
- scope: a file under `prompts/pending/` is found by default; `--plans` excludes it; `--all` finds a
  file in a non-lifecycle area only for REPORTING (not rename).
- recursion: a `.../sources/foo.md` is reported `nested` and NOT renamed without `--include-nested`.
- exclusions: `*/sources/*` (default) protects nested inputs; a `--exclude` pattern protects a named
  file; `--no-default-excludes` re-includes.
- non-numeric: off by default -> reported, not renamed; `--rename-non-numeric` renames a top-level
  `foo-bar.md` to a canonical name with a `foo-bar` slug and a fs/`0000` time; still skips excluded.
- idempotency + no-clobber + staged-git-mv still hold; repo drift-guard still green.

## Directory / eligibility spec (authoritative)

- **Scanned areas:** default {`plans`, `prompts`}; `--plans` / `--prompts` force one; `--all` = every
  dir under `.agents/`.
- **Lifecycle dirs:** `pending`, `executed`, `superseded`, `not-executed`, `reusable`, `done`.
- **Rename-eligible:** `*.md` whose immediate parent is a lifecycle dir within a scanned area, not
  excluded. (`--include-nested` also makes deeper files eligible.)
- **Time:** git-first-commit UTC -> `st_birthtime` -> `st_ctime` -> `st_mtime` -> `0000`.
- **Excluded (default):** `*/sources/*`, `README.md`, `*/MASTER-CONTEXT-*` (+ user `--exclude`).

## Deferred / out of scope

- Coupling the standalone tool to the `aw` package JSON config's `ignore` list. The tool stays
  self-contained; exclusions are built-in defaults + `--exclude`. A future IPD could let `aw` pass
  its `ignore` through, but not here.
- Changing the canonical convention (D48) - unchanged.
- Auto-committing renames - never; staged `git mv` only (P10).
- An `aw plans normalize` CLI verb - still deferred (separate follow-on).

## Scope check (P6 / P7)

The convention is unchanged; this is entirely about the normalizer's find/time/exclude/rename logic
- one standalone stdlib tool + tests + prose. Broadening to all-of-`.agents/` is bounded by the
lifecycle-parent eligibility rule + exclusions, so the blast radius of renames stays controlled.
General-case: every installed repo benefits; nothing project-specific.

## Required tests / validation

Automated: change #8; full `python3 -m unittest discover -s tests -t .` green. Manual: run
`--check` (default, then `--all`) against a scratch repo containing a `prompts/pending/<suite>/
sources/*.md` input, an untracked legacy file, a `YYYY-MM-DD-` file, and a non-numeric top-level
file; confirm the preview classifies each correctly (excluded / nested / to-rename / non-numeric);
`--apply --rename-non-numeric` renames only the intended ones via staged `git mv`; re-run is clean.

## Spec / documentation sync

DECISIONS D50 (change #7); `/setup-repo` prose + tool docstring/`--help` (change #6). The canonical
convention docs (D48 sites) are unchanged.

## Open questions

1. Built-in default exclude set: is `*/sources/*`, `README.md`, `*/MASTER-CONTEXT-*` the right
   starting set, or should it be broader/narrower? (Proposed as above; easy to extend.)
2. When `--rename-non-numeric` derives a slug from a name that ENDS in a date
   (`MASTER-CONTEXT-...-20260711.md`), should that trailing date become the file's date (likely yes,
   more accurate than fs time)? Proposed: if the name contains a parseable YYYYMMDD anywhere, prefer
   it for the DATE and use the time-fallback only for HHMM.

## Plan-review revisions applied (2026-07-11)

Reviewed by `plan-review`. All claims verified against the shipped tool: `_LEGACY_RE =
^\d{8}-<slug>`, `Parsed(date,time,nn,slug,conformant)`, `_time_and_date_for` returns git stamp or
`f"{parsed.date}-0000"`, `git_first_commit_hhmm` uses `--follow`, and `scan` iterates
`PLANS_DIR/<sub>/*.md` non-recursively (line 205) then does `stamp.split("-")` (line 229). The
approach is sound; findings fixed in place (all Low Remediation Risk to fix on paper):

- N-1 (MEDIUM, correctness): the current code round-trips the stamp as a hyphen-joined string and
  splits it with `stamp.split("-")`; adding `YYYY-MM-DD` parsing and fs-date sourcing would risk a
  `ValueError` (too many hyphens). Fixed: date/time are now carried as a structured `(date, time)`
  pair end-to-end, and hyphenated dates are compacted to `YYYYMMDD` AT PARSE TIME, so no downstream
  `split("-")` ambiguity remains. Added a regression test.
- N-2 (MEDIUM, correctness): pinned the fallback to a SINGLE atomic source per file (git gives both
  date+time; else fs gives both; else name-date + `0000`), so a name-date is never mixed with a
  fallback-time.
- N-3 (LOW, KISS/honesty): removed the vague "optionally a repo-local dotfile" from the exclusion
  design; exclusions are exactly built-in defaults + `--exclude` (a dotfile would be its own IPD).
- N-4 (LOW, testing): added a Linux `st_birthtime`-absent test and the hyphenated-date no-raise
  guard.
- N-5 (LOW, anti-regression/usability): pinned that `--all` widens which top-level areas are
  SEARCHED for lifecycle dirs, and still only REPORTS files under lifecycle dirs - it never lists or
  targets the framework `.agents/workflows/**` tree, so `--all` output stays usable.

No scope or approach changed; the review made the time-sourcing, parsing, and scan-scope precise
enough to build without a data-moving bug. Reviewing is not executing.

## Approval and execution gate

Proposal only; not auto-executed. On approval: implement changes 1-8, run the full suite green, do
the manual validation, then move this IPD to `.agents/plans/executed/` with an execution-record
summary.
