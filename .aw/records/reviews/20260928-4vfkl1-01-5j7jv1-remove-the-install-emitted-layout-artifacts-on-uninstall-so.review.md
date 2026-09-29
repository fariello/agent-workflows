# Review findings: plan 5j7jv1

- Subject-Id: 5j7jv1
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `29309281` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan
was committed and byte-identical to the lane input. Every measurement below was taken in this lane with
`python3 -m pytest` or `python3` directly, never through the `aw` console script, per the plan's own
recorded convention about the ambient `aw` re-exec.

THE TECHNICAL WORK IN THIS PLAN IS EXCELLENT AND IS FULLY VERIFIED. Its measurement discipline held up
under independent re-execution, which is rare: every finding that could be reproduced was reproduced.

- F-01 exactly: `tests/test_installer.py::DeepCleanupTests` plus `UninstallCompletenessTests` gives
  `1 failed, 6 passed`, the single failure being `test_deep_cleanup_records_remove_leaves_no_aw_directory`.
- F-02 exactly: `test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`
  fails at HEAD.
- F-03 exactly: after `install_into_repo` -> `write_setup_marker` -> `uninstall_repo`, the layout subset of
  `changed_out` is `[]` and the survivors under `.aw/` are `.aw/system/`, `layout.json`,
  `layout.schema.json` (plus `.aw/workflow-artifacts/README.md`, which deep cleanup then takes). After the
  full `plan_deep_cleanup` -> `run_deep_cleanup(remove_records=True)`, `.aw/` still exists holding exactly
  those three entries. `.aw/system` after install holds `VERSION`, `layout.json`, `layout.schema.json`,
  `managed-sections.json` and `workflows/`, as F-03 states.
- F-04 verified by APPLYING the fix: the layout subset of `changed_out` becomes both paths, `.aw/` no
  longer exists after the sequence, the three named tests go green (`8 passed`), and a BARE
  `python3 -m pytest` reports `3246 passed, 2 skipped, 3 warnings` with ZERO failures.
- F-05 verified by applying the REJECTED alternative: adding `".aw/system"` to `_DEEP_CLEANUP_ROOTS` puts
  both layout paths into `plan.at_risk` and makes `all_recoverable` False, and the test run gives
  `2 failed, 10 passed` failing exactly `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed`
  and `test_deep_cleanup_regenerable.py::RealInstallIntegrationTests::test_real_install_committed_regenerable_readme_lifecycle`,
  the two tests and the two node ids F-05 names.
- F-06 verified by reading the pre-manifest fallback, which removes `AW_SYSTEM_WORKFLOWS_DIR` and
  `f"{AW_SYSTEM_DIR}/{VERSION_FILE}"` as claimed, and by the survivor enumeration showing only the two
  layout files left under `.aw/system/`.
- F-07 verified: the slow subset with the fix applied is `1 failed, 201 passed`, the sole survivor being
  `test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, exactly as
  predicted and owned by `g0bdgg`.
- F-08 verified verbatim in `.github/workflows/tests.yml`, including the owning-item comment naming
  `57dwkc`, `4vfkl1`, `3ypquf`, `g0bdgg` and the stated flip condition.

Both probes were reverted; `git status --short` is clean and this review commits no source change.

WHAT BLOCKS IS NOT THE FIX BUT A DUPLICATE PLAN THE AUTHOR COULD NOT SEE.

**A SECOND PENDING PLAN MAKES THIS IDENTICAL EDIT, AND ONLY ONE MAY RUN (PR-801, BLOCKER, OPEN).** Plan
`g1w58u` (`- Status: to-review`, `- From-Backlog: 57dwkc`, `- Set: 57dwkc`) was authored the same day and
takes the same route: its E-02 changes the same `uninstall_repo` step, iterating the same
`AW_LAYOUT_JSON_PATH`/`AW_LAYOUT_SCHEMA_PATH` constants through the same
`_uninstall_remove`/`_record_changed`/`actions.append` trio, and its E-03 creates the SAME new file
`tests/test_uninstall_layout_artifacts.py` with the same default-visible-plus-one-slow-class shape. This
also falsifies OQ-02's premise and its remedy. OQ-02 assumed `57dwkc` was an unclosed duplicate needing a
post-execution `aw backlog set done 57dwkc --evidence ...` handoff; measured, `57dwkc` is already
`graduated` (by run `run-20260928T235632Z-1358353`) to `g1w58u`, so it is not awaiting closure, it is
awaiting its own carrier. Executing both plans would apply the removal twice and the second would collide
creating a file the first wrote. I did NOT resolve this: retiring another author's plan is a scope and
priority decision that belongs to the maintainer. It is raised as OQ-03 with `- Blocking: yes`, so
`aw ipd lint` now refuses this plan at `author`, `review-finalize` and `pre-execution` alike (verified:
`IPD-Q501` at all three), and `- Readiness: no-go` records the one genuine not-ready condition. OQ-03
carries three routes and a recommendation: run this plan and retire `g1w58u`, on the single objective
difference that this plan also corrects the now-false `PRE-EXISTING FAILURE` docstring (E-04) and carries
the measured rejection of the `_DEEP_CLEANUP_ROOTS` route, which `g1w58u` does not. The recommendation is
explicitly not a decision.

**E-03'S FALLBACK HEDGE IS DEAD AND WAS PROVEN SO (PR-802, MEDIUM).** E-03 said "if a hand-built fixture
cannot reach the removal block ... fall back to a real install in a class-scoped slow class". That hedge
is the escape hatch through which the plan's own central goal leaks away, since taking it slow-marks the
primary cases and reproduces exactly the invisibility F-10 exists to fix. Review built the fixture and
measured it: `git init`, a commit, the two layout files, an unrelated `.aw/system/` sibling and an
`.aw/.gitignore`, then `engine.uninstall_repo(repo, use_git=True, force=True, changed_out=[])`. The
removal block IS reached, both files are removed, both paths appear in `changed_out`, the unrelated
sibling SURVIVES and keeps `.aw/system/` alive (the negative control), and with no sibling both
`.aw/system/` and `.aw/` are pruned. Elapsed 0.008s against the 2 to 3.4 seconds an install costs. FIXED:
the fallback is recorded as contradicted by measurement, so taking it is now itself a finding.

**THREE QUOTED SUITE TOTALS WERE BARS THAT WILL DRIFT (PR-803, MEDIUM).** `## Required tests` told the
executor that authoring measured `3158 passed, 2 skipped` and that "a materially different count is itself
a finding to report rather than to normalize". Review measured `3246 passed, 2 skipped` with the same fix,
and the slow subset `1 failed, 201 passed` where authoring saw `1 failed, 199 passed`. The FAILING SET was
identical both times; only the totals moved. As written the instruction would have had a correct executor
report a finding for a number that drifts with every intervening commit. FIXED by demoting all three
totals to context and restating the bar as the property that actually holds: zero failures, a passed count
no lower than the executor's own measured baseline, and a slow-subset survivor set containing only
`g0bdgg`'s test.

**E-01 CARRIED A CRASHING PROBE CALL AND THE WRONG STOP DIAGNOSIS (PR-804, LOW).** Its probe sequence
omits `run_deep_cleanup`'s positional `use_git`, which raises
`TypeError: run_deep_cleanup() missing 1 required positional argument: 'use_git'` (hit at review). And its
stop condition, "if the survivor set is already empty, report the defect fixed", would misattribute the
likeliest cause: given PR-801, the likeliest reason the defect is already gone is that `g1w58u` executed
first. FIXED: the call signature is given, and the stop instruction now directs the executor to check
`git log -S AW_LAYOUT_JSON_PATH` and `g1w58u`'s disposition before concluding.

**OQ-01 AND OQ-02 ATTRIBUTED THEIR DECISIONS TO THE EXECUTOR (PR-805, LOW).** Both carried
`- Owner: executor`, but both are design decisions the plan author made from repository evidence, and an
executor performs steps rather than owning decisions. The field is what a later reader uses to know who
to ask. FIXED to name the plan author, with the reason stated.

`aw check plans` now reports exactly one finding for this plan, `check.ipd-lint-diagnostic` carrying the
intended `IPD-Q501`. The `check.ipd-uncarried-obligation` error that OQ-03 initially introduced was
resolved by giving the question `- Carrier: 57dwkc`, the live gated item whose plan is the other half of
the collision, so the question cannot vanish when this plan terminates.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | BLOCKER | IN-SCOPE | C. Architecture; G. Executability | `g1w58u` at `- Status: to-review`, `- From-Backlog: 57dwkc`; its E-02 ("ALSO removes the two install-emitted layout artifacts ... Iterate the NAMED CONSTANTS `AW_LAYOUT_JSON_PATH` and `AW_LAYOUT_SCHEMA_PATH`") and its E-03 naming `tests/test_uninstall_layout_artifacts.py`; `- Graduated-To: 57dwkc` plus the graduation record on item `57dwkc` | A second pending plan makes this identical edit and creates the same new test file, so exactly one of the two may execute; running both applies the removal twice and collides on the file. OQ-02's premise that `57dwkc` is an unclosed duplicate awaiting an evidence handoff is falsified: it is already `graduated` to `g1w58u`. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium-High (choosing which plan runs, and retiring the other, is a scope and priority decision the reviewer has no authority to make) | OPEN | Escalated into the plan as blocking OQ-03 with `- Finding: PR-801` and `- Carrier: 57dwkc`, three routes and a labelled recommendation. `IPD-Q501` now refuses the plan at every checkpoint; `- Readiness: no-go`. OQ-02's falsified remedy is marked superseded. |
| PR-802 | MEDIUM | IN-SCOPE | E. Testing | Hand-built fixture measured at review: removal block reached, both files removed, both paths in `changed_out`, unrelated sibling survives and keeps `.aw/system/`, both dirs pruned when no sibling; 0.008s | E-03's "if a hand-built fixture cannot reach the removal block ... fall back to a real install [slow-marked]" is an escape hatch that would slow-mark the primary cases and reproduce the exact invisibility F-10 exists to fix. The fixture demonstrably works. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded the measurement in E-03 and stated that taking the fallback now contradicts it and is itself a finding. |
| PR-803 | MEDIUM | IN-SCOPE | E. Testing | Authoring `3158 passed, 2 skipped` and slow `1 failed, 199 passed`; review `3246 passed, 2 skipped` and slow `1 failed, 201 passed`, with an identical failing set | Three quoted totals were stated as bars ("a materially different count is itself a finding"), but they drift with every intervening commit, so a correct executor would report a finding for normal drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Demoted all three to context; restated the bar as zero failures, a passed count no lower than the executor's own baseline, and the named slow-subset survivor set. |
| PR-804 | LOW | IN-SCOPE | G. Executability | `TypeError: run_deep_cleanup() missing 1 required positional argument: 'use_git'`, hit at review running E-01's probe as written | E-01's probe sequence omits a required positional argument, and its "survivor set already empty -> report fixed" stop condition would misattribute the likeliest cause, which per PR-801 is `g1w58u` having executed first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gave the correct call and added the duplicate-plan check to the stop instruction. |
| PR-805 | LOW | IN-SCOPE | G. Executability | `- Owner: executor` on OQ-01 and OQ-02, whose rationales record decisions made at authoring from repository evidence | An executor performs steps and does not own design decisions; the field tells a later reader who to ask, so a wrong owner misdirects them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both now name the plan author, with the reason stated inline. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Two pending plans make this identical edit. Should the reviewer pick one and retire the other? | NO. Escalate to the maintainer as a blocking open question with three routes and a labelled recommendation | (a) resolve it by retiring `g1w58u`, rejected because retiring another author's plan is a scope and priority decision outside a reviewer's authority and would be exactly the "never guess a human decision" failure; (b) note it non-blocking and let execution proceed, rejected because whichever plan runs second collides, and nothing downstream detects cross-plan duplicate intent since the runner isolates lanes | `g1w58u` `- Status: to-review` with the same E-02 constants and the same E-03 filename; `57dwkc` already `graduated` to it; `IPD-Q501` verified to refuse at `author`, `review-finalize` and `pre-execution` | yes (nothing is deleted; answering the question is the whole remedy) |
| D-2 | Is the plan's chosen fix location (`uninstall_repo` rather than `_DEEP_CLEANUP_ROOTS`) correct? | YES, confirmed by independently applying BOTH candidates | Accepting OQ-01's reasoning without re-measuring, rejected because the whole claim rests on a measured regression and a review that does not reproduce it cannot endorse it | The `uninstall_repo` route: three named tests green, bare suite `3246 passed, 2 skipped`, zero failures. The `_DEEP_CLEANUP_ROOTS` route: both layout paths in `at_risk`, `all_recoverable` False, `2 failed, 10 passed` on the two predicted node ids | yes |
| D-3 | What carrier should the new blocking OQ-03 name, given `check.ipd-uncarried-obligation` is `error`? | `57dwkc` | (a) leave it uncarried, rejected because the rule is `error` and the question would vanish from `aw attention` once this plan reached `executed`; (b) name `4vfkl1`, rejected because that is this plan's own source item and would be closed by this plan's execution, so it is the weaker survivor | `check.ipd-uncarried-obligation` detail: "once this plan reaches `executed` it classes `done` ... and this vanishes with no record"; `57dwkc` is live, `graduated`, and carries `- Blocks-Release: next`; re-measured to 1 finding after the fix | yes |
| D-4 | Does the plan need a spec amendment? | No | Amending spec `kw5y2s`, rejected because Section 6.1 governs what `emit_layout_artifacts` WRITES and this plan does not touch emission | The same two files are written at the same paths with the same content; no approved spec states uninstall preserves them, and the existing tests already assert the opposite | yes |

PR-801 is left OPEN at BLOCKER severity, above the repository's default `HIGH` gate threshold, and is
therefore escalated into the plan as a `- Blocking: yes` question carrying `- Finding: PR-801`, per the
Step 4 escalation rule. No `Reversible: no` decision was taken, so no further escalation is owed.
