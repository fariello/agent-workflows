# Review findings: plan dv7c49

- Subject-Id: dv7c49
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b471551a` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after revision. No pre-review snapshot was owed: the plan was committed and byte-identical to the lane
input. No production code was modified by this review, and none is modified by the plan. Every runtime
measurement below was taken with `AW_NO_REEXEC=1 python3 -m agent_workflows ...` from inside the lane,
following the plan's own recorded convention about the ambient `aw` resolving the main checkout.

DISCLOSURE: this review shares a model family with the plan's author and with Round 1 of the review
being corrected, so a reader should weigh it as a near-self-review. That is the same disclosure the
plan's own E-02 requires of the round it writes.

EVERY SUBSTANTIVE CLAIM IN THIS PLAN REPRODUCED, AND THE MOST CONSEQUENTIAL ONE REPRODUCED IN FULL
DETAIL. The plan's central discovery is that `9iiqmm`'s implementation never landed, and it holds:
`git show main:agent_workflows/attention.py | grep -c inbox` is `0`, the same for
`tests/test_attention.py`, `git log --all -S'waiting in \`.aw/inbox/\`' -- '*.py'` returns nothing, and
neither `InboxWaitingCountTests` nor `InboxFooterNudgeTests` exists in the suite. All five recovery
shas still resolve (`git cat-file -t`: three commits, two blobs), both blob sizes match the plan to the
byte (138154 and 114999), the dangling commit subjects are verbatim as quoted including "WIP INTERRUPTED
SNAPSHOT (not finished work)", and `git cat-file -p 9effdcef` carries the counter at the quoted line
`f"TODO: {waiting} {noun} waiting in \`.aw/inbox/\`. ..."`. The non-TTY findings hold equally:
`select_output`'s docstring says "TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE" and "NEITHER
WAS EVER IMPLEMENTED", `docs/cli-output-contract.md` Section 9 is headed "RETRACTED 2026-09-19", and a
piped `attention` printed the human board while `--agent` printed the JSONL record. F-07, F-08 and F-09
also verify, as do the precedent (`cscv0c` is executed and used exactly the `- <date> note (<id6>):`
shape), the reviews-tree rounds mechanism, Round 1's column counts (9 and 6, exactly as E-02 claims),
the newest-first history ordering, and `note` being outside `ipd_schema.RECOGNIZED_STATUS`. Both
pre-commit gates were probed on a real staged append to `9iiqmm` and both exited 0, so the sanctioned
route works as claimed; the probe was reverted and the tree left clean.

WHAT REVIEW FOUND IS THAT THE PLAN IS ACCURATE ABOUT THE WORLD AND STALE ABOUT ITSELF. All five
findings concern the plan's own self-description, and they share a single cause worth naming because it
generalizes: THIS PLAN'S AUTHORING RUN MUTATED THE ARTIFACTS THE PLAN TEXT DESCRIBES. The run graduated
backlog `3sh9d6` from `open/` to `graduated/` while the plan was asserting it sat at its `open/` path
with `- Status: open`.

**A DECLARED SCOPE-PATH DID NOT EXIST, AND IT MADE THE PLAN FAIL `aw check plans` (PR-701, HIGH).**
`check_engine.stale_record_scope_paths` on this plan reported the `3sh9d6` entry as `moved`, resolving
to the `graduated/` path. `check.scope-path-target-stale` is registered `error`, so the plan failed the
repository's own gate before executing a single step. The failure mode is worse than a clean refusal:
`runner_shared` refuses only `moved-terminal` and `vanished`, so the runner would have DISPATCHED this
plan and the error would have surfaced later as a CI failure on a tree the plan had already touched.
FIXED by correcting the declaration to `graduated/`; re-measured, `stale_record_scope_paths` returns
zero entries and `check_type(repo, "plans")` reports zero findings for this plan.

**E-05 AND V-05 BOTH ASSERTED A STATUS THE ARTIFACT NO LONGER HELD (PR-702, HIGH).** E-05 instructed
"do NOT change the item's `- Status:` (the runner sets `graduated` on verification)" and V-05 required
confirming it "is still `open`". Measured: `- Status: graduated`, with the history record "2026-09-28
set (aw backlog): graduated by run run-20260928T235941Z-1396311: dv7c49" written by this plan's own
authoring run. So the parenthetical describes an event that had already happened, and V-05 as written
would have FAILED on a correct execution. That is the dangerous shape: an executor meeting a validation
that cannot pass is invited to make it pass, and here the obvious way would be to set the status back to
`open`, corrupting the item. FIXED in both places, with the expectation restated as graduated-before and
graduated-after, since `aw backlog note` annotates without transitioning.

**E-04'S REFUSAL BRANCH IS MEASURED-UNREACHABLE AND WAS PRESENTED AS LIKELY (PR-703, MEDIUM).** The
plan called a done-to-live move "the unusual direction [that] may not be permitted" and gave a STOP
instruction. Measured on throwaway copies of `plbkp5`: `aw backlog set graduated plbkp5` exits `rc=0`
and moves the file to `graduated/`, and `aw backlog set open plbkp5` exits `rc=0` and moves it to
`open/`. `backlog.py` enforces no forward-only transition table, and `--allow-terminal-reopen` documents
itself "Inert for backlog items", confirming terminal reopening is ungated on this record type. A
measured-impossible refusal advertised as an expected path invites an executor to stop on an unrelated
error and report it as the anticipated case. FIXED by recording the measurement, stating that success is
expected, and keeping the stop instruction only as a genuine-surprise guard whose firing is itself a
finding. This also collapses the open half of OQ-01: `an77ub` is the live carrier, so the rule the plan
wrote resolves to `graduated` rather than leaving the executor a choice.

**THREE SECTIONS CONTRADICTED E-03 ON WHETHER TO CREATE OR VERIFY THE BACKLOG ITEM (PR-704, LOW).**
E-03 is emphatic ("VERIFY, DO NOT RE-FILE ... DO NOT CREATE A SECOND ITEM") because `an77ub` was filed
at authoring, yet `## Proposed changes` item 3 read "one new backlog item under `open/`" and V-03
required pasting "the `aw backlog new` invocation". An executor following V-03 literally would file a
duplicate and split the defect's history across two items, which is precisely what E-03 forbids. FIXED:
item 3 now describes verification, and V-03 now requires the resolved path of the existing item and
FAILS on an `aw backlog new` invocation.

`an77ub` ITSELF NEEDED NOTHING AND IS EXEMPLARY. It carries all five measured facts with the command
that produced each, all five recovery shas with byte sizes, an explicit `bug`/`Blocks-Release: next`
justification, a stated honest limit on what it does not decide, and a warning not to run `git gc`. One
evidence demand was ADDED to V-03 rather than to the item: paste `git cat-file -p 9effdcef | grep -n
'waiting in'`, so the blob is shown to carry the implementation rather than merely to exist, since
existence alone does not establish recoverability.

A conventions bullet was added recording the generalizable lesson, because this failure mode will recur
for any plan whose Scope-Paths include the backlog item it graduated from: declare the path the item
will hold AFTER graduation, and verify with `stale_record_scope_paths` before review rather than
trusting the path first read. The `- Readiness:` field was written by this review (`go-pending-approval`)
and the gate's self-description, which correctly explained why an AUTHOR must omit it, was updated to
record that the review owning it has now run.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | G. Plan executability | `check_engine.stale_record_scope_paths` on this plan -> `.aw/records/backlog/open/20260920-3sh9d6-...` is `moved` (resolved: `graduated/...`); `check.scope-path-target-stale` registered `error`; `runner_shared` refuses only `moved-terminal`/`vanished` | A declared Scope-Path pointed at `3sh9d6`'s pre-graduation `open/` path, which this plan's own authoring run had already vacated. The plan therefore failed `aw check plans` at `error` before executing, and the runner would still have dispatched it, so it surfaces as a CI failure rather than a clean refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the declaration to `graduated/`. Re-measured: zero stale entries, zero findings for this plan. |
| PR-702 | HIGH | IN-SCOPE | A. Correctness; E. Verification | `- Status: graduated` on `3sh9d6`; history "2026-09-28 set (aw backlog): graduated by run run-20260928T235941Z-1396311: dv7c49" | E-05 said the runner "sets `graduated` on verification" (already done) and V-05 required confirming the status "is still `open`" (already false). V-05 as written would fail on a correct execution, inviting an executor to make it pass by setting the status back and corrupting the item. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Both corrected to expect `graduated` before and after, noting `aw backlog note` does not transition. |
| PR-703 | MEDIUM | IN-SCOPE | C. Operability | `aw backlog set graduated plbkp5` -> `rc=0`, moves to `graduated/`; `aw backlog set open plbkp5` -> `rc=0`, moves to `open/`; `--allow-terminal-reopen` help: "Inert for backlog items"; no transition table in `backlog.py` | E-04 presented a done-to-live refusal as a likely outcome and gave a STOP instruction. Both candidate transitions in fact succeed, so the branch is unreachable. Advertising a measured-impossible refusal invites stopping on an unrelated error and calling it the anticipated case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded the measurement, stated success is expected, kept the stop instruction only as a surprise guard whose firing is itself a finding. OQ-01 now resolves to `graduated` outright. |
| PR-704 | LOW | IN-SCOPE | G. Plan executability | `## Proposed changes` item 3: "one new backlog item"; V-03: "paste the `aw backlog new` invocation"; E-03: "VERIFY, DO NOT RE-FILE ... DO NOT CREATE A SECOND ITEM" | The plan contradicted itself on whether E-03 creates or verifies `an77ub`. Following V-03 literally files a duplicate and splits the defect's history. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 3 now describes verification; V-03 requires the existing item's resolved path and FAILS on an `aw backlog new` invocation. |
| PR-705 | LOW | UNDER-SCOPE | E. Verification | `git cat-file -t 9effdcef` proves existence; `git cat-file -p 9effdcef \| grep -n 'waiting in'` proves content | V-03 required proving the recovery shas RESOLVE but not that the blob carries the implementation. Existence alone does not establish recoverability, which is the property the shas are recorded for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the content-proof command to V-03. `an77ub` itself needed no change. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The declared `3sh9d6` Scope-Path is stale. Correct the path, or drop the entry? | Correct it to the `graduated/` path | (a) drop the entry, rejected because E-05 genuinely writes that file so an undeclared edit would trip the finalize scope gate; (b) leave it and let the executor discover the move, rejected because the rule is `error`-severity and the runner dispatches `moved` anyway, so the cost lands in CI | `stale_record_scope_paths` reports `moved` with the resolved path; `check.scope-path-target-stale` registry severity `error`; `runner_shared` refusal set excludes `moved` | yes |
| D-2 | Should `plbkp5` be re-opened as `graduated` or `open`, which the plan left conditional? | `graduated`, stated outright | `open`, which the plan's own parenthetical suggested "unless `an77ub` is itself made the carrier"; rejected because E-03 in the same plan establishes `an77ub` as exactly that carrier, so the condition is already satisfied and leaving it conditional invites a coin flip | AGENTS.md `graduated` = "design handed off ... code not yet written"; `an77ub` exists at `open/` and owns the lost implementation; both transitions measured `rc=0` | yes |
| D-3 | Should this review verify the recovery shas itself, or trust the plan's measurement? | Verify independently | Trusting the plan, rejected because the shas are unreachable objects whose survival is the plan's own named risk, so a review that does not re-check them cannot claim the recovery route works | All five resolve via `git cat-file -t`; sizes 138154 and 114999 match; `9effdcef` contains the counter line | yes |
| D-4 | Does the plan need a spec amendment? | No | Amending `docs/cli-output-contract.md` or `select_output`, rejected because both are already correct and are the evidence the plan cites; amending them would mean re-asserting a retracted promise | F-01 and F-02 verified: the docstring and Section 9 both already record the retraction; no `.spec.md` governs what a plan's Findings table asserts | yes |

No `Reversible: no` decision was taken, so no escalation is owed. No finding was left `OPEN` or
`DEFERRED`, so no `- Blocking: yes` escalation question is owed under the gate threshold.
