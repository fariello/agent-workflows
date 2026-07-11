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
- Status: DONE (executed 2026-07-11; see DECISIONS D50). Normalizer rewritten with earliest-evidence
  creation time, plans+prompts scan + `--area`/`--all`, exclusions, and opt-in `--rename-non-numeric`;
  suite 153 -> 169 green. Follow-on to D48.
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

## What the filename timestamp represents (SETTLED 2026-07-11)

**CREATION / authoring time, stable for the plan's whole life.** The date is set once when the plan
is authored and NEVER changes as it moves `pending -> executed -> superseded -> ...`. A plan's name
(hence its identity/reference) is permanent; `NN` groups an orchestrator with its child plans by
their shared CREATION moment. We deliberately do NOT use "execution" time (not reliably knowable)
nor "last-modified/completion" time (would rename a plan through its lifecycle and scatter `NN`
groups). This matches the D48 convention already shipped to 27+ repos. This semantic is the reason
for the time-source rule below - do not reintroduce a completion/last-touched interpretation.

## Decisions taken (maintainer, 2026-07-11)

1. **Time source = EARLIEST EVIDENCE of the file's existence (REVISED 2026-07-11):** because the
   goal is CREATION time (above), and no single signal is reliably "real" across all workflows
   (git-first-commit is WRONG for imported/copied files - it records when the file entered THIS
   repo, e.g. a June-authored file committed here in July; fs times can be reset by a checkout or
   copy), the automatic date is the **minimum (earliest)** of the signals that exist:
   `min(st_birthtime, st_mtime, git-first-commit-time)`, in UTC. Rationale: creation is the earliest
   moment for which we have any evidence.
   - This is robust in BOTH edge cases: an IMPORT (git-commit late -> mtime/birthtime wins) and a
     BORN-HERE-THEN-EDITED file (mtime late from edits -> git-first-commit wins). ("Most recent"
     would pick the wrong signal in both.)
   - A **filename-embedded date ALWAYS wins** over all signals (the human already stated it).
   - **Disagreement warning:** when the chosen date and the git-first-commit date differ by more
     than ~1 day (the tell-tale of an import or a reset clock), `--check` surfaces it
     (`chosen=20260601 (mtime); git=20260711 - imported?`) and treats the file as NEEDS-DECISION,
     not a silent rename, unless the operator passes `--assume-dates`. So the clean
     case (all signals agree within a day) stays quiet; only the ambiguous case is loud.
   - If truly nothing is available (no git, no readable stat), fall back to `0000` on whatever date
     exists (name date, else the run date) - effectively unreachable since `stat` succeeds for an
     existing file.
   All times formatted UTC `YYYYMMDD-HHMM`; date and time are taken from the SAME chosen source
   (never a name-date mixed with a fallback-time), carried as a structured `(date, time)` pair.
2. **Scan scope (default narrow, opt-in broadening) - REVISED 2026-07-11:** default run scans ONLY
   `.agents/plans/` + `.agents/prompts/` (the two areas the framework blesses for the lifecycle).
   Broadening is opt-in: `--area <name>` (repeatable) - when given, it REPLACES the default set with
   exactly the named areas (e.g. `--area plans` = only plans; `--area designs --area rfcs` = those
   two); `--all` = every top-level area under `.agents/`. There are NO `--plans`/`--prompts`
   convenience flags (use `--area plans` / `--area prompts`); one uniform mechanism. This reverses
   the earlier "recurse everything by default" idea: defaulting to plans+prompts avoids reaching
   into areas the framework does not own, while `--area`/`--all` let a user who keeps other
   lifecycle-bearing areas opt in.
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

### 1. Creation-time resolution = earliest evidence (decision 1)
Each candidate signal is a UTC `(date, time)` PAIR (never a hyphen-joined string - N-1):
- `git_first_commit_stamp(path)` - from `git log --follow --diff-filter=A` (oldest; already exists).
- `fs_stamp(path)` - `os.stat()`: `st_birthtime` if present (`getattr(st, "st_birthtime", None)`;
  absent on Linux ext4), and `st_mtime`. (We do NOT use `st_ctime` for the value - on Linux it is
  inode-change time, which a `chmod`/rename bumps and which is rarely creation; keep it only as a
  last-ditch tiebreak if neither birthtime nor mtime is readable.)
- `name_date` - a date parsed from the filename, if any.

Rewrite `_time_and_date_for(path, parsed) -> (date, time)`:
1. If the filename has an embedded date (`parsed`/name), USE IT for the date; take the time from the
   earliest-evidence computation below (or `0000` if none). Name date always wins (decision 1).
2. Else compute `chosen = min(...)` over ONLY the EVIDENCE signals that exist among
   {git-first-commit, st_birthtime, st_mtime} (compare on the full `(YYYYMMDD, HHMM)`); this is the
   earliest evidence of the file's existence = its creation proxy. (The name-date from rule 1 is a
   short-circuit, NOT a `min` participant - so a day-only name-date at `0000` never falsely wins the
   min by looking like midnight; R-1.)
3. Else `("<run-or-only-known-date>", "0000")` (effectively unreachable: `stat` succeeds for an
   existing file).
Return the chosen `(date, time)` PAIR directly; the caller uses it as-is (no `split("-")`, N-1;
never mix a name-date with a different source's time except per rule 1 which is intentional and
same-file, N-2).

**Disagreement flag (decision 1):** compute `git_first_commit_stamp` even when it is not chosen; if
it EXISTS and `abs(chosen_date - git_date) > 1 day`, mark the file `imported?` and treat it as
NEEDS-DECISION (not auto-renamed) unless the operator passes `--assume-dates`. This surfaces the
import / reset-clock case (the whole reason git-first was wrong) without nagging on clean files.
- **Limitation (R-2):** for an UNTRACKED file there is no git time to disagree with, so the flag
  cannot fire; the file just uses its earliest fs evidence. This is acceptable (we cannot compare to
  a signal that does not exist); it is stated so it is not mistaken for a bug. Such files are still
  subject to the normal preview before `--apply`.
- **Flag semantics (R-3):** `--assume-dates` specifically means "accept the chosen dates for files
  flagged `imported?` and rename them anyway." It is distinct from the wizard's general
  ask-before-change; a bare `--apply` still HOLDS `imported?` files (reports them, does not rename)
  so the human sees them. (There is no separate `--yes` on this tool; the LLM `/setup-repo` layer
  handles the interactive yes/no and would pass `--assume-dates` only after showing the preview.)

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

### 3. Scan scope: default plans+prompts, `--area`/`--all` to broaden (decisions 2, 3)
Rework `scan` to take a set of AREAS (top-level names under `.agents/`). Default = {`plans`,
`prompts`}. `--area <name>` (repeatable) REPLACES the default with exactly the named areas; `--all`
= every top-level dir under `.agents/`. Within each scanned area, recurse and recognize the
lifecycle subdir set (`pending/executed/superseded/not-executed/reusable/done`). Rename-eligible =
`*.md` whose IMMEDIATE parent is a lifecycle dir within a scanned area; deeper files are reported
(as `nested`, not renamed) unless `--include-nested`. Report every file with a status: conformant /
to-rename / excluded / nested / non-numeric / conflict.

Scope guardrails (N-5): only files under a recognized lifecycle dir are REPORTED and eligible; even
with `--all`, non-lifecycle `*.md` (including the whole framework tree `.agents/workflows/**`) are
NOT listed or targeted. `.agents/workflows/` is never a rename target regardless of flags. So `--all`
widens WHICH top-level areas are searched for lifecycle dirs, not "print/rename every markdown file
under .agents/". This keeps output usable and the blast radius bounded.

### 4. Exclusions (decision 4)
Add `--exclude PATTERN` (repeatable) and a MINIMAL built-in default exclude set of `README.md` ONLY
(RESOLVED 2026-07-11: do NOT hardcode personal-layout patterns like `*/sources/*` or
`*/MASTER-CONTEXT-*` - those are one user's idiom and would surprise downstream repos, violating
P7; the framework only owns the lifecycle dirs and the READMEs it generates. Reference-input folders
are protected structurally by the nested-file rule, not by a baked-in glob). Exclusions are fnmatch
globs on the repo-relative POSIX path. An excluded file is reported `excluded`, never renamed. A
`--no-default-excludes` escape hatch lets a user opt out of the built-ins.

### 5. Non-numeric renaming (decision 5)
Add `--rename-non-numeric`. Off by default: a non-numeric, non-excluded, lifecycle-parent file is
reported `non-numeric (needs --rename-non-numeric)`. On: rename it to canonical. DATE (OQ2 resolved):
if the name contains a parseable `YYYYMMDD` anywhere, use it for the date and take only HHMM from the
git/fs fallback; otherwise take BOTH date and time from the git/fs fallback (change #1). SLUG: derived
from the old stem, lowercased-kebab, with the consumed date removed
(`MASTER-CONTEXT-a-private-repo-20260711` -> `master-context-a-private-repo`; empty -> `untitled`). Never
touch excluded or nested files even with this flag (nesting needs `--include-nested` too).

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
- earliest-evidence date: an untracked file with a known `st_mtime` normalizes to that UTC date+time
  (not `0000`). IMPORT case: a file whose `st_mtime` is OLDER than its git-first-commit time (the
  June-authored / July-committed scenario) resolves to the MTIME date (earliest), and is flagged
  `imported?` (needs `--assume-dates` to auto-rename). BORN-HERE-EDITED case: a file whose mtime is
  NEWER than its git-first-commit resolves to the GIT date (earliest). Exercise the
  `st_birthtime`-absent path (Linux) so the helper degrades to mtime/git without error (N-4).
- name-date wins: a filename with an embedded/leading date keeps that date regardless of fs/git.
- new legacy shapes: `YYYYMMDD-NN-`, `YYYYMMDD-HHMM-`, `YYYY-MM-DD-` (and `YYYY-MM-DD-NN-`) all
  normalize correctly, preserving present time/NN; explicitly assert the hyphenated-date case does
  NOT raise (N-1 regression guard) and yields a compact `YYYYMMDD` date; assert the NN-vs-HHMM
  disambiguation (`...-01-` -> NN, `...-1044-` -> time).
- scope: a file under `prompts/pending/` is found by default; `--area plans` excludes it (only plans
  scanned); `--all` still lists only lifecycle-dir files, never `.agents/workflows/**` (N-5).
- recursion: a `.../<suite>/sources/foo.md` is reported `nested` and NOT renamed without
  `--include-nested` (structural protection, no glob needed).
- exclusions: `README.md` is skipped by default; a `--exclude` pattern protects a named file;
  `--no-default-excludes` drops the README.md default.
- non-numeric: off by default -> reported, not renamed; `--rename-non-numeric` renames a top-level
  `foo-bar.md` to a canonical name with a `foo-bar` slug and a fs/`0000` time; still skips excluded.
- idempotency + no-clobber + staged-git-mv still hold; repo drift-guard still green.

## Directory / eligibility spec (authoritative)

- **Scanned areas:** default {`plans`, `prompts`}; `--area <name>` (repeatable) replaces the set
  with exactly those; `--all` = every top-level dir under `.agents/`. No `--plans`/`--prompts` flags.
- **Lifecycle dirs:** `pending`, `executed`, `superseded`, `not-executed`, `reusable`, `done`.
- **Rename-eligible:** `*.md` whose immediate parent is a lifecycle dir within a scanned area, not
  excluded. (`--include-nested` also makes deeper files eligible.)
- **Time:** CREATION proxy = filename-embedded date if present, else the EARLIEST of
  {git-first-commit, `st_birthtime`, `st_mtime`} in UTC (min = earliest evidence of existence), else
  `0000`. Date+time taken from the same chosen source (structured pair; see change #1). A
  chosen-vs-git disagreement > ~1 day flags the file `imported?` (needs `--assume-dates`).
- **Excluded (default): `README.md` ONLY** (the sole framework-owned file that must never be
  renamed). NO hardcoded personal-layout patterns like `*/sources/*` (that would impose one user's
  idiom on all downstream repos - P7); reference-input folders are protected STRUCTURALLY by the
  nested-file rule instead. Users add their own via repeatable `--exclude PATTERN`;
  `--no-default-excludes` drops even the README.md default.

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

## Open questions (RESOLVED with the maintainer 2026-07-11)

1. Built-in default exclude set: **RESOLVED - `README.md` ONLY.** No hardcoded personal-layout
   globs (`*/sources/*`, `*/MASTER-CONTEXT-*`): those are one user's idiom and would surprise
   downstream repos (P7). The framework only owns the lifecycle dirs + the READMEs it generates;
   reference-input folders are protected structurally by the nested-file rule, and users add
   `--exclude` for their own layouts. (See change #4 and the eligibility spec.)
2. Embedded date in a non-leading position: **RESOLVED - YES, use it.** When `--rename-non-numeric`
   handles a name that contains a parseable `YYYYMMDD` anywhere (e.g.
   `MASTER-CONTEXT-...-20260711.md`), use that date for the file's DATE, take HHMM from the git/fs
   fallback, and drop the consumed date from the derived slug (-> `master-context-...`). If the name
   has no parseable date, both date and time come from the git/fs fallback (change #1).

Related scoping note (raised during this pass): whether to CODIFY a blessed directory for plan
input/reference artifacts (the `sources/` need) is deliberately NOT decided here - it is a
separate lifecycle/structure concern for its own future IPD, not this normalizer change. The
nested-file rule already protects such folders from renaming today.

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

### Post-review semantics revision (2026-07-11, maintainer)

A real case (importing June-authored, untracked files on another machine, then committing them here
in July) exposed that the reviewed decision-1 ordering (git-first-commit -> fs) was WRONG for
imports: git-commit time records when a file entered THIS repo, not when it was created, so those
files would be stamped July 11 and their true June date hidden - the exact "stale value masquerading
as authoritative" failure D48 exists to prevent. Two things were then settled and folded in above
(this is a material change to decision-1, hence a re-review of the changed sections):

- **Semantics pinned:** the filename timestamp is CREATION/authoring time, stable for the plan's
  whole life (new "What the filename timestamp represents" section). NOT execution time (not
  knowable) and NOT last-modified/completion (would rename a plan through its lifecycle). This
  matches D48 as shipped.
- **Time source reversed to EARLIEST EVIDENCE:** `min(git-first-commit, st_birthtime, st_mtime)`,
  with a filename-embedded date always winning, plus a >1-day chosen-vs-git disagreement flag
  (`imported?`, needs `--assume-dates`). Reasoning worked through with the maintainer: creation is
  the earliest evidence of existence, and `min` is correct in BOTH the import case (git late) and
  the born-here-then-edited case (mtime late), whereas both "git-first" and "most recent" are wrong
  in one of those. `st_ctime` dropped as a value source (Linux inode-change time, not creation).

Re-review of the changed sections (2026-07-11) found and fixed three follow-on points, all Low RR:
R-1 - only the evidence signals enter the `min`; a day-only name-date is a short-circuit, not a
`min` participant (else its `0000` time could falsely win as "earliest"). R-2 - stated the
limitation that the `imported?` disagreement flag cannot fire for an UNTRACKED file (no git time to
compare), which is acceptable, not a bug. R-3 - clarified `--assume-dates` is the single flag that
accepts `imported?`-flagged dates; there is no `--yes` on this standalone tool (the `/setup-repo`
layer handles interactive confirmation and passes `--assume-dates` after previewing).

No scope or approach changed; the review made the time-sourcing, parsing, and scan-scope precise
enough to build without a data-moving bug. Reviewing is not executing.

## Approval and execution gate

Proposal only; not auto-executed. On approval: implement changes 1-8, run the full suite green, do
the manual validation, then move this IPD to `.agents/plans/executed/` with an execution-record
summary.
