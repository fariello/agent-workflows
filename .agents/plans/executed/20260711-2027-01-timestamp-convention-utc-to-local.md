# IPD: Human-facing timestamp convention - reverse UTC to LOCAL time (plan filenames AND run-ids)

- Date: 2026-07-11
- Concern: developer UX / convention correctness. The plan filename convention
  (`YYYYMMDD-HHMM-NN-<slug>.md`) was defined in D48/D50 to use UTC date+time. For a solo/small-team
  tool where a human constantly reads these filenames, UTC is confusing: a file created at 8:27pm
  local (EDT) is named `20260712-0027-...`, off by a day and four hours from the wall clock. UTC's
  justification (a monotonic global order for cross-timezone teams) does not fit this use; filenames
  are for humans first. Reverse the UTC directive to LOCAL time (the creating machine's local tz),
  keeping the same `YYYYMMDD-HHMM` shape (no offset suffix in the name).
- Scope (BROADENED by plan-review): ALL human-facing timestamp NAMES flip UTC -> local - both plan
  filenames (`YYYYMMDD-HHMM-NN-<slug>`) AND `workflow-artifacts/` RUN_IDs (`YYYYMMDD-HHMMSS`). Only
  the timezone changes; shapes, `NN` sequence, `00`-orchestrator, and earliest-evidence creation
  semantics are UNCHANGED. EXCLUDED (not filenames): log/telemetry timestamps (`logging-audit.md`
  "prefer UTC" for logs; `bench_env.py` `captured_at_utc` ISO-8601 field) and the dev-version-string
  date segment (`versioning.py:52`). Touches: `normalize_plan_names.py` date-derivation (real UTC
  code) + ~24 authored docs stating "UTC" for plan/RUN_ID names.
- Status: executed
- Approval: approved by maintainer 2026-07-11 (reviewed; OQ3 resolved - `versioning.py:52` version
  date stays UTC, excluded). Executed 2026-07-11 (changes 1-5); full suite green (178 tests).
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-11 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised in an interactive session - the
  maintainer noted UTC is horrible UX and was never chosen this session (it came from D48/D50 in a
  prior session). Decision: reverse to local time, no offset in the name, update everywhere, add a
  DECISIONS entry reversing the UTC part of D48/D50; leave historical UTC-named files as-is (P4).
  Complete proposal; born to-review.
- 2026-07-11 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  Re-opened the evidence and found: (TL-1) RUN_ID timestamps (verify/benchmark/advise/release-review
  `YYYYMMDD-HHMMSS`) are also UTC in PROSE - maintainer broadened scope to ALL human-facing timestamp
  names; (TL-2) the run-id-generating CODE (`engine.py` x5) already uses `datetime.now()` = LOCAL, so
  those docs are simply WRONG today and flipping the prose to "local" makes docs match code (no code
  change there); (TL-3) `bench_env.py:625 captured_at_utc` and `logging-audit.md:32` are
  telemetry/log timestamps, NOT filenames - EXCLUDED; (TL-4) `versioning.py:52 _utc_date()` is a
   dev-VERSION-string segment, a distinct concern - EXCLUDED pending maintainer confirm. Status ->
   reviewed.
- 2026-07-11 approved (maintainer): OQ3 resolved (versioning.py stays UTC, excluded). Status ->
  approved.
- 2026-07-11 executed (its_direct/pt3-claude-opus-4.8-1m-us): normalizer local-time code + ~12 doc
  reconciliations + DECISIONS D55 + local-time guard tests, committed 5828f04. Full suite green (178).
  Status -> executed; git mv to executed/.


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

1. **Normalizer -> local time (the only real UTC-forcing code).** Remove the forced `TZ=UTC` (drop
   `_utc_env()` or make it a no-op passing the ambient environment) so `git log --date=format-local`
   uses the machine's local tz; change `fs_stamp` to `datetime.datetime.fromtimestamp(min(epochs))`
   (naive local). Update the module docstring + inline comments UTC -> local. Everything else
   (earliest-of semantics, `--follow`, `NN`) identical.
2. **RUN_ID generation - no code change needed (confirm).** VERIFIED the run-id-producing code
   (`engine.py` x5) already uses `datetime.now()` = LOCAL; so RUN_IDs are ALREADY local. This change
   is a DOC correction: the prose that says RUN_ID is "UTC" is wrong today. (If any new run-id helper
   is added later it must use local too.)
3. **Docs reconciliation (plans + RUN_IDs).** In each authored doc, change the timestamp description
   from "UTC" to "the creating machine's LOCAL time" for BOTH the plan-filename convention and the
   `workflow-artifacts/` RUN_ID (`YYYYMMDD-HHMMSS`). Docs to update include AGENTS.md, the IPD
   template, assess/assess-all/setup-repo/verify/benchmark/advise/getting-started, the plans READMEs,
   all release-review section files + templates/README/reference/MANIFEST, ARCHITECTURE.md, and the
   prompts that mention RUN_ID. EXCLUDE and DO NOT edit: `logging-audit.md:32` (log timestamps -
   "prefer UTC" is correct for telemetry) and any ISO-8601 `captured_at_utc`-style data fields.
   Verify each hit is a NAME convention before editing.
4. **DECISIONS reversal entry (Dnn).** Explicitly reverse the UTC portion of D48/D50 with the UX
   rationale (human-readable, wall-clock-matching names; solo/small-team), state the new rule (local
   tz, no offset in the name, for plan filenames AND RUN_IDs), note the mixed-tz caveat (names reflect
   the creating machine's tz; acceptable here), the EXCLUSIONS (log/telemetry + version-string dates
   stay UTC), and that historical UTC-named files are NOT renamed (P4). D48/D50 remain the historical
   record; this supersedes their tz clause.
5. **Tests.** Update/extend the normalizer tests: `fs_stamp` returns LOCAL components for a known
   epoch (compute expected local `YYYYMMDD/HHMM` from the same epoch - tz-agnostic assertion); no test
   asserts UTC; guard that the module no longer forces `TZ=UTC`. Full suite green.

## Deferred / out of scope

- Offset-suffixed names (`-0400`) and a configurable tz knob - rejected in favor of plain local
  (simplest, best UX); can be revisited if a mixed-tz team ever needs it.
- Renaming historical UTC-named plan files - NOT done (P4; they stay as the record).
- Changing the filename SHAPE, `NN` rules, or creation-time semantics - unchanged.

## Open questions

1. **Mixed-tz ordering: RESOLVED lean - accept.** Names reflect the creating machine's local tz;
   ordering within one machine is correct, which is what matters for solo/small-team use.
2. **`logging-audit.md` / telemetry UTC: RESOLVED - leave untouched.** Confirmed it is LOG/telemetry
   time guidance ("prefer UTC"), not a filename; `bench_env.py captured_at_utc` likewise. Excluded.
3. **`versioning.py:52 _utc_date()` (dev-version-string date): OPEN for maintainer.** This is a
   PEP 440 dev-version segment, not a filename. Lean: EXCLUDE (version strings are a distinct,
   ordering-sensitive concern; leave UTC). Confirm, or include it if you want total local consistency.
4. tz annotation in names/JSON: RESOLVED - no; keep names plain local (the human-facing goal).

## Plan-review record (2026-07-11)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off). Findings, evidence re-opened against source:
- TL-1 (scope gap): RUN_IDs are also UTC in prose -> maintainer broadened scope to all human-facing
  timestamp names (plans + RUN_IDs).
- TL-2 (accuracy): run-id CODE (`engine.py` x5 `datetime.now()`) is ALREADY local; the change there
  is doc-only (the prose was wrong). Prevents a needless/incorrect "make code UTC->local" edit.
- TL-3 (exclusion): `logging-audit.md:32` + `bench_env.py:625` are telemetry, not filenames -
  excluded.
- TL-4 (exclusion, needs confirm): `versioning.py:52` is a version-string date, not a filename -
  excluded pending OQ3.
No blocking findings; this IPD does not self-approve.

## Approval and execution gate

`reviewed`. Next: human approve (confirm OQ3), execute changes 1-5, validate (suite green), commit
(never push), `git mv` to executed/. Not auto-executed.
