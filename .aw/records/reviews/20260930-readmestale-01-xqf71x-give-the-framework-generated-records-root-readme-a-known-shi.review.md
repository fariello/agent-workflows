# Review findings: plan xqf71x

- Subject-Id: xqf71x
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0) BEFORE semantic review, with one
info-severity `IPD-Z602` density advisory on E-02 that I judged a FALSE POSITIVE and did not treat as a
split signal: E-02 is one wiring change in one function with five constraints ON that change, not five
deliverables, and it needs exactly one `V-*`. Both `--phase author` and `--phase review-finalize` now
report `clean` with zero findings. The plan is `- Kind: child`, so `IPD-S407` does not apply.

THE CENTRAL EVIDENCE OF THIS PLAN IS EXCEPTIONALLY GOOD AND IT ALL REPRODUCES. The hash census is the
load-bearing claim (it is what converts the backlog item's open policy question into a decidable lookup),
so I re-derived it independently rather than reading it:

- F-02 reproduces EXACTLY. Walking all five commits that ever touched the template under both historical
  paths yields exactly 3 distinct `manifest.hash_content` values, and BOTH pinned literals are correct to
  all 64 hex characters: `7bc1cdde5ef768f1d05ca8979db8cca78c42cff25815537521b08cce8a41ab7f` (heading
  `# .agents/`, reached by `0b4c4e5d`, `f296f6f4`, `1ae9d7f6`) and
  `d31ab028bcc84f3172a3db9dfd04fd8e3dbb1148765c817d9072cf2ec3d350e5` (`e2a362bf`, heading `# .aw/records/`).
  The current template at HEAD hashes `604b435e...` as claimed. The "differ ONLY in the heading line"
  claim also reproduces: a `difflib` unified diff of the two retired normalized texts shows one changed
  line, `-# .agents/` / `+# .aw/records/`.
- F-01 reproduces end to end through a real install. A scratch install writes `604b435e`; planting the
  `e2a362bf` text and re-running the installer prints the literal line `[no change] .aw/records/README.md`
  and leaves the file byte-identical. The dead pointer is real too: `<repo>/.aw/records/workflows/index.md`
  does not exist (the only `index.md` is at `.aw/system/workflows/index.md`).
- F-06 reproduces to the number: 310 files recorded, `.aw/records/README.md` absent, and zero of the
  eighteen scaffolded record READMEs present in the manifest. `plan_uninstall`'s `if entry.kind not in
  ("file", "shim")` filter is exactly as described, so the fragile-coupling argument holds.
- F-07 reproduces exactly: 18 READMEs under `.aw/records/` after a fresh install.
- F-14 reproduces to the hash prefix: this checkout's own records-root README hashes `8dab3e0a`, matching
  none of the three shipped values, so it classifies `user-owned` and is correctly untouchable.
- F-04, F-05, F-12, F-13 all reproduce. `is_shim_customized_vs_expected` is the three-line bool the plan
  describes; it has ZERO production callers (only a comment and two test call sites); `create_backup_path`
  and `write_file`'s three-line backup block are verbatim as quoted; and the `[preserved]` comment is
  verbatim ("A deliberately-preserved customized file is NOT 'already current'").
- E-02(d)'s prompt argument verifies: `write_file`'s prompt is gated on `_shim_is_user_modified` AND on
  the path being a command shim, so a README repair genuinely sits outside the prompting path.
- Both open questions' resolutions verify against code: `write_file` writes under `if not content_current`
  INDEPENDENT of the backup block above it (OQ-01), and `manifest.py`'s docstring does declare itself
  "SELF-CONTAINED" and "PATH-PARAMETERIZED" while `engine.py` imports it as `manifest_mod` (OQ-02).

THE BLOCKER IS A TEST THIS PLAN BREAKS OUTSIDE ITS OWN FENCE. E-05 adds `"releases"` to the `.gitkeep`
scaffold key tuple and says of a count assertion "searched at authoring: no count assertion was found,
but the search was over `.gitkeep` string matches in `tests/`, so confirm rather than assume". I confirmed,
and one EXISTS: `tests/test_installer_scaffold_preview_parity.py` asserts `len(apply_gitkeeps) == 22`.
Measured: a fresh `engine.install_into_repo` produces exactly 22 `.gitkeep` files today, so E-05 makes it
23 and that assertion fails. The plan's own instruction to confirm is what saved it from being a silent
defect, and it deserves credit for that; but the confirmation had to happen, and the file was also absent
from `- Scope-Paths:`. Fixed by naming the assertion and its new value, and by DECLARING the third path
rather than leaving the executor to justify a surprise edit afterwards (a fence should declare what is
known to need editing).

TWO HIGH FINDINGS ARE BOTH WRONG EDIT SITES, and each would have cost an execution pass. E-02 says
`ensure_plans_readmes` short-circuits "before it has even read the template" and instructs "read the
template FIRST"; measured, the function opens with `targets = collect_scaffold_members(...)` and iterates
`for rel_path, content_bytes in targets.items()`, so the template is ALREADY in hand (959 bytes for the
records-root entry) and following the instruction adds a redundant read. E-05 says the `.gitkeep` key tuple
is "in `engine.create_setup_artifacts`"; measured, that function contains NO tuple and delegates via
`collect_scaffold_members(repo_root, category="setup")`, where the tuple actually lives. Both corrected in
place, with the substance of each item preserved because only the site was wrong.

THE THIRD HIGH IS AN UNRUN BASELINE CLAIM, which matters because V-05 was built on it. F-11 asserted "THE
BASELINE SUITE IS GREEN AT THIS HEAD" while its own Evidence column said "to be established by the
executor" - an assertion with no measurement behind it. I ran it: `python3 -m pytest` bare on a clean tree
reports `1 failed, 3498 passed, 2 skipped, 3 warnings in 79.36s`. The failure is
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, and it
is a UTC-versus-local DATE-BOUNDARY FLAKE unrelated to this plan: the assertion diff is
`- 2026-09-30 HIST_ACTOR` versus `+ 2026-10-01 HIST_ACTOR`, measured while the clock straddled local
midnight (`2026-09-30 23:59 EDT` / `2026-10-01 03:59 UTC`), and it touches `status_set`/backlog records
rather than anything this plan edits. Left unfixed, V-05's "zero failures is the bar" would have sent the
executor either hunting someone else's flake or excusing a real regression as "probably that one".

THE MOST SUBSTANTIVE JUDGEMENT CALL IS THAT THE SAFETY ARGUMENT IS OVERSTATED, AND IT IS FIXABLE BY SAYING
SO RATHER THAN BY CHANGING THE DESIGN. The Concern claims a hash match proves the file "cannot be a user's
own work". But `manifest.normalize_for_hash` drops blank lines, per-line whitespace, AND any line whose
stripped form begins `description:`. Measured against the `e2a362bf` text, FIVE classes of real user edit
still hash equal and would therefore be repaired: adding a `description:` line, reindenting every line,
converting to CRLF, appending blank lines, and adding trailing whitespace throughout. The plan's own case-5
check (append a substantive line) correctly does not match, so the gap is exactly these normalization-blind
edits. I did NOT treat this as a reason to reject the design: a byte-exact predicate would fail on every
CRLF checkout and make the repair useless, which is the worse trade, and E-02(a)'s backup makes every one
of those edits recoverable. So the fix is honesty plus coverage: the claim is now bounded ("the substantive
body is ours, modulo this normalization"), the predicate's docstring must say what it is blind to, E-04
gains two cases pinning that blindness as deliberate, and the backup is restated as load-bearing rather
than conventional.

WHAT I DELIBERATELY DID NOT FLAG. The `IPD-Z602` density advisory on E-02 (false positive, as above). The
plan's scope fence, which correctly says nothing about stopping over a scope question and so needs no
2026-09-01-ruling correction. The three `Carrier-Declined` rows, each of which records a measured
prohibition or a rejected alternative rather than deferred work, which is the correct disposition. And the
plan's decision to decline the `aw doctor` route: its reasoning (report-only would need the same predicate
and is additive, not alternative) is sound, and the `user-owned` fallback is the control that makes it safe.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | D (anti-regression) / G | `tests/test_installer_scaffold_preview_parity.py` `assert len(apply_gitkeeps) == 22` with message `f"Expected 22 .gitkeep files from apply, found {len(apply_gitkeeps)}"` | E-05 BREAKS A LIVE COUNT ASSERTION THAT THE AUTHORING SEARCH MISSED, IN A FILE OUTSIDE THE FENCE. E-05 adds `"releases"` to the `.gitkeep` key tuple and reports "no count assertion was found". Measured: a fresh `engine.install_into_repo` produces exactly 22 `.gitkeep` files, and that file asserts `== 22`, so E-05 makes it 23 and the suite goes red. The file was also absent from `- Scope-Paths:` (declared: `engine.py`, `tests/test_installer.py`), so the executor would have hit a failing test in an undeclared path. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names the assertion, its file, the measured 22, and the required update to `23` in the SAME change, and forbids deleting the assertion (it is a preview-versus-apply parity guard whose count must track reality). `tests/test_installer_scaffold_preview_parity.py` ADDED to `- Scope-Paths:` so the work is declared rather than justified after the fact; the Scope check and V-05 reconciled, and V-05 now requires the before/after count and the updating diff as evidence. |
| PR-002 | HIGH | IN-SCOPE | G (executability) | `engine.ensure_plans_readmes` opening `targets = collect_scaffold_members(plan.repo_root, plan.source_root, category="plans")` then `for rel_path, content_bytes in targets.items()` | E-02 DESCRIBES THE WRONG STATE AND INSTRUCTS REDUNDANT WORK. It says the function short-circuits "before it has even read the template" and directs the executor to "read the template FIRST". Measured: `collect_scaffold_members` has already read every template before the loop begins, so `content_bytes` holds the records-root template (959 bytes) on the first iteration. Following the instruction literally adds a second read of a file already in memory, and obscures that the only missing step is classification. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states that the template is already in hand, that the expected-text argument is `content_bytes.decode("utf-8")` with no I/O, and that CLASSIFICATION is the whole change. Added the layout caveat the corrected site exposes: the records-root entry is `.aw/records/README.md` under `aw` and `.agents/README.md` under `legacy`, so match on the layout-derived value or the predicate never fires on a legacy install. |
| PR-003 | HIGH | IN-SCOPE | A (correctness) / B (data integrity) | `manifest.normalize_for_hash`, whose loop does `if stripped.lower().startswith("description:"): continue` and `if not stripped: continue` after `line.strip()` | THE SAFETY CLAIM IS STRONGER THAN THE MECHANISM. The Concern says a hash match proves the file "cannot be a user's own work". Measured against the `e2a362bf` text, five classes of genuine user edit still hash EQUAL and would be classified `known-stale` and overwritten: adding a `description:` line, reindenting every line, converting to CRLF, appending blank lines, adding trailing whitespace throughout. A user's `description:` note is silently destroyed on the next install. The plan never considers this, and an unstated tolerance is one a later reader "fixes" in the wrong direction. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | The claim is BOUNDED rather than the design changed, because a byte-exact predicate would fail on every CRLF checkout and make the repair dead in practice. The Concern now says the substantive BODY is provably ours "modulo this normalization" and names the measured counterexamples; E-01 gains a note requiring the predicate's docstring to state what it is blind to and forbidding both an overstated docstring and a stricter comparison; and E-02(a)'s backup is restated as LOAD-BEARING (the recovery path for exactly these edits) rather than conventional. |
| PR-004 | HIGH | IN-SCOPE | E (testing) / G | `python3 -m pytest` bare on a clean tree; F-11 as authored | F-11 ASSERTED A GREEN BASELINE IT NEVER RAN, and its own Evidence column admits it ("to be established by the executor"). Measured: `1 failed, 3498 passed, 2 skipped` on a clean tree, the failure being `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a UTC-versus-local date-boundary flake (`2026-09-30` versus `2026-10-01` in one history line) wholly unrelated to this plan's files. V-05 then set "zero failures is the bar", which is unachievable and would have the executor either chasing someone else's flake or dismissing a genuine regression as that flake. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-11 rewritten to record the measured failure, its exact assertion diff, the midnight-straddle cause, and that it touches nothing this plan edits. V-05's bar is corrected from "zero failures" to the honest comparative one: no failure in the after-run that the lane-start run did not also show, passed count up by at least the new tests, the known flake identified by name if still present (or noted if it has stopped), and any OTHER failure proven pre-existing on a stashed tree. |
| PR-005 | MEDIUM | IN-SCOPE | G (citation integrity) | `grep` for `_format_install_item` across `agent_workflows/` and `tests/` returning nothing; `engine.format_output_item`'s action-to-tag if-chain | A CITED SYMBOL DOES NOT EXIST. F-13, the Step-0 citation list and E-02(c) all name `engine._format_install_item`, which has zero definition sites and zero references anywhere in the tree. The real renderer is `engine.format_output_item` (public, un-underscored), whose if-chain maps `install`/`overwrite`/`already current`/`preserved` to `[added    ]`/`[overwrite]`/`[no change]`/`[preserved]` exactly as F-13 describes. The plan's own Step-0 convention is to cite by symbol so a reader can find the code, which a symbol resolving to nothing defeats. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All five occurrences renamed to `engine.format_output_item`. F-13 records the correction explicitly (noting the SUBSTANCE held and only the name was wrong) and its Evidence column now cites the actual if-chain plus the negative `grep`, so the next reader can verify rather than re-discover. |
| PR-006 | MEDIUM | IN-SCOPE | A | Fresh install: 10 directories under `.aw/records/`, `releases` absent; the `.gitkeep` key tuple holding 7 keys; 7 of the 10 trees carrying a `.gitkeep` | TWO DIFFERENT COUNTS ARE CONFLATED AS "TEN". The Concern, E-05 and F-08 all say a fresh install "creates ten typed record trees" in the same breath as discussing the `.gitkeep` key tuple. Measured, those are different sets: 10 DIRECTORIES exist under `.aw/records/` (`releases` absent), the key tuple names SEVEN keys, and only 7 of the 10 trees get a `.gitkeep` from it (`comms`, `plans`, `prompts` do not). Since E-05 edits the tuple and V-05 counts directories, the imprecision lands exactly where the executor must be exact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 now names both counts separately, lists the ten directories explicitly, states that the tuple has seven keys and which three trees are not covered by it, and records that the asymmetry claim survives both corrections unchanged. |
| PR-007 | LOW | IN-SCOPE | G | `- Scope-Paths:`, the Scope `IN:` clause, the Step-0 citation list, and `## Proposed changes` item 5, all naming `engine.create_setup_artifacts` | THE WRONG EDIT SITE PROPAGATED TO FOUR MORE PLACES than E-05 itself, so fixing only the E-item would leave the plan internally inconsistent and a reader would not know which statement to trust. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four reconciled to `engine.collect_scaffold_members`' setup branch, and the Scope `IN:` clause and Proposed-changes item 5 now also name the count-assertion update E-05 owes. |
| PR-008 | LOW | IN-SCOPE | E | E-04 as authored | E-04's case list covers CRLF, trailing whitespace and inserted blank lines but NOT the two normalization-blind classes PR-003 measured (`description:` line, reindentation), so the predicate's real domain boundary would ship untested and the next reader would have no signal that it was considered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gains both cases, asserted as `known-stale` WITH a required comment stating the outcome is deliberate and that the backup is the recovery path, plus an explicit instruction not to respond by making the comparison stricter. Pinning the blindness is distinguished in the text from broadening `known-stale`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The normalization makes five classes of real user edit invisible, so a `known-stale` repair can destroy a user's `description:` line or reindentation. Reject the design, tighten the comparison, or bound the claim? | BOUND THE CLAIM and pin the blindness in tests; keep the shared normalization. | (a) Tighten to a byte-exact or whitespace-sensitive comparison: REJECTED, it fails on any CRLF checkout and on any editor that strips trailing space, which makes the repair dead in practice for the very existing installs this plan exists to reach, and it would fork the normalization the M13 invariant requires be shared. (b) Reject the design and keep no-clobber absolute: REJECTED, the measured defect is real and the backup makes every blind-spot edit recoverable, so the residual harm is a user retrieving one line from `.aw/backups/`, not losing it. (c) Add a secondary byte-level check only for `description:` lines: REJECTED as a special case that would still miss reindentation and CRLF, buying inconsistency rather than safety. | `manifest.normalize_for_hash` drops blank lines, per-line whitespace and `description:` lines (read, and measured over five edit classes against the `e2a362bf` text, all hash-equal); `manifest.py`'s M13 docstring requiring ONE shared normalization; `engine.write_file`'s backup block establishing the recovery path this relies on. | yes |
| D-2 | `tests/test_installer_scaffold_preview_parity.py` must change but was undeclared. Declare it in `- Scope-Paths:`, or have the executor justify it with `--scope-reason`? | DECLARE IT. | Leave it undeclared and require a `--scope-reason`: REJECTED. The scope fence is a DECLARATION so the runner can reconcile afterwards, and review has already PROVEN this file must change (measured 22 today, becoming 23), so leaving it out would manufacture a reconciliation exception for work that is known in advance. The `--scope-reason` escape exists for what an executor DISCOVERS, not for what the plan already knows. | The 2026-09-01 maintainer ruling on fences as declarations reconciled by `aw ipd finalize`; measured `len(apply_gitkeeps) == 22` today against the assertion's literal `22`. | yes |
| D-3 | `aw ipd lint` raised `IPD-Z602` (possible multi-concern) on E-02. Split it? | NO split. | Split E-02 into per-requirement items: REJECTED. E-02 is ONE change to ONE function (classify the records-root target and act), and its five lettered points are CONSTRAINTS on that change (back up, leave other targets alone, report distinctly, do not prompt, preserve dry-run), not independent deliverables. Splitting would produce items that cannot be executed or validated independently and would need an artificial `V-*` each, while the rule the workflow actually applies asks whether an item addresses one concern and is executable in one focused pass; this one is. | The advisory's own `severity: info`; `ensure_plans_readmes` read in full (a single loop whose records-root branch is the entire change surface); the workflow's right-sizing diagnostics (a) through (d), none of which this item trips. | yes |
| D-4 | Should review verify F-02's pinned hash literals, or accept them as authored? | VERIFY, character by character. | Accept them on the plan's say-so: REJECTED, these two 64-character literals ARE the mechanism: a single mistyped character silently disables the repair for one historical version, the suite would stay green, and the symptom (a repo that never gets repaired) is invisible. This is the highest-leverage unverifiable-by-inspection claim in the plan. | Independent census over all five commits touching both historical template paths, re-hashing each blob through `manifest.hash_content`: 3 distinct values, both pinned literals matching in full, plus the `604b435e` current value and the single-line `difflib` diff between the two retired texts. | yes |
| D-5 | The baseline suite has one failure. Is it this plan's concern, and what should the bar be? | NOT this plan's; set a COMPARATIVE bar rather than an absolute one. | (a) Keep "zero failures is the bar": REJECTED, it is unachievable today and would make the executor either hunt an unrelated flake or rationalize a real regression as that flake. (b) Fix the flake in this plan: REJECTED, it is outside `- Scope-Paths:`, unrelated to the concern, and bundling an unrelated test fix into a `followup` chore obscures both changes. (c) Ignore it silently: REJECTED, that is what F-11's unrun assertion already effectively did. | `python3 -m pytest` bare on a clean tree: `1 failed, 3498 passed, 2 skipped`; the narrowed run showing the `2026-09-30` versus `2026-10-01` history-line diff; `date -u`/`date` showing the midnight straddle; the test exercising `status_set` and backlog records, none of which this plan touches. | yes |
