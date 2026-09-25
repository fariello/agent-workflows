# Review findings: plan wmuu4k

- Subject-Id: wmuu4k
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `ctrlstate`: keep per-machine control state in-repo and gitignored, and
ignore the lane worktrees root in managed repos. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize` conforms after the revisions. The plan file was committed and unchanged at
review start (`git status --porcelain` empty; last touched by `c41b69fb`), so no pre-review snapshot
was needed.

THIS PLAN IS UNUSUALLY VERIFIABLE AND IT SURVIVED VERIFICATION. Its whole thesis is a claim about
`git check-ignore` behavior in a freshly installed repo, so the review reproduced the probe end to end
rather than reading it: built a fresh `git init` repo, ran `engine._ensure_aw_gitignore`, created a
file under each control path, created a REAL `git worktree add .aw/worktrees/abc123` plus an owner
record, and ran `git check-ignore` on each. Every claim the plan makes about the CURRENT state is
TRUE, including the negative control (`.aw/config/project.json` correctly NOT ignored), and appending
one `/worktrees/` line flips exactly the two failing paths. So the diagnosis and the one-line fix are
both confirmed, and the review's findings are about the plan's MECHANICS, not its thesis.

TWO OF THE FIVE FINDINGS WOULD HAVE STOPPED THE EXECUTOR DEAD, and neither is visible by reading.
PR-001: E-01's prescribed `anchored=True` activates a repair branch that no code can satisfy, so the
new test row would have failed PERMANENTLY rather than only before the fix. PR-002: E-03's prescribed
regeneration command is a measured no-op on an existing file, and after the engine edit it produces a
file that fails E-03's own V-03 assertion. Both were found by running the code, and both are now
corrected in the items with the measurement recorded.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (testing) | `engine._ensure_aw_gitignore` contains exactly one repair: `bare_inbox = re.compile(r"(?m)^inbox/[ \t]*$")`. MEASURED by driving the helper: a pre-existing bare `worktrees/` yields `['worktrees/']` where the branch wants `['/worktrees/']`; `/state/` yields `['state/', '/state/']`; `/workflow-artifacts/` yields `['workflow-artifacts/', '/workflow-artifacts/']` | E-01 PRESCRIBED A TEST ROW THAT CAN NEVER PASS. `AwGitignoreLaneTests` runs branch (d) REPAIR only when `anchored=True`, asserting a pre-existing BARE form is rewritten to the anchored one. That repair is hardcoded to `inbox` and exists for no other lane, so an `anchored=True` row for `/worktrees/` fails FOREVER, not just before E-03. The executor would land the correct engine fix, watch the test still fail on "was not repaired", and have no instruction telling them the column was the problem. The same measurement explains an otherwise puzzling fact the plan did not notice: `/state/` and `/workflow-artifacts/` are anchored in the template yet have NO LANES row, precisely because they would fail this branch too, so `/inbox/` is the only row the existing table can carry at `anchored=True`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now specifies `anchored=False` with the measurement and the reason, states explicitly that the column selects the REPAIR ASSERTION and not the pattern's form (the pattern stays `/worktrees/`, anchored, for the `/inbox/` reason), and points a would-be generalizer at OQ-02 instead of at this plan. V-01 now demands the row be pasted showing `False`, and names the "was not repaired" failure so an executor who gets it wrong is told what it means. |
| PR-002 | HIGH | IN-SCOPE | A (correctness) / E | MEASURED twice: running `_ensure_aw_gitignore` against this repo's existing `.aw/.gitignore` returned `wrote: False` and left it md5-identical; and `_ensure_aw_gitignore` writes the template ONLY under `if not gi.is_file()`, so an existing file takes the BACK-FILL branch, which appends a BARE pattern with no comment (demonstrated: a minimal file back-fills to 14 bare lines, comment-free) | E-03's REGENERATION COMMAND CANNOT PRODUCE THE FILE E-03 ASKS FOR, AND ITS OWN V-03 WOULD CATCH IT. The plan said to regenerate `.aw/.gitignore` by calling `_ensure_aw_gitignore`. Today that is a NO-OP (the file exists and already carries every pattern). After the engine edit it would append a bare `/worktrees/` with no comment, leaving the tracked file differing from `_AW_GITIGNORE_TEMPLATE` by exactly the comment block - and V-03 demands `diff <template> .aw/.gitignore && echo SAME`. Simulated directly: the diff is one line, the comment. The dangerous repair is the obvious one: an executor trusting the command and wanting `SAME` would delete the comment from the template, discarding the anchoring rationale this file's own history says not to remove. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now forbids the regen call, names the measured reason, states the invariant (tracked file byte-identical to the template, which it IS today, measured empty `diff`), and supplies a command that writes the template verbatim: `Path('.aw/.gitignore').write_text(E._AW_GITIGNORE_TEMPLATE, ...)`. VERIFIED at review: that command produces `SAME`. V-03 now names the failure mode and explicitly forbids "fixing" it by deleting the template comment. |
| PR-003 | MEDIUM | UNDER-SCOPE | A (correctness) / B | MEASURED: in a fresh repo with a real lane, `git add -A` staged `.aw/worktrees/.owners/lane1.json` at mode `100644` AND `.aw/worktrees/lane1` at mode `160000`, with git printing its `git rm --cached` submodule hint | THE RECORDED HARM UNDERSTATED ITSELF. The plan described the consequence as untracked paths offered to `git add -A`. What actually happens is worse and is the real argument for the fix: a lane is a REAL git worktree, so a broad add commits an EMBEDDED GITLINK pointing at a commit that exists only on that lane's branch, which is unresolvable for anyone who clones. A reviewer or maintainer weighing a one-line gitignore change against "some scratch shows up in status" may reasonably deprioritize it; against "a phantom submodule enters permanent history" they will not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-4 with the measured modes and the git hint, and referenced from the gate's commit-discipline paragraph so the executor meets it where it matters. E-02 additionally records that its test may use a PLAIN directory (same `check-ignore` verdict, no nested repo in the fixture) and that the gitlink behavior is the WHY rather than something the unit test must reproduce. |
| PR-004 | MEDIUM | IN-SCOPE | G (executability) | The plan's `## Approval and execution gate` (three sentences before the fix) | THE GATE CARRIED ALMOST NO EXECUTION CONTRACT: approval, a path-scoped commit, never push, and the lint checkpoint. Missing were the scope fence, the honesty rule, the disposition of the open questions, the declared spec edit, and - specific to this plan - any instruction preserving its TEST-FIRST structure, which is the only thing that gives a one-line gitignore change any evidence at all. It also did not warn that this repo's root `.gitignore` MASKS the very defect under test, so an executor sanity-checking with `git status` here would see nothing wrong and could conclude the plan was already done. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten with: OQ-01/OQ-02 dispositions and an explicit instruction not to widen scope to OQ-02; a do-not-reorder rule for the test-first structure tied to V-01/V-02's BEFORE+AFTER pastes; a DECLARATION-style scope fence (make-then-justify, no stop-over-scope) naming the two high-traffic files as the genuinely-unsafe case and putting the ROOT `.gitignore` explicitly out of scope; the declared spec edit with a do-not-alter note for the existing placement vocabulary; the honesty rule; commit discipline citing F-4; the conditional transition; and the backlog follow-up with its measured non-failing close. The masking hazard is recorded in `## Scope check`. |
| PR-005 | MEDIUM | IN-SCOPE | G / repository rule | `check_engine.evaluate_durable_carrier` on this file at review start -> `check.ipd-uncarried-obligation`; `carrier_severity_for_plan` -> `error` | OQ-01 CARRIED NO DURABLE CARRIER. Unlike its siblings in this sweep the defect here is subtler, because OQ-01 is `Status: resolved` rather than open - but the rule covers a resolved question too, and this plan's whole point is that the resolution be findable later. Once the plan reached `executed` it would class `done` in `aw attention` and the recorded decision would survive only in the plan body. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Carrier-Declined:` added to OQ-01 noting the decision leaves no successor work and that its one concrete harm is fixed inside this plan; the newly authored OQ-02 carries one from the start. Re-measured: 0 findings. Note the decision ALSO reaches a durable home independently via E-04's spec paragraph, which is the strongest form of this obligation being met. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: the row cannot pass with `anchored=True`. Fix the ROW, or generalize the repair in `_ensure_aw_gitignore` so `anchored=True` becomes truthful? | Fix the ROW to `anchored=False`; record the repair gap as OQ-02 with a recommendation to file it separately. | Generalizing the repair regex over the anchored-pattern list. Rejected: it edits a back-fill that runs on EVERY install in EVERY managed repo and would rewrite lines this plan was never asked to touch, turning a one-line hygiene fix into a change with its own blast radius and its own required before/after evidence. | The gap is strictly PRE-EXISTING and measured: `/state/` and `/workflow-artifacts/` are anchored in the template, have no LANES row, and fail the same branch, so the plan neither creates nor worsens it. `anchored=False` makes the new row assert exactly what is true (template + fresh + back-fill + idempotence). | yes |
| D-2 | PR-002: the regen command is wrong. Replace the command, or relax V-03's `SAME` assertion to tolerate the comment difference? | Replace the command with a verbatim template write. | Relaxing V-03. Rejected: `SAME` is the assertion that keeps the tracked file and the template from drifting, and it currently HOLDS (measured empty `diff`). Weakening a true invariant to accommodate a broken command is backwards. | Measured that the replacement command produces `SAME`; measured that the tracked file equals the template today. The template branch of `_ensure_aw_gitignore` only fires when the file is absent, so no helper call can be the right tool here. | yes |
| D-3 | Should the E-02 test create a REAL `git worktree add`, since that is what a lane actually is? | No. A plain directory is sufficient for the test; record the gitlink behavior as a FINDING (F-4) instead. | Using `git worktree add` in the fixture. Rejected: it puts a second git repo inside a temp fixture for no additional assertion, and `check-ignore` returns the same verdict either way. | Measured both: `check-ignore` reports NOT-ignored for the plain path and for the real worktree identically, while `git add -A` distinguishes them (mode `160000`). The test's claim is about ignore coverage; the gitlink is about consequence, which belongs in the record and the gate. | yes |
| D-4 | OQ-01 is already `Status: resolved` and is the plan's deliverable. Is the missing carrier a real finding, or a false positive of the rule? | A real finding. Add the carrier. | Treating a `resolved` question as exempt. Rejected: the rule's own predicate does not exempt it, and the concern it encodes (the record vanishes when the plan classes `done`) applies to a recorded DECISION as much as to an open question. | `evaluate_durable_carrier` reported it at `error` severity against this file; `carrier_severity_for_plan` -> `error` because `- Date: 2026-09-24` is after `CARRIER_CUTOVER_DATE` 20260919. E-04's spec paragraph independently gives the decision a durable home, which is why `Carrier-Declined` is honest here rather than a dodge. | yes |
| D-5 | This review ran `git worktree add` and `git init` in temp dirs outside the lane. Does that violate the lane-containment instruction? | No, and it was necessary. Keep the probes; clean up after. | (a) Reviewing the claim by reading only. Rejected: the plan's entire thesis is a runtime `git check-ignore` behavior, and PR-001/PR-002 were BOTH invisible to reading. (b) Probing inside the lane. Rejected: this repo's root `.gitignore` MASKS the defect, so a probe here would have produced a false negative. | Lane containment governs where WORK PRODUCTS are written; every edit and commit in this review is inside the lane, and the probes were read-only throwaway repos under the pre-approved temp area. The masking effect is itself now recorded in the plan's `## Scope check` so the next executor does not repeat the mistake. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author           --agent wmuu4k -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize  --agent wmuu4k -> {"outcome":"clean","exit":0,"findings":0}  (after revisions)
check_engine.evaluate_durable_carrier(wmuu4k)  BEFORE -> 1 finding, error (OQ-01)
                                                AFTER -> 0 findings
review_findings._resolved_escalated_questions  -> {'F-6': ('OQ-02','open')}   (join resolves; open, so not stale)

--- THE PLAN'S CENTRAL PROBE, REPRODUCED. Fresh `git init` + engine._ensure_aw_gitignore (wrote: True)
git check-ignore -q .aw/state/x                      -> IGNORED
git check-ignore -q .aw/config/local.json            -> IGNORED
git check-ignore -q .aw/records/runs/r1/x            -> IGNORED
git check-ignore -q .aw/workflow-artifacts/wf1/x     -> IGNORED
git check-ignore -q .aw/config/project.json          -> NOT ignored   (correct: portable, tracked)
git worktree add -q .aw/worktrees/abc123 -b lane1    (a REAL worktree, as a lane is)
git check-ignore -q .aw/worktrees/abc123             -> NOT ignored   <-- the defect
git check-ignore -q .aw/worktrees/.owners/abc123.json-> NOT ignored   <-- the defect
git status --porcelain (with .aw partly tracked)     -> ?? .aw/worktrees/
   => every claim in the plan's Findings table is TRUE as written.

--- THE FIX IS SUFFICIENT (same repo, one line appended)
printf '/worktrees/\n' >> .aw/.gitignore
git check-ignore -q .aw/worktrees/abc123             -> IGNORED
git check-ignore -q .aw/worktrees/.owners/abc123.json-> IGNORED
git status --porcelain                               -> (worktrees line gone)

--- PR-003 / F-4: WHAT `git add -A` ACTUALLY DOES with an unignored lane
git add -A ; git diff --cached --raw
  :000000 100644 ... A  .aw/worktrees/.owners/lane1.json
  :000000 160000 ... A  .aw/worktrees/lane1            <-- mode 160000 = embedded GITLINK
  git also printed its "git rm --cached .aw/worktrees/lane1" submodule hint.

--- PR-001 / F-6: THE REPAIR BRANCH IS inbox-ONLY (helper driven directly, pre-existing bare line)
/workflow-artifacts/     repair -> ['workflow-artifacts/', '/workflow-artifacts/']  PASSES=False
/state/                  repair -> ['state/', '/state/']                            PASSES=False
/worktrees/              repair -> ['worktrees/']                                   PASSES=False
engine._ensure_aw_gitignore repair regex: bare_inbox = re.compile(r"(?m)^inbox/[ \t]*$")   (the only one)
current LANES rows: 'records/runs/' anchored=False | 'records/history.jsonl' anchored=False
                    '/inbox/' anchored=True        (the one lane the repair covers)
python3 -m pytest -o addopts="" -q tests/test_installer.py \
  -k test_every_lane_is_present_anchored_backfilled_and_idempotent  -> 1 passed, 91 deselected
   => a latent constraint on NEW rows, not a current failure.

--- PR-002 / F-7: THE REGEN COMMAND
_ensure_aw_gitignore writes the template only under `if not gi.is_file()`
against this repo's existing .aw/.gitignore     -> wrote: False, md5 UNCHANGED (a no-op today)
back-fill branch output on a minimal file        -> 14 BARE pattern lines, NO comments
simulated post-fix backfilled == template_fixed  -> False (differs by exactly the comment line)
diff <(render _AW_GITIGNORE_TEMPLATE) .aw/.gitignore  -> empty, i.e. SAME   (the invariant, today)
REPLACEMENT command verified: write_text(E._AW_GITIGNORE_TEMPLATE) -> diff SAME

--- Tree facts the plan cites, all confirmed
worktree_lease.WORKTREES_SUBDIR == ".aw/worktrees"
worktree_lease.OWNERS_SUBDIR    == ".aw/worktrees/.owners", whose comment reads
  "Inside the gitignored worktrees root, so it is never committed"   (the quoted claim, verbatim)
check_engine (scope-delta sweep) comment: "`.aw/state/` and `.aw/worktrees/` are gitignored RUNTIME
  scratch ... exclude defensively in case a repo has not gitignored them"   (the plan's claim, true)
this repo's ROOT .gitignore: .aw/state/ | .aw/config/local.json | .aw/workflow-artifacts/ |
  .aw/worktrees/     => THIS is what masks the defect locally
spec 20260810-1447-01: Section 5 "Placement and Git policy" EXISTS, Status: implemented,
  Canonical: true; it defines target-ignored and says config_local/state_runtime MUST be untracked,
  and it does NOT currently name the worktrees root -> E-04's target is correct
backlog e820ka: graduated, Graduated-To: ctrlstate, Work-Kind followup, NO Blocks-Release
  -> the follow-up close will not fail closed; HANDOFF already in place via From-Backlog
```

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001 through PR-005 all FIXED, none deferred, none open. The plan's
diagnosis and its one-line fix were independently reproduced and are correct; the revisions repair two
mechanical instructions that would have blocked the executor and would not have been visible without
running the code.

Readiness `go-pending-approval`. Three things worth a human's attention, none a finding against this
file. FIRST, the defect is REAL in managed repos and is masked in THIS repo by its root `.gitignore`,
so do not sanity-check it with a local `git status`. SECOND, the consequence is a phantom submodule at
mode `160000` in permanent history, not merely untidy status output (F-4), which is the case for doing
it. THIRD, OQ-02 records a genuine PRE-EXISTING hazard this plan deliberately does not fix: the
bare-form repair in `_ensure_aw_gitignore` covers only `inbox`, so `/state/`, `/workflow-artifacts/`
and the new `/worktrees/` have none; the recommendation is to file it rather than widen this plan.
