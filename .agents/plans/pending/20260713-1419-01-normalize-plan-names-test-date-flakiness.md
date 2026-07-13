# IPD: Fix date-relative flakiness in test_normalize_plan_names (test-only; product unchanged)

- Date: 2026-07-13
- Concern: test correctness / CI reliability. 8 tests in `tests/test_normalize_plan_names.py` fail once
  the system clock advances more than a day past their hardcoded filename dates. They create a file
  named `20260711-...`, `git commit` it "now", and expect status `to-rename`. The normalizer CORRECTLY
  flags a file as `imported` when its filename date differs from its git-first-commit date by > 1 day
  (`normalize_plan_names.py:297`, a real import-detection rule). On 2026-07-11/12 the hardcoded date was
  within 1 day of "now" so the files were `to-rename`; from 2026-07-13 on they are 2+ days apart and
  correctly classified `imported`, so the tests fail. This is a TEST bug (wall-clock-proximity
  dependence), NOT a product bug: verified the product logic is intended and correct.
- Scope: `tests/test_normalize_plan_names.py` ONLY (make the affected tests date-relative/deterministic
  so the name-date agrees with the commit "now"). Product code (`normalize_plan_names.py`) is NOT
  changed. Docs/DECISIONS. Ship with 1.2.1 (or its own tiny patch) so the suite is fully green before
  the release.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-13 to-review (its_direct/pt3-claude-opus-4.8-1m-us): discovered during 2326-01 execution when
  the clock rolled past midnight; root-caused to date-relative test assumptions vs. the normalizer's
  git-vs-name-date import rule. Product confirmed correct. Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- The normalizer sets `imported` when `_days_apart(chosen_name_date, git_first_commit_date) > 1`
  (`normalize_plan_names.py:297`); git-first-commit date comes from the file's first commit time
  (`:231`). `imported` files are held from auto-rename (reported, not renamed) unless `--assume-dates`
  (`:409-410`, `:474`). This is intended (the tell-tale of a copied/imported file); NOT to be changed.
- The 8 failing tests all follow the pattern "create a file named `<hardcoded-recent-date>-...`, commit
  it now, expect `to-rename`". Their own comment admits the assumption: "committed today so the
  name-date agrees with git and none is flagged imported" (test file ~:81-82). That assumption rots.
- NOT all hardcoded `20260711` uses are broken: pure-parse assertions (`is_conformant`/`parse_name`,
  test lines ~24-36, ~106-109) do not touch git and are date-agnostic - leave them. And
  `test_name_date_wins_over_git_and_fs` (~:142-149) DELIBERATELY uses an OLD date `20260101` and expects
  the name-date kept; confirm whether it asserts `to-rename` (would also be affected) or only checks the
  resolved date (unaffected) and handle accordingly.
- Analogous precedent in the codebase: `versioning.parse_describe` accepts an injected `date=` for
  deterministic tests. Same idea applies here (inject/relativize "now") but the chosen fix is test-side
  only per this IPD's scope.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Make the affected tests use a RECENT date computed at runtime, not a hardcoded one.** Add a small
   test helper that yields "today" (and, where a legacy/hyphenated shape is needed, today formatted in
   that shape), so a file created + committed during the test has a name-date within 1 day of its
   git-first-commit and is therefore `to-rename`, deterministically, regardless of the calendar day the
   suite runs. Apply it to exactly the tests that create-commit-and-expect-`to-rename`
   (the 8 failing ones). Keep the tests asserting the SAME behavior (legacy shapes normalize, sequential
   NN, exclude patterns, apply/rename, no-clobber, nested-not-renamed) - only the date source changes.
2. **Leave date-agnostic and deliberately-old-date tests alone.** Do NOT touch the pure-parse
   assertions (`is_conformant`/`parse_name`) or `test_name_date_wins_over_git_and_fs` unless step 0's
   check shows the latter also asserts `to-rename` on an old committed-today date; if it does, give it a
   fixed EXPECTATION that matches the intended `imported`-vs-`to-rename` outcome for an old name-date
   committed today (i.e. assert `imported` when that is the correct product result), rather than forcing
   `to-rename`. Do not weaken a test into passing against wrong behavior.
3. **Docs + DECISIONS.** DECISIONS entry (next free number) recording: this was a test-only
   wall-clock-proximity flakiness, the product import-detection rule is correct and unchanged, and the
   fix relativizes the test dates. Note in CHANGELOG under 1.2.1 (test reliability) if it ships there.

## Deferred / out of scope

- Any change to `normalize_plan_names.py` product behavior (the `imported`/`>1 day` rule is correct).
- Adding an injectable reference-date SEAM to the product (a `date=`-style param) - a legitimate
  alternative for determinism, but it touches product code; this IPD is deliberately test-only. Capture
  as a possible follow-up if the test-only fix proves insufficient.

## Open questions (v1 leans for review)

1. `test_name_date_wins_over_git_and_fs` (old `20260101` committed today): does it assert `to-rename`
   (affected) or only the resolved date (unaffected)? Resolve by reading it at execution; fix the
   EXPECTATION to the correct product outcome, do not force a wrong pass. (Lean: it likely only checks
   the resolved date/prefix and is unaffected; confirm.)
2. Helper shape: a module-level `_recent_date()`/`_today()` returning `YYYYMMDD` (and variants for
   hyphenated/legacy shapes) vs. parameterizing each test. (Lean: one small helper returning today's
   compact date, plus a hyphenated variant where needed.)

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY `tests/test_normalize_plan_names.py`, `DECISIONS.md` (next free number), and
   `CHANGELOG.md` (if shipping in 1.2.1). Do NOT modify `normalize_plan_names.py` or any product code.
   If a change seems to need product edits, STOP and report (it would mean this is not test-only).
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. The previously-failing 8 tests
   must PASS, and the whole suite must be green (no other test regressed). Because the bug is
   date-relative, ALSO sanity-check the fix is not itself date-relative (the helper uses runtime
   "today", so it holds on any day). Confirm `aw plan-names` clean.
4. COMMIT only this IPD's touched files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.

HARD MUST: paste the real test output; product code untouched; do not force a test to pass against wrong
behavior; stay inside the scope fence; never push. Not auto-executed; requires human approval.
