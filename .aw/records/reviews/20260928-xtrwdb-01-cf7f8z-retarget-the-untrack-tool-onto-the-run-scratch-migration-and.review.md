# Review findings: plan cf7f8z

- Subject-Id: cf7f8z
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `463e0f25` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified, byte-identical to its `.aw/state/lane-inputs/rev-8/` copy. No production
code was modified by this review; every probe ran in its own throwaway `git init` repo under
`.aw/state/`, all removed afterwards, and the one test-assembly probe was written to a temporary
`tests/` file that was deleted immediately. `git status --short` was empty before and after.

**THE PLAN'S DIAGNOSIS IS CORRECT, ITS DESIGN IS THE RIGHT ONE, AND BOTH HALVES WERE RE-MEASURED
RATHER THAN ACCEPTED.** F-01 reproduces verbatim: `--apply` prints `Removed 1 tracked path(s) from
the Git index; local files were retained.` and `Added and staged the workflow-artifacts/ ignore
rule.`, afterwards `git ls-files` returns `.gitignore` and `README.md`, the record is STILL at
`workflow-artifacts/assess/20260101-000000/report.md`, and the user's root `.gitignore` now contains
`workflow-artifacts/` under the quoted comment. F-02 reproduces character-for-character on BOTH
action lines, creates no root `.gitignore`, places the bytes at `.aw/workflow-artifacts/...`, removes
the emptied retired directory, and `git log --follow` on the new path reaches the pre-migration `init`
commit through the engine's two relocation commits. So the plan's central claim, that the tool is a
worse history-losing version of a migration the toolkit already performs correctly, is exactly true.
F-03 holds (`rg` over `tests/` returns nothing, the file is absent, the class recovers with 13 `def
test` methods and is the last class). F-04 holds (no caller in `agent_workflows/` beyond the one
comment; the wheel packages only `agent_workflows` and the sdist `include` list omits `tools/`). F-05
holds (the heading, the "Recommended" line, five bare occurrences). F-06 reproduces exactly: in a repo
with no `.aw/.gitignore` the migration leaves `?? .aw/` and `git check-ignore` exits 1. E-02's every
named deletion target exists; its exact call shape is valid against the shipped signature; E-03's
two-commit premise is verbatim in `_commit_relocation`'s docstring and observable in `git log`; the
dry run touches nothing; both shim precedents read as described; `tests.support.run_tool` exists with
the quoted docstring. The plan's honesty about F-06 as an inherited limit, and about the tool not
being shipped, is accurate and well placed.

**PR-B01 (HIGH): E-01's RESTORATION RECIPE IS INCOMPLETE AND PRODUCES 13 ERRORS AS WRITTEN.** This is
the finding that would have cost an execution turn. E-01 says to recover the file and "take ONLY
`RootRunScratchMigrationTests`", naming its exact boundaries, and then says the only fix needed is
that "the file's `REPO_ROOT`/`git`/`init_repo` helpers come from `tests.support`". Review assembled it
exactly that way and got 13 ERRORS, every one `NameError: name '_seed_committed_repo' is not
defined`. An AST free-variable pass over the recovered class reports it closes over `['INS', 'Path',
'_install', '_seed_committed_repo', 'git', 'tempfile', 'unittest']`, and the two underscore names are
MODULE-LEVEL HELPERS defined above the class in the deleted file and mentioned nowhere in this plan.
With both carried over the class reports `13 passed`. Review also determined the minimal sufficient
import set: six lines, since the deleted file's `cli as CLI`, `Term`, `mock`, `json`, `stat` and
`argparse` imports are all unused by this class, so a mechanical carry-everything would ship six
unused imports implying dependencies that do not exist.

**PR-B02 (MEDIUM): E-05 INVALIDATES A PREMISE PENDING PLAN `fzueyy` RELIES ON, AND BOTH PLANS ARE
UNAPPROVED.** `fzueyy` excludes `tools/README.md` from its restored run-scratch path guard, and its
E-04 requires that exclusion be a NAMED CONSTANT carrying a one-line reason, which reads that the
README "documents `tools/untrack-workflow-artifacts.py`, a migration tool whose subject IS the retired
path". E-05 of this plan removes exactly that property. The plan does note the interaction, which is
good and better than most, but frames it as settled ("that is why this plan, not that one, owns this
section"). The real consequence is an ORDERING DEPENDENCY between two `to-review` plans that neither
declares: if `fzueyy` lands first its guard ships an exclusion whose stated reason is now false; if
this plan lands first, `fzueyy`'s executor must not copy the stale reason forward. Neither executor may
assume the other's outcome, and resolving it is a scheduling decision for the human.

**PR-B03 (MEDIUM): THE FALSIFICATION V-04 DEMANDS NEEDS TWO ASSERTIONS AND A SAFE STAGING METHOD.**
E-04 lists four assertions and V-04 expects "the assertion that fired (expected: the root-`.gitignore`
assertion, and the new-path assertion)". Measured against today's tool, TWO fail (the root-`.gitignore`
one and the new-path one) while assertions (1) and (4) pass against BOTH tools, so they are regression
guards rather than discriminators and presenting them as the proof would overstate the evidence. There
is also a subtlety worth pinning: the old tool ALSO untracks the record, so a `git ls-files` assertion
must require the record tracked at NEITHER path, not merely absent from the retired one. Separately,
Required tests suggests staging the comparison with `git stash`, which in this shared checkout can
discard a co-worker's concurrent edit to the very file being changed.

**PR-B04 (MEDIUM): THE GATE HAD NO SCOPE FENCE AND NO APPROVAL SUMMARY.** It carried a good execution
contract and a strong post-gate section, but no declaration for the runner to reconcile against and no
single paragraph stating what a human is approving. This plan has five distinct prohibitions spread
across its Scope statement and seven Deferred rows (do not touch the engine function, do not restore
other classes, do not touch `ARCHITECTURE.md`/`CONTRIBUTING.md`, do not touch `fzueyy`'s guard file, do
not soften the `filter-repo` warning), none collected where an executor looks.

**PR-B05 (LOW): TWO EXECUTION-TIME UNKNOWNS WERE CHEAP TO PRE-MEASURE AND WERE NOT.** E-01 requires an
outcome-rule audit of each restored test with a record of any dropped; review ran it
(`rg -n "inspect\.|import ast|getsource|__doc__"` over the recovered class returns nothing), so the
expected result is 13 kept and 0 dropped, and an executor now has a bar to match rather than a judgement
to improvise. E-04's assertion (1) requires proving the index and working tree are byte-identical after
a dry run; review measured that `dry_run=True` leaves HEAD unchanged, `git status --porcelain` empty,
and the record in place, so the assertion is achievable rather than aspirational.

**WHAT REVIEW CHECKED AND FOUND SOUND.** OQ-01's resolution is correct and its evidence verbatim:
`_commit_relocation` genuinely makes two path-scoped commits and its docstring explains why the split
is load-bearing, so a post-hoc `--commit` would find nothing staged; the refusal of the third option
(commit whatever is staged) on shared-checkout grounds is right. OQ-02's retarget-not-retire choice
rests on a real measured property (dry-run-by-default has no `aw install` equivalent) and volunteers
the maintainer's cheap override, including that E-01 stands either way. All seven Deferred rows are
sound, and the four `Carrier-Declined` reasons are honest rather than formulaic, especially the one
declining to file a blanket carrier for four unexamined test classes. The E-01-before-E-02 ordering is
correct: the function gains coverage before it gains a second caller. Right-sizing is appropriate: five
E-items, one deliverable each. The plan transcribes NO suite total, which is the correct handling of a
live population and is notably better than its sibling plans in this sweep.

Every finding is FIXED by in-place revision. None was deferred, so no escalation to a
`- Blocking: yes` question is owed and none was written. OQ-01 and OQ-02 both survive review unchanged
and are UPHELD on re-measured evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | HIGH | IN-SCOPE | E. Testing / G. Plan executability | an AST free-variable pass over the recovered class printing `['INS', 'Path', '_install', '_seed_committed_repo', 'git', 'tempfile', 'unittest']`; a first assembly of class-plus-imports giving `13 failed`, all `NameError: name '_seed_committed_repo' is not defined`; a second adding both helpers giving `13 passed in 30.19s`; a third with only six imports giving `13 passed in 61.79s`; both helper bodies read from `git show 19313eed^:tests/test_engine_install.py` | E-01's "take ONLY the class" RECIPE PRODUCES 13 ERRORS. The class closes over two module-level helpers (`_install`, `_seed_committed_repo`) defined above it in the deleted file and named nowhere in this plan, and E-01's only stated fix concerns `tests.support` helpers. An executor following it literally gets 13 `NameError`s on the plan's first E-item. | C:Low; U:Low; S:Low; F:Low; Overall:Low (name the two helpers and the working import set; review already assembled and ran it) | FIXED | Added F-07 with the AST analysis, all three assembly measurements, and both helper bodies. E-01 gained a paragraph naming both helpers with their docstring rationale, the EXACT minimal import set, and an instruction not to carry the six imports this class does not use; it also now records that review proved the restoration passes and that the outcome audit's expected result is 13 kept / 0 dropped. V-01 requires both helpers quoted and FAILS a restoration missing either. A Step-0 conventions bullet generalizes the lesson (always run a free-variable pass over a recovered class). |
| PR-B02 | MEDIUM | IN-SCOPE | C. Architecture and operability (cross-plan) | `fzueyy`'s `- Status: to-review`, its `- Scope-Paths:` omitting `tools/README.md`, its OUT clause ("whose SUBJECT is the retired path") and its E-04 exclusion-constant requirement, all read verbatim; this plan's E-05 reviewer note | E-05 INVALIDATES A PREMISE `fzueyy` RECORDS IN A NAMED TEST-EXCLUSION CONSTANT, AND BOTH PLANS ARE UNAPPROVED. The plan notes the interaction but frames it as settled ownership; the actual consequence is an undeclared ordering dependency where whichever lands second must reconcile, and `fzueyy`'s guard would otherwise ship an exclusion whose stated reason is false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-08 with both plans' texts and statuses. E-05's reviewer note replaced by a CROSS-PLAN ORDERING OBLIGATION paragraph stating both landing orders and what each requires, forbidding this plan's executor from editing `fzueyy`'s guard file (not in `- Scope-Paths:`, does not exist yet), and requiring the reconciliation be REPORTED to the human as a scheduling decision. E-05's expected outcome now includes that report. The scope fence names the guard file as out of bounds. |
| PR-B03 | MEDIUM | IN-SCOPE | E. Testing and verification | measured against today's tool: the record remains at the retired path AND a root `.gitignore` is created, so two assertions fail; the dry-run and exit-code assertions pass against both tools; the old tool also untracks the record, so "absent from the retired path in `git ls-files`" passes against both; the Required-tests `git stash` suggestion versus the shared-checkout rule | THE FALSIFICATION NEEDS TWO ASSERTIONS AND A SAFE STAGING METHOD. V-04 expected one discriminating assertion; two fire. Two of E-04's four assertions pass against both tools and are regression guards, not proofs, and presenting them as the falsification would overstate the evidence. The `git ls-files` assertion needs strengthening to "tracked at NEITHER path". And staging by `git stash` risks discarding a co-worker's edit to the file under change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gained a paragraph naming which assertions discriminate and which are guards, the "tracked at NEITHER path" strengthening, and review's measurement that the dry-run assertion is achievable. Required tests now demands both assertions fire and forbids `git stash`, naming a separate worktree or a scratch copy of the pre-change tool instead, with `git status --short` pasted. V-04 requires the discriminator/guard distinction stated and the staging method declared. |
| PR-B04 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | the gate as authored, carrying an execution contract and post-gate lifecycle but no fence and no approval summary; five prohibitions spread across the Scope statement and seven Deferred rows | THE GATE HAD NO SCOPE FENCE AND NO APPROVAL SUMMARY. The runner needs a declaration to reconcile the diff against, and a human approving had no single statement of what changes and what the user-visible effect is. The five prohibitions this plan carries are each well reasoned but none sits where an executor looks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a WHAT A HUMAN WOULD BE APPROVING paragraph (the change, the measured before/after, the not-shipped context, the one judgement to overrule, and the unresolved `fzueyy` ordering) and a SCOPE FENCE naming the three paths and all five negative constraints, written as a DECLARATION with no "STOP and report" clause per the 2026-09-01 maintainer ruling. The first gate paragraph updated to the reviewed state with its readiness and approval command. |
| PR-B05 | LOW | IN-SCOPE | E. Testing (evidence pre-measurement) | an outcome-rule grep over the recovered class (searching for `inspect.`, `import ast`, `getsource`, `__doc__`) returning nothing; a dry-run probe showing HEAD unchanged, `git status --porcelain` empty, and the record still at the retired path | TWO EXECUTION-TIME UNKNOWNS WERE CHEAP TO PRE-MEASURE AND WERE NOT. E-01 requires an outcome-rule audit with a record of any dropped test but gives no expected result, leaving an executor to improvise a judgement review could settle in one command. E-04's dry-run assertion asserted a property nobody had confirmed the engine actually has. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now records the expected audit result (13 kept, 0 dropped) with the command that establishes it, while still requiring the executor to name anything they drop. E-04 records that the dry-run case was measured performable. V-01 carries the expected audit result as a bar. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The recovered class needs two module-level helpers. Should the plan name them, or should E-01 simply say "carry whatever the class needs"? | NAME BOTH EXPLICITLY, with their bodies' purpose, plus the exact minimal import set, and add a general convention bullet about running a free-variable pass. | (a) A vague "carry any helpers the class needs" - rejected: that is what E-01 effectively said (it named only the `tests.support` helpers) and it is precisely what produced 13 `NameError`s; a restoration recipe that does not enumerate its dependencies has not been tested. (b) Tell the executor to carry the deleted file's imports wholesale - rejected: measured, six of them are unused by this class, so that ships lint noise and implies dependencies that do not exist. (c) Restore the whole deleted file - rejected: the plan's Scope explicitly excludes the other five classes and the Deferred section declines to carry them with a reasoned argument. | The AST free-variable analysis; three measured assemblies (class-only failing, class-plus-helpers passing, minimal-imports passing); the two helper bodies and docstrings read from the pre-trim file; the plan's own Scope boundary. | yes |
| D-2 | E-05 invalidates a premise `fzueyy` records. Should review edit `fzueyy`, edit this plan, or raise it to the human? | EDIT THIS PLAN to state the ordering obligation in both directions and require the executor REPORT it; do not touch `fzueyy`. | (a) Edit `fzueyy`'s exclusion reason now - rejected: it is a separate plan under review in this same sweep, editing another plan's deliverable from this review would be out of scope, and `fzueyy` is not this review's target. (b) Raise it as a `- Blocking: yes` question here - rejected: nothing in THIS plan's execution is blocked (E-05 is correct either way), so a blocking question would stall an executable plan for a scheduling matter. (c) Leave the plan's "this plan owns this section" framing - rejected: it reads as settled when the dependency is live, and a future executor would not know a reconciliation is owed. | Both plans' `- Status: to-review`; `fzueyy`'s E-04 exclusion-constant requirement and its verbatim reason; this plan's `- Scope-Paths:` not containing the guard file, which makes editing it out of bounds for its executor too. | yes |
| D-3 | Should review require a fifth E-04 assertion, given that two of the four do not discriminate? | NO. Keep four and label which discriminate, rather than adding one. | (a) Add an assertion to make all discriminate - rejected: the dry-run and exit-code assertions are legitimate REGRESSION guards (the tool's one genuine safety property is dry-run-by-default, per OQ-02, so pinning it is right) and their value does not depend on failing against the old tool. (b) Drop the two non-discriminating assertions - rejected outright: that would delete the coverage of the exact property the plan retains the tool FOR. | The measured behavior of today's tool on all four assertions; OQ-02's reasoning that dry-run-by-default is the tool's justification for existing. | yes |
| D-4 | PR-B01 is HIGH. Does it make this plan NO-GO, or is escalation owed? | NEITHER. It was FIXED by in-place revision, so no unfixed HIGH remains and the readiness is `go-pending-approval`. | (a) NO-GO on the HIGH - rejected: severity is for reporting and the Fix Bar alone decides fixing; this fix is Low Remediation Risk on all four axes (name two helpers and an import set, both already measured working) and touches no code. (b) Escalate as `- Blocking: yes` - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the gate threshold, and this one is FIXED. (c) REPLAN - rejected: the plan's design is right, the defect is measured end-to-end, and the delegation target is verified strictly better on every axis. | The `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision; `review_findings_gate` absent from `.aw/config/project.json` so the default `HIGH` threshold applies and nothing sits unfixed at it. | yes |
| D-5 | The plan transcribes no suite total, unlike its siblings in this sweep. Should review add the measured figure as a bar? | NO. Record it explicitly as CONTEXT ONLY and keep the plan's own "record your own baseline first" instruction as the bar. | (a) Add `3217 passed` as the bar - rejected: three sibling plans in this same sweep each carried a transcribed total that had already drifted (by 60, 138 and 93 tests), and this plan's authoring choice avoided that failure mode; adding the number would import the defect. (b) Say nothing - rejected: a same-week reading is genuinely useful as a sanity check, and recording that the omission was DELIBERATE stops a later reader from "helpfully" adding a bar. | Review's measured `3217 passed, 2 skipped, 3 warnings in 53.42s` at HEAD `463e0f25`; the plan's existing Required-tests wording; the three measured drifts in sibling plans reviewed in this sweep. | yes |
