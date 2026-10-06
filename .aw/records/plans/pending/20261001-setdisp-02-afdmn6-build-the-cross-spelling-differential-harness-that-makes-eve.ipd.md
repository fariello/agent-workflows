# IPD: Build the cross-spelling differential harness that makes every later dispatch move attributable

- Date: 2026-10-01
- Kind: child
- Concern: Children 04 and 05 move `aw specs set --status` and `aw backlog set --status` from their own engines onto the shared one. That is a large behavior-preserving move across roughly forty measured axes, and there is TODAY NO SURFACE THAT COMPARES THE TWO SPELLINGS SYSTEMATICALLY. Parity coverage exists but only for the three axes that were separately fixed after a release-blocking bug was found: `tests/test_backlog_positional_close_gate.py` pins the release-gate close predicate, `tests/test_backlog_gate_follows_status.py` pins the gate default, and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange` pins gate-field clearing. Each exists because the asymmetry had ALREADY caused a defect. Without a harness that asserts the axes which currently AGREE, a regression introduced by the dispatch move would be indistinguishable from a pre-existing difference, and an executor would have no way to tell which of forty axes they broke.
- Scope: IN: author one differential harness that drives BOTH spellings of `aw backlog set` and BOTH spellings of `aw specs set` over identical fixtures and asserts agreement on every axis spec `wy9aru` Section 4 rules canonical AND that already agrees today, with the axes `wy9aru` Section 7 assigns elsewhere normalized by SHAPE; record the axes that currently DISAGREE as explicit, individually justified expected-difference assertions, so each later child can flip exactly one of them and show the flip. OUT, each with a reason recorded under "Deferred": any production code change whatsoever (this child is tests only); any dispatch move (children 04, 05); the two gate bypasses (child 03); fixing any axis `wy9aru` Section 7 assigns elsewhere.
- Scope-Paths: tests/test_set_dispatch_parity.py
- Item-Dependencies: executed:c6f6sj
- Status: draft
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

- [ ] E-01 Author `tests/test_set_dispatch_parity.py` with the shared fixture machinery and the NORMALIZATION helpers, before any axis assertion. The module must drive real CLI surfaces via `cli.main` over temporary git repositories, following the pattern `tests/test_history_provenance.py` and `tests/test_backlog_positional_close_gate.py` already use, and must pass `--no-commit` on every invocation so no test commits into its fixture.

    THE TWO NORMALIZERS ARE THE LOAD-BEARING PART AND THEIR ABSENCE IS A MEASURED FAILURE MODE, not a hypothetical one. (1) DATE, normalized BY SHAPE with a regex on `^- \d{4}-\d{2}-\d{2} `, never by reading a clock in the test. The two engines read DIFFERENT CLOCKS (`status_set` UTC, `backlog` local), so an un-normalized cross-spelling comparison is red for part of every day: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` is exactly that test and plan `jbipfa` F-09 measured it red at base. Reading a clock in the test reintroduces the same race. (2) ACTOR, normalized by substituting the parenthesized writer identity, because `(aw backlog)` versus `(aw set)` is a DELIBERATE difference (`jbipfa` declines to unify it: the parenthesis names the writer, and the two writers genuinely differ).

    EVERY CROSS-SPELLING COMPARISON MUST ALSO PASS AN EXPLICIT `--message`, because the DEFAULTED messages differ (`status -> <s>` versus `status set to <s>`, measured in `jbipfa` F-10) and that is a third axis assigned elsewhere.

    ALONGSIDE EVERY NORMALIZATION, ASSERT THE NORMALIZED FIELD POSITIVELY SOMEWHERE. A normalizer that silently matches nothing turns its test vacuous, which is the one way this harness could pass while proving nothing. Each comparison must therefore also assert the label token by name, so a vacuous normalization cannot hide a real divergence.

    Put a comment beside each normalizer naming WHICH axis it hides and WHICH artifact owns it (date: `2wae2x`/`fnb8pl`/`lq2w86`, release-gated; actor: declined in `jbipfa`; message: `jbipfa` F-10), so a later reader does not delete a normalizer believing the axis is closed, or restore a raw comparison believing the normalizer was a fixture detail.
  - Depends on: none
  - Expected outcome: a new test module with fixture helpers that build a temporary git repository containing one backlog item and one spec, a runner that invokes both spellings over identical copies of a fixture, a shape-based date normalizer, an actor normalizer, and one self-test asserting that the normalizers actually SUBSTITUTED (not silently matched nothing) on a real record.
  - Execution state: pending

### Task group 2: pin the axes that already agree

- [ ] E-02 Assert AGREEMENT for `aw backlog set`, on every axis that agrees today. Each must be a named test asserting a specific observable, never a whole-file diff, so a failure names the axis rather than printing two blobs.

    Cover at minimum: the resulting STATUS value in the file; the resulting FILE LOCATION (the status directory the item ends in); the gate-field clearing behavior on a transition out of `blocked` (both must clear `Gate-Kind`/`Gate-Ref`); the release-gate close predicate refusal on an illegitimate blocking close (both must refuse, rc 1, nothing written); the gate DEFAULT applied when a `bug` transitions into a live status; `--blocks-release` set and cleared; `--graduated-to` canonicalization; `--priority` and `--work-kind` writes; the preservation of every PRIOR history record; and the number of records appended (exactly one on a genuine transition).

    THREE OF THESE OVERLAP EXISTING TEST FILES AND THAT DUPLICATION IS DELIBERATE, so do not "consolidate" them away: `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py` and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange` each exist because an asymmetry on that axis ALREADY caused a defect. They pin the axis as a POLICY; this harness pins it as PARITY under a migration. Removing either leaves one of the two questions unasked. State that reasoning in a module comment.
  - Depends on: E-01
  - Expected outcome: a set of named backlog-parity tests, every one PASSING at base (they assert agreement that already holds), each naming its axis in its test name so a migration failure identifies the axis directly.
  - Execution state: pending

- [ ] E-03 Assert AGREEMENT for `aw specs set`, on every axis that agrees today. Cover: the resulting status and file location; the `->reviewed` review attestation refusal (both consume the shared `review_findings.review_attestation_missing` predicate); the `approved` gate via `plan_readiness.approval_refusals`; the `--by-human` authority floor refusal when the attestation is absent; `--blocks-release`; `--graduated-to`; prior-history preservation.

    DO NOT assert agreement on the two axes that are MEASURED TO DISAGREE (the `implemented` evidence gate and the `deferred` gate-kind validation). Those are E-04's subject and asserting agreement on them here would make this item fail at base, which would be a false regression signal exactly when the harness most needs to be trustworthy.
  - Depends on: E-01
  - Expected outcome: a set of named specs-parity tests, every one PASSING at base.
  - Execution state: pending

### Task group 3: pin the axes that currently DISAGREE, as expected differences

- [ ] E-04 Record every axis that currently DISAGREES as an EXPECTED-DIFFERENCE test that passes at base by asserting the difference, with a comment naming the artifact that owns the axis and what will flip it. This inverts the usual direction deliberately: the harness's job is to make the CURRENT state fully described, so a later child can flip exactly one assertion and point at it as the proof of its own effect.

    Cover each of these, which were read off the two engines and, where marked MEASURED, reproduced:
    (a) MEASURED: positional `specs set implemented` SUCCEEDS without `--evidence` while `--status` REFUSES (`h4fiwa`; child 03 flips it to refuse-on-both);
    (b) MEASURED: positional `specs set deferred --gate-kind <invalid>` SUCCEEDS and writes the invalid kind while `--status` REFUSES (`fv4b6s`; child 03 flips it);
    (c) relocation shape: the positional path produces a single staged `R` rename in `git status --porcelain` while `backlog.run_set` produces a delete plus an untracked file (`wy9aru` 4.2 rules `git mv` canonical; child 05 flips it);
    (d) the sidecar: `aw backlog set --status` appends a `record_history` entry and the positional spelling appends none (`wy9aru` 4.3 rules on it, and its OQ-1 is BLOCKING, so this assertion records the state the maintainer's answer will change);
    (e) multi-selector: an ambiguous selector makes the positional spelling REFUSE while `backlog.run_set` acts on one arbitrary match (`wy9aru` 4.5 rules the refusal canonical);
    (f) `specs set --status` accepts a PATH ONLY while the positional spelling resolves an id6 or setid (`wy9aru` OQ-2, non-blocking);
    (g) `--work-kind`/`--priority` enum refusal: `backlog.run_set` refuses an invalid value at exit 2 while the shared engine writes it (relies on argparse `choices` alone, so the refusal is reachable only when the function is called directly);
    (h) the unsafe-descriptive refusal on `--message`/`--gate-ref`, present on `backlog.run_set` only.

    FOR EACH, THE COMMENT MUST SAY WHICH SIDE IS CANONICAL PER `wy9aru` AND WHICH CHILD FLIPS IT. A bare "these differ" assertion is a trap: a later executor reading it cannot tell whether the difference is a bug being preserved deliberately or a contract being pinned, and the safe-looking action (deleting the test) destroys the Set's attribution.

    WHERE AN AXIS CANNOT BE REACHED THROUGH A CLI SURFACE, say so and call the function directly, naming why. Item (g) is the known case: argparse `choices` rejects an invalid `--work-kind` before dispatch, so the FUNCTION-level asymmetry is only observable via a direct call. That is still an outcome assertion (the returned code and the written file), so P16 holds.
  - Depends on: E-01
  - Expected outcome: a set of named expected-difference tests, every one PASSING at base by asserting the CURRENT divergence, each carrying a comment naming the owning artifact, the canonical side per `wy9aru`, and the child that will flip it.
  - Execution state: pending

### Task group 4: prove the harness can fail

- [ ] E-05 DEMONSTRATE that the harness actually detects a regression, rather than trusting that it would. Apply a THROWAWAY probe that breaks one preserved axis (for example make `backlog.run_set` skip the gate-field clearing, or make it write a second history record), run the harness, paste the failure naming the axis, then REVERT the probe and show `git status --porcelain` clean.

    THIS ITEM EXISTS BECAUSE A PARITY HARNESS IS THE EASIEST KIND OF TEST TO WRITE VACUOUSLY. Every assertion in E-02 and E-03 passes at base by construction, so a harness that silently compares nothing (a normalizer that eats the whole record, a fixture that never actually reaches the second spelling, a comparison of two identically-wrong values) is indistinguishable from a working one until the migration it was built to protect lands and silently breaks something. One demonstrated failure per task group is the cheapest proof that the harness has teeth.

    Probe at least TWO distinct axes, one from E-02 and one from E-03, so the demonstration covers both verbs rather than only the one whose fixture happens to work.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: pasted failure output from at least two probes, each naming the axis it broke and each clearly attributable to a specific named test; the probes reverted, with `git status --porcelain` showing only this plan's own intended files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). Every test here drives a CLI surface (or, for one named unreachable case, a function) and asserts on exit codes, written files and emitted output. None may read production source with `inspect`/`ast`/regex, count callers, or assert docstring text.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `-n0` is forbidden (several times slower here) and a second `-q` suppresses the `N passed` line this plan requires pasted.
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
| F-07 | MEDIUM (REACHABILITY) | `backlog.run_set` validates `--work-kind`/`--priority` against its enums and exits 2; the shared engine performs no function-level enum validation and relies on argparse `choices`. | **ONE ASYMMETRY IS NOT REACHABLE THROUGH THE CLI AT ALL**, because argparse rejects the invalid value before dispatch. E-04 item (g) therefore calls the function directly and says why. This is still an outcome assertion (return code plus written file), so P16 holds; a reader who assumes every case can be driven through `cli.main` will otherwise conclude the axis does not exist. |

## Proposed changes (ordered, validatable)

1. `tests/test_set_dispatch_parity.py`: fixture machinery, the date and actor normalizers, and a self-test proving the normalizers substitute (E-01).
2. Same file: backlog agreement assertions, all green at base (E-02).
3. Same file: specs agreement assertions, all green at base (E-03).
4. Same file: expected-difference assertions for the eight currently-diverging axes, each naming its owner and the child that flips it (E-04).
5. No production file is touched by this plan at all. The probes in E-05 are throwaway and reverted.

## Deferred / out of scope (with reason)

- NO PRODUCTION CODE IS CHANGED BY THIS CHILD, deliberately and as its defining property. A harness authored in the same commit as the change it validates proves nothing, because an author who writes both will shape the assertions around what the change happens to do. Landing it first, green, against UNCHANGED production code is what makes it evidence.
  - Carrier-Declined: not a deferral of work; it is this plan's design, and the production changes are carried by children 03, 04 and 05 of this Set
- THE TWO MEASURED GATE BYPASSES ARE RECORDED, NOT FIXED (F-02, F-03). Each is a release-gated bug with its own carrier and child 03 fixes both. This child asserts the CURRENT behavior so that fix has a specific assertion to flip.
  - Carrier: m1jlwm
- EVERY AXIS SPEC `wy9aru` SECTION 7 ASSIGNS ELSEWHERE is normalized around rather than fixed: the UTC-versus-local clock, the history label, the same-status dedup, the sidecar write order, the dead `apply` read, and the defaulted-message divergence.
  - Carrier: wy9aru
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
- Status: open
- Owner: executor
- Resolution or deferral rationale: F-07 establishes that item (g) (the `--work-kind`/`--priority` enum refusal) is NOT CLI-reachable because argparse `choices` rejects the value before dispatch, so it must be driven by a direct function call. Whether any of the other seven share that property is answerable only by attempting each, which is E-04's own work. It cannot change the design (a direct call asserting a return code and a written file still satisfies P16); it changes only how many cases carry the explanatory comment. Record the final answer per axis in E-04's evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted source of the two normalizers and the self-test that proves they SUBSTITUTED on a real record (not merely ran); pasted output of the self-test passing; and a statement, with the comment text quoted, that each normalizer names the axis it hides and the artifact that owns it.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest tests/test_set_dispatch_parity.py -o addopts=""` output listing every backlog-parity test as passed, run under both the local timezone and `TZ=UTC` with both results pasted; plus the quoted module comment explaining why the three existing retrospective parity files are deliberately not consolidated.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted per-test output listing every specs-parity test as passed under both timezones; plus an explicit statement that NO assertion of agreement was written for the `implemented` evidence gate or the `deferred` gate-kind validation, with the reason.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted per-test output listing all eight expected-difference tests as passed at base; for each, the quoted comment naming the owning artifact, the canonical side per `wy9aru`, and the child that flips it; and the answer to OQ-01 stating which axes required a direct function call and why.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted failure output from at least two throwaway probes breaking two distinct preserved axes (one backlog, one specs), each failure naming the specific test that caught it; then pasted `git status --porcelain` after reverting both probes, showing no production file modified.
  - Observed evidence:
  - Result: pending

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

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Do not set the backlog item `fcnz1r` to any status: the orchestrator
`63zo2f` owns its disposition.
