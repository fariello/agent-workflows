# IPD: Plan/walkthrough timestamp convention - reverse UTC to LOCAL time

- Date: 2026-07-11
- Concern: developer UX / convention correctness. The plan filename convention
  (`YYYYMMDD-HHMM-NN-<slug>.md`) was defined in D48/D50 to use UTC date+time. For a solo/small-team
  tool where a human constantly reads these filenames, UTC is confusing: a file created at 8:27pm
  local (EDT) is named `20260712-0027-...`, off by a day and four hours from the wall clock. UTC's
  justification (a monotonic global order for cross-timezone teams) does not fit this use; filenames
  are for humans first. Reverse the UTC directive to LOCAL time (the creating machine's local tz),
  keeping the same `YYYYMMDD-HHMM` shape (no offset suffix in the name).
- Scope: the timestamp SEMANTICS only. Reverses the "UTC" portion of D48/D50; the shape
  (`YYYYMMDD-HHMM-NN-<slug>`), the `NN` per-minute sequence, the `00`-orchestrator rule, and the
  creation-time = earliest-evidence semantics are UNCHANGED - only the timezone flips UTC -> local.
  Touches: `normalize_plan_names.py` date-derivation, and ~12 authored docs that state "UTC".
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-11 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised in an interactive session - the
  maintainer noted UTC is horrible UX and was never chosen this session (it came from D48/D50 in a
  prior session). Decision: reverse to local time, no offset in the name, update everywhere, add a
  DECISIONS entry reversing the UTC part of D48/D50; leave historical UTC-named files as-is (P4).
  Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- Decision origin: D48 (DECISIONS.md:1448 "UTC date + 24h time") set UTC; D50 (:1516) reaffirmed
  "min({git-first-commit, st_birthtime, st_mtime}) in UTC". This IPD reverses ONLY the timezone.
- Normalizer code (`.agents/workflows/setup-repo/tools/normalize_plan_names.py`):
  - `_utc_env()` (:166) forces `TZ=UTC`; `git_first_commit_stamp` (:172) passes it to a
    `git log --date=format-local:%Y%m%d %H%M` call - `format-local` honors `TZ`, so forcing UTC
    yields UTC. Dropping the forced `TZ` makes `format-local` use the machine's LOCAL tz.
  - `fs_stamp()` (:211) uses `datetime.datetime.fromtimestamp(min(epochs), datetime.timezone.utc)` -
    switching to `datetime.datetime.fromtimestamp(min(epochs))` (naive) yields LOCAL time.
  - Docstrings/comments at :14, :15, :20, :23, :26, :173, :212 say "UTC" and must become "local".
- Authored docs stating "UTC" (to update): `AGENTS.md`, `.agents/workflows/assess/templates/ipd.md`,
  `.agents/workflows/assess/assess.md`, `.agents/workflows/setup-repo/setup-repo.md`,
  `.agents/plans/README.md`, `.agents/workflows/templates/plans-README.md`,
  `.agents/workflows/verify/verify.md`, `.agents/workflows/benchmark/benchmark.md`,
  `.agents/workflows/advise/advise.md`, `.agents/workflows/assess/lenses/logging-audit.md`,
  `prompts/final-release-validation-executable.md`, and DECISIONS.md (the new reversal entry).
  (`logging-audit.md` may reference UTC for LOG timestamps, which is legitimate and separate - verify
  before editing; do NOT change guidance about log/telemetry timestamps, only the plan-filename
  convention.)
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Normalizer -> local time.** Remove the forced `TZ=UTC` (drop `_utc_env()` or make it a no-op
   passing the ambient environment) so `git log --date=format-local` uses the machine's local tz; and
   change `fs_stamp` to `datetime.datetime.fromtimestamp(min(epochs))` (naive local). Update the
   module docstring + inline comments UTC -> local. Keep everything else (earliest-of semantics,
   `--follow`, `NN`) identical.
2. **Docs reconciliation.** In each authored doc, change the plan-filename timestamp description from
   "UTC date and time" to "the creating machine's LOCAL date and time" (same `YYYYMMDD-HHMM` shape).
   Leave any non-plan UTC guidance (e.g. log timestamps in `logging-audit.md`) untouched - verify each
   hit is about the plan-filename convention before editing.
3. **DECISIONS reversal entry (Dnn).** Add an entry that EXPLICITLY reverses the UTC portion of
   D48/D50 with the UX rationale (human-readable filenames; solo/small-team; wall-clock match), states
   the new rule (local tz, no offset in the name), notes the mixed-timezone caveat (names reflect the
   creating machine's tz; acceptable for this use), and that historical UTC-named files are NOT
   renamed (P4). D48/D50 remain as the historical record; this entry supersedes their tz clause.
4. **Tests.** Update/extend the normalizer tests: `fs_stamp` returns local-time components for a known
   epoch (compute the expected local `YYYYMMDD/HHMM` from the same epoch, tz-agnostic assertion); no
   test asserts UTC. Add a guard that the module no longer forces `TZ=UTC`. Full suite green.

## Deferred / out of scope

- Offset-suffixed names (`-0400`) and a configurable tz knob - rejected in favor of plain local
  (simplest, best UX); can be revisited if a mixed-tz team ever needs it.
- Renaming historical UTC-named plan files - NOT done (P4; they stay as the record).
- Changing the filename SHAPE, `NN` rules, or creation-time semantics - unchanged.

## Open questions (v1 leans for review)

1. Mixed-timezone contributors produce names in their own local tz, so global ordering across
   machines is approximate. Accept for this use? (Lean: yes - single/small-team; ordering within one
   machine is correct and that is what matters here.)
2. `logging-audit.md` UTC mention: confirm it is about LOG timestamps (leave it) vs the plan
   convention (change it). (Lean: leave log guidance; UTC for logs is a real best practice.)
3. Should the normalizer's `--format json` output or any stamp be tz-annotated? (Lean: no; keep names
   plain local, matching the human-facing goal.)

## Approval and execution gate

`to-review`. Next: `/plan-review` (two-commit per D52), resolve OQs, human approve, execute changes
1-4, validate (suite green), commit (never push), `git mv` to executed/. Not auto-executed.
