# Review findings: plan fv6kep

- Subject-Id: fv6kep
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `54d43a38b`. The plan file was committed and the tree
clean (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE any edit;
`--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:` bullet
reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING CLAIM INDEPENDENTLY, including writing the tests the plan proposes
and running them against live code. The premise is correct and the plan is honest about being coverage
debt rather than a live defect:

- F-01 holds: `rg "PreservesOrderAndDate|PlansGroupPreservesOrder"` over the worktree returns nothing
  and `tests/test_awnaming_grammar_and_producers.py` does not exist.
- F-02 holds exactly: `git show 19313eed^:tests/test_awnaming_grammar_and_producers.py` lists all
  eight named cases, 1 in `PlansMvPreservesOrderAndDateTests` and 7 in
  `PlansGroupPreservesOrderTests`, with the method names as quoted. The commit deleted 318 files.
- F-03 holds. I implemented E-03's cases and ran them against live code: a bare `--rename` regroup of
  a child at Order 1 produced `20260908-oldset-01-bbb222-probe-child-one.ipd.md` retaining
  `- Order: 1`; a bare metadata-only regroup retained `- Order: 1`; a child with NO `- Order:` line
  whose filename carried `04` gained `- Order: 4`; and an orchestrator kept `- Order: 0` with the `00`
  slot. `4 passed in 2.23s`. `_preserved_order` and `plan_set_assign` are intact, and the docstring
  the plan quotes is accurate.
- F-04 holds precisely, which matters because E-05 asserts a presence/absence PAIR: a `Kind: child` at
  `- Order: 0` emits `IPD-M104: Order:` and at `- Order: 1` does not, while `IPD-H202` is present in
  BOTH cases. So the "absence of M104 plus presence of H202" assertion is sound and the exit code is
  1 in both cases, which is exactly why the plan is right to assert on the code and not on exit
  status.
- E-04's rename case reproduces end to end: a bare `--slug` rename of
  `20260810-demo-03-zzz111-old-slug.md` produced `20260810-demo-03-zzz111-new-slug.ipd.md` retaining
  both `- Order: 3` and `- Date: 20260810`.
- The `aw ipd lint` convention holds: passing `--dir` exits 2 with "unrecognized arguments".
- The GAP IS GENUINE, which I checked rather than assumed, because `tests/test_group_verb_policy.py`
  does contain six Order tests. Those are RESEARCH records (`test_group_research_*`), not plans, and
  no test file anywhere references `_preserved_order`. The five plans tests in that module assert
  only the filename DATE prefix. So plans Order is uncovered.

PR-001 IS THE FINDING THAT MATTERED AND IT IS A DEFECT IN THE PLAN'S OWN VALIDATION LOGIC. V-06
prescribes ONE negative control (force `_preserved_order` to return 0) and the gate says "If the
negative control in V-06 does NOT fail, STOP: the restored guard is inert and the plan must not be
marked executed." Measured: under that control, three of E-03's six cases fail and three PASS, so a
correct execution would have hit the stop directive.

The three that cannot fail, each for a distinct and verifiable reason. The two explicit-`--order`
cases (E-03(c), E-03(f)) passed under the forced regression because `plans_refs.plan_set_assign`
resolves an explicit `--order` without consulting `_preserved_order` at all, so breaking the helper
cannot affect them. The orchestrator case (E-03(e)) passed because its expected Order is 0 and the
forced return value is also 0, which makes the assertion a TAUTOLOGY under this control: it cannot
distinguish "the code preserved 0" from "the helper returned 0 for every input". That last one is the
more interesting defect, because E-03(e) is listed as one of the plan's "three must-not-break guards"
while being, under the plan's own control, unfalsifiable.

I fixed this by naming the falsifiable subset explicitly in E-06, V-06, Required tests and the gate's
stop condition, and by adding a SECOND control: forcing a nonzero sentinel (9) makes E-03(e)
meaningful. The stop condition now reads "STOP if control A does not fail E-03(a), (b) and (d), or if
control B does not fail E-03(e)", and says in terms that the other three passing is the correct
result. The production file was restored byte-identical after my probing (verified with an empty
`git diff --stat agent_workflows/plans_refs.py`).

PR-002: E-01's fixture is heavier than the behavior requires, and the plan could have measured that.
It prescribes a scoped `AW_HOME`, a `register_or_update_project` call, a `.aw/config/config.json`
naming `DeliveryMode.TRACKED`/`RecordsBackend.REPOSITORY`, and committing the seeded files. All four
Order behaviors reproduce against nothing but `git init -q` in `tmp_path` plus plan files written
directly under `.aw/records/plans/pending/`. That minimal shape is exactly the shipped
`test_group_verb_policy.temp_git_repo` fixture (two lines) plus its `_seed_plan_record` (no
registration, no commit), so the simpler form is both sufficient AND already conventional here. E-01
now starts from the shipped fixture, reuses the three existing helper shapes
(`_seed_plan_record`, `_run_group_plans`, `_run_rename_plans`, which already accept every parameter
these cases need), and requires a pasted failure before any extra machinery is added.

PR-003: both halves of OQ-01's stated basis are factually wrong, which matters because OQ-01 is the
plan's one open question and a later reader would inherit the error. It says that module's docstring
"scopes it to setid length policy enforcement alone"; the docstring actually reads "Outcome tests for
setid length policy enforcement and date preservation across aw group and rename" and explicitly says
it "Also covers date preservation for `aw group plans` and `aw rename plans` ... restoring date
regression coverage deleted in `19313eed` (IPD 949enf)". And it says a new module "keeps this plan's
`Scope-Paths` disjoint from pending plan `949enf`"; `949enf` is `- Status: executed` under
`.aw/records/plans/executed/`, so it claims nothing going forward. The DECISION (a new module) is
still right, so I replaced the basis rather than the outcome: that module is already a large
multi-subject file carrying six research Order tests plus the parametrized backend sweep, and the
deleted coverage was lost precisely by being buried in a grab-bag module. I recorded the honest cost
(two plausible homes for a reader) and had E-01 reuse the helper shapes to keep them consistent. The
same correction was swept into the Project-conventions bullet and the Deferred row that cited
"pending plan `949enf`".

PR-004: the gate was missing an open-questions statement and a scope fence, and its lifecycle
paragraph said to transition via `aw ipd set executed <plan>` without noting that a runner owns the
finalize when one is driving. Added all three, plus the explicit `Status`/`Readiness` statement. The
scope fence is worth having here specifically because V-06 requires TWO temporary edits to a
non-scope-path production file, which the fence now names along with the revert obligation.

WORTH KNOWING AT EXECUTION, recorded as F-08 rather than as a finding against the plan: a bare suite
run is not currently all-green. On a clean tree it reported `1 failed, 3648 passed, 2 skipped`, the
failure being `tests/test_runner_shared.py::DanglingCommitSearchTests::test_07_real_corpus_arm_conditional`,
which PASSES when re-run alone on the same clean tree. It is an order-dependent flake in a module this
plan does not touch, surfaced by the configured random ordering. E-06's original bar ("the full suite
passes") would have failed on a cause this plan does not own, so E-06, V-06 and Required tests now
demand a re-derived baseline with per-node attribution.

ONE THING I DELIBERATELY DID NOT CHANGE. E-02's prohibition on `subprocess.run([sys.executable, "-m",
"agent_workflows", ...])` is correct and well evidenced by F-05, and it matches the in-process pattern
the surviving module already uses. The plan's refusal to touch `plans_refs.py` is also correct: F-03
measured the fix intact, and the three `Carrier-Declined` rows each state a real reason rather than
hand-waving.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (testing) / G (executability) | the plan's E-06, V-06 and the gate's "If the negative control in V-06 does NOT fail, STOP"; `agent_workflows/plans_refs.py` `plan_set_assign` resolving an explicit order without `_preserved_order` | the single return-0 negative control cannot falsify three of E-03's six cases (both explicit-`--order` cases never reach the helper; the orchestrator case is a tautology since expected 0 equals forced 0), so a correct execution would trip the all-must-fail stop directive, and E-03(e) is listed as a must-not-break guard while being unfalsifiable | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named the falsifiable subset in E-06, V-06, Required tests and the gate; added a second return-9 control that makes E-03(e) meaningful; restated the stop condition so expected passes cannot misfire; added F-07 |
| PR-002 | MEDIUM | OVER-SCOPE | F (KISS) / C (reuse existing mechanisms) | `tests/test_group_verb_policy.py` `temp_git_repo` (two lines) and `_seed_plan_record` (no registration, no commit) | E-01 prescribes a scoped `AW_HOME`, `register_or_update_project`, a `config.json` and committed files, none of which the behavior needs: all four Order cases reproduce against `git init -q` plus direct file writes, and the module it cites as its pattern already ships the minimal fixture plus the three helpers this plan needs | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now starts from the shipped fixture, reuses `_seed_plan_record`/`_run_group_plans`/`_run_rename_plans`, and requires a pasted failure before adding machinery; V-01 demands the justification; added F-09 |
| PR-003 | MEDIUM | IN-SCOPE | Step 1 (evidence accuracy) | `tests/test_group_verb_policy.py` module docstring; `.aw/records/plans/executed/20260929-j84jg3-01-949enf-...ipd.md` carrying `- Status: executed` | OQ-01's basis is wrong in both halves: that module's docstring is not setid-length-only and already hosts restored `19313eed` date coverage for these two verbs, and `949enf` is executed rather than pending so the disjoint-Scope-Paths argument is void | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced OQ-01's basis with discoverability grounds that hold, kept the new-module decision, recorded the honest cost; swept the same correction into the Project-conventions bullet and the Deferred row; added F-10 |
| PR-004 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's "Approval and execution gate" section | missing open-questions statement and scope fence (notable here because V-06 requires two temporary edits to a non-scope-path production file), and the lifecycle paragraph instructed `aw ipd set executed` unconditionally, omitting runner finalize ownership | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the open-questions statement, a declaration-style scope fence naming the temporary-edit-and-revert obligation, the explicit `Status`/`Readiness` statement, and conditional runner/executor finalize ownership |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Three of E-03's six cases cannot fail under the prescribed control; drop those cases, or add a second control? | Add a second control and name the falsifiable subset per case | Drop E-03(c)/(e)/(f) as unfalsifiable; keep one control and loosen the stop directive to "some case fails" | The three cases guard real behavior a reader needs pinned (an explicit `--order` must still renumber; an orchestrator must stay at 0), so deleting them would remove coverage to satisfy a control. Loosening the stop directive to "some case fails" would let a genuinely inert orchestrator assertion pass unnoticed, which is the exact failure mode the control exists to catch. Measured that a return-9 control falsifies E-03(e) specifically | yes |
| D-2 | E-01's heavy fixture: trim it on measurement, or leave it as authored since a heavier fixture is harmless? | Trim it, and require a pasted failure before any machinery is re-added | Leave the fixture as authored; delete E-01's fixture guidance entirely and let the executor choose | A heavier fixture is not harmless here: `register_or_update_project` plus a scoped `AW_HOME` is exactly the machinery whose spelling the deleted module got wrong (its `agent_workflows.config`/`agent_workflows.projects` imports no longer resolve, per the plan's own Step 0), so prescribing unneeded setup invites a repeat of that breakage. Measured that the minimal form suffices for all four behaviors | yes |
| D-3 | OQ-01's basis is wrong but its decision is defensible; re-resolve the question, or correct the basis? | Correct the basis, keep the decision, record the cost | Re-open OQ-01 as unresolved and ask the maintainer where the tests belong; silently fix the citation | The decision survives on independent grounds I verified (that module is already multi-subject and large, and burial in a grab-bag module is how the coverage was lost), so re-opening would ask a human to re-decide something the evidence settles. Silently fixing the citation would leave the next reader with a basis that does not support the conclusion, which is the propagation failure the review rules warn about | yes |
