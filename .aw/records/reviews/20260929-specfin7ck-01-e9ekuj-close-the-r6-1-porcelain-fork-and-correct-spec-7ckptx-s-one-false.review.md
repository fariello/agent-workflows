# Review findings: plan e9ekuj

- Subject-Id: e9ekuj
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `17387e25` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED before revision (exit 0, `findings: 0`); `--phase review-finalize` conforms after revision
with all five `E-*`/`V-*` pairs. No pre-review snapshot was owed: the plan was committed and unmodified
at review start, and the lane-input copy under `.aw/state/lane-inputs/rev-15/` is byte-identical to the
tracked plan (`diff` reported no difference). NO PRODUCTION FILE, TEST OR SPEC WAS MODIFIED by this
review: every measurement was a read, a read-only CLI call, or a scratch probe in an ephemeral
`TemporaryDirectory`; the two throwaway lint probes were written under `.aw/state/runtime/` and deleted.
Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 49.80s`, 207 deselected.

THE PLAN'S CENTRAL DIAGNOSIS IS CORRECT AND ITS TWO LOAD-BEARING FINDINGS BOTH REPRODUCE. F-1 is live:
`runner_shared.dirty_tree_overlap` still decodes the porcelain format itself (the two-column strip
`entry = line[3:] if len(line) > 3 else line.strip()` and the `" -> "` rename split) while
`lane_containment.parse_porcelain_entries` documents itself "THE ONE PORCELAIN PARSER (spec R6.1)" and
`parse_porcelain_paths` is its stated projection holding "no format knowledge of its own". Both drivers
re-export the shared function (`oc_runipd`, `agy_runipd`), so the fork is reached by every driver, as the
plan says. F-4 reproduces exactly: A12b asserts parts (i)/(ii) "currently have no shipped test since
commit `19313eed` deleted `tests/test_lane_input_manifest.py`", and that file exists at HEAD with 17
tests, restored by `654a3adb` (restorecov `dmxc5h`). F-3 reproduces: `tests/test_runner_shared.py` lists
`dirty_tree_overlap` in `LANE_INTEGRATION_MOVED` and asserts object identity, and the two driver tests
assert only the overlap RESULT, so no existing assertion can fail on a fork.

THE FIX IS PROVABLY BEHAVIOR-PRESERVING, which the plan asserts and did not demonstrate. Probed at
review over 12 porcelain inputs (plain modify, untracked, ignored, rename, quoted-path rename, multiple
entries, blank lines, `MM`, short lines, nested path): the forked decode and `parse_porcelain_paths`
returned identical sets in all 12 cases, 0 differing. So E-02 is a pure R6.1 conformance change, and the
"no behavior change" claim V-02 demands is sound.

E-03'S PATCH POINT WAS VERIFIED TO DISCRIMINATE, which matters because a test that cannot fail is
exactly the gap F-3 records. With a spy bound over `lane_containment.parse_porcelain_entries`, driving
`runner_shared.dirty_tree_overlap` against a real repo with a dirty tracked file returned `['a.txt']`
with the spy recording ZERO calls (so the proposed test FAILS at HEAD, as intended), while
`parse_porcelain_paths(" M a.txt\nR  orig.txt -> dest.txt\n")` returned
`['a.txt', 'dest.txt', 'orig.txt']` with the spy recording ONE call (so the patch point is reached
through the projection E-02 delegates to). Recorded into E-03 so the executor does not have to rediscover
which of the two functions to patch.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (plan executability) / `ipd-structure-and-linting` 5.2-5.3 | `.aw/records/plans/pending/20260929-specfin7ck-01-e9ekuj-*.ipd.md` E-01 `Expected outcome` and the gate's `EXECUTION CONTRACT`; `agent_workflows/ipd_schema.py` `EXEC_STATES`, `VALIDATION_RESULTS` | The conditional-abandon path instructed the executor to record E-02/E-03 and V-02/V-03 `not-needed`, which is not a legal state in either closed vocabulary. Probed on a scratch copy: `Execution state: not-needed` yields `IPD-S401 E-02: unknown execution state 'not-needed'` and `Result: not-needed` yields `IPD-S402 V-02: unknown validation result 'not-needed'`, each flipping the `author` disposition from `conforming` to `error`. An executor following the branch as written would strand the plan mid-execution | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01, V-01, the gate and Proposed changes rewritten onto the legal states: E-02 `blocked` with a required `Execution note:` citing the closing commit, V-02 `blocked` carrying that commit as evidence, and E-03 STILL PERFORMED because the test gap is independent of who closed the fork. The gate now also states the honest consequence, that `IPD-S404` makes a `blocked` E-item unfinalizable, and directs the executor to stop and report for retirement or re-scope rather than force a refused transition |
| PR-002 | MEDIUM | IN-SCOPE | E (testing) / GUIDING_PRINCIPLES P16 | Plan E-04; `tests/test_lane_input_manifest.py` `SealTests.test_an_accidental_in_place_write_fails`, `test_a_restored_write_bit_is_detected` | E-04 instructed the executor to rewrite A12b's coverage sentence to say the restored tests cover parts (i)/(ii), but A12b asks for each file's MODE to be pasted and the restored tests assert no mode string: they assert `PermissionError` on a stray write and a `verify_lane_input_seal` refusal on a restored write bit. Those are the correct tests under P16, so the risk is that a literal reading of E-04 replaces one false sentence with another that overclaims | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires the corrected sentence to describe the coverage as BEHAVIORAL and to name what each test asserts, explicitly forbidding a claim that the tests paste a mode; V-04 makes an overclaiming rewrite a FAILURE of the item |
| PR-003 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | Plan F-6 and workflow-history measurement (1) vs `.aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` | F-6 claimed the spec defines 43 requirement ids rather than the backlog item's 42, and blamed a letter-blind `R[0-9]+\.[0-9]+` pattern. Re-measured: the spec DEFINES 42 (unique line-start `R<n>.<n>[a-z] `) and MENTIONS 43; the 43rd is `R3.3b`, never defined at HEAD, surviving only inside WITHDRAWN criterion A7c and R3.3a's supersession prose. The blamed pattern yields 32, not 42, so it cannot be the cause either. The item's 42 was right and this plan's 43 was the error, and Order 02's E-01 was instructed to carry the wrong figure forward | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 rewritten with the re-measurement, the defined-vs-mentioned distinction, and `R3.3b`'s withdrawn status named; a Deferred row records that nothing is owed against the backlog item's summary and that Order 02 must re-derive the count rather than adopt either number. Coverage conclusion re-verified independently: all 42 defined ids are cited by an executed `lanectn` plan |
| PR-004 | MEDIUM | IN-SCOPE | G (plan executability) / plan-review Step 4 | Plan gate, final paragraph | The gate instructed the executor unconditionally to "move this plan to `executed/` via `aw ipd finalize`", which plan-review Step 4 names as a finding to fix: the obligation is unconditional but its OWNER is conditional, since under `aw oc run`/`aw agy run` the runner owns the transition | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the conditional-ownership wording used across the pending population, plus an explicit instruction not to close backlog `eozq91` (already `graduated`, its gate carried by Order 02) |
| PR-005 | LOW | IN-SCOPE | F (honest documentation) | Plan title, `- Concern:` | Title and Concern claimed the plan refreshes "two stale coverage claims" / "two acceptance-criterion texts (A12b, A15)", while the plan edits only A12b and explicitly defers A15. The two stalenesses are also different in kind: A12b's TEXT is false at HEAD, whereas A15's text is correct and merely undemonstrated since the amendment inverted its gitignored clause | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Title changed to "one false coverage sentence", Concern reworded to name one criterion and to characterize A15 as a re-verification obligation owned by Order 02; new F-8 records the distinction; Scope check and the Deferred row state that A15 receives no edit of any kind |
| PR-006 | LOW | IN-SCOPE | E (testing) | Plan E-03 | E-03 named `parse_porcelain_entries` as the monkeypatch target without saying why, and did not require the spy be restored. `lane_containment` is imported process-wide, so a leaked spy would corrupt unrelated tests under the configured `-n auto` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states why the decoder and not the projection is the right patch point, carries the review probe's measured numbers (0 calls at HEAD, 1 call through the projection) so the executor inherits the demonstration, and requires restoration via `finally` or `monkeypatch` |
| PR-007 | LOW | IN-SCOPE | Step 1 evidence accuracy | Plan F-7; `aw attention --format json` | F-7 recorded `valid: false` repository-wide with no cause, which is a bare condition a reader cannot check. Re-run at review: exactly two violations, both lane hygiene (`attention.lane-superseded` lane `3brgb6`, `attention.lane-stranded` lane `om3rzi`), neither touching a spec, plan or backlog record | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-7 now names both violations and their rule codes, which also strengthens its stated purpose: an executor can now see the condition is lane-only and could not have been caused by this Set |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` is satisfied vacuously). No `BLOCKER` was found.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | When E-01 finds the fork already closed, what should E-03 do, given `not-needed` is illegal and the plan paired E-02 and E-03 as one abandon unit? | E-02 goes `blocked`; E-03 is STILL PERFORMED | (a) block both, which was the plan's own pairing, rejected because it discards the regression test whose absence F-3 measures and leaves the next fork equally invisible; (b) invent a `skipped` state, refused by the closed vocabulary | `agent_workflows/ipd_schema.py` `EXEC_STATES`/`VALIDATION_RESULTS` and the plan's own F-3, which grounds the test gap in the EXISTING assertions rather than in who closed the fork | yes |
| D-2 | Does correcting A12b's sentence require re-verifying A12b's behavior, which would pull Order 02's scope into this plan? | No; the text correction and the re-demonstration stay split | Folding A15/A12b re-demonstration in here, rejected because it would put criterion evidence under V-items scoped to a code fix and leave Order 02 recommending a transition on another plan's evidence | The plan's own OQ-01 resolution and the Set's Order split; Order 02 `uuh71v` E-04 already owns every A12b part including the out-of-position dispatch clause | yes |
| D-3 | Is the A12b edit legitimate for an agent to make while spec `7ckptx` is `approved` and `Blocks-Release: next`? | Yes, as an in-place criterion-BODY correction with the spec declared in `- Scope-Paths:` and the status untouched | Escalating to the maintainer first, rejected because the repository answers it: AGENTS.md states specs are living contracts and a plan amending one must declare the path, which this plan does | AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"; precedent in this spec's own history (`xzroy8` at `095a8619` amended R5.1a/A12b on 2026-09-25 while `approved`); the status guard is on `aw specs set`, which this plan does not invoke | yes |
| D-4 | Should the wrong requirement count be corrected only in F-6, or also in the authoring workflow-history line that states 43? | Correct F-6 and add a Deferred row pointing at the discrepancy; leave the history line intact | Editing the history line, rejected because a workflow-history record is an append-only account of what the author measured at the time, and rewriting it would destroy the audit trail the correction is evidence of | plan-review Step 2.4's rule that a superseded wording be swept and reconciled where readers will find it, satisfied by the pointer rather than by rewriting history | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.

### Edits applied

- Title: "two stale coverage claims" -> "one false coverage sentence" (PR-005).
- `- Concern:`: reworded to one criterion; A15 characterized as Order 02's re-verification obligation (PR-005).
- E-01 `Expected outcome`: abandon branch rewritten onto legal states, with `not-needed` named as illegal (PR-001).
- E-03: patch-point rationale, the review probe's measured discrimination, and spy restoration added (PR-006).
- E-04: behavioral-coverage constraint added so the corrected sentence cannot overclaim (PR-002).
- `## Project conventions discovered`: closed state vocabularies, the `blocked` note requirement, and the `IPD-S404` finalize consequence added, with the probe that demonstrated each (PR-001).
- Findings F-6 rewritten (PR-003), F-7 given its measured cause (PR-007), F-8 added for the A12b/A15 distinction (PR-005).
- `## Proposed changes` items 1 and 4 reconciled with the rewritten E-01 and E-04 (PR-001, PR-002).
- `## Deferred / out of scope`: A15 row strengthened; new `Carrier-Declined` row for the backlog item's count (PR-003, PR-005).
- `## Scope check` under-scope: A15 receives no edit of any kind (PR-005).
- V-01 IS-NOT branch rewritten onto `blocked` (PR-001); V-04 makes an overclaiming rewrite a failure (PR-002).
- Gate: abandon path, legal-state vocabulary, the unfinalizable consequence, conditional finalize ownership, and the do-not-close-`eozq91` instruction (PR-001, PR-004).
