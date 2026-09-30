# Review findings: plan oq4ual

- Subject-Id: oq4ual
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1001 (HIGH, fixed), PR-1002 (HIGH, fixed), PR-1003 (MEDIUM, fixed), PR-1004 (MEDIUM, fixed), PR-1005 (LOW, fixed)

## Round 1

Reviewed at HEAD `60e21419` in an isolated review lane. The plan file was already committed and identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming`, exit 0, with a single advisory `IPD-Z602` (size density) before semantic
review, and `--phase review-finalize --agent` still reports `conforming` with the same single advisory after
revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

ALL SEVEN AUTHORED FINDINGS HOLD AND THE DIAGNOSIS IS EXACTLY RIGHT, so I record that first because it is the
substance of the plan. Both guards exist verbatim as quoted (`attention.run` and `cli._run_plans`), and a
repository-wide search confirms they are the ONLY two sites carrying the `not explicit_dir` conjunct, so F-02's
claim that these two verbs are the whole population is literally true. On targets created outside the
repository, all three surfaces greenwash exactly as F-01 states: bare prints `0 artifacts shown` at rc=0,
`--agent` emits `outcome:clean, exit:0, verified:true, complete:true, findings:0`, and `--check` prints
`aw attention --check: the view is valid.` at rc=0, identically for a git-but-not-AW and a non-git directory.
The cwd reference path refuses honestly on exactly two of three (rc=3 with `aw attention: no AW project found
here.` on stderr and empty stdout; rc=2 with a `cannot-run` record) and greenwashes only on `--check`, which
is precisely the asymmetry E-01's Expected outcome predicts. F-02 reproduces (`✓ CLEAN  no plans found` at
rc=0, `outcome:clean` on `--agent`). F-05 reproduces and its consequence verifies: `is_project_dir` is False
for `docs`, so after the fix `--dir docs` returns rc=3 where the repo root reports 503 artifacts. F-07 is
exact: three citations of `test_awretrofit_project_root_climb`, no such file, and zero test references to
`find_project_root`, `is_project_dir`, `no_project_message` or `resolve_verb_repo_root` by name, with
`NoProjectAgentEnvelopeTests` (cwd path only) the sole live pin and `NoProjectSubprocessMatrixTests`
referenced nowhere. Every API the plan cites exists with the signature it assumes
(`agent_schema.validate_agent_record` returning a list, `unresolved_selector_agent_record` whose docstring
carries the quoted reasoning word for word).

I VERIFIED F-03 AND F-04 BY BUILDING THE FIX RATHER THAN READING IT, which is where the review's value is. I
simulated the conjunct deletion in-process (blanking the `dir` attribute the guard consults while still
resolving the caller's target, which is exactly the conjunct-deleted state) rather than editing tracked
source. F-03 is confirmed precisely: in that state bare returns rc=3 and `--agent` returns rc=2 correctly,
while `--check` still returns rc=0 printing `the view is valid` and `--check --agent` still returns rc=0
emitting `outcome:clean, exit:0, verified:true, complete:true`. So the two-of-four honest and two-of-four
greenwashed split after E-02 alone is measured, and the machine half is the worse one. F-04's zero blast
radius also re-confirms independently: the bare suite is `3387 passed, 2 skipped` and the same suite with the
deletion simulated is ALSO `3387 passed, 2 skipped`, a zero delta.

PR-1001 IS THE FINDING THAT MAKES THIS PLAN SHIP A REPOSITORY ERROR, AND IT IS INVISIBLE FROM THE PLAN TEXT.
The five `NEEDS-BACKLOG-ITEM` carrier placeholders are not a cosmetic to-do: `aw check plans` reports them
TODAY as `check.ipd-uncarried-obligation` with severity **error**, detail "3 obligation(s) name no durable
carrier: deferred row 1: malformed `Carrier` reference(s) 'NEEDS-BACKLOG-ITEM ...'", and this plan is one of
nine plans currently contributing to that rule's 49 errors. E-07 deferred filing the items to its own last
item AFTER the verification sweep, so an executor following the order would run a verification pass against a
repository error this very plan introduced, and would have no way to distinguish it from a pre-existing one.
The ordering is the defect, not the placeholders' existence, and it is cheap to fix by filing first.

PR-1002 WOULD HAVE PRODUCED A TEST THAT PASSES FOR THE WRONG REASON. E-05(5) instructs "the same four for
`aw ipd board` where the surface exists", which invites testing `--check` and `--format json` on that verb.
Measured: `aw ipd board --help` offers `--agent --color --dir -h --interactive --json --no-color
--no-interactive --status`, so it has NEITHER `--check` NOR `--format`. The trap is specific and nasty:
`ipd board --dir <d> --format json` exits **2** as an argparse USAGE error, the same exit code the refusal
this plan is building uses, so a test asserting only the exit code would go green against a build where the
fix does nothing at all. The hedge "where the surface exists" is too weak to stop it, because an executor
reading it still has to discover which surfaces exist and may assume `--format json` is universal (it is on
`attention`).

PR-1003 is a one-character error with a disproportionate consequence. E-06's body directs the executor at
`test_awstretrofit_project_root_climb` (an inserted `s`), which matches NOTHING in the tree, while the actual
string is `test_awretrofit_project_root_climb` and returns the three sites. An executor greping the item's own
spelling finds zero hits and could reasonably conclude F-07 had already been fixed by someone else and skip
the item. The plan's Scope, F-07 and V-06 all use the correct spelling, so this is isolated to the one
instruction that matters most.

PR-1004 is the live-count convention. F-04's `3251 passed, 2 skipped` is an authoring measurement; the bare
suite is `3387 passed, 2 skipped` at review HEAD, and V-07 told the executor a "comparable count plus the new
tests is expected". The census figures drifted the same way (163 `dir=str(` sites now, not 151, with 276
`"--dir"` CLI sites beside them). The plan's CONCLUSION survives every re-measurement, which is why this is a
convention fix rather than a substantive one.

PR-1005 is two small gaps. First, the F-06 reproduction trap is wider than the plan says: it warns about
`.aw/state/`, but my first attempt used a plain gitignored `tmp/<probe>/` inside the lane worktree with no AW
markers of its own, and all three surfaces returned the OUTER repository's answer (rc=1, `VIEW INVALID`, five
stranded-lane lines) instead of the greenwash. Any in-repository path does this, which makes the trap much
easier to hit than a reader would expect, and the wrong measurement looks like an entirely different bug.
Second, E-04 changes the CWD `--check` path too and E-05 pinned only `--dir` cases, leaving the behavior
change E-04's own gate paragraph calls out to an approver covered by no test. That CWD case is also the
single most persuasive evidence for E-04: measured today, a CWD non-project `--check --agent` emits
`outcome:clean, exit:0, verified:true, complete:true, findings:0` about a directory it never surveyed.

THINGS I CHECKED THAT PRODUCED NO FINDING. E-04's CI warning is correctly scoped: the only `attention --check`
in CI runs at the repository root, which `is_project_dir` accepts, so that job is unaffected and the plan's
warning is about hypothetical external jobs, which is honest rather than alarmist. The one shipped test
asserting `the view is valid` uses `_mk_repo`, a fixture measured to satisfy `is_project_dir`, so E-04 does
not break it; I recorded that builder in E-05 as the known-good positive control. The human/machine 3-versus-2
split the plan preserves is genuinely forced by `aw.agent/v1` admitting only 0/1/2. `xnb551` is `graduated`
with `Blocks-Release: next` and `Work-Kind: bug`, and the plan correctly inherits the gate; `aw check
release-gates` CONFORMS. The gate's ordering paragraph about closing `xnb551` only after finalize is correct
and well reasoned. OQ-01 is resolved from real repository evidence (Section 3, Section 4, and the in-module
precedent all say what it claims) and I left it resolved.

Bare suite at review HEAD: `3387 passed, 2 skipped, 3 warnings in 55.19s`. This review changed only the plan
and this review record; no production file was modified at any point, every probe was an in-process patch, and
the probe targets were created under a system temporary directory outside the repository.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1001 | HIGH | IN-SCOPE | Rubric C (operability), G (executability) | `aw check plans --json`: rule `check.ipd-uncarried-obligation`, severity `error`, on this plan, detail "3 obligation(s) name no durable carrier: deferred row 1: malformed `Carrier` reference(s) 'NEEDS-BACKLOG-ITEM ...'"; 9 distinct plans and 49 errors in that rule's family; 5 placeholder occurrences in this plan | THE PLAN SHIPS A STATE `aw check` ALREADY CALLS AN ERROR, AND DEFERS FIXING IT TO ITS OWN LAST STEP. E-07 files the three carrier items AFTER the verification sweep, so an executor runs verification against a repository error this plan introduced and cannot distinguish it from a pre-existing one. The ordering is the defect; the placeholders are legitimate at authoring time. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 rewritten to FILE FIRST then verify, naming the rule, its error severity and the measured detail string, specifying the work-kind per item and requiring `aw backlog new --apply` rather than hand-naming. Its Expected outcome and V-07 now require `grep -c NEEDS-BACKLOG-ITEM` to return 0 and `aw check plans` to show no uncarried-obligation finding for this plan. |
| PR-1002 | HIGH | IN-SCOPE | Rubric E (testing) | `aw ipd board --help` lists `--agent --color --dir -h --interactive --json --no-color --no-interactive --status`: no `--check`, no `--format`. `ipd board --dir <d> --format json` exits 2 as an argparse usage error; `--json` exits 0 | E-05 DIRECTS A TEST AT TWO SURFACES `aw ipd board` DOES NOT HAVE, and the failure mode is silent: `--format json` exits 2 as a USAGE error, the same code the refusal uses, so a test asserting only the exit code goes green against a build where the fix does nothing. The hedge "where the surface exists" does not prevent it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05(5) now names ONLY the two surfaces that verb has (human, `--agent`), records the measured flag list, states the argparse-2 trap explicitly, directs `--json` instead of `--format json`, and forbids a `--check` case. V-03 carries the same warning plus the measured before-state string. |
| PR-1003 | MEDIUM | IN-SCOPE | Rubric G (executability) | `grep -rn test_awretrofit_project_root_climb agent_workflows/` returns the three sites; the `awstretrofit` spelling returns ZERO | E-06'S BODY MISSPELLS THE SEARCH STRING it tells the executor to use (`test_awstretrofit_`, an inserted `s`), which matches nothing. An executor using the item's own spelling finds zero sites and could conclude the finding was already fixed and skip the item. Scope, F-07 and V-06 all spell it correctly, so the error sits in exactly the one place that directs the work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now states the correct string explicitly, flags the prior misspelling with its zero-hit measurement so a reader is not confused by the plan's history, and names the three sites by symbol. |
| PR-1004 | MEDIUM | IN-SCOPE | Rubric G (live-artifact success criteria) | F-04's `3251 passed, 2 skipped`; re-measured bare at HEAD `60e21419`: `3387 passed, 2 skipped`. Census drift: 163 `dir=str(` sites (not 151), 276 `"--dir"` sites | A LIVE COUNT IS USED AS A COMPARISON BAR. V-07 tells the executor a count "comparable" to `3251` plus new tests is expected; the real baseline has drifted +136, so the instruction cannot be followed literally. The plan's conclusion is unaffected, which is what makes this a convention fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-07 now requires RE-DERIVING the baseline at the executing HEAD and comparing against that, stating both measured numbers so the drift is visible. F-04 carries the review re-measurement, the independent zero-delta confirmation of its central claim, and the corrected census figures, all labelled dated context. |
| PR-1005 | LOW | IN-SCOPE | Rubric E (testing), D (anti-regression) | First review attempt used `tmp/<probe>/` inside the lane: all three surfaces returned rc=1 with `VIEW INVALID` and five stranded-lane lines. CWD non-project `--check --agent` today: `outcome:clean, exit:0, verified:true, complete:true, findings:0` | TWO GAPS. The F-06 reproduction trap is wider than the plan's `.aw/state/` warning: ANY in-repository path leaks the outer repository's answer, including a plain gitignored directory, so the wrong measurement is easy to take and looks like a different defect. Separately, E-04 changes the CWD `--check` path and E-05 pinned only `--dir` cases, leaving that deliberate behavior change covered by no test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and F-06 now record that any in-repository path leaks, with the measured symptoms, and require a system temporary directory. E-05 gains case (8) pinning the CWD `--check` case on both surfaces with the measured greenwashed record quoted, and case (7) now names `_mk_repo` as the known-good positive-control builder. F-03 carries the review's in-process re-verification. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-1001: should the review FILE the three backlog items itself, so the plan stops contributing an `aw check` error immediately? | NO; reorder E-07 to file them first, and leave the filing to execution. | File them now during review: rejected, and this is the constraint I checked before deciding. `/plan-review` is explicitly limited to planning documents ("Do not change code, tests, runtime configuration, or production data"; commit only reviewed plan files and the review record), and a backlog item is a tracked record outside that scope. Filing three items would also mint ids this plan's text must then match, entangling the review with execution. Leave the ordering alone: rejected, that is the defect. | The plan-review workflow's scope restriction and its two-commit rule; `aw check plans` reporting the rule at severity `error` today | yes |
| D-2 | PR-1002: should E-05 test `aw ipd board`'s `--json`, or drop its second machine surface entirely? | TEST `--json`, and forbid `--check`/`--format json`. | Drop the second machine surface: rejected, `--agent` alone would leave the verb's other machine consumer unpinned for the same defect, and `--json` exists and works (exit 0 today, so it greenwashes exactly like the rest). Keep `--format json` and accept its exit 2: rejected outright, that is the false-green trap. | Measured `--help` flag list; `--format json` exiting 2 as argparse usage versus `--json` exiting 0; the plan's own principle that these two verbs are one behavior | yes |
| D-3 | PR-1005: should the CWD `--check` case be a new E-item, or an added case in E-05? | AN ADDED CASE IN E-05. | A separate E-item: rejected, it is the same test file, the same fixture shape and the same assertion style as the seven cases already there, so splitting it would add an item without adding a focused pass. It is also E-04's own behavior change, so it belongs with the test that fences E-04. | The plan's right-sizing rule (one concern, one focused pass); E-05 already spanning both verbs and four surfaces; E-04 declaring the CWD change in its own body | yes |
| D-4 | Is E-04 (the `--check` refusal) correctly bundled here, or should it be split out given it changes CWD behavior beyond `--dir`? | CORRECTLY BUNDLED. | Split E-04 into its own plan: rejected. F-03 measured that E-02 alone leaves two of four surfaces greenwashed, so a plan stopping at E-02/E-03 would ship a half fix that a CI consumer still reads as clean, which is the defect this plan exists to remove. The plan already offers the approver the separation explicitly in its gate ("E-04 is separable from E-02 and E-03"), which is the honest way to present it rather than pre-splitting. | Measured post-E-02 state (rc=0 with `the view is valid` and `verified:true`); `docs/cli-output-contract.md` Sections 3 and 4; the plan's gate paragraph offering the split | yes |
| D-5 | OQ-01 resolves the `--check` question to exit 2 on the author's own authority. Re-open it for the maintainer, since it changes shipped CWD behavior? | LEAVE IT RESOLVED. | Re-open as blocking: rejected. The question is answered twice by repository evidence the review confirmed independently: Section 4's anti-greenwashing invariant forbids `clean` for `cannot-run` work, Section 3 classifies a condition preventing domain inspection as exit 2, and `unresolved_selector_agent_record` already refuses the sibling case with the identical shape and reasoning. The plan also surfaces the CWD consequence prominently to the approver rather than burying it, which is what the resolution owes a reader. | `docs/cli-output-contract.md` Sections 3 and 4; `unresolved_selector_agent_record`'s shipped shape and docstring; the measured CWD `--check --agent` record claiming `verified:true` for unexamined ground | yes |
