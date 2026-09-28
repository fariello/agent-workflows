# Review findings: plan 8njbv5

- Subject-Id: 8njbv5
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `53799d62` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --json`
conforms after revision with zero diagnostics. No pre-review snapshot was owed: the plan was committed
and unmodified (`git status --short` showed no entry for it). `aw sanitize --agent` clean.

THIS IS AN UNUSUALLY WELL MEASURED PLAN AND ITS CENTRAL JUDGEMENT IS CORRECT. Its whole value is that
it REFUSES the mechanism its own backlog item proposed. The item says to scope the change to the `bits`
list, where the only signal in hand is `display is None`; the plan measured that omission has three
causes and that keying on the display would print "no worktree remains" for a tree that IS THERE, which
is the same class of false assertion `0ta5vg` E-05 was written to remove. That refusal is right, and the
plan carries the maintainer's own intent faithfully while correcting only the mechanism.

EVERY ONE OF ITS TWELVE FINDINGS REPRODUCED. F-03's six-case probe returned exactly the six values
quoted (`falsy`/absent-inside/outside-non-wt-parent/outside-absent -> None; inside-exists ->
`.aw/worktrees/live`; outside-exists-wt-parent -> `.aw/worktrees/abc123`). F-04's reclaimed fixture
yields one `STRANDED` record, `commits_ahead: 1`, `dirty: False`, worktree absent, display None. F-05's
`review_sweep_lane` fixture yields one `STRANDED` record with `worktree: None`. F-06's fixture pins
exactly 34 symbols with the six lane entries as listed, and `describe_lane` IS pinned while
`lane_worktree_display` and `stranded_lane_records` are NOT. F-07's simulation gives max 223 characters
against `MAX_DESCRIPTIVE_LEN` 300 (77 headroom), a 21-character segment cost, and one pre-existing
over-bound row at 414 that gains nothing. F-08 holds: `is_safe_descriptive` has no caller in
`attention.py`. F-09 holds and is the strongest argument for the spec amendment: F3a literally reads "A
WORKTREE THAT IS NOT ON DISK MUST NOT BE RENDERED", which a strict reader takes to forbid the marker.
F-10's single 414-character row reproduced byte for byte. OQ-02's claims about the lazy `runner_shared`
import and `rs_lane_superseded` both check out. The `aw specs note` hazard is real and its fix is
verified: run against this spec's exact text, `specs._append_history` prepends and preserves both prior
records, with `pr5b0t` and `0ta5vg` intact and the tracked file untouched.

WHAT REVIEW FOUND ARE THREE EXECUTOR TRAPS, none of which changes the design.

**V-03 PREDICTS THE WRONG NUMBER OF FAILURES (PR-401, MEDIUM).** E-03 calls the
existing-outside-the-repository case "the discriminating one" and V-03 requires showing it failing
"while the other three pass". Measured over all four inputs with the predicate rewritten as
`lane_worktree_display(...) is None`: TWO diverge, not one. The FALSY case fails too, because a falsy
record yields `None`, so the naive form answers "provably absent" for a lane that never had a worktree
and would print the marker on exactly the row the item asks it to stay off. This strengthens F-03 (the
naive form is wrong twice over) but it makes V-03 as authored unsatisfiable as literally written, and an
executor seeing two failures where one was predicted could reasonably conclude the fixture was broken
and "fix" it by deleting an assertion.

**THE RECLAIMED FIXTURE SWAPS WHICH `worktree` VALUE THE RECORD CARRIES (PR-402, MEDIUM).**
`describe_lane` prefers the REGISTERED worktree over the recorded `preserved_worktree`. Measured before
and after `git worktree remove --force` on the real `_fixture` shape: BEFORE, `rec["worktree"]` is the
live in-repo path (exists, display `.aw/worktrees/lane01`); AFTER, git deregisters the tree and the
fallback yields the fixture's ABSOLUTE home-directory value (absent, display None, marker fires). E-04 did
not mention this. It is a feature (the reclaimed case now exercises the leak guard on a genuine absolute
home path, and the rendered detail measured clean of any home-directory prefix), but an executor asserting on
`rec["worktree"]` would be asserting on a value whose identity changes across the operation the fixture
performs.

**TWO LIVE COUNTS HAD ALREADY DRIFTED BY REVIEW (PR-403, LOW).** F-02 states 298 readable records / 519
lane records / 514 absent / 5 exists; re-measured four hours later through the same probe shape: 301
readable / 538 / 531 / 7, with the `lane_state` census 532/1/3/2 against the plan's 515/1/1/2. Every
CONCLUSION survives and is reinforced (the reclaimed case still dominates; the never-had-one case is
still ZERO in the live corpus, which is why F-05's fixture is necessary). But the repository's own
convention forbids a live-artifact count as an acceptance bar, and V-02 pointed at the row count as
though it were fixed.

**NO EXISTING ASSERTION COVERS THE EDITED SEGMENT (PR-404, LOW).** The only existing test driving this
`bits` assembly asserts on `rec.location` alone and patches in a sentinel record with no `worktree` key,
so it could not observe the marker either way. Worth stating because it makes E-04 net-new coverage
rather than a strengthening, and because it means a green suite proves nothing about this segment.

**THE GATE NAMED NO FORBIDDEN NEIGHBOUR (PR-405, LOW).** `lane_worktree_display` nearly answers the new
predicate's question and sits in a file the plan edits, so the temptation to fold the marker decision
into it is real; doing so would destroy the additivity E-03 asserts. `describe_lane` is a pinned
fingerprint symbol in the same file.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. Three open questions were resolved by the author and all three survive review (OQ-03 upheld on the
maintainer-ownership ground, which is the operative one: a reviewer has no standing to re-decide a
presentation choice the item assigns to the maintainer). OQ-04 is new, recording the unreadable-path
fail direction, whose conservative directions point opposite ways for the two callers.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | MEDIUM | IN-SCOPE | E. Testing / D. Anti-regression | plan E-03 ("the fourth case is the discriminating one"), V-03 ("FAILING while the other three pass"); `runner_shared.lane_worktree_display`'s `if not worktree: return None` | V-03 PREDICTS ONE FAILURE WHERE TWO OCCUR, making its evidence requirement unsatisfiable as written. Under the naive `display is None` form, the FALSY case diverges as well as the existing-outside case, because a falsy record also yields `None`, so the naive predicate answers "provably absent" for a lane that never had a worktree - the exact row the item asks the marker to stay off. An executor seeing two reds where one was predicted may conclude the fixture is wrong and delete an assertion, removing the very guard this plan exists to add. | C:Low; U:Low; S:Low; F:Low; Overall:Low (a corrected count and a strengthened finding; no code design changes) | FIXED | Added F-13 with the divergence probe naming both cases. E-03 now states both discriminating cases and tells the executor to expect BOTH red. V-03 requires EXACTLY TWO failures, names which two, and says a single failure means the fixtures do not match E-03. The gate adds that V-03's two and V-04's one are both correct and that any other count has not reproduced the measurement. |
| PR-402 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing | `describe_lane`'s preference for the REGISTERED worktree (recorded in `StrandedLaneViewTests._fixture`'s own comment); before/after probe across `git worktree remove --force` | THE RECLAIMED FIXTURE SILENTLY CHANGES WHICH VALUE `rec["worktree"]` HOLDS, and E-04 did not say so. Measured: before the remove it is the live in-repo path (display `.aw/worktrees/lane01`); after, git deregisters the tree and the fallback supplies the fixture's absolute home-directory value (display None, marker fires). An assertion on the record field rather than on the rendered detail would be pinned to a value whose identity changes across the operation the fixture performs. | C:Low; U:Low; S:Low; F:Medium (a test asserting the wrong field could pass for the wrong reason); Overall:Medium | FIXED | Added F-14 with the before/after probe and the rendered-detail leak measurement. E-04 now requires asserting on the rendered `detail`, states the swap and why it is a feature, and repeats the runtime-composition rule for any new absolute fixture value. V-04 requires stating that the reclaimed record carries the absolute value at render time, so the leak assertion is exercising the real shape. |
| PR-403 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | plan F-02 (298/519/514/5), F-10 (515/2/1/1); re-measurement in this lane (301/538/531/7; 532/1/3/2) | TWO LIVE POPULATIONS ARE PRESENTED AS MEASUREMENTS AND HAVE ALREADY DRIFTED, and V-02 pointed at the row count as a bar. The repository's convention is that a criterion counting live artifacts must state the PROPERTY and require re-derivation at execution time. Every conclusion the plan draws survives unchanged; only the digits moved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16 with the re-measurement and an explicit statement that the conclusions are reinforced. F-02 and F-10 now label their digits as context and name the PROPERTY that must hold. V-02 requires re-deriving the row set in the executing tree and states the bar is before/after equality, never any count written in the plan. V-04's suite comparison now says to compare failing node ids rather than totals. |
| PR-404 | LOW | UNDER-SCOPE | E. Testing | `tests/test_runner_shared.py::test_attention_stranded_lane_drift_delegates_to_shared_records` (asserts `[rec.location ...]` twice); its sentinel record carrying no `worktree` key | NO EXISTING ASSERTION COVERS THE SEGMENT THIS PLAN EDITS, which the plan neither claimed nor ruled out. The one test driving this `bits` assembly asserts on `location` only and its sentinel is the never-had-one shape, so it could not observe the marker in either direction. This makes E-04 net-new coverage and means a green suite proves nothing here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 with both assertions read and the sentinel probed. E-04 opens by stating it is net-new coverage rather than a strengthening. The Scope check's under-scope paragraph records the same fact. |
| PR-405 | LOW | UNDER-SCOPE | G. Plan executability | plan gate; `runner_shared.lane_worktree_display` and `describe_lane`, both in a declared path | THE GATE NAMED NO FORBIDDEN NEIGHBOUR although the most tempting wrong edit is in a file the plan declares. `lane_worktree_display` nearly answers the new predicate's question, and folding the marker decision into it (or hoisting its `_exists` helper) would break the additivity E-03 asserts. `describe_lane` is a pinned fingerprint symbol. E-01 forbids both in passing; the gate did not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a do-not-edit paragraph to the gate naming both functions with the reason for each, and restating F-06's pinned-versus-unpinned measurement. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The naive form is refuted by two assertions, not one. Correct the count, or drop the weaker case to make V-03's "exactly one" true? | CORRECT THE COUNT and keep both assertions, requiring exactly two reds. | (a) Drop the falsy assertion so one red remains - rejected: the falsy case is the never-had-one row the ITEM explicitly asks the marker to stay off, so it is the single most important behavior to pin, and removing it to tidy a prediction would delete the guard for the item's own stated requirement. (b) Leave V-03 as written - rejected: an executor seeing two reds where one was predicted is invited to "repair" the fixture, and a mutation whose expected result is misstated is not a usable guard. | Divergence probe over E-03's four inputs: the naive form's answers differ from the wanted answers at `2 falsy` and `4 existing-outside-non-lane`. `lane_worktree_display`'s `if not worktree: return None` is the mechanism. The item's own words: "the marker appears only when the record HAD a worktree that is now absent, not when it never had one". | yes |
| D-2 | Is the reclaimed fixture's record-field swap a defect in the fixture design, or a property to document? | DOCUMENT IT and require assertions on the rendered `detail`. | (a) Change the fixture to keep the in-repo path recorded after the remove - rejected: that would mean not using `_fixture`'s real recorded shape, and the absolute value is what makes this case exercise the leak guard the surface's own spec clause F8a exists for. (b) Say nothing and let the executor discover it - rejected: the natural assertion for "the worktree is gone" is on `rec["worktree"]`, which is precisely the field that changes identity, so silence invites a test that passes for the wrong reason. | Before/after probe on the `_fixture` shape: record worktree goes from the in-repo path (exists, display `.aw/worktrees/lane01`) to the absolute home path (absent, display None). `_fixture`'s own comment states `describe_lane` prefers the registered worktree. Rendered detail measured free of `/home/` and of the absolute string. | yes |
| D-3 | Should the predicate treat an unreadable path as absent, when that direction ADDS a marker rather than suppressing output? | YES, inherit `lane_worktree_display`'s direction, as E-01 already specifies; recorded as OQ-04 because the two callers' conservative directions oppose each other. | (a) Treat unreadable as PRESENT and suppress the marker - rejected: it restores the silent ambiguity this item exists to remove, and does so exactly where the reader most needs telling something is wrong with the path. (b) Emit a third distinct marker for an unreadable path - rejected: unrequested new vocabulary on a surface whose wording the maintainer owns, and no measurement shows the case occurring. | `lane_worktree_display`'s `_exists` docstring states the omission direction is conservative "for a rendering decision"; for the marker the same treatment adds rather than removes output, so the shared direction needed checking. Cost of being wrong is one superfluous marker on a row already reported for attention, whose remedy is unaffected. | yes |
| D-4 | OQ-03 asks whether the marker's wording should name the remedy. Re-open it at review? | NO, uphold the author's resolution (the item's literal wording). | (a) Propose better wording - rejected: the item records "DECISION OWNER: maintainer" for this presentation choice, so a reviewer substituting its own phrasing would take a decision it has no standing to take. (b) Escalate it as blocking - rejected: it is explicitly non-blocking, the shipped behavior is already truthful, and E-04 pins the literal so any later change is visible rather than silent. | The item's own `DECISION OWNER: maintainer` line; `lane_remedy_hint` already ends every detail with `aw oc integrate <id6>` (verified present in the one live row), so a remedy-naming marker would duplicate it. | yes |
