# Review: re-scope check.setid-collision to its within-type half and settle the include_retired split, child 216rgg (Set setidfix)

- Subject-Id: 216rgg
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `a58d8f1b`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0
findings) before semantic review. At `review-finalize` the linter now returns exit 1 with a single
`IPD-Q501`, which is the CORRECT fail-closed state: this review escalated OQ-01 to `Blocking: yes`,
and the gate is supposed to refuse the plan until the maintainer answers. No pre-review snapshot was
needed; the plan was already committed.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this
as a near-self-review and worth less than an independent one.

THE DIAGNOSIS IS CORRECT IN EVERY MEASURABLE PARTICULAR, AND THE RESTRAINT IS THE BEST PART. I
re-ran every count rather than trusting any: 38 findings on the default scope across 28 distinct
setids, all cross-type; 86 with retired records included, of which 5 are the within-type
descriptive conflicts; both emitting branches exactly where cited; the `RuleSpec` row registered
under `I-09`; `I-16` present in `pqsx96` with a Section 4 note that says the code will be repointed
here. The plan is also right about the two things it refuses to do: it will not delete the rule (the
5 genuine findings would go with it) and it will not achieve silence by renaming artifacts, which it
correctly identifies as the retired sweep plan all over again. Its `info`-severity rejection is
grounded in the spec's own measurement rather than in taste.

SO EVERY FINDING BELOW IS ABOUT THE REMEDY, NOT THE DIAGNOSIS, and two of them change what the plan
delivers rather than how it is written.

THE FIRST IS THE ONE THAT MATTERS MOST AND IT IS WHY THIS REVIEW ENDS IN A BLOCKING QUESTION RATHER
THAN A CLEAN PASS. All 5 of the within-type findings that E-02 and E-05 exist to preserve live under
`executed/`. They are therefore visible ONLY when retired records are included. E-04 tells the
executor to make the two surfaces agree on a population, and OQ-01 leans toward EXCLUDING retired
records. Follow both and `check.setid-collision` emits nothing at all, on any surface, today and until
some future non-retired conflict appears: the rule becomes latent and two of the plan's six items
guard code that never runs, while E-02's stated outcome ("the 5 within-type findings still report")
becomes false. That may still be the right end state, but it is a different deliverable from the one
the plan promises, and choosing it silently would be the worst outcome. OQ-01 is re-classified from
non-blocking-executor-choice to blocking-maintainer-decision with a recommendation recorded.

THE SECOND IS A SILENT-REGRESSION HAZARD THE PLAN SPOTTED BUT ONLY ASKED ABOUT. E-02 said to "state
whether" a cross-type predecessor can occupy the shared `seen_sets` slot. It can, and I reproduced
it: `seen_sets` is keyed on the setid alone, `SUPPORTED` iterates `plans` first, so with one PLAN
`demo (PlanDesc)` and two SPECS `demo (Alpha)`/`demo (Beta)`, HEAD emits two cross-type findings and
NEVER reports the genuine spec-vs-spec conflict, and with the cross-type branch removed it emits
zero. E-01 therefore converts a noisy miss into a silent one, precisely for the behavior this plan
is preserving. A same-type guard alone does not fix it (that is what produces the zero); the slot
must be per-type. E-02 now requires that fix and E-05 must pin the fixture in all three states.

THREE SMALLER CORRECTIONS EACH SAVED AN EXECUTION CYCLE. The plan predicted the wrong breaking test:
applying E-01 gives `1 failed, 5958 passed` and the single failure is
`test_adversarial_setid_collision`, which asserts the cross-type case IS a finding and calls it
"adversarial" in its own comment, so its INTENT is now wrong; meanwhile `test_all_runs_collisions_once`,
which F-4 said "must be retargeted", passes unedited because it asserts only id6 counts. E-06's two
premises were both false: the goldens render from a hardcoded synthetic `CommandResult` in
`test_cli_quality_gates.py:68-82` rather than from a corpus scan, so no emission change can alter
them, and no test asserts this rule's invariant VALUE (the field is free text with no validator), so
E-03's repoint is safe by construction. That item accordingly shrank from "regenerate the goldens" to
"prove they need no change", which is a smaller and more honest job. And a fifth rule-id surface was
missing entirely: `test_doctor_remediations.py:132-144`.

I ALSO CORRECTED A COUNTING CLAIM AND AN AMBIGUITY THAT WOULD HAVE LET A WRONG ANSWER LOOK RIGHT. The
38-versus-86 gap is really three populations, because `doctor.py:517-521` demotes `executed/`
findings into `executed_warnings` independently of `include_retired`: measured, `aw check` shows 38,
`aw doctor` shows 81, the predicate returns 86. Reconciling only `include_retired` cannot make the
surfaces agree, so E-04's authored outcome was unreachable as written. Separately the plan says
"`--all`" throughout where it means retired inclusion, but `aw check all` is the TYPE scope (already
the default) and `aw check --all` is the retired flag; an executor conflating them could report
"0 findings" as success while never having looked at the population the surviving rule depends on.

WHAT I LEFT ALONE. The removal of the cross-type emission with no `info` fallback and no flag, the
refusal to repoint the two id6 rules off `I-09`, the refusal to rename anything, the `I-16` repoint
itself, and the deferral of type-scoped resolution to Order 02 are all correct and untouched.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | IN-SCOPE | G/D (deliverable coherence) | all 5 descriptive findings' paths under `.aw/records/plans/executed/`; OQ-01's own lean | E-02/E-05 preserve 5 findings that exist ONLY with retired records included, while E-04 + OQ-01 lean toward excluding them. Follow both and the rule emits ZERO on every surface, making E-02/E-05 guard dead code and E-02's stated outcome false. The plan cannot deliver both of its promises. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | OPEN | Escalated into OQ-01, now `Blocking: yes` and maintainer-owned with a recommendation (INCLUDE, and stop demoting this rule's executed findings). E-04 and E-02 now state the interaction explicitly. |
| PR-002 | high | UNDER-SCOPE | A (silent regression) | scratch fixture: HEAD 2 cross-type findings, conflict missed; cross-type branch removed, 0 findings | The shared `seen_sets` slot (keyed on setid alone, `plans` iterated first) lets a foreign-type predecessor hide a genuine within-type conflict. E-01 turns that noisy miss into a SILENT miss for the exact behavior being preserved. E-02 only asked whether this was possible. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now REQUIRES a per-type slot plus the same-type guard, states that the guard alone is insufficient, and E-05/V-02 pin the fixture in all three states. |
| PR-003 | high | UNDER-SCOPE | E (wrong test predicted) | suite with E-01 applied: `1 failed, 5958 passed`; the failure is `test_adversarial_setid_collision` (`AssertionError: 'check.setid-collision' not found in set()`) | The plan named `test_all_runs_collisions_once` as the affected test; it passes unedited. The test that actually breaks is `test_adversarial_setid_collision`, which asserts the cross-type case IS a finding and whose comment calls it adversarial, so its intent is now wrong and it was undeclared in `Scope-Paths`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 retargeted onto the real failure with its stale comment to correct; F-4 marked half-wrong; the path declared; V-05 requires showing the other two tests unedited. |
| PR-004 | high | UNDER-SCOPE | A/C (unreachable outcome) | `doctor.py:517-521`; measured 38 / 81 / 86 | There is a THIRD population axis (doctor's `executed/` demotion) independent of `include_retired`, so E-04's outcome ("the two surfaces report the same population") is unreachable by changing `include_retired` alone, and the plan's 38-versus-86 framing is incomplete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires deciding BOTH axes and justifying both; the Concern and F-5/F-10 carry the three measured counts; V-04 demands both decisions. |
| PR-005 | medium | IN-SCOPE | E (falsifiable evidence) | `tests/test_cli_quality_gates.py:68-82` | E-06 assumed the goldens are corpus-derived and must be regenerated. They render from a hardcoded synthetic `CommandResult`, so no change to `check_collisions` can alter them, and an executor "regenerating" one would be masking an unrelated renderer change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 rewritten to PROVE the goldens are unchanged and to stop if either moves; V-06 requires the fixture source and a clean `git status` for both files. |
| PR-006 | medium | IN-SCOPE | C (unfounded coupling worry) | `grep I-09\|I-16 tests/` finds only two prose comments; `RuleSpec.invariant` has no validator | E-06 warned that a policy-engine test asserts the rule's invariant FAMILY and that E-03 "may break it". No test asserts the invariant value, so E-03 is safe by construction; the warning would have sent an executor looking for a coupling that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in E-06 and F-6; recorded in the conventions section that the field is a free-text label with no consumer. |
| PR-007 | medium | UNDER-SCOPE | G (missed surface) | `tests/test_doctor_remediations.py:132-144` | A fifth rule-id surface was not named anywhere in the plan: the doctor remediation test asserting `aw group <type> <path> --set <new-set-id>` for this rule, guidance written when the cross-type case was also reported. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to E-06 and to `Scope-Paths`; V-06 requires reading the remediation text for cross-type wording. |
| PR-008 | medium | IN-SCOPE | F/G (invocation ambiguity) | `aw check --help`: `all` is the type scope and default; `-a/--all` is retired inclusion | The plan writes "`--all`" throughout for the retired-inclusive population, but `aw check all` is the type scope and is already the default. Measured: `aw check all` returns 38 (no within-type findings), `aw check --all` reaches 86. An executor conflating them could report zero as success without ever inspecting the surviving population. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Distinction stated in the conventions section, in E-02, and in V-02/V-04, each requiring the exact invocation to be named. |
| PR-009 | low | IN-SCOPE | E (reproducible baseline) | measured `5959 passed, 3 skipped, 2 xfailed` at `a58d8f1b`; `1 failed, 5958 passed` with E-01 | The plan required a baseline but recorded none, and predicted an environmental `test_reporting_contract.py` failure that did not reproduce in a clean worktree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both measurements and the failing node id written into Required tests, with the non-reproducing prediction noted. |
| PR-010 | low | OVER-SCOPE (declaration honesty) | G (scope fence) | `Scope-Paths` versus E-06's revised job | Two golden files are declared as if they will be edited, but after PR-005 they must NOT change, which would leave two declared-but-unmodified paths at finalize with no stated reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Scope check section now states they are deliberately declared-and-expected-unchanged, to be reconciled with a `--scope-ack` rather than silently dropped. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the "all 5 surviving findings are retired-only" fact a detail for E-04, or does it change the plan's readiness? | It changes readiness: escalate OQ-01 to `Blocking: yes`, maintainer-owned, and report NO-GO. | Leaving OQ-01 non-blocking with the fact noted (rejected: the executor would then be free to pick the answer that voids two of the plan's own items, and the plan's E-02 outcome would silently become unachievable). Resolving it myself toward INCLUDE (rejected: it decides whether a shipped `error` rule keeps any live effect, which is the same class of policy call the maintainer just made in D153). | all 5 descriptive findings located under `.aw/records/plans/executed/`; OQ-01's own stated lean toward EXCLUDE | yes |
| D-2 | Should E-02's shared-slot concern remain "state whether it is possible"? | No: reproduce it, and require the fix. It is possible, and E-01 makes it silent. | Leaving it as an investigation (rejected: the answer took one fixture to obtain, and an executor who concluded "not possible" would ship a silent regression in the plan's own protected behavior). Deferring the slot fix to a follow-up (rejected: E-01 is what makes the miss silent, so the two must land together). | scratch fixture measured at HEAD (2 findings, conflict missed) and with the branch removed (0 findings) | yes |
| D-3 | Is a same-type guard sufficient for the surviving branch? | No. It is necessary but not sufficient; the `seen_sets` slot must also be per-type. | Guard only (rejected by measurement: the guard alone produced 0 findings on the three-file fixture, i.e. it silences rather than fixes the miss). | the guard-only patch returning 0 findings on the PLAN + two-SPEC fixture | yes |
| D-4 | Should the review trust F-4's identification of the affected tests? | No: run the suite with E-01 applied. F-4 is half wrong; the real failure is a test F-4 never mentions. | Trusting it (rejected: the plan explicitly told the executor it was "confirming rather than exploring", which is exactly the framing that suppresses re-measurement). | `1 failed, 5958 passed` naming `test_adversarial_setid_collision`; `test_all_runs_collisions_once` passing unedited | yes |
| D-5 | Do the conformance goldens need regenerating? | No, and E-06 must PROVE it rather than edit them; a golden that moves means a renderer changed, which is out of scope. | Regenerating them as instructed (rejected: they are synthetic fixtures, so a regeneration would either be a no-op or would silently absorb an unrelated renderer change). | `tests/test_cli_quality_gates.py:68-82` hardcoding `Diagnostic("b.md", "check.setid-collision", "dup")` | yes |
| D-6 | Does E-03's invariant repoint risk breaking a test that asserts an invariant family? | No. The field has no validator and no value-asserting consumer, so the repoint is safe by construction. | Keeping the warning (rejected: it would send an executor hunting a coupling that does not exist, and might invite a defensive no-op edit). | `grep I-09\|I-16 tests/` returning only two prose comments; no `.invariant` assertion for this rule | yes |
| D-7 | Is the plan's 38-versus-86 gap the whole story? | No: there are three populations, because doctor demotes `executed/` findings independently of `include_retired`. | Accepting the two-way framing (rejected: E-04's outcome would then be unreachable, and an executor aligning `include_retired` alone would report success while the surfaces still disagreed). | `doctor.py:517-521`; measured `aw check` 38, `aw doctor` 81, predicate 86 | yes |
| D-8 | Should the review report GO - PENDING HUMAN APPROVAL, given that 8 of 10 findings are fixed? | No: `REVIEWED - OPEN QUESTIONS` and NO-GO, because a blocking question remains open by this review's own act. | Reporting go-pending-approval (rejected: the readiness vocabulary reserves NO-GO for a genuine not-ready condition, and an unanswered blocking question that determines whether two items have any effect is exactly that). | the plan-review readiness rules; `aw ipd lint` returning `IPD-Q501` at review-finalize | yes |
