# Review findings: plan cvs2b7

- Subject-Id: cvs2b7
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (MEDIUM, fixed), PR-804 (MEDIUM, fixed), PR-805 (LOW, fixed), PR-806 (LOW, fixed)

## Round 1

Reviewed at HEAD `f4543b7b` in an isolated review lane. The plan file was tracked, unmodified, and
byte-identical to the lane input (`diff` reported no difference), so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `outcome: clean`, exit 0, ZERO findings
and no `IPD-Z602` density advisory BEFORE semantic review; `--phase review-finalize` reports `conforming`
after every revision including the two answered open questions.

I RE-RAN THIS PLAN'S WORK RATHER THAN READING IT, INCLUDING THE TWO EXPENSIVE MEASUREMENTS, AND ALL NINE
FACTS REPRODUCED. F-1 is verbatim: `run_suite_check`'s docstring still reads "`tests/test_run_viewer.py`
gives `36 passed` in the primary checkout and `15 failed, 20 passed` in a lane" and "permanently red".
F-2 reproduced in the condition that matters: this lane IS a linked worktree (`git rev-parse --git-dir`
gives `.git/worktrees/review-sweep-...` against a `--git-common-dir` of `.git`) and
`tests/test_run_viewer.py` gives `38 passed`, with the full bare suite at `3344 passed, 2 skipped`, fully
green. So the docstring's stated reason is false in the exact venue it calls permanently red, which is the
plan's central claim and it is correct. F-4 I re-confirmed by actually PERFORMING the mutation rather than
trusting it: with the integration-gate call site passing the lane, the bare suite gives `3344 passed, 2
skipped` and nothing fails, so the contract genuinely has no regression test. I restored the file from a
byte copy and verified `git status --short` empty. F-7 reproduced exactly, including the asymmetry the plan
predicts: from this lane `checkout_control_root(".")` returns the MAIN checkout's `.aw` while
`state_root(".")` returns the LANE's records tree, and `checkout_control_root`'s docstring still says of
the `--git-common-dir` collapse "That collapse IS the fix". F-3's three commits all resolve, F-6 is exact
(one `def run_suite_check`, in `runner_shared`, against two comments saying `oc_runipd`), F-8's autouse
guard is present.

SO THE DIAGNOSIS IS RIGHT AND THE PLAN'S RESHAPING OF THE BACKLOG ITEM IS RIGHT. The item asked for a
docstring correction; the plan measured that the contract has no test and made the test the central
deliverable, refusing the item's "replace with a current measurement" on the ground that a fresh number
re-creates the item. Both judgements are correct and I verified the evidence for each.

WHAT REVIEW FOUND IS THE ONE THING THAT WOULD HAVE MADE THIS PLAN'S CENTRAL DELIVERABLE SHIP AS
DECORATION (PR-801). E-03 says "spy on `run_suite_check`" without naming a patch target, and the obvious
reading is wrong. `runner_shared` rebinds the function from the host at call time:
`run_suite_check = getattr(driver_module, "run_suite_check", run_suite_check)`. I built the pin and
patched `runner_shared.run_suite_check`, exactly as the instruction invites, and measured
`SUITE_CHECK_CWDS: []` with `n calls: 0`. That is worse than a failing test: an assertion written as "the
first recorded cwd must be the repo root" over an empty list either errors confusingly or, if written
defensively, PASSES while observing nothing. Patching `oc_runipd.run_suite_check` reaches it. I then
prototyped the whole pin properly and confirmed F-5 character for character: clean run
`['<repo>', '<repo>/.aw/records/runs/run-test/revalidation/revalidate-7989f1021a59']`, mutated run
`['<repo>/.aw/worktrees/wir001', '<repo>/.aw/records/runs/.../revalidate-7989f1021a59']`, with the second
entry byte-identical across both. So the "first call only" constraint is correct and necessary, and the
mutation triple V-03 demands is achievable. Two further prototype facts an executor needs and the plan
does not give: the spy's return stub must carry a `reason` attribute (I hit `AttributeError: 'R' object
has no attribute 'reason'` from the gate-answer read), and `options["no_audit"] = True` drives a SECOND
execute turn whose `git commit` fails because the first already committed, so the fixture's fake agent
must tolerate a repeat turn or the test errors before asserting anything. The scratch test was deleted and
`runner_shared.py` restored; the tree is clean.

THE SECOND SUBSTANTIVE CORRECTION IS A MISCOUNTED SURFACE (PR-802). The plan says "the sole call site"
(E-01) and "the sole integration-gate call site" (Scope check). There are TWO invocations passing `repo`,
both in `runner_shared.py`: the integration-gate assignment, and the gate-answer construction's
`rerun_suite=lambda: run_suite_check(repo, ...)`. The second is the very lambda whose COMMENT E-05(a)
rewrites, so the plan already edits prose beside a call site it does not count. E-03's fixture reaches
only the first, so the `rerun_suite` path stays unpinned after this plan. That is an acceptable limit for
a chore, but it had to be stated rather than hidden behind "sole", because the plan's whole value
proposition is "the contract is now defended".

BOTH OPEN QUESTIONS WERE MINE TO ANSWER AND I ANSWERED BOTH, since each named `- Owner: reviewer`.
OQ-01 (keep the `dh0uno` citation): KEEP, marked historical and retracted. The decisive evidence is this
review itself, which had to read `dh0uno`'s status and `checkout_control_root`'s docstring to establish
that the reason was retracted rather than unlucky - the second time that archaeology has been done. A note
naming the retracted reason converts a re-measurement from a contradiction into a confirmation. OQ-02
(test placement): KEEP it in `tests/test_oc_runipd.py`, and the deciding factor is measured rather than
argued: because the function is resolved off the host module, ANY working spy is host-bound by
construction, so a "host-neutral" file would still have to pick a host. Given that, sitting beside the
fixture that already builds the isolated execute turn is strictly cheaper. The real cost (an agy-side
regression is not caught) is now required in the test's own docstring.

WHAT I DELIBERATELY DID NOT FLAG. The plan's six-fact preamble is the right shape for a plan whose subject
is a falsified measurement, and its refusal to install a fresh count is correct and well evidenced. Its
Deferred section is unusually disciplined: five entries, each with either a real carrier or a
`Carrier-Declined` that argues why nothing is owed, and I agree with all five, including the correct
refusal to touch the `state_root` asymmetry (separately owned by executed plan `swps4w`) and the correct
refusal to fix the eight dangling `NoRunnerImportTests` citations (carried by `gia5i7`, which exists and
is `open`). Its Spec/documentation sync section correctly records that historical records quoting the
stale figure must NOT be rewritten. I left the five-item structure alone; the linter raised no density
advisory and each item has one deliverable.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | E (testing); G (executability) | plan E-03 ("spy on `run_suite_check`", no patch target named); `runner_shared` line `run_suite_check = getattr(driver_module, "run_suite_check", run_suite_check)`; review prototype patching `runner_shared` -> `SUITE_CHECK_CWDS: []`, `n calls: 0`; patching `oc_runipd` -> 2 calls | **THE PIN'S SPY MUST PATCH THE DRIVER MODULE AND THE PLAN DOES NOT SAY SO, SO THE OBVIOUS READING PRODUCES A SILENTLY VACUOUS TEST.** The effective function is rebound from the host at call time, so patching where it is defined observes nothing. An assertion over an empty call list either errors confusingly or passes while testing nothing, which is exactly the vacuous pin this plan exists to replace | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-11 with all four prototype measurements; E-03 now names `oc_runipd.run_suite_check` as the target, records that patching both is acceptable and patching only `runner_shared` is what fails, requires the stub to carry `reason`, and warns that `no_audit=True` drives a second execute turn the fixture's fake must tolerate. Required tests gains a NON-EMPTY call-list assertion as a separate vacuity check, since the mutation triple alone does not catch this |
| PR-802 | HIGH | IN-SCOPE | D (evidence accuracy); C (scope of the guarantee) | plan E-01 ("the sole call site"), Scope check ("the sole integration-gate call site"); `grep -n "run_suite_check(" agent_workflows/*.py` returning the gate assignment AND `rerun_suite=lambda: run_suite_check(repo, ...)` | **THERE ARE TWO CALL SITES PASSING `repo`, NOT ONE, AND E-03 PINS ONLY THE FIRST.** The uncounted one is the lambda whose comment E-05(a) rewrites, so the plan edits prose beside a site it does not count. Left as written, the plan would report a contract "pinned" while half its surface is untested | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10; E-01 records both sites and states that the `rerun_suite` path stays unpinned; fact 4 annotated; Scope check's "sole" wording corrected and a new under-scope paragraph states the pin's reach explicitly; E-03's required test docstring must carry the limit |
| PR-803 | MEDIUM | IN-SCOPE | E (testing) | plan F-5 (asserted from an authoring prototype); review's own prototype: clean `['<repo>', '<repo>/.aw/.../revalidate-7989f1021a59']`, mutated `['<repo>/.aw/worktrees/wir001', '<repo>/.aw/.../revalidate-7989f1021a59']` | **THE PIN'S FEASIBILITY AND NON-VACUITY WERE ASSERTED FROM AN AUTHORING PROTOTYPE THAT A REVIEWER COULD NOT REPRODUCE FROM THE PLAN'S TEXT ALONE** (it omits the patch target, the `reason` field and the repeat-turn hazard). Without those, an executor's failure to reproduce it looks like a defect in the plan's premise rather than in their harness | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-12 records the full review prototype with both halves of the mutation triple, so the executor inherits a reproduced result rather than a claimed one; Required tests now says that a failure to reproduce points at the test's shape (most likely the patch target) and not at the plan |
| PR-804 | MEDIUM | IN-SCOPE | E (testing); live-artifact convention | plan facts 2 and 4, F-2, F-4, Required tests (`3246 passed, 2 skipped` at `4bf73373`); review at `f4543b7b`: `3344 passed, 2 skipped`; `tests/test_run_viewer.py` `38 passed` at both | **THE BARE-SUITE BASELINE MOVED 98 PASSES IN EIGHT DAYS.** The plan already instructs re-derivation and already argues (F-3) that a transcribed count rots, so leaving one figure standing as the comparison target is inconsistent with its own thesis | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both measurements recorded side by side with their HEADs in facts 2 and 4, F-4's code block, and Required tests, with the 98-pass movement stated as the reason neither figure is the bar. `tests/test_run_viewer.py` reproducing at `38 passed` from a DIFFERENT lane eight days later is recorded too, since that strengthens F-2 |
| PR-805 | LOW | IN-SCOPE | D (evidence accuracy) | plan F-9 ("cited nine times", "eight sites in `runner_shared` plus once in `oc_runipd`"); `grep -c NoRunnerImportTests agent_workflows/runner_shared.py` -> `7`; `agent_workflows/oc_runipd.py` -> `1` | **THE DANGLING-CITATION COUNT IS WRONG BY ONE: 8 TOTAL, NOT 9.** Immaterial to the plan (the whole matter is deferred to `gia5i7`) but the figure would be inherited by whoever executes that carrier | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 corrected to 7 + 1 = 8 with the per-file `grep -c` evidence; the Deferred row's prose left otherwise intact since its reasoning does not turn on the count |
| PR-806 | LOW | IN-SCOPE | G (open questions); records | plan OQ-01 and OQ-02, both `- Status: open` with `- Owner: reviewer` | **TWO OPEN QUESTIONS NAMED THE REVIEWER AS OWNER AND WERE THEREFORE THIS REVIEW'S TO ANSWER, NOT TO PASS ON.** Leaving them open would strand a decision the plan explicitly assigned to review, and would leave `- Owner: reviewer` asserting an act nobody performed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both ANSWERED and marked `resolved`, with the owner line recording who answered and when. OQ-01: keep the `dh0uno` citation marked historical (basis: this review performed the retraction archaeology for the second time). OQ-02: keep the test in `tests/test_oc_runipd.py` (basis: the host-rebinding measurement makes every working spy host-bound, so no placement is host-neutral). Both recorded as D-1 and D-2 below |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: should the corrected docstring keep the `dh0uno` citation, or drop it as settled history? | Keep it, marked as the original-and-retracted reason | Drop it, on the plan's own stated ground that a closed-bug citation invites re-litigation. Rejected because the citation is being rewritten to say the bug is CLOSED and its acceptance claim WITHDRAWN, which is the opposite of an invitation, and because dropping it forces the next re-measurer to repeat the archaeology | This review had to read `dh0uno`'s `done` status and `checkout_control_root`'s docstring ("That collapse IS the fix") to establish the reason was retracted rather than unlucky - the second performance of that work, the backlog item recording the first. A note naming the retracted reason turns a re-measurement into a confirmation. V-04's evidence list is identical either way, so keeping costs nothing an executor must judge | yes |
| D-2 | OQ-02: should E-03's pin live in `tests/test_oc_runipd.py` or in a host-neutral module? | `tests/test_oc_runipd.py`, beside `WorktreeIsolationTests` | A host-neutral module, on the plan's stated ground that the call site is now shared and a host-named file understates the reach. Rejected on a measurement the question did not have: `run_suite_check` is resolved off `driver_module` at call time, so the spy must patch a specific host module and EVERY working test is host-bound by construction; a host-neutral file would still pick one host while paying for a second fixture | Review prototyped the pin in that exact location and confirmed green, red under mutation, green again (F-12). The real cost (an agy-side regression is not caught) is not eliminated by either choice, so it is recorded in the test's required docstring instead of being traded for a worse fixture | yes |
| D-3 | Is the two-call-site discovery (PR-802) a scope expansion that should add an E-item pinning `rerun_suite` too? | No: record the limit, do not expand | Add a sixth E-item with a gate-answer fixture. Rejected because reaching that lambda needs a gate answer claiming `fixed`, which is a materially larger fixture than this `low`/`chore` plan carries, and because the plan's value is the correction plus the first pin; bundling a second fixture would make the review about test scope rather than about the falsified record | The plan's own Deferred discipline is to name a limit and carry it rather than absorb it. The limit is now stated in three places (F-10, the Scope check's new under-scope paragraph, and the required test docstring), which is what stops a later reader believing the contract is fully guarded | yes |
| D-4 | Should the reviewer fix the eight dangling `NoRunnerImportTests` citations while editing these comments? | No: leave them to `gia5i7`, correcting only the count | Strike them here, since E-05 already edits two comments that contain one. Rejected for the plan's own stated reason, which I verified: the remedy is a nine-site sweep across two modules with a different subject, and it would bury the correction this plan exists to make. `gia5i7` exists and is `open` | The 2026-09-28 maintainer ruling recorded in F-9 already says such pins "will not be restored" and stale comments should drop the reference, so the remedy is settled and only its scheduling is open. E-05 is already instructed not to ADD a new citation | yes |
