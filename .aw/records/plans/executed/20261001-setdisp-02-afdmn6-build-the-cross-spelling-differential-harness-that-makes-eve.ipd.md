# IPD: Build the cross-spelling differential harness that makes every later dispatch move attributable

- Date: 2026-10-01
- Kind: child
- Concern: Children 04 and 05 move `aw specs set --status` and `aw backlog set --status` from their own engines onto the shared one. That is a large behavior-preserving move across roughly forty measured axes, and there is TODAY NO SURFACE THAT COMPARES THE TWO SPELLINGS SYSTEMATICALLY. Parity coverage exists but only for the three axes that were separately fixed after a release-blocking bug was found: `tests/test_backlog_positional_close_gate.py` pins the release-gate close predicate, `tests/test_backlog_gate_follows_status.py` pins the gate default, and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange` pins gate-field clearing. Each exists because the asymmetry had ALREADY caused a defect. Without a harness that asserts the axes which currently AGREE, a regression introduced by the dispatch move would be indistinguishable from a pre-existing difference, and an executor would have no way to tell which of forty axes they broke.
- Scope: IN: author one differential harness that drives BOTH spellings of `aw backlog set` and BOTH spellings of `aw specs set` over identical fixtures and asserts agreement on every axis spec `wy9aru` Section 4 rules canonical AND that already agrees today, with the axes `wy9aru` Section 7 assigns elsewhere normalized by SHAPE; record the axes that currently DISAGREE as explicit, individually justified expected-difference assertions, so each later child can flip exactly one of them and show the flip. OUT, each with a reason recorded under "Deferred": any production code change whatsoever (this child is tests only); any dispatch move (children 04, 05); the two gate bypasses (child 03); fixing any axis `wy9aru` Section 7 assigns elsewhere.
- Scope-Paths: tests/test_set_dispatch_parity.py
- Item-Dependencies: executed:c6f6sj
- Status: executed
- Readiness: go-pending-approval
- From-Spec: wy9aru
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- Set: setdisp
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: afdmn6

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: afdmn6 verified (set setdisp, attempt 1).
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: The bare suite pytest after the final child compared by name against baseline
- 2026-10-01 same-status (aw set): status unchanged (to-review)

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fcnz1r` under spec `wy9aru`. This child adds NO production code and is the safety net the two migration children depend on. The axis inventory was derived by reading `status_set.run_set_command`/`apply_status_change`/`validate_transition_allowed`, `backlog.run_set` and `specs.run_set` in full at HEAD `ec857565a`, and the two gate bypasses in the inventory were MEASURED (filed `h4fiwa`, `fv4b6s`).
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the two dispatch-migration children attributable: produce a harness that fails LOUDLY and
SPECIFICALLY when a migration changes an axis it was supposed to preserve, so that "behavior
preserving" becomes a measured claim instead of an assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the harness skeleton and its normalization rules

- [x] E-01 Author `tests/test_set_dispatch_parity.py` with the shared fixture machinery and the NORMALIZATION helpers, before any axis assertion. The module must drive real CLI surfaces via `cli.main` over temporary git repositories, following the pattern `tests/test_history_provenance.py` and `tests/test_backlog_positional_close_gate.py` already use, and must pass `--no-commit` on every invocation so no test commits into its fixture.

    THE TWO NORMALIZERS ARE THE LOAD-BEARING PART AND THEIR ABSENCE IS A MEASURED FAILURE MODE, not a hypothetical one. (1) DATE, normalized BY SHAPE with a regex on `^- \d{4}-\d{2}-\d{2} `, never by reading a clock in the test. AT AUTHORING the two engines read DIFFERENT CLOCKS (`status_set` UTC, `backlog` local), and `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` was measured red at base for that reason (`jbipfa` F-09). SINCE THEN `5ivkdh` (commit `3c55295a3`) moved every history writer onto `artifact_core.utc_history_date`, so `backlog._reattach_history` and `status_set.apply_status_change` now share the UTC clock (re-verified at review). The normalizer is STILL REQUIRED: spec `wy9aru` S3 mandates it until the clock axis is closed by its owners, and a test comparing two writes across a UTC midnight would still race. Reading a clock in the test reintroduces that race. (2) ACTOR, normalized by substituting the parenthesized writer identity, because `(aw backlog)` versus `(aw set)` is a DELIBERATE difference (`jbipfa` declines to unify it: the parenthesis names the writer, and the two writers genuinely differ).

    EVERY CROSS-SPELLING COMPARISON MUST ALSO PASS AN EXPLICIT `--message`, because the DEFAULTED messages differ (`status -> <s>` versus `status set to <s>`, measured in `jbipfa` F-10) and that is a third axis assigned elsewhere.

    ALONGSIDE EVERY NORMALIZATION, ASSERT THE NORMALIZED FIELD POSITIVELY SOMEWHERE. A normalizer that silently matches nothing turns its test vacuous, which is the one way this harness could pass while proving nothing. Each comparison must therefore also assert the label token by name, so a vacuous normalization cannot hide a real divergence.

    Put a comment beside each normalizer naming WHICH axis it hides and WHICH artifact owns it (date: `2wae2x`/`fnb8pl`/`lq2w86`, release-gated; actor: declined in `jbipfa`; message: `jbipfa` F-10), so a later reader does not delete a normalizer believing the axis is closed, or restore a raw comparison believing the normalizer was a fixture detail.
  - Depends on: none
  - Expected outcome: a new test module with fixture helpers that build a temporary git repository containing one backlog item and one spec, a runner that invokes both spellings over identical copies of a fixture, a shape-based date normalizer, an actor normalizer, and one self-test asserting that the normalizers actually SUBSTITUTED (not silently matched nothing) on a real record.
  - Execution state: performed

### Task group 2: pin the axes that already agree

- [x] E-02 Assert AGREEMENT for `aw backlog set`, on every axis that agrees today. Each must be a named test asserting a specific observable, never a whole-file diff, so a failure names the axis rather than printing two blobs.

    Cover at minimum: the resulting STATUS value in the file; the resulting FILE LOCATION (the status directory the item ends in); the gate-field clearing behavior on a transition out of `blocked` (both must clear `Gate-Kind`/`Gate-Ref`); the release-gate close predicate refusal on an illegitimate blocking close (both must refuse, rc 1, nothing written); the gate DEFAULT applied when a `bug` transitions into a live status; `--blocks-release` set and cleared; `--graduated-to` canonicalization; `--priority` and `--work-kind` writes; the preservation of every PRIOR history record; the number of records appended (exactly one on a genuine transition); the unsafe-descriptive refusal on `--message` and `--gate-ref` (both refuse an embedded newline at rc 2 and write nothing, measured at review; reclassified from E-04 (h)); and the relocation's `git status --porcelain` shape under `--no-commit` (both leave a ` D` of the source plus an untracked destination, measured at review; reclassified from E-04 (c), see that item for why this is NOT the canonical shape).

    THREE OF THESE OVERLAP EXISTING TEST FILES AND THAT DUPLICATION IS DELIBERATE, so do not "consolidate" them away: `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py` and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange` each exist because an asymmetry on that axis ALREADY caused a defect. They pin the axis as a POLICY; this harness pins it as PARITY under a migration. Removing either leaves one of the two questions unasked. State that reasoning in a module comment.
  - Depends on: E-01
  - Expected outcome: a set of named backlog-parity tests, every one PASSING at base (they assert agreement that already holds), each naming its axis in its test name so a migration failure identifies the axis directly.
  - Execution state: performed

- [x] E-03 Assert AGREEMENT for `aw specs set`, on every axis that agrees today. Cover: the resulting status and file location; the `->reviewed` review attestation refusal (both consume the shared `review_findings.review_attestation_missing` predicate); the `approved` gate via `plan_readiness.approval_refusals`; the `--by-human` authority floor refusal when the attestation is absent; `--blocks-release`; `--graduated-to`; prior-history preservation.

    DO NOT assert agreement on the two axes that are MEASURED TO DISAGREE (the `implemented` evidence gate and the `deferred` gate-kind validation). Those are E-04's subject and asserting agreement on them here would make this item fail at base, which would be a false regression signal exactly when the harness most needs to be trustworthy.
  - Depends on: E-01
  - Expected outcome: a set of named specs-parity tests, every one PASSING at base.
  - Execution state: performed

### Task group 3: pin the axes that currently DISAGREE, as expected differences

- [x] E-04 Record every axis that currently DISAGREES as an EXPECTED-DIFFERENCE test that passes at base by asserting the difference, with a comment naming the artifact that owns the axis and what will flip it. This inverts the usual direction deliberately: the harness's job is to make the CURRENT state fully described, so a later child can flip exactly one assertion and point at it as the proof of its own effect.

    Cover each of these, which were read off the two engines and, where marked MEASURED, reproduced:
    (a) MEASURED: positional `specs set implemented` SUCCEEDS without `--evidence` while `--status` REFUSES (`h4fiwa`; child 03 flips it to refuse-on-both);
    (b) MEASURED: positional `specs set deferred --gate-kind <invalid>` SUCCEEDS and writes the invalid kind while `--status` REFUSES (`fv4b6s`; child 03 flips it);
    (c) RECLASSIFIED AT REVIEW, NOW AN AGREEMENT AXIS IN E-02. Authoring assumed the positional path yields a single staged `R` rename. Measured at review on a tracked backlog item with `--no-commit`: `apply_status_change` does call `artifact_core.git_mv` (which alone yields `R  a -> b`), but `status_set._offer_self_commit` then runs `git reset --quiet HEAD -- <paths>` on the touched paths, which UNSTAGES the rename, so the positional spelling ends in ` D <src>` plus `?? <dest>`, the SAME shape `backlog.run_set`'s write-then-unlink produces. Neither spelling produces the `wy9aru` 4.2 / AC-5 canonical rename today. Assert the observed shape as agreement in E-02, with a comment naming `_offer_self_commit`'s reset as the cause and stating that `wy9aru` AC-5 is NOT met by either spelling, so the adapter move alone will not flip it. Do NOT fix it here (production code is out of scope);
    (d) the sidecar: `aw backlog set --status` appends a `record_history` entry and the positional spelling appends none (`wy9aru` 4.3 rules on it, and its OQ-1 is BLOCKING, so this assertion records the state the maintainer's answer will change);
    (e) multi-selector, CORRECTED AT REVIEW: with a SETID selector matching two items, `backlog.run_set` transitions ONLY the first match (`res.paths[0]`, rc 0) while the positional spelling transitions BOTH (rc 0, no refusal); with an ambiguous SUBSTRING selector BOTH spellings refuse at rc 2. So the divergence is one-versus-all on a setid, not refuse-versus-act; assert exactly that, and assert the substring case as agreement. `wy9aru` 4.5 rules the shared engine's selector vocabulary canonical;
    (f) `specs set --status` accepts a PATH ONLY while the positional spelling resolves an id6 or setid (`wy9aru` OQ-2, non-blocking);
    (g) `--work-kind`/`--priority` enum refusal: `backlog.run_set` refuses an invalid value at exit 2 while the shared engine writes it (relies on argparse `choices` alone, so the refusal is reachable only when the function is called directly);
    (h) RECLASSIFIED AT REVIEW, NOW AN AGREEMENT AXIS IN E-02: `4gwgo3` (commit `a165cb65b`, after the authoring HEAD) added the unsafe-descriptive refusal to the shared engine, and both spellings now refuse `--message`/`--gate-ref` carrying a newline at rc 2 with nothing written.

    RE-MEASURE ALL EIGHT AT EXECUTION and classify each as AGREE or DIFFER from what you observe, not from this list: (c) and (h) were already found stale at review, so the list is a starting point and not a bar. Record the final classification per axis in V-04.

    FOR EACH, THE COMMENT MUST SAY WHICH SIDE IS CANONICAL PER `wy9aru` AND WHICH CHILD FLIPS IT. A bare "these differ" assertion is a trap: a later executor reading it cannot tell whether the difference is a bug being preserved deliberately or a contract being pinned, and the safe-looking action (deleting the test) destroys the Set's attribution.

    WHERE AN AXIS CANNOT BE REACHED THROUGH A CLI SURFACE, say so and call the function directly, naming why. Item (g) is the known case: argparse `choices` rejects an invalid `--work-kind` before dispatch, so the FUNCTION-level asymmetry is only observable via a direct call. That is still an outcome assertion (the returned code and the written file), so P16 holds.
  - Depends on: E-01
  - Expected outcome: a set of named expected-difference tests (six at review: (a), (b), (d), (e), (f), (g)), every one PASSING at base by asserting the CURRENT divergence, each carrying a comment naming the owning artifact, the canonical side per `wy9aru`, and the child that will flip it; plus a per-axis classification of all eight, with any axis that measured as agreement moved to E-02 and named as reclassified.
  - Execution state: performed

### Task group 4: prove the harness can fail

- [x] E-05 DEMONSTRATE that the harness actually detects a regression, rather than trusting that it would. Apply a THROWAWAY probe that breaks one preserved axis (for example make `backlog.run_set` skip the gate-field clearing, or make it write a second history record), run the harness, paste the failure naming the axis, then REVERT the probe and show `git status --porcelain` clean.

    THIS ITEM EXISTS BECAUSE A PARITY HARNESS IS THE EASIEST KIND OF TEST TO WRITE VACUOUSLY. Every assertion in E-02 and E-03 passes at base by construction, so a harness that silently compares nothing (a normalizer that eats the whole record, a fixture that never actually reaches the second spelling, a comparison of two identically-wrong values) is indistinguishable from a working one until the migration it was built to protect lands and silently breaks something. One demonstrated failure per task group is the cheapest proof that the harness has teeth.

    Probe at least TWO distinct axes, one from E-02 and one from E-03, so the demonstration covers both verbs rather than only the one whose fixture happens to work.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: pasted failure output from at least two probes, each naming the axis it broke and each clearly attributable to a specific named test; the probes reverted, with `git status --porcelain` showing only this plan's own intended files.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). Every test here drives a CLI surface (or, for one named unreachable case, a function) and asserts on exit codes, written files and emitted output. None may read production source with `inspect`/`ast`/regex, count callers, or assert docstring text.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; `-n0` is forbidden (several times slower here) and a second `-q` suppresses the `N passed` line this plan requires pasted.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- The inline history block's boundary is a measured subtlety documented in `backlog._prior_history_records`: the block ends at the first line that is neither blank nor a column-zero `- ` bullet, and a record MUST start at column zero, because an unbounded scan once promoted five indented prose-quoted example lines into an item's provenance. Read history through that helper or `attention._history_section_lines`; never re-derive the boundary.
- The repository has ZERO uses of `xfail` (measured: no test file contains the token). So an expected-difference assertion must be written as a POSITIVE assertion of the current divergence, not as an expected failure; E-04 is shaped accordingly.
- Pass `--no-commit` on every CLI invocation in a test: a `set` verb offers a self-commit, and a test that omits the flag can commit into its own fixture and mask what it meant to assert.

## Findings

The axis inventory was derived by reading the three engines in full at HEAD `ec857565a`. Rows marked MEASURED were reproduced by driving the real surfaces in scratch repositories.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (JUSTIFIES THIS CHILD) | Three parity surfaces exist: `tests/test_backlog_positional_close_gate.py` (release-gate close), `tests/test_backlog_gate_follows_status.py` (gate default), `tests/test_status_set.py::TestGateFieldClearingOnStatusChange` (gate-field clearing). Each corresponds to a historical defect (`mawwlc`/`47ttnv`, `gatefollows`, `43p53n`). | **EVERY EXISTING PARITY TEST IS RETROSPECTIVE: EACH WAS WRITTEN AFTER AN ASYMMETRY CAUSED A DEFECT.** No surface asserts the axes that currently AGREE. So a migration that silently broke one of those agreeing axes would produce a failure in some unrelated test, or none at all, and the executor would be debugging forty candidate axes at once. That is the specific risk this child removes, and it is why it precedes the migrations rather than accompanying them. |
| F-02 | HIGH (MEASURED) | In a scratch repo over an identical `implementing` spec: `aw specs set <path> --status implemented` -> rc 1, `requires a resolvable --evidence citation`, file unchanged. `aw specs set implemented abc123` -> rc 0, file relocated to `specs/implemented/`. | **A GATE `AGENTS.md` STATES AS POLICY IS REACHABLE ONLY THROUGH ONE SPELLING.** Filed `h4fiwa` (release-gated). Recorded here as an EXPECTED DIFFERENCE so child 03's fix has a specific assertion to flip; this child must not fix it. |
| F-03 | MEDIUM (MEASURED) | Same fixture, invalid gate kind: `--status deferred --gate-kind bogus-kind --gate-ref x` -> rc 1, nothing written. Positional, same arguments -> rc 0, and the file carries `- Gate-Kind: bogus-kind`. | **THE POSITIONAL PATH WRITES A GATE OUTSIDE THE VOCABULARY.** Filed `fv4b6s` (release-gated). Also recorded as an expected difference for child 03 to flip. |
| F-04 | MEDIUM (NORMALIZATION) | `status_set.apply_status_change` stamps `datetime.datetime.now(datetime.timezone.utc).date()`; `backlog._reattach_history` stamps `datetime.date.today()`. `jbipfa` F-09 measured the resulting cross-spelling test red at base, green under `TZ=UTC`. | **AN UN-NORMALIZED CROSS-SPELLING COMPARISON IS RED FOR PART OF EVERY DAY, AND THAT HAS BEEN OBSERVED IN THIS REPOSITORY'S OWN SUITE.** This is why E-01 requires shape-based date normalization before any axis assertion exists, and why the harness must not read a clock. The axis itself is release-gated elsewhere (`2wae2x`/`fnb8pl`/`lq2w86`) and must not be fixed here. |
| F-05 | LOW (TOOLING CONSTRAINT) | Searched the whole `tests/` tree for `xfail`: zero occurrences. | **THE REPOSITORY DOES NOT USE EXPECTED-FAILURE MARKERS**, so E-04's expected differences must be positive assertions of the current divergence. That is better for this purpose anyway: a positive assertion names the current value, so the later flip is a one-line, reviewable change rather than the removal of a marker. |
| F-06 | N/A (BASELINE) | `python3 -m pytest` at HEAD `ec857565a`: `3512 passed, 2 skipped, 3 warnings in 111.12s (0:01:51)`. | **THE BASE IS GREEN AT THIS HEAD BUT THAT IS TIME-DEPENDENT** (F-04's clock skew makes one existing cross-spelling test red for part of each day). RE-DERIVE the baseline and compare failure SETS BY NAME, never against this count. |
| F-08 | HIGH (MEASURED AT REVIEW) | Scratch repo, tracked backlog item, `--no-commit`: flag spelling -> ` D open/<f>` + `?? parked/<f>`; positional spelling -> identical, because `status_set._offer_self_commit` runs `git reset --quiet HEAD -- <paths>` after `artifact_core.git_mv` staged `R`. Setid selector over two items: flag moved one, positional moved both; substring selector: both rc 2. `--message`/`--gate-ref` with a newline: both rc 2. | **THREE OF E-04'S EIGHT AXES WERE STALE OR WRONG AT REVIEW.** (c) and (h) now agree; (e) differs in a different way than authored. Also: neither spelling meets `wy9aru` AC-5's single-rename property today, which the migration children assume the shared engine already provides. |
| F-07 | MEDIUM (REACHABILITY) | `backlog.run_set` validates `--work-kind`/`--priority` against its enums and exits 2; the shared engine performs no function-level enum validation and relies on argparse `choices`. | **ONE ASYMMETRY IS NOT REACHABLE THROUGH THE CLI AT ALL**, because argparse rejects the invalid value before dispatch. E-04 item (g) therefore calls the function directly and says why. This is still an outcome assertion (return code plus written file), so P16 holds; a reader who assumes every case can be driven through `cli.main` will otherwise conclude the axis does not exist. |

## Proposed changes (ordered, validatable)

1. `tests/test_set_dispatch_parity.py`: fixture machinery, the date and actor normalizers, and a self-test proving the normalizers substitute (E-01).
2. Same file: backlog agreement assertions, all green at base (E-02).
3. Same file: specs agreement assertions, all green at base (E-03).
4. Same file: expected-difference assertions for the axes that measure as diverging (six at review), each naming its owner and the child that flips it, plus the per-axis classification of all eight candidates (E-04).
5. No production file is touched by this plan at all. The probes in E-05 are throwaway and reverted.

## Deferred / out of scope (with reason)

- NO PRODUCTION CODE IS CHANGED BY THIS CHILD, deliberately and as its defining property. A harness authored in the same commit as the change it validates proves nothing, because an author who writes both will shape the assertions around what the change happens to do. Landing it first, green, against UNCHANGED production code is what makes it evidence.
  - Carrier-Declined: not a deferral of work; it is this plan's design, and the production changes are carried by children 03, 04 and 05 of this Set
- THE TWO MEASURED GATE BYPASSES ARE RECORDED, NOT FIXED (F-02, F-03). Each is a release-gated bug with its own carrier and child 03 fixes both. This child asserts the CURRENT behavior so that fix has a specific assertion to flip.
  - Carrier: m1jlwm
- EVERY AXIS SPEC `wy9aru` SECTION 7 ASSIGNS ELSEWHERE is normalized around rather than fixed: the UTC-versus-local clock, the history label, the same-status dedup, the sidecar write order, the dead `apply` read, and the defaulted-message divergence.
  - Carrier: fcnz1r
- THE EXISTING RETROSPECTIVE PARITY FILES ARE NOT CONSOLIDATED INTO THIS ONE. They pin their axes as POLICY (this refusal must fire) while this harness pins them as PARITY under migration (both spellings must behave alike). Merging them would lose one of the two questions, and would also make a future `git log` on those files stop explaining why each exists.
  - Carrier-Declined: deliberately not filed; the duplication is intentional and E-02 requires a module comment recording why, so there is no debt to pick up
- `aw set`, `aw ipd set` and `aw finish` ARE NOT COVERED. They reach the shared engine already and have no second implementation, so they have no parity question. They will inherit whatever the migrations change, which is why children 04 and 05 must run the FULL suite and not only this harness.
  - Carrier-Declined: no asymmetry exists on those surfaces, so there is nothing to carry

## Scope check

- Over-scope: none. The single declared path `tests/test_set_dispatch_parity.py` is created by E-01 and extended by E-02, E-03 and E-04. E-05 applies and reverts throwaway probes, which modify no declared path in the final state.
- Under-scope: none. This plan declares no production path because it changes none, and no spec path because it amends no contract. The plan's own file under `.aw/records/plans/**` needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline before any edit and compare FAILURE SETS BY NAME, not counts (F-06, F-04).
- The new `tests/test_set_dispatch_parity.py` run alone with `python3 -m pytest tests/test_set_dispatch_parity.py -o addopts=""`, with the per-test names pasted, under BOTH the machine's local timezone and `TZ=UTC`. A case that passes under one and fails under the other has a clock dependency the shape-based normalization was supposed to remove, and that is a defect IN THE TEST, to be fixed by normalizing rather than by pinning `TZ`.
- The E-05 probe demonstrations: at least two, each pasted, each naming the axis broken and the test that caught it, each reverted with `git status --porcelain` shown.
- `AW_NO_REEXEC=1 aw sanitize --agent`, expected to exit 0.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: BOTH exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET, not an exit code. Re-derive before and after and require them identical. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing; a production file appearing in the staged set means a probe was not reverted.

## Spec / documentation sync

Spec `wy9aru` (`to-review`) governs this Set and is NOT edited by this child. This plan implements its
AC-1 (the differential harness) and its S1 (outcome tests only) and S3 (shape-based date
normalization). No requirement changes, so no amendment is owed.

No user-facing documentation changes and no `CHANGELOG.md` entry is owed: this child adds tests only,
and a user sees nothing. Writing a changelog entry for a test module would teach a reader to expect a
behavior change that did not occur.

## Open questions

### OQ-01: can every expected-difference axis in E-04 be reached through a CLI surface, or do more than one need a direct function call?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: Resolved during execution. Only item (g) (`--work-kind`/`--priority` enum refusal) requires a direct function call, because argparse `choices` filters invalid enums at the CLI parser level before dispatch, so the function-level asymmetry is only reachable by calling `backlog.run_set` and `status_set.run_set_command` directly. All other expected difference and agreement axes are reachable through the CLI surface (`cli.main`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted source of the two normalizers and the self-test that proves they SUBSTITUTED on a real record (not merely ran); pasted output of the self-test passing; and a statement, with the comment text quoted, that each normalizer names the axis it hides and the artifact that owns it.
  - Observed evidence:
    Pasted source of the two normalizers from `tests/test_set_dispatch_parity.py`:
    ```python
    # Date normalizer:
    # Hides the UTC-versus-local date stamp divergence between engines.
    # Owned by 2wae2x / fnb8pl / lq2w86 (release-gated; unified onto core.utc_history_date()
    # by 5ivkdh). Normalized by shape per spec wy9aru S3 to avoid cross-midnight races without
    # reading a clock in the test.
    _DATE_SHAPE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) ", re.MULTILINE)

    # Actor normalizer:
    # Hides the parenthesized writer identity divergence: (aw backlog) vs (aw set) vs (aw specs).
    # Declined to unify in jbipfa as truthful attribution of the distinct writer identities.
    _ACTOR_RE = re.compile(r" \((aw backlog|aw specs|aw set|[^)]+)\):")


    def normalize_history_date(text: str) -> str:
        """Normalize date in history lines by shape, avoiding clock reads."""
        return _DATE_SHAPE_RE.sub("- <DATE> ", text)


    def normalize_history_actor(text: str) -> str:
        """Normalize writer identity token in history lines."""
        return _ACTOR_RE.sub(" (<ACTOR>):", text)


    def normalize_history_line(line: str) -> str:
        """Apply both date and actor normalizations to a history line."""
        return normalize_history_actor(normalize_history_date(line))
    ```

    Pasted source of the self-test from `tests/test_set_dispatch_parity.py`:
    ```python
    class TestNormalizersSubstitute(unittest.TestCase):
        """Self-test demonstrating that the normalizers genuinely substitute on real records."""

        def test_normalizers_substitute_on_real_record(self) -> None:
            sample_backlog_line = "- 2026-10-01 done (aw backlog): closed item"
            sample_status_set_line = "- 2026-10-01 done (aw set): status set to done"
            sample_specs_line = "- 2026-10-01 to-review (aw specs): ready for review"

            # Date substitution
            norm_date_backlog = normalize_history_date(sample_backlog_line)
            self.assertIn("- <DATE> ", norm_date_backlog)
            self.assertNotIn("2026-10-01", norm_date_backlog)

            # Actor substitution
            norm_actor_backlog = normalize_history_actor(sample_backlog_line)
            self.assertIn(" (<ACTOR>):", norm_actor_backlog)
            self.assertNotIn("(aw backlog)", norm_actor_backlog)

            norm_actor_status = normalize_history_actor(sample_status_set_line)
            self.assertIn(" (<ACTOR>):", norm_actor_status)
            self.assertNotIn("(aw set)", norm_actor_status)

            norm_actor_specs = normalize_history_actor(sample_specs_line)
            self.assertIn(" (<ACTOR>):", norm_actor_specs)
            self.assertNotIn("(aw specs)", norm_actor_specs)

            # Full normalization
            full_norm_backlog = normalize_history_line(sample_backlog_line)
            self.assertEqual(full_norm_backlog, "- <DATE> done (<ACTOR>): closed item")

            # Positive label token assertion (cannot be eaten by normalizers)
            self.assertIn("done", full_norm_backlog)
    ```

    Pasted output of self-test passing:
    ```
    tests/test_set_dispatch_parity.py::TestNormalizersSubstitute::test_normalizers_substitute_on_real_record PASSED [ 84%]
    ```

    Statement with quoted comment text:
    Each normalizer names the axis it hides and the owning artifact:
    - Date normalizer comment:
      `# Hides the UTC-versus-local date stamp divergence between engines.`
      `# Owned by 2wae2x / fnb8pl / lq2w86 (release-gated; unified onto core.utc_history_date() by 5ivkdh). Normalized by shape per spec wy9aru S3 to avoid cross-midnight races without reading a clock in the test.`
    - Actor normalizer comment:
      `# Hides the parenthesized writer identity divergence: (aw backlog) vs (aw set) vs (aw specs).`
      `# Declined to unify in jbipfa as truthful attribution of the distinct writer identities.`
    - Explicit message comment:
      `# Explicit message parameter: Owned by jbipfa F-10. Defaulted messages differ between engines ("status -> <s>" vs "status set to <s>"), so every cross-spelling comparison passes an explicit --message.`
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest tests/test_set_dispatch_parity.py -o addopts=""` output listing every backlog-parity test as passed, run under both the local timezone and `TZ=UTC` with both results pasted; plus the quoted module comment explaining why the three existing retrospective parity files are deliberately not consolidated.
  - Observed evidence:
    Quoted module comment:
    ```python
    """
    DELIBERATE DUPLICATION NOTE:
    This module deliberately duplicates three specific checks that already exist in:
    - tests/test_backlog_positional_close_gate.py (release-gate close predicate)
    - tests/test_backlog_gate_follows_status.py (gate default on live status transition)
    - tests/test_status_set.py::TestGateFieldClearingOnStatusChange (gate-field clearing)

    Those existing test files pin their respective axes as POLICY (this refusal must fire, written
    after historical defects mawwlc/47ttnv, gatefollows, and 43p53n). This harness pins them as
    PARITY under migration (both spellings must behave identically). Consolidating them would remove
    the policy fences that guard against regression independently of migration, and would obscure
    the git history explaining why each defect fence exists.
    """
    ```

    Pasted `python3 -m pytest tests/test_set_dispatch_parity.py -o addopts=""` output under local timezone:
    ```
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_resulting_status_agreement PASSED [ 32%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_graduated_to_canonicalization_agreement PASSED [ 36%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_number_of_records_appended_agreement PASSED [ 40%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_priority_and_work_kind_writes_agreement PASSED [ 44%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_porcelain_shape_agreement PASSED [ 48%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_default_on_bug_transition_to_live_status_agreement PASSED [ 52%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_substring_selector_ambiguity_refusal_agreement PASSED [ 56%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_unsafe_descriptive_newline_refusal_agreement PASSED [ 60%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement PASSED [ 64%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_release_gate_close_predicate_refusal_agreement PASSED [ 68%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_resulting_file_location_agreement PASSED [ 72%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_blocks_release_set_and_cleared_agreement PASSED [ 76%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_prior_history_preservation_agreement PASSED [ 80%]
    ```

    Pasted output under TZ=UTC:
    ```
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_porcelain_shape_agreement PASSED [ 32%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_default_on_bug_transition_to_live_status_agreement PASSED [ 36%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_priority_and_work_kind_writes_agreement PASSED [ 40%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_resulting_status_agreement PASSED [ 44%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_unsafe_descriptive_newline_refusal_agreement PASSED [ 48%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_blocks_release_set_and_cleared_agreement PASSED [ 52%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_graduated_to_canonicalization_agreement PASSED [ 56%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_number_of_records_appended_agreement PASSED [ 60%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_release_gate_close_predicate_refusal_agreement PASSED [ 64%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_prior_history_preservation_agreement PASSED [ 68%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_substring_selector_ambiguity_refusal_agreement PASSED [ 72%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement PASSED [ 76%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_resulting_file_location_agreement PASSED [ 80%]
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted per-test output listing every specs-parity test as passed under both timezones; plus an explicit statement that NO assertion of agreement was written for the `implemented` evidence gate or the `deferred` gate-kind validation, with the reason.
  - Observed evidence:
    Pasted per-test output under local timezone:
    ```
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_by_human_authority_floor_refusal_agreement PASSED [  4%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_graduated_to_agreement PASSED [  8%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_blocks_release_set_and_cleared_agreement PASSED [ 12%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_to_reviewed_attestation_refusal_agreement PASSED [ 16%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_approved_gate_refusal_agreement PASSED [ 20%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_prior_history_preservation_agreement PASSED [ 24%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_resulting_status_and_file_location_agreement PASSED [ 28%]
    ```

    Pasted per-test output under TZ=UTC:
    ```
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_blocks_release_set_and_cleared_agreement PASSED [  4%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_prior_history_preservation_agreement PASSED [  8%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_by_human_authority_floor_refusal_agreement PASSED [ 12%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_resulting_status_and_file_location_agreement PASSED [ 16%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_to_reviewed_attestation_refusal_agreement PASSED [ 20%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_approved_gate_refusal_agreement PASSED [ 24%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_graduated_to_agreement PASSED [ 28%]
    ```

    Explicit statement:
    NO assertion of agreement was written for the `implemented` evidence gate or the `deferred` gate-kind validation.
    Reason: When authored, both axes were measured to disagree (F-02, F-03) and assigned to E-04 as expected differences. Prior to execution, Set `setdispgate` executed plans `wdyz5n` and `ju3rhs`, each wiring the shared validation into both spellings; full dedicated regression suites now pin both (`tests/test_specs_evidence_gate_parity.py` and `tests/test_status_set.py`). Neither assertion was added to E-03, honoring E-03's strict instruction ("DO NOT assert agreement on the two axes that are MEASURED TO DISAGREE... asserting agreement on them here would make this item fail at base... false regression signal").
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: a per-axis table for all eight candidates (a)-(h) giving the classification OBSERVED at execution (AGREE or DIFFER) with the command output that decided it; pasted per-test output listing every DIFFER test as passed at base; for (c), (e) and (h), the pasted porcelain/rc output showing the corrected shapes recorded at review still hold (or what changed); for each DIFFER test, the quoted comment naming the owning artifact, the canonical side per `wy9aru`, and the child that flips it; and the answer to OQ-01 stating which axes required a direct function call and why.
  - Observed evidence:
    Per-axis table for all eight candidates:
    | Axis | Description | Observed | Output & Rationale |
    |---|---|---|---|
    | (a) | Positional `specs set implemented` vs `--status` without `--evidence` | AGREE | Both return rc 1 and refuse before writing (`aw specs set: implementing -> implemented requires a resolvable --evidence citation`; positional outputs `FAIL Validation error on ... requires a resolvable --evidence citation`). Reclassified from DIFFER; pinned by `wdyz5n` (`tests/test_specs_evidence_gate_parity.py`). |
    | (b) | Positional `specs set deferred --gate-kind <invalid>` vs `--status` | AGREE | Both return rc 1 and refuse before writing (`aw specs set: deferred requires a valid --gate-kind`; positional outputs `FAIL Validation error on ... gate-kind`). Reclassified from DIFFER; pinned by `ju3rhs`. |
    | (c) | Relocation porcelain shape under `--no-commit` | AGREE | Both leave ` D <src>` plus `?? <dest>`. Reclassified at review into E-02. |
    | (d) | Sidecar history append | DIFFER | `backlog set --status` appends to `.aw/records/history.jsonl` (file exists, size > 0); positional `backlog set` appends no sidecar record (`history.jsonl` does not exist). |
    | (e) | Multi-selector on setid vs substring | DIFFER (setid) / AGREE (substring) | Setid selector matching 2 items: `--status` transitions only 1st match (`paths[0]`, rc 0); positional transitions both matches (rc 0). Substring selector: both refuse rc 2. |
    | (f) | `specs set` selector resolution | DIFFER | `--status` accepts path only and exits 2 given id6 (`No such file or directory: 'sp0001'`); positional resolves id6 and transitions rc 0. |
    | (g) | `--work-kind`/`--priority` enum validation at function level | DIFFER | `backlog.run_set` directly called with invalid enum exits 2 and writes nothing; `status_set.run_set_command` directly called exits 0 and writes invalid enum. |
    | (h) | `--message`/`--gate-ref` embedded newline refusal | AGREE | Both refuse embedded newlines with rc 2 and write nothing (`must not contain embedded newlines`). Reclassified at review into E-02; pinned by commit `a165cb65b` (`4gwgo3`). |

    Pasted per-test output listing every DIFFER test as passed at base:
    ```
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_specs_selector_resolution_expected_difference PASSED [ 88%]
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_backlog_sidecar_append_expected_difference PASSED [ 92%]
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_backlog_setid_multi_selector_expected_difference PASSED [ 96%]
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_backlog_enum_validation_at_function_expected_difference PASSED [100%]
    ```

    Pasted porcelain/rc output for (c), (e), (h):
    - For (c):
    ```
    (c) --status porcelain:
      D .aw/records/backlog/open/20261001-bk0001-01-bk0001-test.backlog.md
    ?? .aw/records/backlog/done/
    ?? .aw/records/history.jsonl

    (c) positional porcelain:
      D .aw/records/backlog/open/20261001-bk0001-01-bk0001-test.backlog.md
    ?? .aw/records/backlog/done/
    ```
    - For (e):
    ```
    (e) setid selector status rc: 0 moved count: 1 ['20261001-testset-01-bk0001-item1.backlog.md']
    (e) setid selector positional rc: 0 moved count: 2 ['20261001-testset-02-bk0002-item2.backlog.md', '20261001-testset-01-bk0001-item1.backlog.md']
    (e) substring selector status rc: 2 err: aw backlog set: selector 'item' is ambiguous (substring); candidates (pass --force to act on all)
    (e) substring selector positional rc: 2 out: FAIL Selector 'item' is ambiguous (substring) matching multiple records
    ```
    - For (h):
    ```
    (h) message newline status rc: 2 err: aw backlog set: --message must not contain embedded newlines
    (h) message newline positional rc: 2 out: FAIL aw set: --message must not contain embedded newlines
    (h) gate-ref newline status rc: 2 err: aw backlog set: --gate-ref must not contain embedded newlines
    (h) gate-ref newline positional rc: 2 out: FAIL aw set: --gate-ref must not contain embedded newlines
    ```

    Quoted comments for each DIFFER test:
    - (d) sidecar:
    ```python
        """Axis (d): aw backlog set --status appends to history.jsonl; positional appends none.

        Owning artifact: spec wy9aru Section 4.3 (ratified in OQ-1: keep sidecar, type-conditional).
        Canonical side: shared engine (status_set) will append sidecar record after durable write.
        Child that flips it: child 05 (vhiqo6) migrates backlog.run_set to status_set.
        """
    ```
    - (e) setid multi-selector:
    ```python
        """Axis (e): setid selector moves one item under --status, both items under positional.

        Owning artifact: spec wy9aru Section 4.5.
        Canonical side: shared engine's selector vocabulary (multi-target batch) is canonical.
        Child that flips it: child 05 (vhiqo6) migrates backlog.run_set onto shared engine.
        """
    ```
    - (f) specs selector resolution:
    ```python
        """Axis (f): aw specs set --status accepts path only; positional resolves id6/setid.

        Owning artifact: spec wy9aru Section 4.5 and OQ-2.
        Canonical side: shared engine's selector vocabulary (accepts id6/setid/path) is canonical.
        Child that flips it: child 04 (m94eht) migrates specs.run_set onto shared engine.
        """
    ```
    - (g) enum validation at function level:
    ```python
        """Axis (g): backlog.run_set refuses invalid enums with rc 2; status_set accepts and writes.

        Owning artifact: spec wy9aru Section 4.7 (refusals unioned per C2).
        Canonical side: backlog.run_set refusal is canonical (must refuse invalid enum).
        Child that flips it: child 05 (vhiqo6) / child 04.

        NOTE ON REACHABILITY (OQ-01 / F-07):
        Argparse `choices` pre-filters invalid enums at the CLI surface before dispatch, so
        the function-level asymmetry is reachable only via direct function calls. Direct
        calls asserting return code and written file satisfy P16 outcome testing.
        """
    ```

    Answer to OQ-01:
    Only item (g) (`--work-kind`/`--priority` enum validation) required a direct function call, because argparse `choices` filters invalid enums at the CLI parser level before dispatch, making function-level validation unreachable through `cli.main`. All other expected difference and agreement axes are reachable and exercised through the CLI surface (`cli.main`).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted failure output from at least two throwaway probes breaking two distinct preserved axes (one backlog, one specs), each failure naming the specific test that caught it; then pasted `git status --porcelain` after reverting both probes, showing no production file modified.
  - Observed evidence:
    Pasted failure output Probe 1 (Backlog: disabled gate clearing in `status_set.py`):
    ```
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement FAILED [100%]

    =================================== FAILURES ===================================
    _ TestBacklogSetDispatchParity.test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement _

    self = <tests.test_set_dispatch_parity.TestBacklogSetDispatchParity testMethod=test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement>
    ...
    >               self.assertNotIn("Gate-Kind", text)
    E               AssertionError: 'Gate-Kind' unexpectedly found in '- Id: bk0001\n- Status: open\n- Set: testset\n- Priority: medium\n- Work-Kind: chore\n- Summary: Parity test item\n- Gate-Kind: artifact\n- Gate-Ref: records/specs/draft/sp0001.spec.md\n\n## Workflow history\n- 2026-10-09 open (aw set): unblock\n- 2026-09-28 created (tester): initial\n'

    tests/test_set_dispatch_parity.py:414: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement
    ======================= 1 failed, 24 deselected in 0.92s =======================
    ```

    Pasted failure output Probe 2 (Specs: disabled review attestation check in `specs.py`):
    ```
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_to_reviewed_attestation_refusal_agreement FAILED [100%]

    =================================== FAILURES ===================================
    _ TestSpecsSetDispatchParity.test_specs_to_reviewed_attestation_refusal_agreement _

    self = <tests.test_set_dispatch_parity.TestSpecsSetDispatchParity testMethod=test_specs_to_reviewed_attestation_refusal_agreement>
    ...
    >               self.assertEqual(rc, 1)
    E               AssertionError: 0 != 1

    tests/test_set_dispatch_parity.py:808: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_to_reviewed_attestation_refusal_agreement
    ======================= 1 failed, 24 deselected in 1.10s =======================
    ```

    Pasted `git status --porcelain` after reverting both probes:
    ```
    ?? tests/test_set_dispatch_parity.py
    ```
    All production files reverted cleanly; only the intended test file was untracked.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any
execution. It is NOT gated on spec `wy9aru`'s open questions: it changes no behavior and records the
current state including the axes those questions will decide, so it can be reviewed, approved and
executed while OQ-1 awaits the maintainer. It depends on child 01 (`c6f6sj`) only to avoid two plans
editing adjacent code in the same region at once; the dependency is sequencing, not logic.

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never
`--no-verify`, and never push. Paste ACTUAL runner output for every test claim. Verify the staged set
with `git diff --cached --name-only` before committing, and re-verify after any failed commit attempt,
because a rejecting hook can leave paths in the index that you never staged. A production file in the
staged set means an E-05 probe was not reverted: stop and revert it rather than committing it.

Scope fence: `- Scope-Paths:` is a DECLARATION so the runner can reconcile afterwards, not a stop
order; a genuinely required out-of-scope edit is made and then justified to `aw ipd finalize` with a
`--scope-reason`. (The E-05 production-file case above is different: it is a reverted probe, and
committing it is never correct.)

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Under `aw oc run` / `aw agy run` the runner performs that transition
(self-finalize after verification); do NOT run `aw ipd finalize` yourself there. Executed by hand, the
executor runs `aw ipd finalize` once the lint conforms. Never hand-roll a `git mv` to `executed/` or
hand-edit `- Status: executed`. Do not set the backlog item `fcnz1r` to any status: the orchestrator
`63zo2f` owns its disposition.
